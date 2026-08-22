# Release 0.1: Minimal local RAG

## Status

In progress. Stories are implemented and committed one at a time; later stories remain planned until their acceptance criteria are verified.

## Objective

Provide the shortest complete document-to-answer workflow while keeping data local, persistent, inspectable, and easy to understand.

## Story map

| Story | Title | Status |
| --- | --- | --- |
| MRA-001 | Run the branded local monorepo | Implemented |
| MRA-002 | Select and remember Ollama models | Implemented |
| MRA-003 | Upload and persist supported documents | Implemented |
| MRA-004 | Index documents with a separate worker | Implemented |
| MRA-005 | Inspect and manage document status | Implemented |
| MRA-006 | Persist conversations and messages | Planned |
| MRA-007 | Answer from documents with references | Planned |

## Release boundary

No authentication, cloud storage, OCR, non-Ollama model provider, web crawler, reranker, hybrid search, or agent framework is included.
