# Release 0.4 verification

These records were moved from the implemented story files by `MRA-018`. They keep the original proof and the shipped Release 0.4 facts.

## MRA-013: Recover local API connectivity

Implementation proof:

- The browser API client uses relative `/api` URLs and maps fetch plus proxy 502, 503, and 504 failures to one actionable CiteNook message.
- Vite proxies to configurable API targets, Compose defaults to `api:8000`, host work defaults to `localhost:8000`, and direct FastAPI CORS includes both loopback names.
- Startup has explicit checking, Ollama, API-failure, and retry states, and the docs describe the same supported flow.

Focused and release proof:

- Seven API settings tests, 10 API-client tests, and 37 focused header/app tests passed, including a deterministic clipboard test boundary.
- Ruff, all 61 API tests, TypeScript, all 48 web tests, the brand test, Python compileall, all builds, the repository verifier, both Compose configurations, and `git diff --check` passed.
- The external-Ollama stack started API, worker, web, and PostgreSQL and found both chat models plus the embedding model.
- Chromium loaded both `localhost:5173` and `127.0.0.1:5173` with same-origin requests and no error; after an API stop it showed `CiteNook API unavailable` and recovered on the same page after restart and retry.
- Counts stayed at 2 conversations and 8 documents during the read-only recovery check.
- Commit: `fbd3eec` (`feat(mra-013): recover local API connectivity`).

Compose ports remain bound to host loopback, and access from another device was outside this story. A custom absolute `VITE_API_URL` must match its API CORS policy.

## MRA-014: Add browser favicon identity

Implementation proof:

- `apps/web/public/favicon.svg` uses the CiteNook palette and an accessible book-and-citation mark.
- `packages/brand/brand.json` and its typed contract own the favicon path, while HTML supplies it before React and the browser entrypoint applies the shared value.
- `docs/brand-configuration.md` records the source and public path.

Focused and release proof:

- The API brand test, Ruff, the brand package test, web TypeScript, and the Vite production build passed in the Linux Node project image.
- The production build contained `dist/favicon.svg`, the browser loaded it, the repository audit passed with 14 stories, and the staged diff passed `git diff --check`.
- Commit: `126db5c` (`feat(mra-014): add branded browser favicon`).

## MRA-015: Capture privacy-safe product screenshots

Implementation proof:

- `apps/web/e2e/demo-screenshots.e2e.ts` intercepts every app API request with invented data and writes four PNG files without touching persistent app data or Ollama.
- `apps/web/playwright.screenshots.config.ts` fixes the server, locale, time zone, color scheme, viewports, and worker count.
- Root and web scripts expose `npm run screenshots`, and `@playwright/test` plus the browser image are pinned to `1.62.0`.
- `docs/screenshots/README.md` is the gallery and privacy record.

Focused and release proof:

- The suite passed in `mcr.microsoft.com/playwright:v1.62.0-noble`: 1 test generated all four PNG files.
- The outputs measured 1440×960 for desktop chat, 1440×960 for new conversation, 1326×526 for document management, and 430×1487 for mobile chat.
- Each PNG was inspected and contained only generic fixture names and content; web lint, all web tests, the web build, repository audit, and staged diff checks passed.
- Commit: `6028e34` (`docs(mra-015): add privacy-safe product screenshots`).

## MRA-016: Publish a linked user guide

Implementation proof:

- `docs/user-guide.md` follows startup, grounded answers, lifecycle actions, privacy, and troubleshooting through the implemented local flow.
- The guide links the generic `MRA-015` screenshots, while the root README and documentation index link the guide.

Focused and release proof:

- Every relative Markdown and screenshot link in the guide resolved to a tracked file.
- The repository audit passed with 16 stories, and the staged documentation diff passed `git diff --check`.
- Commit: `be477f5` (`docs(mra-016): publish linked user guide`).

## MRA-017: Document the interface design in Penpot

Implementation proof:

- `docs/design/citenook-interface-plan.svg` is the portable board based on the brand contract, React UI, and privacy-safe screenshots; its Chromium PNG and Penpot PNG are stored separately.
- Three detailed screen exports mirror the chat, document, and new-conversation captures.
- `docs/design/README.md` links both formats and records the exact Penpot target and board ID `5cc6ef41-e335-8023-8008-8692985e4d8d`.

Focused and release proof:

- Chromium rendered and visually verified the 1800×1050 SVG; the Penpot plugin created, exported, and visually verified the matching 1800×1050 board.
- Penpot also re-exported 1440×960 chat, 1326×526 documents, and 1440×960 new-conversation boards with no containment violations and byte-identical copies of the checked sources.
- The privacy-safe screenshot workflow passed with 1 test and all four images; the repository audit passed with 17 stories and `git diff --check` passed.
- In a Node 26 container, all 3 lint tasks, all 61 API tests, 48 web tests, 1 brand test, all 3 builds, and both Compose configurations passed.
- Commits: `8089450` (design handoff), `9e42b0e` (Penpot synchronization), and `98c4d6f` (detailed Penpot screens).

Penpot omitted two decorative SVG drop shadows but retained the full hierarchy, tokens, flow, design rules, and privacy boundary. The host npm wrapper did not run under WSL1, so the same repository scripts ran in the Node 26 container with the existing uv runtime.
