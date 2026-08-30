# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any
from uuid import UUID, uuid4

import pytest

from app.application.answers import (
    GROUNDING_SYSTEM_PROMPT,
    INSUFFICIENT_ANSWER,
    GroundedAnswerError,
    GroundedAnswerService,
)
from app.persistence.models import Conversation, ConversationMessage
from app.rag.contracts import RetrievedSource


class FakeChatProvider:
    def __init__(self, answer: str = "The answer is supported [S1].") -> None:
        self.answer = answer
        self.calls: list[tuple[str, list[dict[str, str]]]] = []

    def chat(self, model: str, messages: Sequence[Mapping[str, str]]) -> str:
        self.calls.append((model, [dict(message) for message in messages]))
        return self.answer


class FakeRetriever:
    def __init__(self, sources: list[RetrievedSource]) -> None:
        self.sources = sources
        self.calls: list[tuple[Any, str, str, int]] = []

    def retrieve(
        self,
        session: Any,
        *,
        question: str,
        embedding_model: str,
        top_k: int,
    ) -> list[RetrievedSource]:
        self.calls.append((session, question, embedding_model, top_k))
        return self.sources


class AnswerSession:
    def __init__(self, conversation: Conversation) -> None:
        self.conversation = conversation
        self.refreshed: list[Any] = []

    def get(self, model: type[Any], identifier: UUID) -> Conversation | None:
        assert model is Conversation
        return self.conversation if identifier == self.conversation.id else None

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


def conversation() -> Conversation:
    return Conversation(
        id=uuid4(),
        title="New conversation",
        chat_model="chat-a",
        embedding_model="embed-a",
    )


def source(name: str, ordinal: int, score: float) -> RetrievedSource:
    return RetrievedSource(
        source_id=f"S{ordinal + 1}",
        document_id=uuid4(),
        document_name=name,
        page_number=ordinal + 1,
        chunk_id=uuid4(),
        snippet=f"Grounded passage from {name}.",
        score=score,
    )


def test_answer_uses_retrieved_sources_and_keeps_grounding_rules() -> None:
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
    chat_provider = FakeChatProvider(
        "The second passage supports this statement [S2]."
    )
    retriever = FakeRetriever(
        [source("first.txt", 0, 0.9), source("second.pdf", 1, 0.8)]
    )
    session = AnswerSession(stored_conversation)
    service = GroundedAnswerService(
        chat_provider=chat_provider,
        retriever=retriever,
        top_k=2,
        conversations=conversation_service,  # type: ignore[arg-type]
        clock=iter([100.0, 102.345]).__next__,
    )

    result = service.answer(
        session,  # type: ignore[arg-type]
        conversation_id=stored_conversation.id,
        question="  What   is supported? ",
    )

    assert result is not None
    assert retriever.calls == [(session, "What is supported?", "embed-a", 2)]
    assert chat_provider.calls[0][0] == "chat-a"
    chat_messages = chat_provider.calls[0][1]
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


def test_missing_sources_returns_explicit_insufficiency_without_chat() -> None:
    stored_conversation = conversation()
    conversation_service = FakeConversationService(stored_conversation)
    chat_provider = FakeChatProvider()
    retriever = FakeRetriever([])
    session = AnswerSession(stored_conversation)
    service = GroundedAnswerService(
        chat_provider=chat_provider,
        retriever=retriever,
        top_k=3,
        conversations=conversation_service,  # type: ignore[arg-type]
    )

    result = service.answer(
        session,  # type: ignore[arg-type]
        conversation_id=stored_conversation.id,
        question="Unknown topic?",
    )

    assert result is not None
    assert retriever.calls == [(session, "Unknown topic?", "embed-a", 3)]
    assert chat_provider.calls == []
    assert conversation_service.record_call is not None
    assert conversation_service.record_call["answer"] == INSUFFICIENT_ANSWER
    assert conversation_service.record_call["citations"] == []


def test_chat_answer_with_an_unknown_source_marker_is_rejected() -> None:
    stored_conversation = conversation()
    conversation_service = FakeConversationService(stored_conversation)
    service = GroundedAnswerService(
        chat_provider=FakeChatProvider("Unsupported claim [S9]."),
        retriever=FakeRetriever([source("only.txt", 0, 0.9)]),
        top_k=2,
        conversations=conversation_service,  # type: ignore[arg-type]
    )

    with pytest.raises(GroundedAnswerError, match="unavailable source markers: S9"):
        service.answer(
            AnswerSession(stored_conversation),  # type: ignore[arg-type]
            conversation_id=stored_conversation.id,
            question="Question",
        )

    assert conversation_service.record_call is None


def test_chat_answer_without_marker_or_insufficiency_is_rejected() -> None:
    stored_conversation = conversation()
    conversation_service = FakeConversationService(stored_conversation)
    service = GroundedAnswerService(
        chat_provider=FakeChatProvider("An ungrounded answer."),
        retriever=FakeRetriever([source("only.txt", 0, 0.9)]),
        top_k=2,
        conversations=conversation_service,  # type: ignore[arg-type]
    )

    with pytest.raises(GroundedAnswerError, match="without a source marker"):
        service.answer(
            AnswerSession(stored_conversation),  # type: ignore[arg-type]
            conversation_id=stored_conversation.id,
            question="Question",
        )

    assert conversation_service.record_call is None
