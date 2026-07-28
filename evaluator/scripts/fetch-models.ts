// Refresh pricing.json from the live OpenRouter models API.
//
// Fetches https://openrouter.ai/api/v1/models, keeps only tool-capable models
// (those advertising "tools" in supported_parameters), and writes them as JSON:
//   [{ id, name, context, in_per_M, out_per_M, multimodal, reasoning }, ...]
//
// Sarvam models are NOT on OpenRouter; their pricing rows are appended manually
// so the harness can still compute $/q for them.
//
// Usage:  pnpm fetch-models            -> pricing.json
//         pnpm fetch-models --out x.json

import "dotenv/config";
import { writeFileSync } from "node:fs";

const MODELS_URL = "https://openrouter.ai/api/v1/models";

// Sarvam is not on OpenRouter — keep its pricing so $/q still resolves.
const SARVAM_ROWS = [
  { id: "sarvam-30b", name: "Sarvam: Sarvam-30B", context: 32768, in_per_M: 0.029412, out_per_M: 0.117647, multimodal: false, reasoning: false },
  { id: "sarvam-105b", name: "Sarvam: Sarvam-105B", context: 32768, in_per_M: 0.047059, out_per_M: 0.188235, multimodal: false, reasoning: false },
];

function argValue(flag: string, fallback: string): string {
  const i = process.argv.indexOf(flag);
  return i >= 0 && process.argv[i + 1] ? process.argv[i + 1] : fallback;
}

async function fetchModels(url: string): Promise<any[]> {
  const headers: Record<string, string> = { "User-Agent": "dhee-eval-fetch/1.0" };
  const key = process.env.OPENROUTER_API_KEY;
  if (key) headers.Authorization = `Bearer ${key}`;
  const r = await fetch(url, { headers });
  if (!r.ok) throw new Error(`HTTP ${r.status}: ${await r.text()}`);
  return ((await r.json()) as any).data as any[];
}

function toRow(m: any) {
  const p = m.pricing || {};
  const inputs = (m.architecture || {}).input_modalities || [];
  // OpenRouter uses sentinel "-1" for "varies" (e.g. openrouter/auto); clamp
  // negatives to 0 so they don't poison cost math downstream.
  const price = (field: string) => Math.round(Math.max(Number(p[field] || 0), 0) * 1e6 * 1e6) / 1e6;
  return {
    id: m.id,
    name: m.name || m.id,
    context: m.context_length || 0,
    in_per_M: price("prompt"),
    out_per_M: price("completion"),
    multimodal: inputs.includes("image"),
    reasoning: (m.supported_parameters || []).includes("reasoning"),
  };
}

async function main(): Promise<void> {
  const out = argValue("--out", "pricing.json");
  const url = argValue("--url", MODELS_URL);

  const data = await fetchModels(url);
  const toolModels = data.filter((m) => (m.supported_parameters || []).includes("tools"));
  const rows = toolModels.map(toRow);
  rows.push(...SARVAM_ROWS);
  // cheapest-first (in, then out)
  rows.sort((a, b) => a.in_per_M - b.in_per_M || a.out_per_M - b.out_per_M);

  writeFileSync(out, JSON.stringify(rows, null, 2));
  console.log(
    `fetched ${data.length} models, ${toolModels.length} tool-capable ` +
      `(+${SARVAM_ROWS.length} sarvam) -> ${out}`,
  );
}

main().catch((e) => {
  console.error(e?.message || e);
  process.exit(1);
});
