/*
 * SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
 * SPDX-License-Identifier: Apache-2.0
 */

import { useEffect, useMemo, useState } from 'react';
import { api } from './api';
import { ConversationSidebar } from './components/ConversationSidebar';
import { DocumentUpload } from './components/DocumentUpload';
import { Header } from './components/Header';
import type { Conversation, ModelCatalog, ModelOption, StoredUpload } from './types';

export default function App() {
  const [catalog, setCatalog] = useState<ModelCatalog | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [chatModel, setChatModel] = useState('');
  const [embeddingModel, setEmbeddingModel] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploaded, setUploaded] = useState<StoredUpload | null>(null);
  const [error, setError] = useState<string | null>(null);

  const activeConversation = useMemo(
    () => conversations.find((conversation) => conversation.id === activeId) ?? null,
    [activeId, conversations],
  );
  const canCreate =
    isInstalled(catalog?.chatModels ?? [], chatModel) &&
    isInstalled(catalog?.embeddingModels ?? [], embeddingModel);
  const canUpload = isInstalled(catalog?.embeddingModels ?? [], embeddingModel);

  useEffect(() => {
    void loadInitialState();

    async function loadInitialState() {
      try {
        const [models, storedConversations] = await Promise.all([
          api.models(),
          api.conversations(),
        ]);
        setCatalog(models);
        setConversations(storedConversations);

        const firstConversation = storedConversations[0];
        if (firstConversation) {
          restoreConversation(firstConversation);
        } else {
          setChatModel(preferredInstalled(models.chatModels, models.defaultChatModel));
          setEmbeddingModel(
            preferredInstalled(models.embeddingModels, models.defaultEmbeddingModel),
          );
        }
      } catch (cause) {
        setError(errorMessage(cause));
      } finally {
        setLoading(false);
      }
    }
  }, []);

  function restoreConversation(conversation: Conversation) {
    setActiveId(conversation.id);
    setChatModel(conversation.chatModel);
    setEmbeddingModel(conversation.embeddingModel);
  }

  async function createConversation() {
    if (!canCreate) return;
    setSaving(true);
    setError(null);
    try {
      const created = await api.createConversation(chatModel, embeddingModel);
      setConversations((items) => [created, ...items]);
      restoreConversation(created);
    } catch (cause) {
      setError(errorMessage(cause));
    } finally {
      setSaving(false);
    }
  }

  async function changeModels(nextChatModel: string, nextEmbeddingModel: string) {
    const previousChatModel = chatModel;
    const previousEmbeddingModel = embeddingModel;
    setChatModel(nextChatModel);
    setEmbeddingModel(nextEmbeddingModel);
    if (!activeId) return;

    setSaving(true);
    setError(null);
    try {
      const updated = await api.updateConversation(
        activeId,
        nextChatModel,
        nextEmbeddingModel,
      );
      setConversations((items) =>
        items.map((conversation) =>
          conversation.id === updated.id ? updated : conversation,
        ),
      );
    } catch (cause) {
      setChatModel(previousChatModel);
      setEmbeddingModel(previousEmbeddingModel);
      setError(errorMessage(cause));
    } finally {
      setSaving(false);
    }
  }

  async function uploadDocument(file: File): Promise<boolean> {
    if (!canUpload) return false;
    setUploading(true);
    setUploaded(null);
    setError(null);
    try {
      setUploaded(await api.uploadDocument(file, embeddingModel));
      return true;
    } catch (cause) {
      setError(errorMessage(cause));
      return false;
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="app-shell">
      <Header
        chatModels={catalog?.chatModels ?? []}
        embeddingModels={catalog?.embeddingModels ?? []}
        chatModel={chatModel}
        embeddingModel={embeddingModel}
        loading={loading}
        saving={saving}
        ollamaAvailable={catalog?.ollamaAvailable ?? null}
        onChatModelChange={(value) => void changeModels(value, embeddingModel)}
        onEmbeddingModelChange={(value) => void changeModels(chatModel, value)}
      />

      {error && (
        <div className="error-banner" role="alert">
          <span>{error}</span>
          <button onClick={() => setError(null)} aria-label="Dismiss error">×</button>
        </div>
      )}

      <main className="workspace">
        <ConversationSidebar
          conversations={conversations}
          activeId={activeId}
          canCreate={canCreate && !saving}
          onCreate={() => void createConversation()}
          onSelect={restoreConversation}
        />

        <div className="content-column">
          <section className="model-panel">
            <p className="eyebrow">Model configuration</p>
            <h1>{activeConversation?.title ?? 'Start a conversation'}</h1>
            {activeConversation ? (
              <p>
                This conversation remembers <strong>{chatModel}</strong> for chat and{' '}
                <strong>{embeddingModel}</strong> for document embeddings.
              </p>
            ) : (
              <p>
                Select installed chat and embedding models, then create a conversation. Messages
                arrive in a following story.
              </p>
            )}
            {saving && <p className="saving-note">Saving model selection…</p>}
          </section>

          <DocumentUpload
            embeddingModel={embeddingModel}
            enabled={canUpload}
            uploading={uploading}
            uploaded={uploaded}
            onUpload={uploadDocument}
          />
        </div>
      </main>
    </div>
  );
}

function preferredInstalled(models: ModelOption[], preferred: string): string {
  if (models.some((model) => model.name === preferred && model.installed)) return preferred;
  return models.find((model) => model.installed)?.name ?? '';
}

function isInstalled(models: ModelOption[], selected: string): boolean {
  return models.some((model) => model.name === selected && model.installed);
}

function errorMessage(cause: unknown): string {
  return cause instanceof Error ? cause.message : 'An unexpected error occurred.';
}
