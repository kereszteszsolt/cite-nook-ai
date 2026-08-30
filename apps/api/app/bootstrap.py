# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass

from .ai.contracts import ModelProvider
from .ai.ollama import OllamaProvider
from .application.answers import GroundedAnswerService
from .application.conversations import ConversationService
from .application.documents import DocumentService
from .application.ingestion import IngestionService
from .application.model_catalog import ModelCatalogService
from .application.uploads import DocumentUploadService
from .core.settings import Settings, get_settings


@dataclass(frozen=True, slots=True)
class ApplicationContainer:
    settings: Settings
    conversation_service: ConversationService
    answer_service: GroundedAnswerService
    document_service: DocumentService
    upload_service: DocumentUploadService
    model_catalog_service: ModelCatalogService
    ingestion_service: IngestionService


def build_application(
    *,
    settings: Settings | None = None,
    model_provider: ModelProvider | None = None,
    worker_id: str | None = None,
) -> ApplicationContainer:
    resolved_settings = settings or get_settings()
    provider = model_provider or OllamaProvider(host=resolved_settings.ollama_host)
    conversations = ConversationService(resolved_settings)
    return ApplicationContainer(
        settings=resolved_settings,
        conversation_service=conversations,
        answer_service=GroundedAnswerService(
            chat_provider=provider,
            embedding_provider=provider,
            settings=resolved_settings,
            conversations=conversations,
        ),
        document_service=DocumentService(resolved_settings),
        upload_service=DocumentUploadService(resolved_settings),
        model_catalog_service=ModelCatalogService(
            provider=provider,
            settings=resolved_settings,
        ),
        ingestion_service=IngestionService(
            embedding_provider=provider,
            settings=resolved_settings,
            worker_id=worker_id,
        ),
    )
