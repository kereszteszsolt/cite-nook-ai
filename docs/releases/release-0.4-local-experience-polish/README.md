# Release 0.4: Local experience polish

## Status

Implemented. MRA-013 is complete; further polish stories may follow.

## Objective

Polish the supported local experience with reliable startup behavior and complete, consistent frontend identity details.

## Story map

| Story | Title | Status |
| --- | --- | --- |
| MRA-013 | Recover local API connectivity | Implemented |

## Release boundary

MRA-013 changes only the browser-to-API local transport and startup feedback. Later stories may fill small frontend identity gaps without changing stable technical identifiers. External Ollama remains the default, the optional Ollama Compose service remains separate, and no persistence, model-selection, ingestion, retrieval, authentication, or remote-deployment contract is added.
