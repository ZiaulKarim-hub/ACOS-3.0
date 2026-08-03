// git-manager — permanent row numbers.
//
// The `#` column used to be a POSITION. scan.ts sorted by severity and then
// numbered 1..N by position, so a row's number changed whenever its state
// changed — or whenever any riskier row above it did. Committing three repos on
// 2026-08-02 dropped them out of UNCOMMITTED and silently renumbered the whole
// table under the human, who had already sent "4,5,6 commit to personal" against
// the old numbering. A number that moves cannot be pointed at, which defeats the
// renderer's own design rule ("the reader must be able to point at a row number
// and act").
//
// This module separates IDENTITY from ORDER. Rows still SORT by severity, so the
// risky ones stay on top; but the number PRINTED beside a row belongs to that
// project for good.
//
// Design rules, each one load-bearing:
//
//   * EXACT PATH, LIKE DECISIONS. The key is the absolute path, matched exactly,
//     the same rule decisions.ts uses. Rename or move a folder and it is a new
//     project with a new number — the alternative is quietly carrying a number
//     onto a path it was never given to.
//   * NUMBERS ARE NEVER REUSED. A retired path keeps its entry forever and new
//     projects take max+1. Recycling the number of a deleted folder would let
//     "row 12" mean one thing on Monday and another on Friday — the exact bug
//     this module exists to kill. Gaps are the price, and gaps are harmless.
//   * SEED IN DISPLAY ORDER. On a first run the registry is empty, so ids are
//     handed out in the order the rows are already sorted. The first table
//     therefore reads 1..N as before; every table after it is stable.
//   * NO CLOCK IN HERE. The caller supplies any date. A module that reads the
//     clock cannot be tested against a fixed expectation.
//   * WRITE ONLY WHEN SOMETHING IS NEW. A pure re-scan must not rewrite the
//     file, so its mtime stays meaningful and concurrent scans do not thrash it.

import { existsSync, readFileSync, renameSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));

export interface IdsFile {
  version: number;
  note: string;
  /** absolute path -> permanent row number */
  ids: Record<string, number>;
}

/** The file permanent numbers live in. Beside decisions.json, deliberately separate. */
export function idsPath(explicit?: string): string {
  return explicit ? resolve(explicit) : join(HERE, "ids.json");
}

/**
 * Read the registry. A missing file is normal — it means no project has been
 * numbered yet — and returns an empty map.
 *
 * A file that exists but cannot be parsed THROWS, for the same reason
 * loadDecisions does: silently starting from zero would renumber every project
 * at once, which is precisely the failure this file prevents.
 */
export function loadIds(explicit?: string): { path: string; ids: Map<string, number> } {
  const path = idsPath(explicit);
  if (!existsSync(path)) return { path, ids: new Map() };
  let parsed: unknown;
  try {
    parsed = JSON.parse(readFileSync(path, "utf8"));
  } catch (err) {
    throw new Error(
      `git-manager: ${path} exists but is not valid JSON. Refusing to continue, ` +
        `because starting fresh would renumber every project. Fix or delete it. (${String(err)})`,
    );
  }
  const raw = (parsed as IdsFile)?.ids;
  if (!raw || typeof raw !== "object") return { path, ids: new Map() };
  const ids = new Map<string, number>();
  for (const [p, n] of Object.entries(raw)) {
    if (typeof n === "number" && Number.isInteger(n) && n > 0) ids.set(p, n);
  }
  return { path, ids };
}

/** Highest number ever handed out, so the next one cannot collide with a retired row. */
export function highestId(ids: Map<string, number>): number {
  let max = 0;
  for (const n of ids.values()) if (n > max) max = n;
  return max;
}

function writeIds(path: string, ids: Map<string, number>): void {
  const sorted = [...ids.entries()].sort((a, b) => a[1] - b[1]);
  const body: IdsFile = {
    version: 1,
    note:
      "Permanent git-manager row numbers, keyed on absolute path. Numbers are " +
      "NEVER reused: a path that disappears keeps its entry so its number can " +
      "never come to mean a different project. Gaps are expected. Editing this " +
      "file changes what a number points at — do it deliberately.",
    ids: Object.fromEntries(sorted),
  };
  // tmp + rename: a scan interrupted mid-write must not leave a truncated
  // registry, because an unreadable registry stops the whole report.
  const tmp = `${path}.tmp`;
  writeFileSync(tmp, `${JSON.stringify(body, null, 2)}\n`);
  renameSync(tmp, path);
}

/**
 * Give every row its permanent number, minting one for any project seen for the
 * first time. Mutates `rows[].index`. Returns what changed, so the caller can
 * tell the human that new numbers were issued.
 *
 * `rows` must already be in display order — new projects are numbered in that
 * order, which is what makes a first run read 1..N.
 */
export function assignStableIds<T extends { path: string; index: number }>(
  rows: T[],
  explicit?: string,
): { path: string; minted: Array<{ path: string; id: number }> } {
  const { path, ids } = loadIds(explicit);
  let next = highestId(ids) + 1;
  const minted: Array<{ path: string; id: number }> = [];
  for (const r of rows) {
    let id = ids.get(r.path);
    if (id === undefined) {
      id = next++;
      ids.set(r.path, id);
      minted.push({ path: r.path, id });
    }
    r.index = id;
  }
  if (minted.length) writeIds(path, ids);
  return { path, minted };
}
