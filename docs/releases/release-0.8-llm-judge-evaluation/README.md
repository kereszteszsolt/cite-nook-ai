# Release 0.8 — Optional LLM-as-a-Judge evaluation

## Status

**Planned, not implemented.** One small story, `MRA-033`; existing native/LlamaIndex RAG and both evaluated fixture suites stay unchanged.

## Goal

Add an **optional, developer-only DeepEval quality assessment** on top of saved CiteNook fixture results. This introduces a popular evaluation framework without adding a third RAG backend, additional product features or expensive CI model calls.

## Story

| Story | Scope | Status |
| --- | --- | --- |
| [MRA-033](stories/MRA-033-optional-deepeval-judge.md) | Evaluate saved baseline/safety responses with controlled judge metrics | Planned |

## Guardrails for evaluation accuracy

- Existing 12-case baseline and 8-case adversarial test results remain immutable; judge results are written to **new output files**.
- The current API returns **citations and cited snippets**, not all chunks considered by the retriever. `FaithfulnessMetric` given citation snippets must be reported as **faithfulness to cited excerpts**, not full retrieval faithfulness/precision/recall.
- `AnswerRelevancyMetric` can grade question/answer relevance without retrieved-context data. For cases without suitable cited snippets, the context-based metric is **N/A**, not fabricated or interpreted as a zero.
- LLM-as-a-Judge scores are **model-dependent** and can vary between runs; do not claim deterministic reproducibility of scores, general factual accuracy or security certification.
- Keep DeepEval an optional evaluation/dev dependency, not an application import or required Docker/CI service. Only synthetic fixture text is eligible for a configured judge; do not send personal uploads or conversation data to a remote endpoint.

## Codex-friendly effort estimate

**Estimated with Codex doing most implementation:** around **2–5 hours of Codex iterations/integration checks + 30–60 minutes of user review/commit work**. This is an estimate, not an observed duration. A suitable local judge and any approved runtime execution may add time. One story avoids an extra plan/commit cycle.

## Evidence and scope

Use the [Release 0.8 verification](verification.md) to record actual results. The [RAG skill](../../../.agents/skills/rag-pipeline/SKILL.md) already covers evaluation work: **no new agent or skill is required**.

Out of scope: production prompt changes, Langfuse, Ragas in parallel, new API/DB endpoints, model fine-tuning, hosted evaluation dashboards, paid/default judge calls in CI, changes to historical measurements, or claims that test-only metrics prove prompt-injection protection.
