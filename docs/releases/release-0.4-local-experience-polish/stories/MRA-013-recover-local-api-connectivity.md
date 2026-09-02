# MRA-013: Recover local API connectivity

## Status

Implemented

## User story

As a local user, I want CiteNook to load from both common loopback names.

## Goal

Use one API path in the browser. Show a clear retry when it fails.

## Dependencies

`MRA-012`.

## Acceptance criteria

- [x] The supported Compose web application reaches FastAPI through a same-origin `/api` route, so both `http://localhost:5173` and `http://127.0.0.1:5173` work without browser CORS rejection.
- [x] The web proxy targets the Compose API service by default while host development retains a configurable local API target, and direct API CORS defaults include both supported loopback origins.
- [x] A successful clean-stack start with an external Ollama instance loads models, conversations, and documents and reports the installed-model connection state through either supported browser URL.
- [x] While initial data is loading, the header shows a neutral checking state; if the CiteNook API cannot be reached, it stops checking and reports API unavailability rather than claiming an Ollama result.
- [x] Browser network failures use a clear CiteNook API explanation instead of the raw `Failed to fetch` message and provide an explicit retry that reloads the initial state without requiring a page refresh.
- [x] Retrying a failed initial load clears the failure state after success and restores normal conversation and document controls without duplicating persisted data.
- [x] Automated tests cover same-origin API URL behavior, connection-error normalization, header states, failed startup, and successful retry; both Compose modes and a real browser smoke remain functional.

## Out of scope

Remote hosting, TLS termination, authentication, service-worker caching, automatic Docker startup, changing Ollama's external-by-default deployment model, and retrying grounded chat or ingestion jobs are out of scope.
