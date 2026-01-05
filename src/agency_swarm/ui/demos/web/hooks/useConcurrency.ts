"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import type {
  AgentLockState,
  LockEvent,
  ConflictEvent,
  ConcurrencyAnalytics,
  ConflictPattern,
  DeadlockInfo,
  DeadlockResolutionStrategy,
  ConcurrencyWebSocketEvent,
} from "@/types";

interface UseConcurrencyOptions {
  apiBase?: string;
  enableWebSocket?: boolean;
  refreshInterval?: number; // ms
}

interface UseConcurrencyResult {
  // State
  locks: AgentLockState[];
  lockHistory: LockEvent[];
  conflicts: ConflictEvent[];
  deadlocks: DeadlockInfo[];
  analytics: ConcurrencyAnalytics | null;
  patterns: ConflictPattern[];
  isConnected: boolean;
  isLoading: boolean;
  error: string | null;
  activeLocksCount: number;

  // Actions
  refreshLocks: () => Promise<void>;
  refreshHistory: () => Promise<void>;
  refreshConflicts: () => Promise<void>;
  refreshAnalytics: () => Promise<void>;
  refreshPatterns: () => Promise<void>;
  overrideLock: (lockId: string, reason: string) => Promise<boolean>;
  detectDeadlocks: () => Promise<DeadlockInfo[]>;
  resolveDeadlock: (
    cycle: string[],
    strategy?: DeadlockResolutionStrategy,
    victimLockId?: string
  ) => Promise<boolean>;

  // Connection
  connect: () => void;
  disconnect: () => void;
}

const DEFAULT_ANALYTICS: ConcurrencyAnalytics = {
  total_locks_acquired: 0,
  total_locks_released: 0,
  conflicts_detected: 0,
  deadlocks_resolved: 0,
  most_locked_agents: [],
  conflict_hotspots: [],
  peak_concurrency_time: null,
  avg_lock_duration: 0,
};

