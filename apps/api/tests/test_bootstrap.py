# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Mapping, Sequence
from pathlib import Path

from app.bootstrap import build_application
from app.core.settings import Settings


class FakeModelProvider:
    def __init__(self) -> None:
        self.list_calls = 0

    def list_models(self) -> set[str]:
        self.list_calls += 1
        return {"chat-a", "embed-a"}

    def embed(
        self, model: str, inputs: str | Sequence[str]
    ) -> list[list[float]]:
        values = [inputs] if isinstance(inputs, str) else inputs
        return [[float(len(value))] for value in values]

    def chat(self, model: str, messages: Sequence[Mapping[str, str]]) -> str:
        return "Grounded answer [S1]."


def settings(tmp_path: Path) -> Settings:
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
