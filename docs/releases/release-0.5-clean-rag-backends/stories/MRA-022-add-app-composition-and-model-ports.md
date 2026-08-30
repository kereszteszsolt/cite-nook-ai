# MRA-022: Add app composition and model ports

## Status

Implemented

## User story

As a maintainer, I want app services to receive their tools so dependencies are clear and easy to test.

## Goal

Build services in one place. Keep the Ollama client out of app use cases.

## Dependencies

`MRA-021`.

## Acceptance criteria

- [x] Small `ChatProvider`, `EmbeddingProvider`, and `ModelCatalogProvider` ports define model work.
- [x] One Ollama adapter implements the model ports and is the only app module that imports the Ollama client.
- [x] One composition root reads settings and builds the shared provider and app services.
- [x] FastAPI dependencies return built services instead of routers creating them.
- [x] The worker uses the same composition root as the API.
- [x] App services do not call `get_settings()` or create a concrete model provider.
- [x] Unit tests can pass small fake providers without network access.
- [x] Current model discovery, ingestion, answer, error, and retry behavior stays the same.

## Out of scope

This story does not add a cloud provider, provider fallback, cost tracking, or model routing.
