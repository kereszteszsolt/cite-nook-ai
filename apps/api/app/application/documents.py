# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import shutil
from pathlib import Path
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.settings import Settings, get_settings
from ..persistence.models import Document


class DocumentService:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    def list(self, session: Session) -> list[Document]:
        return list(
            session.scalars(
                select(Document).order_by(Document.created_at.desc(), Document.id.desc())
            )
        )

    def get(self, session: Session, document_id: UUID) -> Document | None:
        return session.get(Document, document_id)

    def set_active(
        self, session: Session, document_id: UUID, *, is_active: bool
    ) -> Document | None:
        document = self.get(session, document_id)
        if document is None:
            return None

        document.is_active = is_active
        try:
            session.commit()
        except Exception:
            session.rollback()
            raise
        session.refresh(document)
        return document

    def original_file(self, document: Document) -> Path | None:
        path = Path(document.file_path).resolve()
        if not _is_document_path(path, document.id, self._settings.upload_dir):
            return None
        return path if path.is_file() else None

    def delete(self, session: Session, document_id: UUID) -> bool:
        document = self.get(session, document_id)
        if document is None:
            return False

        directory = _document_directory(document, self._settings.upload_dir)
        quarantine: Path | None = None
        if directory is not None and directory.is_dir():
            quarantine = directory.with_name(f".{directory.name}.{uuid4()}.deleting")
            directory.replace(quarantine)

        try:
            session.delete(document)
            session.commit()
        except Exception:
            session.rollback()
            if quarantine is not None and quarantine.exists() and not directory.exists():
                quarantine.replace(directory)
            raise

        if quarantine is not None:
            shutil.rmtree(quarantine)
        return True


def _document_directory(document: Document, upload_dir: Path) -> Path | None:
    path = Path(document.file_path).resolve()
    if not _is_document_path(path, document.id, upload_dir):
        return None
    return path.parent


def _is_document_path(path: Path, document_id: UUID, upload_dir: Path) -> bool:
    root = upload_dir.resolve()
    try:
        relative = path.relative_to(root)
    except ValueError:
        return False
    return len(relative.parts) == 2 and relative.parts[0] == str(document_id)
