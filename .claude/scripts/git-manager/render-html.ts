// git-manager — the browser view.
//
// Self-contained single file: no external stylesheet, no script from the network,
// works offline. Same data as the terminal table, more room to breathe. Light and
// dark are both styled because the page is opened straight from the filesystem.

import { groupByHost } from "./inventory.ts";
import type { RepoRow, ScanResult, StateKey } from "./types.ts";

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

const STATE_HELP: Record<StateKey, string> = {
  NOT_A_REPO: "git has never tracked this folder — no copy exists anywhere but here",
  NO_REMOTE: "it is a repo, but no online destination is set up — still only on this machine",
  UNCOMMITTED: "files changed but not yet saved into git history",
  NO_UPSTREAM: "the branch has no matching online branch set",
  AHEAD: "saved locally, but those commits were never sent up",
  PARTIAL: "sent to one destination but not to every destination this repo has",
  BRANCH_WORK: "the branch you are on is clean, but another local branch has unsent commits",
  SYNCED: "nothing waiting — every destination has what this machine has",
};

function esc(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function accountClass(kind: string): string {
  return kind === "personal" ? "acc-personal" : kind === "work" ? "acc-work" : "acc-other";
}

function rowHtml(r: RepoRow): string {
  const waiting = Math.max(0, ...r.remotes.map((x) => x.unpushed ?? 0));
  const holdsCell = `<span class="danger">nowhere but here</span><div class="muted">holds ${esc(
    r.inventory.summary === "—" ? "contents not recognised" : r.inventory.summary,
  )}</div>`;

  const dests = r.isRepo
    ? r.remotes.length
      ? r.remotes
          .map(
            (rm) =>
              `<span class="dest"><code>${esc(rm.name)}</code> → <span class="${accountClass(
                rm.account,
              )}">${esc(rm.accountLabel)}</span>${
                (rm.unpushed ?? 0) > 0
                  ? ` <span class="wait">+${rm.unpushed}</span>`
                  : ` <span class="ok">ok</span>`
              }${!rm.hasBranchRef ? ` <span class="never">never pushed here</span>` : ""}</span>`,
          )
          .join("")
      : holdsCell
    : holdsCell;

  const violations = r.risk.ruleViolations
    .map(
      (v) =>
        `<div class="violation">RULE BREACH — remote <code>${esc(
          v.remote,
        )}</code>: ${esc(v.rule.reason)}</div>`,
    )
    .join("");

  const both = r.risk.bothAccounts
    ? `<div class="warn">Both accounts are wired into this repo — always name the remote when pushing.</div>`
    : "";

  const remoteDetail = r.remotes
    .map(
      (rm) =>
        `<li><code>${esc(rm.name)}</code> → <span class="${accountClass(rm.account)}">${esc(
          rm.accountLabel,
        )}</span><br><code class="url">${esc(rm.url)}</code><br>${
          (rm.unpushed ?? 0) > 0
            ? `<span class="wait">${rm.unpushed} commit${
                rm.unpushed === 1 ? "" : "s"
              } waiting to be sent</span>`
            : `<span class="ok">up to date</span>`
        }${!rm.hasBranchRef ? ` <span class="never">(branch never pushed here)</span>` : ""}${
          (rm.behind ?? 0) > 0 ? ` <span class="muted">· ${rm.behind} to pull</span>` : ""
        }${rm.isUpstream ? ` <span class="muted">· default destination</span>` : ""}</li>`,
    )
    .join("");

  const rec = r.recommendation;
  const actionClass = !rec
    ? ""
    : rec.action.startsWith("check vs")
      ? "act-check"
      : rec.action.startsWith("git init") || rec.action.startsWith("commit,")
        ? "act-init"
        : rec.action.startsWith("commit ") || rec.action.startsWith("add remote")
          ? "act-commit"
          : rec.action.startsWith("push") || rec.action.startsWith("checkout")
            ? "act-push"
            : "act-none";

  return `<tr class="sev-${r.severity >= 90 ? "hi" : r.severity >= 25 ? "mid" : "lo"}${
    r.decided ? " is-decided" : ""
  }">
  <td class="num">${r.index}</td>
  <td class="name"><strong>${esc(r.name)}</strong><div class="path">${esc(r.path)}</div>${violations}${both}</td>
  <td><span class="kind k-${rec?.kind ?? "docs"}">${esc(rec?.kind ?? "—")}</span></td>
  <td><span class="state s-${r.state}" title="${esc(STATE_HELP[r.state])}">${
    STATE_LABEL[r.state]
  }</span></td>
  <td class="num">${r.flags.uncommitted || "—"}</td>
  <td class="num">${waiting || "—"}</td>
  <td class="doit"><span class="${actionClass}">${esc(rec?.action ?? "—")}</span>${
    rec ? `<div class="why">${esc(rec.why)}</div>` : ""
  }</td>
  <td class="dests">${dests}</td>
  <td class="holds">${esc(r.inventory.summary)}
    <details><summary>details</summary>
      <div class="det">
        ${r.branch ? `<div>branch <code>${esc(r.branch)}</code></div>` : ""}
        ${r.lastCommitISO ? `<div class="muted">last commit ${esc(r.lastCommitISO)}</div>` : ""}
        ${
          r.inventory.skills.length
            ? `<div><b>skills (${r.inventory.skills.length})</b><br>${esc(
                r.inventory.skills.join(", "),
              )}</div>`
            : ""
        }
        ${
          r.inventory.subProjects.length
            ? `<div><b>sub-projects</b><br>${esc(r.inventory.subProjects.join(", "))}</div>`
            : ""
        }
        ${groupByHost(r.inventory.linkedSkills)
          .map(
            (g) =>
              `<div><b>${g.names.length} skill${
                g.names.length === 1 ? "" : "s"
              } linked in — hosted by ${esc(g.host)}</b><br>${esc(g.names.join(", "))}</div>`,
          )
          .join("")}
        ${
          r.otherBranches.length
            ? `<div><b>other local branches with unsent commits</b><ul class="remotes">${r.otherBranches
                .map(
                  (b) =>
                    `<li><code>${esc(b.branch)}</code> — ${b.waiting
                      .map(
                        (w) =>
                          `${esc(w.remote)} <span class="wait">+${w.count}</span>${
                            w.neverPushed ? ` <span class="never">never pushed</span>` : ""
                          }`,
                      )
                      .join(", ")}</li>`,
                )
                .join("")}</ul></div>`
            : ""
        }
        ${remoteDetail ? `<ul class="remotes">${remoteDetail}</ul>` : ""}
        ${r.notes.map((n) => `<div class="muted">${esc(n)}</div>`).join("")}
      </div>
    </details>
  </td>
</tr>`;
}

export function renderHtml(scan: ScanResult): string {
  const attention = scan.rows.filter((r) => r.attention);
  // Same three buckets as the terminal view — see render-terminal.ts for why a
  // decided row belongs in neither "needs attention" nor "safely stored".
  const decided = scan.rows.filter((r) => r.decided);
  const clean = scan.rows.filter((r) => !r.attention && !r.decided);
  const violations = scan.rows.filter((r) => r.risk.ruleViolations.length);

  const head = `<tr><th>#</th><th>Project</th><th>Kind</th><th>State</th><th>Unsaved</th><th>Waiting</th><th>Do this</th><th>Destinations</th><th>What lives here</th></tr>`;

  // Explicit share of the page per column. With table-layout:fixed these are the
  // ACTUAL widths, not suggestions, so no single long path or reason can widen a
  // column and push the table off the page. They total exactly 100.
  const colgroup =
    `<colgroup>` +
    [
      ["num", 4], // #
      ["", 18], // Project — carries the full path underneath
      ["", 7], // Kind
      ["", 9], // State
      ["", 7], // Unsaved — wide enough for its own header word
      ["", 7], // Waiting — ditto
      ["", 20], // Do this — widest, because it is read first
      ["", 15], // Destinations
      ["", 13], // What lives here
    ]
      .map(([cls, w]) => `<col${cls ? ` class="c-${cls}"` : ""} style="width:${w}%">`)
      .join("") +
    `</colgroup>`;

  return `<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Git Manager — ${esc(scan.generatedAtISO)}</title>
<style>
:root{--bg:#fbfaf8;--fg:#1c1b19;--muted:#6b6862;--line:#e2ded7;--card:#fff;
--red:#b3261e;--amber:#8a6100;--green:#1d6b3f;--personal:#6d2f8f;--work:#1b4f8a;--chip:#f0ece5}
@media (prefers-color-scheme:dark){:root{--bg:#14130f;--fg:#eae7e0;--muted:#9a958c;--line:#2e2b25;
--card:#1c1a16;--red:#ff8a80;--amber:#e0b24c;--green:#6fd39a;--personal:#c99bec;--work:#8ab8ea;--chip:#252219}}
*{box-sizing:border-box}
body{margin:0;padding:32px 28px 64px;background:var(--bg);color:var(--fg);
font:14px/1.55 ui-sans-serif,-apple-system,"Segoe UI",sans-serif;
max-width:1400px;margin-inline:auto}
h1{font-size:22px;margin:0 0 6px;letter-spacing:-.01em}
h2{font-size:12px;margin:32px 0 10px;letter-spacing:.09em;text-transform:uppercase;
color:var(--muted);font-weight:600}
h2 .count{color:var(--fg);opacity:.55;margin-left:6px;font-variant-numeric:tabular-nums}
.meta{color:var(--muted);font-size:12px;margin-bottom:3px}
.stats{display:flex;flex-wrap:wrap;gap:0 28px;margin:18px 0 20px;
padding:14px 18px;border:1px solid var(--line);border-radius:10px;background:var(--card)}
.stat{display:flex;flex-direction:column;gap:2px}
.stat b{font-size:20px;font-weight:650;font-variant-numeric:tabular-nums;line-height:1.1}
.stat span{font-size:11px;color:var(--muted);letter-spacing:.04em;text-transform:uppercase}
.stat.warn b{color:var(--amber)} .stat.bad b{color:var(--red)} .stat.good b{color:var(--green)}
thead th{position:sticky;top:0;background:var(--card);z-index:1}
tbody tr:hover td{background:var(--chip)}
/* The table must FIT the page. Two things used to stop it:
   1. automatic column sizing, under which max-width on a cell is only a hint —
      the browser widens the column to fit the text and ignores it;
   2. white-space:nowrap on the action, the destinations and the state chip, so
      that text could not wrap and forced its column wider.
   table-layout:fixed plus the percentage colgroup below makes the widths real.
   overflow-wrap:anywhere lets long paths and URLs break instead of shoving the
   table sideways. .wrap keeps its own scrollbar as a last resort on a very
   narrow window, so any overflow stays INSIDE the card and the page body never
   scrolls sideways. min-width is 720px, not 900px, so that rarely fires. */
.wrap{overflow-x:auto;border:1px solid var(--line);border-radius:10px;background:var(--card)}
table{border-collapse:collapse;width:100%;min-width:720px;table-layout:fixed}
/* Headers wrap between words but NEVER inside one — "Unsaved" split as
   "UNSAVE / D" is worse than a header on two lines. Only body cells get
   overflow-wrap:anywhere, because only they carry unbreakable paths and URLs. */
th{text-align:left;font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);
padding:10px 12px;border-bottom:1px solid var(--line);white-space:normal;overflow-wrap:normal;
word-break:keep-all}
td{padding:10px 12px;border-bottom:1px solid var(--line);vertical-align:top;overflow-wrap:anywhere}
tr:last-child td{border-bottom:none}
.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.name strong{font-size:14px}
.path{color:var(--muted);font-size:11px;font-family:ui-monospace,monospace;word-break:break-all}
.state{display:inline-block;padding:2px 8px;border-radius:99px;font-size:11px;font-weight:600;
letter-spacing:.03em;white-space:nowrap;background:var(--chip)}
.s-NOT_A_REPO,.s-NO_REMOTE{background:var(--red);color:#fff}
.s-UNCOMMITTED,.s-NO_UPSTREAM,.s-AHEAD{color:var(--amber);border:1px solid var(--amber)}
.s-PARTIAL{color:var(--work);border:1px solid var(--work)}
.s-SYNCED{color:var(--green);border:1px solid var(--green)}
.dest{display:block;font-size:12px;margin-bottom:2px;white-space:normal}
code{font-family:ui-monospace,monospace;font-size:12px}
.url{color:var(--muted);word-break:break-all}
.acc-personal{color:var(--personal);font-weight:600}
.acc-work{color:var(--work);font-weight:600}
.acc-other{color:var(--red);font-weight:600}
.wait{color:var(--amber);font-weight:600}
.ok{color:var(--green)}
.never{color:var(--red);font-size:11px}
.danger{color:var(--red);font-weight:600}
/* A row the human already ruled on must not shout. Red is reserved for "this
   still needs fixing"; a decided row does not. The WORDS stay exactly as they
   were — NOT A REPO is still what git found — only the alarm colour is dropped,
   so the fact survives and the false urgency does not. Higher specificity than
   .s-NOT_A_REPO, which is what lets it win. */
tr.is-decided .state{background:var(--chip);color:var(--muted);
border:1px solid var(--line);font-weight:600}
tr.is-decided .danger{color:var(--muted);font-weight:600}
tr.is-decided .never{color:var(--muted)}
.muted{color:var(--muted);font-size:11px}
.violation{margin-top:6px;padding:6px 8px;border-left:3px solid var(--red);background:var(--chip);
color:var(--red);font-size:12px;border-radius:0 6px 6px 0}
.warn{margin-top:6px;padding:6px 8px;border-left:3px solid var(--amber);background:var(--chip);
color:var(--amber);font-size:12px;border-radius:0 6px 6px 0}
.holds{font-size:12px}
/* A chip is one short label. The cell-wide overflow-wrap:anywhere would split
   "config" as "confi / g", so chips opt out of it. */
.kind{display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;font-weight:600;
background:var(--chip);color:var(--muted);white-space:nowrap;overflow-wrap:normal}
.k-skills,.k-agents{color:var(--personal)} .k-code{color:var(--work)}
/* The action may wrap now. It is the column people read first, so losing a word
   off the right edge was worse than losing a line of height. */
.doit>span{font-weight:600;font-size:12.5px;white-space:normal;display:inline-block}
.act-init{color:var(--red)} .act-commit{color:var(--amber)} .act-push{color:var(--work)}
.act-check{color:var(--amber)} .act-none{color:var(--muted)}
.why{margin-top:4px;font-size:11px;color:var(--muted);line-height:1.4;white-space:normal}
details summary{cursor:pointer;color:var(--muted);font-size:11px;margin-top:4px}
.det{margin-top:6px;font-size:12px}
.det>div{margin-bottom:4px}
ul.remotes{margin:6px 0 0;padding-left:16px}
ul.remotes li{margin-bottom:6px}
.legend{margin-top:24px;font-size:12px;color:var(--muted)}
.legend div{margin-bottom:4px}
.banner{margin:16px 0;padding:12px 14px;border:1px solid var(--red);border-radius:10px;color:var(--red)}
</style></head><body>
<h1>Git Manager</h1>
<div class="meta">generated ${esc(scan.generatedAtISO)}</div>
<div class="meta">roots: ${scan.roots.map(esc).join(" · ")}</div>
<div class="stats">
  <div class="stat"><b>${scan.totals.repos}</b><span>repos</span></div>
  <div class="stat ${scan.totals.notRepos ? "bad" : ""}"><b>${
    scan.totals.notRepos
  }</b><span>untracked</span></div>
  <div class="stat ${scan.totals.needAttention ? "warn" : ""}"><b>${
    scan.totals.needAttention
  }</b><span>need attention</span></div>
  ${
    scan.totals.decided
      ? `<div class="stat"><b>${scan.totals.decided}</b><span>you ruled out</span></div>`
      : ""
  }
  <div class="stat good"><b>${scan.totals.clean}</b><span>safe</span></div>
  <div class="stat"><b>${scan.totals.uncommittedFiles}</b><span>unsaved files</span></div>
</div>
<div class="meta">${
    scan.fetched
      ? "remote counts refreshed from the network on this run"
      : "remote counts are as of each repo&#39;s last fetch — re-run with --fetch for live counts"
  }</div>
${
  scan.filteredWeak.count > 0 && !scan.loose
    ? `<div class="meta">${scan.filteredWeak.count} folder(s) holding only a script or two beside documents were left out — re-run with --loose to list them</div>`
    : ""
}
${
  scan.ignoredCount > 0
    ? `<div class="meta">${scan.ignoredCount} untracked folder(s) hidden by the config ignore rules (build output) — repos are never hidden this way</div>`
    : ""
}
<div class="meta">rows are ordered worst first; within one state, by how much work sits there</div>

${
  violations.length
    ? `<div class="banner"><b>Wrong-account rule breach (${violations.length})</b>${violations
        .map((r) =>
          r.risk.ruleViolations
            .map(
              (v) =>
                `<div>${esc(r.name)} — remote <code>${esc(v.remote)}</code>: ${esc(
                  v.rule.reason,
                )}</div>`,
            )
            .join(""),
        )
        .join("")}</div>`
    : ""
}

${
  attention.length
    ? `<h2>Needs attention<span class="count">${
        attention.length
      }</span></h2><div class="wrap"><table>${colgroup}<thead>${head}</thead><tbody>${attention
        .map(rowHtml)
        .join("")}</tbody></table></div>`
    : ""
}
${
  scan.orphanDecisions.length
    ? `<div class="banner"><b>Rulings that matched nothing (${
        scan.orphanDecisions.length
      })</b><div>The folder was renamed, moved, or deleted, so the ruling no longer applies to any row.</div>${scan.orphanDecisions
        .map((d) => `<div><code>${esc(d.path)}</code></div>`)
        .join("")}</div>`
    : ""
}
${
  decided.length
    ? `<h2>Decided — not tracked<span class="count">${
        decided.length
      }</span></h2><div class="meta">You ruled these out. The STATE column is still what git actually found — the ruling changes what to do about it, not the fact.${
        scan.decisionsPath
          ? ` Read from <code>${esc(scan.decisionsPath)}</code>; nothing is hidden by them.`
          : ""
      }</div><div class="wrap"><table>${colgroup}<thead>${head}</thead><tbody>${decided
        .map(rowHtml)
        .join("")}</tbody></table></div>`
    : ""
}
${
  clean.length
    ? `<h2>Safely stored<span class="count">${
        clean.length
      }</span></h2><div class="wrap"><table>${colgroup}<thead>${head}</thead><tbody>${clean
        .map(rowHtml)
        .join("")}</tbody></table></div>`
    : ""
}

<div class="legend"><b>What each state means</b>
${Object.entries(STATE_HELP)
  .map(([k, v]) => `<div><span class="state s-${k}">${STATE_LABEL[k as StateKey]}</span> ${esc(v)}</div>`)
  .join("")}
<div style="margin-top:12px"><b>What each kind means</b></div>
${[
  ["config", "a settings folder — much of it is regenerable cache, so check before tracking"],
  ["skills", "owns skill definitions that live nowhere else"],
  ["agents", "owns agent definitions that live nowhere else"],
  ["code", "has a build file, a source folder, or 3+ scripts"],
  ["docs", "no build file and no scripts — documents rather than software"],
]
  .map(([k, v]) => `<div><span class="kind k-${k}">${k}</span> ${esc(v)}</div>`)
  .join("")}
<div style="margin-top:12px">Do this names the account for any push. A trailing <b>?</b> means the work account — your call. <b>·dup#N</b> means another row has the same name once backup/copy wrappers are stripped.</div>
<div style="margin-top:12px">Nothing here pushes anything. Name a row number and a destination in the session to plan a push.</div>
</div>
</body></html>`;
}
