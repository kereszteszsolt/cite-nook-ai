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
  it('shows branding and a connected status pill without model controls', () => {
    render(<Header loading={false} ollamaAvailable />);

    expect(screen.getByText('CiteNook')).toBeDefined();
    expect(screen.getByText('Local document Q&A with citations')).toBeDefined();
    const status = screen.getByRole('status');
    expect(status.textContent).toBe('Ollama connected');
    expect(status.classList.contains('ready')).toBe(true);
    expect(screen.queryByRole('combobox')).toBeNull();
    expect(screen.queryByText('Model configuration')).toBeNull();
  });

  it('keeps unavailable and checking states text-labelled and separately styled', () => {
    const { rerender } = render(<Header loading={false} ollamaAvailable={false} />);

    let status = screen.getByRole('status');
    expect(status.textContent).toBe('Ollama unavailable');
    expect(status.classList.contains('unavailable')).toBe(true);

    rerender(<Header loading ollamaAvailable={null} />);
    status = screen.getByRole('status');
    expect(status.textContent).toBe('Checking Ollama');
    expect(status.classList.contains('checking')).toBe(true);

    rerender(<Header loading={false} ollamaAvailable={null} />);
    status = screen.getByRole('status');
    expect(status.textContent).toBe('CiteNook API unavailable');
    expect(status.classList.contains('unavailable')).toBe(true);
  });
});
