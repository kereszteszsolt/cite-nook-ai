# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import socket
from datetime import timedelta
from pathlib import Path
from uuid import UUID

from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

from ..ai.contracts import EmbeddingProvider
from ..core.settings import Settings
from ..persistence.models import DocumentChunk, IngestionJob, utc_now
from ..rag.native.chunking import chunk_sections
from .extraction import extract_sections

MAX_INGESTION_ERROR_LENGTH = 2000


class IngestionService:
    def __init__(
        self,
        *,
        embedding_provider: EmbeddingProvider,
        settings: Settings,
        worker_id: str | None = None,
    ) -> None:
        self._embedding_provider = embedding_provider
        self._settings = settings
        self.worker_id = worker_id or socket.gethostname()

    def reset_stale_jobs(self, session: Session) -> int:
        threshold = utc_now() - timedelta(minutes=self._settings.ingestion_stale_minutes)
        jobs = session.scalars(
            select(IngestionJob).where(
                IngestionJob.status == "processing",
                IngestionJob.started_at.is_not(None),
                IngestionJob.started_at < threshold,
            )
        ).all()
        for job in jobs:
            job.status = "queued"
            job.worker_id = None
            job.started_at = None
            job.finished_at = None
            job.error_message = None
            job.document.status = "queued"
            job.document.error_message = None
        session.commit()
        return len(jobs)

    def claim_next_job(self, session: Session) -> UUID | None:
        row = session.execute(
            text(
                """
                WITH next_job AS (
                    SELECT id
                    FROM ingestion_jobs
                    WHERE status = 'queued'
                    ORDER BY created_at, id
                    FOR UPDATE SKIP LOCKED
                    LIMIT 1
                )
                UPDATE ingestion_jobs AS job
                SET status = 'processing',
                    attempts = attempts + 1,
                    worker_id = :worker_id,
                    started_at = NOW(),
                    finished_at = NULL,
                    error_message = NULL
                FROM next_job
                WHERE job.id = next_job.id
                RETURNING job.id
                """
            ),
            {"worker_id": self.worker_id},
        ).first()
        session.commit()
        return row[0] if row else None

    def process_job(self, session: Session, job_id: UUID) -> bool:
        job = session.get(IngestionJob, job_id)
        if job is None or job.status != "processing":
            return False

        document = job.document
        document.status = "processing"
        document.error_message = None
        session.commit()

        try:
            chunks = chunk_sections(extract_sections(Path(document.file_path)))
            if not chunks:
                raise ValueError("No readable text was found in the document.")

            embeddings: list[list[float]] = []
            batch_size = self._settings.embedding_batch_size
            for start in range(0, len(chunks), batch_size):
                batch = chunks[start : start + batch_size]
                embeddings.extend(
                    self._embedding_provider.embed(
                        document.embedding_model,
                        [chunk.content for chunk in batch],
                    )
                )
            _validate_embeddings(embeddings, len(chunks))

            session.execute(
                delete(DocumentChunk).where(DocumentChunk.document_id == document.id)
            )
            session.add_all(
                [
                    DocumentChunk(
                        document_id=document.id,
                        ordinal=chunk.ordinal,
                        page_number=chunk.page_number,
                        content=chunk.content,
                        embedding_model=document.embedding_model,
                        embedding=embedding,
                    )
                    for chunk, embedding in zip(chunks, embeddings, strict=True)
                ]
            )
            document.status = "ready"
            document.chunk_count = len(chunks)
            document.error_message = None
            job.status = "completed"
            job.error_message = None
            job.finished_at = utc_now()
            session.commit()
            return True
        except Exception as error:
            session.rollback()
            failed_job = session.get(IngestionJob, job_id)
            if failed_job is None:
                raise
            message = _bounded_error(error)
            failed_job.status = "failed"
            failed_job.error_message = message
            failed_job.finished_at = utc_now()
            failed_job.document.status = "failed"
            failed_job.document.error_message = message
            session.commit()
            return False


def _validate_embeddings(embeddings: list[list[float]], expected_count: int) -> None:
    if len(embeddings) != expected_count:
        raise RuntimeError("The embedding model returned an unexpected number of vectors.")
    dimensions = {len(embedding) for embedding in embeddings}
    if not dimensions or 0 in dimensions or len(dimensions) != 1:
        raise RuntimeError("The embedding model returned inconsistent vector dimensions.")


def _bounded_error(error: Exception) -> str:
    message = " ".join(str(error).split()) or type(error).__name__
    return message[:MAX_INGESTION_ERROR_LENGTH]
