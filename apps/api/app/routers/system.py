# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from fastapi import APIRouter

from ..schemas import ModelCatalog
from ..services.model_catalog import ModelCatalogService

router = APIRouter(tags=["system"])


@router.get("/models", response_model=ModelCatalog)
def models() -> ModelCatalog:
    return ModelCatalogService().catalog()
