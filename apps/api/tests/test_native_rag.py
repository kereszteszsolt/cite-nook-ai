# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections.abc import Sequence
from typing import Any
from uuid import uuid4

import pytest

from app.persistence.models import Document, DocumentChunk
from app.rag.contracts import IndexDocument, SourceRetrievalError, TextSection
from app.rag.native.indexer import NativeDocumentIndexer
from app.rag.native.retriever import NativeSourceRetriever


class FakeEmbeddingProvider:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str | list[str]]] = []

    def embed(
        self, model: str, inputs: str | Sequence[str]
    ) -> list[list[float]]:
        values = inputs if isinstance(inputs, str) else list(inputs)
        self.calls.append((model, values))
        if isinstance(values, str):
            return [[0.1, 0.2, 0.3]]
        return [[float(len(value)), 0.5, 1.0] for value in values]


class IndexSession:
    def __init__(self) -> None:
        self.statements: list[Any] = []
        self.added: list[DocumentChunk] = []
        self.events: list[str] = []

    def execute(self, statement: Any) -> None:
        self.events.append("delete")
        self.statements.append(statement)

    def add_all(self, objects: list[DocumentChunk]) -> None:
        self.events.append("add")
        self.added.extend(objects)


class FakeRows:
    def __init__(self, rows: list[tuple[DocumentChunk, Document, float]]) -> None:
        self._rows = rows

    def all(self) -> list[tuple[DocumentChunk, Document, float]]:
        return self._rows


class RetrievalSession:
    def __init__(self, rows: list[tuple[DocumentChunk, Document, float]]) -> None:
        self.rows = rows
        self.statement: Any | None = None

    def execute(self, statement: Any) -> FakeRows:
        self.statement = statement
        return FakeRows(self.rows)


def existing_native_row(
    name: str,
    ordinal: int,
    distance: float,
) -> tuple[DocumentChunk, Document, float]:
    document_id = uuid4()
    document = Document(
        id=document_id,
        file_name=name,
        content_type="text/plain",
        file_path=f"/uploads/{document_id}/{name}",
        size_bytes=100,
        sha256="0" * 64,
        status="ready",
        chunk_count=1,
        is_active=True,
        embedding_model="embed-a",
    )
    chunk = DocumentChunk(
        id=uuid4(),
        document_id=document_id,
        ordinal=ordinal,
        page_number=ordinal + 1,
        content=f"Grounded passage from {name}.",
        embedding_model="embed-a",
        embedding=[0.1, 0.2, 0.3],
    )
    return chunk, document, distance


def test_native_indexer_keeps_chunk_batches_and_release_04_rows() -> None:
    provider = FakeEmbeddingProvider()
    session = IndexSession()
    document_id = uuid4()
    indexer = NativeDocumentIndexer(
        embedding_provider=provider,
        embedding_batch_size=2,
    )
    sections = [
        TextSection(
            " ".join(f"sentence-{index}." for index in range(600)),
            page_number=3,
        )
    ]

    count = indexer.replace_document(
        session,  # type: ignore[arg-type]
        IndexDocument(document_id, "notes.pdf", "embed-a"),
        sections,
    )

    assert count == len(session.added)
    assert count > 2
    assert session.events == ["delete", "add"]
    assert "DELETE FROM document_chunks" in str(session.statements[0])
    batches = [inputs for _, inputs in provider.calls]
    assert all(isinstance(batch, list) and len(batch) <= 2 for batch in batches)
    assert sum(len(batch) for batch in batches if isinstance(batch, list)) == count
    assert [chunk.ordinal for chunk in session.added] == list(range(count))
    assert all(chunk.document_id == document_id for chunk in session.added)
    assert all(chunk.page_number == 3 for chunk in session.added)
    assert all(chunk.embedding_model == "embed-a" for chunk in session.added)
    assert all(len(chunk.embedding) == 3 for chunk in session.added)


def test_native_indexer_deletes_selected_document_rows_without_committing() -> None:
    session = IndexSession()
    document_id = uuid4()
    indexer = NativeDocumentIndexer(
        embedding_provider=FakeEmbeddingProvider(),
        embedding_batch_size=2,
    )

    indexer.delete_document(session, document_id)  # type: ignore[arg-type]

    statement = session.statements[0]
    assert "DELETE FROM document_chunks" in str(statement)
    assert document_id in statement.compile().params.values()
    assert session.added == []


def test_native_retriever_keeps_filters_order_scores_and_source_ids() -> None:
    provider = FakeEmbeddingProvider()
    session = RetrievalSession(
        [
            existing_native_row("first.txt", 0, 0.1),
            existing_native_row("second.pdf", 1, 0.2),
        ]
    )
    retriever = NativeSourceRetriever(embedding_provider=provider)

    sources = retriever.retrieve(
        session,  # type: ignore[arg-type]
        question="What is supported?",
        embedding_model="embed-a",
        top_k=2,
    )

    assert provider.calls == [("embed-a", "What is supported?")]
    assert [source.source_id for source in sources] == ["S1", "S2"]
    assert [source.document_name for source in sources] == ["first.txt", "second.pdf"]
    assert [source.page_number for source in sources] == [1, 2]
    assert [source.score for source in sources] == [0.9, 0.8]
    assert session.statement is not None
    sql = str(session.statement)
    assert "documents.status" in sql
    assert "documents.is_active IS true" in sql
    assert "documents.embedding_model" in sql
    assert "document_chunks.embedding_model" in sql
    assert "<=>" in sql
    parameters = session.statement.compile().params.values()
    assert "ready" in parameters
    assert list(parameters).count("embed-a") == 2
    assert 2 in parameters


class MultipleQueryEmbeddings(FakeEmbeddingProvider):
    def embed(
        self, model: str, inputs: str | Sequence[str]
    ) -> list[list[float]]:
        return [[0.1], [0.2]]


def test_native_retriever_rejects_multiple_query_embeddings() -> None:
    retriever = NativeSourceRetriever(embedding_provider=MultipleQueryEmbeddings())

    with pytest.raises(SourceRetrievalError, match="unexpected number of vectors"):
        retriever.retrieve(
            RetrievalSession([]),  # type: ignore[arg-type]
            question="Question",
            embedding_model="embed-a",
            top_k=2,
        )
