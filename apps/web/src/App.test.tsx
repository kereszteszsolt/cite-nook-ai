/*
 * SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
 * SPDX-License-Identifier: Apache-2.0
 */

// @vitest-environment jsdom

import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from '@testing-library/react';
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
  updateConversationTitle: vi.fn(),
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
    responseDurationMs: null,
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
    responseDurationMs: 2345,
    createdAt: '2026-08-22T00:01:01Z',
  },
];

beforeEach(() => {
  Object.defineProperty(navigator, 'clipboard', {
    configurable: true,
    value: { writeText: vi.fn().mockResolvedValue(undefined) },
  });
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
  apiMock.createConversation.mockImplementation(
    (chatModel: string, embeddingModel: string) =>
      Promise.resolve({
        ...storedConversation,
        id: 'conversation-2',
        chatModel,
        embeddingModel,
      }),
  );
  apiMock.updateConversation.mockImplementation(
    (_id: string, chatModel: string, embeddingModel: string) =>
      Promise.resolve({ ...storedConversation, chatModel, embeddingModel }),
  );
  apiMock.updateConversationTitle.mockImplementation((_id: string, title: string) =>
    Promise.resolve({ ...storedConversation, title }),
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
  it('shows the stored model pair in the conversation header and nowhere in the app header', async () => {
    render(<App />);

    const modelSummary = await screen.findByLabelText('Conversation models');
    expect(within(modelSummary).getByText('qwen3.5:9b')).toBeDefined();
    expect(within(modelSummary).getByText('qwen3-embedding:0.6b')).toBeDefined();
    expect(screen.queryByRole('combobox')).toBeNull();
    expect(screen.queryByText('Model configuration')).toBeNull();
    expect(screen.queryByText('Saved messages')).toBeNull();
  });

  it('asks for both models before creating a conversation and preselects available defaults', async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole('button', { name: 'New conversation' }));
    const dialog = screen.getByRole('dialog', { name: 'Start a new conversation' });
    const chatSelect = within(dialog).getByLabelText('Chat model') as HTMLSelectElement;
    const embeddingSelect = within(dialog).getByLabelText(
      'Embedding model',
    ) as HTMLSelectElement;

    expect(chatSelect.value).toBe('llama3.1:8b');
    expect(embeddingSelect.value).toBe('qwen3-embedding:0.6b');
    expect(apiMock.createConversation).not.toHaveBeenCalled();
    fireEvent.click(within(dialog).getByRole('button', { name: 'Create conversation' }));

    await waitFor(() =>
      expect(apiMock.createConversation).toHaveBeenCalledWith(
        'llama3.1:8b',
        'qwen3-embedding:0.6b',
      ),
    );
    expect(screen.queryByRole('dialog', { name: 'Start a new conversation' })).toBeNull();
    expect(
      within(screen.getByLabelText('Conversation models')).getByText('llama3.1:8b'),
    ).toBeDefined();
  });

  it('falls back to the first installed models when configured defaults are unavailable', async () => {
    apiMock.models.mockResolvedValue({
      chatModels: [
        { name: 'llama3.1:8b', installed: false },
        { name: 'qwen3.5:9b', installed: true },
      ],
      embeddingModels: [
        { name: 'qwen3-embedding:0.6b', installed: false },
        { name: 'embeddinggemma', installed: true },
      ],
      defaultChatModel: 'llama3.1:8b',
      defaultEmbeddingModel: 'qwen3-embedding:0.6b',
      ollamaAvailable: true,
    });
    render(<App />);

    fireEvent.click(await screen.findByRole('button', { name: 'New conversation' }));
    const dialog = screen.getByRole('dialog', { name: 'Start a new conversation' });
    expect((within(dialog).getByLabelText('Chat model') as HTMLSelectElement).value).toBe(
      'qwen3.5:9b',
    );
    expect((within(dialog).getByLabelText('Embedding model') as HTMLSelectElement).value).toBe(
      'embeddinggemma',
    );
  });

  it('persists both edited models on the active conversation', async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole('button', { name: 'Edit models' }));
    const dialog = screen.getByRole('dialog', { name: 'Change conversation models' });
    const chatSelect = within(dialog).getByLabelText('Chat model');
    fireEvent.change(chatSelect, { target: { value: 'llama3.1:8b' } });
    fireEvent.click(within(dialog).getByRole('button', { name: 'Save models' }));

    await waitFor(() =>
      expect(apiMock.updateConversation).toHaveBeenCalledWith(
        'conversation-1',
        'llama3.1:8b',
        'qwen3-embedding:0.6b',
      ),
    );
    expect(screen.queryByRole('dialog', { name: 'Change conversation models' })).toBeNull();
    expect(
      within(screen.getByLabelText('Conversation models')).getByText('llama3.1:8b'),
    ).toBeDefined();
  });

  it('cancels model editing without persisting changes', async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole('button', { name: 'Edit models' }));
    const dialog = screen.getByRole('dialog', { name: 'Change conversation models' });
    fireEvent.change(within(dialog).getByLabelText('Chat model'), {
      target: { value: 'llama3.1:8b' },
    });
    fireEvent.click(within(dialog).getByRole('button', { name: 'Cancel' }));

    expect(apiMock.updateConversation).not.toHaveBeenCalled();
    expect(screen.queryByRole('dialog', { name: 'Change conversation models' })).toBeNull();
  });

  it('keeps the model editor open and the stored pair visible after a failed update', async () => {
    apiMock.updateConversation.mockRejectedValue(new Error('Model update failed.'));
    render(<App />);

    fireEvent.click(await screen.findByRole('button', { name: 'Edit models' }));
    const dialog = screen.getByRole('dialog', { name: 'Change conversation models' });
    fireEvent.change(within(dialog).getByLabelText('Chat model'), {
      target: { value: 'llama3.1:8b' },
    });
    fireEvent.click(within(dialog).getByRole('button', { name: 'Save models' }));

    expect((await screen.findByRole('alert')).textContent).toContain('Model update failed.');
    expect(screen.getByRole('dialog', { name: 'Change conversation models' })).toBeDefined();
    expect(
      within(screen.getByLabelText('Conversation models')).getByText('qwen3.5:9b'),
    ).toBeDefined();
  });

  it('keeps creation disabled when no installed model pair is available', async () => {
    apiMock.models.mockResolvedValue({
      chatModels: [{ name: 'missing-chat', installed: false }],
      embeddingModels: [{ name: 'missing-embedding', installed: false }],
      defaultChatModel: 'missing-chat',
      defaultEmbeddingModel: 'missing-embedding',
      ollamaAvailable: true,
    });
    apiMock.conversations.mockResolvedValue([]);
    render(<App />);

    fireEvent.click(await screen.findByRole('button', { name: 'New conversation' }));
    const dialog = screen.getByRole('dialog', { name: 'Start a new conversation' });
    expect((within(dialog).getByLabelText('Chat model') as HTMLSelectElement).value).toBe('');
    expect((within(dialog).getByLabelText('Embedding model') as HTMLSelectElement).value).toBe(
      '',
    );
    expect(
      (within(dialog).getByRole('button', {
        name: 'Create conversation',
      }) as HTMLButtonElement).disabled,
    ).toBe(true);
    expect(within(dialog).getByRole('status').textContent).toContain('required');

    fireEvent.click(within(dialog).getByRole('button', { name: 'Cancel' }));
    fireEvent.click(screen.getByRole('tab', { name: 'Documents' }));
    const fileInput = (await screen.findByLabelText('Document file')) as HTMLInputElement;
    expect(fileInput.disabled).toBe(true);
    expect(screen.getByText('Choose file').closest('label')?.getAttribute('aria-disabled')).toBe(
      'true',
    );
    expect((screen.getByRole('button', { name: 'Upload' }) as HTMLButtonElement).disabled).toBe(
      true,
    );
  });

  it('uploads a supported file with the selected embedding model', async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole('tab', { name: 'Documents' }));
    const fileInput = (await screen.findByLabelText('Document file')) as HTMLInputElement;
    await waitFor(() => expect(fileInput.disabled).toBe(false));
    expect(screen.getByText('Choose file')).toBeDefined();
    expect(screen.getByText('No file selected')).toBeDefined();
    const file = new File(['content'], 'notes.md', { type: 'text/markdown' });
    fireEvent.change(fileInput, { target: { files: [file] } });
    expect(screen.getByText('notes.md')).toBeDefined();
    fireEvent.click(screen.getByRole('button', { name: 'Upload' }));

    await waitFor(() =>
      expect(apiMock.uploadDocument).toHaveBeenCalledWith(
        file,
        'qwen3-embedding:0.6b',
      ),
    );
    expect(await screen.findByText(/was stored successfully/)).toBeDefined();
    expect(screen.getByText('No file selected')).toBeDefined();
    expect(fileInput.value).toBe('');
  });
});

