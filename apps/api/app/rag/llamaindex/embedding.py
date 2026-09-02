# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.bridge.pydantic import PrivateAttr

from ...ai.contracts import EmbeddingProvider


class CiteNookEmbedding(BaseEmbedding):
    _provider: EmbeddingProvider = PrivateAttr()

    def __init__(
        self,
        *,
        provider: EmbeddingProvider,
        model_name: str,
        batch_size: int,
    ) -> None:
        super().__init__(model_name=model_name, embed_batch_size=batch_size)
        self._provider = provider

    def _get_query_embedding(self, query: str) -> list[float]:
        return self._embed_one(query)

    async def _aget_query_embedding(self, query: str) -> list[float]:
        return self._embed_one(query)

    def _get_text_embedding(self, text: str) -> list[float]:
        return self._embed_one(text)

    def _get_text_embeddings(self, texts: list[str]) -> list[list[float]]:
        embeddings = self._provider.embed(self.model_name, texts)
        _validate_embeddings(embeddings, len(texts))
        return embeddings

    def _embed_one(self, value: str) -> list[float]:
        embeddings = self._provider.embed(self.model_name, value)
        _validate_embeddings(embeddings, 1)
        return embeddings[0]


def _validate_embeddings(embeddings: list[list[float]], expected_count: int) -> None:
    if len(embeddings) != expected_count:
        raise RuntimeError("The embedding model returned an unexpected number of vectors.")
    dimensions = {len(embedding) for embedding in embeddings}
    if not dimensions or 0 in dimensions or len(dimensions) != 1:
        raise RuntimeError("The embedding model returned inconsistent vector dimensions.")
