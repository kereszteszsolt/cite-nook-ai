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

describe('document status and management', () => {
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
