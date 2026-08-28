# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

MIN_CASES = 8
MAX_CASES = 10
CASE_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
UNIX_ABSOLUTE_PATH = re.compile(r"(?:^|\s)/(?:home|Users|mnt|tmp|var|etc)/\S+")
WINDOWS_ABSOLUTE_PATH = re.compile(r"(?:^|\s)[A-Za-z]:[\\/]\S+")
SECRET_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b"),
    re.compile(r"(?i)\b(?:api[_-]?key|access[_-]?token|secret|password)\b\s*[:=]\s*[^\s,;]+"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)


class DatasetValidationError(ValueError):
    """The committed evaluation dataset is unsafe or structurally invalid."""


@dataclass(frozen=True, slots=True)
class EvaluationCase:
    case_id: str
    question: str
    reference: str
    evidence_hints: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class EvaluationDataset:
    schema_version: int
    fixture_path: Path
    fixture_text: str
    cases: tuple[EvaluationCase, ...]


def _require_exact_fields(value: dict[str, Any], *, allowed: set[str], location: str) -> None:
    unsupported = sorted(set(value).difference(allowed))
    missing = sorted(allowed.difference(value))
    if unsupported:
        raise DatasetValidationError(
            f"{location} contains unsupported fields: {', '.join(unsupported)}"
        )
    if missing:
        raise DatasetValidationError(f"{location} is missing fields: {', '.join(missing)}")


def _walk_strings(value: Any, *, location: str = "dataset") -> list[tuple[str, str]]:
    if isinstance(value, str):
        return [(location, value)]
    if isinstance(value, list):
        strings: list[tuple[str, str]] = []
        for index, item in enumerate(value):
            strings.extend(_walk_strings(item, location=f"{location}[{index}]"))
        return strings
    if isinstance(value, dict):
        strings = []
        for key, item in value.items():
            strings.extend(_walk_strings(item, location=f"{location}.{key}"))
        return strings
    return []


def _reject_paths_and_secrets(payload: dict[str, Any]) -> None:
    for location, value in _walk_strings(payload):
        stripped = value.strip()
        if (
            stripped.startswith("/")
            or UNIX_ABSOLUTE_PATH.search(value)
            or WINDOWS_ABSOLUTE_PATH.search(value)
        ):
            raise DatasetValidationError(f"{location} contains an absolute path")
        if any(pattern.search(value) for pattern in SECRET_PATTERNS):
            raise DatasetValidationError(f"{location} appears to contain a secret")


def _nonempty_string(value: Any, *, location: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DatasetValidationError(f"{location} must be a non-empty string")
    return " ".join(value.split())


def _fixture_path(repo_root: Path, value: Any) -> Path:
    fixture = _nonempty_string(value, location="dataset.fixture")
    relative = PurePosixPath(fixture)
    if relative.is_absolute() or ".." in relative.parts:
        raise DatasetValidationError("dataset.fixture must be a repository-relative safe path")
    if not fixture.startswith("evals/fixtures/"):
        raise DatasetValidationError("dataset.fixture must be stored under evals/fixtures/")
    resolved_root = repo_root.resolve()
    resolved = (resolved_root / Path(*relative.parts)).resolve()
    if resolved_root not in resolved.parents:
        raise DatasetValidationError("dataset.fixture escapes the repository root")
    if not resolved.is_file():
        raise DatasetValidationError(f"dataset.fixture does not exist: {fixture}")
    return resolved


def load_evaluation_dataset(dataset_path: Path, *, repo_root: Path) -> EvaluationDataset:
    try:
        payload = json.loads(dataset_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise DatasetValidationError(f"Could not read dataset: {dataset_path}") from error
    if not isinstance(payload, dict):
        raise DatasetValidationError("dataset must be a JSON object")
    _require_exact_fields(
        payload,
        allowed={"schemaVersion", "fixture", "cases"},
        location="dataset",
    )
    _reject_paths_and_secrets(payload)
    if payload["schemaVersion"] != 1:
        raise DatasetValidationError("dataset.schemaVersion must be 1")
    fixture_path = _fixture_path(repo_root, payload["fixture"])
    fixture_text = fixture_path.read_text(encoding="utf-8")
    raw_cases = payload["cases"]
    if not isinstance(raw_cases, list) or not MIN_CASES <= len(raw_cases) <= MAX_CASES:
        raise DatasetValidationError(
            f"dataset.cases must contain between {MIN_CASES} and {MAX_CASES} cases"
        )

    cases: list[EvaluationCase] = []
    seen_ids: set[str] = set()
    normalized_fixture = " ".join(fixture_text.lower().split())
    for index, raw_case in enumerate(raw_cases):
        location = f"dataset.cases[{index}]"
        if not isinstance(raw_case, dict):
            raise DatasetValidationError(f"{location} must be an object")
        _require_exact_fields(
            raw_case,
            allowed={"id", "question", "reference", "evidenceHints"},
            location=location,
        )
        case_id = _nonempty_string(raw_case["id"], location=f"{location}.id")
        if not CASE_ID_PATTERN.fullmatch(case_id):
            raise DatasetValidationError(f"{location}.id must be a stable kebab-case ID")
        if case_id in seen_ids:
            raise DatasetValidationError(f"duplicate case ID: {case_id}")
        seen_ids.add(case_id)
        question = _nonempty_string(raw_case["question"], location=f"{location}.question")
        reference = _nonempty_string(raw_case["reference"], location=f"{location}.reference")
        raw_hints = raw_case["evidenceHints"]
        if not isinstance(raw_hints, list) or not raw_hints:
            raise DatasetValidationError(f"{location}.evidenceHints must be a non-empty list")
        hints = tuple(
            _nonempty_string(hint, location=f"{location}.evidenceHints[{hint_index}]")
            for hint_index, hint in enumerate(raw_hints)
        )
        for hint in hints:
            if " ".join(hint.lower().split()) not in normalized_fixture:
                raise DatasetValidationError(
                    f"{location} evidence hint is missing from the fixture: {hint}"
                )
        cases.append(
            EvaluationCase(
                case_id=case_id,
                question=question,
                reference=reference,
                evidence_hints=hints,
            )
        )
    return EvaluationDataset(
        schema_version=1,
        fixture_path=fixture_path,
        fixture_text=fixture_text,
        cases=tuple(cases),
    )
