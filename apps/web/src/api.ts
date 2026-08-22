/*
 * SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Conversation, DocumentRecord, ModelCatalog } from './types';

export const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api';

export interface HealthResponse {
  status: string;
  appId: string;
}

export async function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/health');
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${API_URL}${path}`;
  const requestInit = init
    ? {
        ...init,
        headers: {
          ...(init.body && !(init.body instanceof FormData)
            ? { 'Content-Type': 'application/json' }
            : {}),
          ...init.headers,
        },
      }
    : null;
  const response = requestInit ? await fetch(url, requestInit) : await fetch(url);
  if (!response.ok) {
    let message = `Request failed with status ${response.status}.`;
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
  documents: () => request<DocumentRecord[]>('/documents'),
  createConversation: (chatModel: string, embeddingModel: string) =>
    request<Conversation>('/conversations', {
      method: 'POST',
      body: JSON.stringify({ chatModel, embeddingModel }),
    }),
  updateConversation: (id: string, chatModel: string, embeddingModel: string) =>
    request<Conversation>(`/conversations/${id}`, {
      method: 'PATCH',
      body: JSON.stringify({ chatModel, embeddingModel }),
    }),
  uploadDocument: (file: File, embeddingModel: string) => {
    const body = new FormData();
    body.append('file', file);
    body.append('embedding_model', embeddingModel);
    return request<DocumentRecord>('/documents', { method: 'POST', body });
  },
  documentFileUrl: (id: string) => `${API_URL}/documents/${encodeURIComponent(id)}/file`,
  deleteDocument: (id: string) =>
    request<void>(`/documents/${encodeURIComponent(id)}`, { method: 'DELETE' }),
};
