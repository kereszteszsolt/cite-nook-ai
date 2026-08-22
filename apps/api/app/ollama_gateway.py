# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any, Protocol

from ollama import Client

from .settings import get_settings


class OllamaClientProtocol(Protocol):
    def list(self) -> Any: ...


class OllamaUnavailableError(RuntimeError):
    pass


class OllamaGateway:
    def __init__(self, client: OllamaClientProtocol | None = None) -> None:
        self._client = client or Client(host=get_settings().ollama_host)

    def installed_models(self) -> set[str]:
        try:
            response = self._client.list()
        except Exception as error:
            raise OllamaUnavailableError("Ollama model discovery failed.") from error

        names: set[str] = set()
        for model in response.models:
            name = getattr(model, "model", None) or getattr(model, "name", None)
            if not name:
                continue
            normalized = str(name)
            names.add(normalized)
            if normalized.endswith(":latest"):
                names.add(normalized.removesuffix(":latest"))
        return names
