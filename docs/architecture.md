# Architecture

MRA-001 establishes the local runtime boundary. React talks only to FastAPI; the API and worker share PostgreSQL/pgvector and never install Ollama inside their images. MRA-002 keeps Ollama access behind the API gateway and stores each conversation's chat and embedding model in PostgreSQL. MRA-003 stores upload metadata in PostgreSQL and original bytes in the shared upload volume. MRA-004 processes those bytes in the separate worker and persists their chunks and embeddings. MRA-006 stores complete conversation histories and their answer provenance in PostgreSQL. MRA-007 completes the path with model-compatible pgvector retrieval and grounded Ollama chat. MRA-008 adds a global Documents workspace and a persistent per-document retrieval switch. MRA-009 adds partial conversation updates for durable custom titles and refines the browser-only chat interaction layer. MRA-010 keeps the existing per-conversation model contract while moving selection into custom creation/edit dialogs and conversation deletion into a custom confirmation dialog. MRA-011 adds equivalent document-deletion safety and restrained status presentation. MRA-012 adds persisted server-side answer duration and browser message actions without branching the linear conversation model. MRA-013 makes the local browser-to-API boundary same-origin and distinguishes API startup failure from Ollama availability. MRA-018 and MRA-019 add optional developer commands around this product path without replacing it: LlamaIndex compares a query over selected existing chunks, while Ragas evaluates answers collected through the public local API.

```mermaid
flowchart LR
    subgraph PRODUCT[Primary CiteNook product path]
        BROWSER[Browser] -->|same-origin /api| WEB[React and Vite proxy]
        WEB --> API[FastAPI]
        API --> DB[(PostgreSQL + pgvector)]
        DB --> WORKER[worker]
        API -. configured HTTP .-> OLLAMA[external or Compose Ollama]
        WORKER -. configured HTTP .-> OLLAMA
        API --> FILES[(upload volume)]
        WORKER --> FILES
    end

    subgraph DEV[Optional developer tooling]
        LLAMAINDEX[LlamaIndex comparison CLI]
        RAGAS[Ragas evaluation CLI]
    end

    LLAMAINDEX -. read selected stored chunks .-> DB
    LLAMAINDEX -. local query models .-> OLLAMA
    RAGAS -. setup and questions through public API .-> API
    RAGAS -. local evaluator model .-> OLLAMA

    style DEV stroke-dasharray: 6 4
```

The default `docker-compose.yml` expects an external Ollama endpoint. `docker-compose.ollama.yml` adds Ollama as a separate service, redirects the application services to it, and exposes it on host port `11435` by default to avoid colliding with an existing external instance. The browser uses the web origin's relative `/api` path; Vite forwards that path to `http://api:8000` in Compose and to a configurable `VITE_API_PROXY_TARGET` in host development. Consequently `localhost:5173` and `127.0.0.1:5173` do not depend on cross-origin browser access. Direct development origins for both loopback names remain allowed by FastAPI's default CORS list.

The web client reads the configured model catalog from FastAPI. FastAPI uses the official Ollama client only to discover which configured names are installed; configured but unavailable names remain part of the API response. The global header has no model controls. New-conversation and active-conversation edit dialogs expose the catalog, allow only installed choices, and send both selected names through the centralized API client. Conversation creation and updates accept only configured names and persist both selections directly on the conversation.

For uploads, the API reduces the supplied name to a safe base name, streams the body into a temporary file while enforcing the configured limit and calculating SHA-256, and atomically moves it to `<UPLOAD_DIR>/<document UUID>/<file name>`. Only after the final path exists does the database transaction commit the document and its queued ingestion job. The API and worker mount the same named upload volume.

The worker atomically claims one queued job at a time with `FOR UPDATE SKIP LOCKED`. It extracts one-based PDF pages or DOCX/TXT/Markdown text, creates deterministic overlapping chunks, and calls the official Ollama client in bounded batches. It then stores the chunk text, ordinal, optional page number, embedding model, and pgvector value in PostgreSQL before marking the document ready. A configurable age threshold returns abandoned processing jobs to the queue.

The document API lists persisted processing and active state and returns original files only from the configured upload root. `PATCH /api/documents/{id}` changes only whether retrieval may use the document; it does not remove bytes, chunks, or jobs and does not trigger ingestion. New and existing database volumes receive a non-null active column with a true default during idempotent startup initialization. Deletion first moves the document's UUID directory aside, commits the database cascade for its chunks and jobs, restores the directory if that commit fails, and removes the quarantined bytes after success. The web client polls this API only while queued or processing documents remain.

Conversation turns are written atomically after locking the conversation row. Every message has a stable ordinal; assistant messages also store the exact chat model, structured citation snapshot as JSONB, and nullable non-negative `response_duration_ms`. The duration uses a server monotonic clock around embedding, retrieval, validation, and chat generation; user messages and pre-MRA-012 assistant rows keep `null`. Startup initialization adds the nullable timing column and check constraint idempotently for existing PostgreSQL volumes. The first normalized question creates a deterministic title bounded to 80 characters without a title-generation model call only while the title is still the untouched default. `PATCH /api/conversations/{id}` can independently change a normalized custom title of at most 120 characters or the stored model pair. The API returns the full ordered history, including timing, for reloads, while the model-input boundary selects only the most recent `CHAT_HISTORY_MESSAGES` records. Conversation deletion cascades to every message.

For each question, the API embeds normalized text with the conversation embedding model. A cosine-distance query joins chunks to documents, filters both stored model names to that same model, accepts only active `ready` documents, orders by distance and chunk UUID, and limits the result to `RAG_TOP_K`. The result order becomes deterministic `S1`, `S2`, and so on.

The system prompt treats source text as untrusted data, permits only the current sources, requires exact source markers, and mandates an explicit insufficiency sentence. Recent conversation messages are bounded context rather than evidence. `OllamaGateway` makes the one non-streaming official-client chat call with the conversation chat model. The API rejects missing or invented markers, persists only sources actually cited by the answer, and returns their document, page, chunk, snippet, score, and server-measured response duration fields. If retrieval returns no compatible source, it stores the explicit insufficiency answer without inventing a citation. Asking an answer's preceding question again calls this same endpoint and appends a new atomic user/assistant turn; the original turn remains unchanged.

## Optional developer-tooling boundary

The dashed boundary in the diagram is not part of request-time CiteNook operation. The normal API and worker installation excludes LlamaIndex and Ragas, and neither Compose file adds a framework or evaluation service.

`citenook-llamaindex` reads a bounded, explicit selection of existing active, `ready`, embedding-compatible chunks from PostgreSQL. It maps their stored text, embeddings, and source metadata into an in-memory LlamaIndex `VectorStoreIndex`, queries local Ollama, prints the answer and returned source nodes, and exits without writing a conversation, index, embedding, or document state.

`citenook-ragas` deliberately exercises the shipped public API. It uploads the committed invented fixture, waits for the normal worker, creates one tagged conversation per single-turn case, collects each grounded answer and its public citation snippets, and evaluates those snippets through a separately configured local Ollama judge. Its temporary API resources are deleted in a final cleanup path, and its JSON/CSV output remains under ignored `evals/experiments/`.

These tools do not add routes, change the database schema, alter worker ownership, expose a frontend selector, or branch the direct grounded-answer and `[S1]` citation contract. They are removable comparison and review surfaces around the primary custom Ollama + pgvector implementation.
