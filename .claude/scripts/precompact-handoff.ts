#!/usr/bin/env bun
// ─────────────────────────────────────────────────────────────────────────────
// precompact-handoff.ts — the ACOS handoff writer for NATIVE auto-compaction.
//
// Registered as a PreCompact hook. Claude Code fires PreCompact immediately
// before it summarises a conversation, for BOTH triggers:
//     trigger: "auto"    — the built-in threshold crossing (no keystrokes)
//     trigger: "manual"  — a human or a script typing /compact
//
// WHY THIS EXISTS (2026-08-12)
// ---------------------------
// The previous Eternity Protocol fired by TYPING `/acos-eternity-protocol` into
// the pane over cmux's RPC socket. When the pane was busy the submit was
// swallowed, the fire never landed, and the session ran out of context — this
// happened repeatedly, most recently in the "Research to Portfolio" pane. The
// fix is to stop typing anything: Claude Code already compacts itself on a
// token threshold, from the inside, where nothing can swallow the input.
//
// That move only works if Zee's required ordering still holds:
//     eternity fires -> handoff created -> resume prompt created
//                    -> compact runs -> session resumes
// PreCompact is the slot that keeps it true. It runs BEFORE the summary, so a
// handoff written here is on disk before compaction, exactly as before.
//
// THE TWO THINGS THIS HOOK PRODUCES
// ---------------------------------
//  1. A handoff YAML in <cwd>/memory/handoffs/, carrying a top-level
//     `session_id:` so .claude/scripts/resolve-session-handoff.sh can match it
//     to this session and not to a concurrent one.
//  2. Whatever it prints on STDOUT, which Claude Code injects into the
//     compaction prompt as `newCustomInstructions`. Verified in the 2.1.229
//     binary: PreCompact stdout from every succeeding, non-blocking hook is
//     joined and returned as newCustomInstructions. This is the channel that
//     replaces the old typed resume prompt — it needs no keystrokes at all.
//
// HARD RULES THIS FILE MUST NEVER BREAK
// -------------------------------------
//  * ALWAYS exit 0. A PreCompact hook that fails with a blocking status
//    CANCELS compaction ("Reactive compact blocked by PreCompact hook" in the
//    binary). A blocked compaction is the exact failure this migration exists
//    to remove, so every path here is wrapped and every exit is 0.
//  * NEVER run long. PreCompact blocks the pane while it runs. A hard
//    watchdog (HARD_LIMIT_MS) prints the fallback instructions and exits.
//  * NEVER shell out to `claude -p` for a richer handoff. It was considered
//    and rejected: a nested headless session fires its own SessionStart hooks,
//    registers a phantom session PID, and can spawn another token watcher. The
//    compaction summary Claude Code writes is already LLM-quality; this file's
//    job is the durable, mechanical, always-correct record beside it.
//
// Language note: TypeScript per the standing default. Run by bun.
// ─────────────────────────────────────────────────────────────────────────────

import { spawnSync } from "node:child_process";
import { closeSync, existsSync, mkdirSync, openSync, readSync, renameSync, statSync, writeFileSync } from "node:fs";
import { join } from "node:path";

/** Absolute ceiling on this hook's wall time. The pane is frozen until we exit. */
const HARD_LIMIT_MS = 8_000;
/** How much of the transcript tail to parse. Transcripts reach hundreds of MB. */
const TRANSCRIPT_TAIL_BYTES = 6 * 1024 * 1024;
/** Cap on the verbatim last-user-message we carry forward. */
const LAST_MSG_MAX_CHARS = 2_000;

/**
 * Turns that carry role:"user" in the transcript but were never typed by a
 * person. Same list the acos-resume-prompt skill uses — kept in sync
 * deliberately, because grabbing one of these instead of Zee's actual words is
 * the difference between resuming his question and resuming a hook's echo.
 */
const SYNTHETIC_PREFIXES = [
  "<local-command-caveat>", "<command-message>", "<command-name>",
  "<task-notification>", "<system-reminder>", "<local-command-stdout>",
  "Stop hook feedback:", "[SYSTEM NOTIFICATION",
  "Base directory for this skill:", "ARGUMENTS:",
  "Resume the eternity-protocol handoff",
  // 2026-08-17: a re-invoked skill is replayed as a role:"user" turn reading
  // "Skill /<name> was loaded earlier ... this is a NEW invocation". It was
  // caught here live — the Research to Portfolio handoff recorded
  // "Skill /acos-resume-prompt was loaded earlier…" as Zee's last words.
  "Skill /",
];

