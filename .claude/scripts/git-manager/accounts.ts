// git-manager — mapping a remote URL to the GitHub account that owns it.
//
// This is the single most safety-relevant function in the tool. On this machine
// two accounts exist and one standing rule says personal work must never land in
// the work account. Every destination shown to the user is labelled here.

import type { AccountKind, Config, NeverPushRule } from "./types.ts";

export interface Attribution {
  account: AccountKind;
  label: string;
  slug: string;
}

/**
 * Classify a remote URL. Matching is substring-based against the configured
 * `match` strings, which covers both SSH host aliases (github.com-personal)
 * and plain owner names (ZiaulKarim-hub) in HTTPS URLs.
 */
export function attribute(url: string, cfg: Config): Attribution {
  const lower = url.toLowerCase();
  for (const [kind, acc] of Object.entries(cfg.accounts)) {
    for (const needle of acc.match) {
      if (lower.includes(needle.toLowerCase())) {
        return { account: kind as AccountKind, label: acc.label, slug: parseSlug(url) };
      }
    }
  }
  return { account: "other", label: describeOther(url), slug: parseSlug(url) };
}

function describeOther(url: string): string {
  const host = parseHost(url);
  return host ? `${host} (unrecognised)` : "unrecognised destination";
}

/** owner/repo when the URL looks like a GitHub-style remote; "" otherwise. */
export function parseSlug(url: string): string {
  // git@host:owner/repo.git  |  ssh://git@host/owner/repo.git  |  https://host/owner/repo.git
  const scp = url.match(/^[^@]+@[^:]+:([^/]+\/[^/]+?)(?:\.git)?$/);
  if (scp) return scp[1];
  const uri = url.match(/^(?:ssh|https?|git):\/\/[^/]+\/([^/]+\/[^/]+?)(?:\.git)?$/);
  if (uri) return uri[1];
  return "";
}

export function parseHost(url: string): string {
  const scp = url.match(/^[^@]+@([^:]+):/);
  if (scp) return scp[1];
  const uri = url.match(/^(?:ssh|https?|git):\/\/(?:[^@/]+@)?([^/:]+)/);
  if (uri) return uri[1];
  return "";
}

/**
 * Which neverPush rules apply to this repo path, and for which account.
 * A rule fires on a case-insensitive substring match against the absolute path.
 */
export function rulesFor(repoPath: string, cfg: Config): NeverPushRule[] {
  const lower = repoPath.toLowerCase();
  return (cfg.neverPush ?? []).filter((r) => lower.includes(r.repoMatch.toLowerCase()));
}

/** True when pushing this repo to this account is forbidden by configuration. */
export function isForbidden(
  repoPath: string,
  account: AccountKind,
  cfg: Config,
): NeverPushRule | null {
  for (const rule of rulesFor(repoPath, cfg)) {
    if (rule.forbidAccount === account) return rule;
  }
  return null;
}
