# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .settings import get_settings


class Base(DeclarativeBase):
    pass


engine = create_engine(get_settings().database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, class_=Session)


def init_database() -> None:
    from . import models  # noqa: F401

    get_settings().upload_dir.mkdir(parents=True, exist_ok=True)
    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        Base.metadata.create_all(bind=connection)
        connection.execute(
            text(
                "ALTER TABLE documents "
                "ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE conversation_messages "
                "ADD COLUMN IF NOT EXISTS response_duration_ms INTEGER"
            )
        )
        connection.execute(
            text(
                "DO $$ BEGIN "
                "IF NOT EXISTS ("
                "SELECT 1 FROM pg_constraint "
                "WHERE conname = 'ck_conversation_messages_response_duration'"
                ") THEN "
                "ALTER TABLE conversation_messages "
                "ADD CONSTRAINT ck_conversation_messages_response_duration "
                "CHECK (response_duration_ms IS NULL OR response_duration_ms >= 0); "
                "END IF; "
                "END $$"
            )
        )


def get_session() -> Generator[Session]:
    with SessionLocal() as session:
        yield session
