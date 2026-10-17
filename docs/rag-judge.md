# Optional local judge for saved RAG results

`python -m evaluation.judge` assesses existing synthetic fixture results without starting CiteNook or rerunning ingestion/retrieval. It uses optional DeepEval metrics with an explicit local Ollama model. API, worker, web, Docker, and normal CI do not install or import DeepEval. Offline checks and an [approved local judge run](releases/release-0.8-llm-judge-evaluation/verification.md#first-approved-local-judge-run) are recorded. Several judge explanations were wrong; treat the scores as model-dependent findings.

## Setup and authorization

From the repository root:

```bash
cd apps/api
uv sync --locked --extra judge
uv run --locked --extra judge python -m evaluation.judge --help
```

Install a suitable local judge model separately, then inspect its installed digest/version with `ollama list`. The CLI does not download models. Record that version explicitly; `--model-version` is operator-supplied metadata, not an automatic server check. A model that can produce structured JSON is needed by DeepEval's [answer relevancy](https://deepeval.com/docs/metrics-answer-relevancy) and [faithfulness](https://deepeval.com/docs/metrics-faithfulness) metrics.

Only the bundled synthetic baseline/safety exports are eligible. `--synthetic-data` attests that answers came from the isolated fixture deployment and contain no personal uploads, private conversations, or secrets. The CLI verifies suite ID/hash, known case IDs, exact fixture questions and no-answer expectations, citation document ownership, and snippet membership in the bundled documents, allowing whitespace normalization. These checks cannot prove the origin of arbitrary answer text; inspect the export before making the attestation.

The supported judge is a local Ollama model at a loopback HTTP(S) endpoint. Remote endpoints, embedded URL credentials, and cloud model names are rejected; environment proxies, redirects, dotenv loading, DeepEval telemetry, and update checks are disabled. The CLI calls individual metrics, without dashboard login, `evaluate()`, tracing, or result upload. Use a local inference server and model you control; do not route its loopback endpoint through a remote proxy or rename a cloud model to bypass the local-only restriction.

Remote or paid calls require **separate, explicit user approval** of provider, model, data, and cost. This CLI does not enable them even with approval. Local evaluation also consumes time, memory, and power: each metric can make several model requests per case, and model retries may extend the supplied per-request timeout. Obtain approval before a costly run; installing the extra and running offline tests grants no approval for inference.

## Judge an existing result

After approval for the intended local run, use an output directory that does not exist. Replace the example model and version with the installed local judge:

```bash
uv run --locked --extra judge python -m evaluation.judge \
  --input ../../docs/releases/release-0.7-rag-safety-checks/results/2026-10-16/native/results.json \
  --output-dir /tmp/citenook-judge-safety-native-run1 \
  --model llama3.1:8b \
  --model-version paste-installed-model-digest \
  --base-url http://127.0.0.1:11434 \
  --temperature 0 \
  --threshold 0.5 \
  --request-timeout 120 \
  --synthetic-data
```

For the preserved baseline use `../../docs/releases/release-0.6-rag-evaluation-and-ci/results/2026-10-14/native/results.json` and a fresh output directory. To assess LlamaIndex, select its corresponding saved file and another new output directory; this does not switch a live backend. Keep identical judge versions/settings, suite hashes, and scored case IDs when comparing backend runs.

Every judge setting is required and printed before execution. There is no default model, endpoint, threshold, or inference request. Temperature must be finite and non-negative, threshold must be within `[0, 1]`, and timeout must be finite and positive. The original HTTP fixture CLI and its outputs remain unchanged.

## Eligibility and missing data

| Saved data | Treatment |
| --- | --- |
| Schema 1 baseline with matching suite ID/hash | Accept; relevance can be scored; absent cited snippets make faithfulness N/A |
| Schema 2 baseline or safety with matching name/ID/hash/count | Accept and validate each known case |
| Completed `passed` or `failed` run | Score suitable pairs even when deterministic fixture checks failed |
| Run status `error`, run/cleanup error, missing cases or timestamps | Skip the entire run with reasons; make no judge calls |
| Expected or actual fixed no-answer reply; empty answer | Skip both metrics; retain the deterministic outcome |
| Missing/empty citations or any missing/empty cited snippet | Relevance may be scored; faithfulness is N/A, with no partial-context substitution |
| Invalid/mismatched source markers | Relevance may be scored; faithfulness is N/A |
| Malformed pair/citation, changed question, or non-fixture snippet | Record per-case metric errors and make no calls for that pair |
| Unknown schema/suite/hash, duplicate/unknown IDs or malformed run structure | Reject input with a reason before creating output or loading DeepEval |
| Missing extra, judge exception, bad/non-finite score or missing judge reason | Record metric errors; exclude them from score means |

`AnswerRelevancyMetric` receives only the completed question and answer. `FaithfulnessMetric` also receives the saved, non-empty cited snippets as its `retrieval_context`; reports always name it **cited-excerpt faithfulness**. No fixture document is used to reconstruct missing context. An excerpt score says nothing about omitted retrieval chunks, recall, retrieval precision, or whether all needed evidence was retrieved.

## Separate output and interpretation

A new output directory contains `judge-scores.json` and `judge-report.md`; existing directories are rejected. The input is read only, and its absolute path and SHA-256 are saved with suite/backend/model provenance. Results include judge settings, DeepEval/Ollama-client/Python versions, the supplied model version and its verification limit, UTC timestamps, per-case metric scores, reasons, skip/error reasons, usage when exposed, and original deterministic checks. DeepEval's Ollama adapter does not expose token counts; unavailable usage stays `null`, and reported evaluation cost does not measure hardware/energy costs.

Each metric has separate scored/skipped/error counts, scored case IDs, a mean over scored cases only, and judge verdicts meeting the threshold. No combined score, cross-suite average, or cross-backend aggregate is produced. Compare only matching scored case sets under the same judge/software/settings; a high score over a small surviving subset does not characterize excluded cases. Judge thresholds never change the original fixture `passed` flag.

Exit codes are `0` for a completed assessment (including below-threshold judge verdicts), `1` when everything is skipped, and `2` for input/output or judge errors. Partial valid scores remain in reports alongside errors. An all-skipped run has `null` means, not zero or a successful judge verdict.

Model judgments can vary even at temperature zero. On-topic answers can still invent facts; citation snippets may themselves contain hostile instructions that bias a judge. Neither metric certifies factual truth or prompt-injection protection. Record actual scores in [Release 0.8 verification](releases/release-0.8-llm-judge-evaluation/verification.md) only after an approved real run, with the source input, model digest, settings, commands, outputs, timing, and limitations.
