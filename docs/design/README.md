# CiteNook interface design handoff

The checked [interface design plan](citenook-interface-plan.svg) records the current CiteNook product baseline as a portable vector board. A [Chromium-rendered PNG](citenook-interface-plan.png) keeps the same handoff easy to preview in documentation. The board combines the desktop grounded-chat hierarchy, the responsive mobile hierarchy, central brand tokens, the primary user flow, and the privacy boundary used by project imagery.

[![CiteNook interface design plan](citenook-interface-plan.svg)](citenook-interface-plan.svg)

## Source contracts

- Product name and colors: `packages/brand/brand.json`
- Implemented interface: `apps/web/src`
- Visual implementation evidence: `docs/screenshots`
- User workflow: `docs/user-guide.md`

## Penpot target

- Team: `9080f45a-69d5-801b-8008-5645e5939d3f`
- Project: `f0a77847-b187-8122-8008-868c5a188f29`
- File: `f0a77847-b187-8122-8008-868c7dc025ca`
- Page: `f0a77847-b187-8122-8008-868c7dc025cb`
- Planned board name: `MRA-017 · CiteNook interface plan`

The SVG is suitable for import into Penpot and remains reviewable without a running design service. A Penpot-origin export must be added separately after the Penpot MCP plugin is connected to the target file; until then, this file is a repository design handoff, not evidence of a Penpot edit.
