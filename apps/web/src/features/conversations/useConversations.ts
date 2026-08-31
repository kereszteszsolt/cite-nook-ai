/*
 * SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMemo, useRef, useState } from 'react';
import { api } from '../../api';
import type {
  Conversation,
  ConversationMessage,
  ModelCatalog,
  ModelOption,
} from '../../types';

type ModelDialogMode = 'create' | 'edit';
type SetError = (message: string | null) => void;
interface PendingQuestion {
  conversationId: string;
  content: string;
}

export function useConversations(catalog: ModelCatalog | null, setError: SetError) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [chatModel, setChatModel] = useState('');
  const [embeddingModel, setEmbeddingModel] = useState('');
  const [saving, setSaving] = useState(false);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [asking, setAsking] = useState(false);
  const [pendingQuestion, setPendingQuestion] = useState<PendingQuestion | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [renaming, setRenaming] = useState(false);
  const [modelDialog, setModelDialog] = useState<ModelDialogMode | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const messageRequestId = useRef(0);

  const activeConversation = useMemo(
    () => conversations.find((conversation) => conversation.id === activeId) ?? null,
    [activeId, conversations],
  );

  async function fetchInitial(): Promise<Conversation[]> {
    return api.conversations();
  }

  async function restoreInitial(items: Conversation[], models: ModelCatalog) {
    setConversations(items);
    setMessages([]);
    const firstConversation = items[0];
    if (firstConversation) {
      await openConversation(firstConversation);
      return;
    }
    setActiveId(null);
    setChatModel(preferredInstalled(models.chatModels, models.defaultChatModel));
    setEmbeddingModel(
      preferredInstalled(models.embeddingModels, models.defaultEmbeddingModel),
    );
  }

  function restoreConversation(conversation: Conversation) {
    setActiveId(conversation.id);
    setChatModel(conversation.chatModel);
    setEmbeddingModel(conversation.embeddingModel);
  }

  async function openConversation(conversation: Conversation) {
    setModelDialog(null);
    setDeleteDialogOpen(false);
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

  async function createConversation(nextChatModel: string, nextEmbeddingModel: string) {
    if (
      !isInstalled(catalog?.chatModels ?? [], nextChatModel) ||
      !isInstalled(catalog?.embeddingModels ?? [], nextEmbeddingModel)
    ) {
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const created = await api.createConversation(nextChatModel, nextEmbeddingModel);
      setConversations((items) => [created, ...items]);
      restoreConversation(created);
      messageRequestId.current += 1;
      setMessages([]);
      setLoadingMessages(false);
      setModelDialog(null);
    } catch (cause) {
      setError(errorMessage(cause));
    } finally {
      setSaving(false);
    }
  }

  async function changeModels(
    nextChatModel: string,
    nextEmbeddingModel: string,
  ): Promise<boolean> {
    if (!activeId) return false;
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
      setChatModel(updated.chatModel);
      setEmbeddingModel(updated.embeddingModel);
      setModelDialog(null);
      return true;
    } catch (cause) {
      setError(errorMessage(cause));
      return false;
    } finally {
      setSaving(false);
    }
  }

  async function deleteActiveConversation() {
    if (!activeConversation) return;
    setDeleting(true);
    setError(null);
    try {
      await api.deleteConversation(activeConversation.id);
      const remaining = conversations.filter(
        (conversation) => conversation.id !== activeConversation.id,
      );
      setConversations(remaining);
      messageRequestId.current += 1;
      setMessages([]);
      setDeleteDialogOpen(false);
      if (remaining[0]) {
        await openConversation(remaining[0]);
      } else {
        setActiveId(null);
        setChatModel(
          preferredInstalled(catalog?.chatModels ?? [], catalog?.defaultChatModel ?? ''),
        );
        setEmbeddingModel(
          preferredInstalled(
            catalog?.embeddingModels ?? [],
            catalog?.defaultEmbeddingModel ?? '',
          ),
        );
      }
    } catch (cause) {
      setError(errorMessage(cause));
    } finally {
      setDeleting(false);
    }
  }

  async function renameActiveConversation(title: string): Promise<boolean> {
    if (!activeConversation) return false;
    setRenaming(true);
    setError(null);
    try {
      const updated = await api.updateConversationTitle(activeConversation.id, title);
      setConversations((items) =>
        items.map((conversation) =>
          conversation.id === updated.id ? updated : conversation,
        ),
      );
      return true;
    } catch (cause) {
      setError(errorMessage(cause));
      return false;
    } finally {
      setRenaming(false);
    }
  }

  async function askQuestion(question: string): Promise<boolean> {
    if (!activeConversation) return false;
    const conversationId = activeConversation.id;
    const requestId = messageRequestId.current;
    setAsking(true);
    setPendingQuestion({ conversationId, content: question });
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
      setPendingQuestion((pending) =>
        pending?.conversationId === conversationId ? null : pending,
      );
      setAsking(false);
    }
  }

  return {
    conversations,
    messages,
    activeId,
    activeConversation,
    chatModel,
    embeddingModel,
    saving,
    loadingMessages,
    asking,
    pendingQuestion,
    deleting,
    renaming,
    modelDialog,
    deleteDialogOpen,
    fetchInitial,
    restoreInitial,
    openConversation,
    createConversation,
    changeModels,
    deleteActiveConversation,
    renameActiveConversation,
    askQuestion,
    setModelDialog,
    setDeleteDialogOpen,
  };
}

export type ConversationsController = ReturnType<typeof useConversations>;

export function preferredInstalled(models: ModelOption[], preferred: string): string {
  if (models.some((model) => model.name === preferred && model.installed)) return preferred;
  return models.find((model) => model.installed)?.name ?? '';
}

function isInstalled(models: ModelOption[], selected: string): boolean {
  return models.some((model) => model.name === selected && model.installed);
}

function errorMessage(cause: unknown): string {
  return cause instanceof Error ? cause.message : 'An unexpected error occurred.';
}
