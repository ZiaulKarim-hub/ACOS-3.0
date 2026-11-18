/**
 * ladder.ts — the escalation ladder (R-018..R-024, D-04, D-08, D-09, D-12).
 *
 * Rungs 1→6 move ONLY on the judge's history assessment (stuck + recommended rung). There
 * is no attempt counter anywhere in this file, on purpose. Rungs 7 and 8 are POSITIONS
 * (task end, goal end), not escalations the judge decides. No rung asks Zee to fix code.
 */
import * as fs from "node:fs";
import * as path from "node:path";
import { P, type Issue, writeIssue, nowIso, appendRecord, readJson } from "./state";
import { laneOf, repairInstruction } from "./lane";
import type { HistoryAssessment } from "./verdict";

export interface Rung { n: number; name: string; who: string; instruction: (i: Issue, root: string) => string }

export const RUNGS: readonly Rung[] = [
  { n: 1, name: "rewrite from the deny reason", who: "writer",
    instruction: (i) => `Rewrite the chunk so the finding no longer holds. Finding: ${i.what}${i.fix_hint ? ` Hint: ${i.fix_hint}` : ""} Re-submit the edit; it will be judged again.` },
  { n: 2, name: "fix the root cause, not the line", who: "writer",
    instruction: (i) => `The judge says the problem is upstream of this line. Root cause: ${i.root_cause ?? "(see the issue history)"}. Fix THAT cause (a missing policy, a function returning too much, a library default), then re-submit. Do not write around it.` },
  { n: 3, name: "fresh-context fixer", who: "a new agent",
    instruction: (i, root) => `Spawn a fresh agent: Task(developer) with ONLY these inputs — the issue file ${path.relative(root, P.issue(root, i.id))} (it carries every attempt and the judge's reasons), the task records under .nemesis/tasks/${i.task}/, and the repository path. Do not pass the conversation. Its edits are judged like any other.` },
  { n: 4, name: "second opinion from a different model family", who: "external model + agent",
    instruction: (i) => `Run: nemesis second-opinion ${i.id}  — it asks the configured external model (via run-external-agent.py) for an analysis and a patch and stores both in the issue. Then have a Claude agent apply the patch (it is judged as any edit).` },
  { n: 5, name: "redo the design (S1)", who: "writer",
    instruction: (i) => `The design itself is judged wrong for this feature. Write a new design review for task ${i.task} and run: nemesis task redesign ${i.task} ${i.id} <design-file>  — the old S1 is kept as v1; S2/S3 reopen; rebuild the feature from the new design.` },
  { n: 6, name: "revert to green and continue", who: "CLI",
    instruction: (i) => `Run: nemesis revert ${i.id}  — restores this issue's files from the last green snapshot. The issue stays open (status reverted-open). Continue with other work; it is retried at task end.` },
  { n: 7, name: "task-end retry with full history", who: "writer",
    instruction: (i) => `Task end reached with this issue open. Retry from rung 3 with the FULL attempt history in the issue file. Nothing is parked silently: the task cannot close until this is fixed and proven.` },
  { n: 8, name: "goal end — product decision", who: "Zee (product only)",
    instruction: (i) => `Every automatic rung was tried. Zee is asked ONLY if this is a change to what the product DOES or how it LOOKS, and never for a security finding (D-50): nemesis issue product-question ${i.id} --kind <functionality|design> --why "<why no code change can clear it>"  - an independent reader must agree. If it agrees, Zee gets a plain-language report with TWO choices (drop the feature / change the requirement): nemesis report --product, then nemesis issue decide ${i.id} --choice <drop|change> --owner <who>. If it does not agree, the finding is the machine's to fix. No code fix is ever asked of him.` },
];

export function rung(n: number): Rung { return RUNGS[Math.max(1, Math.min(8, n)) - 1]!; }

/**
 * Apply the judge's assessment. Advances ONLY when the judge says stuck and recommends a
 * HIGHER rung (capped at 6; 7/8 are positions). Records the judge's why. Returns the rung.
 */
export function applyAssessment(root: string, issue: Issue, ha: HistoryAssessment, verdictId: string): number {
  const rec = Math.max(1, Math.min(6, Math.floor(ha.recommended_rung || 1)));
  if (ha.stuck && rec > issue.rung) {
    const from = issue.rung;
    issue.rung = rec;
    issue.history.push({ at: nowIso(), event: "rung", detail: `${from} → ${rec} by judge ${verdictId}: ${ha.why}` });
    writeIssue(root, issue);
    appendRecord(root, "ladder", { issue: issue.id, from, to: rec, verdict: verdictId, why: ha.why });
  } else if (ha.why) {
    issue.history.push({ at: nowIso(), event: "assessed", detail: `judge ${verdictId}: not stuck — ${ha.why}` });
    writeIssue(root, issue);
  }
  return issue.rung;
}

