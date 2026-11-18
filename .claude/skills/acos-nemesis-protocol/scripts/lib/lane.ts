/**
 * lane.ts — WHO clears a finding: the machine, or Zee (D-42, D-43, D-44).
 *
 * WHY THIS FILE EXISTS. D-08 is the oldest promise in this protocol: "Nemesis NEVER hands a
 * bug to Zee to fix. He is not a coder. The only things that may reach him are product
 * decisions, in plain language." On 2026-11-02 the website-design-okoa/v2 ledger sent him
 * 356 findings at once, in a 517,926-byte report. R-024 as written says the gate "moves EVERY
 * open issue to rung 8", with no test for whether a finding is even a question a product
 * owner could answer. Of those 356, 104 were about Nemesis's own paperwork — a stale threat
 * sketch, a missing verdict record, a skipped scan. You cannot "drop the feature" of a stale
 * sketch. Zee's words: "If the decision comes to me, I will not know everything and the
 * complete context."
 *
 * THE RULE. Rung 8 offers exactly TWO choices — drop the feature, or change the requirement. A
 * finding may only reach Zee if those are ANSWERABLE for it. That needs two anchors: a feature he
 * could drop (the task's title) and a requirement he could change (the task's PRD refs). A
 * finding with neither is not a product decision; it is unfinished machine work wearing a
 * product decision's clothes.
 *
 * D-50 (2026-11-04) ADDS THE TEST THAT MATTERS MOST, and it is about KIND, not volume. Zee:
 * "Still, I am not a programmar. Now it is 23, if I do a large enough job, it could become 230...
 * no coding decision should come to me unless I specifically want some change be made. I care
 * about functionality and security... Only questions about any change in functionality and design
 * should come to me, nothing else. It is the systems job to code to ensure the functionality and
 * the security."
 *
 * So two further gates, and they are what hold the door:
 *   - A SECURITY finding (lens PSC) NEVER reaches him. He has pre-decided every one of them:
 *     there is to be no lapse, in any way, and coding the security is the system's job. There is
 *     nothing left to ask. "Accept the risk with a named owner" is therefore DELETED as a choice
 *     - it existed only to let him sign off a lapse he has said he will never sign off.
 *   - Every other finding needs a POSITIVE, RECORDED, INDEPENDENTLY CONFIRMED claim that no code
 *     change can clear it and the remaining question is about what the product DOES or how it
 *     LOOKS. A bug is not that. A contradiction between two notes is not that. A test that
 *     disagrees with its own comment is not that. Those are the machine's to fix, forever.
 * The volume objection is answered by construction: these tests scale with the number of genuine
 * functionality and design changes, which is a property of the PRODUCT, not of how much code was
 * written. Ten times the code does not make ten times the product questions.
 *
 * NOTHING HERE WEAKENS A CHECK. D-06, D-07 and D-29 still hold: every finding still blocks,
 * at every severity, and Low is still not deferrable. This file changes only WHO clears it.
 * A record-lane finding is repaired by the machine and the gate stays shut until it is.
 */
import * as path from "node:path";
import { readTask, currentTask, type Issue } from "./state";

export type Lane = "product" | "record";

/** Checklist ids that name one of Nemesis's OWN records, not a rule about shipped code. */
const RECORD_STEPS = new Set(["S0", "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8"]);

