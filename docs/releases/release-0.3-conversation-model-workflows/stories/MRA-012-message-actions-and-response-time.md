# MRA-012: Widen messages and add answer actions

## Status

Implemented

## User story

As a CiteNook user, I want messages to use the available conversation width and provide familiar answer actions so that long answers are easier to read, copy, retry, and evaluate by response time.

## Acceptance criteria

- [x] User and assistant message bubbles use a wider but bounded share of the conversation panel, remain visually distinct, and stay responsive without page-level overflow.
- [x] Every message provides an accessible copy action that writes its complete text to the clipboard and gives clear success or failure feedback without changing the stored message.
- [x] Every assistant answer provides an accessible retry action that resubmits its preceding user question through the existing grounded-answer path, appends the successful new turn without replacing history, disables conflicting requests while active, and preserves the existing conversation on failure.
- [x] CiteNook measures the server-side grounded-answer duration across embedding, retrieval, and chat work, stores a non-negative millisecond value only on the assistant message, and returns it consistently in new-turn and reloaded-history API responses.
- [x] Existing assistant messages without recorded timing remain readable and show an explicit unavailable timing state, while recorded durations use a concise human-readable millisecond, second, or minute format.
- [x] Copy, retry, and response-time controls use restrained icons with text alternatives, keyboard focus, hover/focus guidance, busy states, and polite status feedback that fit the CiteNook visual language.
- [x] Message actions remain below their message content and references, and neither wider bubbles nor the new controls overlap the composer or break independent message-history scrolling at desktop or mobile widths.

## Out of scope

Branching conversation histories, replacing or deleting an earlier answer during retry, editing message content, copying citations as a separate structured format, token counts, streaming timing, and client-only timing are out of scope. Retry deliberately appends a new persisted user/assistant turn so the original answer and references remain auditable.

## Verification

Run focused API/web tests, all repository lint/test/build gates, both Compose configuration checks, a real PostgreSQL timing migration/reload check, and the MRA-012 browser smoke described in `docs/testing.md`.

## Implementation evidence

- `conversation_messages.response_duration_ms` is a nullable, non-negative persisted field returned as `responseDurationMs`; idempotent startup initialization upgrades existing PostgreSQL volumes.
- `GroundedAnswerService` measures the complete embedding, retrieval, citation-validation, and chat interval with a monotonic server clock and persists it only on the assistant half of the atomic turn.
- `ConversationMessages` renders wider bounded bubbles, per-message clipboard actions, and assistant retry/timing actions after content and citations. Retry submits the exact preceding question through the existing answer endpoint and keeps the linear persisted history.
- Accessible labels, titles, focus styles, live feedback, disabled/busy states, concise duration formatting, and an explicit unavailable state cover mouse, keyboard, asynchronous, and legacy-message behavior.

## Focused tests

- API service tests use a deterministic clock to prove `2345` ms assistant persistence, user-message `null`, reload serialization, and negative-duration rejection.
- Web tests cover clipboard success/failure, exact retry input, pending and failed retries, append-only history, legacy timing, and millisecond/second/minute formatting.
- Focused suites passed: 14 API tests and 35 web tests.

## Verification evidence

- API: Ruff passed; all 60 tests passed; Python byte-compilation passed.
- Web: TypeScript lint, all 45 tests, and the Vite production build passed in the Linux project image.
- Brand: TypeScript lint, its test, and build passed in the Linux project image. Host WSL Node remains unusable, so the documented Docker verification path was used.
- Repository and infrastructure: repository verification passed with 3 agents, 3 skills, and 12 stories; the default and optional-Ollama Compose configurations passed; `git diff --check` passed.
- Real stack: a dedicated grounded answer persisted `107794` ms on its assistant message and `null` on its user message. The POST response, history GET, PostgreSQL row, and GET after API restart agreed; the existing-volume migration and non-negative constraint were present. The dedicated smoke conversation and its messages were deleted afterward.
- Browser smoke: at 1440 x 900 both message roles occupied about 93% of the conversation panel without page overflow; actions followed content/references; clipboard content matched the complete answer; retry sent the exact preceding question, disabled while pending, and appended a new turn with `850 ms` timing. At 390 x 844 all bubbles/actions stayed inside the panel with no horizontal overflow.

## Known limitations

- Clipboard writes depend on browser permission and secure-context support; failure must remain recoverable without altering the message.
- Response time is wall-clock server processing time for one grounded-answer request and is not a model benchmark or token-throughput metric.
