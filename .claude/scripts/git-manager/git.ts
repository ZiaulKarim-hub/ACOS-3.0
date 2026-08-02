// git-manager — thin, read-only wrappers around the git CLI.
//
// Everything here is safe to run against any repo: no command mutates the
// working tree, the index, the config, or a remote. The one network call
// (fetchAll) is opt-in and read-only.

import { spawnSync } from "node:child_process";

export interface GitResult {
  ok: boolean;
  stdout: string;
  stderr: string;
  code: number;
}

/** Run a git subcommand inside `dir`. Never throws. */
export function git(dir: string, args: string[], timeoutMs = 15_000): GitResult {
  const r = spawnSync("git", ["-C", dir, ...args], {
    encoding: "utf8",
    timeout: timeoutMs,
    // Keep git from ever opening an editor, a pager, or a credential prompt.
    env: {
      ...process.env,
      GIT_TERMINAL_PROMPT: "0",
      GIT_PAGER: "cat",
      GIT_OPTIONAL_LOCKS: "0",
    },
  });
  return {
    ok: r.status === 0,
    stdout: (r.stdout ?? "").trim(),
    stderr: (r.stderr ?? "").trim(),
    code: r.status ?? -1,
  };
}

/** True when `dir` is the top level of a git working tree. */
export function isRepoRoot(dir: string): boolean {
  const r = git(dir, ["rev-parse", "--show-toplevel"]);
  if (!r.ok) return false;
  try {
    return require("node:fs").realpathSync(r.stdout) === require("node:fs").realpathSync(dir);
  } catch {
    return r.stdout === dir;
  }
}

export function currentBranch(dir: string): string | null {
  const r = git(dir, ["rev-parse", "--abbrev-ref", "HEAD"]);
  if (!r.ok || !r.stdout) return null;
  // Detached HEAD reports the literal string "HEAD".
  return r.stdout;
}

export function headSha(dir: string): string | null {
  const r = git(dir, ["rev-parse", "HEAD"]);
  return r.ok && r.stdout ? r.stdout : null;
}

/** Count of changed/untracked entries — the "not even saved into git yet" number. */
export function dirtyCount(dir: string): number {
  const r = git(dir, ["status", "--porcelain", "--untracked-files=normal"]);
  if (!r.ok || !r.stdout) return 0;
  return r.stdout.split("\n").filter((l) => l.trim().length > 0).length;
}

export function remotes(dir: string): { name: string; url: string }[] {
  const r = git(dir, ["remote", "-v"]);
  if (!r.ok || !r.stdout) return [];
  const seen = new Map<string, string>();
  for (const line of r.stdout.split("\n")) {
    const m = line.match(/^(\S+)\s+(\S+)\s+\((fetch|push)\)$/);
    if (!m) continue;
    // Prefer the push URL when it differs from the fetch URL.
    if (m[3] === "push" || !seen.has(m[1])) seen.set(m[1], m[2]);
  }
  return [...seen.entries()].map(([name, url]) => ({ name, url }));
}

/** The branch's configured upstream, e.g. "origin/main". null when unset. */
export function upstreamRef(dir: string): string | null {
  const r = git(dir, ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"]);
  return r.ok && r.stdout ? r.stdout : null;
}

export function refExists(dir: string, ref: string): boolean {
  return git(dir, ["rev-parse", "--verify", "--quiet", ref]).ok;
}

/** Commits in `b` that are not in `a`. null when either ref is missing. */
export function countCommits(dir: string, range: string): number | null {
  const r = git(dir, ["rev-list", "--count", range]);
  if (!r.ok) return null;
  const n = Number.parseInt(r.stdout, 10);
  return Number.isFinite(n) ? n : null;
}

/** Total commits reachable from HEAD — used when a remote has never seen the branch. */
export function totalCommits(dir: string): number | null {
  const r = git(dir, ["rev-list", "--count", "HEAD"]);
  if (!r.ok) return null;
  const n = Number.parseInt(r.stdout, 10);
  return Number.isFinite(n) ? n : null;
}

export function lastCommit(dir: string): { iso: string | null; subject: string | null } {
  const r = git(dir, ["log", "-1", "--format=%cI%x1f%s"]);
  if (!r.ok || !r.stdout) return { iso: null, subject: null };
  const [iso, subject] = r.stdout.split("\x1f");
  return { iso: iso ?? null, subject: subject ?? null };
}

/** Subjects of the commits that a push would send, newest first. */
export function commitSubjects(dir: string, range: string, limit = 10): string[] {
  const r = git(dir, ["log", `--max-count=${limit}`, "--format=%h %s", range]);
  if (!r.ok || !r.stdout) return [];
  return r.stdout.split("\n").filter(Boolean);
}

/** Opt-in, read-only network refresh so remote-tracking refs are not stale. */
export function fetchAll(dir: string, timeoutMs = 60_000): GitResult {
  return git(dir, ["fetch", "--all", "--quiet", "--no-tags"], timeoutMs);
}

/** Every local branch, newest-committed first. Capped to keep the scan quick. */
export function localBranches(dir: string, limit = 60): string[] {
  const r = git(dir, [
    "for-each-ref",
    "--sort=-committerdate",
    `--count=${limit}`,
    "--format=%(refname:short)",
    "refs/heads",
  ]);
  if (!r.ok || !r.stdout) return [];
  return r.stdout.split("\n").filter(Boolean);
}

/**
 * The unified diff a push would send, added lines only.
 * Capped: a huge diff is truncated rather than loaded whole, and the caller is
 * told, so a scan of it is never presented as complete when it was cut short.
 */
export function addedLines(
  dir: string,
  range: string,
  maxBytes = 5_000_000,
  maxCommits = 1000,
): { lines: { file: string; line: number; text: string }[]; truncated: boolean } {
  // `git log -p` is used rather than `git diff` on purpose. When a branch has
  // never been pushed, the range is just "HEAD" — and `git diff HEAD` compares
  // the working tree to HEAD, which is EMPTY once everything is committed. That
  // would silently scan nothing and report a clean push. `log -p` walks the
  // commits themselves, so both the range and the whole-history case work.
  const r = git(
    dir,
    ["log", "-p", "--unified=0", "--no-color", "--no-merges", `--max-count=${maxCommits}`, range],
    45_000,
  );
  if (!r.ok) return { lines: [], truncated: false };

  const raw = r.stdout;
  const truncated = raw.length > maxBytes;
  const body = truncated ? raw.slice(0, maxBytes) : raw;

  const out: { file: string; line: number; text: string }[] = [];
  let file = "";
  let lineNo = 0;
  for (const l of body.split("\n")) {
    if (l.startsWith("+++ ")) {
      file = l.slice(4).replace(/^b\//, "");
      continue;
    }
    if (l.startsWith("@@")) {
      // @@ -old,count +new,count @@
      const m = l.match(/\+(\d+)/);
      lineNo = m ? Number.parseInt(m[1], 10) : 0;
      continue;
    }
    if (l.startsWith("+") && !l.startsWith("+++")) {
      out.push({ file, line: lineNo, text: l.slice(1) });
      lineNo++;
    }
  }
  return { lines: out, truncated };
}
