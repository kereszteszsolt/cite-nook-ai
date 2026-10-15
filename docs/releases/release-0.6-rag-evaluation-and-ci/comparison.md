# Measured RAG fixture comparison

On 2026-10-14, native and LlamaIndex each passed all twelve checks in `citenook-small-rag-v1`. Both used the same installed models and three invented documents, in separate deployments run one at a time. These results cover this small fixture set only; they do not establish a general quality or speed winner.

## Results

| Check | Native | LlamaIndex |
| --- | ---: | ---: |
| Ready documents | 3/3 | 3/3 |
| Questions attempted | 12/12 | 12/12 |
| Complete fixture checks passed | 12/12 | 12/12 |
| Expected source sets, all questions | 12/12 | 12/12 |
| Expected source sets, supported questions | 9/9 | 9/9 |
| Literal key facts | 9/9 | 9/9 |
| Canonical no-answer reply with no citations | 3/3 | 3/3 |
| Run errors / cleanup errors | 0 / 0 | 0 / 0 |
| CLI exit code | 0 | 0 |

The all-question source count includes three expected empty citation sets. Each supported question cited its expected document, and each unsupported question returned the fixed insufficient-source reply without citations. Every document had one index item; LlamaIndex stored three nodes in its own schema and wrote no native chunks.

## Response times

Values below are the API's stored `responseDurationMs`, in milliseconds. They cover retrieval, chat, and common answer checks, ending before the turn is stored. They exclude upload, indexing, warm-up, client network time, and cleanup.

| Statistic across twelve answers | Native (ms) | LlamaIndex (ms) |
| --- | ---: | ---: |
| Minimum | 11131 | 10819 |
| Median | 12163.5 | 12018 |
| Mean | 12319.25 | 13508.75 |
| Maximum | 14473 | 19731 |

| Case | Native (ms) | LlamaIndex (ms) | Fixture check, both |
| --- | ---: | ---: | --- |
| amber-leader | 14473 | 10819 | pass |
| amber-lens | 11648 | 11133 | pass |
| amber-badge | 11355 | 15369 | pass |
| birch-manager | 13863 | 17470 | pass |
| birch-varieties | 12490 | 19731 | pass |
| birch-room | 12461 | 17893 | pass |
| copper-departure | 11866 | 11926 | pass |
| copper-capacity | 11207 | 11064 | pass |
| copper-destination | 11131 | 10984 | pass |
| amber-price-unknown | 12770 | 12191 | pass |
| birch-latitude-unknown | 11805 | 11415 | pass |
| copper-ticket-unknown | 12762 | 12110 | pass |

This is one pass per backend on a shared CPU host and shared Ollama service, with native first. Other host activity was not controlled, and another loaded model was observed before LlamaIndex. The overlapping times and single samples per question do not support a general performance ranking.

## Run record

| Setting | Recorded value |
| --- | --- |
| Date | 2026-10-14, UTC |
| Native start / finish | 20:17:13 / 20:19:45 UTC |
| LlamaIndex start / finish | 20:22:24 / 20:25:10 UTC |
| Application and evaluator revision | `d0a04f7546a61e18dd578bd9cf1957794b812616`; only story documentation was edited before the runs |
| Fixture suite | `citenook-small-rag-v1` |
| Suite SHA-256, both runs | `3896a8fd81ef0ee754d769b60b2c47742bfb0ae30ce15fef61d2f7b0d092ed5a` |
| Chat model | `llama3.1:8b`, 8.0B, Q4_K_M |
| Embedding model | `qwen3-embedding:0.6b`, 595.78M, Q8_0, 1024 dimensions |
| `RAG_TOP_K` | 5, also checked in both API and worker environments |
| Chat options | Temperature 0, `think=false`, structured JSON answer and citations; no seed or context override |
| Embedding batch / chat history limit | 32 / 12; each question had a fresh conversation |
| Ollama request timeout | 300 seconds |
| Runner indexing timeout / poll / HTTP timeout | 300 / 1 / 330 seconds |
| Python runtime / Ollama | 3.14.6 in both API images / 0.32.0 |
| LlamaIndex packages | Core 0.14.24; PostgreSQL vector store 0.8.1; absent from the native image |
| Database | PostgreSQL 17.10; LlamaIndex recorded pgvector extension 0.8.5 |
| Docker / Compose | 29.6.1 / 5.3.0, x86_64, 24 logical CPUs, 33613303808 bytes Docker memory |
| Loaded model execution | CPU, zero VRAM, 4096 context reported for both selected models after warm-up |

