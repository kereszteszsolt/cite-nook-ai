# MRA-031: Publish measured results

## Status

Implemented

## User story

As a reader, I want to see what the RAG tests found and how they ran.

## Goal

Show real results with a clear scope and no guessed scores.

## Dependencies

`MRA-029` and `MRA-030`.

## Acceptance criteria

- [x] The same fixtures and model settings are run on real native and LlamaIndex deployments one at a time.
- [x] The result record names each backend, installed model pair, test settings, date, and run outcome.
- [x] The comparison shows fixture-check counts, expected source matches, no-answer checks, and response-time values.
- [x] The guide explains that a small fixture check is not full RAG accuracy, retrieval recall, or faithfulness scoring.
- [x] The root `README.md` links to the measured comparison and keeps planned work separate from shipped features.
- [x] Release proof includes repository verification, lint, tests, build, Compose checks, and both live RAG runs.

## Out of scope

This story does not add dashboard charts, new packages, model judges, Ragas, or a new user feature.
