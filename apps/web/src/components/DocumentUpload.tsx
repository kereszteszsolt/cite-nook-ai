/*
 * SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
 * SPDX-License-Identifier: Apache-2.0
 */

import { useRef, useState, type ChangeEvent, type FormEvent } from 'react';
import type { StoredUpload } from '../types';

interface DocumentUploadProps {
  embeddingModel: string;
  enabled: boolean;
  uploading: boolean;
  uploaded: StoredUpload | null;
  onUpload: (file: File) => Promise<boolean>;
}

export function DocumentUpload(props: DocumentUploadProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [file, setFile] = useState<File | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!file || !props.enabled || props.uploading) return;
    if (!(await props.onUpload(file))) return;
    setFile(null);
    if (inputRef.current) inputRef.current.value = '';
  }

  return (
    <section className="upload-panel" aria-labelledby="upload-heading">
      <div>
        <p className="eyebrow">Documents</p>
        <h2 id="upload-heading">Upload a document</h2>
        <p>Supported formats: PDF, DOCX, TXT, and Markdown.</p>
      </div>

      <form className="upload-form" onSubmit={(event) => void submit(event)}>
        <label htmlFor="document-file">Document file</label>
        <input
          ref={inputRef}
          id="document-file"
          type="file"
          accept=".pdf,.docx,.txt,.md,.markdown,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain,text/markdown"
          disabled={!props.enabled || props.uploading}
          onChange={(event: ChangeEvent<HTMLInputElement>) =>
            setFile(event.target.files?.[0] ?? null)
          }
        />
        <button
          className="primary-button"
          disabled={!file || !props.enabled || props.uploading}
        >
          {props.uploading ? 'Uploading…' : 'Upload'}
        </button>
      </form>

      <p className="upload-note">
        {props.enabled ? (
          <>
            New uploads use <strong>{props.embeddingModel}</strong>.
          </>
        ) : (
          <>Select an installed embedding model before uploading.</>
        )}
      </p>

      {props.uploaded && (
        <div className="upload-success" role="status">
          <strong>{props.uploaded.fileName}</strong> was stored successfully.
          <small>
            {formatBytes(props.uploaded.sizeBytes)} · SHA-256 {props.uploaded.sha256}
          </small>
        </div>
      )}
    </section>
  );
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}