/** Position rungs: set by task end (7) and goal end (8). */
export function setPositionRung(root: string, issue: Issue, n: 7 | 8, why: string): void {
  if (issue.rung !== n) {
    issue.history.push({ at: nowIso(), event: "rung", detail: `${issue.rung} → ${n} (${why})` });
    issue.rung = n;
    writeIssue(root, issue);
    appendRecord(root, "ladder", { issue: issue.id, to: n, why });
  }
}

/** Rung 7 then retries from rung 3 with the full history (R-023). */
export function retryFromRung3(root: string, issue: Issue): void {
  issue.history.push({ at: nowIso(), event: "rung", detail: `${issue.rung} → 3 (task-end retry with full history)` });
  issue.rung = 3;
  issue.status = issue.status === "reverted-open" ? "reverted-open" : "open";
  writeIssue(root, issue);
}

export function rungInstruction(root: string, issue: Issue): string {
  // D-42: a finding about Nemesis's OWN records is machine work at every rung. Showing it
  // the rung-8 text ("Zee gets a report, record his pick") is what sent him 104 findings he
  // could not answer, so that text is never reachable for this lane.
  if (laneOf(issue) === "record") return `machine work — Nemesis's own record (D-42): ${repairInstruction(root, issue)}`;
  const r = rung(issue.rung);
  return `rung ${r.n} — ${r.name} (${r.who}): ${r.instruction(issue, root)}`;
}


/* ────────────────────────────────────────────────────────────────────────────
 * D-56 — THE JUDGE'S ADVICE IS ENFORCED, NOT MERELY LABELLED.
 *
 * `applyAssessment` above raises the rung when the judge says the writer is stuck. That is
 * ALL it did: write a label. Nothing stopped the next turn re-editing the same file the same
 * way, and the live ledger shows the writer doing exactly that, hundreds of times.
 *
 * Measured on website-design-okoa/v2, 2026-11-09, over 553 judged edits:
 *   - 227 edits (41%) were attempted AFTER the judge had already flagged `stuck`.
 *   - Of those 227, 9 were allowed: a 4% pass rate, against 61% when not stuck.
 *   - 124 of them were on ONE file, `_build/headings.test.ts`; 61 on one checklist document.
 *   - The judge asked for rung 2 ("fix the root cause, not the line") 166 times and rung 5
 *     ("redo the design") 48 times. The writer kept editing the same file instead.
 *   - Each denial opens 2.0 findings, so ~218 doomed edits manufactured ~436 findings —
 *     roughly 44% of every finding that project has ever created.
 *
 * THE BRAKE. After BRAKE_AT consecutive denials on one file while the judge says stuck,
 * further edits to THAT file are refused BEFORE a judge call is spent. The refusal quotes the
 * rung instruction and the judge's own reason. Other files stay editable, which is the point:
 * rung 2's root cause usually lives somewhere else, so the brake pushes work there.
 *
 * WHY CLEARING NEEDS AN EXPLICIT ACK. Rung 3 is "a fresh agent takes over", and a fresh agent
 * edits the SAME file through the same tool. Nothing in the edit itself distinguishes it from
 * the stuck writer's next try, so the ladder step has to be SAID OUT LOUD: `nemesis rung ack`
 * records which advice was followed and why. The brake can therefore never deadlock — the way
 * out is always one command — and the advice can never be followed silently, which is the
 * whole point. The ack lands in the issue history, so the next judge reads it.
 *
 * WHY THE ACK IS CAPPED. An unlimited ack is a tape over the problem: say the words, edit the
 * same way, repeat. So a file gets at most ACK_LIMIT acks before a judged-clean edit lands on
 * it. After that the only exits are rung 5 (`nemesis task redesign`) and rung 6
 * (`nemesis revert`) — both CLI commands, neither judged by this hook, so there is still no
 * deadlock, but the cheap exit is gone. A clean edit deletes the record and restores both
 * budgets, because a clean edit is the one unfakeable proof that something actually moved.
 * ──────────────────────────────────────────────────────────────────────────── */

export const BRAKE_AT = 3;
export const ACK_LIMIT = 2;
export const ACK_ACTIONS = ["root-cause", "fresh-agent", "second-opinion", "redesign", "revert"] as const;
export type AckAction = (typeof ACK_ACTIONS)[number];

export interface BrakeEntry { denials: number; acks: number; rung: number; why: string; since: string; issues: string[] }
export type BrakeFile = Record<string, BrakeEntry>;

function brakePath(root: string): string { return path.join(P.state(root), "brake.json"); }
export function readBrake(root: string): BrakeFile { return readJson<BrakeFile>(brakePath(root), {}); }
function writeBrake(root: string, b: BrakeFile): void {
  fs.mkdirSync(path.dirname(brakePath(root)), { recursive: true });
  fs.writeFileSync(brakePath(root), JSON.stringify(b, null, 2));
}

