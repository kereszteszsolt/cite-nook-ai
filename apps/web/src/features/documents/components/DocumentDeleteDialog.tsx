/*
 * SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
 * SPDX-License-Identifier: Apache-2.0
 */

import { DestructiveConfirmationDialog } from '../../../components/DestructiveConfirmationDialog';

interface DocumentDeleteDialogProps {
  fileName: string;
  deleting: boolean;
  onCancel: () => void;
  onConfirm: () => void;
}

export function DocumentDeleteDialog(props: DocumentDeleteDialogProps) {
  return (
    <DestructiveConfirmationDialog
      idPrefix="document-delete"
      title="Delete document?"
      description={
        <>
          <strong>{props.fileName}</strong>, its stored file, indexed chunks, and processing record
          will be permanently deleted. This action cannot be undone.
        </>
      }
      confirmLabel="Delete document"
      busyLabel="Deleting…"
      busy={props.deleting}
      onCancel={props.onCancel}
      onConfirm={props.onConfirm}
    />
  );
}
