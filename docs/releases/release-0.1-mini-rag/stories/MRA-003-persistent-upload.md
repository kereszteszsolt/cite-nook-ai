# MRA-003: Upload and persist supported documents

## Status

Planned

## User story

As a user, I want to upload a document that remains available after a restart so that it can be indexed and used later.

## Acceptance criteria

- [ ] The API accepts PDF, DOCX, TXT, and Markdown multipart uploads.
- [ ] The selected embedding model is stored with the document.
- [ ] File names are reduced to a safe base name and each upload receives a UUID directory.
- [ ] Uploads are streamed with a configurable size limit and SHA-256 digest.
- [ ] The file is moved into its final persistent path before the ingestion job is committed.
- [ ] Uploaded bytes use a named Docker volume.

## Out of scope

Features outside the Release 0.1 boundary documented in the release README.

## Verification

Run the focused automated checks and the Docker smoke test described in `docs/testing.md`.
