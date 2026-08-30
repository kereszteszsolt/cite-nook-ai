# MRA-021: Align repository documentation with Release 0.5

## Status

Implemented

## User story

As a maintainer or technical reviewer, I want the verified Release 0.5 behavior reflected consistently across CiteNook's maintained documentation so that LlamaIndex and Ragas are understandable without relying only on release stories and no page presents stale setup, architecture, testing, or product-boundary information.

## Context

MRA-018 through MRA-020 implemented and verified the optional LlamaIndex comparison command and local Ragas evaluation harness. The main README, architecture, RAG pipeline, development, and testing guides already contain targeted additions, but the repository still needs one explicit documentation-wide reconciliation pass. For example, the documentation index still labels `docs/rag-pipeline.md` as a roadmap after that page became the current pipeline guide.

This story treats release stories as evidence rather than the sole product documentation. It audits every maintained non-release Markdown page, updates only the surfaces affected by Release 0.5, and records why unrelated user, brand, design, and screenshot documentation remains unchanged when appropriate.

## Scope

Reconcile the root README and maintained pages under `docs/` with the implemented Release 0.5 behavior. Keep the direct Ollama + pgvector product path primary, keep both additions explicitly optional and developer-only, and make navigation, terminology, commands, limitations, and cross-links consistent.

Expected documentation surfaces are `README.md`, `docs/README.md`, `docs/llamaindex-comparison.md`, `docs/architecture.md`, `docs/rag-pipeline.md`, `docs/development.md`, `docs/testing.md`, and—only where the audit finds a real reader-facing gap—`docs/user-guide.md`, `docs/brand-configuration.md`, `docs/design/README.md`, or `docs/screenshots/README.md`.

## Acceptance criteria

- [x] Inventory every maintained non-release Markdown page and record whether Release 0.5 requires an update or why the page is unaffected; do not edit unrelated pages merely to make the diff larger.
- [x] Keep the root README capability summary concise and accurate: LlamaIndex is an optional bounded comparison over existing chunks, Ragas is local evaluation tooling over an invented fixture, and neither is required for normal CiteNook operation.
- [x] Add a dedicated English LlamaIndex comparison guide, link it from the documentation index and relevant overview/technical pages, and include a verified WSL2 + Compose example with an English question, abridged result, interpretation, no-data behavior, privacy guidance, and cleanup.
- [x] Update `docs/README.md` so navigation labels, page purposes, and Release 0.5 links match the current documents; remove stale wording such as the old RAG-pipeline roadmap label.
- [x] Reconcile `docs/architecture.md` with the implementation: the direct product RAG remains primary, the developer-tooling boundary is visually distinct, LlamaIndex reads existing compatible chunks without writes, and Ragas exercises the public API plus a local evaluator.
- [x] Reconcile `docs/rag-pipeline.md` with the current product and evaluation data flows, including stored-versus-in-memory data, cited snippets versus raw retrieved candidates, cleanup ownership, and non-production limitations.
- [x] Reconcile `docs/development.md` with the actual optional dependency extra and CLI interfaces, including supported Python versions, required local models, exact commands, output locations, cleanup behavior, and actionable troubleshooting.
- [x] Reconcile `docs/testing.md` with focused-test and real-smoke coverage, base-install exclusion, privacy-safe evidence, generated-artifact ignore rules, cleanup checks, evaluator limitations, and the explicit decision not to regenerate screenshots for a non-visual release.
- [x] Review the user guide, brand guide, design handoff, and screenshot gallery for Release 0.5 impact. Preserve their end-user or design scope and add only concise boundary/navigation text when it prevents a real misunderstanding.
- [x] Use consistent names for CiteNook, LlamaIndex, Ragas, `framework-evaluation`, the two CLI commands, local Ollama roles, and the direct Ollama + pgvector path across all maintained documentation.
- [x] Keep run-specific UUIDs, timings, scores, and detailed verification evidence in the release evidence pages; broader documentation may describe verified capabilities and limitations without duplicating one local run as a general benchmark.
- [x] Validate documented commands, options, paths, package names, environment variables, and supported Python claims against the current entry points, lock file, Compose configuration, and CLI `--help` output.
- [x] Validate every changed local Markdown link and heading target, run the repository release-evidence audit and relevant lint/test/build/Compose gates, and record exact outcomes plus any environment limitation.
- [x] Confirm the story changes no application source, public route, schema, worker behavior, Compose service, UI, screenshot, binary asset, fixture, or generated experiment artifact.
- [x] Review the final documentation diff for private source text, model output, local absolute paths, credentials, hosted telemetry, unsupported claims, and duplicated or contradictory guidance.
- [x] Mark MRA-021 and Release 0.5 `Implemented` only after every criterion has criterion-specific evidence; keep both non-complete while any documentation gap or verification step remains.

