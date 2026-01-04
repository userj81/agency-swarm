"use client";

import { type Message } from "@/types";
import { marked } from "marked";
import DOMPurify from "dompurify";

interface ChatContainerProps {
  messages: Message[];
  isLoading: boolean;
  error: string | null;
}

// Markdown renderer with syntax highlighting
const renderMarkdown = (content: string) => {
  const html = marked(content) as string;
  return DOMPurify.sanitize(html);
};

// Function call display
function FunctionCall({ name, arguments: args }: { name: string; arguments: string }) {
  return (
    <div className="my-2 p-3 bg-gray-900 rounded-lg border border-gray-700">
      <div className="flex items-center gap-2 text-sm">
        <span className="text-indigo-400 font-mono">🛠️ {name}</span>
      </div>
      <pre className="mt-2 text-xs text-gray-400 overflow-x-auto">
        {args}
      </pre>
    </div>
  );
}

// Function output display
function FunctionOutput({ output }: { output: string }) {
  return (
    <div className="my-2 p-3 bg-gray-800/50 rounded-lg border border-gray-700/50">
      <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
        <span>⚙️ Function Output</span>
      </div>
      <pre className="text-xs text-gray-400 overflow-x-auto whitespace-pre-wrap">
        {output}
      </pre>
    </div>
  );
}

// Reasoning display
function ReasoningBlock({ content }: { content: string }) {
  return (
    <div className="my-2 p-3 bg-purple-950/30 rounded-lg border border-purple-800/30">
      <div className="flex items-center gap-2 text-sm text-purple-400 mb-2">
        <span>🧠 Reasoning</span>
      </div>
      <div
        className="text-sm text-gray-400 prose prose-invert prose-sm max-w-none"
        dangerouslySetInnerHTML={{ __html: renderMarkdown(content) }}
      />
    </div>
  );
}

// Message bubble
function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";

  if (message.type === "message") {
    const agentName = message.agent || (isUser ? "User" : "Assistant");
    const content = message.content || "";

    return (
      <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
        <div className={`max-w-3xl ${isUser ? "order-2" : "order-1"}`}>
          {/* Agent header */}
          <div className={`flex items-center gap-2 mb-1 ${isUser ? "justify-end" : "justify-start"}`}>
            <span className={`text-xs font-medium ${
              isUser ? "text-gray-400" : "text-indigo-400"
            }`}>
              {isUser ? "👤 You" : `🤖 ${agentName}`}
            </span>
            {message.callerAgent && (
              <span className="text-xs text-gray-500">
                → {message.callerAgent}
              </span>
            )}
          </div>

          {/* Content */}
          <div className={`rounded-lg px-4 py-3 ${
            isUser
              ? "bg-indigo-600 text-white"
              : "bg-gray-800 text-gray-100"
          }`}>
            {content.includes("```") || content.includes("**") || content.includes("*") ? (
              <div
                className="prose prose-invert prose-sm max-w-none"
                dangerouslySetInnerHTML={{ __html: renderMarkdown(content) }}
              />
            ) : (
              <p className="whitespace-pre-wrap">{content}</p>
            )}
          </div>
        </div>
      </div>
    );
  }

  if (message.type === "reasoning") {
    const summary = message.summary?.[0]?.text || "";
    if (summary) {
      return <ReasoningBlock content={summary} />;
    }
    return null;
  }

  if (message.type === "function") {
    return (
      <div className="flex justify-start mb-2">
        <div className="max-w-3xl">
          <FunctionCall name={message.name} arguments={message.arguments} />
        </div>
      </div>
    );
  }

  if (message.type === "function_output") {
    return (
      <div className="flex justify-start mb-2">
        <div className="max-w-3xl">
          <FunctionOutput output={message.output} />
        </div>
      </div>
    );
  }

  return null;
}

// Loading indicator
function LoadingIndicator() {
  return (
    <div className="flex justify-start mb-4">
      <div className="bg-gray-800 rounded-lg px-4 py-3">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce" />
          <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce delay-100" />
          <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce delay-200" />
        </div>
      </div>
    </div>
  );
}

export default function ChatContainer({ messages, isLoading, error }: ChatContainerProps) {
  return (
    <div className="p-4">
      {messages.length === 0 && !isLoading && (
        <div className="flex flex-col items-center justify-center h-full text-gray-500">
          <div className="text-6xl mb-4">🤖</div>
          <h2 className="text-xl font-semibold mb-2">Welcome to Agency Swarm</h2>
          <p className="text-sm">Start a conversation with your AI agents</p>
          <div className="mt-6 text-sm space-y-1">
            <p><kbd className="px-2 py-1 bg-gray-800 rounded text-xs">Ctrl+K</kbd> Command menu</p>
            <p><kbd className="px-2 py-1 bg-gray-800 rounded text-xs">Ctrl+/</kbd> Focus input</p>
            <p><kbd className="px-2 py-1 bg-gray-800 rounded text-xs">@agent</kbd> Mention agent</p>
          </div>
        </div>
      )}

      {messages.map((message, index) => (
        <MessageBubble key={index} message={message} />
      ))}

      {isLoading && <LoadingIndicator />}

      {error && (
        <div className="bg-red-900/30 border border-red-700 rounded-lg px-4 py-3 text-red-300">
          <div className="flex items-center gap-2 mb-1">
            <span>⚠️</span>
            <span className="font-medium">Error</span>
          </div>
          <p className="text-sm">{error}</p>
        </div>
      )}
    </div>
  );
}
