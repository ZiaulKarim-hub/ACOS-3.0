#!/usr/bin/env bun
/**
 * tests.ts — the repo's `test` check (FUN-5).
 *
 * WHAT WAS ACTUALLY WRONG, measured 2026-11-18. The S3 scan reported `test: fail` with
 * 74 failures, and the obvious reading — a parser regression in apps/visual-composer —
 * was wrong. Three facts settle it:
 *
 *   1. Those suites import from "vitest" and run under `environment: 'happy-dom'`
 *      (apps/visual-composer/vite.config.ts). Neither vitest nor happy-dom is installed
 *      anywhere in this checkout, and that app has no node_modules at all.
 *   2. src/parser/index.ts line 115 reads `if (typeof DOMParser === 'undefined') return [];`
 *      — a deliberate guard. `bun -e 'typeof DOMParser'` prints "undefined".
 *   3. So extract() correctly returned [] for every input, and 74 assertions about its
 *      output failed. The code was behaving exactly as written; the RUNNER was wrong.
 *
 * `bun test` with no arguments walks the repo and adopts any *.test.ts it finds, whatever
 * framework the file was written for and whatever environment it needs. In this workspace
 * that sweeps up another project's suites. So the root `test` check names what it runs.
 *
 * THREE KINDS OF SUITE LIVE HERE, and they need three different invocations:
 *   bun test roots   — files importing "bun:test". `bun test` SKIPS HIDDEN DIRECTORIES, so
 *                      everything under .claude/ is invisible to a bare `bun test` and has
 *                      to be reached with --cwd. That is why the bare command appeared to
 *                      run "the repo's tests" while running none of this repo's own.
 *   script suites    — standalone bun programs with their own counters and exit codes,
 *                      written that way on purpose (a suite that throws mid-run still
 *                      prints "N/N passed", so these own their tally). `bun test` finds
 *                      0 tests in them, which would be a silent pass.
 *   not ours         — named, with the reason.
 *
 * HOW IT STAYS HONEST. Every test file in the workspace must be accounted for, and a run
 * that executed ZERO tests fails: a vacuous pass is the failure mode this whole check
 * exists to prevent.
 */

import { existsSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { isUnder, walkRepo } from "./discover.ts";
import { runGate } from "./gate-env.ts";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");
const TEST_FILE = /(\.test|\.spec|_test)\.[cm]?tsx?$/;

/**
 * `filters` exists for the repo root only. `bun test --cwd .` would walk the whole
 * workspace again and re-adopt apps/visual-composer, so the one root-level suite is named
 * as a positional filter instead, which restricts the run to paths matching it.
 */
const BUN_TEST_ROOTS: { cwd: string; filters: string[] }[] = [
  { cwd: ".", filters: ["deps-audit.test.ts"] },
  { cwd: "tools/checks", filters: [] },
  { cwd: ".claude/skills/acos-jason-breakglass", filters: [] },
  { cwd: ".claude/skills/acos-journal-submission", filters: [] },
  { cwd: ".claude/scripts/oracle", filters: [] },
  { cwd: ".claude/_retired/2026-11-18-account-sharing/scripts-account-sharing", filters: [] },
  // The protocol's OWN scan logic (SEC-38). It decides what "clean" means for every other
  // check here, so until this root existed the one component that can silently excuse a
  // failure was the only one nothing tested.
  { cwd: ".claude/skills/acos-nemesis-protocol/scripts", filters: [] },
];

const SCRIPT_SUITES = [
  ".claude/scripts/git-manager/stable-ids.test.ts",
  ".claude/skills/investigate/scripts/investigate-plan.test.ts",
  ".claude/skills/research/scripts/research-plan.test.ts",
];

const NOT_OURS: { prefix: string; why: string }[] = [
  {
    prefix: "apps/visual-composer",
    why: "12 vitest suites needing the happy-dom environment; vitest and happy-dom are not "
      + "installed in this checkout and the app has no node_modules. It owns `test` "
      + "(`vitest run`); run it from inside that directory after `bun install`.",
  },
  {
    prefix: "Website Builder",
    why: "spike folders holding VENDORED copies of zod and entities inside their own "
      + "node_modules — third-party library suites, not this repo's tests.",
  },
];

/**
 * THE BUN RUNNING THIS GATE, BY ABSOLUTE PATH -- NOT THE NAME `bun` (SEC-30).
 *
 * This is the fourth place in the project with the same shape, after `ps` (SEC-14),
 * `doppler` (SEC-26) and `bun audit` (FUN-73): a bare command name is looked up through
 * whatever PATH the caller happens to carry, so a stub placed earlier on PATH answers
 * instead. Here the cost is the worst of the four, because this gate decides whether the
 * whole test suite passed: a stub printing "Ran 1 tests" and exiting 0 would turn every
 * suite group green and the release gate would open on nothing.
 *
 * `process.execPath` is the interpreter already running this file, so it needs no lookup
 * and cannot be redirected. The recorded lesson for this project is to fix the CLASS
 * rather than the instance, and this is the instance that was still open.
 */
const BUN = process.execPath;

/** Which framework a file was written for, read from the file rather than guessed. */
function runnerOf(rel: string): "bun" | "script" | "other" {
  let src: string;
  try { src = readFileSync(resolve(ROOT, rel), "utf8"); } catch { return "other"; }
  if (/from\s*["']bun:test["']/.test(src)) return "bun";
  if (/from\s*["'](vitest|@jest\/globals|node:test)["']/.test(src)) return "other";
  return "script";
}

function coveredByRoot(rel: string): boolean {
  return BUN_TEST_ROOTS.some((r) =>
    isUnder(rel, r.cwd) && (r.filters.length === 0 || r.filters.some((f) => rel.includes(f))));
}


/**
 * WHAT THE INVENTORY SAYS ABOUT ONE FILE, as a function, so the POLICY can be tested
 * without running every suite in the repository (FUN-86).
 *
 * THE RUNNER IS DECIDED FIRST, AND ONLY THEN IS THE PREFIX SKIP APPLIED. Skipping by path
 * alone meant a bun:test suite or a standalone script added under one of those projects
 * later would be run by no gate and reported by nobody. The NOT_OURS reasons are about
 * suites written for a runner that cannot execute HERE — vitest needing happy-dom, vendored
 * third-party libraries — not about the directory being out of bounds.
 *
 * Measured before changing it: all 12 files under apps/visual-composer import vitest, and
 * every test file under "Website Builder" sits inside a node_modules that walkRepo already
 * skips. So this tightening changes nothing today and catches the next addition.
 */
export function accountFor(rel: string, kind: "bun" | "script" | "other"): string | null {
  if (kind === "other" && NOT_OURS.some((n) => isUnder(rel, n.prefix))) return null;
  if (kind === "script") {
    return SCRIPT_SUITES.includes(rel) ? null
      : `UNACCOUNTED  ${rel}\n             a standalone suite that nothing runs — add it to SCRIPT_SUITES.`;
  }
  if (kind === "bun") {
    return coveredByRoot(rel) ? null
      : `UNACCOUNTED  ${rel}\n             a bun:test suite under no root — add a BUN_TEST_ROOTS entry.`;
  }
  return `UNACCOUNTED  ${rel}\n             written for another runner and outside every NOT_OURS path — name it with a reason.`;
}

function main(): number {
  const discovered = walkRepo(ROOT).filter((f) => TEST_FILE.test(f));
  const problems: string[] = [];

  for (const rel of discovered) {
    const problem = accountFor(rel, runnerOf(rel));
    if (problem !== null) problems.push(problem);
  }

  for (const r of BUN_TEST_ROOTS) {
    if (!existsSync(resolve(ROOT, r.cwd))) problems.push(`MISSING      ${r.cwd} — listed as a test root but not on disk.`);
  }
  for (const s of SCRIPT_SUITES) {
    if (!existsSync(resolve(ROOT, s))) problems.push(`MISSING      ${s} — listed as a script suite but not on disk.`);
  }

  if (problems.length > 0) {
    console.error("test: the test inventory no longer matches the repo.\n");
    for (const p of problems) console.error(`  ${p}`);
    return 1;
  }

  let failed = 0;
  let ran = 0;

  for (const root of BUN_TEST_ROOTS) {
    const run = runGate(BUN, ["test", "--cwd", root.cwd, ...root.filters], { cwd: ROOT });
    const output = `${run.stdout}${run.stderr}`;
    const ok = run.error === undefined && run.signal === null && run.status === 0;
    // "Ran N tests across M files." — a root that matched nothing still exits 0 in some
    // bun versions, so the tally is read and a zero is treated as a failure.
    const tally = /Ran (\d+) tests?/.exec(output);
    const count = tally === null ? 0 : Number(tally[1]);
    ran += count;
    const vacuous = ok && count === 0;
    console.log(`${ok && !vacuous ? "pass" : "FAIL"}  ${root.cwd} — ${count} test(s)`);
    if (!ok || vacuous) {
      failed += 1;
      if (vacuous) console.error("      ran ZERO tests; a root that matches nothing is not a pass.");
      console.error(output.trim().split("\n").slice(-25).map((l) => `      ${l}`).join("\n"));
    }
  }

  for (const suite of SCRIPT_SUITES) {
    const run = runGate(BUN, [suite], { cwd: ROOT });
    const output = `${run.stdout}${run.stderr}`;
    const ok = run.error === undefined && run.signal === null && run.status === 0;
    const last = output.trim().split("\n").pop() ?? "";
    console.log(`${ok ? "pass" : "FAIL"}  ${suite} — ${last}`);
    if (!ok) {
      failed += 1;
      console.error(output.trim().split("\n").slice(-25).map((l) => `      ${l}`).join("\n"));
    }
  }

  for (const n of NOT_OURS) console.log(`skip  ${n.prefix} — ${n.why}`);

  const groups = BUN_TEST_ROOTS.length + SCRIPT_SUITES.length;
  console.log(`\ntest: ${groups - failed}/${groups} suite groups pass (${ran} bun tests + ${SCRIPT_SUITES.length} script suites)`);
  return failed === 0 ? 0 : 1;
}


// GUARDED, SO THE POLICY ABOVE CAN BE IMPORTED. Without this, importing `accountFor` to
// test it ran main() in the importing process — which here means running every suite in
// the repository, including the one holding that test, so the gate would recurse into
// itself. The same defect probe-child.ts had (an unguarded script that also exports), one
// layer out and with a much larger blast radius.
if (import.meta.main) process.exit(main());
