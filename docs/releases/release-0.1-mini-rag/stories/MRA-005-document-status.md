# MRA-005: Inspect and manage document status

## Status

Implemented

## User story

As a user, I want to see when each file is ready to use.

## Goal

Show file state and errors. Let me open or delete a file.

## Dependencies

`MRA-004`.

## Acceptance criteria

- [x] The Documents section lists file name, size, embedding model, status, chunk count, and upload time.
- [x] Document status uses queued, processing, ready, or failed.
- [x] Failed processing stores and displays a bounded error message.
- [x] The web app polls only while queued or processing documents exist.
- [x] The original file can be opened from the document list.
- [x] Deleting a document removes its database rows, chunks, jobs, and stored file directory.

## Out of scope

Features outside the Release 0.1 boundary documented in the release README.
