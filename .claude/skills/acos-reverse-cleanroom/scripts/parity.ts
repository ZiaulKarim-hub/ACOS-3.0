#!/usr/bin/env bun
/**
 * parity.ts — behavioral-parity oracle (golden-master capture + replay).
 *
 * Phase 0 records "golden" cases: an observed input → observed output from the
 * ORIGINAL app. Phase 6 wires each case into a rebuild slice's verification_method.
 * Phase "recheck" replays cases against the REBUILT app and diffs, so drift and
 * regressions are loud, not silent.
 *
 * A golden case is deliberately implementation-agnostic: it asserts observable
 * behavior (status, JSON body shape/values, redirect, key DOM text), never how
 * the original produced it. Confidence-banded; known deviations are recorded, not
 * hidden (an original bug you do NOT want to reproduce is a knownDeviation).
 *
 * Usage:
 *   record: bun parity.ts record --base <url> --cases cases.json --out parity-manifest.json
 *   verify: bun parity.ts verify --base <rebuilt-url> --manifest parity-manifest.json --report parity-report.json
 *
 * cases.json: [{ id, description, request:{method,path,headers?,body?}, assert:{status?, jsonIncludes?, bodyMatches?} , confidence, knownDeviation? }]
 */

import { readFileSync, writeFileSync } from "node:fs";
import { volatileFields } from "./lib/stats.ts";

interface Case {
  id: string;
  description: string;
  request: { method: string; path: string; headers?: Record<string, string>; body?: any };
  assert: { status?: number; jsonIncludes?: Record<string, unknown>; bodyMatches?: string };
  confidence: "high" | "medium" | "low";
  knownDeviation?: string; // behavior of the original we deliberately do NOT reproduce
}

function deepIncludes(actual: any, expected: any): boolean {
  if (expected === null || typeof expected !== "object") return actual === expected;
  if (Array.isArray(expected)) return Array.isArray(actual) && expected.every((e, i) => deepIncludes(actual?.[i], e));
  return Object.entries(expected).every(([k, v]) => deepIncludes(actual?.[k], v));
}

async function run(base: string, c: Case) {
  const url = new URL(c.request.path, base).toString();
  const res = await fetch(url, {
    method: c.request.method,
    headers: { "content-type": "application/json", ...(c.request.headers || {}) },
    ...(c.request.body ? { body: JSON.stringify(c.request.body) } : {}),
  });
  const text = await res.text();
  let json: any = undefined;
  try { json = JSON.parse(text); } catch { /* non-json */ }
  return { status: res.status, text, json };
}

async function main() {
  const [mode, ...rest] = process.argv.slice(2);
  const a: Record<string, string> = {};
  for (let i = 0; i < rest.length; i++) if (rest[i].startsWith("--")) a[rest[i].slice(2)] = rest[i + 1];

  if (mode === "record") {
    const cases: Case[] = JSON.parse(readFileSync(a.cases, "utf8"));
    // --samples N (oracle multi-sample robustness): observe each case N times, keep every
    // sample, and TAG which fields vary across samples so a parity assertion never pins a
    // volatile field (timestamp/id/token). N=1 keeps the original single-observation shape.
    const samples = Math.max(1, Number(a.samples) || 1);
    const manifest = { version: "1.0.0", base: a.base, provenance: "captured from ORIGINAL", samples, cases: [] as any[] };
    for (const c of cases) {
      const obs = await run(a.base, c).catch((e) => ({ error: String(e) }));
      if (samples <= 1) {
        manifest.cases.push({ ...c, observed: obs });
        continue;
      }
      const runs: any[] = [obs];
      for (let i = 1; i < samples; i++) runs.push(await run(a.base, c).catch((e) => ({ error: String(e) })));
      // Flatten each observation to a comparable record: status + top-level JSON fields.
      const flat = runs.map((o: any) => ({
        status: o.status,
        ...(o.json && typeof o.json === "object"
          ? Object.fromEntries(Object.entries(o.json).map(([k, v]) => [`json.${k}`, v]))
          : { body: o.text }),
      }));
      const volatile = volatileFields(flat);
      manifest.cases.push({ ...c, observed: obs, samples: runs, volatile_fields: volatile });
    }
    writeFileSync(a.out, JSON.stringify(manifest, null, 2));
    console.log(`recorded ${cases.length} golden case(s)${samples > 1 ? ` × ${samples} samples` : ""} → ${a.out}`);
    return;
  }

  if (mode === "verify") {
    const manifest = JSON.parse(readFileSync(a.manifest, "utf8"));
    const report = { base: a.base, total: 0, passed: 0, failed: 0, results: [] as any[] };
    for (const c of manifest.cases as Case[]) {
      if (c.knownDeviation) {
        report.results.push({ id: c.id, skipped: true, reason: `knownDeviation: ${c.knownDeviation}` });
        continue;
      }
      report.total++;
      const got = await run(a.base, c).catch((e) => ({ error: String(e) }));
      let ok = true;
      const fails: string[] = [];
      if (c.assert.status != null && (got as any).status !== c.assert.status) {
        ok = false; fails.push(`status ${(got as any).status} != ${c.assert.status}`);
      }
      if (c.assert.jsonIncludes && !deepIncludes((got as any).json, c.assert.jsonIncludes)) {
        ok = false; fails.push("jsonIncludes mismatch");
      }
      if (c.assert.bodyMatches && !new RegExp(c.assert.bodyMatches).test((got as any).text || "")) {
        ok = false; fails.push("bodyMatches mismatch");
      }
      ok ? report.passed++ : report.failed++;
      report.results.push({ id: c.id, confidence: c.confidence, ok, fails });
    }
    writeFileSync(a.report, JSON.stringify(report, null, 2));
    console.log(`parity: ${report.passed}/${report.total} passed, ${report.failed} failed → ${a.report}`);
    if (report.failed > 0) process.exit(1);
    return;
  }

  console.error("usage: bun parity.ts record|verify …");
  process.exit(1);
}

main();
