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
  inventory: Inventory;
  /** Repo path this row sits inside, when it is a nested repo or a plain folder. */
  parentRepo: string | null;
  notes: string[];
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
  totals: {
    repos: number;
    notRepos: number;
    needAttention: number;
    clean: number;
    uncommittedFiles: number;
    unpushedCommits: number;
  };
}
