# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

import copy
import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

from evaluation import deepeval_judge, judge
from evaluation.judge import METRICS, JudgeConfig, render_report, run_judge
from evaluation.judge_input import load_results
from evaluation.suite import NO_ANSWER, load_suite

ROOT = Path(__file__).resolve().parents[3]
CONFIG = JudgeConfig("local-judge:8b", "test-digest", "http://127.0.0.1:11434", 0, 0.5, 120, True)
HISTORIC_RESULTS = sorted(ROOT.glob("docs/releases/release-0.[67]-*/results/*/*/results.json"))


def payload(suite_name="baseline", schema=2):
    suite = load_suite(suite_name)
    documents = {str(index): path.name for index, path in enumerate(suite.documents)}
    cases = []
    for case in suite.cases:
        citations = [
            {
                "documentId": document_id,
                "documentName": name,
                "sourceId": f"S{index + 1}",
                "snippet": next(path for path in suite.documents if path.name == name).read_text(),
            }
            for index, (document_id, name) in enumerate(documents.items())
            if name in case.expected_sources
        ]
        row = {
            "id": case.id,
            "question": case.question,
            "expectsNoAnswer": case.no_answer,
            "answer": NO_ANSWER
            if case.no_answer
            else " ".join(case.key_facts)
            + " "
            + " ".join(f"[{citation['sourceId']}]" for citation in citations),
            "citations": citations,
            "checks": {"keyFacts": None if case.no_answer else True},
            "passed": True,
            "error": None,
            "responseDurationMs": 100,
        }
        if schema == 1:
            del row["citations"]
        cases.append(row)
    result = {
        "schemaVersion": schema,
        "suiteId": suite.id,
        "suiteSha256": suite.sha256,
        "startedAt": "2026-10-17T08:00:00+00:00",
        "finishedAt": "2026-10-17T08:01:00+00:00",
        "ragBackend": "native",
        "chatModel": "fixture-model",
        "embeddingModel": "fixture-embedding",
        "ragTopK": 5,
        "documents": documents,
        "status": "passed",
        "error": None,
        "cleanupErrors": [],
        "cases": cases,
    }
    if schema == 2:
        result.update(suiteName=suite_name, plannedCases=len(cases))
    return result


def save(tmp_path, data):
    path = tmp_path / "results.json"
    path.write_text(json.dumps(data))
    return load_results(path)


class FakeJudge:
    def __init__(self):
        self.calls = []

    def measure(self, name, question, answer, snippets):
        self.calls.append((name, question, answer, snippets))
        return {
            "score": 0.8 if name == METRICS[0] else 0.4,
            "judgeReason": "Mocked test verdict only.",
            "usage": {"tokens": 10},
        }


def evaluate(tmp_path, data, fake=None):
    fake = fake or FakeJudge()
    saved = save(tmp_path, data)
    before = saved.path.read_bytes()
    result = run_judge(saved, CONFIG, judge_factory=lambda config: fake)
    assert saved.path.read_bytes() == before
    return result, fake


