# MRA-009: Refine chat interaction and conversation controls

## Status

Implemented

## User story

As a user, I want it to be easy to write and manage a chat.

## Goal

Make chat tools clear. Keep long text easy to read and send.

## Dependencies

`MRA-008`.

## Acceptance criteria

- [x] The active title can be edited, validated, persisted, and shown at once with accessible save, cancel, saving, and failure states.
- [x] A manual title survives reloads and container restarts and is not replaced by the first-question title.
- [x] User and assistant message bubbles use more of the available width while remaining visually distinct.
- [x] The composer has an accessible send icon, sends with Enter, and preserves Shift+Enter for line breaks.
- [x] The question field grows upward from a compact height to a bounded internal scrollbar.
- [x] The compact header and full-width composer keep chat content above the composer with no default desktop page scrollbar.
- [x] A successful send clears and collapses the composer, while a failed send preserves the question for retry.
- [x] The conversation delete control has a restrained destructive treatment with confirmation, loading, and disabled behavior.

## Out of scope

Streaming responses, rich-text editing, conversation search, bulk deletion, undo, and changes to the grounded-answer or document-selection contracts.
