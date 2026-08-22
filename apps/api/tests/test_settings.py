# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from app.settings import get_settings


def test_ollama_host_can_point_to_an_external_instance(monkeypatch) -> None:
    monkeypatch.setenv("OLLAMA_HOST", "http://ollama.example.test:11434")
    get_settings.cache_clear()

    assert get_settings().ollama_host == "http://ollama.example.test:11434"

    get_settings.cache_clear()
