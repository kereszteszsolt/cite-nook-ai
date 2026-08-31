# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from types import SimpleNamespace

import pytest
from httpx import ReadTimeout

from app.ai.contracts import ChatResult, ModelProviderUnavailableError, ModelResponseError
from app.ai.ollama import OllamaProvider


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
        return SimpleNamespace(
            message=SimpleNamespace(content='{"answer":"Grounded answer.","citations":["S1","S1"]}')
        )


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


class UnknownCitationClient(FakeClient):
    def chat(self, **request):
        return SimpleNamespace(
            message=SimpleNamespace(content='{"answer":"Grounded answer.","citations":["S9"]}')
        )


class TimeoutClient:
    def list(self):
        raise ReadTimeout("stalled")

    def embed(self, *, model: str, input):
        raise ReadTimeout("stalled")

    def chat(self, **request):
        raise ReadTimeout("stalled")


def test_provider_configures_a_finite_official_client_timeout(monkeypatch) -> None:
    captured = {}

    def build_client(*, host, timeout):
        captured.update(host=host, timeout=timeout)
        return FakeClient()

    monkeypatch.setattr("app.ai.ollama.Client", build_client)

    OllamaProvider(
        host="http://ollama.example.test:11434",
        request_timeout_seconds=45,
    )

    assert captured == {
        "host": "http://ollama.example.test:11434",
        "timeout": 45,
    }


def test_provider_rejects_a_non_positive_timeout() -> None:
    with pytest.raises(ValueError, match="timeout must be positive"):
        OllamaProvider(client=FakeClient(), request_timeout_seconds=0)


def test_list_models_normalizes_the_latest_tag() -> None:
    assert OllamaProvider(client=FakeClient()).list_models() == {
        "embeddinggemma:latest",
        "embeddinggemma",
        "llama3.1:8b",
    }


def test_provider_connection_errors_are_wrapped() -> None:
    with pytest.raises(ModelProviderUnavailableError, match="model discovery failed"):
        OllamaProvider(client=UnavailableClient()).list_models()


def test_model_discovery_timeout_is_explicit() -> None:
    with pytest.raises(ModelProviderUnavailableError, match="discovery timed out"):
        OllamaProvider(client=TimeoutClient()).list_models()


def test_embeddings_are_requested_in_one_official_client_call() -> None:
    assert OllamaProvider(client=FakeClient()).embed("embeddinggemma", ["first", "second"]) == [
        [0.1, 0.2],
        [0.1, 0.2],
    ]


def test_embedding_connection_errors_are_wrapped() -> None:
    with pytest.raises(ModelProviderUnavailableError, match="embedding request failed"):
        OllamaProvider(client=UnavailableClient()).embed("embeddinggemma", ["text"])


def test_embedding_timeout_is_explicit() -> None:
    with pytest.raises(ModelProviderUnavailableError, match="embedding request timed out"):
        OllamaProvider(client=TimeoutClient()).embed("embeddinggemma", ["text"])


def test_empty_embedding_response_is_rejected() -> None:
    with pytest.raises(ModelProviderUnavailableError, match="empty embedding response"):
        OllamaProvider(client=EmptyClient()).embed("embeddinggemma", ["text"])


def test_chat_uses_one_deterministic_official_client_call() -> None:
    client = FakeClient()
    messages = [
        {"role": "system", "content": "Use sources."},
        {"role": "user", "content": "Question and [S1]."},
    ]

    assert OllamaProvider(client=client).chat(
        "llama3.1:8b", messages, allowed_source_ids=["S1", "S2"]
    ) == ChatResult(content="Grounded answer.", source_ids=("S1",))
    assert client.chat_request == {
        "model": "llama3.1:8b",
        "messages": messages,
        "stream": False,
        "think": False,
        "format": {
            "type": "object",
            "properties": {
                "answer": {"type": "string"},
                "citations": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["S1", "S2"]},
                    "uniqueItems": True,
                },
            },
            "required": ["answer", "citations"],
            "additionalProperties": False,
        },
        "options": {"temperature": 0},
    }


def test_chat_connection_errors_are_wrapped() -> None:
    with pytest.raises(ModelProviderUnavailableError, match="chat request failed"):
        OllamaProvider(client=UnavailableClient()).chat(
            "llama3.1:8b",
            [{"role": "user", "content": "Question"}],
            allowed_source_ids=["S1"],
        )


def test_chat_timeout_is_explicit() -> None:
    with pytest.raises(ModelProviderUnavailableError, match="chat request timed out"):
        OllamaProvider(client=TimeoutClient()).chat(
            "llama3.1:8b",
            [{"role": "user", "content": "Question"}],
            allowed_source_ids=["S1"],
        )


def test_invalid_structured_chat_response_is_rejected() -> None:
    with pytest.raises(ModelResponseError, match="invalid structured chat response"):
        OllamaProvider(client=EmptyClient()).chat(
            "llama3.1:8b",
            [{"role": "user", "content": "Question"}],
            allowed_source_ids=["S1"],
        )


def test_structured_chat_rejects_a_source_outside_the_allowlist() -> None:
    with pytest.raises(ModelResponseError, match="invalid structured chat response"):
        OllamaProvider(client=UnknownCitationClient()).chat(
            "llama3.1:8b",
            [{"role": "user", "content": "Question"}],
            allowed_source_ids=["S1"],
        )
