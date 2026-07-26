/**
 * The claim corpus: what the panel actually found, and how the live riff answers
 * from it.
 *
 * Every claim carries provenance (source + as_of date) because embeddings and
 * text alike are time-blind — without a stamp the Q&A layer cannot down-weight
 * or refuse a stale answer (design invariant I1).
 *
 * The retrieval here is dependency-free lexical cosine similarity. It is a
 * deliberate floor, not a ceiling: the optional LanceDB index under
 * .claude/scripts/rag/ can replace `search()` without changing callers.
 */

import { existsSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { appendJsonl, readJsonl, similarity, termFreq, cosine, today } from "./util.ts";
import { paths } from "./session.ts";
import type { Confidence, Provenance } from "./ledger.ts";

export interface Claim {
  id: string;
  claim: string;
  dimension?: string;
  question?: string;
  sources: Provenance[];
  tier?: 1 | 2 | 3 | 4;
  as_of: string;
  agent: string;
  model?: string;
  volatile?: boolean;
}

export interface ScoredClaim extends Claim {
  score: number;
  slug: string;
}

export function dossierFiles(sessionId: string): Array<{ slug: string; path: string }> {
  const dir = paths(sessionId).dossiers;
  if (!existsSync(dir)) return [];
  return readdirSync(dir)
    .filter((f) => f.endsWith(".claims.jsonl"))
    .map((f) => ({ slug: f.replace(/\.claims\.jsonl$/, ""), path: join(dir, f) }));
}

/**
 * The corpus: every claim that has been through ingest.
 *
 * Agents write their claims files themselves, so a file can exist on disk before
 * `riff claims ingest` has seen it. Those raw claims have no id yet — they have
 * not been deduped against the rest of the corpus and nothing can cite them. If
 * they were readable here they would surface in answers as hits with no
 * identifier, which breaks citation, surfaced-tracking and the report bundle.
 * So the corpus is defined as claims carrying an id, and un-ingested files are
 * reported separately rather than silently mixed in.
 */
export function allClaims(sessionId: string): Array<Claim & { slug: string }> {
  const out: Array<Claim & { slug: string }> = [];
  for (const { slug, path } of dossierFiles(sessionId)) {
    for (const c of readJsonl<Claim>(path)) {
      if (typeof c.id === "string" && c.id) out.push({ ...c, slug });
    }
  }
  return out;
}

/** Dossier files written by an agent but not yet run through ingest. */
export function pendingIngest(sessionId: string): Array<{ slug: string; claims: number }> {
  const out: Array<{ slug: string; claims: number }> = [];
  for (const { slug, path } of dossierFiles(sessionId)) {
    const raw = readJsonl<Claim>(path);
    const unided = raw.filter((c) => !c.id).length;
    if (unided > 0) out.push({ slug, claims: unided });
  }
  return out;
}

/** Canonical key for dedup — parallel agents find the same thing under different names. */
export function canonicalKey(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9 ]+/g, " ")
    .split(/\s+/)
    .filter(Boolean)
    .sort()
    .slice(0, 12)
    .join(" ");
}

export interface AddResult {
  added: Claim[];
  duplicates: Array<{ claim: string; duplicate_of: string }>;
}

/**
 * Append claims for one dossier, dropping near-duplicates of anything already in
 * the corpus. Returns what was novel — the caller feeds that count straight into
 * the coverage saturation counter.
 */
