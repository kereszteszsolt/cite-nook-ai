# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import csv
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from app.evaluation.ragas_dataset import (
    DatasetValidationError,
    EvaluationCase,
    EvaluationDataset,
    load_evaluation_dataset,
)
from app.evaluation.ragas_evaluate import (
    AnswerCapture,
    CaseResult,
    Citation,
    EvaluationError,
    EvaluationRunner,
    EvaluationSample,
    MetricScores,
    RagasOllamaEvaluator,
    RunResult,
    build_ragas_sample,
    validate_local_http_url,
    write_artifacts,
)


def dataset_payload() -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "fixture": "evals/fixtures/invented.md",
        "cases": [
            {
                "id": f"case-{index}",
                "question": f"Question {index}?",
                "reference": f"Reference {index}.",
                "evidenceHints": [f"Evidence {index}."],
            }
            for index in range(1, 9)
        ],
    }


def write_dataset(tmp_path: Path, payload: dict[str, Any]) -> tuple[Path, Path]:
    fixture = tmp_path / "evals/fixtures/invented.md"
    fixture.parent.mkdir(parents=True)
    fixture.write_text("\n".join(f"Evidence {index}." for index in range(1, 9)), encoding="utf-8")
    dataset_path = fixture.parent / "cases.json"
    dataset_path.write_text(json.dumps(payload), encoding="utf-8")
    return dataset_path, tmp_path


def test_dataset_validation_accepts_reviewable_privacy_safe_cases(tmp_path: Path) -> None:
    dataset_path, repo_root = write_dataset(tmp_path, dataset_payload())

    dataset = load_evaluation_dataset(dataset_path, repo_root=repo_root)

    assert len(dataset.cases) == 8
    assert dataset.cases[0].case_id == "case-1"
    assert dataset.fixture_path.name == "invented.md"


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda payload: payload["cases"][1].update(id="case-1"), "duplicate case ID"),
        (lambda payload: payload["cases"][0].update(question=" "), "non-empty string"),
        (lambda payload: payload["cases"][0].update(reference=""), "non-empty string"),
        (lambda payload: payload["cases"][0].update(extra="no"), "unsupported fields"),
        (
            lambda payload: payload["cases"][0].update(evidenceHints=["Absent evidence"]),
            "missing from the fixture",
        ),
        (lambda payload: payload.update(fixture="/tmp/private.md"), "absolute path"),
        (
            lambda payload: payload["cases"][0].update(reference="api_key=secret-value"),
            "appears to contain a secret",
        ),
        (
            lambda payload: payload["cases"][0].update(
                reference="Read the answer from /home/user/private.txt"
            ),
            "contains an absolute path",
        ),
    ],
)
def test_dataset_validation_rejects_unsafe_or_ambiguous_input(
    tmp_path: Path, mutate: Any, message: str
) -> None:
    payload = dataset_payload()
    mutate(payload)
    dataset_path, repo_root = write_dataset(tmp_path, payload)

    with pytest.raises(DatasetValidationError, match=message):
        load_evaluation_dataset(dataset_path, repo_root=repo_root)


def evaluation_dataset(tmp_path: Path, *, case_count: int = 2) -> EvaluationDataset:
    fixture = tmp_path / "fixture.md"
    fixture.write_text("Invented evidence.", encoding="utf-8")
    return EvaluationDataset(
        schema_version=1,
        fixture_path=fixture,
        fixture_text="Invented evidence.",
        cases=tuple(
            EvaluationCase(
                case_id=f"case-{index}",
                question=f"Question {index}?",
                reference=f"Reference {index}.",
                evidence_hints=("Invented evidence.",),
            )
            for index in range(1, case_count + 1)
        ),
    )


def citation(index: int = 1) -> Citation:
    return Citation(
        source_id=f"S{index}",
        document_id="document-1",
        document_name="fixture.md",
        page_number=None,
        chunk_id=f"chunk-{index}",
        snippet=f"Cited context {index}.",
        score=0.91,
    )


