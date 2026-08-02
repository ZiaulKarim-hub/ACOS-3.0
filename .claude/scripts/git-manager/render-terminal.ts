// git-manager — the terminal report.
//
// A pure function of the ScanResult. It decorates nothing the scanner did not
// compute, and it hides no row: risky rows go first, clean rows still appear.
//
// Layout goals, in order:
//   1. a wrong-account push must be the loudest thing on the screen
//   2. every column must line up, at any terminal width
//   3. the reader must be able to point at a row number and act
// Detail is rendered as bounded cards, not a wall of indented text.

import { groupByHost } from "./inventory.ts";
import type { RepoRow, ScanResult, StateKey } from "./types.ts";

/* ---------------------------------------------------------------- colour -- */

const C = {
  reset: "\x1b[0m",
  dim: "\x1b[2m",
  bold: "\x1b[1m",
  red: "\x1b[31m",
  yellow: "\x1b[33m",
  green: "\x1b[32m",
  cyan: "\x1b[36m",
  magenta: "\x1b[35m",
  blue: "\x1b[34m",
  redBg: "\x1b[41m\x1b[97m",
};

let useColor = true;
function c(code: string, s: string): string {
  return useColor ? `${code}${s}${C.reset}` : s;
}

/* ------------------------------------------------------------- constants -- */

const STATE_LABEL: Record<StateKey, string> = {
  NOT_A_REPO: "NOT A REPO",
  NO_REMOTE: "NO REMOTE",
  UNCOMMITTED: "UNCOMMITTED",
  NO_UPSTREAM: "NO UPSTREAM",
  AHEAD: "UNPUSHED",
  PARTIAL: "PARTIAL",
  BRANCH_WORK: "SIDE BRANCH",
  SYNCED: "SAFE",
};

const STATE_COLOR: Record<StateKey, string> = {
  NOT_A_REPO: C.red,
  NO_REMOTE: C.red,
  UNCOMMITTED: C.yellow,
  NO_UPSTREAM: C.yellow,
  AHEAD: C.yellow,
  PARTIAL: C.cyan,
  BRANCH_WORK: C.cyan,
  SYNCED: C.green,
};

const STATE_FIX: Record<StateKey, string> = {
  NOT_A_REPO: "never tracked by git — no copy exists anywhere but here",
  NO_REMOTE: "a repo with no online destination — still only on this machine",
  UNCOMMITTED: "files changed but not yet saved into git history",
  NO_UPSTREAM: "the branch has no matching online branch set",
  AHEAD: "saved locally, but those commits were never sent up",
  PARTIAL: "one destination has it, another does not",
  BRANCH_WORK: "current branch is clean, another local branch is not",
  SYNCED: "every destination has what this machine has",
};

const B = {
  h: "─",
  v: "│",
  tl: "┌",
  tr: "┐",
  bl: "└",
  br: "┘",
  tj: "┬",
  bj: "┴",
  lj: "├",
  rj: "┤",
  x: "┼",
};

/* ----------------------------------------------------------------- utils -- */

function visibleWidth(s: string): number {
  return s.replace(/\x1b\[[0-9;]*m/g, "").length;
}

function padRight(s: string, w: number): string {
  const d = w - visibleWidth(s);
  return d > 0 ? s + " ".repeat(d) : s;
}

function padLeft(s: string, w: number): string {
  const d = w - visibleWidth(s);
  return d > 0 ? " ".repeat(d) + s : s;
}

/**
 * Truncate to `w` VISIBLE characters, stepping over ANSI colour codes rather
 * than counting them. Measuring raw string length here is what makes a coloured
 * cell overflow its border while an uncoloured one fits.
 */
function trunc(s: string, w: number): string {
  if (w <= 0) return "";
  if (visibleWidth(s) <= w) return s;

  let out = "";
  let seen = 0;
  let i = 0;
  const limit = w - 1; // leave room for the ellipsis
  while (i < s.length && seen < limit) {
    if (s[i] === "\x1b") {
      const end = s.indexOf("m", i);
      if (end === -1) break;
      out += s.slice(i, end + 1);
      i = end + 1;
      continue;
    }
    out += s[i];
    i++;
    seen++;
  }
  return `${out}${useColor ? C.reset : ""}…`;
}

function plural(n: number, word: string): string {
  return `${n} ${word}${n === 1 ? "" : "s"}`;
}

/** First `n` names, then an honest count of what was not shown. */
function listSome(items: string[], n: number): string {
  return items.length <= n
    ? items.join(", ")
    : `${items.slice(0, n).join(", ")} (+${items.length - n} more — see --json)`;
}

/** "ZiaulKarim-hub (personal)" -> "ZiaulKarim-hub" — the account, not the nickname. */
function ownerOf(label: string): string {
  return label.replace(/\s*\([^)]*\)\s*$/, "");
}

