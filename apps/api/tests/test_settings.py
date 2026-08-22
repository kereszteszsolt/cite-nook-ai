# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

import pytest

from app.settings import get_settings


def test_ollama_host_can_point_to_an_external_instance(monkeypatch) -> None:
    monkeypatch.setenv("OLLAMA_HOST", "http://ollama.example.test:11434")
    get_settings.cache_clear()

    assert get_settings().ollama_host == "http://ollama.example.test:11434"

    get_settings.cache_clear()


def test_model_catalog_and_defaults_are_configurable(monkeypatch) -> None:
    monkeypatch.setenv("CHAT_MODELS", "chat-a, chat-b")
    monkeypatch.setenv("EMBEDDING_MODELS", "embed-a, embed-b")
    monkeypatch.setenv("DEFAULT_CHAT_MODEL", "chat-b")
    monkeypatch.setenv("DEFAULT_EMBEDDING_MODEL", "embed-b")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.chat_models == ("chat-a", "chat-b")
    assert settings.embedding_models == ("embed-a", "embed-b")
    assert settings.default_chat_model == "chat-b"
    assert settings.default_embedding_model == "embed-b"

    get_settings.cache_clear()


def test_default_model_must_be_in_the_configured_catalog(monkeypatch) -> None:
    monkeypatch.setenv("CHAT_MODELS", "chat-a")
    monkeypatch.setenv("DEFAULT_CHAT_MODEL", "chat-b")
    get_settings.cache_clear()

    with pytest.raises(RuntimeError, match="DEFAULT_CHAT_MODEL"):
        get_settings()

    get_settings.cache_clear()
