# Optional LlamaIndex comparison

The `citenook-llamaindex` command is a developer-only comparison path over chunks that CiteNook has already indexed. It lets a contributor run a real LlamaIndex `VectorStoreIndex` and query engine against an explicit document selection while the normal CiteNook application continues to use its direct Ollama + SQLAlchemy/pgvector RAG path.

The command is optional. It is not available in the browser UI, does not add a public API route, and is not required to run CiteNook.

## When to use it

Use the comparison command to:

- inspect how LlamaIndex retrieves from the same stored corpus;
- compare an answer and returned source nodes with the normal CiteNook answer;
- review framework integration without migrating the product backend;
- reproduce a bounded local experiment with explicit models and documents.

Do not use it as:

- the normal user chat workflow;
- a second ingestion pipeline or persistent index;
- a production benchmark or automatic claim that one implementation is better;
- a replacement for CiteNook's validated `[S1]`, `[S2]`, and similar citation contract.

## What it reads and writes

The command reads only chunks whose documents are all of the following:

- explicitly selected with one or more `--document-id` arguments;
- active;
- in the `ready` state;
- embedded with the exact `--embedding-model` value.

It maps the stored text, embedding, document ID, file name, page number, chunk ID, chunk ordinal, and embedding-model metadata into an in-memory LlamaIndex index. It embeds only the comparison question, calls the selected local Ollama chat model, prints a structured result, and exits.

It does not upload or re-ingest files, write embeddings, create a conversation, change document state, or persist the in-memory LlamaIndex index.

## Prerequisites

Before running the example, confirm that:

1. Docker Desktop and WSL2 are running.
2. The CiteNook Compose stack is healthy.
3. The selected chat and embedding models are installed in the configured Ollama instance.
4. At least one privacy-safe document is active, `ready`, and uses the selected embedding model.

Start the default external-Ollama stack and inspect the configured models:

```bash
docker compose up --build --detach
curl --fail http://127.0.0.1:8000/api/models
```

The example below uses the checked-in, invented [`Mosslight Community Workshop` fixture](../evals/fixtures/mosslight-workshop.md), `llama3.1:8b`, and `qwen3-embedding:0.6b`. The commands never pull a model automatically.

## English example from WSL2

### 1. Prepare the example document

Open `http://127.0.0.1:5173`, select **Documents**, upload `evals/fixtures/mosslight-workshop.md` with `qwen3-embedding:0.6b`, and wait until it becomes `ready`. Keep **Use for answers** enabled.

List the stored documents and copy the UUID of the ready Mosslight document:

```bash
curl --silent http://127.0.0.1:8000/api/documents \
  | python3 -m json.tool

export MOSSLIGHT_DOCUMENT_UUID="replace-with-the-ready-document-uuid"
export DOCUMENT_UUID="$MOSSLIGHT_DOCUMENT_UUID"
```

Do not select a personal document when preparing public screenshots, logs, or release evidence.

### 2. Run the comparison

The base Compose file intentionally does not publish PostgreSQL to the WSL host. The following disposable container therefore joins the existing `citenook_default` network, reads the checkout through a read-only mount, copies only the Python project into temporary container storage, installs the locked optional environment there, and removes the container after the command exits:

```bash
docker run --rm \
  --network citenook_default \
  --add-host host.docker.internal:host-gateway \
  --volume "$PWD:/source:ro" \
  --workdir /tmp \
  --env DOCUMENT_UUID \
  --env UV_PROJECT_ENVIRONMENT=/tmp/citenook-llamaindex \
  --env DATABASE_URL=postgresql+psycopg://cite_nook:checked-in-development-only@postgres:5432/cite_nook \
  --env OLLAMA_HOST=http://host.docker.internal:11434 \
  --env BRAND_CONFIG_PATH=/source/packages/brand/brand.json \
  ghcr.io/astral-sh/uv:python3.13-bookworm-slim \
  sh -lc '
    mkdir -p /tmp/apps-api &&
    cp -a /source/apps/api/pyproject.toml \
      /source/apps/api/uv.lock \
      /source/apps/api/app \
      /tmp/apps-api/ &&
    uv run --project /tmp/apps-api \
      --extra framework-evaluation \
      --frozen \
      citenook-llamaindex \
      --question "When is Mosslight open, and which days is it closed?" \
      --chat-model llama3.1:8b \
      --embedding-model qwen3-embedding:0.6b \
      --document-id "$DOCUMENT_UUID" \
      --max-chunks 200 \
      --top-k 5 \
      --request-timeout 300 \
      --pretty
  '
```

