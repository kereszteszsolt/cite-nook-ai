/*
 * SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
 * SPDX-License-Identifier: Apache-2.0
 */

import { afterEach, describe, expect, it, vi } from 'vitest';
import { api, getHealth } from './api';

describe('API client', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('loads health through the configured API boundary', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ status: 'ok', appId: 'cite-nook-ai' })),
    );
    vi.stubGlobal('fetch', fetchMock);

    await expect(getHealth()).resolves.toEqual({ status: 'ok', appId: 'cite-nook-ai' });
    expect(fetchMock).toHaveBeenCalledWith('http://localhost:8000/api/health');
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
      createdAt: '2026-08-22T00:00:00Z',
    };
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(payload)));
    vi.stubGlobal('fetch', fetchMock);
    const file = new File(['content'], 'notes.md', { type: 'text/markdown' });

    await expect(api.uploadDocument(file, 'embed-a')).resolves.toEqual(payload);

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe('http://localhost:8000/api/documents');
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
      'http://localhost:8000/api/documents',
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      'http://localhost:8000/api/documents/document-1',
      { method: 'DELETE', headers: {} },
    );
    expect(api.documentFileUrl('document-1')).toBe(
      'http://localhost:8000/api/documents/document-1/file',
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
      'http://localhost:8000/api/conversations/conversation-1/messages',
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      'http://localhost:8000/api/conversations/conversation-1',
      { method: 'DELETE', headers: {} },
    );
  });
});
