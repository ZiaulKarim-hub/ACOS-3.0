// git-manager — the scanner.
//
// Walks the configured roots, finds every git repo and every project folder that
// is NOT a repo, then works out for each one: what lives inside it, where it can
// be pushed, which GitHub account each destination belongs to, and exactly which
// of the five "not safely stored" states it is in.
//
// Read-only. The only command that touches the network is `git fetch`, and only
// when the caller passes fetch: true.

import { existsSync, readdirSync, statSync } from "node:fs";
import { basename, join } from "node:path";
import { attribute, rulesFor } from "./accounts.ts";
import { decisionIndex, loadDecisions } from "./decisions.ts";
import * as G from "./git.ts";
import { inventory, isDir, projectKind } from "./inventory.ts";
import { recommendAll } from "./recommend.ts";
import { assignStableIds } from "./stable-ids.ts";
import type {
  BranchWork,
  Config,
  Decision,
  OptionalPush,
  RemoteInfo,
  RepoRow,
  RiskFlags,
  ScanResult,
  StateFlags,
  StateKey,
} from "./types.ts";

interface Found {
  path: string;
  isRepo: boolean;
  parentRepo: string | null;
}

/** Depth-limited walk that records repo roots and orphan project folders. */
function walk(root: string, cfg: Config, loose: boolean, weak: { count: number; paths: string[] }): Found[] {
  const out: Found[] = [];
  const skip = new Set(cfg.skipDirs);

  const visit = (
    dir: string,
    depth: number,
    nearestRepo: string | null,
    untrackedAncestor: boolean,
  ) => {
    if (depth > cfg.maxDepth) return;

    const repoHere = existsSync(join(dir, ".git"));
    if (repoHere) {
      out.push({ path: dir, isRepo: true, parentRepo: nearestRepo });
      nearestRepo = dir;
      // Inside a repo again: a deeper untracked folder is the repo's business.
      untrackedAncestor = false;
    } else if (!nearestRepo && !untrackedAncestor) {
      const kind = projectKind(dir);
      if (kind === "strong" || (loose && kind === "weak")) {
        // Not inside any repo, and it looks like software => nothing tracks this.
        // Only the TOP-MOST such folder is reported. Listing every skill folder
        // under an untracked ~/.claude would bury the one fact that matters.
        out.push({ path: dir, isRepo: false, parentRepo: null });
        untrackedAncestor = true;
      } else if (kind === "weak") {
        // Counted, never silently dropped — the renderer says how many.
        weak.count += 1;
        if (weak.paths.length < 200) weak.paths.push(dir);
      }
    }

    let children: string[] = [];
    try {
      children = readdirSync(dir, { withFileTypes: true })
        // Real directories only. A symlinked folder points at content that lives
        // somewhere else — following it reports the same work twice and invents
        // "untracked" projects that are in fact tracked at the link target.
        .filter((e) => e.isDirectory() && !e.isSymbolicLink())
        .map((e) => e.name);
    } catch {
      return;
    }

    for (const name of children) {
      if (skip.has(name)) continue;
      // Hidden folders never hold projects we manage, and .git internals are noise.
      if (name.startsWith(".") && depth > 0) continue;
      visit(join(dir, name), depth + 1, nearestRepo, untrackedAncestor);
    }
  };

  if (isDir(root)) visit(root, 0, null, false);
  return out;
}

/** Folders holding a few scripts beside deliverables — reported as a count only. */
export interface WeakSet {
  count: number;
  paths: string[];
}

