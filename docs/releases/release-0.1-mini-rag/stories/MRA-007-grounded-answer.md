# MRA-007: Answer from documents with references

## Status

Planned

## User story

As a user, I want answers grounded in indexed documents with inspectable references so that I can verify where the information came from.

## Acceptance criteria

- [ ] The question is embedded with the conversation embedding model.
- [ ] Retrieval searches only ready chunks created with the same embedding model.
- [ ] The top passages are numbered deterministically as S1, S2, and so on.
- [ ] The chat prompt requires source-only answering, source markers, and explicit insufficiency when needed.
- [ ] The answer is generated with the conversation chat model through the official Ollama Python client.
- [ ] The API returns structured document, page, chunk, snippet, and score citations.
- [ ] The web app displays references under the assistant answer and links to the original document.

## Out of scope

Features outside the Release 0.1 boundary documented in the release README.

## Verification

Run the focused automated checks and the Docker smoke test described in `docs/testing.md`.
