#!/usr/bin/env bun
// investigate-plan.ts — the /investigate launcher's depth dial, as data.
//
// ONE source of truth for how the 1..5 depth number maps onto the
// acos-research-riffs engine when it is pointed INWARD (files on this machine)
// instead of outward (the web). The SKILL.md EXECUTES the plan this file
// returns; it never re-derives the mapping in prose. That keeps a rule like
// "level 4 runs the coverage gate" a unit-tested fact instead of a sentence a
// later edit could silently contradict.
//
// Deliberately mirrors research-plan.ts field-for-field where the meaning
// survives the translation, so the two dials can be diffed. Two fields differ,
// and the difference is the whole point of this skill:
//   maxProbes -> maxReaders   (a reader opens files; a probe searches the web)
//   recency   -> history      (the web asks "last 90 days"; code asks git)
//
// Bun + TypeScript, zero deps (project language default: TS/Rust over Python).

export type Depth = 1 | 2 | 3 | 4 | 5;

/**
 * The search angles readers are forced apart onto, from depth 2 up.
 *
 * Data, not prose, for the same reason the dial is: "use different angles" in a
 * document decays into three readers running the same grep. Each angle names a
 * DIFFERENT way into the same code, so a fact only one of them can reach is not
 * missed because all readers walked the same path.
 */
export const ANGLES = [
  {
    id: "by-folder",
    how: "Walk the directory tree that owns the behaviour. Read whole files, not grep hits.",
  },
  {
    id: "by-symbol",
    how: "Follow the named function/type/constant across every file that defines or calls it.",
  },
  {
    id: "by-history",
    how: "Read git log/blame for the region: when it last changed, what the commit said it was fixing.",
  },
  {
    id: "by-test",
    how: "Read the tests that cover it. A test states the intended contract; its absence is itself a finding.",
  },
] as const;

export type AngleId = (typeof ANGLES)[number]["id"];

export interface Plan {
  depth: Depth;
  name: string;
  /** riff init tier when a session/panel is created. */
  tier: "lite" | "standard" | "deep";
  /** Seat a generated panel of readers vs. fire bare readers with no panel. */
  panel: boolean;
  /** Bare-reader count when panel === false; null when a panel is seated. */
  maxReaders: number | null;
  /** Run the coverage gate + auditor — "what file did nobody open?" */
  gate: boolean;
  /**
   * Require a git-history pass before answering. The inward twin of /research's
   * `recency`: on the web, old may mean wrong; in code the clock is git. A line
   * untouched for two years is a different epistemic state from one changed
   * yesterday, and neither is readable from the file's current text alone.
   */
  history: boolean;
  /** Compile a cited report (every citation re-checked against the file). */
  report: boolean;
  /**
   * Skill to hand off to for the full run. Always null: unlike /research, whose
   * level 5 hands to acos-research-riffs, there is no larger inward engine to
   * hand to. Level 5 IS the ceiling and compiles its own report. Kept in the
   * shape so the two dials stay diffable.
   */
  handoff: string | null;
  /** One-line cost heads-up shown BEFORE spending, when a panel is seated. */
  costNote: string | null;
  /** The "dig deeper?" escalation target; null at the ceiling (level 5). */
  nextRung: Depth | null;
}

export interface Parsed {
  depth: Depth;
  /** "" → investigate the message text around /investigate; else this overrides it. */
  topicOverride: string;
  plan: Plan;
}

/** No number given → level 1 (light). Matches /research's "one probe" default. */
const DEFAULT_DEPTH: Depth = 1;

const PLANS: Record<Depth, Omit<Plan, "depth">> = {
  1: {
    name: "light",
    tier: "lite", panel: false, maxReaders: 1,
    gate: false, history: false, report: false,
    handoff: null, costNote: null, nextRung: 2,
  },
  2: {
    name: "light-plus",
    tier: "lite", panel: false, maxReaders: 3,
    gate: false, history: false, report: false,
    handoff: null, costNote: null, nextRung: 3,
  },
  3: {
    name: "higher-than-average",
    tier: "lite", panel: true, maxReaders: null,
    gate: false, history: true, report: false,
    handoff: null,
    costNote:
      "Heads-up: level 3 seats a small reader panel — roughly 15x the tokens of ordinary chat.",
    nextRung: 4,
  },
  4: {
    name: "deep",
    tier: "standard", panel: true, maxReaders: null,
    gate: true, history: true, report: false,
    handoff: null,
    costNote:
      "Heads-up: level 4 seats a fuller reader panel and runs the coverage gate — roughly 15x the tokens of ordinary chat.",
    nextRung: 5,
  },
  5: {
    name: "full-sweep",
    tier: "deep", panel: true, maxReaders: null,
    gate: true, history: true, report: true,
    handoff: null,
    costNote:
      "Heads-up: level 5 runs the full multi-reader sweep and compiles a cited report — roughly 15x the tokens of ordinary chat.",
    nextRung: null,
  },
};

export function planFor(depth: Depth): Plan {
  return { depth, ...PLANS[depth] };
}

/**
 * Parse the raw argument string that follows `/investigate`.
 *  - ""                     → level 1, use the surrounding message text
 *  - "3"                    → level 3, use the surrounding message text
 *  - "3 <topic words>"      → level 3, investigate "<topic words>"
 *  - "<topic words>"        → level 1, investigate "<topic words>"
 *
 * A leading integer OUTSIDE 1..5 is operator error and dies loudly (exit 2),
 * mirroring research-plan.ts and the riff CLI's numericFlag guard — never a
 * silent fallback to 1.
 *
 * NOTE ON POSITION: this parses only what follows the command token.
 * /investigate is normally TRAILING ("why is this broken? /investigate 3"), so
 * `topicOverride` is usually "" and the target comes from the rest of the
 * message. Assembling that target is the SKILL's job (it needs the whole
 * message, which this function never sees), not this parser's.
 */
export function parseInvestigateArgs(raw: string): Parsed {
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

/**
 * Join the message text that surrounds the command into ONE target.
 *
 * The cut rule (user decision, this build): strip the command token and its
 * depth number out of the message; whatever text remains — before it, after it,
 * or both — is the target. One rule covers trailing, leading and mid-sentence
 * placement, so there is no per-position special case to leave untested.
 *
 * Returns "" when nothing is left; the SKILL then falls back to the previous
 * user message.
 */
export function joinTarget(before: string, after: string): string {
  return [before, after]
    .map((s) => (s ?? "").trim())
    .filter(Boolean)
    .join(" ")
    .replace(/\s+/g, " ")
    .trim();
}

function fail(msg: string): never {
  console.error(`investigate-plan: ${msg}`);
  process.exit(2);
}

// CLI: `bun investigate-plan.ts "<the text after /investigate>"` → JSON plan.
if (import.meta.main) {
  const raw = process.argv.slice(2).join(" ");
  console.log(JSON.stringify(parseInvestigateArgs(raw), null, 2));
}
