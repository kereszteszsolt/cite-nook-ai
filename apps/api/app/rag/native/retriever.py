# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from sqlalchemy import select
from sqlalchemy.orm import Session

from ...ai.contracts import EmbeddingProvider
from ...persistence.models import Document, DocumentChunk
from ..contracts import RetrievedSource, SourceRetrievalError


class NativeSourceRetriever:
    def __init__(self, *, embedding_provider: EmbeddingProvider) -> None:
        self._embedding_provider = embedding_provider

    def retrieve(
        self,
        session: Session,
        *,
        question: str,
        embedding_model: str,
        top_k: int,
    ) -> list[RetrievedSource]:
        embeddings = self._embedding_provider.embed(embedding_model, question)
        if len(embeddings) != 1:
            raise SourceRetrievalError(
                "The embedding model returned an unexpected number of vectors."
            )

        distance = DocumentChunk.embedding.cosine_distance(embeddings[0]).label(
            "distance"
        )
        statement = (
            select(DocumentChunk, Document, distance)
            .join(Document, Document.id == DocumentChunk.document_id)
            .where(
                Document.status == "ready",
                Document.is_active.is_(True),
                Document.embedding_model == embedding_model,
                DocumentChunk.embedding_model == embedding_model,
            )
            .order_by(distance.asc(), DocumentChunk.id.asc())
            .limit(top_k)
        )
        rows = session.execute(statement).all()
        return [
            RetrievedSource(
                source_id=f"S{index}",
                document_id=document.id,
                document_name=document.file_name,
                page_number=chunk.page_number,
                chunk_id=chunk.id,
                snippet=chunk.content,
                score=round(max(-1.0, min(1.0, 1.0 - float(row_distance))), 6),
            )
            for index, (chunk, document, row_distance) in enumerate(rows, start=1)
        ]
