# Release 0.6 verification

## Status

In progress. `MRA-029` has mocked-HTTP proof, and `MRA-030` has local workflow and full check proof dated 2026-10-14. The first hosted CI run and live RAG measurements remain pending.

## Story evidence

| Story | Implementation approval | Focused checks | Review | Commit approval | Commit | Status |
| --- | --- | --- | --- | --- | --- | --- |
| MRA-029 | Approved 2026-10-14 | Passed | Passed local review | Approved 2026-10-14 | `a94f196` | Implemented |
| MRA-030 | Approved 2026-10-14 | Local passed; hosted pending | Passed local review | Approved 2026-10-14 | `d783b47` | In progress |
| MRA-031 | Pending | Not run | Pending | Pending | Pending | Planned |

## MRA-029 evidence

The user approved implementation on 2026-10-14 with "implementáld kérlek a MRA-029 es story-t" and approved the commit on the same date. Commit `a94f196` is `feat(mra-029): add API-based RAG fixture evaluation`. This story changes the developer tooling and its guides; it does not change product endpoints, RAG behavior, dependencies, or deployment selection.

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

## MRA-030 evidence

The user approved starting the next story on 2026-10-14 after approving the `MRA-029` commit and later requested `develop` push runs too. `MRA-030` is in progress: criteria 1–5 have local proof, while criterion 6 requires a real GitHub run. Commit approval was given on 2026-10-14; publication approval remains pending. Commit `d783b47` is `ci(mra-030): run repository checks on GitHub Actions`.

Acceptance criteria were verified in order:

1. `checks.yml` is the only workflow and defines one job for pull requests and pushes to `main` and `develop`; the live remote default branch was confirmed with `git ls-remote --symref https://github.com/kereszteszsolt/cite-nook-ai.git HEAD`.
2. The job selects Node.js 24, npm 11.16.0, Python 3.13, and uv 0.11.29, then installs with `npm ci` and `uv sync --locked --extra llamaindex`; local locked installs passed without changing either lockfile.
3. Repository verification, `npm run lint`, `npm run test`, and `npm run build` passed in order through the root Turborepo commands with cache bypass enabled.
4. The final run passed 159 API, 50 web, and 1 brand test without a live database or Ollama; the 3 PostgreSQL integration tests were skipped with `TEST_DATABASE_URL` unset.
5. `actionlint` and a local Bash failure smoke check passed, the workflow has no allow-failure steps, and `docs/testing.md` lists the local equivalent commands.
6. Pending: the first hosted workflow run and its URL have not been verified.

The workflow grants read-only repository access and pins each action to a checked release commit: [checkout v7.0.1](https://github.com/actions/checkout/releases/tag/v7.0.1), [setup-node v7.1.0](https://github.com/actions/setup-node/releases/tag/v7.1.0), and [setup-uv v10.3.0](https://github.com/astral-sh/setup-uv/releases/tag/v10.3.0). The selected runtime lines are supported in the [Node release table](https://nodejs.org/en/about/previous-releases) and [Python version table](https://devguide.python.org/versions/). No product dependency or runtime path changes in this story.

Turborepo now passes `UV_LOCKED` and `UV_PYTHON` to its workspace processes and includes them in task hashes. An optional local `UV_PROJECT_ENVIRONMENT` path passes through without changing the cache key. A dry-run JSON check confirmed all three settings reach the strict-mode task plan.

The full check exposed a startup race in the existing clipboard and retry UI tests. Three tests now await the initial mocked app load inside async `act` before clicking their message actions; all existing assertions remain, including the disabled retry control and appended successful turn. The final full web suite passed all 50 tests with no product UI change.

Commands and results:

| Command or check | Result |
| --- | --- |
| `npm ci --no-audit --no-fund` | Passed; 113 packages installed from the npm lockfile |
| `UV_PYTHON=3.13 UV_LOCKED=1 UV_PROJECT_ENVIRONMENT=/tmp/citenook-mra030-venv uv sync --locked --offline --extra llamaindex` from `apps/api` | Passed; 98 installed packages, unchanged lockfile |
| `/tmp/citenook-mra030-tools/actionlint .github/workflows/checks.yml` | Passed with actionlint 1.7.12; downloaded archive checksum verified |
| `python3 .agents/skills/release-evidence/scripts/verify_repository.py` | Passed before implementation and in the full local run |
| `npm run lint` | Passed; 3 workspace tasks |
| `npm run test` | Passed; 159 API, 50 web, and 1 brand test, plus 3 expected PostgreSQL skips |
| `npm run build` | Passed; 3 workspace tasks and the 32-module web production build |
| Bash with `--noprofile --norc -eo pipefail` | A failing pipeline returned 1 and prevented the next command |
| `git diff --exit-code -- package-lock.json apps/api/uv.lock` | Passed; no dependency or lockfile changes |
| `git -c core.whitespace=cr-at-eol diff --check` | Passed |

The local full run used Node 24.18.0, the already installed npm 11.16.0, Python 3.13.14, uv 0.11.29, `CI=true`, `UV_LOCKED=1`, `UV_PYTHON=3.13`, `UV_PROJECT_ENVIRONMENT=/tmp/citenook-mra030-venv`, `TURBO_TELEMETRY_DISABLED=1`, and `TURBO_FORCE=1`. No hosted success is inferred from the local results. To verify criterion 6, publish the reviewed workflow through an approved commit and push, trigger its pull-request event or a push to `main` or `develop`, then record the actual run URL and outcome here.

## Evaluation runs

Record one real, dated run per backend after `MRA-029` is implemented. Note the selected chat and embedding models, `RAG_TOP_K`, number of answered and no-answer cases, fixture-check outcomes, source-document matches, and API-reported response times. Link the actual per-case output and note failed or missing runs instead of filling in estimates.

## CI and release checks

After `MRA-030`, record the GitHub Actions run URL and its result. For release closeout, record repository verification, lint, unit tests, build, all four Compose configuration checks, and real smoke proof for native and LlamaIndex. Keep logs concise and include commit hashes only after approval.
