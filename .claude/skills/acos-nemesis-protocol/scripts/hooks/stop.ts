#!/usr/bin/env bun
/**
 * stop.ts — Stop hook.
 *
 *  R-026  watchdog: edits/commands in the turn with no S2/S3/bash record behind them are defects
 *  R-027  block while any issue is open or any task step is unfinished; AUTOPILOT_GOAL_COMPLETE
 *         is accepted only with a release-gate record newer than the last edit
 *  R-023  task-end retry is driven by `nemesis task end`; here we only keep the loop alive
 *  R-024  a STALLED writer (no tool calls for `stalled_turns` turns, default 6) gets the product
 *         report written and the stop is then allowed — the goal is NOT complete, Zee gets the
 *         report, and no code fix is asked of him (D-08). This is the only way out while open.
 *  R-030  reads whichever transcript (main or sub-agent) this hook was given
 *  R-082  D-64: the directive names ONE severity band to work - security, then high, then medium,
 *         then low - and defers attention only, never the rule that every open finding blocks
 *  R-075  D-57: every stop record carries `streak`, `last_turn_tool_calls` and the `transcript`
 *         path that produced them, so a NON-blocking
 *         record can answer "was the writer working?"; and the per-turn progress write carries
 *         every idle field forward instead of overwriting the file with three of them
 */
import * as fs from "node:fs";
import * as path from "node:path";
import { readStdinJson, resolveRoot, stopBlock, emit, lastTurnToolUses, toolFilePath, scopeOf, logErr } from "./common";
import { isJudgeChild } from "../lib/judge";
import { listIssues, listTasks, currentTask, recordFindings, readRecords, readIdle, writeIdle, P, readJson, appendRecord, nowIso, type Config, type Finding, type Issue } from "../lib/state";
import { blocks } from "../lib/tier";
import { readSteps, unfinishedSteps } from "../lib/steps";
import { sha256 } from "../lib/state";
import { rungInstruction } from "../lib/ladder";
import { listScans, scanSummary } from "../lib/scan";
import { issueDigest, moreLine, DEFAULT_STOP_DETAIL, DEFAULT_STOP_MAX_CHARS, DEFAULT_MAX_IDENTICAL_BLOCKS } from "../lib/digest";
import { laneOf, admitToRung8, repairInstruction } from "../lib/lane";
import { writeReport } from "../lib/report";

export const AUTOPILOT_GOAL_COMPLETE = "AUTOPILOT_GOAL_COMPLETE";

/** R-026: every in-scope edit needs an S2 record and an S3 scan after it; every Bash needs a bash record. */
export function watchdog(root: string, cfg: Config, uses: ReturnType<typeof lastTurnToolUses>["uses"], turnStart: string): Finding[] {
  const findings: Finding[] = [];
  const task = currentTask(root);
  const scans = listScans(root);
  const bash = readRecords<{ at: string }>(root, "bash");
  const s2Items = task ? (readSteps(root, task.id).entries.S2 as { items: { artifact?: string; at?: string }[] }).items : [];
  const s2For = (rel: string, since: string) => s2Items.some((it) => {
    try { const a = JSON.parse(fs.readFileSync(path.resolve(root, it.artifact ?? ""), "utf8")) as { path: string }; return a.path === rel && (it.at ?? "") >= since; } catch { return false; }
  });
  const scanAfter = (ts: string) => scans.some((s) => s.at >= ts);
  for (const u of uses) {
    const since = turnStart || u.ts;
    if (u.name === "Write" || u.name === "Edit" || u.name === "NotebookEdit") {
      const fp = toolFilePath(u.input); if (!fp) continue;
      const sc = scopeOf(root, cfg, fp); if (!sc.inScope) continue;
      if (!s2For(sc.rel, since)) findings.push({ severity: "high", lens: "PFC", checklist: "S2", where: sc.rel, what: `unrecorded edit: ${sc.rel} was changed in this turn with no S2 verdict record`, fix_hint: "the pre-tool hook did not run or was bypassed; run: nemesis scan --judge " + sc.rel });
      else if (!scanAfter(u.ts || since)) findings.push({ severity: "high", lens: "PFC", checklist: "S3", where: sc.rel, what: `no S3 scan recorded after the edit to ${sc.rel}`, fix_hint: "run: nemesis scan" });
    } else if (u.name === "Bash") {
      if (!bash.some((b) => b.at >= (u.ts || since))) findings.push({ severity: "medium", lens: "PFC", checklist: "S3", where: "Bash", what: `a shell command ran in this turn with no post-command tree check recorded`, fix_hint: "the post-tool hook did not run; run: nemesis scan" });
    }
  }
  return findings;
}

