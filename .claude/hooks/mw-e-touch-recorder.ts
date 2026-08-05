#!/usr/bin/env bun
/**
 * mw-e-touch-recorder.ts — the MW-E feeder (ACOS Resurrection Protocol).
 *
 * WHAT IT IS: a PostToolUse hook that notes which files THIS window edited, so
 * `collisions` can tell you when another live window of the same project is
 * editing the same file. Without a feeder, MW-E has a ledger and a query but
 * nothing writing to the ledger, so it correctly reports nothing forever.
 *
 * NOT REGISTERED BY DEFAULT, ON PURPOSE. Zee approved all five MW items; Claude
 * costed this one high and advised deferring it, and the brief's own guidance
 * was to build it LAST and behind a switch. So it ships complete and inert:
 * it does nothing at all until BOTH
 *   1. the switch file exists — `touch ~/.acos/windows/collision-warning.enabled`
 *   2. it is registered as a PostToolUse hook in settings
 * are true. Either one missing means the hook is a no-op.
 *
 * TypeScript (run by bun), not Python, per the standing language rule: new
 * tooling defaults to TypeScript. It shells out to windows_lib.py rather than
 * re-implementing the manifest, so there is exactly ONE writer of that state
 * and no second copy to drift.
 *
 * FAIL-OPEN, ALWAYS. A recorder that can break a tool call is worse than no
 * recorder. Every path exits 0 and prints nothing on the happy path.
 *
 * Register (only if you want it live):
 *   "PostToolUse": [{ "matcher": "Write|Edit|NotebookEdit",
 *     "hooks": [{ "type": "command",
 *       "command": "bun \"$CLAUDE_PROJECT_DIR/.claude/hooks/mw-e-touch-recorder.ts\"" }] }]
 */

import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

const SWITCH = join(homedir(), ".acos", "windows", "collision-warning.enabled");
const WINDOWS_LIB = join(
  homedir(),
  "Documents",
  "Vibe Coding",
  "ACOS 3.0",
  ".claude",
  "scripts",
  "resurrection",
  "windows_lib.py",
);

/** Tool payloads that name a file we should record. */
const FILE_TOOLS = new Set(["Write", "Edit", "NotebookEdit", "MultiEdit"]);

function readStdin(): string {
  try {
    return require("node:fs").readFileSync(0, "utf8");
  } catch {
    return "";
  }
}

function main(): void {
  // Gate 1: the switch. Checked FIRST and cheapest — when MW-E is off this
  // hook must cost nothing, not even a parse.
  if (!existsSync(SWITCH)) return;

  const workspace = process.env.CMUX_WORKSPACE_ID;
  if (!workspace) return; // not in a cmux window: nothing to attribute a touch to

  if (!existsSync(WINDOWS_LIB)) return;

  let payload: any;
  try {
    payload = JSON.parse(readStdin() || "{}");
  } catch {
    return; // unparseable input is not this hook's problem to report
  }

  const tool = payload?.tool_name ?? "";
  if (!FILE_TOOLS.has(tool)) return;

  const input = payload?.tool_input ?? {};
  const paths: string[] = [];
  if (typeof input.file_path === "string" && input.file_path) {
    paths.push(input.file_path);
  }
  // MultiEdit-shaped payloads carry several edits over one file path.
  if (Array.isArray(input.edits) && typeof input.file_path === "string") {
    // already captured above; the edits array adds no new paths
  }
  if (paths.length === 0) return;

  // `--project auto` resolves from this workspace's own claim, so the hook
  // never re-derives project identity — adopt already recorded it.
  spawnSync(
    "/usr/bin/python3",
    [WINDOWS_LIB, "--project", "auto", "--workspace", workspace, "--touch", ...paths],
    { stdio: "ignore", timeout: 4000 },
  );
}

try {
  main();
} catch {
  // Fail-open by construction: never let a bookkeeping hook break a tool call.
}
process.exit(0);