export function addClaims(
  sessionId: string,
  slug: string,
  incoming: Array<Partial<Claim>>,
  opts: { dupThreshold?: number } = {},
): AddResult {
  const threshold = opts.dupThreshold ?? 0.82;
  const existing = allClaims(sessionId);
  const existingKeys = new Map(existing.map((c) => [canonicalKey(c.claim), c.id]));
  const existingVecs = existing.map((c) => ({ id: c.id, vec: termFreq(c.claim) }));
  const path = join(paths(sessionId).dossiers, `${slug}.claims.jsonl`);

  const added: Claim[] = [];
  const duplicates: Array<{ claim: string; duplicate_of: string }> = [];
  let seq = existing.filter((c) => c.slug === slug).length;

  for (const raw of incoming) {
    const text = (raw.claim ?? "").trim();
    if (!text) continue;
    const key = canonicalKey(text);
    const exactDup = existingKeys.get(key);
    if (exactDup) {
      duplicates.push({ claim: text, duplicate_of: exactDup });
      continue;
    }
    const vec = termFreq(text);
    const near = existingVecs.find((e) => cosine(e.vec, vec) >= threshold);
    if (near) {
      duplicates.push({ claim: text, duplicate_of: near.id });
      continue;
    }
    seq += 1;
    const claim: Claim = {
      id: raw.id ?? `${slug}-${String(seq).padStart(3, "0")}`,
      claim: text,
      ...(raw.dimension ? { dimension: raw.dimension } : {}),
      ...(raw.question ? { question: raw.question } : {}),
      sources: raw.sources ?? [],
      ...(raw.tier ? { tier: raw.tier } : {}),
      as_of: raw.as_of ?? today(),
      agent: raw.agent ?? slug,
      ...(raw.model ? { model: raw.model } : {}),
      ...(raw.volatile ? { volatile: true } : {}),
    };
    appendJsonl(path, claim);
    added.push(claim);
    existingKeys.set(key, claim.id);
    existingVecs.push({ id: claim.id, vec });
  }
  return { added, duplicates };
}

/**
 * Ingest the claims file a research agent wrote in place.
 *
 * Agents write `dossiers/<slug>.claims.jsonl` themselves — that is the charter's
 * contract and it keeps their output out of the orchestrator's context. So
 * ingest reads that file where it lies, drops claims that duplicate other
 * dossiers or repeat within the file, assigns ids, and rewrites it canonically.
 *
 * Dedup deliberately excludes the slug's own prior contents, otherwise every
 * claim would be found to duplicate itself.
 */
export function ingestFile(
  sessionId: string,
  slug: string,
  opts: { dupThreshold?: number } = {},
): AddResult & { malformed: number; total_read: number } {
  const threshold = opts.dupThreshold ?? 0.82;
  const path = join(paths(sessionId).dossiers, `${slug}.claims.jsonl`);
  if (!existsSync(path)) {
    throw new Error(`no claims file at ${path} — did the agent write it?`);
  }
  const rawLines = readFileSync(path, "utf8")
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean);
  let malformed = 0;
  const incoming: Array<Partial<Claim>> = [];
  for (const line of rawLines) {
    try {
      const v = JSON.parse(line) as Partial<Claim>;
      if (v && typeof v.claim === "string" && v.claim.trim()) incoming.push(v);
      else malformed++;
    } catch {
      malformed++;
    }
  }

  const others = allClaims(sessionId).filter((c) => c.slug !== slug);
  const keys = new Map(others.map((c) => [canonicalKey(c.claim), c.id]));
  const vecs = others.map((c) => ({ id: c.id, vec: termFreq(c.claim) }));

  const added: Claim[] = [];
  const duplicates: Array<{ claim: string; duplicate_of: string }> = [];
  let seq = 0;
  for (const raw of incoming) {
    const text = (raw.claim ?? "").trim();
    const key = canonicalKey(text);
    const exact = keys.get(key);
    if (exact) {
      duplicates.push({ claim: text, duplicate_of: exact });
      continue;
    }
    const vec = termFreq(text);
    const near = vecs.find((e) => cosine(e.vec, vec) >= threshold);
    if (near) {
      duplicates.push({ claim: text, duplicate_of: near.id });
      continue;
    }
    seq += 1;
    const claim: Claim = {
      id: raw.id ?? `${slug}-${String(seq).padStart(3, "0")}`,
      claim: text,
      ...(raw.dimension ? { dimension: raw.dimension } : {}),
      ...(raw.question ? { question: raw.question } : {}),
      sources: raw.sources ?? [],
      ...(raw.tier ? { tier: raw.tier } : {}),
      as_of: raw.as_of ?? today(),
      agent: raw.agent ?? slug,
      ...(raw.model ? { model: raw.model } : {}),
      ...(raw.volatile ? { volatile: true } : {}),
    };
    added.push(claim);
    keys.set(key, claim.id);
    vecs.push({ id: claim.id, vec });
  }

  writeFileSync(path, added.map((c) => JSON.stringify(c)).join("\n") + (added.length ? "\n" : ""), "utf8");
  return { added, duplicates, malformed, total_read: rawLines.length };
}

