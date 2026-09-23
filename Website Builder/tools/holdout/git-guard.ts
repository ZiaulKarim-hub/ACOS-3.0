/**
 * git-guard.ts — the git-borne defenses (X2, Z1, AA1).
 *
 * X2 (seventh security review, EXECUTED): a case ran `git config core.fsmonitor
 * /tmp/x.sh`; git executed that command inside reveal's own `git status`, with
 * reveal's FULL environment. GIT_SAFE is the neutralizing prefix every git call
 * in these tools carries: no hooks, no fsmonitor, no askpass, no credentials.
 *
 * Z1 (eighth review, EXECUTED): GIT_SAFE immunizes OUR calls only. The planted
 * config persists, and the CUSTODIAN's next plain `git status` — in the
 * authoring window, when the next pack's expected.json is plaintext — executed
 * the payload. Unfixable for processes we do not run, so it is DETECTED.
 *
 * AA1 (ninth review, EXECUTED): the first Z1 detector asked `git config
 * --local --list`, which (a) misses `include.path` — a local key pointing at a
 * SECOND config file whose keys are then never listed by --local; (b) misses
 * worktree-scope config (`extensions.worktreeConfig` + .git/config.worktree);
 * and (c) never looked at hooks at all — a hostile .git/hooks/pre-commit needs
 * NO config key, and the hooksPath carve-out blessed exactly that directory.
 * Four doors, same payload. Fixes here:
 *   - config is read with `--show-scope`, filtered to the LOCAL and WORKTREE
 *     scopes a hostile case can plant. This resolves include.path (its imported
 *     keys carry the including file's scope — measured: an include from local
 *     config lists its keys as `local`), so door 1 and door 2 close together,
 *     while the custodian's own global/system config (keychain helper, editor)
 *     is never flagged — the property that let the real repo audit clean.
 *   - the REDIRECTION keys themselves (include.path, includeIf.*.path,
 *     extensions.worktreeConfig) are on the watch list, so the redirection is
 *     visible even if a value somehow escaped scope classification.
 *   - hooks are handled separately (they are not config): hookCensus lists the
 *     executable non-sample hooks that exist NOW (a warning — a legitimate
 *     repo may carry its own, e.g. this one's post-commit), and hookSnapshot
 *     lets reveal prove none were PLANTED or CHANGED during a run (the hard,
 *     tamper-sealing guarantee, and the exact mechanism door 3 used).
 */
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { readdirSync, readFileSync, realpathSync, statSync } from "node:fs";
import { join } from "node:path";

export const GIT_SAFE = [
  "-c", "core.hooksPath=/var/empty",
  "-c", "core.fsmonitor=false",
  "-c", "core.askPass=",
  "-c", "credential.helper=",
];

// Scopes a hostile CASE can write in this repository. system/global are the
// custodian's own machine config — same trust domain as the custodian, and
// flagging them would refuse on an ordinary credential helper or editor.
const PLANTABLE_SCOPES = new Set(["local", "worktree"]);

const EXACT_KEYS = new Set([
  "core.fsmonitor", "core.attributesfile", "core.sshcommand", "core.pager",
  "core.editor", "core.askpass", "credential.helper", "gpg.program",
  // AA1: the redirection keys themselves — a smuggled second config or a
  // worktree-config switch is suspicious in its own right.
  "include.path", "extensions.worktreeconfig",
]);

const isCommandValued = (key: string): boolean =>
  EXACT_KEYS.has(key)
  || key.startsWith("alias.")
  || (key.startsWith("includeif.") && key.endsWith(".path"))
  || (key.startsWith("filter.") && /\.(clean|smudge|process)$/.test(key))
  || (key.startsWith("diff.") && key.endsWith(".command"))
  || (key.startsWith("difftool.") && key.endsWith(".cmd"))
  || (key.startsWith("merge.") && key.endsWith(".driver"))
  || (key.startsWith("mergetool.") && key.endsWith(".cmd"))
  || (key.startsWith("url.") && /\.insteadof$/.test(key));