function accountColour(kind: string): string {
  return kind === "personal" ? C.magenta : kind === "work" ? C.blue : C.red;
}

/** ISO timestamp to a compact calendar date; --json keeps the full value. */
function shortDate(iso: string | null): string {
  return iso ? iso.slice(0, 10) : "—";
}

/* ----------------------------------------------------------------- table -- */

interface Col {
  head: string;
  width: number;
  align: "l" | "r";
}

function rule(cols: Col[], left: string, join: string, right: string): string {
  return c(
    C.dim,
    left + cols.map((col) => B.h.repeat(col.width + 2)).join(join) + right,
  );
}

function tableRow(cells: string[], cols: Col[]): string {
  const bar = c(C.dim, B.v);
  const body = cols
    .map((col, i) => {
      const cell = cells[i] ?? "";
      return ` ${col.align === "r" ? padLeft(cell, col.width) : padRight(cell, col.width)} `;
    })
    .join(bar);
  return bar + body + bar;
}

function headerRow(cols: Col[]): string {
  return tableRow(
    cols.map((col) => c(C.dim, col.head)),
    cols,
  );
}

/** Where a row can go, or — when it can go nowhere — what would be lost. */
function destinationCell(r: RepoRow): string {
  if (!r.isRepo || !r.remotes.length) {
    const holds = r.inventory.summary === "—" ? "contents not recognised" : r.inventory.summary;
    return `${c(C.red, "nowhere")} ${c(C.dim, "·")} ${holds}`;
  }
  return r.remotes
    .map((rm) => {
      const waiting = rm.unpushed ?? 0;
      const mark = waiting > 0 ? c(C.yellow, `+${waiting}`) : c(C.green, "ok");
      return `${rm.name}${c(C.dim, "→")}${c(accountColour(rm.account), ownerOf(rm.accountLabel))} ${mark}`;
    })
    .join(c(C.dim, "  ·  "));
}

/**
 * Column widths are computed ONCE from every row in the report, not per table,
 * so the "needs attention" and "safely stored" tables line up as one grid.
 */
function layout(all: RepoRow[], termWidth: number): Col[] {
  const numW = Math.max(2, String(all.length).length);
  const stateW = 11;
  const unsavedW = 7;
  const waitW = 7;
  const NAME_MIN = 10;
  const DEST_WANT = 24;

  // Each of the 6 cells costs its width + 2 spaces; 7 vertical bars enclose them.
  const chrome = 6 * 2 + 7;
  const free = termWidth - (numW + stateW + unsavedW + waitW) - chrome;

  // The two flexible columns must together consume `free` EXACTLY. Flooring one
  // of them instead is what pushes the table past its own border.
  let nameW = Math.min(30, Math.max(NAME_MIN, ...all.map((r) => Math.min(r.name.length, 30))));
  if (free - nameW < DEST_WANT) nameW = Math.max(NAME_MIN, free - DEST_WANT);
  const destW = Math.max(6, free - nameW);

  return [
    { head: "#", width: numW, align: "r" },
    { head: "PROJECT", width: nameW, align: "l" },
    { head: "STATE", width: stateW, align: "l" },
    { head: "UNSAVED", width: unsavedW, align: "r" },
    { head: "WAITING", width: waitW, align: "r" },
    { head: "WHERE IT CAN GO", width: destW, align: "l" },
  ];
}

function buildTable(rows: RepoRow[], cols: Col[]): string[] {
  const nameW = cols[1].width;
  const destW = cols[5].width;
  const out: string[] = [];
  out.push(rule(cols, B.tl, B.tj, B.tr));
  out.push(headerRow(cols));
  out.push(rule(cols, B.lj, B.x, B.rj));

  for (const r of rows) {
    const waiting = Math.max(0, ...r.remotes.map((x) => x.unpushed ?? 0));
    const unsaved = r.flags.uncommitted;
    const flag = r.risk.ruleViolations.length ? c(C.red, "!") : "";
    const name = trunc(r.name, nameW - (flag ? 2 : 0));

    out.push(
      tableRow(
        [
          String(r.index),
          flag ? `${flag} ${name}` : name,
          c(STATE_COLOR[r.state], STATE_LABEL[r.state]),
          unsaved ? c(C.yellow, String(unsaved)) : c(C.dim, "—"),
          waiting ? c(C.yellow, String(waiting)) : c(C.dim, "—"),
          trunc(destinationCell(r), destW),
        ],
        cols,
      ),
    );
  }
  out.push(rule(cols, B.bl, B.bj, B.br));
  return out;
}

