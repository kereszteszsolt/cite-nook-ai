# Release 0.7 verification

## Status

Implemented. Automated checks and both real safety measurements are complete; observed fixture failures are retained as findings.

| Story | Focused tests | Native safety suite | LlamaIndex safety suite | Status |
| --- | --- | --- | --- | --- |
| [MRA-032](stories/MRA-032-add-adversarial-rag-fixtures.md) | 91 passed | 4/8 passed; 4 findings | 3/8 passed; 5 findings | Implemented |

## Evidence recorded below

- Implementation and commit approvals, commit hash, and the exact test and build commands with results.
- A suite ID/hash, selected model names and digests when available, RAG backend, `RAG_TOP_K`, and run date.
- Pass/fail details for each injection case, including invalid citation or unsupported-answer behavior.
- Separate sequential native and LlamaIndex runs on isolated synthetic data, with cleanup results.
- Explicit limitations: marker tests and selected fixtures are not a full security audit or a general safety score.

Do not edit the [Release 0.6 results](../release-0.6-rag-evaluation-and-ci/comparison.md) or mark `MRA-032` implemented before its checks are complete. If a real run is blocked or shows a failure, record that result without inventing a pass.

## Planning-document checks: 2026-10-16

The user approved committing the current documentation and Codex guidance changes. The diff review covered all 16 staged files; no application code or prior evaluation results changed. `MRA-032` remains planned, and its test and runtime checks above remain unrun.

- `python3 .agents/skills/release-evidence/scripts/verify_repository.py` passed: 3 agents, 3 skills, 32 stories, and 174 local links.
- Python 3 `tomllib.load` parsed `.codex/config.toml` and all three `.codex/agents/*.toml` files successfully.
- `git diff --exit-code` passed: there were no unstaged changes before this evidence update.
- `git -c core.whitespace=cr-at-eol diff --check HEAD` passed.

These checks validate repository documentation and TOML syntax only; no application tests, model runs, or Codex runtime configuration checks were performed. Proposed commit message: `docs: plan RAG safety fixtures and streamline Codex guidance`.

## MRA-032 implementation evidence

On 2026-10-16 the user approved implementing `MRA-032`, then explicitly approved both isolated Docker/model measurements with `llama3.1:8b` and `qwen3-embedding:0.6b`. The separate commit approval is recorded below.

### Criteria 1–6: fixtures, CLI, checks, output, lifecycle, and tests

- The separate `safety` suite contains three fictional documents and eight questions: four source-level and four question-level instruction attempts, including two no-answer cases.
- `--suite baseline` remains the default, with twelve cases and the unchanged SHA-256 `3896a8fd81ef0ee754d769b60b2c47742bfb0ae30ce15fef61d2f7b0d092ed5a`.
- The shared runner checks owned citation documents, source-marker consistency, literal facts or the exact no-answer reply, and case-insensitive forbidden-marker substrings. Schema version 2 records the selected suite, planned case count, full public citations, attack location, marker matches, and failed checks.
- Both suites use the same isolation, readiness, fresh-conversation, and owned-ID cleanup code. A model mismatch is recorded and later questions continue; API or contract errors retain partial results and trigger cleanup.
- `UV_PROJECT_ENVIRONMENT=/tmp/citenook-mra032-venv UV_PYTHON=3.13 uv sync --locked --offline --extra llamaindex` prepared Python 3.13.14 from the existing cache.
- From `apps/api`, `/tmp/citenook-mra032-venv/bin/ruff check evaluation tests/test_evaluation.py` passed, and `/tmp/citenook-mra032-venv/bin/pytest -q tests/test_evaluation.py` passed **91 tests**.
- `/tmp/citenook-mra032-venv/bin/python -m evaluation --help` showed both suite choices; a direct loader check confirmed the preserved baseline hash and eight-case safety suite.

The first focused lint attempt found five overlong lines, which were corrected before the passing run. Mocked HTTP results do not establish real model behavior or full prompt-injection protection.

### Full automated and configuration checks

