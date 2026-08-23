# MRA-017: Document the interface design in Penpot

## Status

In progress

## User story

As a CiteNook maintainer, I want a portable interface plan synchronized to the project Penpot file and exported back into the repository so that product intent, current implementation, and reviewable design documentation stay connected.

## Acceptance criteria

- [x] A repository-owned vector board documents the current desktop grounded-chat hierarchy, responsive mobile hierarchy, primary user flow, core brand tokens, design principles, and screenshot privacy boundary.
- [x] A browser-rendered PNG preview of that board is checked into the documentation and visually inspected.
- [x] The root README and documentation index link to a design handoff page that records both source contracts and the exact Penpot target identifiers.
- [ ] A matching board named `MRA-017 · CiteNook interface plan` is created in the configured Penpot file and page through the connected Penpot MCP plugin.
- [ ] A fresh image exported from that Penpot board is committed and clearly distinguished from the portable repository source.

## Out of scope

Changing the implemented React interface, replacing the central brand contract, publishing personal application data, designing unimplemented features, or claiming a Penpot edit without a connected plugin is out of scope.

## Implementation evidence

- `docs/design/citenook-interface-plan.svg` is the portable, importable source board derived from `packages/brand/brand.json`, the implemented React interface, and the privacy-safe screenshot baseline.
- `docs/design/citenook-interface-plan.png` is a Chromium render of the complete vector board and was visually inspected after correcting inverse text colors.
- `docs/design/README.md` links the two formats, identifies the implementation and workflow source contracts, and records the team, project, file, page, and planned board name.

## Verification evidence

- Chromium rendered the SVG at 1800×1050 without load errors, and the final PNG was visually inspected at full-board scale.
- The repository audit passed with 17 stories, and the staged handoff diff passed `git diff --check`.

## Known limitation

The Penpot MCP plugin is not currently connected to the supplied local file. Three write-context checks returned `No plugin instance connected for user token`, so no Penpot change or Penpot-origin export is claimed in this commit.
