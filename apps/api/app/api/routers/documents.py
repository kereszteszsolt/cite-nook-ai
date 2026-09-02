# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile, status
from fastapi.responses import FileResponse

from ...application.uploads import (
    EmptyUploadError,
    UnsupportedDocumentTypeError,
    UnsupportedEmbeddingModelError,
    UploadTooLargeError,
)
from ...persistence.models import Document
from ..dependencies import (
    DatabaseSession,
    DocumentServiceDependency,
    UploadServiceDependency,
)
from ..schemas import DocumentRead, DocumentUpdate

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=list[DocumentRead])
def list_documents(
    session: DatabaseSession,
    service: DocumentServiceDependency,
) -> list[Document]:
    return service.list(session)


@router.post("", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    session: DatabaseSession,
    file: Annotated[UploadFile, File()],
    embedding_model: Annotated[str, Form()],
    service: UploadServiceDependency,
) -> Document:
    try:
        return await service.store(
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


@router.patch("/{document_id}", response_model=DocumentRead)
def update_document(
    document_id: UUID,
    payload: DocumentUpdate,
    session: DatabaseSession,
    service: DocumentServiceDependency,
) -> Document:
    document = service.set_active(session, document_id, is_active=payload.is_active)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    return document


@router.get("/{document_id}/file", response_class=FileResponse)
def open_document(
    document_id: UUID,
    session: DatabaseSession,
    service: DocumentServiceDependency,
) -> FileResponse:
    document = service.get(session, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    path = service.original_file(document)
    if path is None:
        raise HTTPException(status_code=404, detail="Stored document file not found.")
    return FileResponse(
        path,
        media_type=document.content_type,
        filename=document.file_name,
        content_disposition_type="inline",
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: UUID,
    session: DatabaseSession,
    service: DocumentServiceDependency,
) -> Response:
    if not service.delete(session, document_id):
        raise HTTPException(status_code=404, detail="Document not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
