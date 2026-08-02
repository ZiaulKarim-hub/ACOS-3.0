#!/usr/bin/env bun
// git-manager — command line entry point.
//
//   scan        inventory every repo and untracked folder, and say what is not
//               safely stored anywhere yet
//   plan-push   for ONE repo and ONE destination, print what would be sent, which
//               GitHub account it would land in, and the exact command to run
//
// This tool NEVER pushes. plan-push deliberately stops at printing the literal
// `git ... push <remote> <branch>` command. That command must be run directly by
// the session so the repo guard hook (~/.claude/hooks/github-repo-guard.ts) sees
// a real push and can prompt. Wrapping the push inside this script would hide it
// from the guard, which is exactly the failure the guard exists to prevent.

import { spawnSync } from "node:child_process";
import { existsSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { attribute, isForbidden } from "./accounts.ts";
import { forgetDecision, loadDecisions, recordDecision } from "./decisions.ts";
import * as G from "./git.ts";
import { renderHtml } from "./render-html.ts";
import { renderTerminal } from "./render-terminal.ts";
import { scan } from "./scan.ts";
import { scanForSecrets } from "./secrets.ts";
import type { AccountKind, Config } from "./types.ts";

const HERE = dirname(fileURLToPath(import.meta.url));

function loadConfig(explicit?: string): Config {
  const candidates = [
    explicit,
    join(HERE, "config.json"),
    join(HERE, "config.default.json"),
  ].filter(Boolean) as string[];
  for (const p of candidates) {
    if (existsSync(p)) return JSON.parse(readFileSync(p, "utf8")) as Config;
  }
  throw new Error(`no config found; looked in: ${candidates.join(", ")}`);
}

interface Args {
  cmd: string;
  flags: Record<string, string | boolean>;
  repeated: Record<string, string[]>;
}

function parseArgs(argv: string[]): Args {
  const cmd = argv[0] && !argv[0].startsWith("-") ? argv[0] : "scan";
  const rest = argv[0] && !argv[0].startsWith("-") ? argv.slice(1) : argv;
  const flags: Record<string, string | boolean> = {};
  const repeated: Record<string, string[]> = {};
  for (let i = 0; i < rest.length; i++) {
    const a = rest[i];
    if (!a.startsWith("--")) continue;
    const key = a.slice(2);
    const next = rest[i + 1];
    if (next && !next.startsWith("--")) {
      flags[key] = next;
      (repeated[key] ??= []).push(next);
      i++;
    } else {
      flags[key] = true;
    }
  }
  return { cmd, flags, repeated };
}

const HELP = `git-manager — see where every project lives, and what is not saved anywhere yet

  bun git-manager.ts scan [options]
      --fetch              refresh remote counts over the network first (read-only, slower)
      --all                show a detail card for every row, not just the top 5 by risk
      --width <cols>       fix the table width (default: terminal width, clamped 96-160)
      --open               open the browser view in Google Chrome (implies --html)
      --loose              also list folders holding only a script or two beside documents
      --json               print machine-readable JSON instead of the table
      --html <path>        also write a self-contained browser page to <path>
      --root <path>        scan this root instead of the configured ones (repeatable)
      --config <path>      use this config file
      --color never        disable ANSI colour

  bun git-manager.ts plan-push --repo <path> --to <remote|personal|work> [--config <path>]
      Prints the destination, the account it belongs to, the commits that would be
      sent, and the exact command to run. It does NOT push. Run the printed command
      yourself so the repo guard hook can check the destination.
      Scans the lines the push would add for credentials and BLOCKS (exit 4) if any
      are found; values are always masked. --acknowledge-secrets overrides that
      block and is a deliberate human decision, never a default.

  bun git-manager.ts decide --repo <path> --not-tracked --why "<reason>" [--date YYYY-MM-DD]
  bun git-manager.ts decide --repo <path> --undo
  bun git-manager.ts decide --list
      Record that the human ruled a folder out, so scan stops asking about it.
      The row is NOT hidden — it moves to its own "DECIDED — NOT TRACKED" table and
      keeps its real git state. --undo withdraws the ruling and the row returns to
      needs-attention. Matching is on the exact absolute path: rename or move the
      folder and the ruling stops applying, on purpose.

Exit codes: 0 ok · 2 bad input or unknown remote · 3 destination forbidden by rule
            4 suspected secret in the outgoing diff
`;

/**
 * Open the report in Google Chrome specifically, not the default handler.
 * Failing to open is never fatal — the file:// path is already printed, so the
 * report is still reachable by hand.
 */
function openInBrowser(path: string): string {
  const chrome = spawnSync("open", ["-a", "Google Chrome", path], { encoding: "utf8" });
  if (chrome.status === 0) return "opened in Google Chrome";

  const fallback = spawnSync("open", [path], { encoding: "utf8" });
  if (fallback.status === 0)
    return "Google Chrome not available — opened in the default browser instead";

  const why = (chrome.stderr || fallback.stderr || "").split("\n")[0];
  return `could not open a browser${why ? ` (${why})` : ""} — use the file:// path above`;
}

function cmdScan(args: Args): number {
  const cfg = loadConfig(args.flags.config as string | undefined);
  if (args.repeated.root?.length) cfg.roots = args.repeated.root.map((r) => resolve(r));

  const result = scan(cfg, {
    fetch: !!args.flags.fetch,
    loose: !!args.flags.loose,
    decisionsFile: args.flags["decisions-file"] as string | undefined,
  });

  // --open implies --html: there must be a file before anything can open it.
  const htmlPath =
    typeof args.flags.html === "string"
      ? resolve(args.flags.html)
      : args.flags.open
        ? join(mkdtempSync(join(tmpdir(), "git-manager-")), "git-manager.html")
        : null;

  if (htmlPath) {
    writeFileSync(htmlPath, renderHtml(result), "utf8");
    if (!args.flags.json) console.log(`browser view written: file://${encodeURI(htmlPath)}`);
    if (args.flags.open) {
      const how = openInBrowser(htmlPath);
      if (!args.flags.json) console.log(how);
    }
    if (!args.flags.json) console.log("");
  }

  if (args.flags.json) {
    console.log(JSON.stringify(result, null, 2));
    return 0;
  }

  console.log(
    renderTerminal(result, {
      color: args.flags.color !== "never",
      all: !!args.flags.all,
      width: args.flags.width ? Number.parseInt(String(args.flags.width), 10) : undefined,
    }),
  );
  return 0;
}

function cmdPlanPush(args: Args): number {
  const cfg = loadConfig(args.flags.config as string | undefined);
  const repoArg = args.flags.repo;
  const toArg = args.flags.to;

  if (typeof repoArg !== "string" || typeof toArg !== "string") {
    console.error("REFUSED — plan-push needs --repo <path> and --to <remote|personal|work>");
    return 2;
  }
  const repo = resolve(repoArg);
  if (!existsSync(join(repo, ".git"))) {
    console.error(`REFUSED — not a git repo: ${repo}`);
    return 2;
  }

  const branch = G.currentBranch(repo);
  if (!branch || branch === "HEAD") {
    console.error(`REFUSED — ${repo} is not on a branch (detached HEAD). Check out a branch first.`);
    return 2;
  }

  const all = G.remotes(repo).map((r) => ({ ...r, ...attribute(r.url, cfg) }));
  if (!all.length) {
    console.error(
      `REFUSED — ${repo} has no remotes. Add one first, then plan the push again.\n` +
        `  the repo exists only on this machine right now`,
    );
    return 2;
  }

  const wanted = toArg.toLowerCase();

  // Refuse on the standing rule BEFORE looking for a remote, so the answer is
  // "this destination is forbidden", not the weaker "no such remote here".
  if (wanted === "personal" || wanted === "work" || wanted === "other") {
    const early = isForbidden(repo, wanted as AccountKind, cfg);
    if (early) {
      console.error(
        `REFUSED — pushing this repo to the ${wanted} account is forbidden.\n` +
          `  reason: ${early.reason}\n` +
          `  repo:   ${repo}\n` +
          `  No command is printed. This refusal is not overridable from inside this tool.`,
      );
      return 3;
    }
  }

  let matches = all.filter((r) => r.name.toLowerCase() === wanted);
  if (!matches.length) matches = all.filter((r) => r.account === (wanted as AccountKind));

  if (!matches.length) {
    console.error(
      `REFUSED — no remote on ${repo} matches "${toArg}".\n  available:\n` +
        all.map((r) => `    ${r.name}  →  ${r.label}  ${r.url}`).join("\n"),
    );
    return 2;
  }
  if (matches.length > 1) {
    console.error(
      `AMBIGUOUS — "${toArg}" matches more than one remote. Name one exactly:\n` +
        matches.map((r) => `    ${r.name}  →  ${r.label}  ${r.url}`).join("\n"),
    );
    return 2;
  }

  const target = matches[0];
  const rule = isForbidden(repo, target.account, cfg);
  if (rule) {
    console.error(
      `REFUSED — pushing this repo to ${target.label} is forbidden.\n` +
        `  reason: ${rule.reason}\n` +
        `  repo:   ${repo}\n` +
        `  remote: ${target.name} → ${target.url}\n` +
        `  No command is printed. This refusal is not overridable from inside this tool.`,
    );
    return 3;
  }

  const ref = `${target.name}/${branch}`;
  const hasRef = G.refExists(repo, ref);
  const range = hasRef ? `${ref}..HEAD` : "HEAD";
  const count = hasRef ? G.countCommits(repo, range) : G.totalCommits(repo);
  const subjects = G.commitSubjects(repo, range, 10);
  const dirty = G.dirtyCount(repo);
  const behind = hasRef ? G.countCommits(repo, `HEAD..${ref}`) : 0;

  const L: string[] = [];
  L.push("PUSH PLAN — nothing has been pushed. This is a preview.");
  L.push("");
  L.push(`  repo         ${repo}`);
  L.push(`  branch       ${branch}`);
  L.push(`  remote       ${target.name}`);
  L.push(`  url          ${target.url}`);
  L.push(`  ACCOUNT      ${target.label}`);
  L.push("");
  if (!hasRef) {
    L.push(
      `  this branch has never been pushed to "${target.name}" as far as this machine knows,`,
    );
    L.push(`  so the push would send its full history: ${count ?? "?"} commits.`);
  } else {
    L.push(`  commits that would be sent: ${count ?? "?"}`);
  }
  if (subjects.length) {
    L.push("");
    for (const s of subjects) L.push(`    ${s}`);
    if ((count ?? 0) > subjects.length) L.push(`    … and ${(count ?? 0) - subjects.length} more`);
  }
  L.push("");
  if (dirty > 0) {
    L.push(
      `  WARNING: ${dirty} file${dirty === 1 ? "" : "s"} changed but not committed. A push sends`,
    );
    L.push(`  only committed work — those ${dirty} would stay behind on this machine.`);
  }
  if ((behind ?? 0) > 0) {
    L.push(
      `  WARNING: ${behind} commit${
        behind === 1 ? "" : "s"
      } exist on ${ref} that you do not have locally.`,
    );
    L.push(`  Pull first, or the push will be rejected as non-fast-forward.`);
  }
  if (!G.refExists(repo, ref) && !G.upstreamRef(repo)) {
    L.push(`  NOTE: this branch has no upstream set. The command below names the remote and`);
    L.push(`  branch explicitly, which works without an upstream.`);
  }
  // ---- secret gate -------------------------------------------------------
  // Scan the lines this push would ADD. A credential that reaches a place other
  // people can read must be rotated even if the commit is later removed, so the
  // cheapest moment to catch it is now.
  const diff = G.addedLines(repo, hasRef ? range : "HEAD");
  const hits = scanForSecrets(diff.lines);

  if (hits.length) {
    const S: string[] = [];
    S.push("BLOCKED — this push would send lines that look like credentials.");
    S.push("");
    S.push(`  repo    ${repo}`);
    S.push(`  branch  ${branch}`);
    S.push(`  remote  ${target.name} → ${target.label}`);
    S.push("");
    S.push(`  ${hits.length} suspected secret${hits.length === 1 ? "" : "s"} (values masked):`);
    S.push("");
    for (const h of hits.slice(0, 25)) {
      S.push(`    ${h.file}:${h.line}  ${h.rule}`);
      S.push(`      ${h.masked}`);
    }
    if (hits.length > 25) S.push(`    … and ${hits.length - 25} more`);
    if (diff.truncated)
      S.push(
        "\n  NOTE: the diff was larger than the scan limit and was cut short. There may be more.",
      );
    S.push("");
    S.push("  No push command is printed. Deleting a pushed key does NOT un-expose it:");
    S.push("  rotate anything real, and remove it from the commits before pushing.");
    S.push("");
    S.push("  If every hit is a false alarm, re-run this exact command with");
    S.push("  --acknowledge-secrets and the plan will print. That flag is a human decision.");
    if (args.flags["acknowledge-secrets"]) {
      S.push("");
      S.push("  --acknowledge-secrets WAS PASSED — the findings above stand, and the plan follows.");
      console.log(S.join("\n"));
      L[0] =
        `PUSH PLAN — ${hits.length} secret warning${
          hits.length === 1 ? "" : "s"
        } ACKNOWLEDGED, not resolved. Nothing has been pushed yet.`;
    } else {
      console.error(S.join("\n"));
      return 4;
    }
  } else if (diff.truncated) {
    L.push("  NOTE: the diff was larger than the secret-scan limit and was only partly scanned.");
    L.push("");
  }

  L.push("");
  L.push("  RUN THIS COMMAND to perform the push (the repo guard will ask you to confirm):");
  L.push("");
  L.push(`    git -C ${JSON.stringify(repo)} push ${target.name} ${branch}`);
  L.push("");
  L.push("  This tool does not run it. Naming the remote in the command is what keeps the");
  L.push("  destination visible in the transcript.");

  console.log(L.join("\n"));
  return 0;
}

/**
 * Record, withdraw, or list the human's rulings.
 *
 * This is the ONLY command that writes anything, and it writes one small JSON
 * file. It never touches a repo, never runs git, and never pushes. Recording a
 * ruling is a statement about attention, not about content.
 */
function cmdDecide(args: Args): number {
  const file = args.flags["decisions-file"] as string | undefined;

  if (args.flags.list) {
    const { path, decisions } = loadDecisions(file);
    console.log(`decisions file: ${path}`);
    if (!decisions.length) {
      console.log("  (empty — nothing has been ruled out yet)");
      return 0;
    }
    for (const d of decisions) {
      console.log(`\n  ${d.path}`);
      console.log(`    ruled   do-not-track${d.date ? ` on ${d.date}` : ""}`);
      console.log(`    reason  ${d.reason || "(none recorded)"}`);
    }
    return 0;
  }

  const repoArg = args.flags.repo;
  if (typeof repoArg !== "string") {
    console.error('REFUSED — decide needs --repo <path>, or --list to show what is recorded');
    return 2;
  }
  const target = resolve(repoArg);

  if (args.flags.undo) {
    const { path, removed } = forgetDecision(target, file);
    if (!removed) {
      console.error(`REFUSED — no ruling is recorded for that exact path:\n  ${target}`);
      console.error(`  file: ${path}\n  Run decide --list to see the paths that ARE recorded.`);
      return 2;
    }
    console.log(`WITHDRAWN — the ruling for this path is gone.\n`);
    console.log(`  path    ${removed.path}`);
    console.log(`  was     do-not-track${removed.date ? ` on ${removed.date}` : ""}`);
    console.log(`  reason  ${removed.reason || "(none recorded)"}`);
    console.log(`  file    ${path}\n`);
    console.log("  The row returns to NEEDS ATTENTION on the next scan. That is the point:");
    console.log("  withdrawing a ruling puts the question back rather than leaving a gap.");
    return 0;
  }

  if (!args.flags["not-tracked"]) {
    console.error(
      'REFUSED — decide needs a verdict. The only one that exists is --not-tracked.\n' +
        '  "track it later" is not a ruling; it is an item still on the list.',
    );
    return 2;
  }

  const why = args.flags.why;
  if (typeof why !== "string" || !why.trim()) {
    console.error(
      'REFUSED — decide needs --why "<reason>".\n' +
        "  A ruling with no reason cannot be reviewed later, and an unreviewable\n" +
        "  ruling is indistinguishable from the tool having simply forgotten.",
    );
    return 2;
  }

  // The date is supplied, never read from the clock here: a module that reads the
  // clock cannot be tested against a fixed expectation.
  const dateArg = args.flags.date;
  const date =
    typeof dateArg === "string" && /^\d{4}-\d{2}-\d{2}$/.test(dateArg)
      ? dateArg
      : new Date().toISOString().slice(0, 10);

  if (!existsSync(target))
    console.log(`NOTE: nothing exists at that path right now — recording the ruling anyway.\n`);

  const { path, action, previous } = recordDecision(
    { path: target, decision: "do-not-track", date, reason: why.trim() },
    file,
  );

  console.log(`${action === "added" ? "RECORDED" : "REPLACED"} — this path will stop being asked about.\n`);
  if (previous) {
    console.log(`  previous  do-not-track${previous.date ? ` on ${previous.date}` : ""}`);
    console.log(`            ${previous.reason || "(none recorded)"}\n`);
  }
  console.log(`  path      ${target}`);
  console.log(`  ruled     do-not-track on ${date}`);
  console.log(`  reason    ${why.trim()}`);
  console.log(`  file      ${path}\n`);
  console.log("  The row is NOT hidden. It moves to the DECIDED — NOT TRACKED table and");
  console.log("  keeps its real git state, so the ruling stays visible and reversible");
  console.log("  with: decide --repo <path> --undo");
  return 0;
}

function main(): number {
  const args = parseArgs(process.argv.slice(2));
  if (args.flags.help || args.cmd === "help") {
    console.log(HELP);
    return 0;
  }
  switch (args.cmd) {
    case "scan":
      return cmdScan(args);
    case "plan-push":
      return cmdPlanPush(args);
    case "decide":
      return cmdDecide(args);
    default:
      console.error(`unknown command: ${args.cmd}\n\n${HELP}`);
      return 2;
  }
}

/**
 * A refusal this tool raises deliberately must reach the user as the sentence it
 * was written as, not as a stack trace with the message buried in it. Anything
 * else is an internal fault and keeps its trace, because hiding one would make a
 * real bug look like a polite refusal.
 */
function isDeliberateRefusal(e: unknown): e is Error {
  const m = e instanceof Error ? e.message : "";
  return m.startsWith("decisions file is present but unreadable") || m.startsWith("no config found");
}

try {
  process.exit(main());
} catch (e) {
  if (isDeliberateRefusal(e)) {
    console.error(`REFUSED — ${e.message}`);
    process.exit(2);
  }
  throw e;
}
