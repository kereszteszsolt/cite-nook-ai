# Release 0.1: Minimal local RAG

## Status

Implemented. All seven stories have complete acceptance and verification evidence and follow the one-story-per-commit workflow.

## Objective

Provide the shortest complete document-to-answer workflow while keeping data local, persistent, inspectable, and easy to understand.

## Story map

| Story | Title | Status |
| --- | --- | --- |
| [MRA-001](stories/MRA-001-local-stack-and-brand.md) | Run the branded local monorepo | Implemented |
| [MRA-002](stories/MRA-002-model-selection.md) | Select and remember Ollama models | Implemented |
| [MRA-003](stories/MRA-003-persistent-upload.md) | Upload and persist supported documents | Implemented |
| [MRA-004](stories/MRA-004-worker-ingestion.md) | Index documents with a separate worker | Implemented |
| [MRA-005](stories/MRA-005-document-status.md) | Inspect and manage document status | Implemented |
| [MRA-006](stories/MRA-006-conversations.md) | Persist conversations and messages | Implemented |
| [MRA-007](stories/MRA-007-grounded-answer.md) | Answer from documents with references | Implemented |

## Verification

See the [Release 0.1 verification record](verification.md).

## Release boundary

No authentication, cloud storage, OCR, non-Ollama model provider, web crawler, reranker, hybrid search, or agent framework is included.
