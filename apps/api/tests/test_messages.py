# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest

from app.application.conversations import (
    ConversationService,
    InvalidConversationTitleError,
    deterministic_title,
)
from app.core.settings import Settings
from app.persistence.models import Conversation, ConversationMessage


class MessageSession:
    def __init__(
        self,
        *,
        conversation: Conversation | None = None,
        scalar_results: list[Any] | None = None,
        messages: list[ConversationMessage] | None = None,
    ) -> None:
        self.conversation = conversation
        self.scalar_results = list(scalar_results or [])
        self.messages = list(messages or [])
        self.scalar_statements: list[Any] = []
        self.scalars_statement: Any | None = None
        self.added: list[Any] = []
        self.deleted: list[Any] = []
        self.committed = False
        self.refreshed: list[Any] = []

    def scalar(self, statement: Any) -> Any:
        self.scalar_statements.append(statement)
        return self.scalar_results.pop(0)

    def scalars(self, statement: Any) -> list[ConversationMessage]:
        self.scalars_statement = statement
        return self.messages

    def get(self, model: type[Any], identifier: UUID) -> Conversation | None:
        assert model is Conversation
        if self.conversation is not None and self.conversation.id == identifier:
            return self.conversation
        return None

    def add_all(self, objects: list[Any]) -> None:
        self.added.extend(objects)

    def delete(self, value: Any) -> None:
        self.deleted.append(value)

    def commit(self) -> None:
        self.committed = True

    def refresh(self, value: Any) -> None:
        self.refreshed.append(value)


def message_service(*, history_messages: int = 12) -> ConversationService:
    return ConversationService(
        Settings(
            database_url="postgresql+psycopg://unused",
            ollama_host="http://ollama.test",
            chat_models=("chat-a", "chat-b"),
            embedding_models=("embed-a", "embed-b"),
            default_chat_model="chat-a",
            default_embedding_model="embed-a",
            brand_config_path=Path("brand.json"),
            cors_origins=("http://localhost:5173",),
            chat_history_messages=history_messages,
        )
    )


def conversation() -> Conversation:
    return Conversation(
        id=uuid4(),
        title="New conversation",
        chat_model="chat-a",
        embedding_model="embed-a",
    )


def message(ordinal: int) -> ConversationMessage:
    return ConversationMessage(
        id=uuid4(),
        conversation_id=uuid4(),
        ordinal=ordinal,
        role="user" if ordinal % 2 else "assistant",
        content=f"message {ordinal}",
        chat_model=None if ordinal % 2 else "chat-a",
        citations=[],
    )


def test_first_turn_is_atomic_titled_and_preserves_assistant_provenance() -> None:
    stored_conversation = conversation()
    document_id = uuid4()
    chunk_id = uuid4()
    citation = {
        "source_id": "S1",
        "document_id": document_id,
        "document_name": "notes.md",
        "page_number": 2,
        "chunk_id": chunk_id,
        "snippet": "Relevant text",
        "score": 0.91,
    }
    session = MessageSession(
        conversation=stored_conversation,
        scalar_results=[stored_conversation, 0],
    )
    question = "  What   does the document say about deterministic titles?  "

    result = message_service().record_turn(  # type: ignore[arg-type]
        session,
        conversation_id=stored_conversation.id,
        question=question,
        answer="It describes a bounded local title.",
        chat_model="chat-a",
        citations=[citation],
        response_duration_ms=1234,
    )

    assert result is not None
    user_message, assistant_message = result
    assert user_message.ordinal == 1
    assert user_message.role == "user"
    assert user_message.content == "What does the document say about deterministic titles?"
    assert user_message.chat_model is None
    assert user_message.citations == []
    assert assistant_message.ordinal == 2
    assert assistant_message.role == "assistant"
    assert assistant_message.chat_model == "chat-a"
    assert user_message.response_duration_ms is None
    assert assistant_message.response_duration_ms == 1234
    assert set(assistant_message.citations[0]) == {
        "source_id",
        "document_id",
        "document_name",
        "page_number",
        "chunk_id",
        "snippet",
        "score",
    }
    assert assistant_message.citations[0]["document_id"] == str(document_id)
    assert assistant_message.citations[0]["chunk_id"] == str(chunk_id)
    assert stored_conversation.title == user_message.content
    assert session.added == [user_message, assistant_message]
    assert session.committed is True
    assert len(session.scalar_statements) == 2
    assert "FOR UPDATE" in str(session.scalar_statements[0])


def test_turn_rejects_a_negative_response_duration_before_persistence() -> None:
    stored_conversation = conversation()
    session = MessageSession(
        conversation=stored_conversation,
        scalar_results=[stored_conversation, 0],
    )

    with pytest.raises(ValueError, match="must not be negative"):
        message_service().record_turn(  # type: ignore[arg-type]
            session,
            conversation_id=stored_conversation.id,
            question="Question",
            answer="Answer",
            chat_model="chat-a",
            citations=[],
            response_duration_ms=-1,
        )

    assert session.added == []
    assert session.committed is False


