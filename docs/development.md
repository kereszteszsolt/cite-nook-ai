# Development

The repository uses npm workspaces and Turborepo. Python dependencies are managed with `uv` inside `apps/api`.

```bash
npm install
uv sync --directory apps/api --group dev
npm run dev
```

For host development, PostgreSQL/pgvector must be reachable through `DATABASE_URL`. Ollama is an external dependency by default and is configured with `OLLAMA_HOST`.

The model catalog is configured with comma-separated `CHAT_MODELS` and `EMBEDDING_MODELS`. `DEFAULT_CHAT_MODEL` and `DEFAULT_EMBEDDING_MODEL` must each name an entry in the corresponding list. Models remain visible when Ollama does not have them installed, but the web interface disables them for new selections.

Copy `.env.example` to `.env` only when local overrides are needed.
