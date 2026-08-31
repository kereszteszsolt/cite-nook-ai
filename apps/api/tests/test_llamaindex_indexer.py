# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections.abc import Sequence
from typing import Any
from uuid import UUID, uuid4

import pytest
from llama_index.core.schema import BaseNode

from app.persistence.models import Document
from app.rag.contracts import IndexDocument, TextSection
from app.rag.llamaindex.embedding import CiteNookEmbedding
from app.rag.llamaindex.indexer import LlamaIndexDocumentIndexer, build_nodes
from app.rag.llamaindex.store import (
    LLAMAINDEX_SCHEMA,
    PostgresNodeStoreFactory,
    table_name,
    table_prefix,
)


class FakeEmbeddingProvider:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str | list[str]]] = []

    def embed(
        self,
        model: str,
        inputs: str | Sequence[str],
    ) -> list[list[float]]:
        values = inputs if isinstance(inputs, str) else list(inputs)
        self.calls.append((model, values))
        count = 1 if isinstance(values, str) else len(values)
        return [[float(index + 1), 0.5, 1.0] for index in range(count)]


class PipeSplitter:
    def split_text(self, text: str) -> list[str]:
        return [value.strip() for value in text.split("|") if value.strip()]


class FakeStore:
    def __init__(
        self,
        name: str,
        events: list[str],
        *,
        add_error: Exception | None = None,
    ) -> None:
        self.name = name
        self.events = events
        self.add_error = add_error
        self.added: list[BaseNode] = []
        self.deleted: list[str] = []

    def add(self, nodes: list[BaseNode]) -> list[str]:
        self.events.append(f"add:{self.name}")
        self.added = nodes
        if self.add_error is not None:
            raise self.add_error
        return [node.node_id for node in nodes]

    def delete(self, ref_doc_id: str) -> None:
        self.events.append(f"delete:{self.name}")
        self.deleted.append(ref_doc_id)


class FakeStoreFactory:
    def __init__(
        self,
        *,
        existing: list[FakeStore] | None = None,
        write_store: FakeStore | None = None,
    ) -> None:
        self.events: list[str] = []
        self.existing = existing or []
        self.created = write_store or FakeStore("new", self.events)
        self.write_calls: list[tuple[str, int]] = []
        self.existing_calls: list[str] = []

    def write_store(self, embedding_model: str, dimension: int) -> FakeStore:
        self.events.append("write-store")
        self.write_calls.append((embedding_model, dimension))
        return self.created

    def existing_stores(self, session: Any, embedding_model: str) -> list[FakeStore]:
        self.events.append("existing-stores")
        self.existing_calls.append(embedding_model)
        return self.existing


class DocumentSession:
    def __init__(self, document: Document | None = None) -> None:
        self.document = document

    def get(self, model: type[Any], document_id: UUID) -> Document | None:
        assert model is Document
        if self.document is None or self.document.id != document_id:
            return None
        return self.document


def index_document(document_id: UUID | None = None) -> IndexDocument:
    return IndexDocument(
        document_id=document_id or uuid4(),
        document_name="guide.pdf",
        embedding_model="embed-a",
    )


def test_build_nodes_keeps_page_metadata_order_and_stable_uuid() -> None:
    document = index_document()
    sections = [
        TextSection("First page A | First page B", page_number=1),
        TextSection("Second page", page_number=2),
    ]

    first = build_nodes(document, sections, PipeSplitter())
    second = build_nodes(document, sections, PipeSplitter())

    assert [node.node_id for node in first] == [node.node_id for node in second]
    assert len(set(node.node_id for node in first)) == 3
    assert all(UUID(node.node_id) for node in first)
    assert [node.text for node in first] == [
        "First page A",
        "First page B",
        "Second page",
    ]
    assert [node.metadata["page_number"] for node in first] == [1, 1, 2]
    assert [node.metadata["ordinal"] for node in first] == [0, 1, 2]
    assert all(node.ref_doc_id == str(document.document_id) for node in first)
    for node in first:
        assert node.metadata == {
            "document_id": str(document.document_id),
            "document_name": "guide.pdf",
            "page_number": node.metadata["page_number"],
            "ordinal": node.metadata["ordinal"],
            "embedding_model": "embed-a",
            "node_id": node.node_id,
        }
        assert set(node.excluded_embed_metadata_keys) == set(node.metadata)
        assert set(node.excluded_llm_metadata_keys) == set(node.metadata)


def test_embedding_bridge_uses_configured_provider_model_and_batches() -> None:
    provider = FakeEmbeddingProvider()
    embedding = CiteNookEmbedding(
        provider=provider,
        model_name="embed-a",
        batch_size=2,
    )

    vectors = embedding.get_text_embedding_batch(["one", "two", "three"])

    assert vectors == [[1.0, 0.5, 1.0], [2.0, 0.5, 1.0], [1.0, 0.5, 1.0]]
    assert provider.calls == [
        ("embed-a", ["one", "two"]),
        ("embed-a", ["three"]),
    ]


