# Release 0.6 verification

## Status

Implemented. `MRA-029` has mocked-HTTP proof, `MRA-030` has local checks and a successful hosted GitHub Actions run, and `MRA-031` has both live fixture runs. Release-closeout checks and documentation review passed on 2026-10-14. The user approved the `MRA-031` commit on the same date.

## Story evidence

| Story | Implementation approval | Focused checks | Review | Commit approval | Commit | Status |
| --- | --- | --- | --- | --- | --- | --- |
| MRA-029 | Approved 2026-10-14 | Passed | Passed local review | Approved 2026-10-14 | `a94f196` | Implemented |
| MRA-030 | Approved 2026-10-14 | Passed locally and on GitHub | Passed local and hosted review | Approved 2026-10-14 | `d783b47` | Implemented |
| MRA-031 | Approved 2026-10-14 | Both live runs and release checks passed | Passed local evidence and documentation review | Approved 2026-10-14 | This story commit; see Git history | Implemented |

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

The user approved starting the next story on 2026-10-14 after approving the `MRA-029` commit and later requested `develop` push runs too. Commit approval was given on 2026-10-14, and commit `d783b47` is `ci(mra-030): run repository checks on GitHub Actions`. The user then committed the verification reference as `7b16acd`, pushed `develop`, and reported the successful GitHub run. All six criteria now have proof; approval to commit this evidence update was given on 2026-10-14.

Acceptance criteria were verified in order:

