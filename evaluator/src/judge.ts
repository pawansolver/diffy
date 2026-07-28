// LLM-as-judge. The rubric is config-driven: each profile declares its own list
// of scoring dimensions, and the judge prompt is composed from them. Scores come
// back keyed by dimension name.

import { chatCompletion } from "./chat.js";
import { getProvider, providerKey, type Config, type ProfileConfig } from "./config.js";
import type { JudgeScores, RunResult } from "./types.js";
import { z } from "zod";

const DEFAULT_PREAMBLE = `You are a strict evaluator for an AI assistant.
You are given: the user QUESTION, an EXPECTATION note, the list of TOOL CALLS the
model made (names + args), the TOOL RESULTS it received, and the model's FINAL
ANSWER. Judge the answer against the expectation and the retrieved tool results.`;

/** Build the judge system prompt from the profile's dimensions. */
export function buildJudgeSystem(preamble: string, dimensions: ProfileConfig["dimensions"]): string {
  const dimLines = dimensions.map((d, i) => `${i + 1}. ${d.name}: ${d.description}`).join("\n");
  const jsonKeys = dimensions.map((d) => `"${d.name}":N`).join(",");
  return `${preamble}

Score each dimension 1-5 (5 best). Be harsh about hallucination and unsupported claims.

${dimLines}

Return ONLY a JSON object (no prose):
{${jsonKeys},"notes":"<=40 words"}`;
}

function emptyScores(profile: ProfileConfig, note: string): JudgeScores {
  const o: JudgeScores = {};
  for (const d of profile.dimensions) o[d.name] = null;
  o.notes = note;
  return o;
}

/** Parse and strictly validate an LLM judge response against the active rubric. */
export function parseJudgeScores(
  text: string,
  dimensions: ProfileConfig["dimensions"],
): JudgeScores {
  const start = text.indexOf("{");
  const end = text.lastIndexOf("}");
  if (start < 0 || end < start) {
    throw new Error("judge response did not contain a JSON object");
  }

  let json: unknown;
  try {
    json = JSON.parse(text.slice(start, end + 1));
  } catch (error: any) {
    throw new Error(`judge returned invalid JSON: ${error?.message || error}`);
  }

  const scoreShape: Record<string, z.ZodTypeAny> = {};
  for (const dimension of dimensions) {
    scoreShape[dimension.name] = z.number().int().min(1).max(5);
  }
  scoreShape.notes = z.string().trim().max(400);

  const parsed = z.object(scoreShape).strict().safeParse(json);
  if (!parsed.success) {
    const details = parsed.error.issues
      .map((issue) => `${issue.path.join(".") || "(root)"}: ${issue.message}`)
      .join("; ");
    throw new Error(`judge response failed schema validation: ${details}`);
  }
  return parsed.data as JudgeScores;
}

export async function judgeOne(
  cfg: Config,
  profile: ProfileConfig,
  question: string,
  expectation: string,
  runResult: RunResult,
): Promise<JudgeScores> {
  const jcfg = cfg.judge;
  const jprov = getProvider(cfg, jcfg.provider);
  const key = providerKey(jprov);
  if (!key) return emptyScores(profile, `judge error: no API key for provider '${jcfg.provider}'`);

  // Tool-result digest. NOTE: the judge MUST see at least what the model saw
  // (tool results are truncated to 12k chars in MCPTools.call). A tighter cap
  // here makes the judge flag legitimately-cited pages as "hallucinated" simply
  // because it never saw them — an unfair faithfulness failure.
  const toolResults: string[] = [];
  for (const m of runResult.transcript || []) {
    if (m.role === "tool") {
      toolResults.push(`[${m.name}] -> ${String(m.content).slice(0, jcfg.max_tool_result_chars)}`);
    }
  }

  const payload = {
    QUESTION: question,
    EXPECTATION: expectation,
    TOOL_CALLS: runResult.tool_calls,
    TOOL_RESULTS: toolResults.slice(0, jcfg.max_tool_results),
    FINAL_ANSWER: (runResult.answer || "").slice(0, jcfg.max_answer_chars),
  };

  const system = buildJudgeSystem(jcfg.preamble || DEFAULT_PREAMBLE, profile.dimensions);
  const messages = [
    { role: "system", content: system },
    { role: "user", content: JSON.stringify(payload) },
  ];

  try {
    const resp = await chatCompletion({
      baseUrl: jprov.base_url,
      apiKey: key,
      model: jcfg.id,
      messages,
      temperature: jcfg.temperature,
      timeoutMs: 120_000,
      retries: 2,
      extraHeaders: jprov.extra_headers,
      authHeader: jprov.auth_header,
      authScheme: jprov.auth_scheme,
    });
    const txt: string = resp.choices[0].message.content;
    return parseJudgeScores(txt, profile.dimensions);
  } catch (e: any) {
    return emptyScores(profile, `judge error: ${e?.message || e}`);
  }
}
