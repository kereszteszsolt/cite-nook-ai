---
name: release-evidence
description: Maintain CiteNook story format, approval records, verification proof, release maps, documentation links, and release archives.
---

# Release evidence

Run the repository audit first:

```bash
python3 .agents/skills/release-evidence/scripts/verify_repository.py
```

For one active story:

1. Confirm the story is the next valid item.
2. Ask for implementation approval before implementation work.
3. Keep four to eight short criteria and follow them in order.
4. Record focused commands and short results in the release `verification.md`.
5. Keep large logs outside the story and link them when needed.
6. Propose a commit message and ask for commit approval.
7. Record the approved commit hash after it succeeds.
8. Ask before the next story starts.

Rules:

- `Implemented` is a claim about tested behavior.
- Story prose blocks use at most five sentences.
- `User story` plus `Goal` aims for Flesch Reading Ease 80 or more.
- Story files do not use issue or limitation sections.
- Past shipped facts must not change during cleanup.
- Source comments stay short and do not hold release proof.
