# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections.abc import Sequence
from datetime import timedelta
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from app.ai.contracts import ModelProviderUnavailableError
from app.application.ingestion import IngestionService
from app.core.settings import Settings
from app.persistence.models import Document, IngestionJob, utc_now
from app.rag.contracts import IndexDocument, TextSection


class FakeIndexer:
    def __init__(
        self,
        *,
        item_count: int = 3,
        error: Exception | None = None,
    ) -> None:
        self.item_count = item_count
        self.error = error
        self.replace_calls: list[
            tuple[Any, IndexDocument, list[TextSection]]
        ] = []

    def replace_document(
        self,
        session: Any,
        document: IndexDocument,
        sections: Sequence[TextSection],
    ) -> int:
        self.replace_calls.append((session, document, list(sections)))
        if self.error is not None:
            raise self.error
        return self.item_count

    def delete_document(self, session: Any, document_id: UUID) -> None:
        pass


class ProcessSession:
    def __init__(self, job: IngestionJob) -> None:
        self.job = job
        self.commits = 0
        self.rollbacks = 0

    def get(self, model: type[Any], identifier: UUID) -> IngestionJob | None:
        assert model is IngestionJob
        return self.job if identifier == self.job.id else None

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


class ClaimResult:
    def __init__(self, job_id: UUID | None) -> None:
        self.job_id = job_id

    def first(self) -> tuple[UUID] | None:
        return (self.job_id,) if self.job_id else None


class ClaimSession:
    def __init__(self, job_id: UUID | None) -> None:
        self.job_id = job_id
        self.sql = ""
        self.parameters: dict[str, str] = {}
        self.committed = False

    def execute(self, statement: Any, parameters: dict[str, str]) -> ClaimResult:
        self.sql = str(statement)
        self.parameters = parameters
        return ClaimResult(self.job_id)

    def commit(self) -> None:
        self.committed = True


class ScalarRows:
    def __init__(self, jobs: list[IngestionJob]) -> None:
        self.jobs = jobs

    def all(self) -> list[IngestionJob]:
        return self.jobs


class StaleSession:
    def __init__(self, jobs: list[IngestionJob]) -> None:
        self.jobs = jobs
        self.committed = False

    def scalars(self, _: Any) -> ScalarRows:
        return ScalarRows(self.jobs)

    def commit(self) -> None:
        self.committed = True


def settings(upload_dir: Path, *, stale_minutes: int = 15) -> Settings:
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
        ingestion_stale_minutes=stale_minutes,
    )


def document_and_job(path: Path, *, status: str = "processing") -> tuple[Document, IngestionJob]:
    document_id = uuid4()
    document = Document(
        id=document_id,
        file_name=path.name,
        content_type="text/plain",
        file_path=str(path),
        size_bytes=path.stat().st_size,
        sha256="0" * 64,
        status=status,
        embedding_model="embed-a",
    )
    job = IngestionJob(
        id=uuid4(),
        document_id=document_id,
        status=status,
        started_at=utc_now(),
    )
    job.document = document
    return document, job


def test_claim_uses_skip_locked_and_marks_the_worker() -> None:
    job_id = uuid4()
    session = ClaimSession(job_id)

    claimed = IngestionService(
        indexer=FakeIndexer(),
        settings=settings(Path("uploads")),
        worker_id="worker-a",
    ).claim_next_job(session)  # type: ignore[arg-type]

    assert claimed == job_id
    assert "FOR UPDATE SKIP LOCKED" in session.sql
    assert session.parameters == {"worker_id": "worker-a"}
    assert session.committed is True


def test_processing_extracts_text_and_delegates_index_work(tmp_path: Path) -> None:
    path = tmp_path / "notes.txt"
    path.write_text("Readable document content.", encoding="utf-8")
    document, job = document_and_job(path)
    session = ProcessSession(job)
    indexer = FakeIndexer(item_count=4)
    service = IngestionService(indexer=indexer, settings=settings(tmp_path))

    assert service.process_job(session, job.id) is True  # type: ignore[arg-type]

    assert len(indexer.replace_calls) == 1
    called_session, index_document, sections = indexer.replace_calls[0]
    assert called_session is session
    assert index_document == IndexDocument(
        document_id=document.id,
        document_name="notes.txt",
        embedding_model="embed-a",
    )
    assert sections == [TextSection("Readable document content.")]
    assert document.status == "ready"
    assert document.chunk_count == 4
    assert job.status == "completed"
    assert session.commits == 2


def test_index_failure_keeps_the_existing_failed_job_behavior(tmp_path: Path) -> None:
    path = tmp_path / "notes.txt"
    path.write_text("Readable content.", encoding="utf-8")
    document, job = document_and_job(path)
    session = ProcessSession(job)
    service = IngestionService(
        indexer=FakeIndexer(
            error=ModelProviderUnavailableError("Ollama embedding request failed.")
        ),
        settings=settings(tmp_path),
    )

    assert service.process_job(session, job.id) is False  # type: ignore[arg-type]

    assert session.rollbacks == 1
    assert session.commits == 2
    assert job.status == "failed"
    assert job.error_message == "Ollama embedding request failed."
    assert document.status == "failed"
    assert document.error_message == "Ollama embedding request failed."


def test_stale_processing_jobs_are_requeued_after_the_configured_interval(
    tmp_path: Path,
) -> None:
    path = tmp_path / "notes.txt"
    path.write_text("content", encoding="utf-8")
    document, job = document_and_job(path)
    job.started_at = utc_now() - timedelta(minutes=16)
    job.worker_id = "lost-worker"
    session = StaleSession([job])

    reset = IngestionService(
        indexer=FakeIndexer(),
        settings=settings(tmp_path, stale_minutes=15),
    ).reset_stale_jobs(session)  # type: ignore[arg-type]

    assert reset == 1
    assert session.committed is True
    assert job.status == "queued"
    assert job.worker_id is None
    assert job.started_at is None
    assert document.status == "queued"