The first run downloads the locked optional dependencies into the disposable container. If `.env` changes the development database credentials, Compose project name, or Ollama endpoint, update the matching values and network name in this command.

### 3. Read the result

A successful run prints a JSON document. The following is an abridged English example; UUIDs, elapsed time, scores, and exact wording vary by index state, hardware, and model generation:

```text
{
  "answer": "Mosslight is open Tuesday through Saturday from 09:30 to 17:30. It is closed on Sunday and Monday.",
  "chat_model": "llama3.1:8b",
  "document_ids": ["<selected document UUID>"],
  "elapsed_ms": <positive integer; varies>,
  "eligible_chunk_count": 2,
  "embedding_model": "qwen3-embedding:0.6b",
  "question": "When is Mosslight open, and which days is it closed?",
  "sources": [
    {
      "chunk_id": "<stored chunk UUID>",
      "chunk_ordinal": 0,
      "document_id": "<selected document UUID>",
      "document_name": "mosslight-workshop.md",
      "embedding_model": "qwen3-embedding:0.6b",
      "page_number": null,
      "score": <floating-point value; varies>
    }
  ],
  "status": "answered"
}
```

Check these fields:

- `status` is `answered` when compatible selected chunks exist, or `no_data` when none exist;
- `eligible_chunk_count` is positive and does not exceed `--max-chunks`;
- every source belongs to a selected document and reports its stored chunk metadata;
- `answer` is supported by the returned source text;
- `elapsed_ms` is local execution evidence, not a cross-machine performance benchmark.

The complete command output also includes a source snippet. Treat it as document content: do not commit or share output produced from private files.

### 4. Compare it with normal CiteNook

Create a normal CiteNook conversation with the same `llama3.1:8b` chat model and `qwen3-embedding:0.6b` embedding model. Ask the same English question in the browser and compare:

- the answer wording;
- which passages were selected;
- similarity scores;
- whether every statement is supported;
- the normal CiteNook `[S1]` citation result versus LlamaIndex source-node metadata.

This is a qualitative local comparison. One question does not establish retrieval quality, answer quality, or framework superiority.

### 5. Verify explicit no-data behavior

Set `DOCUMENT_UUID` to an absent but valid UUID and repeat the command:

```bash
export DOCUMENT_UUID="00000000-0000-0000-0000-000000000000"
```

The verified result has `status: "no_data"`, `eligible_chunk_count: 0`, and an empty `sources` array. The command must not fall back to unrelated documents or model prior knowledge.

### 6. Clean up the example document

The comparison command itself writes no product data. If you uploaded the Mosslight fixture only for this example, remove that dedicated document through the **Documents** UI or the public API:

```bash
curl --fail-with-body --request DELETE \
  "http://127.0.0.1:8000/api/documents/$MOSSLIGHT_DOCUMENT_UUID"
```

Delete only the dedicated example document. Ordinary `docker compose down` preserves the PostgreSQL and upload named volumes.

## Selecting multiple documents

Repeat `--document-id` to include another explicit document:

```text
--document-id <first UUID> --document-id <second UUID>
```

All selected chunks must still match the chosen embedding model. Keep `--max-chunks` bounded; the command rejects values above 1,000.

## Direct host execution

If PostgreSQL is reachable directly from WSL through the configured `DATABASE_URL`, install the optional environment and use the shorter host command documented in the [development guide](development.md#optional-llamaindex-comparison). The default Compose configuration does not publish PostgreSQL, so the disposable network-attached container is the supported example for the current WSL2 + Compose layout.

## Troubleshooting

- **`network citenook_default not found`:** start the base Compose stack from the repository root. If the Compose project name was overridden, use its actual default network.
- **Database connection failure:** confirm the container uses host `postgres`, port `5432`, and the same checked development credentials as the active Compose configuration.
- **Ollama connection failure:** confirm Docker can reach `http://host.docker.internal:11434`, or replace `OLLAMA_HOST` with the endpoint used by the active stack. The optional Compose Ollama service is reachable from this network as `http://ollama:11434`.
- **Model unavailable:** inspect `GET /api/models` and Ollama `GET /api/tags`; install the exact selected models outside the command.
- **`no_data` for an existing UUID:** confirm the document is active, `ready`, and embedded with the exact selected embedding model.
- **Eligible chunk limit exceeded:** narrow the document selection or deliberately raise `--max-chunks`, never beyond 1,000.
- **Slow first start:** the disposable environment downloads the locked optional dependencies before executing the command.

For architecture and data-flow details, see [Architecture](architecture.md#optional-developer-tooling-boundary) and [RAG pipeline](rag-pipeline.md#optional-llamaindex-comparison). For focused tests and smoke expectations, see [Testing](testing.md).
