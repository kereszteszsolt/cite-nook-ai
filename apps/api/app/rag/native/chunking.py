# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from ..contracts import TextSection

DEFAULT_CHUNK_SIZE = 1200
DEFAULT_CHUNK_OVERLAP = 160


@dataclass(frozen=True, slots=True)
class TextChunk:
    content: str
    page_number: int | None
    ordinal: int


def chunk_sections(
    sections: Sequence[TextSection],
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[TextChunk]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be non-negative and smaller than chunk_size")

    chunks: list[TextChunk] = []
    ordinal = 0
    for section in sections:
        text = _normalize_text(section.text)
        if not text:
            continue

        start = 0
        while start < len(text):
            upper = min(len(text), start + chunk_size)
            end = _best_break(text, start, upper)
            content = text[start:end].strip()
            if content:
                chunks.append(
                    TextChunk(
                        content=content,
                        page_number=section.page_number,
                        ordinal=ordinal,
                    )
                )
                ordinal += 1
            if end >= len(text):
                break
            start = max(end - overlap, start + 1)

    return chunks


def _normalize_text(value: str) -> str:
    return "\n".join(line.strip() for line in value.splitlines() if line.strip())


def _best_break(text: str, start: int, upper: int) -> int:
    if upper >= len(text):
        return len(text)
    lower = start + (upper - start) // 2
    candidates = [
        text.rfind("\n", lower, upper),
        text.rfind(". ", lower, upper),
        text.rfind(" ", lower, upper),
    ]
    best = max(candidates)
    if best <= start:
        return upper
    return best + (2 if text[best : best + 2] == ". " else 1)
