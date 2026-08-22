/*
 * SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
 * SPDX-License-Identifier: Apache-2.0
 */

// @vitest-environment jsdom

import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import App from './App';

const apiMock = vi.hoisted(() => ({
  models: vi.fn(),
  conversations: vi.fn(),
  documents: vi.fn(),
  createConversation: vi.fn(),
  updateConversation: vi.fn(),
  uploadDocument: vi.fn(),
  documentFileUrl: vi.fn(),
  deleteDocument: vi.fn(),
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

const readyDocument = {
  id: 'document-1',
  fileName: 'notes.md',
  contentType: 'text/markdown',
  sizeBytes: 2048,
  sha256: 'abc123',
  embeddingModel: 'qwen3-embedding:0.6b',
  status: 'ready',
  errorMessage: null,
  chunkCount: 4,
  createdAt: '2026-08-22T00:00:00Z',
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
  apiMock.documents.mockResolvedValue([]);
  apiMock.updateConversation.mockImplementation(
    (_id: string, chatModel: string, embeddingModel: string) =>
      Promise.resolve({ ...storedConversation, chatModel, embeddingModel }),
  );
  apiMock.uploadDocument.mockResolvedValue({
    ...readyDocument,
    sizeBytes: 7,
    status: 'queued',
    chunkCount: 0,
  });
  apiMock.documentFileUrl.mockImplementation(
    (id: string) => `http://localhost:8000/api/documents/${id}/file`,
  );
  apiMock.deleteDocument.mockResolvedValue(undefined);
});

afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.restoreAllMocks();
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

describe('document status and management', () => {
  it('lists document metadata, opens the original, and displays bounded failures', async () => {
    apiMock.documents.mockResolvedValue([
      readyDocument,
      {
        ...readyDocument,
        id: 'document-2',
        fileName: 'broken.pdf',
        status: 'failed',
        errorMessage: 'The PDF structure is invalid.',
        chunkCount: 0,
      },
    ]);

    render(<App />);

    expect(await screen.findByText('notes.md')).toBeDefined();
    expect(screen.getAllByText('2.0 KB')).toHaveLength(2);
    expect(screen.getAllByText('qwen3-embedding:0.6b').length).toBeGreaterThan(0);
    expect(screen.getByText('4')).toBeDefined();
    expect(screen.getByText('The PDF structure is invalid.')).toBeDefined();
    const openLink = screen.getAllByRole('link', { name: 'Open' })[0];
    expect(openLink.getAttribute('href')).toBe(
      'http://localhost:8000/api/documents/document-1/file',
    );
  });

  it('polls while work is active and stops after every document is terminal', async () => {
    vi.useFakeTimers();
    apiMock.documents
      .mockResolvedValueOnce([{ ...readyDocument, status: 'queued', chunkCount: 0 }])
      .mockResolvedValueOnce([readyDocument]);

    await act(async () => {
      render(<App />);
      await Promise.resolve();
      await Promise.resolve();
    });
    expect(apiMock.documents).toHaveBeenCalledTimes(1);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000);
    });
    expect(apiMock.documents).toHaveBeenCalledTimes(2);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(6000);
    });
    expect(apiMock.documents).toHaveBeenCalledTimes(2);
  });

  it('deletes a confirmed document from the persistent list', async () => {
    apiMock.documents.mockResolvedValue([readyDocument]);
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    render(<App />);

    await screen.findByText('notes.md');
    fireEvent.click(screen.getByRole('button', { name: 'Delete notes.md' }));

    await waitFor(() =>
      expect(apiMock.deleteDocument).toHaveBeenCalledWith('document-1'),
    );
    await waitFor(() => expect(screen.queryByText('notes.md')).toBeNull());
  });
});
