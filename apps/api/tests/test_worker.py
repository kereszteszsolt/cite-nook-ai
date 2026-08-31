# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from types import SimpleNamespace

from app import worker


class RetryStopEvent:
    def __init__(self) -> None:
        self.checks = 0
        self.waits: list[float] = []

    def is_set(self) -> bool:
        self.checks += 1
        return self.checks > 1

    def wait(self, seconds: float) -> None:
        self.waits.append(seconds)


def test_worker_uses_the_shared_composition_root(monkeypatch) -> None:
    ingestion_service = object()
    build_calls = 0

    def build_application():
        nonlocal build_calls
        build_calls += 1
        return SimpleNamespace(
            ingestion_service=ingestion_service,
            settings=SimpleNamespace(rag_backend="native"),
        )

    monkeypatch.setattr(worker, "build_application", build_application)
    database_calls: list[str] = []
    monkeypatch.setattr(worker, "init_database", database_calls.append)
    monkeypatch.setattr(worker.signal, "signal", lambda *_: None)
    monkeypatch.setattr(
        worker,
        "stop_event",
        SimpleNamespace(is_set=lambda: True),
    )

    worker.main()

    assert build_calls == 1
    assert database_calls == ["native"]


def test_worker_retries_after_a_loop_error(monkeypatch) -> None:
    retry_event = RetryStopEvent()

    monkeypatch.setattr(
        worker,
        "build_application",
        lambda: SimpleNamespace(
            ingestion_service=object(),
            settings=SimpleNamespace(rag_backend="native"),
        ),
    )
    monkeypatch.setattr(worker, "init_database", lambda _: None)
    monkeypatch.setattr(worker.signal, "signal", lambda *_: None)
    monkeypatch.setattr(worker, "stop_event", retry_event)
    monkeypatch.setattr(
        worker,
        "SessionLocal",
        lambda: (_ for _ in ()).throw(RuntimeError("database unavailable")),
    )

    worker.main()

    assert retry_event.waits == [worker.WORKER_POLL_SECONDS]
