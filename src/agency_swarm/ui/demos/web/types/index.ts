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
