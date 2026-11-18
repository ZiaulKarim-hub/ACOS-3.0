/**
 * policy.ts — MACHINE POLICY: standing rules the machine applies to itself (D-49).
 *
 * WHY THIS FILE EXISTS. D-08 is the oldest promise here: the machine decides, not Zee. D-44
 * gave the machine an escape so the ladder could never deadlock — the judge may rule a rung
 * inapplicable with a written reason. Measured on website-design-okoa/v2, that escape was used
 * 496 times with 123 distinct reasons, and 356 findings reached Zee anyway. Roughly four
 * rulings per reason: the SAME judgement was re-derived from scratch again and again, reviewed
 * by nobody, remembered by nothing, and auditable only by reading 496 history lines.
 *
 * Zee, 2026-11-04: "Just using the judgement is not enough, it has to be best judgement with
 * checks and balances. that was one of the main purpose of the nemesis protocol. The codes
 * writed needs to be invincible."
 *
 * So a recurring judgement stops being a per-finding ruling and becomes a POLICY: written once,
 * reviewed once by an independent reader, recorded with the evidence that justified it, applied
 * mechanically afterwards, and auditable as one row instead of hundreds. Zee can veto any
 * policy by id at any time, and a veto walks back every finding it moved.
 *
 * THE INVINCIBILITY LINE — the single most important property in this file.
 * A policy may choose only among the rungs the MACHINE owns (2..6). It can NEVER close a
 * finding, mark it decided, drop it, accept it, change a requirement, or rule it N/A. There is
 * no field on a Policy that could express any of those, so this is a structural guarantee and
 * not a check that can be forgotten. D-11's four closure criteria still hold for every finding,
 * every time: a reproduction test that passes, a green suite, two clean scans, an independent
 * reviewer. A policy makes the machine FASTER at spending its own options. It can never make
 * the gate LAXER, and it can never shorten the ladder — only move along it.
 */
import * as fs from "node:fs";
import * as path from "node:path";
import { P, nemesisDir, readJson, writeJson, nowIso, appendRecord, readIssue, writeIssue, listIssues, type Issue, type Lens } from "./state";

export const POLICY_SCHEMA = "nemesis-policy/1" as const;
/** The rungs a policy may send a finding to: exactly the ones the machine owns itself. */
export const POLICY_RUNGS = [2, 3, 4, 5, 6] as const;
export type PolicyRung = (typeof POLICY_RUNGS)[number];

export interface PolicyProbe { checklist: string; where: string; what: string; lens?: Lens }
export interface PolicyWhen { checklist?: string; where?: string; what?: string; lens?: Lens }
export interface Policy {
  schema: typeof POLICY_SCHEMA;
  id: string;
  /** One sentence a person can read and veto. */
  rule: string;
  when: PolicyWhen;
  /** The machine rung this whole class takes. Never a closure — see the header. */
  then_rung: PolicyRung;
  why: string;
  /** What measurement justified it. A policy with no evidence is an opinion, and is refused. */
  evidence: string;
  /** A case it MUST fire on and a near-miss it MUST NOT. Both required (D-25 traceability). */
  test: { fires_on: PolicyProbe; not_on: PolicyProbe };
  origin: "machine-proposed" | "zee-confirmed";
  proposed_at: string;
  proposed_by: string;
  review?: { at: string; by: string; approved: boolean; note: string };
  status: "proposed" | "active" | "vetoed";
  vetoed?: { at: string; by: string; why: string };
  applications: { at: string; issue: string; from_rung: number; to_rung: number }[];
}

export const PP = {
  dir: (r: string) => path.join(nemesisDir(r), "policy"),
  file: (r: string, id: string) => path.join(nemesisDir(r), "policy", `${id}.json`),
  counter: (r: string) => path.join(nemesisDir(r), "policy", "_counter.json"),
};

function reSafe(src: string): RegExp | null {
  try { return new RegExp(src, "i"); } catch { return null; }
}

/** Does this policy's matcher select that finding? Every stated field must match. */
export function matches(when: PolicyWhen, probe: PolicyProbe): boolean {
  const fields: [keyof PolicyWhen, string][] = [["checklist", probe.checklist], ["where", probe.where], ["what", probe.what]];
  let any = false;
  for (const [k, v] of fields) {
    const src = when[k] as string | undefined;
    if (!src) continue;
    any = true;
    const re = reSafe(src);
    if (!re || !re.test(v ?? "")) return false;
  }
  if (when.lens) { any = true; if (when.lens !== probe.lens) return false; }
  return any;
}

