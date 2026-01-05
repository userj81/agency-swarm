"use client";

import type { AgentLockState } from "@/types";
import LockCard from "./LockCard";

interface ActiveLocksTabProps {
  locks: AgentLockState[];
  isLoading: boolean;
  onOverrideLock: (lockId: string, reason: string) => Promise<boolean>;
}

export default function ActiveLocksTab({ locks, isLoading, onOverrideLock }: ActiveLocksTabProps) {
  const handleOverride = async (lockId: string, reason: string) => {
    await onOverrideLock(lockId, reason);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-sm text-gray-500">Loading locks...</p>
        </div>
      </div>
    );
  }

  if (locks.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <div className="w-12 h-12 bg-gray-800 rounded-full flex items-center justify-center mb-3">
          <svg className="w-6 h-6 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
        </div>
        <h3 className="text-lg font-semibold text-gray-300 mb-1">No Active Locks</h3>
        <p className="text-sm text-gray-500 max-w-xs">
          All tools are free. Locks will appear here when agents are executing tools.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Summary Header */}
      <div className="flex items-center justify-between px-1">
        <div className="flex items-center gap-4">
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wide">Total Locks</p>
            <p className="text-2xl font-semibold text-white">{locks.length}</p>
          </div>
          <div className="h-8 w-px bg-gray-800" />
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wide">Waiting</p>
            <p className="text-2xl font-semibold text-yellow-400">
              {locks.reduce((sum, lock) => sum + lock.waiting_queue.length, 0)}
            </p>
          </div>
        </div>
      </div>

      {/* Lock Cards Grid */}
      <div className="grid gap-4 md:grid-cols-2">
        {locks.map((lock) => (
          <LockCard key={lock.lock_id} lock={lock} onOverride={handleOverride} />
        ))}
      </div>
    </div>
  );
}