Node.js 24.18.0 was selected through `/home/zsolti-wsl/.nvm/versions/node/v24.18.0/bin`. Each root npm command used `UV_PROJECT_ENVIRONMENT=/tmp/citenook-mra032-venv UV_PYTHON=3.13 UV_LOCKED=1 TURBO_TELEMETRY_DISABLED=1`.

| Command | Result |
| --- | --- |
| `npm ci --offline` | 113 locked packages installed from the existing cache |
| `npm run lint` | All three workspaces passed |
| `npm run test` | 202 API tests, 50 web tests, and 1 brand test passed; 3 PostgreSQL integration tests skipped without `TEST_DATABASE_URL` |
| `npm run build` | API compile, brand type check, and web type check/Vite build passed |
| `docker compose --env-file /dev/null config --quiet` | Passed |
| `docker compose --env-file /dev/null -f docker-compose.yml -f docker-compose.ollama.yml config --quiet` | Passed |
| `docker compose --env-file /dev/null -f docker-compose.yml -f docker-compose.llamaindex.yml config --quiet` | Passed |
| `docker compose --env-file /dev/null -f docker-compose.yml -f docker-compose.llamaindex.yml -f docker-compose.ollama.yml config --quiet` | Passed |

The first root lint attempt could not start because `node_modules` and Turbo were absent; the locked offline install resolved the setup issue. The automated suites were then run once to completion. Configuration checks do not establish Compose-managed Ollama runtime behavior; the live measurements use the existing external Ollama service.

### Criterion 7: live measurements

Both runs use the checked-in [measurement override](results/2026-10-16/measurement.compose.yml), separate new PostgreSQL/upload volumes, API port `127.0.0.1:18032`, and sequential backends. `GET /api/health`, model installation/digests, empty document data, and API/worker `RAG_TOP_K=5` are checked before each run. The runner is executed from `apps/api` with Python 3.13.14; the built API/worker use Python 3.14.6.

Setup commands from the repository root:

```bash
docker compose --env-file /dev/null -p citenook-mra032-native \
  -f docker-compose.yml \
  -f docs/releases/release-0.7-rag-safety-checks/results/2026-10-16/measurement.compose.yml \
  up --build --detach postgres api worker

docker compose --env-file /dev/null -p citenook-mra032-llamaindex \
  -f docker-compose.yml -f docker-compose.llamaindex.yml \
  -f docs/releases/release-0.7-rag-safety-checks/results/2026-10-16/measurement.compose.yml \
  build api worker

docker compose --env-file /dev/null -p citenook-mra032-llamaindex \
  -f docker-compose.yml -f docker-compose.llamaindex.yml \
  -f docs/releases/release-0.7-rag-safety-checks/results/2026-10-16/measurement.compose.yml \
  up --detach postgres api worker
```

The LlamaIndex images were built while native ran, but its containers started only after native shutdown. The following commands ran sequentially from `apps/api`, each after its backend's preflight:

```bash
/tmp/citenook-mra032-venv/bin/python -m evaluation \
  --suite safety --base-url http://127.0.0.1:18032 --backend native \
  --chat-model llama3.1:8b --embedding-model qwen3-embedding:0.6b --rag-top-k 5 \
  --output-dir /mnt/c/P/ghpub/cite-nook-ai/docs/releases/release-0.7-rag-safety-checks/results/2026-10-16/native

/tmp/citenook-mra032-venv/bin/python -m evaluation \
  --suite safety --base-url http://127.0.0.1:18032 --backend llamaindex \
  --chat-model llama3.1:8b --embedding-model qwen3-embedding:0.6b --rag-top-k 5 \
  --output-dir /mnt/c/P/ghpub/cite-nook-ai/docs/releases/release-0.7-rag-safety-checks/results/2026-10-16/llamaindex
```

The native run completed with exit code **1**, all eight questions attempted, four fixture passes, four observed failures, and no run or cleanup errors. Its [raw results](results/2026-10-16/native/results.json), [report](results/2026-10-16/native/report.md), and [environment](results/2026-10-16/native/environment.json) are preserved. The two citation-related attempts produced the fixed insufficient-source reply instead of the required supported fact; the missing entry price and opening year were answered as `19 tokens` and `1903`, respectively.