export function probeOf(i: Issue): PolicyProbe {
  return { checklist: i.checklist, where: i.where, what: i.what, lens: i.lens };
}

/**
 * Every way a policy can be malformed. An empty list is the ONLY thing that may be activated.
 * These are the checks and balances, stated once, enforced in code:
 *   1. the rung is one the machine owns (the invincibility line);
 *   2. the rule, the reasoning and the EVIDENCE are all actually written down;
 *   3. the matcher selects something, and every pattern in it compiles;
 *   4. it fires on the case that motivated it, and does NOT fire on a stated near-miss.
 * (4) is the one that catches a rule written too wide, which is how my own lane fix went wrong
 * on 2026-11-02: it reclassified 17 findings it was never meant to touch.
 */
export function policyShapeProblems(p: Policy): string[] {
  const out: string[] = [];
  if (p.schema !== POLICY_SCHEMA) out.push(`schema must be ${POLICY_SCHEMA}`);
  if (!(POLICY_RUNGS as readonly number[]).includes(p.then_rung)) out.push(`then_rung must be one of ${POLICY_RUNGS.join(", ")} — the rungs the machine owns. A policy may never close, decide, accept, drop or rule a finding N/A (D-49).`);
  if ((p.rule ?? "").trim().length < 20) out.push("rule: write the standing rule as one readable sentence (20+ chars) — Zee vetoes by reading it");
  if ((p.why ?? "").trim().length < 20) out.push("why: state the reasoning (20+ chars)");
  if ((p.evidence ?? "").trim().length < 20) out.push("evidence: name the measurement that justified this (20+ chars). A policy with no evidence is an opinion.");
  const w = p.when ?? {};
  if (!w.checklist && !w.where && !w.what && !w.lens) out.push("when: give at least one of checklist / where / what / lens, or this would match everything");
  for (const k of ["checklist", "where", "what"] as const) {
    const src = w[k]; if (src && !reSafe(src)) out.push(`when.${k}: not a valid regular expression`);
  }
  const t = p.test;
  if (!t?.fires_on || !t?.not_on) out.push("test: both a fires_on case and a not_on near-miss are required (D-25)");
  else {
    if (!matches(w, t.fires_on)) out.push("test.fires_on: this policy does NOT match the case it says motivated it — the matcher is too narrow");
    if (matches(w, t.not_on)) out.push("test.not_on: this policy ALSO matches the near-miss it says it must not — the matcher is too wide");
  }
  return out;
}

function nextPolicyId(root: string): string {
  const c = readJson<{ POL: number }>(PP.counter(root), { POL: 0 });
  c.POL += 1; fs.mkdirSync(PP.dir(root), { recursive: true }); writeJson(PP.counter(root), c);
  return `POL-${c.POL}`;
}

export function readPolicy(root: string, id: string): Policy | null { return readJson<Policy | null>(PP.file(root, id), null); }
export function writePolicy(root: string, p: Policy): void { fs.mkdirSync(PP.dir(root), { recursive: true }); writeJson(PP.file(root, p.id), p); }
export function listPolicies(root: string): Policy[] {
  const d = PP.dir(root);
  if (!fs.existsSync(d)) return [];
  return fs.readdirSync(d).filter((f) => f.endsWith(".json") && !f.startsWith("_"))
    .map((f) => readPolicy(root, f.replace(/\.json$/, ""))).filter((p): p is Policy => !!p)
    .sort((a, b) => a.id.localeCompare(b.id, undefined, { numeric: true }));
}
export function activePolicies(root: string): Policy[] { return listPolicies(root).filter((p) => p.status === "active"); }

/** Propose a policy. Shape is checked HERE, so a malformed one never reaches the store. */
export function proposePolicy(root: string, draft: Omit<Policy, "schema" | "id" | "status" | "proposed_at" | "applications">): { policy?: Policy; problems: string[] } {
  const p: Policy = { ...draft, schema: POLICY_SCHEMA, id: "POL-?", status: "proposed", proposed_at: nowIso(), applications: [] };
  const problems = policyShapeProblems(p);
  if (problems.length) return { problems };
  p.id = nextPolicyId(root);
  writePolicy(root, p);
  appendRecord(root, "policy", { event: "proposed", id: p.id, rule: p.rule, then_rung: p.then_rung, origin: p.origin });
  return { policy: p, problems: [] };
}

/**
 * Record an INDEPENDENT review of a policy and activate it only on approval.
 * The reviewer is a separate reader that never saw the proposer's reasoning (D-15), which is
 * what makes this a balance rather than the same judgement twice.
 */
