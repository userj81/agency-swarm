"use client";

import { type ChatMetadata } from "@/types";
import { formatRelative } from "@/utils/format";

interface SidebarProps {
  chats: ChatMetadata[];
  currentChatId: string | null;
  onNewChat: () => void;
  onResumeChat: (chatId: string) => void;
  onClose: () => void;
}

export default function Sidebar({
  chats,
  currentChatId,
  onNewChat,
  onResumeChat,
  onClose,
}: SidebarProps) {
  return (
    <aside className="w-80 border-r border-gray-800 flex flex-col bg-gray-900/50">
      {/* Header */}
      <div className="p-4 border-b border-gray-800">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Chats</h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-800 rounded transition-colors lg:hidden"
            aria-label="Close sidebar"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* New chat button */}
        <button
          onClick={onNewChat}
          className="w-full px-4 py-2 bg-indigo-600 hover:bg-indigo-700 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          New Chat
        </button>
      </div>

      {/* Chat list */}
      <div className="flex-1 overflow-y-auto">
        {chats.length === 0 ? (
          <div className="p-4 text-center text-gray-500 text-sm">
            <p>No saved chats yet</p>
            <p className="text-xs mt-1">Start a conversation to see it here</p>
          </div>
        ) : (
          <ul className="divide-y divide-gray-800">
            {chats.map((chat) => (
              <li key={chat.chat_id}>
                <button
                  onClick={() => onResumeChat(chat.chat_id)}
                  className={`w-full px-4 py-3 text-left hover:bg-gray-800/50 transition-colors ${
                    chat.chat_id === currentChatId ? "bg-gray-800 border-l-2 border-indigo-500" : ""
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      {/* Summary */}
                      <p className="text-sm font-medium text-gray-200 truncate">
                        {chat.summary || "(no summary)"}
                      </p>

                      {/* Metadata */}
                      <div className="flex items-center gap-2 mt-1 text-xs text-gray-500">
                        <span>{formatRelative(chat.modified_at)}</span>
                        {chat.msgs > 0 && (
                          <>
                            <span>•</span>
                            <span>{chat.msgs} messages</span>
                          </>
                        )}
                        {chat.usage && chat.usage.total_cost > 0 && (
                          <>
                            <span>•</span>
                            <span>${chat.usage.total_cost.toFixed(4)}</span>
                          </>
                        )}
                      </div>

                      {/* Branch (if exists) */}
                      {chat.branch && (
                        <span className="inline-block mt-1 px-2 py-0.5 bg-gray-800 rounded text-xs text-gray-500">
                          {chat.branch}
                        </span>
                      )}
                    </div>

                    {/* Current indicator */}
                    {chat.chat_id === currentChatId && (
                      <span className="text-indigo-500">
                        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </span>
                    )}
                  </div>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-800 text-xs text-gray-500">
        <div className="flex items-center justify-between">
          <span>{chats.length} chat{chats.length !== 1 ? "s" : ""}</span>
          <span>Agency Swarm UI</span>
        </div>
      </div>
    </aside>
  );
}
