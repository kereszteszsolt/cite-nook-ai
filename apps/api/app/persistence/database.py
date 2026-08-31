# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from ..core.settings import get_settings


class Base(DeclarativeBase):
    pass


engine = create_engine(get_settings().database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, class_=Session)
RAG_BACKEND_METADATA_KEY = "rag_backend"


def init_database(rag_backend: str) -> None:
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
        claim_database_backend(connection, rag_backend)


def claim_database_backend(connection: Connection, selected_backend: str) -> None:
    if selected_backend not in {"native", "llamaindex"}:
        raise RuntimeError("RAG_BACKEND must be native or llamaindex.")
    marker = connection.scalar(
        text("SELECT value FROM app_metadata WHERE key = :key"),
        {"key": RAG_BACKEND_METADATA_KEY},
    )
    if marker is None:
        has_native_chunks = bool(
            connection.scalar(
                text("SELECT EXISTS (SELECT 1 FROM document_chunks LIMIT 1)")
            )
        )
        if selected_backend == "llamaindex" and has_native_chunks:
            raise RuntimeError(
                "This database contains native index data; select native or use separate data."
            )
        connection.execute(
            text(
                "INSERT INTO app_metadata (key, value) VALUES (:key, :value) "
                "ON CONFLICT (key) DO NOTHING"
            ),
            {"key": RAG_BACKEND_METADATA_KEY, "value": selected_backend},
        )
        marker = connection.scalar(
            text("SELECT value FROM app_metadata WHERE key = :key"),
            {"key": RAG_BACKEND_METADATA_KEY},
        )
    if marker != selected_backend:
        raise RuntimeError(
            f"This database belongs to the {marker} RAG backend; "
            f"the selected backend is {selected_backend}."
        )


def get_session() -> Generator[Session]:
    with SessionLocal() as session:
        yield session
