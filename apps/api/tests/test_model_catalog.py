# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from app.ai.contracts import ModelProviderUnavailableError
from app.application.model_catalog import ModelCatalogService
from app.core.settings import Settings


class AvailableProvider:
    def list_models(self) -> set[str]:
        return {"llama3.1:8b", "qwen3-embedding:0.6b"}


class UnavailableProvider:
    def list_models(self) -> set[str]:
        raise ModelProviderUnavailableError("offline")


def settings() -> Settings:
    return Settings(
        database_url="postgresql+psycopg://unused",
        ollama_host="http://ollama.test",
        chat_models=("llama3.1:8b", "missing-chat"),
        embedding_models=("qwen3-embedding:0.6b", "missing-embedding"),
        default_chat_model="llama3.1:8b",
        default_embedding_model="qwen3-embedding:0.6b",
        brand_config_path=Path("brand.json"),
        cors_origins=("http://localhost:5173",),
    )


def test_catalog_keeps_configured_models_and_marks_installed_ones() -> None:
    catalog = ModelCatalogService(
        provider=AvailableProvider(), settings=settings()
    ).catalog()

    assert catalog.ollama_available is True
    assert [(model.name, model.installed) for model in catalog.chat_models] == [
        ("llama3.1:8b", True),
        ("missing-chat", False),
    ]
    assert [(model.name, model.installed) for model in catalog.embedding_models] == [
        ("qwen3-embedding:0.6b", True),
        ("missing-embedding", False),
    ]


def test_catalog_remains_visible_when_ollama_is_unreachable() -> None:
    catalog = ModelCatalogService(
        provider=UnavailableProvider(), settings=settings()
    ).catalog()

    assert catalog.ollama_available is False
    assert all(not model.installed for model in catalog.chat_models)
    assert all(not model.installed for model in catalog.embedding_models)
