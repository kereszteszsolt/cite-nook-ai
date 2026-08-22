/*
 * SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
 * SPDX-License-Identifier: Apache-2.0
 */

import { useEffect, useRef, useState, type FormEvent } from 'react';
import { api } from '../api';
import type { Conversation, ConversationMessage } from '../types';

interface ConversationMessagesProps {
  conversation: Conversation | null;
  messages: ConversationMessage[];
  loading: boolean;
  asking: boolean;
  deleting: boolean;
  onAsk: (question: string) => Promise<boolean>;
  onDelete: () => void;
}

export function ConversationMessages(props: ConversationMessagesProps) {
  const [question, setQuestion] = useState('');
  const historyRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const history = historyRef.current;
    if (history) history.scrollTop = history.scrollHeight;
  }, [props.messages]);

  async function submitQuestion(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const normalized = question.trim();
    if (!normalized || !props.conversation || props.asking) return;
    if (await props.onAsk(normalized)) setQuestion('');
  }

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
            disabled={props.deleting || props.asking}
            onClick={props.onDelete}
          >
            {props.deleting ? 'Deleting…' : 'Delete conversation'}
          </button>
        )}
      </div>

      <div className="message-history" ref={historyRef}>
        {!props.conversation ? (
          <p className="messages-state">Create or select a conversation to view its history.</p>
        ) : props.loading ? (
          <p className="messages-state" role="status">Loading messages…</p>
        ) : props.messages.length === 0 ? (
          <p className="messages-state">
            Ask a question after at least one compatible document is ready.
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
                  <section
                    className="message-references"
                    aria-label={`References for answer ${message.ordinal}`}
                  >
                    <h3>References</h3>
                    <ol>
                      {message.citations.map((citation) => (
                        <li key={citation.chunkId}>
                          <a
                            href={api.documentFileUrl(citation.documentId)}
                            target="_blank"
                            rel="noreferrer"
                          >
                            <strong>[{citation.sourceId}]</strong>{' '}
                            {citation.documentName}
                            {citation.pageNumber !== null && ` — page ${citation.pageNumber}`}
                          </a>
                          <p>{citation.snippet}</p>
                          <small>Similarity {formatScore(citation.score)}</small>
                        </li>
                      ))}
                    </ol>
                  </section>
                )}
              </article>
            ))}
          </div>
        )}
      </div>

      {props.conversation && (
        <form className="question-form" onSubmit={(event) => void submitQuestion(event)}>
          <label htmlFor="conversation-question">Ask your documents</label>
          <div>
            <textarea
              id="conversation-question"
              value={question}
              maxLength={4000}
              rows={2}
              disabled={props.loading || props.asking}
              placeholder="Ask a question grounded in your ready documents…"
              onChange={(event) => setQuestion(event.target.value)}
            />
            <button
              className="primary-button"
              type="submit"
              disabled={props.loading || props.asking || !question.trim()}
            >
              {props.asking ? 'Answering…' : 'Ask'}
            </button>
          </div>
        </form>
      )}
    </section>
  );
}

function formatScore(score: number): string {
  return `${(score * 100).toFixed(1)}%`;
}
