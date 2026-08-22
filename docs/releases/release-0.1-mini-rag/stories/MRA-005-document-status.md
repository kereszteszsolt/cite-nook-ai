# MRA-005: Inspect and manage document status

## Status

Planned

## User story

As a user, I want to see document processing status and errors so that I know when a document is ready for questions.

## Acceptance criteria

- [ ] The Documents section lists file name, size, embedding model, status, chunk count, and upload time.
- [ ] Document status uses queued, processing, ready, or failed.
- [ ] Failed processing stores and displays a bounded error message.
- [ ] The web app polls only while queued or processing documents exist.
- [ ] The original file can be opened from the document list.
- [ ] Deleting a document removes its database rows, chunks, jobs, and stored file directory.

## Out of scope

Features outside the Release 0.1 boundary documented in the release README.

## Verification

Run the focused automated checks and the Docker smoke test described in `docs/testing.md`.
