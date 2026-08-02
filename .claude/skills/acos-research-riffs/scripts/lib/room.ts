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

import { existsSync, statSync, readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { readJsonl } from "./util.ts";
import { loadManifest, paths, MODERATOR_L, SATURATION_K, TIERS } from "./session.ts";
import { loadCoverage, computeGate, type Dimension } from "./coverage.ts";
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
  /** Sections that failed to load this tick (torn file mid-write, malformed
   *  corpus lines) — each degraded to a default instead of killing the build. */
  errors: string[];
}

export function buildRoomState(sessionId: string): RoomState {
  const m = loadManifest(sessionId);
  const p = paths(sessionId);

  // Every load below is individually guarded: writeJson is non-atomic, so a
  // server poll racing a CLI write — or a session hard-killed mid-write — can
  // leave any one of these files torn. A torn file must degrade its own
  // section and land in errors[], not throw: the server swallows build
  // throws, so an unguarded throw here is a permanently blank room with zero
  // diagnostic. Only the manifest stays load-bearing — without it there is no
  // session to show, and loadManifest already fails with a recovery hint.
  const errors: string[] = [];
  const section = <T>(name: string, load: () => T, fallback: T): T => {
    try {
      return load();
    } catch (e) {
      errors.push(`${name}: ${e instanceof Error ? e.message : String(e)}`);
      return fallback;
    }
  };
  const cov = section("coverage", () => loadCoverage(sessionId), { k: SATURATION_K, dimensions: [] });
  const claims = section("claims", () => allClaims(sessionId), []);
  const seen = section("surfaced", () => surfacedIds(sessionId), new Set<string>());
  const panel = section("panel", () => loadPanel(sessionId), { seats: [], approved: false, history: [] });
  const entries = section("ledger", () => view(sessionId), []);
  const ev = section(
    "eval",
    () => evaluate(sessionId),
    { checks: [], summary: {}, verdict: "FAIL" } as ReturnType<typeof evaluate>,
  );
  const corpus = section("corpus", () => corpusStats(sessionId), {} as Record<string, number>);
  const outlineText = section("outline", () => outline(sessionId), "");

  // Agent-written dossier lines can carry an in-namespace id but no sources
  // array. Treat those as unsourced and COUNT them into errors[] instead of
  // throwing (M8) — one malformed line must not kill every state build.
  const unsourced = claims.filter((c) => !Array.isArray(c.sources)).length;
  if (unsourced) errors.push(`claims: ${unsourced} corpus line(s) missing a sources array — treated as unsourced`);

  // Gate + dimension statuses via coverage.ts's computeGate — the ONE gate
  // implementation, shared with evaluateGate so the room can never show a
  // different verdict than the ledger records (I40). computeGate is pure: no
  // saveCoverage side effect. The room is rebuilt on every server poll;
  // persisting here would rewrite a fingerprinted file each tick (so the
  // server would broadcast forever) and race the CLI's own load-modify-save
  // on coverage.json. A room read must stay a read.
  const gate = computeGate(cov);
  const statusOf = new Map([...gate.blocking, ...gate.ready].map((d: Dimension) => [d.id, d.status] as const));
  const dims = cov.dimensions.map((d) => ({ ...d, status: statusOf.get(d.id) ?? d.status }));

  const claimsBySlug = new Map<string, typeof claims>();
  for (const c of claims) {
    const arr = claimsBySlug.get(c.slug) ?? [];
    arr.push(c);
    claimsBySlug.set(c.slug, arr);
  }

  // "Recent" must be recent for EVERY seat: allClaims returns whole dossiers in
  // directory-listing order, so a plain global tail is just whichever dossiers
  // list last — early-listed seats would vanish from the feed once the corpus
  // outgrows the window. Instead take each dossier's tail (file order within a
  // dossier IS its append order) and interleave them newest-first.
  const RECENT = 40;
  const per = Math.ceil(RECENT / Math.max(1, claimsBySlug.size));
  const tails = [...claimsBySlug.values()].map((arr) => arr.slice(-per).reverse());
  const recent: typeof claims = [];
  for (let i = 0; recent.length < RECENT; i++) {
    let took = false;
    for (const t of tails) {
      if (i < t.length && recent.length < RECENT) {
        recent.push(t[i]!);
        took = true;
      }
    }
    if (!took) break;
  }

  const blockingIds = new Set<string>(gate.blocking.map((d: Dimension) => d.id));

  return {
    session_id: sessionId,
    topic: m.topic,
    phase: m.phase,
    tier: m.tier,
    mode: m.mode,
    updated: m.updated,
    gate: { passed: gate.passed, reason: gate.reason, blocking: [...blockingIds] },
    coverage: dims.map((d) => ({
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
      claims: claimsBySlug.get(s.slug)?.length ?? 0,
    })),
    claims_recent: recent.map((c) => {
      // Displayed tier is the BEST evidence tier across sources (claim-level
      // tier as fallback), matching how assess() and the report checks judge
      // evidence quality — not whichever source happens to be listed first.
      // A missing sources array reads as no sources (counted above, M8).
      const srcs = Array.isArray(c.sources) ? c.sources : [];
      const tier = Math.min(...srcs.map((s) => s.tier ?? 9), c.tier ?? 9);
      return {
        id: c.id,
        slug: c.slug,
        ...(c.dimension ? { dimension: c.dimension } : {}),
        claim: c.claim,
        ...(tier <= 4 ? { tier } : {}),
        as_of: c.as_of,
        volatile: !!c.volatile,
        sources: srcs.length,
        surfaced: seen.has(c.id),
      };
    }),
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
    corpus,
    outline: outlineText,
    eval: {
      verdict: ev.verdict,
      warn: ev.checks.filter((c) => c.verdict === "warn").length,
      fail: ev.checks.filter((c) => c.verdict === "fail").length,
      pass: ev.checks.filter((c) => c.verdict === "pass").length,
    },
    moderator_due: m.mode === "standard" && m.moderator_streak >= MODERATOR_L,
    errors,
  };
}

