// git-manager — shared types.
// Everything the scanner learns about the machine lands in these shapes.
// The renderers are pure functions of a ScanResult; they compute nothing new.

export type AccountKind = "personal" | "work" | "other";

/** One configured GitHub account and the strings that identify it in a remote URL. */
export interface AccountConfig {
  label: string;
  match: string[];
}

export interface NeverPushRule {
  /** Case-insensitive substring matched against the repo's absolute path. */
  repoMatch: string;
  forbidAccount: AccountKind;
  reason: string;
}

export interface Config {
  roots: string[];
  maxDepth: number;
  skipDirs: string[];
  /**
   * Case-insensitive substrings. Any repo or folder whose absolute path contains
   * one is left out of the report entirely. Empty by default: prune only after
   * you have SEEN a row and decided it is noise.
   */
  ignorePaths?: string[];
  /**
   * Exact folder names never reported as untracked projects — generated output
   * that is meant to be rebuilt, not backed up. Safer than `ignorePaths`
   * because it matches the final path segment exactly, not any substring.
   */
  ignoreNames?: string[];
  /**
   * Path fragments the LIVE WATCHER ignores. Nothing to do with what the report
   * contains — these folders are still scanned and still counted. They are
   * simply not worth WAKING UP for.
   *
   * The case that forced this: `~/.claude/projects` holds session transcripts,
   * which Claude Code rewrites every few seconds. Each write triggered a full
   * 1.7-second rescan that changed nothing on the page. Left alone, the server
   * would have rescanned almost continuously while the machine was in use.
   *
   * The trade is explicit: a change under one of these appears on the periodic
   * re-check (default 60s) instead of instantly.
   */
  watchIgnore?: string[];
  accounts: Record<string, AccountConfig>;
  neverPush: NeverPushRule[];
}

/** One remote (a named online destination) on one repo. */
export interface RemoteInfo {
  name: string;
  url: string;
  account: AccountKind;
  accountLabel: string;
  /** owner/repo parsed out of the URL when it looks like GitHub; "" otherwise. */
  slug: string;
  /**
   * Does a local remote-tracking ref exist for the current branch on this remote?
   * false => as far as this machine knows, the branch has never been pushed here.
   */
  hasBranchRef: boolean;
  /** Commits on HEAD that are not on <remote>/<branch>. null when it cannot be computed. */
  unpushed: number | null;
  /** Commits on <remote>/<branch> not on HEAD (you are behind). null when unknown. */
  behind: number | null;
  /** True when this remote is the branch's configured upstream. */
  isUpstream: boolean;
}

export type StateKey =
  | "NOT_A_REPO"
  | "NO_REMOTE"
  | "UNCOMMITTED"
  | "NO_UPSTREAM"
  | "AHEAD"
  | "PARTIAL"
  | "BRANCH_WORK"
  | "SYNCED";

/**
 * A ruling the HUMAN made about a row, recorded so the report stops asking.
 *
 * Deliberately NOT a StateKey: a state describes what git found on disk, and
 * "Zee said no" is not something git can find. Keeping the two apart means a
 * decided row still reports its true state (NOT_A_REPO stays NOT_A_REPO) while
 * moving out of the attention list.
 *
 * Keyed by absolute path and matched exactly. If the folder is renamed or moved
 * the decision stops matching and the row RETURNS to needs-attention. That is
 * deliberate: a moved folder deserves a fresh look, and silently carrying an old
 * ruling onto a path the human never ruled on would be the worse failure.
 */
export interface Decision {
  /** Absolute path this ruling applies to, exactly as it was when recorded. */
  path: string;
  /** Only one verdict exists today. "track later" is just an item still on the list. */
  decision: "do-not-track";
  /** YYYY-MM-DD, supplied by the caller — this module never reads the clock. */
  date: string;
  /** Why, in the human's terms. Printed on the row's detail card. */
  reason: string;
}

export interface DecisionsFile {
  decisions: Decision[];
}

/** A branch other than the checked-out one that still has commits to send. */
export interface BranchWork {
  branch: string;
  waiting: { remote: string; count: number; neverPushed: boolean }[];
}

export interface StateFlags {
  notARepo: boolean;
  noRemote: boolean;
  uncommitted: number;
  noUpstream: boolean;
  ahead: number;
  /** Remote names this branch has commits waiting for. */
  unpushedTo: string[];
  /** Remote names this branch has never been pushed to at all (no local ref). */
  neverPushedTo: string[];
  /**
   * The subset of `unpushedTo` that actually threatens the backup — see
   * OptionalPush below for the full reasoning. Empty means every personal-account
   * destination already has this machine's work, so the repo is SAFE even if
   * some other account is behind.
   */
  blockingRemotes: string[];
}

