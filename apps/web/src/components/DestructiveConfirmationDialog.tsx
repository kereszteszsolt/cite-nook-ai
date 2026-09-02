/*
 * SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
 * SPDX-License-Identifier: Apache-2.0
 */

import { useEffect, useRef, type ReactNode } from 'react';

interface DestructiveConfirmationDialogProps {
  idPrefix: string;
  title: string;
  description: ReactNode;
  confirmLabel: string;
  busyLabel: string;
  busy: boolean;
  onCancel: () => void;
  onConfirm: () => void;
}

export function DestructiveConfirmationDialog(
  props: DestructiveConfirmationDialogProps,
) {
  const cancelRef = useRef<HTMLButtonElement>(null);
  const titleId = `${props.idPrefix}-title`;
  const descriptionId = `${props.idPrefix}-description`;

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key !== 'Escape' || props.busy) return;
      event.preventDefault();
      props.onCancel();
    }

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [props.busy, props.onCancel]);

  useEffect(() => {
    cancelRef.current?.focus();
  }, []);

  return (
    <div className="modal-backdrop" role="presentation">
      <section
        className="modal-card delete-dialog"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={descriptionId}
      >
        <div className="delete-dialog-icon" aria-hidden="true">
          <TrashIcon />
        </div>
        <div className="modal-heading">
          <p className="eyebrow danger-eyebrow">Permanent action</p>
          <h2 id={titleId}>{props.title}</h2>
          <p id={descriptionId}>{props.description}</p>
        </div>
        <div className="modal-actions">
          <button
            ref={cancelRef}
            type="button"
            className="secondary-button"
            disabled={props.busy}
            onClick={props.onCancel}
          >
            Cancel
          </button>
          <button
            type="button"
            className="modal-danger-button"
            disabled={props.busy}
            onClick={props.onConfirm}
          >
            {props.busy ? props.busyLabel : props.confirmLabel}
          </button>
        </div>
      </section>
    </div>
  );
}

function TrashIcon() {
  return (
    <svg viewBox="0 0 24 24" width="22" height="22">
      <path
        d="M8 8v10m4-10v10m4-10v10M5 5h14M9 5V3h6v2m2 0 1 16H6L7 5"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.8"
      />
    </svg>
  );
}
