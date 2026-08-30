# Release 0.3: Conversation model workflows

## Status

Implemented. MRA-010 through MRA-012 are complete.

## Objective

Keep model selection attached to each conversation while making conversation creation, model changes, and deletion explicit, compact, and consistent with CiteNook.

## Story map

| Story | Title | Status |
| --- | --- | --- |
| [MRA-010](stories/MRA-010-conversation-model-workflows.md) | Configure models and controls per conversation | Implemented |
| [MRA-011](stories/MRA-011-document-safety-and-status-polish.md) | Refine document safety and status feedback | Implemented |
| [MRA-012](stories/MRA-012-message-actions-and-response-time.md) | Widen messages and add answer actions | Implemented |

## Verification

See the [Release 0.3 verification record](verification.md).

## Release boundary

MRA-010 uses the existing conversation model fields and API contract. MRA-011 refines frontend deletion safety and status presentation without changing document persistence or status values. MRA-012 adds persistent response timing and message-level interaction controls while retaining one linear conversation history. This release does not introduce named or reusable model-configuration entities, branching answer alternatives, a global configuration workspace, authentication, or cloud synchronization.
