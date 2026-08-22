# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from app.models import Document, DocumentChunk, IngestionJob, utc_now
from app.services.ingestion import IngestionService
from app.settings import Settings


class FakeGateway:
    def __init__(self) -> None:
        self.batches: list[list[str]] = []

    def embed(self, model: str, inputs: list[str]) -> list[list[float]]:
        assert model == "embed-a"
        self.batches.append(inputs)
        return [[float(len(value)), 0.5, 1.0] for value in inputs]


class ProcessSession:
    def __init__(self, job: IngestionJob) -> None:
        self.job = job
        self.added: list[Any] = []
        self.executed: list[Any] = []
        self.commits = 0
        self.rollbacks = 0

    def get(self, model: type[Any], identifier: UUID) -> IngestionJob | None:
        assert model is IngestionJob
        return self.job if identifier == self.job.id else None

    def execute(self, statement: Any) -> None:
        self.executed.append(statement)

    def add_all(self, objects: list[Any]) -> None:
        self.added.extend(objects)

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


def settings(upload_dir: Path, *, batch_size: int = 2, stale_minutes: int = 15) -> Settings:
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
        embedding_batch_size=batch_size,
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
        gateway=FakeGateway(),
        settings=settings(Path("uploads")),
        worker_id="worker-a",
    ).claim_next_job(session)  # type: ignore[arg-type]

    assert claimed == job_id
    assert "FOR UPDATE SKIP LOCKED" in session.sql
    assert session.parameters == {"worker_id": "worker-a"}
    assert session.committed is True


def test_processing_extracts_batches_and_builds_persistent_chunks(tmp_path: Path) -> None:
    path = tmp_path / "notes.txt"
    path.write_text(" ".join(f"content-{index}." for index in range(600)), encoding="utf-8")
    document, job = document_and_job(path)
    session = ProcessSession(job)
    gateway = FakeGateway()
    service = IngestionService(gateway=gateway, settings=settings(tmp_path, batch_size=2))

    assert service.process_job(session, job.id) is True  # type: ignore[arg-type]

    chunks = [item for item in session.added if isinstance(item, DocumentChunk)]
    assert len(chunks) > 2
    assert all(len(batch) <= 2 for batch in gateway.batches)
    assert sum(len(batch) for batch in gateway.batches) == len(chunks)
    assert [chunk.ordinal for chunk in chunks] == list(range(len(chunks)))
    assert all(chunk.embedding_model == "embed-a" for chunk in chunks)
    assert all(chunk.page_number is None for chunk in chunks)
    assert all(len(chunk.embedding) == 3 for chunk in chunks)
    assert document.status == "ready"
    assert document.chunk_count == len(chunks)
    assert job.status == "completed"
    assert session.commits == 2


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
        gateway=FakeGateway(),
        settings=settings(tmp_path, stale_minutes=15),
    ).reset_stale_jobs(session)  # type: ignore[arg-type]

    assert reset == 1
    assert session.committed is True
    assert job.status == "queued"
    assert job.worker_id is None
    assert job.started_at is None
    assert document.status == "queued"
