# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import asyncio
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest

from app.application.uploads import (
    DocumentUploadService,
    EmptyUploadError,
    UnsupportedDocumentTypeError,
    UploadTooLargeError,
    safe_file_name,
)
from app.core.settings import Settings
from app.persistence.models import Document, IngestionJob


class RecordingSession:
    def __init__(self) -> None:
        self.added: list[Any] = []
        self.committed = False
        self.rolled_back = False

    def add_all(self, objects: list[Any]) -> None:
        self.added.extend(objects)

    def commit(self) -> None:
        document = next(item for item in self.added if isinstance(item, Document))
        assert Path(document.file_path).is_file()
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True


class ChunkedUpload:
    def __init__(
        self,
        filename: str,
        chunks: list[bytes],
        content_type: str = "text/plain",
    ) -> None:
        self.filename = filename
        self.content_type = content_type
        self._chunks = chunks
        self.read_sizes: list[int] = []
        self.closed = False

    async def read(self, size: int) -> bytes:
        self.read_sizes.append(size)
        return self._chunks.pop(0) if self._chunks else b""

    async def close(self) -> None:
        self.closed = True


def upload_settings(upload_dir: Path, max_upload_bytes: int = 20 * 1024 * 1024) -> Settings:
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
        max_upload_bytes=max_upload_bytes,
    )


@pytest.mark.parametrize(
    ("file_name", "content_type"),
    [
        ("paper.pdf", "application/pdf"),
        (
            "report.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ),
        ("notes.txt", "text/plain"),
        ("guide.md", "text/markdown"),
        ("guide.markdown", "text/markdown"),
    ],
)
def test_upload_service_accepts_supported_document_types(
    tmp_path: Path,
    file_name: str,
    content_type: str,
) -> None:
    upload = ChunkedUpload(file_name, [b"document bytes"], content_type)
    session = RecordingSession()
    document = asyncio.run(
        DocumentUploadService(upload_settings(tmp_path)).store(
            session,  # type: ignore[arg-type]
            file=upload,  # type: ignore[arg-type]
            embedding_model="embed-a",
        )
    )

    assert document.file_name == file_name
    assert document.content_type == content_type
    assert document.embedding_model == "embed-a"
    assert document.is_active is True
    assert session.committed is True
    assert any(isinstance(item, IngestionJob) for item in session.added)


def test_upload_is_streamed_hashed_and_moved_before_job_commit(tmp_path: Path) -> None:
    first_chunk = b"first chunk"
    second_chunk = b"second chunk"
    upload = ChunkedUpload("../../notes.txt", [first_chunk, second_chunk])
    session = RecordingSession()

    document = asyncio.run(
        DocumentUploadService(upload_settings(tmp_path)).store(
            session,  # type: ignore[arg-type]
            file=upload,  # type: ignore[arg-type]
            embedding_model="embed-a",
        )
    )

    assert document.file_name == "notes.txt"
    assert Path(document.file_path).parent.name == str(document.id)
    assert Path(document.file_path).read_bytes() == first_chunk + second_chunk
    assert document.sha256 == sha256(first_chunk + second_chunk).hexdigest()
    assert document.embedding_model == "embed-a"
    assert upload.read_sizes == [1024 * 1024, 1024 * 1024, 1024 * 1024]
    assert upload.closed is True
    assert session.committed is True


def test_oversized_upload_rolls_back_and_removes_partial_bytes(tmp_path: Path) -> None:
    upload = ChunkedUpload("large.txt", [b"too large"])
    session = RecordingSession()

    with pytest.raises(UploadTooLargeError, match="upload exceeds"):
        asyncio.run(
            DocumentUploadService(upload_settings(tmp_path, max_upload_bytes=4)).store(
                session,  # type: ignore[arg-type]
                file=upload,  # type: ignore[arg-type]
                embedding_model="embed-a",
            )
        )

    assert list(tmp_path.iterdir()) == []
    assert session.rolled_back is True
    assert upload.closed is True


def test_empty_and_unsupported_uploads_are_rejected(tmp_path: Path) -> None:
    empty = ChunkedUpload("empty.md", [])
    unsupported = ChunkedUpload("archive.zip", [b"content"])
    session = RecordingSession()
    service = DocumentUploadService(upload_settings(tmp_path))

    with pytest.raises(EmptyUploadError):
        asyncio.run(
            service.store(
                session,  # type: ignore[arg-type]
                file=empty,  # type: ignore[arg-type]
                embedding_model="embed-a",
            )
        )
    with pytest.raises(UnsupportedDocumentTypeError):
        asyncio.run(
            service.store(
                session,  # type: ignore[arg-type]
                file=unsupported,  # type: ignore[arg-type]
                embedding_model="embed-a",
            )
        )

    assert empty.closed is True
    assert unsupported.closed is True


def test_safe_file_name_removes_paths_controls_and_bounds_length() -> None:
    assert safe_file_name(r"C:\fakepath\report.txt") == "report.txt"
    assert safe_file_name("../nested/control\x00.md") == "control.md"
    assert len(safe_file_name(f"{'x' * 300}.pdf")) == 240
