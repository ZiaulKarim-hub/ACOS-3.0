#!/usr/bin/env bun
/**
 * build-rulebook.ts — generate rulebook/rulebook.json FROM rulebook/SECURITY-PROTOCOL.md.
 *
 * R-003 (D-30, D-06): the protocol has ONE source of truth. This file parses the markdown
 * into the machine-readable rulebook the judge charter, the step ledger, and the checklist
 * validator read. rulebook.json is never hand-edited: it records `source_sha256` and
 * `nemesis selftest` fails when that hash no longer matches the markdown.
 *
 *   bun build-rulebook.ts [--check]      (--check: exit 1 if the JSON is stale)
 */
import * as fs from "node:fs";
import * as path from "node:path";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
export const RULEBOOK_DIR = path.resolve(HERE, "..", "rulebook");
export const SOURCE_MD = path.join(RULEBOOK_DIR, "SECURITY-PROTOCOL.md");
export const RULEBOOK_JSON = path.join(RULEBOOK_DIR, "rulebook.json");

export interface Checklist { id: string; title: string; items: { id: string; text: string }[] }
export interface Step { id: string; title: string; body: string[]; bullets: string[] }
export interface Rulebook {
  schema: "nemesis-rulebook/1";
  source: string;
  source_sha256: string;
  generated_at: string;
  rule_zero: string;
  principles: { n: number; title: string; text: string }[];
  steps: Step[];
  twelve_questions: string[];
  severity: { level: string; meaning: string; rule: string }[];
  checklists: Checklist[];
  templates: Record<string, string>;
  short_version: string[];
}

function sha256(s: string | Buffer): string { return createHash("sha256").update(s).digest("hex"); }

/** Join wrapped markdown bullet lines ("- text\n  continued") into single items. */
function collectBullets(lines: string[]): string[] {
  const out: string[] = [];
  for (const raw of lines) {
    const line = raw.replace(/\s+$/, "");
    if (/^\s*[-*]\s+/.test(line)) out.push(line.replace(/^\s*[-*]\s+/, "").trim());
    else if (/^\s{2,}\S/.test(line) && out.length) out[out.length - 1] += " " + line.trim();
  }
  return out.map((s) => s.replace(/\*\*/g, "").replace(/`/g, ""));
}

function collectNumbered(lines: string[]): string[] {
  const out: string[] = [];
  for (const raw of lines) {
    const line = raw.replace(/\s+$/, "");
    const m = line.match(/^\s*(\d+)\.\s+(.*)$/);
    if (m) out.push(m[2]!.trim());
    else if (/^\s{2,}\S/.test(line) && out.length) out[out.length - 1] += " " + line.trim();
  }
  return out.map((s) => s.replace(/\*\*/g, "").replace(/`/g, ""));
}

