# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import shutil
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.orm import Session

from ..models import Document, IngestionJob
from ..settings import Settings, get_settings

SUPPORTED_DOCUMENT_SUFFIXES = frozenset({".pdf", ".docx", ".txt", ".md", ".markdown"})
UPLOAD_CHUNK_BYTES = 1024 * 1024


class UploadValidationError(ValueError):
    pass


class UnsupportedEmbeddingModelError(UploadValidationError):
    pass


class UnsupportedDocumentTypeError(UploadValidationError):
    pass


class EmptyUploadError(UploadValidationError):
    pass


class UploadTooLargeError(UploadValidationError):
    pass


class DocumentUploadService:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    async def store(
        self,
        session: Session,
        *,
        file: UploadFile,
        embedding_model: str,
    ) -> Document:
        directory: Path | None = None
        try:
            if embedding_model not in self._settings.embedding_models:
                raise UnsupportedEmbeddingModelError("Unsupported embedding model.")

            file_name = safe_file_name(file.filename)
            if Path(file_name).suffix.lower() not in SUPPORTED_DOCUMENT_SUFFIXES:
                raise UnsupportedDocumentTypeError(
                    "Supported document types: PDF, DOCX, TXT, and Markdown."
                )

            document_id = uuid4()
            directory = self._settings.upload_dir / str(document_id)
            directory.mkdir(parents=True, exist_ok=False)
            destination = directory / file_name
            temporary = directory / f".{file_name}.uploading"
            digest = sha256()
            size_bytes = 0

            with temporary.open("wb") as output:
                while chunk := await file.read(UPLOAD_CHUNK_BYTES):
                    size_bytes += len(chunk)
                    if size_bytes > self._settings.max_upload_bytes:
                        limit_mb = self._settings.max_upload_bytes // 1024 // 1024
                        raise UploadTooLargeError(
                            f"The upload exceeds the {limit_mb} MB limit."
                        )
                    digest.update(chunk)
                    output.write(chunk)

            if size_bytes == 0:
                raise EmptyUploadError("The uploaded document is empty.")

            temporary.replace(destination)
            document = Document(
                id=document_id,
                file_name=file_name,
                content_type=(file.content_type or "application/octet-stream")[:150],
                file_path=str(destination),
                size_bytes=size_bytes,
                sha256=digest.hexdigest(),
                status="queued",
                embedding_model=embedding_model,
            )
            job = IngestionJob(document_id=document_id, status="queued")
            session.add_all([document, job])
            session.commit()
            return document
        except Exception:
            session.rollback()
            if directory is not None:
                shutil.rmtree(directory, ignore_errors=True)
            raise
        finally:
            await file.close()


def safe_file_name(value: str | None) -> str:
    candidate = Path((value or "document").replace("\\", "/")).name.strip()
    candidate = "".join(character for character in candidate if character.isprintable())
    if candidate in {"", ".", ".."}:
        return "document"
    if len(candidate) <= 240:
        return candidate
    suffix = Path(candidate).suffix[:20]
    stem_limit = max(1, 240 - len(suffix))
    return f"{Path(candidate).stem[:stem_limit]}{suffix}"
