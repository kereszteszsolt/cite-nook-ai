# MRA-007: Answer from documents with references

## Status

Implemented

## User story

As a user, I want answers grounded in indexed documents with inspectable references so that I can verify where the information came from.

## Acceptance criteria

- [x] The question is embedded with the conversation embedding model.
- [x] Retrieval searches only ready chunks created with the same embedding model.
- [x] The top passages are numbered deterministically as S1, S2, and so on.
- [x] The chat prompt requires source-only answering, source markers, and explicit insufficiency when needed.
- [x] The answer is generated with the conversation chat model through the official Ollama Python client.
- [x] The API returns structured document, page, chunk, snippet, and score citations.
- [x] The web app displays references under the assistant answer and links to the original document.

## Out of scope

Features outside the Release 0.1 boundary documented in the release README.

## Verification

Run the focused automated checks and the Docker smoke test described in `docs/testing.md`.

## Implementation evidence

- Retrieval: `GroundedAnswerService` embeds the normalized question with the conversation embedding model, joins `DocumentChunk` to `Document`, filters both model fields plus `ready` status, orders by cosine distance and chunk UUID, and applies `RAG_TOP_K`.
- Prompt and provider boundary: deterministic retrieval order becomes `S1`, `S2`, and so on. The system prompt permits only current sources, treats their text as untrusted data, requires exact markers and explicit insufficiency, and `OllamaGateway` performs the official-client non-streaming chat request with the conversation chat model.
- Citation integrity: unavailable or missing markers are rejected; only markers actually used in the answer become persisted structured citations. No compatible result produces the explicit insufficiency answer with no fabricated reference.
- API and web flow: `POST /api/conversations/{id}/messages` returns the updated conversation plus both persisted messages. The React composer remains fixed at the viewport bottom, and each assistant reference links to the original file with its source ID, optional page, snippet, and score.

## Focused tests

- `apps/api/tests/test_grounded_answers.py` verifies model selection, ready/model filters, cosine SQL, top-k, deterministic sources, prompt content, bounded history use, cited-source filtering, insufficiency, and invalid-marker rejection.
- `apps/api/tests/test_ollama_gateway.py` verifies the single deterministic official-client chat request plus connection and empty-response failures.
- `apps/web/src/App.test.tsx` and `apps/web/src/api.test.ts` verify question submission, returned message rendering, page-aware references, similarity, original-file links, and the JSON API boundary.

## Verification evidence

Verified on 2026-08-22:

- Focused checks — Ruff passed; 23 focused API tests and all 15 web tests passed.
- Full repository gates — lint passed for all three packages; 52 API, 15 web, and 1 brand test passed; all three production builds completed.
- External-Ollama Docker smoke — the question used `qwen3-embedding:0.6b` against 960 compatible 1024-dimensional pgvector chunks and `qwen3.5:9b` returned a grounded answer with valid `[S1]` through `[S4]` markers.
- Citation audit — all four persisted citations joined to their exact chunk UUID; every document was `ready`, and both document and chunk stored `qwen3-embedding:0.6b`.
- Browser smoke — headless Chromium displayed the persisted answer, scrollable reference content, and a responsive question composer fixed at the viewport bottom.
- Original-file link smoke — the first reference returned HTTP 200 with inline `safe-name.md` content.
- Cleanup smoke — the dedicated conversation and both of its messages were removed after verification; no document was changed.

## Known limitations

- Release 0.1 answers are non-streaming. Authentication, OCR, reranking, hybrid retrieval, agents, and cloud features remain outside the documented release boundary.
