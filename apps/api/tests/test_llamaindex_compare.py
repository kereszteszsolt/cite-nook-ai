# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest

from app.evaluation.llamaindex_compare import (
    ComparisonChunk,
    ComparisonError,
    ComparisonRequest,
    ComparisonService,
    FrameworkResponse,
    FrameworkSource,
    LlamaIndexQueryAdapter,
    SqlAlchemyChunkRepository,
    build_node_payloads,
    framework_source,
)
from app.models import Document, DocumentChunk
from app.settings import Settings


def settings() -> Settings:
    return Settings(
        database_url="postgresql+psycopg://unused",
        ollama_host="http://ollama.test",
        chat_models=("chat-a",),
        embedding_models=("embed-a",),
        default_chat_model="chat-a",
        default_embedding_model="embed-a",
        brand_config_path=Path("brand.json"),
        cors_origins=("http://localhost:5173",),
        rag_top_k=2,
    )


def comparison_chunk(*, ordinal: int = 0) -> ComparisonChunk:
    return ComparisonChunk(
        document_id=uuid4(),
        document_name="guide.txt",
        page_number=ordinal + 1,
        chunk_id=uuid4(),
        chunk_ordinal=ordinal,
        content="A grounded comparison passage.",
        embedding_model="embed-a",
        embedding=(0.1, 0.2, 0.3),
    )


class FakeGateway:
    def __init__(self, installed: set[str] | None = None) -> None:
        self.installed = installed or {"chat-a", "embed-a"}

    def installed_models(self) -> set[str]:
        return self.installed


class FakeRepository:
    def __init__(self, chunks: list[ComparisonChunk]) -> None:
        self.chunks = chunks
        self.call: dict[str, Any] | None = None

    def load_eligible(self, session: Any, **values: Any) -> list[ComparisonChunk]:
        self.call = values
        return self.chunks


class FakeAdapter:
    def __init__(self) -> None:
        self.call: dict[str, Any] | None = None

    def query(self, **values: Any) -> FrameworkResponse:
        self.call = values
        node = values["nodes"][0]
        return FrameworkResponse(
            answer="The passage supports the answer.",
            sources=(
                FrameworkSource(
                    document_id=str(node.metadata["document_id"]),
                    document_name=str(node.metadata["document_name"]),
                    page_number=int(node.metadata["page_number"]),
                    chunk_id=str(node.metadata["chunk_id"]),
                    chunk_ordinal=int(node.metadata["chunk_ordinal"]),
                    embedding_model=str(node.metadata["embedding_model"]),
                    score=0.75,
                    snippet=node.text,
                ),
            ),
        )


def request(document_id: UUID | None = None, **overrides: Any) -> ComparisonRequest:
    values: dict[str, Any] = {
        "question": "  What   is supported? ",
        "chat_model": "chat-a",
        "embedding_model": "embed-a",
        "document_ids": (document_id or uuid4(),),
        "max_chunks": 20,
        "top_k": 2,
    }
    values.update(overrides)
    return ComparisonRequest(**values)


def test_node_payload_preserves_citenook_identity_and_stored_embedding() -> None:
    chunk = comparison_chunk(ordinal=3)

    payload = build_node_payloads([chunk])[0]

    assert payload.node_id == str(chunk.chunk_id)
    assert payload.text == chunk.content
    assert payload.embedding == chunk.embedding
    assert payload.metadata == {
        "document_id": str(chunk.document_id),
        "document_name": "guide.txt",
        "page_number": 4,
        "chunk_id": str(chunk.chunk_id),
        "chunk_ordinal": 3,
        "embedding_model": "embed-a",
    }


