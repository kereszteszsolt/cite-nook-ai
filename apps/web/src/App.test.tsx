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
  messages: vi.fn(),
  askQuestion: vi.fn(),
  documents: vi.fn(),
  createConversation: vi.fn(),
  updateConversation: vi.fn(),
  deleteConversation: vi.fn(),
  uploadDocument: vi.fn(),
  documentFileUrl: vi.fn(),
  updateDocument: vi.fn(),
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
  isActive: true,
  createdAt: '2026-08-22T00:00:00Z',
};

const storedMessages = [
  {
    id: 'message-1',
    conversationId: 'conversation-1',
    ordinal: 1,
    role: 'user',
    content: 'What does the document say?',
    chatModel: null,
    citations: [],
    createdAt: '2026-08-22T00:01:00Z',
  },
  {
    id: 'message-2',
    conversationId: 'conversation-1',
    ordinal: 2,
    role: 'assistant',
    content: 'The persisted answer.',
    chatModel: 'qwen3.5:9b',
    citations: [
      {
        sourceId: 'S1',
        documentId: 'document-1',
        documentName: 'notes.md',
        pageNumber: 2,
        chunkId: 'chunk-1',
        snippet: 'Relevant text',
        score: 0.91,
      },
    ],
    createdAt: '2026-08-22T00:01:01Z',
  },
];

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
  apiMock.messages.mockResolvedValue([]);
  apiMock.askQuestion.mockResolvedValue({
    conversation: { ...storedConversation, title: 'What does the document say?' },
    userMessage: storedMessages[0],
    assistantMessage: storedMessages[1],
  });
  apiMock.documents.mockResolvedValue([]);
  apiMock.updateConversation.mockImplementation(
    (_id: string, chatModel: string, embeddingModel: string) =>
      Promise.resolve({ ...storedConversation, chatModel, embeddingModel }),
  );
  apiMock.deleteConversation.mockResolvedValue(undefined);
  apiMock.uploadDocument.mockResolvedValue({
    ...readyDocument,
    sizeBytes: 7,
    status: 'queued',
    chunkCount: 0,
  });
  apiMock.documentFileUrl.mockImplementation(
    (id: string) => `http://localhost:8000/api/documents/${id}/file`,
  );
  apiMock.updateDocument.mockImplementation((_id: string, isActive: boolean) =>
    Promise.resolve({ ...readyDocument, isActive }),
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

    fireEvent.click(await screen.findByRole('tab', { name: 'Documents' }));
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

describe('persistent conversation history', () => {
  it('reloads the selected conversation and all stored messages', async () => {
    apiMock.messages.mockResolvedValue(storedMessages);

    render(<App />);

    expect(await screen.findByText('What does the document say?')).toBeDefined();
    expect(screen.getByText('The persisted answer.')).toBeDefined();
    expect(screen.getAllByText('qwen3.5:9b').length).toBeGreaterThan(0);
    expect(screen.getByRole('heading', { name: 'References' })).toBeDefined();
    expect(screen.getByText('Relevant text')).toBeDefined();
    expect(screen.getByText('Similarity 91.0%')).toBeDefined();
    expect(
      screen.getByRole('link', { name: /\[S1\] notes.md — page 2/ }).getAttribute('href'),
    ).toBe('http://localhost:8000/api/documents/document-1/file');
    expect(apiMock.messages).toHaveBeenCalledWith('conversation-1');
  });

  it('asks a grounded question and renders the returned linked references', async () => {
    render(<App />);

    const input = (await screen.findByLabelText('Ask your documents')) as HTMLTextAreaElement;
    fireEvent.change(input, { target: { value: 'What does the document say?' } });
    fireEvent.click(screen.getByRole('button', { name: 'Ask' }));

    await waitFor(() =>
      expect(apiMock.askQuestion).toHaveBeenCalledWith(
        'conversation-1',
        'What does the document say?',
      ),
    );
    expect(await screen.findByText('The persisted answer.')).toBeDefined();
    expect(screen.getByRole('link', { name: /\[S1\] notes.md/ })).toBeDefined();
    expect(input.value).toBe('');
  });

  it('deletes a confirmed conversation from the persistent list', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    render(<App />);

    await screen.findByRole('button', { name: 'Delete conversation' });
    fireEvent.click(screen.getByRole('button', { name: 'Delete conversation' }));

    await waitFor(() =>
      expect(apiMock.deleteConversation).toHaveBeenCalledWith('conversation-1'),
    );
    expect(await screen.findByText('No conversations yet.')).toBeDefined();
    expect(screen.getByText('Create or select a conversation to view its history.')).toBeDefined();
  });
});

describe('document status and management', () => {
  it('keeps document management out of Chat and exposes it on the Documents tab', async () => {
    apiMock.documents.mockResolvedValue([readyDocument]);
    render(<App />);

    await screen.findByRole('tab', { name: 'Documents' });
    expect(screen.queryByLabelText('Document file')).toBeNull();
    expect(screen.queryByRole('heading', { name: 'Stored documents' })).toBeNull();

    fireEvent.click(screen.getByRole('tab', { name: 'Documents' }));

    expect(await screen.findByLabelText('Document file')).toBeDefined();
    expect(screen.getByRole('heading', { name: 'Stored documents' })).toBeDefined();
    expect(screen.getByText('notes.md')).toBeDefined();
    expect(screen.getByRole('tab', { name: 'Documents' }).getAttribute('aria-selected')).toBe(
      'true',
    );
  });

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
    fireEvent.click(await screen.findByRole('tab', { name: 'Documents' }));

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

    fireEvent.click(await screen.findByRole('tab', { name: 'Documents' }));
    await screen.findByText('notes.md');
    fireEvent.click(screen.getByRole('button', { name: 'Delete notes.md' }));

    await waitFor(() =>
      expect(apiMock.deleteDocument).toHaveBeenCalledWith('document-1'),
    );
    await waitFor(() => expect(screen.queryByText('notes.md')).toBeNull());
  });

  it('deactivates a stored document without removing its management actions', async () => {
    apiMock.documents.mockResolvedValue([readyDocument]);
    render(<App />);

    fireEvent.click(await screen.findByRole('tab', { name: 'Documents' }));
    const toggle = await screen.findByRole('switch', {
      name: 'Disable notes.md for answers',
    });
    expect(toggle.getAttribute('aria-checked')).toBe('true');
    fireEvent.click(toggle);

    await waitFor(() =>
      expect(apiMock.updateDocument).toHaveBeenCalledWith('document-1', false),
    );
    const inactiveToggle = await screen.findByRole('switch', {
      name: 'Enable notes.md for answers',
    });
    expect(inactiveToggle.getAttribute('aria-checked')).toBe('false');
    expect(screen.getByRole('link', { name: 'Open' })).toBeDefined();
    expect(screen.getByRole('button', { name: 'Delete notes.md' })).toBeDefined();
  });

  it('keeps the active state and reports an update failure', async () => {
    apiMock.documents.mockResolvedValue([readyDocument]);
    apiMock.updateDocument.mockRejectedValue(new Error('Document update failed.'));
    render(<App />);

    fireEvent.click(await screen.findByRole('tab', { name: 'Documents' }));
    fireEvent.click(
      await screen.findByRole('switch', { name: 'Disable notes.md for answers' }),
    );

    expect((await screen.findByRole('alert')).textContent).toContain(
      'Document update failed.',
    );
    expect(
      screen.getByRole('switch', { name: 'Disable notes.md for answers' }).getAttribute(
        'aria-checked',
      ),
    ).toBe('true');
  });
});
