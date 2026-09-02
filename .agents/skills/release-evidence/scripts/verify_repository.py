#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

"""Run dependency-free structural checks for the CiteNook repository."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote

import tomllib
from comment_rules import find_comment_rule_errors

ROOT = Path(__file__).resolve().parents[4]
ERRORS: list[str] = []


def fail(message: str) -> None:
    ERRORS.append(message)


def section_text(text: str, heading: str) -> str:
    match = re.search(
        rf"^## {re.escape(heading)}\s*$\n(.*?)(?=^## |\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    return match.group(1).strip() if match else ""


def syllable_count(word: str) -> int:
    clean = re.sub(r"[^a-z]", "", word.casefold())
    if not clean:
        return 0
    count = len(re.findall(r"[aeiouy]+", clean))
    if clean.endswith("e") and count > 1 and not clean.endswith(("le", "ye")):
        count -= 1
    if clean.endswith("es") and count > 1 and not clean.endswith(("aes", "ees", "oes")):
        count -= 1
    return max(1, count)


def flesch_reading_ease(text: str) -> float:
    plain = re.sub(r"`[^`]+`", " ", text)
    words = re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", plain)
    sentences = re.findall(r"[.!?]+", plain)
    if not words or not sentences:
        return 0.0
    syllables = sum(syllable_count(word) for word in words)
    return 206.835 - 1.015 * (len(words) / len(sentences)) - 84.6 * (
        syllables / len(words)
    )


def sentence_count(text: str) -> int:
    return len(re.findall(r"[.!?](?:$|\s|[`*_])", text.strip()))


def markdown_fragments(text: str) -> set[str]:
    fragments: set[str] = set()
    occurrences: dict[str, int] = {}
    for heading in re.findall(r"^#{1,6}\s+(.+?)\s*#*$", text, re.MULTILINE):
        plain = re.sub(r"[`*_~]", "", heading).casefold()
        base = re.sub(r"[^\w\s-]", "", plain)
        base = re.sub(r"\s+", "-", base.strip())
        occurrence = occurrences.get(base, 0)
        occurrences[base] = occurrence + 1
        fragments.add(base if occurrence == 0 else f"{base}-{occurrence}")
    return fragments


IGNORED_PARTS = {
    ".generated-code-backup",
    ".git",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "node_modules",
}

json_paths = [
    ROOT / "package.json",
    ROOT / "turbo.json",
    ROOT / "apps/api/package.json",
    ROOT / "apps/web/package.json",
    ROOT / "packages/brand/brand.json",
    ROOT / "packages/brand/package.json",
    ROOT / "packages/brand/tsconfig.json",
]
for path in json_paths:
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError) as error:
        fail(f"Invalid JSON {path.relative_to(ROOT)}: {error}")

toml_paths = [ROOT / "apps/api/pyproject.toml", ROOT / ".codex/config.toml"]
toml_paths.extend((ROOT / ".codex/agents").glob("*.toml"))
for path in toml_paths:
    try:
        tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError, UnicodeDecodeError) as error:
        fail(f"Invalid TOML {path.relative_to(ROOT)}: {error}")

agents = sorted((ROOT / ".codex/agents").glob("*.toml"))
skills = sorted((ROOT / ".agents/skills").glob("*/SKILL.md"))
stories = sorted((ROOT / "docs/releases").rglob("MRA-*.md"))

if len(agents) != 3:
    fail(f"Expected 3 Codex agents, found {len(agents)}.")
if len(skills) != 3:
    fail(f"Expected 3 repository skills, found {len(skills)}.")
if not stories:
    fail("Expected at least one MRA story.")

story_ids: dict[int, Path] = {}
for path in stories:
    match = re.match(r"MRA-(\d+)-", path.name)
    if not match:
        fail(f"Invalid story filename: {path.relative_to(ROOT)}")
        continue
    story_number = int(match.group(1))
    if story_number in story_ids:
        fail(f"Duplicate story ID: MRA-{story_number:03d}")
    story_ids[story_number] = path

if story_ids:
    expected_ids = set(range(1, max(story_ids) + 1))
    missing_ids = sorted(expected_ids.difference(story_ids))
    if missing_ids:
        missing = ", ".join(f"MRA-{value:03d}" for value in missing_ids)
        fail(f"Missing story IDs: {missing}")

required_headings = [
    "## Status",
    "## User story",
    "## Goal",
    "## Dependencies",
    "## Acceptance criteria",
    "## Out of scope",
]
for story_number, path in sorted(story_ids.items()):
    text = path.read_text(encoding="utf-8")
    headings = [line.strip() for line in text.splitlines() if line.startswith("## ")]
    if headings != required_headings:
        fail(
            f"Invalid story headings in {path.relative_to(ROOT)}: "
            + ", ".join(headings)
        )

    if re.search(
        r"^## (?:Known issue|Known issues|Known limitation|Known limitations)\s*$",
        text,
        re.IGNORECASE | re.MULTILINE,
    ):
        fail(f"Story has a forbidden issue section: {path.relative_to(ROOT)}")

    status_match = re.search(
        r"^## Status\s+^(Planned|In progress|Implemented)\s*$",
        text,
        re.MULTILINE,
    )
    if not status_match:
        fail(f"Invalid story status in {path.relative_to(ROOT)}")
        status = None
    else:
        status = status_match.group(1)

    criteria = re.findall(r"^- \[([ xX])\] (.+)$", text, re.MULTILINE)
    if not 4 <= len(criteria) <= 8:
        fail(
            f"Expected 4 to 8 criteria in {path.relative_to(ROOT)}, "
            f"found {len(criteria)}."
        )
    for _, criterion in criteria:
        if sentence_count(criterion) != 1:
            fail(
                f"Criterion must be one sentence in {path.relative_to(ROOT)}: "
                f"{criterion}"
            )

    if status == "Planned" and any(mark.casefold() == "x" for mark, _ in criteria):
        fail(f"Planned story has checked criteria: {path.relative_to(ROOT)}")
    if status == "Implemented" and any(mark == " " for mark, _ in criteria):
        fail(f"Implemented story has unchecked criteria: {path.relative_to(ROOT)}")

    readable_text = " ".join(
        [section_text(text, "User story"), section_text(text, "Goal")]
    )
    reading_score = flesch_reading_ease(readable_text)
    if reading_score < 80:
        fail(
            f"Story prose is below Flesch 80 in {path.relative_to(ROOT)}: "
            f"{reading_score:.1f}"
        )

    for paragraph in re.split(r"\n\s*\n", text):
        stripped = paragraph.strip()
        if not stripped or stripped.startswith(("#", "-", "```")):
            continue
        if sentence_count(stripped) > 5:
            fail(f"Story prose block exceeds five sentences: {path.relative_to(ROOT)}")

    release_map = path.parent.parent / "README.md"
    verification = path.parent.parent / "verification.md"
    if not release_map.exists():
        fail(f"Missing release map for {path.relative_to(ROOT)}")
    elif f"stories/{path.name}" not in release_map.read_text(encoding="utf-8"):
        fail(f"Story is not linked from its release map: {path.relative_to(ROOT)}")
    if not verification.exists():
        fail(f"Missing release verification for {path.relative_to(ROOT)}")
    elif release_map.exists() and "(verification.md)" not in release_map.read_text(
        encoding="utf-8"
    ):
        fail(f"Verification is not linked from its release map: {path.relative_to(ROOT)}")

required_services = {"web", "api", "worker", "postgres"}
compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
for service in required_services:
    if not re.search(rf"^  {service}:$", compose, re.MULTILINE):
        fail(f"Base Docker Compose service is missing: {service}")

if re.search(r"^  ollama:$", compose, re.MULTILINE):
    fail("Base Docker Compose must use an external Ollama instance by default.")

ollama_compose = (ROOT / "docker-compose.ollama.yml").read_text(encoding="utf-8")
if not re.search(r"^  ollama:$", ollama_compose, re.MULTILINE):
    fail("The optional Docker Compose override is missing the Ollama service.")
if "ollama_data:/root/.ollama" not in ollama_compose:
    fail("The optional Ollama service is missing its persistent model volume.")

llamaindex_compose = (ROOT / "docker-compose.llamaindex.yml").read_text(
    encoding="utf-8"
)
if not re.search(r"^name: citenook-llamaindex$", llamaindex_compose, re.MULTILINE):
    fail("The LlamaIndex Compose override must use its isolated project name.")
if llamaindex_compose.count("target: runtime-llamaindex") != 2:
    fail("The LlamaIndex Compose override must select both runtime images.")
if llamaindex_compose.count("RAG_BACKEND: llamaindex") != 2:
    fail("The LlamaIndex Compose override must select both service backends.")

source_roots = [
    ROOT / ".agents/skills/release-evidence/scripts",
    ROOT / "apps/api/app",
    ROOT / "apps/api/tests",
    ROOT / "apps/web/src",
    ROOT / "infra/postgres",
    ROOT / "packages/brand/src",
]
for source_root in source_roots:
    for path in source_root.rglob("*"):
        if (
            not path.is_file()
            or path.name == "__init__.py"
            or any(part in IGNORED_PARTS for part in path.parts)
        ):
            continue
        if "SPDX-License-Identifier: Apache-2.0" not in path.read_text(encoding="utf-8"):
            fail(f"Missing SPDX header: {path.relative_to(ROOT)}")

comment_source_roots = [
    ROOT / ".agents/skills",
    ROOT / "apps/api",
    ROOT / "apps/web",
    ROOT / "infra/postgres",
    ROOT / "packages/brand/src",
    ROOT / "scripts",
]
ERRORS.extend(find_comment_rule_errors(ROOT, comment_source_roots))

standard_config_paths = [
    ROOT / ".dockerignore",
    ROOT / ".env.example",
    ROOT / ".gitignore",
    ROOT / "apps/api/Dockerfile",
    ROOT / "apps/api/pyproject.toml",
    ROOT / "apps/web/Dockerfile",
    ROOT / "apps/web/vite.config.ts",
    ROOT / "docker-compose.llamaindex.yml",
    ROOT / "docker-compose.ollama.yml",
    ROOT / "docker-compose.yml",
    ROOT / ".codex/config.toml",
]
standard_config_paths.extend((ROOT / ".codex/agents").glob("*.toml"))
for path in standard_config_paths:
    if "SPDX-License-Identifier" in path.read_text(encoding="utf-8"):
        fail(f"Unexpected SPDX header in standard configuration: {path.relative_to(ROOT)}")

package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
if package.get("name") != "cite-nook-ai":
    fail("The stable root package name changed unexpectedly.")
if package.get("license") != "Apache-2.0":
    fail("The root package license is not Apache-2.0.")

brand = json.loads((ROOT / "packages/brand/brand.json").read_text(encoding="utf-8"))
if brand.get("productName") != "CiteNook" or brand.get("extendedName") != "CiteNook AI":
    fail("The public CiteNook brand identity is invalid.")
if brand.get("technical") != {
    "repository": "cite-nook-ai",
    "packageScope": "@citenook/*",
    "appId": "cite-nook-ai",
    "dockerProject": "citenook",
    "storyPrefix": "MRA",
}:
    fail("The stable CiteNook technical identity is invalid.")

markdown_paths = [
    path
    for path in ROOT.rglob("*.md")
    if not any(part in IGNORED_PARTS for part in path.parts)
]
for path in markdown_paths:
    if re.search(
        r"\bportfolio project\b",
        path.read_text(encoding="utf-8"),
        re.IGNORECASE,
    ):
        fail(f"Project documentation uses a forbidden project label: {path.relative_to(ROOT)}")

local_link_count = 0
for path in markdown_paths:
    source = re.sub(
        r"^```.*?^```\s*$",
        "",
        path.read_text(encoding="utf-8"),
        flags=re.MULTILINE | re.DOTALL,
    )
    for target in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", source):
        if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.IGNORECASE):
            continue
        local_link_count += 1
        target_path, _, fragment = target.partition("#")
        resolved = path if not target_path else (path.parent / unquote(target_path)).resolve()
        try:
            resolved.relative_to(ROOT)
        except ValueError:
            fail(f"Local Markdown link escapes the repository in {path.relative_to(ROOT)}: {target}")
            continue
        if not resolved.exists():
            fail(f"Broken local Markdown link in {path.relative_to(ROOT)}: {target}")
            continue
        if fragment and resolved.suffix.casefold() == ".md":
            fragments = markdown_fragments(resolved.read_text(encoding="utf-8"))
            if unquote(fragment).casefold() not in fragments:
                fail(f"Broken Markdown fragment in {path.relative_to(ROOT)}: {target}")

if ERRORS:
    print("Repository verification failed:")
    for error in ERRORS:
        print(f"- {error}")
    sys.exit(1)

print(
    "Repository verification passed: "
    f"{len(agents)} agents, {len(skills)} skills, {len(stories)} stories, "
    f"{local_link_count} local links."
)
