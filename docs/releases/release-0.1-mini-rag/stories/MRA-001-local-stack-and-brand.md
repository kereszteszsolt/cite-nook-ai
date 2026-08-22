# MRA-001: Run the branded local monorepo

## Status

Implemented

## User story

As a local user, I want one Docker command to start the branded application and its required services so that I can use it without creating an account.

## Acceptance criteria

- [x] The repository is an npm-workspace Turborepo containing React, Python API, and brand workspaces.
- [x] The default Compose stack runs web, API, worker, and PostgreSQL/pgvector while using a configurable external Ollama instance.
- [x] An optional Compose override runs Ollama as a separate service without installing it in an application container.
- [x] PostgreSQL records, uploaded files, and optional container-managed Ollama models use named persistent volumes.
- [x] The display identity comes from one replaceable brand JSON file and matches the documented CiteNook identities.
- [x] The developer metadata is Keresztes Zsolt and https://kereszteszsolt.hu.
- [x] Hand-authored project source files keep the short Apache-2.0 SPDX header, while standard and configuration files do not receive it.

## Out of scope

Features outside the Release 0.1 boundary documented in the release README.

## Verification

Run the focused automated checks and both Compose configuration checks described in `docs/testing.md`.

## Implementation evidence

- Monorepo and runtime: `package.json`, `turbo.json`, `apps/web`, `apps/api`, `docker-compose.yml`, and `docker-compose.ollama.yml`.
- Shared identity: `packages/brand/brand.json`, consumed by both the React application and FastAPI.
- Persistence: the rendered project owns `citenook_postgres_data`, `citenook_uploads_data`, and, in container mode, `citenook_ollama_data`.
- Header policy: `.agents/skills/release-evidence/scripts/verify_repository.py` checks required source headers and rejects them in standard configuration files.

## Focused tests

- `apps/api/tests/test_brand.py` verifies the public and technical identities loaded by Python.
- `apps/api/tests/test_settings.py` verifies that an external Ollama URL is configurable.
- `packages/brand/src/index.test.ts` verifies the typed shared brand contract.
- `apps/web/src/api.test.ts` verifies that React uses its API client boundary.

## Verification evidence

Verified on 2026-08-22:

- `python3 .agents/skills/release-evidence/scripts/verify_repository.py` — passed with 3 agents, 3 skills, and 7 stories.
- `npm run lint` through Turborepo — 3/3 package tasks passed.
- `npm run test` through Turborepo — 4/4 tasks passed; 2 Python and 2 TypeScript tests passed.
- `npm run build` through Turborepo — 3/3 package tasks passed; the Vite production build completed.
- Both Compose configuration commands — passed; the base has no Ollama service and the override adds the isolated service and volume.
- External-mode Docker smoke — web, API, worker, and PostgreSQL started; `/api/health` returned `cite-nook-ai` and the branded page loaded.
- Container-mode Docker smoke — all five services started; API, PostgreSQL, and Ollama were healthy, `/api/tags` returned successfully on host port 11435, and the branded page loaded.
- After teardown, all three named volumes remained present.

## Known limitations

- No Ollama models were pulled for MRA-001; the successful container smoke returned an empty model list. Model discovery and selection belong to MRA-002.