class FakeApi:
    def __init__(self, states: list[tuple[str, str | None]] | None = None) -> None:
        self.states = states or [("ready", None)]
        self.state_index = 0
        self.events: list[str] = []
        self.answer_error: Exception | None = None
        self.citations: tuple[Citation, ...] = (citation(),)

    def upload_document(self, **values: Any) -> str:
        self.events.append(f"upload:{values['upload_name']}")
        return "document-1"

    def document_state(self, document_id: str) -> tuple[str, str | None]:
        self.events.append(f"poll:{document_id}")
        state = self.states[min(self.state_index, len(self.states) - 1)]
        self.state_index += 1
        return state

    def create_conversation(self, **values: Any) -> str:
        conversation_id = (
            f"conversation-{len([e for e in self.events if e.startswith('create:')]) + 1}"
        )
        self.events.append(f"create:{conversation_id}:{values['title']}")
        return conversation_id

    def ask(self, *, conversation_id: str, question: str) -> AnswerCapture:
        self.events.append(f"ask:{conversation_id}:{question}")
        if self.answer_error is not None:
            raise self.answer_error
        return AnswerCapture(
            response=f"Answer to {question}", citations=self.citations, duration_ms=125
        )

    def delete_conversation(self, conversation_id: str) -> None:
        self.events.append(f"delete-conversation:{conversation_id}")

    def delete_document(self, document_id: str) -> None:
        self.events.append(f"delete-document:{document_id}")


class FakeEvaluator:
    def __init__(self, error: BaseException | None = None) -> None:
        self.error = error
        self.samples: list[EvaluationSample] = []

    def score(self, sample: EvaluationSample) -> MetricScores:
        self.samples.append(sample)
        if self.error is not None:
            raise self.error
        return MetricScores(faithfulness=0.75, factual_correctness=0.625)


def run_evaluation(
    tmp_path: Path,
    *,
    api: FakeApi | None = None,
    evaluator: FakeEvaluator | None = None,
    clock: Any = None,
    sleeper: Any = None,
    retain_resources: bool = False,
) -> tuple[RunResult, FakeApi, FakeEvaluator]:
    api = api or FakeApi()
    evaluator = evaluator or FakeEvaluator()
    runner = EvaluationRunner(
        api=api,
        evaluator=evaluator,
        **({"clock": clock} if clock is not None else {}),
        **({"sleeper": sleeper} if sleeper is not None else {}),
    )
    result = runner.run(
        evaluation_dataset(tmp_path),
        run_id="mra019-test",
        started_at="2026-08-28T10:00:00+00:00",
        api_url="http://localhost:8000/api",
        ollama_url="http://localhost:11434",
        answer_model="answer-a",
        embedding_model="embed-a",
        evaluator_model="judge-a",
        ingestion_timeout_seconds=5,
        poll_interval_seconds=1,
        retain_resources=retain_resources,
    )
    return result, api, evaluator


def test_runner_maps_only_returned_citations_and_cleans_owned_resources(
    tmp_path: Path,
) -> None:
    result, api, evaluator = run_evaluation(tmp_path)

    assert result.status == "completed"
    assert len(result.case_results) == 2
    assert all(case.status == "scored" for case in result.case_results)
    assert evaluator.samples[0] == EvaluationSample(
        user_input="Question 1?",
        response="Answer to Question 1?",
        reference="Reference 1.",
        retrieved_contexts=("Cited context 1.",),
    )
    assert "delete-conversation:conversation-2" in api.events
    assert "delete-conversation:conversation-1" in api.events
    assert api.events[-1] == "delete-document:document-1"


def test_polling_timeout_is_bounded_and_cleans_document(tmp_path: Path) -> None:
    api = FakeApi([("processing", None)])
    times = iter([0.0, 0.0, 5.0])

    with pytest.raises(EvaluationError, match="not ready within 5 seconds"):
        run_evaluation(
            tmp_path,
            api=api,
            clock=times.__next__,
            sleeper=lambda _: None,
        )

    assert api.events[-1] == "delete-document:document-1"


def test_answer_and_evaluator_failures_are_structured_and_cleanup_runs(
    tmp_path: Path,
) -> None:
    answer_api = FakeApi()
    answer_api.answer_error = EvaluationError("answer unavailable")
    answer_result, answer_api, _ = run_evaluation(tmp_path, api=answer_api)
    judge_result, judge_api, _ = run_evaluation(
        tmp_path, evaluator=FakeEvaluator(EvaluationError("judge unavailable"))
    )

    assert [case.status for case in answer_result.case_results] == ["error", "error"]
    assert answer_result.case_results[0].error == "answer unavailable"
    assert judge_result.case_results[0].answer == "Answer to Question 1?"
    assert judge_result.case_results[0].error == "judge unavailable"
    assert answer_api.events[-1] == "delete-document:document-1"
    assert judge_api.events[-1] == "delete-document:document-1"


def test_missing_cited_context_is_actionable_and_not_sent_to_ragas(tmp_path: Path) -> None:
    api = FakeApi()
    api.citations = ()
    evaluator = FakeEvaluator()

    result, _, evaluator = run_evaluation(tmp_path, api=api, evaluator=evaluator)

    assert result.case_results[0].error == (
        "CiteNook returned no citation snippets; Ragas faithfulness cannot be scored."
    )
    assert evaluator.samples == []


