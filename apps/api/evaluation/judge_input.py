# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

from .suite import SUITE_PATHS, Case, Suite, load_suite


@dataclass(frozen=True)
class SavedRun:
    path: Path
    sha256: str
    payload: dict[str, Any]
    suite: Suite
    incomplete_reason: str | None


def reject_constant(value: str) -> None:
    raise ValueError(f"Non-finite JSON number: {value}.")


def load_results(path: Path) -> SavedRun:
    raw = path.read_bytes()
    payload = json.loads(raw, parse_constant=reject_constant)
    if not isinstance(payload, dict) or type(payload.get("schemaVersion")) is not int:
        raise ValueError("Expected a fixture result object with an integer schemaVersion.")
    version = payload["schemaVersion"]
    if version not in {1, 2}:
        raise ValueError("Only fixture schema versions 1 and 2 are supported.")
    name = "baseline" if version == 1 else payload.get("suiteName")
    if not isinstance(name, str) or name not in SUITE_PATHS:
        raise ValueError("Unknown fixture suiteName.")
    suite = load_suite(name)
    if payload.get("suiteId") != suite.id or payload.get("suiteSha256") != suite.sha256:
        raise ValueError("Suite ID/hash does not match the bundled synthetic fixtures.")
    if version == 1 and payload.get("suiteName", "baseline") != "baseline":
        raise ValueError("Schema version 1 supports only baseline results.")
    if version == 2 and (
        type(payload.get("plannedCases")) is not int or payload["plannedCases"] != len(suite.cases)
    ):
        raise ValueError("plannedCases does not match the suite.")
    if payload.get("ragBackend") not in ("native", "llamaindex"):
        raise ValueError("Unknown saved ragBackend.")
    for field in ("chatModel", "embeddingModel"):
        if not isinstance(payload.get(field), str) or not payload[field].strip():
            raise ValueError(f"Missing saved {field}.")
    if type(payload.get("ragTopK")) is not int or payload["ragTopK"] <= 0:
        raise ValueError("Invalid saved ragTopK.")
    for field in ("startedAt", "finishedAt"):
        value = payload.get(field)
        if value is not None:
            if not isinstance(value, str) or datetime.fromisoformat(value).tzinfo is None:
                raise ValueError(f"Invalid UTC-aware {field} timestamp.")
    documents = payload.get("documents")
    names = {document.name for document in suite.documents}
    if not isinstance(documents, dict) or any(
        not key or not isinstance(value, str) or value not in names
        for key, value in documents.items()
    ):
        raise ValueError("documents must contain only this suite's synthetic files.")
    rows = payload.get("cases")
    if not isinstance(rows, list):
        raise ValueError("cases must be a list.")
    ids = []
    known = {case.id for case in suite.cases}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("id"), str):
            raise ValueError("Malformed case record: expected an object with an ID.")
        if row["id"] not in known or row["id"] in ids:
            raise ValueError("Unknown or duplicate case ID.")
        ids.append(row["id"])
    if payload.get("status") not in ("passed", "failed", "error"):
        raise ValueError("Unknown saved run status.")
    if payload.get("error") is not None and not isinstance(payload["error"], str):
        raise ValueError("Invalid saved run error.")
    if not isinstance(payload.get("cleanupErrors"), list):
        raise ValueError("Missing cleanupErrors list.")
    incomplete = None
    if (
        payload["status"] == "error"
        or payload.get("error") is not None
        or payload["cleanupErrors"]
        or len(rows) != len(suite.cases)
        or not payload.get("startedAt")
        or not payload.get("finishedAt")
    ):
        incomplete = "Saved run is incomplete or has a run/cleanup error; no judge calls made."
    return SavedRun(path.resolve(), sha256(raw).hexdigest(), payload, suite, incomplete)


def validate_pair(row: dict[str, Any], case: Case) -> None:
    if row.get("question") != case.question or row.get("expectsNoAnswer") is not case.no_answer:
        raise ValueError("Question or no-answer expectation differs from the synthetic manifest.")
    if row.get("error") is not None:
        raise ValueError(f"Saved case failed to complete: {row['error']}")
    if not isinstance(row.get("answer"), str):
        raise ValueError("Missing or malformed answer text.")
    if type(row.get("passed")) is not bool or not isinstance(row.get("checks"), dict):
        raise ValueError("Missing deterministic fixture outcome/checks.")
    if not row["checks"] or any(
        value is not None and type(value) is not bool for value in row["checks"].values()
    ):
        raise ValueError("Malformed deterministic fixture checks.")
    if type(row.get("responseDurationMs")) is not int or row["responseDurationMs"] < 0:
        raise ValueError("Missing or invalid responseDurationMs.")


def cited_excerpts(row: dict[str, Any], saved: SavedRun) -> tuple[list[str], str | None]:
    citations = row.get("citations")
    if citations is None:
        return [], "No saved citations/snippets; cited-excerpt faithfulness is N/A."
    if not isinstance(citations, list):
        raise ValueError("Malformed citations: expected a list.")
    if not citations:
        return [], "No citations; cited-excerpt faithfulness is N/A."
    documents = {path.name: path.read_text(encoding="utf-8") for path in saved.suite.documents}
    snippets, source_ids = [], []
    gap = False
    for citation in citations:
        if not isinstance(citation, dict):
            raise ValueError("Malformed citation record.")
        name = citation.get("documentName")
        document_id = citation.get("documentId")
        source_id = citation.get("sourceId")
        if (
            not isinstance(name, str)
            or name not in documents
            or not isinstance(document_id, str)
            or saved.payload["documents"].get(document_id) != name
            or not isinstance(source_id, str)
            or not re.fullmatch(r"S[1-9][0-9]*", source_id)
            or source_id in source_ids
        ):
            raise ValueError("Citation identity is invalid or outside the synthetic suite.")
        source_ids.append(source_id)
        snippet = citation.get("snippet")
        if snippet is None or (isinstance(snippet, str) and not snippet.strip()):
            gap = True
        elif not isinstance(snippet, str):
            raise ValueError("Malformed citation snippet.")
        elif " ".join(snippet.split()) not in " ".join(documents[name].split()):
            raise ValueError("Citation snippet does not match its bundled synthetic document.")
        else:
            snippets.append(snippet)
    markers = set(re.findall(r"\[(S[^\]\s]*)\]", row["answer"], re.IGNORECASE))
    if markers != set(source_ids):
        return [], "Citation markers do not match the saved citations; faithfulness is N/A."
    if gap:
        return [], "At least one cited snippet is missing/empty; faithfulness is N/A."
    return snippets, None
