// git-manager — "what is this, and what should I do with it?"
//
// Two derived fields per row. Both are computed from what the scanner already
// found; nothing here re-reads the disk or invents a fact.
//
//   kind   — what KIND of thing the folder is (skills / code / docs / …)
//   action — the ONE next step, naming the destination account when a push
//            is involved, because the account is the safety-critical part
//
// Honesty rules this module keeps:
//   * a duplicate is always "possible", never asserted — same name is evidence,
//     not proof, and deleting the wrong copy is unrecoverable
//   * the personal account is the default destination (standing rule 2026-08-01);
//     the work account is only ever SUGGESTED, never assumed
//   * a row with nothing to do says so plainly rather than inventing busywork

import { basename } from "node:path";
import type { RepoRow } from "./types.ts";

export type Kind = "config" | "skills" | "agents" | "code" | "docs";

export interface Recommendation {
  kind: Kind;
  /** Terse next step for the table column. */
  action: string;
  /** One sentence of reasoning for the detail card. */
  why: string;
  /** Index of a row this one may duplicate, or null. */
  duplicateOf: number | null;
}

/* --------------------------------------------------------------- helpers -- */

/**
 * Collapse a folder name to a comparison key: drop backup/clone/copy wrappers,
 * trailing counters, punctuation and case. "Backup okoa-loan-intake-system",
 * "Clone-okoa-loan-intake-system" and "okoa-loan-intake-system" all land on the
 * same key, and so do "Fastest Decision tree" and "fastest-decision-tree".
 */
export function nameKey(name: string): string {
  let s = name.toLowerCase();
  s = s.replace(/^(backup|clone|copy)[\s_-]+(of[\s_-]+)?/, "");
  s = s.replace(/[\s_-]*(copy|backup|old|bak)$/, "");
  s = s.replace(/[\s_-]*\(?\d+\)?$/, ""); // trailing " 2", "-3", "(2)"
  return s.replace(/[^a-z0-9]/g, "");
}

/**
 * Sub-folder names that mean "software lives here" even when the top level has
 * no build file. A project can keep all its code one level down and still be a
 * project — calling that "docs" would under-report the risk.
 */
const CODE_SUBDIR = new Set([
  "src",
  "app",
  "lib",
  "scripts",
  "bin",
  "tests",
  "test",
  "engine",
  "convex",
  "extension",
  "diagnostics",
  "server",
  "api",
  "public",
]);

function kindOf(r: RepoRow): Kind {
  if (basename(r.path).startsWith(".")) return "config";
  if (r.inventory.skills.length) return "skills";
  if (r.inventory.agents.length) return "agents";
  if (r.inventory.packageName) return "code";
  if (r.inventory.scriptCount >= 3) return "code";
  if (r.inventory.subProjects.some((s) => CODE_SUBDIR.has(s.toLowerCase()))) return "code";
  return "docs";
}

/** The remote this row should be pushed to by default, if it has one. */
function personalRemote(r: RepoRow) {
  return r.remotes.find((rm) => rm.account === "personal") ?? null;
}

function behindRemotes(r: RepoRow) {
  return r.remotes.filter((rm) => (rm.unpushed ?? 0) > 0);
}

function shortAccount(label: string): string {
  const m = label.match(/\(([^)]+)\)$/);
  return m ? m[1] : label;
}

/* ---------------------------------------------------------------- decide -- */

const DUP_WHY = (n: number) =>
  `The name matches row ${n} after stripping backup/copy wrappers. Compare the two before tracking or deleting either — same name is evidence, not proof, and deleting the wrong copy cannot be undone.`;

