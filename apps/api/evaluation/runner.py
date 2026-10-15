# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

import httpx

from .suite import NO_ANSWER, Case, load_suite

SCOPE = (
    "Small synthetic fixture checks only; these are not retrieval recall, factual accuracy, "
    "or model-graded faithfulness scores. Key facts use case-insensitive whole-term matching."
)


@dataclass(frozen=True)
class RunConfig:
    backend: str
    chat_model: str
    embedding_model: str
    rag_top_k: int
    indexing_timeout: float = 300
    poll_interval: float = 1

    def __post_init__(self) -> None:
        if self.backend not in {"native", "llamaindex"}:
            raise ValueError("Backend must be native or llamaindex.")
        if not self.chat_model.strip() or not self.embedding_model.strip():
            raise ValueError("Select both chat and embedding models.")
        for value in (self.rag_top_k, self.indexing_timeout, self.poll_interval):
            if not math.isfinite(value) or value <= 0:
                raise ValueError("RAG_TOP_K and timeout/poll values must be finite and positive.")


class EvaluationError(RuntimeError):
    pass


def request(client: httpx.Client, method: str, path: str, **kwargs: Any) -> httpx.Response:
    try:
        response = client.request(method, path, **kwargs)
        response.raise_for_status()
        return response
    except httpx.HTTPError as error:
        raise EvaluationError(f"{method} {path}: {error}") from error


def request_json(client: httpx.Client, method: str, path: str, **kwargs: Any) -> Any:
    response = request(client, method, path, **kwargs)
    try:
        return response.json()
    except ValueError as error:
        raise EvaluationError(f"{method} {path}: invalid JSON response.") from error


def check_backend(client: httpx.Client, backend: str) -> None:
    health = request_json(client, "GET", "health")
    if (
        not isinstance(health, dict)
        or health.get("status") != "ok"
        or health.get("appId") != "cite-nook-ai"
    ):
        raise EvaluationError("The endpoint is not a healthy CiteNook deployment.")
    if health.get("ragBackend") != backend:
        raise EvaluationError(
            f"Expected ragBackend={backend}, received {health.get('ragBackend')!r}."
        )


def check_models(client: httpx.Client, chat_model: str, embedding_model: str) -> None:
    catalog = request_json(client, "GET", "models")
    if not isinstance(catalog, dict) or catalog.get("ollamaAvailable") is not True:
        raise EvaluationError("Ollama is unavailable; install the selected models before running.")
    for key, model in (("chatModels", chat_model), ("embeddingModels", embedding_model)):
        if not any(item["name"] == model and item["installed"] is True for item in catalog[key]):
            raise EvaluationError(
                f"Selected model is not configured and installed in {key}: {model}."
            )


def run_documents(client: httpx.Client, owned: dict[str, str]) -> dict[str, Any]:
    rows = request_json(client, "GET", "documents")
    if not isinstance(rows, list):
        raise EvaluationError("GET documents: expected a document list.")
    documents = {row["id"]: row for row in rows}
    if documents.keys() - owned.keys():
        raise EvaluationError("Use an isolated deployment with no documents outside this run.")
    if owned.keys() - documents.keys():
        raise EvaluationError("A document created by this run is missing.")
    return documents


def wait_for_ready(
    client: httpx.Client,
    owned: dict[str, str],
    config: RunConfig,
    *,
    clock: Callable[[], float],
    sleep: Callable[[float], None],
) -> None:
    deadline = clock() + config.indexing_timeout
    while True:
        documents = run_documents(client, owned)
        for document_id, row in documents.items():
            if row["status"] == "failed":
                raise EvaluationError(
                    f"Indexing failed for {owned[document_id]}: {row['errorMessage']}"
                )
            if row["status"] not in {"queued", "processing", "ready"}:
                raise EvaluationError(f"Unexpected indexing state for {owned[document_id]}.")
            if row["embeddingModel"] != config.embedding_model or row["isActive"] is not True:
                raise EvaluationError(
                    f"Document model or active state changed: {owned[document_id]}."
                )
        if all(row["status"] == "ready" for row in documents.values()):
            return
        remaining = deadline - clock()
        if remaining <= 0:
            raise EvaluationError("Timed out waiting for fixture documents to become ready.")
        sleep(min(config.poll_interval, remaining))


