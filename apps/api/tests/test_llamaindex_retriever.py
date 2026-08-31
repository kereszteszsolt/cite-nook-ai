# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections.abc import Sequence
from typing import Any
from uuid import UUID, uuid4

import pytest
from llama_index.core.schema import NodeWithScore, QueryBundle, TextNode

from app.rag.contracts import SourceRetrievalError
from app.rag.llamaindex.retriever import LlamaIndexSourceRetriever


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
        return [[0.2, 0.4, 0.8]]


class ScalarRows:
    def __init__(self, values: list[UUID]) -> None:
        self._values = values

    def all(self) -> list[UUID]:
        return self._values


class RetrievalSession:
    def __init__(self, document_ids: list[UUID]) -> None:
        self.document_ids = document_ids
        self.statement: Any | None = None

    def scalars(self, statement: Any) -> ScalarRows:
        self.statement = statement
        return ScalarRows(self.document_ids)


class FakeStoreFactory:
    def __init__(self, store: Any = None) -> None:
        self.store = store
        self.calls: list[tuple[Any, str, int]] = []

    def read_store(
        self,
        session: Any,
        embedding_model: str,
        dimension: int,
    ) -> Any:
        self.calls.append((session, embedding_model, dimension))
        return self.store


class FakeNodeRetriever:
    def __init__(self, nodes: list[NodeWithScore]) -> None:
        self.nodes = nodes
        self.queries: list[QueryBundle] = []

    def retrieve(self, query: QueryBundle) -> list[NodeWithScore]:
        self.queries.append(query)
        return self.nodes


class CapturingRetrieverBuilder:
    def __init__(self, retriever: FakeNodeRetriever) -> None:
        self.retriever = retriever
        self.calls: list[tuple[Any, Any, int, Any]] = []

    def __call__(self, store: Any, embedder: Any, top_k: int, filters: Any) -> Any:
        self.calls.append((store, embedder, top_k, filters))
        return self.retriever


def scored_node(
    *,
    document_id: UUID,
    node_id: UUID,
    ordinal: int,
    score: float,
    name: str,
    page_number: int | None,
) -> NodeWithScore:
    return NodeWithScore(
        node=TextNode(
            id_=str(node_id),
            text=f"Grounded passage from {name}.",
            metadata={
                "document_id": str(document_id),
                "document_name": name,
                "page_number": page_number,
                "ordinal": ordinal,
                "embedding_model": "embed-a",
                "node_id": str(node_id),
            },
        ),
        score=score,
    )


def test_retriever_filters_maps_and_orders_equal_scores_before_source_ids() -> None:
    first_document_id = uuid4()
    second_document_id = uuid4()
    first_node_id = uuid4()
    second_node_id = uuid4()
    node_retriever = FakeNodeRetriever(
        [
            scored_node(
                document_id=second_document_id,
                node_id=second_node_id,
                ordinal=2,
                score=0.75,
                name="second.pdf",
                page_number=4,
            ),
            scored_node(
                document_id=first_document_id,
                node_id=first_node_id,
                ordinal=1,
                score=0.75,
                name="first.txt",
                page_number=None,
            ),
        ]
    )
    builder = CapturingRetrieverBuilder(node_retriever)
    store = object()
    stores = FakeStoreFactory(store)
    provider = FakeEmbeddingProvider()
    session = RetrievalSession([first_document_id, second_document_id])
    retriever = LlamaIndexSourceRetriever(
        embedding_provider=provider,
        store_factory=stores,  # type: ignore[arg-type]
        retriever_builder=builder,  # type: ignore[arg-type]
    )

    sources = retriever.retrieve(
        session,  # type: ignore[arg-type]
        question="What is supported?",
        embedding_model="embed-a",
        top_k=2,
    )

    assert provider.calls == [("embed-a", "What is supported?")]
    assert stores.calls == [(session, "embed-a", 3)]
    assert len(builder.calls) == 1
    assert builder.calls[0][0] is store
    assert builder.calls[0][1].model_name == "embed-a"
    assert builder.calls[0][2] == 2
    filters = builder.calls[0][3]
    assert filters.condition.value == "and"
    assert filters.filters[0].key == "document_id"
    assert filters.filters[0].operator.value == "in"
    assert filters.filters[0].value == [
        str(first_document_id),
        str(second_document_id),
    ]
    assert filters.filters[1].key == "embedding_model"
    assert filters.filters[1].value == "embed-a"
    assert node_retriever.queries[0].query_str == "What is supported?"
    assert node_retriever.queries[0].embedding == [0.2, 0.4, 0.8]
    assert [source.source_id for source in sources] == ["S1", "S2"]
    assert [source.chunk_id for source in sources] == [first_node_id, second_node_id]
    assert [source.document_name for source in sources] == ["first.txt", "second.pdf"]
    assert [source.page_number for source in sources] == [None, 4]
    assert [source.score for source in sources] == [0.75, 0.75]
    assert sources[0].snippet == "Grounded passage from first.txt."
    assert session.statement is not None
    sql = str(session.statement)
    assert "documents.status" in sql
    assert "documents.is_active IS true" in sql
    assert "documents.embedding_model" in sql
    parameters = session.statement.compile().params.values()
    assert "ready" in parameters
    assert "embed-a" in parameters


