# MRA-021: Reorganize the Python packages

## Status

Planned

## User story

As a maintainer, I want each Python file in a clear folder so I can find and change it fast.

## Goal

Split web input, app work, model calls, RAG work, settings, and data code. Keep the app the same.

## Dependencies

`MRA-019`.

## Acceptance criteria

- [ ] HTTP routers, schemas, and request dependencies live under `app/api`.
- [ ] Use-case services and common document extraction live under `app/application`.
- [ ] Settings and brand loading live under `app/core`.
- [ ] SQLAlchemy setup and ORM models live under `app/persistence`.
- [ ] Model access lives under `app/ai`, and RAG code lives under `app/rag`.
- [ ] All imports and tests use the final package paths with no duplicate compatibility modules.
- [ ] Public HTTP routes, JSON shapes, database tables, and runtime behavior stay the same.
- [ ] The final tree has no empty layer that only forwards a call.

## Out of scope

This story does not add ports, LlamaIndex, a new database tool, or a new public API.
