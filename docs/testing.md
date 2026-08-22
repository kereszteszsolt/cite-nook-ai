# Testing

## Automated checks

```bash
python3 .agents/skills/release-evidence/scripts/verify_repository.py
npm run lint
npm run test
npm run build
docker compose config
docker compose -f docker-compose.yml -f docker-compose.ollama.yml config
```

The first Compose command must contain no `ollama` service and must resolve `OLLAMA_HOST` to an external endpoint. The override configuration must add the `ollama` service, its named volume, `http://ollama:11434` for the API and worker, and host port `11435` by default.

MRA-002's API tests cover model-name normalization, installed/unavailable catalog results, and configured-name validation. Its web tests cover separate selectors, disabled unavailable options, restoration of a stored model pair, and updating the active conversation.

MRA-003's API tests cover all supported suffixes, safe names, UUID directories, chunked writes, size enforcement, SHA-256, cleanup, and the file-before-commit ordering. Its web tests cover multipart requests and uploading with the selected embedding model.

## Runtime smoke checks

External Ollama mode:

```bash
docker compose up --build --detach
curl --fail http://localhost:8000/api/health
curl --fail http://localhost:8000/api/models
curl --fail http://localhost:5173
docker compose down
```

Separate Ollama container mode:

```bash
docker compose -f docker-compose.yml -f docker-compose.ollama.yml up --build --detach
curl --fail http://localhost:8000/api/health
curl --fail http://localhost:8000/api/models
curl --fail http://localhost:11435/api/tags
curl --fail http://localhost:5173
docker compose -f docker-compose.yml -f docker-compose.ollama.yml down
```

For MRA-002, create a conversation through `POST /api/conversations`, update its model pair through `PATCH /api/conversations/{id}`, and confirm that `GET /api/conversations` returns the stored pair after switching between the two Compose modes.

For MRA-003, upload a supported file and its configured embedding model as multipart data:

```bash
curl --fail -X POST http://localhost:8000/api/documents \
  -F 'file=@README.md;filename=smoke.md;type=text/markdown' \
  -F 'embedding_model=qwen3-embedding:0.6b'
```

Restart the stack without `--volumes`, then verify that the document row, queued job, and `<UUID>/smoke.md` file remain present.

These commands remove containers and networks only. Named volumes remain persistent.
