# CiteNook

Local document Q&A with citations.

**CiteNook AI** — Ask your documents. Verify the sources.

This repository is being built in independently working MRA stories. MRA-001 provides the branded React/FastAPI/PostgreSQL foundation and a separate worker. MRA-002 adds configured Ollama model discovery and stores the selected chat and embedding model on each conversation. Document ingestion, persistent messages, and grounded answers are introduced by the following stories.

## Start with an existing Ollama instance (default)

Ollama is not installed in the API, worker, or web containers. By default the application connects to `http://host.docker.internal:11434`; set `OLLAMA_HOST` to use another reachable URL.

```bash
docker compose up --build
```

## Start with Ollama in a separate container

The optional override adds the official Ollama service and its persistent model volume:

```bash
docker compose -f docker-compose.yml -f docker-compose.ollama.yml up --build
```

The containerized Ollama API is exposed on `http://localhost:11435` by default so it can coexist with an external instance on port `11434`. Override `OLLAMA_CONTAINER_PORT` if needed.

Open CiteNook at `http://localhost:5173` and the API documentation at `http://localhost:8000/docs`.

## Configure models

The header lists the chat and embedding models configured through `CHAT_MODELS` and `EMBEDDING_MODELS`. CiteNook checks the selected Ollama instance and disables configured models that are not installed. The initial selections come from `DEFAULT_CHAT_MODEL` and `DEFAULT_EMBEDDING_MODEL`; every created conversation remembers both names.

For example, install the default models in an external Ollama instance with:

```bash
ollama pull llama3.1:8b
ollama pull qwen3-embedding:0.6b
```

When using the optional Compose service, run the equivalent commands through `docker compose exec ollama ollama pull ...`.

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
