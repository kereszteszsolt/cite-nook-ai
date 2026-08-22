# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def to_camel(value: str) -> str:
    head, *tail = value.split("_")
    return head + "".join(part.capitalize() for part in tail)


class ApiModel(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        alias_generator=to_camel,
    )


class ModelOption(ApiModel):
    name: str
    installed: bool


class ModelCatalog(ApiModel):
    chat_models: list[ModelOption]
    embedding_models: list[ModelOption]
    default_chat_model: str
    default_embedding_model: str
    ollama_available: bool


class ConversationCreate(ApiModel):
    chat_model: str = Field(min_length=1, max_length=200)
    embedding_model: str = Field(min_length=1, max_length=200)


class ConversationUpdate(ApiModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    chat_model: str | None = Field(default=None, min_length=1, max_length=200)
    embedding_model: str | None = Field(default=None, min_length=1, max_length=200)

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = " ".join(value.split())
        if not normalized:
            raise ValueError("Conversation title must not be empty.")
        return normalized

    @model_validator(mode="after")
    def require_change(self) -> ConversationUpdate:
        if self.title is None and self.chat_model is None and self.embedding_model is None:
            raise ValueError("At least one conversation field must be provided.")
        return self


class QuestionCreate(ApiModel):
    question: str = Field(min_length=1, max_length=4000)


class ConversationRead(ApiModel):
    id: UUID
    title: str
    chat_model: str
    embedding_model: str
    created_at: datetime
    updated_at: datetime


class CitationRead(ApiModel):
    source_id: str = Field(min_length=1, max_length=20)
    document_id: UUID
    document_name: str
    page_number: int | None
    chunk_id: UUID
    snippet: str
    score: float


class MessageRead(ApiModel):
    id: UUID
    conversation_id: UUID
    ordinal: int
    role: Literal["user", "assistant"]
    content: str
    chat_model: str | None
    citations: list[CitationRead]
    created_at: datetime


class AnswerRead(ApiModel):
    conversation: ConversationRead
    user_message: MessageRead
    assistant_message: MessageRead


class DocumentRead(ApiModel):
    id: UUID
    file_name: str
    content_type: str
    size_bytes: int
    sha256: str
    embedding_model: str
    status: Literal["queued", "processing", "ready", "failed"]
    error_message: str | None
    chunk_count: int
    is_active: bool
    created_at: datetime


class DocumentUpdate(ApiModel):
    is_active: bool
