# Release 0.6 verification

## Status

Planned. No Release 0.6 tests, hosted CI runs, or live RAG measurements have been performed for this release.

## Story evidence

| Story | Implementation approval | Focused checks | Review | Commit approval | Commit | Status |
| --- | --- | --- | --- | --- | --- | --- |
| MRA-029 | Pending | Not run | Pending | Pending | Pending | Planned |
| MRA-030 | Pending | Not run | Pending | Pending | Pending | Planned |
| MRA-031 | Pending | Not run | Pending | Pending | Pending | Planned |

## Evaluation runs

Record one real, dated run per backend after `MRA-029` is implemented. Note the selected chat and embedding models, `RAG_TOP_K`, number of answered and no-answer cases, fixture-check outcomes, source-document matches, and API-reported response times. Link the actual per-case output and note failed or missing runs instead of filling in estimates.

## CI and release checks

After `MRA-030`, record the GitHub Actions run URL and its result. For release closeout, record repository verification, lint, unit tests, build, all four Compose configuration checks, and real smoke proof for native and LlamaIndex. Keep logs concise and include commit hashes only after approval.
