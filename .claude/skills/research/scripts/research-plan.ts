#!/usr/bin/env bun
// research-plan.ts — the /research launcher's depth dial, as data.
//
// ONE source of truth for how the 1..5 depth number maps onto the
// acos-research-riffs engine. The SKILL.md EXECUTES the plan this file returns;
// it never re-derives the mapping in prose. That keeps a rule like "level 4 runs
// the coverage gate" a unit-tested fact instead of a sentence a later edit could
// silently contradict (the "single source of truth, not N copies" lesson the
// eternity-protocol scripts learned the hard way).
//
// Bun + TypeScript, zero deps (project language default: TS/Rust over Python).

export type Depth = 1 | 2 | 3 | 4 | 5;

export interface Plan {
  depth: Depth;
  name: string;
  /** riff init tier when a session/panel is created. */
  tier: "lite" | "standard" | "deep";
  /** Seat a generated panel (dossiers) vs. fire bare probes with no panel. */
  panel: boolean;
  /** Bare-probe count when panel === false; null when a panel is seated instead. */
  maxProbes: number | null;
  /** Run the coverage gate + auditor (Phase 3). */
  gate: boolean;
  /** Require at least one last-90-days recency sweep before answering. */
  recency: boolean;
  /** Compile a cited report (Phase 5). */
  report: boolean;
  /** Skill to hand off to for the full run (level 5 only). */
  handoff: string | null;
  /** One-line cost heads-up shown BEFORE spending, when a panel is seated. */
  costNote: string | null;
  /** The "keep riffing?" escalation target; null at the ceiling (level 5). */
  nextRung: Depth | null;
}

export interface Parsed {
  depth: Depth;
  /** "" → research the message that preceded /research; else this overrides it. */
  topicOverride: string;
  plan: Plan;
}

/** No number given → level 1 (light). Matches the agreed "one probe" default. */
const DEFAULT_DEPTH: Depth = 1;

const PLANS: Record<Depth, Omit<Plan, "depth">> = {
  1: {
    name: "light",
    tier: "lite", panel: false, maxProbes: 1,
    gate: false, recency: false, report: false,
    handoff: null, costNote: null, nextRung: 2,
  },
  2: {
    name: "light-plus",
    tier: "lite", panel: false, maxProbes: 3,
    gate: false, recency: false, report: false,
    handoff: null, costNote: null, nextRung: 3,
  },
  3: {
    name: "higher-than-average",
    tier: "lite", panel: true, maxProbes: null,
    gate: false, recency: true, report: false,
    handoff: null,
    costNote:
      "Heads-up: level 3 seats a small research panel — roughly 15x the tokens of ordinary chat.",
    nextRung: 4,
  },
  4: {
    name: "deep",
    tier: "standard", panel: true, maxProbes: null,
    gate: true, recency: true, report: false,
    handoff: null,
    costNote:
      "Heads-up: level 4 seats a fuller panel and runs the coverage gate — roughly 15x the tokens of ordinary chat.",
    nextRung: 5,
  },
  5: {
    name: "research-riffs-deep",
    tier: "deep", panel: true, maxProbes: null,
    gate: true, recency: true, report: true,
    handoff: "acos-research-riffs",
    costNote:
      "Heads-up: level 5 runs the full multi-agent research and compiles a cited report — roughly 15x the tokens of ordinary chat.",
    nextRung: null,
  },
};

export function planFor(depth: Depth): Plan {
  return { depth, ...PLANS[depth] };
}

/**
 * Parse the raw argument string that follows `/research`.
 *  - ""                     → level 1, use the preceding message
 *  - "3"                    → level 3, use the preceding message
 *  - "3 <topic words>"      → level 3, research "<topic words>"
 *  - "<topic words>"        → level 1, research "<topic words>"
 * A leading integer OUTSIDE 1..5 is operator error and dies loudly (exit 2),
 * mirroring the riff CLI's numericFlag guard — never a silent fallback to 1.
 */
export function parseResearchArgs(raw: string): Parsed {
  const trimmed = (raw ?? "").trim();
  const tokens = trimmed.length ? trimmed.split(/\s+/) : [];
  let depth: Depth = DEFAULT_DEPTH;
  let rest = trimmed;

  // A leading token that is a WHOLE number is read as the depth dial. A leading
  // non-integer (e.g. "3.5", "SOFR") is topic text, not a depth.
  if (tokens.length > 0 && /^-?\d+$/.test(tokens[0]!)) {
    const n = Number(tokens[0]);
    if (!Number.isInteger(n) || n < 1 || n > 5) {
      fail(`depth must be 1-5 (got "${tokens[0]}")`);
    }
    depth = n as Depth;
    rest = tokens.slice(1).join(" ");
  }

  return { depth, topicOverride: rest.trim(), plan: planFor(depth) };
}

function fail(msg: string): never {
  console.error(`research-plan: ${msg}`);
  process.exit(2);
}

// CLI: `bun research-plan.ts "<the text after /research>"` → prints the JSON plan.
if (import.meta.main) {
  const raw = process.argv.slice(2).join(" ");
  console.log(JSON.stringify(parseResearchArgs(raw), null, 2));
}