| Installed model | Full Ollama digest, identical in both runs |
| --- | --- |
| `llama3.1:8b` | `46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e` |
| `qwen3-embedding:0.6b` | `ac6da0dfba84a81fdbfbaf330198c33cd77c4cdfc53e8bc50eb581914a15621d` |

Both runs followed the same chat and embedding warm-up inputs: `Reply with OK.` and `CiteNook evaluation warm-up.` LlamaIndex startup also made an earlier warm-up pair before API readiness. Warm-up time is outside the answer measurements; these are warmed runs, with no cold-start comparison.

The application source fingerprint matched on the host and in both API images: `7693ede80ecb12204cefb0684df9d951999751022443234e6e5e7f7895eeb071`. It hashes sorted `app/**/*.py` paths relative to `apps/api`, followed by a NUL byte, file bytes, and another NUL byte for each file. Exact image IDs, package versions, model metadata, ready-document records, and post-run cleanup checks are in the environment files below.

## Evidence and reproduction

The runner's `results.json` and `report.md` files are preserved unchanged. Environment files supplement them with direct container and Ollama observations; the runner itself still labels top-k as operator-supplied because the public API does not expose it.

| Backend | Full answers and checks | Runner report | Environment and cleanup |
| --- | --- | --- | --- |
| Native | [results.json](results/2026-10-14/native/results.json) | [report.md](results/2026-10-14/native/report.md) | [environment.json](results/2026-10-14/native/environment.json) |
| LlamaIndex | [results.json](results/2026-10-14/llamaindex/results.json) | [report.md](results/2026-10-14/llamaindex/report.md) | [environment.json](results/2026-10-14/llamaindex/environment.json) |

An earlier local [LlamaIndex preflight](results/2026-10-14/llamaindex-preflight.json) was blocked by sandbox networking at `GET health`, before any upload or question. The complete run used permitted localhost access and a fresh output directory. No fixture, prompt, model, or app code was adjusted between measured runs.

The [fixture runner guide](../../rag-evaluation.md) describes the existing CLI and its cleanup rules. These runs used the checked-in Compose files plus this [measurement override](results/2026-10-14/measurement.compose.yml), which pins the model pair and local scratch database settings. API and worker were built from the repository's locked native and LlamaIndex targets; the already installed Ollama service remained outside the application images.

Use the archived override to reproduce the deployment setup from the repository root:

```bash
docker compose -p citenook-mra031-native \
  -f docker-compose.yml \
  -f docs/releases/release-0.6-rag-evaluation-and-ci/results/2026-10-14/measurement.compose.yml \
  up --build --detach api worker
```

After the native run and its cleanup, the native project was stopped and its scratch volumes removed. LlamaIndex images had been built separately before measurement; its API and worker were then started with a separate project and the extra backend override. The equivalent build-and-start command is:

```bash
docker compose -p citenook-mra031-llamaindex \
  -f docker-compose.yml -f docker-compose.llamaindex.yml \
  -f docs/releases/release-0.6-rag-evaluation-and-ci/results/2026-10-14/measurement.compose.yml \
  up --build --detach api worker
```

Both measurements ran from `apps/api`, using the already locked host Python environment:

```bash
/tmp/citenook-mra030-venv/bin/python -m evaluation \
  --base-url http://127.0.0.1:8000 --backend native \
  --chat-model llama3.1:8b --embedding-model qwen3-embedding:0.6b \
  --rag-top-k 5 --output-dir /tmp/citenook-mra031/native

/tmp/citenook-mra030-venv/bin/python -m evaluation \
  --base-url http://127.0.0.1:8000 --backend llamaindex \
  --chat-model llama3.1:8b --embedding-model qwen3-embedding:0.6b \
  --rag-top-k 5 --output-dir /tmp/citenook-mra031/llamaindex-run1
```

For a new run, prepare the host environment as the guide describes, choose unused project names and output directories, and confirm both selected models are installed. Start only one deployment at a time with empty documents and matching API/worker settings. After each run, public document and conversation lists, uploaded files, ingestion jobs, messages, and selected index rows were empty; both scratch projects and their volumes were then removed.

## Scope

Expected-source checks compare returned citation file names and verify ownership of cited IDs. They do not inspect every retrieved item, so they are not retrieval recall. Literal whole-term key facts can reject a correct paraphrase, and a passing fact match does not check every statement in an answer. The three no-answer cases check the app's final canonical reply and empty citations, including any common grounding fallback.

Three short, single-item documents and twelve fixed questions cannot establish full RAG accuracy or general faithfulness. This run does not evaluate large corpora, multi-chunk ranking, PDF extraction, or multi-turn chat. There is no model judge, Ragas score, new dependency, backend, or product feature. [Release verification](verification.md#mra-031-evidence) records the separate code and configuration checks.
