# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"
NO_ANSWER = "The provided sources are insufficient to answer this question."


@dataclass(frozen=True)
class Case:
    id: str
    question: str
    expected_sources: tuple[str, ...]
    key_facts: tuple[str, ...]
    no_answer: bool


@dataclass(frozen=True)
class Suite:
    id: str
    sha256: str
    documents: tuple[Path, ...]
    cases: tuple[Case, ...]


def load_suite() -> Suite:
    raw = (FIXTURES / "cases.json").read_bytes()
    payload = json.loads(raw)
    documents = tuple(sorted((FIXTURES / "documents").glob("*.md")))
    cases = tuple(
        Case(
            id=item["id"],
            question=item["question"],
            expected_sources=tuple(item["expectedSources"]),
            key_facts=tuple(item["keyFacts"]),
            no_answer=item["noAnswer"],
        )
        for item in payload["cases"]
    )
    names = {path.name for path in documents}
    if len(documents) != 3 or len(cases) != 12 or len({case.id for case in cases}) != 12:
        raise ValueError("The fixture suite must contain three documents and twelve unique cases.")
    for case in cases:
        if not case.question.strip() or not set(case.expected_sources) <= names:
            raise ValueError(f"Invalid fixture question or source: {case.id}.")
        if case.no_answer:
            if case.expected_sources or case.key_facts:
                raise ValueError(f"No-answer case must have no sources or key facts: {case.id}.")
        elif not case.expected_sources or not case.key_facts:
            raise ValueError(f"Supported case must name sources and key facts: {case.id}.")
    digest = sha256(raw)
    for path in documents:
        digest.update(path.name.encode("utf-8") + b"\0" + path.read_bytes() + b"\0")
    return Suite(payload["id"], digest.hexdigest(), documents, cases)
