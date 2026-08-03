/**
 * Append-only research ledger (design invariant I3).
 *
 * Entries are NEVER edited or deleted. A reversal or correction is a new entry
 * carrying `supersedes: <id>`; superseded status is DERIVED at read time, so the
 * file on disk is a true append-only log (Nygard ADR status semantics + ALCOA+
 * attributability: every entry names the agent and model that produced it).
 */

import { appendJsonl, nowIso, readJsonlStrict } from "./util.ts";
import { loadManifest, paths, saveManifest, type Manifest } from "./session.ts";

export const ENTRY_TYPES = [
  "finding",
  "decision",
  "assumption",
  "correction",
  "question",
  "answer",
  "panel-change",
  "stop-decision",
  "gap",
  "note",
] as const;

export type EntryType = (typeof ENTRY_TYPES)[number];

export const CONFIDENCES = ["verified", "provisional", "not-in-corpus", "n/a"] as const;

export type Confidence = (typeof CONFIDENCES)[number];

export interface Provenance {
  source: string;
  url?: string;
  tier?: 1 | 2 | 3 | 4;
  as_of?: string;
}

export interface LedgerEntry {
  id: string;
  ts: string;
  type: EntryType;
  supersedes?: string;
  concept?: string;
  question?: string;
  context?: string;
  body: string;
  consequences?: string[];
  confidence?: Confidence;
  provenance?: Provenance[];
  author?: { agent?: string; model?: string };
  claim_ids?: string[];
  /** Drill-thread id (deep-drill chat mode, e.g. "T3") — optional and
   *  additive: entries without it are legal forever. The orchestrator assigns
   *  thread ids per SKILL.md; the engine only records them. */
  thread?: string;
  /** Depth-ladder level (0-2) this entry was produced at — optional and
   *  additive, same discipline as `thread`. The ladder semantics live in
   *  SKILL.md; the engine only validates the range. */
  depth?: number;
}

export interface LedgerView extends LedgerEntry {
  status: "active" | "superseded";
  superseded_by?: string;
  /**
   * Set when MORE than one entry claims to supersede this one — a recorded
   * conflict of corrections. Holds the losing superseders oldest first;
   * `superseded_by` holds the newest.
   */
  superseded_by_conflict?: string[];
}

export function nextId(m: Manifest): string {
  const id = `L-${String(m.next_ledger_id).padStart(4, "0")}`;
  m.next_ledger_id += 1;
  saveManifest(m);
  return id;
}

export function addEntry(sessionId: string, partial: Partial<LedgerEntry>): LedgerEntry {
  const m = loadManifest(sessionId);
  if (!partial.body || !partial.body.trim()) {
    throw new Error("ledger entry requires a non-empty `body`");
  }
  if (!partial.type) throw new Error("ledger entry requires a `type`");
  // Append-only means a bad entry can never be edited out — validate BEFORE
  // nextId() burns an id (it saves the manifest), so a reject leaves no gap.
  if (!ENTRY_TYPES.includes(partial.type)) {
    throw new Error(`unknown entry type "${partial.type}" — one of: ${ENTRY_TYPES.join(", ")}`);
  }
  if (partial.confidence && !CONFIDENCES.includes(partial.confidence)) {
    throw new Error(
      `unknown confidence "${partial.confidence}" — one of: ${CONFIDENCES.join(", ")}`,
    );
  }
  // Deep-drill fields are optional, but when present they must be usable: an
  // empty thread id stamps nothing traceable, and an out-of-range depth would
  // mislabel where on the ladder (L0-L2) an answer came from.
  if (
    partial.thread !== undefined &&
    (typeof partial.thread !== "string" || !partial.thread.trim())
  ) {
    throw new Error("`thread` must be a non-empty string when present (e.g. \"T3\")");
  }
  if (
    partial.depth !== undefined &&
    (!Number.isInteger(partial.depth) || partial.depth < 0 || partial.depth > 2)
  ) {
    throw new Error(`\`depth\` must be an integer 0-2 when present, got: ${partial.depth}`);
  }
  if (partial.supersedes && !readLedger(sessionId).some((e) => e.id === partial.supersedes)) {
    throw new Error(
      `supersedes target ${partial.supersedes} does not exist in the ledger — ` +
        `a dangling supersedes would leave the wrong entry active forever`,
    );
  }
  const entry: LedgerEntry = {
    id: nextId(m),
    ts: nowIso(),
    type: partial.type,
    body: partial.body,
    ...(partial.supersedes ? { supersedes: partial.supersedes } : {}),
    ...(partial.concept ? { concept: partial.concept } : {}),
    ...(partial.question ? { question: partial.question } : {}),
    ...(partial.context ? { context: partial.context } : {}),
    ...(partial.consequences ? { consequences: partial.consequences } : {}),
    ...(partial.confidence ? { confidence: partial.confidence } : {}),
    ...(partial.provenance ? { provenance: partial.provenance } : {}),
    ...(partial.author ? { author: partial.author } : {}),
    ...(partial.claim_ids ? { claim_ids: partial.claim_ids } : {}),
    ...(partial.thread ? { thread: partial.thread } : {}),
    // depth 0 (L0) is falsy — spread on !== undefined, never on truthiness.
    ...(partial.depth !== undefined ? { depth: partial.depth } : {}),
  };
  appendJsonl(paths(sessionId).ledger, entry);
  return entry;
}

