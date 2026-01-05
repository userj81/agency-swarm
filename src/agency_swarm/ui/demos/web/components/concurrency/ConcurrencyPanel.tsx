"use client";

import { useState, useEffect } from "react";
import type { LockEvent, ConflictEvent, ConcurrencyAnalytics, ConflictPattern, DeadlockResolutionStrategy } from "@/types";
import ActiveLocksTab from "./ActiveLocksTab";
import DeadlockAlert from "./DeadlockAlert";

interface ConcurrencyPanelProps {
  onClose: () => void;

  // Locks
  locks: any[];
  locksLoading: boolean;
  refreshLocks: () => Promise<void>;
  overrideLock: (lockId: string, reason: string) => Promise<boolean>;

  // History
  lockHistory: LockEvent[];
  refreshHistory: () => Promise<void>;

  // Conflicts
  conflicts: ConflictEvent[];
  refreshConflicts: () => Promise<void>;

  // Analytics
  analytics: ConcurrencyAnalytics | null;
  refreshAnalytics: () => Promise<void>;

  // Patterns
  patterns: ConflictPattern[];
  refreshPatterns: () => Promise<void>;

  // Deadlocks
  deadlocks: any[];
  detectDeadlocks: () => Promise<any[]>;
  resolveDeadlock: (cycle: string[], strategy?: DeadlockResolutionStrategy) => Promise<boolean>;

  // Connection
  isConnected: boolean;
}

type TabValue = "locks" | "history" | "conflicts" | "analytics";

