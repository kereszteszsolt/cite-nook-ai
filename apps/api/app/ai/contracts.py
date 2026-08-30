# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Mapping, Sequence
from typing import Protocol


class ModelProviderUnavailableError(RuntimeError):
    pass


class ChatProvider(Protocol):
    def chat(self, model: str, messages: Sequence[Mapping[str, str]]) -> str: ...


class EmbeddingProvider(Protocol):
    def embed(
        self, model: str, inputs: str | Sequence[str]
    ) -> list[list[float]]: ...


class ModelCatalogProvider(Protocol):
    def list_models(self) -> set[str]: ...


class ModelProvider(ChatProvider, EmbeddingProvider, ModelCatalogProvider, Protocol):
    pass
