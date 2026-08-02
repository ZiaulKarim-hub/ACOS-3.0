// lib/loops.ts — capture convergence loops (Phase 0), pure + testable.
//
// Two loops wrap the adaptive layer selection (see lib/layers.ts):
//   • INNER (top-up): add the next-best layer until estimated/measured coverage ≥ benchmark.
//     The math for that lives in layers.ts (selectLayers / remainingExtByValue); this file
//     provides the driver that repeats it against MEASURED coverage during a live run.
//   • OUTER (re-run): re-run the WHOLE capture until a fresh pass adds nothing MATERIAL,
//     capped by max_reruns. Comparison is on NORMALIZED features/intent keys — NEVER raw
//     bytes (raw diffs drown in timestamps/tokens/ordering). Conditions VARY each pass so a
//     re-run probes new ground rather than re-confirming the same blind spots.

/**
 * A normalized snapshot of what a capture pass found — sets of stable KEYS, not raw text.
 * Keys are e.g. surface ids ("route:/dashboard"), intent-claim keys, rule ids, probe ids.
 * Comparing keys (not bytes) is what makes "did this pass add anything real?" answerable.
 */
export interface PassFeatures {
  surfaces: string[];
  intents: string[];
  rules: string[];
  probes?: string[];
}

export interface FeatureDelta {
  material: boolean; // did the compared pass add or remove any feature key?
  added: string[];
  removed: string[];
  before: number; // key count before
  after: number; // key count after
}

const norm = (k: string): string => k.trim().toLowerCase().replace(/\s+/g, " ");

function keySet(f: PassFeatures): Set<string> {
  const s = new Set<string>();
  for (const [kind, arr] of Object.entries(f)) {
    if (!Array.isArray(arr)) continue;
    for (const v of arr) s.add(`${kind}:${norm(String(v))}`);
  }
  return s;
}

/**
 * Normalized material-delta between two passes. `added`/`removed` are the feature KEYS
 * that changed; `material` is true iff either is non-empty. A pass that only reshuffles
 * timestamps/tokens produces the same key set → material=false → the outer loop converges.
 */
export function materialDelta(prev: PassFeatures, next: PassFeatures): FeatureDelta {
  const a = keySet(prev);
  const b = keySet(next);
  const added = [...b].filter((k) => !a.has(k)).sort();
  const removed = [...a].filter((k) => !b.has(k)).sort();
  return { material: added.length > 0 || removed.length > 0, added, removed, before: a.size, after: b.size };
}

export interface ConvergenceResult {
  passes: number; // total capture passes run (>=1)
  converged: boolean; // true = a fresh pass added nothing material; false = hit the rerun cap
  cumulative: PassFeatures; // union of every feature key seen across all passes
  per_pass: { pass: number; new_keys: string[]; material: boolean }[];
  stopped_reason: "converged" | "max_reruns";
}

/**
 * Outer re-run driver. `runPass(passIndex)` executes one full capture pass and returns its
 * normalized features. We accumulate the UNION of features and, each pass, measure what the
 * new pass adds BEYOND the cumulative union. When a fresh pass adds nothing material — or the
 * rerun cap is hit — we stop. `max_reruns` = extra passes after the first (default 2 → 3 total).
 *
 * Pure over its injected runPass, so a fake pass sequence unit-tests convergence + the cap.
 */
export async function outerConverge(
  runPass: (passIndex: number) => Promise<PassFeatures>,
  opts: { maxReruns?: number } = {},
): Promise<ConvergenceResult> {
  const maxReruns = Math.max(0, opts.maxReruns ?? 2);
  const cumulativeKeys = new Set<string>();
  const per_pass: ConvergenceResult["per_pass"] = [];
  let lastFeatures: PassFeatures = { surfaces: [], intents: [], rules: [], probes: [] };
  let passes = 0;
  let stopped: ConvergenceResult["stopped_reason"] = "max_reruns";

  const totalPasses = maxReruns + 1; // first pass + reruns
  for (let i = 0; i < totalPasses; i++) {
    const f = await runPass(i);
    lastFeatures = f;
    passes++;
    const before = new Set(cumulativeKeys);
    for (const k of keySet(f)) cumulativeKeys.add(k);
    const newKeys = [...cumulativeKeys].filter((k) => !before.has(k)).sort();
    const material = i === 0 ? true : newKeys.length > 0; // pass 1 is always "material" (it's the baseline)
    per_pass.push({ pass: i + 1, new_keys: newKeys, material });
    // Converged when a RE-RUN (not the first pass) adds nothing new to the union.
    if (i > 0 && newKeys.length === 0) {
      stopped = "converged";
      break;
    }
  }

  // Rebuild cumulative features from the key union (kind:value → grouped arrays).
  const cumulative: PassFeatures = { surfaces: [], intents: [], rules: [], probes: [] };
  for (const key of [...cumulativeKeys].sort()) {
    const idx = key.indexOf(":");
    const kind = key.slice(0, idx);
    const val = key.slice(idx + 1);
    if (kind in cumulative) (cumulative as any)[kind].push(val);
  }
  void lastFeatures; // last pass retained for callers that want the freshest raw snapshot

  return { passes, converged: stopped === "converged", cumulative, per_pass, stopped_reason: stopped };
}