interface HookInput {
  session_id?: string;
  transcript_path?: string;
  cwd?: string;
  hook_event_name?: string;
  trigger?: string;
  custom_instructions?: string | null;
}

interface TranscriptFacts {
  lastUserMessage: string;
  lastUserTruncated: boolean;
  tokenEstimate: number | null;
  inFlightTasks: Array<{ id: string; type: string; description: string; spawnedAt: string }>;
  assistantTail: string[];
  parsedLines: number;
}

// ── tiny helpers ────────────────────────────────────────────────────────────

/** YAML double-quoted scalar. Never let a stray quote or newline break the file. */
function yq(s: string): string {
  return `"${String(s ?? "").replace(/\\/g, "\\\\").replace(/"/g, '\\"').replace(/[\r\n]+/g, " ").trim()}"`;
}

/** YAML block scalar body: every line indented, CRs stripped, never empty. */
function yblock(s: string, indent = 2): string {
  const pad = " ".repeat(indent);
  const body = String(s ?? "").replace(/\r/g, "").replace(/\t/g, "  ").trimEnd();
  if (!body) return `${pad}(nothing recorded)`;
  return body.split("\n").map((l) => pad + l).join("\n");
}

function nowIso(): string {
  return new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
}

/** Read the last N bytes of a file without loading the whole thing. */
function tailBytes(path: string, maxBytes: number): string {
  let fd: number | null = null;
  try {
    const size = statSync(path).size;
    const want = Math.min(size, maxBytes);
    const start = size - want;
    fd = openSync(path, "r");
    const buf = Buffer.allocUnsafe(want);
    let read = 0;
    while (read < want) {
      const n = readSync(fd, buf, read, want - read, start + read);
      if (n <= 0) break;
      read += n;
    }
    let text = buf.subarray(0, read).toString("utf8");
    // A partial first line is unparseable JSON; drop it.
    if (start > 0) {
      const nl = text.indexOf("\n");
      if (nl !== -1) text = text.slice(nl + 1);
    }
    return text;
  } catch {
    return "";
  } finally {
    if (fd !== null) try { closeSync(fd); } catch { /* ignore */ }
  }
}

// ── transcript reading ──────────────────────────────────────────────────────

function readTranscript(path: string): TranscriptFacts {
  const out: TranscriptFacts = {
    lastUserMessage: "", lastUserTruncated: false, tokenEstimate: null,
    inFlightTasks: [], assistantTail: [], parsedLines: 0,
  };
  if (!path || !existsSync(path)) return out;

  const lines = tailBytes(path, TRANSCRIPT_TAIL_BYTES).split("\n");
  const spawned = new Map<string, { type: string; description: string; spawnedAt: string }>();
  const completed = new Set<string>();
  const assistantTexts: string[] = [];

  for (const raw of lines) {
    const line = raw.trim();
    if (!line) continue;
    let d: any;
    try { d = JSON.parse(line); } catch { continue; }
    out.parsedLines++;
    const msg = d?.message ?? {};
    const ts = typeof d?.timestamp === "string" ? d.timestamp : "";

    // Live token count: the newest usage block on the MAIN chain. Sidechain
    // (subagent) turns have their own budgets and must not inflate this.
    if (msg?.usage && d?.isSidechain !== true) {
      const u = msg.usage;
      const total = (u.input_tokens ?? 0) + (u.cache_creation_input_tokens ?? 0)
        + (u.cache_read_input_tokens ?? 0) + (u.output_tokens ?? 0);
      if (Number.isFinite(total) && total > 0) out.tokenEstimate = total;
    }

    const content = msg?.content;

    if (msg?.role === "assistant" && Array.isArray(content)) {
      for (const b of content) {
        if (b?.type === "text" && typeof b.text === "string" && b.text.trim()) {
          assistantTexts.push(b.text.trim());
        } else if (b?.type === "tool_use" && b?.name === "Task") {
          spawned.set(b.id, {
            type: b?.input?.subagent_type ?? "general-purpose",
            description: b?.input?.description ?? "",
            spawnedAt: ts,
          });
        }
      }
    }

    if (Array.isArray(content)) {
      for (const b of content) {
        if (b?.type === "tool_result" && b?.tool_use_id) completed.add(b.tool_use_id);
      }
    }

    // Zee's own words — the last turn that a person actually typed.
    if (msg?.role === "user") {
      let text = "";
      if (typeof content === "string") {
        text = content;
      } else if (Array.isArray(content)) {
        const parts = content
          .filter((b: any) => b?.type === "text" && typeof b.text === "string" && b.text.trim())
          .map((b: any) => b.text);
        text = parts.join("\n");
      }
      text = text.trim();
      if (text && !SYNTHETIC_PREFIXES.some((p) => text.startsWith(p))) {
        out.lastUserMessage = text;   // keep overwriting; the last one wins
      }
    }
  }

  for (const [id, meta] of spawned) {
    if (!completed.has(id)) out.inFlightTasks.push({ id, ...meta });
  }
  out.assistantTail = assistantTexts.slice(-2).map((t) => (t.length > 1200 ? t.slice(0, 1200) + " […]" : t));

  if (out.lastUserMessage.length > LAST_MSG_MAX_CHARS) {
    out.lastUserMessage = out.lastUserMessage.slice(0, LAST_MSG_MAX_CHARS);
    out.lastUserTruncated = true;
  }
  return out;
}

