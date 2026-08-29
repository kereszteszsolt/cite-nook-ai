# MRA-021: Align repository documentation with Release 0.5

## Status

Planned

## User story

As a maintainer or technical reviewer, I want the verified Release 0.5 behavior reflected consistently across CiteNook's maintained documentation so that LlamaIndex and Ragas are understandable without relying only on release stories and no page presents stale setup, architecture, testing, or product-boundary information.

## Context

MRA-018 through MRA-020 implemented and verified the optional LlamaIndex comparison command and local Ragas evaluation harness. The main README, architecture, RAG pipeline, development, and testing guides already contain targeted additions, but the repository still needs one explicit documentation-wide reconciliation pass. For example, the documentation index still labels `docs/rag-pipeline.md` as a roadmap after that page became the current pipeline guide.

This story treats release stories as evidence rather than the sole product documentation. It audits every maintained non-release Markdown page, updates only the surfaces affected by Release 0.5, and records why unrelated user, brand, design, and screenshot documentation remains unchanged when appropriate.

## Scope

Reconcile the root README and maintained pages under `docs/` with the implemented Release 0.5 behavior. Keep the direct Ollama + pgvector product path primary, keep both additions explicitly optional and developer-only, and make navigation, terminology, commands, limitations, and cross-links consistent.

Expected documentation surfaces are `README.md`, `docs/README.md`, `docs/architecture.md`, `docs/rag-pipeline.md`, `docs/development.md`, `docs/testing.md`, and—only where the audit finds a real reader-facing gap—`docs/user-guide.md`, `docs/brand-configuration.md`, `docs/design/README.md`, or `docs/screenshots/README.md`.

## Acceptance criteria

- [ ] Inventory every maintained non-release Markdown page and record whether Release 0.5 requires an update or why the page is unaffected; do not edit unrelated pages merely to make the diff larger.
- [ ] Keep the root README capability summary concise and accurate: LlamaIndex is an optional bounded comparison over existing chunks, Ragas is local evaluation tooling over an invented fixture, and neither is required for normal CiteNook operation.
- [ ] Update `docs/README.md` so navigation labels, page purposes, and Release 0.5 links match the current documents; remove stale wording such as the old RAG-pipeline roadmap label.
- [ ] Reconcile `docs/architecture.md` with the implementation: the direct product RAG remains primary, the developer-tooling boundary is visually distinct, LlamaIndex reads existing compatible chunks without writes, and Ragas exercises the public API plus a local evaluator.
- [ ] Reconcile `docs/rag-pipeline.md` with the current product and evaluation data flows, including stored-versus-in-memory data, cited snippets versus raw retrieved candidates, cleanup ownership, and non-production limitations.
- [ ] Reconcile `docs/development.md` with the actual optional dependency extra and CLI interfaces, including supported Python versions, required local models, exact commands, output locations, cleanup behavior, and actionable troubleshooting.
- [ ] Reconcile `docs/testing.md` with focused-test and real-smoke coverage, base-install exclusion, privacy-safe evidence, generated-artifact ignore rules, cleanup checks, evaluator limitations, and the explicit decision not to regenerate screenshots for a non-visual release.
- [ ] Review the user guide, brand guide, design handoff, and screenshot gallery for Release 0.5 impact. Preserve their end-user or design scope and add only concise boundary/navigation text when it prevents a real misunderstanding.
- [ ] Use consistent names for CiteNook, LlamaIndex, Ragas, `framework-evaluation`, the two CLI commands, local Ollama roles, and the direct Ollama + pgvector path across all maintained documentation.
- [ ] Keep run-specific UUIDs, timings, scores, and detailed verification evidence in the release evidence pages; broader documentation may describe verified capabilities and limitations without duplicating one local run as a general benchmark.
- [ ] Validate documented commands, options, paths, package names, environment variables, and supported Python claims against the current entry points, lock file, Compose configuration, and CLI `--help` output.
- [ ] Validate every changed local Markdown link and heading target, run the repository release-evidence audit and relevant lint/test/build/Compose gates, and record exact outcomes plus any environment limitation.
- [ ] Confirm the story changes no application source, public route, schema, worker behavior, Compose service, UI, screenshot, binary asset, fixture, or generated experiment artifact.
- [ ] Review the final documentation diff for private source text, model output, local absolute paths, credentials, hosted telemetry, unsupported claims, and duplicated or contradictory guidance.
- [ ] Mark MRA-021 and Release 0.5 `Implemented` only after every criterion has criterion-specific evidence; keep both non-complete while any documentation gap or verification step remains.

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

Prefer one canonical explanation for each concern and link to it from shorter summaries. The root README should orient readers, architecture and RAG pages should explain boundaries and data flow, development should own setup and operation, testing should own verification, and release stories should retain dated evidence. Documentation that is already accurate may remain unchanged when the audit records that decision.
