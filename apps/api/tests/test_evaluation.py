# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

import json
from dataclasses import replace
from uuid import UUID

import httpx
import pytest

from evaluation import runner
from evaluation.runner import (
    EvaluationError,
    RunConfig,
    check_backend,
    check_models,
    run_evaluation,
)
from evaluation.suite import NO_ANSWER, load_suite


def test_fixture_suite_defines_three_documents_and_twelve_cases() -> None:
    suite = load_suite()

    assert suite.id == "citenook-small-rag-v1"
    assert len(suite.documents) == 3
    assert len(suite.cases) == 12
    assert suite.sha256 == "3896a8fd81ef0ee754d769b60b2c47742bfb0ae30ce15fef61d2f7b0d092ed5a"
    assert load_suite("baseline") == suite
    assert sum(case.no_answer for case in suite.cases) == 3
    documents = {path.name: path.read_text(encoding="utf-8") for path in suite.documents}
    for case in suite.cases:
        for fact in case.key_facts:
            assert any(fact in documents[name] for name in case.expected_sources)


@pytest.mark.parametrize("backend", ["native", "llamaindex"])
def test_backend_preflight_checks_the_health_contract(backend) -> None:
    def respond(request):
        assert request.method == "GET"
        assert request.url.path == "/api/health"
        return httpx.Response(
            200,
            json={
                "status": "ok",
                "appId": "cite-nook-ai",
                "ragBackend": backend,
            },
        )

    with httpx.Client(
        base_url="http://fixture.test/api/", transport=httpx.MockTransport(respond)
    ) as c:
        check_backend(c, backend)
        other = "llamaindex" if backend == "native" else "native"
        with pytest.raises(EvaluationError, match="Expected ragBackend"):
            check_backend(c, other)


@pytest.mark.parametrize("missing", ["chatModels", "embeddingModels", "ollama"])
def test_model_preflight_rejects_unavailable_models(missing) -> None:
    catalog = {
        "chatModels": [{"name": "chat", "installed": missing != "chatModels"}],
        "embeddingModels": [{"name": "embed", "installed": missing != "embeddingModels"}],
        "ollamaAvailable": missing != "ollama",
    }
    with (
        httpx.Client(
            base_url="http://fixture.test/api/",
            transport=httpx.MockTransport(lambda request: httpx.Response(200, json=catalog)),
        ) as client,
        pytest.raises(EvaluationError, match=r"unavailable|not configured and installed"),
    ):
        check_models(client, "chat", "embed")


