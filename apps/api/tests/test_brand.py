# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from app.brand import load_brand
from app.settings import get_settings


def test_brand_contains_public_and_technical_identity() -> None:
    get_settings.cache_clear()
    load_brand.cache_clear()

    brand = load_brand()

    assert brand["productName"] == "CiteNook"
    assert brand["extendedName"] == "CiteNook AI"
    assert brand["description"] == "Local document Q&A with citations"
    assert brand["tagline"] == "Ask your documents. Verify the sources."
    assert brand["assets"] == {"favicon": "/favicon.svg"}
    assert brand["technical"] == {
        "repository": "cite-nook-ai",
        "packageScope": "@citenook/*",
        "appId": "cite-nook-ai",
        "dockerProject": "citenook",
        "storyPrefix": "MRA",
    }
