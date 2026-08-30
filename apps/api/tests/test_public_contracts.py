# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.ai.contracts import ModelProviderUnavailableError
from app.api.routers.conversations import answer_question
from app.api.schemas import ModelCatalog as ApiModelCatalog
from app.api.schemas import QuestionCreate
from app.application.model_catalog import ModelCatalog, ModelOption
from app.main import app
from app.persistence.database import Base


def test_public_routes_are_unchanged() -> None:
    http_methods = {"delete", "get", "patch", "post"}
    routes = {
        (method.upper(), path)
        for path, operations in app.openapi()["paths"].items()
        for method in operations
        if method in http_methods
    }

    assert routes == {
        ("GET", "/api/brand"),
        ("GET", "/api/conversations"),
        ("POST", "/api/conversations"),
        ("DELETE", "/api/conversations/{conversation_id}"),
        ("PATCH", "/api/conversations/{conversation_id}"),
        ("GET", "/api/conversations/{conversation_id}/messages"),
        ("POST", "/api/conversations/{conversation_id}/messages"),
        ("GET", "/api/documents"),
        ("POST", "/api/documents"),
        ("DELETE", "/api/documents/{document_id}"),
        ("PATCH", "/api/documents/{document_id}"),
        ("GET", "/api/documents/{document_id}/file"),
        ("GET", "/api/health"),
        ("GET", "/api/models"),
    }


def test_model_catalog_json_shape_is_unchanged() -> None:
    catalog = ModelCatalog(
        chat_models=[ModelOption(name="chat", installed=True)],
        embedding_models=[ModelOption(name="embed", installed=False)],
        default_chat_model="chat",
        default_embedding_model="embed",
        ollama_available=True,
    )

    assert ApiModelCatalog.model_validate(catalog).model_dump(by_alias=True) == {
        "chatModels": [{"name": "chat", "installed": True}],
        "embeddingModels": [{"name": "embed", "installed": False}],
        "defaultChatModel": "chat",
        "defaultEmbeddingModel": "embed",
        "ollamaAvailable": True,
    }


def test_database_table_names_are_unchanged() -> None:
    assert set(Base.metadata.tables) == {
        "conversation_messages",
        "conversations",
        "document_chunks",
        "documents",
        "ingestion_jobs",
    }


class UnavailableAnswerService:
    def answer(self, session, *, conversation_id, question):
        raise ModelProviderUnavailableError("Ollama chat request failed.")


def test_model_provider_failure_keeps_the_public_503_error() -> None:
    with pytest.raises(HTTPException) as raised:
        answer_question(
            uuid4(),
            QuestionCreate(question="Question"),
            object(),  # type: ignore[arg-type]
            UnavailableAnswerService(),  # type: ignore[arg-type]
        )

    assert raised.value.status_code == 503
    assert raised.value.detail == "Ollama chat request failed."
