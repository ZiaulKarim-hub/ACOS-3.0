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

import { existsSync, readdirSync, readFileSync, renameSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import {
  appendJsonl,
  nowIso,
  readJsonl,
  readJsonlStrict,
  similarity,
  termFreq,
  cosine,
  today,
} from "./util.ts";
import { paths } from "./session.ts";
import type { Confidence, Provenance } from "./ledger.ts";

export interface Claim {
  id: string;
  claim: string;
  dimension?: string;
  question?: string;
  sources: Provenance[];
  /** Best (lowest) tier across sources, stamped at ingest so display readers
   *  and the source-tier trust gates agree; the gates also honor it as a
   *  fallback when a source carries no tier of its own. */
  tier?: 1 | 2 | 3 | 4;
  as_of: string;
  /** Source publication date (ISO), when the researcher captured one. as_of is
   *  the date OF the information; published is when the source said it. The
   *  newer of the two drives the recency label (CONTRACT-7). */
  published?: string;
  agent: string;
  model?: string;
  volatile?: boolean;
  /** Ids this claim is in recorded disagreement with — stamped when a
   *  near-duplicate was KEPT because its figures or negation parity differ. A
   *  recorded disputant never corroborates this claim (M1), and the pair is
   *  preserved until reconciled, never silently harmonized. */
  conflicts_with?: string[];
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
 * So the corpus is defined as claims carrying an id in the dossier's own
 * namespace (`<slug>-NNN`) — ids are assigned by ingest, so an agent-invented
 * foreign id cannot spoof its way in or collide with another dossier's
 * citations. Un-ingested files are reported separately, not silently mixed in.
 */
export function allClaims(sessionId: string): Array<Claim & { slug: string }> {
  const out: Array<Claim & { slug: string }> = [];
  for (const { slug, path } of dossierFiles(sessionId)) {
    for (const c of readJsonl<Claim>(path)) {
      if (typeof c.id === "string" && c.id.startsWith(`${slug}-`)) out.push({ ...c, slug });
    }
  }
  return out;
}

/** Dossier files written by an agent but not yet run through ingest. */
export function pendingIngest(
  sessionId: string,
): Array<{ slug: string; claims: number; malformed_lines?: number }> {
  const out: Array<{ slug: string; claims: number; malformed_lines?: number }> = [];
  for (const { slug, path } of dossierFiles(sessionId)) {
    // Strict read: a dossier whose every line is unparseable (pretty-printed
    // array, prose) must show up as pending/damaged here, not report 0 pending
    // and vanish from the safety net entirely (I22).
    const { rows: raw, dropped } = readJsonlStrict<Claim>(path);
    // A claim outside the slug's id namespace is still un-ingested — ingest
    // will reassign its id — so it counts as pending rather than vanishing
    // from both the corpus and this safety net.
    const unided = raw.filter(
      (c) => !(typeof c.id === "string" && c.id.startsWith(`${slug}-`)),
    ).length;
    if (unided > 0 || dropped.length > 0)
      out.push({
        slug,
        claims: unided,
        ...(dropped.length > 0 ? { malformed_lines: dropped.length } : {}),
      });
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
  duplicates: Array<{ claim: string; duplicate_of: string; sources_merged?: number }>;
  /** Kept despite near-duplicate wording: the figures or the negation parity
   *  differ, so this is the corpus disagreeing with itself — a conflict to
   *  reconcile (usually via a ledger correction), never something to drop
   *  silently. */
  conflicts: Array<{ id: string; conflicts_with: string; claim: string }>;
}

/**
 * Numeric tokens of a claim text ("$99" -> "99", "1.2s" -> "1.2", "1,200" ->
 * "1200"), in the ORDER they appear. Extracted directly rather than via
 * tokenize(), which drops single-character digit runs — a blindness that let
 * "$9" vs "$5" (and, with longer claims, any one differing figure) score as
 * cosine near-duplicates.
 */
export function numericTokens(text: string): string[] {
  const out: string[] = [];
  for (const m of text.matchAll(/\d[\d.,]*/g)) {
    out.push(m[0].replace(/[.,]+$/, "").replace(/,/g, ""));
  }
  return out;
}

/**
 * Ordered figure comparison (M16): "improved from 264ms to 75ms" and its
 * reversal carry the same number SET but state opposite facts, so the
 * sequences are compared element-wise — order and multiplicity both count,
 * never membership alone.
 */
function sameNumbers(a: string, b: string): boolean {
  const na = numericTokens(a);
  const nb = numericTokens(b);
  return na.length === nb.length && na.every((t, i) => t === nb[i]);
}

/**
 * Negation parity, taken on the RAW text (M2): tokenize() treats not/no as
 * stopwords, so "does not offer X" and "does offer X" are cosine-identical.
 * Differing parity between near-duplicates means one claim REFUTES the other —
 * that is a conflict to keep, never a duplicate to merge, because a merge
 * would hand the refuting source to the very claim it refutes.
 */
const NEGATION_RE = /\b(?:not|no|never|cannot|without)\b|n't\b/g;
function negationParity(text: string): number {
  return (text.toLowerCase().match(NEGATION_RE) ?? []).length % 2;
}

function sameNegation(a: string, b: string): boolean {
  return negationParity(a) === negationParity(b);
}

/**
 * The one tier normalizer (M17): agents routinely emit tiers as JSON strings
 * ("1") or out-of-range numbers, and loose comparison let those pass the
 * primary-source gate while the strict stamp ignored the same value. Coerce
 * numeric strings, clamp to 1-4, everything else is undefined — and every
 * tier reader in this file (the claim-level stamp and the trust gate alike)
 * goes through here, so the two can never disagree on one dossier line.
 */
export function normalizeTier(t: unknown): 1 | 2 | 3 | 4 | undefined {
  const n = typeof t === "number" ? t : typeof t === "string" && t.trim() !== "" ? Number(t) : NaN;
  if (!Number.isFinite(n)) return undefined;
  return Math.min(4, Math.max(1, Math.round(n))) as 1 | 2 | 3 | 4;
}

/** Normalize the tier on each source as it crosses the ingest boundary. */
function normalizeSources(sources: Provenance[] | undefined): Provenance[] {
  return (sources ?? []).map((s) => {
    const norm: Provenance = { ...s };
    const t = normalizeTier(s.tier);
    if (t) norm.tier = t;
    else delete norm.tier;
    return norm;
  });
}

/** Union extra provenance into a claim (dedup by url), normalizing tiers as
 *  they land. Returns sources gained. */
function unionSources(target: Claim, extra: Provenance[] | undefined): number {
  if (!extra?.length) return 0;
  const have = new Set((target.sources ?? []).map((s) => s.url ?? s.source));
  let gained = 0;
  for (const s of normalizeSources(extra)) {
    const k = s.url ?? s.source;
    if (have.has(k)) continue;
    have.add(k);
    target.sources = [...(target.sources ?? []), s];
    gained += 1;
  }
  return gained;
}

/**
 * Rewrite a dossier file atomically (tmp + rename) so a crash mid-write can
 * never truncate it (I6). A concurrent agent append landing between the read
 * and the rename can still be lost — that residual race is accepted; silent
 * truncation of the whole file is not.
 */
function writeDossierAtomic(path: string, content: string): void {
  const tmp = `${path}.tmp-${process.pid}`;
  writeFileSync(tmp, content, "utf8");
  renameSync(tmp, path);
}

/**
 * A dropped duplicate's provenance is real corroboration: merge it into the
 * surviving claim's dossier line so a later Tier 1-2 find can upgrade a
 * blog-first figure and same-fact corroboration accumulates on one claim
 * instead of being discarded with the duplicate text (invariant I9).
 *
 * The survivor's dossier is derived from its id (`<slug>-NNN`) and ONLY that
 * file is opened — a copied id inside some other agent's un-ingested file must
 * never receive the merge (the id-namespace discipline the read path already
 * has, applied to this write path; I7). Rewrites only the one matching line,
 * atomically; all other lines are left byte-for-byte.
 */
function mergeSourcesOnDisk(
  sessionId: string,
  claimId: string,
  extra: Provenance[] | undefined,
): number {
  if (!extra?.length) return 0;
  const slug = claimId.replace(/-\d+$/, "");
  if (slug === claimId) return 0; // not a `<slug>-NNN` id — no dossier owns it
  const path = join(paths(sessionId).dossiers, `${slug}.claims.jsonl`);
  if (!existsSync(path)) return 0;
  const lines = readFileSync(path, "utf8").split("\n");
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]!.trim();
    if (!line) continue;
    let c: Claim;
    try {
      c = JSON.parse(line) as Claim;
    } catch {
      continue;
    }
    if (c.id !== claimId) continue;
    const gained = unionSources(c, extra);
    if (gained > 0) {
      // Restamp so a merged Tier 1-2 source upgrades the claim-level tier —
      // the two tier fields must never disagree, least of all on the upgrade
      // path the merge feature was built for (I19).
      const bt = bestSourceTier(c.sources);
      if (bt) c.tier = bt;
      lines[i] = JSON.stringify(c);
      writeDossierAtomic(path, lines.join("\n"));
    }
    return gained;
  }
  return 0;
}

/** Best (lowest) tier carried by a claim's sources, or undefined. Normalized
 *  per source so the stamp and the gate read the same value (M17). */
function bestSourceTier(sources: Provenance[] | undefined): 1 | 2 | 3 | 4 | undefined {
  const tiers = (sources ?? [])
    .map((s) => normalizeTier(s.tier))
    .filter((t): t is 1 | 2 | 3 | 4 => t !== undefined);
  return tiers.length > 0 ? (Math.min(...tiers) as 1 | 2 | 3 | 4) : undefined;
}

/** Escape a slug for use inside a RegExp (slugs are model-authored). */
function escapeRegExp(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/**
 * Append claims for one dossier, dropping near-duplicates of anything already in
 * the corpus. Returns what was novel — the caller feeds that count straight into
 * the coverage saturation counter. A near-duplicate whose FIGURES differ (in
 * ordered sequence) or whose NEGATION PARITY differs is not a duplicate: it is
 * kept, stamped with `conflicts_with`, and reported in `conflicts`; a dropped
 * duplicate's sources are merged into the surviving claim.
 */
export function addClaims(
  sessionId: string,
  slug: string,
  incoming: Array<Partial<Claim>>,
  opts: { dupThreshold?: number } = {},
): AddResult {
  const threshold = opts.dupThreshold ?? 0.82;
  const existing = allClaims(sessionId);
  const existingKeys = new Map(
    existing.map((c) => [canonicalKey(c.claim), { id: c.id, text: c.claim }]),
  );
  const existingVecs = existing.map((c) => ({ id: c.id, text: c.claim, vec: termFreq(c.claim) }));
  const usedIds = new Set(existing.map((c) => c.id));
  const path = join(paths(sessionId).dossiers, `${slug}.claims.jsonl`);
  // Full id shape `<slug>-NNN` (I21): bare startsWith let `cost-model-001`
  // pass for slug `cost`, and non-numeric suffixes escaped the audit's
  // slug-\d+ token shape while still entering the corpus.
  const idShape = new RegExp(`^${escapeRegExp(slug)}-\\d{3,}$`);

  const added: Claim[] = [];
  const duplicates: AddResult["duplicates"] = [];
  const conflicts: AddResult["conflicts"] = [];
  let seq = existing.filter((c) => c.slug === slug).length;

  for (const raw of incoming) {
    const text = (raw.claim ?? "").trim();
    if (!text) continue;
    // The exact-dup key keeps digit tokens, so DIFFERING figures never collide
    // here — but the key sorts its tokens, so a figure-SWAPPED rewording (and
    // sometimes a negation) lands on the same key. A key hit is only a
    // duplicate when the ordered figures and negation parity also agree;
    // anything else falls through to the conflict logic below (M16/M2).
    const key = canonicalKey(text);
    const exactDup = existingKeys.get(key);
    if (exactDup && sameNumbers(text, exactDup.text) && sameNegation(text, exactDup.text)) {
      const merged = mergeSourcesOnDisk(sessionId, exactDup.id, raw.sources);
      duplicates.push({
        claim: text,
        duplicate_of: exactDup.id,
        ...(merged > 0 ? { sources_merged: merged } : {}),
      });
      continue;
    }
    const vec = termFreq(text);
    // Rank ALL above-threshold candidates best-first (M15): a same-figure,
    // same-parity match anywhere in the corpus is the claim to merge into —
    // first-match .find() let an existing conflict pair block the correction
    // probe from ever corroborating the claim it confirms. Only when NO such
    // candidate exists is this a conflict, flagged against the closest match.
    const cands = existingVecs
      .map((e) => ({ e, score: cosine(e.vec, vec) }))
      .filter((c) => c.score >= threshold)
      .sort((x, y) => y.score - x.score);
    const dup = cands.find((c) => sameNumbers(text, c.e.text) && sameNegation(text, c.e.text))?.e;
    // A cosine near-match stating the SAME thing is a duplicate. With
    // different figures — or opposite negation parity — it is the corpus
    // disagreeing with itself, and dropping it would let the first-stated
    // claim win forever: a wrong "$99" surviving its "$49" correction, or a
    // refuted claim absorbing its refutation's source. Keep and flag instead.
    if (dup) {
      const merged = mergeSourcesOnDisk(sessionId, dup.id, raw.sources);
      duplicates.push({
        claim: text,
        duplicate_of: dup.id,
        ...(merged > 0 ? { sources_merged: merged } : {}),
      });
      continue;
    }
    const conflictWith = cands[0]?.e;
    // Accept an agent-supplied id only in this slug's own namespace and only
    // if unused — anything else gets reassigned so ids stay collision-free.
    let id = typeof raw.id === "string" && idShape.test(raw.id) && !usedIds.has(raw.id) ? raw.id : "";
    while (!id || usedIds.has(id)) {
      seq += 1;
      id = `${slug}-${String(seq).padStart(3, "0")}`;
    }
    usedIds.add(id);
    // Claim-level tier is stamped from the best source tier so the two tier
    // fields never disagree: display consumers read claim.tier, the trust
    // gates read source tiers. Both run through normalizeTier (M17).
    const srcs = normalizeSources(raw.sources);
    const tier = bestSourceTier(srcs) ?? normalizeTier(raw.tier);
    const claim: Claim = {
      id,
      claim: text,
      ...(raw.dimension ? { dimension: raw.dimension } : {}),
      ...(raw.question ? { question: raw.question } : {}),
      sources: srcs,
      ...(tier ? { tier } : {}),
      as_of: raw.as_of ?? today(),
      ...(typeof raw.published === "string" && raw.published ? { published: raw.published } : {}),
      agent: raw.agent ?? slug,
      ...(raw.model ? { model: raw.model } : {}),
      ...(raw.volatile ? { volatile: true } : {}),
      ...(conflictWith ? { conflicts_with: [conflictWith.id] } : {}),
    };
    appendJsonl(path, claim);
    added.push(claim);
    if (conflictWith) conflicts.push({ id: claim.id, conflicts_with: conflictWith.id, claim: text });
    existingKeys.set(key, { id: claim.id, text });
    existingVecs.push({ id: claim.id, text, vec });
  }
  return { added, duplicates, conflicts };
}

/**
 * Ingest the claims file a research agent wrote in place.
 *
 * Agents write `dossiers/<slug>.claims.jsonl` themselves — that is the charter's
 * contract and it keeps their output out of the orchestrator's context. So
 * ingest reads that file where it lies, drops claims that duplicate other
 * dossiers or repeat within the file, assigns ids, and rewrites it canonically.
 * A near-duplicate whose figures or negation parity differ is kept and
 * reported in `conflicts` (see addClaims), a dropped duplicate's sources are
 * merged into the surviving claim, and malformed lines are preserved in a
 * `<slug>.claims.rejected.jsonl` sidecar before the rewrite discards them.
 *
 * Dedup deliberately excludes the slug's own prior contents, otherwise every
 * claim would be found to duplicate itself.
 */
export function ingestFile(
  sessionId: string,
  slug: string,
  opts: { dupThreshold?: number } = {},
): AddResult & { malformed: number; total_read: number; rejected_sidecar?: string } {
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
  const malformedLines: string[] = [];
  const incoming: Array<Partial<Claim>> = [];
  for (const line of rawLines) {
    try {
      const v = JSON.parse(line) as Partial<Claim>;
      if (v && typeof v.claim === "string" && v.claim.trim()) incoming.push(v);
      else {
        malformed++;
        malformedLines.push(line);
      }
    } catch {
      malformed++;
      malformedLines.push(line);
    }
  }

  const others = allClaims(sessionId).filter((c) => c.slug !== slug);
  const keys = new Map(others.map((c) => [canonicalKey(c.claim), { id: c.id, text: c.claim }]));
  const vecs = others.map((c) => ({ id: c.id, text: c.claim, vec: termFreq(c.claim) }));
  // Own-slug ids are excluded: this file is rebuilt from scratch, so re-ingest
  // must be able to keep the ids it assigned last time.
  const usedIds = new Set(others.map((c) => c.id));
  // Full id shape `<slug>-NNN`, same rule as addClaims (I21).
  const idShape = new RegExp(`^${escapeRegExp(slug)}-\\d{3,}$`);

  const added: Claim[] = [];
  const duplicates: AddResult["duplicates"] = [];
  const conflicts: AddResult["conflicts"] = [];
  let seq = 0;
  for (const raw of incoming) {
    const text = (raw.claim ?? "").trim();
    const key = canonicalKey(text);
    const exact = keys.get(key);
    // The survivor may be in this batch (not yet written) or on disk in
    // another dossier — merge the dropped duplicate's sources either way, and
    // restamp the in-batch survivor's tier so a merged Tier 1-2 source
    // upgrades it (I19; mergeSourcesOnDisk restamps the on-disk case).
    const mergeInto = (dupId: string): number => {
      const survivor = added.find((c) => c.id === dupId);
      if (!survivor) return mergeSourcesOnDisk(sessionId, dupId, raw.sources);
      const gained = unionSources(survivor, raw.sources);
      if (gained > 0) {
        const bt = bestSourceTier(survivor.sources);
        if (bt) survivor.tier = bt;
      }
      return gained;
    };
    // Key hits are only duplicates when ordered figures and negation parity
    // agree — the sorted key collides on figure swaps and some negations
    // (M16/M2; same rule as addClaims).
    if (exact && sameNumbers(text, exact.text) && sameNegation(text, exact.text)) {
      const merged = mergeInto(exact.id);
      duplicates.push({
        claim: text,
        duplicate_of: exact.id,
        ...(merged > 0 ? { sources_merged: merged } : {}),
      });
      continue;
    }
    const vec = termFreq(text);
    // Best-match dedup over ALL above-threshold candidates, then the
    // figure/negation conflict guard — same rules as addClaims (M15/M16/M2).
    const cands = vecs
      .map((e) => ({ e, score: cosine(e.vec, vec) }))
      .filter((c) => c.score >= threshold)
      .sort((x, y) => y.score - x.score);
    const dup = cands.find((c) => sameNumbers(text, c.e.text) && sameNegation(text, c.e.text))?.e;
    if (dup) {
      const merged = mergeInto(dup.id);
      duplicates.push({
        claim: text,
        duplicate_of: dup.id,
        ...(merged > 0 ? { sources_merged: merged } : {}),
      });
      continue;
    }
    const conflictWith = cands[0]?.e;
    // Accept an agent-supplied id only in this slug's own namespace and only
    // if unused — anything else gets reassigned so ids stay collision-free.
    let id = typeof raw.id === "string" && idShape.test(raw.id) && !usedIds.has(raw.id) ? raw.id : "";
    while (!id || usedIds.has(id)) {
      seq += 1;
      id = `${slug}-${String(seq).padStart(3, "0")}`;
    }
    usedIds.add(id);
    // Claim-level tier is stamped from the best source tier so the two tier
    // fields never disagree (same normalizeTier rule as addClaims; M17).
    const srcs = normalizeSources(raw.sources);
    const tier = bestSourceTier(srcs) ?? normalizeTier(raw.tier);
    const claim: Claim = {
      id,
      claim: text,
      ...(raw.dimension ? { dimension: raw.dimension } : {}),
      ...(raw.question ? { question: raw.question } : {}),
      sources: srcs,
      ...(tier ? { tier } : {}),
      as_of: raw.as_of ?? today(),
      ...(typeof raw.published === "string" && raw.published ? { published: raw.published } : {}),
      agent: raw.agent ?? slug,
      ...(raw.model ? { model: raw.model } : {}),
      ...(raw.volatile ? { volatile: true } : {}),
      ...(conflictWith ? { conflicts_with: [conflictWith.id] } : {}),
    };
    added.push(claim);
    if (conflictWith) conflicts.push({ id: claim.id, conflicts_with: conflictWith.id, claim: text });
    keys.set(key, { id: claim.id, text });
    vecs.push({ id: claim.id, text, vec });
  }

  // A malformed line is often a torn-but-recoverable claim from a crashed
  // agent write. The canonical rewrite below would destroy it, so its CONTENT
  // goes to a sidecar first — a count alone is uninvestigable (I23).
  const rejectedPath = join(paths(sessionId).dossiers, `${slug}.claims.rejected.jsonl`);
  for (const line of malformedLines) appendJsonl(rejectedPath, { ts: nowIso(), line });
  // Atomic rewrite: a crash mid-write must never truncate the dossier (I6).
  writeDossierAtomic(path, added.map((c) => JSON.stringify(c)).join("\n") + (added.length ? "\n" : ""));
  return {
    added,
    duplicates,
    conflicts,
    malformed,
    total_read: rawLines.length,
    ...(malformed > 0 ? { rejected_sidecar: rejectedPath } : {}),
  };
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

/** Delivery label: the ledger's Confidence states plus `primary-new` — a
 *  young, primary-sourced, not-yet-corroborated claim that is deliverable
 *  DATED rather than hedged (CONTRACT-7). Never written into ledger
 *  `confidence` fields, which stay on the Confidence enum. */
export type AssessLabel = Confidence | "primary-new";

export interface Sufficiency {
  label: AssessLabel;
  reason: string;
  hits: ScoredClaim[];
  independent_sources: number;
  /** Distinct sources corroborating the ANSWERING claim itself — its own
   *  sources plus those of hits stating (near enough) THE SAME thing: same
   *  ordered figures, same negation parity, no recorded conflict. A disputant
   *  never corroborates (M1). This is what "verified" is judged on;
   *  independent_sources remains the set-wide breadth count for reporting. */
  corroborating_sources: number;
  /** Hits in recorded conflict with the answering claim. Non-empty means an
   *  active dispute — surfaced and preserved, never silently harmonized. */
  conflicting_ids: string[];
  stale: boolean;
  volatile: boolean;
  /** The answering claim states a measurement (latency, price, size, throughput…). */
  numeric: boolean;
  /** At least one answering source is Tier 1-2 (a primary/authoritative source). */
  primary_sourced: boolean;
  /** Ids of strong hits that state a figure with no Tier 1-2 source. The
   *  answer is composed from every strong hit, not just the top one, so the
   *  orchestrator must never quote these as fact — deliver them as
   *  provisional or verify them first. */
  numeric_unprimaried_ids: string[];
  /** Recency of the answering claim (CONTRACT-6/7): its newest known date
   *  (as_of vs published) and whether the label is the dated primary-new
   *  state. Computed fresh at ask time, so past the 60-day window an
   *  uncorroborated primary claim decays back to provisional on its own. */
  recency: { as_of_newest: string | null; primary_new: boolean };
}

/**
 * Does this claim state a measurement — a latency, price, size, throughput,
 * parameter count, or percentage? Those are the claims that must rest on a
 * primary source, because a figure lifted from a blog or from memory is exactly
 * how "ElevenLabs ~264ms" got stated as fact when the vendor's own number was
 * ~75ms model / ~100-200ms. Deliberately narrow: it targets figures-with-units,
 * not incidental numbers like "3 seats" or a version string.
 *
 * The unit group ends with (?!\w) instead of a trailing \b: after a non-word
 * character like "%" or "×" a \b requires a following WORD character, so
 * "grew 40%" could never match the old \b form — the symbol alternatives were
 * dead. The lookahead also lets short alphabetic units ("3x", "10k") match at
 * end-of-token while still rejecting "3 seats".
 *
 * The bare-s (seconds) unit lives in its own alternative (I20): it must be
 * attached to the digits ("1.2s", "30s") and is refused for 4-digit
 * decade/year runs ("the 1990s") and for plural-of-quantity phrasing
 * ("100s of users") — both of which previously read as measurements and
 * pushed non-figures into numeric_unprimaried_ids. Spelled-out percentages
 * ("40 percent", "40 pct") now count as the measurements they are.
 */
export const MEASUREMENT_RE =
  /([$€£]\s?\d)|(\b\d[\d.,]*\s?[%×])|(\b\d[\d.,]*\s?(ms|milliseconds?|secs?|seconds?|mins?|minutes?|hrs?|hours?|tokens?\/s(ec(onds?)?)?|tok\/s|gib|mib|gb|mb|tb|kb|x|hz|khz|ghz|b|billion|million|k|usd|eur|gbp|cents?|percent|pct|params?|fps|rps|qps)(?!\w))|(\b(?!\d{4}s)\d[\d.,]*s(?!\w)(?!\s+of\b))/i;

export function looksNumeric(text: string): boolean {
  return MEASUREMENT_RE.test(text);
}

/** Newest parseable date on a claim — as_of (date OF the information) vs
 *  published (when the source said it). Null when neither parses. */
function newestDate(c: Claim): { ms: number; iso: string } | null {
  let best: { ms: number; iso: string } | null = null;
  for (const d of [c.as_of, c.published]) {
    if (!d) continue;
    const t = Date.parse(d);
    if (!Number.isNaN(t) && (best === null || t > best.ms)) best = { ms: t, iso: d };
  }
  return best;
}

/** Recorded-conflict test, symmetric: only the later-ingested side of a kept
 *  conflict carries conflicts_with, so both directions are checked. */
function inConflict(a: Claim, b: Claim): boolean {
  return (a.conflicts_with ?? []).includes(b.id) || (b.conflicts_with ?? []).includes(a.id);
}

/** Days a primary-sourced, uncorroborated claim stays `primary-new` before
 *  decaying back to provisional (CONTRACT-7). */
const PRIMARY_NEW_WINDOW_DAYS = 60;

/**
 * The CRAG-shaped sufficiency check that routes the live riff:
 *   verified       -> answer from corpus, cite it
 *   primary-new    -> answer DATED: young primary-sourced claim, corroboration
 *                     structurally not expectable yet (CONTRACT-7)
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
  let hits = search(sessionId, query, 8).filter((h) => h.score >= minScore);
  if (hits.length === 0) {
    return {
      label: "not-in-corpus",
      reason: "no dossier claim matches this question",
      hits: [],
      independent_sources: 0,
      corroborating_sources: 0,
      conflicting_ids: [],
      stale: false,
      volatile: false,
      numeric: false,
      primary_sourced: false,
      numeric_unprimaried_ids: [],
      recency: { as_of_newest: null, primary_new: false },
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
      corroborating_sources: 0,
      conflicting_ids: [],
      stale: false,
      volatile: false,
      numeric: false,
      primary_sourced: false,
      numeric_unprimaried_ids: [],
      recency: { as_of_newest: null, primary_new: false },
    };
  }
  const urls = new Set<string>();
  for (const h of hits) {
    for (const s of h.sources) urls.add(s.url ?? s.source);
  }
  const agents = new Set(hits.map((h) => h.slug));
  const independent = Math.max(urls.size, agents.size > 1 ? agents.size : 1);
  // The answering set: the strong hits an answer is actually composed from.
  // Trust judgments (staleness, volatility, figure gating) run over these —
  // not just hits[0], which would leave a figure at hits[1] unjudged, and not
  // the weak tail, where a barely-above-minScore old hit would poison a
  // perfectly fresh answer with caveats about evidence nobody is quoting.
  const strong = hits.filter((h) => h.score >= strongScore);
  const cutoff = Date.now() - staleDays * 86400_000;
  const stale = strong.some((h) => {
    const t = Date.parse(h.as_of);
    // An unparseable as_of cannot prove freshness — it reads stale, not fresh.
    return Number.isNaN(t) || t < cutoff;
  });
  const volatile = strong.some((h) => h.volatile === true);
  // A measurement is only as trustworthy as its most authoritative source. If
  // the answering claim states a figure, it must carry its OWN Tier 1-2
  // (primary/authoritative) source, or the figure cannot read "verified" — it is
  // a number nobody checked against the thing it describes. Judged per hit: a
  // different vendor's primary source elsewhere in the hits must not launder a
  // blog-only figure into looking primary-sourced. Claim-level tier is honored
  // as a fallback for sources that carry no tier of their own; every tier
  // value runs through normalizeTier so the gate and the stamp agree (M17).
  const hasPrimary = (h: ScoredClaim) =>
    h.sources.some((s) => (normalizeTier(s.tier) ?? normalizeTier(h.tier) ?? 9) <= 2);
  // CONTRACT-7 (recency §6): on conflicting VERSIONED figures, a newer
  // primary-sourced claim outranks an older one REGARDLESS of source count —
  // the answer comes from the newer primary, and the conflict stays surfaced
  // below rather than being harmonized away.
  {
    const first = hits[0]!;
    const firstDate = newestDate(first);
    const winner = strong
      .filter(
        (h) =>
          h !== first && inConflict(first, h) && !sameNumbers(first.claim, h.claim) && hasPrimary(h),
      )
      .map((h) => ({ h, d: newestDate(h) }))
      .filter((x): x is { h: ScoredClaim; d: { ms: number; iso: string } } => x.d !== null)
      .filter((x) => firstDate === null || x.d.ms > firstDate.ms)
      .sort((x, y) => y.d.ms - x.d.ms)[0];
    if (winner) hits = [winner.h, ...hits.filter((h) => h !== winner.h)];
  }
  const answer = hits[0]!;
  const numericUnprimaried = strong.filter((h) => looksNumeric(h.claim) && !hasPrimary(h));
  const unprimariedIds = numericUnprimaried.map((h) => h.id);
  const numeric = looksNumeric(answer.claim);
  const primary_sourced = hasPrimary(answer);
  // Corroboration must attach to the ANSWERING claim, not the topic area:
  // pooling URLs across the whole hit set measures breadth, so a single-source
  // answer would read "2+ independent sources" whenever any other hit carried
  // a different URL. Count the answering claim's own sources plus sources on
  // hits that state THE SAME thing — same ordered figures, same negation
  // parity, and no recorded conflict. A kept figure-conflict is >=0.82-similar
  // by construction, so without these guards a disputant's source would count
  // as corroboration for the very claim it disputes (M1).
  const answerUrls = new Set<string>();
  for (const s of answer.sources) answerUrls.add(s.url ?? s.source);
  for (const h of hits.slice(1)) {
    if (inConflict(answer, h)) continue;
    if (similarity(answer.claim, h.claim) < 0.6) continue;
    if (!sameNumbers(answer.claim, h.claim) || !sameNegation(answer.claim, h.claim)) continue;
    for (const s of h.sources) answerUrls.add(s.url ?? s.source);
  }
  const corroborating = answerUrls.size;
  const conflictingIds = hits.slice(1).filter((h) => inConflict(answer, h)).map((h) => h.id);
  const answerDate = newestDate(answer);
  const recencyOf = (primaryNew: boolean) => ({
    as_of_newest: answerDate ? answerDate.iso : null,
    primary_new: primaryNew,
  });
  if (numeric && !primary_sourced) {
    return {
      label: "provisional",
      reason:
        "states a figure with no Tier 1-2 source — verify against the vendor's own page or docs before relying on it",
      hits,
      independent_sources: independent,
      corroborating_sources: corroborating,
      conflicting_ids: conflictingIds,
      stale,
      volatile,
      numeric,
      primary_sourced,
      numeric_unprimaried_ids: unprimariedIds,
      recency: recencyOf(false),
    };
  }
  // A conflict the recency rule did not settle caps delivery at provisional:
  // while the corpus disagrees on a figure, NEITHER side may read verified.
  // The answer "beats" a disputant only as the newer primary on differing
  // figures (versioned facts) — negation disputes and undated claims are
  // never recency-settled.
  const beats = (h: ScoredClaim) => {
    const d = newestDate(h);
    return (
      !sameNumbers(answer.claim, h.claim) &&
      primary_sourced &&
      answerDate !== null &&
      (d === null || answerDate.ms > d.ms)
    );
  };
  const unresolved = hits
    .slice(1)
    .filter((h) => inConflict(answer, h) && !beats(h))
    .map((h) => h.id);
  if (unresolved.length > 0) {
    return {
      label: "provisional",
      reason:
        `corpus disagrees: ${answer.id} vs ${unresolved.join(", ")} state conflicting versions — ` +
        `reconcile (probe the primary source) before delivering either as settled`,
      hits,
      independent_sources: independent,
      corroborating_sources: corroborating,
      conflicting_ids: conflictingIds,
      stale,
      volatile,
      numeric,
      primary_sourced,
      numeric_unprimaried_ids: unprimariedIds,
      recency: recencyOf(false),
    };
  }
  // An unprimaried figure on a SUPPORTING hit must stay visible even when the
  // answering claim itself is clean — the orchestrator gates quoting per hit.
  const figureCaveat =
    unprimariedIds.length > 0
      ? `; ${unprimariedIds.join(", ")} state${
          unprimariedIds.length === 1 ? "s" : ""
        } a figure with no Tier 1-2 source — quote ${
          unprimariedIds.length === 1 ? "it" : "those"
        } only as provisional`
      : "";
  // A recency-settled conflict is preserved, not hidden: the reason names the
  // outranked claim(s) so delivery can say what the older source said.
  const conflictNote =
    conflictingIds.length > 0
      ? `; outranks conflicting ${conflictingIds.join(", ")} on recency — newer primary source wins, conflict preserved`
      : "";
  if (corroborating >= 2) {
    return {
      label: "verified",
      reason:
        `${corroborating} independent sources corroborate the answering claim ` +
        `(${agents.size} dossier(s))${conflictNote}${figureCaveat}`,
      hits,
      independent_sources: independent,
      corroborating_sources: corroborating,
      conflicting_ids: conflictingIds,
      stale,
      volatile,
      numeric,
      primary_sourced,
      numeric_unprimaried_ids: unprimariedIds,
      recency: recencyOf(false),
    };
  }
  // CONTRACT-7: a young claim from a primary source is not the same epistemic
  // state as a lone aged blog post. Best source Tier 1-2 + newest date within
  // the window => deliverable DATED as primary-new instead of hedged as
  // provisional. Youth explains low corroboration; it does not disqualify.
  // Computed fresh on every ask, so the label decays to provisional by itself
  // once the window passes without corroboration arriving. The I9 floor is
  // untouched: an unprimaried figure never reaches this branch.
  const young =
    answerDate !== null && Date.now() - answerDate.ms <= PRIMARY_NEW_WINDOW_DAYS * 86400_000;
  if (primary_sourced && young) {
    return {
      label: "primary-new",
      reason:
        `single primary source dated ${answerDate!.iso} — too new for independent corroboration yet; ` +
        `deliver it dated ("per the source, as of ${answerDate!.iso}"), never as settled fact` +
        conflictNote +
        figureCaveat,
      hits,
      independent_sources: independent,
      corroborating_sources: corroborating,
      conflicting_ids: conflictingIds,
      stale,
      volatile,
      numeric,
      primary_sourced,
      numeric_unprimaried_ids: unprimariedIds,
      recency: recencyOf(true),
    };
  }
  return {
    label: "provisional",
    reason:
      (corroborating <= 1
        ? "single source — corroboration missing"
        : "matched, but sources are not clearly independent") +
      conflictNote +
      figureCaveat,
    hits,
    independent_sources: independent,
    corroborating_sources: corroborating,
    conflicting_ids: conflictingIds,
    stale,
    volatile,
    numeric,
    primary_sourced,
    numeric_unprimaried_ids: unprimariedIds,
    recency: recencyOf(false),
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

/** One questions.jsonl record. `thread`/`depth` are the deep-drill stamps —
 *  optional and additive; records without them are legal forever. `label` is
 *  the assess label captured at ask time, so `riff thread` can replay a
 *  drill history without re-assessing a corpus that has since changed. */
export interface QuestionRecord {
  text: string;
  ts: string;
  thread?: string;
  depth?: number;
  label?: string;
}

export function recordQuestion(
  sessionId: string,
  text: string,
  extra: { thread?: string; depth?: number; label?: string } = {},
): void {
  appendJsonl(paths(sessionId).questions, {
    text,
    ts: new Date().toISOString(),
    ...(extra.thread ? { thread: extra.thread } : {}),
    // depth 0 (L0) is falsy — spread on !== undefined, never on truthiness.
    ...(extra.depth !== undefined ? { depth: extra.depth } : {}),
    ...(extra.label ? { label: extra.label } : {}),
  });
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
    // Only citable claims may be surfaced: the moderator hands its pick
    // straight to the reader, so a sourceless claim here would deliver an
    // unprovenanced statement with the session's authority behind it (I1).
    .filter((c) => !seen.has(c.id) && (c.sources?.length ?? 0) > 0)
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
    // Unparseable dossier lines awaiting ingest — a damaged dossier must show
    // as damaged here, not as empty (I22).
    pending_malformed: pending.reduce((n, p) => n + (p.malformed_lines ?? 0), 0),
  };
}

export { similarity };
