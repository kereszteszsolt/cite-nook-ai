# MRA-033: Add optional DeepEval judge metrics for saved RAG fixtures

## Status

Implemented

## User story

As a user, I want to check if my saved AI answers are good.

## Goal

Let a judge score saved test answers.

## Dependencies

`MRA-032` implemented; the existing `baseline` and `safety` suite outputs must remain available and unmodified.

## Acceptance criteria

- [x] Add a minimal, optional `deepeval` dependency in the API evaluation/dev tooling; normal API, worker, web, Docker and CI remain usable with no judge installed or configured.
- [x] A documented CLI accepts an existing `results.json` from either suite, validates schema/suite identity, and writes **separate** structured scores and a Markdown report without changing the input.
- [x] Provide `AnswerRelevancyMetric` for suitable completed question/answer pairs; include `FaithfulnessMetric` only for cases with **cited snippets**, explicitly labeled `cited-excerpt faithfulness` (not full retrieved-context faithfulness).
- [x] Missing or empty citations, no-answer cases, malformed records and incomplete/failed runs are handled as **N/A / skipped / error** with reasons, never silently counted as zero or success.
- [x] Judge settings must be explicit, logged as metadata and used only with synthetic test data, with separate user approval for remote or paid calls.
- [x] Store per-case score, judge reason, skip/error reason, timestamps, model/version info and known usage when available; aggregate only comparable cases and distinguish judge verdicts from existing deterministic fixture pass/fail checks.
- [x] Mocked offline tests cover valid scores, bad input, no-answer/citation gaps and judge errors while keeping all prior fixtures and reports unchanged.
- [x] Document setup, commands, cost/privacy rules and limits, and record actual judge scores only after a real run.

## Out of scope

No new retrieval tracer, DeepEval instrumentation in production requests, new UI, third-party score dashboard, Ragas, CI calls to paid models, retrieval recall claims, runtime guardrails, prompt changes or general safety guarantees. This is an optional assessment of already-saved **synthetic** evaluation outputs.
