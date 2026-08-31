# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections.abc import Sequence
from contextlib import suppress
from typing import Protocol
from uuid import NAMESPACE_URL, UUID, uuid5

from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import NodeRelationship, RelatedNodeInfo, TextNode
from sqlalchemy.orm import Session

from ...ai.contracts import EmbeddingProvider
from ...persistence.models import Document
from ..contracts import IndexDocument, TextSection
from .embedding import CiteNookEmbedding
from .store import NodeStoreFactory, PostgresNodeStoreFactory

LLAMAINDEX_CHUNK_SIZE = 1024
LLAMAINDEX_CHUNK_OVERLAP = 200


class TextSplitter(Protocol):
    def split_text(self, text: str) -> list[str]: ...


class LlamaIndexDocumentIndexer:
    def __init__(
        self,
        *,
        embedding_provider: EmbeddingProvider,
        embedding_batch_size: int,
        database_url: str | None = None,
        store_factory: NodeStoreFactory | None = None,
        splitter: TextSplitter | None = None,
    ) -> None:
        if store_factory is None and database_url is None:
            raise ValueError("A database URL or node store factory is required.")
        self._embedding_provider = embedding_provider
        self._embedding_batch_size = embedding_batch_size
        self._stores = store_factory or PostgresNodeStoreFactory(str(database_url))
        self._splitter = splitter or SentenceSplitter(
            chunk_size=LLAMAINDEX_CHUNK_SIZE,
            chunk_overlap=LLAMAINDEX_CHUNK_OVERLAP,
        )

    def replace_document(
        self,
        session: Session,
        document: IndexDocument,
        sections: Sequence[TextSection],
    ) -> int:
        nodes = build_nodes(document, sections, self._splitter)
        if not nodes:
            raise ValueError("No readable text was found in the document.")

        embedder = CiteNookEmbedding(
            provider=self._embedding_provider,
            model_name=document.embedding_model,
            batch_size=self._embedding_batch_size,
        )
        embeddings = embedder.get_text_embedding_batch([node.text for node in nodes])
        for node, embedding in zip(nodes, embeddings, strict=True):
            node.embedding = embedding

        dimension = len(embeddings[0])
        self._delete_model_nodes(session, document.document_id, document.embedding_model)
        store = self._stores.write_store(document.embedding_model, dimension)
        try:
            stored_ids = store.add(nodes)
            if stored_ids != [node.node_id for node in nodes]:
                raise RuntimeError("The LlamaIndex store returned unexpected node IDs.")
        except Exception as error:
            with suppress(Exception):
                store.delete(str(document.document_id))
            raise RuntimeError("LlamaIndex node storage failed.") from error
        return len(nodes)

    def delete_document(self, session: Session, document_id: UUID) -> None:
        document = session.get(Document, document_id)
        if document is None:
            return
        self._delete_model_nodes(session, document_id, document.embedding_model)

    def _delete_model_nodes(
        self,
        session: Session,
        document_id: UUID,
        embedding_model: str,
    ) -> None:
        try:
            stores = self._stores.existing_stores(session, embedding_model)
            for store in stores:
                store.delete(str(document_id))
        except Exception as error:
            raise RuntimeError("LlamaIndex index cleanup failed.") from error


def build_nodes(
    document: IndexDocument,
    sections: Sequence[TextSection],
    splitter: TextSplitter,
) -> list[TextNode]:
    nodes: list[TextNode] = []
    for section in sections:
        for content in splitter.split_text(section.text.strip()):
            if not content.strip():
                continue
            ordinal = len(nodes)
            node_id = str(
                uuid5(NAMESPACE_URL, f"citenook:{document.document_id}:{ordinal}")
            )
            metadata: dict[str, str | int | None] = {
                "document_id": str(document.document_id),
                "document_name": document.document_name,
                "page_number": section.page_number,
                "ordinal": ordinal,
                "embedding_model": document.embedding_model,
                "node_id": node_id,
            }
            metadata_keys = list(metadata)
            nodes.append(
                TextNode(
                    id_=node_id,
                    text=content,
                    metadata=metadata,
                    excluded_embed_metadata_keys=metadata_keys,
                    excluded_llm_metadata_keys=metadata_keys,
                    relationships={
                        NodeRelationship.SOURCE: RelatedNodeInfo(
                            node_id=str(document.document_id)
                        )
                    },
                )
            )
    return nodes
