// Run one (profile × model × question) through the full MCP tool-calling loop.

import { chatCompletion } from "./chat.js";
import { getProvider, providerKey, type Config } from "./config.js";
import type { MCPTools } from "./mcp.js";
import type { ChatMessage, RunResult, ToolCall } from "./types.js";

/** Most frequent element of a non-empty array. */
function mode(arr: string[]): string {
  const counts = new Map<string, number>();
  for (const x of arr) counts.set(x, (counts.get(x) || 0) + 1);
  let best = arr[0];
  let bestN = -1;
  for (const [k, v] of counts) if (v > bestN) ((best = k), (bestN = v));
  return best;
}

export async function runOne(
  cfg: Config,
  mcp: MCPTools,
  modelId: string,
  systemPrompt: string,
  question: string,
  provider = "openrouter",
): Promise<RunResult> {
  const prov = getProvider(cfg, provider);
  const key = providerKey(prov);
  if (!key) {
    throw new Error(
      `No API key for provider '${provider}' (set ${prov.api_key_env || "its api_key"}).`,
    );
  }
  const rcfg = cfg.run;
  const messages: ChatMessage[] = [
    { role: "system", content: systemPrompt },
    { role: "user", content: question },
  ];

  const toolCallsMade: ToolCall[] = [];
  let nIters = 0;
  let inTok = 0;
  let outTok = 0;
  const errors: string[] = [];
  const served: string[] = [];
  const t0 = Date.now();

  for (let i = 0; i < rcfg.max_tool_iterations; i++) {
    nIters++;
    let resp: any;
    try {
      resp = await chatCompletion({
        baseUrl: prov.base_url,
        apiKey: key,
        model: modelId,
        messages,
        tools: mcp.openaiTools,
        temperature: rcfg.temperature,
        timeoutMs: rcfg.request_timeout_s * 1000,
        retries: rcfg.retries,
        extraHeaders: prov.extra_headers,
        authHeader: prov.auth_header,
        authScheme: prov.auth_scheme,
      });
    } catch (e: any) {
      errors.push(String(e?.message || e));
      break;
    }

    const usage = resp.usage || {};
    inTok += usage.prompt_tokens || 0;
    outTok += usage.completion_tokens || 0;
    if (resp.model) served.push(resp.model);

    const msg = resp.choices?.[0]?.message;
    if (!msg) {
      errors.push("no message in response");
      break;
    }
    messages.push(msg);

    const tcs = msg.tool_calls;
    if (!tcs || !tcs.length) break; // model produced a final answer

    for (const tc of tcs) {
      const fn = tc.function?.name;
      let args: Record<string, unknown> = {};
      try {
        args = JSON.parse(tc.function?.arguments || "{}");
      } catch {
        errors.push(`bad JSON args for ${fn}`);
        args = {};
      }
      toolCallsMade.push({ name: fn, args });
      const result = await mcp.call(fn, args);
      messages.push({ role: "tool", tool_call_id: tc.id, name: fn, content: result });
    }
  }

  const latency = Math.round((Date.now() - t0) / 10) / 100;

  let final = "";
  for (let i = messages.length - 1; i >= 0; i--) {
    const m = messages[i];
    if (m.role === "assistant" && m.content) {
      final = typeof m.content === "string" ? m.content : JSON.stringify(m.content);
      break;
    }
  }

  const servedDistinct = [...new Set(served)];
  const servedModel = served.length ? mode(served) : null;

  return {
    answer: final,
    tool_calls: toolCallsMade,
    n_tool_calls: toolCallsMade.length,
    called_any_tool: toolCallsMade.length > 0,
    n_iters: nIters,
    in_tokens: inTok,
    out_tokens: outTok,
    latency_s: latency,
    errors,
    served_model: servedModel,
    served_models: servedDistinct,
    transcript: rcfg.save_transcripts ? messages : null,
  };
}