export function search(sessionId: string, query: string, limit = 8): ScoredClaim[] {
  const qv = termFreq(query);
  return allClaims(sessionId)
    .map((c) => ({
      ...c,
      score: cosine(qv, termFreq(`${c.claim} ${c.question ?? ""} ${c.dimension ?? ""}`)),
    }))
    .filter((c) => c.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, limit);
}

export interface Sufficiency {
  label: Confidence;
  reason: string;
  hits: ScoredClaim[];
  independent_sources: number;
  stale: boolean;
  volatile: boolean;
  /** The answering claim states a measurement (latency, price, size, throughput…). */
  numeric: boolean;
  /** At least one answering source is Tier 1-2 (a primary/authoritative source). */
  primary_sourced: boolean;
}

/**
 * Does this claim state a measurement — a latency, price, size, throughput,
 * parameter count, or percentage? Those are the claims that must rest on a
 * primary source, because a figure lifted from a blog or from memory is exactly
 * how "ElevenLabs ~264ms" got stated as fact when the vendor's own number was
 * ~75ms model / ~100-200ms. Deliberately narrow: it targets figures-with-units,
 * not incidental numbers like "3 seats" or a version string.
 */
export const MEASUREMENT_RE =
  /(\$\s?\d)|(\b\d[\d.,]*\s?(ms|milliseconds?|secs?|seconds?|tokens?\/s|tok\/s|gb|mb|tb|gib|mib|kb|%|×|x\b|hz|khz|ghz|b\b|billion|million|k\b|usd|eur|gbp|cents?|params?|fps|rps|qps)\b)/i;

export function looksNumeric(text: string): boolean {
  return MEASUREMENT_RE.test(text);
}

/**
 * The CRAG-shaped sufficiency check that routes the live riff:
 *   verified       -> answer from corpus, cite it
 *   provisional    -> answer, but say so and offer to deepen
 *   not-in-corpus  -> ABSTAIN and dispatch a probe (design invariant I2)
 *
 * Labels are categorical on purpose. Numeric confidence scores are known to be
 * unreliable in retrieval-augmented settings, so evidence state is reported
 * directly rather than dressed up as a probability.
 */
export function assess(
  sessionId: string,
  query: string,
  opts: { minScore?: number; strongScore?: number; staleDays?: number } = {},
): Sufficiency {
  const minScore = opts.minScore ?? 0.12;
  const strongScore = opts.strongScore ?? 0.25;
  const staleDays = opts.staleDays ?? 45;
  const hits = search(sessionId, query, 8).filter((h) => h.score >= minScore);
  if (hits.length === 0) {
    return {
      label: "not-in-corpus",
      reason: "no dossier claim matches this question",
      hits: [],
      independent_sources: 0,
      stale: false,
      volatile: false,
      numeric: false,
      primary_sourced: false,
    };
  }
  // A corpus that genuinely covers a topic produces at least one strong match.
  // Weak overlap on generic shared words is how an off-topic question gets
  // answered "provisionally" from evidence that is not about it at all — a
  // quieter version of improvising, and the thing invariant I2 forbids. The
  // cost of abstaining wrongly is one probe; the cost of answering wrongly is a
  // confident wrong answer, so the bias goes to abstention.
  const top = hits[0]!.score;
  if (top < strongScore) {
    return {
      label: "not-in-corpus",
      reason: `only weak overlap (best match ${top.toFixed(
        2,
      )} < ${strongScore}) — the corpus does not actually address this`,
      hits,
      independent_sources: 0,
      stale: false,
      volatile: false,
      numeric: false,
      primary_sourced: false,
    };
  }
  const urls = new Set<string>();
  for (const h of hits) {
    for (const s of h.sources) urls.add(s.url ?? s.source);
  }
  const agents = new Set(hits.map((h) => h.slug));
  const independent = Math.max(urls.size, agents.size > 1 ? agents.size : 1);
  const cutoff = Date.now() - staleDays * 86400_000;
  const stale = hits.some((h) => Date.parse(h.as_of) < cutoff);
  const volatile = hits.some((h) => h.volatile);
  // A measurement is only as trustworthy as its most authoritative source. If
  // the answering claim states a figure, at least one hit must carry a Tier 1-2
  // (primary/authoritative) source, or the figure cannot read "verified" — it is
  // a number nobody checked against the thing it describes.
  // Judge the ANSWERING claim (the top hit), not the whole result set: a
  // different vendor's primary source lower in the hits must not launder a
  // blog-only figure at the top into looking primary-sourced.
  const numeric = looksNumeric(hits[0]!.claim);
  const primary_sourced = hits[0]!.sources.some((s) => (s.tier ?? 9) <= 2);
  if (numeric && !primary_sourced) {
    return {
      label: "provisional",
      reason:
        "states a figure with no Tier 1-2 source — verify against the vendor's own page or docs before relying on it",
      hits,
      independent_sources: independent,
      stale,
      volatile,
      numeric,
      primary_sourced,
    };
  }
  if (independent >= 2 && urls.size >= 2) {
    return {
      label: "verified",
      reason: `${independent} independent sources across ${agents.size} dossier(s)`,
      hits,
      independent_sources: independent,
      stale,
      volatile,
      numeric,
      primary_sourced,
    };
  }
  return {
    label: "provisional",
    reason:
      urls.size <= 1
        ? "single source — corroboration missing"
        : "matched, but sources are not clearly independent",
    hits,
    independent_sources: independent,
    stale,
    volatile,
    numeric,
    primary_sourced,
  };
}

