# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

import pytest

from app.application.conversations import ConversationService, UnsupportedModelError
from app.core.settings import Settings


def service() -> ConversationService:
    return ConversationService(
        Settings(
            database_url="postgresql+psycopg://unused",
            ollama_host="http://ollama.test",
            chat_models=("chat-a",),
            embedding_models=("embed-a",),
            default_chat_model="chat-a",
            default_embedding_model="embed-a",
            brand_config_path=Path("brand.json"),
            cors_origins=("http://localhost:5173",),
        )
    )


def test_rejects_chat_models_outside_the_configured_catalog() -> None:
    with pytest.raises(UnsupportedModelError, match="chat model"):
        service().create(object(), chat_model="chat-b", embedding_model="embed-a")  # type: ignore[arg-type]


def test_rejects_embedding_models_outside_the_configured_catalog() -> None:
    with pytest.raises(UnsupportedModelError, match="embedding model"):
        service().create(object(), chat_model="chat-a", embedding_model="embed-b")  # type: ignore[arg-type]
