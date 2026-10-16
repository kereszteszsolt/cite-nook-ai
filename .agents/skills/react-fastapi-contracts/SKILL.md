---
name: react-fastapi-contracts
description: Use for CiteNook changes involving React/TypeScript, FastAPI request/response schemas, HTTP client integration, or asynchronous worker status in the UI.
---

# React / FastAPI contracts

## When to use

Load only if an approved change affects `apps/web`, `apps/api/app/api`, shared request/response shapes, or worker status visible to the browser. For retrieval-only changes use `rag-pipeline` instead.

## Implementation path

1. Read the active story and the affected UI feature, `apps/web/src/api.ts`, FastAPI router/schema and application service. Avoid unrelated features.
2. Trace one request: component/state → typed API client → FastAPI schema/router → application service → persistence or worker → response.
3. Keep feature state inside its existing React feature; reuse the common API client. Preserve loading, error/retry and cancellation/polling behavior where relevant.
4. Validate external input at the FastAPI boundary. Keep business orchestration out of routers and direct persistence/adapter calls out of React.
5. Change API and UI tests together when contracts change; check worker state transitions and failure responses rather than only the happy path.

## Focused verification

Run only tests for changed components/routes first (`apps/web` Vitest, `apps/api` pytest). Add build/Compose/browser checks when the story spans those boundaries. Report actual results to the active release record; follow `AGENTS.md` for approval and commit gates.
