#!/usr/bin/env bun
/**
 * gate.ts — CLI dispatch over the four mechanical gates (lib/gates.ts).
 *
 * Each sub-command reads its JSON inputs, writes a structured report, and sets an exit code
 * the orchestrator branches on: 0 = the gate PASSED (proceed), 1 = the gate FAILED / BLOCKED
 * (loop back or halt). Failing is a normal, expected outcome here — it never throws.
 *
 * Usage:
 *   bun gate.ts completeness  --kept <kept.json> --requirements <req.json> [--waivers <w.json>] [--out r.json]
 *   bun gate.ts protected-set --cuts <cuts.json> --protected <protected-gate.json>               [--out r.json]
 *   bun gate.ts buildability  --components <component-tree.json>                                   [--out r.json]
 *   bun gate.ts traceability  --items <ids.json> --mapped <mapped-ids.json> [--waivers <w.json>] [--out r.json]
 *
 * JSON shapes:
 *   kept.json         { intents:[], surfaces:[], rules:[], parity:[] }
 *   req.json          [ { req_id, maps:[ids] }, ... ]   (also accepts JSONL: one obj per line)
 *   protected-gate    { rule_ledger:[], behavior_critical:[], human_essential:[] }
 *   cuts.json         [ { id, reason? }, ... ]          (also accepts a bare ["id", ...])
 *   component-tree    [ { id, deps:[], testable? }, ... ]  OR { components:[ ... ] }
 *   items / mapped    ["id", ...]  (mapped may also be [{req_id|id}] — the id field is read)
 */

import { readFileSync, writeFileSync } from "node:fs";
import {
  completenessGate,
  protectedSetGate,
  buildabilityGate,
  traceabilityGate,
  type Requirement,
  type Cut,
  type Component,
} from "./lib/gates.ts";

function parseArgs(argv: string[]): Record<string, string> {
  const a: Record<string, string> = {};
  for (let i = 0; i < argv.length; i++) if (argv[i].startsWith("--")) a[argv[i].slice(2)] = argv[i + 1] ?? "true";
  return a;
}
function readJson(path: string): any {
  const txt = readFileSync(path, "utf8").trim();
  // Tolerate JSONL (one object per line) for the *.jsonl artifacts the agents emit.
  if (txt.startsWith("{") && txt.includes("\n") && !txt.startsWith("{\n") && txt.split("\n").every((l) => l.trim().startsWith("{") || !l.trim())) {
    return txt.split("\n").filter((l) => l.trim()).map((l) => JSON.parse(l));
  }
  try {
    return JSON.parse(txt);
  } catch {
    // last resort: treat as JSONL
    return txt.split("\n").filter((l) => l.trim()).map((l) => JSON.parse(l));
  }
}
function idList(v: any): string[] {
  if (Array.isArray(v)) return v.map((x) => (typeof x === "string" ? x : x?.id ?? x?.req_id ?? x?.intent_id)).filter(Boolean).map(String);
  return [];
}
function emit(report: any, out: string | undefined, passed: boolean, summary: string): never {
  if (out) writeFileSync(out, JSON.stringify(report, null, 2));
  console.log(summary + (out ? ` → ${out}` : ""));
  process.exit(passed ? 0 : 1);
}

function main() {
  const [cmd, ...rest] = process.argv.slice(2);
  const a = parseArgs(rest);

  if (cmd === "completeness") {
    if (!a.kept || !a.requirements) { console.error("need --kept and --requirements"); process.exit(2); }
    const kept = readJson(a.kept);
    const reqs = readJson(a.requirements) as Requirement[];
    const waivers = a.waivers ? idList(readJson(a.waivers)) : [];
    const r = completenessGate(kept, Array.isArray(reqs) ? reqs : (reqs as any).requirements ?? [], waivers);
    emit(r, a.out, r.verdict === "PASS", `completeness: ${r.verdict} — ${r.mapped} mapped, ${r.waived} waived, ${r.unmapped.length} UNMAPPED`);
  }

  if (cmd === "protected-set") {
    if (!a.cuts || !a.protected) { console.error("need --cuts and --protected"); process.exit(2); }
    const rawCuts = readJson(a.cuts);
    const cuts: Cut[] = (Array.isArray(rawCuts) ? rawCuts : []).map((c: any) => (typeof c === "string" ? { id: c } : c));
    const prot = readJson(a.protected);
    const r = protectedSetGate(cuts, prot);
    emit(r, a.out, r.verdict === "OK", `protected-set: ${r.verdict} — ${r.checked} cut(s) checked, ${r.violations.length} violation(s)`);
  }

  if (cmd === "buildability") {
    if (!a.components) { console.error("need --components"); process.exit(2); }
    const raw = readJson(a.components);
    const comps: Component[] = Array.isArray(raw) ? raw : raw.components ?? [];
    const r = buildabilityGate(comps);
    const detail = r.verdict === "PASS" ? `${r.order.length} components, leaves-first order derived` : `acyclic=${r.acyclic}, cycle=[${r.cycle.join(",")}], untestable=[${r.untestable.join(",")}]`;
    emit(r, a.out, r.verdict === "PASS", `buildability: ${r.verdict} — ${detail}`);
  }

  if (cmd === "traceability") {
    if (!a.items || !a.mapped) { console.error("need --items and --mapped"); process.exit(2); }
    const items = idList(readJson(a.items));
    const mapped = idList(readJson(a.mapped));
    const waivers = a.waivers ? idList(readJson(a.waivers)) : [];
    const r = traceabilityGate(items, mapped, waivers);
    emit(r, a.out, r.verdict === "PASS", `traceability: ${r.verdict} — ${r.mapped}/${r.total} mapped, ${r.waived} waived, ${r.unmapped.length} UNMAPPED`);
  }

  console.error("usage: bun gate.ts completeness|protected-set|buildability|traceability …");
  process.exit(2);
}

main();
