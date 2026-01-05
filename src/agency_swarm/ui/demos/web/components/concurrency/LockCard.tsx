"use client";

import { useState, useEffect } from "react";
import type { AgentLockState } from "@/types";

interface LockCardProps {
  lock: AgentLockState;
  onOverride?: (lockId: string, reason: string) => void;
}

const STAGE_COLORS = {
  acquired: "bg-blue-500",
  executing: "bg-yellow-500",
  releasing: "bg-green-500",
};

const STAGE_LABELS = {
  acquired: "Acquired",
  executing: "Executing",
  releasing: "Releasing",
};

function formatDuration(seconds: number): string {
  if (seconds < 1) return `${Math.round(seconds * 1000)}ms`;
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  const minutes = Math.floor(seconds / 60);
  const secs = Math.round(seconds % 60);
  return `${minutes}m ${secs}s`;
}

function getPriorityColor(priority: number): string {
  if (priority <= 2) return "text-red-400";
  if (priority <= 4) return "text-orange-400";
  if (priority <= 6) return "text-yellow-400";
  if (priority <= 8) return "text-blue-400";
  return "text-gray-400";
}

export default function LockCard({ lock, onOverride }: LockCardProps) {
  const [duration, setDuration] = useState(lock.duration_seconds);
  const [showOverride, setShowOverride] = useState(false);
  const [overrideReason, setOverrideReason] = useState("");

  // Update duration every second
  useEffect(() => {
    const interval = setInterval(() => {
      setDuration((prev) => prev + 1);
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  const handleOverride = () => {
    if (overrideReason.trim() && onOverride) {
      onOverride(lock.lock_id, overrideReason);
      setShowOverride(false);
      setOverrideReason("");
    }
  };

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 hover:border-gray-700 transition-colors">
      {/* Header - Agent and Tool */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 bg-indigo-600/20 text-indigo-400 text-xs font-medium rounded">
              {lock.agent_name}
            </span>
            <span className="text-gray-500">→</span>
            <span className="text-gray-300 text-sm font-medium">{lock.tool_name}</span>
          </div>
          <p className="text-xs text-gray-500 mt-1 font-mono">{lock.lock_id.slice(0, 8)}</p>
        </div>

        {/* Status Badge */}
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${STAGE_COLORS[lock.execution_stage]}`} />
          <span className="text-xs text-gray-400">{STAGE_LABELS[lock.execution_stage]}</span>
        </div>
      </div>

      {/* Details Grid */}
      <div className="grid grid-cols-3 gap-3 mb-3">
        {/* Duration */}
        <div>
          <p className="text-xs text-gray-500">Duration</p>
          <p className="text-sm font-semibold text-gray-200">{formatDuration(duration)}</p>
        </div>

        {/* Priority */}
        <div>
          <p className="text-xs text-gray-500">Priority</p>
          <p className={`text-sm font-semibold ${getPriorityColor(lock.priority)}`}>
            {lock.priority}/10
          </p>
        </div>

        {/* Retry Count */}
        <div>
          <p className="text-xs text-gray-500">Retries</p>
          <p className="text-sm font-semibold text-gray-200">{lock.retry_count}</p>
        </div>
      </div>

      {/* Waiting Queue */}
      {lock.waiting_queue.length > 0 && (
        <div className="mb-3 p-2 bg-gray-800/50 rounded border border-gray-700">
          <p className="text-xs text-gray-400 mb-1">
            Waiting Queue ({lock.waiting_queue.length})
          </p>
          <div className="space-y-1">
            {lock.waiting_queue.slice(0, 3).map((req) => (
              <div key={req.request_id} className="flex items-center justify-between text-xs">
                <span className="text-gray-300">{req.agent_name}</span>
                <span className="text-gray-500">
                  P{req.priority} · {formatDuration(req.waiting_duration || 0)}
                </span>
              </div>
            ))}
            {lock.waiting_queue.length > 3 && (
              <p className="text-xs text-gray-500">
                +{lock.waiting_queue.length - 3} more
              </p>
            )}
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center justify-between pt-3 border-t border-gray-800">
        <div className="text-xs text-gray-500">
          {lock.owner_thread_id && (
            <span>Thread: {lock.owner_thread_id}</span>
          )}
        </div>

        {!showOverride ? (
          <button
            onClick={() => setShowOverride(true)}
            className="px-3 py-1.5 text-xs font-medium text-red-400 hover:bg-red-900/20 rounded transition-colors"
          >
            Override Lock
          </button>
        ) : (
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={overrideReason}
              onChange={(e) => setOverrideReason(e.target.value)}
              placeholder="Reason..."
              className="px-2 py-1 text-xs bg-gray-800 border border-gray-700 rounded focus:outline-none focus:border-indigo-500"
              autoFocus
            />
            <button
              onClick={handleOverride}
              disabled={!overrideReason.trim()}
              className="px-2 py-1 text-xs font-medium bg-red-600 hover:bg-red-700 disabled:bg-gray-700 disabled:text-gray-500 text-white rounded transition-colors"
            >
              Confirm
            </button>
            <button
              onClick={() => {
                setShowOverride(false);
                setOverrideReason("");
              }}
              className="px-2 py-1 text-xs text-gray-400 hover:bg-gray-800 rounded transition-colors"
            >
              Cancel
            </button>
          </div>
        )}
      </div>

      {/* Expiry Warning */}
      {lock.expires_at && (
        <div className="mt-2 text-xs text-yellow-500">
          Expires: {new Date(lock.expires_at * 1000).toLocaleTimeString()}
        </div>
      )}
    </div>
  );
}
