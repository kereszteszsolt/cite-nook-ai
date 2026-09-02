# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..core.settings import Settings
from ..persistence.models import Conversation, ConversationMessage, utc_now

CONVERSATION_TITLE_LENGTH = 80
CONVERSATION_TITLE_MAX_LENGTH = 120


class UnsupportedModelError(ValueError):
    pass


class InvalidConversationTitleError(ValueError):
    pass


class ConversationService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def list(self, session: Session) -> list[Conversation]:
        return list(
            session.scalars(
                select(Conversation).order_by(
                    Conversation.updated_at.desc(), Conversation.id.desc()
                )
            )
        )

    def create(
        self,
        session: Session,
        *,
        chat_model: str,
        embedding_model: str,
    ) -> Conversation:
        self._validate(chat_model, embedding_model)
        conversation = Conversation(chat_model=chat_model, embedding_model=embedding_model)
        session.add(conversation)
        session.commit()
        session.refresh(conversation)
        return conversation

    def list_messages(
        self, session: Session, conversation_id: UUID
    ) -> list[ConversationMessage] | None:
        if session.get(Conversation, conversation_id) is None:
            return None
        return list(
            session.scalars(
                select(ConversationMessage)
                .where(ConversationMessage.conversation_id == conversation_id)
                .order_by(ConversationMessage.ordinal)
            )
        )

    def recent_history(
        self, session: Session, conversation_id: UUID
    ) -> list[ConversationMessage]:
        messages = list(
            session.scalars(
                select(ConversationMessage)
                .where(ConversationMessage.conversation_id == conversation_id)
                .order_by(ConversationMessage.ordinal.desc())
                .limit(self._settings.chat_history_messages)
            )
        )
        messages.reverse()
        return messages

    def record_turn(
        self,
        session: Session,
        *,
        conversation_id: UUID,
        question: str,
        answer: str,
        chat_model: str,
        citations: list[Mapping[str, Any]],
        response_duration_ms: int | None = None,
    ) -> tuple[ConversationMessage, ConversationMessage] | None:
        normalized_question = " ".join(question.split())
        normalized_answer = answer.strip()
        if not normalized_question:
            raise ValueError("Question must not be empty.")
        if not normalized_answer:
            raise ValueError("Answer must not be empty.")
        if chat_model not in self._settings.chat_models:
            raise UnsupportedModelError("Unsupported chat model.")
        if response_duration_ms is not None and response_duration_ms < 0:
            raise ValueError("Response duration must not be negative.")

        conversation = session.scalar(
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .with_for_update()
        )
        if conversation is None:
            return None
        if conversation.chat_model != chat_model:
            raise UnsupportedModelError("Chat model does not match the conversation.")

        last_ordinal = session.scalar(
            select(func.coalesce(func.max(ConversationMessage.ordinal), 0)).where(
                ConversationMessage.conversation_id == conversation_id
            )
        )
        next_ordinal = int(last_ordinal or 0) + 1
        user_message = ConversationMessage(
            conversation_id=conversation_id,
            ordinal=next_ordinal,
            role="user",
            content=normalized_question,
            chat_model=None,
            citations=[],
            response_duration_ms=None,
        )
        assistant_message = ConversationMessage(
            conversation_id=conversation_id,
            ordinal=next_ordinal + 1,
            role="assistant",
            content=normalized_answer,
            chat_model=chat_model,
            citations=[serialize_citation(citation) for citation in citations],
            response_duration_ms=response_duration_ms,
        )
        if next_ordinal == 1 and conversation.title == "New conversation":
            conversation.title = deterministic_title(normalized_question)
        conversation.updated_at = utc_now()
        session.add_all([user_message, assistant_message])
        session.commit()
        session.refresh(user_message)
        session.refresh(assistant_message)
        return user_message, assistant_message

    def delete(self, session: Session, conversation_id: UUID) -> bool:
        conversation = session.get(Conversation, conversation_id)
        if conversation is None:
            return False
        session.delete(conversation)
        session.commit()
        return True

    def update(
        self,
        session: Session,
        *,
        conversation_id: UUID,
        chat_model: str | None = None,
        embedding_model: str | None = None,
        title: str | None = None,
    ) -> Conversation | None:
        if chat_model is None and embedding_model is None and title is None:
            raise ValueError("At least one conversation field must be provided.")
        if chat_model is not None and chat_model not in self._settings.chat_models:
            raise UnsupportedModelError("Unsupported chat model.")
        if (
            embedding_model is not None
            and embedding_model not in self._settings.embedding_models
        ):
            raise UnsupportedModelError("Unsupported embedding model.")
        normalized_title = normalize_custom_title(title) if title is not None else None

        conversation = session.get(Conversation, conversation_id)
        if conversation is None:
            return None
        if chat_model is not None:
            conversation.chat_model = chat_model
        if embedding_model is not None:
            conversation.embedding_model = embedding_model
        if normalized_title is not None:
            conversation.title = normalized_title
        conversation.updated_at = utc_now()
        session.commit()
        session.refresh(conversation)
        return conversation

    def _validate(self, chat_model: str, embedding_model: str) -> None:
        if chat_model not in self._settings.chat_models:
            raise UnsupportedModelError("Unsupported chat model.")
        if embedding_model not in self._settings.embedding_models:
            raise UnsupportedModelError("Unsupported embedding model.")


def deterministic_title(question: str) -> str:
    normalized = " ".join(question.split())
    if len(normalized) <= CONVERSATION_TITLE_LENGTH:
        return normalized
    return f"{normalized[: CONVERSATION_TITLE_LENGTH - 1].rstrip()}…"


def normalize_custom_title(title: str) -> str:
    normalized = " ".join(title.split())
    if not normalized:
        raise InvalidConversationTitleError("Conversation title must not be empty.")
    if len(normalized) > CONVERSATION_TITLE_MAX_LENGTH:
        raise InvalidConversationTitleError(
            f"Conversation title must be at most {CONVERSATION_TITLE_MAX_LENGTH} characters."
        )
    return normalized


def serialize_citation(citation: Mapping[str, Any]) -> dict[str, Any]:
    page_number = citation["page_number"]
    return {
        "source_id": str(citation["source_id"]),
        "document_id": str(UUID(str(citation["document_id"]))),
        "document_name": str(citation["document_name"]),
        "page_number": None if page_number is None else int(page_number),
        "chunk_id": str(UUID(str(citation["chunk_id"]))),
        "snippet": str(citation["snippet"]),
        "score": float(citation["score"]),
    }
