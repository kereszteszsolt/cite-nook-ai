# MRA-017: Document the interface design in Penpot

## Status

Implemented

## User story

As a CiteNook maintainer, I want a portable interface plan synchronized to the project Penpot file and exported back into the repository so that product intent, current implementation, and reviewable design documentation stay connected.

## Acceptance criteria

- [x] A repository-owned vector board documents the current desktop grounded-chat hierarchy, responsive mobile hierarchy, primary user flow, core brand tokens, design principles, and screenshot privacy boundary.
- [x] A browser-rendered PNG preview of that board is checked into the documentation and visually inspected.
- [x] The root README and documentation index link to a design handoff page that records both source contracts and the exact Penpot target identifiers.
- [x] A matching board named `MRA-017 · CiteNook interface plan` is created in the configured Penpot file and page through the connected Penpot MCP plugin.
- [x] A fresh image exported from that Penpot board is committed and clearly distinguished from the portable repository source.

## Out of scope

Changing the implemented React interface, replacing the central brand contract, publishing personal application data, designing unimplemented features, or claiming a Penpot edit without a connected plugin is out of scope.

## Implementation evidence

- `docs/design/citenook-interface-plan.svg` is the portable, importable source board derived from `packages/brand/brand.json`, the implemented React interface, and the privacy-safe screenshot baseline.
- `docs/design/citenook-interface-plan.png` is a Chromium render of the complete vector board and was visually inspected after correcting inverse text colors.
- `docs/design/citenook-interface-plan.penpot.png` is the fresh export from Penpot board `5cc6ef41-e335-8023-8008-8692985e4d8d`, kept separate from the portable source preview.
- `docs/design/README.md` links the repository and Penpot formats, identifies the implementation and workflow source contracts, and records the exact team, project, file, page, board name, and board ID.

## Verification evidence

- Chromium rendered the SVG at 1800×1050 without load errors, and the final PNG was visually inspected at full-board scale.
- The connected Penpot plugin confirmed the configured file and page, created the named 1800×1050 board, and exported a complete 1800×1050 PNG that was visually inspected after synchronization.
- The repository audit passed with 17 stories, and the supplementary handoff diff passed `git diff --check`.
- In a Node 26 container, all 3 lint tasks, all 61 API tests, 48 web tests, 1 brand test, and all 3 build tasks passed; both base and optional Ollama Compose configurations also validated.

## Known limitation

Penpot's SVG importer did not render the two decorative drop-shadow filters. The synchronized board therefore omits those shadows, but retains the complete desktop and mobile hierarchy, tokens, user flow, design principles, and privacy boundary. The host `npm` wrapper cannot start under WSL1, so the same repository scripts ran in the available Node 26 container with the existing uv runtime mounted for API tasks.