/**
 * The blocking reason. BUDGETED since 2026-11-01 (see lib/digest.ts): this text is injected
 * into the writer's conversation at the end of EVERY turn while the ledger is open, so an
 * unbounded enumeration of it is a context leak that compaction cannot clear. The header
 * count is always the true total and every severity still blocks; only the per-issue
 * bullets are capped, worst-severity-first, with the remainder accounted for by `moreLine`.
 */
/**
 * D-64: WHAT TO WORK FIRST. Zee's instruction, 2026-11-10: "Do a prioritization. Have the high
 * issues be tackled first, and then the medium issues, and then finally the low issues."
 *
 * WHY IT WAS NEEDED. The directive already ranked the list worst-first, but its header said
 * "every severity counts; Low is not deferrable" - so the writer was told that all 828 open
 * findings mattered equally and none could wait. With 538 of them low, the hardest low cases
 * absorbed turns while high ones sat. The measured history: findings created per day ran +343,
 * +93, +59, +20, +161, +100, +48, +13, +95 before today's -16, so the pile was growing while
 * attention was spread flat across it.
 *
 * WHAT CHANGED, AND WHAT DID NOT. Only the ORDER of work. The finish line is untouched: nothing
 * completes while any finding is open, lows included, and a deferred finding is still open, still
 * counted in the header, and still blocks completion. This defers ATTENTION, never the rule.
 *
 * SECURITY IS NOT DEFERRED BY SEVERITY. A low security finding waiting behind 205 medium ones is
 * a security lapse on a timer, and Zee's standing ruling is "no security laps in any way". So the
 * security lens (PSC) forms the FIRST band whatever its severity. That is an assumption added on
 * top of his order, stated here so he can strike it: with it gone, the bands are simply
 * high, medium, low.
 */
export const BANDS = ["critical", "security", "high", "medium", "low"] as const;
export type Band = (typeof BANDS)[number];

/**
 * CRITICAL IS A REAL SEVERITY AND IT LEADS EVERYTHING. The first version of this mapped `high` and
 * `medium` by name and sent EVERYTHING ELSE to `low` - so a `critical` finding would have been
 * worked after all 538 low ones, the exact inverse of the instruction. `SEVERITIES` in lib/state.ts
 * is ["critical", "high", "medium", "low"] and the live ledger held 6 criticals when this was
 * written. Found by a positive control, not by reading: dropping the security band made a fixture's
 * critical issue stop being named first, which is only possible if critical was being banded as low.
 *
 * Security sits second rather than first, so a critical finding of any kind outranks a LOW security
 * one, while every security finding still outranks all ordinary high/medium/low work.
 */
export function bandOf(i: Issue): Band {
  if (i.severity === "critical") return "critical";
  if (i.lens === "PSC" || String(i.id ?? "").startsWith("SEC")) return "security";
  return i.severity === "high" ? "high" : i.severity === "medium" ? "medium" : "low";
}

/** The worst band that still has an open finding, plus what is waiting behind it. */
export function activeBand(open: Issue[]): { band: Band | null; inBand: Issue[]; waiting: { band: Band; n: number }[] } {
  const by = new Map<Band, Issue[]>();
  for (const i of open) { const b = bandOf(i); const a = by.get(b); if (a) a.push(i); else by.set(b, [i]); }
  const band = BANDS.find((b) => (by.get(b)?.length ?? 0) > 0) ?? null;
  if (!band) return { band: null, inBand: [], waiting: [] };
  const after = BANDS.slice(BANDS.indexOf(band) + 1);
  return { band, inBand: by.get(band) ?? [], waiting: after.map((b) => ({ band: b, n: by.get(b)?.length ?? 0 })).filter((w) => w.n > 0) };
}

