# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

import asyncio
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app import main as main_module
from app.ai.contracts import ModelProviderUnavailableError
from app.api.routers.conversations import answer_question
from app.api.routers.system import health
from app.api.schemas import ModelCatalog as ApiModelCatalog
from app.api.schemas import QuestionCreate
from app.application.model_catalog import ModelCatalog, ModelOption
from app.main import app
from app.persistence.database import Base
from app.rag.contracts import SourceRetrievalError


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


def test_database_tables_include_the_backend_marker() -> None:
    assert set(Base.metadata.tables) == {
        "app_metadata",
        "conversation_messages",
        "conversations",
        "document_chunks",
        "documents",
        "ingestion_jobs",
    }


def test_health_reports_the_selected_rag_backend() -> None:
    application = SimpleNamespace(settings=SimpleNamespace(rag_backend="llamaindex"))

    assert health(application) == {
        "status": "ok",
        "appId": "cite-nook-ai",
        "ragBackend": "llamaindex",
    }


def test_api_startup_stops_when_the_database_rejects_the_backend(monkeypatch) -> None:
    application = SimpleNamespace(settings=SimpleNamespace(rag_backend="llamaindex"))
    monkeypatch.setattr(main_module, "application", application)

    def reject_backend(backend: str) -> None:
        assert backend == "llamaindex"
        raise RuntimeError("database backend mismatch")

    monkeypatch.setattr(main_module, "init_database", reject_backend)

    async def start() -> None:
        async with main_module.lifespan(main_module.app):
            pass

    with pytest.raises(RuntimeError, match="database backend mismatch"):
        asyncio.run(start())


class UnavailableAnswerService:
    def answer(self, session, *, conversation_id, question):
        raise ModelProviderUnavailableError("Ollama chat request failed.")


class FailedRetrievalService:
    def answer(self, session, *, conversation_id, question):
        raise SourceRetrievalError(
            "The embedding model returned an unexpected number of vectors."
        )


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


def test_native_retrieval_failure_keeps_the_public_502_error() -> None:
    with pytest.raises(HTTPException) as raised:
        answer_question(
            uuid4(),
            QuestionCreate(question="Question"),
            object(),  # type: ignore[arg-type]
            FailedRetrievalService(),  # type: ignore[arg-type]
        )

    assert raised.value.status_code == 502
    assert raised.value.detail == (
        "The embedding model returned an unexpected number of vectors."
    )
