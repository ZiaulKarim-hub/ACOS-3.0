#!/usr/bin/env bun
/**
 * capture-diff.ts — the Phase-0 OUTER-loop convergence check.
 *
 * After a full capture pass, the orchestrator re-runs capture under VARIED conditions and asks:
 * "did this fresh pass find anything MATERIAL, or have we converged?" This compares two passes on
 * NORMALIZED feature keys (surfaces / intents / rules / probes) — NEVER raw bytes, which would
 * drown in timestamps, tokens, and ordering. "No new material findings" is the convergence proxy
 * for the coverage benchmark (evidence, not proof).
 *
 * Usage:
 *   bun capture-diff.ts --prev <features-prev.json> --next <features-next.json> [--out delta.json]
 *
 * features JSON: { "surfaces":[...], "intents":[...], "rules":[...], "probes":[...] }  (all optional)
 * Exit codes: 0 = CONVERGED (no material delta) · 3 = MATERIAL delta remains (keep looping).
 * (Designed for a shell `until bun capture-diff.ts ...; do <re-run>; done` outer loop.)
 */

import { readFileSync, writeFileSync } from "node:fs";
import { materialDelta, type PassFeatures } from "./lib/loops.ts";

function parseArgs(argv: string[]): Record<string, string> {
  const a: Record<string, string> = {};
  for (let i = 0; i < argv.length; i++) if (argv[i].startsWith("--")) a[argv[i].slice(2)] = argv[i + 1] ?? "true";
  return a;
}
function readFeatures(path: string): PassFeatures {
  const raw = JSON.parse(readFileSync(path, "utf8"));
  return {
    surfaces: raw.surfaces ?? [],
    intents: raw.intents ?? [],
    rules: raw.rules ?? [],
    probes: raw.probes ?? [],
  };
}

function main() {
  const a = parseArgs(process.argv.slice(2));
  if (!a.prev || !a.next) {
    console.error("usage: bun capture-diff.ts --prev <features-prev.json> --next <features-next.json> [--out delta.json]");
    process.exit(2);
  }
  const delta = materialDelta(readFeatures(a.prev), readFeatures(a.next));
  if (a.out) writeFileSync(a.out, JSON.stringify(delta, null, 2));
  console.log(
    `capture-diff: ${delta.material ? "MATERIAL" : "CONVERGED"} — ` +
      `+${delta.added.length} added / -${delta.removed.length} removed (${delta.before}→${delta.after} keys)` +
      (a.out ? ` → ${a.out}` : ""),
  );
  if (delta.material && delta.added.length) console.log(`  new: ${delta.added.slice(0, 8).join(", ")}${delta.added.length > 8 ? " …" : ""}`);
  process.exit(delta.material ? 3 : 0);
}

main();