const canon = (p: string): string => { try { return realpathSync(p); } catch { return p; } };

const absoluteGitDir = (): string | null => {
  try {
    return execFileSync("git", [...GIT_SAFE, "rev-parse", "--absolute-git-dir"],
      { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] }).trim();
  } catch { return null; }
};

/**
 * Command-valued config keys active in the LOCAL or WORKTREE scope (or reached
 * by an include from them). [] outside a repository. core.hooksPath pointing at
 * the repository's OWN hooks dir is the default location spelled out loud (this
 * repo does exactly that) and is NOT flagged — but hookCensus/hookSnapshot then
 * make that carve-out safe by auditing that very directory.
 */
export function commandValuedConfigKeys(): string[] {
  let raw = "";
  try {
    raw = execFileSync("git", [...GIT_SAFE, "config", "--show-scope", "--list", "-z"],
      { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] });
  } catch { return []; }
  const gitDir = absoluteGitDir();
  const ownHooks = gitDir ? canon(join(gitDir, "hooks")) : "";
  // `--show-scope -z` emits alternating NUL-separated tokens: scope, then
  // "key\nvalue", repeating. (Measured on git 2.x.)
  const tokens = raw.split("\0");
  const bad = new Set<string>();
  for (let i = 0; i + 1 < tokens.length; i += 2) {
    const scope = tokens[i];
    const kv = tokens[i + 1];
    if (!scope || kv === undefined) continue;
    if (!PLANTABLE_SCOPES.has(scope)) continue;
    const nl = kv.indexOf("\n");
    const key = (nl >= 0 ? kv.slice(0, nl) : kv).toLowerCase();
    const value = nl >= 0 ? kv.slice(nl + 1) : "";
    if (key === "core.hookspath") {
      if (ownHooks && canon(value) === ownHooks) continue;   // default location
      bad.add(key);
      continue;
    }
    if (isCommandValued(key)) bad.add(key);
  }
  return [...bad].sort();
}

// A hook is "live" if it is an executable regular file that git will run: the
// standard names, minus the *.sample templates git ships (never executed).
const isLiveHook = (name: string): boolean => !name.endsWith(".sample");

/** Executable non-sample hook files in the repo's active hooks dir, sorted. */
export function hookCensus(): string[] {
  const gitDir = absoluteGitDir();
  if (!gitDir) return [];
  const dir = join(gitDir, "hooks");
  let names: string[] = [];
  try { names = readdirSync(dir); } catch { return []; }
  const live: string[] = [];
  for (const name of names) {
    if (!isLiveHook(name)) continue;
    try {
      const st = statSync(join(dir, name));
      if (st.isFile() && (st.mode & 0o111) !== 0) live.push(name);
    } catch {}
  }
  return live.sort();
}

/** name -> sha256:mode for every live hook, so reveal can diff before/after. */
export function hookSnapshot(): Record<string, string> {
  const gitDir = absoluteGitDir();
  if (!gitDir) return {};
  const dir = join(gitDir, "hooks");
  let names: string[] = [];
  try { names = readdirSync(dir); } catch { return {}; }
  const out: Record<string, string> = {};
  for (const name of names) {
    if (!isLiveHook(name)) continue;
    try {
      const st = statSync(join(dir, name));
      if (!st.isFile() || (st.mode & 0o111) === 0) continue;
      const h = createHash("sha256").update(readFileSync(join(dir, name))).digest("hex");
      out[name] = `${h}:${(st.mode & 0o777).toString(8)}`;
    } catch {}
  }
  return out;
}

/** Hook names added, removed, or changed between two snapshots. */
export function hookDelta(before: Record<string, string>, after: Record<string, string>): string[] {
  const changed = new Set<string>();
  for (const k of Object.keys(after)) if (before[k] !== after[k]) changed.add(k);
  for (const k of Object.keys(before)) if (!(k in after)) changed.add(k);
  return [...changed].sort();
}