export function reviewPolicy(root: string, id: string, by: string, approved: boolean, note: string): { policy?: Policy; problems: string[] } {
  const p = readPolicy(root, id);
  if (!p) return { problems: [`no policy ${id}`] };
  if (p.status === "vetoed") return { problems: [`${id} was vetoed by Zee and cannot be revived — propose a new one`] };
  if (!note.trim()) return { problems: ["a review needs a written note, approved or not"] };
  const problems = policyShapeProblems(p);
  if (approved && problems.length) return { problems: [`${id} cannot be activated while malformed:`, ...problems] };
  p.review = { at: nowIso(), by, approved, note: note.trim() };
  p.status = approved ? "active" : "proposed";
  writePolicy(root, p);
  appendRecord(root, "policy", { event: approved ? "activated" : "review-rejected", id, by, note: note.trim() });
  return { policy: p, problems: [] };
}

/** Zee's veto. Stops future application AND walks back every finding this policy moved. */
export function vetoPolicy(root: string, id: string, why: string): { policy?: Policy; reopened: string[]; problems: string[] } {
  const p = readPolicy(root, id);
  if (!p) return { reopened: [], problems: [`no policy ${id}`] };
  p.status = "vetoed";
  p.vetoed = { at: nowIso(), by: "Zee", why: why.trim() || "(no reason given)" };
  const reopened: string[] = [];
  for (const a of p.applications) {
    const i = readIssue(root, a.issue);
    if (!i || i.status === "closed" || i.status === "decided") continue;
    if (i.rung !== a.to_rung) continue; // moved on since; leave it where it is
    i.rung = a.from_rung;
    i.history.push({ at: nowIso(), event: "policy-vetoed", detail: `${p.id} vetoed by Zee; rung ${a.to_rung} → ${a.from_rung} restored` });
    writeIssue(root, i);
    reopened.push(i.id);
  }
  writePolicy(root, p);
  appendRecord(root, "policy", { event: "vetoed", id, why: p.vetoed.why, reopened });
  return { policy: p, reopened, problems: [] };
}

/**
 * Apply the active policies to one finding. Returns the policy that fired, if any.
 *
 * Only ever moves a finding UP the ladder, never down, and never past rung 6. A policy that
 * matches a finding already at or above its rung does nothing, which is what stops two
 * policies from fighting over the same finding forever.
 */
export function applyPolicies(root: string, i: Issue): { policy: Policy; from: number; to: number } | null {
  if (i.status === "closed" || i.status === "decided") return null;
  const probe = probeOf(i);
  for (const p of activePolicies(root)) {
    if (!matches(p.when, probe)) continue;
    if (p.then_rung <= i.rung) continue;
    const from = i.rung;
    i.rung = p.then_rung;
    i.history.push({ at: nowIso(), event: "policy", detail: `${from} → ${p.then_rung} by ${p.id}: ${p.rule}` });
    writeIssue(root, i);
    p.applications.push({ at: nowIso(), issue: i.id, from_rung: from, to_rung: p.then_rung });
    writePolicy(root, p);
    appendRecord(root, "policy", { event: "applied", id: p.id, issue: i.id, from, to: p.then_rung });
    return { policy: p, from, to: p.then_rung };
  }
  return null;
}

// ── The reuse cap: a reason used again and again is a policy, not a ruling ───

export function normalizeReason(s: string): string {
  return s.toLowerCase().replace(/\b(sec|fun)-\d+\b/g, "<id>").replace(/\bR-\d+\b/gi, "<req>")
    .replace(/\d+/g, "#").replace(/[^a-z#<>]+/g, " ").trim().split(/\s+/).slice(0, 14).join(" ");
}

export const DEFAULT_NA_REASON_CAP = 3;

/**
 * How many times this same reason has already been used to rule a rung inapplicable, across
 * the whole ledger. Counting is over the NORMALIZED reason, so re-wording it does not reset
 * the count — re-wording is exactly how 123 "distinct" reasons covered 496 rulings.
 */
export function naReasonUses(root: string, reason: string): { count: number; issues: string[] } {
  const key = normalizeReason(reason);
  if (!key) return { count: 0, issues: [] };
  const issues: string[] = [];
  for (const i of listIssues(root)) {
    for (const h of i.history) {
      if (h.event !== "rung-na" && h.event !== "rung-na-proposed" && h.event !== "rung-na-confirmed") continue;
      const m = (h.detail ?? "").replace(/^rung \d+ ruled inapplicable: /, "");
      if (normalizeReason(m) === key) { issues.push(i.id); break; }
    }
  }
  return { count: issues.length, issues };
}