def test_retriever_returns_empty_before_embedding_when_no_document_is_eligible() -> None:
    provider = FakeEmbeddingProvider()
    stores = FakeStoreFactory(object())
    builder = CapturingRetrieverBuilder(FakeNodeRetriever([]))
    retriever = LlamaIndexSourceRetriever(
        embedding_provider=provider,
        store_factory=stores,  # type: ignore[arg-type]
        retriever_builder=builder,  # type: ignore[arg-type]
    )

    sources = retriever.retrieve(
        RetrievalSession([]),  # type: ignore[arg-type]
        question="Unknown topic?",
        embedding_model="embed-a",
        top_k=3,
    )

    assert sources == []
    assert provider.calls == []
    assert stores.calls == []
    assert builder.calls == []


def test_retriever_returns_empty_when_the_model_store_is_missing() -> None:
    document_id = uuid4()
    provider = FakeEmbeddingProvider()
    stores = FakeStoreFactory()
    builder = CapturingRetrieverBuilder(FakeNodeRetriever([]))
    session = RetrievalSession([document_id])
    retriever = LlamaIndexSourceRetriever(
        embedding_provider=provider,
        store_factory=stores,  # type: ignore[arg-type]
        retriever_builder=builder,  # type: ignore[arg-type]
    )

    sources = retriever.retrieve(
        session,  # type: ignore[arg-type]
        question="Question",
        embedding_model="embed-a",
        top_k=2,
    )

    assert sources == []
    assert provider.calls == [("embed-a", "Question")]
    assert stores.calls == [(session, "embed-a", 3)]
    assert builder.calls == []


@pytest.mark.parametrize("case", ["missing", "mismatched", "ineligible"])
def test_retriever_rejects_missing_mismatched_or_ineligible_node_data(
    case: str,
) -> None:
    eligible_document_id = uuid4()
    document_id = uuid4() if case == "ineligible" else eligible_document_id
    node_id = uuid4()
    metadata = {
        "document_id": str(document_id),
        "document_name": "guide.pdf",
        "page_number": 1,
        "ordinal": 0,
        "embedding_model": "embed-b" if case == "mismatched" else "embed-a",
        "node_id": str(node_id),
    }
    if case == "missing":
        metadata.pop("node_id")
    invalid_node = TextNode(
        id_=str(node_id),
        text="Passage",
        metadata=metadata,
    )
    builder = CapturingRetrieverBuilder(
        FakeNodeRetriever([NodeWithScore(node=invalid_node, score=0.8)])
    )
    retriever = LlamaIndexSourceRetriever(
        embedding_provider=FakeEmbeddingProvider(),
        store_factory=FakeStoreFactory(object()),  # type: ignore[arg-type]
        retriever_builder=builder,  # type: ignore[arg-type]
    )

    with pytest.raises(SourceRetrievalError, match="invalid source data"):
        retriever.retrieve(
            RetrievalSession([eligible_document_id]),  # type: ignore[arg-type]
            question="Question",
            embedding_model="embed-a",
            top_k=2,
        )
