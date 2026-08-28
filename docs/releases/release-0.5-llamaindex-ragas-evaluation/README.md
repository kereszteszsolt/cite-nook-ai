# Release 0.5 — Optional LlamaIndex and local RAG evaluation

## Status

Planned

Release 0.5 adds one deliberately bounded LlamaIndex comparison path and one reproducible Ragas evaluation harness to CiteNook. The existing direct `OllamaGateway` + SQLAlchemy/pgvector RAG pipeline remains the default, user-facing implementation and the reference behavior. The release demonstrates framework-based querying and local RAG evaluation without replacing ingestion, migrating the database, adding a frontend setting, or requiring a hosted service.

| Story | Outcome | Status |
| --- | --- | --- |
| [MRA-018](stories/MRA-018-optional-llamaindex-comparison-path.md) | Query existing CiteNook chunks through a local, developer-only LlamaIndex path | Implemented |
| [MRA-019](stories/MRA-019-local-ragas-evaluation-harness.md) | Evaluate grounded answers locally with a small reproducible Ragas dataset | Implemented |
| [MRA-020](stories/MRA-020-framework-evaluation-verification-and-presentation.md) | Verify regressions and document the two additions accurately | Planned |

## Delivery order

Implement the stories in numeric order. Keep every acceptance criterion unchecked until code, configuration, documentation, or recorded verification evidence supports it. Do not broaden the release merely to expose more LlamaIndex or Ragas features.

## Release boundary

This release is limited to portfolio-quality, developer-facing framework examples around the existing local RAG system:

- the direct CiteNook ingestion, retrieval, prompt, citation-validation, persistence, and HTTP paths remain unchanged by default;
- LlamaIndex is an explicit comparison command, not a replacement product backend or a new user-facing mode;
- the LlamaIndex path reads only existing `ready`, active, embedding-compatible chunks and must not create a second persistent vector database or rewrite CiteNook rows;
- Ragas evaluates a small committed, privacy-safe fixture through local Ollama models and stores results only as local console/CSV/JSON artifacts;
- framework dependencies remain optional so the normal API and worker images do not grow solely for evaluation tooling;
- no hosted tracing, telemetry, API keys, dashboard, agents, reranking, hybrid search, synthetic test generation, authentication, or frontend work is introduced.

## Completion conditions

Release 0.5 is complete only when the optional dependency set resolves on the repository's supported Python versions, the LlamaIndex command performs a real local query over existing CiteNook chunk data, the Ragas command produces per-case and aggregate results from a reproducible fixture, all existing product checks remain green, and the documentation states the limitations of both paths without presenting them as production replacements or statistically meaningful benchmarks.

If the pinned LlamaIndex packages cannot consume CiteNook's existing chunk metadata and embeddings safely without a database migration or duplicate persistent index, record the no-go evidence instead of changing the production schema. If the pinned Ragas release cannot run with a local Ollama judge without a hosted dependency or broad application refactor, keep the dataset and adapter boundary documented but do not force the integration.
