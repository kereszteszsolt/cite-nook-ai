/*
 * SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Conversation } from '../../../types';

interface ConversationSidebarProps {
  conversations: Conversation[];
  activeId: string | null;
  canCreate: boolean;
  onCreate: () => void;
  onSelect: (conversation: Conversation) => void;
}

export function ConversationSidebar(props: ConversationSidebarProps) {
  return (
    <aside className="conversation-sidebar" aria-label="Conversations">
      <button
        className="primary-button full-width"
        onClick={props.onCreate}
        disabled={!props.canCreate}
      >
        New conversation
      </button>

      <div className="conversation-list">
        {props.conversations.map((conversation) => (
          <button
            key={conversation.id}
            className={
              conversation.id === props.activeId
                ? 'conversation-row active'
                : 'conversation-row'
            }
            onClick={() => props.onSelect(conversation)}
          >
            <strong>{conversation.title}</strong>
            <small>{conversation.chatModel}</small>
            <small>{conversation.embeddingModel}</small>
          </button>
        ))}
        {props.conversations.length === 0 && (
          <p className="empty-copy">No conversations yet.</p>
        )}
      </div>
    </aside>
  );
}
