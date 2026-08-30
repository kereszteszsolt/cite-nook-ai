# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import dataclass

from ..ai.contracts import ModelCatalogProvider, ModelProviderUnavailableError
from ..core.settings import Settings


@dataclass(frozen=True, slots=True)
class ModelOption:
    name: str
    installed: bool


@dataclass(frozen=True, slots=True)
class ModelCatalog:
    chat_models: list[ModelOption]
    embedding_models: list[ModelOption]
    default_chat_model: str
    default_embedding_model: str
    ollama_available: bool


class ModelCatalogService:
    def __init__(
        self,
        *,
        provider: ModelCatalogProvider,
        settings: Settings,
    ) -> None:
        self._provider = provider
        self._settings = settings

    def catalog(self) -> ModelCatalog:
        try:
            installed = self._provider.list_models()
            ollama_available = True
        except ModelProviderUnavailableError:
            installed = set()
            ollama_available = False

        return ModelCatalog(
            chat_models=[
                ModelOption(name=name, installed=name in installed)
                for name in self._settings.chat_models
            ],
            embedding_models=[
                ModelOption(name=name, installed=name in installed)
                for name in self._settings.embedding_models
            ],
            default_chat_model=self._settings.default_chat_model,
            default_embedding_model=self._settings.default_embedding_model,
            ollama_available=ollama_available,
        )
