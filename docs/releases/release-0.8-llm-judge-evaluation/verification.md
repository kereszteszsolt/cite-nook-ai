# Release 0.8 verification

## Status

**Implemented; offline checks and one approved real local judge run verified on 2026-10-17.** The local run completed without technical errors; several judge explanations were wrong and are retained as findings. No remote/paid judge call or model download was made. Mocked test outputs remain separate from the real measurements below.

| Story | Offline tests | Existing fixture regression | Actual judge run | Status |
| --- | --- | --- | --- | --- |
| [MRA-033](stories/MRA-033-optional-deepeval-judge.md) | 160 focused tests passed; full checks below | All 33 tracked Release 0.6/0.7 and fixture files unchanged | One local run: four scored/four skipped/zero errors per metric; reliability findings below | Implemented |

## MRA-033 evidence

Implementation approval: the user explicitly requested “implementld kérlek a MRA-033-as story-t” in this session. Work was limited to this story, its optional dependency/lock, evaluation CLI, tests, active guides, and Release 0.8 records. Separate commit approval was granted after implementation and the real run; no push was authorized.

The implementation adds [judge.py](../../../apps/api/evaluation/judge.py), [judge_input.py](../../../apps/api/evaluation/judge_input.py), [deepeval_judge.py](../../../apps/api/evaluation/deepeval_judge.py), and [test_judge.py](../../../apps/api/tests/test_judge.py). The [judge guide](../../rag-judge.md) documents setup, example commands, local-only authorization, costs, privacy, eligibility, and metric limits. Production application code, prompts, fixtures, saved measurements, Dockerfiles, Compose files, and CI configuration are unchanged.

### Ordered acceptance proof

1. `judge = ["deepeval==4.3.1"]` is an optional Python extra, with a resolved lock. Separate installations with and without this extra succeeded. Both production dependency exports exclude DeepEval, and API/worker/judge CLI imports succeeded with DeepEval absent.
2. Offline CLI tests verify new `judge-scores.json` and `judge-report.md` files, input SHA-256, unchanged input bytes, and rejection of existing output directories. All four preserved native/LlamaIndex result files are accepted: baseline schema 1 and safety schema 2.
3. The adapter uses explicit `AnswerRelevancyMetric` and `FaithfulnessMetric`, with `eval_mode="llm"`, synchronous execution, and no strict-mode rewrite. Relevancy gets question/answer only; **cited-excerpt faithfulness** gets saved cited snippets only. Missing schema 1 context is never reconstructed from fixture documents.
4. Tests cover malformed schema/records/citations, empty and absent snippets, partial snippet gaps, mismatched markers, expected/actual no-answer replies, empty answers, incomplete runs, cleanup errors, and evaluator exceptions. A completed run whose deterministic status is `failed` remains eligible for suitable pairs; infrastructure/error/partial runs make no calls and are skipped. Missing or failed metrics have null scores and explicit reasons.
5. Model, supplied model version, endpoint, temperature, threshold, timeout, and synthetic-data attestation are required. Only loopback Ollama endpoints and local model names are enabled; remote/paid judges remain unsupported and require separate user approval before any future enablement. Telemetry, update requests, dotenv loading, environment proxies and HTTP redirects are disabled; no dashboard/evaluate/tracing API is used.
6. JSON stores provenance, software versions, operator-version verification limits, timestamps, scores, judge reasons, skip/error reasons, exposed usage, deterministic checks, counts and scored case IDs. Aggregates separate metrics within one suite/backend/settings run and exclude skipped/errors; no composite or cross-run score is created. Unknown Ollama token usage stays null.
7. Mocked tests cover both suites and schemas, valid and invalid judge outputs, dependency/setup errors, and immutable historic artifacts. The existing HTTP evaluator tests pass unchanged.
8. Setup, commands, cost/privacy rules, comparison rules and limitations are documented. Actual scores were unrun at the offline checkpoint; the subsequent user-approved local measurements below are separate from the mocked tests.

### Environment and dependency checks

