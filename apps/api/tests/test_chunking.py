# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

import pytest

from app.rag.native.chunking import TextSection, chunk_sections


def test_chunking_is_deterministic_overlapping_and_preserves_page_numbers() -> None:
    text = " ".join(f"sentence-{index}." for index in range(160))
    sections = [TextSection(text=text, page_number=3)]

    first = chunk_sections(sections, chunk_size=240, overlap=48)
    second = chunk_sections(sections, chunk_size=240, overlap=48)

    assert first == second
    assert len(first) > 2
    assert [chunk.ordinal for chunk in first] == list(range(len(first)))
    assert all(chunk.page_number == 3 for chunk in first)
    assert first[0].content[-24:] in first[1].content


def test_chunking_skips_blank_sections_and_validates_bounds() -> None:
    assert chunk_sections([TextSection(text="  \n\n ")]) == []
    with pytest.raises(ValueError, match="smaller than chunk_size"):
        chunk_sections([TextSection(text="text")], chunk_size=10, overlap=10)
