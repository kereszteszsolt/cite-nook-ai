# Codex roles and skills

Codex follows the repository's [engineering guide](../AGENTS.md) and [story workflow](../docs/story-workflow.md). This is **story-driven, human-approved development**, not autonomous release management.

**Default:** the main agent reads one active story, edits the smallest relevant scope, runs focused checks and reviews the diff. The roles below are optional, never an automatic pipeline:

| Role | Ownership | When to delegate |
| --- | --- | --- |
| `implementation_worker` | One story's code and focused tests | Only as the sole writer; main agent does not edit concurrently |
| `architect` | Read-only design risks and affected boundaries | Data migrations, backend replacement, or broad cross-layer changes |
| `reviewer` | Read-only diff review and verification gaps | Security-sensitive changes and release checks |

**Skills are loaded by technology, not by release or product feature:**

- `react-fastapi-contracts`: React/FastAPI/worker-to-UI contracts.
- `rag-pipeline`: embedding, native/LlamaIndex retrieval, citation handling, eval fixtures.
- `release-evidence`: story records, repository audit and verifiable release proof.

Avoid parallel implementations, duplicate research and repeated test runs. Up to two threads may be active, and only one may write. Do not create commits or continue to another story without explicit approval.