/**
 * A destination that is behind, but whose being behind is NOT a backup problem.
 *
 * The rule (Zee's, 2026-08-03): a repo is SAFE once every destination on the
 * PERSONAL account has everything this machine has. That is what backup means.
 * A work account, or a third account, lagging behind is a CHOICE, not a risk —
 * so it must not sit in the same list as work that is genuinely unprotected.
 * Colouring both the same way is how a real gap gets lost among nine harmless ones.
 *
 * `kind` separates two very different reasons a remote can read as behind:
 *
 *   "optional"  — a real gap, on an account that is not personal. Pushing is
 *                 available and never required.
 *   "stale-ref" — NOT a gap at all. The remote points at the SAME GitHub repo
 *                 as a remote that is current, just under a different nickname
 *                 whose local cache is out of date. Nothing to push; the commits
 *                 are already there. Detected by comparing owner/repo slugs.
 */
export interface OptionalPush {
  kind: "optional" | "stale-ref";
  /** The remote nickname, e.g. "origin". */
  remote: string;
  account: AccountKind;
  accountLabel: string;
  /** owner/repo, when the URL looked like GitHub. */
  slug: string;
  /** Commits this remote is missing, as of the last fetch. */
  count: number;
  /** For "stale-ref": the up-to-date remote that points at the same repo. */
  sameRepoAs?: string;
}

export interface RiskFlags {
  /** Remotes span BOTH the personal and the work account. */
  bothAccounts: boolean;
  /** A neverPush rule matches this repo and a forbidden remote exists on it. */
  ruleViolations: { rule: NeverPushRule; remote: string }[];
  /** No remote at all, or not a repo — nothing exists off this machine. */
  noOffMachineCopy: boolean;
}

/** What lives inside a repo — the "which skill/system is hosted here" half. */
/** A skill installed here by symlink but whose files live in another repo. */
export interface LinkedSkill {
  name: string;
  target: string;
  /** The repo that actually tracks the link target, or null if nothing does. */
  hostRepo: string | null;
  hostName: string | null;
}

export interface Inventory {
  /** Skills whose files actually live in this repo. */
  skills: string[];
  /** Skills symlinked in from another location — installed here, hosted there. */
  linkedSkills: LinkedSkill[];
  agents: string[];
  scriptCount: number;
  subProjects: string[];
  packageName: string | null;
  /** How much irreplaceable work sits here. Orders rows that share a state. */
  weight: number;
  /** Short human sentence summarising the above. */
  summary: string;
}

export interface RepoRow {
  index: number;
  name: string;
  path: string;
  isRepo: boolean;
  branch: string | null;
  head: string | null;
  lastCommitISO: string | null;
  lastCommitSubject: string | null;
  /** mtime of .git/FETCH_HEAD — how fresh the remote-tracking refs are. */
  lastFetchISO: string | null;
  remotes: RemoteInfo[];
  /** Branches other than the current one that still have commits to send. */
  otherBranches: BranchWork[];
  flags: StateFlags;
  risk: RiskFlags;
  state: StateKey;
  /**
   * Sort key. Built as stateRank * 1000 + content/volume score, so a state band
   * is never crossed by content weight — content only orders rows WITHIN a band.
   * A forbidden-account breach adds 100000 and floats to the very top.
   */
  severity: number;
  /** True when this row belongs in the "needs attention" half of the report. */
  attention: boolean;
  /**
   * The human's ruling for this path, or null if none was ever recorded.
   * Non-null pulls the row into its own table and silences the recommendation.
   * The row stays VISIBLE — a decision you cannot see is one you cannot reverse.
   */
  decided: Decision | null;
  /**
   * Destinations that are behind but do not make this repo unsafe. Listed in
   * their own section so an available-but-unnecessary push is never mistaken
   * for unprotected work. Empty on most rows.
   */
  optionalPushes: OptionalPush[];
  inventory: Inventory;
  /** Repo path this row sits inside, when it is a nested repo or a plain folder. */
  parentRepo: string | null;
  notes: string[];
  /**
   * What this row IS and what to do about it. Derived after sorting, because a
   * duplicate recommendation refers to another row by its printed number.
   */
  recommendation?: {
    kind: "config" | "skills" | "agents" | "code" | "docs";
    action: string;
    why: string;
    duplicateOf: number | null;
  };
}

export interface ScanResult {
  generatedAtISO: string;
  roots: string[];
  fetched: boolean;
  /** True when folders holding only a few loose scripts were included as rows. */
  loose: boolean;
  rows: RepoRow[];
  /**
   * Folders that hold a script or two beside deliverables (a deal folder with a
   * render script). Excluded from the rows by default so the report stays about
   * software, but counted here so the exclusion is never silent.
   */
  filteredWeak: { count: number; paths: string[] };
  /** Rows removed by the config's `ignorePaths` / `ignoreNames`. Never silent. */
  ignoredCount: number;
  /** Where the human's rulings were read from — printed so the file is findable. */
  decisionsPath: string | null;
  /**
   * Rulings in the file that matched no row this run. Almost always a renamed or
   * moved folder. Surfaced, never dropped, so a stale ruling cannot rot unseen.
   */
  orphanDecisions: Decision[];
  totals: {
    repos: number;
    notRepos: number;
    /** Rows still awaiting a decision. Decided rows are NOT counted here. */
    needAttention: number;
    clean: number;
    /** Rows the human has ruled on. */
    decided: number;
    /** Rows that are safe but have a push available on another account. */
    optional: number;
    uncommittedFiles: number;
    unpushedCommits: number;
  };
}
