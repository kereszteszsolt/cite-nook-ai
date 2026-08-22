/*
 * SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
 * SPDX-License-Identifier: Apache-2.0
 */

import { brand } from '@citenook/brand';
import type { ChangeEvent } from 'react';
import type { ModelOption } from '../types';

interface HeaderProps {
  chatModels: ModelOption[];
  embeddingModels: ModelOption[];
  chatModel: string;
  embeddingModel: string;
  loading: boolean;
  saving: boolean;
  ollamaAvailable: boolean | null;
  onChatModelChange: (model: string) => void;
  onEmbeddingModelChange: (model: string) => void;
}

export function Header(props: HeaderProps) {
  const selectorsDisabled = props.loading || props.saving;

  return (
    <header className="app-header">
      <div className="brand-block">
        <strong>{brand.productName}</strong>
        <span>{brand.description}</span>
      </div>

      <span className={`ollama-status ${statusClass(props.ollamaAvailable)}`} role="status">
        {statusLabel(props.ollamaAvailable, props.loading)}
      </span>

      <div className="model-selectors">
        <ModelSelect
          id="chat-model"
          label="Chat model"
          value={props.chatModel}
          models={props.chatModels}
          disabled={selectorsDisabled}
          onChange={props.onChatModelChange}
        />
        <ModelSelect
          id="embedding-model"
          label="Embedding model"
          value={props.embeddingModel}
          models={props.embeddingModels}
          disabled={selectorsDisabled}
          onChange={props.onEmbeddingModelChange}
        />
      </div>
    </header>
  );
}

function ModelSelect(props: {
  id: string;
  label: string;
  value: string;
  models: ModelOption[];
  disabled: boolean;
  onChange: (model: string) => void;
}) {
  return (
    <label htmlFor={props.id}>
      {props.label}
      <select
        id={props.id}
        value={props.value}
        disabled={props.disabled || props.models.length === 0}
        onChange={(event: ChangeEvent<HTMLSelectElement>) => props.onChange(event.target.value)}
      >
        <option value="">No installed model selected</option>
        {props.models.map((model) => (
          <option key={model.name} value={model.name} disabled={!model.installed}>
            {model.name}{model.installed ? '' : ' — not installed'}
          </option>
        ))}
      </select>
    </label>
  );
}

function statusClass(available: boolean | null): string {
  if (available === null) return 'checking';
  return available ? 'ready' : 'unavailable';
}

function statusLabel(available: boolean | null, loading: boolean): string {
  if (loading || available === null) return 'Checking Ollama';
  return available ? 'Ollama connected' : 'Ollama unavailable';
}
