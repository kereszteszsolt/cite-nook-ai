# MRA-026: Deploy one RAG backend

## Status

Implemented

## User story

As an admin, I want one deploy choice so the whole app uses the same RAG path.

## Goal

Use native by default. Give LlamaIndex its own command and data.

## Dependencies

`MRA-025`.

## Acceptance criteria

- [x] `RAG_BACKEND` accepts only `native` or `llamaindex`, with `native` as the default.
- [x] The native image installs no LlamaIndex package, while the LlamaIndex image installs the locked optional set.
- [x] Base Compose starts native, and one LlamaIndex override selects the other image and backend for API and worker.
- [x] The supported native and LlamaIndex Compose projects use separate PostgreSQL and upload volumes.
- [x] A database backend marker lets Release 0.4 data adopt native and stops a mismatched backend at startup.
- [x] The health response reports the selected RAG backend for deploy checks.
- [x] Native and LlamaIndex each pass external and Compose-managed Ollama configuration and smoke checks.
- [x] There is no UI switch, dual write, dual query, runtime hot switch, or silent backend fallback.

## Out of scope

This story does not migrate indexed data between backends or keep both backends live in one deployment.
