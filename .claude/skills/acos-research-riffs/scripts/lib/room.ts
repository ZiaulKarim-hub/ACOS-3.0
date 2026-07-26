/**
 * Room state — what the browser dashboard shows.
 *
 * Deliberately COMPUTED from the session directory on every read, rather than
 * written to a separate state file by the conversation. The Investment
 * Committee room works the other way: its engine writes `meeting-state.json` as
 * the meeting progresses. That is right for a meeting, where the state IS the
 * transcript and only the engine knows it.
 *
 * Here it would be wrong. Every fact the room shows already exists on disk —
 * coverage counters, the ledger, the claim corpus, the panel. Asking the
 * conversation to also maintain a mirror of it would add a step the model can
 * forget, and a forgotten step means the room quietly shows stale research
 * while looking live. Recomputing costs microseconds and cannot drift.
 */

import { existsSync, statSync } from "node:fs";
import { join } from "node:path";
import { readJsonl } from "./util.ts";
import { loadManifest, paths, MODERATOR_L, TIERS } from "./session.ts";
import { evaluateGate, loadCoverage, type Dimension } from "./coverage.ts";
import { allClaims, corpusStats, dossierFiles, surfacedIds } from "./claims.ts";
import { loadPanel } from "./panel.ts";
import { view } from "./ledger.ts";
import { outline } from "./tree.ts";
import { evaluate } from "./report.ts";

export interface RoomState {
  session_id: string;
  topic: string;
  phase: string;
  tier: string;
  mode: string;
  updated: string;
  gate: { passed: boolean; reason: string; blocking: string[] };
  coverage: Array<
    Dimension & { fill: number; blocking: boolean }
  >;
  panel: Array<{ slug: string; role: string; title: string; status: string; claims: number }>;
  claims_recent: Array<{
    id: string;
    slug: string;
    dimension?: string;
    claim: string;
    tier?: number;
    as_of: string;
    volatile: boolean;
    sources: number;
    surfaced: boolean;
  }>;
  moderator: Array<{ id: string; claim: string; slug: string }>;
  ledger: Array<{
    id: string;
    type: string;
    status: string;
    supersedes?: string;
    body: string;
    ts: string;
  }>;
  corpus: Record<string, number>;
  outline: string;
  eval: { verdict: string; warn: number; fail: number; pass: number };
  moderator_due: boolean;
}

export function buildRoomState(sessionId: string): RoomState {
  const m = loadManifest(sessionId);
  const p = paths(sessionId);
  const cov = loadCoverage(sessionId);
  const gate = evaluateGate(sessionId);
  const claims = allClaims(sessionId);
  const seen = surfacedIds(sessionId);
  const panel = loadPanel(sessionId);
  const entries = view(sessionId);
  const ev = evaluate(sessionId);

  const claimsBySlug = new Map<string, number>();
  for (const c of claims) claimsBySlug.set(c.slug, (claimsBySlug.get(c.slug) ?? 0) + 1);

  const blockingIds = new Set(gate.blocking.map((d) => d.id));

  return {
    session_id: sessionId,
    topic: m.topic,
    phase: m.phase,
    tier: m.tier,
    mode: m.mode,
    updated: m.updated,
    gate: { passed: gate.passed, reason: gate.reason, blocking: [...blockingIds] },
    coverage: cov.dimensions.map((d) => ({
      ...d,
      // A capped or attested dimension reads as full; an unprobed one reads as
      // empty no matter how many claims landed elsewhere.
      fill:
        d.status === "saturated" || d.status === "capped" || d.status === "attested"
          ? 1
          : d.probes === 0
            ? 0
            : Math.min(0.85, d.probes / Math.max(1, d.cap)),
      blocking: blockingIds.has(d.id),
    })),
    panel: panel.seats.map((s) => ({
      slug: s.slug,
      role: s.role,
      title: s.title,
      status: s.status,
      claims: claimsBySlug.get(s.slug) ?? 0,
    })),
    claims_recent: claims.slice(-40).reverse().map((c) => ({
      id: c.id,
      slug: c.slug,
      ...(c.dimension ? { dimension: c.dimension } : {}),
      claim: c.claim,
      ...(c.sources[0]?.tier ? { tier: c.sources[0].tier } : {}),
      as_of: c.as_of,
      volatile: !!c.volatile,
      sources: c.sources.length,
      surfaced: seen.has(c.id),
    })),
    moderator: readJsonl<{ claim_id: string }>(p.surfaced)
      .slice(-6)
      .reverse()
      .map((r) => {
        const c = claims.find((x) => x.id === r.claim_id);
        return { id: r.claim_id, claim: c?.claim ?? "(claim not found)", slug: c?.slug ?? "?" };
      }),
    ledger: entries.slice(-25).reverse().map((e) => ({
      id: e.id,
      type: e.type,
      status: e.status,
      ...(e.supersedes ? { supersedes: e.supersedes } : {}),
      body: e.body,
      ts: e.ts,
    })),
    corpus: corpusStats(sessionId),
    outline: outline(sessionId),
    eval: {
      verdict: ev.verdict,
      warn: ev.checks.filter((c) => c.verdict === "warn").length,
      fail: ev.checks.filter((c) => c.verdict === "fail").length,
      pass: ev.checks.filter((c) => c.verdict === "pass").length,
    },
    moderator_due: m.mode === "standard" && m.moderator_streak >= MODERATOR_L,
  };
}

/**
 * A cheap fingerprint of everything the room reads, so the server can poll for
 * change without re-serialising the whole state on every tick.
 */
