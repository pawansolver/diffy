// Output: append per-run JSONL, write an aggregated scores JSON, and print a
// per-profile console summary (dimension columns adapt to each profile's rubric).

import { appendFileSync, writeFileSync } from "node:fs";
import type { ProfileConfig } from "./config.js";
import type { ResultRow } from "./types.js";

/** Append one record as a JSON line (writes are synchronous, so pool workers
 *  can't interleave a half-written line). */
export function appendJsonl(path: string, record: unknown): void {
  appendFileSync(path, JSON.stringify(record) + "\n");
}

/** Write the full result set as a single JSON array (answers dropped to keep it
 *  scannable; full answers + transcripts live in the JSONL). */
export function writeScoresJson(path: string, rows: ResultRow[]): void {
  const slim = rows.map(({ answer, ...rest }) => rest);
  writeFileSync(path, JSON.stringify(slim, null, 2));
}

function mean(nums: number[]): number | null {
  if (!nums.length) return null;
  return nums.reduce((a, b) => a + b, 0) / nums.length;
}

function avgScore(rows: ResultRow[], key: string): string {
  const vals = rows.map((r) => r[key]).filter((v): v is number => typeof v === "number");
  const m = mean(vals);
  return m == null ? "—" : m.toFixed(2);
}

const pad = (s: string, w: number) => s.padStart(w);
const padEnd = (s: string, w: number) => s.padEnd(w);

/** Print one summary table per profile, plus an OpenRouter auto-routing tally. */
export function printSummary(rows: ResultRow[], profiles: ProfileConfig[]): void {
  console.log("\n" + "=".repeat(72));
  console.log("SUMMARY (averages per model, grouped by profile)");
  console.log("=".repeat(72));

  for (const profile of profiles) {
    const pr = rows.filter((r) => r.profile === profile.name);
    if (!pr.length) continue;

    console.log(`\n### profile: ${profile.name}`);
    const dims = profile.dimensions.map((d) => d.name);
    const dimW = 7;

    let hdr = padEnd("model", 22) + " " + pad("tool%", 6);
    for (const d of dims) hdr += " " + pad(d.slice(0, dimW), dimW);
    hdr += " " + pad("lat_s", 7) + " " + pad("$/q", 10);
    console.log(hdr);
    console.log("-".repeat(hdr.length));

    // group by model label, preserving first-seen order
    const byModel = new Map<string, ResultRow[]>();
    for (const r of pr) {
      if (!byModel.has(r.model)) byModel.set(r.model, []);
      byModel.get(r.model)!.push(r);
    }

    for (const [model, mrows] of byModel) {
      const toolPct = Math.round((100 * mrows.filter((x) => x.called_any_tool).length) / mrows.length);
      let line = padEnd(model.slice(0, 22), 22) + " " + pad(toolPct + "%", 6);
      for (const d of dims) line += " " + pad(avgScore(mrows, `score_${d}`), dimW);
      const lat = mean(mrows.map((x) => x.latency_s));
      const cost = mean(mrows.map((x) => x.cost_usd));
      line += " " + pad(lat == null ? "—" : lat.toFixed(2), 7);
      line += " " + pad(cost == null ? "—" : cost.toFixed(6), 10);
      console.log(line);
    }
  }

  // Auto-routing tally: only routers (openrouter/*) actually reroute; pinned
  // models "serve themselves" but report dated ids, so restrict to routers.
  const routed = new Map<string, Map<string, number>>();
  for (const r of rows) {
    const sm = r.served_model;
    if (sm && r.model_id.startsWith("openrouter/")) {
      const key = `${r.profile}/${r.model}`;
      if (!routed.has(key)) routed.set(key, new Map());
      const m = routed.get(key)!;
      m.set(sm, (m.get(sm) || 0) + 1);
    }
  }
  if (routed.size) {
    console.log("\nAUTO ROUTING (served model × question count)");
    console.log("-".repeat(46));
    for (const [key, counts] of routed) {
      console.log(`  ${key}:`);
      for (const [served, n] of [...counts.entries()].sort((a, b) => b[1] - a[1])) {
        console.log(`    ${pad(String(n), 3)}x  ${served}`);
      }
    }
  }
}
