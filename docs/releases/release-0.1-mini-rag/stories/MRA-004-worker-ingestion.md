# MRA-004: Index documents with a separate worker

## Status

Planned

## User story

As a user, I want document extraction and embedding to happen outside the API request so that uploads return quickly and processing state remains visible.

## Acceptance criteria

- [ ] An upload creates a PostgreSQL-backed ingestion job.
- [ ] A separate worker claims jobs with FOR UPDATE SKIP LOCKED.
- [ ] PDF page numbers are retained; DOCX, TXT, and Markdown text is extracted.
- [ ] Text is split into deterministic overlapping chunks.
- [ ] Embeddings are produced in batches with the official Ollama Python client.
- [ ] Chunks, model name, page number, and pgvector embedding are persisted.
- [ ] Stale processing jobs are requeued after a bounded interval.

## Out of scope

Features outside the Release 0.1 boundary documented in the release README.

## Verification

Run the focused automated checks and the Docker smoke test described in `docs/testing.md`.
