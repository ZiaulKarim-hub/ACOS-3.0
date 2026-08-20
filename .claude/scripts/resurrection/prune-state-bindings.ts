#!/usr/bin/env bun
/**
 * prune-state-bindings.ts — bound the token-monitor state directory.
 *
 * Why this exists (2026-08-18). `register-session-pid.sh` rewrites
 * `cmux-surface-<sid>` on EVERY SessionStart, and a session id is minted afresh
 * at every /clear and /compact. Nothing ever pruned the old bindings, so they
 * accumulated without limit: 1034 `cmux-surface-*` files mapping onto 105
 * surfaces, with eight sessions all claiming surface F354478B. That collapsed
 * the surface discriminator the resume chain relied on, and the last-resort
 * pick fell back to `ls -t` mtime order — which served FruitSync's handoff to
 * the Research to Portfolio pane.
 *
 * DISCIPLINE — this never deletes. Pruned files are MOVED to
 * `state/pruned/<utc-stamp>/`, mirroring the preserve-by-move rule the resume
 * hook already follows for consumed artifacts. A wrong prune is undone with mv.
 *
 * SAFETY — a binding is pruned only when ALL of these hold:
 *   1. no live process holds the session (its `pid-<sid>` is missing, or names
 *      a PID that is not running, or names a PID whose start time has drifted);
 *   2. no `pending-resume-<sid>.txt` exists — an unclaimed resume must keep its
 *      bindings or recovery for that session dies with them;
 *   3. the file is older than --older-than days (default 7).
 * Anything it cannot prove dead is LEFT ALONE.
 *
 * Usage:
 *   bun prune-state-bindings.ts                 # dry run (default), prints a plan
 *   bun prune-state-bindings.ts --apply         # move the provably-dead ones
 *   bun prune-state-bindings.ts --older-than 14 # widen the age floor
 */

import { existsSync, mkdirSync, readdirSync, readFileSync, renameSync, statSync } from "node:fs";
import { join } from "node:path";
import { homedir } from "node:os";
import { execFileSync } from "node:child_process";

const STATE = join(homedir(), "Library", "Application Support", "acos-token-monitor", "state");

const argv = process.argv.slice(2);
const APPLY = argv.includes("--apply");
const olderIdx = argv.indexOf("--older-than");
const OLDER_DAYS = olderIdx >= 0 ? Number(argv[olderIdx + 1]) : 7;
if (!Number.isFinite(OLDER_DAYS) || OLDER_DAYS < 0) {
  console.error("REFUSED — --older-than needs a non-negative number of days");
  process.exit(2);
}

/** Prefixes this tool is allowed to touch. Everything else in state/ is off limits. */
const PREFIXES = ["cmux-surface-", "pid-", "project-", "stop-"] as const;

/** The live process's start time, or null when the pid is not running. */
function pidStart(pid: string): string | null {
  try {
    return execFileSync("ps", ["-o", "lstart=", "-p", pid], { encoding: "utf8" }).trim();
  } catch {
    return null;
  }
}

/**
 * A session is live when its `pid-<sid>` names a running process AND that
 * process's start time still matches the one recorded when the binding was
 * written.
 *
 * The start-time half is not decoration. PIDs are reused: a long-dead
 * session's file can name a number that now belongs to some unrelated
 * process, which would make the binding look live forever and keep it out of
 * every prune. `register-session-pid.sh` records `ps -o lstart=` on line 2 of
 * the pid file for exactly this identity check, so this honours it. A pid file
 * with no recorded start time is treated as live (fail-safe: never prune what
 * cannot be proven dead).
 */
function sessionLive(sid: string): boolean {
  const pidFile = join(STATE, `pid-${sid}`);
  if (!existsSync(pidFile)) return false;
  let lines: string[] = [];
  try {
    lines = readFileSync(pidFile, "utf8").split("\n");
  } catch {
    return false;
  }
  const pid = (lines[0] ?? "").trim();
  if (!/^\d+$/.test(pid)) return false;
  const liveStart = pidStart(pid);
  if (liveStart === null) return false;          // not running at all
  const recordedStart = (lines[1] ?? "").trim();
  if (!recordedStart) return true;               // cannot disprove — keep it
  return recordedStart === liveStart;            // same process, or a reused pid
}

function hasPendingResume(sid: string): boolean {
  return existsSync(join(STATE, `pending-resume-${sid}.txt`));
}

if (!existsSync(STATE)) {
  console.error(`REFUSED — state directory not found: ${STATE}`);
  process.exit(2);
}

const now = Date.now();
const ageFloorMs = OLDER_DAYS * 24 * 60 * 60 * 1000;

type Verdict = { file: string; sid: string; reason: string };
const prune: Verdict[] = [];
const keep: Verdict[] = [];

for (const name of readdirSync(STATE)) {
  const prefix = PREFIXES.find((p) => name.startsWith(p));
  if (!prefix) continue;
  const sid = name.slice(prefix.length);
  if (!/^[A-Za-z0-9_-]+$/.test(sid)) continue;

  const full = join(STATE, name);
  let mtime = 0;
  try {
    mtime = statSync(full).mtimeMs;
  } catch {
    continue;
  }

  if (sessionLive(sid)) {
    keep.push({ file: name, sid, reason: "session is live" });
  } else if (hasPendingResume(sid)) {
    keep.push({ file: name, sid, reason: "unclaimed pending-resume — recovery still needs this" });
  } else if (now - mtime < ageFloorMs) {
    keep.push({ file: name, sid, reason: `younger than ${OLDER_DAYS}d` });
  } else {
    prune.push({ file: name, sid, reason: "session dead, no pending resume, past the age floor" });
  }
}

const byPrefix = (list: Verdict[]) => {
  const counts: Record<string, number> = {};
  for (const v of list) {
    const p = PREFIXES.find((x) => v.file.startsWith(x)) ?? "?";
    counts[p] = (counts[p] ?? 0) + 1;
  }
  return counts;
};

console.log(`state: ${STATE}`);
console.log(`age floor: ${OLDER_DAYS} day(s)`);
const keepReasons: Record<string, number> = {};
for (const v of keep) keepReasons[v.reason] = (keepReasons[v.reason] ?? 0) + 1;
console.log(`keep:  ${keep.length}  ${JSON.stringify(byPrefix(keep))}`);
for (const [reason, n] of Object.entries(keepReasons).sort((a, b) => b[1] - a[1])) {
  console.log(`       ${String(n).padStart(5)}  ${reason}`);
}
console.log(`prune: ${prune.length}  ${JSON.stringify(byPrefix(prune))}`);

if (prune.length === 0) {
  console.log("nothing to prune — every binding is live, needed, or too young.");
  process.exit(0);
}

if (!APPLY) {
  console.log("");
  console.log("DRY RUN — nothing was moved. Re-run with --apply to move these");
  console.log("into state/pruned/<utc-stamp>/. Files are MOVED, never deleted.");
  process.exit(0);
}

const stamp = new Date().toISOString().replace(/[:.]/g, "-");
const dest = join(STATE, "pruned", stamp);
mkdirSync(dest, { recursive: true });

let moved = 0;
const failures: string[] = [];
for (const v of prune) {
  try {
    renameSync(join(STATE, v.file), join(dest, v.file));
    moved += 1;
  } catch (err) {
    failures.push(`${v.file}: ${(err as Error).message}`);
  }
}

console.log("");
console.log(`MOVED ${moved} binding(s) -> ${dest}`);
if (failures.length) {
  console.log(`could not move ${failures.length}:`);
  for (const f of failures.slice(0, 10)) console.log(`  ${f}`);
}
console.log("undo: mv the files back out of that folder.");