@pytest.mark.parametrize(
    "suite,schema,supported", [("baseline", 1, 9), ("baseline", 2, 9), ("safety", 2, 6)]
)
def test_scores_keep_judge_and_fixture_verdicts_separate(tmp_path, suite, schema, supported):
    data = payload(suite, schema)
    data["status"] = "failed"
    data["cases"][0]["passed"] = False
    data["cases"][0]["checks"]["keyFacts"] = False
    result, fake = evaluate(tmp_path, data)
    assert result["status"] == "completed"
    assert result["input"]["status"] == "failed"
    assert result["cases"][0]["fixturePassed"] is False
    assert result["cases"][0]["metrics"][METRICS[0]]["judgePassed"] is True
    relevancy = result["aggregates"][METRICS[0]]
    faithfulness = result["aggregates"][METRICS[1]]
    assert relevancy["counts"] == {
        "scored": supported,
        "skipped": len(data["cases"]) - supported,
        "error": 0,
    }
    assert relevancy["meanScore"] == pytest.approx(0.8)
    assert faithfulness["counts"]["scored"] == (0 if schema == 1 else supported)
    assert faithfulness["meanScore"] == (None if schema == 1 else pytest.approx(0.4))
    assert faithfulness["judgePassed"] == 0
    assert len(fake.calls) == supported * (1 if schema == 1 else 2)
    assert result["judge"]["model_version"] == "test-digest"
    for row in result["cases"]:
        for metric in row["metrics"].values():
            assert metric["startedAt"] and metric["finishedAt"]
            if metric["status"] == "scored":
                assert metric["usage"] == {"tokens": 10}
    report = render_report(result)
    assert "cited-excerpt faithfulness" in report
    assert "Original deterministic fixture status: failed" in report
    assert "N/A" in report


@pytest.mark.parametrize("path", HISTORIC_RESULTS, ids=lambda path: str(path.relative_to(ROOT)))
def test_actual_saved_schemas_are_supported_without_changing_historic_files(path):
    before = path.read_bytes()
    result = run_judge(load_results(path), CONFIG, judge_factory=lambda config: FakeJudge())
    assert result["status"] == "completed"
    assert result["aggregates"][METRICS[0]]["counts"]["error"] == 0
    assert result["aggregates"][METRICS[1]]["counts"]["error"] == 0
    assert path.read_bytes() == before


@pytest.mark.parametrize(
    "field,value",
    [
        ("schemaVersion", 3),
        ("schemaVersion", True),
        ("suiteSha256", "bad"),
        ("suiteId", "private-chats"),
        ("suiteName", []),
        ("plannedCases", 99),
        ("documents", {"1": "personal.md"}),
        ("status", "running"),
        ("cases", "bad"),
        ("ragTopK", False),
        ("cleanupErrors", None),
        ("startedAt", "yesterday"),
    ],
)
def test_invalid_run_schema_is_rejected_before_judge(tmp_path, field, value):
    data = payload()
    data[field] = value
    with pytest.raises(ValueError):
        save(tmp_path, data)


def test_unknown_duplicate_and_malformed_cases_are_rejected(tmp_path):
    for row in (None, {"id": "personal"}, payload()["cases"][0]):
        data = payload()
        data["cases"].append(row)
        with pytest.raises(ValueError):
            save(tmp_path, data)
    path = tmp_path / "results.json"
    for content in ("{", "[]", '{"schemaVersion": NaN}'):
        path.write_text(content)
        with pytest.raises(ValueError):
            load_results(path)


@pytest.mark.parametrize(
    "field,value",
    [
        ("question", "A personal question"),
        ("expectsNoAnswer", True),
        ("answer", None),
        ("error", "API timeout"),
        ("checks", None),
        ("checks", {"keyFacts": "true"}),
        ("responseDurationMs", True),
        ("passed", None),
        ("citations", "bad"),
        ("citations", [None]),
    ],
)
def test_malformed_case_is_an_error_and_never_submitted(tmp_path, field, value):
    data = payload()
    data["cases"][0][field] = value
    result, fake = evaluate(tmp_path, data)
    assert result["status"] == "error"
    assert all(
        metric["status"] == "error" and metric["errorReason"]
        for metric in result["cases"][0]["metrics"].values()
    )
    assert not any(call[1] == data["cases"][0]["question"] for call in fake.calls)


@pytest.mark.parametrize(
    "field,value",
    [
        ("documentName", "private.md"),
        ("documentId", "unowned"),
        ("sourceId", "S0"),
        ("snippet", "Personal uploaded text"),
        ("snippet", 4),
    ],
)
def test_non_fixture_or_malformed_citations_are_never_sent(tmp_path, field, value):
    data = payload()
    data["cases"][0]["citations"][0][field] = value
    result, fake = evaluate(tmp_path, data)
    assert all(metric["status"] == "error" for metric in result["cases"][0]["metrics"].values())
    assert not any(call[1] == data["cases"][0]["question"] for call in fake.calls)