def check_answer(case: Case, message: dict[str, Any], owned: dict[str, str]) -> dict[str, Any]:
    answer = message["content"]
    citations = message["citations"]
    duration = message["responseDurationMs"]
    if not isinstance(answer, str) or not isinstance(citations, list):
        raise EvaluationError("The assistant response must contain answer text and citations.")
    if type(duration) is not int or duration < 0:
        raise EvaluationError(
            "The assistant response must contain a non-negative responseDurationMs."
        )
    for citation in citations:
        if (
            citation["documentId"] not in owned
            or owned[citation["documentId"]] != citation["documentName"]
        ):
            raise EvaluationError(
                "The answer cites a document outside this run or a wrong file name."
            )
    names = sorted({citation["documentName"] for citation in citations})
    fact_matches = {
        fact: bool(re.search(r"(?<!\w)" + re.escape(fact) + r"(?!\w)", answer, re.IGNORECASE))
        for fact in case.key_facts
    }
    checks = {
        "expectedSources": names == sorted(case.expected_sources),
        "keyFacts": all(fact_matches.values()) if not case.no_answer else None,
        "noAnswer": answer.strip() == NO_ANSWER and not citations if case.no_answer else None,
    }
    return {
        "answer": answer,
        "citedDocumentNames": names,
        "responseDurationMs": duration,
        "factMatches": fact_matches,
        "checks": checks,
        "passed": all(value is not False for value in checks.values()),
    }


def cleanup(client: httpx.Client, resource: str, ids: list[str]) -> list[dict[str, str]]:
    errors = []
    for record_id in reversed(ids):
        try:
            response = client.delete(f"{resource}/{record_id}")
            if response.status_code not in {204, 404}:
                raise EvaluationError(f"DELETE returned HTTP {response.status_code}.")
        except (httpx.HTTPError, EvaluationError) as error:
            errors.append({"resource": resource, "id": record_id, "error": str(error)})
    return errors


