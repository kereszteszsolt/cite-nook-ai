# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import argparse
import asyncio
import csv
import ipaddress
import json
import os
import sys
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic, sleep
from typing import Any, Protocol
from urllib.parse import urlparse

import httpx

from .ragas_dataset import EvaluationCase, EvaluationDataset, load_evaluation_dataset

DEFAULT_API_URL = "http://localhost:8000/api"
DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_INGESTION_TIMEOUT_SECONDS = 180.0
DEFAULT_POLL_INTERVAL_SECONDS = 1.0
DEFAULT_REQUEST_TIMEOUT_SECONDS = 180.0


class EvaluationError(RuntimeError):
    """A bounded, actionable local evaluation failure."""


@dataclass(frozen=True, slots=True)
class Citation:
    source_id: str
    document_id: str
    document_name: str
    page_number: int | None
    chunk_id: str
    snippet: str
    score: float


@dataclass(frozen=True, slots=True)
class AnswerCapture:
    response: str
    citations: tuple[Citation, ...]
    duration_ms: int


@dataclass(frozen=True, slots=True)
class EvaluationSample:
    user_input: str
    response: str
    reference: str
    retrieved_contexts: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MetricScores:
    faithfulness: float
    factual_correctness: float


@dataclass(frozen=True, slots=True)
class CaseResult:
    case_id: str
    question: str
    reference: str
    answer_model: str
    embedding_model: str
    evaluator_model: str
    answer: str
    citations: tuple[Citation, ...]
    faithfulness: float | None
    factual_correctness: float | None
    duration_ms: int | None
    status: str
    error: str | None


@dataclass(frozen=True, slots=True)
class RunResult:
    run_id: str
    started_at: str
    api_url: str
    ollama_url: str
    answer_model: str
    embedding_model: str
    evaluator_model: str
    case_results: tuple[CaseResult, ...]
    cleanup_errors: tuple[str, ...]
    retained_resources: bool

    @property
    def status(self) -> str:
        if self.cleanup_errors or any(result.status != "scored" for result in self.case_results):
            return "completed_with_errors"
        return "completed"

    def to_dict(self) -> dict[str, Any]:
        scores = {
            "faithfulness": aggregate_score(result.faithfulness for result in self.case_results),
            "factualCorrectness": aggregate_score(
                result.factual_correctness for result in self.case_results
            ),
        }
        return {
            "schemaVersion": 1,
            "runId": self.run_id,
            "startedAt": self.started_at,
            "status": self.status,
            "apiUrl": self.api_url,
            "ollamaUrl": self.ollama_url,
            "models": {
                "answer": self.answer_model,
                "embedding": self.embedding_model,
                "evaluator": self.evaluator_model,
            },
            "caseCount": len(self.case_results),
            "scoredCaseCount": sum(result.status == "scored" for result in self.case_results),
            "aggregateScores": scores,
            "cleanupErrors": list(self.cleanup_errors),
            "retainedResources": self.retained_resources,
            "interpretation": "Model-assisted signals, not human ground truth or a benchmark.",
            "cases": [case_result_dict(result) for result in self.case_results],
        }


class ApiBoundary(Protocol):
    def upload_document(
        self, *, fixture_path: Path, upload_name: str, embedding_model: str
    ) -> str: ...

    def document_state(self, document_id: str) -> tuple[str, str | None]: ...

    def create_conversation(self, *, title: str, chat_model: str, embedding_model: str) -> str: ...

    def ask(self, *, conversation_id: str, question: str) -> AnswerCapture: ...

    def delete_conversation(self, conversation_id: str) -> None: ...

    def delete_document(self, document_id: str) -> None: ...


class EvaluatorBoundary(Protocol):
    def score(self, sample: EvaluationSample) -> MetricScores: ...


