/**
 * Append-only research ledger (design invariant I3).
 *
 * Entries are NEVER edited or deleted. A reversal or correction is a new entry
 * carrying `supersedes: <id>`; superseded status is DERIVED at read time, so the
 * file on disk is a true append-only log (Nygard ADR status semantics + ALCOA+
 * attributability: every entry names the agent and model that produced it).
 */

import { appendJsonl, nowIso, readJsonl } from "./util.ts";
import { loadManifest, paths, saveManifest, type Manifest } from "./session.ts";

export type EntryType =
  | "finding"
  | "decision"
  | "assumption"
  | "correction"
  | "question"
  | "answer"
  | "panel-change"
  | "stop-decision"
  | "gap"
  | "note";

export type Confidence = "verified" | "provisional" | "not-in-corpus" | "n/a";

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
}

export interface LedgerView extends LedgerEntry {
  status: "active" | "superseded";
  superseded_by?: string;
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
  };
  appendJsonl(paths(sessionId).ledger, entry);
  return entry;
}

export function readLedger(sessionId: string): LedgerEntry[] {
  return readJsonl<LedgerEntry>(paths(sessionId).ledger);
}

/** Ledger with derived supersession status — the canonical read model. */
export function view(sessionId: string): LedgerView[] {
  const raw = readLedger(sessionId);
  const supersededBy = new Map<string, string>();
  for (const e of raw) {
    if (e.supersedes) supersededBy.set(e.supersedes, e.id);
  }
  return raw.map((e) => {
    const by = supersededBy.get(e.id);
    return by
      ? ({ ...e, status: "superseded", superseded_by: by } as LedgerView)
      : ({ ...e, status: "active" } as LedgerView);
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
