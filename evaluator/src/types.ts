// Runtime types that aren't part of the config schema (see config.ts for those).

/** An OpenAI/OpenRouter-style chat message (loosely typed — we pass provider
 *  message objects through the tool loop verbatim, including raw `tool_calls`). */
export interface ChatMessage {
  role: string;
  content?: unknown;
  tool_calls?: any[];
  tool_call_id?: string;
  name?: string;
  [k: string]: unknown;
}

/** One tool invocation the model requested during the loop. */
export interface ToolCall {
  name: string;
  args: Record<string, unknown>;
}

/** Result of running a single (profile × model × question) through the tool loop. */
export interface RunResult {
  answer: string;
  tool_calls: ToolCall[];
  n_tool_calls: number;
  called_any_tool: boolean;
  n_iters: number;
  in_tokens: number;
  out_tokens: number;
  latency_s: number;
  errors: string[];
  served_model: string | null;
  served_models: string[];
  transcript: ChatMessage[] | null;
}

/** Judge scores: one numeric field per configured dimension name, plus notes. */
export type JudgeScores = Record<string, number | null | string>;

/** A flat output row (one per profile × model × question). */
export interface ResultRow {
  profile: string;
  model: string;
  model_id: string;
  served_model: string;
  served_models: string;
  qid: string;
  category: string;
  question: string;
  answer: string;
  called_any_tool: boolean;
  n_tool_calls: number;
  tools_used: string;
  n_iters: number;
  latency_s: number;
  in_tokens: number;
  out_tokens: number;
  cost_usd: number;
  errors: string;
  // score_<dimension> fields are added dynamically
  [k: string]: unknown;
}
