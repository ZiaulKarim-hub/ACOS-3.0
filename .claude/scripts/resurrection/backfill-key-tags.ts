#!/usr/bin/env bun
/**
 * backfill-key-tags.ts — give every tab the durable [key:<uuid>] tag it is missing.
 *
 * Why (2026-08-18). A tab's `[key:<uuid>]` description tag is the ONLY binding
 * that survives a rename and outranks folder matching. `adopt-project.sh` writes
 * it, but its set-description and rename steps are both non-fatal (adopt :530/
 * :555, launch :218/:236), so a tab can end up renamed with NO tag. That is the
 * state workspace:24 'Research to Portfolio' was found in — and an untagged tab
 * falls back to matching by folder and name, which is exactly what let the
 * Research to Portfolio session mint a row called 'FruitSync (duplicate)'.
 *
 * Zee's Rule 3 is built in: this tool tags only what it can prove, and REFUSES
 * anything ambiguous with a named next step rather than guessing. Guessing here
 * would cement the wrong project onto a tab permanently.
 *
 * Resolution rule for an untagged tab — deliberately strict:
 *   tag it ONLY when EXACTLY ONE live row carries the tab's sidebar name.
 *   Anything else REFUSES with the candidates printed.
 *
 * The strictness is not caution for its own sake. An earlier draft resolved a
 * name clash by preferring the row whose root matched the tab's folder, and on
 * the very first run that would have bound workspace:24 'Research to Portfolio'
 * to row 1b4e2505 (rooted at ACOS 3.0) instead of d86cf151 (rooted at the R2P
 * folder) — cementing the exact wrong-folder binding this whole exercise exists
 * to undo. When two live rows share a name, the tab's current folder is
 * evidence of where it was OPENED, never of which project it IS. That is a
 * ruling only Zee can make.
 *
 * Existing description text is PRESERVED; the tag is appended.
 *
 * Usage:
 *   bun backfill-key-tags.ts           # dry run (default)
 *   bun backfill-key-tags.ts --apply
 */

import { existsSync, readFileSync, readdirSync, realpathSync } from "node:fs";
import { join } from "node:path";
import { homedir } from "node:os";
import { execFileSync } from "node:child_process";

const CMUX_BIN = process.env.CMUX_CLAUDE_HOOK_CMUX_BIN
  ?? "/Applications/cmux.app/Contents/Resources/bin/cmux";
const REGISTRY = join(homedir(), ".acos", "registry.d");
const KEY_RE = /\[key:([0-9a-fA-F-]{36})\]/;
const APPLY = process.argv.includes("--apply");

type Row = {
  project_uuid: string;
  root: string;
  name?: string;
  workspace_name?: string | null;
  status?: string;
};

function liveRows(): Row[] {
  if (!existsSync(REGISTRY)) return [];
  const rows: Row[] = [];
  for (const f of readdirSync(REGISTRY)) {
    if (!f.endsWith(".json")) continue;
    try {
      const r = JSON.parse(readFileSync(join(REGISTRY, f), "utf8")) as Row;
      if (r.status !== "tombstoned") rows.push(r);
    } catch { /* a malformed row must not stop the sweep */ }
  }
  return rows;
}

function workspaces(): any[] {
  const out = execFileSync(CMUX_BIN, ["rpc", "workspace.list"], { encoding: "utf8" });
  return JSON.parse(out).workspaces ?? [];
}

function real(p: string): string {
  try { return realpathSync(p); } catch { return p; }
}

const rows = liveRows();
const ws = workspaces();

let tagged = 0;
let refused = 0;
let already = 0;

for (const w of ws) {
  const desc: string = w.description ?? "";
  const title: string = (w.custom_title ?? "").trim();
  const cwd: string = w.current_directory ?? "";
  const ref = w.ref ?? w.id;

  if (KEY_RE.test(desc)) { already += 1; continue; }
  if (!title) {
    console.log(`SKIP   ${ref} — no sidebar name to match on`);
    continue;
  }

  const named = rows.filter(
    (r) => ((r.workspace_name ?? r.name ?? "").trim().toLowerCase() === title.toLowerCase()),
  );
  const sameRoot = named.filter((r) => real(r.root) === real(cwd));

  let pick: Row | null = null;
  let why = "";
  if (named.length === 1) {
    pick = named[0];
    why = real(named[0].root) === real(cwd)
      ? "the only row with this name; its root matches this folder"
      : "the only row with this name (its root is a DIFFERENT folder — see conflict-scan.py)";
  }

  if (!pick) {
    refused += 1;
    console.log(`REFUSED ${ref} ${JSON.stringify(title)} in ${JSON.stringify(cwd)}`);
    if (named.length === 0) {
      console.log(`        no live row is named ${JSON.stringify(title)} — pick the project once with /acos-resurrect, which mints the tag.`);
    } else {
      console.log(`        ${named.length} live rows carry that name (${sameRoot.length} also match this folder — which is NOT enough to decide):`);
      for (const c of named) {
        console.log(`          ${c.project_uuid}  root=${JSON.stringify(c.root)}  status=${c.status}`);
      }
      console.log("        Your ruling is needed — tagging the wrong one binds this tab to the wrong project permanently.");
    }
    continue;
  }

  const newDesc = (desc ? `${desc} ` : "") + `[key:${pick.project_uuid}]`;
  if (!APPLY) {
    console.log(`WOULD TAG ${ref} ${JSON.stringify(title)} -> [key:${pick.project_uuid}]  (${why})`);
    tagged += 1;
    continue;
  }
  try {
    execFileSync(CMUX_BIN, ["workspace-action", "--action", "set-description",
      "--workspace", w.id, "--description", newDesc], { stdio: "ignore" });
    const back = workspaces().find((x) => (x.id ?? "").toLowerCase() === (w.id ?? "").toLowerCase());
    const ok = back && (back.description ?? "").includes(`[key:${pick.project_uuid}]`);
    console.log(`${ok ? "TAGGED " : "NOT-VERIFIED "}${ref} ${JSON.stringify(title)} -> [key:${pick.project_uuid}]  (${why})`);
    if (ok) tagged += 1;
  } catch (err) {
    console.log(`WARN   ${ref} set-description failed: ${(err as Error).message}`);
  }
}

console.log("");
console.log(`already tagged: ${already}   ${APPLY ? "tagged" : "would tag"}: ${tagged}   refused: ${refused}`);
if (!APPLY && tagged > 0) console.log("DRY RUN — re-run with --apply to write these tags.");
if (refused > 0) console.log("Refused tabs need a ruling from you; nothing about them was changed.");
