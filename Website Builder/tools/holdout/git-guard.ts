/**
 * git-guard.ts — one place for the two git-borne defenses (X2, Z1).
 *
 * X2 (seventh security review, EXECUTED): a case ran `git config
 * core.fsmonitor /tmp/x.sh` — .git/config is untracked, invisible to every
 * tree check — and git executed that command inside reveal's own next
 * `git status`, with reveal's FULL environment. GIT_SAFE is the neutralizing
 * prefix every git call in these tools carries: no hooks, no fsmonitor, no
 * askpass, no credential helper.
 *
 * Z1 (eighth security review, EXECUTED): GIT_SAFE immunizes OUR calls only.
 * The planted config persists, and the CUSTODIAN's next plain `git status` —
 * in the authoring window, when the next pack's expected.json is plaintext —
 * executed the payload and harvested the answers. The foothold cannot be
 * neutralized for processes we do not run, so it is DETECTED instead:
 * commandValuedConfigKeys() lists every local-config key whose value git will
 * execute as (or feed to) a command. seal REFUSES while any is present;
 * reveal refuses pre-run and seals the fact if one appears MID-run.
 *
 * core.hooksPath gets one carve-out: pointing at the repository's own
 * .git/hooks directory is the DEFAULT location spelled out loud (this very
 * repository does it) and executes nothing that was not already there.
 * Any other value is a redirection and counts.
 */
import { execFileSync } from "node:child_process";
import { realpathSync } from "node:fs";
import { join } from "node:path";

export const GIT_SAFE = [
  "-c", "core.hooksPath=/var/empty",
  "-c", "core.fsmonitor=false",
  "-c", "core.askPass=",
  "-c", "credential.helper=",
];

const EXACT_KEYS = new Set([
  "core.fsmonitor", "core.attributesfile", "core.sshcommand", "core.pager",
  "core.editor", "core.askpass", "credential.helper", "gpg.program",
]);

const canon = (p: string): string => { try { return realpathSync(p); } catch { return p; } };

/** Local-config keys whose values git executes; [] outside a repository. */
export function commandValuedConfigKeys(): string[] {
  let raw = "";
  try {
    raw = execFileSync("git", [...GIT_SAFE, "config", "--local", "--list", "-z"],
      { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] });
  } catch { return []; }   // not a repository (or no local config): nothing to audit
  const bad = new Set<string>();
  for (const entry of raw.split("\0")) {
    if (!entry) continue;
    const nl = entry.indexOf("\n");
    const key = (nl >= 0 ? entry.slice(0, nl) : entry).toLowerCase();
    const value = nl >= 0 ? entry.slice(nl + 1) : "";
    if (key === "core.hookspath") {
      let ownHooks = "";
      try {
        ownHooks = join(execFileSync("git", [...GIT_SAFE, "rev-parse", "--absolute-git-dir"],
          { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] }).trim(), "hooks");
      } catch {}
      if (ownHooks && canon(value) === canon(ownHooks)) continue;   // the default location, spelled out
      bad.add(key);
      continue;
    }
    if (EXACT_KEYS.has(key)
      || key.startsWith("alias.")
      || (key.startsWith("filter.") && /\.(clean|smudge|process)$/.test(key))
      || (key.startsWith("diff.") && key.endsWith(".command"))
      || (key.startsWith("difftool.") && key.endsWith(".cmd"))
      || (key.startsWith("merge.") && key.endsWith(".driver"))
      || (key.startsWith("mergetool.") && key.endsWith(".cmd"))) {
      bad.add(key);
    }
  }
  return [...bad].sort();
}