/**
 * The ONE rule whose risk exists because the bytes are on disk, wherever they sit.
 *
 * Checklist 3.4 is secrets and credentials. A hard-coded credential inside `.nemesis/` is a
 * real credential, so calling it bookkeeping and telling the machine to "repair the record"
 * would be the wrong instruction as well as the wrong lane.
 *
 * NARROWED 2026-11-02, measured. This began as a wide "is the rule about code" test - any
 * `3.x`, `Qn` or `PFC-x` beat the path test - on the reasoning that a code rule must never
 * be filed as paperwork. Run against website-design-okoa/v2 that reclassified 17 findings
 * whose only files live under `.nemesis/` (ten about a stale holdout pack, six about
 * contradictory passages, one about an S1 summary saying "SEVENTEEN tests") as questions for
 * Zee, because the judge had cited rules 3.14, 3.11 and 3.7 while describing Nemesis's own
 * records. None of them was a secret. "The S1 summary says seventeen tests and there are
 * nineteen" is not a product decision in any wording.
 *
 * The safety worry behind the wide version does not survive either: `record` does not drop a
 * finding. It stays OPEN, the release gate stays SHUT, and the machine must clear it. The
 * lane decides WHO, never WHETHER. And R-034's rotation gate is independent of lanes, so a
 * secret is caught by that check whichever lane it lands in.
 */
function isSecretsRule(checklist: string): boolean {
  return /^3\.4(\.|$)/.test(checklist.trim());
}

/** Nemesis's own missing evidence: the project needs the check to EXIST, which is work. */
function isMissingCheck(i: Issue): boolean {
  return /\bSKIPPED\b|a skip is not a pass/i.test(i.what);
}

/**
 * Does this finding POINT AT one of Nemesis's own records?
 *
 * `where` is the place the judge is pointing at, so it decides. The old test asked whether
 * EVERY path the finding names is under `.nemesis/`, and that was wrong in a way the live
 * ledger showed within the hour: FUN-180 points at `.nemesis/holdout/R-019/manifest.json:35`
 * and also names `_build/headings.test.ts`, so "every path" was false and it came back
 * `product`. It then reached Zee as a question about dropping a feature, when its own N/A
 * ruling said in plain words: "one of Nemesis's own records, not shipping code. There is no
 * code root cause to fix." The machine was right and the lane test was wrong.
 */
function pointsAtNemesisOwnRecord(i: Issue): boolean {
  // `where` can be "path:line", or a path followed by symbol names, so take the first token.
  const here = (i.where.split(":")[0] ?? "").trim().split(/\s+/)[0] ?? "";
  if (here && here.split(path.sep).includes(".nemesis")) return true;
  const paths = [...i.files, here].map((p) => p.trim()).filter(Boolean);
  return paths.length > 0 && paths.every((p) => p.split(path.sep).includes(".nemesis"));
}

/**
 * Which lane clears this finding.
 *
 * `record` — Nemesis's own bookkeeping: a missing or stale S0/S1, an edit with no S2 verdict,
 *   a scan that was skipped, a holdout or review record, anything whose only files are under
 *   `.nemesis/`. The machine repairs these. They NEVER reach Zee.
 * `product` — everything else: a rule about code or content that ships.
 */
export function laneOf(i: Issue): Lane {
  // Order matters, and each line earned its place against the real ledger.
  // A missing check is machine work whatever rule it sits under - even a skipped secrets
  // scan, where the answer is "make the scan exist", not "accept the risk".
  if (isMissingCheck(i)) return "record";
  // A secret that was FOUND is product lane wherever the file lives (see isSecretsRule).
  if (isSecretsRule(i.checklist)) return "product";
  // Otherwise the file decides: nothing under `.nemesis/` ships, so clearing it means
  // editing one of Nemesis's own records, and that is the machine's job.
  if (pointsAtNemesisOwnRecord(i)) return "record";
  if (RECORD_STEPS.has(i.checklist.trim())) return "record";
  return "product";
}

export interface Admission { ok: boolean; feature?: string; requirements?: string[]; missing: string[] }

/**
 * Security is never Zee's decision (D-50). PSC is the Prime Security Checks lens (D-06).
 * His standing answer to all of them is already on record: no lapse, in any way. So a PSC
 * finding has no question left in it — only work.
 */
export function isSecurityFinding(i: Issue): boolean { return i.lens === "PSC"; }

/** Is there a CONFIRMED claim that this is a functionality-or-design change question? (D-50) */
export function hasConfirmedProductQuestion(i: Issue): boolean {
  return i.product_question?.confirmed?.agreed === true;
}

