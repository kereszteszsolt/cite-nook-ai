# MRA-029: Add a small RAG evaluation

## Status

Planned

## User story

As a maintainer, I want to test both RAG paths with the same files and questions.

## Goal

See which path can cite good sources, say when it lacks proof, and reply in time.

## Dependencies

`MRA-028`.

## Acceptance criteria

- [ ] Three small invented documents and twelve questions define expected source files, key facts, and no-answer cases.
- [ ] One CLI runner checks `/api/health` and rejects a deployment with the wrong `ragBackend`.
- [ ] The runner checks `/api/models` for installed chat and embedding models before starting a run.
- [ ] The runner uploads only its fixtures, waits for `ready`, and asks every question through the public API.
- [ ] Each case records the answer, cited document names, fixture-check results, and `responseDurationMs`.
- [ ] The runner writes machine-readable results and a brief report without claiming retrieval recall or factual accuracy.
- [ ] The runner deletes only its own documents and conversations after each run, including failed runs.
- [ ] Focused mocked-HTTP tests cover valid answers, no-answer cases, wrong backends, pending jobs, and API errors.

## Out of scope

This story does not add Ragas, an evaluation endpoint, retrieval tracing, a new RAG path, or model-based scoring. It does not alter production answer rules.
