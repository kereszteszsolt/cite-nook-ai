# Release 0.5 verification

## Status

Release 0.5 is in progress. `MRA-018` is committed, and `MRA-019` is implemented and awaits commit approval; later stories remain planned.

## Evidence table

| Story | Implementation approval | Focused checks | Review result | Commit approval | Commit | Status |
| --- | --- | --- | --- | --- | --- | --- |
| MRA-018 | Approved 2026-08-30 | Passed | Passed | Approved 2026-08-30 | `98beb09` | Implemented |
| MRA-019 | Approved 2026-08-30 | Passed | Passed | Approved 2026-08-30 | This commit | Implemented |
| MRA-020 | Pending | Pending | Pending | Pending | — | Planned |
| MRA-021 | Pending | Pending | Pending | Pending | — | Planned |
| MRA-022 | Pending | Pending | Pending | Pending | — | Planned |
| MRA-023 | Pending | Pending | Pending | Pending | — | Planned |
| MRA-024 | Pending | Pending | Pending | Pending | — | Planned |
| MRA-025 | Pending | Pending | Pending | Pending | — | Planned |
| MRA-026 | Pending | Pending | Pending | Pending | — | Planned |
| MRA-027 | Pending | Pending | Pending | Pending | — | Planned |

## MRA-018 evidence

Implementation approval was given on 2026-08-30 when the user asked to start implementing `MRA-018`.

- `python3 .agents/skills/release-evidence/scripts/verify_repository.py` passed with 3 agents, 3 skills, and 27 stories under one strict rule set.
- The focused historical audit found 17 implemented stories with the exact section order and four to eight checked criteria each.
- The proof audit found `MRA-001` through `MRA-017` once and in order across the four historical release verification files.
- The heading audit found no issue or limitation section in any story.
- The historical release-link audit resolved 21 local Markdown targets across four release maps.
- `git diff --check` passed.
- Review found no application, runtime, dependency, Docker, or data-contract change.

Commit approval was given on 2026-08-30. Commit `98beb09` contains the implementation.

## MRA-019 evidence

Implementation approval was given on 2026-08-30 when the user asked to start `MRA-019`.

- The comment inventory reviewed 59 hand-written Python, TypeScript, TSX, JavaScript, shell, and SQL source files.
- The only retained prose notes are two one-sentence repository-script docstrings and one one-sentence TypeScript comment that explains a non-JSON error fallback.
- No comment repeats code, records old work, or stores plans, history, logs, or release proof.
- SPDX headers, `noqa`, `type: ignore`, lint, coverage, TypeScript, and Vitest directives remain excluded from prose limits.
- `python3 .agents/skills/release-evidence/scripts/test_comment_rules.py` passed all 7 focused tests, including grouped line comments, file-line errors, directives, and a mixed license/prose block.
- `python3 .agents/skills/release-evidence/scripts/verify_repository.py` passed with 3 agents, 3 skills, and 27 stories, including the source-comment audit.
- In the Node 26 container, `npm run lint` passed 3/3 tasks; `npm run test` passed 61 API, 48 web, and 1 brand test; `npm run build` passed 3/3 tasks.
- The host Node command remains unavailable under WSL1, so the documented isolated container path supplied the full gate result.
- `git diff --check` passed, and review found no application behavior, runtime, dependency, Docker, or data-contract change.

Commit approval was given on 2026-08-30. The resulting hash is reported after the commit succeeds because a commit cannot contain its own hash.

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
