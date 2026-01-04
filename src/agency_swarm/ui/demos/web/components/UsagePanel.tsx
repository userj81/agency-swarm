"use client";

import { type UsageStats } from "@/types";

interface UsagePanelProps {
  usage: UsageStats;
  onClose: () => void;
}

function StatCard({ label, value, unit, color = "indigo" }: {
  label: string;
  value: number;
  unit?: string;
  color?: string;
}) {
  const colorClasses = {
    indigo: "text-indigo-400",
    green: "text-green-400",
    blue: "text-blue-400",
    purple: "text-purple-400",
  }[color] || "text-gray-400";

  return (
    <div className="bg-gray-900 rounded-lg p-4">
      <p className="text-xs text-gray-500 uppercase tracking-wide">{label}</p>
      <p className={`text-2xl font-semibold mt-1 ${colorClasses}`}>
        {value.toLocaleString()}
        {unit && <span className="text-sm text-gray-500 ml-1">{unit}</span>}
      </p>
    </div>
  );
}

export default function UsagePanel({ usage, onClose }: UsagePanelProps) {
  const avgCostPerToken = usage.total_tokens > 0
    ? usage.total_cost / usage.total_tokens
    : 0;

  return (
    <div
      className="fixed inset-y-0 right-0 w-96 bg-gray-900 border-l border-gray-800 shadow-xl z-40 flex flex-col"
      onClick={(e) => e.stopPropagation()}
    >
      {/* Header */}
      <div className="p-4 border-b border-gray-800 flex items-center justify-between">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <span>💰</span>
          Usage & Costs
        </h2>
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

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {/* Total cost */}
        <div className="bg-gradient-to-br from-green-900/30 to-green-950/30 border border-green-800/30 rounded-lg p-4">
          <p className="text-sm text-gray-400 mb-1">Total Cost</p>
          <p className="text-3xl font-bold text-green-400">
            ${usage.total_cost.toFixed(4)}
          </p>
          <p className="text-xs text-gray-500 mt-2">
            across {usage.request_count} request{usage.request_count !== 1 ? "s" : ""}
          </p>
        </div>

        {/* Token stats grid */}
        <div className="grid grid-cols-2 gap-3">
          <StatCard
            label="Input Tokens"
            value={usage.input_tokens}
            color="blue"
          />
          <StatCard
            label="Output Tokens"
            value={usage.output_tokens}
            color="purple"
          />
          <StatCard
            label="Cached Tokens"
            value={usage.cached_tokens}
            color="green"
          />
          <StatCard
            label="Total Tokens"
            value={usage.total_tokens}
            color="indigo"
          />
        </div>

        {/* Special token types */}
        {(usage.reasoning_tokens || usage.audio_tokens) && (
          <div className="space-y-3">
            {usage.reasoning_tokens !== undefined && usage.reasoning_tokens > 0 && (
              <StatCard
                label="Reasoning Tokens"
                value={usage.reasoning_tokens}
                color="purple"
              />
            )}
            {usage.audio_tokens !== undefined && usage.audio_tokens > 0 && (
              <StatCard
                label="Audio Tokens"
                value={usage.audio_tokens}
                color="blue"
              />
            )}
          </div>
        )}

        {/* Average cost */}
        {usage.total_tokens > 0 && (
          <div className="bg-gray-800/50 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-400">Avg. Cost / 1K Tokens</span>
              <span className="text-lg font-semibold text-gray-200">
                ${(avgCostPerToken * 1000).toFixed(4)}
              </span>
            </div>
          </div>
        )}

        {/* Token distribution bar */}
        {usage.total_tokens > 0 && (
          <div>
            <p className="text-sm text-gray-400 mb-2">Token Distribution</p>
            <div className="h-3 bg-gray-800 rounded-full overflow-hidden flex">
              {/* Input */}
              <div
                className="bg-blue-500"
                style={{
                  width: `${(usage.input_tokens / usage.total_tokens) * 100}%`,
                }}
                title={`Input: ${usage.input_tokens.toLocaleString()}`}
              />
              {/* Cached */}
              <div
                className="bg-green-500"
                style={{
                  width: `${(usage.cached_tokens / usage.total_tokens) * 100}%`,
                }}
                title={`Cached: ${usage.cached_tokens.toLocaleString()}`}
              />
              {/* Output */}
              <div
                className="bg-purple-500"
                style={{
                  width: `${(usage.output_tokens / usage.total_tokens) * 100}%`,
                }}
                title={`Output: ${usage.output_tokens.toLocaleString()}`}
              />
            </div>
            <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 bg-blue-500 rounded-full" />
                Input
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 bg-green-500 rounded-full" />
                Cached
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 bg-purple-500 rounded-full" />
                Output
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-800 text-xs text-gray-500">
        <p>Costs are estimated based on model pricing</p>
      </div>
    </div>
  );
}
