# Release 0.8 — Optional LLM-as-a-Judge evaluation

## Status

**Implemented; offline and locally verified.** `MRA-033` provides an optional local judge CLI; one approved real run completed with no technical errors, but several judge explanations were wrong. Existing native/LlamaIndex RAG and both evaluated fixture suites stay unchanged.

## Goal

Use the [optional developer-only DeepEval CLI](../../rag-judge.md) to assess saved CiteNook synthetic fixture results with a local Ollama model. The CLI writes separate structured scores and a Markdown report. It adds no third RAG backend, product feature, or CI model calls.

## Story

| Story | Scope | Status |
| --- | --- | --- |
| [MRA-033](stories/MRA-033-optional-deepeval-judge.md) | Evaluate saved baseline/safety responses with controlled judge metrics | Implemented |

## Guardrails for evaluation accuracy

- Existing 12-case baseline and 8-case adversarial test results remain immutable; judge results are written to **new output files**.
- The current API returns **citations and cited snippets**, not all chunks considered by the retriever. `FaithfulnessMetric` given citation snippets must be reported as **faithfulness to cited excerpts**, not full retrieval faithfulness/precision/recall.
- `AnswerRelevancyMetric` can grade question/answer relevance without retrieved-context data. For cases without suitable cited snippets, the context-based metric is **N/A**, not fabricated or interpreted as a zero.
- LLM-as-a-Judge scores are **model-dependent** and can vary between runs; do not claim deterministic reproducibility of scores, general factual accuracy or security certification.
- Keep DeepEval an optional evaluation/dev dependency, not an application import or required Docker/CI service. Only synthetic fixture text is eligible for a configured judge; do not send personal uploads or conversation data to a remote endpoint.

## Evidence and scope

The [Release 0.8 verification](verification.md) records offline tests, dependency isolation and unchanged historical evidence. The [recorded local run](verification.md#first-approved-local-judge-run) has limited coverage and observed judge reasoning errors. The [RAG skill](../../../.agents/skills/rag-pipeline/SKILL.md) covers evaluation work; no new agent or skill is required.

Out of scope: production prompt changes, Langfuse, Ragas in parallel, new API/DB endpoints, model fine-tuning, hosted evaluation dashboards, paid/default judge calls in CI, changes to historical measurements, or claims that test-only metrics prove prompt-injection protection.
