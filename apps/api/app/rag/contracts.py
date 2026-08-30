# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Protocol
from uuid import UUID

from sqlalchemy.orm import Session


@dataclass(frozen=True, slots=True)
class TextSection:
    text: str
    page_number: int | None = None


@dataclass(frozen=True, slots=True)
class IndexDocument:
    document_id: UUID
    document_name: str
    embedding_model: str


@dataclass(frozen=True, slots=True)
class RetrievedSource:
    source_id: str
    document_id: UUID
    document_name: str
    page_number: int | None
    chunk_id: UUID
    snippet: str
    score: float

    def citation(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "document_id": self.document_id,
            "document_name": self.document_name,
            "page_number": self.page_number,
            "chunk_id": self.chunk_id,
            "snippet": self.snippet,
            "score": self.score,
        }


class SourceRetrievalError(RuntimeError):
    pass


class DocumentIndexer(Protocol):
    def replace_document(
        self,
        session: Session,
        document: IndexDocument,
        sections: Sequence[TextSection],
    ) -> int: ...

    def delete_document(self, session: Session, document_id: UUID) -> None: ...


class SourceRetriever(Protocol):
    def retrieve(
        self,
        session: Session,
        *,
        question: str,
        embedding_model: str,
        top_k: int,
    ) -> list[RetrievedSource]: ...
