/*
 * SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
 * SPDX-License-Identifier: Apache-2.0
 */

// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import App from './App';

const apiMock = vi.hoisted(() => ({
  models: vi.fn(),
  conversations: vi.fn(),
  createConversation: vi.fn(),
  updateConversation: vi.fn(),
  uploadDocument: vi.fn(),
}));

vi.mock('./api', () => ({ api: apiMock }));

const storedConversation = {
  id: 'conversation-1',
  title: 'New conversation',
  chatModel: 'qwen3.5:9b',
  embeddingModel: 'qwen3-embedding:0.6b',
  createdAt: '2026-08-22T00:00:00Z',
  updatedAt: '2026-08-22T00:00:00Z',
};

beforeEach(() => {
  apiMock.models.mockResolvedValue({
    chatModels: [
      { name: 'llama3.1:8b', installed: true },
      { name: 'qwen3.5:9b', installed: true },
      { name: 'missing-chat', installed: false },
    ],
    embeddingModels: [
      { name: 'qwen3-embedding:0.6b', installed: true },
      { name: 'embeddinggemma', installed: false },
    ],
    defaultChatModel: 'llama3.1:8b',
    defaultEmbeddingModel: 'qwen3-embedding:0.6b',
    ollamaAvailable: true,
  });
  apiMock.conversations.mockResolvedValue([storedConversation]);
  apiMock.updateConversation.mockImplementation(
    (_id: string, chatModel: string, embeddingModel: string) =>
      Promise.resolve({ ...storedConversation, chatModel, embeddingModel }),
  );
  apiMock.uploadDocument.mockResolvedValue({
    id: 'document-1',
    fileName: 'notes.md',
    contentType: 'text/markdown',
    sizeBytes: 7,
    sha256: 'abc123',
    embeddingModel: 'qwen3-embedding:0.6b',
  });
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe('conversation model selection', () => {
  it('restores the stored models when an existing conversation opens', async () => {
    render(<App />);

    const chatSelect = (await screen.findByLabelText('Chat model')) as HTMLSelectElement;
    await waitFor(() => expect(chatSelect.value).toBe('qwen3.5:9b'));
    expect((screen.getByLabelText('Embedding model') as HTMLSelectElement).value).toBe(
      'qwen3-embedding:0.6b',
    );
  });

  it('persists selector changes on the active conversation', async () => {
    render(<App />);

    const chatSelect = (await screen.findByLabelText('Chat model')) as HTMLSelectElement;
    await waitFor(() => expect(chatSelect.value).toBe('qwen3.5:9b'));
    fireEvent.change(chatSelect, { target: { value: 'llama3.1:8b' } });

    await waitFor(() =>
      expect(apiMock.updateConversation).toHaveBeenCalledWith(
        'conversation-1',
        'llama3.1:8b',
        'qwen3-embedding:0.6b',
      ),
    );
  });

  it('uploads a supported file with the selected embedding model', async () => {
    render(<App />);

    const fileInput = (await screen.findByLabelText('Document file')) as HTMLInputElement;
    await waitFor(() => expect(fileInput.disabled).toBe(false));
    const file = new File(['content'], 'notes.md', { type: 'text/markdown' });
    fireEvent.change(fileInput, { target: { files: [file] } });
    fireEvent.click(screen.getByRole('button', { name: 'Upload' }));

    await waitFor(() =>
      expect(apiMock.uploadDocument).toHaveBeenCalledWith(
        file,
        'qwen3-embedding:0.6b',
      ),
    );
    expect(await screen.findByText(/was stored successfully/)).toBeDefined();
  });
});
