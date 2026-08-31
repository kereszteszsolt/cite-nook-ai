# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
from collections.abc import Sequence
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.persistence.database import Base
from app.persistence.models import Document
from app.rag.contracts import IndexDocument, TextSection
from app.rag.llamaindex.indexer import LlamaIndexDocumentIndexer
from app.rag.llamaindex.store import LLAMAINDEX_SCHEMA, table_name

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    TEST_DATABASE_URL is None,
    reason="TEST_DATABASE_URL is required for PostgreSQL integration.",
)


class FakeEmbeddingProvider:
    def embed(
        self,
        model: str,
        inputs: str | Sequence[str],
    ) -> list[list[float]]:
        values = [inputs] if isinstance(inputs, str) else list(inputs)
        return [[float(len(value)), 0.5, 1.0] for value in values]


class PipeSplitter:
    def split_text(self, value: str) -> list[str]:
        return [part.strip() for part in value.split("|") if part.strip()]


def test_postgres_store_persists_replaces_and_repeats_delete() -> None:
    assert TEST_DATABASE_URL is not None
    engine = create_engine(TEST_DATABASE_URL)
    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        Base.metadata.create_all(connection)

    document = Document(
        id=uuid4(),
        file_name="guide.pdf",
        content_type="application/pdf",
        file_path="/tmp/guide.pdf",
        size_bytes=128,
        sha256="0" * 64,
        status="processing",
        chunk_count=0,
        is_active=True,
        embedding_model="embed-a",
    )
    indexer = LlamaIndexDocumentIndexer(
        embedding_provider=FakeEmbeddingProvider(),
        embedding_batch_size=2,
        database_url=TEST_DATABASE_URL,
        splitter=PipeSplitter(),
    )
    collection = table_name("embed-a", 3)
    select_nodes = text(
        f'SELECT node_id, text, metadata_ FROM "{LLAMAINDEX_SCHEMA}".'
        f'"data_{collection}" ORDER BY node_id'
    )

    try:
        with Session(engine) as session:
            session.add(document)
            session.commit()
            first_count = indexer.replace_document(
                session,
                IndexDocument(document.id, document.file_name, document.embedding_model),
                [TextSection("First node | Second node", page_number=4)],
            )
            first_rows = session.execute(select_nodes).all()

            assert first_count == 2
            assert len(first_rows) == 2
            assert all(UUID(row.node_id) for row in first_rows)
            assert {row.text for row in first_rows} == {"First node", "Second node"}
            first_node_id = next(
                row.node_id for row in first_rows if row.metadata_["ordinal"] == 0
            )
            for row in first_rows:
                assert row.metadata_["document_id"] == str(document.id)
                assert row.metadata_["document_name"] == "guide.pdf"
                assert row.metadata_["page_number"] == 4
                assert row.metadata_["embedding_model"] == "embed-a"
                assert row.metadata_["node_id"] == row.node_id

            second_count = indexer.replace_document(
                session,
                IndexDocument(document.id, document.file_name, document.embedding_model),
                [TextSection("Replacement node", page_number=7)],
            )
            second_rows = session.execute(select_nodes).all()

            assert second_count == 1
            assert len(second_rows) == 1
            assert second_rows[0].node_id == first_node_id
            assert second_rows[0].text == "Replacement node"
            assert second_rows[0].metadata_["page_number"] == 7

            indexer.delete_document(session, document.id)
            indexer.delete_document(session, document.id)
            assert session.execute(select_nodes).all() == []
    finally:
        engine.dispose()
