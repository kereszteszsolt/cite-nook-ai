# MRA-003: Upload and persist supported documents

## Status

Implemented

## User story

As a user, I want my files to stay safe after a restart.

## Goal

Save each supported file for later work.

## Dependencies

`MRA-002`.

## Acceptance criteria

- [x] The API accepts PDF, DOCX, TXT, and Markdown multipart uploads.
- [x] The selected embedding model is stored with the document.
- [x] File names are reduced to a safe base name and each upload receives a UUID directory.
- [x] Uploads are streamed with a configurable size limit and SHA-256 digest.
- [x] The file is moved into its final persistent path before the ingestion job is committed.
- [x] Uploaded bytes use a named Docker volume.

## Out of scope

Features outside the Release 0.1 boundary documented in the release README.
