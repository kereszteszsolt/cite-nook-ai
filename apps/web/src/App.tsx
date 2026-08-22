/*
 * SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
 * SPDX-License-Identifier: Apache-2.0
 */

import { useEffect, useMemo, useRef, useState } from 'react';
import { api } from './api';
import { ConversationSidebar } from './components/ConversationSidebar';
import { ConversationMessages } from './components/ConversationMessages';
import { DocumentList } from './components/DocumentList';
import { DocumentUpload } from './components/DocumentUpload';
import { Header } from './components/Header';
import type {
  Conversation,
  ConversationMessage,
  DocumentRecord,
  ModelCatalog,
  ModelOption,
  StoredUpload,
} from './types';

const DOCUMENT_POLL_INTERVAL_MS = 2000;
type ActiveView = 'chat' | 'documents';

export default function App() {
  const [catalog, setCatalog] = useState<ModelCatalog | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [chatModel, setChatModel] = useState('');
  const [embeddingModel, setEmbeddingModel] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploaded, setUploaded] = useState<StoredUpload | null>(null);
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [activeView, setActiveView] = useState<ActiveView>('chat');
  const [deletingDocumentId, setDeletingDocumentId] = useState<string | null>(null);
  const [togglingDocumentId, setTogglingDocumentId] = useState<string | null>(null);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [asking, setAsking] = useState(false);
  const [deletingConversation, setDeletingConversation] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messageRequestId = useRef(0);

  const activeConversation = useMemo(
    () => conversations.find((conversation) => conversation.id === activeId) ?? null,
    [activeId, conversations],
  );
  const canCreate =
    isInstalled(catalog?.chatModels ?? [], chatModel) &&
    isInstalled(catalog?.embeddingModels ?? [], embeddingModel);
  const canUpload = isInstalled(catalog?.embeddingModels ?? [], embeddingModel);
  const hasProcessingDocuments = documents.some(
    (document) => document.status === 'queued' || document.status === 'processing',
  );

  useEffect(() => {
    void loadInitialState();

    async function loadInitialState() {
      try {
        const [models, storedConversations, storedDocuments] = await Promise.all([
          api.models(),
          api.conversations(),
          api.documents(),
        ]);
        setCatalog(models);
        setConversations(storedConversations);
        setDocuments(storedDocuments);

        const firstConversation = storedConversations[0];
        if (firstConversation) {
          await openConversation(firstConversation);
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

  useEffect(() => {
    if (!hasProcessingDocuments) return;
    let cancelled = false;
    let timer: number | undefined;

    async function pollDocuments() {
      try {
        const latest = await api.documents();
        if (cancelled) return;
        setDocuments(latest);
        if (latest.some(isProcessingDocument)) {
          timer = window.setTimeout(
            () => void pollDocuments(),
            DOCUMENT_POLL_INTERVAL_MS,
          );
        }
      } catch (cause) {
        if (cancelled) return;
        setError(errorMessage(cause));
        timer = window.setTimeout(
          () => void pollDocuments(),
          DOCUMENT_POLL_INTERVAL_MS,
        );
      }
    }

    timer = window.setTimeout(() => void pollDocuments(), DOCUMENT_POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      if (timer !== undefined) window.clearTimeout(timer);
    };
  }, [hasProcessingDocuments]);

  function restoreConversation(conversation: Conversation) {
    setActiveId(conversation.id);
    setChatModel(conversation.chatModel);
    setEmbeddingModel(conversation.embeddingModel);
  }

  async function openConversation(conversation: Conversation) {
    restoreConversation(conversation);
    const requestId = ++messageRequestId.current;
    setLoadingMessages(true);
    setError(null);
    try {
      const storedMessages = await api.messages(conversation.id);
      if (requestId === messageRequestId.current) setMessages(storedMessages);
    } catch (cause) {
      if (requestId === messageRequestId.current) {
        setMessages([]);
        setError(errorMessage(cause));
      }
    } finally {
      if (requestId === messageRequestId.current) setLoadingMessages(false);
    }
  }

  async function createConversation() {
    if (!canCreate) return;
    setSaving(true);
    setError(null);
    try {
      const created = await api.createConversation(chatModel, embeddingModel);
      setConversations((items) => [created, ...items]);
      restoreConversation(created);
      messageRequestId.current += 1;
      setMessages([]);
      setLoadingMessages(false);
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
      const created = await api.uploadDocument(file, embeddingModel);
      setUploaded(created);
      setDocuments((items) => [created, ...items.filter((item) => item.id !== created.id)]);
      return true;
    } catch (cause) {
      setError(errorMessage(cause));
      return false;
    } finally {
      setUploading(false);
    }
  }

  async function deleteDocument(document: DocumentRecord) {
    if (!window.confirm(`Delete "${document.fileName}" and its indexed chunks?`)) return;
    setDeletingDocumentId(document.id);
    setError(null);
    try {
      await api.deleteDocument(document.id);
      setDocuments((items) => items.filter((item) => item.id !== document.id));
      if (uploaded?.id === document.id) setUploaded(null);
    } catch (cause) {
      setError(errorMessage(cause));
    } finally {
      setDeletingDocumentId(null);
    }
  }

  async function setDocumentActive(document: DocumentRecord, isActive: boolean) {
    setTogglingDocumentId(document.id);
    setError(null);
    try {
      const updated = await api.updateDocument(document.id, isActive);
      setDocuments((items) =>
        items.map((item) => (item.id === updated.id ? updated : item)),
      );
      if (uploaded?.id === updated.id) setUploaded(updated);
    } catch (cause) {
      setError(errorMessage(cause));
    } finally {
      setTogglingDocumentId(null);
    }
  }

  async function deleteActiveConversation() {
    if (!activeConversation) return;
    if (!window.confirm(`Delete "${activeConversation.title}" and all of its messages?`)) {
      return;
    }
    setDeletingConversation(true);
    setError(null);
    try {
      await api.deleteConversation(activeConversation.id);
      const remaining = conversations.filter(
        (conversation) => conversation.id !== activeConversation.id,
      );
      setConversations(remaining);
      messageRequestId.current += 1;
      setMessages([]);
      if (remaining[0]) {
        await openConversation(remaining[0]);
      } else {
        setActiveId(null);
      }
    } catch (cause) {
      setError(errorMessage(cause));
    } finally {
      setDeletingConversation(false);
    }
  }

  async function askQuestion(question: string): Promise<boolean> {
    if (!activeConversation) return false;
    const conversationId = activeConversation.id;
    const requestId = messageRequestId.current;
    setAsking(true);
    setError(null);
    try {
      const turn = await api.askQuestion(conversationId, question);
      setConversations((items) => [
        turn.conversation,
        ...items.filter((conversation) => conversation.id !== turn.conversation.id),
      ]);
      if (requestId === messageRequestId.current) {
        setMessages((items) => [...items, turn.userMessage, turn.assistantMessage]);
      }
      return true;
    } catch (cause) {
      setError(errorMessage(cause));
      return false;
    } finally {
      setAsking(false);
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
        saving={saving || asking}
        ollamaAvailable={catalog?.ollamaAvailable ?? null}
        onChatModelChange={(value) => void changeModels(value, embeddingModel)}
        onEmbeddingModelChange={(value) => void changeModels(chatModel, value)}
      />

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
          <button onClick={() => setError(null)} aria-label="Dismiss error">×</button>
        </div>
      )}

      {activeView === 'chat' ? (
        <main
          id="chat-panel"
          className="workspace"
          role="tabpanel"
          aria-labelledby="chat-tab"
        >
          <ConversationSidebar
            conversations={conversations}
            activeId={activeId}
            canCreate={canCreate && !saving && !asking}
            onCreate={() => void createConversation()}
            onSelect={(conversation) => void openConversation(conversation)}
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
                  saved by the grounded answer flow will appear below.
                </p>
              )}
              {saving && <p className="saving-note">Saving model selection…</p>}
            </section>

            <ConversationMessages
              conversation={activeConversation}
              messages={messages}
              loading={loadingMessages}
              asking={asking}
              deleting={deletingConversation}
              onAsk={askQuestion}
              onDelete={() => void deleteActiveConversation()}
            />
          </div>
        </main>
      ) : (
        <main
          id="documents-panel"
          className="documents-workspace"
          role="tabpanel"
          aria-labelledby="documents-tab"
        >
          <section className="documents-intro">
            <p className="eyebrow">Document workspace</p>
            <h1>Documents</h1>
            <p>
              Upload and manage all local sources in one place. Inactive documents stay stored
              but are excluded from answers until you enable them again.
            </p>
          </section>

          <DocumentUpload
            embeddingModel={embeddingModel}
            enabled={canUpload}
            uploading={uploading}
            uploaded={uploaded}
            onUpload={uploadDocument}
          />

          <DocumentList
            documents={documents}
            loading={loading}
            deletingId={deletingDocumentId}
            togglingId={togglingDocumentId}
            onDelete={(document) => void deleteDocument(document)}
            onActiveChange={(document, isActive) =>
              void setDocumentActive(document, isActive)
            }
          />
        </main>
      )}
    </div>
  );
}

function isProcessingDocument(document: DocumentRecord): boolean {
  return document.status === 'queued' || document.status === 'processing';
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
