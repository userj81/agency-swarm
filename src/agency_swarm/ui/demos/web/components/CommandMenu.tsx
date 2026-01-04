"use client";

import { useState, useEffect, KeyboardEvent } from "react";
import { type SlashCommand, type CommandDefinition } from "@/types";

const COMMANDS: CommandDefinition[] = [
  {
    name: "help",
    description: "Show available commands and help",
    usage: "/help",
  },
  {
    name: "new",
    description: "Start a new chat session",
    usage: "/new",
  },
  {
    name: "compact",
    description: "Summarize current conversation and continue",
    usage: "/compact [instructions]",
    args: true,
  },
  {
    name: "resume",
    description: "Resume a previous conversation",
    usage: "/resume",
  },
  {
    name: "status",
    description: "Show current agency status and setup",
    usage: "/status",
  },
  {
    name: "cost",
    description: "Show usage statistics and costs",
    usage: "/cost",
  },
  {
    name: "exit",
    description: "Exit the current session",
    usage: "/exit",
  },
];

interface CommandMenuProps {
  onClose: () => void;
  onCommand: (command: SlashCommand, args?: string[]) => void;
  input: string;
  onInputChange: (value: string) => void;
}

export default function CommandMenu({
  onClose,
  onCommand,
  input,
  onInputChange,
}: CommandMenuProps) {
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [commandArgs, setCommandArgs] = useState("");

  // Filter commands based on input
  const filteredCommands = input
    ? COMMANDS.filter((cmd) => cmd.name.startsWith(input.toLowerCase()))
    : COMMANDS;

  useEffect(() => {
    setSelectedIndex(0);
    setCommandArgs("");
  }, [input]);

  const handleKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        setSelectedIndex((i) => (i + 1) % filteredCommands.length);
        break;
      case "ArrowUp":
        e.preventDefault();
        setSelectedIndex((i) => (i - 1 + filteredCommands.length) % filteredCommands.length);
        break;
      case "Enter":
        e.preventDefault();
        if (filteredCommands[selectedIndex]) {
          handleSelectCommand(filteredCommands[selectedIndex].name);
        }
        break;
      case "Escape":
        e.preventDefault();
        onClose();
        break;
      case "Tab":
        e.preventDefault();
        if (filteredCommands[selectedIndex]) {
          const cmd = filteredCommands[selectedIndex];
          onInputChange(cmd.name);
          if (cmd.args) {
            setCommandArgs(" ");
          }
        }
        break;
    }
  };

  const handleSelectCommand = (commandName: SlashCommand) => {
    const args = commandArgs.trim() ? commandArgs.trim().split(/\s+/) : undefined;
    onCommand(commandName, args);
  };

  return (
    <div
      className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div
        className="bg-gray-900 border border-gray-700 rounded-xl shadow-2xl w-full max-w-2xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
        onKeyDown={handleKeyDown}
        tabIndex={0}
      >
        {/* Header */}
        <div className="p-4 border-b border-gray-800">
          <div className="flex items-center gap-3">
            <span className="text-2xl">⌨️</span>
            <div>
              <h3 className="text-lg font-semibold">Command Menu</h3>
              <p className="text-sm text-gray-400">
                Type a command or select one below
              </p>
            </div>
          </div>

          {/* Search input */}
          <div className="mt-4 relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">
              /
            </span>
            <input
              type="text"
              value={input}
              onChange={(e) => onInputChange(e.target.value)}
              placeholder="Search commands..."
              className="w-full pl-8 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              autoFocus
            />
          </div>
        </div>

        {/* Command list */}
        <div className="max-h-80 overflow-y-auto p-2">
          {filteredCommands.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <p>No commands found</p>
            </div>
          ) : (
            <ul>
              {filteredCommands.map((cmd, index) => (
                <li key={cmd.name}>
                  <button
                    onClick={() => handleSelectCommand(cmd.name)}
                    onMouseEnter={() => setSelectedIndex(index)}
                    className={`w-full px-4 py-3 rounded-lg text-left transition-colors ${
                      index === selectedIndex
                        ? "bg-indigo-600/20 border border-indigo-500/50"
                        : "hover:bg-gray-800"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-indigo-400">/{cmd.name}</span>
                        </div>
                        <p className="text-sm text-gray-400 mt-1">{cmd.description}</p>
                      </div>
                      <kbd className="px-2 py-1 bg-gray-800 rounded text-xs text-gray-500">
                        Tab
                      </kbd>
                    </div>
                    <div className="mt-2 text-xs text-gray-500 font-mono">
                      {cmd.usage}
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Footer with hints */}
        <div className="p-3 border-t border-gray-800 flex items-center justify-between text-xs text-gray-500">
          <div className="flex items-center gap-4">
            <span><kbd className="px-1 bg-gray-800 rounded">↑↓</kbd> Navigate</span>
            <span><kbd className="px-1 bg-gray-800 rounded">Enter</kbd> Select</span>
            <span><kbd className="px-1 bg-gray-800 rounded">Esc</kbd> Close</span>
          </div>
          <span>{selectedIndex + 1} / {filteredCommands.length}</span>
        </div>
      </div>
    </div>
  );
}