def test_service_returns_structured_framework_answer_without_session_writes() -> None:
    chunk = comparison_chunk()
    repository = FakeRepository([chunk])
    adapter = FakeAdapter()
    service = ComparisonService(
        settings=settings(),
        gateway=FakeGateway(),  # type: ignore[arg-type]
        repository=repository,
        adapter=adapter,
        clock=iter([10.0, 10.345]).__next__,
    )
    session = object()

    result = service.run(session, request(chunk.document_id))  # type: ignore[arg-type]

    assert result.status == "answered"
    assert result.question == "What is supported?"
    assert result.eligible_chunk_count == 1
    assert result.elapsed_ms == 345
    assert result.sources[0].chunk_id == str(chunk.chunk_id)
    assert result.sources[0].score == 0.75
    assert repository.call == {
        "document_ids": (chunk.document_id,),
        "embedding_model": "embed-a",
        "max_chunks": 20,
    }
    assert adapter.call is not None
    assert adapter.call["chat_model"] == "chat-a"
    assert adapter.call["embedding_model"] == "embed-a"
    assert adapter.call["ollama_host"] == "http://ollama.test"
    assert result.to_dict()["sources"][0]["document_name"] == "guide.txt"


def test_no_compatible_chunks_returns_no_data_without_calling_framework() -> None:
    repository = FakeRepository([])
    adapter = FakeAdapter()
    service = ComparisonService(
        settings=settings(),
        gateway=FakeGateway(),  # type: ignore[arg-type]
        repository=repository,
        adapter=adapter,
        clock=iter([5.0, 5.001]).__next__,
    )

    result = service.run(object(), request())  # type: ignore[arg-type]

    assert result.status == "no_data"
    assert result.eligible_chunk_count == 0
    assert result.sources == ()
    assert "No eligible CiteNook chunks" in result.answer
    assert adapter.call is None


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"question": "   "}, "question must not be empty"),
        ({"chat_model": "missing-chat"}, "not configured in CHAT_MODELS"),
        ({"embedding_model": "missing-embed"}, "not configured in EMBEDDING_MODELS"),
        ({"document_ids": ()}, "document-id is required"),
        ({"max_chunks": 1001}, "max-chunks must be between"),
        ({"top_k": 21}, "top-k must be between"),
        ({"request_timeout_seconds": 0}, "request-timeout must be positive"),
    ],
)
def test_request_validation_is_actionable(overrides: dict[str, Any], message: str) -> None:
    service = ComparisonService(
        settings=settings(),
        gateway=FakeGateway(),  # type: ignore[arg-type]
        repository=FakeRepository([]),
        adapter=FakeAdapter(),
    )

    with pytest.raises(ComparisonError, match=message):
        service.run(object(), request(**overrides))  # type: ignore[arg-type]


def test_unavailable_configured_model_is_rejected_before_query() -> None:
    service = ComparisonService(
        settings=settings(),
        gateway=FakeGateway({"chat-a"}),  # type: ignore[arg-type]
        repository=FakeRepository([]),
        adapter=FakeAdapter(),
    )

    with pytest.raises(ComparisonError, match="not installed: embed-a"):
        service.run(object(), request())  # type: ignore[arg-type]


class FakeRows:
    def __init__(self, rows: list[tuple[DocumentChunk, Document]]) -> None:
        self.rows = rows

    def all(self) -> list[tuple[DocumentChunk, Document]]:
        return self.rows


class CapturingSession:
    def __init__(self, rows: list[tuple[DocumentChunk, Document]]) -> None:
        self.rows = rows
        self.statement: Any | None = None

    def execute(self, statement: Any) -> FakeRows:
        self.statement = statement
        return FakeRows(self.rows)


def database_row() -> tuple[DocumentChunk, Document]:
    document_id = uuid4()
    document = Document(
        id=document_id,
        file_name="guide.txt",
        content_type="text/plain",
        file_path=f"/uploads/{document_id}/guide.txt",
        size_bytes=10,
        sha256="0" * 64,
        status="ready",
        chunk_count=1,
        is_active=True,
        embedding_model="embed-a",
    )
    chunk = DocumentChunk(
        id=uuid4(),
        document_id=document_id,
        ordinal=0,
        page_number=None,
        content="Stored passage.",
        embedding_model="embed-a",
        embedding=[0.1, 0.2, 0.3],
    )
    return chunk, document


