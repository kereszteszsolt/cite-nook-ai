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
from .rag.contracts import DocumentIndexer, SourceRetriever
from .rag.native.indexer import NativeDocumentIndexer
from .rag.native.retriever import NativeSourceRetriever


@dataclass(frozen=True, slots=True)
class ApplicationContainer:
    settings: Settings
    conversation_service: ConversationService
    answer_service: GroundedAnswerService
    document_service: DocumentService
    upload_service: DocumentUploadService
    model_catalog_service: ModelCatalogService
    ingestion_service: IngestionService
    document_indexer: DocumentIndexer
    source_retriever: SourceRetriever


def build_application(
    *,
    settings: Settings | None = None,
    model_provider: ModelProvider | None = None,
    worker_id: str | None = None,
) -> ApplicationContainer:
    resolved_settings = settings or get_settings()
    provider = model_provider or OllamaProvider(host=resolved_settings.ollama_host)
    conversations = ConversationService(resolved_settings)
    indexer = NativeDocumentIndexer(
        embedding_provider=provider,
        embedding_batch_size=resolved_settings.embedding_batch_size,
    )
    retriever = NativeSourceRetriever(embedding_provider=provider)
    return ApplicationContainer(
        settings=resolved_settings,
        conversation_service=conversations,
        answer_service=GroundedAnswerService(
            chat_provider=provider,
            retriever=retriever,
            top_k=resolved_settings.rag_top_k,
            conversations=conversations,
        ),
        document_service=DocumentService(settings=resolved_settings, indexer=indexer),
        upload_service=DocumentUploadService(resolved_settings),
        model_catalog_service=ModelCatalogService(
            provider=provider,
            settings=resolved_settings,
        ),
        ingestion_service=IngestionService(
            indexer=indexer,
            settings=resolved_settings,
            worker_id=worker_id,
        ),
        document_indexer=indexer,
        source_retriever=retriever,
    )