@pytest.mark.parametrize("citations", [None, [], "missing", "empty", "partial", "markers"])
def test_citation_gaps_skip_faithfulness_but_allow_relevancy(tmp_path, citations):
    data = payload()
    row = data["cases"][0]
    if citations == "missing":
        del row["citations"]
    elif citations == "empty":
        row["citations"][0]["snippet"] = "  "
    elif citations == "partial":
        second = copy.deepcopy(row["citations"][0])
        second.update(sourceId="S99", snippet=None)
        row["citations"].append(second)
        row["answer"] += " [S99]"
    elif citations == "markers":
        row["answer"] += " [S99]"
    else:
        row["citations"] = citations
    result, _ = evaluate(tmp_path, data)
    metrics = result["cases"][0]["metrics"]
    assert metrics[METRICS[0]]["status"] == "scored"
    assert metrics[METRICS[1]]["status"] == "skipped"
    assert metrics[METRICS[1]]["skipReason"]
    assert metrics[METRICS[1]]["score"] is None


@pytest.mark.parametrize("answer", ["", "  ", NO_ANSWER])
def test_empty_and_actual_no_answer_are_skipped(tmp_path, answer):
    data = payload()
    data["cases"][0].update(answer=answer, citations=[])
    result, _ = evaluate(tmp_path, data)
    assert all(metric["status"] == "skipped" for metric in result["cases"][0]["metrics"].values())


@pytest.mark.parametrize("change", ["error", "cleanup", "missing", "unfinished"])
def test_incomplete_or_errored_run_makes_no_judge_calls(tmp_path, change):
    data = payload()
    if change == "error":
        data.update(status="error", error="Interrupted")
    elif change == "cleanup":
        data["cleanupErrors"] = [{"error": "Delete failed"}]
    elif change == "missing":
        data["cases"].pop()
    else:
        del data["finishedAt"]
    result = run_judge(
        save(tmp_path, data),
        CONFIG,
        judge_factory=lambda config: pytest.fail("Judge must not start"),
    )
    assert result["status"] == "skipped"
    for aggregate in result["aggregates"].values():
        assert aggregate["meanScore"] is None
        assert aggregate["counts"] == {"scored": 0, "skipped": 12, "error": 0}


@pytest.mark.parametrize("failure", ["setup", "call", "nan", "range", "bool", "reason"])
def test_judge_errors_never_count_as_zero_or_success(tmp_path, failure):
    class BrokenJudge(FakeJudge):
        def measure(self, *args):
            if failure == "call":
                raise RuntimeError("Judge timed out")
            result = super().measure(*args)
            if failure in {"nan", "range", "bool"}:
                result["score"] = {"nan": float("nan"), "range": 2, "bool": True}[failure]
            else:
                result["judgeReason"] = None
            return result

    def factory(config):
        if failure == "setup":
            raise ImportError("Optional judge is missing")
        return BrokenJudge()

    result = run_judge(save(tmp_path, payload()), CONFIG, judge_factory=factory)
    assert result["status"] == "error"
    for aggregate in result["aggregates"].values():
        assert aggregate["meanScore"] is None
        assert aggregate["judgePassed"] == 0
        assert aggregate["counts"]["error"] == 9
    assert result["cases"][0]["metrics"][METRICS[0]]["errorReason"]


@pytest.mark.parametrize(
    "changes",
    [
        {"synthetic_data": False},
        {"model": ""},
        {"model_version": ""},
        {"base_url": "https://remote.test"},
        {"base_url": "http://user:pass@localhost:11434"},
        {"base_url": "http://localhost:11434/path"},
        {"base_url": "http://localhost:0"},
        {"model": "large-model:cloud"},
        {"model": "large-model-cloud"},
        {"temperature": float("nan")},
        {"threshold": 1.1},
        {"request_timeout": 0},
    ],
)
def test_explicit_config_rejects_unapproved_or_invalid_settings(changes):
    with pytest.raises(ValueError):
        replace(CONFIG, **changes)


