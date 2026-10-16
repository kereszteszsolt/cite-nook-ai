# Roadmap

## Release 0.5: clean architecture and selectable RAG backends

This release is implemented. It cleans old story records, source comments, the web structure, and the Python structure. It keeps the native RAG path and adds a LlamaIndex path behind the same app rules. Each deployment starts one backend.

See the [Release 0.5 story map and proof](releases/release-0.5-clean-rag-backends/README.md).

## Release 0.6: small RAG evaluation and CI

This release is implemented. It provides a small synthetic fixture runner through `MRA-029` and one GitHub Actions workflow through `MRA-030`. `MRA-031` records [real native and LlamaIndex measurements](releases/release-0.6-rag-evaluation-and-ci/comparison.md) dated 2026-10-14; each deployment passed twelve checks with the same installed model pair. The workflow has local proof and a successful hosted run.

The [fixture runner](rag-evaluation.md) checks expected citations, simple fixture facts, unsupported questions, and API response times. It does not claim full factual accuracy or retrieval recall from the public citations alone. Release 0.6 adds no Ragas, new RAG backend, or new product feature.

See [Release 0.6 stories](releases/release-0.6-rag-evaluation-and-ci/README.md) for the three scoped stories and [verification](releases/release-0.6-rag-evaluation-and-ci/verification.md) for checks and runtime proof. Optional later work is listed separately below.

## Release 0.7: RAG safety regression checks (planned)

`MRA-032` plans a small, separate set of synthetic prompt-injection tests for both existing RAG deployments. The tests will reuse the public API and current evaluator while leaving the Release 0.6 twelve-case fixture set and its measurements unchanged. Failed cases will be recorded as findings; this release does not promise a production guardrail or full security coverage.

See the [Release 0.7 story map](releases/release-0.7-rag-safety-checks/README.md) and [unrun verification record](releases/release-0.7-rag-safety-checks/verification.md). This work is not implemented yet.

## Later options

Possible later work includes an OpenAI-compatible model provider, hybrid search, reranking, retrieval tracing, and a citation inspector. Other options include authentication, OCR, streaming answers, agent workflows, per-conversation source sets, conversation search, and retryable ingestion. These items are not part of the completed releases or the scoped Release 0.7 plan.
