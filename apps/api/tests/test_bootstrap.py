# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest

from app.ai.contracts import ChatResult
from app.bootstrap import build_application
from app.core.settings import Settings
from app.rag.llamaindex.indexer import LlamaIndexDocumentIndexer
from app.rag.llamaindex.retriever import LlamaIndexSourceRetriever
from app.rag.native.indexer import NativeDocumentIndexer
from app.rag.native.retriever import NativeSourceRetriever


class FakeModelProvider:
    def __init__(self) -> None:
        self.list_calls = 0

    def list_models(self) -> set[str]:
        self.list_calls += 1
        return {"chat-a", "embed-a"}

    def embed(self, model: str, inputs: str | Sequence[str]) -> list[list[float]]:
        values = [inputs] if isinstance(inputs, str) else inputs
        return [[float(len(value))] for value in values]

    def chat(
        self,
        model: str,
        messages: Sequence[Mapping[str, str]],
        *,
        allowed_source_ids: Sequence[str],
    ) -> ChatResult:
        return ChatResult(content="Grounded answer.", source_ids=("S1",))


def settings(
    tmp_path: Path,
    *,
    rag_backend: str = "native",
    ollama_request_timeout_seconds: int = 300,
) -> Settings:
    return Settings(
        database_url="postgresql+psycopg://unused",
        ollama_host="http://ollama.test",
        chat_models=("chat-a",),
        embedding_models=("embed-a",),
        default_chat_model="chat-a",
        default_embedding_model="embed-a",
        brand_config_path=Path("brand.json"),
        cors_origins=("http://localhost:5173",),
        upload_dir=tmp_path,
        rag_backend=rag_backend,
        ollama_request_timeout_seconds=ollama_request_timeout_seconds,
    )


def test_composition_root_shares_settings_and_model_provider(tmp_path: Path) -> None:
    configured_settings = settings(tmp_path)
    provider = FakeModelProvider()

    application = build_application(
        settings=configured_settings,
        model_provider=provider,
        worker_id="worker-a",
    )

    assert application.settings is configured_settings
    assert isinstance(application.document_indexer, NativeDocumentIndexer)
    assert isinstance(application.source_retriever, NativeSourceRetriever)
    assert application.conversation_service._settings is configured_settings
    assert application.answer_service._chat_provider is provider
    assert application.answer_service._retriever is application.source_retriever
    assert application.model_catalog_service._provider is provider
    assert application.ingestion_service._indexer is application.document_indexer
    assert application.document_service._indexer is application.document_indexer
    assert application.document_indexer._embedding_provider is provider
    assert application.source_retriever._embedding_provider is provider
    assert application.ingestion_service.worker_id == "worker-a"
    assert application.model_catalog_service.catalog().ollama_available is True
    assert provider.list_calls == 1


def test_composition_root_passes_the_timeout_to_ollama(monkeypatch, tmp_path: Path) -> None:
    captured = {}
    provider = FakeModelProvider()

    def build_provider(*, host, request_timeout_seconds):
        captured.update(
            host=host,
            request_timeout_seconds=request_timeout_seconds,
        )
        return provider

    monkeypatch.setattr("app.bootstrap.OllamaProvider", build_provider)

    application = build_application(settings=settings(tmp_path, ollama_request_timeout_seconds=45))

    assert application.answer_service._chat_provider is provider
    assert captured == {
        "host": "http://ollama.test",
        "request_timeout_seconds": 45,
    }


def test_composition_root_builds_only_the_llamaindex_backend(tmp_path: Path) -> None:
    application = build_application(
        settings=settings(tmp_path, rag_backend="llamaindex"),
        model_provider=FakeModelProvider(),
    )

    assert isinstance(application.document_indexer, LlamaIndexDocumentIndexer)
    assert isinstance(application.source_retriever, LlamaIndexSourceRetriever)
    assert application.answer_service._retriever is application.source_retriever
    assert application.ingestion_service._indexer is application.document_indexer
    assert application.document_service._indexer is application.document_indexer


def test_composition_root_rejects_an_unvalidated_backend(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="RAG_BACKEND must be native or llamaindex"):
        build_application(
            settings=settings(tmp_path, rag_backend="both"),
            model_provider=FakeModelProvider(),
        )
