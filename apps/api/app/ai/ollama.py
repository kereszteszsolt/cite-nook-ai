# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Protocol

from ollama import Client

from ..core.settings import get_settings


class OllamaClientProtocol(Protocol):
    def list(self) -> Any: ...

    def embed(self, *, model: str, input: str | Sequence[str]) -> Any: ...

    def chat(
        self,
        *,
        model: str,
        messages: Sequence[Mapping[str, Any]],
        stream: bool,
        think: bool,
        options: Mapping[str, Any],
    ) -> Any: ...


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

    def embed(self, model: str, inputs: str | Sequence[str]) -> list[list[float]]:
        try:
            response = self._client.embed(model=model, input=inputs)
        except Exception as error:
            raise OllamaUnavailableError("Ollama embedding request failed.") from error

        embeddings = [list(vector) for vector in response.embeddings]
        if not embeddings or any(not vector for vector in embeddings):
            raise OllamaUnavailableError("Ollama returned an empty embedding response.")
        return embeddings

    def chat(self, model: str, messages: Sequence[Mapping[str, str]]) -> str:
        try:
            response = self._client.chat(
                model=model,
                messages=list(messages),
                stream=False,
                think=False,
                options={"temperature": 0},
            )
        except Exception as error:
            raise OllamaUnavailableError("Ollama chat request failed.") from error

        content = getattr(getattr(response, "message", None), "content", None)
        answer = str(content or "").strip()
        if not answer:
            raise OllamaUnavailableError("Ollama returned an empty chat response.")
        return answer
