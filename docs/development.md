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
uv sync --directory apps/api --extra framework-evaluation --group dev
```

The configured chat and embedding models must already be installed in the Ollama instance selected by `OLLAMA_HOST`. Choose one or more existing CiteNook document UUIDs explicitly, then run:

```bash
uv run --directory apps/api --extra framework-evaluation citenook-llamaindex \
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

MRA-019 uses the same `framework-evaluation` extra and keeps Ragas out of the normal API and worker images. Use Python 3.13 for this developer-only environment because Ragas 0.4.3's transitive `scikit-network` release does not publish a Python 3.14 wheel:

```bash
uv sync --directory apps/api --python 3.13 \
  --extra framework-evaluation --group dev --frozen
```

Start the supported CiteNook stack and ensure the answer, embedding, and evaluator models are already installed in the local Ollama instance. Run the committed eight-case fixture through the public API with:

```bash
RAGAS_DO_NOT_TRACK=true \
uv run --directory apps/api --python 3.13 --extra framework-evaluation \
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