/**
 * Can Zee's three choices even be answered for this finding? (D-43)
 *
 * Needs a FEATURE he could drop (the task's title) and a REQUIREMENT he could change (the
 * task's `prd_refs`). Both are recorded by `nemesis task start`, so a finding that lacks them
 * is not blocked forever — supplying them is machine work, and the refusal says so.
 */
export function admission(root: string, i: Issue): Admission {
  const missing: string[] = [];
  if (laneOf(i) === "record") {
    missing.push("this is one of Nemesis's own records, not a product decision — the machine repairs it (D-42)");
    return { ok: false, missing };
  }
  // D-50, the KIND tests, before anything about answerability.
  if (isSecurityFinding(i)) {
    missing.push(`this is a SECURITY finding (${i.checklist}) and Zee has already answered every one of those: no lapse, in any way, and coding the security is the system's job (D-50). There is nothing to ask him - fix it.`);
    return { ok: false, missing };
  }
  const t = i.task ? readTask(root, i.task) : null;
  if (!t) missing.push(`no task on record for "${i.task || "(none)"}", so there is no feature to drop`);
  else if (!t.title.trim()) missing.push(`task ${t.id} has no title, so there is no feature to name`);
  const reqs = (t?.prd_refs ?? []).filter((r) => r.trim());
  if (!reqs.length) missing.push(`task ${i.task} records no PRD requirement, so "change the requirement" has nothing to point at — run: nemesis task prd-refs ${i.task} <R-00x,...>`);
  return missing.length
    ? { ok: false, missing }
    : { ok: true, feature: t!.title, requirements: reqs, missing: [] };
}

/** What the MACHINE must do to clear a record-lane finding (D-42). Never shown to Zee. */
export function repairInstruction(root: string, i: Issue): string {
  const c = i.checklist.trim();
  if (c === "S0") return `Rewrite the threat sketch for task ${i.task} so it covers this file and this data, then: nemesis task sketch ${i.task} <file>. The sketch is Nemesis's own record; repairing it is machine work, never Zee's decision.`;
  if (c === "S1") return `Redo the design review for task ${i.task} so it covers this change, then: nemesis task design ${i.task} <file>.`;
  if (c === "S2") return `This edit has no verdict on record. Re-submit it so the judge sees it, or run: nemesis scan --judge ${i.where.split(":")[0]}`;
  if (c === "S3") return `Make the named check EXIST and pass, then re-run: nemesis scan. A skipped check is a missing record, not a risk to accept.`;
  if (c === "S7") return `Re-run the holdout reveal for task ${i.task}: nemesis task end ${i.task}. If the pack is stale, re-seal it with: nemesis task redesign ${i.task} <file>`;
  if (c === "S6") return `Re-run the independent review: nemesis review ${i.id}`;
  return `Repair the record this finding names, then re-run the step that writes it. This is Nemesis's own bookkeeping (D-42) — it is machine work, and the release gate stays shut until it is done.`;
}

/**
 * The rungs the machine must spend before Zee's attention is spent (D-44).
 *
 * WIDENED from [2, 3, 4] on 2026-11-02, within the hour, by the live ledger. With only 2, 3
 * and 4 required, the machine ruled rung 2 inapplicable 345 times and rung 3 inapplicable 151
 * times - with real, written, non-boilerplate reasons (123 distinct ones) - and 356 findings
 * reached Zee. Its own reasons named the route it should have taken: "the sanctioned route is
 * nemesis task redesign R-019 <issue-id> <design-file> (rung 5)". So ruling a rung out was
 * SHORTENING the ladder instead of moving along it. Rungs 1-6 are all the machine's own; 7 and
 * 8 are positions. "Every automatic rung was tried" means all of them.
 */
export const REQUIRED_RUNGS = [2, 3, 4, 5, 6] as const;