def test_keyboard_interrupt_still_cleans_owned_resources(tmp_path: Path) -> None:
    api = FakeApi()

    with pytest.raises(KeyboardInterrupt):
        run_evaluation(tmp_path, api=api, evaluator=FakeEvaluator(KeyboardInterrupt()))

    assert "delete-conversation:conversation-1" in api.events
    assert api.events[-1] == "delete-document:document-1"


def test_explicit_retain_option_preserves_diagnostic_resources(tmp_path: Path) -> None:
    result, api, _ = run_evaluation(tmp_path, retain_resources=True)

    assert result.retained_resources is True
    assert not any(event.startswith("delete-") for event in api.events)


def test_ragas_single_turn_mapping_uses_all_required_fields() -> None:
    pytest.importorskip("ragas")
    sample = EvaluationSample(
        user_input="Question?",
        response="Answer.",
        reference="Reference.",
        retrieved_contexts=("Cited one.", "Cited two."),
    )

    mapped = build_ragas_sample(sample)

    assert mapped.user_input == sample.user_input
    assert mapped.response == sample.response
    assert mapped.reference == sample.reference
    assert mapped.retrieved_contexts == list(sample.retrieved_contexts)


def test_ragas_evaluator_reuses_one_event_loop_across_cases() -> None:
    evaluator = RagasOllamaEvaluator.__new__(RagasOllamaEvaluator)
    evaluator._async_runner = __import__("asyncio").Runner()
    loop_ids: list[int] = []

    async def fake_score(_: EvaluationSample) -> MetricScores:
        import asyncio

        loop_ids.append(id(asyncio.get_running_loop()))
        return MetricScores(faithfulness=0.5, factual_correctness=0.5)

    evaluator._score = fake_score  # type: ignore[method-assign]
    sample = EvaluationSample("Question?", "Answer.", "Reference.", ("Context.",))
    try:
        evaluator.score(sample)
        evaluator.score(sample)
    finally:
        evaluator._async_runner.close()

    assert len(set(loop_ids)) == 1


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost:11434",
        "http://127.0.0.1:8000/api",
        "http://192.168.1.20:11434",
        "http://ollama:11434",
        "http://workstation.local:11434",
    ],
)
def test_local_endpoint_validation_accepts_only_explicit_local_hosts(url: str) -> None:
    assert validate_local_http_url(url, label="Test URL") == url


@pytest.mark.parametrize(
    "url",
    [
        "https://localhost:11434",
        "http://user:password@localhost:11434",
        "http://models.example.com:11434",
        "http://8.8.8.8:11434",
    ],
)
def test_local_endpoint_validation_rejects_hosted_or_credentialed_urls(url: str) -> None:
    with pytest.raises(EvaluationError, match=r"local|credentials"):
        validate_local_http_url(url, label="Test URL")


def scored_case(case_id: str) -> CaseResult:
    return CaseResult(
        case_id=case_id,
        question="Question?",
        reference="Reference.",
        answer_model="answer-a",
        embedding_model="embed-a",
        evaluator_model="judge-a",
        answer="Answer.",
        citations=(citation(),),
        faithfulness=0.5,
        factual_correctness=0.75,
        duration_ms=321,
        status="scored",
        error=None,
    )


def test_json_and_csv_artifacts_agree_on_case_coverage_and_models(tmp_path: Path) -> None:
    result = RunResult(
        run_id="mra019-test",
        started_at="2026-08-28T10:00:00+00:00",
        api_url="http://localhost:8000/api",
        ollama_url="http://localhost:11434",
        answer_model="answer-a",
        embedding_model="embed-a",
        evaluator_model="judge-a",
        case_results=(scored_case("case-1"), replace(scored_case("case-2"), faithfulness=1.0)),
        cleanup_errors=(),
        retained_resources=False,
    )

    json_path, csv_path = write_artifacts(result, tmp_path / "experiments")
    json_payload = json.loads(json_path.read_text(encoding="utf-8"))
    with csv_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert json_payload["caseCount"] == len(rows) == 2
    assert json_payload["scoredCaseCount"] == 2
    assert json_payload["aggregateScores"] == {
        "faithfulness": 0.75,
        "factualCorrectness": 0.75,
    }
    assert {row["case_id"] for row in rows} == {"case-1", "case-2"}
    assert all(row["answer_model"] == "answer-a" for row in rows)
    assert json.loads(rows[0]["citation_ids"]) == ["chunk-1"]
