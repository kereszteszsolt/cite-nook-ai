# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import logging
import signal
import threading
from time import monotonic

from .database import SessionLocal, init_database
from .services.ingestion import IngestionService

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("citenook-worker")
stop_event = threading.Event()
WORKER_POLL_SECONDS = 2.0
STALE_CHECK_SECONDS = 60.0


def _stop(*_: object) -> None:
    stop_event.set()


def main() -> None:
    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)
    init_database()
    service = IngestionService()
    next_stale_check = 0.0

    logger.info("CiteNook ingestion worker started.")
    while not stop_event.is_set():
        try:
            if monotonic() >= next_stale_check:
                with SessionLocal() as session:
                    reset_count = service.reset_stale_jobs(session)
                if reset_count:
                    logger.info("Requeued %s stale ingestion job(s).", reset_count)
                next_stale_check = monotonic() + STALE_CHECK_SECONDS

            with SessionLocal() as session:
                job_id = service.claim_next_job(session)
            if job_id is None:
                stop_event.wait(WORKER_POLL_SECONDS)
                continue

            logger.info("Processing ingestion job %s.", job_id)
            with SessionLocal() as session:
                completed = service.process_job(session, job_id)
            if completed:
                logger.info("Completed ingestion job %s.", job_id)
            else:
                logger.warning("Ingestion job %s failed.", job_id)
        except Exception:
            logger.exception("Worker loop failed; retrying shortly.")
            stop_event.wait(WORKER_POLL_SECONDS)

    logger.info("CiteNook ingestion worker stopped.")


if __name__ == "__main__":
    main()
