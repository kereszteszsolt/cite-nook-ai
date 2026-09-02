/*
 * SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
 * SPDX-License-Identifier: Apache-2.0
 */

import { brand } from '@citenook/brand';

interface HeaderProps {
  loading: boolean;
  ollamaAvailable: boolean | null;
}

export function Header(props: HeaderProps) {
  return (
    <header className="app-header">
      <div className="brand-block">
        <strong>{brand.productName}</strong>
        <span>{brand.description}</span>
      </div>

      <span
        className={`ollama-status ${statusClass(props.ollamaAvailable, props.loading)}`}
        role="status"
      >
        {statusLabel(props.ollamaAvailable, props.loading)}
      </span>
    </header>
  );
}

function statusClass(available: boolean | null, loading: boolean): string {
  if (loading) return 'checking';
  if (available === null) return 'unavailable';
  return available ? 'ready' : 'unavailable';
}

function statusLabel(available: boolean | null, loading: boolean): string {
  if (loading) return 'Checking Ollama';
  if (available === null) return 'CiteNook API unavailable';
  return available ? 'Ollama connected' : 'Ollama unavailable';
}
