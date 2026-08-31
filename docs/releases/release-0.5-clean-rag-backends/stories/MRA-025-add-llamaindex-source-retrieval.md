# MRA-025: Add LlamaIndex source retrieval

## Status

Implemented

## User story

As a user, I want LlamaIndex to find source text while the app keeps the same answer rules.

## Goal

Read saved nodes and return the same source fields as the native path.

## Dependencies

`MRA-024`.

## Acceptance criteria

- [x] The LlamaIndex retriever searches the persistent vector store through the LlamaIndex retrieval API.
- [x] Search includes only ready, active documents that use the conversation embedding model.
- [x] Node text, page data, stable UUID, document data, and score map to the common source type.
- [x] Equal scores use a stable tie order before source markers are assigned.
- [x] The common answer service builds the prompt, calls chat, checks citations, and stores the turn.
- [x] No result uses the existing insufficient-source answer and stores no citation.
- [x] Tests cover inactive, failed, missing, and model-mismatched data plus valid cited answers.
- [x] No LlamaIndex query engine, second prompt, or second message storage path is added.

## Out of scope

This story does not compare backend quality or run both retrievers for one question.
