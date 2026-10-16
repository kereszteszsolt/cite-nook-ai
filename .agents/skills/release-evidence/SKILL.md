---
name: release-evidence
description: Use for CiteNook story status, verification records, repository checks, documentation integrity, and release closeout; not for every code edit.
---

# Verification and release evidence

Use the existing story format and approval gates in `docs/story-workflow.md` instead of duplicating those rules here. Do not load past release records unless a current criterion or regression requires them.

## Repository audit

```bash
python3 .agents/skills/release-evidence/scripts/verify_repository.py
```

Run focused checks for changed files first. The repository audit validates story structure, local references, Codex role/skill counts and source-comment conventions; **it does not prove runtime behavior**.

## Release record

1. Identify the active `MRA-*` story and its release `verification.md`.
2. Record the exact command, environment/deployment, result and important limitation for each checked criterion.
3. Keep large logs outside story files; link to evidence when useful. Leave a blocked or untested criterion unchecked.
4. Report security test failures as findings, not as safety claims. Preserve previously verified numbers and historical records.
5. Propose a commit message only after reviewing the diff and evidence; commit and continue only with distinct approvals.

For release closeout, use `docs/testing.md` to select lint, build, Compose and live backend checks; do not rerun full suites after every small documentation change.
