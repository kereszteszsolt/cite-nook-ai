# MRA-009: Refine chat interaction and conversation controls

## Status

Implemented

## User story

As a user, I want a more natural chat composer and clearer conversation controls so that longer questions and saved conversations are easier to manage.

## Acceptance criteria

- [x] The active conversation title can be edited from the Chat workspace, is validated and persisted by the API, and updates every visible occurrence without a reload.
- [x] A manually edited title survives reloads and container restarts and is not replaced by the automatic first-question title.
- [x] Title editing provides accessible edit, save, cancel, saving, and failed-update states without losing the previous stored title.
- [x] User and assistant message bubbles use more of the available width while remaining visually distinct.
- [x] The composer integrates an accessible send icon with the text field, sends with Enter, and preserves Shift+Enter for line breaks.
- [x] The question field grows upward from a compact initial height, stops at a bounded maximum, and then uses an internal scrollbar.
- [x] The composer spans the conversation panel, remains below the message history without covering it, and the desktop app shell has no page scrollbar in its default state; only bounded workspace content scrolls.
- [x] The application header and conversation summary remain compact enough to prioritize the active chat area.
- [x] A successful send clears and collapses the composer, while a failed send preserves the entered question for retry.
- [x] The conversation delete control has a polished, restrained destructive treatment while preserving confirmation, loading, and disabled behavior.

## Out of scope

Streaming responses, rich-text editing, conversation search, bulk deletion, undo, and changes to the grounded-answer or document-selection contracts.

## Verification

Run the focused automated checks, repository gates, Compose configuration checks, and the MRA-009 runtime/browser smoke described in `docs/testing.md`.

## Implementation evidence

- Title contract: `ConversationUpdate` is a validated partial PATCH schema. `ConversationService.update` changes only supplied fields, normalizes a custom title to one line, enforces the 120-character database boundary, and preserves the stored model pair during a title-only update.
- Automatic-title boundary: the first normalized question generates the existing deterministic title only while the conversation still has the untouched `New conversation` title, so an earlier manual edit is preserved.
- Title UI: `ConversationTitle` provides an inline pencil action, autofocus input, 120-character limit, Save/Cancel controls, Escape cancellation, saving disablement, and retryable failure behavior. The successful API response updates both the main heading and sidebar state.
- Chat UI: message bubbles use an 88%/920 px desktop maximum with distinct alignment and surfaces. The restrained delete action combines an outline trash icon with destructive color and adds its soft surface only on hover.
- Composer behavior: the panel-contained composer spans the same usable width as the message history and uses a one-row textarea with an integrated accessible arrow button. Enter submits, Shift+Enter remains multiline, successful requests clear the controlled value, and failed requests keep it.
- Bounded sizing and scrolling: the textarea measures its content on first conversation mount, conversation changes, and every input change; it grows from 48 px to 160 px and switches from hidden to internal vertical overflow at the cap. The message history occupies a separate bounded grid row above it and scrolls without moving behind the composer.
- Viewport layout: the desktop application shell is constrained to the dynamic viewport, with a 72 px minimum header, compact conversation summary, and independently scrolling conversation/document content instead of a default page scrollbar.

## Focused tests

- `apps/api/tests/test_messages.py` verifies custom-title normalization and limits, model preservation, persistence calls, and protection from first-question replacement.
- `apps/web/src/App.test.tsx` verifies edit/save/cancel/loading/failure states, immediate heading/sidebar updates, accessible SVG controls, Enter and Shift+Enter, initial and maximum heights, internal overflow, success collapse, failed-question retention, and confirmed deletion.
- `apps/web/src/api.test.ts` verifies the encoded title-only PATCH request does not resend the model pair.

## Verification evidence

Verified on 2026-08-22:

- Repository gates — structural verification passed with 3 agents, 3 skills, and 9 stories; full lint passed for all packages.
- Automated tests — 58 API, 27 web, and 1 brand test passed; all API, web, and brand production builds completed.
- Compose validation — both the external-Ollama base configuration and optional separate-Ollama override configuration passed.
- API runtime — a dedicated title-only PATCH normalized repeated whitespace while retaining `qwen3.5:9b` and `qwen3-embedding:0.6b`; whitespace-only input returned 422.
- Restart persistence — a separate dedicated custom title reloaded unchanged after an API-container restart with the same stored model pair.
- Desktop browser smoke — Chromium exercised the real title editor and confirmed immediate heading/sidebar synchronization, a 48 px initial composer, accessible send/delete icons, wider distinct user/assistant bubbles, and the 160 px internal-scroll cap. At both 1800 × 900 and 1366 × 768, the composer exactly matched the message-history width, the history ended above it, and the page had no scrollbar; the rendered header was 74 px high.
- Expanded composer smoke — at the 160 px input cap, the message history still ended 10 px above the composer and the document remained exactly viewport-height without a page scrollbar.
- Mobile browser smoke — at 390 px, the 308 px composer matched the message-history width, stayed inside the 20–370 px conversation panel, and remained below the message history without overlap.
- Cleanup — both explicitly tracked final runtime/browser conversations were deleted; their conversation and message counts were zero. The pre-existing conversation opened for read-only message rendering remained present.

## Known limitations

- Title edits use the shared error banner and have no undo history. The composer remains non-streaming and keeps the existing 4000-character question limit.
