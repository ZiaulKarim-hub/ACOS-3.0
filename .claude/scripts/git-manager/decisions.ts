// git-manager — the human's rulings, and the only part of this tool with memory.
//
// Everything else recomputes from disk on every run, which is why the report kept
// asking "docs — track?" about folders the human had already ruled out. A scan can
// see what git knows; it cannot see what was decided. This module is that memory.
//
// Design rules, each one load-bearing:
//
//   * RECORDED, NOT HIDDEN. A ruling moves a row into its own table. It never
//     removes the row. `ignorePaths` already hides things, and a hidden row is a
//     decision nobody can review or reverse.
//   * THE STATE STAYS TRUE. A decided folder that is not a repo still reports
//     NOT_A_REPO. The ruling changes what to DO about the fact, never the fact.
//   * EXACT PATH, FAILS LOUD. Matching is on the absolute path, exactly. Rename
//     or move the folder and the ruling stops applying, so the row comes back.
//     Loose matching would quietly carry a ruling onto a path never ruled on.
//   * NO CLOCK IN HERE. The caller supplies the date. A module that reads the
//     clock cannot be tested against a fixed expectation.

import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import type { Decision, DecisionsFile } from "./types.ts";

const HERE = dirname(fileURLToPath(import.meta.url));

/** The file rulings live in. Beside the config, but deliberately separate from it. */
export function decisionsPath(explicit?: string): string {
  return explicit ? resolve(explicit) : join(HERE, "decisions.json");
}

/**
 * Read the rulings. A missing file is normal — it means nothing has been decided
 * yet — and returns an empty list rather than an error.
 *
 * A file that exists but cannot be parsed is a different matter and THROWS. Doing
 * otherwise would silently discard every ruling in it, and the report would go
 * back to asking about folders the human already settled, with no sign why.
 */
export function loadDecisions(explicit?: string): { path: string; decisions: Decision[] } {
  const path = decisionsPath(explicit);
  if (!existsSync(path)) return { path, decisions: [] };

  let parsed: DecisionsFile;
  try {
    parsed = JSON.parse(readFileSync(path, "utf8")) as DecisionsFile;
  } catch (e) {
    throw new Error(
      `decisions file is present but unreadable: ${path}\n` +
        `  ${(e as Error).message}\n` +
        `  Refusing to continue as if nothing was ever decided. Fix the JSON, or move the file aside.`,
    );
  }

  const list = Array.isArray(parsed?.decisions) ? parsed.decisions : [];
  const out: Decision[] = [];
  for (const d of list) {
    if (!d || typeof d.path !== "string" || d.decision !== "do-not-track") continue;
    out.push({
      path: resolve(d.path),
      decision: "do-not-track",
      date: typeof d.date === "string" ? d.date : "",
      reason: typeof d.reason === "string" ? d.reason : "",
    });
  }
  return { path, decisions: out };
}

/** Exact-path lookup, built once per scan. */
export function decisionIndex(decisions: Decision[]): Map<string, Decision> {
  const m = new Map<string, Decision>();
  for (const d of decisions) m.set(d.path, d);
  return m;
}

/**
 * Record one ruling, or replace the ruling already held for that exact path.
 * Returns what happened so the caller can say so plainly rather than guessing.
 */
export function recordDecision(
  d: Decision,
  explicit?: string,
): { path: string; action: "added" | "replaced"; previous: Decision | null } {
  const path = decisionsPath(explicit);
  const { decisions } = loadDecisions(explicit);
  const target = resolve(d.path);

  const at = decisions.findIndex((x) => x.path === target);
  const previous = at >= 0 ? decisions[at] : null;
  const next: Decision = { ...d, path: target };

  if (at >= 0) decisions[at] = next;
  else decisions.push(next);

  decisions.sort((a, b) => a.path.localeCompare(b.path));
  writeFileSync(path, `${JSON.stringify({ decisions }, null, 2)}\n`, "utf8");
  return { path, action: at >= 0 ? "replaced" : "added", previous };
}

/**
 * Withdraw a ruling. The row returns to needs-attention on the next scan, which
 * is the whole point — undoing must put the question back, not leave a gap.
 */
export function forgetDecision(
  targetPath: string,
  explicit?: string,
): { path: string; removed: Decision | null } {
  const path = decisionsPath(explicit);
  const { decisions } = loadDecisions(explicit);
  const target = resolve(targetPath);

  const at = decisions.findIndex((x) => x.path === target);
  if (at < 0) return { path, removed: null };

  const [removed] = decisions.splice(at, 1);
  writeFileSync(path, `${JSON.stringify({ decisions }, null, 2)}\n`, "utf8");
  return { path, removed };
}
