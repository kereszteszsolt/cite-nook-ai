/*
 * SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
 * SPDX-License-Identifier: Apache-2.0
 */

import { useEffect, useState } from 'react';
import { api } from '../../api';
import type { DocumentRecord, ModelOption, StoredUpload } from '../../types';

const DOCUMENT_POLL_INTERVAL_MS = 2000;
type SetError = (message: string | null) => void;

export function useDocuments(
  embeddingModel: string,
  embeddingModels: ModelOption[],
  setError: SetError,
) {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploaded, setUploaded] = useState<StoredUpload | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<DocumentRecord | null>(null);
  const [togglingId, setTogglingId] = useState<string | null>(null);
  const canUpload = isInstalled(embeddingModels, embeddingModel);
  const hasProcessingDocuments = documents.some(isProcessingDocument);

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
  }, [hasProcessingDocuments, setError]);

  async function fetchInitial(): Promise<DocumentRecord[]> {
    return api.documents();
  }

  function restoreInitial(items: DocumentRecord[]) {
    setDocuments(items);
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
    setDeletingId(document.id);
    setError(null);
    try {
      await api.deleteDocument(document.id);
      setDocuments((items) => items.filter((item) => item.id !== document.id));
      if (uploaded?.id === document.id) setUploaded(null);
      setDeleteTarget(null);
    } catch (cause) {
      setError(errorMessage(cause));
    } finally {
      setDeletingId(null);
    }
  }

  async function setDocumentActive(document: DocumentRecord, isActive: boolean) {
    setTogglingId(document.id);
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
      setTogglingId(null);
    }
  }

  return {
    documents,
    uploading,
    uploaded,
    deletingId,
    deleteTarget,
    togglingId,
    canUpload,
    fetchInitial,
    restoreInitial,
    uploadDocument,
    deleteDocument,
    setDocumentActive,
    setDeleteTarget,
  };
}

export type DocumentsController = ReturnType<typeof useDocuments>;

function isProcessingDocument(document: DocumentRecord): boolean {
  return document.status === 'queued' || document.status === 'processing';
}

function isInstalled(models: ModelOption[], selected: string): boolean {
  return models.some((model) => model.name === selected && model.installed);
}

function errorMessage(cause: unknown): string {
  return cause instanceof Error ? cause.message : 'An unexpected error occurred.';
}
