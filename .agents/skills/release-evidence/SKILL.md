---
name: release-evidence
description: Maintain CiteNook MRA user stories and release evidence. Use when adding or reconciling acceptance criteria, implementation status, architecture links, verification commands, or release ZIP contents.
---

# Release evidence

Run the dependency-free repository audit first:

```bash
python3 .agents/skills/release-evidence/scripts/verify_repository.py
```

For each changed story record:

- observable acceptance criteria;
- implementation files;
- focused tests;
- commands run and exact outcomes;
- known environment limitations;
- status: `Planned`, `In progress`, or `Implemented`.

Rules:

- `Implemented` is a claim about behavior, not intent.
- Keep criteria at user/system outcome level rather than listing every code task.
- Keep out-of-scope features explicit so the mini application stays small.
- Keep documentation focused on product behavior, architecture, and verification evidence.
