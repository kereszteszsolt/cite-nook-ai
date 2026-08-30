/*
 * SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
 * SPDX-License-Identifier: Apache-2.0
 */

import { DocumentDeleteDialog } from './components/DocumentDeleteDialog';
import { DocumentList } from './components/DocumentList';
import { DocumentUpload } from './components/DocumentUpload';
import type { DocumentsController } from './useDocuments';

interface DocumentsWorkspaceProps {
  controller: DocumentsController;
  loading: boolean;
  embeddingModel: string;
}

export function DocumentsWorkspace({
  controller,
  loading,
  embeddingModel,
}: DocumentsWorkspaceProps) {
  const deleteTarget = controller.deleteTarget;

  return (
    <>
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
            Upload and manage all local sources in one place. Inactive documents stay stored but
            are excluded from answers until you enable them again.
          </p>
        </section>

        <DocumentUpload
          embeddingModel={embeddingModel}
          enabled={controller.canUpload}
          uploading={controller.uploading}
          uploaded={controller.uploaded}
          onUpload={controller.uploadDocument}
        />

        <DocumentList
          documents={controller.documents}
          loading={loading}
          deletingId={controller.deletingId}
          togglingId={controller.togglingId}
          onDelete={controller.setDeleteTarget}
          onActiveChange={(document, isActive) =>
            void controller.setDocumentActive(document, isActive)
          }
        />
      </main>

      {deleteTarget && (
        <DocumentDeleteDialog
          fileName={deleteTarget.fileName}
          deleting={controller.deletingId === deleteTarget.id}
          onCancel={() => controller.setDeleteTarget(null)}
          onConfirm={() => void controller.deleteDocument(deleteTarget)}
        />
      )}
    </>
  );
}