1. `checks.yml` is the only workflow and defines one job for pull requests and pushes to `main` and `develop`; the live remote default branch was confirmed with `git ls-remote --symref https://github.com/kereszteszsolt/cite-nook-ai.git HEAD`.
2. The job selects Node.js 24, npm 11.16.0, Python 3.13, and uv 0.11.29, then installs with `npm ci` and `uv sync --locked --extra llamaindex`; local locked installs passed without changing either lockfile.
3. Repository verification, `npm run lint`, `npm run test`, and `npm run build` passed in order through the root Turborepo commands with cache bypass enabled.
4. The final run passed 159 API, 50 web, and 1 brand test without a live database or Ollama; the 3 PostgreSQL integration tests were skipped with `TEST_DATABASE_URL` unset.
5. `actionlint` and a local Bash failure smoke check passed, the workflow has no allow-failure steps, and `docs/testing.md` lists the local equivalent commands.
6. [Checks #1](https://github.com/kereszteszsolt/cite-nook-ai/actions/runs/38624888748) completed successfully for the `develop` push at `7b16acd`; its workflow and job results were verified through the GitHub API.

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

The local full run used Node 24.18.0, the already installed npm 11.16.0, Python 3.13.14, uv 0.11.29, `CI=true`, `UV_LOCKED=1`, `UV_PYTHON=3.13`, `UV_PROJECT_ENVIRONMENT=/tmp/citenook-mra030-venv`, `TURBO_TELEMETRY_DISABLED=1`, and `TURBO_FORCE=1`. Hosted proof comes from the separate GitHub run below, not from those local results.

### Hosted GitHub Actions run

| Field | Verified value |
| --- | --- |
| Workflow | [Checks #1](https://github.com/kereszteszsolt/cite-nook-ai/actions/runs/38624888748) |
| Job | [Repository checks](https://github.com/kereszteszsolt/cite-nook-ai/actions/runs/38624888748/job/116061413218) |
| Event and branch | `push` to `develop` |
| Head commit | `7b16acde38e80166b240d734bd47a2dff57a7aad` |
| Status and conclusion | `completed` / `success` for both workflow and job |
| Workflow start and finish | 2026-10-14 19:34:58–19:35:35 UTC; 37 seconds |
| Job start and finish | 2026-10-14 19:35:00–19:35:35 UTC; 35 seconds |

The public GitHub API confirmed successful checkout, tool setup, locked npm and uv installs, repository verification, lint, tests, build, and job cleanup. The run covers the committed workflow on `develop`; the `main` and pull-request triggers were checked in the workflow configuration, not through additional hosted runs. This CI proof does not run or score the real RAG deployments; live measurements are recorded separately under `MRA-031` below.

## MRA-031 evidence

The user approved this story on 2026-10-14 with "MRA-031" and approved its commit with "commit kérlek" on the same date. The implementation publishes measured evidence and updates active guides; application code, fixtures, dependencies, and RAG behavior are unchanged. The measurements used application and evaluator revision `d0a04f7`, before this documentation commit. The approved commit message is `docs(mra-031): publish measured RAG fixture results`; its hash is reported after Git creates the commit.

Acceptance criteria were verified in order:

1. Native ran first, followed by LlamaIndex after native was stopped; each used a new project with its own empty PostgreSQL and upload volumes, the same twelve questions, suite SHA-256, installed model digests, and top-k of 5.
2. Both [environment records](comparison.md#evidence-and-reproduction) identify the backend, model catalog, full installed model digests, API/worker settings, date, runtime versions, source fingerprint, images, ready documents, and cleanup checks.
3. The [comparison](comparison.md) reports 12/12 complete fixture checks, 9/9 supported source sets, 9/9 literal key facts, 3/3 no-answer replies, and per-case API response times for each backend; raw runner JSON and Markdown files are preserved unchanged.
4. The comparison and [run guide](../../rag-evaluation.md) explain literal-match limits, returned citations versus retrieved items, canonical no-answer checks, and the lack of full accuracy, retrieval recall, or model-graded faithfulness scoring.
5. The root [README](../../../README.md) links the measured comparison and separate later options; documentation, testing, technology, roadmap, release map, and repository guidance no longer describe these measurements as future work.
6. Repository verification, full root lint, tests, builds, all four Compose configuration checks, both real backend runs, and the final link and documentation review passed.

Both catalogs confirmed `llama3.1:8b` and `qwen3-embedding:0.6b` were installed. Direct API and worker checks confirmed the same model pair and `RAG_TOP_K=5`; the runner correctly retains its operator-supplied top-k label because that setting is absent from the public API. The host and both API images had the same application source fingerprint, recorded with full model digests in the comparison. LlamaIndex had three stored nodes and zero native chunks during its run.

Each run exited 0 with no run or cleanup errors. Follow-up API and SQL checks found no documents, conversations, messages, ingestion jobs, native chunks, uploaded files, or remaining selected LlamaIndex nodes. Both scratch projects, networks, and their newly created volumes were removed, and a Docker prefix check found no remaining measurement resources. Existing services and installed Ollama models were preserved.

An initial LlamaIndex [network preflight](results/2026-10-14/llamaindex-preflight.json) exited 2 when sandbox policy rejected `GET health`; it created no records and attempted no questions. The actual run used permitted localhost access and a fresh output directory. A startup environment capture also retried after API readiness, with its earlier model warm-up outside the measurements. No fixture or product change was made to obtain passing results.

The runs used CPU inference on a shared Docker host and shared Ollama service. Another loaded model was observed before LlamaIndex; other activity was not controlled. Native's mean API answer time was 12319.25 ms, and LlamaIndex's was 13508.75 ms, with medians of 12163.5 and 12018 ms. These one-pass timings do not establish a general backend ranking.

## Evaluation runs

| Backend | UTC interval, 2026-10-14 | Outcome | Raw results | Runner report |
| --- | --- | --- | --- | --- |
| Native | 20:17:13–20:19:45 | Passed, 12/12; 9 fact and 3 no-answer cases | [JSON](results/2026-10-14/native/results.json) | [Markdown](results/2026-10-14/native/report.md) |
| LlamaIndex | 20:22:24–20:25:10 | Passed, 12/12; 9 fact and 3 no-answer cases | [JSON](results/2026-10-14/llamaindex/results.json) | [Markdown](results/2026-10-14/llamaindex/report.md) |

See the [measured comparison](comparison.md) for the common installed pair, settings, suite hash, all timing values, environment records, reproduction commands, and limits.

## CI and release checks

Hosted CI proof is the successful `MRA-030` run linked above. The following release-closeout commands ran locally on 2026-10-14, after both live measurements had finished:

| Command or check | Result |
| --- | --- |
| `python3 .agents/skills/release-evidence/scripts/verify_repository.py` | Passed before the full checks; repeated after final documentation updates |
| `npm run lint` | Passed, all 3 workspaces, cache bypassed |
| `npm run test` | 159 API, 50 web, and 1 brand test passed; 3 PostgreSQL integration tests skipped with `TEST_DATABASE_URL` unset |
| `npm run build` | Passed, all 3 workspaces; 32-module web production build |
| `docker compose config --quiet` | Passed |
| `docker compose -f docker-compose.yml -f docker-compose.ollama.yml config --quiet` | Passed |
| `docker compose -f docker-compose.yml -f docker-compose.llamaindex.yml config --quiet` | Passed |
| `docker compose -f docker-compose.yml -f docker-compose.llamaindex.yml -f docker-compose.ollama.yml config --quiet` | Passed |
| Native and LlamaIndex locked API/worker image builds | Passed; native omits the LlamaIndex extra, LlamaIndex includes it |
| Real native and LlamaIndex fixture CLI runs | Both exited 0; 12/12 checks each, no cleanup errors |
| Artifact validation | Published runner files match the originals byte for byte; model/settings identity, sequential timestamps, case counts, source sets, and timing tables verified |
| Active documentation and version review | Local links passed; package tables match manifests and runtime records; no stale planned measurement claim or application/dependency change |
| `git -c core.whitespace=cr-at-eol diff --check` and new artifact whitespace checks | Passed |

The root checks used Node 24.18.0, npm 11.16.0, Python 3.13.14, uv 0.11.29, `CI=true`, `UV_LOCKED=1`, `UV_PYTHON=3.13`, `UV_PROJECT_ENVIRONMENT=/tmp/citenook-mra030-venv`, `TURBO_TELEMETRY_DISABLED=1`, and `TURBO_FORCE=1`. Runtime measurements used Python 3.14.6 in the application images and the same locked host environment for the HTTP runner. The four supported Compose combinations have static configuration proof here; the two live measurements used existing external Ollama, without starting a second model service.
