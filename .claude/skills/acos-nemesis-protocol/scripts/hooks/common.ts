/**
 * common.ts — shared plumbing for the four Nemesis hooks. Reads the hook JSON from stdin,
 * resolves the enrolled project, and emits the exact JSON shapes Claude Code expects.
 */
import * as fs from "node:fs";
import * as path from "node:path";
import { spawnSync } from "node:child_process";
import { projectRootFrom, readConfig, readActive, type Config, type Active } from "../lib/state";
import { isInScope } from "../lib/scope";

export interface HookInput {
  session_id?: string;
  transcript_path?: string;
  cwd?: string;
  hook_event_name?: string;
  tool_name?: string;
  tool_input?: Record<string, unknown>;
  tool_response?: unknown;
  stop_hook_active?: boolean;
  prompt?: string;
}

export async function readStdinJson(): Promise<HookInput> {
  const chunks: Buffer[] = [];
  for await (const c of process.stdin) chunks.push(c as Buffer);
  const raw = Buffer.concat(chunks).toString("utf8").trim();
  if (!raw) return {};
  try { return JSON.parse(raw) as HookInput; } catch { return {}; }
}

export interface Resolved { root: string; cfg: Config; active: Active }

/** The enrolled, ACTIVE project for this call — or null, which means "be inert". */
export function resolveRoot(input: HookInput): Resolved | null {
  const root = projectRootFrom(input.cwd ?? process.cwd());
  if (!root) return null;
  let cfg: Config;
  try { cfg = readConfig(root); } catch { return null; }
  const active = readActive(root);
  if (!active) return null;
  // ── WINDOW SCOPE (Zee, 2026-11-18) ───────────────────────────────────────
  // The four hooks are registered in the PROJECT's settings file, so Claude Code
  // runs them in EVERY window whose cwd is this project — including windows doing
  // work that has nothing to do with the goal. On 2026-11-17 that trapped an
  // unrelated window for 30+ turns: its Stop hook kept refusing to let the turn
  // end over another window's open task, and there was no way to say "not mine"
  // short of disarming the judge for everyone.
  //
  // Both halves of the fix already existed and were simply never compared:
  // `nemesis on` records the id of the window that started it (nemesis.ts,
  // `session: sid` from CLAUDE_CODE_SESSION_ID), and Claude Code hands every hook
  // the id of the window it is running in (HookInput.session_id). One comparison
  // keeps Nemesis inside the window that asked for it.
  //
  // FAIL CLOSED (Zee, 2026-11-18). This block previously failed OPEN: if either id was
  // missing there was nothing to compare, so every window was judged exactly as before.
  // The reasoning was that a missing id must never quietly disarm the judge — which is
  // sound, and is why the gap is now closed where it can actually be FIXED rather than
  // merely detected: `cmdOn` refuses to arm at all without a window id (NO_WINDOW_ID).
  //
  // Given that, an activation reaching here WITHOUT an owner is a stale record from before
  // that rule, not a live window that needs judging. Acting on it would re-create the exact
  // harm the limit exists to prevent: on 2026-11-17 an unrelated window was held for 30+
  // turns by another window's open task, with no way from inside it to say "not mine".
  //
  // The asymmetry, stated plainly: refusing to judge an UNOWNED activation costs coverage
  // the operator can restore in one command, `/acos-nemesis-protocol on "<goal>"`, from the
  // window that should own it. Judging every window costs other people's work, and cannot
  // be undone from the window it traps.
  //
  // THE TRADE, unchanged: a second window working this same code is NOT judged. That is
  // the point of the change, not an oversight.
  if (!active.session) return null;
  if (!input.session_id) return null;
  if (active.session !== input.session_id) return null;
  return { root, cfg, active };
}

export function emit(obj: unknown): void { process.stdout.write(JSON.stringify(obj)); }
export function preAllow(reason?: string): void {
  emit({ hookSpecificOutput: { hookEventName: "PreToolUse", permissionDecision: "allow", ...(reason ? { permissionDecisionReason: reason } : {}) } });
}
export function preDeny(reason: string): void {
  emit({ hookSpecificOutput: { hookEventName: "PreToolUse", permissionDecision: "deny", permissionDecisionReason: reason } });
}
export function postBlock(reason: string): void { emit({ decision: "block", reason }); }
export function stopBlock(reason: string): void { emit({ decision: "block", reason }); }

export function toolFilePath(toolInput: Record<string, unknown> | undefined): string | undefined {
  if (!toolInput) return undefined;
  const p = (toolInput.file_path ?? toolInput.notebook_path ?? toolInput.path) as string | undefined;
  return typeof p === "string" && p ? p : undefined;
}

