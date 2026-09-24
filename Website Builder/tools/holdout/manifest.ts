/**
 * manifest.ts — the holdout manifest schema, parser and validator.
 *
 * The manifest is PUBLIC and committed BEFORE the code exists (PRD §22.1). It
 * carries the SHAPE of the exam — how many cases, which classes, which invariants
 * — and the HASHES of the sealed content. The cases and answers live in
 * `qa-private/`, git-ignored in the implementation worktree.
 *
 * Shape carried over from R2P's Appendix F.6 unchanged, plus one added field:
 * `hash_method`, so a manifest is self-describing (PRD §22.6).
 *
 * WHAT THIS FILE DOES NOT CHECK, stated because the gap matters — the same
 * limitation R2P's own verifier header records, and restating it does not fix it:
 *   - It does NOT verify that a filled `revealed_at` is TRUE. A well-formed
 *     timestamp for a reveal that never happened would pass. Truth comes from the
 *     evidence bundle, not from this parser.
 *   - It approves and ratifies nothing. A manifest that parses is a manifest that
 *     parses.
 */

import { HASH_METHOD } from "./canonical-hash.ts";

/** PRD §22.2. `counterexample` is the class most often skipped and the one that
 *  catches the most: a suite of only should-pass cases cannot tell a working gate
 *  from a gate that approves everything. */
export const CASE_CLASSES = ["nominal", "boundary", "hostile", "counterexample"] as const;
export type CaseClass = (typeof CASE_CLASSES)[number];

export interface HoldoutManifest {
  artifact_type: "HoldoutManifest";
  id: string;                      // HLD-<slice-id>-v<n>
  parent_story_id: string;
  dev_id: string;                  // the slice this gates
  qa_id: string;
  contract_version: string;
  created_at: string;              // ISO-8601 UTC
  custodian: string;
  hash_method: typeof HASH_METHOD;
  case_classes: CaseClass[];
  case_count: number;
  covered_invariants: string[];
  private_pack_sha256: string;
  expected_results_sha256: string;
  revealed_at: string | null;      // null until the pack is spent
  run_evidence_bundle: string | null;
}

/**
 * ISO-8601 UTC, `Z` only, optional fractional seconds.
 *
 * A local-offset timestamp is REFUSED rather than normalised: two custodians in
 * two zones would then write two different strings for one instant, and the
 * ordering of reveals is evidence. Refusing is loud; normalising is silent.
 */
const ISO_UTC = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,9})?Z$/;

/** `HLD-<slice-id>-v<n>` — PRD §22.4. The slice id is carried verbatim, because
 *  this project mints no second numbering scheme (it already carries O31–O34 and
 *  A91+ collisions and will not add to them). */
export const ID_SHAPE = /^HLD-(S\d{2,}[A-Za-z0-9-]*)-v(\d+)$/;

export const SHA256_HEX = /^[0-9a-f]{64}$/;

export interface Problem { field: string; message: string }

