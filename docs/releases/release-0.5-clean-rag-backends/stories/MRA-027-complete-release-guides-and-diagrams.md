# MRA-027: Complete the release guides and diagrams

## Status

Implemented

## User story

As an operator, I want clear docs so I can start and test either RAG path.

## Goal

Make each guide match the final code. Keep Ragas work in the next release plan.

## Dependencies

`MRA-018` through `MRA-026`.

## Acceptance criteria

- [x] The root README names the default backend and shows the exact command for each backend and Ollama mode.
- [x] Architecture and RAG diagrams match the final package tree, shared flow, and one-backend rule.
- [x] Development and testing guides cover settings, images, data isolation, startup checks, and reindex needs.
- [x] The technology page lists the actual locked tools and marks optional backend packages clearly.
- [x] Story rules, Codex rules, repository skills, release maps, and verification records agree.
- [x] The roadmap keeps Ragas evaluation as Release 0.6 and uses the two real deployments.
- [x] Documentation describes the app by its product and technical purpose, and stories use no issue or limitation sections.
- [x] Repository checks, local link checks, lint, tests, builds, Compose checks, and both smoke paths pass.

## Out of scope

This story does not add Ragas, cloud model providers, hybrid search, reranking, or new product features.
