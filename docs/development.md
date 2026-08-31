# Development

## Local setup

The repository uses npm workspaces and Turborepo. Python dependencies are managed with `uv` inside `apps/api`.

```bash
npm install
uv sync --directory apps/api --group dev
npm run dev
```

For host development, PostgreSQL/pgvector must be reachable through `DATABASE_URL`. Ollama is external by default and uses `OLLAMA_HOST`.

Copy the root environment file before the first Compose start:

```bash
cp .env.example .env
```

For host-run API and worker processes, `RAG_BACKEND` selects `native` or `llamaindex`. Compose pins native in the base file and selects LlamaIndex through its override so both processes cannot drift.

## Settings

| Setting | Job |
| --- | --- |
| `DATABASE_URL` | PostgreSQL connection |
| `OLLAMA_HOST` | Reachable Ollama URL |
| `CHAT_MODELS` | Chat models shown by CiteNook |
| `EMBEDDING_MODELS` | Embedding models shown by CiteNook |
| `DEFAULT_CHAT_MODEL` | Default chat choice |
| `DEFAULT_EMBEDDING_MODEL` | Default embedding choice |
| `UPLOAD_DIR` | Original file storage |
| `MAX_UPLOAD_MB` | Positive upload size limit |
| `EMBEDDING_BATCH_SIZE` | Native embedding batch size |
| `INGESTION_STALE_MINUTES` | Time before a stuck job is queued again |
| `CHAT_HISTORY_MESSAGES` | Recent messages sent to chat |
| `RAG_TOP_K` | Maximum retrieved sources |
| `RAG_BACKEND` | Host-run backend selection: `native` or `llamaindex` |

A conversation stores its chat and embedding models. A document stores the embedding model used for its index.

## Compose matrix

### Native with external Ollama

```bash
docker compose up --build
```

### Native with Compose-managed Ollama

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.ollama.yml \
  up --build
```

### LlamaIndex with external Ollama

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.llamaindex.yml \
  up --build
```

### LlamaIndex with Compose-managed Ollama

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.llamaindex.yml \
  -f docker-compose.ollama.yml \
  up --build
```

The LlamaIndex override selects `runtime-llamaindex`, sets `RAG_BACKEND=llamaindex` for API and worker, and uses the `citenook-llamaindex` project name. The Ollama override remains independent.

## Dependency installs and images

The common and native development environment uses the base project dependencies:

```bash
uv sync --directory apps/api --group dev
```

Install the locked optional LlamaIndex set for host development with:

```bash
uv sync --directory apps/api --group dev --extra llamaindex
```

The API Dockerfile exposes `runtime-native` and `runtime-llamaindex`. The native target installs only common packages; the optional target adds the lock-file LlamaIndex extra.

## Data rules

- Native keeps compatibility with the Release 0.4 database and `document_chunks`.
- LlamaIndex stores nodes in its own PostgreSQL vector table or collection.
- Supported native and LlamaIndex Compose paths use separate named volumes.
- Changing `RAG_BACKEND` is not a data migration.
- A database marker stops an unsafe backend mismatch.
- Moving documents between backends requires a new upload and index run in the destination deployment.
- Moving a file or package must not rename a table or change an HTTP field by accident.

Base Compose stores data in `citenook_postgres_data` and `citenook_uploads_data`. The LlamaIndex override stores data in `citenook-llamaindex_postgres_data` and `citenook-llamaindex_uploads_data`. Ordinary `docker compose down` keeps these volumes.

After startup, verify the deployment before uploading documents:

```bash
curl --fail http://localhost:8000/api/health
curl --fail http://localhost:8000/api/models
```

The health JSON must report the expected `ragBackend`. The model catalog must show the chosen chat and embedding models as installed.

## Development workflow

Read the active story and the [story workflow](story-workflow.md) first. Codex must ask before implementation and must ask again before commit. After an approved commit, it asks before it starts the next story.

For the package structure, see [Architecture](architecture.md). For the completed story order, see the [Release 0.5 story map](releases/release-0.5-clean-rag-backends/README.md).