class FixtureApi:
    def __init__(self, backend="native", suite="baseline") -> None:
        self.backend = backend
        self.suite_name = suite
        self.suite = load_suite(suite)
        self.requests = []
        self.documents = {}
        self.conversations = set()
        self.uploads = []
        self.questions = []
        self.statuses = ["ready"]
        self.polls = 0
        self.override = lambda request: None
        self.answer_patch = {}

    def __call__(self, request):
        self.requests.append(request)
        response = self.override(request)
        if response is not None:
            return response
        path = request.url.path
        if request.method == "GET" and path == "/api/health":
            return httpx.Response(
                200,
                json={
                    "status": "ok",
                    "appId": "cite-nook-ai",
                    "ragBackend": self.backend,
                },
            )
        if request.method == "GET" and path == "/api/models":
            return httpx.Response(
                200,
                json={
                    "ollamaAvailable": True,
                    "chatModels": [{"name": "chat", "installed": True}],
                    "embeddingModels": [{"name": "embed", "installed": True}],
                },
            )
        if request.method == "POST" and path == "/api/documents":
            document = self.suite.documents[len(self.uploads)]
            assert f'filename="{document.name}"'.encode() in request.content
            assert document.read_bytes() in request.content
            assert b'name="embedding_model"\r\n\r\nembed' in request.content
            self.uploads.append(document.name)
            row = {
                "id": str(UUID(int=100 + len(self.uploads))),
                "fileName": document.name,
                "status": "queued",
                "embeddingModel": "embed",
                "isActive": True,
                "errorMessage": None,
            }
            self.documents[row["id"]] = row
            return httpx.Response(201, json=row)
        if request.method == "GET" and path == "/api/documents":
            if self.documents:
                state = self.statuses[min(self.polls, len(self.statuses) - 1)]
                self.polls += 1
                for row in self.documents.values():
                    row["status"] = state
                    if state == "failed":
                        row["errorMessage"] = "Fixture indexing error."
            return httpx.Response(200, json=list(self.documents.values()))
        if request.method == "POST" and path == "/api/conversations":
            assert json.loads(request.content) == {"chatModel": "chat", "embeddingModel": "embed"}
            conversation_id = str(UUID(int=1000 + len(self.conversations)))
            self.conversations.add(conversation_id)
            return httpx.Response(
                201,
                json={
                    "id": conversation_id,
                    "chatModel": "chat",
                    "embeddingModel": "embed",
                },
            )
        if request.method == "POST" and path.endswith("/messages"):
            conversation_id = path.split("/")[3]
            assert conversation_id in self.conversations
            assert all(row["status"] == "ready" for row in self.documents.values())
            question = json.loads(request.content)["question"]
            self.questions.append(question)
            case = next(case for case in self.suite.cases if case.question == question)
            message = {
                "role": "assistant",
                "conversationId": conversation_id,
                "chatModel": "chat",
                "content": NO_ANSWER if case.no_answer else " ".join(case.key_facts) + "\n[S1]",
                "citations": [
                    {
                        "sourceId": f"S{index}",
                        "documentId": row["id"],
                        "documentName": row["fileName"],
                    }
                    for index, row in enumerate(self.documents.values(), start=1)
                    if row["fileName"] in case.expected_sources
                ],
                "responseDurationMs": 42,
            }
            if message["citations"]:
                message["content"] = " ".join(case.key_facts) + "\n" + " ".join(
                    f"[{citation['sourceId']}]" for citation in message["citations"]
                )
            message.update(self.answer_patch)
            return httpx.Response(200, json={"assistantMessage": message})
        if request.method == "DELETE" and path.startswith("/api/documents/"):
            del self.documents[path.split("/")[-1]]
            return httpx.Response(204)
        if request.method == "DELETE" and path.startswith("/api/conversations/"):
            self.conversations.remove(path.split("/")[-1])
            return httpx.Response(204)
        raise AssertionError(f"Unexpected API request: {request.method} {path}")


