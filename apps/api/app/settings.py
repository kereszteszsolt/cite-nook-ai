# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


def _csv(name: str, default: str) -> tuple[str, ...]:
    return tuple(value.strip() for value in os.getenv(name, default).split(",") if value.strip())


@dataclass(frozen=True, slots=True)
class Settings:
    database_url: str
    ollama_host: str
    chat_models: tuple[str, ...]
    embedding_models: tuple[str, ...]
    default_chat_model: str
    default_embedding_model: str
    brand_config_path: Path
    cors_origins: tuple[str, ...]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    chat_models = _csv("CHAT_MODELS", "llama3.1:8b,qwen3.5:9b")
    embedding_models = _csv("EMBEDDING_MODELS", "qwen3-embedding:0.6b,embeddinggemma")
    if not chat_models:
        raise RuntimeError("CHAT_MODELS must contain at least one model name.")
    if not embedding_models:
        raise RuntimeError("EMBEDDING_MODELS must contain at least one model name.")

    default_chat_model = os.getenv("DEFAULT_CHAT_MODEL", chat_models[0])
    default_embedding_model = os.getenv("DEFAULT_EMBEDDING_MODEL", embedding_models[0])
    if default_chat_model not in chat_models:
        raise RuntimeError("DEFAULT_CHAT_MODEL must be included in CHAT_MODELS.")
    if default_embedding_model not in embedding_models:
        raise RuntimeError("DEFAULT_EMBEDDING_MODEL must be included in EMBEDDING_MODELS.")

    return Settings(
        database_url=os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg://cite_nook:checked-in-development-only@localhost:5432/cite_nook",
        ),
        ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        chat_models=chat_models,
        embedding_models=embedding_models,
        default_chat_model=default_chat_model,
        default_embedding_model=default_embedding_model,
        brand_config_path=Path(
            os.getenv("BRAND_CONFIG_PATH", "../../packages/brand/brand.json")
        ).resolve(),
        cors_origins=_csv("CORS_ORIGINS", "http://localhost:5173"),
    )
