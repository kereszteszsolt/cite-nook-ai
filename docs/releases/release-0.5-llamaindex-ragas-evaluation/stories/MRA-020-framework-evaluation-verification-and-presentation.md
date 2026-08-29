# MRA-020: Verify and present the framework/evaluation release

## Status

Implemented

## User story

As a prospective contributor or technical reviewer, I want concise evidence and accurate documentation for the LlamaIndex comparison path and Ragas evaluation harness so that I can reproduce them locally and understand exactly what they do and do not replace in CiteNook.

## Context

Release 0.5 is intended to demonstrate hands-on framework and evaluation experience with minimal product risk. Its credibility depends on preserving the direct CiteNook RAG path, recording real local execution evidence, and avoiding claims that a tiny fixture or LLM judge provides production-grade benchmarking.

## Scope

Complete dependency, regression, local-smoke, cleanup, and documentation verification. Update only the repository surfaces directly affected by the two developer commands, then close the release stories according to recorded evidence.

## Acceptance criteria

- [x] Run the complete repository lint, test, build, release-evidence, and both Compose configuration checks, recording any pre-existing failure separately from Release 0.5 changes.
- [x] Verify the base API/worker installation excludes optional LlamaIndex/Ragas packages, while the documented optional installation resolves reproducibly on the supported Python versions and passes focused tests.
- [x] Verify focused coverage for LlamaIndex chunk filtering, node/metadata mapping, query/result handling, no-write behavior, Ragas dataset validation, API setup/polling, metric-input mapping, artifact serialization, failures, and cleanup.
- [x] Run one privacy-safe LlamaIndex smoke query over existing indexed chunks with local Ollama and retain only non-sensitive evidence: command, versions, models, eligible chunk count, elapsed time, source identifiers, and limitations.
- [x] Run one complete Ragas fixture evaluation with local Ollama, verify every case is represented in CSV/JSON output, and confirm no temporary conversation, messages, document, chunks, job, or uploaded file remains after cleanup.
- [x] Confirm the two commands do not alter the default FastAPI route behavior, React UI, worker ingestion, database schema, Compose services, configured model ownership, or direct grounded-answer/citation contract.
- [x] Update `docs/architecture.md` with a clearly dashed developer-tooling boundary: the direct product RAG remains primary, while LlamaIndex reads existing chunks for comparison and Ragas calls the local application/evaluator flow.
- [x] Update `docs/rag-pipeline.md` with the purpose, data flow, non-production status, and limitations of both additions, including the distinction between cited contexts and all raw retrieved candidates.
- [x] Update `docs/testing.md` and the relevant development instructions with exact optional-install, LlamaIndex-query, and Ragas-evaluation commands, required local models, output locations, cleanup behavior, and troubleshooting guidance.
- [x] Add a concise root README capability/release mention only after both commands are implemented and verified. Describe LlamaIndex as an optional comparison path and Ragas as local evaluation tooling, not as requirements for CiteNook operation.
- [x] Do not regenerate product screenshots because Release 0.5 introduces no supported visual product state. A sanitized console excerpt or small results table may be documented instead.
- [x] Document evaluator limitations: score variance, model dependence, small fixture size, lack of human judge alignment, and the absence of a full raw top-k retrieval trace through the current public response.
- [x] Review committed files for model outputs, private documents, absolute local paths, API keys, telemetry endpoints, database credentials beyond existing development defaults, and generated experiment artifacts that should remain ignored.
- [x] Update the Release 0.5 overview and MRA-018 through MRA-020 from `Planned` only when each checked criterion is backed by code, configuration, tests, local execution evidence, or updated documentation.

## Verification plan

- Reproduce both developer commands from the documented clean setup and compare their output schema with the committed examples.
- Validate all new Markdown links, command paths, optional dependency names, environment variables, and ignored artifact directories.
- Diff the database schema and supported HTTP/OpenAPI contract before and after Release 0.5; no intentional change is expected.
- Review the final diff to ensure it contains only optional framework/evaluation dependencies, bounded tooling, focused tests, ignored local artifacts, and directly affected documentation.

