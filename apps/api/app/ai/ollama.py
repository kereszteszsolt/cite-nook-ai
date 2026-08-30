# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Protocol

from ollama import Client

from .contracts import ModelProviderUnavailableError


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


class OllamaProvider:
    def __init__(
        self,
        host: str | None = None,
        client: OllamaClientProtocol | None = None,
    ) -> None:
        if client is None and host is None:
            raise ValueError("An Ollama host is required when no client is provided.")
        self._client = client or Client(host=host)

    def list_models(self) -> set[str]:
        try:
            response = self._client.list()
        except Exception as error:
            raise ModelProviderUnavailableError(
                "Ollama model discovery failed."
            ) from error

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
            raise ModelProviderUnavailableError(
                "Ollama embedding request failed."
            ) from error

        embeddings = [list(vector) for vector in response.embeddings]
        if not embeddings or any(not vector for vector in embeddings):
            raise ModelProviderUnavailableError(
                "Ollama returned an empty embedding response."
            )
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
            raise ModelProviderUnavailableError("Ollama chat request failed.") from error

        content = getattr(getattr(response, "message", None), "content", None)
        answer = str(content or "").strip()
        if not answer:
            raise ModelProviderUnavailableError(
                "Ollama returned an empty chat response."
            )
        return answer