/**
 * At least this many required rungs must be GENUINELY ATTEMPTED — not ruled inapplicable —
 * before a finding may reach Zee (D-49, the floor in `ladderExhausted`).
 */
export const MIN_RUNGS_SPENT = 1;

/**
 * A judge ruling that a rung cannot apply — and that a SECOND, independent reader confirmed.
 *
 * D-49, 2026-11-04. The ruling used to count the moment one judge wrote it. Measured on
 * website-design-okoa/v2 that escape was used 496 times with 123 distinct reasons, reviewed by
 * nobody, and 356 findings reached Zee anyway. Zee: "Just using the judgement is not enough, it
 * has to be best judgement with checks and balances."
 *
 * So `rung-na-proposed` is a claim and counts for nothing. Only `rung-na-confirmed` — written
 * after a reader that never saw the first judge's reasoning agreed the rung is IMPOSSIBLE, not
 * merely unpromising — shortens nothing and opens the door. The legacy `rung-na` event is still
 * honoured so an existing ledger is not retroactively broken, and it is recorded as legacy.
 */
export function rungRuledNA(i: Issue, n: number): boolean {
  const re = new RegExp(`\\brung ${n}\\b`);
  return i.history.some((h) => (h.event === "rung-na-confirmed" || h.event === "rung-na") && re.test(h.detail ?? ""));
}

/**
 * Was rung `n` actually SPENT? Only real work counts.
 *
 * NARROWED 2026-11-02, within the hour, by the live ledger. This used to also accept a history
 * line matching "\u2192 n", meaning the issue was MOVED to rung n. But task end parks an open
 * finding at rung 3 and writes "7 \u2192 3 (task-end retry with full history)", so 345 of 396
 * open findings counted rung 3 as spent when nobody had done a single thing at rung 3. Being
 * parked somewhere is not work. Only an attempt the judge actually saw, or a CLI step that
 * recorded its own result, counts now.
 */
export function rungAttempted(i: Issue, n: number): boolean {
  // An edit re-judged at that rung. This is the ordinary case for rungs 1, 2, 3 and 5.
  if (i.attempts.some((a) => a.rung === n)) return true;
  // Rung 4 is the second opinion from another model family, and the CLI spends it by itself:
  // `nemesis second-opinion <id>` records an analysis when a provider answers, or
  // `status: "unavailable"` with the reason when none is configured. Both are rung 4 spent.
  // Without this a project with no `second_opinion_provider` could never clear rung 4 at all
  // (253 of 356 findings on website-design-okoa/v2), which would be a brand-new stuck state.
  if (n === 4 && i.second_opinion) return true;
  // Rung 5 is the redesign: `nemesis task redesign` writes this event onto the issue itself.
  if (n === 5 && i.history.some((h) => h.event === "redesign")) return true;
  // Rung 6 is revert-to-green: `nemesis revert` sets `revert` and writes "reverted".
  if (n === 6 && (i.revert || i.history.some((h) => h.event === "reverted"))) return true;
  return false;
}

/**
 * Was rung `n` spent on REAL WORK — an idea actually tried, not a non-event recorded?
 *
 * ADDED 2026-11-04, measured, within minutes of shipping the floor below. `rungAttempted`
 * deliberately counts rung 4 the moment `second_opinion` exists, INCLUDING
 * `status: "unavailable"`, so that a project with no `second_opinion_provider` can still clear
 * what rung 4 OWES instead of deadlocking. That allowance is correct for the owed list and
 * fatal for the floor: measured on website-design-okoa/v2, 338 open findings carry
 * `unavailable` and ZERO carry `received` — there is no external model configured there at all
 * — so one auto-recorded non-event was the ENTIRE ladder for 243 of the 266 findings the gate
 * was admitting. "We have no second model" is a fact about the project, not an idea the machine
 * spent on the finding.
 *
 * So the floor counts only: an attempt the judge actually saw, a second opinion genuinely
 * RECEIVED, a redesign, or a revert. This cannot deadlock — rung 3 (a fresh agent with the
 * written history) is available on any finding, and ruling it out now needs an independent
 * confirmation that it is impossible, which it is not.
 */
