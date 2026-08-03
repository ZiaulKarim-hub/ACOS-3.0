// git-manager — noticing that something changed, without burning the machine.
//
// A full scan costs about 2 seconds. Running it on a tight loop would keep a
// core busy all day for a report that changes a few times an hour. So the
// server does not poll: it asks macOS to TELL it when a file under the scanned
// roots changes, and only then re-scans.
//
// Three things make that practical:
//
//   * IGNORE THE NOISE. node_modules, virtual environments, caches and build
//     output churn constantly and never affect the report. They are dropped
//     before anything else happens, by the same skipDirs list the scanner uses.
//   * DEBOUNCE. One `git commit` fires dozens of events. A quiet-period timer
//     collapses a burst into a single re-scan.
//   * A SAFETY NET. Recursive watching can miss events under load, and it does
//     not see changes outside the roots at all. A slow periodic re-scan catches
//     anything the watcher dropped, so a missed event costs a delay, never a
//     permanently wrong page.
//
// Read-only throughout. This module never writes, never runs git, never pushes.

import { watch, type FSWatcher } from "node:fs";
import { basename, sep } from "node:path";

export interface WatchOptions {
  roots: string[];
  /** Folder names never worth reacting to — reuse the scanner's skipDirs. */
  skipDirs: string[];
  /**
   * Path fragments not worth WAKING UP for, even though they are still scanned
   * and still counted. See Config.watchIgnore for why this is separate.
   */
  watchIgnore?: string[];
  /** Quiet period before a burst of events counts as one change, in ms. */
  debounceMs?: number;
  /**
   * Re-scan even with no events after this long, in ms. This is the safety net
   * for events the watcher dropped; it is NOT the main path.
   */
  safetyNetMs?: number;
  /** Called with a short human reason: what appeared to change. */
  onChange: (reason: string) => void;
  /** Called when a root cannot be watched at all — surfaced, never swallowed. */
  onWatchError?: (root: string, message: string) => void;
}

/** Paths that fire constantly and never change what the report says. */
const ALWAYS_IGNORE = new Set([
  ".DS_Store",
  "COMMIT_EDITMSG",
  ".git-manager-serve.lock",
]);

/**
 * `.git` MUST NOT be skipped here, even though the scanner skips it.
 *
 * The scanner skips `.git` because it does not walk repo internals looking for
 * projects. The WATCHER has the opposite need: a commit, a branch move and a
 * push change nothing outside `.git`, so skipping it made exactly the events
 * this page exists to show invisible until the slow safety net fired. Caught by
 * testing a real commit, which produced no update at all.
 *
 * Inside `.git`, two sub-paths are still dropped: `objects` and `lfs` churn with
 * hundreds of writes per operation, and every one of them is accompanied by a
 * ref or index write that we DO see. Dropping them costs no signal.
 */
const GIT_INTERNAL_NOISE = ["objects", "lfs"];

function isGitNoise(segments: string[]): boolean {
  const i = segments.indexOf(".git");
  return i !== -1 && GIT_INTERNAL_NOISE.includes(segments[i + 1] ?? "");
}

/**
 * Turn a changed path into the sentence a human wants: which project, and
 * roughly what happened. "ACOS 3.0 — a commit or branch moved" beats a raw path.
 */
function describe(relPath: string): string {
  const parts = relPath.split(sep).filter(Boolean);
  const project = parts[0] ?? "something";
  const inGit = parts.includes(".git");
  const name = basename(relPath);

  if (inGit) {
    if (name === "HEAD" || name === "ORIG_HEAD") return `${project} — branch moved`;
    if (name === "index") return `${project} — files staged or committed`;
    if (parts.includes("refs")) return `${project} — a commit or branch moved`;
    return `${project} — git state changed`;
  }
  return `${project} — a file changed`;
}

/**
 * Start watching. Returns a stop function.
 *
 * Every watcher is best-effort: if one root cannot be watched, the others still
 * work and the failure is reported rather than hidden. A page that silently
 * stopped noticing one of three roots would be the worst possible outcome here.
 */
export function startWatching(opts: WatchOptions): () => void {
  const debounceMs = opts.debounceMs ?? 700;
  const safetyNetMs = opts.safetyNetMs ?? 60_000;
  // Everything the scanner skips EXCEPT ".git" — see GIT_INTERNAL_NOISE above.
  const skip = new Set(
    opts.skipDirs.map((s) => s.toLowerCase()).filter((s) => s !== ".git"),
  );

  const watchers: FSWatcher[] = [];
  let timer: ReturnType<typeof setTimeout> | null = null;
  let pendingReason = "";
  let stopped = false;

  const fire = (reason: string) => {
    // Keep the FIRST reason of a burst. `git commit` ends by touching several
    // files; the first one names what actually happened, the last is noise.
    if (!pendingReason) pendingReason = reason;
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => {
      timer = null;
      const r = pendingReason;
      pendingReason = "";
      if (!stopped) opts.onChange(r);
    }, debounceMs);
  };

  const noisy = (opts.watchIgnore ?? []).map((s) => s.toLowerCase());

  for (const root of opts.roots) {
    try {
      const w = watch(root, { recursive: true }, (_event, filename) => {
        if (!filename) return;
        const rel = String(filename);
        if (ALWAYS_IGNORE.has(basename(rel))) return;
        const segments = rel.split(sep);
        // A single ignored segment anywhere in the path kills the event.
        if (segments.some((seg) => skip.has(seg.toLowerCase()))) return;
        if (isGitNoise(segments)) return;
        // High-churn folders that never change the report. Matched against the
        // full path so a fragment like "/.claude/projects/" is unambiguous.
        const full = `${root}${sep}${rel}`.toLowerCase();
        if (noisy.some((frag) => full.includes(frag))) return;
        fire(describe(rel));
      });
      w.on("error", (e) => opts.onWatchError?.(root, (e as Error).message));
      watchers.push(w);
    } catch (e) {
      // Watching is an optimisation. Losing it degrades to the safety net,
      // which is slower but still correct — so this is reported, not fatal.
      opts.onWatchError?.(root, (e as Error).message);
    }
  }

  const net = setInterval(() => {
    if (!stopped) opts.onChange("periodic re-check");
  }, safetyNetMs);

  return () => {
    stopped = true;
    if (timer) clearTimeout(timer);
    clearInterval(net);
    for (const w of watchers) {
      try {
        w.close();
      } catch {
        /* already gone */
      }
    }
  };
}
