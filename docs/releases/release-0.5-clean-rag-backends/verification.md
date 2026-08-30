# Release 0.5 verification

## Status

Planned. Results are added only after an approved story implementation and an approved commit.

## Evidence table

| Story | Implementation approval | Focused checks | Review result | Commit approval | Commit | Status |
| --- | --- | --- | --- | --- | --- | --- |
| MRA-018 | Pending | Pending | Pending | Pending | — | Planned |
| MRA-019 | Pending | Pending | Pending | Pending | — | Planned |
| MRA-020 | Pending | Pending | Pending | Pending | — | Planned |
| MRA-021 | Pending | Pending | Pending | Pending | — | Planned |
| MRA-022 | Pending | Pending | Pending | Pending | — | Planned |
| MRA-023 | Pending | Pending | Pending | Pending | — | Planned |
| MRA-024 | Pending | Pending | Pending | Pending | — | Planned |
| MRA-025 | Pending | Pending | Pending | Pending | — | Planned |
| MRA-026 | Pending | Pending | Pending | Pending | — | Planned |
| MRA-027 | Pending | Pending | Pending | Pending | — | Planned |

## Required release checks

```bash
python3 .agents/skills/release-evidence/scripts/verify_repository.py
npm run lint
npm run test
npm run build
docker compose config
docker compose -f docker-compose.yml -f docker-compose.ollama.yml config
docker compose -f docker-compose.yml -f docker-compose.llamaindex.yml config
docker compose -f docker-compose.yml -f docker-compose.llamaindex.yml -f docker-compose.ollama.yml config
```

The two LlamaIndex Compose commands become runnable after `MRA-026`. Before that story, they remain planned checks.

## Runtime proof

The final release proof must record separate native and LlamaIndex smoke runs. Each run records the backend from `/api/health`, one completed document job, one grounded answer, valid source data, restart persistence, document cleanup, and container shutdown without deleting named volumes.

## Evidence rules

- Record exact commands and short results.
- Link large logs as files instead of pasting them into a story.
- Record the approved commit hash for each story.
- Do not mark a story implemented while a criterion is open.
- Do not add issue or limitation sections to story files.
