/*
 * SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
 * SPDX-License-Identifier: Apache-2.0
 */

// @vitest-environment jsdom

import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import App from '../App';
import {
  cleanupAppTest,
  configureAppTest,
  type AppApiMock,
} from './appTestSupport';

const apiMock = vi.hoisted<AppApiMock>(() => ({
  models: vi.fn(),
  conversations: vi.fn(),
  messages: vi.fn(),
  askQuestion: vi.fn(),
  documents: vi.fn(),
  createConversation: vi.fn(),
  updateConversation: vi.fn(),
  updateConversationTitle: vi.fn(),
  deleteConversation: vi.fn(),
  uploadDocument: vi.fn(),
  documentFileUrl: vi.fn(),
  updateDocument: vi.fn(),
  deleteDocument: vi.fn(),
}));

vi.mock('../api', () => ({ api: apiMock }));

beforeEach(() => configureAppTest(apiMock));
afterEach(() => cleanupAppTest());

describe('local API startup recovery', () => {
  it('replaces a raw fetch failure with API status and recovers through retry', async () => {
    apiMock.models.mockRejectedValueOnce(new TypeError('Failed to fetch'));
    render(<App />);

    const alert = await screen.findByRole('alert');
    expect(alert.textContent).toContain('CiteNook could not reach its API');
    expect(alert.textContent).not.toContain('Failed to fetch');
    expect(screen.getByText('CiteNook API unavailable')).toBeDefined();
    expect(screen.getByRole('button', { name: 'Retry connection' })).toBeDefined();

    fireEvent.click(screen.getByRole('button', { name: 'Retry connection' }));

    expect(await screen.findByText('Ollama connected')).toBeDefined();
    expect(screen.queryByRole('alert')).toBeNull();
    expect(apiMock.models).toHaveBeenCalledTimes(2);
    expect(apiMock.conversations).toHaveBeenCalledTimes(2);
    expect(apiMock.documents).toHaveBeenCalledTimes(2);
    await waitFor(() => expect(apiMock.messages).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(screen.queryByText('Loading messages…')).toBeNull());
    expect(
      (screen.getByRole('button', { name: 'New conversation' }) as HTMLButtonElement)
        .disabled,
    ).toBe(false);
  });
});
