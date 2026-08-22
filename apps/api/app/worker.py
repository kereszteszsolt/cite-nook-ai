# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import logging
import signal
import threading

from sqlalchemy import text

from .database import SessionLocal, init_database

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("citenook-worker")
stop_event = threading.Event()


def _stop(*_: object) -> None:
    stop_event.set()


def main() -> None:
    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)
    init_database()
    logger.info("CiteNook worker started; ingestion is introduced by MRA-004.")

    while not stop_event.wait(30.0):
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))

    logger.info("CiteNook worker stopped.")


if __name__ == "__main__":
    main()
