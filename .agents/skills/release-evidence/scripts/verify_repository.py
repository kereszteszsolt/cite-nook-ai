#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

"""Dependency-free structural checks for the CiteNook repository."""

from __future__ import annotations

import json
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
ERRORS: list[str] = []


def fail(message: str) -> None:
    ERRORS.append(message)


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
    except Exception as error:
        fail(f"Invalid JSON {path.relative_to(ROOT)}: {error}")

toml_paths = [ROOT / "apps/api/pyproject.toml", ROOT / ".codex/config.toml"]
toml_paths.extend((ROOT / ".codex/agents").glob("*.toml"))
for path in toml_paths:
    try:
        tomllib.loads(path.read_text(encoding="utf-8"))
    except Exception as error:
        fail(f"Invalid TOML {path.relative_to(ROOT)}: {error}")

agents = sorted((ROOT / ".codex/agents").glob("*.toml"))
skills = sorted((ROOT / ".agents/skills").glob("*/SKILL.md"))
stories = sorted((ROOT / "docs/releases").rglob("MRA-*.md"))

if len(agents) != 3:
    fail(f"Expected 3 Codex agents, found {len(agents)}.")
if len(skills) != 3:
    fail(f"Expected 3 repository skills, found {len(skills)}.")
if len(stories) != 17:
    fail(f"Expected 17 MRA stories, found {len(stories)}.")

story_ids: set[str] = set()
for path in stories:
    match = re.match(r"(MRA-\d+)-", path.name)
    if not match:
        fail(f"Invalid story filename: {path.relative_to(ROOT)}")
        continue
    story_id = match.group(1)
    if story_id in story_ids:
        fail(f"Duplicate story ID: {story_id}")
    story_ids.add(story_id)

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

standard_config_paths = [
    ROOT / ".dockerignore",
    ROOT / ".env.example",
    ROOT / ".gitignore",
    ROOT / "apps/api/Dockerfile",
    ROOT / "apps/api/pyproject.toml",
    ROOT / "apps/web/Dockerfile",
    ROOT / "apps/web/vite.config.ts",
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

if ERRORS:
    print("Repository verification failed:")
    for error in ERRORS:
        print(f"- {error}")
    sys.exit(1)

print(
    "Repository verification passed: "
    f"{len(agents)} agents, {len(skills)} skills, {len(stories)} stories."
)