def test_deterministic_title_is_normalized_and_bounded() -> None:
    question = "  Why   is this title deterministic? " + ("detail " * 30)

    first = deterministic_title(question)
    second = deterministic_title(question)

    assert first == second
    assert len(first) == 80
    assert first.endswith("…")
    assert "  " not in first


def test_later_turn_keeps_the_first_question_title() -> None:
    stored_conversation = conversation()
    stored_conversation.title = "Original first question"
    session = MessageSession(
        conversation=stored_conversation,
        scalar_results=[stored_conversation, 2],
    )

    result = message_service().record_turn(  # type: ignore[arg-type]
        session,
        conversation_id=stored_conversation.id,
        question="A later question",
        answer="A later answer",
        chat_model="chat-a",
        citations=[],
    )

    assert result is not None
    assert stored_conversation.title == "Original first question"
    assert [item.ordinal for item in result] == [3, 4]


def test_first_turn_keeps_a_manually_edited_title() -> None:
    stored_conversation = conversation()
    stored_conversation.title = "My research notes"
    session = MessageSession(
        conversation=stored_conversation,
        scalar_results=[stored_conversation, 0],
    )

    message_service().record_turn(  # type: ignore[arg-type]
        session,
        conversation_id=stored_conversation.id,
        question="The first question",
        answer="The first answer",
        chat_model="chat-a",
        citations=[],
    )

    assert stored_conversation.title == "My research notes"


def test_update_persists_a_normalized_title_without_changing_models() -> None:
    stored_conversation = conversation()
    session = MessageSession(conversation=stored_conversation)

    updated = message_service().update(  # type: ignore[arg-type]
        session,
        conversation_id=stored_conversation.id,
        title="  Project   sources  ",
    )

    assert updated is stored_conversation
    assert stored_conversation.title == "Project sources"
    assert stored_conversation.chat_model == "chat-a"
    assert stored_conversation.embedding_model == "embed-a"
    assert session.committed is True
    assert session.refreshed == [stored_conversation]


def test_update_changes_the_conversation_pair_without_rewriting_message_provenance() -> None:
    stored_conversation = conversation()
    stored_assistant = message(2)
    session = MessageSession(
        conversation=stored_conversation,
        messages=[stored_assistant],
    )

    updated = message_service().update(  # type: ignore[arg-type]
        session,
        conversation_id=stored_conversation.id,
        chat_model="chat-b",
        embedding_model="embed-b",
    )

    assert updated is stored_conversation
    assert stored_conversation.chat_model == "chat-b"
    assert stored_conversation.embedding_model == "embed-b"
    assert stored_assistant.chat_model == "chat-a"
    assert session.messages == [stored_assistant]
    assert session.committed is True
    assert session.refreshed == [stored_conversation]


def test_update_rejects_empty_and_oversized_titles() -> None:
    stored_conversation = conversation()
    session = MessageSession(conversation=stored_conversation)
    service = message_service()

    with pytest.raises(InvalidConversationTitleError, match="must not be empty"):
        service.update(  # type: ignore[arg-type]
            session,
            conversation_id=stored_conversation.id,
            title="   ",
        )
    with pytest.raises(InvalidConversationTitleError, match="at most 120"):
        service.update(  # type: ignore[arg-type]
            session,
            conversation_id=stored_conversation.id,
            title="x" * 121,
        )

    assert stored_conversation.title == "New conversation"
    assert session.committed is False


def test_full_history_is_ordered_and_recent_history_is_bounded() -> None:
    stored_conversation = conversation()
    full_messages = [message(index) for index in range(1, 7)]
    full_session = MessageSession(
        conversation=stored_conversation,
        messages=full_messages,
    )

    assert message_service().list_messages(  # type: ignore[arg-type]
        full_session, stored_conversation.id
    ) == full_messages
    assert "ORDER BY conversation_messages.ordinal" in str(full_session.scalars_statement)
    assert "LIMIT" not in str(full_session.scalars_statement)

    recent_descending = [full_messages[5], full_messages[4], full_messages[3]]
    recent_session = MessageSession(messages=recent_descending)
    recent = message_service(history_messages=3).recent_history(  # type: ignore[arg-type]
        recent_session, stored_conversation.id
    )

    assert [item.ordinal for item in recent] == [4, 5, 6]
    assert "ORDER BY conversation_messages.ordinal DESC" in str(
        recent_session.scalars_statement
    )
    assert "LIMIT" in str(recent_session.scalars_statement)
    assert 3 in recent_session.scalars_statement.compile().params.values()


def test_conversation_list_uses_recent_activity_and_delete_cascades_by_model() -> None:
    stored_conversation = conversation()
    session = MessageSession(
        conversation=stored_conversation,
        messages=[],
    )

    message_service().list(session)  # type: ignore[arg-type]
    assert "conversations.updated_at DESC" in str(session.scalars_statement)

    assert message_service().delete(  # type: ignore[arg-type]
        session, stored_conversation.id
    ) is True
    assert session.deleted == [stored_conversation]
    assert session.committed is True
    assert "delete" in Conversation.messages.property.cascade
    assert "delete-orphan" in Conversation.messages.property.cascade
