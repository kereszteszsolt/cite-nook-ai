# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


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


class ConversationUpdate(ConversationCreate):
    pass


class ConversationRead(ApiModel):
    id: UUID
    title: str
    chat_model: str
    embedding_model: str
    created_at: datetime
    updated_at: datetime


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
    created_at: datetime