export function scopeOf(root: string, cfg: Config, filePath: string): { inScope: boolean; rel: string; rule?: string } {
  return isInScope(root, filePath, cfg);
}

/** Apply the proposed edit in memory. Returns null when the edit cannot apply (the tool itself will fail). */
export function applyEdit(before: string, toolName: string, ti: Record<string, unknown>): string | null {
  if (toolName === "Write") return String(ti.content ?? "");
  if (toolName === "Edit") {
    const oldS = String(ti.old_string ?? ""), newS = String(ti.new_string ?? "");
    if (!oldS) return before + newS;
    if (!before.includes(oldS)) return null;
    return ti.replace_all ? before.split(oldS).join(newS) : before.replace(oldS, () => newS);
  }
  if (toolName === "NotebookEdit") {
    const src = String(ti.new_source ?? "");
    const mode = String(ti.edit_mode ?? "replace");
    return `${before}\n# --- notebook ${mode} cell ${String(ti.cell_id ?? "?")} ---\n${src}\n`;
  }
  return null;
}

/** Unified diff via the system `diff`; falls back to a whole-file marker. */
/**
 * D-60 — WHICH ORIGINAL LINES DID THIS EDIT ACTUALLY TOUCH?
 *
 * Returns the OLD-side line ranges a `diff -u` actually changed. A finding `where` is a line
 * against the file AS IT WAS, so these are the ranges to test one against (see R-078).
 *
 * The `@@ -a,b +c,d @@` header is NOT the answer on its own: `b` counts the three lines of
 * surrounding CONTEXT that diff prints either side, so a one-line change reports a seven-line
 * range and a finding six lines away would look touched. So the hunk BODY is walked instead,
 * advancing the old-line counter on context and `-` lines only. A hunk that removes nothing
 * (a pure insertion) still gets a range: the old line the new text lands before, because that
 * is the only place in the old file the insertion can be said to be about.
 */
export function changedOldLines(diff: string): { start: number; end: number }[] {
  const out: { start: number; end: number }[] = [];
  let old = 0, inHunk = false, run: number | null = null, last = 0;
  const flush = (): void => { if (run !== null) { out.push({ start: run, end: last }); run = null; } };
  for (const l of diff.split("\n")) {
    const m = /^@@ -(\d+)(?:,\d+)? \+/.exec(l);
    if (m) { flush(); old = Number(m[1]); inHunk = true; continue; }
    if (!inHunk) continue;                       // the ---/+++ file headers live here
    if (l.startsWith("-")) { if (run === null) run = old; last = old; old++; continue; }
    if (l.startsWith("+")) { if (run === null) { run = old; last = old; } continue; }
    if (l.startsWith(" ") || l === "") { flush(); old++; continue; }
    flush();                                     // "\ No newline at end of file", or anything else
  }
  flush();
  return out;
}

/** Is the finding recorded line inside (or within `slack` of) a line this edit changed? */
export function lineIsInChange(where: string, ranges: { start: number; end: number }[], slack = 3): boolean {
  const n = Number(where.split(":")[1]);
  if (!Number.isFinite(n)) return false;              // no line recorded -> no per-line evidence
  return ranges.some((r) => n >= r.start - slack && n <= r.end + slack);
}

export function unifiedDiff(before: string, after: string, rel: string): string {
  const tmp = fs.mkdtempSync(path.join(require("node:os").tmpdir(), "nemesis-diff-"));
  try {
    const a = path.join(tmp, "a"), b = path.join(tmp, "b");
    fs.writeFileSync(a, before); fs.writeFileSync(b, after);
    const r = spawnSync("diff", ["-u", "--label", `a/${rel}`, "--label", `b/${rel}`, a, b], { encoding: "utf8", maxBuffer: 32 * 1024 * 1024 });
    if (r.stdout) return r.stdout;
    if (r.status === 0) return `(no textual change in ${rel})`;
    return `(diff unavailable: ${r.stderr}) — full candidate follows`;
  } finally { fs.rmSync(tmp, { recursive: true, force: true }); }
}

export function logErr(where: string, e: unknown): void {
  try { fs.appendFileSync("/tmp/nemesis-hook.err", `[${new Date().toISOString()}] ${where}: ${e instanceof Error ? e.stack ?? e.message : String(e)}\n`); } catch { /* best effort */ }
}

// ── Transcript reading (Stop watchdog, R-026; sub-agents too, R-030) ────────

export interface ToolUse { name: string; input: Record<string, unknown>; ts: string }

/** Which rule actually ended the backward walk. `window` means NO boundary was found, so the
    count is the window's content and not a turn - the one case the old return value could not
    express, and the one that must never be read as a turn's true count. */
