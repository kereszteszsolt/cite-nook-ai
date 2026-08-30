# Release 0.5 plan manifest

## Baseline

The plan starts from the supplied Release 0.4 `develop` archive. No file under `apps/api/app`, `apps/api/tests`, `apps/web/src`, `infra`, or `packages/brand/src` was changed while this plan was prepared.

## Planning changes

The plan adds or updates:

- ten implementation stories, `MRA-018` through `MRA-027`;
- the release map, cleanup plan, implementation plan, and verification table;
- the root README and documentation index;
- architecture, RAG, development, testing, technology, workflow, and roadmap docs;
- `AGENTS.md`, Codex agent rules, and repository skills;
- the repository audit so all stories use strict rules without a fixed story total.

## Implementation boundary

`MRA-018` moves the old story proof into release records and applies strict rules to every story. Existing source comments remain unchanged until `MRA-019`. The current web and Python source stay in the Release 0.4 structure until their own stories are approved.

No Release 0.5 app feature, Docker target, Compose override, database marker, LlamaIndex package, or Ragas code is included in this planning archive.

## Git state

This archive does not contain a new Git commit. Commit approval remains part of the story workflow.

## Planning archive checks

The planning archive passed the repository audit with 27 continuous story IDs. All ten new stories passed their section, criterion count, sentence, status, Flesch 80+, and release-map checks. Local Markdown links had no broken target. A hash comparison confirmed no change under `apps`, `infra`, or `packages` from the supplied baseline.
