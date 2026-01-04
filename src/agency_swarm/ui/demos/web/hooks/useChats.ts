"use client";

import { useState, useEffect, useCallback } from "react";
import { type ChatMetadata } from "@/types";

interface UseChatsOptions {
  apiBase?: string;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

interface UseChatsResult {
  chats: ChatMetadata[];
  isLoading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  createChat: (chatId?: string) => Promise<string | null>;
  loadChat: (chatId: string) => Promise<ChatMetadata | null>;
  deleteChat: (chatId: string) => Promise<boolean>;
}

export function useChats(options: UseChatsOptions = {}): UseChatsResult {
  const { apiBase = "/api", autoRefresh = true, refreshInterval = 5000 } = options;

  const [chats, setChats] = useState<ChatMetadata[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${apiBase}/chats`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setChats(data.chats || []);
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : "Failed to fetch chats";
      setError(errMsg);
    } finally {
      setIsLoading(false);
    }
  }, [apiBase]);

  const createChat = useCallback(async (chatId?: string) => {
    try {
      const response = await fetch(`${apiBase}/chats/new`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: chatId ? JSON.stringify({ chat_id: chatId }) : undefined,
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      await refresh(); // Refresh the list
      return data.chat_id || null;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create chat");
      return null;
    }
  }, [apiBase, refresh]);

  const loadChat = useCallback(async (chatId: string) => {
    try {
      const response = await fetch(`${apiBase}/chats/${chatId}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return data as ChatMetadata;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load chat");
      return null;
    }
  }, [apiBase]);

  const deleteChat = useCallback(async (chatId: string) => {
    try {
      const response = await fetch(`${apiBase}/chats/${chatId}`, {
        method: "DELETE",
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      await refresh(); // Refresh the list
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete chat");
      return false;
    }
  }, [apiBase, refresh]);

  // Auto-refresh on mount and interval
  useEffect(() => {
    refresh();
    if (!autoRefresh) return;

    const interval = setInterval(refresh, refreshInterval);
    return () => clearInterval(interval);
  }, [refresh, autoRefresh, refreshInterval]);

  return {
    chats,
    isLoading,
    error,
    refresh,
    createChat,
    loadChat,
    deleteChat,
  };
}