/**
 * A cheap fingerprint of everything the room reads, so the server can poll for
 * change without re-serialising the whole state on every tick.
 */
export function stateFingerprint(sessionId: string): string {
  const p = paths(sessionId);
  const watched = [
    p.manifest, p.coverage, p.panel, p.ledger, p.surfaced, p.tree, p.questions,
    // live-room files written by riff-live — without these the server would not
    // push when a seat starts thinking or a turn lands, so the room would stall.
    join(p.root, "room-turns.jsonl"), join(p.root, "room-thinking.json"), join(p.root, "room-level.json"),
  ];
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
  // RoomState.eval depends on report/ — REPORT.md freshness and the
  // CITATIONS*.md verdict files (same glob citationVerdict uses) — so those
  // must be watched too, or the room's eval row stalls stale during exactly
  // Phase 5, when the compiler and citation verifier write them.
  try {
    const r = statSync(p.report);
    parts.push(`report:${r.mtimeMs}`);
    for (const f of readdirSync(p.report).filter((f) => /^(REPORT|CITATIONS.*)\.md$/i.test(f))) {
      try {
        const s = statSync(join(p.report, f));
        parts.push(`${f}:${s.mtimeMs}:${s.size}`);
      } catch {
        parts.push(`${f}:0`);
      }
    }
  } catch {
    parts.push("report:0");
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
  deal: { name: string; amount: string; ltv: string; leaning: string; sub: string; close_note: string };
  // Data-driven labels (CONTRACT-4): the page's committee-vote wording
  // (FOR/AGAINST and its close line) is only a fallback for when these fields
  // are absent — a research room relabels the gauge, the per-seat status and
  // the close line in gate language.
  vote: { for: number; against: number; label_a: string; label_f: string; note: string };
  seats: Array<{
    n: number; short: string; name: string; vote: string; vote_label: string; emoji: string;
    research: number; threads: Array<{ topic: string; status: string }>; objections: unknown[];
  }>;
  briefing: Array<{
    seat: number; short: string; name: string; vote: string; vote_label: string;
    question: string; context: string; mitigant: string; n_objections: number;
  }>;
  timeline: Array<{
    type: string; seat: number; name: string; short: string;
    text: string; reactions: Record<string, string>; hands: number[];
    // The chair question a live turn answered (from room-turns.jsonl), so the
    // page can backfill a Chair line; `fallback` marks ledger-derived context
    // lines (type "note", neutral "Session log" speaker) that are not spoken
    // turns and must never be typewriter-played or transcript-backfilled.
    chair?: string; fallback?: boolean;
  }>;
  /** Monotonic count of live turns in room-turns.jsonl, err turns excluded
   *  (CONTRACT-3). The page detects new answers by THIS, never by timeline
   *  length — the timeline shrinks at the fallback->live switchover and is
   *  capped, so raw length regresses. */
  turns_total: number;
  /** What a seat's `research` counter counts ("findings") — the IC page's
   *  "research agents running" framing would be a fabrication here (I41). */
  research_label: string;
  phase: string;
  reading_level: number;
  thinking?: { seat: number };
  /** Degraded sections from this build (see RoomState.errors). */
  errors: string[];
}

export function buildIcState(sessionId: string): IcState {
  const s = buildRoomState(sessionId);
  const dims = s.coverage;
  const total = dims.length || 1;
  const covered = dims.filter((d) => d.fill >= 1).length;
  const blocking = dims.filter((d) => d.blocking).length;

  // Threads come from each seat's OWN dossier tail (newest first), not from the
  // shared recent-claims window — a seat must not lose its threads just because
  // other seats dominate the recent feed.
  const corpus = allClaims(sessionId);
  const seen = surfacedIds(sessionId);
  const corpusBySlug = new Map<string, typeof corpus>();
  for (const c of corpus) {
    const arr = corpusBySlug.get(c.slug) ?? [];
    arr.push(c);
    corpusBySlug.set(c.slug, arr);
  }

  // A research seat maps to a committee seat. The skeptic votes "against" so it
  // renders in IC's red — it is the seat whose whole job is to dissent. Retired
  // seats keep their number (riff-live indexes panel[n-1], so filtering would
  // desync seat numbering) but are labeled so the chair sees the abandoned lane.
  // vote_label overrides the page's FOR/AGAINST wording per seat (CONTRACT-4).
  const seats = s.panel.map((p, i) => {
    const cs = (corpusBySlug.get(p.slug) ?? []).slice(-4).reverse();
    const retired = p.status === "retired";
    return {
      n: i + 1,
      short: shortLabel(p.title || p.slug) + (retired ? " (retired)" : ""),
      name: (p.title || p.slug) + (retired ? " (retired)" : ""),
      vote: p.role === "skeptic" ? "against" : "for",
      vote_label: retired ? "DORMANT" : p.role === "skeptic" ? "DISSENT" : "RESEARCH",
      emoji: retired ? "😴" : p.role === "skeptic" ? "😠" : "🙂",
      research: p.claims,
      threads: cs.map((c) => ({ topic: c.claim, status: seen.has(c.id) ? "done" : "running" })),
      objections: [] as unknown[],
    };
  });

  const briefing = seats.map((seat) => ({
    seat: seat.n,
    short: seat.short,
    name: seat.name,
    vote: seat.vote,
    vote_label: seat.vote_label,
    question: seat.name,
    context: `${seat.research} findings gathered`,
    mitigant: seat.threads[0]?.topic ?? "",
    n_objections: seat.research,
  }));

  // The transcript: once seats start speaking live (riff-live writes room-turns.jsonl),
  // the timeline IS those spoken turns, attributed to the real seat. Before the
  // meeting opens, fall back to the ledger so the room is never empty — those
  // are orchestrator log lines, not anything a seat said, so they carry a
  // neutral "Session log" speaker and the fallback tag (M13); the page renders
  // them as dimmed context, never as seat speech. IC plays the LAST timeline
  // entry as the newest turn, so order oldest -> newest — by APPEND order,
  // never a timestamp re-sort: ledger timestamps are second-granularity and
  // the CLI appends in bursts, so re-sorting would shuffle same-second entries
  // and typewriter-play the wrong one as "latest".
  const p = paths(sessionId);
  const liveAll = readJsonl<{
    seat: number; name: string; short: string; text: string; ts: string; chair?: string; err?: boolean;
  }>(join(p.root, "room-turns.jsonl"));
  // err-tagged turns are riff-live's synthetic failure notices — diagnostics,
  // not something a seat said. They never enter the spoken record (CONTRACT-8),
  // and turns_total counts only what remains so the page's detector agrees.
  const liveTurns = liveAll.filter((t) => !t.err);
  const timeline = (liveTurns.length
    ? liveTurns.map((t) => ({
        type: "turn",
        seat: t.seat,
        name: t.name,
        short: t.short,
        text: t.text,
        ...(t.chair ? { chair: t.chair } : {}),
        reactions: {} as Record<string, string>,
        hands: [] as number[],
      }))
    : [...s.ledger].reverse().map((e) => ({
        // s.ledger is newest-first; reversing restores append order.
        type: "note",
        seat: 0,
        name: "Session log",
        short: "Session log",
        text: e.body,
        fallback: true,
        reactions: {} as Record<string, string>,
        hands: [] as number[],
      }))
  ).slice(-100); // capped per push — the page keys on turns_total, not length (I42)

  // The seat the live responder is generating for (instant "thinking" feedback),
  // and the reading-level dial, both written by riff-live.
  let thinking: { seat: number } | undefined;
  try {
    const th = JSON.parse(readFileSync(join(p.root, "room-thinking.json"), "utf8"));
    // riff-live stamps ts on every marker; trust it only while fresh (well
    // above the ~5-7s generation time). A dead daemon or stalled worker must
    // not leave a seat pulsing "gathering their point" forever — a missing or
    // unparseable ts fails toward NOT thinking.
    if (th && typeof th.seat === "number" && Date.now() - Date.parse(th.ts) < 120_000) {
      thinking = { seat: th.seat };
    }
  } catch {
    /* none */
  }
  let reading_level = 0;
  try {
    // Math.round: the chair-cmd whitelist admits any finite number, and a
    // fractional dial value would miss integer-keyed level lookups downstream.
    reading_level = Math.max(0, Math.min(5, Math.round(Number(JSON.parse(readFileSync(join(p.root, "room-level.json"), "utf8")).level)) || 0));
  } catch {
    /* default 0 */
  }

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
      // Research phrasing for the page's close line: a riff session closes on
      // the record via the gate and the compiled report, not a committee vote.
      close_note:
        "Close requested — a live research session closes on the record when the coverage gate and the compiled report land in the ledger (riff report compile), not from this page.",
    },
    // Coverage counts in gate language: the page's AGAINST/FOR defaults are
    // committee-vote words and must never describe dimension coverage (M12).
    vote: {
      for: covered,
      against: blocking,
      label_a: "BLOCKING",
      label_f: "COVERED",
      note: s.gate.reason,
    },
    seats,
    briefing,
    timeline,
    turns_total: liveTurns.length,
    research_label: "findings",
    phase: s.phase,
    reading_level,
    ...(thinking ? { thinking } : {}),
    errors: s.errors,
  };
}
