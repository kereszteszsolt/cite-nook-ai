# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import socket
from datetime import timedelta
from pathlib import Path
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from ..core.settings import Settings
from ..persistence.models import IngestionJob, utc_now
from ..rag.contracts import DocumentIndexer, IndexDocument
from .extraction import extract_sections

MAX_INGESTION_ERROR_LENGTH = 2000


class IngestionService:
    def __init__(
        self,
        *,
        indexer: DocumentIndexer,
        settings: Settings,
        worker_id: str | None = None,
    ) -> None:
        self._indexer = indexer
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
            chunk_count = self._indexer.replace_document(
                session,
                IndexDocument(
                    document_id=document.id,
                    document_name=document.file_name,
                    embedding_model=document.embedding_model,
                ),
                extract_sections(Path(document.file_path)),
            )
            document.status = "ready"
            document.chunk_count = chunk_count
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


def _bounded_error(error: Exception) -> str:
    message = " ".join(str(error).split()) or type(error).__name__
    return message[:MAX_INGESTION_ERROR_LENGTH]
