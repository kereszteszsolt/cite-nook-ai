# Architecture

MRA-001 establishes the local runtime boundary. React talks only to FastAPI; the API and worker share PostgreSQL/pgvector and never install Ollama inside their images. MRA-002 keeps Ollama access behind the API gateway and stores each conversation's chat and embedding model in PostgreSQL.

```mermaid
flowchart LR
    WEB[React web] --> API[FastAPI]
    API --> DB[(PostgreSQL + pgvector)]
    DB --> WORKER[worker]
    API -. configured HTTP .-> OLLAMA[external or Compose Ollama]
    WORKER -. configured HTTP .-> OLLAMA
    API --> FILES[(upload volume)]
    WORKER --> FILES
```

The default `docker-compose.yml` expects an external Ollama endpoint. `docker-compose.ollama.yml` adds Ollama as a separate service, redirects the application services to it, and exposes it on host port `11435` by default to avoid colliding with an existing external instance.

The web client reads the configured model catalog from FastAPI. FastAPI uses the official Ollama client only to discover which configured names are installed; configured but unavailable names remain part of the API response. Conversation creation and updates accept only configured names and persist both selections.

Later MRA stories add document and message entities without changing these boundaries.
