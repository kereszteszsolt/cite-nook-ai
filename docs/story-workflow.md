# Story and Codex workflow

## Scope

This guide is the source of truth for all CiteNook stories. `MRA-018` moved `MRA-001` through `MRA-017` to this format, so the strict checks now apply to every story.

## Story sections

Each story uses these sections in this order:

1. `Status`
2. `User story`
3. `Goal`
4. `Dependencies`
5. `Acceptance criteria`
6. `Out of scope`

Use `Planned`, `In progress`, or `Implemented`. A planned story has unchecked criteria. An implemented story has all criteria checked and linked proof in its release verification file.

## Story writing rules

- Keep each prose block at five sentences or less.
- Aim for three short sentences when that is enough.
- Keep each acceptance criterion to one short, testable sentence.
- Use four to eight criteria per story.
- Keep the combined `User story` and `Goal` at Flesch Reading Ease 80 or more.
- Put paths, code names, settings, and commands in code style.
- Put long commands, logs, totals, and proof in the release `verification.md` file.
- Do not add issue or limitation sections to story files.
- Do not change a past shipped fact just to make a story shorter.

## Acceptance criterion order

Codex uses the listed criteria as an ordered checklist. It verifies each criterion before it claims the next one. Shared setup may support more than one criterion, but Codex may not skip, reorder, or mark a later criterion early without clear user approval.

## Source comment rules

These rules apply to code comments and docstrings, not user-facing help text.

- Add a comment only when names and structure cannot make the reason clear.
- Explain why a choice exists; do not repeat what the code does.
- Prefer one short sentence.
- Use at most three short sentences in one comment block.
- Use at most five short sentences in one docstring.
- Put plans, change history, story text, and long design notes in Markdown docs.
- Keep SPDX headers and required tool directives unchanged.
- Use plain English and aim for Flesch Reading Ease 80 or more when a prose block is long enough to score.

## Approval gates

Codex works on one story at a time.

1. Codex names the next valid story, scope, likely files, and checks.
2. Codex asks for clear approval before it edits implementation files.
3. Codex implements only the approved story and follows its criteria in order.
4. Codex runs the focused checks and shows the result.
5. Codex proposes one commit message and asks for clear commit approval.
6. Codex creates the commit only after that approval.
7. Codex reports the commit hash after the commit succeeds.
8. Codex asks whether it may start the next valid story.

Approval for one step does not grant approval for another. Codex may not commit, continue to a later story, force-push, reset shared history, or rewrite commits without clear approval for that action.

## Evidence rules

The release `verification.md` file stores short proof for each story. It records implementation approval, key commands, results, review, commit approval, and commit hash. Large logs remain separate files. A failed or blocked criterion stays unchecked, and the story stays `Planned` or `In progress`.

## Transition rule

The repository check applies the same strict format, status, criterion, sentence, reading, and release-link rules to every story. There is no compatibility mode for old records.
