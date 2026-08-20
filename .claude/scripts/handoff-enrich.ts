#!/usr/bin/env bun
// ─────────────────────────────────────────────────────────────────────────────
// handoff-enrich.ts — puts the DEPTH back into an auto-compaction handoff.
//
// WHY THIS EXISTS (2026-08-13, at Zee's direction)
// ------------------------------------------------
// Moving the Eternity Protocol onto Claude Code's native auto-compaction fixed
// the swallowed-keystroke failure, but it cost something real. The old handoff
// was written by `handoff-agent` — a model that read the whole conversation and
// produced judgement: current_work, completed_this_session, decisions_made,
// candidate_learnings, blockers, context_for_next_session.
//
// A PreCompact hook cannot do that. It is a script in a frozen pane with an
// 8-second ceiling; it can record facts, not form opinions. So precompact-
// handoff.ts writes the facts and stamps `enrichment_status: "pending"`.
// This file is what clears that stamp, in two passes.
//
// PASS 1 — PostCompact  (mechanical, no model call, always runs)
//   Claude Code hands a PostCompact hook the finished summary in a
//   `compact_summary` field (verified in the 2.1.229 binary:
//   `{hook_event_name:"PostCompact", trigger, compact_summary}`). That summary
//   IS the model-written narrative, produced with the whole conversation in
//   view. Pasting it into the handoff restores the narrative for free — no
//   second model call, no frozen pane, no nested session.
//   -> enrichment_status: "summary-written"
//
// PASS 2 — SessionStart(compact)  (best-effort, asks the live session)
//   A summary is prose. The old handoff also carried STRUCTURED judgement, and
//   prose does not reliably answer "what is blocked" or "what did the user
//   decide". Only SessionStart and UserPromptSubmit can inject `additionalContext`
//   (PostCompact cannot — its stdout only becomes a display message), so this
//   pass asks the just-resumed session to append those fields itself. It costs
//   one small edit and no extra process.
//   -> enrichment_status: "deepened"  (written by the session, not by this file)
//
// FAILURE POSTURE: identical to the PreCompact hook. Always exit 0, never write
// to stderr, never block. A handoff that stops at "pending" or "summary-written"
// is degraded, never broken — every mechanical fact in it is still true.
//
// Language note: TypeScript per the standing default. Run by bun.
// ─────────────────────────────────────────────────────────────────────────────

import { appendFileSync, existsSync, readFileSync, readdirSync, renameSync, statSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const HARD_LIMIT_MS = 6_000;
/** Don't touch a handoff from an older cycle — only the one this compaction wrote. */
const MAX_HANDOFF_AGE_MS = 30 * 60 * 1000;

interface HookInput {
  session_id?: string;
  transcript_path?: string;
  cwd?: string;
  hook_event_name?: string;
  trigger?: string;
  source?: string;
  compact_summary?: string;
}

function readStdin(): string {
  try {
    const { readSync } = require("node:fs");
    const chunks: Buffer[] = [];
    const buf = Buffer.allocUnsafe(65536);
    let total = 0;
    for (;;) {
      let n = 0;
      try { n = readSync(0, buf, 0, buf.length, null); } catch { break; }
      if (n <= 0) break;
      chunks.push(Buffer.from(buf.subarray(0, n)));
      total += n;
      if (total > 8 * 1024 * 1024) break;
    }
    return Buffer.concat(chunks).toString("utf8");
  } catch {
    return "";
  }
}

/** YAML block scalar body: indent every line, strip CRs, never emit nothing. */
function yblock(s: string, indent = 2): string {
  const pad = " ".repeat(indent);
  const body = String(s ?? "").replace(/\r/g, "").replace(/\t/g, "  ").trimEnd();
  if (!body) return `${pad}(empty)`;
  return body.split("\n").map((l) => pad + l).join("\n");
}

/**
 * The handoff THIS session's PreCompact hook just wrote. Matched on session_id,
 * not on "newest file" — several Claude sessions work this repo at once, and
 * newest-wins is exactly how a session got handed someone else's handoff before
 * (see resolve-session-handoff.sh's header for that incident).
 */
function findHandoff(cwd: string, sessionId: string, wantStatus: string[]): string | null {
  const dir = join(cwd, "memory", "handoffs");
  if (!existsSync(dir)) return null;
  let best: { path: string; mtime: number } | null = null;
  const now = Date.now();
  for (const f of readdirSync(dir)) {
    if (!f.endsWith(".yaml")) continue;
    const p = join(dir, f);
    let text = "", mtime = 0;
    try {
      mtime = statSync(p).mtimeMs;
      if (now - mtime > MAX_HANDOFF_AGE_MS) continue;
      text = readFileSync(p, "utf8");
    } catch { continue; }
    const sid = text.match(/^session_id:\s*"?([^"\s]+)"?/m)?.[1];
    if (sid !== sessionId) continue;
    const st = text.match(/^enrichment_status:\s*"?([^"\s]+)"?/m)?.[1];
    if (!st || !wantStatus.includes(st)) continue;
    if (!best || mtime > best.mtime) best = { path: p, mtime };
  }
  return best?.path ?? null;
}