class HttpApiBoundary:
    def __init__(self, *, api_url: str, request_timeout_seconds: float) -> None:
        self._client = httpx.Client(
            base_url=api_url.rstrip("/"),
            timeout=request_timeout_seconds,
        )

    def _json(self, response: httpx.Response, *, action: str) -> dict[str, Any]:
        try:
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as error:
            detail = response.text.strip()[:300]
            raise EvaluationError(f"CiteNook API could not {action}: {detail or error}") from error
        if not isinstance(payload, dict):
            raise EvaluationError(
                f"CiteNook API returned an invalid response while trying to {action}"
            )
        return payload

    def upload_document(self, *, fixture_path: Path, upload_name: str, embedding_model: str) -> str:
        try:
            with fixture_path.open("rb") as fixture:
                response = self._client.post(
                    "/documents",
                    data={"embedding_model": embedding_model},
                    files={"file": (upload_name, fixture, "text/markdown")},
                )
        except (OSError, httpx.HTTPError) as error:
            raise EvaluationError(f"Could not upload the evaluation fixture: {error}") from error
        payload = self._json(response, action="upload the evaluation fixture")
        return required_string(payload, "id", action="upload the evaluation fixture")

    def document_state(self, document_id: str) -> tuple[str, str | None]:
        try:
            response = self._client.get("/documents")
        except httpx.HTTPError as error:
            raise EvaluationError(f"Could not poll evaluation document: {error}") from error
        try:
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as error:
            raise EvaluationError("CiteNook API returned an invalid document list") from error
        if not isinstance(payload, list):
            raise EvaluationError("CiteNook API returned an invalid document list")
        document = next(
            (item for item in payload if isinstance(item, dict) and item.get("id") == document_id),
            None,
        )
        if document is None:
            raise EvaluationError("The evaluation document disappeared while ingestion was polled")
        status = required_string(document, "status", action="poll the evaluation document")
        error_message = document.get("errorMessage")
        return status, error_message if isinstance(error_message, str) else None

    def create_conversation(self, *, title: str, chat_model: str, embedding_model: str) -> str:
        try:
            response = self._client.post(
                "/conversations",
                json={"chatModel": chat_model, "embeddingModel": embedding_model},
            )
        except httpx.HTTPError as error:
            raise EvaluationError(f"Could not create evaluation conversation: {error}") from error
        payload = self._json(response, action="create an evaluation conversation")
        conversation_id = required_string(payload, "id", action="create an evaluation conversation")
        try:
            rename_response = self._client.patch(
                f"/conversations/{conversation_id}", json={"title": title}
            )
        except httpx.HTTPError as error:
            self._best_effort_delete_conversation(conversation_id)
            raise EvaluationError(f"Could not tag evaluation conversation: {error}") from error
        try:
            self._json(rename_response, action="tag an evaluation conversation")
        except EvaluationError:
            self._best_effort_delete_conversation(conversation_id)
            raise
        return conversation_id

    def ask(self, *, conversation_id: str, question: str) -> AnswerCapture:
        try:
            response = self._client.post(
                f"/conversations/{conversation_id}/messages", json={"question": question}
            )
        except httpx.HTTPError as error:
            raise EvaluationError(f"Could not collect CiteNook answer: {error}") from error
        payload = self._json(response, action="collect a CiteNook answer")
        assistant = payload.get("assistantMessage")
        if not isinstance(assistant, dict):
            raise EvaluationError("CiteNook answer is missing assistantMessage")
        raw_citations = assistant.get("citations")
        if not isinstance(raw_citations, list):
            raise EvaluationError("CiteNook answer contains invalid citations")
        citations = tuple(parse_citation(value) for value in raw_citations)
        duration = assistant.get("responseDurationMs")
        if not isinstance(duration, int) or isinstance(duration, bool) or duration < 0:
            raise EvaluationError("CiteNook answer contains an invalid responseDurationMs")
        return AnswerCapture(
            response=required_string(assistant, "content", action="collect a CiteNook answer"),
            citations=citations,
            duration_ms=duration,
        )

    def delete_conversation(self, conversation_id: str) -> None:
        self._delete(f"/conversations/{conversation_id}", "conversation")

    def _best_effort_delete_conversation(self, conversation_id: str) -> None:
        try:
            self.delete_conversation(conversation_id)
        except EvaluationError:
            pass

    def delete_document(self, document_id: str) -> None:
        self._delete(f"/documents/{document_id}", "document")

    def _delete(self, path: str, resource: str) -> None:
        try:
            response = self._client.delete(path)
            response.raise_for_status()
        except httpx.HTTPError as error:
            raise EvaluationError(f"Could not delete evaluation {resource}: {error}") from error

    def close(self) -> None:
        self._client.close()


