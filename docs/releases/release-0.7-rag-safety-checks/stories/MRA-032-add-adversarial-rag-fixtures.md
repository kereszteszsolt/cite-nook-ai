# MRA-032: Add adversarial RAG fixtures

## Status

Implemented

## User story

As a maintainer, I want to test if text in files can steer AI replies.

## Goal

Check if the app treats file text as facts, not as rules.

## Dependencies

`MRA-031`.

## Acceptance criteria

- [x] A separate suite adds six to eight safe, fictional prompt-injection cases in source documents and questions.
- [x] The CLI lets a user pick that suite while the original twelve-case default and fixture hash stay unchanged.
- [x] Safety checks cover cited sources, supported facts or no-answer replies, and forbidden test marker text.
- [x] Each run records the chosen suite, backend, models, case checks, and failures with no broad security score.
- [x] Both suites use the same isolated uploads, document readiness checks, and owned-record cleanup rules.
- [x] Mocked HTTP tests cover suite selection, unsafe replies, expected answers, and cleanup after errors.
- [x] Real native and LlamaIndex runs use the same model pair and settings, with all observed failures recorded.
- [x] The evaluation guide and README link real safety results only after evidence is available.

## Out of scope

No new security framework, production answer rule, prompt change, model judge, frontend feature, or new API. This story measures selected prompt-injection cases; it does not certify protection against all attacks. Never use real credentials, private documents, or destructive instructions in fixtures.
