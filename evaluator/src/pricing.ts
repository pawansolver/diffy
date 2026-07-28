// Cost estimation from a pricing JSON file (produced by scripts/fetch-models.ts).
// The file is an array of { id, name, context, in_per_M, out_per_M, ... } rows.

import { existsSync, readFileSync } from "node:fs";

/** model id -> [in $/token, out $/token] */
export type Pricing = Record<string, [number, number]>;

export function loadPricing(path: string): Pricing {
  const pricing: Pricing = {};
  if (!existsSync(path)) return pricing;
  let rows: any[];
  try {
    rows = JSON.parse(readFileSync(path, "utf8"));
  } catch {
    return pricing;
  }
  for (const row of rows || []) {
    const inP = Number(row.in_per_M);
    const outP = Number(row.out_per_M);
    if (Number.isFinite(inP) && Number.isFinite(outP)) {
      pricing[row.id] = [inP / 1e6, outP / 1e6];
    }
  }
  return pricing;
}

/** Map a served model id to a pricing key. OpenRouter completions return DATED
 *  ids (e.g. 'openai/gpt-5.5-20260423') while the pricing file uses undated ids;
 *  match the longest key the served id starts with ('<key>-<date>'). */
export function canonicalPriceId(modelId: string, pricing: Pricing): string {
  if (modelId in pricing) return modelId;
  const cands = Object.keys(pricing).filter((k) => modelId.startsWith(k + "-"));
  return cands.length ? cands.reduce((a, b) => (b.length > a.length ? b : a)) : modelId;
}

function priceOf(modelId: string | null, pricing: Pricing): [number, number] | null {
  if (!modelId) return null;
  const pr = pricing[canonicalPriceId(modelId, pricing)];
  if (pr && pr[0] >= 0 && pr[1] >= 0) return pr;
  return null;
}

/** Return [in, out] $/token. The CONFIGURED id (mid) is authoritative — it's a
 *  real pricing key with the exact variant/price. Only fall back to the served
 *  model when mid has no usable price (i.e. mid is a router like openrouter/auto
 *  whose own price is a '-1' sentinel). */
export function resolvePrice(
  served: string | null,
  mid: string,
  pricing: Pricing,
): [number, number] {
  const midPr = priceOf(mid, pricing);
  if (midPr && (midPr[0] > 0 || midPr[1] > 0)) return midPr;
  const servedPr = priceOf(served, pricing);
  return servedPr || midPr || [0, 0];
}
