# MRA-012: Widen messages and add answer actions

## Status

Implemented

## User story

As a user, I want to copy or retry an answer and see how long it took.

## Goal

Add clear message actions. Save the time used for each answer.

## Dependencies

`MRA-011`.

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
