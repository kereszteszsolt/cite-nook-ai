/*
 * SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
 * SPDX-License-Identifier: Apache-2.0
 */

// @vitest-environment jsdom

import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import App from '../../App';
import {
  cleanupAppTest,
  configureAppTest,
  readyDocument,
  storedConversation,
  storedMessages,
  type AppApiMock,
} from '../../test/appTestSupport';

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

vi.mock('../../api', () => ({ api: apiMock }));

beforeEach(() => configureAppTest(apiMock));
afterEach(() => cleanupAppTest());

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

});

describe('persistent conversation history', () => {
  it('edits a conversation title and updates the header and sidebar', async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole('button', { name: 'Edit conversation title' }));
    const titleInput = (await screen.findByLabelText(
      'Conversation title',
    )) as HTMLInputElement;
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
    const titleInput = (await screen.findByLabelText(
      'Conversation title',
    )) as HTMLInputElement;
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
    fireEvent.change(await screen.findByLabelText('Conversation title'), {
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

    const copyButton = await screen.findByRole('button', { name: 'Copy message 2' });
    await act(async () => {
      fireEvent.click(copyButton);
      await Promise.resolve();
    });

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
    const writeText = vi.fn().mockRejectedValue(new Error('Denied'));
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: { writeText },
    });
    apiMock.messages.mockResolvedValue(storedMessages);
    render(<App />);

    const copyButton = await screen.findByRole('button', { name: 'Copy message 1' });
    await act(async () => {
      fireEvent.click(copyButton);
      await Promise.resolve();
    });

    expect(writeText).toHaveBeenCalledWith('What does the document say?');
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
    const retrying = await screen.findByRole('button', {
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
    let resolveAnswer: ((turn: unknown) => void) | undefined;
    apiMock.askQuestion.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveAnswer = resolve;
        }),
    );
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
    expect(input.value).toBe('');
    expect(input.disabled).toBe(true);
    const messages = screen.getByLabelText('Conversation messages');
    expect(
      within(messages).getByRole('status', {
        name: 'CiteNook is preparing an answer',
      }),
    ).toBeDefined();
    expect(within(messages).getAllByText('What does the document say?')).toHaveLength(1);

    await act(async () =>
      resolveAnswer?.({
        conversation: { ...storedConversation, title: 'What does the document say?' },
        userMessage: storedMessages[0],
        assistantMessage: storedMessages[1],
      }),
    );

    expect(await screen.findByText('The persisted answer.')).toBeDefined();
    expect(screen.getByRole('link', { name: /\[S1\] notes.md/ })).toBeDefined();
    expect(
      within(messages).queryByRole('status', {
        name: 'CiteNook is preparing an answer',
      }),
    ).toBeNull();
    expect(within(messages).getAllByText('What does the document say?')).toHaveLength(1);
    expect(input.value).toBe('');
    expect(input.disabled).toBe(false);
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
    let rejectAnswer: ((cause: Error) => void) | undefined;
    apiMock.askQuestion.mockImplementation(
      () =>
        new Promise((_resolve, reject) => {
          rejectAnswer = reject;
        }),
    );
    render(<App />);

    const input = (await screen.findByLabelText('Ask your documents')) as HTMLTextAreaElement;
    fireEvent.change(input, { target: { value: 'Please retry this question' } });
    fireEvent.click(screen.getByRole('button', { name: 'Send question' }));

    await waitFor(() =>
      expect(apiMock.askQuestion).toHaveBeenCalledWith(
        'conversation-1',
        'Please retry this question',
      ),
    );
    expect(input.value).toBe('');
    expect(input.disabled).toBe(true);
    expect(
      screen.getByRole('status', { name: 'CiteNook is preparing an answer' }),
    ).toBeDefined();

    await act(async () => rejectAnswer?.(new Error('Answer failed.')));

    expect((await screen.findByRole('alert')).textContent).toContain('Answer failed.');
    expect(input.value).toBe('Please retry this question');
    expect(input.disabled).toBe(false);
    expect(
      screen.queryByRole('status', { name: 'CiteNook is preparing an answer' }),
    ).toBeNull();
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
