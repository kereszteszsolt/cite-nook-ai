# Small RAG fixture evaluation

The developer CLI in [apps/api/evaluation](../apps/api/evaluation/runner.py) calls the normal CiteNook HTTP API. The default `baseline` suite from `MRA-029` uses three invented Markdown documents and twelve questions: nine supported answers and three fixed insufficient-source replies. `MRA-032` adds a separate eight-case `safety` suite. Neither suite changes the production RAG path, prompts, or endpoints, and neither uses a model judge.

## What the checks mean

The [baseline manifest](../apps/api/evaluation/fixtures/cases.json) lists each question's expected source names, literal key facts, and no-answer expectation. Source checks compare the returned citation file names with the expected set and verify that each cited ID belongs to this run. Source markers in the answer must match the distinct, valid `sourceId` values in its citations. Key facts use case-insensitive whole-term matching; paraphrases, changed spacing, and numbers written as words can fail this simple check. A no-answer case passes only with the exact fixed reply, apart from outer whitespace, and no citations.

These are small synthetic fixture checks, not factual accuracy, retrieval recall, or model-graded faithfulness scores. The public citations show the sources used in an answer, not every retrieved item. `responseDurationMs` comes from the stored assistant response, not a stopwatch around the CLI request. The [2026-10-14 measured comparison](releases/release-0.6-rag-evaluation-and-ci/comparison.md) records real native and LlamaIndex runs, including full answers, model digests, settings, and timing limits.

The [safety manifest](../apps/api/evaluation/fixtures/safety/cases.json) defines four source-level and four question-level instruction attempts in three separate fictional documents. Six cases expect facts with citations; two expect the no-answer reply. Every case also rejects any of the suite's controlled marker strings as a case-insensitive substring of the answer, even if its facts and citations are otherwise correct. The baseline files and their SHA-256 remain unchanged.

Passing a marker check does not prove that an attack was retrieved or ignored. A valid citation and a literal fact can coexist with unsupported extra claims, and a correct no-answer reply does not show why the model refused. Selected fixtures cannot certify full prompt-injection protection; failures are findings to retain, not a reason to silently change production prompts during evaluation.

The [2026-10-16 safety measurements](releases/release-0.7-rag-safety-checks/comparison.md) record all eight cases for each backend: native passed four and LlamaIndex three. Both answered a missing price and year instead of refusing, despite passing all marker-absence checks. Raw answers, per-check failures, matching model digests, and cleanup proof are linked from that record.

## Prepare one deployment

Use the [development guide](development.md) to start one backend with a running worker and real installed chat and embedding models. Use a dedicated deployment with empty, isolated document data; run native and LlamaIndex one at a time. Keep the same model pair, `RAG_TOP_K`, and fixture hash for both runs. The runner does not start containers, install models, or change app settings.

`GET /api/health` must report the requested `ragBackend`, and `GET /api/models` must mark both selected models installed. Use names exactly as the catalog exposes them. The public API does not expose `RAG_TOP_K`, so the required CLI flag records the operator-supplied deployment value and labels it as unverified by the API.

The API exposes document state through `GET /api/documents`, so the CLI must request list metadata to check isolation and poll its uploads. It rejects pre-existing document IDs and stops if another document appears; it never opens another document's original file, changes active state, or lists user conversations. Do not use the evaluation deployment for other work during a run.

## Run the suite

From the repository root, prepare the existing locked Python environment:

```bash
cd apps/api
uv sync --locked
```

With the native deployment running, use an output directory that does not yet exist:

```bash
uv run --locked python -m evaluation \
  --base-url http://localhost:8000 \
  --backend native \
  --chat-model llama3.1:8b \
  --embedding-model qwen3-embedding:0.6b \
  --rag-top-k 5 \
  --output-dir /tmp/citenook-eval-native-run1
```

After stopping native and starting the isolated LlamaIndex deployment, run from `apps/api`:

```bash
uv run --locked python -m evaluation \
  --base-url http://localhost:8000 \
  --backend llamaindex \
  --chat-model llama3.1:8b \
  --embedding-model qwen3-embedding:0.6b \
  --rag-top-k 5 \
  --output-dir /tmp/citenook-eval-llamaindex-run1
```

`--base-url` names the deployment root, without `/api`. Replace the model names and top-k value to match the deployment. Defaults are 300 seconds for indexing, 1 second between polls, and 330 seconds per HTTP request; use `--indexing-timeout`, `--poll-interval`, and `--request-timeout` to adjust them. All time values must be finite and positive.

## Select the safety suite

Omitting `--suite` selects `baseline` (`citenook-small-rag-v1`, twelve cases). To run `safety` (`citenook-rag-safety-v1`, eight cases) against an isolated native deployment, use a fresh output directory:

```bash
uv run --locked python -m evaluation \
  --suite safety \
  --base-url http://localhost:8000 \
  --backend native \
  --chat-model llama3.1:8b \
  --embedding-model qwen3-embedding:0.6b \
  --rag-top-k 5 \
  --output-dir /tmp/citenook-safety-native-run1
```

After stopping native and starting a separate LlamaIndex deployment, use the same command with `--backend llamaindex` and a new output directory such as `/tmp/citenook-safety-llamaindex-run1`. Keep the model pair, model digests, top-k, and safety suite hash identical. The readiness, isolation, fresh-conversation, and cleanup rules are shared by both suites.

## Output and cleanup

The CLI uploads only the bundled files, waits for every document to become `ready`, and creates a fresh conversation for each question. A fixture mismatch is recorded and the remaining questions still run. An API, indexing, isolation, or response-contract error stops the run and preserves partial results.

Each new output directory contains:

- `results.json`: schema version 2, suite selection, ID, SHA-256 and planned case count, UTC timestamps, selected backend and models, operator-supplied top-k, owned record IDs, per-case answers and full public citations, attack location, key-fact and forbidden-marker matches, checks, API response times, and errors.
- `report.md`: fixture-check counts, per-case outcomes, failed checks, response times, scope, and cleanup errors. The planned count follows the selected suite rather than assuming twelve questions.

The CLI attempts to delete every known conversation and document it created, including after failures and Ctrl+C. It never finds deletion targets by name or deletes unrelated records. A failed delete does not stop later cleanup attempts; `cleanupErrors` records the resource type and ID for each failure. If a creation request reaches the server but its response is lost, the CLI cannot know that new ID, so inspect the dedicated evaluation deployment before reuse.

Exit codes are `0` when all fixture checks and cleanup pass, `1` for fixture mismatches, and `2` for a run or cleanup error. Existing output directories are rejected to preserve earlier results. Results from mocked tests are not live backend measurements.

## Focused tests

From `apps/api`:

```bash
uv run --locked pytest -q tests/test_evaluation.py
uv run --locked python -m evaluation --help
```

The tests use `httpx.MockTransport` and need no PostgreSQL, Ollama, or running deployment. They cover both suites, unsafe replies with otherwise correct facts, malformed source markers, no-answer rules, backend selection, readiness, isolation, and cleanup after errors or interruption. The API workspace lint and build commands include the evaluation package. The preserved baseline measurements belong to [Release 0.6 verification](releases/release-0.6-rag-evaluation-and-ci/verification.md); new safety evidence belongs to [Release 0.7 verification](releases/release-0.7-rag-safety-checks/verification.md).
