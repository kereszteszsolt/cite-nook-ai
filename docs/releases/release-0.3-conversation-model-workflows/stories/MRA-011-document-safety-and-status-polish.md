# MRA-011: Refine document safety and status feedback

## Status

Implemented

## User story

As a local CiteNook user, I want document deletion and operational feedback to feel clear and consistent so that destructive actions are deliberate and document/model states are easy to understand without overwhelming the interface.

## Acceptance criteria

- [x] Document deletion opens a CiteNook-styled confirmation modal instead of a native browser dialog and identifies the selected file, its indexed data, and the irreversible result.
- [x] The document confirmation flow provides explicit Cancel and Delete document actions, initial safe focus, idle Escape cancellation, disabled deletion state, retryable failure behavior, and removes only the confirmed document after API success.
- [x] Ollama connected and unavailable states use restrained, harmonious pastel green and red status pills that fit the CiteNook palette, while the checking state remains neutral and every state keeps a text label.
- [x] Document queued, processing, ready, and failed badges use distinct but subtle pastel status colors without tinting the complete table row or workspace.
- [x] The upload control replaces the browser's default file input presentation with an accessible CiteNook-styled Choose file control that shows the selected file name and preserves disabled, upload, success, and reset behavior.
- [x] A failed processing explanation remains fully readable and receives only a gentle red treatment with bounded content, without turning the complete document row into a high-emphasis error surface.
- [x] The revised controls remain keyboard accessible and responsive, and no changed document state or control introduces a default page scrollbar.

## Out of scope

Document deletion undo, bulk deletion, retrying failed ingestion, changing backend document status values, upload drag-and-drop, and replacing the existing document deletion API are out of scope.

## Verification

Run focused web tests, all repository lint/test/build gates, both Compose configuration checks, and the MRA-011 browser smoke described in `docs/testing.md`.

## Implementation evidence

- `App` now opens a document-specific `alertdialog` before calling the existing deletion API and keeps its selected target until a successful response. Failure leaves the dialog and document intact for retry.
- `ConversationDialogs` shares one accessible destructive-confirmation implementation between conversation and document deletion. Document copy names the file, stored bytes, indexed chunks, processing record, and irreversible outcome.
- `DocumentUpload` preserves the native file input's semantics while presenting a CiteNook-styled Choose file surface, selected-file label, disabled state, and existing upload-success reset behavior.
- `Header`, `DocumentList`, and the shared stylesheet keep text labels while applying muted color only to Ollama/document status pills. Failed processing uses a small bounded explanation surface; its complete table row remains transparent.
- Desktop content stays inside the viewport with Documents as the bounded scrolling region. Grid/table containment and anchored visually-hidden labels prevent page-level overflow at narrow widths.

## Focused tests

- `apps/web/src/App.test.tsx` covers the document dialog's copy, initial focus, Cancel/Escape, no native confirmation, busy state, target-only success, failure retry, status badge classes, bounded failure message, and file-picker selection/reset/disabled behavior.
- `apps/web/src/components/Header.test.tsx` verifies connected, unavailable, and checking states retain distinct classes and text labels without restoring model controls to the application header.

## Verification evidence

Verified on 2026-08-22:

- Automated gates — Ruff and TypeScript checks passed; all 59 API tests, 39 web tests, and 1 brand test passed. API compileall and web/brand production builds completed successfully.
- Repository and Compose — structural verification passed with 3 agents, 3 skills, and 11 stories. Both the external-Ollama base configuration and optional separate-Ollama override resolved successfully.
- Desktop browser smoke — Chromium rendered the built Compose web image at 1440 × 900 with no page-level horizontal or vertical scrollbar. The four status pills used separate muted amber, blue, green, and red surfaces; the failed row remained transparent and only its bounded explanation used a light red surface.
- Connection and upload smoke — connected and unavailable Ollama responses rendered text-labelled pastel green/red pills. The browser-native file control was visually hidden but remained labelled; the CiteNook picker displayed `browser-smoke.md` after selection.
- Deletion smoke — the custom document alert dialog named `notes.md`, explained removal of its stored file, chunks, and processing record, focused Cancel, and closed with Escape. Chromium observed no native dialog and no DELETE request during cancellation.
- Responsive smoke — at 390 × 844 the file picker and deletion dialog remained inside the viewport and the page width equalled the viewport; the wide document table stayed within its own horizontal scrolling region.

## Known limitations

- The selected-file label displays the browser-provided file name only; CiteNook does not inspect local paths before upload.
- Failed ingestion remains terminal in this story and must be addressed by deleting/re-uploading the document after correcting the source or service issue.
- Document deletion remains permanent and has no undo or recovery flow after API success.
