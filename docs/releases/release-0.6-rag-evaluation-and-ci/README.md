# Release 0.6: Small RAG evaluation and CI

## Status

In progress. `MRA-029` implements the fixture runner with mocked-HTTP proof. Hosted CI and real backend measurements remain planned.

## Objective

Compare the two existing RAG deployments with the same small, invented document set and questions. Automate existing checks in GitHub Actions, then publish only real measurements. Keep the user interface, RAG contracts, and backend selection unchanged.

## Story map

| Order | Story | Title | Main result | Status |
| ---: | --- | --- | --- | --- |
| 1 | [MRA-029](stories/MRA-029-add-a-small-rag-evaluation.md) | Add a small RAG evaluation | Repeatable API-based fixture runs | Implemented |
| 2 | [MRA-030](stories/MRA-030-run-existing-checks-in-ci.md) | Run existing checks in CI | One lean GitHub Actions workflow | Planned |
| 3 | [MRA-031](stories/MRA-031-publish-measured-results.md) | Publish measured results | Real comparison and updated README | Planned |

## Evaluation boundary

- Reuse the public `/api` routes; do not add a third RAG pipeline or an evaluation API.
- Start `native` and `llamaindex` one at a time, each with its own isolated data.
- Use three small invented documents and twelve questions, including questions with no supported answer.
- Use the same installed chat model, embedding model, question set, and `RAG_TOP_K` for both runs.
- Check expected document citations, simple answer facts, the fixed no-answer reply, and API-reported `responseDurationMs`.
- Label those results as *fixture checks*, not retrieval recall, factual accuracy, or model-graded faithfulness.
- Use only records created by the evaluation; do not read or delete a user's documents or conversations.
- Keep local model runtime checks out of hosted CI; real RAG runs are manual and documented.

## Execution

Follow [story and Codex workflow](../../story-workflow.md): one story at a time, explicit implementation and commit approval, and acceptance criteria in order. Use only the needed implementation role; do not start parallel agents for these small stories.

The [fixture runner guide](../../rag-evaluation.md) describes the implemented CLI, data, checks, and cleanup. Real measurements will be added by `MRA-031`; mocked test output is not a backend benchmark.

## Proof

[Release 0.6 verification](verification.md) records checks and actual results as they occur. Do not mark a story or release implemented before its evidence exists.

## Out of scope

No Ragas, external LLM provider, agent workflow, MCP, extra RAG framework, hybrid search, reranker, authentication, or UI feature belongs to Release 0.6. Those are optional future ideas, not planned stories.