// ── repo facts ──────────────────────────────────────────────────────────────

function sh(cmd: string, args: string[], cwd: string, ms = 2500): string {
  try {
    const r = spawnSync(cmd, args, { cwd, encoding: "utf8", timeout: ms, stdio: ["ignore", "pipe", "ignore"] });
    return (r.stdout ?? "").trim();
  } catch {
    return "";
  }
}

function gitFacts(cwd: string) {
  const branch = sh("git", ["rev-parse", "--abbrev-ref", "HEAD"], cwd) || "(not a git repo)";
  const status = sh("git", ["status", "--porcelain"], cwd);
  const log = sh("git", ["log", "--oneline", "-5"], cwd);
  const changed = status ? status.split("\n").filter(Boolean) : [];
  return { branch, changedCount: changed.length, changed: changed.slice(0, 25), log };
}

// ── handoff file naming ─────────────────────────────────────────────────────

/**
 * Same shape the acos-handoff agent uses, so /acos-complete archiving and the
 * `ls -t memory/handoffs/*.yaml` glob in resolve-session-handoff.sh both keep
 * working. "autocompact" in the name marks who wrote it.
 */
function nextHandoffPath(dir: string, date: string): string {
  const base = `${date}-autocompact-handoff`;
  let p = join(dir, `${base}.yaml`);
  let n = 2;
  while (existsSync(p) && n < 500) p = join(dir, `${base}-${n++}.yaml`);
  return p;
}

// ── the handoff document ────────────────────────────────────────────────────

