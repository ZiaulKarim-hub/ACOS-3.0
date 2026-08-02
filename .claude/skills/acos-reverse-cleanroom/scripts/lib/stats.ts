// lib/stats.ts — tiny statistics helpers for Phase-0 robustness (pure, no deps).
//
// Two design rules from references/capture-layers.md ("Baselines"):
//   • oracle multi-sample: sample each golden case N times, keep the SPREAD not one number,
//     and tag fields stable-vs-volatile so parity assertions don't fail on volatile fields.
//   • baseline spread: repeat Lighthouse/latency/a11y a few times, keep the spread.
// Both need the same primitives, so they live here and are shared by parity.ts + baselines.

export interface Spread {
  n: number;
  min: number;
  p50: number; // median
  p95: number;
  max: number;
  mean: number;
}

/** Nearest-rank percentile (0..1) over a numeric sample. */
export function percentile(nums: number[], q: number): number {
  if (nums.length === 0) return NaN;
  const sorted = [...nums].sort((a, b) => a - b);
  const rank = Math.ceil(q * sorted.length);
  const idx = Math.min(sorted.length - 1, Math.max(0, rank - 1));
  return sorted[idx];
}

/** Summarize a numeric sample as min / p50 / p95 / max / mean. */
export function spread(nums: number[]): Spread {
  const n = nums.length;
  if (n === 0) return { n: 0, min: NaN, p50: NaN, p95: NaN, max: NaN, mean: NaN };
  const sorted = [...nums].sort((a, b) => a - b);
  const sum = nums.reduce((a, b) => a + b, 0);
  return {
    n,
    min: sorted[0],
    p50: percentile(nums, 0.5),
    p95: percentile(nums, 0.95),
    max: sorted[n - 1],
    mean: sum / n,
  };
}

/**
 * Given N sampled observations of the same case (each a flat key→value object), return the
 * set of field keys whose value VARIES across samples. Those are "volatile" fields (timestamps,
 * ids, tokens) that a parity assertion must not pin; the rest are "stable" and safe to assert.
 */
export function volatileFields(samples: Record<string, unknown>[]): string[] {
  if (samples.length < 2) return [];
  const keys = new Set<string>();
  for (const s of samples) for (const k of Object.keys(s ?? {})) keys.add(k);
  const volatile: string[] = [];
  for (const k of keys) {
    const first = JSON.stringify(samples[0]?.[k]);
    if (samples.some((s) => JSON.stringify(s?.[k]) !== first)) volatile.push(k);
  }
  return volatile.sort();
}

export function stableFields(samples: Record<string, unknown>[]): string[] {
  if (samples.length === 0) return [];
  const vol = new Set(volatileFields(samples));
  const keys = new Set<string>();
  for (const s of samples) for (const k of Object.keys(s ?? {})) keys.add(k);
  return [...keys].filter((k) => !vol.has(k)).sort();
}
