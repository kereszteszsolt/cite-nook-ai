# Release 0.3: Conversation model workflows

## Status

Implemented. MRA-010 and MRA-011 are complete.

## Objective

Keep model selection attached to each conversation while making conversation creation, model changes, and deletion explicit, compact, and consistent with CiteNook.

## Story map

| Story | Title | Status |
| --- | --- | --- |
| MRA-010 | Configure models and controls per conversation | Implemented |
| MRA-011 | Refine document safety and status feedback | Implemented |

## Release boundary

MRA-010 uses the existing conversation model fields and API contract. MRA-011 refines frontend deletion safety and status presentation without changing document persistence or status values. This release does not introduce named or reusable model-configuration entities, a global configuration workspace, authentication, or cloud synchronization.
