"use client";

import { useState, useCallback, useRef } from "react";
import { type Message, type UsageStats, type SlashCommand } from "@/types";

interface UseChatOptions {
  apiBase?: string;
}

interface UseChatResult {
  messages: Message[];
  currentChatId: string | null;
  usage: UsageStats;
  isLoading: boolean;
  error: string | null;
  sendMessage: (message: string, recipientAgent?: string) => Promise<void>;
  executeCommand: (command: SlashCommand, args?: string[]) => Promise<void>;
  cancelStream: () => void;
  createNewChat: () => Promise<string | null>;
  resumeChat: (chatId: string) => Promise<boolean>;
}

const DEFAULT_USAGE: UsageStats = {
  request_count: 0,
  cached_tokens: 0,
  input_tokens: 0,
  output_tokens: 0,
  total_tokens: 0,
  total_cost: 0,
};

export function useChat(options: UseChatOptions = {}): UseChatResult {
  const { apiBase = "/api" } = options;

  const [messages, setMessages] = useState<Message[]>([]);
  const [currentChatId, setCurrentChatId] = useState<string | null>(null);
  const [usage, setUsage] = useState<UsageStats>(DEFAULT_USAGE);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const processStream = useCallback(async (
    response: Response,
    onMessage?: (message: Message) => void,
    onUsage?: (usage: UsageStats) => void,
    onDone?: () => void
  ) => {
    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error("No response body");
    }

    const decoder = new TextDecoder();
    let buffer = "";

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = line.slice(6);
            if (data === "[DONE]") {
              onDone?.();
              continue;
            }

            try {
              const event = JSON.parse(data);
              switch (event.type) {
                case "text":
                case "reasoning":
                case "function":
                case "function_output":
                case "agent":
                  onMessage?.(event);
                  break;
                case "usage":
                  onUsage?.(event.data);
                  break;
                case "error":
                  setError(event.error || "Unknown error");
                  break;
              }
            } catch (e) {
              console.error("Failed to parse SSE data:", data, e);
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }, []);

  const sendMessage = useCallback(async (
    message: string,
    recipientAgent?: string
  ) => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = new AbortController();

    setIsLoading(true);
    setError(null);

    // Add user message immediately
    const userMessage: Message = {
      type: "message",
      role: "user",
      content: message,
    };
    setMessages((prev) => [...prev, userMessage]);

    try {
      const response = await fetch(`${apiBase}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message,
          recipient_agent: recipientAgent,
          chat_id: currentChatId,
        }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Update chat ID from response headers if available
      const newChatId = response.headers.get("X-Chat-ID");
      if (newChatId) {
        setCurrentChatId(newChatId);
      }

      const assistantMessages: Message[] = [];

      await processStream(
        response,
        (msg) => {
          // Append or update message in stream
          if (msg.type === "text" || msg.type === "reasoning") {
            const lastIdx = assistantMessages.length - 1;
            if (lastIdx >= 0 && assistantMessages[lastIdx].type === msg.type) {
              // Delta update
              const lastMsg = assistantMessages[lastIdx];
              if ("content" in lastMsg && "content" in msg) {
                (lastMsg as any).content += (msg as any).delta || "";
              } else if ("summary" in lastMsg && "summary" in msg) {
                (lastMsg as any).summary = (msg as any).summary;
              }
            } else {
              assistantMessages.push(msg);
            }
          } else {
            assistantMessages.push(msg);
          }
          setMessages((prev) => [...prev.slice(0, -1), userMessage, ...assistantMessages]);
        },
        (newUsage) => {
          setUsage(newUsage);
        }
      );

    } catch (err) {
      const errMsg = err instanceof Error ? err.message : "Unknown error";
      setError(errMsg);
      // Remove user message if failed
      setMessages((prev) => prev.slice(0, -1));
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  }, [apiBase, currentChatId, processStream]);

  const executeCommand = useCallback(async (
    command: SlashCommand,
    args?: string[]
  ) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${apiBase}/command`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command, args }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();

      // Handle specific commands
      switch (command) {
        case "new":
          const newChatId = result.chat_id;
          setCurrentChatId(newChatId);
          setMessages([]);
          setUsage(DEFAULT_USAGE);
          break;
        case "resume":
          setCurrentChatId(result.chat_id);
          setMessages(result.messages || []);
          setUsage(result.usage || DEFAULT_USAGE);
          break;
        case "compact":
          // Compact adds a summary message
          if (result.summary) {
            setMessages((prev) => [...prev, result.summary]);
          }
          setCurrentChatId(result.chat_id);
          break;
        case "status":
          // Status is info only, could show in a modal
          console.log("Agency status:", result);
          break;
        case "cost":
          // Update usage from command
          if (result.usage) {
            setUsage(result.usage);
          }
          break;
      }

    } catch (err) {
      const errMsg = err instanceof Error ? err.message : "Unknown error";
      setError(errMsg);
    } finally {
      setIsLoading(false);
    }
  }, [apiBase]);

  const cancelStream = useCallback(() => {
    abortControllerRef.current?.abort();
    setIsLoading(false);
  }, []);

  const createNewChat = useCallback(async () => {
    try {
      const response = await fetch(`${apiBase}/chats/new`, {
        method: "POST",
      });
      if (!response.ok) throw new Error("Failed to create chat");
      const data = await response.json();
      const chatId = data.chat_id;
      setCurrentChatId(chatId);
      setMessages([]);
      setUsage(DEFAULT_USAGE);
      return chatId;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create chat");
      return null;
    }
  }, [apiBase]);

  const resumeChat = useCallback(async (chatId: string) => {
    try {
      const response = await fetch(`${apiBase}/chats/${chatId}`, {
        method: "POST",
      });
      if (!response.ok) throw new Error("Failed to resume chat");
      const data = await response.json();
      setCurrentChatId(chatId);
      setMessages(data.messages || []);
      setUsage(data.usage || DEFAULT_USAGE);
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to resume chat");
      return false;
    }
  }, [apiBase]);

  return {
    messages,
    currentChatId,
    usage,
    isLoading,
    error,
    sendMessage,
    executeCommand,
    cancelStream,
    createNewChat,
    resumeChat,
  };
}
