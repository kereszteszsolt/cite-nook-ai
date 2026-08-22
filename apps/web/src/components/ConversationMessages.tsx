/*
 * SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
 * SPDX-License-Identifier: Apache-2.0
 */

import {
  useEffect,
  useRef,
  useState,
  type FormEvent,
  type KeyboardEvent,
} from 'react';
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

const COMPOSER_MIN_HEIGHT_PX = 48;
const COMPOSER_MAX_HEIGHT_PX = 160;

export function ConversationMessages(props: ConversationMessagesProps) {
  const [question, setQuestion] = useState('');
  const historyRef = useRef<HTMLDivElement>(null);
  const questionRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const history = historyRef.current;
    if (history) history.scrollTop = history.scrollHeight;
  }, [props.messages]);

  useEffect(() => {
    const input = questionRef.current;
    if (!input) return;
    input.style.height = 'auto';
    input.style.height = `${Math.max(
      COMPOSER_MIN_HEIGHT_PX,
      Math.min(input.scrollHeight, COMPOSER_MAX_HEIGHT_PX),
    )}px`;
    input.style.overflowY =
      input.scrollHeight > COMPOSER_MAX_HEIGHT_PX ? 'auto' : 'hidden';
  }, [props.conversation?.id, question]);

  async function submitQuestion(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const normalized = question.trim();
    if (!normalized || !props.conversation || props.asking) return;
    if (await props.onAsk(normalized)) setQuestion('');
  }

  function handleQuestionKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (
      event.key !== 'Enter' ||
      event.shiftKey ||
      event.nativeEvent.isComposing
    ) {
      return;
    }
    event.preventDefault();
    event.currentTarget.form?.requestSubmit();
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
            type="button"
            className="conversation-delete-button"
            disabled={props.deleting || props.asking}
            onClick={props.onDelete}
          >
            <TrashIcon />
            <span>{props.deleting ? 'Deleting…' : 'Delete conversation'}</span>
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
          <label className="visually-hidden" htmlFor="conversation-question">
            Ask your documents
          </label>
          <div className="composer-field">
            <textarea
              ref={questionRef}
              id="conversation-question"
              value={question}
              maxLength={4000}
              rows={1}
              disabled={props.loading || props.asking}
              placeholder="Ask a question grounded in your ready documents…"
              onChange={(event) => setQuestion(event.target.value)}
              onKeyDown={handleQuestionKeyDown}
              aria-describedby="composer-hint"
            />
            <button
              className="composer-send-button"
              type="submit"
              disabled={props.loading || props.asking || !question.trim()}
              aria-label={props.asking ? 'Answering question' : 'Send question'}
            >
              <SendIcon />
            </button>
          </div>
          <small id="composer-hint" className="composer-hint">
            Enter to send · Shift+Enter for a new line
          </small>
        </form>
      )}
    </section>
  );
}

function formatScore(score: number): string {
  return `${(score * 100).toFixed(1)}%`;
}

function SendIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" width="20" height="20">
      <path
        d="M12 20V5m0 0-6 6m6-6 6 6"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="2.2"
      />
    </svg>
  );
}

function TrashIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" width="16" height="16">
      <path
        d="M8 8v10m4-10v10m4-10v10M5 5h14M9 5V3h6v2m2 0 1 16H6L7 5"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.8"
      />
    </svg>
  );
}
