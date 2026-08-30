# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routers import conversations, documents, system
from .core.brand import load_brand
from .core.settings import get_settings
from .persistence.database import init_database


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_database()
    yield


brand = load_brand()
settings = get_settings()
app = FastAPI(
    title=f"{brand['extendedName']} API",
    description=brand["description"],
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["*"],
)


app.include_router(system.router, prefix="/api")
app.include_router(conversations.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
