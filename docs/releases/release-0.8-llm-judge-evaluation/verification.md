# Release 0.8 verification

## Status

**Planned; not run.** No DeepEval code, dependency, judge score, remote request or test has been implemented or executed for this release.

| Story | Offline tests | Existing fixture regression | Actual judge run | Status |
| --- | --- | --- | --- | --- |
| [MRA-033](stories/MRA-033-optional-deepeval-judge.md) | Not run | Not run | Not run | Planned |

## Evidence to record after implementation approval

- Explicit implementation and separate commit approvals, changed files, actual test/build commands and outputs.
- Input suite ID/hash, saved result origin, count of scored/skipped/error cases, and source-snippet availability.
- Judge software version and configured model/provider, network/cost authorization, run time, output file paths, any model usage data, and observed limitations.
- Separate results for native and LlamaIndex only when both are actually evaluated using comparable judge settings.
- Assertions that source-file baseline/safety fixtures and Release 0.6/0.7 measurements are unchanged.

Do not mark a planned metric or unrun live judge check successful. LLM-judge outputs are estimates from the selected evaluator/model, not ground truth.
