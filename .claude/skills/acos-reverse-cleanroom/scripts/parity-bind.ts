#!/usr/bin/env bun
/**
 * parity-bind.ts — Phase-6 parity-as-verifier WIRING (the key win of the build backend).
 *
 * acos-genesis-protocol produces a component tree; each component needs a verifier. This binds
 * each component's acceptance criterion to (a) its PRD requirement id AND (b) the Phase-0 GOLDEN
 * PARITY CASE(s) captured from the ORIGINAL app, writing them into `component.verifier.auto_check`.
 * The result: every rebuilt part is proven against the original's observed behavior, not a
 * re-derived guess. This is a deterministic transform (no agent), so it is unit-testable.
 *
 * Usage:
 *   bun parity-bind.ts --tree <component-tree.json> --parity <parity-manifest.json> \
 *       [--requirements <requirements.jsonl>] --out <component-tree.bound.json> [--report <bind-report.json>]
 *
 * Matching sources (any/all): component.parity[] direct refs · component.req → requirement.parity[] ·
 * a requirement's `maps[]`/`parity[]` that names a case id present in the manifest.
 * Exit 0 always writes the bound tree; a component with no bindable parity case is reported as a gap
 * (NOT a failure here — the traceability gate is where an unverifiable component blocks).
 */

import { readFileSync, writeFileSync } from "node:fs";

function parseArgs(argv: string[]): Record<string, string> {
  const a: Record<string, string> = {};
  for (let i = 0; i < argv.length; i++) if (argv[i].startsWith("--")) a[argv[i].slice(2)] = argv[i + 1] ?? "true";
  return a;
}
function readJson(path: string): any {
  const txt = readFileSync(path, "utf8").trim();
  try {
    return JSON.parse(txt);
  } catch {
    return txt.split("\n").filter((l) => l.trim()).map((l) => JSON.parse(l)); // JSONL
  }
}
const asArray = (v: any, key: string): any[] => (Array.isArray(v) ? v : v?.[key] ?? []);
const reqOf = (c: any): string | undefined => c.req ?? c.req_id ?? c.requirement ?? undefined;
const directParity = (c: any): string[] => (c.parity ?? c.parity_cases ?? []).map(String);

export interface BindReport {
  components: number;
  bound: number;
  unbound: { id: string; req?: string; reason: string }[];
  orphan_cases: string[]; // parity cases not referenced by any component
  bindings: { component: string; req?: string; case_ids: string[] }[];
}

/** Pure core — exported for the self-test. Returns the mutated tree + a bind report. */
export function bindParity(
  components: any[],
  parityCaseIds: string[],
  requirements: any[],
): { components: any[]; report: BindReport } {
  const caseSet = new Set(parityCaseIds.map(String));
  // req_id → parity case ids it declares (via `parity[]` or any `maps[]` entry that is a real case)
  const reqParity = new Map<string, Set<string>>();
  for (const r of requirements) {
    const id = r.req_id ?? r.id;
    if (!id) continue;
    const cases = new Set<string>();
    for (const p of (r.parity ?? []).map(String)) if (caseSet.has(p)) cases.add(p);
    for (const m of (r.maps ?? []).map(String)) if (caseSet.has(m)) cases.add(m);
    reqParity.set(String(id), cases);
  }

  const referenced = new Set<string>();
  const bindings: BindReport["bindings"] = [];
  const unbound: BindReport["unbound"] = [];
  let bound = 0;

  for (const c of components) {
    const req = reqOf(c);
    const cases = new Set<string>();
    for (const p of directParity(c)) if (caseSet.has(p)) cases.add(p);
    if (req && reqParity.has(String(req))) for (const p of reqParity.get(String(req))!) cases.add(p);

    const caseIds = [...cases].sort();
    if (caseIds.length > 0) {
      c.verifier = c.verifier ?? {};
      c.verifier.auto_check = {
        type: "parity",
        manifest: "golden/parity-manifest.json",
        case_ids: caseIds,
        ...(req ? { req } : {}),
      };
      caseIds.forEach((id) => referenced.add(id));
      bindings.push({ component: c.id, req, case_ids: caseIds });
      bound++;
    } else {
      unbound.push({
        id: c.id,
        req,
        reason: req ? `no parity case maps to requirement '${req}'` : "component declares no requirement or direct parity case",
      });
    }
  }

  const orphan_cases = [...caseSet].filter((id) => !referenced.has(id)).sort();
  return {
    components,
    report: { components: components.length, bound, unbound, orphan_cases, bindings },
  };
}

function main() {
  const a = parseArgs(process.argv.slice(2));
  if (!a.tree || !a.parity || !a.out) {
    console.error("usage: bun parity-bind.ts --tree <component-tree.json> --parity <parity-manifest.json> [--requirements <req.jsonl>] --out <bound.json> [--report <bind-report.json>]");
    process.exit(2);
  }
  const treeRaw = readJson(a.tree);
  const components = asArray(treeRaw, "components");
  const manifest = readJson(a.parity);
  const caseIds = asArray(manifest, "cases").map((c: any) => String(c.id));
  const requirements = a.requirements ? asArray(readJson(a.requirements), "requirements") : [];

  const { report } = bindParity(components, caseIds, requirements);

  // Preserve the tree's original wrapper shape (bare array vs { components }).
  const outTree = Array.isArray(treeRaw) ? components : { ...treeRaw, components };
  writeFileSync(a.out, JSON.stringify(outTree, null, 2));
  if (a.report) writeFileSync(a.report, JSON.stringify(report, null, 2));
  console.log(
    `parity-bind: ${report.bound}/${report.components} components bound to parity cases, ` +
      `${report.unbound.length} unbound, ${report.orphan_cases.length} orphan case(s) → ${a.out}`,
  );
  if (report.unbound.length) console.log(`  unbound: ${report.unbound.slice(0, 6).map((u) => u.id).join(", ")}${report.unbound.length > 6 ? " …" : ""}`);
}

if (import.meta.main) main();
