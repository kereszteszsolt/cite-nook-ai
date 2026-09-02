# Release 0.4: Local experience polish

## Status

Implemented. MRA-013 through MRA-017 are complete.

## Objective

Polish the supported local experience with reliable startup behavior and complete, consistent frontend identity details.

## Story map

| Story | Title | Status |
| --- | --- | --- |
| [MRA-013](stories/MRA-013-recover-local-api-connectivity.md) | Recover local API connectivity | Implemented |
| [MRA-014](stories/MRA-014-add-browser-favicon-identity.md) | Add browser favicon identity | Implemented |
| [MRA-015](stories/MRA-015-capture-privacy-safe-product-screenshots.md) | Capture privacy-safe product screenshots | Implemented |
| [MRA-016](stories/MRA-016-publish-linked-user-guide.md) | Publish a linked user guide | Implemented |
| [MRA-017](stories/MRA-017-document-interface-design-in-penpot.md) | Document the interface design in Penpot | Implemented |

## Verification

See the [Release 0.4 verification record](verification.md).

## Release boundary

MRA-013 changes only the browser-to-API local transport and startup feedback. MRA-014 fills the browser favicon identity gap without changing stable technical identifiers. MRA-015 adds a dev-only visual documentation path with generic fixtures; it never seeds or reads the persistent application stack. MRA-016 documents the already implemented user workflows without adding new product behavior. MRA-017 documents and synchronizes the current interface baseline without authorizing a product redesign. External Ollama remains the default, the optional Ollama Compose service remains separate, and no persistence, model-selection, ingestion, retrieval, authentication, or remote-deployment contract is added.
