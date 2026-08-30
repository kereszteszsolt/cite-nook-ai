# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, status

from ...ai.contracts import ModelProviderUnavailableError
from ...application.answers import AnswerResult, GroundedAnswerError
from ...application.conversations import (
    InvalidConversationTitleError,
    UnsupportedModelError,
)
from ...persistence.models import Conversation, ConversationMessage
from ..dependencies import (
    AnswerServiceDependency,
    ConversationServiceDependency,
    DatabaseSession,
)
from ..schemas import (
    AnswerRead,
    ConversationCreate,
    ConversationRead,
    ConversationUpdate,
    MessageRead,
    QuestionCreate,
)

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationRead])
def list_conversations(
    session: DatabaseSession,
    service: ConversationServiceDependency,
) -> list[Conversation]:
    return service.list(session)


@router.post("", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
def create_conversation(
    payload: ConversationCreate,
    session: DatabaseSession,
    service: ConversationServiceDependency,
) -> Conversation:
    try:
        return service.create(
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
    service: ConversationServiceDependency,
) -> Conversation:
    try:
        conversation = service.update(
            session,
            conversation_id=conversation_id,
            chat_model=payload.chat_model,
            embedding_model=payload.embedding_model,
            title=payload.title,
        )
    except (InvalidConversationTitleError, UnsupportedModelError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return conversation


@router.get("/{conversation_id}/messages", response_model=list[MessageRead])
def list_messages(
    conversation_id: UUID,
    session: DatabaseSession,
    service: ConversationServiceDependency,
) -> list[ConversationMessage]:
    messages = service.list_messages(session, conversation_id)
    if messages is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return messages


@router.post("/{conversation_id}/messages", response_model=AnswerRead)
def answer_question(
    conversation_id: UUID,
    payload: QuestionCreate,
    session: DatabaseSession,
    service: AnswerServiceDependency,
) -> AnswerResult:
    try:
        result = service.answer(
            session, conversation_id=conversation_id, question=payload.question
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except ModelProviderUnavailableError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except GroundedAnswerError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    if result is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return result


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: UUID,
    session: DatabaseSession,
    service: ConversationServiceDependency,
) -> Response:
    if not service.delete(session, conversation_id):
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
