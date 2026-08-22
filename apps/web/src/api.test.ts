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
});
