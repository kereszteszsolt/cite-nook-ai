# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
from collections.abc import Sequence
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

import pytest
from sqlalchemy import create_engine, delete, text
from sqlalchemy.orm import Session

from app.persistence.database import Base
from app.persistence.models import Document
from app.rag.contracts import IndexDocument, TextSection
from app.rag.llamaindex.indexer import LlamaIndexDocumentIndexer
from app.rag.llamaindex.retriever import LlamaIndexSourceRetriever
from app.rag.llamaindex.store import (
    LLAMAINDEX_SCHEMA,
    PostgresNodeStoreFactory,
    table_name,
)

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


def test_postgres_retrieval_filters_common_document_state_and_orders_ties() -> None:
    assert TEST_DATABASE_URL is not None
    engine = create_engine(TEST_DATABASE_URL)
    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        Base.metadata.create_all(connection)

    valid = Document(
        id=uuid4(),
        file_name="valid.txt",
        content_type="text/plain",
        file_path="/tmp/valid.txt",
        size_bytes=64,
        sha256="1" * 64,
        status="ready",
        chunk_count=2,
        is_active=True,
        embedding_model="embed-retrieval",
    )
    inactive = Document(
        id=uuid4(),
        file_name="inactive.txt",
        content_type="text/plain",
        file_path="/tmp/inactive.txt",
        size_bytes=64,
        sha256="2" * 64,
        status="ready",
        chunk_count=1,
        is_active=False,
        embedding_model="embed-retrieval",
    )
    failed = Document(
        id=uuid4(),
        file_name="failed.txt",
        content_type="text/plain",
        file_path="/tmp/failed.txt",
        size_bytes=64,
        sha256="3" * 64,
        status="failed",
        chunk_count=1,
        is_active=True,
        embedding_model="embed-retrieval",
    )
    mismatched = Document(
        id=uuid4(),
        file_name="mismatched.txt",
        content_type="text/plain",
        file_path="/tmp/mismatched.txt",
        size_bytes=64,
        sha256="4" * 64,
        status="ready",
        chunk_count=1,
        is_active=True,
        embedding_model="other-model",
    )
    missing_document_id = uuid4()
    indexed_document_ids = [
        valid.id,
        inactive.id,
        failed.id,
        mismatched.id,
        missing_document_id,
    ]
    provider = FakeEmbeddingProvider()
    indexer = LlamaIndexDocumentIndexer(
        embedding_provider=provider,
        embedding_batch_size=2,
        database_url=TEST_DATABASE_URL,
        splitter=PipeSplitter(),
    )
    retriever = LlamaIndexSourceRetriever(
        embedding_provider=provider,
        database_url=TEST_DATABASE_URL,
    )
    stores = PostgresNodeStoreFactory(TEST_DATABASE_URL)

    try:
        with Session(engine) as session:
            session.add_all([valid, inactive, failed, mismatched])
            session.commit()
            indexer.replace_document(
                session,
                IndexDocument(valid.id, valid.file_name, "embed-retrieval"),
                [TextSection("Alpha | Bravo", page_number=2)],
            )
            for document in [inactive, failed, mismatched]:
                indexer.replace_document(
                    session,
                    IndexDocument(
                        document.id,
                        document.file_name,
                        "embed-retrieval",
                    ),
                    [TextSection(f"Hidden {document.file_name}", page_number=3)],
                )
            indexer.replace_document(
                session,
                IndexDocument(
                    missing_document_id,
                    "missing.txt",
                    "embed-retrieval",
                ),
                [TextSection("Missing document row", page_number=4)],
            )

            sources = retriever.retrieve(
                session,
                question="Which passages are valid?",
                embedding_model="embed-retrieval",
                top_k=10,
            )

            assert [source.document_id for source in sources] == [valid.id, valid.id]
            assert [source.document_name for source in sources] == [
                "valid.txt",
                "valid.txt",
            ]
            assert [source.page_number for source in sources] == [2, 2]
            assert [source.source_id for source in sources] == ["S1", "S2"]
            assert [source.chunk_id for source in sources] == [
                uuid5(NAMESPACE_URL, f"citenook:{valid.id}:0"),
                uuid5(NAMESPACE_URL, f"citenook:{valid.id}:1"),
            ]
            assert all(source.score == sources[0].score for source in sources)
    finally:
        with Session(engine) as cleanup_session:
            for store in stores.existing_stores(
                cleanup_session,
                "embed-retrieval",
            ):
                for document_id in indexed_document_ids:
                    store.delete(str(document_id))
            cleanup_session.execute(
                delete(Document).where(
                    Document.id.in_([valid.id, inactive.id, failed.id, mismatched.id])
                )
            )
            cleanup_session.commit()
        engine.dispose()
