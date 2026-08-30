# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from types import SimpleNamespace

import pytest

from app.ai.ollama import OllamaGateway, OllamaUnavailableError


class FakeClient:
    def __init__(self) -> None:
        self.chat_request = None

    def list(self):
        return SimpleNamespace(
            models=[
                SimpleNamespace(model="embeddinggemma:latest"),
                SimpleNamespace(model="llama3.1:8b"),
            ]
        )

    def embed(self, *, model: str, input):
        assert model == "embeddinggemma"
        return SimpleNamespace(embeddings=[[0.1, 0.2] for _ in input])

    def chat(self, **request):
        self.chat_request = request
        return SimpleNamespace(message=SimpleNamespace(content="Grounded answer [S1]."))


class UnavailableClient:
    def list(self):
        raise ConnectionError("not reachable")

    def embed(self, *, model: str, input):
        raise ConnectionError("not reachable")

    def chat(self, **request):
        raise ConnectionError("not reachable")


class EmptyClient(FakeClient):
    def embed(self, *, model: str, input):
        return SimpleNamespace(embeddings=[])

    def chat(self, **request):
        return SimpleNamespace(message=SimpleNamespace(content="  "))


def test_installed_models_normalize_the_latest_tag() -> None:
    assert OllamaGateway(client=FakeClient()).installed_models() == {
        "embeddinggemma:latest",
        "embeddinggemma",
        "llama3.1:8b",
    }


def test_provider_connection_errors_are_wrapped() -> None:
    with pytest.raises(OllamaUnavailableError, match="model discovery failed"):
        OllamaGateway(client=UnavailableClient()).installed_models()


def test_embeddings_are_requested_in_one_official_client_call() -> None:
    assert OllamaGateway(client=FakeClient()).embed(
        "embeddinggemma", ["first", "second"]
    ) == [[0.1, 0.2], [0.1, 0.2]]


def test_embedding_connection_errors_are_wrapped() -> None:
    with pytest.raises(OllamaUnavailableError, match="embedding request failed"):
        OllamaGateway(client=UnavailableClient()).embed("embeddinggemma", ["text"])


def test_empty_embedding_response_is_rejected() -> None:
    with pytest.raises(OllamaUnavailableError, match="empty embedding response"):
        OllamaGateway(client=EmptyClient()).embed("embeddinggemma", ["text"])


def test_chat_uses_one_deterministic_official_client_call() -> None:
    client = FakeClient()
    messages = [
        {"role": "system", "content": "Use sources."},
        {"role": "user", "content": "Question and [S1]."},
    ]

    assert OllamaGateway(client=client).chat("llama3.1:8b", messages) == (
        "Grounded answer [S1]."
    )
    assert client.chat_request == {
        "model": "llama3.1:8b",
        "messages": messages,
        "stream": False,
        "think": False,
        "options": {"temperature": 0},
    }


def test_chat_connection_errors_are_wrapped() -> None:
    with pytest.raises(OllamaUnavailableError, match="chat request failed"):
        OllamaGateway(client=UnavailableClient()).chat(
            "llama3.1:8b", [{"role": "user", "content": "Question"}]
        )


def test_empty_chat_response_is_rejected() -> None:
    with pytest.raises(OllamaUnavailableError, match="empty chat response"):
        OllamaGateway(client=EmptyClient()).chat(
            "llama3.1:8b", [{"role": "user", "content": "Question"}]
        )