export default function ConcurrencyPanel({
  onClose,
  locks,
  locksLoading,
  refreshLocks,
  overrideLock,
  lockHistory,
  refreshHistory,
  conflicts,
  refreshConflicts,
  analytics,
  refreshAnalytics,
  patterns,
  refreshPatterns,
  deadlocks,
  detectDeadlocks,
  resolveDeadlock,
  isConnected,
}: ConcurrencyPanelProps) {
  const [activeTab, setActiveTab] = useState<TabValue>("locks");
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Auto-detect deadlocks when on locks tab
  useEffect(() => {
    if (activeTab === "locks") {
      detectDeadlocks();
    }
  }, [activeTab, detectDeadlocks]);

  const handleRefreshAll = async () => {
    setIsRefreshing(true);
    await Promise.all([
      refreshLocks(),
      refreshHistory(),
      refreshConflicts(),
      refreshAnalytics(),
      refreshPatterns(),
    ]);
    setIsRefreshing(false);
  };

  const handleResolveDeadlock = async (cycle: string[], strategy?: DeadlockResolutionStrategy) => {
    return await resolveDeadlock(cycle, strategy);
  };

  return (
    <div
      className="fixed inset-y-0 right-0 w-[480px] bg-gray-900 border-l border-gray-800 shadow-xl z-40 flex flex-col"
      onClick={(e) => e.stopPropagation()}
    >
      {/* Header */}
      <div className="p-4 border-b border-gray-800">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <span>🔒</span>
            Concurrency Monitor
          </h2>
          <div className="flex items-center gap-2">
            {/* Connection Status */}
            <div className={`flex items-center gap-1.5 px-2 py-1 rounded ${
              isConnected ? "bg-green-900/30 text-green-400" : "bg-gray-800 text-gray-500"
            }`}>
              <span className={`w-2 h-2 rounded-full ${isConnected ? "bg-green-400" : "bg-gray-500"}`} />
              <span className="text-xs">
                {isConnected ? "Live" : "Offline"}
              </span>
            </div>

            <button
              onClick={handleRefreshAll}
              disabled={isRefreshing}
              className="p-1.5 hover:bg-gray-800 rounded transition-colors disabled:opacity-50"
              title="Refresh all"
            >
              <svg className={`w-4 h-4 ${isRefreshing ? "animate-spin" : ""}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>

            <button
              onClick={onClose}
              className="p-1 hover:bg-gray-800 rounded transition-colors"
              aria-label="Close panel"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1">
          <TabButton value="locks" active={activeTab === "locks"} onClick={setActiveTab}>
            Locks ({locks.length})
          </TabButton>
          <TabButton value="history" active={activeTab === "history"} onClick={setActiveTab}>
            History
          </TabButton>
          <TabButton value="conflicts" active={activeTab === "conflicts"} onClick={setActiveTab}>
            Conflicts ({conflicts.length})
          </TabButton>
          <TabButton value="analytics" active={activeTab === "analytics"} onClick={setActiveTab}>
            Analytics
          </TabButton>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {/* Deadlock Alert */}
        {deadlocks.length > 0 && (
          <div className="mb-4">
            <DeadlockAlert deadlocks={deadlocks} onResolve={handleResolveDeadlock} />
          </div>
        )}

        {/* Tab Content */}
        {activeTab === "locks" && (
          <ActiveLocksTab
            locks={locks}
            isLoading={locksLoading}
            onOverrideLock={overrideLock}
          />
        )}

        {activeTab === "history" && (
          <LockHistoryTab events={lockHistory} onRefresh={refreshHistory} />
        )}

        {activeTab === "conflicts" && (
          <ConflictsTab
            conflicts={conflicts}
            patterns={patterns}
            onRefresh={refreshConflicts}
            onRefreshPatterns={refreshPatterns}
          />
        )}

        {activeTab === "analytics" && (
          <AnalyticsTab
            analytics={analytics}
            onRefresh={refreshAnalytics}
          />
        )}
      </div>

      {/* Footer */}
      <div className="p-3 border-t border-gray-800 flex items-center justify-between text-xs text-gray-500">
        <span>Real-time concurrency monitoring</span>
        {locks.length > 0 && (
          <span className="text-indigo-400">{locks.length} active lock{locks.length > 1 ? "s" : ""}</span>
        )}
      </div>
    </div>
  );
}

interface TabButtonProps {
  value: TabValue;
  active: boolean;
  onClick: (value: TabValue) => void;
  children: React.ReactNode;
}

function TabButton({ value, active, onClick, children }: TabButtonProps) {
  return (
    <button
      onClick={() => onClick(value)}
      className={`px-3 py-1.5 text-sm font-medium rounded transition-colors ${
        active
          ? "bg-indigo-600 text-white"
          : "text-gray-400 hover:text-gray-200 hover:bg-gray-800"
      }`}
    >
      {children}
    </button>
  );
}

// ============================================================================
// History Tab Component
// ============================================================================

interface LockHistoryTabProps {
  events: LockEvent[];
  onRefresh: () => Promise<void>;
}

function LockHistoryTab({ events, onRefresh }: LockHistoryTabProps) {
  const getEventColor = (eventType: string) => {
    switch (eventType) {
      case "acquired": return "bg-green-500";
      case "released": return "bg-gray-500";
      case "overridden": return "bg-red-500";
      case "queued": return "bg-yellow-500";
      case "timeout": return "bg-orange-500";
      default: return "bg-gray-500";
    }
  };

  return (
    <div className="space-y-3">
      {events.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <p>No lock history yet</p>
        </div>
      ) : (
        <div className="space-y-2">
          {events.map((event) => (
            <div key={event.event_id} className="flex items-start gap-3 p-3 bg-gray-800/50 rounded-lg">
              <span className={`w-2 h-2 rounded-full mt-1.5 ${getEventColor(event.event_type)}`} />
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-medium text-white capitalize">{event.event_type}</p>
                  <p className="text-xs text-gray-500">
                    {new Date(event.timestamp * 1000).toLocaleTimeString()}
                  </p>
                </div>
                <p className="text-xs text-gray-400 mt-1">
                  {event.agent_name} → {event.tool_name}
                </p>
                {Object.keys(event.details).length > 0 && (
                  <p className="text-xs text-gray-500 mt-1 truncate">
                    {JSON.stringify(event.details)}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Conflicts Tab Component
// ============================================================================

interface ConflictsTabProps {
  conflicts: ConflictEvent[];
  patterns: ConflictPattern[];
  onRefresh: () => Promise<void>;
  onRefreshPatterns: () => Promise<void>;
}

function ConflictsTab({ conflicts, patterns, onRefresh, onRefreshPatterns }: ConflictsTabProps) {
  return (
    <div className="space-y-4">
      {/* Conflict Patterns */}
      {patterns.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-gray-300 mb-2">Conflict Hotspots</h3>
          <div className="space-y-2">
            {patterns.slice(0, 5).map((pattern, idx) => (
              <div key={idx} className="flex items-center justify-between p-2 bg-gray-800/50 rounded">
                <div className="flex items-center gap-2">
                  <span className="text-red-400">⚡</span>
                  <span className="text-sm text-gray-300">
                    {pattern.agent_a} ↔ {pattern.agent_b}
                  </span>
                </div>
                <span className="text-xs font-medium text-red-400">
                  {pattern.conflict_count}x
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Conflict History */}
      <div>
        <h3 className="text-sm font-semibold text-gray-300 mb-2">Conflict History</h3>
        {conflicts.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p>No conflicts detected</p>
          </div>
        ) : (
          <div className="space-y-2">
            {conflicts.map((conflict) => (
              <div key={conflict.conflict_id} className="p-3 bg-gray-800/50 rounded-lg">
                <div className="flex items-center justify-between mb-1">
                  <span className={`px-2 py-0.5 text-xs font-medium rounded ${
                    conflict.conflict_type === "deadlock" ? "bg-red-900/50 text-red-300" :
                    conflict.conflict_type === "timeout" ? "bg-orange-900/50 text-orange-300" :
                    "bg-yellow-900/50 text-yellow-300"
                  }`}>
                    {conflict.conflict_type}
                  </span>
                  <span className="text-xs text-gray-500">
                    {new Date(conflict.timestamp * 1000).toLocaleString()}
                  </span>
                </div>
                <p className="text-sm text-gray-300">{conflict.description}</p>
                <div className="flex items-center justify-between mt-2 text-xs text-gray-500">
                  <span>{conflict.involved_agents.join(" → ")}</span>
                  {conflict.auto_resolved && (
                    <span className="text-green-400">Auto-resolved</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// Analytics Tab Component
// ============================================================================

interface AnalyticsTabProps {
  analytics: ConcurrencyAnalytics | null;
  onRefresh: () => Promise<void>;
}

function AnalyticsTab({ analytics, onRefresh }: AnalyticsTabProps) {
  if (!analytics) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-gray-500">Loading analytics...</div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-3">
        <StatCard label="Locks Acquired" value={analytics.total_locks_acquired} color="blue" />
        <StatCard label="Locks Released" value={analytics.total_locks_released} color="green" />
        <StatCard label="Conflicts" value={analytics.conflicts_detected} color="red" />
        <StatCard label="Deadlocks Resolved" value={analytics.deadlocks_resolved} color="purple" />
      </div>

      {/* Average Duration */}
      {analytics.avg_lock_duration > 0 && (
        <div className="p-3 bg-gray-800/50 rounded-lg">
          <p className="text-xs text-gray-400 mb-1">Average Lock Duration</p>
          <p className="text-lg font-semibold text-white">
            {analytics.avg_lock_duration.toFixed(2)}s
          </p>
        </div>
      )}

      {/* Most Locked Agents */}
      {analytics.most_locked_agents.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-gray-300 mb-2">Most Active Agents</h3>
          <div className="space-y-2">
            {analytics.most_locked_agents.slice(0, 5).map((agent, idx) => (
              <div key={idx} className="flex items-center justify-between p-2 bg-gray-800/50 rounded">
                <span className="text-sm text-gray-300">{agent.agent}</span>
                <span className="text-xs font-medium text-indigo-400">{agent.count} locks</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Conflict Hotspots */}
      {analytics.conflict_hotspots.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-gray-300 mb-2">Conflict Hotspots</h3>
          <div className="space-y-2">
            {analytics.conflict_hotspots.slice(0, 5).map((hotspot, idx) => (
              <div key={idx} className="flex items-center justify-between p-2 bg-gray-800/50 rounded">
                <span className="text-sm text-gray-300">
                  {hotspot.agent_a} ↔ {hotspot.agent_b}
                </span>
                <span className="text-xs font-medium text-red-400">{hotspot.count}x</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

interface StatCardProps {
  label: string;
  value: number;
  color?: "blue" | "green" | "red" | "purple" | "indigo";
}

function StatCard({ label, value, color = "indigo" }: StatCardProps) {
  const colorClasses = {
    blue: "text-blue-400",
    green: "text-green-400",
    red: "text-red-400",
    purple: "text-purple-400",
    indigo: "text-indigo-400",
  };

  return (
    <div className="bg-gray-800/50 rounded-lg p-3">
      <p className="text-xs text-gray-500 uppercase tracking-wide">{label}</p>
      <p className={`text-xl font-semibold ${colorClasses[color]}`}>
        {value.toLocaleString()}
      </p>
    </div>
  );
}
