# MRA-024: Add persistent LlamaIndex indexing

## Status

Implemented

## User story

As an operator, I want a LlamaIndex option so I can use it when I start the app.

## Goal

Use LlamaIndex to split text, make vectors, and save nodes.

## Dependencies

`MRA-023`.

## Acceptance criteria

- [x] The LlamaIndex packages are optional, pinned, locked, and absent from the native runtime image.
- [x] The LlamaIndex indexer turns common extracted sections into page-aware LlamaIndex nodes.
- [x] A small LlamaIndex embedding bridge uses the configured `EmbeddingProvider` and model name.
- [x] A persistent PostgreSQL vector store uses a dedicated table or collection for LlamaIndex nodes.
- [x] Each node has a stable UUID and metadata for document, file name, page, order, and embedding model.
- [x] Reindex and delete work are safe to repeat and remove old nodes for the same document.
- [x] A document becomes ready only after all nodes are stored, and a failed job keeps a short error.
- [x] Focused tests cover node metadata, replacement, delete, failure cleanup, and stored node count.

## Out of scope

This story does not enable deployment choice or use a LlamaIndex query engine to write answers.
