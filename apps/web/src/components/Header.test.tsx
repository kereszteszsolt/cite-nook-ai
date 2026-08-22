/*
 * SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
 * SPDX-License-Identifier: Apache-2.0
 */

// @vitest-environment jsdom

import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import { Header } from './Header';

afterEach(cleanup);

describe('compact application header', () => {
  it('shows branding and connection status without model controls', () => {
    render(<Header loading={false} ollamaAvailable />);

    expect(screen.getByText('CiteNook')).toBeDefined();
    expect(screen.getByText('Local document Q&A with citations')).toBeDefined();
    expect(screen.getByRole('status').textContent).toBe('Ollama connected');
    expect(screen.queryByRole('combobox')).toBeNull();
    expect(screen.queryByText('Model configuration')).toBeNull();
  });
});
