# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import delete
from sqlalchemy.orm import Session

from ...ai.contracts import EmbeddingProvider
from ...persistence.models import DocumentChunk
from ..contracts import IndexDocument, TextSection
from .chunking import chunk_sections


class NativeDocumentIndexer:
    def __init__(
        self,
        *,
        embedding_provider: EmbeddingProvider,
        embedding_batch_size: int,
    ) -> None:
        self._embedding_provider = embedding_provider
        self._embedding_batch_size = embedding_batch_size

    def replace_document(
        self,
        session: Session,
        document: IndexDocument,
        sections: Sequence[TextSection],
    ) -> int:
        chunks = chunk_sections(sections)
        if not chunks:
            raise ValueError("No readable text was found in the document.")

        embeddings: list[list[float]] = []
        for start in range(0, len(chunks), self._embedding_batch_size):
            batch = chunks[start : start + self._embedding_batch_size]
            embeddings.extend(
                self._embedding_provider.embed(
                    document.embedding_model,
                    [chunk.content for chunk in batch],
                )
            )
        _validate_embeddings(embeddings, len(chunks))

        session.execute(
            delete(DocumentChunk).where(
                DocumentChunk.document_id == document.document_id
            )
        )
        session.add_all(
            [
                DocumentChunk(
                    document_id=document.document_id,
                    ordinal=chunk.ordinal,
                    page_number=chunk.page_number,
                    content=chunk.content,
                    embedding_model=document.embedding_model,
                    embedding=embedding,
                )
                for chunk, embedding in zip(chunks, embeddings, strict=True)
            ]
        )
        return len(chunks)

    def delete_document(self, session: Session, document_id: UUID) -> None:
        session.execute(
            delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
        )


def _validate_embeddings(embeddings: list[list[float]], expected_count: int) -> None:
    if len(embeddings) != expected_count:
        raise RuntimeError("The embedding model returned an unexpected number of vectors.")
    dimensions = {len(embedding) for embedding in embeddings}
    if not dimensions or 0 in dimensions or len(dimensions) != 1:
        raise RuntimeError("The embedding model returned inconsistent vector dimensions.")
