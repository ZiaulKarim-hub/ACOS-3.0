#!/usr/bin/env bun
/**
 * prompt.ts — UserPromptSubmit hook (R-028). Re-injects the open ledger every prompt, read
 * from disk, so it survives compaction and /clear. Inert when Nemesis is off.
 *
 * BUDGETED (2026-11-01, see lib/digest.ts). This text lands in the conversation on every
 * prompt, so it is capped by BOTH a count and a byte ceiling, and the issues it names are
 * ranked worst-severity-first. The previous `slice(0, 12)` was a count cap only, over
 * creation order — so on a project with 436 open issues it named the twelve OLDEST and
 * could leave the single critical one unmentioned, while still having no byte ceiling.
 */
import { readStdinJson, resolveRoot, emit, logErr } from "./common";
import { isJudgeChild } from "../lib/judge";
import { listIssues, listTasks, currentTask, readIdle, type Config } from "../lib/state";
import { unfinishedSteps } from "../lib/steps";
import { rungInstruction } from "../lib/ladder";
import { listScans, scanSummary } from "../lib/scan";
import { issueDigest, moreLine, DEFAULT_PROMPT_DETAIL, DEFAULT_PROMPT_MAX_CHARS } from "../lib/digest";

export function additionalContext(root: string, goal: string, cfg?: Config): string {
  const lines: string[] = [`[NEMESIS ACTIVE] goal: ${goal}`];
  const task = currentTask(root);
  if (task) {
    const un = unfinishedSteps(root, task.id);
    lines.push(`current task: ${task.id} — ${task.title}; next unfinished step: ${un[0] ?? "(all steps done — run: nemesis task end " + task.id + ")"}`);
  } else lines.push(`no open task — before any edit: nemesis task start <id> --title "…", then task sketch, task design`);
  const open = listIssues(root, true);
  if (open.length) {
    lines.push(`open issues (${open.length}) — nothing is done while any is open:`);
    const d = issueDigest(open, {
      detail: cfg?.prompt_issue_detail ?? DEFAULT_PROMPT_DETAIL,
      maxChars: cfg?.prompt_context_max_chars ?? DEFAULT_PROMPT_MAX_CHARS,
      bullet: (i) => `  ${i.id} [${i.severity}/${i.lens}/${i.checklist}] ${i.what} → ${rungInstruction(root, i)}`,
    });
    lines.push(...d.lines);
    const more = moreLine(d.hidden, `nemesis issue list --open`);
    if (more) lines.push(`  ${more}`);
  } else lines.push(`open issues: none`);
  const tasksOpen = listTasks(root).filter((t) => t.status === "open").length;
  const scans = listScans(root); const last = scans[scans.length - 1];
  lines.push(`tasks open: ${tasksOpen}; last S3: ${last ? scanSummary(last) : "none"}`);
  const idle = readIdle(root);
  if (idle.streak >= 3) lines.push(`warning: ${idle.streak} turns with no tool calls while the ledger is open — act, or the product report is written and the run stops as NOT complete.`);
  return lines.join("\n");
}

async function main(): Promise<void> {
  const input = await readStdinJson();
  if (isJudgeChild()) return emit({});
  const r = resolveRoot(input);
  if (!r) return emit({});
  emit({ hookSpecificOutput: { hookEventName: "UserPromptSubmit", additionalContext: additionalContext(r.root, r.active.goal, r.cfg) } });
}

if (import.meta.main) {
  if (process.argv.includes("--health")) { console.log("prompt hook loads; libs resolve"); process.exit(0); }
  main().catch((e) => { logErr("prompt", e); emit({}); });
}