def test_repository_filters_selected_ready_active_model_compatible_chunks() -> None:
    row = database_row()
    session = CapturingSession([row])

    chunks = SqlAlchemyChunkRepository().load_eligible(
        session,  # type: ignore[arg-type]
        document_ids=(row[1].id,),
        embedding_model="embed-a",
        max_chunks=10,
    )

    assert chunks[0].embedding == (0.1, 0.2, 0.3)
    assert session.statement is not None
    sql = str(session.statement)
    assert "documents.id IN" in sql
    assert "documents.status" in sql
    assert "documents.is_active IS true" in sql
    assert "documents.embedding_model" in sql
    assert "document_chunks.embedding_model" in sql
    assert "ORDER BY documents.id ASC" in sql
    values = list(session.statement.compile().params.values())
    assert "ready" in values
    assert values.count("embed-a") == 2
    assert 11 in values


def test_repository_stops_when_eligible_chunk_limit_is_exceeded() -> None:
    row = database_row()
    session = CapturingSession([row, row])

    with pytest.raises(ComparisonError, match="More than 1 eligible chunks matched"):
        SqlAlchemyChunkRepository().load_eligible(
            session,  # type: ignore[arg-type]
            document_ids=(row[1].id,),
            embedding_model="embed-a",
            max_chunks=1,
        )


class FakeNode:
    def __init__(self, metadata: dict[str, Any], text: str) -> None:
        self.metadata = metadata
        self.text = text

    def get_content(self, metadata_mode: str) -> str:
        assert metadata_mode == "none"
        return self.text


def test_framework_source_serializes_actual_metadata_score_and_text() -> None:
    chunk = comparison_chunk(ordinal=2)
    payload = build_node_payloads([chunk])[0]
    source = type(
        "Source",
        (),
        {"node": FakeNode(payload.metadata, payload.text), "score": 0.81234567},
    )()

    result = framework_source(source)

    assert result.chunk_id == str(chunk.chunk_id)
    assert result.chunk_ordinal == 2
    assert result.embedding_model == "embed-a"
    assert result.score == 0.812346
    assert result.snippet == chunk.content


def test_adapter_reports_missing_optional_dependencies(monkeypatch: pytest.MonkeyPatch) -> None:
    import builtins

    real_import = builtins.__import__

    def missing_llama_index(name: str, *args: Any, **kwargs: Any) -> Any:
        if name.startswith("llama_index"):
            raise ModuleNotFoundError(name)
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", missing_llama_index)

    with pytest.raises(ComparisonError, match="optional LlamaIndex dependencies"):
        LlamaIndexQueryAdapter().query(
            question="Question?",
            nodes=build_node_payloads([comparison_chunk()]),
            chat_model="chat-a",
            embedding_model="embed-a",
            ollama_host="http://ollama.test",
            top_k=1,
            request_timeout_seconds=10,
        )


def test_adapter_runs_real_in_memory_llamaindex_query_with_fake_models(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pytest.importorskip("llama_index.core")
    embeddings_core = pytest.importorskip("llama_index.core.embeddings")
    llms_core = pytest.importorskip("llama_index.core.llms")
    embeddings_module = pytest.importorskip("llama_index.embeddings.ollama")
    llms_module = pytest.importorskip("llama_index.llms.ollama")

    monkeypatch.setattr(
        embeddings_module,
        "OllamaEmbedding",
        lambda **_: embeddings_core.MockEmbedding(embed_dim=3),
    )
    monkeypatch.setattr(
        llms_module,
        "Ollama",
        lambda **_: llms_core.MockLLM(max_tokens=8),
    )
    chunks = [comparison_chunk(ordinal=0), comparison_chunk(ordinal=1)]

    result = LlamaIndexQueryAdapter().query(
        question="Which passage is relevant?",
        nodes=build_node_payloads(chunks),
        chat_model="chat-a",
        embedding_model="embed-a",
        ollama_host="http://ollama.test",
        top_k=1,
        request_timeout_seconds=10,
    )

    assert result.answer
    assert len(result.sources) == 1
    assert result.sources[0].chunk_id in {str(chunk.chunk_id) for chunk in chunks}
    assert result.sources[0].embedding_model == "embed-a"
    assert result.sources[0].score is not None
