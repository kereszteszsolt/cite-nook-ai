# CiteNook

Local document Q&A with citations.

**CiteNook AI** — Ask your documents. Verify the sources.

This repository is being built in independently working MRA stories. MRA-001 provides the branded React/FastAPI/PostgreSQL foundation and a separate worker. MRA-002 adds configured Ollama model discovery and stores the selected chat and embedding model on each conversation. MRA-003 adds persistent PDF, DOCX, TXT, and Markdown uploads. MRA-004 indexes those uploads in the worker with Ollama embeddings and pgvector storage. MRA-005 shows processing state and supports opening and deleting stored documents. MRA-006 persists and reloads complete conversation histories. Grounded questions and answers are introduced by MRA-007.

## Quick start

Create the local configuration file before the first start:

```bash
cp .env.example .env
```

Docker Compose automatically reads the repository-root `.env`. Edit that file to configure the Ollama endpoint, the available model names, and local ports. The file is ignored by Git and must not be committed. `.env.local` and `.env.dev` are not used by the supported Compose commands.

Choose one of the following Ollama modes.

### Option A: use an existing Ollama instance (default)

Ollama is not installed in the API, worker, or web containers. By default the application connects to `http://host.docker.internal:11434`. Set `OLLAMA_HOST` in `.env` to use another URL that is reachable from Docker.

```bash
docker compose up --build
```

### Option B: run Ollama as a separate container

This is optional and is not the default. The override adds the official Ollama image as an independent service with its own persistent model volume:

```bash
docker compose -f docker-compose.yml -f docker-compose.ollama.yml up --build
```

The containerized Ollama API is exposed on `http://localhost:11435` by default so it can coexist with an external instance on port `11434`. Override `OLLAMA_CONTAINER_PORT` if needed.

Open CiteNook at `http://localhost:5173` and the API documentation at `http://localhost:8000/docs`.

## Configure models

The header lists the chat and embedding models configured through `CHAT_MODELS` and `EMBEDDING_MODELS`. CiteNook checks the selected Ollama instance and disables configured models that are not installed. The initial selections come from `DEFAULT_CHAT_MODEL` and `DEFAULT_EMBEDDING_MODEL`; every created conversation remembers both names.

Uploads use `UPLOAD_DIR` and the `MAX_UPLOAD_MB` size limit from `.env`. Under Compose, uploaded bytes are stored in the persistent `citenook_uploads_data` volume.

The separate worker extracts queued uploads, creates deterministic overlapping chunks, and sends them to Ollama in batches controlled by `EMBEDDING_BATCH_SIZE`. Jobs left in `processing` longer than `INGESTION_STALE_MINUTES` are returned to the queue. Both values must be positive whole numbers.

The Stored documents table updates while queued or processing work exists. It shows the original file metadata, embedding model, status, chunk count, upload time, and bounded processing errors. Original files open through the API; confirmed deletion removes the document, its chunks and jobs, and its UUID-scoped upload directory.

Conversations and their messages remain in PostgreSQL across reloads and container restarts. The first stored question becomes a deterministic title of at most 80 characters, while `CHAT_HISTORY_MESSAGES` limits only the recent history prepared for model requests. Deleting a conversation also deletes all of its messages.

For example, install the default models in an external Ollama instance with:

```bash
ollama pull llama3.1:8b
ollama pull qwen3-embedding:0.6b
```

When using the optional Compose service, include the override file when installing the models in another terminal:

```bash
docker compose -f docker-compose.yml -f docker-compose.ollama.yml exec ollama ollama pull llama3.1:8b
docker compose -f docker-compose.yml -f docker-compose.ollama.yml exec ollama ollama pull qwen3-embedding:0.6b
```

Reload CiteNook after installing a model so the selectors refresh their installed status.

## Project identity

- Display brand: `CiteNook`
- Extended name: `CiteNook AI`
- Repository and technical app ID: `cite-nook-ai`
- Package scope: `@citenook/*`
- Docker project: `citenook`
- Story prefix: `MRA`

Product identity is defined once in [`packages/brand/brand.json`](packages/brand/brand.json).

## Verification

```bash
npm run lint
npm run test
npm run build
docker compose config
docker compose -f docker-compose.yml -f docker-compose.ollama.yml config
```

See [the testing guide](docs/testing.md) and the [Release 0.1 story map](docs/releases/release-0.1-mini-rag/README.md).

## License

Apache License 2.0. See [`LICENSE`](LICENSE).
