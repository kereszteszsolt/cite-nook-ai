# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from math import isfinite
from typing import Any
from uuid import UUID

from llama_index.core import VectorStoreIndex
from llama_index.core.base.base_retriever import BaseRetriever
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.schema import MetadataMode, NodeWithScore, QueryBundle
from llama_index.core.vector_stores.types import (
    BasePydanticVectorStore,
    FilterCondition,
    FilterOperator,
    MetadataFilter,
    MetadataFilters,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...ai.contracts import EmbeddingProvider
from ...persistence.models import Document
from ..contracts import RetrievedSource, SourceRetrievalError
from .embedding import CiteNookEmbedding
from .store import PostgresNodeStoreFactory, RetrievalStoreFactory

NodeRetrieverBuilder = Callable[
    [BasePydanticVectorStore, BaseEmbedding, int, MetadataFilters],
    BaseRetriever,
]


@dataclass(frozen=True, slots=True)
class _SourceCandidate:
    document_id: UUID
    document_name: str
    page_number: int | None
    chunk_id: UUID
    snippet: str
    score: float
    ordinal: int


class LlamaIndexSourceRetriever:
    def __init__(
        self,
        *,
        embedding_provider: EmbeddingProvider,
        database_url: str | None = None,
        store_factory: RetrievalStoreFactory | None = None,
        retriever_builder: NodeRetrieverBuilder | None = None,
    ) -> None:
        if store_factory is None and database_url is None:
            raise ValueError("A database URL or retrieval store factory is required.")
        self._embedding_provider = embedding_provider
        self._stores = store_factory or PostgresNodeStoreFactory(str(database_url))
        self._build_retriever = retriever_builder or build_node_retriever

    def retrieve(
        self,
        session: Session,
        *,
        question: str,
        embedding_model: str,
        top_k: int,
    ) -> list[RetrievedSource]:
        eligible_document_ids = session.scalars(
            select(Document.id)
            .where(
                Document.status == "ready",
                Document.is_active.is_(True),
                Document.embedding_model == embedding_model,
            )
            .order_by(Document.id.asc())
        ).all()
        if not eligible_document_ids:
            return []

        embedder = CiteNookEmbedding(
            provider=self._embedding_provider,
            model_name=embedding_model,
            batch_size=1,
        )
        try:
            query_embedding = embedder.get_query_embedding(question)
            store = self._stores.read_store(
                session,
                embedding_model,
                len(query_embedding),
            )
            if store is None:
                return []
            filters = source_filters(eligible_document_ids, embedding_model)
            retriever = self._build_retriever(store, embedder, top_k, filters)
            nodes = retriever.retrieve(
                QueryBundle(query_str=question, embedding=query_embedding)
            )
            eligible_ids = set(eligible_document_ids)
            candidates = [
                _source_candidate(node, embedding_model, eligible_ids)
                for node in nodes
            ]
        except SourceRetrievalError:
            raise
        except Exception as error:
            raise SourceRetrievalError("LlamaIndex source retrieval failed.") from error

        candidates.sort(
            key=lambda item: (-item.score, item.ordinal, str(item.chunk_id))
        )
        return [
            RetrievedSource(
                source_id=f"S{index}",
                document_id=item.document_id,
                document_name=item.document_name,
                page_number=item.page_number,
                chunk_id=item.chunk_id,
                snippet=item.snippet,
                score=round(max(-1.0, min(1.0, item.score)), 6),
            )
            for index, item in enumerate(candidates[:top_k], start=1)
        ]


def build_node_retriever(
    store: BasePydanticVectorStore,
    embedder: BaseEmbedding,
    top_k: int,
    filters: MetadataFilters,
) -> BaseRetriever:
    index = VectorStoreIndex.from_vector_store(store, embed_model=embedder)
    return index.as_retriever(similarity_top_k=top_k, filters=filters)


def source_filters(
    document_ids: list[UUID],
    embedding_model: str,
) -> MetadataFilters:
    return MetadataFilters(
        filters=[
            MetadataFilter(
                key="document_id",
                value=[str(document_id) for document_id in document_ids],
                operator=FilterOperator.IN,
            ),
            MetadataFilter(
                key="embedding_model",
                value=embedding_model,
                operator=FilterOperator.EQ,
            ),
        ],
        condition=FilterCondition.AND,
    )


def _source_candidate(
    node_with_score: NodeWithScore,
    embedding_model: str,
    eligible_document_ids: set[UUID],
) -> _SourceCandidate:
    try:
        metadata = node_with_score.node.metadata
        document_id = UUID(_required_text(metadata, "document_id"))
        if document_id not in eligible_document_ids:
            raise ValueError
        document_name = _required_text(metadata, "document_name")
        chunk_id = UUID(_required_text(metadata, "node_id"))
        if node_with_score.node.node_id != str(chunk_id):
            raise ValueError
        if _required_text(metadata, "embedding_model") != embedding_model:
            raise ValueError
        ordinal = metadata["ordinal"]
        page_number = metadata.get("page_number")
        score = float(node_with_score.score)
        snippet = node_with_score.node.get_content(metadata_mode=MetadataMode.NONE)
        if (
            isinstance(ordinal, bool)
            or not isinstance(ordinal, int)
            or ordinal < 0
            or isinstance(page_number, bool)
            or (page_number is not None and not isinstance(page_number, int))
            or not isfinite(score)
            or not snippet.strip()
        ):
            raise ValueError
    except (KeyError, TypeError, ValueError) as error:
        raise SourceRetrievalError(
            "LlamaIndex returned invalid source data."
        ) from error
    return _SourceCandidate(
        document_id=document_id,
        document_name=document_name,
        page_number=page_number,
        chunk_id=chunk_id,
        snippet=snippet,
        score=max(-1.0, min(1.0, score)),
        ordinal=ordinal,
    )


def _required_text(metadata: dict[str, Any], key: str) -> str:
    value = metadata[key]
    if not isinstance(value, str) or not value:
        raise ValueError
    return value
