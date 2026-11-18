/**
 * verdict.ts — parse a judge reply, and when it cannot be read, FIND OUT WHY and recover
 * (R-037, D-14). Zee: "make sure that the oracle finds the reason of a verdict being
 * unreadable and finds a way to read this and then makes the decision, not just passes it
 * to me." So an unreadable reply is a CLASSIFIED failure with a recovery plan, never an
 * allow, and a deny only at the very end, naming the class.
 */
import type { Finding, Severity, Lens } from "./state";

export interface HistoryAssessment { stuck: boolean; recommended_rung: number; why: string }
export interface Verdict {
  decision: "allow" | "deny";
  findings: Finding[];
  history_assessment: HistoryAssessment;
  reason?: string;
}

export type FailureClass = "empty" | "usage_limit" | "too_long" | "prose" | "malformed" | "auth" | "crash";

const SEVS: Severity[] = ["critical", "high", "medium", "low"];

/** Last JSON object carrying a "decision" wins — a thinking-aloud reply ends with its answer. */
export function parseVerdict(raw: string): Verdict | null {
  const text = (raw ?? "").trim();
  if (!text) return null;
  const candidates = extractJsonObjects(text).filter((s) => /"decision"\s*:/.test(s));
  for (let i = candidates.length - 1; i >= 0; i--) {
    const v = tryParse(candidates[i]!);
    if (v) return v;
    const repaired = tryParse(repairJson(candidates[i]!));
    if (repaired) return repaired;
  }
  return null;
}

function tryParse(s: string): Verdict | null {
  try {
    const o = JSON.parse(s) as Partial<Verdict> & { decision?: string };
    if (o.decision !== "allow" && o.decision !== "deny") return null;
    const findings: Finding[] = Array.isArray(o.findings) ? o.findings.map(normalizeFinding).filter((f): f is Finding => !!f) : [];
    // Deny-by-default: an "allow" that still lists findings is a deny — EXCEPT a finding
    // that is only about the wording of a comment (D-55). Zee, 2026-11-09: "No need to
    // correct the grammar and prose of comments at all, for comments, only the understanding
    // is important. As long as it is understood correctly by another bot, it is good to go."
    //
    // WHY THIS IS THE WHOLE FIX AND NOT A FILTER. Measured on website-design-okoa/v2:
    // 553 edits judged, 345 denied (62%), and each denial opened 2.0 findings on average.
    // One attempt therefore produced 0.62 * 2.0 = 1.24 new findings, and any figure above
    // 1.0 grows without limit — which is why that ledger went 42 open to 789 and never fell.
    // 515 of the 764 open findings (67%) were comment wording. Taking those out of the DENY
    // path is what moves the multiplier below 1.0; nothing about batching or ordering can.
    // The finding is still RECORDED, so nothing is hidden; it simply stops blocking.
    const blocking = findings.filter((f) => !f.comment_only);
    const decision: "allow" | "deny" = blocking.length ? "deny" : o.decision === "deny" && findings.length === 0 ? "deny" : "allow";
    const ha = o.history_assessment ?? { stuck: false, recommended_rung: 1, why: "" };
    return {
      decision, findings,
      history_assessment: { stuck: !!ha.stuck, recommended_rung: clampRung(Number(ha.recommended_rung) || 1), why: String(ha.why ?? "") },
      reason: typeof o.reason === "string" ? o.reason.slice(0, 2000) : undefined,
    };
  } catch { return null; }
}

function clampRung(n: number): number { return Math.max(1, Math.min(6, Math.floor(n))); }

function normalizeFinding(f: unknown): Finding | null {
  if (!f || typeof f !== "object") return null;
  const o = f as Record<string, unknown>;
  const what = String(o.what ?? "").trim();
  if (!what) return null;
  const sev = String(o.severity ?? "high").toLowerCase() as Severity;
  const lens = (String(o.lens ?? "PSC").toUpperCase() === "PFC" ? "PFC" : "PSC") as Lens;
  return {
    id: o.id ? String(o.id) : undefined,
    severity: SEVS.includes(sev) ? sev : "high",
    lens,
    checklist: String(o.checklist ?? (lens === "PFC" ? "PFC-a" : "Q0")),
    where: String(o.where ?? "(unspecified)"),
    what,
    root_cause: o.root_cause ? String(o.root_cause) : undefined,
    fix_hint: o.fix_hint ? String(o.fix_hint) : undefined,
    comment_only: o.comment_only === true,
  };
}

/** Balanced-brace scan that tolerates braces inside strings. */
export function extractJsonObjects(text: string): string[] {
  const out: string[] = [];
  let depth = 0, start = -1, inStr = false, esc = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i]!;
    if (inStr) { if (esc) esc = false; else if (c === "\\") esc = true; else if (c === '"') inStr = false; continue; }
    if (c === '"') { inStr = true; continue; }
    if (c === "{") { if (depth === 0) start = i; depth++; }
    else if (c === "}") { depth--; if (depth === 0 && start >= 0) { out.push(text.slice(start, i + 1)); start = -1; } if (depth < 0) depth = 0; }
  }
  return out;
}

