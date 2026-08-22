/*
 * SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
 * SPDX-License-Identifier: Apache-2.0
 */

import {
  useEffect,
  useRef,
  useState,
  type ChangeEvent,
  type FormEvent,
  type ReactNode,
  type RefObject,
} from 'react';
import type { ModelOption } from '../types';

interface ConversationModelDialogProps {
  mode: 'create' | 'edit';
  chatModels: ModelOption[];
  embeddingModels: ModelOption[];
  defaultChatModel: string;
  defaultEmbeddingModel: string;
  initialChatModel: string;
  initialEmbeddingModel: string;
  saving: boolean;
  onCancel: () => void;
  onSubmit: (chatModel: string, embeddingModel: string) => void;
}

export function ConversationModelDialog(props: ConversationModelDialogProps) {
  const [chatModel, setChatModel] = useState(props.initialChatModel);
  const [embeddingModel, setEmbeddingModel] = useState(props.initialEmbeddingModel);
  const firstSelectRef = useRef<HTMLSelectElement>(null);
  const canSubmit =
    isInstalled(props.chatModels, chatModel) &&
    isInstalled(props.embeddingModels, embeddingModel) &&
    !props.saving;
  const isCreate = props.mode === 'create';

  useEscapeToCancel(props.saving, props.onCancel);

  useEffect(() => {
    firstSelectRef.current?.focus();
  }, []);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSubmit) return;
    props.onSubmit(chatModel, embeddingModel);
  }

  return (
    <div className="modal-backdrop" role="presentation">
      <section
        className="modal-card model-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="model-dialog-title"
        aria-describedby="model-dialog-description"
      >
        <div className="modal-heading">
          <p className="eyebrow">Conversation models</p>
          <h2 id="model-dialog-title">
            {isCreate ? 'Start a new conversation' : 'Change conversation models'}
          </h2>
          <p id="model-dialog-description">
            {isCreate
              ? 'Choose the chat and embedding models this conversation should remember.'
              : 'Future questions use the new model pair. Existing messages keep their original model information.'}
          </p>
        </div>

        <form onSubmit={submit}>
          <div className="modal-model-fields">
            <ModelSelect
              inputRef={firstSelectRef}
              id="conversation-chat-model"
              label="Chat model"
              value={chatModel}
              models={props.chatModels}
              defaultModel={props.defaultChatModel}
              disabled={props.saving}
              onChange={setChatModel}
            />
            <ModelSelect
              id="conversation-embedding-model"
              label="Embedding model"
              value={embeddingModel}
              models={props.embeddingModels}
              defaultModel={props.defaultEmbeddingModel}
              disabled={props.saving}
              onChange={setEmbeddingModel}
            />
          </div>

          {!canSubmit && !props.saving && (
            <p className="modal-note" role="status">
              An installed chat model and embedding model are required.
            </p>
          )}

          <div className="modal-actions">
            <button
              type="button"
              className="secondary-button"
              disabled={props.saving}
              onClick={props.onCancel}
            >
              Cancel
            </button>
            <button type="submit" className="primary-button" disabled={!canSubmit}>
              {props.saving
                ? isCreate
                  ? 'Creating…'
                  : 'Saving…'
                : isCreate
                  ? 'Create conversation'
                  : 'Save models'}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}

interface ConversationDeleteDialogProps {
  conversationTitle: string;
  deleting: boolean;
  onCancel: () => void;
  onConfirm: () => void;
}

export function ConversationDeleteDialog(props: ConversationDeleteDialogProps) {
  return (
    <DestructiveConfirmationDialog
      idPrefix="conversation-delete"
      title="Delete conversation?"
      description={
        <>
          <strong>{props.conversationTitle}</strong> and all of its messages will be permanently
          deleted. This action cannot be undone.
        </>
      }
      confirmLabel="Delete conversation"
      busyLabel="Deleting…"
      busy={props.deleting}
      onCancel={props.onCancel}
      onConfirm={props.onConfirm}
    />
  );
}

interface DocumentDeleteDialogProps {
  fileName: string;
  deleting: boolean;
  onCancel: () => void;
  onConfirm: () => void;
}

export function DocumentDeleteDialog(props: DocumentDeleteDialogProps) {
  return (
    <DestructiveConfirmationDialog
      idPrefix="document-delete"
      title="Delete document?"
      description={
        <>
          <strong>{props.fileName}</strong>, its stored file, indexed chunks, and processing record
          will be permanently deleted. This action cannot be undone.
        </>
      }
      confirmLabel="Delete document"
      busyLabel="Deleting…"
      busy={props.deleting}
      onCancel={props.onCancel}
      onConfirm={props.onConfirm}
    />
  );
}

function DestructiveConfirmationDialog(props: {
  idPrefix: string;
  title: string;
  description: ReactNode;
  confirmLabel: string;
  busyLabel: string;
  busy: boolean;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  const cancelRef = useRef<HTMLButtonElement>(null);
  const titleId = `${props.idPrefix}-title`;
  const descriptionId = `${props.idPrefix}-description`;

  useEscapeToCancel(props.busy, props.onCancel);

  useEffect(() => {
    cancelRef.current?.focus();
  }, []);

  return (
    <div className="modal-backdrop" role="presentation">
      <section
        className="modal-card delete-dialog"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={descriptionId}
      >
        <div className="delete-dialog-icon" aria-hidden="true">
          <TrashIcon />
        </div>
        <div className="modal-heading">
          <p className="eyebrow danger-eyebrow">Permanent action</p>
          <h2 id={titleId}>{props.title}</h2>
          <p id={descriptionId}>{props.description}</p>
        </div>
        <div className="modal-actions">
          <button
            ref={cancelRef}
            type="button"
            className="secondary-button"
            disabled={props.busy}
            onClick={props.onCancel}
          >
            Cancel
          </button>
          <button
            type="button"
            className="modal-danger-button"
            disabled={props.busy}
            onClick={props.onConfirm}
          >
            {props.busy ? props.busyLabel : props.confirmLabel}
          </button>
        </div>
      </section>
    </div>
  );
}

function ModelSelect(props: {
  inputRef?: RefObject<HTMLSelectElement | null>;
  id: string;
  label: string;
  value: string;
  models: ModelOption[];
  defaultModel: string;
  disabled: boolean;
  onChange: (model: string) => void;
}) {
  return (
    <label htmlFor={props.id}>
      <span>{props.label}</span>
      <select
        ref={props.inputRef}
        id={props.id}
        value={props.value}
        disabled={props.disabled || props.models.length === 0}
        onChange={(event: ChangeEvent<HTMLSelectElement>) => props.onChange(event.target.value)}
      >
        <option value="">No installed model available</option>
        {props.models.map((model) => (
          <option key={model.name} value={model.name} disabled={!model.installed}>
            {model.name}
            {model.name === props.defaultModel ? ' — default' : ''}
            {model.installed ? '' : ' — not installed'}
          </option>
        ))}
      </select>
    </label>
  );
}

function isInstalled(models: ModelOption[], selected: string): boolean {
  return models.some((model) => model.name === selected && model.installed);
}

function useEscapeToCancel(blocked: boolean, onCancel: () => void) {
  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key !== 'Escape' || blocked) return;
      event.preventDefault();
      onCancel();
    }

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [blocked, onCancel]);
}

function TrashIcon() {
  return (
    <svg viewBox="0 0 24 24" width="22" height="22">
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