describe('persistent conversation history', () => {
  it('edits a conversation title and updates the header and sidebar', async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole('button', { name: 'Edit conversation title' }));
    const titleInput = screen.getByLabelText('Conversation title') as HTMLInputElement;
    fireEvent.change(titleInput, { target: { value: 'Project sources' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save title' }));

    await waitFor(() =>
      expect(apiMock.updateConversationTitle).toHaveBeenCalledWith(
        'conversation-1',
        'Project sources',
      ),
    );
    expect(await screen.findAllByText('Project sources')).toHaveLength(2);
  });

  it('cancels title editing without changing the stored title', async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole('button', { name: 'Edit conversation title' }));
    fireEvent.change(await screen.findByLabelText('Conversation title'), {
      target: { value: 'Discard this title' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));

    expect(apiMock.updateConversationTitle).not.toHaveBeenCalled();
    expect(screen.getByRole('heading', { name: 'New conversation' })).toBeDefined();
    expect(
      within(screen.getByRole('complementary', { name: 'Conversations' })).getByText(
        'New conversation',
        { selector: 'strong' },
      ),
    ).toBeDefined();
  });

  it('disables title controls while the update is being saved', async () => {
    let resolveUpdate: (() => void) | undefined;
    apiMock.updateConversationTitle.mockImplementation(
      (_id: string, title: string) =>
        new Promise((resolve) => {
          resolveUpdate = () => resolve({ ...storedConversation, title });
        }),
    );
    render(<App />);

    fireEvent.click(await screen.findByRole('button', { name: 'Edit conversation title' }));
    const titleInput = screen.getByLabelText('Conversation title') as HTMLInputElement;
    fireEvent.change(titleInput, { target: { value: 'Saving title' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save title' }));

    expect(await screen.findByRole('button', { name: 'Saving…' })).toBeDefined();
    expect(titleInput.disabled).toBe(true);
    expect((screen.getByRole('button', { name: 'Cancel' }) as HTMLButtonElement).disabled).toBe(
      true,
    );

    await act(async () => resolveUpdate?.());
    expect(await screen.findAllByText('Saving title')).toHaveLength(2);
  });

  it('keeps title editing open and reports a failed update', async () => {
    apiMock.updateConversationTitle.mockRejectedValue(new Error('Title update failed.'));
    render(<App />);

    fireEvent.click(await screen.findByRole('button', { name: 'Edit conversation title' }));
    fireEvent.change(screen.getByLabelText('Conversation title'), {
      target: { value: 'Retry this title' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Save title' }));

    expect((await screen.findByRole('alert')).textContent).toContain(
      'Title update failed.',
    );
    expect((screen.getByLabelText('Conversation title') as HTMLInputElement).value).toBe(
      'Retry this title',
    );
    expect(
      within(screen.getByRole('complementary', { name: 'Conversations' })).getByText(
        'New conversation',
        { selector: 'strong' },
      ),
    ).toBeDefined();
  });

  it('reloads the selected conversation and all stored messages', async () => {
    apiMock.messages.mockResolvedValue(storedMessages);

    render(<App />);

    expect(await screen.findByText('What does the document say?')).toBeDefined();
    expect(screen.getByText('The persisted answer.')).toBeDefined();
    expect(screen.getAllByText('qwen3.5:9b').length).toBeGreaterThan(0);
    expect(screen.getByRole('heading', { name: 'References' })).toBeDefined();
    expect(screen.getByText('Relevant text')).toBeDefined();
    expect(screen.getByText('Similarity 91.0%')).toBeDefined();
    expect(screen.getByRole('button', { name: 'Copy message 1' })).toBeDefined();
    expect(screen.getByRole('button', { name: 'Copy message 2' })).toBeDefined();
    expect(
      screen.getByRole('button', { name: 'Ask question again for answer 2' }),
    ).toBeDefined();
    expect(screen.getByLabelText('Response time 2.3 s')).toBeDefined();
    expect(
      screen.getByRole('link', { name: /\[S1\] notes.md — page 2/ }).getAttribute('href'),
    ).toBe('http://localhost:8000/api/documents/document-1/file');
    expect(apiMock.messages).toHaveBeenCalledWith('conversation-1');
  });

  it('copies complete message text and reports clipboard success', async () => {
    apiMock.messages.mockResolvedValue(storedMessages);
    render(<App />);

    fireEvent.click(await screen.findByRole('button', { name: 'Copy message 2' }));

    await waitFor(() =>
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
        'The persisted answer.',
      ),
    );
    expect(await screen.findByText('Message 2 copied to the clipboard.')).toBeDefined();
    expect(screen.getByRole('button', { name: 'Copied message 2' })).toBeDefined();
    expect(screen.getByText('The persisted answer.')).toBeDefined();
  });

  it('reports clipboard failure without changing the message', async () => {
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: { writeText: vi.fn().mockRejectedValue(new Error('Denied')) },
    });
    apiMock.messages.mockResolvedValue(storedMessages);
    render(<App />);

    fireEvent.click(await screen.findByRole('button', { name: 'Copy message 1' }));

    expect(
      await screen.findByText(
        'Message 1 could not be copied. Check clipboard permission and try again.',
      ),
    ).toBeDefined();
    expect(screen.getByText('What does the document say?')).toBeDefined();
  });

  it('asks an assistant question again and appends the successful turn', async () => {
    let resolveRetry: ((turn: unknown) => void) | undefined;
    apiMock.messages.mockResolvedValue(storedMessages);
    apiMock.askQuestion.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveRetry = resolve;
        }),
    );
    render(<App />);

    fireEvent.click(
      await screen.findByRole('button', { name: 'Ask question again for answer 2' }),
    );

    await waitFor(() =>
      expect(apiMock.askQuestion).toHaveBeenCalledWith(
        'conversation-1',
        'What does the document say?',
      ),
    );
    const retrying = screen.getByRole('button', {
      name: 'Asking question again for answer 2',
    }) as HTMLButtonElement;
    expect(retrying.disabled).toBe(true);
    expect((screen.getByLabelText('Ask your documents') as HTMLTextAreaElement).disabled).toBe(
      true,
    );

    await act(async () =>
      resolveRetry?.({
        conversation: { ...storedConversation, title: 'What does the document say?' },
        userMessage: {
          ...storedMessages[0],
          id: 'message-3',
          ordinal: 3,
        },
        assistantMessage: {
          ...storedMessages[1],
          id: 'message-4',
          ordinal: 4,
          content: 'A newly grounded answer.',
          responseDurationMs: 980,
        },
      }),
    );

    expect(await screen.findByText('A newly grounded answer.')).toBeDefined();
    expect(
      within(screen.getByLabelText('Conversation messages')).getAllByText(
        'What does the document say?',
      ),
    ).toHaveLength(2);
    expect(screen.getByText('The persisted answer.')).toBeDefined();
    expect(screen.getByLabelText('Response time 980 ms')).toBeDefined();
    expect(
      screen.getByText('The question was asked again and a new answer was added.'),
    ).toBeDefined();
  });

  it('preserves existing history when asking again fails', async () => {
    apiMock.messages.mockResolvedValue(storedMessages);
    apiMock.askQuestion.mockRejectedValue(new Error('Retry failed.'));
    render(<App />);

    fireEvent.click(
      await screen.findByRole('button', { name: 'Ask question again for answer 2' }),
    );

    expect((await screen.findByRole('alert')).textContent).toContain('Retry failed.');
    expect(
      await screen.findByText(
        'The question could not be asked again. The existing history was preserved.',
      ),
    ).toBeDefined();
    expect(screen.getAllByText('What does the document say?')).toHaveLength(1);
    expect(screen.getAllByText('The persisted answer.')).toHaveLength(1);
  });

  it('keeps legacy assistant responses explicit when timing is unavailable', async () => {
    apiMock.messages.mockResolvedValue([
      storedMessages[0],
      { ...storedMessages[1], responseDurationMs: null },
    ]);
    render(<App />);

    expect(await screen.findByLabelText('Response time unavailable')).toBeDefined();
  });

  it('asks a grounded question and renders the returned linked references', async () => {
    render(<App />);

    const input = (await screen.findByLabelText('Ask your documents')) as HTMLTextAreaElement;
    fireEvent.change(input, { target: { value: 'What does the document say?' } });
    const sendButton = screen.getByRole('button', { name: 'Send question' });
    expect(sendButton.querySelector('svg')).not.toBeNull();
    fireEvent.click(sendButton);

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

  it('sends with Enter but keeps Shift+Enter available for a new line', async () => {
    render(<App />);

    const input = (await screen.findByLabelText('Ask your documents')) as HTMLTextAreaElement;
    fireEvent.change(input, { target: { value: 'First line' } });
    fireEvent.keyDown(input, { key: 'Enter', shiftKey: true });
    expect(apiMock.askQuestion).not.toHaveBeenCalled();

    fireEvent.keyDown(input, { key: 'Enter' });
    await waitFor(() =>
      expect(apiMock.askQuestion).toHaveBeenCalledWith('conversation-1', 'First line'),
    );
  });

  it('bounds long input, scrolls internally, and collapses after a successful send', async () => {
    render(<App />);

    const input = (await screen.findByLabelText('Ask your documents')) as HTMLTextAreaElement;
    await waitFor(() => expect(input.style.height).toBe('48px'));
    let measuredHeight = 240;
    Object.defineProperty(input, 'scrollHeight', {
      configurable: true,
      get: () => measuredHeight,
    });
    fireEvent.change(input, { target: { value: 'A long question '.repeat(30) } });

    await waitFor(() => expect(input.style.height).toBe('160px'));
    expect(input.style.overflowY).toBe('auto');

    measuredHeight = 24;
    fireEvent.click(screen.getByRole('button', { name: 'Send question' }));
    await waitFor(() => expect(input.value).toBe(''));
    await waitFor(() => expect(input.style.height).toBe('48px'));
    expect(input.style.overflowY).toBe('hidden');
  });

  it('preserves the question when answer generation fails', async () => {
    apiMock.askQuestion.mockRejectedValue(new Error('Answer failed.'));
    render(<App />);

    const input = (await screen.findByLabelText('Ask your documents')) as HTMLTextAreaElement;
    fireEvent.change(input, { target: { value: 'Please retry this question' } });
    fireEvent.click(screen.getByRole('button', { name: 'Send question' }));

    expect((await screen.findByRole('alert')).textContent).toContain('Answer failed.');
    expect(input.value).toBe('Please retry this question');
  });

  it('deletes through the custom confirmation dialog without a browser confirm', async () => {
    let resolveDelete: (() => void) | undefined;
    apiMock.deleteConversation.mockImplementation(
      () =>
        new Promise<void>((resolve) => {
          resolveDelete = resolve;
        }),
    );
    const browserConfirm = vi.spyOn(window, 'confirm');
    render(<App />);

    const deleteButton = await screen.findByRole('button', { name: 'Delete conversation' });
    expect(deleteButton.querySelector('svg')).not.toBeNull();
    fireEvent.click(deleteButton);

    const dialog = screen.getByRole('alertdialog', { name: 'Delete conversation?' });
    expect(within(dialog).getByText(/cannot be undone/i)).toBeDefined();
    expect(apiMock.deleteConversation).not.toHaveBeenCalled();
    expect(browserConfirm).not.toHaveBeenCalled();
    fireEvent.click(within(dialog).getByRole('button', { name: 'Delete conversation' }));

    await waitFor(() =>
      expect(apiMock.deleteConversation).toHaveBeenCalledWith('conversation-1'),
    );
    const deletingButton = within(dialog).getByRole('button', { name: 'Deleting…' });
    expect((deletingButton as HTMLButtonElement).disabled).toBe(true);

    await act(async () => resolveDelete?.());
    expect(await screen.findByText('No conversations yet.')).toBeDefined();
    expect(screen.getByText('Create or select a conversation to view its history.')).toBeDefined();
  });

  it('cancels conversation deletion without calling the API', async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole('button', { name: 'Delete conversation' }));
    const dialog = screen.getByRole('alertdialog', { name: 'Delete conversation?' });
    fireEvent.click(within(dialog).getByRole('button', { name: 'Cancel' }));

    expect(apiMock.deleteConversation).not.toHaveBeenCalled();
    expect(screen.queryByRole('alertdialog', { name: 'Delete conversation?' })).toBeNull();
    expect(screen.getByRole('heading', { name: 'New conversation' })).toBeDefined();
  });

  it('keeps the delete dialog available for retry when deletion fails', async () => {
    apiMock.deleteConversation.mockRejectedValue(new Error('Conversation deletion failed.'));
    render(<App />);

    fireEvent.click(await screen.findByRole('button', { name: 'Delete conversation' }));
    const dialog = screen.getByRole('alertdialog', { name: 'Delete conversation?' });
    fireEvent.click(within(dialog).getByRole('button', { name: 'Delete conversation' }));

    expect((await screen.findByRole('alert')).textContent).toContain(
      'Conversation deletion failed.',
    );
    expect(screen.getByRole('alertdialog', { name: 'Delete conversation?' })).toBeDefined();
    await waitFor(() =>
      expect(
        (within(dialog).getByRole('button', {
          name: 'Delete conversation',
        }) as HTMLButtonElement).disabled,
      ).toBe(false),
    );
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
    const failedStatus = screen.getByText('failed');
    expect(failedStatus.classList.contains('document-status')).toBe(true);
    expect(failedStatus.classList.contains('failed')).toBe(true);
    const failure = screen.getByText('The PDF structure is invalid.').closest(
      '.document-error-message',
    );
    expect(failure).not.toBeNull();
    expect(failure?.querySelector('svg')).not.toBeNull();
    expect(failure?.closest('tr')?.classList.contains('document-error-row')).toBe(true);
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

  it('opens an accessible document deletion dialog and supports safe cancellation', async () => {
    apiMock.documents.mockResolvedValue([readyDocument]);
    const browserConfirm = vi.spyOn(window, 'confirm');
    render(<App />);

    fireEvent.click(await screen.findByRole('tab', { name: 'Documents' }));
    await screen.findByText('notes.md');
    fireEvent.click(screen.getByRole('button', { name: 'Delete notes.md' }));

    const dialog = screen.getByRole('alertdialog', { name: 'Delete document?' });
    expect(within(dialog).getByText('notes.md')).toBeDefined();
    expect(
      within(dialog).getByText(/stored file, indexed chunks, and processing record/),
    ).toBeDefined();
    expect(within(dialog).getByText(/cannot be undone/i)).toBeDefined();
    const cancel = within(dialog).getByRole('button', { name: 'Cancel' });
    expect(document.activeElement).toBe(cancel);
    expect(apiMock.deleteDocument).not.toHaveBeenCalled();
    expect(browserConfirm).not.toHaveBeenCalled();

    fireEvent.keyDown(document, { key: 'Escape' });
    expect(screen.queryByRole('alertdialog', { name: 'Delete document?' })).toBeNull();
    expect(apiMock.deleteDocument).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole('button', { name: 'Delete notes.md' }));
    fireEvent.click(
      within(screen.getByRole('alertdialog', { name: 'Delete document?' })).getByRole(
        'button',
        { name: 'Cancel' },
      ),
    );
    expect(screen.queryByRole('alertdialog', { name: 'Delete document?' })).toBeNull();
    expect(screen.getByText('notes.md')).toBeDefined();
  });

  it('deletes only the confirmed document after the API succeeds', async () => {
    let resolveDelete: (() => void) | undefined;
    apiMock.documents.mockResolvedValue([
      readyDocument,
      { ...readyDocument, id: 'document-2', fileName: 'keep.pdf' },
    ]);
    apiMock.deleteDocument.mockImplementation(
      () =>
        new Promise<void>((resolve) => {
          resolveDelete = resolve;
        }),
    );
    render(<App />);

    fireEvent.click(await screen.findByRole('tab', { name: 'Documents' }));
    fireEvent.click(await screen.findByRole('button', { name: 'Delete notes.md' }));
    const dialog = screen.getByRole('alertdialog', { name: 'Delete document?' });
    fireEvent.click(within(dialog).getByRole('button', { name: 'Delete document' }));

    await waitFor(() =>
      expect(apiMock.deleteDocument).toHaveBeenCalledWith('document-1'),
    );
    expect(
      (within(dialog).getByRole('button', { name: 'Deleting…' }) as HTMLButtonElement)
        .disabled,
    ).toBe(true);
    expect(
      (within(dialog).getByRole('button', { name: 'Cancel' }) as HTMLButtonElement)
        .disabled,
    ).toBe(true);
    expect(screen.getAllByText('notes.md')).toHaveLength(2);
    expect(screen.getByText('keep.pdf')).toBeDefined();

    await act(async () => resolveDelete?.());
    await waitFor(() => expect(screen.queryByText('notes.md')).toBeNull());
    expect(screen.getByText('keep.pdf')).toBeDefined();
    expect(screen.queryByRole('alertdialog', { name: 'Delete document?' })).toBeNull();
  });

  it('keeps document deletion available for retry after an API failure', async () => {
    apiMock.documents.mockResolvedValue([readyDocument]);
    apiMock.deleteDocument.mockRejectedValue(new Error('Document deletion failed.'));
    render(<App />);

    fireEvent.click(await screen.findByRole('tab', { name: 'Documents' }));
    fireEvent.click(await screen.findByRole('button', { name: 'Delete notes.md' }));
    const dialog = screen.getByRole('alertdialog', { name: 'Delete document?' });
    fireEvent.click(within(dialog).getByRole('button', { name: 'Delete document' }));

    expect((await screen.findByRole('alert')).textContent).toContain(
      'Document deletion failed.',
    );
    expect(screen.getByRole('alertdialog', { name: 'Delete document?' })).toBeDefined();
    expect(screen.getAllByText('notes.md')).toHaveLength(2);
    await waitFor(() =>
      expect(
        (within(dialog).getByRole('button', {
          name: 'Delete document',
        }) as HTMLButtonElement).disabled,
      ).toBe(false),
    );
  });

  it('renders each document lifecycle state as its own status badge', async () => {
    apiMock.documents.mockResolvedValue([
      { ...readyDocument, id: 'queued', fileName: 'queued.txt', status: 'queued' },
      { ...readyDocument, id: 'processing', fileName: 'processing.txt', status: 'processing' },
      readyDocument,
      { ...readyDocument, id: 'failed', fileName: 'failed.txt', status: 'failed' },
    ]);
    render(<App />);

    fireEvent.click(await screen.findByRole('tab', { name: 'Documents' }));
    for (const status of ['queued', 'processing', 'ready', 'failed']) {
      const badge = await screen.findByText(status);
      expect(badge.classList.contains('document-status')).toBe(true);
      expect(badge.classList.contains(status)).toBe(true);
    }
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