/** Split the markdown into sections keyed by heading text, preserving order. */
function sections(md: string): { level: number; title: string; lines: string[] }[] {
  const out: { level: number; title: string; lines: string[] }[] = [];
  let cur: { level: number; title: string; lines: string[] } | null = null;
  for (const line of md.split("\n")) {
    const h = line.match(/^(#{1,6})\s+(.*)$/);
    if (h) { cur = { level: h[1]!.length, title: h[2]!.trim(), lines: [] }; out.push(cur); }
    else if (cur) cur.lines.push(line);
  }
  return out;
}

export function buildRulebook(md: string): Rulebook {
  const secs = sections(md);
  const find = (re: RegExp) => secs.find((s) => re.test(s.title));
  const between = (startRe: RegExp, level: number) => {
    const i = secs.findIndex((s) => startRe.test(s.title));
    if (i < 0) return [] as typeof secs;
    const out: typeof secs = [];
    for (let j = i + 1; j < secs.length && secs[j]!.level > level; j++) out.push(secs[j]!);
    return out;
  };

  // Rule zero lives in the preamble under the H1.
  const h1 = secs.find((s) => s.level === 1);
  const ruleZero = (h1?.lines.join("\n").match(/\*\*Rule zero\.\*\*([\s\S]*?)\n\n/)?.[1] ?? "").replace(/^>\s?/gm, "").replace(/\s+/g, " ").trim();

  // Part 1 — principles (numbered, bold title then text)
  const p1 = find(/^Part 1/);
  const principles = collectNumbered(p1?.lines ?? []).map((t, i) => {
    const m = t.match(/^(.*?\.)\s+(.*)$/);
    return { n: i + 1, title: (m?.[1] ?? t).trim(), text: (m?.[2] ?? "").trim() };
  });

  // Part 2 — steps S0..S8
  const stepSecs = between(/^Part 2/, 2).filter((s) => /^S\d\./.test(s.title));
  const steps: Step[] = stepSecs.map((s) => {
    const id = s.title.match(/^(S\d)/)![1]!;
    const title = s.title.replace(/^S\d\.\s*/, "").trim();
    const body = s.lines.filter((l) => l.trim() && !/^\s*[-*]\s+/.test(l) && !/^\s{2,}\S/.test(l) && !/^```/.test(l)).map((l) => l.replace(/\*\*/g, "").trim());
    return { id, title, body, bullets: collectBullets(s.lines) };
  });

  // The twelve questions are the numbered list inside S2.
  const s2 = stepSecs.find((s) => s.title.startsWith("S2"));
  const twelve = collectNumbered(s2?.lines ?? []);

  // Severity table
  const sev = find(/^Severity/);
  const severity = (sev?.lines ?? [])
    .filter((l) => /^\|/.test(l) && !/^\|\s*Level/.test(l) && !/^\|\s*-/.test(l))
    .map((l) => l.split("|").slice(1, -1).map((c) => c.trim().replace(/\*\*/g, "")))
    .filter((c) => c.length >= 3)
    .map((c) => ({ level: c[0]!, meaning: c[1]!, rule: c[2]! }));

  // Part 3 — checklists 3.1 .. 3.14
  const checklists: Checklist[] = between(/^Part 3/, 2)
    .filter((s) => /^3\.\d+/.test(s.title))
    .map((s) => {
      const id = s.title.match(/^(3\.\d+)/)![1]!;
      const title = s.title.replace(/^3\.\d+\s*/, "").trim();
      const items = collectBullets(s.lines).map((text, i) => ({ id: `${id}.${i + 1}`, text }));
      return { id, title, items };
    });

  // Part 4 — record templates (code blocks)
  const templates: Record<string, string> = {};
  for (const s of between(/^Part 4/, 2)) {
    const key = s.title.match(/^4\.(\d)/)?.[1];
    const block = s.lines.join("\n").match(/```(?:yaml)?\n([\s\S]*?)```/)?.[1];
    if (key && block) templates[{ "1": "threat_sketch", "2": "design_review", "3": "security_issue", "4": "check_record" }[key] ?? key] = block.trimEnd();
  }

  // Part 6 — the short version
  const p6 = find(/^Part 6/);
  const shortVersion = collectNumbered(p6?.lines ?? []).concat(collectBullets(p6?.lines ?? []));

  return {
    schema: "nemesis-rulebook/1",
    source: "OKOA Investor Portal design/security/SECURITY-PROTOCOL.md (byte copy in rulebook/)",
    source_sha256: sha256(md),
    generated_at: new Date().toISOString(),
    rule_zero: ruleZero,
    principles,
    steps,
    twelve_questions: twelve,
    severity,
    checklists,
    templates,
    short_version: shortVersion,
  };
}

export function rulebookIsFresh(): { fresh: boolean; why: string } {
  if (!fs.existsSync(RULEBOOK_JSON)) return { fresh: false, why: "rulebook.json missing" };
  try {
    const j = JSON.parse(fs.readFileSync(RULEBOOK_JSON, "utf8")) as Rulebook;
    const want = sha256(fs.readFileSync(SOURCE_MD));
    return j.source_sha256 === want ? { fresh: true, why: "source_sha256 matches" } : { fresh: false, why: `source_sha256 ${j.source_sha256.slice(0, 12)} != ${want.slice(0, 12)}` };
  } catch (e) { return { fresh: false, why: `unreadable: ${String(e)}` }; }
}

if (import.meta.main) {
  const check = process.argv.includes("--check");
  if (check) {
    const r = rulebookIsFresh();
    console.log(`rulebook ${r.fresh ? "fresh" : "STALE"}: ${r.why}`);
    process.exit(r.fresh ? 0 : 1);
  }
  const md = fs.readFileSync(SOURCE_MD, "utf8");
  const rb = buildRulebook(md);
  const problems: string[] = [];
  if (rb.principles.length !== 12) problems.push(`principles ${rb.principles.length} != 12`);
  if (rb.steps.length !== 9) problems.push(`steps ${rb.steps.length} != 9`);
  if (rb.twelve_questions.length !== 12) problems.push(`questions ${rb.twelve_questions.length} != 12`);
  if (rb.severity.length !== 4) problems.push(`severity rows ${rb.severity.length} != 4`);
  if (rb.checklists.length !== 14) problems.push(`checklists ${rb.checklists.length} != 14`);
  if (Object.keys(rb.templates).length !== 4) problems.push(`templates ${Object.keys(rb.templates).length} != 4`);
  if (problems.length) { console.error("build-rulebook: parse problems:\n  " + problems.join("\n  ")); process.exit(1); }
  fs.writeFileSync(RULEBOOK_JSON, JSON.stringify(rb, null, 2) + "\n");
  console.log(`rulebook.json written: ${rb.principles.length} principles, ${rb.steps.length} steps, ${rb.twelve_questions.length} questions, ${rb.severity.length} severities, ${rb.checklists.length} checklists (${rb.checklists.reduce((n, c) => n + c.items.length, 0)} items), ${Object.keys(rb.templates).length} templates; source_sha256 ${rb.source_sha256.slice(0, 16)}…`);
}