export function rungSpentOnRealWork(i: Issue, n: number): boolean {
  if (i.attempts.some((a) => a.rung === n)) return true;
  if (n === 4 && i.second_opinion?.status === "received") return true;
  if (n === 5 && i.history.some((h) => h.event === "redesign")) return true;
  if (n === 6 && (i.revert || i.history.some((h) => h.event === "reverted"))) return true;
  return false;
}

/**
 * D-44 — has the MACHINE spent its own options yet?
 *
 * Rung 8 is "every automatic rung was tried". That sentence was never enforced, and the
 * position rungs (7 at task end, 8 at goal end) promoted findings straight past rungs 2-6.
 * Measured on website-design-okoa/v2, 2026-11-02: of 356 open findings, 0 had ever been
 * moved up a rung by the judge, NONE had ever reached rung 4, 5 or 6, and 83 went from
 * rung 1 to Zee in a single hop. So this test now holds the door.
 *
 * The escape, so the gate can never deadlock: the judge may rule a rung inapplicable, with
 * a reason, via `nemesis ladder <id> --na <n> --why "..."`. That keeps a human out of it.
 */
export function ladderExhausted(i: Issue): { ok: boolean; owed: number[]; next?: number; spent: number; floor?: boolean } {
  const owed = REQUIRED_RUNGS.filter((n) => !rungAttempted(i, n) && !rungRuledNA(i, n));
  const spent = REQUIRED_RUNGS.filter((n) => rungSpentOnRealWork(i, n)).length;
  if (owed.length) return { ok: false, owed: [...owed], next: owed[0], spent };
  // THE FLOOR (D-49). An exhausted ladder means the machine SPENT ITS IDEAS, not that it wrote
  // down why it had none. `spent` counts real work only (see rungSpentOnRealWork): an attempt
  // the judge saw, a second opinion genuinely RECEIVED, a redesign, or a revert. An
  // `unavailable` second opinion does NOT count here, because measured on
  // website-design-okoa/v2 that single auto-recorded non-event was the entire ladder for 243 of
  // the 266 findings this gate was admitting. This cannot deadlock: rung 3 hands the finding
  // with its full written history to a fresh agent and is available on anything, and ruling
  // rung 3 out now needs an independent confirmation that it is impossible.
  if (spent < MIN_RUNGS_SPENT) return { ok: false, owed: [], spent, floor: true };
  return { ok: true, owed: [], spent };
}

/**
 * What the machine can actually DO to pay the floor on this finding — and have it recorded.
 *
 * REWRITTEN 2026-11-04 after the `v2-ee` session measured that the previous text named a move
 * the ledger cannot credit. Rungs 2 and 3 are paid by an edit being re-judged, and
 * `recordFindings` appends an attempt only when the finding's task matches the task being worked
 * (`i.where === f.where && i.checklist === f.checklist && i.task === task`). So on a finding
 * belonging to any task other than the current one, a fresh agent can do real work and nothing
 * records it. Measured there: 217 of 447 open findings sit on a task that is not current.
 *
 * There is no deadlock, which is why the floor stays as it is: rungs 5 and 6 have CLI commands
 * that take the target explicitly and carry no rung gate and no current-task gate, so they are
 * payable on any finding — `cmdTaskRedesign(taskId, issueId, file)` writes the `redesign` event
 * onto the issue itself, and `cmdRevert(id)` writes `revert`. This function names the cheapest
 * route that will actually be credited, which depends on whether the finding is on the task in
 * hand.
 */