// ---------------------------------------------------------------------------
// Moderator: surface what the user never asked about
// ---------------------------------------------------------------------------

export function surfacedIds(sessionId: string): Set<string> {
  return new Set(
    readJsonl<{ claim_id: string }>(paths(sessionId).surfaced).map((r) => r.claim_id),
  );
}

export function markSurfaced(sessionId: string, ids: string[]): void {
  for (const id of ids) {
    appendJsonl(paths(sessionId).surfaced, { claim_id: id, ts: new Date().toISOString() });
  }
}

export function recentQuestions(sessionId: string, n = 3): string[] {
  return readJsonl<{ text: string }>(paths(sessionId).questions)
    .slice(-n)
    .map((q) => q.text);
}

export function recordQuestion(sessionId: string, text: string): void {
  appendJsonl(paths(sessionId).questions, { text, ts: new Date().toISOString() });
}

/**
 * Pick the most worthwhile thing the user has NOT been shown.
 *
 * Score = relevance to the brief, weighted against similarity to what has just
 * been asked. High-relevance / low-overlap material is exactly the "you didn't
 * ask, but…" find — the conversation-time cure for research that never reaches
 * the reader. Alpha mirrors the published 0.5 balance.
 */
export function moderatorPick(
  sessionId: string,
  brief: string,
  alpha = 0.5,
): ScoredClaim | null {
  const seen = surfacedIds(sessionId);
  const recent = recentQuestions(sessionId, 3).join(" ");
  const bv = termFreq(brief);
  const rv = termFreq(recent);
  const candidates = allClaims(sessionId)
    .filter((c) => !seen.has(c.id))
    .map((c) => {
      const cv = termFreq(`${c.claim} ${c.question ?? ""}`);
      const rel = cosine(bv, cv);
      const dissim = 1 - cosine(rv, cv);
      return { ...c, score: Math.pow(rel, alpha) * Math.pow(dissim, 1 - alpha) };
    })
    .filter((c) => c.score > 0)
    .sort((a, b) => b.score - a.score);
  return candidates[0] ?? null;
}

export function corpusStats(sessionId: string): Record<string, number> {
  const claims = allClaims(sessionId);
  const seen = surfacedIds(sessionId);
  const urls = new Set<string>();
  for (const c of claims) for (const s of c.sources) urls.add(s.url ?? s.source);
  const pending = pendingIngest(sessionId);
  return {
    claims: claims.length,
    dossiers: dossierFiles(sessionId).length,
    unique_sources: urls.size,
    surfaced: claims.filter((c) => seen.has(c.id)).length,
    unsurfaced: claims.filter((c) => !seen.has(c.id)).length,
    pending_ingest: pending.reduce((n, p) => n + p.claims, 0),
    pending_dossiers: pending.length,
  };
}

export { similarity };
