# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from .settings import get_settings


@lru_cache(maxsize=1)
def load_brand() -> dict[str, Any]:
    with get_settings().brand_config_path.open(encoding="utf-8") as file:
        brand: dict[str, Any] = json.load(file)

    required = {
        "productName",
        "extendedName",
        "description",
        "tagline",
        "developer",
        "technical",
        "theme",
    }
    missing = required.difference(brand)
    if missing:
        raise RuntimeError(f"Brand configuration is missing: {', '.join(sorted(missing))}")
    return brand
