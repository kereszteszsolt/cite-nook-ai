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