/** Fix the common ways a model mangles JSON: fences, trailing commas, single quotes, smart quotes. */
export function repairJson(s: string): string {
  return s
    .replace(/```(?:json)?/g, "")
    .replace(/[\u201c\u201d]/g, '"').replace(/[\u2018\u2019]/g, "'")
    .replace(/,\s*([}\]])/g, "$1")
    .replace(/'([^'\\]*)'\s*:/g, '"$1":')
    .replace(/:\s*'([^'\\]*)'/g, ': "$1"')
    .replace(/\bTrue\b/g, "true").replace(/\bFalse\b/g, "false").replace(/\bNone\b/g, "null");
}

/** Why could the reply not be read? Decide from stdout, stderr and the exit code. */
export function classifyFailure(stdout: string, stderr: string, exitCode: number | null): FailureClass {
  const all = `${stdout}\n${stderr}`;
  if (/E2BIG|argument list too long|prompt is too long|too many tokens|exceeds the (maximum|context)|context window/i.test(all)) return "too_long";
  if (/usage limit|rate limit|rate_limit|quota|429|overloaded|too many requests|limit reached|You've reached/i.test(all)) return "usage_limit";
  if (/not logged in|unauthori[sz]ed|invalid api key|authentication|please run \/login|OAuth/i.test(all)) return "auth";
  if (!stdout.trim()) return exitCode === 0 ? "empty" : "crash";
  if (extractJsonObjects(stdout).some((s) => /"decision"/.test(s))) return "malformed";
  return "prose";
}

export interface RecoveryStep { action: "retry_direct" | "retry_backoff" | "shrink_to_file" | "json_only_reask" | "extract_from_prose" | "repair_json" | "alternate_account" | "wait_then_retry"; note: string }

/** The ordered plan for each class. The daemon executes it; every step is logged. */
export function recoveryPlan(cls: FailureClass): RecoveryStep[] {
  switch (cls) {
    case "empty":
    case "crash":
      return [
        { action: "retry_direct", note: "child produced no answer — retry once directly" },
        { action: "retry_backoff", note: "retry with backoff (3s, 10s)" },
        { action: "shrink_to_file", note: "move the large inputs into a file the judge reads; resend a short prompt" },
      ];
    case "usage_limit":
      return [
        { action: "wait_then_retry", note: "usage/rate limit — wait and retry with backoff (bounded)" },
        { action: "alternate_account", note: "try the alternate Claude config dir if configured" },
      ];
    case "too_long":
      return [
        { action: "shrink_to_file", note: "prompt too long — write candidate and records to a temp file and ask the judge to read it" },
        { action: "retry_direct", note: "retry with the shrunk prompt" },
      ];
    case "prose":
      return [
        { action: "extract_from_prose", note: "the model answered in prose — ask a second, JSON-only call to extract the decision from it" },
        { action: "json_only_reask", note: "re-ask the original question demanding JSON only" },
      ];
    case "malformed":
      return [
        { action: "repair_json", note: "JSON-like answer with faults — repair fences/trailing commas/quotes and re-parse" },
        { action: "json_only_reask", note: "re-ask demanding strict JSON" },
      ];
    case "auth":
      return [
        { action: "alternate_account", note: "authentication problem — try the alternate Claude config dir if configured" },
        { action: "retry_backoff", note: "retry after backoff in case the login was mid-refresh" },
      ];
  }
}

/** The prompt for the extract-from-prose call: turn a prose answer into the JSON verdict. */
export function extractionPrompt(prose: string): string {
  return `A reviewer wrote the following answer in prose instead of JSON. Convert it FAITHFULLY into the required JSON and output ONLY the JSON, nothing else. If the prose names any problem, defect, risk, or violation, the decision is "deny" and each problem is a finding. If it clearly says the change is acceptable with no problems, the decision is "allow" with an empty findings array. Do not add problems the prose did not raise.

Required shape:
{"decision":"allow"|"deny","findings":[{"severity":"critical|high|medium|low","lens":"PSC"|"PFC","checklist":"<3.x.y or Qn or PFC-a..e>","where":"<file:line or symbol>","what":"<one sentence>","root_cause":"<one sentence>","fix_hint":"<one sentence>"}],"history_assessment":{"stuck":false,"recommended_rung":1,"why":""}}

--- THE PROSE ---
${prose.slice(0, 20000)}
--- END ---`;
}

/** The final, named denial when every recovery failed. Never an allow. */
export function finalDenial(cls: FailureClass, lastError: string, attempts: string[]): Verdict {
  return {
    decision: "deny",
    findings: [],
    history_assessment: { stuck: false, recommended_rung: 1, why: "" },
    reason: `Nemesis could not obtain a readable verdict. Cause class: ${cls}. Last error: ${lastError.slice(0, 300)}. Recovery tried: ${attempts.join(" → ") || "(none)"}. Nemesis allows nothing it has not judged; fix the cause (see ~/.acos/nemesis/daemon.log) and retry the edit.`,
  };
}
