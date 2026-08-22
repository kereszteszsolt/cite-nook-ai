# Development

The repository uses npm workspaces and Turborepo. Python dependencies are managed with `uv` inside `apps/api`.

```bash
npm install
uv sync --directory apps/api --group dev
npm run dev
```

For host development, PostgreSQL/pgvector must be reachable through `DATABASE_URL`. Ollama is an external dependency by default and is configured with `OLLAMA_HOST`.

The model catalog is configured with comma-separated `CHAT_MODELS` and `EMBEDDING_MODELS`. `DEFAULT_CHAT_MODEL` and `DEFAULT_EMBEDDING_MODEL` must each name an entry in the corresponding list. Models remain visible when Ollama does not have them installed, but the web interface disables them for new selections.

For the supported Docker Compose workflow, copy `.env.example` to the repository-root `.env` before the first start. Compose reads that file automatically, and Git ignores it. The supported startup commands do not read `.env.local` or `.env.dev`.
