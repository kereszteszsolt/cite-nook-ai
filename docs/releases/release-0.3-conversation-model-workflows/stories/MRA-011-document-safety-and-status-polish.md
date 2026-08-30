# MRA-011: Refine document safety and status feedback

## Status

Implemented

## User story

As a user, I want file state and delete steps to be clear.

## Goal

Make file actions safe. Keep status notes easy to scan.

## Dependencies

`MRA-010`.

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