export function stateFingerprint(sessionId: string): string {
  const p = paths(sessionId);
  const watched = [p.manifest, p.coverage, p.panel, p.ledger, p.surfaced, p.tree, p.questions];
  const parts: string[] = [];
  for (const f of watched) {
    try {
      const s = statSync(f);
      parts.push(`${f}:${s.mtimeMs}:${s.size}`);
    } catch {
      parts.push(`${f}:0`);
    }
  }
  // Each dossier's claim file must be stat'd individually. Appending to a file
  // does NOT change its directory's mtime, so watching the directory alone would
  // miss an agent adding claims to a dossier that already exists — which is the
  // most common change the room needs to react to.
  try {
    const d = statSync(p.dossiers);
    parts.push(`dossiers:${d.mtimeMs}`);
    for (const { slug, path } of dossierFiles(sessionId)) {
      try {
        const s = statSync(path);
        parts.push(`${slug}:${s.mtimeMs}:${s.size}`);
      } catch {
        parts.push(`${slug}:0`);
      }
    }
  } catch {
    parts.push("dossiers:0");
  }
  return parts.join("|");
}

export function roomExists(sessionId: string): boolean {
  return existsSync(join(paths(sessionId).root, "manifest.json"));
}

// ---------------------------------------------------------------------------
// IC-state adapter: the room PAGE is the Investment Committee's own meeting.html
// (verbatim, relabeled), so the layout, the call-a-seat buttons, hand-raising,
// reactions and the typewriter floor all come from IC's real code. That page
// consumes a `meeting-state.json`-shaped object; this maps a riff RoomState into
// exactly that shape. Nothing here reimplements the UI — it only translates data.

/** A concise seat label for the arc (IC's `short`): full titles overflow the tiny name slot. */
function shortLabel(s: string): string {
  const t = (s || "").trim();
  if (t.length <= 18) return t;
  const cut = t.slice(0, 18);
  const sp = cut.lastIndexOf(" ");
  return (sp > 8 ? cut.slice(0, sp) : cut).trim() + "…";
}

export interface IcState {
  session_id: string;
  deal: { name: string; amount: string; ltv: string; leaning: string; sub: string };
  vote: { for: number; against: number };
  seats: Array<{
    n: number; short: string; name: string; vote: string; emoji: string;
    research: number; threads: Array<{ topic: string; status: string }>; objections: unknown[];
  }>;
  briefing: Array<{
    seat: number; short: string; name: string; vote: string;
    question: string; context: string; mitigant: string; n_objections: number;
  }>;
  timeline: Array<{
    type: string; seat: number; name: string; short: string;
    text: string; reactions: Record<string, string>; hands: number[];
  }>;
  phase: string;
}

export function buildIcState(sessionId: string): IcState {
  const s = buildRoomState(sessionId);
  const dims = s.coverage;
  const total = dims.length || 1;
  const covered = dims.filter((d) => d.fill >= 1).length;
  const blocking = dims.filter((d) => d.blocking).length;

  const claimsBySlug = new Map<string, typeof s.claims_recent>();
  for (const c of s.claims_recent) {
    const arr = claimsBySlug.get(c.slug) ?? [];
    arr.push(c);
    claimsBySlug.set(c.slug, arr);
  }

  // A research seat maps to a committee seat. The skeptic votes "against" so it
  // renders in IC's red — it is the seat whose whole job is to dissent.
  const seats = s.panel.map((p, i) => {
    const cs = claimsBySlug.get(p.slug) ?? [];
    return {
      n: i + 1,
      short: shortLabel(p.title || p.slug),
      name: p.title || p.slug,
      vote: p.role === "skeptic" ? "against" : "for",
      emoji: p.role === "skeptic" ? "😠" : "🙂",
      research: p.claims,
      threads: cs.slice(0, 4).map((c) => ({ topic: c.claim, status: c.surfaced ? "done" : "running" })),
      objections: [] as unknown[],
    };
  });

  const briefing = seats.map((seat) => ({
    seat: seat.n,
    short: seat.short,
    name: seat.name,
    vote: seat.vote,
    question: seat.name,
    context: `${seat.research} findings gathered`,
    mitigant: seat.threads[0]?.topic ?? "",
    n_objections: seat.research,
  }));

  // The ledger becomes the meeting transcript. IC plays the LAST timeline entry
  // as the newest turn, so order oldest -> newest; attribute each to a seat in
  // rotation for visual variety (RoomState ledger rows carry no author slug).
  const byN = seats.length ? seats : [{ n: 1, name: "Panel", short: "Panel" }];
  const led = [...s.ledger].sort((a, b) => (a.ts ?? "").localeCompare(b.ts ?? ""));
  const timeline = led.map((e, i) => {
    const seat = byN[i % byN.length]!;
    return {
      type: "turn",
      seat: seat.n,
      name: seat.name,
      short: seat.short,
      text: e.body,
      reactions: {} as Record<string, string>,
      hands: [] as number[],
    };
  });

  const sources = (s.corpus as Record<string, number>).unique_sources ?? (s.corpus as Record<string, number>).sources ?? 0;
  return {
    session_id: s.session_id,
    deal: {
      name: s.topic,
      amount: `${(s.corpus as Record<string, number>).claims ?? 0} claims`,
      ltv: `${covered}/${total} covered`,
      leaning: s.gate.passed ? "COVERAGE MET" : "GATE OPEN",
      sub: [s.tier ? `${s.tier} tier` : "", s.mode, `${sources} sources`, s.updated ? `updated ${s.updated}` : ""]
        .filter(Boolean)
        .join(" · "),
    },
    vote: { for: covered, against: blocking },
    seats,
    briefing,
    timeline,
    phase: s.phase,
  };
}
