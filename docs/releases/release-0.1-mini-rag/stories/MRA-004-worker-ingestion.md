# MRA-004: Index documents with a separate worker

## Status

Implemented

## User story

As a user, I want file jobs to run away from the web request.

## Goal

Return uploads fast. Let a worker make the search index.

## Dependencies

`MRA-003`.

## Acceptance criteria

- [x] An upload creates a PostgreSQL-backed ingestion job.
- [x] A separate worker claims jobs with FOR UPDATE SKIP LOCKED.
- [x] PDF page numbers are retained; DOCX, TXT, and Markdown text is extracted.
- [x] Text is split into deterministic overlapping chunks.
- [x] Embeddings are produced in batches with the official Ollama Python client.
- [x] Chunks, model name, page number, and pgvector embedding are persisted.
- [x] Stale processing jobs are requeued after a bounded interval.

## Out of scope

Features outside the Release 0.1 boundary documented in the release README.
