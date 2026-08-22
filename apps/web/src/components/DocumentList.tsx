/*
 * SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
 * SPDX-License-Identifier: Apache-2.0
 */

import { api } from '../api';
import type { DocumentRecord, DocumentStatus } from '../types';

interface DocumentListProps {
  documents: DocumentRecord[];
  loading: boolean;
  deletingId: string | null;
  onDelete: (document: DocumentRecord) => void;
}

export function DocumentList(props: DocumentListProps) {
  return (
    <section className="document-list-panel" aria-labelledby="document-list-heading">
      <div className="document-list-heading">
        <div>
          <p className="eyebrow">Documents</p>
          <h2 id="document-list-heading">Stored documents</h2>
        </div>
        <p aria-live="polite">
          {props.documents.length} {props.documents.length === 1 ? 'document' : 'documents'}
        </p>
      </div>

      {props.loading ? (
        <p className="document-list-state" role="status">Loading documents…</p>
      ) : props.documents.length === 0 ? (
        <p className="document-list-state">No documents uploaded yet.</p>
      ) : (
        <div className="document-table-scroll">
          <table className="document-table">
            <thead>
              <tr>
                <th scope="col">File</th>
                <th scope="col">Size</th>
                <th scope="col">Embedding model</th>
                <th scope="col">Status</th>
                <th scope="col">Chunks</th>
                <th scope="col">Uploaded</th>
                <th scope="col"><span className="visually-hidden">Actions</span></th>
              </tr>
            </thead>
            <tbody>
              {props.documents.map((document) => (
                <DocumentRows
                  key={document.id}
                  document={document}
                  deleting={props.deletingId === document.id}
                  onDelete={props.onDelete}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

function DocumentRows(props: {
  document: DocumentRecord;
  deleting: boolean;
  onDelete: (document: DocumentRecord) => void;
}) {
  const { document } = props;
  return (
    <>
      <tr>
        <td className="document-name" title={document.fileName}>{document.fileName}</td>
        <td>{formatBytes(document.sizeBytes)}</td>
        <td className="document-model" title={document.embeddingModel}>
          {document.embeddingModel}
        </td>
        <td><StatusBadge status={document.status} /></td>
        <td>{document.chunkCount}</td>
        <td>
          <time dateTime={document.createdAt}>{formatDate(document.createdAt)}</time>
        </td>
        <td>
          <div className="document-actions">
            <a
              className="secondary-link"
              href={api.documentFileUrl(document.id)}
              target="_blank"
              rel="noreferrer"
            >
              Open
            </a>
            <button
              className="danger-button"
              disabled={props.deleting}
              onClick={() => props.onDelete(document)}
              aria-label={`Delete ${document.fileName}`}
            >
              {props.deleting ? 'Deleting…' : 'Delete'}
            </button>
          </div>
        </td>
      </tr>
      {document.status === 'failed' && document.errorMessage && (
        <tr className="document-error-row">
          <td colSpan={7}>
            <strong>Processing failed:</strong> {document.errorMessage}
          </td>
        </tr>
      )}
    </>
  );
}

function StatusBadge({ status }: { status: DocumentStatus }) {
  return <span className={`document-status ${status}`}>{status}</span>;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function formatDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date);
}