/* ------------------------------------------------------------------ card -- */

const LABEL_W = 13;

function card(r: RepoRow, width: number): string[] {
  // width counts the border characters; content lives inside a 1-space margin.
  const inner = width - 4;
  const valueW = inner - LABEL_W;
  const bar = c(C.dim, B.v);
  const L: string[] = [];

  /* title bar: "┌─ 1 · .claude ─────────── NOT A REPO ─┐" */
  const state = ` ${STATE_LABEL[r.state]} `;
  // Corners (2) + the two single rules (2) + at least one fill character.
  const maxLeft = Math.max(4, width - 5 - visibleWidth(state));
  const left = trunc(` ${r.index} · ${r.name} `, Math.min(52, maxLeft));
  const fill = Math.max(1, width - 2 - 1 - visibleWidth(left) - visibleWidth(state) - 1);
  L.push(
    c(C.dim, B.tl + B.h) +
      c(C.bold, left) +
      c(C.dim, B.h.repeat(fill)) +
      c(STATE_COLOR[r.state], state) +
      c(C.dim, B.h + B.tr),
  );

  /** A label/value row, padded so the right border stays true. */
  const line = (label: string, value: string) => {
    const body = c(C.dim, padRight(trunc(label, LABEL_W - 1), LABEL_W)) + trunc(value, valueW);
    L.push(`${bar} ${padRight(body, inner)} ${bar}`);
  };
  const note = (text: string, colour: string) => {
    const body = c(colour, trunc(text, inner));
    L.push(`${bar} ${padRight(body, inner)} ${bar}`);
  };

  line("path", r.path);
  if (r.parentRepo) line("inside", r.parentRepo);
  line("holds", r.inventory.summary);

  if (r.inventory.skills.length) line("skills", listSome(r.inventory.skills, 6));
  for (const g of groupByHost(r.inventory.linkedSkills)) {
    line("linked in", `${plural(g.names.length, "skill")} hosted by ${c(C.cyan, g.host)}`);
  }
  if (r.inventory.subProjects.length)
    line("sub-projects", listSome(r.inventory.subProjects, 6));

  if (r.isRepo) {
    line("branch", `${r.branch ?? "?"}   last commit ${shortDate(r.lastCommitISO)}`);
    if (!r.remotes.length) note("no remotes — this repo exists only on this machine", C.red);
    for (const rm of r.remotes) {
      const waiting = rm.unpushed ?? 0;
      const status =
        waiting > 0
          ? c(C.yellow, `${plural(waiting, "commit")} waiting`)
          : c(C.green, "up to date");
      const extra = [
        !rm.hasBranchRef ? c(C.red, "branch never pushed here") : "",
        (rm.behind ?? 0) > 0 ? c(C.dim, `${rm.behind} to pull`) : "",
        rm.isUpstream ? c(C.dim, "default") : "",
      ].filter(Boolean);
      line(
        rm.name,
        `${c(accountColour(rm.account), rm.accountLabel)}  ${status}${
          extra.length ? `  ${c(C.dim, "·")} ${extra.join(c(C.dim, " · "))}` : ""
        }`,
      );
      line("", c(C.dim, rm.url));
    }
    for (const b of r.otherBranches) {
      const w = b.waiting
        .map((x) => `${x.remote} +${x.count}${x.neverPushed ? " (never pushed)" : ""}`)
        .join(", ");
      line("branch", `${c(C.yellow, b.branch)}  ${w}`);
    }
  }

  for (const v of r.risk.ruleViolations)
    note(`!  RULE BREACH — remote "${v.remote}": ${v.rule.reason}`, C.red);
  if (r.risk.bothAccounts)
    note("!  both accounts wired here — always name the remote when pushing", C.yellow);
  for (const n of r.notes) note(n, C.dim);

  L.push(c(C.dim, B.bl + B.h.repeat(width - 2) + B.br));
  return L;
}

/* ---------------------------------------------------------------- render -- */

