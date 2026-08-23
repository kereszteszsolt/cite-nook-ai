/*
 * SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
 * SPDX-License-Identifier: Apache-2.0
 */

import { describe, expect, it } from 'vitest';
import { brand } from './index';

describe('brand configuration', () => {
  it('contains the public and stable technical identities', () => {
    expect(brand.productName).toBe('CiteNook');
    expect(brand.extendedName).toBe('CiteNook AI');
    expect(brand.description).toBe('Local document Q&A with citations');
    expect(brand.tagline).toBe('Ask your documents. Verify the sources.');
    expect(brand.assets.favicon).toBe('/favicon.svg');
    expect(brand.technical).toEqual({
      repository: 'cite-nook-ai',
      packageScope: '@citenook/*',
      appId: 'cite-nook-ai',
      dockerProject: 'citenook',
      storyPrefix: 'MRA',
    });
  });
});