function payableRungs(root: string, i: Issue): string {
  const cur = currentTask(root);
  const onCurrent = !!cur && cur.id === i.task;
  const fresh = `rung 3 — hand ${i.id} to a FRESH agent with its written history: Task(developer) given .nemesis/issues/${i.id}.json and .nemesis/tasks/${i.task}/, never the conversation`;
  const redesign = `rung 5 — nemesis task redesign ${i.task} ${i.id} <design-file>`;
  const revert = `rung 6 — nemesis revert ${i.id}`;
  return onCurrent
    ? `${fresh}; or ${redesign}; or ${revert}`
    : `this finding is on task ${i.task}, which is NOT the task in hand${cur ? ` (${cur.id})` : ""}, so an edit re-judged now would be recorded against ${cur?.id ?? "no task"} and would NOT credit rungs 2 or 3 on it. The routes that take the target explicitly and WILL be credited: ${redesign}; or ${revert}. To pay rung 3 instead, make ${i.task} the task in hand first.`;
}

/**
 * Why the KIND test runs LAST (D-50, ordering settled by this skill's own selftests).
 *
 * Put the product-question test first and every refusal reads "nothing says this is Zee's -
 * claim it if you think it is", which is the wrong instruction when it is not his: it names a
 * claim to make instead of a move to make. The machine should always be told its next MOVE, so
 * the order is: Nemesis's own paperwork (D-42), security (D-50, decisive and permanent), the
 * anchors Zee would need (D-43), the ladder the machine still owes (D-44/D-49), and only then
 * the question of whether this is a functionality or design change at all.
 */
function productQuestionRefusal(root: string, i: Issue): string {
  const pq = i.product_question;
  if (pq?.confirmed && !pq.confirmed.agreed) return `an independent reader REFUSED the claim that this is a functionality or design question: "${pq.confirmed.why}" - so it is the machine's to fix (D-50), and no re-claim changes that. Next move: ${payableRungs(root, i)}`;
  if (pq) return `the claim that this is a ${pq.kind} question is recorded but NOT confirmed independently, so it counts for nothing (D-50). Re-run: nemesis issue product-question ${i.id} --kind ${pq.kind} --why "<why no code change can clear it>"`;
  return `this is the MACHINE's to fix: nothing on record says it is a change to what the product DOES or how it LOOKS, and Zee gets functionality and design questions and nothing else (D-50). A bug, a contradiction between two documents, a stale note, or a comment that disagrees with its code are all machine work however often they recur. Next move: ${payableRungs(root, i)}. ONLY if no code change could ever clear this, claim it and have it confirmed: nemesis issue product-question ${i.id} --kind <functionality|design> --why "<reason>"`;
}

/** The ONE gate that decides whether a finding may reach Zee: D-42 + D-43 + D-44 + D-49 + D-50. */
export function admitToRung8(root: string, i: Issue): { ok: boolean; why: string[]; feature?: string; requirements?: string[] } {
  const a = admission(root, i);
  if (!a.ok) return { ok: false, why: a.missing };
  const l = ladderExhausted(i);
  if (!l.ok && l.floor) return { ok: false, why: [`nothing was actually TRIED on this finding — every required rung is either ruled inapplicable or satisfied only by a recorded non-event (an "unavailable" second opinion is not an idea spent). That is not an exhausted ladder (D-49). Spend one for real: ${payableRungs(root, i)}`] };
  if (!l.ok) return { ok: false, why: [`the machine still owes rung ${l.next} on this finding (owed: ${l.owed.join(", ")}) — D-44 forbids spending Zee's attention first. Record it, or rule it inapplicable: nemesis ladder ${i.id} --na ${l.next} --why "<reason>"`] };
  // D-50, LAST: an exhausted ladder is not a reason to ask him. Only a confirmed functionality
  // or design question is. "Now it is 23, if I do a large enough job, it could become 230" - the
  // count scales with the code, so the gate has to test the KIND.
  if (!hasConfirmedProductQuestion(i)) return { ok: false, why: [productQuestionRefusal(root, i)] };
  return { ok: true, why: [], feature: a.feature, requirements: a.requirements };
}
