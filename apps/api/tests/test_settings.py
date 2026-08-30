# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

import pytest

from app.core.settings import get_settings


def test_ollama_host_can_point_to_an_external_instance(monkeypatch) -> None:
    monkeypatch.setenv("OLLAMA_HOST", "http://ollama.example.test:11434")
    get_settings.cache_clear()

    assert get_settings().ollama_host == "http://ollama.example.test:11434"

    get_settings.cache_clear()


def test_default_cors_origins_support_both_loopback_hostnames(monkeypatch) -> None:
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    get_settings.cache_clear()

    assert get_settings().cors_origins == (
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    )

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


def test_upload_directory_and_size_limit_are_configurable(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path))
    monkeypatch.setenv("MAX_UPLOAD_MB", "7")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.upload_dir == tmp_path.resolve()
    assert settings.max_upload_bytes == 7 * 1024 * 1024

    get_settings.cache_clear()


def test_upload_size_limit_must_be_positive(monkeypatch) -> None:
    monkeypatch.setenv("MAX_UPLOAD_MB", "0")
    get_settings.cache_clear()

    with pytest.raises(RuntimeError, match="positive integer"):
        get_settings()

    get_settings.cache_clear()


def test_ingestion_batch_and_stale_interval_are_configurable(monkeypatch) -> None:
    monkeypatch.setenv("EMBEDDING_BATCH_SIZE", "8")
    monkeypatch.setenv("INGESTION_STALE_MINUTES", "11")
    monkeypatch.setenv("CHAT_HISTORY_MESSAGES", "7")
    monkeypatch.setenv("RAG_TOP_K", "4")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.embedding_batch_size == 8
    assert settings.ingestion_stale_minutes == 11
    assert settings.chat_history_messages == 7
    assert settings.rag_top_k == 4

    get_settings.cache_clear()