class RagasOllamaEvaluator:
    def __init__(
        self,
        *,
        evaluator_model: str,
        ollama_url: str,
        request_timeout_seconds: float,
    ) -> None:
        validate_local_http_url(ollama_url, label="Ollama URL")
        os.environ["RAGAS_DO_NOT_TRACK"] = "true"
        try:
            from openai import AsyncOpenAI
            from ragas.llms import llm_factory
            from ragas.metrics.collections import FactualCorrectness, Faithfulness
        except ModuleNotFoundError as error:
            raise EvaluationError(
                "The optional Ragas dependencies are not installed. Run "
                "'uv sync --directory apps/api --extra framework-evaluation --group dev'."
            ) from error
        client = AsyncOpenAI(
            api_key="ollama-local-no-secret",
            base_url=f"{ollama_url.rstrip('/')}/v1",
            timeout=request_timeout_seconds,
            max_retries=0,
        )
        llm = llm_factory(
            evaluator_model,
            provider="openai",
            client=client,
            temperature=0,
            extra_body={"think": False},
        )
        self._faithfulness = Faithfulness(llm=llm)
        self._factual_correctness = FactualCorrectness(llm=llm)
        self._client = client
        self._async_runner = asyncio.Runner()

    def score(self, sample: EvaluationSample) -> MetricScores:
        try:
            return self._async_runner.run(self._score(sample))
        except Exception as error:
            raise EvaluationError(
                "Local Ragas evaluation failed. Check the evaluator model and Ollama URL."
            ) from error

    def close(self) -> None:
        try:
            self._async_runner.run(self._client.close())
        finally:
            self._async_runner.close()

    async def _score(self, sample: EvaluationSample) -> MetricScores:
        ragas_sample = build_ragas_sample(sample)
        faithfulness = await self._faithfulness.ascore(
            user_input=ragas_sample.user_input,
            response=ragas_sample.response,
            retrieved_contexts=ragas_sample.retrieved_contexts,
        )
        factual_correctness = await self._factual_correctness.ascore(
            response=ragas_sample.response,
            reference=ragas_sample.reference,
        )
        return MetricScores(
            faithfulness=validated_score(float(faithfulness), metric="faithfulness"),
            factual_correctness=validated_score(
                float(factual_correctness), metric="factual correctness"
            ),
        )


def build_ragas_sample(sample: EvaluationSample) -> Any:
    try:
        from ragas.dataset_schema import SingleTurnSample
    except ModuleNotFoundError as error:
        raise EvaluationError("The optional Ragas dependencies are not installed") from error
    return SingleTurnSample(
        user_input=sample.user_input,
        response=sample.response,
        reference=sample.reference,
        retrieved_contexts=list(sample.retrieved_contexts),
    )