def run_evaluation(
    client: httpx.Client,
    config: RunConfig,
    *,
    clock: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    suite = load_suite()
    owned: dict[str, str] = {}
    conversations: list[str] = []
    result: dict[str, Any] = {
        "schemaVersion": 1,
        "suiteId": suite.id,
        "suiteSha256": suite.sha256,
        "startedAt": datetime.now(UTC).isoformat(),
        "apiUrl": str(client.base_url),
        "ragBackend": config.backend,
        "chatModel": config.chat_model,
        "embeddingModel": config.embedding_model,
        "ragTopK": config.rag_top_k,
        "ragTopKSource": "Operator-supplied; the public API does not expose this setting.",
        "scope": SCOPE,
        "status": "error",
        "error": None,
        "documents": owned,
        "conversationIds": conversations,
        "cleanupErrors": [],
        "cases": [],
    }
    current: dict[str, Any] | None = None
    try:
        check_backend(client, config.backend)
        check_models(client, config.chat_model, config.embedding_model)
        run_documents(client, owned)
        for path in suite.documents:
            row = request_json(
                client,
                "POST",
                "documents",
                files={"file": (path.name, path.read_bytes(), "text/markdown")},
                data={"embedding_model": config.embedding_model},
            )
            document_id = str(UUID(row["id"]))
            owned[document_id] = path.name
            if row["fileName"] != path.name:
                raise EvaluationError("The upload returned a wrong fixture file name.")
        wait_for_ready(client, owned, config, clock=clock, sleep=sleep)
        for case in suite.cases:
            current = None
            run_documents(client, owned)
            current = {
                "id": case.id,
                "question": case.question,
                "expectedSources": list(case.expected_sources),
                "keyFacts": list(case.key_facts),
                "expectsNoAnswer": case.no_answer,
                "answer": None,
                "citedDocumentNames": [],
                "responseDurationMs": None,
                "checks": None,
                "passed": False,
                "error": None,
            }
            result["cases"].append(current)
            conversation = request_json(
                client,
                "POST",
                "conversations",
                json={"chatModel": config.chat_model, "embeddingModel": config.embedding_model},
            )
            conversation_id = str(UUID(conversation["id"]))
            conversations.append(conversation_id)
            current["conversationId"] = conversation_id
            if (
                conversation["chatModel"] != config.chat_model
                or conversation["embeddingModel"] != config.embedding_model
            ):
                raise EvaluationError("The conversation returned a wrong model pair.")
            payload = request_json(
                client,
                "POST",
                f"conversations/{conversation_id}/messages",
                json={"question": case.question},
            )
            message = payload["assistantMessage"]
            if (
                message["role"] != "assistant"
                or message["conversationId"] != conversation_id
                or message["chatModel"] != config.chat_model
            ):
                raise EvaluationError(
                    "The response does not match this conversation and chat model."
                )
            current.update(check_answer(case, message, owned))
        result["status"] = "passed" if all(case["passed"] for case in result["cases"]) else "failed"
    except (EvaluationError, KeyError, TypeError, ValueError, OSError) as error:
        result["error"] = str(error)
        if current is not None:
            current["error"] = str(error)
    except KeyboardInterrupt:
        result["error"] = "Run interrupted."
        if current is not None:
            current["error"] = result["error"]
    finally:
        result["cleanupErrors"].extend(cleanup(client, "conversations", conversations))
        result["cleanupErrors"].extend(cleanup(client, "documents", list(owned)))
        if result["cleanupErrors"]:
            result["status"] = "error"
        result["finishedAt"] = datetime.now(UTC).isoformat()
    return result


def render_report(result: dict[str, Any]) -> str:
    cases = result["cases"]
    passed = sum(case["passed"] for case in cases)
    checks = {
        key: [
            case["checks"][key]
            for case in cases
            if case["checks"] is not None and case["checks"][key] is not None
        ]
        for key in ("expectedSources", "keyFacts", "noAnswer")
    }
    lines = [
        "# CiteNook fixture run",
        "",
        SCOPE,
        "",
        f"- Status: {result['status']}",
        f"- Started: {result['startedAt']}",
        f"- Backend: {result['ragBackend']}",
        f"- Chat model: `{result['chatModel']}`",
        f"- Embedding model: `{result['embeddingModel']}`",
        f"- RAG_TOP_K: {result['ragTopK']} (operator-supplied, not API-verified)",
        f"- Suite: `{result['suiteId']}` / `{result['suiteSha256']}`",
        f"- Fixture checks passed: {passed}/{len(cases)} attempted (12 planned)",
        *(f"- {key}: {sum(values)}/{len(values)} checked" for key, values in checks.items()),
        "",
        "| Case | Fixture check | API response time (ms) |",
        "| --- | --- | ---: |",
    ]
    for case in cases:
        state = "error" if case["error"] else "pass" if case["passed"] else "fail"
        lines.append(f"| {case['id']} | {state} | {case['responseDurationMs']} |")
    if result["error"]:
        lines.extend(["", f"Run error: {result['error']}"])
    lines.extend(["", f"Cleanup errors: {len(result['cleanupErrors'])}."])
    for error in result["cleanupErrors"]:
        lines.append(f"- {error['resource']}/{error['id']}: {error['error']}")
    return "\n".join(lines) + "\n"


def positive_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("Use a finite positive number.")
    return number


def positive_int(value: str) -> int:
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("Use a positive integer.")
    return number


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the small CiteNook HTTP fixture suite.")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--backend", choices=("native", "llamaindex"), required=True)
    parser.add_argument("--chat-model", required=True)
    parser.add_argument("--embedding-model", required=True)
    parser.add_argument(
        "--rag-top-k",
        type=positive_int,
        required=True,
        help="Record the deployment's RAG_TOP_K; the API cannot verify it.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Create a new directory for results.json and report.md.",
    )
    parser.add_argument("--indexing-timeout", type=positive_float, default=300)
    parser.add_argument("--poll-interval", type=positive_float, default=1)
    parser.add_argument("--request-timeout", type=positive_float, default=330)
    args = parser.parse_args(argv)
    try:
        config = RunConfig(
            args.backend,
            args.chat_model,
            args.embedding_model,
            args.rag_top_k,
            args.indexing_timeout,
            args.poll_interval,
        )
        args.output_dir.mkdir(parents=True, exist_ok=False)
        with httpx.Client(
            base_url=args.base_url.rstrip("/") + "/api/",
            timeout=args.request_timeout,
        ) as client:
            result = run_evaluation(client, config)
        (args.output_dir / "results.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        (args.output_dir / "report.md").write_text(render_report(result), encoding="utf-8")
    except (OSError, ValueError, httpx.InvalidURL) as error:
        print(f"Evaluation could not write or start: {error}", file=sys.stderr)
        return 2
    print(f"Fixture run {result['status']}; output: {args.output_dir}")
    return {"passed": 0, "failed": 1, "error": 2}[result["status"]]