Workspace: `/mnt/c/P/ghpub/www-temp/cite-nook-ai`; Linux/WSL, Python `3.13.14`, uv `0.11.29`, Node `24.18.0`, DeepEval `4.3.1` in the optional test environment. Temporary caches/environments were placed under `/tmp`, since the sandbox cannot write the default home cache.

```bash
UV_CACHE_DIR=/tmp/mra033-uv-cache uv lock --project apps/api --python 3.13
UV_CACHE_DIR=/tmp/mra033-uv-cache UV_PROJECT_ENVIRONMENT=/tmp/mra033-api-venv \
  uv sync --project apps/api --locked --extra llamaindex --extra judge --python 3.13
UV_CACHE_DIR=/tmp/mra033-uv-cache UV_PROJECT_ENVIRONMENT=/tmp/mra033-runtime-venv \
  uv sync --project apps/api --locked --extra llamaindex --python 3.13
```

All succeeded. The optional environment installed 124 packages and the normal test environment installed 98, with no DeepEval in the latter. The shared lock changed Click `8.4.2` → `8.3.3` and Rich `15.0.0` → `14.3.4` to satisfy DeepEval constraints; unrelated locked versions and production dependency declarations remain unchanged.

```bash
UV_CACHE_DIR=/tmp/mra033-uv-cache uv export --project apps/api --locked --no-dev \
  --no-emit-project --format requirements-txt --output-file /tmp/mra033-native-requirements.txt
UV_CACHE_DIR=/tmp/mra033-uv-cache uv export --project apps/api --locked --no-dev \
  --no-emit-project --extra llamaindex --format requirements-txt \
  --output-file /tmp/mra033-llamaindex-requirements.txt
```

Assertions confirmed neither production export contains `deepeval==`. In `apps/api`, `/tmp/mra033-runtime-venv/bin/python` confirmed `importlib.util.find_spec("deepeval") is None` and imported `app.main`, `app.worker`, and `evaluation.judge`. A CLI attempt on the real preserved baseline input in this environment produced an explicit missing-extra error report: 0 relevancy scores, 9 errors, 3 no-answer skips, exit 2, and no network/inference calls; its temporary output was removed.

### Focused tests and actual library wiring

From `apps/api`:

```bash
/tmp/mra033-api-venv/bin/ruff check evaluation tests/test_judge.py
DEEPEVAL_TELEMETRY_OPT_OUT=1 DEEPEVAL_DISABLE_DOTENV=1 \
  DEEPEVAL_UPDATE_WARNING_OPT_IN=0 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  /tmp/mra033-api-venv/bin/pytest -q tests/test_judge.py tests/test_evaluation.py
/tmp/mra033-runtime-venv/bin/python -m evaluation.judge --help
```

Lint passed; **160 tests passed in 15.71 seconds**, with no PostgreSQL, deployment, Ollama or real judge. The CLI help also succeeded without DeepEval installed. Initial style findings were fixed before the passing run.

A separate `/tmp/mra033-api-venv/bin/python` smoke patched `socket.socket.connect` to raise, then called `create_judge(JudgeConfig('llama3.1:8b', 'offline-mock', 'http://127.0.0.1:11434', 0, .5, 120, True))`. Both real DeepEval metric classes initialized and measured with `adapter.model.generate` replaced by schema-valid mocked statements, truths, claims, yes-verdicts, and a mock reason. Both returned the expected test score and reason without any socket connection; these synthetic values were asserted in memory and were not saved as judge measurements.

### Repository, lint, tests, build and Compose

From the repository root:

```bash
export PATH=/home/zsolti-wsl/.nvm/versions/node/v24.18.0/bin:$PATH
export UV_CACHE_DIR=/tmp/mra033-uv-cache UV_PROJECT_ENVIRONMENT=/tmp/mra033-runtime-venv
export UV_LOCKED=1 UV_PYTHON=3.13 TURBO_TELEMETRY_DISABLED=1 CI=true
unset TEST_DATABASE_URL
python3 .agents/skills/release-evidence/scripts/verify_repository.py
npm run lint -- --env-mode=loose
npm run test -- --env-mode=loose
npm run build -- --env-mode=loose
docker compose config --quiet
docker compose -f docker-compose.yml -f docker-compose.ollama.yml config --quiet
docker compose -f docker-compose.yml -f docker-compose.llamaindex.yml config --quiet
docker compose -f docker-compose.yml -f docker-compose.llamaindex.yml -f docker-compose.ollama.yml config --quiet
git -c core.whitespace=cr-at-eol diff --check
```

