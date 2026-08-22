# Development

The repository uses npm workspaces and Turborepo. Python dependencies are managed with `uv` inside `apps/api`.

```bash
npm install
uv sync --directory apps/api --group dev
npm run dev
```

For host development, PostgreSQL/pgvector must be reachable through `DATABASE_URL`. Ollama is an external dependency by default and is configured with `OLLAMA_HOST`.

Copy `.env.example` to `.env` only when local overrides are needed.
