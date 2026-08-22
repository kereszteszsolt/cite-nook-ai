---
name: full-stack-delivery
description: Deliver a bounded CiteNook feature or fix across React, FastAPI, Turborepo, Docker, branding, API contracts, or persistent conversations. Use when a change crosses application layers or alters user-visible behavior.
---

# Full-stack delivery

1. Read `AGENTS.md` and the relevant `MRA-*` story.
2. Trace the user action from React to API, database/worker, and back.
3. Keep shared product identity in `packages/brand/brand.json`.
4. Keep HTTP types explicit and use one API client module in the web app.
5. Keep FastAPI routers thin; place RAG and ingestion behavior in services.
6. Preserve backend persistence and explicit delete paths.
7. Handle loading, empty, success, and failure states in the UI.
8. Add focused Python or TypeScript tests for changed behavior.
9. Run Turborepo checks and validate Compose configuration.
10. Update story status only when code and verification support it.

Do not add authentication, a frontend state library, a second queue service, or a generic provider framework without an explicit story.
