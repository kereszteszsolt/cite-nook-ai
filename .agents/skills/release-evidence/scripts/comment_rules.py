# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

"""Find source comments that exceed the CiteNook sentence limits."""

from __future__ import annotations

import ast
import io
import os
import re
import tokenize
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path

MAX_COMMENT_SENTENCES = 3
MAX_DOCSTRING_SENTENCES = 5
SUPPORTED_SUFFIXES = {
    ".bash",
    ".cjs",
    ".js",
    ".jsx",
    ".mjs",
    ".py",
    ".sh",
    ".sql",
    ".ts",
    ".tsx",
}
IGNORED_PARTS = {
    ".generated-code-backup",
    ".git",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "coverage",
    "dist",
    "node_modules",
    "test-results",
}
DIRECTIVE_PATTERNS = (
    re.compile(r"^SPDX-", re.IGNORECASE),
    re.compile(
        r"^(?:noqa|type:\s*ignore|ruff:|fmt:|isort:|coverage:|pragma:|"
        r"pylint:|pyright:|mypy:|nosec)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"^@(?:vitest-environment|jest-environment|ts-ignore|ts-expect-error|"
        r"ts-nocheck)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"^(?:eslint|stylelint|prettier|istanbul|c8)(?:[-:\s]|$)",
        re.IGNORECASE,
    ),
)


@dataclass(frozen=True)
class SourceNote:
    line: int
    column: int
    kind: str
    text: str


def sentence_count(text: str) -> int:
    plain = re.sub(r"\s+", " ", text).strip()
    if not re.search(r"[A-Za-z]", plain):
        return 0
    count = len(re.findall(r"[.!?](?=\s|$)", plain))
    if plain[-1] not in ".!?":
        count += 1
    return max(1, count)


def is_directive(text: str) -> bool:
    plain = re.sub(r"\s+", " ", text).strip()
    return any(pattern.search(plain) for pattern in DIRECTIVE_PATTERNS)


def prose_without_directives(text: str) -> str:
    return "\n".join(
        line for line in text.splitlines() if not is_directive(line)
    ).strip()


def clean_block_comment(text: str) -> str:
    lines = []
    for line in text.splitlines():
        clean = line.strip()
        if clean.startswith("*"):
            clean = clean[1:].lstrip()
        lines.append(clean)
    return "\n".join(lines).strip()


def group_line_comments(notes: Iterable[SourceNote]) -> list[SourceNote]:
    grouped: list[SourceNote] = []
    pending: SourceNote | None = None
    pending_last_line = 0

    for note in notes:
        if note.kind == "line-comment" and is_directive(note.text):
            if pending is not None:
                grouped.append(pending)
                pending = None
            continue
        if note.kind != "line-comment":
            if pending is not None:
                grouped.append(pending)
                pending = None
            grouped.append(note)
            continue
        if (
            pending is not None
            and note.line == pending_last_line + 1
            and note.column == pending.column
        ):
            pending = SourceNote(
                line=pending.line,
                column=pending.column,
                kind=pending.kind,
                text=f"{pending.text}\n{note.text}",
            )
        else:
            if pending is not None:
                grouped.append(pending)
            pending = note
        pending_last_line = note.line

    if pending is not None:
        grouped.append(pending)
    return grouped


def python_notes(text: str) -> list[SourceNote]:
    comments: list[SourceNote] = []
    tokens = tokenize.generate_tokens(io.StringIO(text).readline)
    for token in tokens:
        if token.type != tokenize.COMMENT:
            continue
        if token.start[0] == 1 and token.string.startswith("#!"):
            continue
        comments.append(
            SourceNote(
                line=token.start[0],
                column=token.start[1],
                kind="line-comment",
                text=token.string[1:].strip(),
            )
        )

    notes = group_line_comments(comments)
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if not isinstance(
            node,
            (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef),
        ):
            continue
        if not node.body:
            continue
        first = node.body[0]
        if not (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        ):
            continue
        notes.append(
            SourceNote(
                line=first.lineno,
                column=first.col_offset,
                kind="docstring",
                text=first.value.value,
            )
        )
    return sorted(notes, key=lambda note: (note.line, note.column))


def c_style_notes(text: str, line_marker: str) -> list[SourceNote]:
    notes: list[SourceNote] = []
    index = 0
    line = 1
    column = 0
    length = len(text)

    while index < length:
        char = text[index]
        if char == "\n":
            line += 1
            column = 0
            index += 1
            continue
        if char in "'\"`":
            quote = char
            index += 1
            column += 1
            while index < length:
                char = text[index]
                if char == "\\":
                    index += 2
                    column += 2
                    continue
                if char == quote:
                    if index + 1 < length and text[index + 1] == quote:
                        index += 2
                        column += 2
                        continue
                    index += 1
                    column += 1
                    break
                if char == "\n":
                    line += 1
                    column = 0
                else:
                    column += 1
                index += 1
            continue
        if text.startswith("/*", index):
            start_line = line
            start_column = column
            end = text.find("*/", index + 2)
            if end == -1:
                end = length
                next_index = length
            else:
                next_index = end + 2
            raw = text[index + 2 : end]
            notes.append(
                SourceNote(
                    line=start_line,
                    column=start_column,
                    kind="block-comment",
                    text=clean_block_comment(raw),
                )
            )
            consumed = text[index:next_index]
            line_breaks = consumed.count("\n")
            if line_breaks:
                line += line_breaks
                column = len(consumed.rsplit("\n", 1)[-1])
            else:
                column += len(consumed)
            index = next_index
            continue
        if text.startswith(line_marker, index):
            end = text.find("\n", index + len(line_marker))
            if end == -1:
                end = length
            notes.append(
                SourceNote(
                    line=line,
                    column=column,
                    kind="line-comment",
                    text=text[index + len(line_marker) : end].strip(),
                )
            )
            column += end - index
            index = end
            continue
        index += 1
        column += 1

    return group_line_comments(notes)


def shell_notes(text: str) -> list[SourceNote]:
    notes: list[SourceNote] = []
    for line_number, source_line in enumerate(text.splitlines(), start=1):
        quote: str | None = None
        escaped = False
        for column, char in enumerate(source_line):
            if escaped:
                escaped = False
                continue
            if char == "\\" and quote != "'":
                escaped = True
                continue
            if quote is not None:
                if char == quote:
                    quote = None
                continue
            if char in "'\"":
                quote = char
                continue
            if char != "#":
                continue
            if line_number == 1 and column == 0 and source_line.startswith("#!"):
                break
            notes.append(
                SourceNote(
                    line=line_number,
                    column=column,
                    kind="line-comment",
                    text=source_line[column + 1 :].strip(),
                )
            )
            break
    return group_line_comments(notes)


def source_notes(path: Path, text: str) -> list[SourceNote]:
    if path.suffix == ".py":
        return python_notes(text)
    if path.suffix in {".sh", ".bash"}:
        return shell_notes(text)
    if path.suffix == ".sql":
        return c_style_notes(text, "--")
    return c_style_notes(text, "//")


def iter_source_paths(source_roots: Iterable[Path]) -> Iterator[Path]:
    for source_root in source_roots:
        if not source_root.exists():
            continue
        if source_root.is_file():
            if source_root.suffix in SUPPORTED_SUFFIXES:
                yield source_root
            continue
        for current_root, directories, filenames in os.walk(source_root):
            directories[:] = [
                name for name in directories if name not in IGNORED_PARTS
            ]
            current_path = Path(current_root)
            for filename in filenames:
                path = current_path / filename
                if path.suffix in SUPPORTED_SUFFIXES:
                    yield path


def find_comment_rule_errors(
    repository_root: Path,
    source_roots: Iterable[Path],
) -> list[str]:
    errors: list[str] = []
    for path in sorted(set(iter_source_paths(source_roots))):
        try:
            notes = source_notes(path, path.read_text(encoding="utf-8"))
        except (SyntaxError, tokenize.TokenError) as error:
            errors.append(
                f"Could not inspect source comments in "
                f"{path.relative_to(repository_root)}: {error}"
            )
            continue
        for note in notes:
            prose = prose_without_directives(note.text)
            if not prose:
                continue
            count = sentence_count(prose)
            maximum = (
                MAX_DOCSTRING_SENTENCES
                if note.kind == "docstring"
                else MAX_COMMENT_SENTENCES
            )
            if count <= maximum:
                continue
            label = "Docstring" if note.kind == "docstring" else "Comment block"
            errors.append(
                f"{label} has {count} sentences in "
                f"{path.relative_to(repository_root)}:{note.line}; "
                f"maximum is {maximum}."
            )
    return errors