function decide(r: RepoRow, dupOf: number | null): { action: string; why: string } {
  // A recorded ruling outranks every derived suggestion, including the duplicate
  // check. The whole point of recording one is that the report stops asking; a
  // tool that re-opens a settled question is just a slower way of being ignored.
  if (r.decided) {
    const when = r.decided.date ? ` · ${r.decided.date}` : "";
    return {
      action: `— not tracked${when}`,
      why:
        `You ruled this out on ${r.decided.date || "an unrecorded date"}: ${
          r.decided.reason || "no reason recorded"
        } The state above is still what git actually found — the ruling changes what to do about it, not the fact. ` +
        `To put the question back, run: decide --repo <path> --undo`,
    };
  }

  // A duplicate only becomes the HEADLINE when the row is not yet tracked or has
  // nowhere to go. There, "does this copy deserve to exist?" comes before any
  // setup work. On a live repo with commits waiting, the pending push is the
  // real action and the duplicate is a footnote — replacing it would hide work.
  if (dupOf !== null && (r.state === "NOT_A_REPO" || r.state === "NO_REMOTE"))
    return { action: `check vs #${dupOf}`, why: DUP_WHY(dupOf) };

  switch (r.state) {
    case "NOT_A_REPO": {
      const kind = kindOf(r);
      if (kind === "config")
        return {
          action: "track config only",
          why: "A settings folder. Most of its bulk is regenerable — session transcripts, caches, downloaded plugins — and tracking that would bloat the repo for no gain. Track the hand-written parts (settings files, hooks, commands) and ignore the rest.",
        };
      if (kind === "docs")
        return {
          action: "docs — track?",
          why: "No build file, no scripts, and no source folder, so this looks like documents rather than software. Worth tracking only if you want a history of the edits; otherwise leave it out.",
        };
      return {
        action: "git init → personal",
        why: "git has never watched this folder, so no copy exists anywhere else. Create the repo, make a first commit, add the personal remote, then push.",
      };
    }

    case "NO_REMOTE": {
      const noCommits = r.head === null;
      return noCommits
        ? {
            action: "commit, then remote",
            why: "The repo exists but holds no commits at all — someone ran git init and stopped. Nothing can be pushed until a first snapshot is made.",
          }
        : {
            action: "add remote → personal",
            why: "Full history exists here, but no online destination is set. Create the repo on the personal account, add it as a remote, then push.",
          };
    }

    case "UNCOMMITTED": {
      const p = personalRemote(r);
      const n = r.flags.uncommitted;
      const behind = behindRemotes(r);
      const dest = p ? "personal" : (r.remotes[0]?.name ?? "a remote");
      return {
        action: `commit ${n} → ${dest}`,
        why: `${n} file${n === 1 ? " is" : "s are"} newer than the last snapshot. The history that IS committed sits online already${
          behind.length ? `, except for ${behind.map((b) => `${b.unpushed} on ${b.name}`).join(" and ")}` : ""
        }. Commit first — a push only sends committed work.`,
      };
    }

    case "NO_UPSTREAM": {
      const p = personalRemote(r) ?? r.remotes[0];
      return {
        action: p ? `push → ${p.name}` : "set an upstream",
        why: "The branch has no matching online branch. Naming both the remote and the branch in the push command works without one.",
      };
    }

    case "AHEAD":
    case "PARTIAL": {
      const behind = behindRemotes(r);
      const personalBehind = behind.find((b) => b.account === "personal");
      const target = personalBehind ?? behind[0];
      if (!target) return { action: "push", why: "Commits are waiting for a destination." };
      const acct = shortAccount(target.accountLabel);
      const suffix = target.account === "personal" ? "" : " ?";
      return {
        action: `push → ${target.name} (${acct})${suffix}`,
        why:
          target.account === "personal"
            ? `${target.unpushed} commit${target.unpushed === 1 ? "" : "s"} have never reached the personal copy.`
            : `${target.unpushed} commit${target.unpushed === 1 ? "" : "s"} are missing from ${target.accountLabel}. That is the WORK account, so this is your call — the personal copy is already current.`,
      };
    }

    case "BRANCH_WORK": {
      const b = r.otherBranches[0];
      return {
        action: b ? `checkout ${b.branch}` : "check side branches",
        why: `The branch you are on is fully pushed, but ${r.otherBranches.length} other local branch${
          r.otherBranches.length === 1 ? "" : "es"
        } hold commits no remote has taken. Check each out and push it before it is forgotten.`,
      };
    }

    default:
      return { action: "—", why: "Every destination already has what this machine has." };
  }
}

/* ----------------------------------------------------------------- entry -- */

/**
 * Attach a recommendation to every row. Runs AFTER sorting and indexing,
 * because a duplicate recommendation refers to another row by its printed number.
 */
export function recommendAll(rows: RepoRow[]): Map<number, Recommendation> {
  // Group rows by collapsed name. The FIRST row in a group (lowest index, so
  // highest risk) is the anchor; later ones are flagged as possible copies.
  const groups = new Map<string, RepoRow[]>();
  for (const r of rows) {
    const k = nameKey(r.name);
    if (!k) continue;
    (groups.get(k) ?? groups.set(k, []).get(k)!).push(r);
  }
  // Flag EVERY member of a duplicate group, each pointing at the lowest-numbered
  // OTHER member. Flagging only the later copies hides the pairing from the row
  // you are most likely to be looking at — the risky one, which sorts first.
  const dupOf = new Map<number, number>();
  for (const g of groups.values()) {
    if (g.length < 2) continue;
    const indexes = g.map((r) => r.index).sort((a, b) => a - b);
    for (const r of g) {
      const other = indexes.find((i) => i !== r.index);
      if (other !== undefined) dupOf.set(r.index, other);
    }
  }

  const out = new Map<number, Recommendation>();
  for (const r of rows) {
    const d = dupOf.get(r.index) ?? null;
    let { action, why } = decide(r, d);
    // Duplicate not used as the headline: keep it visible as a suffix and a
    // second sentence, so it is never silently dropped. A decided row keeps the
    // sentence but not the suffix — its action column must stay a clean "—",
    // or the row still reads as something with work left in it.
    if (d !== null && r.decided) {
      why = `${why} ${DUP_WHY(d)}`;
    } else if (d !== null && !action.startsWith("check vs")) {
      action = `${action} ·dup#${d}`;
      why = `${why} ${DUP_WHY(d)}`;
    }
    out.set(r.index, { kind: kindOf(r), action, why, duplicateOf: d });
  }
  return out;
}
