# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Conversation, utc_now
from ..settings import Settings, get_settings


class UnsupportedModelError(ValueError):
    pass


class ConversationService:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    def list(self, session: Session) -> list[Conversation]:
        return list(session.scalars(select(Conversation).order_by(Conversation.created_at.desc())))

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

    def update(
        self,
        session: Session,
        *,
        conversation_id: UUID,
        chat_model: str,
        embedding_model: str,
    ) -> Conversation | None:
        self._validate(chat_model, embedding_model)
        conversation = session.get(Conversation, conversation_id)
        if conversation is None:
            return None
        conversation.chat_model = chat_model
        conversation.embedding_model = embedding_model
        conversation.updated_at = utc_now()
        session.commit()
        session.refresh(conversation)
        return conversation

    def _validate(self, chat_model: str, embedding_model: str) -> None:
        if chat_model not in self._settings.chat_models:
            raise UnsupportedModelError("Unsupported chat model.")
        if embedding_model not in self._settings.embedding_models:
            raise UnsupportedModelError("Unsupported embedding model.")