export function renderTerminal(
  scan: ScanResult,
  opts: { color?: boolean; all?: boolean; width?: number } = {},
): string {
  useColor = opts.color !== false;
  const width = Math.max(96, Math.min(opts.width ?? process.stdout.columns ?? 120, 160));

  const attention = scan.rows.filter((r) => r.attention);
  const clean = scan.rows.filter((r) => !r.attention);
  const violations = scan.rows.filter((r) => r.risk.ruleViolations.length);
  const L: string[] = [];

  /* ---- banner ---- */
  const stamp = `${scan.generatedAtISO.slice(0, 10)} ${scan.generatedAtISO.slice(11, 16)} UTC`;
  const title = "GIT MANAGER";
  // Build the inside as plain text first, then colour it. Padding measured on
  // the coloured string is what puts a border one character out of true.
  const gap = Math.max(1, width - 4 - title.length - stamp.length);
  L.push(c(C.dim, "╭" + "─".repeat(width - 2) + "╮"));
  L.push(
    c(C.dim, "│") +
      " " +
      c(C.bold, title) +
      " ".repeat(gap) +
      c(C.dim, stamp) +
      " " +
      c(C.dim, "│"),
  );
  L.push(c(C.dim, "╰" + "─".repeat(width - 2) + "╯"));
  L.push("");

  /* ---- counters ---- */
  const stat = (n: number, label: string, colour: string) =>
    `${c(colour, String(n))} ${c(C.dim, label)}`;
  L.push(
    "  " +
      [
        stat(scan.totals.repos, "repos", C.bold),
        stat(scan.totals.notRepos, "untracked", scan.totals.notRepos ? C.red : C.dim),
        stat(scan.totals.needAttention, "need attention", attention.length ? C.yellow : C.dim),
        stat(scan.totals.clean, "safe", C.green),
        stat(scan.totals.uncommittedFiles, "unsaved files", C.dim),
      ].join(c(C.dim, "   ·   ")),
  );
  L.push("");

  /* ---- scope + honesty notes ---- */
  const notes: string[] = [];
  notes.push(`roots  ${scan.roots.join("  ·  ")}`);
  notes.push(
    scan.fetched
      ? "counts refreshed from the network on this run"
      : "counts are as of each repo's last fetch — add --fetch for live numbers",
  );
  if (scan.filteredWeak.count > 0 && !scan.loose)
    notes.push(
      `${plural(scan.filteredWeak.count, "folder")} holding only a script or two beside documents left out — add --loose`,
    );
  if (scan.ignoredCount > 0)
    notes.push(
      `${plural(scan.ignoredCount, "untracked folder")} hidden by the config ignore rules — repos are never hidden this way`,
    );
  for (const n of notes) L.push(c(C.dim, `  ${n}`));
  L.push("");

  /* ---- breach banner ---- */
  if (violations.length) {
    L.push("  " + c(C.redBg, ` WRONG-ACCOUNT RULE BREACH · ${violations.length} `));
    for (const r of violations)
      for (const v of r.risk.ruleViolations)
        L.push(`  ${c(C.red, `${r.name} — remote "${v.remote}": ${v.rule.reason}`)}`);
    L.push("");
  }

  /* ---- tables (one shared grid so both line up) ---- */
  const inner = width - 2;
  const cols = layout(scan.rows, inner);
  if (attention.length) {
    L.push("  " + c(C.bold, "NEEDS ATTENTION") + c(C.dim, `  ${attention.length}`));
    L.push(...buildTable(attention, cols).map((l) => "  " + l));
    L.push("");
  }
  if (clean.length) {
    L.push("  " + c(C.bold, "SAFELY STORED") + c(C.dim, `  ${clean.length}`));
    L.push(...buildTable(clean, cols).map((l) => "  " + l));
    L.push("");
  }

  /* ---- detail cards ---- */
  const DEFAULT_CARDS = 5;
  const cardRows = opts.all ? scan.rows : attention.slice(0, DEFAULT_CARDS);
  if (cardRows.length) {
    const heading = opts.all
      ? "DETAIL · every row"
      : `DETAIL · top ${cardRows.length} by risk`;
    L.push("  " + c(C.bold, heading));
    L.push("");
    for (const r of cardRows) {
      L.push(...card(r, inner).map((l) => "  " + l));
      L.push("");
    }
    if (!opts.all && attention.length > cardRows.length) {
      L.push(
        c(
          C.dim,
          `  ${attention.length - cardRows.length} more rows need attention — add --all for every card, or --json for the full data`,
        ),
      );
      L.push("");
    }
  }

  /* ---- legend ---- */
  L.push("  " + c(C.bold, "WHAT EACH STATE MEANS"));
  for (const k of Object.keys(STATE_FIX) as StateKey[]) {
    L.push(`  ${padRight(c(STATE_COLOR[k], STATE_LABEL[k]), 12)} ${c(C.dim, STATE_FIX[k])}`);
  }
  L.push("");
  L.push(
    c(C.dim, "  rows are ordered worst first; within one state, by how much work sits there"),
  );
  L.push(c(C.dim, '  next: name a row number and a destination — e.g. "push 27 to origin"'));
  L.push(c(C.dim, "  nothing is pushed until you say so"));

  return L.join("\n");
}
