# MRA-015: Capture privacy-safe product screenshots

## Status

Implemented

## User story

As a project visitor, I want a small set of current product screenshots so that I can understand CiteNook before starting the local stack, without exposing a developer's private documents or conversations.

## Acceptance criteria

- [x] A dev-only Playwright workflow captures the real React application at deterministic desktop and mobile viewports.
- [x] Every application API request is intercepted with invented fixture data; the workflow does not read or seed PostgreSQL, uploaded files, Ollama, or the running Compose stack.
- [x] The checked gallery shows grounded chat with a citation, the document-management states, and the responsive mobile chat layout.
- [x] The root README and documentation index link to the screenshots, and the testing guide documents repeatable host and WSL-container commands.
- [x] The dependency and browser image use the same pinned Playwright version.

## Out of scope

End-to-end RAG validation, fixture persistence, a production demo mode, installing Playwright in application images, visual-regression baselines, marketing imagery, or copying any live application record is out of scope.

## Implementation evidence

- `apps/web/e2e/demo-screenshots.e2e.ts` supplies generic energy, garden, transit, and workshop data through request interception and writes four named PNG files. Its name keeps it outside Vitest's unit-test discovery pattern.
- `apps/web/playwright.screenshots.config.ts` starts a dedicated Vite server on port 4173 with deterministic locale, timezone, color scheme, viewports, and one worker.
- The root and web package scripts expose `npm run screenshots`; `@playwright/test` and the documented browser image are both pinned to `1.62.0`.
- `docs/screenshots/README.md` is the gallery and records the privacy boundary and regeneration source.

## Verification evidence

- The screenshot suite passed in `mcr.microsoft.com/playwright:v1.62.0-noble`: 1 test passed and generated all four PNG files.
- The final images are 1440×960 desktop chat, 1440×960 new-conversation dialog, 1326×526 document management, and 430×1487 mobile chat.
- Each final PNG was visually inspected after generation; the copies contain only the generic fixture names and content.
- Web lint, all web tests, the web production build, repository audit, and staged diff checks passed.
