# Release 0.7: RAG safety regression checks

## Status

Implemented. `MRA-032` adds a separate eight-case suite and [real native/LlamaIndex measurements](comparison.md): four and three cases passed, respectively. Observed failures remain documented; no full prompt-injection protection is claimed.

## Objective

The existing API-based evaluator now has a separate prompt-injection suite. It checks how each deployed RAG backend handles untrusted instructions inside synthetic documents and questions. The Release 0.6 twelve-case comparison and its results remain unchanged.

## Story map

| Order | Story | Focus | Status |
| ---: | --- | --- | --- |
| 1 | [MRA-032](stories/MRA-032-add-adversarial-rag-fixtures.md) | Isolated prompt-injection fixtures, checks, and measured results | Implemented |

## Scope

- Reuse the existing evaluator, public HTTP API, synthetic data, and cleanup rules.
- Keep the existing 12-case default suite and its published 2026-10-14 proof unchanged.
- Add a small **separate** suite of safe, fictional source- and question-level instruction attempts.
- Test citation validity, supported facts, no-answer rules, and whether controlled injected marker text appears in replies.
- Evaluate native and LlamaIndex deployments one at a time with the same selected models and settings.
- Record actual passes, failures, test limits, and runtime evidence without claiming complete prompt-injection protection.

## Execution and evidence

The user approved implementation and both isolated model runs. The [story workflow](../../story-workflow.md) still requires separate commit approval. No extra agents or production RAG changes were needed.

[Release 0.7 verification](verification.md) records the focused/full checks, run commands and cleanup proof. The [evaluation guide](../../rag-evaluation.md) documents `--suite baseline` (the unchanged default) and `--suite safety`; [measured findings](comparison.md) link every real answer and observed failure.

## Out of scope

No new RAG backend, production prompt/guardrail modification, Ragas or DeepEval, model judge, UI, external LLM service, MCP, tool calling, or agent workflow. A failed safety check must be documented, not silently fixed or hidden as part of this evaluation-only release.
