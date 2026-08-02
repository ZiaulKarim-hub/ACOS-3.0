#!/usr/bin/env bun
/**
 * select-layers.ts — the Phase-0 layer SELECTION pass (pure decision, no browser).
 *
 * The recon pass (capture.ts --recon) writes signals.json describing the app's shape
 * (auth-role count + detected signals). This script consumes that and picks the adaptive
 * subset of the 27-layer library that reaches the coverage benchmark for THIS app — the
 * inner-loop estimate side. Browser-driving is capture.ts's job; the "which layers" decision
 * is here so it is deterministic and unit-tested (see lib/layers.ts + selftest.ts).
 *
 * Usage:
 *   bun select-layers.ts --signals <signals.json> [--benchmark 0.99] [--out selected-layers.json]
 *
 * signals.json: { "roles": <int>, "detected": ["forms-or-calc", "search-present", ...] }
 * Exit 0 always (selection cannot "fail"); a benchmark it can't reach sets benchmark_met=false.
 */

import { readFileSync, writeFileSync } from "node:fs";
import { selectLayers, KNOWN_SIGNALS, type ReconSignals } from "./lib/layers.ts";

function parseArgs(argv: string[]): Record<string, string> {
  const a: Record<string, string> = {};
  for (let i = 0; i < argv.length; i++) if (argv[i].startsWith("--")) a[argv[i].slice(2)] = argv[i + 1] ?? "true";
  return a;
}

function main() {
  const a = parseArgs(process.argv.slice(2));
  if (!a.signals) {
    console.error("usage: bun select-layers.ts --signals <signals.json> [--benchmark 0.99] [--out selected-layers.json]");
    console.error(`known signals: ${KNOWN_SIGNALS.join(", ")}`);
    process.exit(1);
  }
  let signals: ReconSignals;
  try {
    const raw = JSON.parse(readFileSync(a.signals, "utf8"));
    signals = {
      roles: Number(raw.roles) || 1,
      detected: Array.isArray(raw.detected) ? raw.detected.map(String) : [],
    };
  } catch (e) {
    console.error(`could not read signals.json: ${String(e)}`);
    process.exit(1);
    return;
  }
  const unknown = signals.detected.filter((s) => !KNOWN_SIGNALS.includes(s));
  if (unknown.length) console.warn(`warning: ignoring unknown signal(s): ${unknown.join(", ")}`);

  const benchmark = a.benchmark ? Number(a.benchmark) : 0.99;
  const result = selectLayers(signals, { benchmark });

  const out = a.out || "selected-layers.json";
  writeFileSync(out, JSON.stringify(result, null, 2));
  const layerIds = result.selected.map((s) => s.id).join(",");
  console.log(
    `selected ${result.selected.length}/${result.denominator_layers} applicable layers ` +
      `(coverage ~${(result.coverage * 100).toFixed(1)}%, benchmark ${(benchmark * 100).toFixed(0)}% ` +
      `${result.benchmark_met ? "MET" : "NOT met"}) + always-on ${result.always_on.join(",")} → ${out}`,
  );
  console.log(`--layers ${layerIds}`);
}

main();
