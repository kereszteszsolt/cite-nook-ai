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
