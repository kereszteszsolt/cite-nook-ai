/*
 * SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
 * SPDX-License-Identifier: Apache-2.0
 */

// @vitest-environment jsdom

import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { Header } from './Header';

afterEach(cleanup);

describe('Header model selectors', () => {
  it('shows unavailable models but disables their options', () => {
    render(
      <Header
        chatModels={[
          { name: 'chat-ready', installed: true },
          { name: 'chat-missing', installed: false },
        ]}
        embeddingModels={[
          { name: 'embed-ready', installed: true },
          { name: 'embed-missing', installed: false },
        ]}
        chatModel="chat-ready"
        embeddingModel="embed-ready"
        loading={false}
        saving={false}
        ollamaAvailable
        onChatModelChange={vi.fn()}
        onEmbeddingModelChange={vi.fn()}
      />,
    );

    const missingChat = screen.getByRole('option', {
      name: 'chat-missing — not installed',
    }) as HTMLOptionElement;
    const missingEmbedding = screen.getByRole('option', {
      name: 'embed-missing — not installed',
    }) as HTMLOptionElement;

    expect(missingChat.disabled).toBe(true);
    expect(missingEmbedding.disabled).toBe(true);
    expect((screen.getByLabelText('Chat model') as HTMLSelectElement).value).toBe('chat-ready');
    expect((screen.getByLabelText('Embedding model') as HTMLSelectElement).value).toBe(
      'embed-ready',
    );
  });
});