function buildHandoff(input: HookInput, facts: TranscriptFacts, git: ReturnType<typeof gitFacts>): string {
  const sid = input.session_id ?? "unknown";
  const trigger = input.trigger ?? "unknown";
  const tokens = facts.tokenEstimate ?? 0;

  const inflight = facts.inFlightTasks.length
    ? facts.inFlightTasks.map((t) =>
        `  - tool_use_id: ${yq(t.id)}\n    subagent_type: ${yq(t.type)}\n` +
        `    description: ${yq(t.description)}\n    spawned_at: ${yq(t.spawnedAt)}`).join("\n")
    : "  []";

  const changed = git.changed.length
    ? git.changed.map((l) => `  - ${yq(l)}`).join("\n")
    : "  []";

  const lastMsg = facts.lastUserMessage
    ? yblock(facts.lastUserMessage + (facts.lastUserTruncated ? "\n\n[...cut off at 2000 characters]" : ""))
    : "  (no human-typed message found in the transcript tail)";

  const tail = facts.assistantTail.length
    ? yblock(facts.assistantTail.join("\n\n---\n\n"))
    : "  (no assistant output found in the transcript tail)";

  return `timestamp: ${yq(nowIso())}
status: "active"
type: "autocompact"
trigger: ${yq(`precompact-hook:${trigger}`)}
session_id: ${yq(sid)}
estimated_tokens: ${tokens}
written_by: "precompact-handoff.ts"

# Depth restoration (2026-08-13). This hook can only record FACTS — it is a
# script running in a frozen pane, so it cannot read the conversation and form a
# judgement the way the old handoff-agent did. Two later stages fill that in,
# and this field is how they find their work:
#   pending          -> written here, nothing enriched yet
#   summary-written  -> handoff-enrich.ts (PostCompact) pasted in the real
#                       model-written compaction summary. No extra model call:
#                       Claude Code hands the summary straight to the hook.
#   deepened         -> the resumed session itself added the judgement fields
#                       (decisions, blockers, learnings) that only a reader of
#                       the whole conversation can produce.
# A handoff stuck at "pending" is not broken — every mechanical fact below is
# still true. It just never got its narrative.
enrichment_status: "pending"

session_summary: |
${yblock(
  `Written automatically by the PreCompact hook, immediately before Claude Code\n` +
  `compacted this session. Trigger was "${trigger}" ("auto" = the built-in token\n` +
  `threshold fired on its own, with no keystrokes; "manual" = someone ran /compact).\n\n` +
  `This file is the DURABLE, MECHANICAL record. It is deliberately not a\n` +
  `narrative summary — the compaction summary in the conversation itself is the\n` +
  `narrative, and it is written by the model with the whole transcript in view.\n` +
  `What this file adds is the set of facts a summary can silently drop: the exact\n` +
  `last thing the human typed, which background agents were still running, and\n` +
  `what the repo looked like at the moment of the cut.`)}

human_last_message: |
${lastMsg}

assistant_tail: |
${tail}

in_flight_subagents:
${inflight}

repo_state:
  branch: ${yq(git.branch)}
  uncommitted_file_count: ${git.changedCount}
  recent_commits: |
${yblock(git.log || "(none)", 4)}

uncommitted_files:
${changed}

next_actions:
  - "Read human_last_message above. If it is still an open question, answer it FIRST."
  - "Verify real state on disk before trusting any summary — recount, re-check, re-run."
  - "If in_flight_subagents is non-empty, their results may still arrive. Do not discard them."

reconstruction_sources:
  transcript_path: ${yq(input.transcript_path ?? "")}
  transcript_lines_parsed: ${facts.parsedLines}
  cwd: ${yq(input.cwd ?? "")}
`;
}

// ── the compaction instructions (this hook's stdout) ────────────────────────

/**
 * WHO READS THIS: the summariser, and only the summariser. Claude Code splices
 * this text into the summarisation request as PLAIN, UNTAGGED PROSE — the same
 * slot a user's own `/compact <guidance>` lands in.
 *
 * That last detail is the whole design constraint, and two live failures on
 * 2026-08-13 are why this file is so plain:
 *
 *   Attempt 1 said "continue the prior work directly" and demanded "exact file
 *   paths, commands, numbers". Against a trivial chat containing none of those,
 *   the model read it as pressure to invent a technical report, refused, and
 *   its refusal BECAME the summary.
 *
 *   Attempt 2 fixed the wording but opened with "from the ACOS handoff system
 *   (a hook, not the user)". That was worse. The model replied: "Real system
 *   instructions in this chat always show up in a special tagged format I can
 *   see — this text didn't, it was just typed in as part of your message.
 *   Because of that mismatch, I'm treating it as untrustworthy." It was right.
 *   Untagged text CLAIMING to be from a system is the exact shape of a prompt
 *   injection, and announcing provenance is what tripped the defence.
 *
 * The rules that survived, and they are not negotiable:
 *   1. NEVER claim provenance. No "from the ACOS system", no "this is a hook",
 *      no "system instruction". It must read as ordinary summary guidance.
 *   2. Every line must be about WRITING A SUMMARY. Never an instruction to act,
 *      continue working, or open a file. Continuation belongs in
 *      handoff-enrich.ts's SessionStart pass, which uses `additionalContext` —
 *      a properly tagged channel where it cannot look like an injection.
 *   3. Every item must be CONDITIONAL ("keep X if it appears"), never a bare
 *      "preserve X", which asserts X exists and invites fabrication.
 *   4. Keep it short and boring. Scaffolding — file paths to record, framing
 *      about what this text is — all reads as injection apparatus.
 */