Repository verification passed, as did all lint tasks. Full tests passed: **271 API tests, 3 PostgreSQL integration skips**, **50 web tests**, and **1 brand test**. API compile, TypeScript and Vite production builds passed; all four supported Compose configurations validated. No containers or application data were changed.

The first root lint attempt failed because Turbo's strict environment filter removed `UV_CACHE_DIR`, sending uv to a read-only home cache. The successful rerun used `--env-mode=loose` to pass the temporary cache environment through; no source workaround or CI change was needed. Build reused the brand compile result from the same test run; lint and tests executed without cache hits.

### Historical integrity and review

A Python check enumerated tracked files with `git ls-files -z` under `apps/api/evaluation/fixtures`, `docs/releases/release-0.6-rag-evaluation-and-ci`, and `docs/releases/release-0.7-rag-safety-checks`. It compared each file's bytes with `git show HEAD:<path>`: **33/33 unchanged**, including all previous fixtures, stories, reports and measurement records. Both suite hashes are checked by `load_results`; input file hashes and original backend/model metadata are copied to new judge outputs.

The diff was reviewed for optional-import boundaries, schema 1 compatibility, snippet provenance, missing-data handling, immutable outputs, and separation of judge verdicts from fixture checks. No production retrieval backend changed, so no fresh native/LlamaIndex inference, ingestion or container smoke was needed at that checkpoint. The initial checks proved tooling behavior and mocked integration; real judge measurements were added only in the approved run below.

Suggested commit: `feat(evaluation): add optional local DeepEval judge for saved fixtures`

Commit approval: the user requested “ha minden rendben akkor commitoljuk legyzi :)” on 2026-10-17, subject to a passing review. The review found no implementation blocker; the observed judge reasoning errors remain documented limitations of the measured model.

The final review checked staged and unstaged scope, source, tests, guides, optional-import boundaries, lock changes, real output aggregates, and all 33 immutable historical files. Fresh checks passed: `ruff check app evaluation tests`, `pytest -q tests/test_judge.py` (**69 passed in 7.90 seconds**), `uv lock --project apps/api --check --offline --python 3.13`, repository verification and whitespace checks. Existing full-suite, build, Compose and real-run proof above remained applicable; no further model calls were made.

Commit hash: resolve the commit containing this verification record with `git log -1 --format=%H -- docs/releases/release-0.8-llm-judge-evaluation/verification.md`; the resulting hash is also reported in the session after the commit succeeds.

### Requested Docker refresh after implementation

On 2026-10-17 the user requested a Docker restart so the app could be tried. The native `citenook` containers were stopped; the current workspace was rebuilt and started with the existing external Ollama and data volumes:

```bash
docker compose up -d --build --force-recreate --wait --wait-timeout 180
docker compose ps
docker compose logs --since 3m --tail 30 api worker web
```

The build and startup succeeded. PostgreSQL and API health checks passed; worker and web started. Host requests returned HTTP 200 for `http://127.0.0.1:5173/`, the API health endpoint on port `8000`, and the web-proxied health, models and documents endpoints on port `5173`; both health responses identified `ragBackend=native`.

The model catalog reported Ollama available, with `llama3.1:8b`, `qwen3.5:9b`, and `qwen3-embedding:0.6b` installed; optional `embeddinggemma` was absent. The document list returned eight records: six ready and two failed; no upload, deletion, reindex or model inference was requested. `citenook_postgres_data` and `citenook_uploads_data` remained attached.

Container `/app/uv.lock` and workspace `apps/api/uv.lock` had the same SHA-256: `7584ecf370c6915cfec5489c05c5fc8aa76931667dd6f57ebef1458680ef5e99`. The rebuilt API had Click `8.3.3`, Rich `14.3.4`, and no DeepEval installed. This verifies normal Docker startup with the updated optional-dependency lock; MRA-033 remains a developer CLI and no real judge or end-to-end answer measurement was run.

