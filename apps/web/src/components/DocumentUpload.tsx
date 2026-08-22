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
        <span id="document-file-label" className="upload-field-label">
          Document file
        </span>
        <div className="file-picker">
          <input
            ref={inputRef}
            className="file-picker-input"
            id="document-file"
            type="file"
            aria-labelledby="document-file-label"
            aria-describedby="document-file-name"
            accept=".pdf,.docx,.txt,.md,.markdown,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain,text/markdown"
            disabled={!props.enabled || props.uploading}
            onChange={(event: ChangeEvent<HTMLInputElement>) =>
              setFile(event.target.files?.[0] ?? null)
            }
          />
          <label
            htmlFor="document-file"
            className={`file-picker-control ${!props.enabled || props.uploading ? 'disabled' : ''}`}
            aria-disabled={!props.enabled || props.uploading}
          >
            <span className="file-picker-button">
              <FileIcon />
              Choose file
            </span>
            <span id="document-file-name" className="file-picker-name" aria-live="polite">
              {file?.name ?? 'No file selected'}
            </span>
          </label>
        </div>
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

function FileIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" width="17" height="17">
      <path
        d="M6 3h8l4 4v14H6V3Zm8 0v5h4M9 13h6M9 17h4"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.8"
      />
    </svg>
  );
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}
