"use client";

import { useState } from "react";
import type { DeadlockInfo, DeadlockResolutionStrategy } from "@/types";

interface DeadlockAlertProps {
  deadlocks: DeadlockInfo[];
  onResolve: (cycle: string[], strategy: DeadlockResolutionStrategy) => Promise<boolean>;
}

const SEVERITY_COLORS = {
  low: "border-yellow-700 bg-yellow-900/20",
  medium: "border-orange-700 bg-orange-900/20",
  high: "border-red-700 bg-red-900/20",
};

const SEVERITY_ICONS = {
  low: "⚠️",
  medium: "🔶",
  high: "🚨",
};

export default function DeadlockAlert({ deadlocks, onResolve }: DeadlockAlertProps) {
  if (deadlocks.length === 0) {
    return null;
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <svg className="w-5 h-5 text-red-500 animate-pulse" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
        </svg>
        <h3 className="text-lg font-semibold text-red-400">
          {deadlocks.length} Deadlock{deadlocks.length > 1 ? "s" : ""} Detected
        </h3>
      </div>

      {deadlocks.map((deadlock) => (
        <DeadlockCard key={deadlock.deadlock_id} deadlock={deadlock} onResolve={onResolve} />
      ))}
    </div>
  );
}

interface DeadlockCardProps {
  deadlock: DeadlockInfo;
  onResolve: (cycle: string[], strategy: DeadlockResolutionStrategy) => Promise<boolean>;
}

function DeadlockCard({ deadlock, onResolve }: DeadlockCardProps) {
  const [isResolving, setIsResolving] = useState(false);
  const [selectedStrategy, setSelectedStrategy] = useState<DeadlockResolutionStrategy>("priority");

  const handleResolve = async () => {
    setIsResolving(true);
    await onResolve(deadlock.cycle, selectedStrategy);
    setIsResolving(false);
  };

  return (
    <div className={`border rounded-lg p-4 ${SEVERITY_COLORS[deadlock.severity]}`}>
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-2xl">{SEVERITY_ICONS[deadlock.severity]}</span>
          <div>
            <h4 className="font-semibold text-white">Deadlock Detected</h4>
            <p className="text-xs text-gray-400">
              {new Date(deadlock.detected_at * 1000).toLocaleTimeString()}
            </p>
          </div>
        </div>
        <span className={`px-2 py-1 text-xs font-medium rounded ${
          deadlock.severity === "high" ? "bg-red-900/50 text-red-300" :
          deadlock.severity === "medium" ? "bg-orange-900/50 text-orange-300" :
          "bg-yellow-900/50 text-yellow-300"
        }`}>
          {deadlock.severity.toUpperCase()}
        </span>
      </div>

      {/* Cycle Visualization */}
      <div className="mb-4">
        <p className="text-xs text-gray-400 mb-2">Deadlock Cycle:</p>
        <div className="flex items-center flex-wrap gap-1">
          {deadlock.cycle.map((agent, idx) => (
            <React.Fragment key={idx}>
              <span className="px-2 py-1 bg-gray-800 rounded text-sm font-mono">
                {agent}
              </span>
              {idx < deadlock.cycle.length - 1 && (
                <span className="text-gray-500">→</span>
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Resolution Controls */}
      <div className="space-y-3">
        <div>
          <label className="text-xs text-gray-400 block mb-1">Resolution Strategy:</label>
          <select
            value={selectedStrategy}
            onChange={(e) => setSelectedStrategy(e.target.value as DeadlockResolutionStrategy)}
            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-indigo-500"
          >
            <option value="priority">Priority Based (lowest priority)</option>
            <option value="youngest">Youngest First (most recent)</option>
            <option value="oldest">Oldest First (longest held)</option>
            <option value="random">Random Victim</option>
            <option value="manual">Manual (select specific lock)</option>
          </select>
        </div>

        <button
          onClick={handleResolve}
          disabled={isResolving}
          className="w-full px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-700 disabled:text-gray-500 text-white font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
        >
          {isResolving ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Resolving...
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              Auto-Resolve Deadlock
            </>
          )}
        </button>

        <p className="text-xs text-gray-500 text-center">
          This will release one lock to break the deadlock cycle
        </p>
      </div>
    </div>
  );
}
