# MRA-023: Move the native RAG path behind ports

## Status

Planned

## User story

As a maintainer, I want the old RAG code behind small ports so a new path can use the same app flow.

## Goal

Keep the native path the same. Move index and search work out of the main services.

## Dependencies

`MRA-022`.

## Acceptance criteria

- [ ] `DocumentIndexer` and `SourceRetriever` ports use backend-neutral request and result types.
- [ ] The native indexer owns current chunking, embedding batches, vector writes, replacement, and index delete work.
- [ ] The native retriever owns query embedding, ready and active filters, model matching, and pgvector order.
- [ ] The ingestion service owns job state, extraction, success, and failure work only.
- [ ] The answer service owns prompt building, chat, citation checks, timing, and message storage only.
- [ ] Document delete clears the selected index before app data and file cleanup finish.
- [ ] Source IDs, citation JSON, HTTP responses, and native scores stay compatible with Release 0.4.
- [ ] The native build has no LlamaIndex import and works with an existing Release 0.4 database.

## Out of scope

This story does not add LlamaIndex, change chunk rules, or change the user interface.