/**
 * Count a denial against `rel`. Only a denial the judge calls STUCK with a rung of 2 or more
 * counts: a plain rung-1 denial ("rewrite from the deny reason") is the loop working normally.
 * A not-stuck denial BREAKS the chain, because the judge is no longer saying the writer is
 * going in circles. Acks already spent are kept — only a clean edit returns those.
 */
export function noteDenial(root: string, rel: string, ha: HistoryAssessment, issues: Issue[]): void {
  const rec = Math.max(1, Math.min(6, Math.floor(ha.recommended_rung || 1)));
  const b = readBrake(root);
  const prev = b[rel];
  if (!ha.stuck || rec < 2) {
    if (prev && prev.denials > 0) { b[rel] = { ...prev, denials: 0 }; writeBrake(root, b); }
    return;
  }
  b[rel] = {
    denials: (prev?.denials ?? 0) + 1,
    acks: prev?.acks ?? 0,
    rung: Math.max(rec, prev?.rung ?? 0),
    why: ha.why || prev?.why || "",
    since: prev?.since ?? nowIso(),
    issues: [...new Set([...(prev?.issues ?? []), ...issues.map((i) => i.id)])],
  };
  writeBrake(root, b);
}

/** A judged-clean edit landed on `rel`: the file is free and its ack budget is restored. */
export function clearBrakeOnClean(root: string, rel: string): void {
  const b = readBrake(root);
  if (!b[rel]) return;
  delete b[rel];
  writeBrake(root, b);
}

/**
 * D-68 / R-086 — RUNG 5 AND RUNG 6 REALLY CLEAR THE BRAKE, which is what `brakeRefusal` has been
 * telling braked writers since D-56 while nothing in the code did it.
 *
 * `brakeRefusal` prints "The two exits left both run through the CLI and are not judged by this
 * hook" and names `nemesis task redesign` and `nemesis revert`. Neither touched `brake.json`.
 * `clearBrakeOnClean` above was the ONLY function that removed an entry, and both of its callers
 * fire on a JUDGED-CLEAN edit - while `brakeRefusal` runs BEFORE the judge call, so a braked
 * file's edit can never reach a judge to be called clean. The D-56 promise that rungs 5 and 6
 * always leave a way out was therefore not kept by the code at all: it was a comment.
 *
 * MEASURED on website-design-okoa/v2 at 2026-11-15, which is how it was found rather than
 * reasoned about. The braked toolchain audit suite carried FIVE recorded redesigns (one on
 * SEC-237, four on SEC-240) and SEVEN archived design versions, while `brake.json` stayed
 * byte-identical throughout: 3 denials, 2 acks, rung 5, `since` 2026-11-14T15:01:08.998Z, the
 * same seven findings. SEC-237 to SEC-244 had no exit of any kind, and R-001AF's design point
 * 12am had already recorded a position fix it could not write for exactly this reason.
 *
 * THE MATCHING IS `ackRung`'S, deliberately, so all three ladder exits agree about which files an
 * issue holds. A fourth spelling of that test would be a fourth thing to keep in step.
 *
 * THE ENTRY IS DELETED RATHER THAN ZEROED, like `clearBrakeOnClean` and unlike `ackRung`. A
 * redesign replaces the design those denials were judged against and a revert removes the edits
 * themselves, so the denial chain is about code that no longer exists; carrying a spent ack count
 * forward would re-brake the file on its very first fresh denial and put the writer straight back
 * where they were. Keeping the count would make the exit cosmetic a second time.
 *
 * WHAT THIS IS NOT. It is not a judgement that anything was fixed. A redesign reopens S2 and S3,
 * a revert leaves the finding open as `reverted-open` to be retried at task end, and the next
 * edit is judged exactly as before. Clearing the brake restores the writer's ability to be
 * JUDGED; it does not grant a pass. Returns the paths freed, so the caller can say so out loud.
 */
export function clearBrakeForIssue(root: string, issue: Issue): string[] {
  const b = readBrake(root);
  const freed: string[] = [];
  for (const [rel, e] of Object.entries(b)) {
    if (!(e.issues.includes(issue.id) || issue.files.includes(rel) || issue.where.startsWith(rel))) continue;
    delete b[rel];
    freed.push(rel);
  }
  if (freed.length) writeBrake(root, b);
  return freed;
}

/** The refusal text for an edit to `rel`, or null when the file is free to edit. */
/**
 * D-61 / R-079 — the paths the brake is currently holding, for callers that have a COMMAND rather
 * than a file. Only paths at or past BRAKE_AT count; a file with one or two denials is not braked.
 */
export function brakedPaths(root: string): string[] {
  return Object.entries(readBrake(root)).filter(([, e]) => e.denials >= BRAKE_AT).map(([rel]) => rel);
}

