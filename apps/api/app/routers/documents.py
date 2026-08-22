# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from ..dependencies import DatabaseSession
from ..models import Document
from ..schemas import DocumentUploadRead
from ..services.uploads import (
    DocumentUploadService,
    EmptyUploadError,
    UnsupportedDocumentTypeError,
    UnsupportedEmbeddingModelError,
    UploadTooLargeError,
)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentUploadRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    session: DatabaseSession,
    file: Annotated[UploadFile, File()],
    embedding_model: Annotated[str, Form()],
) -> Document:
    try:
        return await DocumentUploadService().store(
            session,
            file=file,
            embedding_model=embedding_model,
        )
    except UnsupportedEmbeddingModelError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except UnsupportedDocumentTypeError as error:
        raise HTTPException(status_code=415, detail=str(error)) from error
    except UploadTooLargeError as error:
        raise HTTPException(status_code=413, detail=str(error)) from error
    except EmptyUploadError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
