# Development

The repository uses npm workspaces and Turborepo. Python dependencies are managed with `uv` inside `apps/api`.

```bash
npm install
uv sync --directory apps/api --group dev
npm run dev
```

For host development, PostgreSQL/pgvector must be reachable through `DATABASE_URL`. Ollama is an external dependency by default and is configured with `OLLAMA_HOST`.

The model catalog is configured with comma-separated `CHAT_MODELS` and `EMBEDDING_MODELS`. `DEFAULT_CHAT_MODEL` and `DEFAULT_EMBEDDING_MODEL` must each name an entry in the corresponding list. Models remain visible when Ollama does not have them installed, but the web interface disables them for new selections.

`UPLOAD_DIR` selects the original-file storage location and `MAX_UPLOAD_MB` sets the positive whole-megabyte upload limit. Compose defaults to `/data/uploads`, backed by the shared `citenook_uploads_data` volume.

`EMBEDDING_BATCH_SIZE` controls how many chunks the worker sends in one Ollama embedding request. `INGESTION_STALE_MINUTES` defines when an abandoned `processing` job is returned to the PostgreSQL queue. Both settings accept positive whole numbers and default to `32` and `15` respectively.

`CHAT_HISTORY_MESSAGES` controls the positive maximum number of recent persisted messages supplied to a model request. It defaults to `12`; the application still stores and reloads the complete conversation history.

`RAG_TOP_K` controls the positive maximum number of compatible ready chunks supplied to one grounded answer. It defaults to `5`. Retrieved chunks are always filtered by the conversation embedding model before cosine-distance ordering.

For the supported Docker Compose workflow, copy `.env.example` to the repository-root `.env` before the first start. Compose reads that file automatically, and Git ignores it. The supported startup commands do not read `.env.local` or `.env.dev`.

## Optional LlamaIndex comparison

Release 0.5 keeps LlamaIndex outside the normal API and worker installation. Install the exact optional dependency set only in a development environment that needs the comparison command:

```bash
uv python install 3.13
uv sync --directory apps/api --python 3.13 --managed-python \
  --extra framework-evaluation --group dev --frozen
```

Python 3.13 uses the prebuilt locked dependency wheels and is the quickest setup. Python 3.14 is also supported, but Ragas 0.4.3's locked `scikit-network` dependency currently has no CPython 3.14 wheel. On Linux, install a C/C++ build toolchain, then use an uv-managed interpreter so the source build has Python headers:

```bash
uv python install 3.14
uv sync --directory apps/api --python 3.14 --managed-python \
  --extra framework-evaluation --group dev --frozen
```

The release verification used clean uv-managed Python 3.13.14 and 3.14.6 environments. Both resolved the same lock and passed the combined 43 focused framework/evaluation tests.

The configured chat and embedding models must already be installed in the Ollama instance selected by `OLLAMA_HOST`. Choose one or more existing CiteNook document UUIDs explicitly, then run:

```bash
uv run --directory apps/api --python 3.13 --managed-python \
  --extra framework-evaluation citenook-llamaindex \
  --question "What does the selected document say about the topic?" \
  --chat-model llama3.1:8b \
  --embedding-model qwen3-embedding:0.6b \
  --document-id 00000000-0000-0000-0000-000000000000 \
  --max-chunks 200 \
  --top-k 5 \
  --pretty
```

Repeat `--document-id` to include another document. The command reads at most `--max-chunks` rows and accepts a maximum of 1,000. It uses only chunks from selected documents that are active, `ready`, and match the selected embedding model. An empty or incompatible selection produces a structured `no_data` result.

The command maps the stored CiteNook text and embeddings into an in-memory LlamaIndex `VectorStoreIndex`, embeds only the question through the selected local Ollama embedding model, and queries a `RetrieverQueryEngine` with the selected local chat model. It emits the answer, elapsed time, eligible chunk count, and the metadata and score of the source nodes returned by LlamaIndex. It does not re-ingest content, persist a LlamaIndex index, write embeddings, create a conversation, change document state, expose a public API route, or claim compatibility with CiteNook's exact `[S1]` citation contract.

