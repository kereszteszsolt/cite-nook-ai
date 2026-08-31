---
name: full-stack-delivery
description: Deliver one approved CiteNook story across React, FastAPI, Turborepo, Docker, branding, HTTP contracts, or persistent app data.
---

# Full-stack delivery

1. Read `AGENTS.md`, `docs/story-workflow.md`, and the active story.
2. Ask for implementation approval before editing story code.
3. Follow the acceptance criteria in order.
4. Trace the user action from React through API, worker or database, and back.
5. Keep product identity in `packages/brand/brand.json`.
6. Keep web requests behind the shared API client.
7. Keep routers thin and build concrete services in the composition root.
8. Preserve loading, empty, success, error, retry, and delete states.
9. Remove replaced live code and update focused tests.
10. Show checks, then ask for commit approval.
11. After an approved commit, report its hash and ask before the next story.

For Release 0.5 deployment work, keep native as the base Compose backend and select LlamaIndex only with `docker-compose.llamaindex.yml`. Keep the API and worker on one backend and one data project.

Use comments only when code cannot explain a hard reason; prefer one short sentence and allow at most three in a block. Keep docstrings to five short sentences, preserve required directives, and move plans, history, and proof to Markdown. Do not add a state library, a second queue, or a generic framework without an approved story.
