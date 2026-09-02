# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from typing import Annotated, cast

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from ..application.answers import GroundedAnswerService
from ..application.conversations import ConversationService
from ..application.documents import DocumentService
from ..application.model_catalog import ModelCatalogService
from ..application.uploads import DocumentUploadService
from ..bootstrap import ApplicationContainer
from ..persistence.database import get_session

DatabaseSession = Annotated[Session, Depends(get_session)]


def get_application(request: Request) -> ApplicationContainer:
    return cast(ApplicationContainer, request.app.state.application)


ApplicationDependency = Annotated[ApplicationContainer, Depends(get_application)]


def get_conversation_service(
    application: ApplicationDependency,
) -> ConversationService:
    return application.conversation_service


def get_answer_service(application: ApplicationDependency) -> GroundedAnswerService:
    return application.answer_service


def get_document_service(application: ApplicationDependency) -> DocumentService:
    return application.document_service


def get_upload_service(application: ApplicationDependency) -> DocumentUploadService:
    return application.upload_service


def get_model_catalog_service(
    application: ApplicationDependency,
) -> ModelCatalogService:
    return application.model_catalog_service


ConversationServiceDependency = Annotated[
    ConversationService, Depends(get_conversation_service)
]
AnswerServiceDependency = Annotated[GroundedAnswerService, Depends(get_answer_service)]
DocumentServiceDependency = Annotated[DocumentService, Depends(get_document_service)]
UploadServiceDependency = Annotated[
    DocumentUploadService, Depends(get_upload_service)
]
ModelCatalogServiceDependency = Annotated[
    ModelCatalogService, Depends(get_model_catalog_service)
]