## Local Ragas evaluation

MRA-019 uses the same installed `framework-evaluation` environment and keeps Ragas out of the normal API and worker images. Start the supported CiteNook stack and ensure the answer, embedding, and evaluator models are already installed in the local Ollama instance. The evaluator does not have to be listed in CiteNook's product chat-model catalog, but it must be available from the explicit local `--ollama-url`.

Run the committed eight-case fixture through the public API with:

```bash
RAGAS_DO_NOT_TRACK=true \
uv run --directory apps/api --python 3.13 --managed-python \
  --extra framework-evaluation \
  citenook-ragas \
  --api-url http://localhost:8000/api \
  --ollama-url http://localhost:11434 \
  --answer-model llama3.1:8b \
  --embedding-model qwen3-embedding:0.6b \
  --evaluator-model llama3.1:8b \
  --ingestion-timeout-seconds 180 \
  --request-timeout-seconds 600
```

The command validates `evals/fixtures/mra-019-cases.json` before any model call, uploads the invented fixture under a run-specific name, waits for successful ingestion with a bounded timeout, and creates a tagged conversation for each single-turn case. Separate conversations prevent earlier questions from influencing later answers. It evaluates the returned answer with Ragas Faithfulness and Factual Correctness through Ollama's local OpenAI-compatible endpoint. Ragas telemetry is disabled in code as well as in the example command; no hosted key, account, upload, or experiment service is used.

Only citation snippets returned by CiteNook become `retrieved_contexts`. The public answer contract does not expose every raw top-k candidate, so this harness evaluates answer groundedness against cited contexts and does not measure full retriever ranking or recall.

Run-specific conversations and the uploaded document are deleted after success, ingestion timeout, answer or evaluator failure, and keyboard interruption. `--retain-resources` deliberately preserves only that run's tagged resources for diagnosis. Timestamped JSON and CSV artifacts are written under ignored `evals/experiments/`; they contain answers, citations, scores, durations, models, statuses, and errors, but no hidden model prompts or unrelated database content.

The command warns if the answer and evaluator models match. The recorded MRA-019 smoke run uses the same locally available model in both roles, so correlated judgment is an explicit limitation; choose a separate capable local judge when available. Scores are model-assisted review signals, not human ground truth, a benchmark, or proof that one implementation is superior. The local smoke gate checks complete case coverage, scores in the `0..1` range, and successful cleanup; it deliberately imposes no CI quality threshold.

## Framework/evaluation troubleshooting

- **Optional imports are missing:** rerun the exact `uv sync` command with `--extra framework-evaluation --frozen`; the normal API environment intentionally omits these packages.
- **Python 3.14 cannot build `scikit-network`:** confirm `uv python find --managed-python 3.14` resolves to an uv-managed interpreter and that a C/C++ compiler is installed. Use Python 3.13 if a local source-build toolchain is unavailable.
- **A configured model is rejected or unavailable:** inspect `GET /api/models` for CiteNook answer/embedding models and `GET <OLLAMA_HOST>/api/tags` for the evaluator. The commands never pull models automatically.
- **LlamaIndex returns `no_data`:** confirm every selected UUID exists and its document is active, `ready`, and embedded with the exact `--embedding-model`; increase `--max-chunks` only deliberately.
- **Ragas ingestion times out:** verify the worker is running, the embedding model is installed, and the uploaded evaluation document did not enter `failed`. Increase the bounded ingestion timeout only for a demonstrably slower local machine.
- **Ragas evaluation is slow or a judge schema fails:** use a local instruction-following evaluator that reliably produces structured output, keep `--request-timeout-seconds` bounded, and review per-case errors in the JSON artifact. Small models can be faster but less schema-reliable.
- **Temporary resources need inspection:** rerun once with `--retain-resources`, inspect only the run-tagged document/conversations, then delete them through the public API. Retention is diagnostic and deliberately disables automatic cleanup for that run.
