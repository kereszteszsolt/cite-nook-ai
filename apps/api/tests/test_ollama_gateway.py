# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from types import SimpleNamespace

import pytest

from app.ollama_gateway import OllamaGateway, OllamaUnavailableError


class FakeClient:
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


class UnavailableClient:
    def list(self):
        raise ConnectionError("not reachable")

    def embed(self, *, model: str, input):
        raise ConnectionError("not reachable")


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
