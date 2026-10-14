# Release 0.6 verification

## Status

In progress. `MRA-029` has local mocked-HTTP and API regression proof dated 2026-10-14. No hosted CI runs or live RAG measurements have been performed for this release.

## Story evidence

| Story | Implementation approval | Focused checks | Review | Commit approval | Commit | Status |
| --- | --- | --- | --- | --- | --- | --- |
| MRA-029 | Approved 2026-10-14 | Passed | Passed local review | Approved 2026-10-14 | Pending | Implemented |
| MRA-030 | Pending | Not run | Pending | Pending | Pending | Planned |
| MRA-031 | Pending | Not run | Pending | Pending | Pending | Planned |

## MRA-029 evidence

The user approved implementation on 2026-10-14 with "implementáld kérlek a MRA-029 es story-t" and approved the commit on the same date. This story changes the developer tooling and its guides; it does not change product endpoints, RAG behavior, dependencies, or deployment selection.

Acceptance criteria were verified in order:

1. The fixture test passed for three invented documents, twelve unique questions, nine fact cases, three no-answer cases, and source/fact references; the suite records a SHA-256 over the manifest and files.
2. Mocked health checks passed for native and LlamaIndex, including rejection of the other backend before model discovery or data creation.
3. Model preflight checks passed for missing chat models, missing embedding models, and unavailable Ollama; successful complete runs verify both installed selections.
4. Complete mocked runs passed for both backend names; queued and processing states were polled before any question, while failed or stalled jobs stopped the run.
5. Per-case checks verified answer text, owned document IDs and cited names, whole-term fact matches, canonical no-answer replies without citations, and non-negative API `responseDurationMs` values.
6. CLI tests verified `results.json`, a short `report.md`, scope labels, suite/settings records, retained prior output, and distinct pass, fixture-failure, and run-error exit codes.
7. Cleanup tests passed after partial uploads, polling failures, conversation and answer errors, request timeouts, malformed replies, and Ctrl+C; failed deletes were reported while other deletes continued, and unrelated records were preserved.
8. The final API workspace suite passed 159 tests, including 48 evaluation tests; 3 PostgreSQL integration tests were skipped because `TEST_DATABASE_URL` was not set.

Commands and results:

| Command | Result |
| --- | --- |
| `python3 .agents/skills/release-evidence/scripts/verify_repository.py` | Passed before implementation; repeated after final documentation updates |
| `UV_PROJECT_ENVIRONMENT=/tmp/citenook-mra029-venv uv sync --locked --offline --extra llamaindex` | Passed with Python 3.13.14 and the existing uv cache; no lock change |
| `npm run lint --workspace @citenook/api` | Passed; includes `app`, `evaluation`, and `tests` |
| `npm run test --workspace @citenook/api` | 159 passed, 3 skipped |
| `npm run build --workspace @citenook/api` | Passed; compiles `app` and `evaluation` |
| `/tmp/citenook-mra029-venv/bin/python -m evaluation --help` | Passed |
| `git -c core.whitespace=cr-at-eol diff --check` | Passed |

The npm commands used Node 26.3.0, `UV_PROJECT_ENVIRONMENT=/tmp/citenook-mra029-venv`, `UV_CACHE_DIR=/tmp/citenook-mra029-uv-cache`, and `UV_NO_SYNC=1` after the locked sync. The local review checked the public HTTP field names, source ownership, isolated-data precondition, error paths, output claims, and unchanged production RAG modules. No new dependency, CI workflow, live model score, or backend comparison is claimed.

## Evaluation runs

Record one real, dated run per backend after `MRA-029` is implemented. Note the selected chat and embedding models, `RAG_TOP_K`, number of answered and no-answer cases, fixture-check outcomes, source-document matches, and API-reported response times. Link the actual per-case output and note failed or missing runs instead of filling in estimates.

## CI and release checks

After `MRA-030`, record the GitHub Actions run URL and its result. For release closeout, record repository verification, lint, unit tests, build, all four Compose configuration checks, and real smoke proof for native and LlamaIndex. Keep logs concise and include commit hashes only after approval.
