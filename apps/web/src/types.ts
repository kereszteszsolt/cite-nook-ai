/*
 * SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
 * SPDX-License-Identifier: Apache-2.0
 */

export interface ModelOption {
  name: string;
  installed: boolean;
}

export interface ModelCatalog {
  chatModels: ModelOption[];
  embeddingModels: ModelOption[];
  defaultChatModel: string;
  defaultEmbeddingModel: string;
  ollamaAvailable: boolean;
}

export interface Conversation {
  id: string;
  title: string;
  chatModel: string;
  embeddingModel: string;
  createdAt: string;
  updatedAt: string;
}

export interface Citation {
  sourceId: string;
  documentId: string;
  documentName: string;
  pageNumber: number | null;
  chunkId: string;
  snippet: string;
  score: number;
}

export interface ConversationMessage {
  id: string;
  conversationId: string;
  ordinal: number;
  role: 'user' | 'assistant';
  content: string;
  chatModel: string | null;
  citations: Citation[];
  createdAt: string;
}

export type DocumentStatus = 'queued' | 'processing' | 'ready' | 'failed';

export interface DocumentRecord {
  id: string;
  fileName: string;
  contentType: string;
  sizeBytes: number;
  sha256: string;
  embeddingModel: string;
  status: DocumentStatus;
  errorMessage: string | null;
  chunkCount: number;
  createdAt: string;
}

export type StoredUpload = DocumentRecord;