export type TurnBoundary = "human" | "prev-stop" | "window";

/** Reads the TAIL of a transcript without loading the file. These reach hundreds of megabytes on
    a long session - the live writer's was 303,908,810 bytes on 2026-11-09 - and the old code
    slurped the whole thing into one string on every single Stop hook just to keep its last lines.
    The first line of the slice is dropped because a byte-offset read starts mid-line. */
function tailLines(file: string, maxLines: number, maxBytes = 8 * 1024 * 1024): string[] {
  const fd = fs.openSync(file, "r");
  try {
    const size = fs.fstatSync(fd).size;
    const want = Math.min(size, maxBytes);
    const buf = Buffer.alloc(want);
    fs.readSync(fd, buf, 0, want, size - want);
    const lines = buf.toString("utf8").split("\n").filter(Boolean);
    if (want < size && lines.length) lines.shift();
    return lines.slice(-maxLines);
  } finally { fs.closeSync(fd); }
}

/**
 * Tool uses in the last assistant turn chain.
 *
 * D-62: A STOP-HOOK CONTINUATION LEAVES NO TURN BOUNDARY IN THE TRANSCRIPT. The walk used to
 * end only at "a real human message", and that message does not exist on a turn the Stop hook
 * started itself. Verified on the live writer 2026-11-10: between two consecutive spin turns the
 * transcript holds only assistant / attachment / system events, and the nearest non-tool-result
 * user message was 1933 events back - the 05:02:56Z compaction prompt. So the walk ran to the end
 * of its window and counted EARLIER turns' tool calls as this turn's. The stop records then
 * reported 45, 43, 42, 41, 40, 38, 37, 36, 35, 34, 33, 32 tool calls for twenty-two consecutive
 * turns that each made ZERO; the decay is only old lines falling out of the fixed window. A spin
 * alarm keyed on a count of 0 therefore could not fire while the writer sat holding - and that is
 * worse than D-57's absent field, because an absent field reads as "idle" and raises a false
 * alarm, while a stale positive reads as "busy" and hides a real one.
 *
 * `since` is the previous turn's own end - the last Stop hook's `updated_at` - which is the one
 * boundary a hook-continued turn really has. Whichever boundary the walk meets first going
 * backwards is the later in time, so the human-message rule still wins on a genuine new prompt.
 */
export function lastTurnToolUses(transcriptPath: string | undefined, maxLines = 2000, since = ""): { uses: ToolUse[]; lastAssistantText: string; turnStart: string; boundary: TurnBoundary } {
  if (!transcriptPath || !fs.existsSync(transcriptPath)) return { uses: [], lastAssistantText: "", turnStart: "", boundary: "window" };
  let lines: string[];
  try { lines = tailLines(transcriptPath, maxLines); }
  catch (e) { logErr("lastTurnToolUses", e); return { uses: [], lastAssistantText: "", turnStart: "", boundary: "window" }; }
  const events = lines.map((l) => { try { return JSON.parse(l) as Record<string, unknown>; } catch { return null; } }).filter((e): e is Record<string, unknown> => !!e);
  const uses: ToolUse[] = [];
  let lastAssistantText = "";
  let turnStart = "";
  let boundary: TurnBoundary = "window";
  for (let i = events.length - 1; i >= 0; i--) {
    const ev = events[i]!;
    const ts = String(ev.timestamp ?? "");
    // The previous turn's end, checked BEFORE the message shape, so an attachment or a system
    // event stops the walk too. An event with no timestamp cannot be placed, so it is left to
    // the walk - it is inside the turn until something datable says otherwise.
    if (since && ts && ts <= since) { turnStart = since; boundary = "prev-stop"; break; }
    const msg = ev.message as { role?: string; content?: unknown } | undefined;
    if (!msg) continue;
    if (msg.role === "user") {
      const content = msg.content;
      const onlyToolResults = Array.isArray(content) && content.length > 0 && content.every((b) => b && typeof b === "object" && (b as { type?: string }).type === "tool_result");
      if (!onlyToolResults) { turnStart = ts; boundary = "human"; break; } // a real human message ends the walk
      continue;
    }
    if (msg.role === "assistant" && Array.isArray(msg.content)) {
      for (const b of msg.content as { type?: string; name?: string; input?: Record<string, unknown>; text?: string }[]) {
        if (b.type === "tool_use" && b.name) uses.unshift({ name: b.name, input: b.input ?? {}, ts });
        if (b.type === "text" && b.text && !lastAssistantText) lastAssistantText = b.text;
      }
    }
  }
  return { uses, lastAssistantText, turnStart, boundary };
}
