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
  onAsk: (question: string) => Promise<boolean>;
}

const COMPOSER_MIN_HEIGHT_PX = 48;
const COMPOSER_MAX_HEIGHT_PX = 160;

export function ConversationMessages(props: ConversationMessagesProps) {
  const [question, setQuestion] = useState('');
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);
  const [retryingMessageId, setRetryingMessageId] = useState<string | null>(null);
  const [actionStatus, setActionStatus] = useState('');
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

  useEffect(() => {
    setCopiedMessageId(null);
    setRetryingMessageId(null);
    setActionStatus('');
  }, [props.conversation?.id]);

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

  async function copyMessage(message: ConversationMessage) {
    try {
      if (!navigator.clipboard?.writeText) throw new Error('Clipboard unavailable.');
      await navigator.clipboard.writeText(message.content);
      setCopiedMessageId(message.id);
      setActionStatus(`Message ${message.ordinal} copied to the clipboard.`);
    } catch {
      setCopiedMessageId(null);
      setActionStatus(
        `Message ${message.ordinal} could not be copied. Check clipboard permission and try again.`,
      );
    }
  }

  async function retryAnswer(message: ConversationMessage, originalQuestion: string) {
    if (props.asking || props.loading) return;
    setRetryingMessageId(message.id);
    setActionStatus(`Asking message ${message.ordinal}'s question again.`);
    const succeeded = await props.onAsk(originalQuestion);
    setRetryingMessageId(null);
    setActionStatus(
      succeeded
        ? 'The question was asked again and a new answer was added.'
        : 'The question could not be asked again. The existing history was preserved.',
    );
  }

  return (
    <section className="messages-panel" aria-label="Conversation messages">
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
            {props.messages.map((message, index) => {
              const originalQuestion =
                message.role === 'assistant'
                  ? findPreviousQuestion(props.messages, index)
                  : null;
              const copied = copiedMessageId === message.id;
              const retrying = retryingMessageId === message.id;
              return (
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
                  <div
                    className="message-actions"
                    aria-label={`Actions for message ${message.ordinal}`}
                  >
                    <button
                      type="button"
                      className={`message-action-button ${copied ? 'confirmed' : ''}`}
                      aria-label={`${copied ? 'Copied' : 'Copy'} message ${message.ordinal}`}
                      title={copied ? 'Copied to clipboard' : 'Copy message'}
                      onClick={() => void copyMessage(message)}
                    >
                      {copied ? <CheckIcon /> : <CopyIcon />}
                    </button>
                    {message.role === 'assistant' && (
                      <>
                        <button
                          type="button"
                          className="message-action-button"
                          aria-label={`${retrying ? 'Asking question again for' : 'Ask question again for'} answer ${message.ordinal}`}
                          title={
                            originalQuestion
                              ? 'Ask this question again'
                              : 'Original question unavailable'
                          }
                          disabled={
                            props.loading || props.asking || originalQuestion === null
                          }
                          onClick={() =>
                            originalQuestion && void retryAnswer(message, originalQuestion)
                          }
                        >
                          <RetryIcon active={retrying} />
                        </button>
                        <span
                          className="message-response-time"
                          aria-label={responseDurationLabel(message.responseDurationMs)}
                          title={responseDurationLabel(message.responseDurationMs)}
                        >
                          <ClockIcon />
                          <span>{formatResponseDuration(message.responseDurationMs)}</span>
                        </span>
                      </>
                    )}
                  </div>
                </article>
              );
            })}
          </div>
        )}
        <p className="visually-hidden" role="status" aria-live="polite">
          {actionStatus}
        </p>
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

function findPreviousQuestion(
  messages: ConversationMessage[],
  assistantIndex: number,
): string | null {
  for (let index = assistantIndex - 1; index >= 0; index -= 1) {
    if (messages[index]?.role === 'user') return messages[index].content;
  }
  return null;
}

export function formatResponseDuration(durationMs: number | null | undefined): string {
  if (durationMs === null || durationMs === undefined) return '—';
  if (durationMs < 1000) return `${durationMs} ms`;
  if (durationMs < 60_000) {
    const seconds = durationMs / 1000;
    return `${seconds < 10 ? seconds.toFixed(1) : Math.round(seconds)} s`;
  }
  const totalSeconds = Math.round(durationMs / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}m ${seconds}s`;
}

function responseDurationLabel(durationMs: number | null | undefined): string {
  const formatted = formatResponseDuration(durationMs);
  return formatted === '—' ? 'Response time unavailable' : `Response time ${formatted}`;
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

function CopyIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" width="17" height="17">
      <rect x="8" y="8" width="11" height="11" rx="2" fill="none" stroke="currentColor" strokeWidth="1.8" />
      <path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2" fill="none" stroke="currentColor" strokeLinecap="round" strokeWidth="1.8" />
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" width="17" height="17">
      <path d="m5 12 4 4L19 6" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" />
    </svg>
  );
}

function RetryIcon({ active }: { active: boolean }) {
  return (
    <svg
      aria-hidden="true"
      className={active ? 'spinning' : undefined}
      viewBox="0 0 24 24"
      width="17"
      height="17"
    >
      <path d="M20 7v5h-5M4 17v-5h5" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" />
      <path d="M6.1 9A7 7 0 0 1 18.7 7.5L20 12M4 12l1.3 4.5A7 7 0 0 0 17.9 15" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" />
    </svg>
  );
}

function ClockIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" width="16" height="16">
      <circle cx="12" cy="12" r="8" fill="none" stroke="currentColor" strokeWidth="1.8" />
      <path d="M12 7v5l3 2" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" />
    </svg>
  );
}
