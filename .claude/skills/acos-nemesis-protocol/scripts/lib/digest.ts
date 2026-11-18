/**
 * digest.ts — how the open ledger is PRESENTED to the writer, inside a budget.
 *
 * WHY THIS FILE EXISTS (the 2026-11-01 context-burn outage, website-design-okoa/v2).
 * The Stop hook enumerated EVERY open issue in its blocking reason. With 436 open issues
 * that reason measured 336,897 characters — about 84,224 tokens — and the Stop hook fires
 * at the END OF EVERY TURN while the ledger is open. Claude Code puts a blocking reason
 * into the conversation, so each turn re-injected ~84k tokens that compaction could not
 * drop (it had just arrived). Four turns filled a 500,000-token context; the session
 * compacted; the next Stop hook injected it again. 48% of that project's 132.6 MB live
 * transcript was this one message repeated. 73 compactions came out of it.
 *
 * WHAT IS NOT THE CAUSE, so nobody "fixes" the wrong thing: the per-edit judge charter
 * (charter.ts) is big too, but it is sent to the daemon's own `claude -p` child and never
 * enters the writer's conversation. Only the hooks' own text does.
 *
 * THE RULE THIS FILE ENCODES. Nemesis's guarantee is that the writer is BLOCKED while the
 * ledger is open (R-027) — the block is the enforcement, not the length of the prose. A
 * writer can only act on one issue at a time, and the ledger on disk is the complete,
 * durable record (`nemesis issue list --open`, `nemesis ladder <id>`, `nemesis report`).
 * So the hook names the issues that matter MOST, says exactly how many it did not name and
 * at what severities, and points at the ledger. Nothing is hidden; nothing is deferred;
 * no severity is dropped. The count in the header is always the TRUE total.
 *
 * Two independent limits, because either alone can be defeated:
 *   detail   — how many issues get a bullet (a count)
 *   maxChars — a hard ceiling on the bullets (bytes), so one pathological `what` or a
 *              verbose rung instruction can never blow the budget again
 */
import { SEVERITIES, type Issue } from "./state";

/** Issues named in the Stop hook's blocking reason. */
export const DEFAULT_STOP_DETAIL = 12;
export const DEFAULT_STOP_MAX_CHARS = 20_000;
/** Issues named in the every-prompt re-injection (R-028) — smaller, it repeats more often. */
export const DEFAULT_PROMPT_DETAIL = 12;
export const DEFAULT_PROMPT_MAX_CHARS = 8_000;

const SEV_RANK = new Map<string, number>(SEVERITIES.map((s, n) => [s, n]));

/**
 * Worst severity first, then oldest first. The order is what makes a capped list honest:
 * the one critical issue among 436 is always named, and within a severity the issue that
 * has been open longest is named before one opened a minute ago.
 */
export function rankIssues(issues: Issue[]): Issue[] {
  return [...issues].sort((a, b) =>
    (SEV_RANK.get(a.severity) ?? 99) - (SEV_RANK.get(b.severity) ?? 99) ||
    a.created_at.localeCompare(b.created_at) ||
    a.id.localeCompare(b.id));
}

/** "critical: 1, high: 75, medium: 148, low: 212" — only the severities actually present. */
export function severityCensus(issues: Issue[]): string {
  const parts = SEVERITIES
    .map((s) => [s, issues.filter((i) => i.severity === s).length] as const)
    .filter(([, n]) => n > 0)
    .map(([s, n]) => `${s}: ${n}`);
  return parts.length ? parts.join(", ") : "none";
}

export interface DigestOpts {
  detail?: number;
  maxChars?: number;
  /** How one issue is rendered. The caller owns the wording; this file owns the budget. */
  bullet: (i: Issue) => string;
}

/**
 * The capped, ranked view. `hidden` is every issue that did not get a bullet — the caller
 * must account for it (see `moreLine`), never drop it silently.
 */
export function issueDigest(issues: Issue[], opts: DigestOpts): { lines: string[]; shown: number; hidden: Issue[] } {
  const detail = Math.max(1, opts.detail ?? DEFAULT_STOP_DETAIL);
  const budget = Math.max(500, opts.maxChars ?? DEFAULT_STOP_MAX_CHARS);
  const ranked = rankIssues(issues);
  const lines: string[] = [];
  let used = 0;
  for (const i of ranked) {
    if (lines.length >= detail) break;
    const b = opts.bullet(i);
    // Always render the worst issue, however long it is: a budget that could show nothing
    // would turn a block into a riddle. Every later bullet must fit.
    if (lines.length > 0 && used + b.length + 1 > budget) break;
    lines.push(b);
    used += b.length + 1;
  }
  return { lines, shown: lines.length, hidden: ranked.slice(lines.length) };
}

/** The one line that accounts for everything the digest did not name. Null when it named all. */
export function moreLine(hidden: Issue[], howToSeeAll: string): string | null {
  if (!hidden.length) return null;
  return `…and ${hidden.length} more open issue(s) not listed here (${severityCensus(hidden)}) — every one still blocks. The ledger on disk is the full record: ${howToSeeAll}`;
}

/** D-46 default: identical blocks tolerated before the hook releases the turn. Must stay
 *  well under Claude Code's own cap (`CLAUDE_CODE_STOP_HOOK_BLOCK_CAP ?? 8`), because being
 *  overridden by the host means the hook lost control of its own contract. */
export const DEFAULT_MAX_IDENTICAL_BLOCKS = 6;