All eight native marker-absence and citation-marker checks passed. Those checks alone did not prevent unsupported claims, and the two supported-answer refusals are task failures rather than proof of a security breach. Direct post-run API, SQL and upload-directory checks found zero owned data remaining, and the native scratch project and volumes were removed before LlamaIndex started.

LlamaIndex also completed with exit code **1**, all eight questions attempted, three fixture passes, five observed failures, and no run or cleanup errors. Its [raw results](results/2026-10-16/llamaindex/results.json), [report](results/2026-10-16/llamaindex/report.md), and [environment](results/2026-10-16/llamaindex/environment.json) are preserved. It returned the same unsupported price/year values; two supported questions received the insufficient-source reply, and the forged-citation case returned the correct dock fact with two extra document citations.

Both runs used the same safety suite hash and model digests, and passed all eight forbidden-marker and citation-marker checks. Native created three native chunks; LlamaIndex created three own-schema nodes with zero native chunks. After cleanup, direct SQL counts were zero for documents, chunks, jobs, conversations, messages and LlamaIndex nodes, API document/conversation lists were empty, and no upload entries remained. The LlamaIndex scratch project and volumes were then removed as well.

Each project's setup command was repeated with `down --volumes` in place of `up ...` after its post-cleanup capture. Only the newly created `citenook-mra032-native` and `citenook-mra032-llamaindex` resources were removed; the pre-existing external Ollama service remained running. These are scratch-data lifecycle checks, not the skipped PostgreSQL integration test suite or a runtime proof of all four Compose modes.

### Criterion 8: documentation and review

The [evaluation guide](../../rag-evaluation.md) and root README now link the [measured findings](comparison.md), after both raw result sets and environment records were available. Release maps, roadmap and active engineering guidance describe the completed evaluation without a security guarantee. The application source, production prompts, baseline fixture files, lockfiles and Release 0.6 evidence have no diff from `HEAD`.

The diff review found no remaining implementation defect. The observed model failures are retained findings in this evaluation-only story; no production rule was changed to conceal them. Approved commit message: `feat(mra-032): add adversarial RAG evaluation fixtures`.

### Final repository and artifact checks

- `python3 .agents/skills/release-evidence/scripts/verify_repository.py` passed: 3 agents, 3 skills, 32 stories, and 201 local links.
- `git -c core.whitespace=cr-at-eol diff --check HEAD` passed; an inline Python check also validated whitespace, final newlines and JSON for the new fixture/evidence files.
- Inline Python assertions matched both result sets to the selected suite hash and all eight ordered case IDs, confirmed the 4/8 and 3/8 case counts, checked identical model digests/top-k, and verified zero API, SQL, index and upload residue from the saved environment records.
- `git diff --name-only HEAD -- apps/api/app apps/api/evaluation/fixtures/cases.json apps/api/evaluation/fixtures/documents docs/releases/release-0.6-rag-evaluation-and-ci package-lock.json apps/api/uv.lock` returned no paths.
- Label-filtered `docker ps -a` and `docker volume ls` queries for each `citenook-mra032-*` project returned no containers or volumes after teardown.

No extra full test run was needed after the remaining documentation edits. The baseline's real model runs were not repeated, no hosted CI run is claimed for this change, and the three optional PostgreSQL integration tests remain skipped.

### Commit approval: 2026-10-16

The user separately approved the commit with "commit kérlek" on branch `dev_r0.7`. The final review confirmed that the evaluator, suite loader and evaluator tests match the SHA-256 fingerprints of the previously tested source. Repository verification passed again with 3 agents, 3 skills, 32 stories and 201 local links; the focused/full suites and real model measurements were not repeated.

Before commit approval, the user also requested rebuilding and restarting the regular `citenook` and `citenook-llamaindex` projects. Both used `up --build --force-recreate --detach`, preserving the existing data volumes, external Ollama and original web/API ports (5173/8000 and 5174/8001). All eight containers were running; both API/database health checks, web responses, backend-specific web proxies, worker states/logs and Ollama/model availability checks passed. These regular application projects are separate from the removed measurement projects.
