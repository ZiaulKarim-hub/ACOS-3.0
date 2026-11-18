/**
 * discover.ts — walk the workspace once, the same way for every check.
 *
 * WHY A SHARED WALK. Both root checks need the same answer to "what source is actually
 * in this repo", and both are only trustworthy if they can prove they looked everywhere.
 * A hand-maintained list of paths is the thing that rots: it keeps passing while new code
 * appears beside it, uncovered and unnoticed. So each check discovers the whole tree and
 * then has to ACCOUNT for every file it found — either by checking it or by naming the
 * reason it is someone else's. Anything it cannot account for fails the check.
 *
 * WHAT IS SKIPPED, AND WHY EACH SKIP IS SAFE:
 *   node_modules AT ANY DEPTH — third-party code. This is not the usual hygiene: two spike
 *     folders under "Website Builder" carry vendored copies of zod and entities, and those
 *     libraries ship their own vitest suites. 288 of the 318 test files in this workspace
 *     are theirs. `bun test`'s own default walk prunes only the TOP-LEVEL node_modules, so
 *     a naive sweep adopts another project's test suite as if it were ours.
 *   .git — object storage, not source.
 *   .worktree — snapshots git made of this repo; the real file is already counted at its
 *     own path, so counting the copy would double-report and could pin a stale version.
 *   .nemesis — the protocol's own bookkeeping, including `.nemesis/snapshots/<id>/files/`,
 *     where it keeps a copy of every judged file so its revert rung has something to go
 *     back to. Those copies are byte-identical suites at a second path, so the walk found
 *     them and the drift guard quite correctly refused to run a suite nobody had claimed.
 *     Skipped for the same reason as .worktree: the real file is already counted at its own
 *     path, and running a frozen copy would report on code that is no longer current.
 *     This is about DISCOVERY only — the Nemesis scan still reads `.nemesis/` itself for
 *     secrets, which is right, because a credential committed there is a real credential.
 *   dist, build, .next, coverage, out — generated output.
 */

import { readdirSync, statSync } from "node:fs";
import { join, relative, sep } from "node:path";

const SKIP_DIRS = new Set([
  "node_modules", ".git", ".worktree", ".nemesis", "dist", "build", ".next", "coverage", "out",
]);

/** Depth bound so a symlink cycle cannot hang a gate. 12 is deeper than this repo goes. */
const MAX_DEPTH = 12;

/**
 * Every file under `root`, as paths relative to it and always with "/" separators,
 * so a comparison against a listed path means the same thing on any platform.
 */
export function walkRepo(root: string): string[] {
  const found: string[] = [];
  const visit = (dir: string, depth: number): void => {
    if (depth > MAX_DEPTH) return;
    let entries: ReturnType<typeof readdirSync>;
    try {
      entries = readdirSync(dir, { withFileTypes: true });
    } catch {
      return; // an unreadable directory is not a reason to fail a lint gate
    }
    for (const entry of entries) {
      const full = join(dir, entry.name);
      if (entry.isDirectory()) {
        if (SKIP_DIRS.has(entry.name)) continue;
        visit(full, depth + 1);
        continue;
      }
      // A symlink to a file counts, but only if it actually resolves: this repo holds two
      // links dangling at a hook deleted in Apr 2026, and a broken link is not source.
      if (entry.isSymbolicLink()) {
        try { if (!statSync(full).isFile()) continue; } catch { continue; }
      } else if (!entry.isFile()) {
        continue;
      }
      found.push(relative(root, full).split(sep).join("/"));
    }
  };
  visit(root, 0);
  return found.sort();
}

/** Is `file` inside `dir`? Compared on path SEGMENTS, so "tools" never matches "toolsmith". */
export function isUnder(file: string, dir: string): boolean {
  if (dir === "." || dir === "") return true;
  const base = dir.endsWith("/") ? dir : `${dir}/`;
  return file.startsWith(base);
}
