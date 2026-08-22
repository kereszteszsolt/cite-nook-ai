/*
 * SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Conversation, ConversationMessage } from '../types';

interface ConversationMessagesProps {
  conversation: Conversation | null;
  messages: ConversationMessage[];
  loading: boolean;
  deleting: boolean;
  onDelete: () => void;
}

export function ConversationMessages(props: ConversationMessagesProps) {
  return (
    <section className="messages-panel" aria-labelledby="messages-heading">
      <div className="messages-heading">
        <div>
          <p className="eyebrow">Conversation</p>
          <h2 id="messages-heading">Saved messages</h2>
        </div>
        {props.conversation && (
          <button
            className="danger-button"
            disabled={props.deleting}
            onClick={props.onDelete}
          >
            {props.deleting ? 'Deleting…' : 'Delete conversation'}
          </button>
        )}
      </div>

      {!props.conversation ? (
        <p className="messages-state">Create or select a conversation to view its history.</p>
      ) : props.loading ? (
        <p className="messages-state" role="status">Loading messages…</p>
      ) : props.messages.length === 0 ? (
        <p className="messages-state">
          No messages yet. Grounded questions and answers arrive in MRA-007.
        </p>
      ) : (
        <div className="message-list" aria-live="polite">
          {props.messages.map((message) => (
            <article key={message.id} className={`message-bubble ${message.role}`}>
              <div className="message-meta">
                <strong>{message.role === 'user' ? 'You' : 'CiteNook'}</strong>
                {message.chatModel && <span>{message.chatModel}</span>}
              </div>
              <p>{message.content}</p>
              {message.role === 'assistant' && message.citations.length > 0 && (
                <small>
                  {message.citations.length}{' '}
                  {message.citations.length === 1 ? 'stored source' : 'stored sources'}
                </small>
              )}
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
