/*
 * SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
 * SPDX-License-Identifier: Apache-2.0
 */

import { useEffect, useState } from 'react';
import { api } from './api';
import { Header } from './components/Header';
import { ConversationWorkspace } from './features/conversations/ConversationWorkspace';
import { useConversations } from './features/conversations/useConversations';
import { DocumentsWorkspace } from './features/documents/DocumentsWorkspace';
import { useDocuments } from './features/documents/useDocuments';
import type { ModelCatalog } from './types';

type ActiveView = 'chat' | 'documents';

export default function App() {
  const [catalog, setCatalog] = useState<ModelCatalog | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeView, setActiveView] = useState<ActiveView>('chat');
  const [initialLoadFailed, setInitialLoadFailed] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const conversations = useConversations(catalog, setError);
  const documents = useDocuments(
    conversations.embeddingModel,
    catalog?.embeddingModels ?? [],
    setError,
  );

  useEffect(() => {
    void loadInitialState();
  }, []);

  async function loadInitialState() {
    setLoading(true);
    setInitialLoadFailed(false);
    setError(null);
    try {
      const [models, storedConversations, storedDocuments] = await Promise.all([
        api.models(),
        conversations.fetchInitial(),
        documents.fetchInitial(),
      ]);
      setCatalog(models);
      documents.restoreInitial(storedDocuments);
      await conversations.restoreInitial(storedConversations, models);
    } catch (cause) {
      setCatalog(null);
      setInitialLoadFailed(true);
      setError(initialLoadErrorMessage(cause));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app-shell">
      <Header loading={loading} ollamaAvailable={catalog?.ollamaAvailable ?? null} />

      <nav className="view-tabs" aria-label="Primary workspace" role="tablist">
        <button
          id="chat-tab"
          type="button"
          role="tab"
          aria-selected={activeView === 'chat'}
          aria-controls="chat-panel"
          className={activeView === 'chat' ? 'active' : undefined}
          onClick={() => setActiveView('chat')}
        >
          Chat
        </button>
        <button
          id="documents-tab"
          type="button"
          role="tab"
          aria-selected={activeView === 'documents'}
          aria-controls="documents-panel"
          className={activeView === 'documents' ? 'active' : undefined}
          onClick={() => setActiveView('documents')}
        >
          Documents
        </button>
      </nav>

      {error && (
        <div className="error-banner" role="alert">
          <span>{error}</span>
          <div className="error-banner-actions">
            {initialLoadFailed && (
              <button
                type="button"
                className="error-retry-button"
                onClick={() => void loadInitialState()}
              >
                Retry connection
              </button>
            )}
            <button
              type="button"
              className="error-dismiss-button"
              onClick={() => setError(null)}
              aria-label="Dismiss error"
            >
              ×
            </button>
          </div>
        </div>
      )}

      {activeView === 'chat' ? (
        <ConversationWorkspace catalog={catalog} controller={conversations} />
      ) : (
        <DocumentsWorkspace
          controller={documents}
          loading={loading}
          embeddingModel={conversations.embeddingModel}
        />
      )}
    </div>
  );
}

function errorMessage(cause: unknown): string {
  return cause instanceof Error ? cause.message : 'An unexpected error occurred.';
}

function initialLoadErrorMessage(cause: unknown): string {
  const message = errorMessage(cause);
  if (
    message === 'Failed to fetch' ||
    message === 'NetworkError when attempting to fetch resource.'
  ) {
    return 'CiteNook could not reach its API. Check that the Docker services are running, then retry.';
  }
  return message;
}
