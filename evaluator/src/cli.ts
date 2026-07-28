// Entry point. Loads config, connects to the MCP server once, then runs the
// profile × model × question matrix (with configurable concurrency), scoring each
// answer with the judge and writing JSONL + scores JSON + a console summary.

import "dotenv/config";
import { existsSync, mkdirSync } from "node:fs";
import { join, resolve } from "node:path";
import {
  loadConfig,
  loadQuestions,
  type ModelConfig,
  type ProfileConfig,
  type Question,
} from "./config.js";
import { judgeOne } from "./judge.js";
import { MCPTools } from "./mcp.js";
import { loadPricing, resolvePrice } from "./pricing.js";
import { runPool } from "./pool.js";
import { appendJsonl, printSummary, writeScoresJson } from "./report.js";
import { runOne } from "./runner.js";
import type { ResultRow } from "./types.js";

interface Args {
  config: string;
  outdir: string;
  pricing: string;
  noJudge: boolean;
  limitModels: number;
  limitQuestions: number;
  concurrency?: number;
  profiles?: string[];
  listTools: boolean;
}

function parseArgs(argv: string[]): Args {
  const a: Args = {
    config: "config.json",
    outdir: "results",
    pricing: "pricing.json",
    noJudge: false,
    limitModels: 0,
    limitQuestions: 0,
    listTools: false,
  };
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    const next = () => argv[++i];
    switch (arg) {
      case "--config": a.config = next(); break;
      case "--outdir": a.outdir = next(); break;
      case "--pricing": a.pricing = next(); break;
      case "--no-judge": a.noJudge = true; break;
      case "--limit-models": a.limitModels = parseInt(next(), 10); break;
      case "--limit-questions": a.limitQuestions = parseInt(next(), 10); break;
      case "--concurrency": a.concurrency = parseInt(next(), 10); break;
      case "--profile": a.profiles = next().split(",").map((s) => s.trim()); break;
      case "--list-tools": a.listTools = true; break;
      case "-h":
      case "--help":
        printHelp();
        process.exit(0);
      default:
        console.error(`unknown flag: ${arg}`);
        process.exit(2);
    }
  }
  return a;
}

function printHelp(): void {
  console.log(`dhee-eval — sweep candidate LLMs across assistant profiles.

Usage: pnpm eval [options]

  --config <path>          config JSON (default: config.json)
  --outdir <dir>           output directory (default: results)
  --pricing <path>         pricing JSON for cost (default: pricing.json)
  --profile <a,b>          only run these profile name(s)
  --limit-models <n>       cap models under test
  --limit-questions <n>    cap questions per profile
  --concurrency <n>        parallel tasks (overrides run.concurrency)
  --no-judge               skip the LLM judge (faster smoke tests)
  --list-tools             connect to the MCP server, print its tools, exit
  -h, --help               this help`);
}

function stamp(): string {
  const d = new Date();
  const p = (n: number) => String(n).padStart(2, "0");
  return (
    `${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}_` +
    `${p(d.getHours())}${p(d.getMinutes())}${p(d.getSeconds())}`
  );
}

interface Task {
  profile: ProfileConfig;
  model: ModelConfig;
  question: Question;
}

async function main(): Promise<void> {
  const args = parseArgs(process.argv.slice(2));
  const { config, dir: configDir } = loadConfig(args.config);

  // Select profiles / models.
  let profiles = config.profiles;
  if (args.profiles) {
    profiles = profiles.filter((p) => args.profiles!.includes(p.name));
    if (!profiles.length) {
      console.error(`No profiles match --profile ${args.profiles.join(",")}.`);
      process.exit(2);
    }
  }
  let models = config.models;
  if (args.limitModels) models = models.slice(0, args.limitModels);

  const concurrency = args.concurrency ?? config.run.concurrency;
  if (concurrency > 1) {
    throw new Error(
      "Concurrency above 1 is disabled because this evaluator shares one MCP session. " +
        "Use --concurrency 1 until per-worker MCP session isolation is implemented.",
    );
  }
  const pricing = loadPricing(resolve(args.pricing));

  // Connect to the MCP server once; reuse the session for the whole eval.
  const mcp = await MCPTools.connect(config.mcp);
  try {
    const tools = await mcp.discover();
    console.log(
      `[MCP] discovered ${tools.length} tools: ${tools.map((t) => t.function.name).join(", ")}`,
    );
    if (args.listTools) return; // wiring check: connect + discover, then stop

    // Build the task matrix: for each profile -> its questions -> each model.
    const tasks: Task[] = [];
    for (const profile of profiles) {
      let questions = loadQuestions(profile, configDir);
      if (args.limitQuestions) questions = questions.slice(0, args.limitQuestions);
      for (const model of models) {
        for (const question of questions) tasks.push({ profile, model, question });
      }
    }
    console.log(
      `[plan] ${profiles.length} profile(s) × ${models.length} model(s) = ` +
        `${tasks.length} runs, concurrency ${concurrency}${args.noJudge ? ", judge OFF" : ""}\n`,
    );

    if (!existsSync(args.outdir)) mkdirSync(args.outdir, { recursive: true });
    const s = stamp();
    const jsonlPath = join(args.outdir, `runs_${s}.jsonl`);
    const scoresPath = join(args.outdir, `scores_${s}.json`);

    let done = 0;
    const rows = await runPool<Task, ResultRow>(tasks, concurrency, async (task) => {
      const { profile, model } = task;
      const q = task.question;
      const label = model.label || model.id;

      const rr = await runOne(config, mcp, model.id, profile.system_prompt, q.question, model.provider);
      const scores = args.noJudge
        ? {}
        : await judgeOne(config, profile, q.question, q.expectation || "", rr);

      const [cin, cout] = resolvePrice(rr.served_model, model.id, pricing);
      const cost = rr.in_tokens * cin + rr.out_tokens * cout;

      const row: ResultRow = {
        profile: profile.name,
        model: label,
        model_id: model.id,
        served_model: rr.served_model || model.id,
        served_models: rr.served_models.join(","),
        qid: q.id,
        category: q.category || "",
        question: q.question,
        answer: rr.answer,
        called_any_tool: rr.called_any_tool,
        n_tool_calls: rr.n_tool_calls,
        tools_used: rr.tool_calls.map((tc) => tc.name).join(","),
        n_iters: rr.n_iters,
        latency_s: rr.latency_s,
        in_tokens: rr.in_tokens,
        out_tokens: rr.out_tokens,
        cost_usd: Math.round(cost * 1e6) / 1e6,
        errors: rr.errors.join("; "),
      };
      for (const [k, v] of Object.entries(scores)) row[`score_${k}`] = v as never;

      // Persist immediately (full record incl. transcript).
      appendJsonl(jsonlPath, { ...row, transcript: rr.transcript });

      done++;
      const qual = (scores as any).answer_quality ?? "-";
      console.log(
        `[${done}/${tasks.length}] ${profile.name}/${label} ${q.id} ` +
          `tools=${rr.n_tool_calls} ${rr.latency_s}s q=${qual}${rr.errors.length ? " ERR" : ""}`,
      );
      return row;
    });

    writeScoresJson(scoresPath, rows);
    printSummary(rows, profiles);

    console.log(`\nPer-run detail : ${jsonlPath}`);
    console.log(`Scores JSON    : ${scoresPath}`);
    console.log("Open viewer/index.html and load the runs_*.jsonl to read answers + transcripts.");
  } finally {
    await mcp.close();
  }
}

main().catch((e) => {
  console.error(e?.stack || e?.message || e);
  process.exit(1);
});
