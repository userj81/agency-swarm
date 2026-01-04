// Format utilities for the UI

/**
 * Format a timestamp as a relative time string (e.g., "2m ago", "3h ago")
 */
export function formatRelative(timestamp: string | null | undefined): string {
  if (!timestamp) return "-";

  try {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    const weeks = Math.floor(days / 7);

    if (seconds < 60) return `${seconds}s ago`;
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 48) return `${hours}h ago`;
    if (days < 14) return days === 1 ? "1 day ago" : `${days} days ago`;
    return weeks === 1 ? "1 week ago" : `${weeks} weeks ago`;
  } catch (e) {
    return "-";
  }
}

/**
 * Format a number with commas (e.g., 1,234,567)
 */
export function formatNumber(num: number): string {
  return num.toLocaleString();
}

/**
 * Format a cost as a string (e.g., "$0.0123")
 */
export function formatCost(cost: number): string {
  return `$${cost.toFixed(4)}`;
}

/**
 * Format token count with K/M suffixes
 */
export function formatTokens(tokens: number): string {
  if (tokens >= 1_000_000) {
    return `${(tokens / 1_000_000).toFixed(1)}M`;
  }
  if (tokens >= 1_000) {
    return `${(tokens / 1_000).toFixed(1)}K`;
  }
  return tokens.toString();
}

/**
 * Truncate text to a maximum length with ellipsis
 */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - 1) + "…";
}

/**
 * Escape HTML entities in text
 */
export function escapeHtml(text: string): string {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}
