#!/usr/bin/env bun
// investigate-plan.test.ts — proves the /investigate depth dial parses and maps
// correctly, and that the cut rule joins a target from any command position.
//
// Honest-tally discipline (feedback: a suite that throws mid-run still prints
// "N/N passed"): every check updates counters, any failure sets a non-zero exit,
// and out-of-range parsing is exercised ONLY in a subprocess —
// parseInvestigateArgs calls process.exit(2) on bad input, which would kill THIS
// runner if called in-process.

import { parseInvestigateArgs, planFor, joinTarget, ANGLES } from "./investigate-plan.ts";

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
  const p = parseInvestigateArgs("");
  eq("empty → depth 1", p.depth, 1);
  eq("empty → no topic override", p.topicOverride, "");
  eq("empty → plan light", p.plan.name, "light");
}
{
  // The TRAILING case — "why is this broken? /investigate 3" — parses to a bare
  // depth with no override, and the SKILL supplies the target from the message.
  const p = parseInvestigateArgs("3");
  eq("'3' → depth 3", p.depth, 3);
  eq("'3' → no topic override", p.topicOverride, "");
}
{
  const p = parseInvestigateArgs("3 why does the pill flicker");
  eq("'3 <topic>' → depth 3", p.depth, 3);
  eq("'3 <topic>' → topic captured", p.topicOverride, "why does the pill flicker");
}
{
  const p = parseInvestigateArgs("why does the pill flicker");
  eq("bare topic → depth 1", p.depth, 1);
  eq("bare topic → topic captured", p.topicOverride, "why does the pill flicker");
}
{
  const p = parseInvestigateArgs("  5   full report please  ");
  eq("'5 <topic>' w/ whitespace → depth 5", p.depth, 5);
  eq("'5 <topic>' → trimmed topic", p.topicOverride, "full report please");
}
{
  // A leading non-integer number is topic text, not a depth.
  const p = parseInvestigateArgs("3.5 second timeout in the watcher");
  eq("'3.5...' → not a depth, stays level 1", p.depth, 1);
  eq("'3.5...' → whole thing is the topic", p.topicOverride, "3.5 second timeout in the watcher");
}

// ── the cut rule: one rule for trailing / leading / mid-sentence ─────────────
{
  // TRAILING — the normal case. Text sits entirely before the command.
  eq(
    "trailing → text before is the target",
    joinTarget("why is this skill not working?", ""),
    "why is this skill not working?",
  );
  // LEADING — text sits entirely after the command.
  eq(
    "leading → text after is the target",
    joinTarget("", "why is this skill not working?"),
    "why is this skill not working?",
  );
  // MID-SENTENCE — both halves join into ONE target (the settled decision;
  // this is where /investigate deliberately differs from /research, which
  // treats text after the command as a replacement topic).
  eq(
    "mid-sentence → both halves join",
    joinTarget("why is this broken", "and also slow"),
    "why is this broken and also slow",
  );
  // Nothing left → "" so the SKILL can fall back to the previous message.
  eq("nothing left → empty", joinTarget("", ""), "");
  eq("whitespace only → empty", joinTarget("   ", "  "), "");
  // Inner whitespace is collapsed so the target is stable regardless of typing.
  eq("collapses inner whitespace", joinTarget("why   is  this", "broken  "), "why is this broken");
}

// ── plan mapping ─────────────────────────────────────────────────────────────
{
  const p = planFor(1);
  check("L1 seats no panel", p.panel === false);
  eq("L1 maxReaders 1", p.maxReaders, 1);
  check("L1 no gate", p.gate === false);
  check("L1 no history pass", p.history === false);
  check("L1 no report", p.report === false);
  eq("L1 nextRung 2", p.nextRung, 2);
  eq("L1 no cost note", p.costNote, null);
}
{
  const p = planFor(2);
  check("L2 seats no panel", p.panel === false);
  eq("L2 maxReaders 3", p.maxReaders, 3);
  eq("L2 no cost note", p.costNote, null);
}
{
  const p = planFor(3);
  check("L3 seats a panel", p.panel === true);
  check("L3 history pass required", p.history === true);
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
  check("L5 runs the gate", p.gate === true);
  eq("L5 is the ceiling (nextRung null)", p.nextRung, null);
}
{
  // Unlike /research, NO level hands off — there is no larger inward engine.
  // Asserted for every level so a future edit cannot quietly add one.
  for (const d of [1, 2, 3, 4, 5] as const) {
    eq(`L${d} never hands off`, planFor(d).handoff, null);
  }
}
{
  // A panel always costs; a bare-reader level never claims to. Ties the cost
  // note to the thing that actually spends, so the two cannot drift apart.
  for (const d of [1, 2, 3, 4, 5] as const) {
    const p = planFor(d);
    check(
      `L${d} cost note present iff a panel is seated`,
      p.panel === (p.costNote !== null),
    );
  }
}

// ── angles ───────────────────────────────────────────────────────────────────
{
  eq("four distinct angles", ANGLES.length, 4);
  const ids = ANGLES.map((a) => a.id);
  eq("angle ids are unique", new Set(ids).size, ids.length);
  check("every angle says HOW", ANGLES.every((a) => a.how.trim().length > 0));
  // L2 fires up to 3 bare readers, so there must be at least 3 angles to keep
  // them apart — if ANGLES ever shrinks, this is the check that says so.
  check("enough angles for L2's readers", ANGLES.length >= (planFor(2).maxReaders ?? 0));
}

// ── die-loudly on out-of-range depth (subprocess: exit code 2) ───────────────
async function exitCodeFor(arg: string): Promise<number> {
  const proc = Bun.spawn(["bun", `${import.meta.dir}/investigate-plan.ts`, arg], {
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