export function buildDirective(root: string, cfg?: Config): { open: boolean; text: string } {
  // WHAT STOPS THE TURN IS NOW A SUBSET OF WHAT IS OPEN (Zee, 2026-11-18).
  //
  // Until today every open finding held the turn, at every severity. Measured on
  // website-design-okoa/v2: that rule produced a list that cannot be emptied — 2,085 filed,
  // 1,128 closed, and the open count pinned between 950 and 981 for ten days, because each
  // fix is itself judged and files more. Of the 957 open at measurement, 950 carried the
  // functionality label and 7 the security one.
  //
  // Zee's instruction: keep Nemesis exactly as strict on security findings "and other
  // important issues like anything that breaks the system being built or causes goal
  // achievement to fail", and hand the rest to /acos-triplex-repairer. `blocks()` is that
  // line, and it is drawn from the RULE each finding cites, never from its label — 105 of
  // those 957 were labelled functionality while citing a security rule, so a label-based
  // split would have released the very findings this exists to hold.
  const all = listIssues(root, true);
  const open = all.filter(blocks);
  const backlog = all.filter((i) => !blocks(i));
  const tasks = listTasks(root).filter((t) => t.status === "open");
  const lines: string[] = [];
  if (open.length) {
    const { band, inBand, waiting } = activeBand(open);
    const behind = waiting.length ? ` Waiting behind it: ${waiting.map((w) => `${w.n} ${w.band}`).join(", ")}.` : "";
    // THE OLD SENTENCE IS AMENDED, NOT QUIETLY DROPPED. It read "Nothing is done while any
    // is open (every severity counts; Low is not deferrable)" and was marked kept word for
    // word as the 2026-11-01 guarantee. That guarantee has been changed BY THE PERSON IT
    // protected, on 2026-11-18, and the replacement says exactly what still holds and what
    // no longer does — because a stale promise left in place is how a rule quietly becomes
    // a lie. Within the blocking set, no severity is deferrable: Low still blocks.
    lines.push(`NEMESIS — ${open.length} blocking issue(s). Nothing is done while any of THESE is open (within this set every severity counts; Low is not deferrable).${backlog.length ? ` A further ${backlog.length} are on the backlog — real, still owed, repaired by /acos-triplex-repairer, and they do NOT block.` : ""}`);
    lines.push(`WORK THE ${String(band).toUpperCase()} BAND ONLY (${inBand.length} finding(s)).${behind} Work them until none is left, then the next band becomes your focus (D-64). Do not spend a turn on a lower band while this one has an open finding${band === "security" ? "; the security band is first whatever its severity" : ""}. A later band is deferred ATTENTION, not a deferred rule — every one of them still blocks completion.`);
    const d = issueDigest(inBand, {
      detail: cfg?.stop_issue_detail ?? DEFAULT_STOP_DETAIL,
      maxChars: cfg?.stop_directive_max_chars ?? DEFAULT_STOP_MAX_CHARS,
      bullet: (i) => `• ${i.id} [${i.severity}/${i.lens}/${i.checklist}] ${i.status} — ${i.what}\n    → ${rungInstruction(root, i)}`,
    });
    lines.push(...d.lines);
    // EVERY UNLISTED FINDING IS STILL ACCOUNTED FOR, and the first version of D-64 broke that.
    // Listing only the band meant `d.hidden` held just the band's overflow, so a small band
    // produced NO "…and N more" line at all: the header said 305 open and the writer was given
    // no census of the other 302 and no pointer to the ledger. That is exactly the accounting the
    // 2026-11-01 context-burn fix installed. The unlisted set is the band's overflow PLUS every
    // deferred band, so the count and the severity census cover the whole ledger again.
    const listed = new Set(d.lines.length ? inBand.slice(0, d.lines.length).map((i) => i.id) : []);
    const unlisted = open.filter((i) => !listed.has(i.id));
    const more = moreLine(unlisted, `nemesis issue list --open`);
    if (more) lines.push(more, `Worst severity first is the order above, within the ${String(band)} band. Work the named ones; the rest surface here as these close.`);
  }
  for (const t of tasks) {
    const un = unfinishedSteps(root, t.id);
    if (un.length) lines.push(`Task ${t.id} — unfinished steps: ${un.join(", ")}. (S5/S6/S7 run via: nemesis task end ${t.id}; S8 via: nemesis release-gate)`);
  }
  const scans = listScans(root);
  const last = scans[scans.length - 1];
  if (last) lines.push(`Last S3: ${scanSummary(last)}`);
  const isOpen = open.length > 0 || tasks.some((t) => unfinishedSteps(root, t.id).length > 0);
  return { open: isOpen, text: lines.join("\n") };
}

function releaseGateFresh(root: string): { ok: boolean; why: string } {
  const g = readJson<{ at?: string; gate?: string } | null>(P.releaseGate(root), null);
  if (!g || g.gate !== "open") return { ok: false, why: "no release-gate record (run: nemesis release-gate)" };
  const scans = listScans(root);
  const lastEdit = scans[scans.length - 1]?.at ?? "";
  if (g.at && lastEdit && g.at < lastEdit) return { ok: false, why: `release-gate record (${g.at}) is older than the last change (${lastEdit}); rerun: nemesis release-gate` };
  return { ok: true, why: "release gate open" };
}

