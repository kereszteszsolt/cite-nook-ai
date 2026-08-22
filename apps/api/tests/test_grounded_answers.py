# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest

from app.models import Conversation, ConversationMessage, Document, DocumentChunk
from app.services.answers import (
    GROUNDING_SYSTEM_PROMPT,
    INSUFFICIENT_ANSWER,
    GroundedAnswerError,
    GroundedAnswerService,
)
from app.settings import Settings


class FakeGateway:
    def __init__(self, answer: str = "The answer is supported [S1].") -> None:
        self.answer = answer
        self.embed_calls: list[tuple[str, str]] = []
        self.chat_calls: list[tuple[str, list[dict[str, str]]]] = []

    def embed(self, model: str, inputs: str) -> list[list[float]]:
        self.embed_calls.append((model, inputs))
        return [[0.1, 0.2, 0.3]]

    def chat(self, model: str, messages: list[dict[str, str]]) -> str:
        self.chat_calls.append((model, messages))
        return self.answer


class FakeRows:
    def __init__(self, rows: list[tuple[DocumentChunk, Document, float]]) -> None:
        self._rows = rows

    def all(self) -> list[tuple[DocumentChunk, Document, float]]:
        return self._rows


class AnswerSession:
    def __init__(
        self,
        conversation: Conversation,
        rows: list[tuple[DocumentChunk, Document, float]],
    ) -> None:
        self.conversation = conversation
        self.rows = rows
        self.statement: Any | None = None
        self.refreshed: list[Any] = []

    def get(self, model: type[Any], identifier: UUID) -> Conversation | None:
        assert model is Conversation
        return self.conversation if identifier == self.conversation.id else None

    def execute(self, statement: Any) -> FakeRows:
        self.statement = statement
        return FakeRows(self.rows)

    def refresh(self, value: Any) -> None:
        self.refreshed.append(value)


class FakeConversationService:
    def __init__(
        self,
        conversation: Conversation,
        history: list[ConversationMessage] | None = None,
    ) -> None:
        self.conversation = conversation
        self.history = list(history or [])
        self.recent_calls: list[UUID] = []
        self.record_call: dict[str, Any] | None = None

    def recent_history(
        self, session: Any, conversation_id: UUID
    ) -> list[ConversationMessage]:
        self.recent_calls.append(conversation_id)
        return self.history

    def record_turn(self, session: Any, **values: Any):
        self.record_call = values
        user_message = ConversationMessage(
            id=uuid4(),
            conversation_id=values["conversation_id"],
            ordinal=1,
            role="user",
            content=values["question"],
            chat_model=None,
            citations=[],
        )
        assistant_message = ConversationMessage(
            id=uuid4(),
            conversation_id=values["conversation_id"],
            ordinal=2,
            role="assistant",
            content=values["answer"],
            chat_model=values["chat_model"],
            citations=values["citations"],
            response_duration_ms=values["response_duration_ms"],
        )
        return user_message, assistant_message


def settings(*, top_k: int = 2) -> Settings:
    return Settings(
        database_url="postgresql+psycopg://unused",
        ollama_host="http://ollama.test",
        chat_models=("chat-a",),
        embedding_models=("embed-a",),
        default_chat_model="chat-a",
        default_embedding_model="embed-a",
        brand_config_path=Path("brand.json"),
        cors_origins=("http://localhost:5173",),
        rag_top_k=top_k,
    )


def conversation() -> Conversation:
    return Conversation(
        id=uuid4(),
        title="New conversation",
        chat_model="chat-a",
        embedding_model="embed-a",
    )


def source_row(name: str, ordinal: int, distance: float):
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