export function validate(m: unknown, opts: { requireCounterexample?: boolean } = {}): Problem[] {
  const p: Problem[] = [];
  const bad = (field: string, message: string) => p.push({ field, message });
  if (typeof m !== "object" || m === null) return [{ field: "(root)", message: "not a mapping" }];
  const o = m as Record<string, unknown>;

  if (o.artifact_type !== "HoldoutManifest") bad("artifact_type", `expected "HoldoutManifest", got ${JSON.stringify(o.artifact_type)}`);

  const idm = typeof o.id === "string" ? ID_SHAPE.exec(o.id) : null;
  if (!idm) bad("id", `expected HLD-<slice-id>-v<n>, got ${JSON.stringify(o.id)}`);

  // The manifest must name the slice it gates, and the id must agree with it.
  // A manifest pointing at one slice while named for another is a pack that will
  // be revealed against the wrong candidate — silent, and unrecoverable after.
  if (typeof o.dev_id !== "string" || !o.dev_id) bad("dev_id", "missing");
  else if (idm && !o.dev_id.startsWith(idm[1])) bad("id", `id names slice "${idm[1]}" but dev_id is "${o.dev_id}"`);

  for (const f of ["parent_story_id", "qa_id", "contract_version", "custodian"]) {
    if (typeof o[f] !== "string" || !(o[f] as string).trim()) bad(f, "missing or empty");
  }

  // PRD §22.1 property 2: the custodian is not the implementer. This is an
  // ATTESTATION, not a proof — nothing here can tell who actually typed the file.
  // It is checked because an empty or defaulted custodian field is the cheap
  // failure, and the expensive one at least has to be written down on purpose.
  if (typeof o.custodian === "string" && /implement/i.test(o.custodian) && !/not the implement/i.test(o.custodian)) {
    bad("custodian", `names an implementer: ${JSON.stringify(o.custodian)}`);
  }

  if (o.hash_method !== HASH_METHOD) bad("hash_method", `expected "${HASH_METHOD}", got ${JSON.stringify(o.hash_method)} — an unknown method is refused rather than guessed (§22.6)`);

  if (typeof o.created_at !== "string" || !ISO_UTC.test(o.created_at)) bad("created_at", `expected ISO-8601 UTC, got ${JSON.stringify(o.created_at)}`);

  const cc = o.case_classes;
  if (!Array.isArray(cc) || cc.length === 0) bad("case_classes", "missing or empty");
  else {
    for (const c of cc) if (!CASE_CLASSES.includes(c as CaseClass)) bad("case_classes", `unknown class ${JSON.stringify(c)}`);
    if (opts.requireCounterexample && !cc.includes("counterexample")) {
      bad("case_classes", "this slice requires a `counterexample` case: a suite of only should-pass cases cannot distinguish a working gate from one that approves everything (§22.2)");
    }
  }

  if (typeof o.case_count !== "number" || !Number.isInteger(o.case_count) || o.case_count < 1) bad("case_count", `expected a positive integer, got ${JSON.stringify(o.case_count)}`);
  if (!Array.isArray(o.covered_invariants)) bad("covered_invariants", "expected a list");

  for (const f of ["private_pack_sha256", "expected_results_sha256"]) {
    if (typeof o[f] !== "string" || !SHA256_HEX.test(o[f] as string)) bad(f, `expected 64 lowercase hex chars, got ${JSON.stringify(o[f])}`);
  }

  if (!(o.revealed_at === null || (typeof o.revealed_at === "string" && ISO_UTC.test(o.revealed_at)))) {
    bad("revealed_at", `expected null or an ISO-8601 UTC timestamp, got ${JSON.stringify(o.revealed_at)} — a value that is neither is a silently broken record rather than a loud one`);
  }

  // A sealed run must name its evidence bundle, or the one thing that could show
  // the reveal actually happened is unreachable from the manifest.
  if (o.revealed_at !== null && !(typeof o.run_evidence_bundle === "string" && (o.run_evidence_bundle as string).trim())) {
    bad("run_evidence_bundle", "a revealed manifest must name its sealed run record");
  }
  return p;
}

export function parse(text: string): { ok: true; value: unknown } | { ok: false; error: string } {
  try {
    // Bun.YAML — built in, so this tool has zero dependencies and needs no
    // package.json. A hand-edited manifest can read correctly to the eye and
    // still fail to parse, which is why parsing is itself a checked step.
    return { ok: true, value: (globalThis as any).Bun.YAML.parse(text) };
  } catch (e) {
    return { ok: false, error: String(e instanceof Error ? e.message : e) };
  }
}


/**
 * Shape-check every expected.json entry, shared by seal (refuse at authoring,
 * where a fix is free) and reveal (refuse pre-run, before any case executes).
 * `caseIds` are the ids to check; `expected` is the parsed expected.json.
 * Robust-review round 5 factored this out of reveal so seal enforces the same
 * shape — a malformed answer key no longer seals a v1 that can never be revealed.
 */
export function expectedShapeProblems(caseIds: string[], expected: Record<string, unknown>): string[] {
  const problems: string[] = [];
  for (const id of caseIds) {
    const w = (expected as any)[id];
    if (w === undefined) { problems.push(`${id}: no entry in expected.json`); continue; }
    if (w === null || typeof w !== "object" || Array.isArray(w)) {
      problems.push(`${id}: entry is ${w === null ? "null" : Array.isArray(w) ? "an array" : typeof w}, expected an object`);
      continue;
    }
    if (typeof (w as any).exit !== "number") { problems.push(`${id}: "exit" is ${typeof (w as any).exit}, expected a number`); continue; }
    // Security review F10: optional fields were tested for TRUTHINESS at use, so
    // "" or null silently disabled that check, and a misspelled field name was
    // silently ignored. All refused here instead.
    for (const k of Object.keys(w)) {
      if (k !== "exit" && k !== "stdout_sha256" && k !== "stdout_contains") {
        problems.push(`${id}: unknown expectation field ${JSON.stringify(k)} — a typo here would silently weaken the case`);
      }
    }
    if ("stdout_sha256" in w && (typeof (w as any).stdout_sha256 !== "string" || !SHA256_HEX.test((w as any).stdout_sha256))) {
      problems.push(`${id}: "stdout_sha256" must be 64 lowercase hex characters`);
    }
    if ("stdout_contains" in w && (typeof (w as any).stdout_contains !== "string" || (w as any).stdout_contains.length === 0)) {
      problems.push(`${id}: "stdout_contains" must be a non-empty string — an empty one matches everything and checks nothing`);
    }
  }
  return problems;
}
