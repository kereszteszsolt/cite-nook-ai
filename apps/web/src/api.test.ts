/*
 * SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
 * SPDX-License-Identifier: Apache-2.0
 */

import { afterEach, describe, expect, it, vi } from 'vitest';
import { API_CONNECTION_ERROR_MESSAGE, api, getHealth } from './api';

describe('API client', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('loads health through the configured API boundary', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ status: 'ok', appId: 'cite-nook-ai' })),
    );
    vi.stubGlobal('fetch', fetchMock);

    await expect(getHealth()).resolves.toEqual({ status: 'ok', appId: 'cite-nook-ai' });
    expect(fetchMock).toHaveBeenCalledWith('/api/health');
  });

  it('normalizes browser network failures into an actionable API error', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')));

    await expect(getHealth()).rejects.toThrow(API_CONNECTION_ERROR_MESSAGE);
  });

  it('normalizes unavailable proxy responses into the same actionable error', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(null, { status: 502 })));

    await expect(getHealth()).rejects.toThrow(API_CONNECTION_ERROR_MESSAGE);
  });

  it('uploads multipart data without overriding its content type boundary', async () => {
    const payload = {
      id: 'document-1',
      fileName: 'notes.md',
      contentType: 'text/markdown',
      sizeBytes: 7,
      sha256: 'abc123',
      embeddingModel: 'embed-a',
      status: 'queued',
      errorMessage: null,
      chunkCount: 0,
      isActive: true,
      createdAt: '2026-08-22T00:00:00Z',
    };
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(payload)));
    vi.stubGlobal('fetch', fetchMock);
    const file = new File(['content'], 'notes.md', { type: 'text/markdown' });

    await expect(api.uploadDocument(file, 'embed-a')).resolves.toEqual(payload);

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe('/api/documents');
    expect(init.method).toBe('POST');
    expect(init.headers).toEqual({});
    expect(init.body).toBeInstanceOf(FormData);
    expect((init.body as FormData).get('embedding_model')).toBe('embed-a');
    expect((init.body as FormData).get('file')).toBe(file);
  });

  it('lists documents and deletes without parsing a 204 response body', async () => {
    const documents = [{ id: 'document-1', fileName: 'notes.md' }];
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(new Response(JSON.stringify(documents)))
      .mockResolvedValueOnce(new Response(null, { status: 204 }));
    vi.stubGlobal('fetch', fetchMock);

    await expect(api.documents()).resolves.toEqual(documents);
    await expect(api.deleteDocument('document-1')).resolves.toBeUndefined();

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      '/api/documents',
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      '/api/documents/document-1',
      { method: 'DELETE', headers: {} },
    );
    expect(api.documentFileUrl('document-1')).toBe(
      '/api/documents/document-1/file',
    );
  });

  it('updates whether a document participates in answers', async () => {
    const updated = { id: 'document/1', fileName: 'notes.md', isActive: false };
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(updated)));
    vi.stubGlobal('fetch', fetchMock);

    await expect(api.updateDocument('document/1', false)).resolves.toEqual(updated);
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/documents/document%2F1',
      {
        method: 'PATCH',
        body: JSON.stringify({ isActive: false }),
        headers: { 'Content-Type': 'application/json' },
      },
    );
  });

  it('loads conversation messages and deletes a conversation', async () => {
    const messages = [{ id: 'message-1', role: 'user', content: 'Question' }];
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(new Response(JSON.stringify(messages)))
      .mockResolvedValueOnce(new Response(null, { status: 204 }));
    vi.stubGlobal('fetch', fetchMock);

    await expect(api.messages('conversation-1')).resolves.toEqual(messages);
    await expect(api.deleteConversation('conversation-1')).resolves.toBeUndefined();

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      '/api/conversations/conversation-1/messages',
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      '/api/conversations/conversation-1',
      { method: 'DELETE', headers: {} },
    );
  });

  it('creates and updates a conversation with an explicit model pair', async () => {
    const created = {
      id: 'conversation/1',
      chatModel: 'chat-a',
      embeddingModel: 'embed-a',
    };
    const updated = {
      ...created,
      chatModel: 'chat-b',
      embeddingModel: 'embed-b',
    };
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(new Response(JSON.stringify(created)))
      .mockResolvedValueOnce(new Response(JSON.stringify(updated)));
    vi.stubGlobal('fetch', fetchMock);

    await expect(api.createConversation('chat-a', 'embed-a')).resolves.toEqual(created);
    await expect(
      api.updateConversation('conversation/1', 'chat-b', 'embed-b'),
    ).resolves.toEqual(updated);

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      '/api/conversations',
      {
        method: 'POST',
        body: JSON.stringify({ chatModel: 'chat-a', embeddingModel: 'embed-a' }),
        headers: { 'Content-Type': 'application/json' },
      },
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      '/api/conversations/conversation%2F1',
      {
        method: 'PATCH',
        body: JSON.stringify({ chatModel: 'chat-b', embeddingModel: 'embed-b' }),
        headers: { 'Content-Type': 'application/json' },
      },
    );
  });

  it('updates a conversation title without resending model selections', async () => {
    const updated = { id: 'conversation/1', title: 'Project sources' };
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(updated)));
    vi.stubGlobal('fetch', fetchMock);

    await expect(
      api.updateConversationTitle('conversation/1', 'Project sources'),
    ).resolves.toEqual(updated);
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/conversations/conversation%2F1',
      {
        method: 'PATCH',
        body: JSON.stringify({ title: 'Project sources' }),
        headers: { 'Content-Type': 'application/json' },
      },
    );
  });

  it('posts a question through the conversation message boundary', async () => {
    const turn = {
      conversation: { id: 'conversation-1' },
      userMessage: { id: 'message-1', role: 'user' },
      assistantMessage: { id: 'message-2', role: 'assistant' },
    };
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(turn)));
    vi.stubGlobal('fetch', fetchMock);

    await expect(api.askQuestion('conversation-1', 'Grounded question?')).resolves.toEqual(
      turn,
    );
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/conversations/conversation-1/messages',
      {
        method: 'POST',
        body: JSON.stringify({ question: 'Grounded question?' }),
        headers: { 'Content-Type': 'application/json' },
      },
    );
  });
});
