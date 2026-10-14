# Roadmap

## Release 0.5: clean architecture and selectable RAG backends

This release is implemented. It cleans old story records, source comments, the web structure, and the Python structure. It keeps the native RAG path and adds a LlamaIndex path behind the same app rules. Each deployment starts one backend.

See the [Release 0.5 story map and proof](releases/release-0.5-clean-rag-backends/README.md).

## Release 0.6: small RAG evaluation and CI

This release is planned, not implemented. It adds a small synthetic evaluation of the two real Release 0.5 RAG deployments, one at a time, using existing HTTP endpoints. It also adds one GitHub Actions workflow for the repository's existing checks and publishes measured results only after real runs.

The suite will check expected citations, simple fixture facts, unsupported questions, and API response times. It will not claim full factual accuracy or retrieval recall from the public citations alone. No Ragas, new RAG backend, or new product feature is planned for this release.

See [Release 0.6 stories](releases/release-0.6-rag-evaluation-and-ci/README.md) for the three scoped stories and [verification](releases/release-0.6-rag-evaluation-and-ci/verification.md) for future results.

## Later options

Possible later work includes an OpenAI-compatible model provider, hybrid search, reranking, retrieval tracing, and a citation inspector. Other options include authentication, OCR, streaming answers, agent workflows, per-conversation source sets, conversation search, and retryable ingestion. These items are not part of Release 0.5 or Release 0.6.
