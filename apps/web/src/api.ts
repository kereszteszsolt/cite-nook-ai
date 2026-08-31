/*
 * SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
 * SPDX-License-Identifier: Apache-2.0
 */

import type {
  AnswerTurn,
  Conversation,
  ConversationMessage,
  DocumentRecord,
  ModelCatalog,
} from './types';

export const API_URL = (import.meta.env.VITE_API_URL ?? '/api').replace(/\/+$/, '');
export const API_CONNECTION_ERROR_MESSAGE =
  'CiteNook could not reach its API. Check that the Docker services are running, then retry.';
export const ANSWER_REQUEST_TIMEOUT_MS = 620_000;
export const ANSWER_TIMEOUT_MESSAGE =
  'CiteNook stopped waiting for the answer. Check Ollama, then try again.';

export interface HealthResponse {
  status: string;
  appId: string;
  ragBackend: 'native' | 'llamaindex';
}

export async function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/health');
}

async function request<T>(
  path: string,
  init?: RequestInit,
  timeout?: { milliseconds: number; message: string },
): Promise<T> {
  const url = `${API_URL}${path}`;
  const controller = timeout ? new AbortController() : null;
  const timer = timeout
    ? setTimeout(() => controller?.abort(), timeout.milliseconds)
    : null;
  const requestInit = init
    ? {
        ...init,
        ...(controller ? { signal: controller.signal } : {}),
        headers: {
          ...(init.body && !(init.body instanceof FormData)
            ? { 'Content-Type': 'application/json' }
            : {}),
          ...init.headers,
        },
      }
    : null;
  let response: Response;
  try {
    response = requestInit ? await fetch(url, requestInit) : await fetch(url);
  } catch (cause) {
    if (controller?.signal.aborted && timeout) throw new Error(timeout.message, { cause });
    throw new Error(API_CONNECTION_ERROR_MESSAGE, { cause });
  } finally {
    if (timer !== null) clearTimeout(timer);
  }
  if (!response.ok) {
    let message =
      response.status === 502 || response.status === 503 || response.status === 504
        ? API_CONNECTION_ERROR_MESSAGE
        : `Request failed with status ${response.status}.`;
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) message = payload.detail;
    } catch {
      // Keep the status-based fallback for non-JSON errors.
    }
    throw new Error(message);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const api = {
  models: () => request<ModelCatalog>('/models'),
  conversations: () => request<Conversation[]>('/conversations'),
  messages: (conversationId: string) =>
    request<ConversationMessage[]>(
      `/conversations/${encodeURIComponent(conversationId)}/messages`,
    ),
  askQuestion: (conversationId: string, question: string) =>
    request<AnswerTurn>(
      `/conversations/${encodeURIComponent(conversationId)}/messages`,
      {
        method: 'POST',
        body: JSON.stringify({ question }),
      },
      {
        milliseconds: ANSWER_REQUEST_TIMEOUT_MS,
        message: ANSWER_TIMEOUT_MESSAGE,
      },
    ),
  documents: () => request<DocumentRecord[]>('/documents'),
  createConversation: (chatModel: string, embeddingModel: string) =>
    request<Conversation>('/conversations', {
      method: 'POST',
      body: JSON.stringify({ chatModel, embeddingModel }),
    }),
  updateConversation: (id: string, chatModel: string, embeddingModel: string) =>
    request<Conversation>(`/conversations/${encodeURIComponent(id)}`, {
      method: 'PATCH',
      body: JSON.stringify({ chatModel, embeddingModel }),
    }),
  updateConversationTitle: (id: string, title: string) =>
    request<Conversation>(`/conversations/${encodeURIComponent(id)}`, {
      method: 'PATCH',
      body: JSON.stringify({ title }),
    }),
  deleteConversation: (id: string) =>
    request<void>(`/conversations/${encodeURIComponent(id)}`, { method: 'DELETE' }),
  uploadDocument: (file: File, embeddingModel: string) => {
    const body = new FormData();
    body.append('file', file);
    body.append('embedding_model', embeddingModel);
    return request<DocumentRecord>('/documents', { method: 'POST', body });
  },
  documentFileUrl: (id: string) => `${API_URL}/documents/${encodeURIComponent(id)}/file`,
  updateDocument: (id: string, isActive: boolean) =>
    request<DocumentRecord>(`/documents/${encodeURIComponent(id)}`, {
      method: 'PATCH',
      body: JSON.stringify({ isActive }),
    }),
  deleteDocument: (id: string) =>
    request<void>(`/documents/${encodeURIComponent(id)}`, { method: 'DELETE' }),
};
