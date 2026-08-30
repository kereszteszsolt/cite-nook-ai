# MRA-019: Enforce short source comments

## Status

Planned

## User story

As a maintainer, I want short code notes so the code is easy to read.

## Goal

Keep only notes that explain a hard choice. Stop long AI notes from growing in the source.

## Dependencies

`MRA-018`.

## Acceptance criteria

- [ ] Hand-written Python, TypeScript, TSX, and repository script comments are reviewed.
- [ ] Comments that repeat the code or record old work are removed.
- [ ] A normal comment block has at most three short sentences.
- [ ] A docstring has at most five short sentences.
- [ ] License headers, type directives, lint directives, and test directives keep their required form.
- [ ] The repository check flags long prose comments and ignores required tool directives.
- [ ] `AGENTS.md`, Codex agents, and repository skills use the same comment rules.
- [ ] Existing lint, test, and build checks still pass.

## Out of scope

This story does not add user help text or move design notes into source files.
