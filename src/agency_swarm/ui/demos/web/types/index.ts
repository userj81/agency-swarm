// Message types from OpenAI Agents SDK
export type MessageRole = "system" | "user" | "assistant";

export interface BaseMessage {
  type: string;
  role: MessageRole;
  content?: string;
}

export interface TextMessage extends BaseMessage {
  type: "message";
  role: MessageRole;
  content: string;
  agent?: string;
  callerAgent?: string;
}

export interface ReasoningMessage {
  type: "reasoning";
  summary?: Array<{ text: string }>;
}

export interface FunctionCallMessage {
  type: "function";
  name: string;
  arguments: string;
  call_id?: string;
  agent?: string;
}

export interface FunctionOutputMessage {
  type: "function_output";
  output: string;
  call_id?: string;
}

export interface AgentMessage {
  type: "agent_message";
  agent: string;
  content: string;
}

export type Message = TextMessage | ReasoningMessage | FunctionCallMessage | FunctionOutputMessage | AgentMessage;

// Chat metadata
export interface ChatMetadata {
  chat_id: string;
  created_at: string;
  modified_at: string;
  msgs: number;
  branch: string;
  summary: string;
  usage?: UsageStats;
}

// Usage tracking
export interface UsageStats {
  request_count: number;
  cached_tokens: number;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  total_cost: number;
  reasoning_tokens?: number;
  audio_tokens?: number;
}

// Agent info
export interface AgentInfo {
  name: string;
  description?: string;
  instructions?: string;
  model?: string;
}

// Agency info
export interface AgencyInfo {
  name: string;
  entry_points: string[];
  agents: Record<string, AgentInfo>;
  default_agent?: string;
}

// Stream events from backend
export interface StreamEvent {
  type: "text" | "reasoning" | "function" | "function_output" | "agent" | "error" | "done";
  data?: any;
  error?: string;
}

export interface TextDeltaEvent {
  type: "text";
  agent: string;
  delta: string;
  recipient?: string;
}

export interface ReasoningDeltaEvent {
  type: "reasoning";
  agent: string;
  delta: string;
}

export interface FunctionCallEvent {
  type: "function";
  agent: string;
  name: string;
  arguments: string;
}

export interface FunctionOutputEvent {
  type: "function_output";
  output: string;
}

export interface HandoffEvent {
  type: "agent";
  from: string;
  to: string;
}

// Command types
export type SlashCommand =
  | "help"
  | "new"
  | "compact"
  | "resume"
  | "status"
  | "cost"
  | "exit";

export interface CommandDefinition {
  name: SlashCommand;
  description: string;
  args?: boolean;
  usage: string;
}

// API request/response types
export interface SendMessageRequest {
  message: string;
  recipient_agent?: string;
  chat_id?: string;
}

export interface ExecuteCommandRequest {
  command: SlashCommand;
  args?: string[];
}

export interface NewChatResponse {
  chat_id: string;
}

export interface StatusResponse {
  agency: AgencyInfo;
  current_chat: string | null;
  cwd: string;
}

// ============================================================================
// Concurrency Types
// ============================================================================

export type ExecutionStage = "acquired" | "executing" | "releasing";
export type ConflictEventType = "deadlock" | "timeout" | "resource_exhaustion" | "priority_inversion";
export type DeadlockResolutionStrategy = "priority" | "youngest" | "oldest" | "random" | "manual";

export interface PendingLockRequest {
  request_id: string;
  agent_name: string;
  tool_name: string;
  priority: number;
  requested_at: number;
  retry_count: number;
  timeout_seconds: number;
  waiting_duration?: number;
}

export interface AgentLockState {
  agent_name: string;
  tool_name: string;
  lock_id: string;
  acquired_at: number;
  acquired_at_iso: string;
  expires_at: number | null;
  expires_at_iso: string | null;
  priority: number;
  owner_thread_id: number | null;
  retry_count: number;
  waiting_queue: PendingLockRequest[];
  duration_seconds: number;
  execution_stage: ExecutionStage;
}

export interface LockEvent {
  event_id: string;
  timestamp: number;
  timestamp_iso: string;
  event_type: string;
  agent_name: string;
  tool_name: string;
  lock_id: string;
  details: Record<string, unknown>;
}

export interface ConflictEvent {
  conflict_id: string;
  timestamp: number;
  timestamp_iso: string;
  conflict_type: ConflictEventType;
  involved_agents: string[];
  description: string;
  resolution: string | null;
  auto_resolved: boolean;
  resolved_at: number | null;
  resolved_at_iso: string | null;
}

export interface DeadlockInfo {
  cycle: string[];
  detected_at: number;
  detected_at_iso: string;
  deadlock_id: string;
  involved_locks: string[];
  severity: "low" | "medium" | "high";
}

export interface ConflictPattern {
  agent_a: string;
  agent_b: string;
  conflict_count: number;
  last_conflict_iso: string;
  avg_resolution_time: number;
}

export interface ConcurrencyAnalytics {
  total_locks_acquired: number;
  total_locks_released: number;
  conflicts_detected: number;
  deadlocks_resolved: number;
  most_locked_agents: Array<{ agent: string; count: number }>;
  conflict_hotspots: Array<{ agent_a: string; agent_b: string; count: number }>;
  peak_concurrency_time: string | null;
  avg_lock_duration: number;
}

// WebSocket event types
export type ConcurrencyEventType =
  | "lock_event"
  | "conflict_event"
  | "connected"
  | "echo"
  | "deadlock_detected"
  | "lock_released";

export interface ConcurrencyWebSocketEvent {
  type: ConcurrencyEventType;
  data?: LockEvent | ConflictEvent | DeadlockInfo | { active_locks: AgentLockState[] };
}

// ============================================================================
// Settings Types
// ============================================================================

export interface APIData {
  provider: string;
  key: string;
  validated: boolean;
  last_validated?: string;
  models?: string[];
}

export interface ModelConfig {
  default_model: string;
  temperature: number;
  max_tokens: number;
  top_p: number;
  frequency_penalty: number;
  presence_penalty: number;
}

export interface AgentModelOverride {
  agent_name: string;
  model?: string;
  temperature?: number;
  max_tokens?: number;
  top_p?: number;
  frequency_penalty?: number;
  presence_penalty?: number;
}

export interface SettingsEncryption {
  algorithm: string;
  salt: string | null;
  derived_key_hash: string | null;
}

export interface SettingsData {
  version: string;
  created_at: string;
  updated_at: string;
  encryption: SettingsEncryption;
  api_keys: Record<string, APIData>;
  model_config: ModelConfig;
  agent_overrides: Record<string, AgentModelOverride>;
}

export interface SettingsValidationResult {
  valid: boolean;
  provider: string;
  message: string;
  error?: string;
  models?: string[];
}

export interface UnlockSettingsRequest {
  password: string;
}

export interface UnlockSettingsResponse {
  success: boolean;
  data?: SettingsData;
  is_encrypted?: boolean;
  error?: string;
}

export interface ValidateKeyRequest {
  provider: string;
  key: string;
}

export interface ValidateKeyResponse {
  valid: boolean;
  provider: string;
  message: string;
  error?: string;
  models: string[];
}

export interface UpdateSettingsRequest {
  settings: SettingsData;
  password?: string;
}
