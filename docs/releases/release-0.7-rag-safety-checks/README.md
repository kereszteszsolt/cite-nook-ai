# Release 0.7: RAG safety regression checks

## Status

Planned. `MRA-032` is not implemented and no adversarial evaluation has run.

## Objective

Add a small, separate prompt-injection test suite to the existing API-based RAG evaluation. Check how each deployed RAG backend handles untrusted instructions inside synthetic documents and questions. Preserve the Release 0.6 twelve-case comparison and its results.

## Story map

| Order | Story | Focus | Status |
| ---: | --- | --- | --- |
| 1 | [MRA-032](stories/MRA-032-add-adversarial-rag-fixtures.md) | Isolated prompt-injection fixtures, checks, and measured results | Planned |

## Scope

- Reuse the existing evaluator, public HTTP API, synthetic data, and cleanup rules.
- Keep the existing 12-case default suite and its published 2026-10-14 proof unchanged.
- Add a small **separate** suite of safe, fictional source- and question-level instruction attempts.
- Test citation validity, supported facts, no-answer rules, and whether controlled injected marker text appears in replies.
- Evaluate native and LlamaIndex deployments one at a time with the same selected models and settings.
- Record actual passes, failures, test limits, and runtime evidence without claiming complete prompt-injection protection.

## Execution and evidence

Follow the [story workflow](../../story-workflow.md). Get approval before implementing `MRA-032` and again before committing. Do not start extra agents or redesign the existing RAG paths for a test-only change.

[Release 0.7 verification](verification.md) starts empty on purpose; populate it only after focused checks and real evaluation runs. The existing [evaluation guide](../../rag-evaluation.md) documents the implemented Release 0.6 runner, not yet this planned safety suite.

## Out of scope

No new RAG backend, production prompt/guardrail modification, Ragas or DeepEval, model judge, UI, external LLM service, MCP, tool calling, or agent workflow. A failed safety check must be documented, not silently fixed or hidden as part of this evaluation-only release.
