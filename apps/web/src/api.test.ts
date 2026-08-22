/*
 * SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
 * SPDX-License-Identifier: Apache-2.0
 */

import { afterEach, describe, expect, it, vi } from 'vitest';
import { getHealth } from './api';

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
});
