# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import argparse
import json
import math
import platform
import sys
from collections import Counter
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from ipaddress import ip_address
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from .deepeval_judge import create_judge
from .judge_input import SavedRun, cited_excerpts, load_results, validate_pair
from .suite import NO_ANSWER

METRICS = ("answer relevancy", "cited-excerpt faithfulness")
SCOPE = (
    "Model-dependent judge estimates on saved synthetic fixtures only. Cited-excerpt "
    "faithfulness uses only saved cited snippets, never the full retrieved context. "
    "These verdicts are separate from deterministic fixture pass/fail checks and do not "
    "establish factual accuracy, retrieval recall, or prompt-injection protection."
)


@dataclass(frozen=True)
class JudgeConfig:
    model: str
    model_version: str
    base_url: str
    temperature: float
    threshold: float
    request_timeout: float
    synthetic_data: bool

    def __post_init__(self) -> None:
        if not self.synthetic_data:
            raise ValueError("Confirm --synthetic-data; never submit personal uploads or chats.")
        if not self.model.strip() or not self.model_version.strip():
            raise ValueError("Explicit judge model and model-version are required.")
        parsed = urlsplit(self.base_url)
        try:
            local = parsed.hostname == "localhost" or ip_address(parsed.hostname or "").is_loopback
            port = parsed.port
        except ValueError:
            local, port = False, None
        if (
            not local
            or parsed.scheme not in {"http", "https"}
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path not in {"", "/"}
            or parsed.query
            or parsed.fragment
            or port == 0
            or "cloud" in self.model.casefold()
        ):
            raise ValueError(
                "Only a loopback Ollama endpoint and local model are supported; "
                "remote/paid judges require separate approval and are not enabled by this CLI."
            )
        if not math.isfinite(self.temperature) or self.temperature < 0:
            raise ValueError("temperature must be finite and non-negative.")
        if not math.isfinite(self.threshold) or not 0 <= self.threshold <= 1:
            raise ValueError("threshold must be between 0 and 1.")
        if not math.isfinite(self.request_timeout) or self.request_timeout <= 0:
            raise ValueError("request-timeout must be finite and positive.")


def timestamp() -> str:
    return datetime.now(UTC).isoformat()