function buildRemotes(dir: string, branch: string | null, cfg: Config): RemoteInfo[] {
  const upstream = G.upstreamRef(dir);
  const total = G.totalCommits(dir);

  return G.remotes(dir).map(({ name, url }) => {
    const attr = attribute(url, cfg);
    const ref = branch ? `${name}/${branch}` : null;
    const hasBranchRef = ref ? G.refExists(dir, ref) : false;

    let unpushed: number | null = null;
    let behind: number | null = null;
    if (ref && hasBranchRef) {
      unpushed = G.countCommits(dir, `${ref}..HEAD`);
      behind = G.countCommits(dir, `HEAD..${ref}`);
    } else if (branch) {
      // No remote-tracking ref: as far as this machine knows, the branch has
      // never been pushed here, so every commit on it is waiting.
      unpushed = total;
      behind = 0;
    }

    return {
      name,
      url,
      account: attr.account,
      accountLabel: attr.label,
      slug: attr.slug,
      hasBranchRef,
      unpushed,
      behind,
      isUpstream: !!upstream && !!branch && upstream === `${name}/${branch}`,
    };
  });
}

function lastFetchISO(dir: string): string | null {
  const p = join(dir, ".git", "FETCH_HEAD");
  try {
    return statSync(p).mtime.toISOString();
  } catch {
    return null;
  }
}

/**
 * The headline state, and its rank. Rank is a BAND: content weight orders rows
 * inside a band and can never lift a row out of it, so "holds a lot" never
 * outranks "exists nowhere else".
 */
function classify(flags: StateFlags, otherBranchWork: boolean): { state: StateKey; rank: number } {
  if (flags.notARepo) return { state: "NOT_A_REPO", rank: 7 };
  if (flags.noRemote) return { state: "NO_REMOTE", rank: 6 };
  if (flags.uncommitted > 0) return { state: "UNCOMMITTED", rank: 5 };
  // From here down the question is only about BLOCKING remotes — the ones whose
  // being behind means work is unprotected. A work account or a third account
  // lagging is a choice, and a stale local ref for a repo that already has the
  // commits is nothing at all. Ranking those as problems buries the real ones.
  if (flags.noUpstream && flags.blockingRemotes.length) return { state: "NO_UPSTREAM", rank: 4 };
  if (flags.ahead > 0) return { state: "AHEAD", rank: 3 };
  if (flags.blockingRemotes.length) return { state: "PARTIAL", rank: 2 };
  // The checked-out branch is clean, but another local branch is not. Calling
  // this repo "safe" would be false.
  if (otherBranchWork) return { state: "BRANCH_WORK", rank: 1 };
  return { state: "SYNCED", rank: 0 };
}

/**
 * Branches other than `current` that still have commits no remote has taken.
 *
 * Measured against the PERSONAL account only, when one exists — the same rule
 * the headline state uses. A side branch that is safely on personal but absent
 * from the work account is a choice, not lost work, and flagging it would
 * re-create the false alarm one level down. With no personal remote at all,
 * every remote counts, because then nothing is backed up.
 */
function otherBranchWork(dir: string, current: string | null, remotes: RemoteInfo[]): BranchWork[] {
  if (!remotes.length) return [];
  const personal = remotes.filter((r) => r.account === "personal");
  const judgeAgainst = personal.length ? personal : remotes;
  const out: BranchWork[] = [];
  const names = judgeAgainst.map((r) => r.name);
  for (const branch of G.localBranches(dir)) {
    if (branch === current) continue;

    // REACHABILITY, not ref-existence. A branch nobody pushed under its own name
    // is not lost work if its commits already left the machine inside another
    // branch. Asking whether `<remote>/<branch>` exists reported STEPS
    // `fix/archived-tasks-safe` as 26 unprotected commits and OKOA Website/dev
    // `main` as 1 — every one of which was already on a pushed personal branch.
    // Two false alarms of exactly the kind this report exists to avoid.
    const stranded = G.commitsOnNoRemoteRef(dir, branch, names);
    if (stranded === null) {
      // Uncomputable is NOT zero. Fall back to the old per-remote question so an
      // unreadable repo errs toward flagging rather than toward silence.
      const waiting: BranchWork["waiting"] = [];
      for (const rm of judgeAgainst) {
        const ref = `${rm.name}/${branch}`;
        if (G.refExists(dir, ref)) {
          const n = G.countCommits(dir, `${ref}..${branch}`);
          if ((n ?? 0) > 0) waiting.push({ remote: rm.name, count: n as number, neverPushed: false });
        } else {
          const n = G.countCommits(dir, branch);
          if ((n ?? 0) > 0) waiting.push({ remote: rm.name, count: n as number, neverPushed: true });
        }
      }
      if (waiting.length) out.push({ branch, waiting });
      continue;
    }
    if (stranded === 0) continue; // every commit is already off this machine

    // Genuinely stranded. Attribute the count to each judged remote that lacks
    // this branch by name, so the detail card can still say where to send it.
    const waiting: BranchWork["waiting"] = judgeAgainst.map((rm) => ({
      remote: rm.name,
      count: stranded,
      neverPushed: !G.refExists(dir, `${rm.name}/${branch}`),
    }));
    out.push({ branch, waiting });
  }
  return out;
}

