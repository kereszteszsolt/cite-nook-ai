/*
 * SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
 * SPDX-License-Identifier: Apache-2.0
 */

import { useEffect, useState, type FormEvent, type KeyboardEvent } from 'react';
import type { Conversation } from '../types';

interface ConversationTitleProps {
  conversation: Conversation | null;
  saving: boolean;
  onRename: (title: string) => Promise<boolean>;
}

export function ConversationTitle(props: ConversationTitleProps) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(props.conversation?.title ?? '');

  useEffect(() => {
    setEditing(false);
    setDraft(props.conversation?.title ?? '');
  }, [props.conversation?.id]);

  useEffect(() => {
    if (!editing) setDraft(props.conversation?.title ?? '');
  }, [editing, props.conversation?.title]);

  if (!props.conversation) return <h1>Start a conversation</h1>;

  function cancel() {
    setDraft(props.conversation?.title ?? '');
    setEditing(false);
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const normalized = draft.trim().replace(/\s+/g, ' ');
    if (!normalized || props.saving) return;
    if (normalized === props.conversation?.title) {
      setEditing(false);
      return;
    }
    if (await props.onRename(normalized)) setEditing(false);
  }

  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key !== 'Escape') return;
    event.preventDefault();
    cancel();
  }

  return editing ? (
    <form
      className="conversation-title-form"
      aria-label="Edit conversation title"
      onSubmit={(event) => void submit(event)}
    >
      <label className="visually-hidden" htmlFor="conversation-title-input">
        Conversation title
      </label>
      <input
        id="conversation-title-input"
        value={draft}
        maxLength={120}
        autoFocus
        disabled={props.saving}
        onChange={(event) => setDraft(event.target.value)}
        onKeyDown={handleKeyDown}
      />
      <div className="conversation-title-actions">
        <button
          type="submit"
          className="primary-button"
          disabled={props.saving || !draft.trim()}
        >
          {props.saving ? 'Saving…' : 'Save title'}
        </button>
        <button
          type="button"
          className="secondary-button"
          disabled={props.saving}
          onClick={cancel}
        >
          Cancel
        </button>
      </div>
    </form>
  ) : (
    <div className="conversation-title-display">
      <h1>{props.conversation.title}</h1>
      <button
        type="button"
        className="title-edit-button"
        aria-label="Edit conversation title"
        onClick={() => setEditing(true)}
      >
        <PencilIcon />
        <span>Edit title</span>
      </button>
    </div>
  );
}

function PencilIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" width="16" height="16">
      <path
        d="M4 20h4.2L19 9.2 14.8 5 4 15.8V20Zm2-3.4 8.8-8.8 1.4 1.4L7.4 18H6v-1.4ZM17.6 4.2l1.4-1.4a1 1 0 0 1 1.4 0l.8.8a1 1 0 0 1 0 1.4l-1.4 1.4-2.2-2.2Z"
        fill="currentColor"
      />
    </svg>
  );
}