async function main(): Promise<void> {
  const input = await readStdinJson();
  if (isJudgeChild()) return emit({});
  const r = resolveRoot(input);
  if (!r) return emit({});
  const { root, cfg } = r;

  // idle / stalled tracking (R-024). READ FIRST, because `idle.updated_at` is the previous
  // turn's end and D-62 needs it as the turn boundary: a Stop-hook continuation writes no user
  // message into the transcript, so without it the tool-call count is an earlier turn's.
  // A missing idle file is the first turn, and has no previous end to offer - an empty `since`
  // then leaves the human-message rule in charge rather than cutting the turn off at now.
  const idle = readIdle(root);
  const prevTurnEnd = fs.existsSync(P.idle(root)) ? String(idle.updated_at ?? "") : "";
  const turn = lastTurnToolUses(input.transcript_path, undefined, prevTurnEnd);
  const streak = turn.uses.length === 0 ? idle.streak + 1 : 0;
  // D-57: this is a PROGRESS write, not a reset, so it must carry every field forward. It used
  // to pass only these three, and `writeIdle` is a full overwrite (`writeJson`), so it DELETED
  // `last_block_sha`, `latched_sha`, `same_block_streak` and `block_chain` from disk on every
  // single turn. Within one run the later branches wrote them back from the in-memory `idle`,
  // which hid it - but the `!d.open` early return below writes nothing more, so one such turn
  // wiped the host-chain count and D-46's duplicate-report latch. That is the THIRD door into
  // the same defect as D-54: a write that silently drops a field something else is still
  // counting. The first two were fixed one branch at a time; this one is fixed at the source.
  writeIdle(root, { ...idle, streak, last_turn_tool_calls: turn.uses.length, updated_at: nowIso() });

  // watchdog (R-026)
  const task = currentTask(root);
  const wd = watchdog(root, cfg, turn.uses, turn.turnStart);
  if (wd.length && task) recordFindings(root, task.id, wd, { verdict_id: "watchdog", files: wd.map((f) => f.where), outcome: "watchdog" });

  const d = buildDirective(root, cfg);
  const wantsComplete = turn.lastAssistantText.includes(AUTOPILOT_GOAL_COMPLETE);
  const gate = releaseGateFresh(root);

  if (!d.open && (!wantsComplete || gate.ok)) {
    // D-57: carry the writer's own activity. Without it a non-blocking record cannot answer
    // "was the writer working?", which is the first question anyone asks of one.
    appendRecord(root, "stop", { blocked: false, wantsComplete, gate: gate.why, streak, last_turn_tool_calls: turn.uses.length, turn_counted_from: turn.boundary, transcript: input.transcript_path ?? null });
    return emit({});
  }

  const stalledAfter = cfg.stalled_turns ?? 6;
  if (streak >= stalledAfter) {
    // The writer has done nothing for `stalledAfter` turns. Keeping it in a loop burns tokens and
    // fixes nothing. Write the product report (rung 8) and let the stop happen. Goal NOT complete.
    // D-46: LATCH. This used to rewrite the report and re-arm on every cycle — 5 cycles, 1780
    // `stalled` history events and 16 duplicate reports totalling 8.9 MB. The ledger's own
    // fingerprint decides: an unchanged ledger is already reported, so say so and write nothing.
    const ledgerSha = sha256(listIssues(root, true).map((i) => `${i.id}:${i.status}:${i.rung}`).join("|"));
    const alreadyReported = idle.latched_sha === ledgerSha;
    const rep = alreadyReported ? null : writeReport(root, "product");
    if (rep) for (const i of listIssues(root, true)) { i.history.push({ at: nowIso(), event: "stalled", detail: `writer idle ${streak} turns; product report ${path.basename(rep.md)}` }); const { writeIssue } = await import("../lib/state"); writeIssue(root, i); }
    appendRecord(root, "stop", { blocked: false, stalled: true, streak, last_turn_tool_calls: turn.uses.length, turn_counted_from: turn.boundary, transcript: input.transcript_path ?? null, report: rep?.md ?? "(unchanged ledger — the existing report still stands)" });
    // D-54, second reset path: this branch OMITTED block_chain, so `idle.block_chain ?? 0`
    // read 0 on the next turn and the chain count restarted from 1 - the same defect as the
    // cap release, by a different door. The stalled branch does not block, but the HOST's
    // chain can still be live, so the count has to carry across it untouched.
    writeIdle(root, { streak: 0, last_turn_tool_calls: 0, updated_at: nowIso(), last_block_sha: idle.last_block_sha, latched_sha: ledgerSha, same_block_streak: 0, block_chain: idle.block_chain });
    return emit({ hookSpecificOutput: { hookEventName: "Stop", additionalContext: `NEMESIS: the writer made no tool calls for ${streak} turns with the ledger open. The goal is NOT complete. ${rep ? `A product report for Zee was written: ${rep.html}` : "The ledger has not changed since the last report, so no duplicate was written (D-46)."}` } });
  }

  const parts: string[] = [];
  if (wantsComplete) parts.push(`NEMESIS refuses ${AUTOPILOT_GOAL_COMPLETE}: ${gate.ok ? "" : gate.why + "; "}${d.open ? "the ledger is open." : ""}`);
  if (wd.length) parts.push(`Watchdog: ${wd.length} unrecorded action(s) this turn → opened as issues.`);
  parts.push(d.text || "Unfinished steps remain.");

  // D-42: say WHO owes the work, so the writer is never told to "keep working" on something
  // only Zee can answer, and Zee is never handed something only the machine can do.
  const openNow = listIssues(root, true).filter(blocks);
  const mine = openNow.filter((i) => !admitToRung8(root, i).ok);
  const zees = openNow.length - mine.length;
  if (mine.length) {
    const first = mine[0]!;
    const why = laneOf(first) === "record" ? repairInstruction(root, first) : admitToRung8(root, first).why.join("; ");
    parts.push(`${mine.length} of ${openNow.length} are the MACHINE's work, not Zee's (D-08). Start with ${first.id}: ${why}`);
  }
  if (zees) parts.push(`${zees} are product decisions already with Zee at rung 8; they are NOT yours to clear.`);
  parts.push(`Keep working. Do not emit ${AUTOPILOT_GOAL_COMPLETE} until nemesis status shows zero open issues, every task closed, and the release gate open.`);

  // ── D-46 / R-058: the circuit breaker ──────────────────────────────────────
  // A block repeats the SAME words at the end of every turn. If the words have not changed,
  // blocking again cannot change anything — it only spends turns until Claude Code's own cap
  // (`CLAUDE_CODE_STOP_HOOK_BLOCK_CAP ?? 8`) overrides us, which is what happened twice on the
  // website-design-okoa/v2 ledger. So count identical blocks and release well before that.
  const reason = parts.join("\n");
  const sha = sha256(reason);
  const cap = Math.max(1, cfg.max_identical_blocks ?? DEFAULT_MAX_IDENTICAL_BLOCKS);

  // TWO counters, because the website-design-okoa/v2 loop defeated the obvious one. Blocking
  // text that never changes is the easy case; what actually happened is that the watchdog
  // opened a fresh issue nearly every turn, so the directive changed every time while the
  // writer got no closer. A counter keyed on the TEXT resets on each change and climbs to the
  // host's cap anyway, which is how 9 consecutive blocks were reached twice.
  //
  //   same_block_streak — identical directive repeats: repeating it cannot help.
  //   block_chain       — consecutive blocks in ONE Stop chain, whatever the text says.
  //                       Driven by `stop_hook_active`, which is the host telling us a block
  //                       is already live in this chain. This is the counter that bounds us
  //                       below `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP ?? 8`.
  const chainLive = input.stop_hook_active === true;
  const sameStreak = sha === idle.last_block_sha ? (idle.same_block_streak ?? 0) + 1 : 1;
  const chain = chainLive ? (idle.block_chain ?? 0) + 1 : 1;
  const why = sameStreak > cap
    ? `the same instruction has now been given ${sameStreak} times and nothing changed, so repeating it cannot help`
    : chain > cap
      ? `this turn has already been blocked ${chain} times in a row; one more and Claude Code would override the hook instead, which would end the turn with no record of why`
      : "";
  if (why) {
    // D-54: KEEP the chain count on release; zeroing it restarted the count while the HOST's
    // chain was still live, so the release let exactly ONE turn through and then the hook
    // began blocking again from 1. Measured on website-design-okoa/v2 2026-11-09: blocks at
    // chain 2,3,4,5,6, release at 7 ("identical-block"), then chain 1,2,3,4,5 again — and
    // `stop_hook_active` was TRUE on every one of those, which is the host saying its own
    // chain never ended. The host counts consecutive blocks across the whole chain and does
    // not see our reset, so it reached 9 and overrode the hook. Keeping the count makes the
    // release STICKY for the rest of the chain: next turn computes chain + 1, which is still
    // over the cap, so it releases again. When the host's chain truly ends `stop_hook_active`
    // goes false and `chain` falls back to 1 on its own, so blocking resumes normally.
    // D-67: `streak` is CARRIED, not zeroed. This is D-54's lesson by a third door, and it
    // cost 96 wasted turns to find. `streak` counts consecutive turns with no tool calls and is
    // the ONLY input to the stalled branch above (`streak >= cfg.stalled_turns ?? 6`), the branch
    // built to catch exactly this. Zeroing it here meant every pass computed
    // `idle.streak + 1 = 0 + 1 = 1` and then reset it, so the count oscillated 1,0,1,0 and could
    // never reach 6. Measured on website-design-okoa/v2 2026-11-11: `block_chain` climbed to 96
    // with `last_turn_tool_calls: 0` on every record, the writer answering "Holding." every ~3
    // seconds, 842 findings open and 842 of them the MACHINE's own work — and the stall detector
    // never fired once. A release ends a BLOCK; it does not mean the writer did something.
    writeIdle(root, { streak, last_turn_tool_calls: turn.uses.length, updated_at: nowIso(), last_block_sha: sha, latched_sha: idle.latched_sha, same_block_streak: 0, block_chain: chain });
    // D-57: `streak` and `last_turn_tool_calls` were MISSING from this branch alone, and it is
    // the branch that matters most - a release is where you need to know whether the writer is
    // working or spinning. Reading the field's ABSENCE as a zero is how a run of 8 releases was
    // misread as 8 turns with no tool calls, when `idle.json` recorded 4 on the last of them.
    appendRecord(root, "stop", { blocked: false, released: sameStreak > cap ? "identical-block" : "block-chain", same_block_streak: sameStreak, block_chain: chain, stop_hook_active: chainLive, open_issues: openNow.length, machine_owed: mine.length, with_zee: zees, streak, last_turn_tool_calls: turn.uses.length, turn_counted_from: turn.boundary, transcript: input.transcript_path ?? null });
    // D-67: WHAT THE RELEASE SAYS MATTERS, because another turn almost always follows it. The
    // old text opened "NEMESIS let this turn end", which reads as permission to stop, and the
    // writer obeyed it literally — 96 turns of the single word "Holding." while 842 findings
    // sat open. The release exists so Claude Code's own block cap cannot override the hook; it
    // was never meant to tell the writer its work was over. So when the writer did nothing last
    // turn and the machine still owes the work, the release leads with the next action instead
    // of with the permission, and says plainly that holding is not available.
    const idling = turn.uses.length === 0 && mine.length > 0;
    const head = idling
      ? `NEMESIS is not blocking this turn (${why}) — but that is a limit on the HOOK, not permission to stop, and another turn follows. You made no tool calls last turn. Nothing is waiting on Zee: ${mine.length} of ${openNow.length} open findings are the MACHINE's own work. Do NOT answer with "Holding" or any other bare acknowledgement; take the next action below with a tool call this turn.`
      : `NEMESIS let this turn end (D-46): ${why}. The goal is NOT complete and the ledger is NOT cleared — ${openNow.length} open, ${mine.length} owed by the machine, ${zees} with Zee.`;
    return emit({ hookSpecificOutput: { hookEventName: "Stop", additionalContext: `${head} ${reason}` } });
  }
  writeIdle(root, { streak, last_turn_tool_calls: turn.uses.length, updated_at: nowIso(), last_block_sha: sha, latched_sha: idle.latched_sha, same_block_streak: sameStreak, block_chain: chain });
  appendRecord(root, "stop", { blocked: true, wantsComplete, open_issues: openNow.length, machine_owed: mine.length, with_zee: zees, streak, last_turn_tool_calls: turn.uses.length, turn_counted_from: turn.boundary, transcript: input.transcript_path ?? null, same_block_streak: sameStreak, block_chain: chain, stop_hook_active: chainLive });
  return stopBlock(reason);
}

if (import.meta.main) {
  if (process.argv.includes("--health")) { console.log("stop hook loads; libs resolve"); process.exit(0); }
  main().catch((e) => { logErr("stop", e); emit({}); });
}