def test_answer_uses_conversation_models_ready_compatible_chunks_and_markers() -> None:
    stored_conversation = conversation()
    history = [
        ConversationMessage(
            id=uuid4(),
            conversation_id=stored_conversation.id,
            ordinal=1,
            role="user",
            content="Earlier question",
            chat_model=None,
            citations=[],
        )
    ]
    conversation_service = FakeConversationService(stored_conversation, history)
    gateway = FakeGateway("The second passage supports this statement [S2].")
    session = AnswerSession(
        stored_conversation,
        [source_row("first.txt", 0, 0.1), source_row("second.pdf", 1, 0.2)],
    )
    service = GroundedAnswerService(
        gateway=gateway,  # type: ignore[arg-type]
        settings=settings(),
        conversations=conversation_service,  # type: ignore[arg-type]
        clock=iter([100.0, 102.345]).__next__,
    )

    result = service.answer(
        session,  # type: ignore[arg-type]
        conversation_id=stored_conversation.id,
        question="  What   is supported? ",
    )

    assert result is not None
    assert gateway.embed_calls == [("embed-a", "What is supported?")]
    assert gateway.chat_calls[0][0] == "chat-a"
    chat_messages = gateway.chat_calls[0][1]
    assert chat_messages[0] == {"role": "system", "content": GROUNDING_SYSTEM_PROMPT}
    assert chat_messages[1]["content"] == "Earlier question"
    assert '"source": "S1"' in chat_messages[-1]["content"]
    assert '"source": "S2"' in chat_messages[-1]["content"]
    assert INSUFFICIENT_ANSWER in GROUNDING_SYSTEM_PROMPT
    assert conversation_service.recent_calls == [stored_conversation.id]
    assert conversation_service.record_call is not None
    citations = conversation_service.record_call["citations"]
    assert [citation["source_id"] for citation in citations] == ["S2"]
    assert citations[0]["document_name"] == "second.pdf"
    assert citations[0]["page_number"] == 2
    assert citations[0]["score"] == 0.8
    assert conversation_service.record_call["response_duration_ms"] == 2345
    assert result.assistant_message.response_duration_ms == 2345
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
    assert settings().rag_top_k in session.statement.compile().params.values()


def test_missing_compatible_sources_returns_explicit_insufficiency_without_chat() -> None:
    stored_conversation = conversation()
    conversation_service = FakeConversationService(stored_conversation)
    gateway = FakeGateway()
    session = AnswerSession(stored_conversation, [])
    service = GroundedAnswerService(
        gateway=gateway,  # type: ignore[arg-type]
        settings=settings(),
        conversations=conversation_service,  # type: ignore[arg-type]
    )

    result = service.answer(
        session,  # type: ignore[arg-type]
        conversation_id=stored_conversation.id,
        question="Unknown topic?",
    )

    assert result is not None
    assert gateway.embed_calls == [("embed-a", "Unknown topic?")]
    assert gateway.chat_calls == []
    assert conversation_service.record_call is not None
    assert conversation_service.record_call["answer"] == INSUFFICIENT_ANSWER
    assert conversation_service.record_call["citations"] == []


def test_chat_answer_with_an_unknown_source_marker_is_rejected() -> None:
    stored_conversation = conversation()
    conversation_service = FakeConversationService(stored_conversation)
    gateway = FakeGateway("Unsupported claim [S9].")
    session = AnswerSession(stored_conversation, [source_row("only.txt", 0, 0.1)])
    service = GroundedAnswerService(
        gateway=gateway,  # type: ignore[arg-type]
        settings=settings(),
        conversations=conversation_service,  # type: ignore[arg-type]
    )

    with pytest.raises(GroundedAnswerError, match="unavailable source markers: S9"):
        service.answer(
            session,  # type: ignore[arg-type]
            conversation_id=stored_conversation.id,
            question="Question",
        )

    assert conversation_service.record_call is None


def test_chat_answer_without_marker_or_insufficiency_is_rejected() -> None:
    stored_conversation = conversation()
    conversation_service = FakeConversationService(stored_conversation)
    gateway = FakeGateway("An ungrounded answer.")
    service = GroundedAnswerService(
        gateway=gateway,  # type: ignore[arg-type]
        settings=settings(),
        conversations=conversation_service,  # type: ignore[arg-type]
    )

    with pytest.raises(GroundedAnswerError, match="without a source marker"):
        service.answer(
            AnswerSession(  # type: ignore[arg-type]
                stored_conversation, [source_row("only.txt", 0, 0.1)]
            ),
            conversation_id=stored_conversation.id,
            question="Question",
        )

    assert conversation_service.record_call is None
