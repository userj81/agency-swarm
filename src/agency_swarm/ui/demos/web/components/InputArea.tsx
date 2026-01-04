"use client";

import { useState, useRef, useEffect, KeyboardEvent } from "react";

interface InputAreaProps {
  onSendMessage: (message: string) => Promise<void>;
  onCancel: () => void;
  isLoading: boolean;
  placeholder?: string;
}

export default function InputArea({
  onSendMessage,
  onCancel,
  isLoading,
  placeholder = "Type a message...",
}: InputAreaProps) {
  const [input, setInput] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
    }
  }, [input]);

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    // Send on Enter (without Shift)
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }

    // Escape to cancel
    if (e.key === "Escape" && isLoading) {
      onCancel();
    }
  };

  const handleSend = async () => {
    const trimmed = input.trim();
    if (!trimmed || isLoading) return;

    setInput("");
    await onSendMessage(trimmed);

    // Reset height
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  return (
    <div className="border-t border-gray-800 p-4">
      <div className="flex items-end gap-3 max-w-4xl mx-auto">
        {/* Textarea */}
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            id="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={isLoading}
            rows={1}
            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
            style={{ minHeight: "48px", maxHeight: "200px" }}
          />

          {/* Character count for long messages */}
          {input.length > 500 && (
            <div className="absolute bottom-2 right-2 text-xs text-gray-500">
              {input.length.toLocaleString()}
            </div>
          )}
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-2">
          {/* Cancel button (show when loading) */}
          {isLoading && (
            <button
              onClick={onCancel}
              className="p-3 bg-red-600 hover:bg-red-700 rounded-lg transition-colors"
              title="Cancel (Escape)"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}

          {/* Send button */}
          <button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            className="p-3 bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-700 disabled:cursor-not-allowed rounded-lg transition-colors"
            title="Send (Enter)"
          >
            {isLoading ? (
              <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
            ) : (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            )}
          </button>
        </div>
      </div>

      {/* Helper text */}
      <div className="text-xs text-gray-500 text-center mt-2">
        Press <kbd className="px-1 bg-gray-800 rounded">Enter</kbd> to send,
        <kbd className="px-1 bg-gray-800 rounded ml-1">Shift+Enter</kbd> for new line,
        <kbd className="px-1 bg-gray-800 rounded ml-1">Escape</kbd> to cancel
      </div>
    </div>
  );
}
