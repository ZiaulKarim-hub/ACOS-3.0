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

// BB1 item 5 (tenth review, NAMED): this allowlist is a MAINTENANCE SURFACE, not
// a closed set — git keeps adding executable-valued keys, so it must track git's
// evolution. sequence.editor (git commit / rebase -i) joined core.editor here.
const EXACT_KEYS = new Set([
  "core.fsmonitor", "core.attributesfile", "core.sshcommand", "core.pager",
  "core.editor", "sequence.editor", "core.askpass", "credential.helper", "gpg.program",
  // CC1 (eleventh review, EXECUTED): diff.external runs on a plain `git diff`
  // (no tty, no --ext-diff); interactive.diffFilter on `git add -p`. Both were
  // missed and reopened the AA1 harvest. Named here for the bare-command case;
  // the SHAPE rule below is the durable catch for path-valued unlisted keys.
  "diff.external", "interactive.difffilter",
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
  || key.startsWith("pager.")
  || (key.startsWith("trailer.") && key.endsWith(".command"))
  || (key.startsWith("url.") && /\.insteadof$/.test(key))
  // DD2 (twelfth review): gpg.<format>.program runs on a signed commit / tag -s
  // (only gpg.program was listed); *.packObjectsHook runs on fetch/push.
  || (key.startsWith("gpg.") && key.endsWith(".program"))
  || key.endsWith(".packobjectshook");

// CC1 (eleventh review): the allowlist is a hand-enumerated set that TRAILS git
// — diff.external proved it live. The durable defense is DEFAULT-SUSPICIOUS by
// SHAPE, not by name: a local/worktree value that begins with "!" (git's shell
// syntax) or whose first token is an existing executable file is treated as a
// planted command whatever its key. So an UNLISTED executable-valued key is
// caught by what it IS, not by whether we remembered its name.
const valueShapeIsCommand = (value: string): boolean => {
  const v = value.trim();
  if (v.startsWith("!")) return true;
  const first = (v.split(/\s+/)[0] ?? "").replace(/^["']|["']$/g, "");
  if (first.includes("/")) {
    try { const st = statSync(first); if (st.isFile() && (st.mode & 0o111) !== 0) return true; } catch {}
  }
  return false;
};

const canon = (p: string): string => { try { return realpathSync(p); } catch { return p; } };

// BB1 (tenth security review, EXECUTED): the hook audit read
// join(--absolute-git-dir, "hooks"). In a LINKED WORKTREE — the documented QA
// deployment (reviewers run in worktrees; reveal's docstring says "a separate
// QA worktree") — --absolute-git-dir is .git/worktrees/<name>, but git runs
// hooks from the COMMON dir (.git/hooks). The census/snapshot read an empty
// directory that does not exist, saw [], and a case's planted hook fired on the
// custodian's commit while the record certified hook_planted_during_run: false.
// The hooks directory git ACTUALLY runs from is <common-dir>/hooks (a linked
// worktree shares the common dir; core.hooksPath can redirect it, but a
// redirect is flagged by door 4, so the DEFAULT location is what this audits).
// NB: `git rev-parse --git-path hooks` cannot be used — it HONORS core.hooksPath,
// and GIT_SAFE sets core.hooksPath=/var/empty, so it would report /var/empty and
// the audit would read an empty directory (measured). --git-common-dir is not
// hooksPath-sensitive; --path-format=absolute makes it correct from any subdir.
const hooksDir = (): string | null => {
  try {
    const common = execFileSync("git",
      [...GIT_SAFE, "rev-parse", "--path-format=absolute", "--git-common-dir"],
      { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] }).trim();
    return common ? join(common, "hooks") : null;
  } catch { return null; }
};

/**
 * Command-valued config keys active in the LOCAL or WORKTREE scope (or reached
 * by an include from them). [] outside a repository. core.hooksPath pointing at
 * the repository's OWN hooks dir is the default location spelled out loud (this
 * repo does exactly that) and is NOT flagged — but hookCensus/hookSnapshot then
 * make that carve-out safe by auditing that very directory.
 */
export function commandValuedConfigMap(): Record<string, string> {
  let raw = "";
  try {
    raw = execFileSync("git", [...GIT_SAFE, "config", "--show-scope", "--list", "-z"],
      { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] });
  } catch { return {}; }
  const own = hooksDir();
  const ownHooks = own ? canon(own) : "";
  // `--show-scope -z` emits alternating NUL-separated tokens: scope, then
  // "key\nvalue", repeating. (Measured on git 2.x.)
  const tokens = raw.split("\0");
  const out: Record<string, string> = {};
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
      out[key] = value;
      continue;
    }
    // A multivar key can repeat; the value recorded is enough for change
    // detection (a mid-run edit changes it), which is all reveal's delta needs.
    if (isCommandValued(key) || valueShapeIsCommand(value)) out[key] = value;
  }
  return out;
}

// Keys only — for seal's presence WARNING, which cannot tell legit tooling
// (git-lfs, Watchman) from a persisted plant, so it never refuses on presence
// (DD1). reveal's before/after delta is what treats a change as a plant.
export function commandValuedConfigKeys(): string[] {
  return Object.keys(commandValuedConfigMap()).sort();
}

// DD1 (twelfth review): keys whose presence-or-VALUE differs between two
// snapshots — appeared or changed. This is a PLANT; a pre-existing key is not.
export function configDelta(before: Record<string, string>, after: Record<string, string>): string[] {
  const changed = new Set<string>();
  for (const k of Object.keys(after)) if (before[k] !== after[k]) changed.add(k);
  for (const k of Object.keys(before)) if (!(k in after)) changed.add(k);
  return [...changed].sort();
}

// A hook is "live" if it is an executable regular file that git will run: the
// standard names, minus the *.sample templates git ships (never executed).
const isLiveHook = (name: string): boolean => !name.endsWith(".sample");

/** Executable non-sample hook files in the repo's active hooks dir, sorted. */
export function hookCensus(): string[] {
  const dir = hooksDir();
  if (!dir) return [];
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
export function hookSnapshot(): Record<string, string> | null {
  // CC2 (eleventh review): null means "could not audit" (dir unlocatable — git
  // too old for --path-format, rev-parse failed — or unreadable). It is NOT the
  // same as {} ("audited, no live hook"): reveal must refuse or record
  // unverified on null, never seal hook_planted_during_run: false from it.
  const dir = hooksDir();
  if (!dir) return null;
  let names: string[] = [];
  try { names = readdirSync(dir); } catch { return null; }
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