def package_version(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def outcome(status: str, reason: str | None = None) -> dict[str, Any]:
    return {
        "status": status,
        "score": None,
        "judgePassed": None,
        "judgeReason": None,
        "skipReason": reason if status == "skipped" else None,
        "errorReason": reason if status == "error" else None,
        "startedAt": timestamp(),
        "finishedAt": None,
        "usage": None,
    }


def run_judge(
    saved: SavedRun,
    config: JudgeConfig,
    *,
    judge_factory: Callable[[JudgeConfig], Any] | None = None,
) -> dict[str, Any]:
    result = {
        "schemaVersion": 1,
        "scope": SCOPE,
        "startedAt": timestamp(),
        "input": {
            "path": str(saved.path),
            "sha256": saved.sha256,
            "suiteName": saved.payload.get("suiteName", "baseline"),
            "plannedCases": len(saved.suite.cases),
            "attemptedCases": len(saved.payload["cases"]),
            **{
                key: saved.payload.get(key)
                for key in (
                    "schemaVersion",
                    "suiteId",
                    "suiteSha256",
                    "ragBackend",
                    "chatModel",
                    "embeddingModel",
                    "ragTopK",
                    "status",
                    "error",
                    "cleanupErrors",
                    "startedAt",
                    "finishedAt",
                )
            },
            "incompleteReason": saved.incomplete_reason,
        },
        "judge": {
            "provider": "ollama",
            **asdict(config),
            "modelVersionSource": "Operator-supplied; not verified against the running server.",
            "deepevalVersion": package_version("deepeval"),
            "ollamaClientVersion": package_version("ollama"),
            "pythonVersion": platform.python_version(),
            "evalMode": "llm",
            "asyncMode": False,
            "strictMode": False,
            "telemetry": False,
            "remoteOrPaidApproved": False,
        },
        "cases": [],
    }
    rows = {row["id"]: row for row in saved.payload["cases"]}
    judge, init_error = None, None
    for case in saved.suite.cases:
        row = rows.get(case.id)
        record = {
            "id": case.id,
            "fixturePassed": row.get("passed") if row else None,
            "fixtureChecks": row.get("checks") if row else None,
            "citedSnippetCount": 0,
            "metrics": {},
        }
        result["cases"].append(record)
        reason, state, snippets, gap = saved.incomplete_reason, "skipped", [], None
        if not reason and row is not None:
            try:
                validate_pair(row, case)
                snippets, gap = cited_excerpts(row, saved)
            except ValueError as error:
                reason, state = str(error), "error"
            if not reason and (case.no_answer or row["answer"].strip() == NO_ANSWER):
                reason = "Expected or actual no-answer case; use the deterministic no-answer check."
            if not reason and not row["answer"].strip():
                reason = "Empty answer; no completed question/answer pair to judge."
        elif not reason:
            reason = "Case is missing from the saved run."
        record["citedSnippetCount"] = len(snippets)
        for name in METRICS:
            metric = outcome(state if reason else "pending", reason)
            record["metrics"][name] = metric
            if not reason and name == "cited-excerpt faithfulness" and gap:
                metric.update(outcome("skipped", gap))
            elif not reason:
                try:
                    if judge is None and init_error is None:
                        try:
                            judge = (judge_factory or create_judge)(config)
                        except Exception as error:
                            init_error = f"Judge setup failed: {type(error).__name__}: {error}"
                    if init_error:
                        raise RuntimeError(init_error)
                    measured = judge.measure(name, case.question, row["answer"], snippets)
                    score, judge_reason = measured["score"], measured["judgeReason"]
                    if (
                        type(score) not in {int, float}
                        or not math.isfinite(score)
                        or not 0 <= score <= 1
                        or not isinstance(judge_reason, str)
                        or not judge_reason.strip()
                    ):
                        raise ValueError("Judge returned an invalid score or missing reason.")
                    json.dumps(measured.get("usage"), allow_nan=False)
                    metric.update(
                        status="scored",
                        score=score,
                        judgePassed=score >= config.threshold,
                        judgeReason=judge_reason,
                        usage=measured.get("usage"),
                    )
                except Exception as error:
                    metric.update(
                        status="error",
                        errorReason=f"{type(error).__name__}: {error}",
                    )
            metric["finishedAt"] = timestamp()
    result["aggregates"] = {}
    for name in METRICS:
        metrics = [row["metrics"][name] for row in result["cases"]]
        scores = [metric["score"] for metric in metrics if metric["status"] == "scored"]
        result["aggregates"][name] = {
            "counts": {
                state: sum(metric["status"] == state for metric in metrics)
                for state in ("scored", "skipped", "error")
            },
            "scoredCaseIds": [
                row["id"] for row in result["cases"] if row["metrics"][name]["status"] == "scored"
            ],
            "meanScore": sum(scores) / len(scores) if scores else None,
            "judgePassed": sum(metric["judgePassed"] is True for metric in metrics),
        }
    counts = Counter(
        metric["status"] for row in result["cases"] for metric in row["metrics"].values()
    )
    result["status"] = (
        "error" if counts["error"] else "completed" if counts["scored"] else "skipped"
    )
    result["finishedAt"] = timestamp()
    return result


def cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# CiteNook optional judge report",
        "",
        result["scope"],
        "",
        f"- Judge run status: {result['status']}",
        f"- Original deterministic fixture status: {result['input']['status']}",
        f"- Input SHA-256: `{result['input']['sha256']}`",
        f"- Suite: `{result['input']['suiteId']}` / `{result['input']['suiteSha256']}`",
        f"- Backend: {result['input']['ragBackend']}",
        f"- Judge settings and versions: `{json.dumps(result['judge'], ensure_ascii=False)}`",
        f"- UTC: {result['startedAt']} to {result['finishedAt']}",
        "",
        "Means include only scored cases for that metric in this single run; no combined score.",
    ]
    for name, summary in result["aggregates"].items():
        mean = "N/A" if summary["meanScore"] is None else f"{summary['meanScore']:.4f}"
        lines.append(
            f"- {name}: mean {mean}; {summary['counts']}; "
            f"judge verdicts meeting threshold: {summary['judgePassed']}"
        )
    lines.extend(
        [
            "",
            "| Case | Fixture pass | Metric | State | Score | Judge verdict | Reason |",
            "| --- | --- | --- | --- | ---: | --- | --- |",
        ]
    )
    for row in result["cases"]:
        for name, metric in row["metrics"].items():
            detail = metric["judgeReason"] or metric["skipReason"] or metric["errorReason"]
            score = "N/A" if metric["score"] is None else str(metric["score"])
            verdict = "N/A" if metric["judgePassed"] is None else str(metric["judgePassed"])
            lines.append(
                "| "
                + " | ".join(
                    map(
                        cell,
                        (
                            row["id"],
                            row["fixturePassed"],
                            name,
                            metric["status"],
                            score,
                            verdict,
                            detail,
                        ),
                    )
                )
                + " |"
            )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Judge saved synthetic RAG results with local Ollama."
    )
    parser.add_argument("--input", type=Path, required=True, help="Existing fixture results.json.")
    parser.add_argument("--output-dir", type=Path, required=True, help="New output directory only.")
    parser.add_argument("--model", required=True, help="Installed local Ollama judge model.")
    parser.add_argument("--model-version", required=True, help="Operator-supplied digest/version.")
    parser.add_argument("--base-url", required=True, help="Explicit loopback Ollama URL.")
    parser.add_argument("--temperature", type=float, required=True)
    parser.add_argument("--threshold", type=float, required=True)
    parser.add_argument("--request-timeout", type=float, required=True)
    parser.add_argument(
        "--synthetic-data", action="store_true", help="Confirm synthetic fixture data."
    )
    args = parser.parse_args(argv)
    try:
        config = JudgeConfig(
            args.model,
            args.model_version,
            args.base_url,
            args.temperature,
            args.threshold,
            args.request_timeout,
            args.synthetic_data,
        )
        saved = load_results(args.input)
        args.output_dir.mkdir(parents=True, exist_ok=False)
        print(f"Judge settings: {json.dumps(asdict(config))}")
        result = run_judge(saved, config)
        (args.output_dir / "judge-scores.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        (args.output_dir / "judge-report.md").write_text(render_report(result), encoding="utf-8")
    except (OSError, ValueError) as error:
        print(f"Judge could not start or write: {error}", file=sys.stderr)
        return 2
    print(f"Judge run {result['status']}; output: {args.output_dir}")
    return {"completed": 0, "skipped": 1, "error": 2}[result["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
