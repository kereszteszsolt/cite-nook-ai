# Release 0.7 verification

## Status

Planned. No implementation, automated test, or real-model safety measurement is claimed.

| Story | Focused tests | Native safety suite | LlamaIndex safety suite | Status |
| --- | --- | --- | --- | --- |
| [MRA-032](stories/MRA-032-add-adversarial-rag-fixtures.md) | Not run | Not run | Not run | Planned |

## Evidence to record after approval

- Implementation and commit approvals, commit hash, and the exact test and build commands with results.
- A suite ID/hash, selected model names and digests when available, RAG backend, `RAG_TOP_K`, and run date.
- Pass/fail details for each injection case, including invalid citation or unsupported-answer behavior.
- Separate sequential native and LlamaIndex runs on isolated synthetic data, with cleanup results.
- Explicit limitations: marker tests and selected fixtures are not a full security audit or a general safety score.

Do not edit the [Release 0.6 results](../release-0.6-rag-evaluation-and-ci/comparison.md) or mark `MRA-032` implemented before its checks are complete. If a real run is blocked or shows a failure, record that result without inventing a pass.

## Planning-document checks: 2026-10-16

The user approved committing the current documentation and Codex guidance changes. The diff review covered all 16 staged files; no application code or prior evaluation results changed. `MRA-032` remains planned, and its test and runtime checks above remain unrun.

- `python3 .agents/skills/release-evidence/scripts/verify_repository.py` passed: 3 agents, 3 skills, 32 stories, and 174 local links.
- Python 3 `tomllib.load` parsed `.codex/config.toml` and all three `.codex/agents/*.toml` files successfully.
- `git diff --exit-code` passed: there were no unstaged changes before this evidence update.
- `git -c core.whitespace=cr-at-eol diff --check HEAD` passed.

These checks validate repository documentation and TOML syntax only; no application tests, model runs, or Codex runtime configuration checks were performed. Proposed commit message: `docs: plan RAG safety fixtures and streamline Codex guidance`.
