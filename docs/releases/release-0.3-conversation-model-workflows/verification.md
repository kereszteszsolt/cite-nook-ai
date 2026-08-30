# Release 0.3 verification

These records were moved from the implemented story files by `MRA-018`. They keep the original 2026-08-22 proof and the shipped Release 0.3 facts.

## MRA-010: Configure models and controls per conversation

Implementation proof:

- The global header keeps only brand and Ollama status, while conversation dialogs own model selection and the stored pair.
- Create, edit, and delete dialogs enforce installed-model choices, defaults, modal semantics, focus, Escape, busy, cancel, and retry states.
- Existing FastAPI schemas, services, and PostgreSQL model fields remain the only pair-persistence contract; no configuration entity or migration was added.

Focused and release proof:

- App, API-client, header, and message tests covered model selection, persistence, unavailable choices, dialog states, heading removal, and assistant provenance.
- Ruff, all 59 API tests, 35 web tests, 1 brand test, Python compileall, all builds, the repository verifier, and both Compose configurations passed.
- A runtime chat changed atomically from `llama3.1:8b`/`qwen3-embedding:0.6b` to `qwen3.5:9b`/`qwen3-embedding:0.6b`, reloaded with that pair, and was deleted.
- Chromium exercised all three custom dialogs, focus and Escape behavior, a 52 px global header, a 110 px chat header, equal 1320 px history/composer widths, and no page scrollbar or removed headings.
- Prototype cleanup left 2 conversations, 4 messages, and 8 documents while removing the rejected configuration table and foreign key.
- Commit: `17837aa` (`feat(mra-010): configure models per conversation`).

Uploads use the active conversation embedding model or the configured available default when no chat is active. This story changed native confirmation only for conversation deletion.

## MRA-011: Refine document safety and status feedback

Implementation proof:

- A document-specific alert dialog names the target and retains it until the existing deletion API succeeds; failures remain retryable.
- The upload control keeps native input semantics behind a CiteNook surface, and text-labelled Ollama and document pills use restrained state colors.
- Document content stays in bounded scrolling regions at desktop and narrow widths.

Focused and release proof:

- App and header tests covered dialog copy and focus, cancel and Escape, busy and retry states, target-only deletion, status classes, failure text, and file selection.
- Ruff, TypeScript, all 59 API tests, 39 web tests, 1 brand test, Python compileall, all builds, the repository verifier, and both Compose configurations passed.
- Chromium at 1440×900 showed no page scrollbar, distinct muted state pills, a transparent failed row, readable bounded failure text, and the selected `browser-smoke.md` file name.
- The alert dialog named `notes.md`, focused Cancel, closed with Escape, and sent no DELETE request during cancellation; at 390×844 the picker and dialog stayed inside the viewport.
- Commit: `cbd9f8f` (`feat(mra-011): refine document safety and status feedback`).

The label shows only the browser-provided file name. Failed ingestion remains terminal until delete and re-upload, and successful document deletion has no undo.

## MRA-012: Widen messages and add answer actions

Implementation proof:

- `conversation_messages.response_duration_ms` is nullable and non-negative, is added to old volumes idempotently, and is returned as `responseDurationMs`.
- The grounded-answer service measures the whole server interval with a monotonic clock and stores it only on the assistant message.
- Wider message bubbles expose accessible copy, retry, feedback, and concise duration controls after content and references; retry appends through the existing answer path.

Focused and release proof:

- Deterministic API timing tests proved `2345` ms assistant persistence, user `null`, reload output, and negative-value rejection.
- Web tests covered clipboard success and failure, exact retry input, pending and failed retry, append-only history, legacy timing, and duration formatting; 14 focused API tests and 35 focused web tests passed.
- Ruff, all 60 API tests, TypeScript, all 45 web tests, the brand test, all builds, the repository verifier, both Compose configurations, and `git diff --check` passed through the documented Linux container path.
- A real answer stored `107794` ms on the assistant and `null` on the user; POST, GET, PostgreSQL, and GET after restart agreed, and the test chat was deleted.
- Chromium showed about 93% message width at 1440×900, exact clipboard content, exact-question retry with pending disablement, an appended `850 ms` turn, and no overflow at 390×844.
- Commit: `a186263` (`feat(mra-012): add message actions and response timing`).

Clipboard writes depend on browser permission and secure-context support. Response time is wall-clock server processing time, not a model benchmark or token-throughput score.
