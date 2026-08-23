# MRA-016: Publish a linked user guide

## Status

Implemented

## User story

As a new local CiteNook user, I want a task-focused guide reachable from the README so that I can start the stack, prepare sources, ask grounded questions, inspect citations, manage persisted content, and diagnose common local failures.

## Acceptance criteria

- [x] The root README and documentation index link directly to one user guide.
- [x] The guide explains startup and connection states, supported document workflows, conversation model choices, grounded questions, references, message actions, deletion, persistence, and common failures.
- [x] The guide embeds clickable links to the privacy-safe desktop, document, and mobile screenshots.
- [x] Privacy notes distinguish Git configuration, persistent Docker data, personal workspace content, and the static screenshot fixture boundary.
- [x] The guide describes only implemented Release 0.1–0.4 behavior and does not imply authentication, remote access, streaming, or other out-of-scope features.

## Out of scope

Changing application behavior, replacing operator/developer documentation, documenting unsupported deployment modes, publishing private application records, or creating the Penpot design board is out of scope.

## Implementation evidence

- `docs/user-guide.md` follows the main user journey from startup through grounded answers and lifecycle actions, then supplies privacy and troubleshooting guidance.
- The guide uses the MRA-015 generic screenshots as clickable visual examples.
- `README.md` exposes a compact Documentation section; `docs/README.md` places the user guide first in the documentation index.

## Verification evidence

- Every relative Markdown link and embedded screenshot target in the guide resolves to a tracked project file.
- The repository audit passed with 16 stories, and the staged documentation diff passed `git diff --check`.