def test_cli_writes_separate_reports_and_rejects_overwrite(tmp_path, monkeypatch):
    saved = save(tmp_path, payload())
    original = saved.path.read_bytes()
    monkeypatch.setattr(judge, "create_judge", lambda config: FakeJudge())
    args = [
        "--input",
        str(saved.path),
        "--output-dir",
        str(tmp_path / "judge"),
        "--model",
        CONFIG.model,
        "--model-version",
        CONFIG.model_version,
        "--base-url",
        CONFIG.base_url,
        "--temperature",
        "0",
        "--threshold",
        "0.5",
        "--request-timeout",
        "120",
        "--synthetic-data",
    ]
    assert judge.main(args) == 0
    output = (tmp_path / "judge/judge-scores.json").read_bytes()
    assert json.loads(output)["input"]["sha256"] == saved.sha256
    assert (tmp_path / "judge/judge-report.md").exists()
    assert judge.main(args) == 2
    assert judge.main(args[:-1]) == 2
    assert saved.path.read_bytes() == original
    assert (tmp_path / "judge/judge-scores.json").read_bytes() == output


def test_help_and_import_need_no_optional_deepeval_or_network():
    script = """
import builtins, socket, sys
original = builtins.__import__
def guarded(name, *args, **kwargs):
    if name == 'deepeval' or name.startswith('deepeval.'):
        raise ImportError('DeepEval deliberately unavailable')
    return original(name, *args, **kwargs)
builtins.__import__ = guarded
def deny(*args, **kwargs):
    raise AssertionError('Network access is forbidden')
socket.socket.connect = deny
from evaluation.judge import main
assert 'deepeval' not in sys.modules
main(['--help'])
"""
    result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "--synthetic-data" in result.stdout


def test_deepeval_adapter_uses_explicit_model_and_only_cited_context(monkeypatch):
    captured = []

    class Metric:
        def __init__(self, **kwargs):
            captured.append(kwargs)
            self.score, self.reason, self.error, self.evaluation_cost = 0.8, "Test only", None, None

        def measure(self, case, **kwargs):
            captured.append(vars(case))

    for name, attributes in {
        "deepeval.metrics": {"AnswerRelevancyMetric": Metric, "FaithfulnessMetric": Metric},
        "deepeval.models": {"OllamaModel": lambda **kwargs: captured.append(kwargs) or object()},
        "deepeval.test_case": {"LLMTestCase": SimpleNamespace},
    }.items():
        module = ModuleType(name)
        vars(module).update(attributes)
        monkeypatch.setitem(sys.modules, name, module)
    monkeypatch.delitem(sys.modules, "deepeval", raising=False)
    adapter = deepeval_judge.create_judge(CONFIG)
    assert captured[0]["base_url"] == CONFIG.base_url
    assert captured[0]["trust_env"] is False
    assert captured[0]["follow_redirects"] is False
    assert captured[0]["timeout"] == 120
    for name in METRICS:
        measured = adapter.measure(name, "Fixture question", "Fixture answer", ["Saved excerpt"])
        assert measured["score"] == 0.8
        assert captured[-2]["eval_mode"] == "llm"
        assert captured[-2]["async_mode"] is False
        assert captured[-1]["retrieval_context"] == (
            ["Saved excerpt"] if name == METRICS[1] else None
        )
    for key, value in {
        "DEEPEVAL_TELEMETRY_OPT_OUT": "1",
        "DEEPEVAL_DISABLE_DOTENV": "1",
        "DEEPEVAL_UPDATE_WARNING_OPT_IN": "0",
    }.items():
        import os

        assert os.environ[key] == value
