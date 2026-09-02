# MRA-007: Answer from documents with references

## Status

Implemented

## User story

As a user, I want each answer to cite the files that support it.

## Goal

Use ready file text to answer. Show the source for each claim.

## Dependencies

`MRA-004`, `MRA-005`, and `MRA-006`.

## Acceptance criteria

- [x] The question is embedded with the conversation embedding model.
- [x] Retrieval searches only ready chunks created with the same embedding model.
- [x] The top passages are numbered deterministically as S1, S2, and so on.
- [x] The chat prompt requires source-only answering, source markers, and explicit insufficiency when needed.
- [x] The answer is generated with the conversation chat model through the official Ollama Python client.
- [x] The API returns structured document, page, chunk, snippet, and score citations.
- [x] The web app displays references under the assistant answer and links to the original document.

## Out of scope

Features outside the Release 0.1 boundary documented in the release README.
