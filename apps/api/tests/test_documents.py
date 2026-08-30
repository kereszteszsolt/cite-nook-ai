# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest

from app.application.documents import DocumentService
from app.core.settings import Settings
from app.persistence.models import Document


class DocumentSession:
    def __init__(self, documents: list[Document], *, fail_commit: bool = False) -> None:
        self.documents = documents
        self.fail_commit = fail_commit
        self.statement = ""
        self.deleted: list[Document] = []
        self.committed = False
        self.rolled_back = False
        self.refreshed: list[Document] = []

    def scalars(self, statement: Any) -> list[Document]:
        self.statement = str(statement)
        return self.documents

    def get(self, model: type[Any], document_id: UUID) -> Document | None:
        assert model is Document
        return next((item for item in self.documents if item.id == document_id), None)

    def delete(self, document: Document) -> None:
        self.deleted.append(document)

    def commit(self) -> None:
        if self.fail_commit:
            raise RuntimeError("database unavailable")
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True

    def refresh(self, document: Document) -> None:
        self.refreshed.append(document)


def document_settings(upload_dir: Path) -> Settings:
    return Settings(
        database_url="postgresql+psycopg://unused",
        ollama_host="http://ollama.test",
        chat_models=("chat-a",),
        embedding_models=("embed-a",),
        default_chat_model="chat-a",
        default_embedding_model="embed-a",
        brand_config_path=Path("brand.json"),
        cors_origins=("http://localhost:5173",),
        upload_dir=upload_dir,
    )


def stored_document(upload_dir: Path, *, file_name: str = "notes.txt") -> Document:
    document_id = uuid4()
    directory = upload_dir / str(document_id)
    directory.mkdir(parents=True)
    path = directory / file_name
    path.write_text("document content", encoding="utf-8")
    return Document(
        id=document_id,
        file_name=file_name,
        content_type="text/plain",
        file_path=str(path),
        size_bytes=path.stat().st_size,
        sha256="0" * 64,
        status="ready",
        chunk_count=2,
        is_active=True,
        embedding_model="embed-a",
    )


def test_lists_documents_newest_first() -> None:
    documents = [
        Document(id=uuid4(), file_name="new.txt", embedding_model="embed-a"),
        Document(id=uuid4(), file_name="old.txt", embedding_model="embed-a"),
    ]
    session = DocumentSession(documents)

    assert DocumentService(document_settings(Path("uploads"))).list(  # type: ignore[arg-type]
        session
    ) == documents
    assert "documents.created_at DESC" in session.statement


def test_original_file_is_limited_to_the_document_uuid_directory(tmp_path: Path) -> None:
    service = DocumentService(document_settings(tmp_path))
    document = stored_document(tmp_path)

    assert service.original_file(document) == Path(document.file_path)

    outside = tmp_path.parent / "outside.txt"
    outside.write_text("outside", encoding="utf-8")
    document.file_path = str(outside)
    assert service.original_file(document) is None


def test_set_active_persists_only_the_retrieval_selection(tmp_path: Path) -> None:
    document = stored_document(tmp_path)
    original_path = document.file_path
    session = DocumentSession([document])

    updated = DocumentService(document_settings(tmp_path)).set_active(  # type: ignore[arg-type]
        session, document.id, is_active=False
    )

    assert updated is document
    assert document.is_active is False
    assert document.status == "ready"
    assert document.chunk_count == 2
    assert document.file_path == original_path
    assert session.committed is True
    assert session.refreshed == [document]
    assert Path(original_path).is_file()


def test_set_active_returns_none_for_an_unknown_document(tmp_path: Path) -> None:
    session = DocumentSession([])

    updated = DocumentService(document_settings(tmp_path)).set_active(  # type: ignore[arg-type]
        session, uuid4(), is_active=False
    )

    assert updated is None
    assert session.committed is False
    assert session.refreshed == []


def test_set_active_rolls_back_when_the_database_commit_fails(tmp_path: Path) -> None:
    document = stored_document(tmp_path)
    session = DocumentSession([document], fail_commit=True)

    with pytest.raises(RuntimeError, match="database unavailable"):
        DocumentService(document_settings(tmp_path)).set_active(  # type: ignore[arg-type]
            session, document.id, is_active=False
        )

    assert session.rolled_back is True
    assert session.refreshed == []


def test_delete_removes_the_database_record_and_stored_directory(tmp_path: Path) -> None:
    document = stored_document(tmp_path)
    directory = Path(document.file_path).parent
    session = DocumentSession([document])

    deleted = DocumentService(document_settings(tmp_path)).delete(  # type: ignore[arg-type]
        session, document.id
    )

    assert deleted is True
    assert session.deleted == [document]
    assert session.committed is True
    assert directory.exists() is False


def test_delete_restores_the_directory_when_the_database_commit_fails(
    tmp_path: Path,
) -> None:
    document = stored_document(tmp_path)
    path = Path(document.file_path)
    session = DocumentSession([document], fail_commit=True)

    with pytest.raises(RuntimeError, match="database unavailable"):
        DocumentService(document_settings(tmp_path)).delete(  # type: ignore[arg-type]
            session, document.id
        )

    assert session.rolled_back is True
    assert path.read_text(encoding="utf-8") == "document content"


def test_delete_returns_false_for_an_unknown_document(tmp_path: Path) -> None:
    session = DocumentSession([])

    assert (
        DocumentService(document_settings(tmp_path)).delete(  # type: ignore[arg-type]
            session, uuid4()
        )
        is False
    )
    assert session.committed is False
