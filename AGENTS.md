# Codex engineering guide

## Repository

CiteNook is a local-first RAG application: React/TypeScript frontend, FastAPI backend, SQLAlchemy/PostgreSQL with pgvector, a separate ingestion worker, and Ollama. `native` and `llamaindex` are alternative retrieval backends selected per deployment, not simultaneous pipelines.

## Load context progressively

1. Read this file, `docs/story-workflow.md`, and **only the active `MRA-*` story**. Check its release README for status and dependencies.
2. Inspect the affected modules and their tests. Open `docs/architecture.md`, `docs/rag-pipeline.md`, or `docs/testing.md` **only if relevant** to the change.
3. Activate at most the skill(s) that match the actual file/technology scope below. Do not preload every skill, historic release plan, or unrelated module.
4. A planned release is not implemented behavior. Releases 0.6 and 0.7 are complete; their synthetic results record observed failures, not a security guarantee. Release 0.8 (`MRA-033`) is **planned only**: optional DeepEval evaluation of saved results. Preserve previous fixtures and evidence byte-for-byte.

## Technical boundaries

- **React/Vite:** `apps/web/src/features/*` owns feature state and UI; requests go through `apps/web/src/api.ts`, not ad hoc `fetch` calls in feature components. Preserve loading and error handling.
- **FastAPI:** routers validate HTTP contracts; `app/application/*` coordinates use cases; `app/persistence/*` owns SQLAlchemy storage; `app/bootstrap.py` wires concrete adapters. Keep routers thin and application services independent of concrete adapters.
- **Worker / PostgreSQL:** background extraction and embedding run in `app/worker.py`; the PostgreSQL-backed job queue remains the only queue. Preserve transaction boundaries, index metadata and worker retry/error states.
- **RAG / LLM:** one `DocumentIndexer` and `SourceRetriever` per deployment. Keep native code free of LlamaIndex dependencies. Native and LlamaIndex indexes use separate deployment data; never introduce dual indexing, runtime switching or silent fallback.
- **Answer integrity:** the common answer service owns prompts, model calls, grounded citations, timing and persistence. Treat uploaded text as untrusted data. Validate source markers; a citation marker alone does not establish that a claim is grounded.
- **Infra:** API, worker and web may use external Ollama or the existing optional Compose Ollama service. Do not add an unrelated queue, provider, abstraction layer, or library outside an approved story.

## Roles and on-demand skills

The main Codex session should normally do the work itself. Delegate only when a separate result adds value.

| Role | Use only when | Constraint |
| --- | --- | --- |
| `implementation_worker` | A single approved story is intentionally delegated | Sole writer for that story |
| `architect` | A risky cross-boundary change needs a short independent plan | Read-only; no duplicate implementation plan |
| `reviewer` | A security-sensitive, architecture-heavy or release change needs independent review | Read-only; review the diff and existing evidence |

| Skill | Trigger |
| --- | --- |
| `react-fastapi-contracts` | React, FastAPI, typed HTTP contracts or worker-driven UI state |
| `rag-pipeline` | Embeddings, pgvector, native/LlamaIndex retrieval, citations, model outputs or RAG evaluation / safety fixtures |
| `release-evidence` | Story status, repository checks, documentation integrity or release verification |

Use **one writer**. Never delegate overlapping edits, duplicate research or repeat test suites merely to keep agents busy. Parallel read-only review is optional when its input is stable. The session cap is two concurrent threads; it is a limit, not a target.

## One-story delivery loop

- Name the active story, touched files, risk and **focused** checks; obtain approval before implementation.
- Work through the story's acceptance criteria in order. Avoid speculative code, unnecessary refactoring and new dependencies.
- Run affected tests first. Expand to integration, Compose or model smoke checks only when the change calls for them; request approval before costly/destructive checks.
- Record real commands, outcomes and limitations in the active release `verification.md`. Do not rewrite historic evidence.
- Review the diff and propose a commit message. **Do not commit, push or start another story without separate approval.**
- Keep comments for non-obvious reasons, not descriptions of obvious code; follow `docs/story-workflow.md` for comment and docstring limits.

## License headers

New handwritten application source files use the relevant comment syntax for:

```text
SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
SPDX-License-Identifier: Apache-2.0
```

Do not add SPDX headers to Markdown, JSON, TOML, Dockerfiles, Compose/env files, lock files or generated assets. Preserve any existing third-party notices.

## Verification references

Use the commands in `docs/testing.md` appropriate to the changed layers. For repository structure and release-link checks:

```bash
python3 .agents/skills/release-evidence/scripts/verify_repository.py
```

A release closeout additionally requires lint, unit/build checks, supported Compose configurations and real runtime proof for affected retrieval backends; never claim a run that was not performed.
