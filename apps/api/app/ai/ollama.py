# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any, Protocol

from httpx import TimeoutException
from ollama import Client

from .contracts import ChatResult, ModelProviderUnavailableError, ModelResponseError


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
        format: Mapping[str, Any],
        options: Mapping[str, Any],
    ) -> Any: ...


class OllamaProvider:
    def __init__(
        self,
        host: str | None = None,
        client: OllamaClientProtocol | None = None,
        request_timeout_seconds: int = 300,
    ) -> None:
        if client is None and host is None:
            raise ValueError("An Ollama host is required when no client is provided.")
        if request_timeout_seconds <= 0:
            raise ValueError("The Ollama request timeout must be positive.")
        self._client = client or Client(host=host, timeout=request_timeout_seconds)

    def list_models(self) -> set[str]:
        try:
            response = self._client.list()
        except TimeoutException as error:
            raise ModelProviderUnavailableError("Ollama model discovery timed out.") from error
        except Exception as error:
            raise ModelProviderUnavailableError("Ollama model discovery failed.") from error

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
        except TimeoutException as error:
            raise ModelProviderUnavailableError("Ollama embedding request timed out.") from error
        except Exception as error:
            raise ModelProviderUnavailableError("Ollama embedding request failed.") from error

        embeddings = [list(vector) for vector in response.embeddings]
        if not embeddings or any(not vector for vector in embeddings):
            raise ModelProviderUnavailableError("Ollama returned an empty embedding response.")
        return embeddings

    def chat(
        self,
        model: str,
        messages: Sequence[Mapping[str, str]],
        *,
        allowed_source_ids: Sequence[str],
    ) -> ChatResult:
        source_ids = tuple(dict.fromkeys(allowed_source_ids))
        if not source_ids:
            raise ValueError("At least one allowed source ID is required.")
        try:
            response = self._client.chat(
                model=model,
                messages=list(messages),
                stream=False,
                think=False,
                format=grounded_chat_schema(source_ids),
                options={"temperature": 0},
            )
        except TimeoutException as error:
            raise ModelProviderUnavailableError("Ollama chat request timed out.") from error
        except Exception as error:
            raise ModelProviderUnavailableError("Ollama chat request failed.") from error

        content = getattr(getattr(response, "message", None), "content", None)
        try:
            payload = json.loads(str(content or ""))
            answer = payload["answer"].strip()
            citations = payload["citations"]
            if (
                not answer
                or not isinstance(citations, list)
                or any(not isinstance(value, str) for value in citations)
                or any(value not in source_ids for value in citations)
            ):
                raise ValueError
        except (AttributeError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            raise ModelResponseError(
                "Ollama returned an invalid structured chat response."
            ) from error
        return ChatResult(
            content=answer,
            source_ids=tuple(dict.fromkeys(citations)),
        )


def grounded_chat_schema(source_ids: Sequence[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "answer": {"type": "string"},
            "citations": {
                "type": "array",
                "items": {"type": "string", "enum": list(source_ids)},
                "uniqueItems": True,
            },
        },
        "required": ["answer", "citations"],
        "additionalProperties": False,
    }