export function scan(
  cfg: Config,
  opts: { fetch?: boolean; loose?: boolean; decisionsFile?: string } = {},
): ScanResult {
  // Read the human's rulings BEFORE walking, so a decided row can be marked in
  // the same pass. An unreadable file throws here rather than being swallowed —
  // see decisions.ts for why silently forgetting rulings is the worse failure.
  const { path: decPath, decisions } = loadDecisions(opts.decisionsFile);
  const decIndex = decisionIndex(decisions);
  const decisionsUsed = new Set<string>();

  const found: Found[] = [];
  const seen = new Set<string>();
  const weak = { count: 0, paths: [] as string[] };
  const ignore = (cfg.ignorePaths ?? []).map((s) => s.toLowerCase());
  const ignoreNames = new Set((cfg.ignoreNames ?? []).map((s) => s.toLowerCase()));
  let ignored = 0;
  for (const root of cfg.roots) {
    for (const f of walk(root, cfg, !!opts.loose, weak)) {
      if (seen.has(f.path)) continue;
      if (ignore.some((s) => f.path.toLowerCase().includes(s))) {
        ignored++;
        continue;
      }
      // A named-ignore only ever silences an UNTRACKED folder. A real repo is
      // never hidden by a name rule — losing sight of a repo is the failure
      // this whole report exists to prevent.
      if (!f.isRepo && ignoreNames.has(basename(f.path).toLowerCase())) {
        ignored++;
        continue;
      }
      seen.add(f.path);
      found.push(f);
    }
  }

  const rows: RepoRow[] = [];

  for (const f of found) {
    const notes: string[] = [];

    if (!f.isRepo) {
      const flags: StateFlags = {
        notARepo: true,
        noRemote: true,
        uncommitted: 0,
        noUpstream: true,
        ahead: 0,
        unpushedTo: [],
        neverPushedTo: [],
      };
      const risk: RiskFlags = { bothAccounts: false, ruleViolations: [], noOffMachineCopy: true };
      const inv = inventory(f.path);
      rows.push({
        index: 0,
        name: basename(f.path),
        path: f.path,
        isRepo: false,
        branch: null,
        head: null,
        lastCommitISO: null,
        lastCommitSubject: null,
        lastFetchISO: null,
        remotes: [],
        otherBranches: [],
        flags,
        risk,
        state: "NOT_A_REPO",
        severity: 7 * 1000 + Math.min(999, inv.weight * 5),
        attention: true,
        inventory: inv,
        parentRepo: null,
        notes: ["git has never tracked this folder — no backup exists anywhere"],
        decided: null,
        optionalPushes: [],
      });
      continue;
    }

    if (opts.fetch) {
      const r = G.fetchAll(f.path);
      if (!r.ok) notes.push(`fetch failed: ${r.stderr.split("\n")[0] || `exit ${r.code}`}`);
    }

    const branch = G.currentBranch(f.path);
    if (branch === "HEAD") notes.push("detached HEAD — not on a branch");

    const remotes = buildRemotes(f.path, branch === "HEAD" ? null : branch, cfg);
    const uncommitted = G.dirtyCount(f.path);
    const upstream = G.upstreamRef(f.path);
    const { iso, subject } = G.lastCommit(f.path);

    const upstreamRemote = remotes.find((r) => r.isUpstream) ?? null;
    const ahead = upstreamRemote?.unpushed ?? 0;

    const unpushedTo = remotes.filter((r) => (r.unpushed ?? 0) > 0).map((r) => r.name);
    const neverPushedTo = remotes.filter((r) => !r.hasBranchRef).map((r) => r.name);

    // ---- which "behind" remotes actually matter -------------------------
    // Zee's rule, 2026-08-03: the repo is SAFE once every PERSONAL-account
    // destination has this machine's work. Anything else being behind is a
    // choice. Splitting them here is what stops one real gap being lost among
    // eight harmless ones.
    const behind = remotes.filter((r) => (r.unpushed ?? 0) > 0);
    // Repos that some CURRENT remote already points at. Two remotes can name the
    // same GitHub repo under different nicknames (an https `origin` and an ssh
    // `personal`); if one is current the commits are already there, and the
    // other is only reporting an out-of-date local cache. Not a gap.
    const currentSlugs = new Set(
      remotes.filter((r) => (r.unpushed ?? 0) === 0 && r.slug).map((r) => r.slug),
    );
    const hasPersonalRemote = remotes.some((r) => r.account === "personal");

    const optionalPushes: OptionalPush[] = [];
    const blockingRemotes: string[] = [];
    for (const r of behind) {
      if (r.slug && currentSlugs.has(r.slug)) {
        const twin = remotes.find(
          (o) => o.name !== r.name && o.slug === r.slug && (o.unpushed ?? 0) === 0,
        );
        optionalPushes.push({
          kind: "stale-ref",
          remote: r.name,
          account: r.account,
          accountLabel: r.accountLabel,
          slug: r.slug,
          count: r.unpushed ?? 0,
          sameRepoAs: twin?.name,
        });
      } else if (r.account !== "personal" && hasPersonalRemote) {
        // Only optional BECAUSE a personal destination exists and is current.
        // With no personal remote at all, nothing is backed up and this is real.
        optionalPushes.push({
          kind: "optional",
          remote: r.name,
          account: r.account,
          accountLabel: r.accountLabel,
          slug: r.slug,
          count: r.unpushed ?? 0,
        });
      } else {
        blockingRemotes.push(r.name);
      }
    }

    const flags: StateFlags = {
      notARepo: false,
      noRemote: remotes.length === 0,
      uncommitted,
      noUpstream: upstream === null,
      ahead: ahead ?? 0,
      unpushedTo,
      neverPushedTo,
      blockingRemotes,
    };
    // The default destination being behind only counts as UNPUSHED if it is one
    // of the blocking ones. An upstream pointing at the work account, or at a
    // stale twin of a current remote, must not drag the row back into the
    // attention list — that is the whole point of the split above.
    if (!blockingRemotes.includes(upstreamRemote?.name ?? "")) flags.ahead = 0;

    const accountsPresent = new Set(remotes.map((r) => r.account));
    const ruleViolations = rulesFor(f.path, cfg).flatMap((rule) =>
      remotes.filter((r) => r.account === rule.forbidAccount).map((r) => ({ rule, remote: r.name })),
    );
    const risk: RiskFlags = {
      bothAccounts: accountsPresent.has("personal") && accountsPresent.has("work"),
      ruleViolations,
      noOffMachineCopy: remotes.length === 0,
    };

    const branchWork = otherBranchWork(f.path, branch === "HEAD" ? null : branch, remotes);
    const inv = inventory(f.path);
    const { state, rank } = classify(flags, branchWork.length > 0);

    // Content weight leads inside a band; raw volume only breaks ties.
    const volume = uncommitted + Math.max(0, ...remotes.map((r) => r.unpushed ?? 0));
    let severity = rank * 1000 + Math.min(999, inv.weight * 5 + Math.min(volume, 200));
    if (ruleViolations.length) severity += 100_000;

    if (branchWork.length) {
      const total = branchWork.reduce(
        (n, b) => n + Math.max(...b.waiting.map((w) => w.count)),
        0,
      );
      notes.push(
        `${branchWork.length} other local branch${branchWork.length === 1 ? "" : "es"} ${
          branchWork.length === 1 ? "holds" : "hold"
        } ${total} commit${total === 1 ? "" : "s"} no remote has taken`,
      );
    }
    if (!opts.fetch && remotes.length)
      notes.push(
        lastFetchISO(f.path)
          ? `remote counts are as of the last fetch (${lastFetchISO(f.path)}) — run with --fetch to refresh`
          : "this repo has never fetched — remote counts reflect local knowledge only",
      );

    rows.push({
      index: 0,
      name: basename(f.path),
      path: f.path,
      isRepo: true,
      branch,
      head: G.headSha(f.path),
      lastCommitISO: iso,
      lastCommitSubject: subject,
      lastFetchISO: lastFetchISO(f.path),
      remotes,
      otherBranches: branchWork,
      flags,
      risk,
      state,
      severity,
      attention: state !== "SYNCED" || ruleViolations.length > 0,
      inventory: inv,
      parentRepo: f.parentRepo,
      notes,
      decided: null,
      optionalPushes,
    });
  }

  // Attach rulings. This runs BEFORE sorting and before recommendAll, because a
  // decided row's recommendation has to read the ruling to say "you said no".
  for (const r of rows) {
    const d = decIndex.get(r.path);
    if (!d) continue;
    r.decided = d;
    decisionsUsed.add(d.path);
    // The row leaves the attention list but keeps its real state and severity,
    // so undoing the ruling restores its exact former position.
    r.attention = false;
  }

  // A ruling that matched nothing is almost always a renamed or moved folder.
  // Surfaced, never dropped: a stale ruling that rots unseen is how a folder
  // silently stops being watched.
  const orphanDecisions: Decision[] = decisions.filter((d) => !decisionsUsed.has(d.path));

  // Sort decides ORDER — risky rows first, so they are seen. It must not decide
  // IDENTITY. Numbering by position meant a row's number changed whenever its
  // state improved, or whenever any riskier row above it did: committing three
  // repos renumbered the table under the human mid-instruction on 2026-08-02.
  // The number now comes from stable-ids.ts and belongs to the path for good.
  rows.sort((a, b) => b.severity - a.severity || a.name.localeCompare(b.name));
  assignStableIds(rows);

  // Recommendations come LAST: a duplicate recommendation cites another row by
  // its printed number, which only exists once sorting and indexing are done.
  const recs = recommendAll(rows);
  for (const r of rows) r.recommendation = recs.get(r.index);

  const totals = {
    repos: rows.filter((r) => r.isRepo).length,
    notRepos: rows.filter((r) => !r.isRepo).length,
    needAttention: rows.filter((r) => r.attention).length,
    // "clean" means git has nothing outstanding. A decided row is not clean —
    // it is unfinished business the human chose to leave — so it is counted
    // separately rather than folded in and made to look safe.
    clean: rows.filter((r) => !r.attention && !r.decided).length,
    decided: rows.filter((r) => r.decided).length,
    optional: rows.filter((r) => r.optionalPushes.some((o) => o.kind === "optional")).length,
    uncommittedFiles: rows.reduce((n, r) => n + r.flags.uncommitted, 0),
    unpushedCommits: rows.reduce(
      (n, r) => n + Math.max(0, ...r.remotes.map((x) => x.unpushed ?? 0)),
      0,
    ),
  };

  return {
    generatedAtISO: new Date().toISOString(),
    roots: cfg.roots,
    fetched: !!opts.fetch,
    loose: !!opts.loose,
    rows,
    totals,
    filteredWeak: weak,
    ignoredCount: ignored,
    decisionsPath: decisions.length || existsSync(decPath) ? decPath : null,
    orphanDecisions,
  };
}
