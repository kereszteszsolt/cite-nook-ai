# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text

from app.persistence import models as persistence_models
from app.persistence.database import Base, claim_database_backend

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")


class BackendConnection:
    def __init__(self, scalar_values: list[Any]) -> None:
        self.scalar_values = scalar_values
        self.scalar_calls: list[tuple[Any, Any]] = []
        self.execute_calls: list[tuple[Any, Any]] = []

    def scalar(self, statement: Any, parameters: Any = None) -> Any:
        self.scalar_calls.append((statement, parameters))
        return self.scalar_values.pop(0)

    def execute(self, statement: Any, parameters: Any = None) -> None:
        self.execute_calls.append((statement, parameters))


@pytest.mark.parametrize("backend", ["native", "llamaindex"])
def test_empty_database_claims_the_selected_backend(backend: str) -> None:
    connection = BackendConnection([None, False, backend])

    claim_database_backend(connection, backend)  # type: ignore[arg-type]

    assert len(connection.execute_calls) == 1
    assert connection.execute_calls[0][1] == {
        "key": "rag_backend",
        "value": backend,
    }


def test_release_04_native_chunks_adopt_native() -> None:
    connection = BackendConnection([None, True, "native"])

    claim_database_backend(connection, "native")  # type: ignore[arg-type]

    assert len(connection.execute_calls) == 1


def test_release_04_native_chunks_reject_llamaindex() -> None:
    connection = BackendConnection([None, True])

    with pytest.raises(RuntimeError, match="contains native index data"):
        claim_database_backend(connection, "llamaindex")  # type: ignore[arg-type]

    assert connection.execute_calls == []


def test_existing_marker_rejects_a_different_backend() -> None:
    connection = BackendConnection(["native"])

    with pytest.raises(
        RuntimeError,
        match="belongs to the native RAG backend; the selected backend is llamaindex",
    ):
        claim_database_backend(connection, "llamaindex")  # type: ignore[arg-type]

    assert connection.execute_calls == []


def test_existing_marker_accepts_the_same_backend() -> None:
    connection = BackendConnection(["llamaindex"])

    claim_database_backend(connection, "llamaindex")  # type: ignore[arg-type]

    assert connection.execute_calls == []


@pytest.mark.skipif(
    TEST_DATABASE_URL is None,
    reason="TEST_DATABASE_URL is required for PostgreSQL integration.",
)
def test_postgres_marker_adopts_native_and_stops_mismatches() -> None:
    assert TEST_DATABASE_URL is not None
    assert persistence_models.AppMetadata.__tablename__ == "app_metadata"
    engine = create_engine(TEST_DATABASE_URL)
    connection = engine.connect()
    transaction = connection.begin()
    try:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        Base.metadata.create_all(connection)
        connection.execute(text("DELETE FROM app_metadata WHERE key = 'rag_backend'"))
        connection.execute(text("DELETE FROM document_chunks"))

        claim_database_backend(connection, "llamaindex")
        assert connection.scalar(
            text("SELECT value FROM app_metadata WHERE key = 'rag_backend'")
        ) == "llamaindex"
        with pytest.raises(RuntimeError, match="belongs to the llamaindex"):
            claim_database_backend(connection, "native")

        connection.execute(text("DELETE FROM app_metadata WHERE key = 'rag_backend'"))
        document_id = uuid4()
        connection.execute(
            text(
                "INSERT INTO documents ("
                "id, file_name, content_type, file_path, size_bytes, sha256, status, "
                "chunk_count, is_active, embedding_model, created_at, updated_at"
                ") VALUES ("
                ":id, 'legacy.txt', 'text/plain', '/tmp/legacy.txt', 6, :sha256, "
                "'ready', 1, TRUE, 'embed-a', now(), now()"
                ")"
            ),
            {"id": document_id, "sha256": "0" * 64},
        )
        connection.execute(
            text(
                "INSERT INTO document_chunks ("
                "id, document_id, ordinal, content, embedding_model, embedding, created_at"
                ") VALUES ("
                ":id, :document_id, 0, 'Legacy source', 'embed-a', "
                "CAST('[1,0,0]' AS vector), now()"
                ")"
            ),
            {"id": uuid4(), "document_id": document_id},
        )

        with pytest.raises(RuntimeError, match="contains native index data"):
            claim_database_backend(connection, "llamaindex")
        claim_database_backend(connection, "native")
        assert connection.scalar(
            text("SELECT value FROM app_metadata WHERE key = 'rag_backend'")
        ) == "native"
    finally:
        transaction.rollback()
        connection.close()
        engine.dispose()