export function useConcurrency(options: UseConcurrencyOptions = {}): UseConcurrencyResult {
  const {
    apiBase = "/api",
    enableWebSocket = true,
    refreshInterval = 5000,
  } = options;

  // State
  const [locks, setLocks] = useState<AgentLockState[]>([]);
  const [lockHistory, setLockHistory] = useState<LockEvent[]>([]);
  const [conflicts, setConflicts] = useState<ConflictEvent[]>([]);
  const [deadlocks, setDeadlocks] = useState<DeadlockInfo[]>([]);
  const [analytics, setAnalytics] = useState<ConcurrencyAnalytics | null>(null);
  const [patterns, setPatterns] = useState<ConflictPattern[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // WebSocket ref
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const refreshIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Calculate active locks count
  const activeLocksCount = locks.length;

  // ============================================================================
  // API Calls
  // ============================================================================

  const refreshLocks = useCallback(async () => {
    try {
      const response = await fetch(`${apiBase}/concurrency/locks`);
      if (!response.ok) throw new Error("Failed to fetch locks");
      const data = await response.json();
      setLocks(data.locks || []);
      setError(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to fetch locks";
      setError(message);
    }
  }, [apiBase]);

  const refreshHistory = useCallback(async () => {
    try {
      const response = await fetch(`${apiBase}/concurrency/history?limit=100`);
      if (!response.ok) throw new Error("Failed to fetch history");
      const data = await response.json();
      setLockHistory(data.history || []);
    } catch (err) {
      console.error("Failed to fetch history:", err);
    }
  }, [apiBase]);

  const refreshConflicts = useCallback(async () => {
    try {
      const response = await fetch(`${apiBase}/concurrency/conflicts?limit=50`);
      if (!response.ok) throw new Error("Failed to fetch conflicts");
      const data = await response.json();
      setConflicts(data.conflicts || []);
    } catch (err) {
      console.error("Failed to fetch conflicts:", err);
    }
  }, [apiBase]);

  const refreshAnalytics = useCallback(async () => {
    try {
      const response = await fetch(`${apiBase}/concurrency/analytics`);
      if (!response.ok) throw new Error("Failed to fetch analytics");
      const data = await response.json();
      setAnalytics(data);
    } catch (err) {
      console.error("Failed to fetch analytics:", err);
      setAnalytics(DEFAULT_ANALYTICS);
    }
  }, [apiBase]);

  const refreshPatterns = useCallback(async () => {
    try {
      const response = await fetch(`${apiBase}/concurrency/patterns?top_n=10`);
      if (!response.ok) throw new Error("Failed to fetch patterns");
      const data = await response.json();
      setPatterns(data.patterns || []);
    } catch (err) {
      console.error("Failed to fetch patterns:", err);
    }
  }, [apiBase]);

  const overrideLock = useCallback(async (lockId: string, reason: string) => {
    try {
      const response = await fetch(`${apiBase}/concurrency/locks/${lockId}/override`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reason }),
      });
      if (!response.ok) throw new Error("Failed to override lock");
      await refreshLocks();
      return true;
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to override lock";
      setError(message);
      return false;
    }
  }, [apiBase, refreshLocks]);

  const detectDeadlocks = useCallback(async () => {
    try {
      const response = await fetch(`${apiBase}/concurrency/deadlocks/detect`, {
        method: "POST",
      });
      if (!response.ok) throw new Error("Failed to detect deadlocks");
      const data = await response.json();
      const detectedDeadlocks = data.deadlocks || [];
      setDeadlocks(detectedDeadlocks);
      return detectedDeadlocks;
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to detect deadlocks";
      setError(message);
      return [];
    }
  }, [apiBase]);

  const resolveDeadlock = useCallback(async (
    cycle: string[],
    strategy: DeadlockResolutionStrategy = "priority",
    victimLockId?: string
  ) => {
    try {
      const response = await fetch(`${apiBase}/concurrency/deadlocks/resolve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cycle, strategy, victim_lock_id: victimLockId }),
      });
      if (!response.ok) throw new Error("Failed to resolve deadlock");
      await refreshLocks();
      await detectDeadlocks();
      return true;
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to resolve deadlock";
      setError(message);
      return false;
    }
  }, [apiBase, refreshLocks, detectDeadlocks]);

  // ============================================================================
  // WebSocket Connection
  // ============================================================================

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}${apiBase}/ws/concurrency`;

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        setError(null);
      };

      ws.onmessage = (event) => {
        try {
          const message: ConcurrencyWebSocketEvent = JSON.parse(event.data);

          switch (message.type) {
            case "connected":
              // Initial connection, refresh data
              if (message.data && "active_locks" in message.data) {
                setLocks(message.data.active_locks as AgentLockState[]);
              }
              break;

            case "lock_event":
              // Update lock history and refresh locks
              if (message.data && "event_type" in message.data) {
                setLockHistory((prev) => [message.data as LockEvent, ...prev].slice(0, 100));
              }
              refreshLocks();
              break;

            case "conflict_event":
              // New conflict detected
              if (message.data) {
                setConflicts((prev) => [message.data as ConflictEvent, ...prev].slice(0, 50));
              }
              // If it's a deadlock, also update deadlocks list
              if (message.data && "conflict_type" in message.data && (message.data as ConflictEvent).conflict_type === "deadlock") {
                detectDeadlocks();
              }
              break;

            case "deadlock_detected":
              // Deadlock detected
              if (message.data) {
                setDeadlocks((prev) => [message.data as DeadlockInfo, ...prev]);
              }
              break;

            case "lock_released":
              // Lock was released
              refreshLocks();
              break;
          }
        } catch (err) {
          console.error("Failed to parse WebSocket message:", err);
        }
      };

      ws.onerror = () => {
        setError("WebSocket connection error");
      };

      ws.onclose = () => {
        setIsConnected(false);
        wsRef.current = null;

        // Attempt to reconnect
        if (enableWebSocket) {
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, 3000);
        }
      };
    } catch (err) {
      setError("Failed to connect to WebSocket");
    }
  }, [apiBase, enableWebSocket, refreshLocks, detectDeadlocks]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  // ============================================================================
  // Effects
  // ============================================================================

  // Initial data load
  useEffect(() => {
    const loadInitialData = async () => {
      setIsLoading(true);
      await Promise.all([
        refreshLocks(),
        refreshHistory(),
        refreshConflicts(),
        refreshAnalytics(),
        refreshPatterns(),
      ]);
      setIsLoading(false);
    };

    loadInitialData();
  }, [refreshLocks, refreshHistory, refreshConflicts, refreshAnalytics, refreshPatterns]);

  // Setup WebSocket connection
  useEffect(() => {
    if (enableWebSocket) {
      connect();

      return () => {
        disconnect();
      };
    }
  }, [enableWebSocket, connect, disconnect]);

  // Setup refresh interval
  useEffect(() => {
    if (refreshInterval > 0) {
      refreshIntervalRef.current = setInterval(() => {
        refreshLocks();
        refreshAnalytics();
      }, refreshInterval);

      return () => {
        if (refreshIntervalRef.current) {
          clearInterval(refreshIntervalRef.current);
        }
      };
    }
  }, [refreshInterval, refreshLocks, refreshAnalytics]);

  return {
    // State
    locks,
    lockHistory,
    conflicts,
    deadlocks,
    analytics,
    patterns,
    isConnected,
    isLoading,
    error,
    activeLocksCount,

    // Actions
    refreshLocks,
    refreshHistory,
    refreshConflicts,
    refreshAnalytics,
    refreshPatterns,
    overrideLock,
    detectDeadlocks,
    resolveDeadlock,

    // Connection
    connect,
    disconnect,
  };
}