class EvaluationRunner:
    def __init__(
        self,
        *,
        api: ApiBoundary,
        evaluator: EvaluatorBoundary,
        clock: Callable[[], float] = monotonic,
        sleeper: Callable[[float], None] = sleep,
    ) -> None:
        self._api = api
        self._evaluator = evaluator
        self._clock = clock
        self._sleep = sleeper

    def run(
        self,
        dataset: EvaluationDataset,
        *,
        run_id: str,
        started_at: str,
        api_url: str,
        ollama_url: str,
        answer_model: str,
        embedding_model: str,
        evaluator_model: str,
        ingestion_timeout_seconds: float,
        poll_interval_seconds: float,
        retain_resources: bool,
    ) -> RunResult:
        if ingestion_timeout_seconds <= 0 or poll_interval_seconds <= 0:
            raise EvaluationError("Ingestion timeout and poll interval must be positive")
        document_id: str | None = None
        conversation_ids: list[str] = []
        results: list[CaseResult] = []
        cleanup_errors: list[str] = []
        try:
            document_id = self._api.upload_document(
                fixture_path=dataset.fixture_path,
                upload_name=f"mra019-{run_id}-mosslight.md",
                embedding_model=embedding_model,
            )
            self._wait_until_ready(
                document_id,
                timeout_seconds=ingestion_timeout_seconds,
                poll_interval_seconds=poll_interval_seconds,
            )
            for case in dataset.cases:
                results.append(
                    self._run_case(
                        case,
                        run_id=run_id,
                        answer_model=answer_model,
                        embedding_model=embedding_model,
                        evaluator_model=evaluator_model,
                        conversation_ids=conversation_ids,
                    )
                )
        finally:
            if not retain_resources:
                for conversation_id in reversed(conversation_ids):
                    try:
                        self._api.delete_conversation(conversation_id)
                    except Exception as error:
                        cleanup_errors.append(str(error))
                if document_id is not None:
                    try:
                        self._api.delete_document(document_id)
                    except Exception as error:
                        cleanup_errors.append(str(error))
        return RunResult(
            run_id=run_id,
            started_at=started_at,
            api_url=api_url,
            ollama_url=ollama_url,
            answer_model=answer_model,
            embedding_model=embedding_model,
            evaluator_model=evaluator_model,
            case_results=tuple(results),
            cleanup_errors=tuple(cleanup_errors),
            retained_resources=retain_resources,
        )

    def _wait_until_ready(
        self, document_id: str, *, timeout_seconds: float, poll_interval_seconds: float
    ) -> None:
        deadline = self._clock() + timeout_seconds
        while True:
            status, error_message = self._api.document_state(document_id)
            if status == "ready":
                return
            if status == "failed":
                raise EvaluationError(
                    f"Evaluation fixture ingestion failed: {error_message or 'no reason returned'}"
                )
            if status not in {"queued", "processing"}:
                raise EvaluationError(f"Evaluation fixture has unsupported status: {status}")
            remaining = deadline - self._clock()
            if remaining <= 0:
                raise EvaluationError(
                    f"Evaluation fixture was not ready within {timeout_seconds:g} seconds"
                )
            self._sleep(min(poll_interval_seconds, remaining))

    def _run_case(
        self,
        case: EvaluationCase,
        *,
        run_id: str,
        answer_model: str,
        embedding_model: str,
        evaluator_model: str,
        conversation_ids: list[str],
    ) -> CaseResult:
        answer = ""
        citations: tuple[Citation, ...] = ()
        duration_ms: int | None = None
        try:
            conversation_id = self._api.create_conversation(
                title=f"MRA-019 eval {run_id} {case.case_id}",
                chat_model=answer_model,
                embedding_model=embedding_model,
            )
            conversation_ids.append(conversation_id)
            captured = self._api.ask(conversation_id=conversation_id, question=case.question)
            answer = captured.response
            citations = captured.citations
            duration_ms = captured.duration_ms
            if not citations:
                raise EvaluationError(
                    "CiteNook returned no citation snippets; Ragas faithfulness cannot be scored."
                )
            sample = EvaluationSample(
                user_input=case.question,
                response=answer,
                reference=case.reference,
                retrieved_contexts=tuple(citation.snippet for citation in citations),
            )
            scores = self._evaluator.score(sample)
            return CaseResult(
                case_id=case.case_id,
                question=case.question,
                reference=case.reference,
                answer_model=answer_model,
                embedding_model=embedding_model,
                evaluator_model=evaluator_model,
                answer=answer,
                citations=citations,
                faithfulness=scores.faithfulness,
                factual_correctness=scores.factual_correctness,
                duration_ms=duration_ms,
                status="scored",
                error=None,
            )
        except Exception as error:
            return CaseResult(
                case_id=case.case_id,
                question=case.question,
                reference=case.reference,
                answer_model=answer_model,
                embedding_model=embedding_model,
                evaluator_model=evaluator_model,
                answer=answer,
                citations=citations,
                faithfulness=None,
                factual_correctness=None,
                duration_ms=duration_ms,
                status="error",
                error=str(error),
            )


