# MRA-013: Recover local API connectivity

## Status

Implemented

## User story

As a local CiteNook user, I want the application to start reliably through either common loopback hostname and explain API failures accurately so that restarting a clean Docker stack does not leave me at a misleading Ollama check or a raw browser error.

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

## Verification

Run focused web tests, full API/web/brand gates, both Compose configuration checks, and a clean browser smoke through `localhost` and `127.0.0.1` against a separately running Ollama instance. Also force the API proxy target to be unavailable, verify the error and retry states, restore it, and confirm recovery without a page refresh.

## Implementation evidence

- The browser API client defaults to a normalized relative `/api` base, including document links, and converts fetch plus proxy `502`/`503`/`504` failures into one actionable CiteNook API message.
- Vite forwards `/api` to a configurable target. Compose defaults that target to the internal `api:8000` service while host development defaults to `localhost:8000`; the supported `.env` keeps the browser URL same-origin.
- FastAPI's direct-development CORS defaults include both `localhost:5173` and `127.0.0.1:5173`.
- Initial loading now has an explicit failure state. The header distinguishes checking, connected Ollama, unavailable Ollama, and unavailable CiteNook API states; the error banner retries the complete read-only bootstrap without a page refresh.
- README, architecture, testing, Compose, and environment-example documentation describe the same-origin route, both loopback URLs, configurable proxy target, and recovery flow.

## Focused tests

- API settings tests verify the two default loopback CORS origins; all 7 settings tests passed.
- API-client tests verify every relative URL, multipart behavior, network-error normalization, and gateway-error normalization; all 10 tests passed.
- Header and application tests verify the four connection states, clear failure copy, retry, restored models/conversations/documents/history, active controls, and stable pre-existing behavior. The focused Header and App suites passed all 37 tests.
- The existing asynchronous clipboard failure test was made deterministic with an explicit React `act` boundary after the larger startup/retry suite exposed its timing race.

## Verification evidence

- API: Ruff passed; all 61 tests passed; Python byte-compilation passed.
- Web: TypeScript lint, all 48 tests, and the Vite production build passed in the Linux project image.
- Brand: TypeScript lint, its test, and build passed in the Linux project image.
- Repository and infrastructure: repository verification passed with 3 agents, 3 skills, and 13 stories; default and optional-Ollama Compose configurations passed; `git diff --check` passed.
- External-Ollama stack: the rebuilt API, worker, web, and PostgreSQL services started successfully while the independent `ollama` container remained outside the Compose project. Model discovery found both configured chat models and the configured embedding model.
- Loopback browser smoke: Chromium loaded `localhost:5173` and `127.0.0.1:5173`; models, conversations, documents, and active history stayed on each page's own origin, every request succeeded, `Ollama connected` appeared, and no error banner was present.
- Recovery browser smoke: with only the API stopped, the proxy returned 502 and the page showed `CiteNook API unavailable`, actionable copy, and **Retry connection** without raw `Failed to fetch`. After restarting the same API container, clicking retry on the unchanged page restored `Ollama connected`, cleared the alert, and enabled normal controls. Counts remained 2 conversations and 8 documents, confirming the read-only retry created no duplicate persisted data.

## Known limitations

- The base Compose ports remain bound to the host loopback interface; access from another device is not part of this story.
- The Vite proxy is the supported local transport. A custom absolute `VITE_API_URL` remains responsible for matching its deployment's API CORS configuration.
