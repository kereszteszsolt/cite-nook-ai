# MRA-020: Verify and present the framework/evaluation release

## Status

Planned

## User story

As a prospective contributor or technical reviewer, I want concise evidence and accurate documentation for the LlamaIndex comparison path and Ragas evaluation harness so that I can reproduce them locally and understand exactly what they do and do not replace in CiteNook.

## Context

Release 0.5 is intended to demonstrate hands-on framework and evaluation experience with minimal product risk. Its credibility depends on preserving the direct CiteNook RAG path, recording real local execution evidence, and avoiding claims that a tiny fixture or LLM judge provides production-grade benchmarking.

## Scope

Complete dependency, regression, local-smoke, cleanup, and documentation verification. Update only the repository surfaces directly affected by the two developer commands, then close the release stories according to recorded evidence.

## Acceptance criteria

- [ ] Run the complete repository lint, test, build, release-evidence, and both Compose configuration checks, recording any pre-existing failure separately from Release 0.5 changes.
- [ ] Verify the base API/worker installation excludes optional LlamaIndex/Ragas packages, while the documented optional installation resolves reproducibly on the supported Python versions and passes focused tests.
- [ ] Verify focused coverage for LlamaIndex chunk filtering, node/metadata mapping, query/result handling, no-write behavior, Ragas dataset validation, API setup/polling, metric-input mapping, artifact serialization, failures, and cleanup.
- [ ] Run one privacy-safe LlamaIndex smoke query over existing indexed chunks with local Ollama and retain only non-sensitive evidence: command, versions, models, eligible chunk count, elapsed time, source identifiers, and limitations.
- [ ] Run one complete Ragas fixture evaluation with local Ollama, verify every case is represented in CSV/JSON output, and confirm no temporary conversation, messages, document, chunks, job, or uploaded file remains after cleanup.
- [ ] Confirm the two commands do not alter the default FastAPI route behavior, React UI, worker ingestion, database schema, Compose services, configured model ownership, or direct grounded-answer/citation contract.
- [ ] Update `docs/architecture.md` with a clearly dashed developer-tooling boundary: the direct product RAG remains primary, while LlamaIndex reads existing chunks for comparison and Ragas calls the local application/evaluator flow.
- [ ] Update `docs/rag-pipeline.md` with the purpose, data flow, non-production status, and limitations of both additions, including the distinction between cited contexts and all raw retrieved candidates.
- [ ] Update `docs/testing.md` and the relevant development instructions with exact optional-install, LlamaIndex-query, and Ragas-evaluation commands, required local models, output locations, cleanup behavior, and troubleshooting guidance.
- [ ] Add a concise root README capability/release mention only after both commands are implemented and verified. Describe LlamaIndex as an optional comparison path and Ragas as local evaluation tooling, not as requirements for CiteNook operation.
- [ ] Do not regenerate product screenshots because Release 0.5 introduces no supported visual product state. A sanitized console excerpt or small results table may be documented instead.
- [ ] Document evaluator limitations: score variance, model dependence, small fixture size, lack of human judge alignment, and the absence of a full raw top-k retrieval trace through the current public response.
- [ ] Review committed files for model outputs, private documents, absolute local paths, API keys, telemetry endpoints, database credentials beyond existing development defaults, and generated experiment artifacts that should remain ignored.
- [ ] Update the Release 0.5 overview and MRA-018 through MRA-020 from `Planned` only when each checked criterion is backed by code, configuration, tests, local execution evidence, or updated documentation.

## Verification plan

- Reproduce both developer commands from the documented clean setup and compare their output schema with the committed examples.
- Validate all new Markdown links, command paths, optional dependency names, environment variables, and ignored artifact directories.
- Diff the database schema and supported HTTP/OpenAPI contract before and after Release 0.5; no intentional change is expected.
- Review the final diff to ensure it contains only optional framework/evaluation dependencies, bounded tooling, focused tests, ignored local artifacts, and directly affected documentation.

## Out of scope

Marketing benchmarks, hosted demos, framework migration, a product backend selector, UI evaluation views, screenshots without a UI change, cloud observability, agents, reranking, hybrid retrieval, unrelated dependency upgrades, and broad refactoring are excluded.

## Implementation notes

A successful release should support this precise portfolio statement: CiteNook retains a custom local Ollama + pgvector RAG implementation, includes an optional LlamaIndex query comparison over existing indexed chunks, and provides a reproducible local Ragas evaluation harness with Ollama-assisted metrics. Publish a narrower statement if the verified implementation delivers less than this target.
