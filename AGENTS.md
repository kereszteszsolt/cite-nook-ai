# AGENTS.md

## Project

**CiteNook** is the display name for the `cite-nook-ai` repository. It is a local document question-answering app built with React, FastAPI, PostgreSQL/pgvector, a separate ingestion worker, and Ollama.

The core user path is small: upload a file, wait for indexing, ask a question, receive a grounded answer, and inspect its sources.

## Source of truth

Read these files before Release 0.5 work:

- `docs/story-workflow.md` for story, comment, approval, and evidence rules;
- the active `MRA-*` story for scope and ordered acceptance criteria;
- `docs/releases/release-0.5-clean-rag-backends/implementation-plan.md` for the agreed target;
- `docs/architecture.md` and `docs/rag-pipeline.md` for dependency and data rules.

A plan is not implemented behavior. Do not write docs that claim a planned command or backend already works.

## Product principles

- Keep the app local and usable without accounts.
- Persist files, document state, conversations, messages, selected models, index data, and citations.
- Keep explicit source proof with every grounded answer.
- State that sources are not enough rather than inventing an answer.
- Keep product branding in `packages/brand/brand.json`.
- Keep Ollama outside the application images.
- Keep extraction and embedding work in the separate worker.
- Use PostgreSQL for the queue instead of adding another queue service.

## Release 0.5 architecture rules

- Clean the old code before adding a second backend.
- Use one selected RAG backend in one deployment.
- Keep `native` as the default.
- Do not add a UI backend switch.
- Do not write to or query native and LlamaIndex for the same request.
- Keep prompts, chat, citation checks, timing, and message storage common.
- Use LlamaIndex for node indexing and source retrieval, not a second answer path.
- Keep native modules free of LlamaIndex imports.
- Build concrete dependencies in `app/bootstrap.py` only.
- Keep routers thin and make app services depend on ports.
- Do not leave old and new live code paths after a refactor.
- Do not add empty layers or a repository class for every small query.

## Python boundaries

```text
api             HTTP input and output
application     use-case order and product rules
core            settings and brand
persistence     SQLAlchemy sessions and ORM models
ai              model ports and Ollama adapter
rag             RAG ports and backend adapters
bootstrap.py    concrete dependency setup
main.py         API entry point
worker.py       worker entry point
```

These boundaries are implemented. Keep changes within them unless an approved later story changes the design.

## Web boundaries

- `App.tsx` owns app startup, active workspace, shared errors, and top-level layout.
- `features/conversations` owns chat state, requests, dialogs, views, and tests.
- `features/documents` owns document state, polling, requests, views, and tests.
- Web feature code calls `apps/web/src/api.ts` and does not call `fetch` directly.
- Do not add a state library or router without an approved story.

## Story execution

Work on one story at a time and follow its acceptance criteria in order.

1. Name the next valid story, scope, likely files, and checks.
2. Ask for clear approval before implementation starts.
3. Implement only the approved story.
4. Run checks and show the result.
5. Propose one commit message.
6. Ask for clear approval before creating the commit.
7. Report the commit hash after the approved commit.
8. Ask before starting the next valid story.

Earlier approval does not grant later approval. Do not commit, continue, force-push, reset shared history, or rewrite commits without clear approval.

## Story writing rules

- Use the sections and status values in `docs/story-workflow.md`.
- Keep a prose block at five sentences or less.
- Keep each criterion to one short, testable sentence.
- Use four to eight criteria.
- Keep `User story` plus `Goal` at Flesch Reading Ease 80 or more.
- Put long proof in the release `verification.md` file.
- Do not add issue or limitation sections to story files.

## Source comment rules

- Add a comment only when code cannot make the reason clear.
- Explain why; do not narrate what the code does.
- Prefer one short sentence.
- Use at most three short sentences in one comment block.
- Use at most five short sentences in one docstring.
- Do not paste plans, story text, change history, or logs into source comments.
- Keep SPDX and required tool directives unchanged.

## Codex roles

Use the smallest useful role:

- `architect` plans a cross-cutting story and does not edit files;
- `implementation_worker` implements one approved story;
- `reviewer` checks the approved story, regressions, evidence, and needless complexity.

Repository skills:

- `full-stack-delivery` for React, FastAPI, Docker, and shared contract work;
- `rag-pipeline` for index, retrieval, model, grounding, and citation work;
- `release-evidence` for story, rule, verification, and release records.

Do not invoke every role for a small documentation fix.

## License headers

New hand-written project source files use:

```text
SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
SPDX-License-Identifier: Apache-2.0
```

Keep the header at the start of source files. Do not add it to Markdown, JSON, TOML, Dockerfiles, Compose files, environment examples, ignore files, generated lock files, or binary assets.

## Verification

Run the focused checks for the active story. Before a release claim, run:

```bash
python3 .agents/skills/release-evidence/scripts/verify_repository.py
npm run lint
npm run test
npm run build
docker compose config
docker compose -f docker-compose.yml -f docker-compose.ollama.yml config
docker compose -f docker-compose.yml -f docker-compose.llamaindex.yml config
docker compose -f docker-compose.yml -f docker-compose.llamaindex.yml -f docker-compose.ollama.yml config
```

Runtime proof must use a real installed chat model and embedding model for both native and LlamaIndex deployments.

## Release boundary

Release 0.5 does not add Ragas, cloud providers, hybrid search, reranking, backend scoring, runtime backend switching, or indexed-data migration. Release 0.6 keeps the evaluation plan and will use the two real deployments.
