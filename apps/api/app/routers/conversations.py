# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from ..dependencies import DatabaseSession
from ..models import Conversation
from ..schemas import ConversationCreate, ConversationRead, ConversationUpdate
from ..services.conversations import ConversationService, UnsupportedModelError

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationRead])
def list_conversations(session: DatabaseSession) -> list[Conversation]:
    return ConversationService().list(session)


@router.post("", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
def create_conversation(
    payload: ConversationCreate,
    session: DatabaseSession,
) -> Conversation:
    try:
        return ConversationService().create(
            session,
            chat_model=payload.chat_model,
            embedding_model=payload.embedding_model,
        )
    except UnsupportedModelError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.patch("/{conversation_id}", response_model=ConversationRead)
def update_conversation(
    conversation_id: UUID,
    payload: ConversationUpdate,
    session: DatabaseSession,
) -> Conversation:
    service = ConversationService()
    try:
        conversation = service.update(
            session,
            conversation_id=conversation_id,
            chat_model=payload.chat_model,
            embedding_model=payload.embedding_model,
        )
    except UnsupportedModelError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return conversation