export function brakeRefusal(root: string, rel: string, openIssues: Issue[]): string | null {
  const e = readBrake(root)[rel];
  if (!e || e.denials < BRAKE_AT) return null;
  const mine = openIssues.filter((i) => e.issues.includes(i.id) || i.files.includes(rel) || i.where.startsWith(rel));
  const lead = mine.slice().sort((a, b) => b.rung - a.rung)[0];
  const r = rung(e.rung);
  const spent = e.acks >= ACK_LIMIT;
  const out = [
    `NEMESIS STOPPED this edit WITHOUT judging it (D-56). ${rel} has been denied ${e.denials} times in a row since ${e.since}, and every one of those verdicts said the writer is going in circles.`,
    `The judge's standing instruction is rung ${e.rung} — ${r.name} (${r.who}) — and it has not been followed. The judge's reason: ${e.why || "(none recorded)"}`,
    `Editing this file the same way again has a measured 4% chance of passing, so it is no longer tried.`,
    `DO THIS: ${lead ? rungInstruction(root, lead) : `${r.name} — ${r.instruction({ id: "(the open issue on this file)", task: "(this task)", files: [rel] } as Issue, root)}`}`,
  ];
  if (spent) {
    out.push(
      `An ack will NOT clear this file: ${e.acks} have already been spent here with no clean edit since (limit ${ACK_LIMIT}). The two exits left both run through the CLI and are not judged by this hook:`,
      `  nemesis task redesign ${lead?.task ?? "<task>"} ${lead?.id ?? "<issueId>"} <new-design-file>   (rung 5 — the design itself is wrong)`,
      `  nemesis revert ${lead?.id ?? "<issueId>"}                                  (rung 6 — back to the last green snapshot)`,
    );
  } else {
    out.push(
      `THEN say which advice you followed, and this file is free again (${ACK_LIMIT - e.acks} of ${ACK_LIMIT} acks left before only redesign/revert will do):`,
      `  nemesis rung ack ${lead?.id ?? "<issueId>"} --action <${ACK_ACTIONS.join("|")}> --why "<what you actually changed>"`,
    );
  }
  out.push(`Open findings on this file: ${e.issues.slice(0, 6).join(", ") || "(none recorded)"}. Every other file is unaffected — the root cause is usually in one of them.`);
  return out.join("\n");
}

/**
 * Record that a rung's advice was followed, and free the files it covers. Refuses a file whose
 * ack budget is spent (ACK_LIMIT), and says which commands are left. The record is written
 * whether or not a file was freed, because the next judge should see the claim either way.
 */
export function ackRung(root: string, issue: Issue, action: AckAction, why: string): string {
  issue.history.push({ at: nowIso(), event: "rung-ack", detail: `rung ${issue.rung} followed as ${action}: ${why}` });
  /* AND A ROOT-CAUSE ACK FILLS THE FIELD THE REVIEWER READS (FUN-1683). The
     ack used to write history only. But the field is what the review charter
     prints -- "Root cause recorded: (none)" -- and findings filed by a check
     rather than by the judge arrive with no cause at all, because a failing
     test suite has no cause to name. So an issue could have its cause written
     down in full and still be handed to a reviewer as though nobody had looked.
     ONLY WHEN IT IS EMPTY: a cause the judge named is the judge's, and an ack
     is an account of what the writer changed, not a licence to overwrite it. */
  if (action === "root-cause" && !issue.root_cause) issue.root_cause = why;
  writeIssue(root, issue);
  appendRecord(root, "ladder", { event: "rung-ack", issue: issue.id, action, why, rung: issue.rung });
  const b = readBrake(root);
  const freed: string[] = [], refused: string[] = [];
  for (const [rel, e] of Object.entries(b)) {
    if (!(e.issues.includes(issue.id) || issue.files.includes(rel) || issue.where.startsWith(rel))) continue;
    if (e.acks >= ACK_LIMIT) { refused.push(rel); continue; }
    b[rel] = { ...e, denials: 0, acks: e.acks + 1 };
    freed.push(`${rel} (ack ${e.acks + 1}/${ACK_LIMIT})`);
  }
  writeBrake(root, b);
  const lines = [`recorded: ${issue.id} followed rung ${issue.rung} as "${action}" — ${why}`];
  lines.push(freed.length ? `  free to edit again: ${freed.join(", ")}` : `  no file was braked by this issue`);
  if (refused.length) lines.push(`  STILL BRAKED (ack budget spent): ${refused.join(", ")} — only \`nemesis task redesign\` (rung 5) or \`nemesis revert ${issue.id}\` (rung 6) clears those.`);
  lines.push(`  The ack is in the issue history, so the next judge sees it. An ack that was not honoured is visible, not hidden.`);
  return lines.join("\n");
}
