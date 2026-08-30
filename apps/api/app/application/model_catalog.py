# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import dataclass

from ..ai.ollama import OllamaGateway, OllamaUnavailableError
from ..core.settings import Settings, get_settings


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
        gateway: OllamaGateway | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._gateway = gateway or OllamaGateway()
        self._settings = settings or get_settings()

    def catalog(self) -> ModelCatalog:
        try:
            installed = self._gateway.installed_models()
            ollama_available = True
        except OllamaUnavailableError:
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