const warnedDrops = new Set<string>();

export function readLedger(sessionId: string): LedgerEntry[] {
  const file = paths(sessionId).ledger;
  const { rows, dropped } = readJsonlStrict<LedgerEntry>(file);
  // The ledger is the evidence trail (I3) — a malformed line is silent evidence
  // loss, so say so on stderr (once per line per process; readLedger runs on
  // every recompute tick when the room server is up).
  for (const line of dropped) {
    const key = `${file}:${line}`;
    if (!warnedDrops.has(key)) {
      warnedDrops.add(key);
      console.error(`riff: ledger line ${line} is malformed and was skipped — evidence may be missing (${file})`);
    }
  }
  return rows;
}

/** Ledger with derived supersession status — the canonical read model. */
export function view(sessionId: string): LedgerView[] {
  const raw = readLedger(sessionId);
  // ALL superseders per target, in append order — two independent corrections
  // aiming at the same entry are a recorded conflict, not last-writer-wins.
  const supersededBy = new Map<string, string[]>();
  for (const e of raw) {
    if (e.supersedes) {
      const list = supersededBy.get(e.supersedes);
      if (list) list.push(e.id);
      else supersededBy.set(e.supersedes, [e.id]);
    }
  }
  return raw.map((e) => {
    const by = supersededBy.get(e.id);
    if (!by) return { ...e, status: "active" } as LedgerView;
    const v = { ...e, status: "superseded", superseded_by: by[by.length - 1]! } as LedgerView;
    if (by.length > 1) v.superseded_by_conflict = by.slice(0, -1);
    return v;
  });
}

/** Full supersession chains, oldest first — the "decisions and reversals" section. */
export function chains(sessionId: string): LedgerView[][] {
  const all = view(sessionId);
  const byId = new Map(all.map((e) => [e.id, e]));
  const isHead = (e: LedgerView) => !e.supersedes;
  const out: LedgerView[][] = [];
  for (const head of all.filter(isHead)) {
    const chain: LedgerView[] = [head];
    let cur = head;
    while (cur.superseded_by) {
      // Losing superseders of a conflict come first — they are older than the
      // winner, so the chain stays in true append order and no recorded
      // reversal disappears from the "decisions and reversals" section.
      for (const loserId of cur.superseded_by_conflict ?? []) {
        const loser = byId.get(loserId);
        if (loser) chain.push(loser);
      }
      const nxt = byId.get(cur.superseded_by);
      if (!nxt) break;
      chain.push(nxt);
      cur = nxt;
    }
    if (chain.length > 1) out.push(chain);
  }
  return out;
}

export function summarize(sessionId: string): Record<string, number> {
  const all = view(sessionId);
  const counts: Record<string, number> = { total: all.length, active: 0, superseded: 0 };
  for (const e of all) {
    counts[e.status] = (counts[e.status] ?? 0) + 1;
    counts[`type:${e.type}`] = (counts[`type:${e.type}`] ?? 0) + 1;
    if (e.confidence) counts[`conf:${e.confidence}`] = (counts[`conf:${e.confidence}`] ?? 0) + 1;
  }
  return counts;
}
