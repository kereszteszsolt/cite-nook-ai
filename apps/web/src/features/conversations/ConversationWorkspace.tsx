/*
 * SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
 * SPDX-License-Identifier: Apache-2.0
 */

import type { ModelCatalog } from '../../types';
import {
  ConversationDeleteDialog,
  ConversationModelDialog,
} from './components/ConversationDialogs';
import { ConversationMessages } from './components/ConversationMessages';
import { ConversationSidebar } from './components/ConversationSidebar';
import { ConversationTitle } from './components/ConversationTitle';
import {
  preferredInstalled,
  type ConversationsController,
} from './useConversations';

interface ConversationWorkspaceProps {
  catalog: ModelCatalog | null;
  controller: ConversationsController;
}

export function ConversationWorkspace({ catalog, controller }: ConversationWorkspaceProps) {
  return (
    <>
      <main
        id="chat-panel"
        className="workspace"
        role="tabpanel"
        aria-labelledby="chat-tab"
      >
        <ConversationSidebar
          conversations={controller.conversations}
          activeId={controller.activeId}
          canCreate={
            Boolean(catalog) &&
            !controller.saving &&
            !controller.asking &&
            !controller.deleting
          }
          onCreate={() => controller.setModelDialog('create')}
          onSelect={(conversation) => void controller.openConversation(conversation)}
        />

        <div className="content-column">
          <section className="conversation-header">
            <div className="conversation-header-main">
              <ConversationTitle
                conversation={controller.activeConversation}
                saving={controller.renaming}
                onRename={controller.renameActiveConversation}
              />
              {controller.activeConversation && (
                <div className="conversation-header-actions">
                  <button
                    type="button"
                    className="model-edit-button"
                    disabled={controller.saving || controller.asking || controller.deleting}
                    onClick={() => controller.setModelDialog('edit')}
                  >
                    <SlidersIcon />
                    <span>Edit models</span>
                  </button>
                  <button
                    type="button"
                    className="conversation-delete-button"
                    disabled={controller.deleting || controller.asking || controller.saving}
                    onClick={() => controller.setDeleteDialogOpen(true)}
                  >
                    <TrashIcon />
                    <span>Delete conversation</span>
                  </button>
                </div>
              )}
            </div>
            {controller.activeConversation ? (
              <div className="conversation-model-summary" aria-label="Conversation models">
                <span>
                  <small>Chat model</small>
                  <strong>{controller.chatModel}</strong>
                </span>
                <span>
                  <small>Embedding model</small>
                  <strong>{controller.embeddingModel}</strong>
                </span>
              </div>
            ) : (
              <p className="conversation-header-note">
                Create a conversation and choose the two models it should remember.
              </p>
            )}
          </section>

          <ConversationMessages
            conversation={controller.activeConversation}
            messages={controller.messages}
            loading={controller.loadingMessages}
            asking={controller.asking}
            pendingQuestion={
              controller.pendingQuestion?.conversationId ===
              controller.activeConversation?.id
                ? (controller.pendingQuestion?.content ?? null)
                : null
            }
            onAsk={controller.askQuestion}
          />
        </div>
      </main>

      {controller.modelDialog && catalog && (
        <ConversationModelDialog
          key={`${controller.modelDialog}-${controller.activeConversation?.id ?? 'new'}`}
          mode={controller.modelDialog}
          chatModels={catalog.chatModels}
          embeddingModels={catalog.embeddingModels}
          defaultChatModel={catalog.defaultChatModel}
          defaultEmbeddingModel={catalog.defaultEmbeddingModel}
          initialChatModel={
            controller.modelDialog === 'edit'
              ? controller.chatModel
              : preferredInstalled(catalog.chatModels, catalog.defaultChatModel)
          }
          initialEmbeddingModel={
            controller.modelDialog === 'edit'
              ? controller.embeddingModel
              : preferredInstalled(catalog.embeddingModels, catalog.defaultEmbeddingModel)
          }
          saving={controller.saving}
          onCancel={() => controller.setModelDialog(null)}
          onSubmit={(nextChatModel, nextEmbeddingModel) => {
            if (controller.modelDialog === 'create') {
              void controller.createConversation(nextChatModel, nextEmbeddingModel);
            } else {
              void controller.changeModels(nextChatModel, nextEmbeddingModel);
            }
          }}
        />
      )}

      {controller.deleteDialogOpen && controller.activeConversation && (
        <ConversationDeleteDialog
          conversationTitle={controller.activeConversation.title}
          deleting={controller.deleting}
          onCancel={() => controller.setDeleteDialogOpen(false)}
          onConfirm={() => void controller.deleteActiveConversation()}
        />
      )}
    </>
  );
}

function SlidersIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" width="16" height="16">
      <path
        d="M4 7h10m4 0h2M4 17h2m4 0h10M14 4v6M6 14v6"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeWidth="1.8"
      />
    </svg>
  );
}

function TrashIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" width="16" height="16">
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