function writeAtomic(path: string, text: string): boolean {
  try {
    const tmp = path + ".tmp";
    writeFileSync(tmp, text, "utf8");
    renameSync(tmp, path);
    return true;
  } catch {
    return false;
  }
}

// ── Summary health check ────────────────────────────────────────────────────

/**
 * A compaction summary can come back REFUSED, and today that is silent.
 *
 * Proven on 2026-08-13 with a control run: a headless session, given Claude
 * Code's OWN built-in summary prompt and no hook instructions whatsoever,
 * replied "your last message had some odd extra text mixed in... so I didn't"
 * and never wrote a summary. The model was defending against what looked like
 * an injection. Whatever the cause, the effect is the same and it is the worst
 * outcome this whole system can produce: compaction proceeds, the conversation
 * is replaced by a refusal, and the context is gone with no warning.
 *
 * This cannot be prevented from a hook. It CAN be made loud. Detection is
 * deliberately conservative — it only flags, never blocks, never rewrites —
 * and a false positive costs one extra YAML field, which is cheap next to a
 * silently lost session.
 */
const REFUSAL_MARKERS: Array<[RegExp, string]> = [
  [/hidden command/i,                    "called the summary request a hidden command"],
  [/prompt.?injection/i,                 "named it a prompt injection"],
  [/treating it as untrustworthy/i,      "declared the request untrustworthy"],
  [/extra text (that |which )?(looked|tried)/i, "objected to 'extra text'"],
  [/(did ?n[o']t|do ?n[o']t|won[o']t|not) (follow|following) (it|that|these)/i, "refused to follow the request"],
  [/i[' ]?m not doing that/i,            "said it would not do it"],
  [/did ?n[o']t match anything you/i,    "said the request did not match the conversation"],
  [/odd extra text/i,                    "objected to 'odd extra text'"],
];

function summaryHealth(summary: string): { quality: string; reason: string } {
  for (const [re, why] of REFUSAL_MARKERS) {
    if (re.test(summary)) return { quality: "suspect", reason: `the summariser ${why}` };
  }
  if (summary.trim().length < 200) {
    return { quality: "suspect", reason: "the summary is implausibly short for a full context window" };
  }
  return { quality: "ok", reason: "" };
}

// ── PASS 1: paste the real compaction summary into the handoff ──────────────

function passPostCompact(input: HookInput, cwd: string): void {
  const sid = input.session_id ?? "";
  const summary = (input.compact_summary ?? "").trim();
  if (!sid || !summary) return;

  const path = findHandoff(cwd, sid, ["pending"]);
  if (!path) return;

  let text: string;
  try { text = readFileSync(path, "utf8"); } catch { return; }

  const health = summaryHealth(summary);

  const updated = text.replace(/^enrichment_status:.*$/m, 'enrichment_status: "summary-written"')
    + `
# ── The model-written narrative ──────────────────────────────────────────────
# This is the ACTUAL compaction summary Claude Code produced, handed to the
# PostCompact hook verbatim in its \`compact_summary\` field. It replaces what
# handoff-agent used to write, and it is strictly better sourced: it was made
# with the whole conversation in context, not from a transcript tail.
#
# summary_quality is a HEURISTIC, not a verdict. "suspect" means the text looks
# like a refusal rather than a summary — the one failure that would otherwise
# lose a whole session silently. When it says suspect, the mechanical fields
# above are the trustworthy record, and the raw transcript named in
# reconstruction_sources is the fallback.
summary_quality: ${JSON.stringify(health.quality)}
${health.reason ? `summary_quality_reason: ${JSON.stringify(health.reason)}\n` : ""}compaction_summary: |
${yblock(summary)}
`;

  if (!writeAtomic(path, updated)) return;

  // Make it visible outside the file too. The eternity subsystem already reads
  // this alert log, and a lost summary is exactly what it exists to surface.
  if (health.quality === "suspect") {
    try {
      const alert = join(process.env.HOME ?? "", "Library", "Application Support",
                         "acos-token-monitor", "state", ".eternity-ALERT");
      appendFileSync(alert,
        `${new Date().toISOString()} SUSPECT COMPACTION SUMMARY session=${sid} — ` +
        `${health.reason}. Handoff: ${path}\n`);
    } catch { /* never let alerting break the hook */ }
  }
}

// ── PASS 2: ask the resumed session for the structured judgement ────────────

function passSessionStart(input: HookInput, cwd: string): void {
  if ((input.source ?? "") !== "compact") return;   // only after a compaction
  const sid = input.session_id ?? "";
  if (!sid) return;

  // "pending" is included on purpose: if PostCompact somehow did not run, the
  // session can still supply the narrative, which is the whole point.
  const path = findHandoff(cwd, sid, ["pending", "summary-written"]);
  if (!path) return;

  const ctx = [
    `ACOS handoff depth pass. This session was just auto-compacted. The handoff at`,
    `\`${path}\` has the mechanical facts and the compaction summary, but not the`,
    `structured judgement the old handoff-agent used to write.`,
    ``,
    `BEFORE continuing your work, make ONE edit to that file: append the fields`,
    `below, then set enrichment_status to "deepened". Keep it short — a few lines`,
    `each, drawn only from what you actually know right now. Write "(none)" where`,
    `you genuinely have nothing; never invent an entry to fill a field.`,
    ``,
    `  current_work            — what is being worked on this moment, one or two lines`,
    `  completed_this_session  — what is verified DONE, not merely proposed`,
    `  decisions_made          — what the user decided, in their terms, including`,
    `                            decisions they made by rejecting something`,
    `  blockers                — what is genuinely stuck, and on what`,
    `  candidate_learnings     — anything worth remembering beyond this session`,
    `  context_for_next_session — what a fresh reader would most need to know`,
    ``,
    `Then continue the prior work. Do not report this edit to the user as if it`,
    `were the task; it is bookkeeping. One tool call, then carry on.`,
    ``,
    // This continuation framing lives HERE and not in the PreCompact hook's
    // summary instructions, and the reason is load-bearing. additionalContext
    // is a properly tagged channel — the model knows it came from a hook. The
    // summary-instructions slot is plain untagged prose, so the same words
    // there read as an injection attempt and get refused (this happened twice
    // live on 2026-08-13; see precompact-handoff.ts's buildInstructions).
    `Context for continuing: this compaction was triggered automatically when the`,
    `conversation crossed its token threshold. The user did not ask for it and is`,
    `not waiting to re-explain anything — they are waiting on the work that was`,
    `already underway.`,
  ].join("\n");

  process.stdout.write(JSON.stringify({
    hookSpecificOutput: { hookEventName: "SessionStart", additionalContext: ctx },
  }));
}

// ── main ────────────────────────────────────────────────────────────────────

function main(): void {
  const watchdog = setTimeout(() => process.exit(0), HARD_LIMIT_MS);
  try {
    const raw = readStdin();
    const input: HookInput = raw ? JSON.parse(raw) : {};
    const cwd = input.cwd && existsSync(input.cwd) ? input.cwd : process.cwd();

    switch (input.hook_event_name) {
      case "PostCompact":  passPostCompact(input, cwd); break;
      case "SessionStart": passSessionStart(input, cwd); break;
      default: break;   // wired to the wrong event — do nothing, quietly
    }
  } catch {
    // Silent by design: stderr from a hook surfaces to the user as a failure,
    // and enrichment failing is never worth interrupting them over.
  }
  clearTimeout(watchdog);
  process.exit(0);
}

main();
