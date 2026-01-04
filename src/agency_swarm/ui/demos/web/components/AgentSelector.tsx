"use client";

import { useState, useEffect, useRef } from "react";
import { type AgentInfo } from "@/types";

interface AgentSelectorProps {
  selectedAgent: string | null;
  onAgentChange: (agent: string | null) => void;
}

// This would be fetched from the API in a real implementation
// For now, it's a placeholder that will be populated from the backend
const MOCK_AGENTS: AgentInfo[] = [
  { name: "CEO", description: "Agency coordinator" },
  { name: "Developer", description: "Code and technical tasks" },
  { name: "Analyst", description: "Data analysis" },
  { name: "Writer", description: "Content creation" },
];

export default function AgentSelector({
  selectedAgent,
  onAgentChange,
}: AgentSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [agents, setAgents] = useState<AgentInfo[]>(MOCK_AGENTS);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Fetch agents from API on mount
  useEffect(() => {
    fetch("/api/agents")
      .then((res) => res.json())
      .then((data) => {
        if (data.agents) {
          setAgents(data.agents);
        }
      })
      .catch((err) => {
        console.error("Failed to fetch agents:", err);
      });
  }, []);

  const selectedAgentData = agents.find((a) => a.name === selectedAgent);

  return (
    <div ref={dropdownRef} className="relative">
      {/* Trigger button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm transition-colors min-w-[140px] justify-between"
      >
        <span className="flex items-center gap-2">
          <span>🤖</span>
          <span>{selectedAgentData?.name || "All Agents"}</span>
        </span>
        <svg
          className={`w-4 h-4 transition-transform ${isOpen ? "rotate-180" : ""}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute top-full mt-2 right-0 w-64 bg-gray-900 border border-gray-700 rounded-lg shadow-xl z-30 overflow-hidden">
          {/* Clear selection */}
          {selectedAgent && (
            <button
              onClick={() => {
                onAgentChange(null);
                setIsOpen(false);
              }}
              className="w-full px-4 py-2 text-left hover:bg-gray-800 transition-colors flex items-center gap-2 border-b border-gray-800"
            >
              <span>👥</span>
              <div>
                <p className="text-sm">All Agents</p>
                <p className="text-xs text-gray-500">Auto-select based on context</p>
              </div>
            </button>
          )}

          {/* Agent list */}
          <ul>
            {agents.map((agent) => (
              <li key={agent.name}>
                <button
                  onClick={() => {
                    onAgentChange(agent.name === selectedAgent ? null : agent.name);
                    setIsOpen(false);
                  }}
                  className={`w-full px-4 py-2 text-left hover:bg-gray-800 transition-colors flex items-center gap-2 ${
                    agent.name === selectedAgent ? "bg-indigo-600/20 border-l-2 border-indigo-500" : ""
                  }`}
                >
                  <span>🤖</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{agent.name}</p>
                    {agent.description && (
                      <p className="text-xs text-gray-500 truncate">{agent.description}</p>
                    )}
                  </div>
                  {agent.name === selectedAgent && (
                    <svg className="w-4 h-4 text-indigo-400 shrink-0" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  )}
                </button>
              </li>
            ))}
          </ul>

          {/* Footer hint */}
          <div className="px-4 py-2 bg-gray-800/50 text-xs text-gray-500">
            Type <kbd className="px-1 bg-gray-700 rounded">@agent</kbd> in chat to mention
          </div>
        </div>
      )}
    </div>
  );
}
