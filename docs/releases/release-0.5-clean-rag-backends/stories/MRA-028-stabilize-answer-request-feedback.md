# MRA-028: Stabilize answer request feedback

## Status

Implemented

## User story

As a user, I want to see my question at once so I know the app is working.

## Goal

Show pending work, stop stalled calls, and keep retry text after errors.

## Dependencies

`MRA-027`.

## Acceptance criteria

- [x] Ollama calls use a configured finite timeout and return a short provider error when it expires.
- [x] The web answer request has a finite timeout with a clear retry message.
- [x] A sent question appears at once in a temporary user bubble while the input clears and stays disabled.
- [x] A temporary assistant bubble shows a spinner until the answer request ends.
- [x] A successful response replaces temporary state with the persisted turn exactly once.
- [x] An error or timeout removes temporary state, restores the question, and enables the input.
- [x] Grounded chat uses structured allowlisted source IDs and normalizes duplicate citations.
- [x] Focused tests cover timeout, pending, success, and failure behavior without changing backend selection.

## Out of scope

This story does not add streaming, request cancel buttons, model changes, or a backend switch.
