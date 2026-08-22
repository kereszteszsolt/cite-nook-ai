# Codex project setup

This repository intentionally keeps its Codex setup small:

- `architect` plans cross-cutting changes;
- `implementation_worker` owns one bounded write task;
- `reviewer` checks behavior, retrieval grounding, persistence, and evidence.

Reusable workflows live in `.agents/skills/`. Root `AGENTS.md` is the source of truth for scope and working agreements.
