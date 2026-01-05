"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import ChatContainer from "@/components/ChatContainer";
import InputArea from "@/components/InputArea";
import Sidebar from "@/components/Sidebar";
import CommandMenu from "@/components/CommandMenu";
import UsagePanel from "@/components/UsagePanel";
import AgentSelector from "@/components/AgentSelector";
import ConcurrencyPanel from "@/components/concurrency/ConcurrencyPanel";
import { useChat } from "@/hooks/useChat";
import { useChats } from "@/hooks/useChats";
import { useConcurrency } from "@/hooks/useConcurrency";
import { type AgentInfo, type UsageStats } from "@/types";

export default function HomePage() {
  const router = useRouter();
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [showUsage, setShowUsage] = useState(false);
  const [showConcurrency, setShowConcurrency] = useState(false);
  const [showCommandMenu, setShowCommandMenu] = useState(false);
  const [commandInput, setCommandInput] = useState("");
  const chatEndRef = useRef<HTMLDivElement>(null);

  const {
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
  } = useChat();

  const {
    chats,
    createChat: createChatRecord,
    loadChat: loadChatRecord,
  } = useChats();

  // Concurrency hook
  const {
    locks,
    lockHistory,
    conflicts,
    deadlocks,
    analytics,
    patterns,
    isConnected,
    isLoading: concurrencyLoading,
    refreshLocks,
    refreshHistory,
    refreshConflicts,
    refreshAnalytics,
    refreshPatterns,
    overrideLock,
    detectDeadlocks,
    resolveDeadlock,
    activeLocksCount,
  } = useConcurrency({ enableWebSocket: true });

  // Auto-scroll to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl/Cmd + K for command menu
      if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault();
        setShowCommandMenu(true);
      }
      // ESC to close modals
      if (e.key === "Escape") {
        setShowCommandMenu(false);
        setShowUsage(false);
        setShowConcurrency(false);
      }
      // Ctrl/Cmd + / for focus input
      if ((e.ctrlKey || e.metaKey) && e.key === "/") {
        e.preventDefault();
        document.getElementById("chat-input")?.focus();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const handleSendMessage = async (content: string) => {
    // Check for agent mention
    const agentMatch = content.match(/^@(\w+)\s*/);
    let agent = selectedAgent;
    let message = content;

    if (agentMatch) {
      agent = agentMatch[1];
      message = content.slice(agentMatch[0].length);
      setSelectedAgent(agent);
    }

    await sendMessage(message, agent || undefined);
  };

  const handleCommand = async (command: string, args?: string[]) => {
    setShowCommandMenu(false);
    await executeCommand(command, args);
  };

  const handleNewChat = async () => {
    const newChatId = await createNewChat();
    if (newChatId) {
      await createChatRecord(newChatId);
    }
  };

  const handleResumeChat = async (chatId: string) => {
    const success = await resumeChat(chatId);
    if (success) {
      await loadChatRecord(chatId);
    }
  };

  return (
    <div className="flex h-screen bg-gray-950 text-gray-100">
      {/* Sidebar - Chat History */}
      {sidebarOpen && (
        <Sidebar
          chats={chats}
          currentChatId={currentChatId}
          onNewChat={handleNewChat}
          onResumeChat={handleResumeChat}
          onClose={() => setSidebarOpen(false)}
        />
      )}

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="border-b border-gray-800 px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            {!sidebarOpen && (
              <button
                onClick={() => setSidebarOpen(true)}
                className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
                aria-label="Open sidebar"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
            )}
            <h1 className="text-xl font-bold text-white">Agency Swarm</h1>
            {currentChatId && (
              <span className="text-sm text-gray-500">#{currentChatId.slice(0, 8)}</span>
            )}
          </div>

          <div className="flex items-center gap-2">
            {/* Agent Selector */}
            <AgentSelector
              selectedAgent={selectedAgent}
              onAgentChange={setSelectedAgent}
            />

            {/* Settings Button */}
            <button
              onClick={() => router.push('/settings')}
              className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
              aria-label="Settings"
              title="Settings"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 2.924 0 0 1 2.499 2.499 2.499 0 0 1 2.499-2.499zM19 13a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v6z" />
              </svg>
            </button>

            {/* Concurrency Button */}
            <button
              onClick={() => setShowConcurrency(!showConcurrency)}
              className="p-2 hover:bg-gray-800 rounded-lg transition-colors relative"
              aria-label="Show concurrency monitor"
              title="Concurrency Monitor"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              {activeLocksCount > 0 && (
                <span className="absolute -top-1 -right-1 bg-indigo-600 text-xs w-4 h-4 rounded-full flex items-center justify-center">
                  {activeLocksCount > 9 ? "9+" : activeLocksCount}
                </span>
              )}
              {isConnected && (
                <span className="absolute -bottom-0.5 -right-0.5 w-2 h-2 bg-green-500 rounded-full border border-gray-950" />
              )}
            </button>

            {/* Usage Button */}
            <button
              onClick={() => setShowUsage(!showUsage)}
              className="p-2 hover:bg-gray-800 rounded-lg transition-colors relative"
              aria-label="Show usage"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              {usage.total_tokens > 0 && (
                <span className="absolute -top-1 -right-1 bg-green-600 text-xs w-4 h-4 rounded-full flex items-center justify-center">
                  $
                </span>
              )}
            </button>

            {/* New Chat Button */}
            <button
              onClick={handleNewChat}
              className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 rounded-lg text-sm font-medium transition-colors"
            >
              New Chat
            </button>

            {/* Command Menu Button */}
            <button
              onClick={() => setShowCommandMenu(true)}
              className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
              title="Press Ctrl+K"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
            </button>
          </div>
        </header>

        {/* Chat Messages */}
        <div className="flex-1 overflow-y-auto">
          <ChatContainer
            messages={messages}
            isLoading={isLoading}
            error={error}
          />
          <div ref={chatEndRef} />
        </div>

        {/* Input Area */}
        <InputArea
          onSendMessage={handleSendMessage}
          onCancel={cancelStream}
          isLoading={isLoading}
          placeholder={
            selectedAgent
              ? `Message @${selectedAgent}... (Ctrl+/ to focus, Ctrl+K for commands)`
              : "Type a message... (Ctrl+/ to focus, Ctrl+K for commands)"
          }
        />
      </div>

      {/* Usage Panel */}
      {showUsage && (
        <UsagePanel
          usage={usage}
          onClose={() => setShowUsage(false)}
        />
      )}

      {/* Concurrency Panel */}
      {showConcurrency && (
        <ConcurrencyPanel
          onClose={() => setShowConcurrency(false)}
          locks={locks}
          locksLoading={concurrencyLoading}
          refreshLocks={refreshLocks}
          overrideLock={overrideLock}
          lockHistory={lockHistory}
          refreshHistory={refreshHistory}
          conflicts={conflicts}
          refreshConflicts={refreshConflicts}
          analytics={analytics}
          refreshAnalytics={refreshAnalytics}
          patterns={patterns}
          refreshPatterns={refreshPatterns}
          deadlocks={deadlocks}
          detectDeadlocks={detectDeadlocks}
          resolveDeadlock={resolveDeadlock}
          isConnected={isConnected}
        />
      )}

      {/* Command Menu */}
      {showCommandMenu && (
        <CommandMenu
          onClose={() => setShowCommandMenu(false)}
          onCommand={handleCommand}
          input={commandInput}
          onInputChange={setCommandInput}
        />
      )}
    </div>
  );
}