def required_string(payload: dict[str, Any], key: str, *, action: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise EvaluationError(f"CiteNook API response could not {action}: missing {key}")
    return value


def parse_citation(payload: Any) -> Citation:
    if not isinstance(payload, dict):
        raise EvaluationError("CiteNook answer contains an invalid citation")
    page_number = payload.get("pageNumber")
    score = payload.get("score")
    if page_number is not None and (
        not isinstance(page_number, int) or isinstance(page_number, bool)
    ):
        raise EvaluationError("CiteNook citation contains an invalid pageNumber")
    if not isinstance(score, (int, float)) or isinstance(score, bool):
        raise EvaluationError("CiteNook citation contains an invalid score")
    return Citation(
        source_id=required_string(payload, "sourceId", action="parse a citation"),
        document_id=required_string(payload, "documentId", action="parse a citation"),
        document_name=required_string(payload, "documentName", action="parse a citation"),
        page_number=page_number,
        chunk_id=required_string(payload, "chunkId", action="parse a citation"),
        snippet=required_string(payload, "snippet", action="parse a citation"),
        score=float(score),
    )


def validate_local_http_url(value: str, *, label: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme != "http" or not parsed.hostname or parsed.username or parsed.password:
        raise EvaluationError(
            f"{label} must be an explicit local http:// endpoint without credentials"
        )
    if parsed.query or parsed.fragment:
        raise EvaluationError(f"{label} must not contain a query or fragment")
    hostname = parsed.hostname.lower()
    is_local_name = (
        hostname in {"localhost", "host.docker.internal", "api", "ollama"}
        or "." not in hostname
        or hostname.endswith(".local")
    )
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        address = None
    is_local_address = address is not None and (address.is_loopback or address.is_private)
    if not is_local_name and not is_local_address:
        raise EvaluationError(f"{label} must resolve to a local or private-network host")
    return value.rstrip("/")


def validated_score(value: float, *, metric: str) -> float:
    if not 0.0 <= value <= 1.0:
        raise EvaluationError(f"Ragas {metric} score is outside the expected 0..1 range")
    return round(value, 6)


def aggregate_score(values: Sequence[float | None] | Any) -> float | None:
    scores = [value for value in values if value is not None]
    if not scores:
        return None
    return round(sum(scores) / len(scores), 6)


def case_result_dict(result: CaseResult) -> dict[str, Any]:
    payload = asdict(result)
    payload["caseId"] = payload.pop("case_id")
    payload["answerModel"] = payload.pop("answer_model")
    payload["embeddingModel"] = payload.pop("embedding_model")
    payload["evaluatorModel"] = payload.pop("evaluator_model")
    payload["factualCorrectness"] = payload.pop("factual_correctness")
    payload["durationMs"] = payload.pop("duration_ms")
    return payload


def write_artifacts(result: RunResult, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{result.run_id}.json"
    csv_path = output_dir / f"{result.run_id}.csv"
    json_path.write_text(json.dumps(result.to_dict(), indent=2) + "\n", encoding="utf-8")
    fieldnames = [
        "run_id",
        "case_id",
        "status",
        "answer_model",
        "embedding_model",
        "evaluator_model",
        "question",
        "reference",
        "answer",
        "citation_ids",
        "citation_snippets",
        "citation_scores",
        "faithfulness",
        "factual_correctness",
        "duration_ms",
        "error",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for case in result.case_results:
            writer.writerow(
                {
                    "run_id": result.run_id,
                    "case_id": case.case_id,
                    "status": case.status,
                    "answer_model": case.answer_model,
                    "embedding_model": case.embedding_model,
                    "evaluator_model": case.evaluator_model,
                    "question": case.question,
                    "reference": case.reference,
                    "answer": case.answer,
                    "citation_ids": json.dumps([citation.chunk_id for citation in case.citations]),
                    "citation_snippets": json.dumps(
                        [citation.snippet for citation in case.citations]
                    ),
                    "citation_scores": json.dumps([citation.score for citation in case.citations]),
                    "faithfulness": case.faithfulness,
                    "factual_correctness": case.factual_correctness,
                    "duration_ms": case.duration_ms,
                    "error": case.error,
                }
            )
    return json_path, csv_path


def build_parser(repo_root: Path) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the privacy-safe local CiteNook Ragas evaluation."
    )
    parser.add_argument("--api-url", default=os.getenv("CITENOOK_API_URL", DEFAULT_API_URL))
    parser.add_argument("--ollama-url", default=os.getenv("OLLAMA_HOST", DEFAULT_OLLAMA_URL))
    parser.add_argument("--answer-model", required=True)
    parser.add_argument("--embedding-model", required=True)
    parser.add_argument("--evaluator-model", required=True)
    parser.add_argument(
        "--dataset", type=Path, default=repo_root / "evals/fixtures/mra-019-cases.json"
    )
    parser.add_argument("--output-dir", type=Path, default=repo_root / "evals/experiments")
    parser.add_argument(
        "--ingestion-timeout-seconds", type=float, default=DEFAULT_INGESTION_TIMEOUT_SECONDS
    )
    parser.add_argument(
        "--poll-interval-seconds", type=float, default=DEFAULT_POLL_INTERVAL_SECONDS
    )
    parser.add_argument(
        "--request-timeout-seconds", type=float, default=DEFAULT_REQUEST_TIMEOUT_SECONDS
    )
    parser.add_argument(
        "--retain-resources",
        action="store_true",
        help="Retain only resources created by this run for diagnosis.",
    )
    return parser


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    args = build_parser(repo_root).parse_args()
    started = datetime.now(UTC)
    run_id = started.strftime("mra019-%Y%m%dT%H%M%SZ")
    api: HttpApiBoundary | None = None
    evaluator: RagasOllamaEvaluator | None = None
    try:
        api_url = validate_local_http_url(args.api_url, label="CiteNook API URL")
        ollama_url = validate_local_http_url(args.ollama_url, label="Ollama URL")
        dataset = load_evaluation_dataset(args.dataset, repo_root=repo_root)
        if args.answer_model == args.evaluator_model:
            print(
                "Warning: the answer and evaluator models are identical; correlated judgment "
                "may make scores less informative.",
                file=sys.stderr,
            )
        print(
            "Ragas scores are model-assisted signals, not human ground truth or a benchmark.",
            file=sys.stderr,
        )
        api = HttpApiBoundary(api_url=api_url, request_timeout_seconds=args.request_timeout_seconds)
        evaluator = RagasOllamaEvaluator(
            evaluator_model=args.evaluator_model,
            ollama_url=ollama_url,
            request_timeout_seconds=args.request_timeout_seconds,
        )
        result = EvaluationRunner(api=api, evaluator=evaluator).run(
            dataset,
            run_id=run_id,
            started_at=started.isoformat(),
            api_url=api_url,
            ollama_url=ollama_url,
            answer_model=args.answer_model,
            embedding_model=args.embedding_model,
            evaluator_model=args.evaluator_model,
            ingestion_timeout_seconds=args.ingestion_timeout_seconds,
            poll_interval_seconds=args.poll_interval_seconds,
            retain_resources=args.retain_resources,
        )
        json_path, csv_path = write_artifacts(result, args.output_dir)
        summary = result.to_dict()
        print(
            json.dumps(
                {
                    "runId": result.run_id,
                    "status": result.status,
                    "caseCount": summary["caseCount"],
                    "scoredCaseCount": summary["scoredCaseCount"],
                    "aggregateScores": summary["aggregateScores"],
                    "jsonArtifact": str(json_path),
                    "csvArtifact": str(csv_path),
                },
                indent=2,
            )
        )
        if result.status != "completed":
            raise SystemExit(1)
    except (EvaluationError, ValueError) as error:
        print(f"Evaluation failed: {error}", file=sys.stderr)
        raise SystemExit(2) from error
    finally:
        if evaluator is not None:
            evaluator.close()
        if api is not None:
            api.close()


if __name__ == "__main__":
    main()
