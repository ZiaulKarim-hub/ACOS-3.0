// Cleanroom fingerprinting utilities — self-contained, no external deps.
// Used by egress-guard.ts and by the capture/wall phases to build the
// dirty-room fingerprint that the guard checks outgoing payloads against.

import { createHash } from "node:crypto";

/** Normalize text for shingling: lowercase, collapse whitespace, strip most punctuation. */
export function normalize(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^\p{L}\p{N}\s]/gu, " ")
    .replace(/\s+/g, " ")
    .trim();
}

/** sha256 hex of a string. */
export function sha256(text: string): string {
  return createHash("sha256").update(text, "utf8").digest("hex");
}

/**
 * Word-shingle set: overlapping windows of `k` words, each hashed to a short id.
 * Shingles are the unit we use to detect "dirty-room text is leaking into an
 * outgoing payload" without storing the raw dirty text in the fingerprint file.
 */
export function shingles(text: string, k: number): Set<string> {
  const words = normalize(text).split(" ").filter(Boolean);
  const out = new Set<string>();
  if (words.length < k) {
    if (words.length > 0) out.add(sha256(words.join(" ")).slice(0, 16));
    return out;
  }
  for (let i = 0; i + k <= words.length; i++) {
    out.add(sha256(words.slice(i, i + k).join(" ")).slice(0, 16));
  }
  return out;
}

export interface DirtyFingerprint {
  version: string;
  session_id: string;
  shingle_words: number;
  // hashed shingles of every dirty-room artifact (capture + intent, pre-wall)
  shingles: string[];
  // literal forbidden tokens the spec-wall extracted (secrets, identifiers,
  // technology nouns, entity names) — exact-match banned in any egress payload.
  forbidden_tokens: string[];
  // sha256 of files explicitly cleared to leave (e.g. 02-wall/spec-clean.md)
  allow_hashes: string[];
  // OPTIONAL multi-granularity layer (fingerprint-build.ts --multigranularity):
  // per-paragraph hashes so a single pasted dirty CHUNK is caught even when it is
  // shorter than the shingle window. Absent → the guard keeps its original behavior.
  chunk_shingles?: string[];
}

/** Count how many of the payload's paragraph-chunk hashes appear in the dirty fingerprint. */
export function sharedChunkCount(payload: string, fp: DirtyFingerprint): number {
  const dirty = new Set(fp.chunk_shingles ?? []);
  if (dirty.size === 0) return 0;
  let n = 0;
  for (const c of payload.split(/\n\s*\n/)) {
    const nrm = normalize(c);
    if (nrm.split(" ").filter(Boolean).length < 4) continue;
    if (dirty.has(sha256(nrm).slice(0, 16))) n++;
  }
  return n;
}

/** Count how many of the payload's shingles appear in the dirty fingerprint. */
export function sharedShingleCount(payload: string, fp: DirtyFingerprint): number {
  const dirty = new Set(fp.shingles);
  let n = 0;
  for (const s of shingles(payload, fp.shingle_words)) if (dirty.has(s)) n++;
  return n;
}

/** Return the list of forbidden tokens that appear verbatim in the payload. */
export function forbiddenHits(payload: string, fp: DirtyFingerprint): string[] {
  const hay = normalize(payload);
  const hits: string[] = [];
  for (const tok of fp.forbidden_tokens) {
    const needle = normalize(tok);
    if (needle.length >= 3 && hay.includes(needle)) hits.push(tok);
  }
  return hits;
}
