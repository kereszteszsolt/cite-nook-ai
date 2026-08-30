# Technology stack

This page lists the main tools used by the current code and the optional tools planned for Release 0.5. Package files and lock files remain the source of truth for exact versions.

## Web application

| Tool | Current version | Job |
| --- | --- | --- |
| React | `19.2.8` | User interface and feature components |
| React DOM | `19.2.8` | Browser rendering |
| TypeScript | `7.0.2` | Static web types and build checks |
| Vite | `8.2.1` | Development server, API proxy, and production build |
| Vitest | `4.1.10` | Web unit and component tests |
| Testing Library | `16.3.2` | User-focused React tests |
| Playwright | `1.62.0` | Privacy-safe browser screenshots and smoke flows |

## Python application

| Tool | Current version | Job |
| --- | --- | --- |
| Python | `>=3.13,<3.15` | API and worker runtime |
| FastAPI | `0.141.1` | HTTP API and OpenAPI docs |
| SQLAlchemy | `2.0.52` | ORM, transactions, and database queries |
| psycopg | `3.3.4` | PostgreSQL driver |
| pgvector | `0.5.0` | Vector column and cosine search support |
| Ollama Python client | `0.6.2` | Local chat, embeddings, and model discovery |
| pypdf | `6.16.1` | PDF text extraction |
| python-docx | `1.2.0` | DOCX text extraction |
| python-multipart | `0.0.32` | Multipart document upload |
| pytest | `>=8,<10` | Python tests |
| Ruff | `0.16.3` | Python lint and format checks |

## Data and runtime

| Tool | Current source | Job |
| --- | --- | --- |
| PostgreSQL | `pgvector/pgvector:pg17` | App data, queue state, citations, and vector data |
| pgvector extension | Container image | Native vector search and LlamaIndex vector storage |
| Docker Compose | Local runtime | Web, API, worker, PostgreSQL, and optional Ollama startup |
| Ollama | External by default | Local model runtime outside application images |
| Named volumes | Compose | PostgreSQL data, uploads, and optional Ollama models |

## Repository tools

| Tool | Current version | Job |
| --- | --- | --- |
| npm | `11.16.0` | Workspace package install and scripts |
| Node.js | `>=24` | Web and repository task runtime |
| Turborepo | `2.10.11` | Workspace lint, test, build, and development tasks |
| uv | Lock file in `apps/api` | Python dependency install and lock management |
| Codex agents | Repository config | Story planning, bounded implementation, and review |

## Planned optional Release 0.5 tools

| Tool | Planned job | Install rule |
| --- | --- | --- |
| LlamaIndex core | Node and retrieval interfaces | LlamaIndex runtime image only |
| LlamaIndex PostgreSQL vector store | Persistent node vectors in PostgreSQL/pgvector | LlamaIndex runtime image only |

Exact LlamaIndex package names and versions are selected and pinned in `MRA-024` after compatibility tests. The native runtime must not install them.

## Planned later tools

Ragas remains planned for Release 0.6. OpenRouter, Poe, direct cloud APIs, hybrid retrieval, and reranking are not installed by Release 0.5.
