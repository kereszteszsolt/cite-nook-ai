# MRA-020: Split the web app by feature

## Status

Planned

## User story

As a maintainer, I want chat and file work in separate modules so the web app is easier to change.

## Goal

Make `App.tsx` a small shell. Keep each feature close to its state, actions, views, and tests.

## Dependencies

`MRA-019`.

## Acceptance criteria

- [ ] Conversation state, requests, dialogs, and views live under `features/conversations`.
- [ ] Document state, polling, upload, active state, delete work, and views live under `features/documents`.
- [ ] `App.tsx` owns startup, the active workspace, shared errors, and top-level layout only.
- [ ] `App.tsx` does not call conversation or document API methods directly.
- [ ] The shared API client and shared HTTP types remain the only web API boundary.
- [ ] The large app test is split into focused startup, conversation, and document tests.
- [ ] Current desktop, mobile, loading, empty, success, and failure behavior stays the same.
- [ ] No new router, global state library, or UI framework is added.

## Out of scope

This story does not change the visual design or add a RAG backend switch to the UI.
