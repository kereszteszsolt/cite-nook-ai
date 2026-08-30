/*
 * SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
 * SPDX-License-Identifier: Apache-2.0
 */

import { cleanup } from '@testing-library/react';
import { vi, type Mock } from 'vitest';

export type AppApiMock = Record<
  | 'models'
  | 'conversations'
  | 'messages'
  | 'askQuestion'
  | 'documents'
  | 'createConversation'
  | 'updateConversation'
  | 'updateConversationTitle'
  | 'deleteConversation'
  | 'uploadDocument'
  | 'documentFileUrl'
  | 'updateDocument'
  | 'deleteDocument',
  Mock
>;

export const storedConversation = {
  id: 'conversation-1',
  title: 'New conversation',
  chatModel: 'qwen3.5:9b',
  embeddingModel: 'qwen3-embedding:0.6b',
  createdAt: '2026-08-22T00:00:00Z',
  updatedAt: '2026-08-22T00:00:00Z',
};

export const readyDocument = {
  id: 'document-1',
  fileName: 'notes.md',
  contentType: 'text/markdown',
  sizeBytes: 2048,
  sha256: 'abc123',
  embeddingModel: 'qwen3-embedding:0.6b',
  status: 'ready',
  errorMessage: null,
  chunkCount: 4,
  isActive: true,
  createdAt: '2026-08-22T00:00:00Z',
};

export const storedMessages = [
  {
    id: 'message-1',
    conversationId: 'conversation-1',
    ordinal: 1,
    role: 'user',
    content: 'What does the document say?',
    chatModel: null,
    citations: [],
    responseDurationMs: null,
    createdAt: '2026-08-22T00:01:00Z',
  },
  {
    id: 'message-2',
    conversationId: 'conversation-1',
    ordinal: 2,
    role: 'assistant',
    content: 'The persisted answer.',
    chatModel: 'qwen3.5:9b',
    citations: [
      {
        sourceId: 'S1',
        documentId: 'document-1',
        documentName: 'notes.md',
        pageNumber: 2,
        chunkId: 'chunk-1',
        snippet: 'Relevant text',
        score: 0.91,
      },
    ],
    responseDurationMs: 2345,
    createdAt: '2026-08-22T00:01:01Z',
  },
];

export function configureAppTest(apiMock: AppApiMock) {
  Object.defineProperty(navigator, 'clipboard', {
    configurable: true,
    value: { writeText: vi.fn().mockResolvedValue(undefined) },
  });
  apiMock.models.mockResolvedValue({
    chatModels: [
      { name: 'llama3.1:8b', installed: true },
      { name: 'qwen3.5:9b', installed: true },
      { name: 'missing-chat', installed: false },
    ],
    embeddingModels: [
      { name: 'qwen3-embedding:0.6b', installed: true },
      { name: 'embeddinggemma', installed: false },
    ],
    defaultChatModel: 'llama3.1:8b',
    defaultEmbeddingModel: 'qwen3-embedding:0.6b',
    ollamaAvailable: true,
  });
  apiMock.conversations.mockResolvedValue([storedConversation]);
  apiMock.messages.mockResolvedValue([]);
  apiMock.askQuestion.mockResolvedValue({
    conversation: { ...storedConversation, title: 'What does the document say?' },
    userMessage: storedMessages[0],
    assistantMessage: storedMessages[1],
  });
  apiMock.documents.mockResolvedValue([]);
  apiMock.createConversation.mockImplementation(
    (chatModel: string, embeddingModel: string) =>
      Promise.resolve({
        ...storedConversation,
        id: 'conversation-2',
        chatModel,
        embeddingModel,
      }),
  );
  apiMock.updateConversation.mockImplementation(
    (_id: string, chatModel: string, embeddingModel: string) =>
      Promise.resolve({ ...storedConversation, chatModel, embeddingModel }),
  );
  apiMock.updateConversationTitle.mockImplementation((_id: string, title: string) =>
    Promise.resolve({ ...storedConversation, title }),
  );
  apiMock.deleteConversation.mockResolvedValue(undefined);
  apiMock.uploadDocument.mockResolvedValue({
    ...readyDocument,
    sizeBytes: 7,
    status: 'queued',
    chunkCount: 0,
  });
  apiMock.documentFileUrl.mockImplementation(
    (id: string) => `http://localhost:8000/api/documents/${id}/file`,
  );
  apiMock.updateDocument.mockImplementation((_id: string, isActive: boolean) =>
    Promise.resolve({ ...readyDocument, isActive }),
  );
  apiMock.deleteDocument.mockResolvedValue(undefined);
}

export function cleanupAppTest() {
  cleanup();
  vi.useRealTimers();
  vi.restoreAllMocks();
  vi.clearAllMocks();
}