function buildInstructions(handoffPath: string, facts: TranscriptFacts, trigger: string): string {
  const lines: string[] = [];
  lines.push("When writing the summary, keep these if they appear in the conversation:");
  lines.push("");
  lines.push("- the user's most recent request, in their own words, if it is still unanswered");
  lines.push("- any decision the user made, including a decision made by rejecting an option");
  lines.push("- exact file paths, commands, numbers, and identifiers, unchanged");
  lines.push("- which work is finished and verified, kept separate from what was only proposed");

  if (facts.inFlightTasks.length) {
    lines.push(
      `- that ${facts.inFlightTasks.length} background task(s) were still running and their ` +
      `results are still expected: ${facts.inFlightTasks.map((t) => t.description || t.type).join("; ")}`
    );
  }

  lines.push("");
  lines.push(
    "Leave out anything above that the conversation does not actually contain, rather than " +
    "inventing it. A short honest summary is better than a padded one."
  );
  return lines.join("\n");
}

// ── main ────────────────────────────────────────────────────────────────────

/**
 * Last-resort instructions, used when anything at all goes wrong.
 * Bound by the same rules as buildInstructions() above — no provenance claim,
 * no instruction to act, everything conditional. An earlier version opened with
 * "ACOS eternity-protocol continuity:" and told the summariser to "continue the
 * prior work", which is precisely what got the whole message rejected as an
 * injection attempt in the 2026-08-13 live runs.
 */
function fallbackInstructions(): string {
  return "When writing the summary, keep these if they appear in the conversation: the user's " +
    "most recent request in their own words if it is still unanswered; any decision they made; " +
    "exact file paths, commands, numbers and identifiers, unchanged; and which work is finished " +
    "and verified as opposed to only proposed. Leave out anything that the conversation does not " +
    "actually contain, rather than inventing it.";
}

function readStdin(): string {
  try {
    const fd = 0;
    const chunks: Buffer[] = [];
    const buf = Buffer.allocUnsafe(65536);
    let total = 0;
    for (;;) {
      let n = 0;
      try { n = readSync(fd, buf, 0, buf.length, null); } catch { break; }
      if (n <= 0) break;
      chunks.push(Buffer.from(buf.subarray(0, n)));
      total += n;
      if (total > 4 * 1024 * 1024) break;   // a hook payload is never this big
    }
    return Buffer.concat(chunks).toString("utf8");
  } catch {
    return "";
  }
}

function main(): void {
  // The watchdog is the promise that the pane never freezes on this hook.
  const watchdog = setTimeout(() => {
    try { process.stdout.write(fallbackInstructions() + "\n"); } catch { /* ignore */ }
    process.exit(0);
  }, HARD_LIMIT_MS);

  let instructions = fallbackInstructions();
  try {
    const raw = readStdin();
    const input: HookInput = raw ? JSON.parse(raw) : {};
    const cwd = input.cwd && existsSync(input.cwd) ? input.cwd : process.cwd();
    const trigger = input.trigger ?? "unknown";

    const facts = readTranscript(input.transcript_path ?? "");
    const git = gitFacts(cwd);

    const dir = join(cwd, "memory", "handoffs");
    mkdirSync(dir, { recursive: true });

    const date = nowIso().slice(0, 10);
    const path = nextHandoffPath(dir, date);

    // Atomic write: a half-written handoff is worse than none, because
    // resolve-session-handoff.sh would match its session_id and hand the next
    // session a truncated file.
    const tmp = path + ".tmp";
    writeFileSync(tmp, buildHandoff(input, facts, git), "utf8");
    renameSync(tmp, path);

    instructions = buildInstructions(path, facts, trigger);
  } catch {
    // Deliberately silent. stderr from a hook is surfaced to the user as a
    // failure, and a noisy handoff writer would train Zee to ignore it. The
    // fallback instructions still go out, so compaction still gets guidance.
  }

  clearTimeout(watchdog);
  try { process.stdout.write(instructions + "\n"); } catch { /* ignore */ }
  process.exit(0);
}

main();