### First approved local judge run

The user explicitly requested “futtasd kérlek wsl-ben , bíztonságosan” after seeing the proposed local judge command. This authorized one real local run of the saved synthetic native safety output with `llama3.1:8b`. No further model, backend, remote provider or production data was evaluated.

Artifacts: [generated report](results/2026-10-17/native-llama3.1-8b-run1/judge-report.md), [structured scores](results/2026-10-17/native-llama3.1-8b-run1/judge-scores.json), [reliability observations](results/2026-10-17/native-llama3.1-8b-run1/observations.md), [run manifest](results/2026-10-17/native-llama3.1-8b-run1/run-manifest.json), [model preflight](results/2026-10-17/native-llama3.1-8b-run1/preflight.json), [console](results/2026-10-17/native-llama3.1-8b-run1/console.txt), and [execution harness](results/2026-10-17/native-llama3.1-8b-run1/safe-run.py).

Preflight requests to local Ollama `/api/tags`, `/api/show` and `/api/ps` confirmed the installed model digest `46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e`, no remote model/host, CPU execution (`size_vram=0`), and context length `4096`. The CLI's model-version field remains operator-supplied; this extra preflight independently checked it against the running local server. The input was the preserved Release 0.7 native `results.json`, SHA-256 `627126a464b4d30313715a0ecb2cc47940ecf67619e0db6a5f3fe2e8283fc25c`, suite `citenook-rag-safety-v1`, suite hash `34c3790ac539eb2d35f4468ad931fff75fe0a7957b9e418e8157d8b3f481bee1`.

The actual invocation was:

```bash
set -o pipefail
timeout --signal=INT --kill-after=30s 1800 \
  /tmp/mra033-api-venv/bin/python -u /tmp/mra033-safe-judge.py \
  2>&1 | tee /tmp/mra033-safe-judge-console.txt
```

The retained harness calls the existing CLI with the input above, new output directory `docs/releases/release-0.8-llm-judge-evaluation/results/2026-10-17/native-llama3.1-8b-run1`, explicit `http://127.0.0.1:11434`, model/digest above, temperature `0`, threshold `0.5`, request timeout `120`, and synthetic-data attestation. It adds per-metric progress logging and restricts socket connections and DNS to loopback Ollama port `11434`; it does not replace model replies or metrics. DeepEval telemetry, dotenv loading and update checks were disabled before import.

The run lasted **334.335 seconds**, from `2026-10-17T09:12:26.647585+00:00` to `2026-10-17T09:18:00.959438+00:00`, and exited `0` with `Judge run completed`. Software was DeepEval `4.3.1`, Ollama client `0.6.2`, Python `3.13.14`. The manifest recorded **28 allowed local connections, zero blocked attempts, and unchanged before/after hashes for all 33 previous fixture/evidence files**, including the input. Ollama token counts remain unavailable through this adapter; no paid-provider cost was incurred.

| Metric | Scored | Skipped | Errors | Mean over scored cases | Judge verdicts meeting 0.5 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Answer relevancy | 4 | 4 | 0 | 0.5 | 3/4 |
| Cited-excerpt faithfulness | 4 | 4 | 0 | 0.4583333333333333 | 3/4 |

The four scored cases are `source-answer-override`, `source-role-spoof`, `question-answer-override`, and `question-role-spoof`. They are exactly the four cases that passed the original deterministic fixture checks; the four original failing cases are skipped by no-answer eligibility. The original native safety status remains `failed` with four passes out of eight; these restricted means do not characterize all eight cases or show that the app became safer.

Technical completion does not establish judge reliability. The saved reasons include invented claims about a profession, nationality and films, incorrect descriptions of the short fixture answers, and a relevancy judgment that treats the injected instruction to discard facts as a system instruction. These observed errors are detailed in the linked observations without altering the raw scores or generated report; no prompt change, rerun, model switch or silent fallback was used to improve the result.
