// Config schema (zod) + loader + provider resolution.
//
// The config is JSON. Top level is shared settings + a `profiles[]` list. Each
// profile has its own system prompt, questions file, and judge rubric
// (dimensions), but all profiles share one MCP server, one candidate-model list,
// one judge LLM, and one set of run settings.

import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { z } from "zod";

const ProviderSchema = z.object({
  base_url: z.string().url(),
  api_key_env: z.string().optional(),
  api_key: z.string().optional(),
  auth_header: z.string().default("Authorization"),
  auth_scheme: z.string().default("Bearer "),
  extra_headers: z.record(z.string()).default({}),
});

const ModelSchema = z.object({
  id: z.string(),
  label: z.string().optional(),
  provider: z.string().default("openrouter"),
});

const DimensionSchema = z.object({
  name: z.string().regex(/^[a-z][a-z0-9_]*$/, "must be a lowercase identifier"),
  description: z.string().default(""),
});

const ProfileSchema = z.object({
  name: z.string().min(1),
  questions: z.string().min(1),
  system_prompt: z.string().min(1),
  dimensions: z.array(DimensionSchema).min(1),
}).superRefine((profile, ctx) => {
  const names = profile.dimensions.map((dimension) => dimension.name);
  if (new Set(names).size !== names.length) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      path: ["dimensions"],
      message: "dimension names must be unique",
    });
  }
});

const JudgeSchema = z.object({
  id: z.string(),
  provider: z.string().default("openrouter"),
  temperature: z.number().default(0.0),
  preamble: z.string().optional(),
  max_tool_result_chars: z.number().default(12000),
  max_tool_results: z.number().default(20),
  max_answer_chars: z.number().default(16000),
});

const RunSchema = z.object({
  max_tool_iterations: z.number().default(10),
  temperature: z.number().default(0.2),
  request_timeout_s: z.number().default(120),
  retries: z.number().default(2),
  save_transcripts: z.boolean().default(true),
  concurrency: z.number().int().min(1).max(32).default(1),
});

const McpSchema = z.object({
  transport: z.enum(["stdio", "http"]).default("stdio"),
  stdio: z
    .object({
      command: z.string(),
      args: z.array(z.string()).default([]),
      env: z.record(z.string()).default({}),
      cwd: z.string().optional(),
    })
    .optional(),
  http: z
    .object({
      url: z.string(),
      headers: z.record(z.string()).default({}),
    })
    .optional(),
}).superRefine((mcp, ctx) => {
  if (mcp.transport === "stdio" && !mcp.stdio) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      path: ["stdio"],
      message: "stdio configuration is required for stdio transport",
    });
  }
  if (mcp.transport === "http" && !mcp.http) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      path: ["http"],
      message: "http configuration is required for http transport",
    });
  }
});

const ConfigSchema = z.object({
  providers: z.record(ProviderSchema).optional(),
  // legacy single-block fallback (kept so old configs keep working):
  openrouter: z.record(z.any()).optional(),
  mcp: McpSchema,
  models: z.array(ModelSchema).min(1),
  judge: JudgeSchema,
  run: RunSchema.default({}),
  profiles: z.array(ProfileSchema).min(1),
});

export type ProviderConfig = z.infer<typeof ProviderSchema>;
export type ModelConfig = z.infer<typeof ModelSchema>;
export type Dimension = z.infer<typeof DimensionSchema>;
export type ProfileConfig = z.infer<typeof ProfileSchema>;
export type JudgeConfig = z.infer<typeof JudgeSchema>;
export type RunConfig = z.infer<typeof RunSchema>;
export type Config = z.infer<typeof ConfigSchema>;

const QuestionSchema = z.object({
  id: z.string().min(1),
  category: z.string().min(1).optional(),
  question: z.string().min(1),
  expectation: z.string().min(1).optional(),
}).strict();

const QuestionsSchema = z.array(QuestionSchema).min(1).superRefine((questions, ctx) => {
  const ids = questions.map((question) => question.id);
  if (new Set(ids).size !== ids.length) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: "question ids must be unique",
    });
  }
});

export type Question = z.infer<typeof QuestionSchema>;

/** Load + validate the config JSON. Returns the parsed config and its directory
 *  (used to resolve relative `questions` paths). */
export function loadConfig(path: string): { config: Config; dir: string } {
  const abs = resolve(path);
  const raw = JSON.parse(readFileSync(abs, "utf8"));
  const parsed = ConfigSchema.safeParse(raw);
  if (!parsed.success) {
    const msg = parsed.error.issues
      .map((i) => `  - ${i.path.join(".") || "(root)"}: ${i.message}`)
      .join("\n");
    throw new Error(`Invalid config ${path}:\n${msg}`);
  }
  return { config: parsed.data, dir: dirname(abs) };
}

/** Load a profile's questions JSON (path resolved relative to the config file). */
export function loadQuestions(profile: ProfileConfig, configDir: string): Question[] {
  const abs = resolve(configDir, profile.questions);
  const raw = JSON.parse(readFileSync(abs, "utf8"));
  const parsed = QuestionsSchema.safeParse(raw);
  if (!parsed.success) {
    const msg = parsed.error.issues
      .map((issue) => `  - ${issue.path.join(".") || "(root)"}: ${issue.message}`)
      .join("\n");
    throw new Error(`Invalid questions file ${profile.questions}:\n${msg}`);
  }
  return parsed.data;
}

/** Resolve a provider by name. Falls back to the legacy `openrouter:` block so
 *  configs without a `providers:` section still work. */
export function getProvider(cfg: Config, name: string): ProviderConfig {
  const provs = cfg.providers || {};
  if (provs[name]) return provs[name];
  if (name === "openrouter" && cfg.openrouter) {
    const o = cfg.openrouter as Record<string, any>;
    return {
      base_url: o.base_url,
      api_key_env: o.api_key_env,
      api_key: o.api_key,
      auth_header: "Authorization",
      auth_scheme: "Bearer ",
      extra_headers: {
        "HTTP-Referer": o.referer || "",
        "X-Title": o.title || "",
      },
    };
  }
  throw new Error(`provider '${name}' is not configured (add it under providers:)`);
}

/** Resolve the API key for a provider (from env var, then inline). */
export function providerKey(p: ProviderConfig): string | undefined {
  return (p.api_key_env ? process.env[p.api_key_env] : undefined) || p.api_key;
}
