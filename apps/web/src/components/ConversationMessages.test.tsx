/*
 * SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
 * SPDX-License-Identifier: Apache-2.0
 */

import { describe, expect, it } from 'vitest';
import { formatResponseDuration } from './ConversationMessages';

describe('response duration formatting', () => {
  it('formats milliseconds, seconds, minutes, and unavailable legacy values', () => {
    expect(formatResponseDuration(650)).toBe('650 ms');
    expect(formatResponseDuration(2345)).toBe('2.3 s');
    expect(formatResponseDuration(12_500)).toBe('13 s');
    expect(formatResponseDuration(65_000)).toBe('1m 5s');
    expect(formatResponseDuration(null)).toBe('—');
    expect(formatResponseDuration(undefined)).toBe('—');
  });
});