class FakeClock:
    def __init__(self) -> None:
        self.now = 0
        self.sleeps = []

    def clock(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds


def evaluate(api, config=None, clock=None):
    timer = clock or FakeClock()
    with httpx.Client(
        base_url="http://fixture.test/api/",
        transport=httpx.MockTransport(api),
    ) as client:
        return run_evaluation(
            client,
            config or RunConfig(api.backend, "chat", "embed", 5, suite=api.suite_name),
            clock=timer.clock,
            sleep=timer.sleep,
        )


@pytest.mark.parametrize("backend", ["native", "llamaindex"])
@pytest.mark.parametrize("suite", ["baseline", "safety"])
def test_complete_http_run_uses_only_fixtures_and_fresh_conversations(backend, suite) -> None:
    api = FixtureApi(backend, suite)
    result = evaluate(api)

    assert result["status"] == "passed"
    assert result["ragBackend"] == backend
    assert api.uploads == [path.name for path in api.suite.documents]
    assert api.questions == [case.question for case in api.suite.cases]
    assert result["suiteName"] == suite
    assert result["suiteId"] == api.suite.id
    assert result["suiteSha256"] == api.suite.sha256
    assert result["plannedCases"] == len(api.suite.cases)
    assert len(result["conversationIds"]) == len(api.suite.cases)
    assert len(set(result["conversationIds"])) == len(api.suite.cases)
    assert all(case["responseDurationMs"] == 42 for case in result["cases"])
    for case, outcome in zip(api.suite.cases, result["cases"], strict=True):
        assert outcome["citedDocumentNames"] == list(case.expected_sources)
        assert outcome["factMatches"] == dict.fromkeys(case.key_facts, True)
        assert outcome["attackLocation"] == case.attack_location
        assert outcome["forbiddenMatches"] == dict.fromkeys(case.forbidden_texts, False)
        assert outcome["checks"]["citationMarkers"] is True
        if case.no_answer:
            assert outcome["checks"]["noAnswer"] is True
    assert result["cleanupErrors"] == []
    assert api.documents == {}
    assert api.conversations == set()
    assert [(r.method, r.url.path) for r in api.requests[:3]] == [
        ("GET", "/api/health"),
        ("GET", "/api/models"),
        ("GET", "/api/documents"),
    ]


@pytest.mark.parametrize("suite", ["baseline", "safety"])
def test_pending_jobs_are_polled_before_any_question(suite) -> None:
    api = FixtureApi(suite=suite)
    api.statuses = ["queued", "processing", "ready"]
    clock = FakeClock()

    assert evaluate(api, clock=clock)["status"] == "passed"
    assert clock.sleeps == [1, 1]


@pytest.mark.parametrize("status", ["queued", "processing", "failed"])
@pytest.mark.parametrize("suite", ["baseline", "safety"])
def test_failed_or_stalled_indexing_cleans_up_without_asking(status, suite) -> None:
    api = FixtureApi(suite=suite)
    api.statuses = [status]
    config = RunConfig("native", "chat", "embed", 5, indexing_timeout=2, suite=suite)
    result = evaluate(api, config)

    assert result["status"] == "error"
    expected_error = "Indexing failed" if status == "failed" else "Timed out"
    assert expected_error in result["error"]
    assert api.questions == []
    assert api.documents == {}


@pytest.mark.parametrize(
    "requested,available", [("native", "llamaindex"), ("llamaindex", "native")]
)
def test_wrong_backend_aborts_before_models_uploads_or_deletes(requested, available) -> None:
    api = FixtureApi(available)
    result = evaluate(api, RunConfig(requested, "chat", "embed", 5))

    assert result["status"] == "error"
    assert "Expected ragBackend" in result["error"]
    assert len(api.requests) == 1


def test_missing_selected_model_aborts_before_uploads() -> None:
    api = FixtureApi()
    result = evaluate(api, RunConfig("native", "missing", "embed", 5))

    assert result["status"] == "error"
    assert "not configured and installed" in result["error"]
    assert api.uploads == []
    assert len(api.requests) == 2


@pytest.mark.parametrize("suite", ["baseline", "safety"])
def test_nonempty_deployment_is_rejected_without_touching_existing_records(suite) -> None:
    api = FixtureApi(suite=suite)
    foreign_id = str(UUID(int=999))
    api.documents[foreign_id] = {"id": foreign_id}
    result = evaluate(api)

    assert result["status"] == "error"
    assert "isolated deployment" in result["error"]
    assert api.uploads == []
    assert list(api.documents) == [foreign_id]
    assert all(request.method == "GET" for request in api.requests)


@pytest.mark.parametrize("suite", ["baseline", "safety"])
def test_document_appearing_during_run_is_preserved_and_stops_questions(suite) -> None:
    api = FixtureApi(suite=suite)
    foreign_id = str(UUID(int=999))

    def add_foreign(request):
        if request.method == "GET" and request.url.path == "/api/documents" and api.uploads:
            api.documents[foreign_id] = {"id": foreign_id}

    api.override = add_foreign
    result = evaluate(api)

    assert result["status"] == "error"
    assert api.questions == []
    assert list(api.documents) == [foreign_id]
    assert not any(
        request.method == "DELETE" and foreign_id in request.url.path for request in api.requests
    )


@pytest.mark.parametrize(
    "patch,check",
    [
        ({"content": "Someone else [S1]"}, "keyFacts"),
        ({"citations": []}, "expectedSources"),
    ],
)
@pytest.mark.parametrize("suite", ["baseline", "safety"])
def test_fixture_mismatch_is_recorded_and_remaining_questions_are_asked(
    patch, check, suite
) -> None:
    api = FixtureApi(suite=suite)
    api.answer_patch = patch
    result = evaluate(api)

    assert result["status"] == "failed"
    assert result["cases"][0]["checks"][check] is False
    assert len(api.questions) == len(api.suite.cases)
    assert api.documents == {}
    assert api.conversations == set()


@pytest.mark.parametrize("suite", ["baseline", "safety"])
def test_unsupported_answer_must_be_the_fixed_reply_without_citations(suite) -> None:
    api = FixtureApi(suite=suite)
    api.answer_patch = {"content": "The ticket costs 17 credits."}
    result = evaluate(api)

    assert result["cases"][-1]["checks"]["noAnswer"] is False
    assert result["cases"][-1]["answer"] == "The ticket costs 17 credits."


def test_no_answer_reply_with_a_citation_fails_the_no_answer_check() -> None:
    api = FixtureApi()
    api.answer_patch = {
        "content": NO_ANSWER,
        "citations": [{"documentId": str(UUID(int=101)), "documentName": "amber-observatory.md"}],
    }

    result = evaluate(api)

    assert result["status"] == "failed"
    assert result["cases"][-1]["checks"]["noAnswer"] is False


def test_unknown_citation_id_is_rejected_even_with_a_fixture_name() -> None:
    api = FixtureApi()
    api.answer_patch = {
        "citations": [
            {
                "documentId": str(UUID(int=999)),
                "documentName": "amber-observatory.md",
            }
        ]
    }
    result = evaluate(api)

    assert result["status"] == "error"
    assert "outside this run" in result["error"]
    assert api.documents == {}
    assert api.conversations == set()


@pytest.mark.parametrize("duration", [None, -1, "42", True])
def test_missing_or_invalid_api_timing_is_an_error(duration) -> None:
    api = FixtureApi()
    api.answer_patch = {"responseDurationMs": duration}
    result = evaluate(api)

    assert result["status"] == "error"
    assert "responseDurationMs" in result["error"]
    assert api.documents == {}
    assert api.conversations == set()


@pytest.mark.parametrize("stage", ["models", "upload", "poll", "create", "answer"])
@pytest.mark.parametrize("suite", ["baseline", "safety"])
def test_api_errors_clean_up_every_known_resource(stage, suite) -> None:
    api = FixtureApi(suite=suite)

    def fail(request):
        path = request.url.path
        if (
            (stage == "models" and path == "/api/models")
            or (
                stage == "upload"
                and request.method == "POST"
                and path == "/api/documents"
                and len(api.uploads) == 1
            )
            or (
                stage == "poll"
                and request.method == "GET"
                and path == "/api/documents"
                and api.uploads
            )
            or (stage == "create" and request.method == "POST" and path == "/api/conversations")
            or (stage == "answer" and path.endswith("/messages"))
        ):
            return httpx.Response(503, json={"detail": "Service failed."})

    api.override = fail
    result = evaluate(api)

    assert result["status"] == "error"
    assert "503" in result["error"]
    assert api.documents == {}
    assert api.conversations == set()
    assert len(result["documents"]) == (0 if stage == "models" else 1 if stage == "upload" else 3)


@pytest.mark.parametrize("failure", ["timeout", "interrupt", "invalid-json", "missing-field"])
@pytest.mark.parametrize("suite", ["baseline", "safety"])
def test_answer_failures_also_clean_up(failure, suite) -> None:
    api = FixtureApi(suite=suite)

    def fail(request):
        if not request.url.path.endswith("/messages"):
            return None
        if failure == "timeout":
            raise httpx.ReadTimeout("stalled", request=request)
        if failure == "interrupt":
            raise KeyboardInterrupt
        if failure == "invalid-json":
            return httpx.Response(200, text="invalid")
        return httpx.Response(200, json={})

    api.override = fail
    result = evaluate(api)

    assert result["status"] == "error"
    assert result["cases"][0]["error"]
    assert api.documents == {}
    assert api.conversations == set()


@pytest.mark.parametrize("suite", ["baseline", "safety"])
def test_cleanup_failure_is_reported_and_other_deletes_continue(suite) -> None:
    api = FixtureApi(suite=suite)
    failed_id = str(UUID(int=102))
    api.override = lambda request: (
        httpx.Response(500)
        if request.method == "DELETE" and failed_id in request.url.path
        else None
    )
    result = evaluate(api)

    assert result["status"] == "error"
    assert result["cleanupErrors"] == [
        {
            "resource": "documents",
            "id": failed_id,
            "error": "DELETE returned HTTP 500.",
        }
    ]
    assert list(api.documents) == [failed_id]
    assert api.conversations == set()


def test_already_deleted_owned_resource_is_safe_during_cleanup() -> None:
    api = FixtureApi()

    def already_deleted(request):
        if request.method == "DELETE" and request.url.path.startswith("/api/documents/"):
            del api.documents[request.url.path.split("/")[-1]]
            return httpx.Response(404)

    api.override = already_deleted
    assert evaluate(api)["cleanupErrors"] == []
    assert api.documents == {}


@pytest.mark.parametrize("outcome,exit_code", [("passed", 0), ("failed", 1), ("error", 2)])
@pytest.mark.parametrize(
    "suite,planned,supported,unsupported", [("baseline", 12, 9, 3), ("safety", 8, 6, 2)]
)
def test_cli_writes_json_and_report_with_distinct_exit_codes(
    tmp_path, monkeypatch, outcome, exit_code, suite, planned, supported, unsupported
):
    api = FixtureApi(suite=suite)
    if outcome == "failed":
        api.answer_patch = {"content": "Wrong fact."}
    if outcome == "error":
        api.backend = "llamaindex"
    real_client = httpx.Client
    monkeypatch.setattr(
        runner.httpx,
        "Client",
        lambda **kwargs: real_client(
            **kwargs,
            transport=httpx.MockTransport(api),
        ),
    )
    output = tmp_path / "run"

    assert (
        runner.main(
            [
                *(["--suite", suite] if suite == "safety" else []),
                "--base-url",
                "http://fixture.test",
                "--backend",
                "native",
                "--chat-model",
                "chat",
                "--embedding-model",
                "embed",
                "--rag-top-k",
                "5",
                "--output-dir",
                str(output),
            ]
        )
        == exit_code
    )
    result = json.loads((output / "results.json").read_text())
    report = (output / "report.md").read_text()
    assert result["status"] == outcome
    assert result["suiteSha256"] == api.suite.sha256
    assert result["ragTopK"] == 5
    assert "not retrieval recall, factual accuracy" in report
    assert "not API-verified" in report
    assert f"{planned} planned" in report
    if outcome == "passed":
        assert f"expectedSources: {planned}/{planned} checked" in report
        assert f"keyFacts: {supported}/{supported} checked" in report
        assert f"noAnswer: {unsupported}/{unsupported} checked" in report
        if suite == "safety":
            assert "forbiddenTextAbsent: 8/8 checked" in report
    assert api.documents == {}


def test_cli_does_not_overwrite_previous_results(tmp_path) -> None:
    marker = tmp_path / "results.json"
    marker.write_text("previous result")

    assert (
        runner.main(
            [
                "--backend",
                "native",
                "--chat-model",
                "chat",
                "--embedding-model",
                "embed",
                "--rag-top-k",
                "5",
                "--output-dir",
                str(tmp_path),
            ]
        )
        == 2
    )
    assert marker.read_text() == "previous result"


def test_cli_rejects_an_invalid_base_url(tmp_path) -> None:
    assert (
        runner.main(
            [
                "--base-url",
                "http://[",
                "--backend",
                "native",
                "--chat-model",
                "chat",
                "--embedding-model",
                "embed",
                "--rag-top-k",
                "5",
                "--output-dir",
                str(tmp_path / "run"),
            ]
        )
        == 2
    )


@pytest.mark.parametrize(
    "argument,value",
    [
        ("--rag-top-k", "0"),
        ("--indexing-timeout", "-1"),
        ("--poll-interval", "nan"),
        ("--request-timeout", "inf"),
        ("--suite", "unknown"),
    ],
)
def test_cli_rejects_unbounded_or_nonpositive_settings(tmp_path, argument, value) -> None:
    with pytest.raises(SystemExit) as raised:
        runner.main(
            [
                "--backend",
                "native",
                "--chat-model",
                "chat",
                "--embedding-model",
                "embed",
                "--rag-top-k",
                "5",
                "--output-dir",
                str(tmp_path / "run"),
                argument,
                value,
            ]
        )
    assert raised.value.code == 2
    assert not (tmp_path / "run").exists()


def test_fact_check_uses_whole_terms_and_ignores_case() -> None:
    suite = load_suite()
    case = replace(suite.cases[0], key_facts=("47",))
    owned = {"doc": "amber-observatory.md"}
    message = {
        "content": "147",
        "responseDurationMs": 1,
        "citations": [{"documentId": "doc", "documentName": "amber-observatory.md"}],
    }

    assert runner.check_answer(case, message, owned)["checks"]["keyFacts"] is False
    message["content"] = "The lens is 47 centimeters."
    assert runner.check_answer(case, message, owned)["checks"]["keyFacts"] is True
    message["content"] = "MIRA VALE"
    assert runner.check_answer(suite.cases[0], message, owned)["checks"]["keyFacts"] is True


def test_no_answer_fixture_matches_the_public_answer_rule() -> None:
    from app.application.answers import INSUFFICIENT_ANSWER

    assert NO_ANSWER == INSUFFICIENT_ANSWER


def test_safety_suite_is_separate_and_covers_source_and_question_attacks() -> None:
    baseline = load_suite()
    safety = load_suite("safety")

    assert safety.id == "citenook-rag-safety-v1"
    assert len(safety.cases) == 8
    assert sum(case.attack_location == "source" for case in safety.cases) == 4
    assert sum(case.attack_location == "question" for case in safety.cases) == 4
    assert sum(case.no_answer for case in safety.cases) == 2
    assert set(safety.documents).isdisjoint(baseline.documents)
    documents = {path.name: path.read_text() for path in safety.documents}
    for case in safety.cases:
        assert case.forbidden_texts
        for fact in case.key_facts:
            assert any(fact in documents[name] for name in case.expected_sources)
    for marker in safety.cases[0].forbidden_texts:
        assert any(marker in text for text in documents.values()) or any(
            marker in case.question for case in safety.cases
        )


@pytest.mark.parametrize("marker", load_suite("safety").cases[0].forbidden_texts)
def test_injection_marker_fails_even_with_correct_facts_and_citations(marker) -> None:
    api = FixtureApi(suite="safety")
    api.answer_patch = {"content": f"Elin Brook [S1] prefix{marker.lower()}suffix"}

    result = evaluate(api)
    case = result["cases"][0]

    assert result["status"] == "failed"
    assert case["checks"]["expectedSources"] is True
    assert case["checks"]["keyFacts"] is True
    assert case["checks"]["citationMarkers"] is True
    assert case["checks"]["forbiddenTextAbsent"] is False
    assert case["forbiddenMatches"][marker] is True
    assert case["answer"] == api.answer_patch["content"]
    assert len(api.questions) == 8
    assert "forbiddenTextAbsent" in runner.render_report(result)
    assert api.documents == {}
    assert api.conversations == set()


@pytest.mark.parametrize(
    "content,source_ids",
    [
        ("Elin Brook [S999]", ["S1"]),
        ("Elin Brook [S0]", ["S1"]),
        ("Elin Brook [S1] [Sx]", ["S1"]),
        ("Elin Brook [S1] [s999]", ["S1"]),
        ("Elin Brook", ["S1"]),
        ("Elin Brook [S1]", ["S2"]),
        ("Elin Brook [S1]", ["S1", "S1"]),
        ("Elin Brook [S1]", [""]),
    ],
)
def test_invalid_citation_markers_fail_and_the_safety_run_continues(content, source_ids) -> None:
    api = FixtureApi(suite="safety")
    api.answer_patch = {
        "content": content,
        "citations": [
            {
                "sourceId": source_id,
                "documentId": str(UUID(int=101)),
                "documentName": "juniper-clock-house.md",
            }
            for source_id in source_ids
        ],
    }

    result = evaluate(api)

    assert result["status"] == "failed"
    assert result["cases"][0]["checks"]["expectedSources"] is True
    assert result["cases"][0]["checks"]["keyFacts"] is True
    assert result["cases"][0]["checks"]["citationMarkers"] is False
    assert len(api.questions) == 8
    assert api.documents == {}
    assert api.conversations == set()


def test_unknown_suite_cannot_be_used_as_a_fixture_path() -> None:
    with pytest.raises(ValueError, match="Unknown fixture suite"):
        load_suite("../documents")
    with pytest.raises(ValueError, match="Unknown fixture suite"):
        RunConfig("native", "chat", "embed", 5, suite="unknown")
