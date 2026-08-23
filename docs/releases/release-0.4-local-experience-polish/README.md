# Release 0.4: Local experience polish

## Status

Implemented. MRA-013 through MRA-015 are complete; further polish stories may follow.

## Objective

Polish the supported local experience with reliable startup behavior and complete, consistent frontend identity details.

## Story map

| Story | Title | Status |
| --- | --- | --- |
| MRA-013 | Recover local API connectivity | Implemented |
| MRA-014 | Add browser favicon identity | Implemented |
| MRA-015 | Capture privacy-safe product screenshots | Implemented |

## Release boundary

MRA-013 changes only the browser-to-API local transport and startup feedback. MRA-014 fills the browser favicon identity gap without changing stable technical identifiers. MRA-015 adds a dev-only visual documentation path with generic fixtures; it never seeds or reads the persistent application stack. External Ollama remains the default, the optional Ollama Compose service remains separate, and no persistence, model-selection, ingestion, retrieval, authentication, or remote-deployment contract is added.
