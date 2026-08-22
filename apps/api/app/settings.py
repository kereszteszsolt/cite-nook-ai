# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


def _csv(name: str, default: str) -> tuple[str, ...]:
    return tuple(value.strip() for value in os.getenv(name, default).split(",") if value.strip())


@dataclass(frozen=True, slots=True)
class Settings:
    database_url: str
    ollama_host: str
    brand_config_path: Path
    cors_origins: tuple[str, ...]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        database_url=os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg://cite_nook:checked-in-development-only@localhost:5432/cite_nook",
        ),
        ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        brand_config_path=Path(
            os.getenv("BRAND_CONFIG_PATH", "../../packages/brand/brand.json")
        ).resolve(),
        cors_origins=_csv("CORS_ORIGINS", "http://localhost:5173"),
    )
