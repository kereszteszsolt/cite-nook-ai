# Development

## Current Release 0.4 setup

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

The current Release 0.4 code always uses the native RAG path. It does not read `RAG_BACKEND` yet.

## Current settings

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

A conversation stores its chat and embedding models. A document stores the embedding model used for its index.

## Planned Release 0.5 backend setting

`MRA-026` will add:

```env
RAG_BACKEND=native
```

Valid values will be `native` and `llamaindex`. The default stays `native`. The API and worker must receive the same value through Compose.

## Planned Release 0.5 Compose matrix

These commands are planned and become supported only after `MRA-026` is implemented and tested.

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

The LlamaIndex override will select its runtime image, set `RAG_BACKEND=llamaindex` for API and worker, and use a separate Compose project name. The Ollama override will remain independent.

## Planned dependency installs

The common and native development environment will keep the base project dependencies:

```bash
uv sync --directory apps/api --group dev
```

`MRA-024` will add a locked optional LlamaIndex dependency set. The final install command will be recorded here after the extra name and package versions pass Python 3.13 and 3.14 checks.

## Data rules

- Native keeps compatibility with the Release 0.4 database and `document_chunks`.
- LlamaIndex stores nodes in its own PostgreSQL vector table or collection.
- Supported native and LlamaIndex Compose paths use separate named volumes.
- Changing `RAG_BACKEND` is not a data migration.
- A database marker stops an unsafe backend mismatch.
- Moving a file or package must not rename a table or change an HTTP field by accident.

## Development workflow

Read the active story and the [story workflow](story-workflow.md) first. Codex must ask before implementation and must ask again before commit. After an approved commit, it asks before it starts the next story.

For the full target structure, see [Architecture](architecture.md). For the story order, see the [Release 0.5 plan](releases/release-0.5-clean-rag-backends/README.md).
