# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from typing import Any

from fastapi import APIRouter

from ...application.model_catalog import ModelCatalog as ModelCatalogResult
from ...core.brand import load_brand
from ..dependencies import ApplicationDependency, ModelCatalogServiceDependency
from ..schemas import ModelCatalog

router = APIRouter(tags=["system"])
brand = load_brand()


@router.get("/health")
def health(application: ApplicationDependency) -> dict[str, str]:
    return {
        "status": "ok",
        "appId": brand["technical"]["appId"],
        "ragBackend": application.settings.rag_backend,
    }


@router.get("/brand")
def get_brand() -> dict[str, Any]:
    return brand


@router.get("/models", response_model=ModelCatalog)
def models(service: ModelCatalogServiceDependency) -> ModelCatalogResult:
    return service.catalog()
