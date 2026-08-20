#!/usr/bin/env bun
// research-plan.test.ts — proves the /research depth dial parses and maps correctly.
//
// Honest-tally discipline (feedback: a suite that throws mid-run still prints
// "N/N passed"): every check updates counters, any failure sets a non-zero exit,
// and out-of-range parsing is exercised ONLY in a subprocess — parseResearchArgs
// calls process.exit(2) on bad input, which would kill THIS runner if called
// in-process.

import { parseResearchArgs, planFor } from "./research-plan.ts";

let passed = 0;
let failed = 0;

function check(name: string, cond: boolean): void {
  if (cond) passed++;
  else {
    failed++;
    console.error(`FAIL: ${name}`);
  }
}
function eq(name: string, got: unknown, want: unknown): void {
  check(
    `${name} (got ${JSON.stringify(got)}, want ${JSON.stringify(want)})`,
    JSON.stringify(got) === JSON.stringify(want),
  );
}

// ── parsing ────────────────────────────────────────────────────────────────
{
  const p = parseResearchArgs("");
  eq("empty → depth 1", p.depth, 1);
  eq("empty → no topic override", p.topicOverride, "");
  eq("empty → plan light", p.plan.name, "light");
}
{
  const p = parseResearchArgs("3");
  eq("'3' → depth 3", p.depth, 3);
  eq("'3' → no topic override", p.topicOverride, "");
}
{
  const p = parseResearchArgs("3 unitranche spreads right now");
  eq("'3 <topic>' → depth 3", p.depth, 3);
  eq("'3 <topic>' → topic captured", p.topicOverride, "unitranche spreads right now");
}
{
  const p = parseResearchArgs("what are unitranche spreads");
  eq("bare topic → depth 1", p.depth, 1);
  eq("bare topic → topic captured", p.topicOverride, "what are unitranche spreads");
}
{
  const p = parseResearchArgs("  5   full report please  ");
  eq("'5 <topic>' w/ whitespace → depth 5", p.depth, 5);
  eq("'5 <topic>' → trimmed topic", p.topicOverride, "full report please");
}
{
  // A leading non-integer number is topic text, not a depth.
  const p = parseResearchArgs("3.5% cap rate trends");
  eq("'3.5...' → not a depth, stays level 1", p.depth, 1);
  eq("'3.5...' → whole thing is the topic", p.topicOverride, "3.5% cap rate trends");
}

// ── plan mapping ─────────────────────────────────────────────────────────────
{
  const p = planFor(1);
  check("L1 seats no panel", p.panel === false);
  eq("L1 maxProbes 1", p.maxProbes, 1);
  check("L1 no gate", p.gate === false);
  check("L1 no report", p.report === false);
  eq("L1 nextRung 2", p.nextRung, 2);
  eq("L1 no cost note", p.costNote, null);
}
{
  const p = planFor(2);
  check("L2 seats no panel", p.panel === false);
  eq("L2 maxProbes 3", p.maxProbes, 3);
  eq("L2 no cost note", p.costNote, null);
}
{
  const p = planFor(3);
  check("L3 seats a panel", p.panel === true);
  check("L3 recency required", p.recency === true);
  check("L3 no gate", p.gate === false);
  eq("L3 tier lite", p.tier, "lite");
  check("L3 has a cost note", typeof p.costNote === "string" && p.costNote.length > 0);
}
{
  const p = planFor(4);
  check("L4 runs the gate", p.gate === true);
  eq("L4 tier standard", p.tier, "standard");
  check("L4 no report", p.report === false);
  eq("L4 nextRung 5", p.nextRung, 5);
}
{
  const p = planFor(5);
  check("L5 compiles a report", p.report === true);
  eq("L5 tier deep", p.tier, "deep");
  eq("L5 hands off to acos-research-riffs", p.handoff, "acos-research-riffs");
  eq("L5 is the ceiling (nextRung null)", p.nextRung, null);
}

// ── die-loudly on out-of-range depth (subprocess: exit code 2) ───────────────
async function exitCodeFor(arg: string): Promise<number> {
  const proc = Bun.spawn(["bun", `${import.meta.dir}/research-plan.ts`, arg], {
    stdout: "pipe",
    stderr: "pipe",
  });
  await proc.exited;
  return proc.exitCode ?? -1;
}
{
  eq("'0' exits 2", await exitCodeFor("0"), 2);
  eq("'6' exits 2", await exitCodeFor("6"), 2);
  eq("'-1' exits 2", await exitCodeFor("-1"), 2);
  eq("'2' exits 0", await exitCodeFor("2"), 0);
}

// ── tally ────────────────────────────────────────────────────────────────────
if (failed > 0) {
  console.error(`\n${failed} FAILED, ${passed} passed`);
  process.exit(1);
}
console.log(`All ${passed} checks passed`);