## Out of scope

Marketing benchmarks, hosted demos, framework migration, a product backend selector, UI evaluation views, screenshots without a UI change, cloud observability, agents, reranking, hybrid retrieval, unrelated dependency upgrades, and broad refactoring are excluded.

## Implementation notes

A successful release should support this precise portfolio statement: CiteNook retains a custom local Ollama + pgvector RAG implementation, includes an optional LlamaIndex query comparison over existing indexed chunks, and provides a reproducible local Ragas evaluation harness with Ollama-assisted metrics. Publish a narrower statement if the verified implementation delivers less than this target.

## Comments

- Repository verification on 2026-08-28 passed the 3-agent/3-skill/20-story audit, lock check, Ruff, 104 API tests, API bytecode build, 1 brand test, 48 web tests, root `npm run lint`, `npm run test`, `npm run build`, and both Compose configuration checks. Native npm is unavailable because the checkout is accessed through WSL1 (`WSL 1 is not supported`); the npm gates therefore ran in an isolated `node:26.3.0-bookworm-slim` container. That host limitation is separate from Release 0.5 code.
- Clean uv-managed Python 3.13.14 and 3.14.6 environments resolved the locked `framework-evaluation` extra and each passed the same combined 43 focused tests. Both used `llama-index-core==0.14.24`, `ragas==0.4.3`, `openai==2.54.0`, `langchain-community==0.4.1`, and `scikit-network==0.33.5`; Python 3.14 compiled the final package from its locked source distribution. The rebuilt normal API image reported `llama_index`, `ragas`, and `openai` all absent.
- The privacy-safe comparison used `citenook-llamaindex --question "When is Mosslight open, and which days is it closed?" --chat-model llama3.1:8b --embedding-model qwen3-embedding:0.6b --document-id 19a492e5-bc97-49b8-b9fa-70fd107db751 --max-chunks 20 --top-k 2 --request-timeout 300 --pretty` from the clean Python 3.13 environment on the Compose network. LlamaIndex returned `answered` in 51,035 ms from 2 eligible chunks with source IDs `08eb66fd-1b56-45b9-aa5e-4cbcb1ad21f5` and `b570760b-9200-40a8-b16f-530a5cb5c2ee`. The selected document stayed `ready` with 2 chunks, and global row counts stayed at 9 documents, 962 chunks, 9 jobs, 2 conversations, and 6 messages during the query, confirming the command made no product writes. This single local query is functional evidence, not a performance or quality comparison.
- Ragas run `mra019-20260828T144238Z` completed and scored all 8 invented cases with local `llama3.1:8b` answer/evaluator roles and `qwen3-embedding:0.6b`: aggregate Faithfulness `0.8` and Factual Correctness `0.82375`. JSON and CSV contained the same exact 8 case IDs, all 16 per-case values were within `0..1`, cleanup errors were empty, and generated artifacts remained ignored under `evals/experiments/`.
- After deleting the dedicated comparison document, counts returned to 8 documents, 960 chunks, 8 jobs, 2 conversations, and 6 messages. Targeted checks found zero MRA-019/MRA-020 documents, chunks, jobs, conversations, messages, or upload-volume files. No unrelated local resource was exposed or deleted.
- The release diff from the planning commit changes no React, router, schema, model, worker, migration, or Compose surface; only optional evaluation modules, tests, exact dependency/lock entries, invented fixtures, ignore rules, and directly affected documentation are present. All 30 changed local Markdown links resolved, `git diff --check` passed, no screenshot changed, and no experiment artifact is tracked. Privacy hits were limited to deliberate unsafe-input test fixtures, the documented local Ollama adapter placeholder, and statements that telemetry is disabled.
- The documented results remain model-assisted review signals. They can vary by model and run, use only eight invented cases, have no human-judge alignment study, reuse the same local model for answer and evaluator in the recorded run, and evaluate cited snippets rather than a complete raw top-k retrieval trace.