## Verification plan

- Run `python3 .agents/skills/release-evidence/scripts/verify_repository.py` before and after the reconciliation.
- Compare non-release documentation mentions of LlamaIndex, Ragas, Release 0.5, the optional extra, CLI names, output paths, cleanup, and limitations against the implementation and committed MRA-018 through MRA-020 evidence.
- Run both CLI entry points with `--help` from the locked optional environment and verify every copied flag and default.
- Validate local Markdown links and changed heading fragments with a dependency-free checker.
- Run `git diff --check`, inspect the exact changed-file list, and prove the diff is documentation-only with no screenshots or generated evaluation artifacts.
- Run the repository's relevant lint, test, build, lock, and both Compose configuration checks before claiming completion.

## Out of scope

New application behavior, framework migration, a product backend selector, UI or API additions, database migrations, worker changes, new evaluation metrics or cases, dependency upgrades, model pulls, benchmark claims, screenshot regeneration, design changes, release ZIP creation, and rewriting historical story evidence are excluded.

## Implementation notes

Prefer one canonical explanation for each concern and link to it from shorter summaries. The root README should orient readers, the dedicated LlamaIndex guide should own the complete comparison workflow, architecture and RAG pages should explain boundaries and data flow, development should own optional-environment setup, testing should own verification, and release stories should retain dated evidence. Documentation that is already accurate may remain unchanged when the audit records that decision.

## Comments

- The non-release documentation inventory covered the root README plus every maintained page under `docs/`. Release 0.5 required updates to the root overview/navigation, documentation index, architecture, RAG pipeline, development, testing, and user-guide boundary, plus the new `docs/llamaindex-comparison.md`. `docs/brand-configuration.md` remained unchanged because identifiers and assets did not change; `docs/design/README.md` and `docs/screenshots/README.md` remained unchanged because the release adds no product UI or visual state.
- The new English guide explains when the optional command is appropriate, its read/no-write boundary, WSL2 prerequisites, explicit document selection, multiple-document bounds, normal-product comparison, structured output, privacy, no-data behavior, cleanup, direct-host limitations, and troubleshooting. Its complete Mosslight example uses the English question `When is Mosslight open, and which days is it closed?` without publishing a real UUID, timing, score, or private source text.
- Both CLI `--help` surfaces passed from the locked Python 3.13 environment. The final documented WSL container form uses `ghcr.io/astral-sh/uv:python3.13-bookworm-slim`, a read-only checkout mount, and a minimal temporary project copy because setuptools cannot update existing egg-info timestamps on a read-only project root. That exact form passed `--help` and a real Compose-network `no_data` query in 30 ms with the all-zero document UUID, `llama3.1:8b`, and `qwen3-embedding:0.6b`; it returned zero eligible chunks and sources without unrelated fallback.
- Database counts stayed at 8 documents, 960 chunks, 8 jobs, 2 conversations, and 12 messages after the no-data query, confirming no product write. The separately completed WSL Ragas run `mra019-20260829T082538Z` scored all 8 invented cases, produced matching ignored JSON/CSV artifacts, reported no cleanup errors, and left the same baseline counts with zero run-owned database or upload-volume resources.
- Dependency-free documentation validation checked 9 changed Markdown files, 61 local links, and 6 heading fragments. `git diff --check`, terminology/path review, privacy scanning, and the generated-artifact check passed; no application source, package/configuration, Compose, fixture, design, screenshot, or binary asset changed.
- Final gates on 2026-08-29 passed the 3-agent/3-skill/21-story repository audit, lock check, Ruff, 104 API tests, API bytecode build, root npm lint/test/build, and both Compose configurations. The checkout's native Windows npm shim still reports `WSL 1 is not supported` under WSL2, so npm gates ran in an isolated `node:26.3.0-bookworm-slim` container with telemetry disabled; this host-tooling limitation is unrelated to the documentation changes.