def test_replace_deletes_old_nodes_then_stores_embedded_nodes() -> None:
    provider = FakeEmbeddingProvider()
    events: list[str] = []
    old_store = FakeStore("old", events)
    new_store = FakeStore("new", events)
    stores = FakeStoreFactory(existing=[old_store], write_store=new_store)
    stores.events = events
    document = index_document()
    indexer = LlamaIndexDocumentIndexer(
        embedding_provider=provider,
        embedding_batch_size=2,
        store_factory=stores,
        splitter=PipeSplitter(),
    )

    count = indexer.replace_document(
        DocumentSession(),  # type: ignore[arg-type]
        document,
        [TextSection("Alpha | Beta", page_number=4)],
    )

    assert count == 2
    assert events == [
        "existing-stores",
        "delete:old",
        "write-store",
        "add:new",
    ]
    assert stores.existing_calls == ["embed-a"]
    assert stores.write_calls == [("embed-a", 3)]
    assert old_store.deleted == [str(document.document_id)]
    assert [node.embedding for node in new_store.added] == [
        [1.0, 0.5, 1.0],
        [2.0, 0.5, 1.0],
    ]


def test_storage_failure_removes_partial_nodes_and_stays_short() -> None:
    events: list[str] = []
    failed_store = FakeStore(
        "new",
        events,
        add_error=RuntimeError("database details that must not escape"),
    )
    stores = FakeStoreFactory(write_store=failed_store)
    stores.events = events
    document = index_document()
    indexer = LlamaIndexDocumentIndexer(
        embedding_provider=FakeEmbeddingProvider(),
        embedding_batch_size=2,
        store_factory=stores,
        splitter=PipeSplitter(),
    )

    with pytest.raises(RuntimeError, match=r"^LlamaIndex node storage failed\.$"):
        indexer.replace_document(
            DocumentSession(),  # type: ignore[arg-type]
            document,
            [TextSection("Alpha")],
        )

    assert events == [
        "existing-stores",
        "write-store",
        "add:new",
        "delete:new",
    ]
    assert failed_store.deleted == [str(document.document_id)]


def test_delete_is_repeatable_and_uses_the_document_embedding_model() -> None:
    events: list[str] = []
    first_store = FakeStore("first", events)
    second_store = FakeStore("second", events)
    stores = FakeStoreFactory(existing=[first_store, second_store])
    stores.events = events
    document = Document(
        id=uuid4(),
        file_name="guide.pdf",
        embedding_model="embed-a",
    )
    session = DocumentSession(document)
    indexer = LlamaIndexDocumentIndexer(
        embedding_provider=FakeEmbeddingProvider(),
        embedding_batch_size=2,
        store_factory=stores,
        splitter=PipeSplitter(),
    )

    indexer.delete_document(session, document.id)  # type: ignore[arg-type]
    indexer.delete_document(session, document.id)  # type: ignore[arg-type]

    assert stores.existing_calls == ["embed-a", "embed-a"]
    assert first_store.deleted == [str(document.id), str(document.id)]
    assert second_store.deleted == [str(document.id), str(document.id)]


class TableRows:
    def __init__(self, values: list[str]) -> None:
        self.values = values

    def all(self) -> list[str]:
        return self.values


class TableSession:
    def __init__(self, values: list[str]) -> None:
        self.values = values
        self.statement: Any | None = None
        self.parameters: dict[str, Any] = {}

    def scalars(self, statement: Any, parameters: dict[str, Any]) -> TableRows:
        self.statement = statement
        self.parameters = parameters
        return TableRows(self.values)


class CapturingPostgresFactory(PostgresNodeStoreFactory):
    def __init__(self) -> None:
        super().__init__("postgresql+psycopg://user:password@postgres.test/citenook")
        self.created: list[tuple[str, int, bool]] = []

    def _store(
        self,
        *,
        table_name: str,
        dimension: int,
        perform_setup: bool,
    ) -> FakeStore:
        self.created.append((table_name, dimension, perform_setup))
        return FakeStore(table_name, [])


def test_store_factory_discovers_only_model_and_dimension_tables() -> None:
    model_prefix = table_prefix("embed-a")
    values = [
        f"data_{model_prefix}3",
        f"data_{model_prefix}1024",
        f"data_{model_prefix}invalid",
        "data_unrelated_768",
    ]
    session = TableSession(values)
    factory = CapturingPostgresFactory()

    stores = factory.existing_stores(session, "embed-a")  # type: ignore[arg-type]

    assert len(stores) == 2
    assert factory.created == [
        (f"{model_prefix}3", 3, False),
        (f"{model_prefix}1024", 1024, False),
    ]
    assert session.parameters == {
        "schema_name": LLAMAINDEX_SCHEMA,
        "prefix": f"data_{model_prefix}",
        "prefix_length": len(f"data_{model_prefix}"),
    }


def test_table_name_is_stable_and_separates_models_and_dimensions() -> None:
    assert table_name("embed-a", 3) == table_name("embed-a", 3)
    assert table_name("embed-a", 3) != table_name("embed-a", 4)
    assert table_name("embed-a", 3) != table_name("embed-b", 3)
    assert table_name("embed-a", 3).startswith("citenook_nodes_")

    with pytest.raises(ValueError, match="dimension must be positive"):
        table_name("embed-a", 0)
