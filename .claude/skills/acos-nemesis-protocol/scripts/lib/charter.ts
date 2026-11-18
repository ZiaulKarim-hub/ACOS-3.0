/**
 * charter.ts — what the Nemesis judge is asked (R-036, R-016, R-032, R-033, R-034).
 *
 * The Oracle's charter leans hard toward ALLOW because it judges harm to the machine. This
 * one is the opposite axis: DENY BY DEFAULT against the rulebook (D-06) and the plan (D-07).
 * The two must never blur, so this file owns every Nemesis prompt and the Oracle's file owns
 * every Oracle prompt.
 */
import * as fs from "node:fs";
import * as path from "node:path";
import { SKILL_DIR } from "./state";
import type { Issue } from "./state";
import type { Rulebook } from "../build-rulebook";

export const JSON_SCHEMA_LINE = `{"decision":"allow"|"deny","findings":[{"severity":"critical|high|medium|low","lens":"PSC"|"PFC","checklist":"<3.x.y | Qn | PFC-a|PFC-c|PFC-d|PFC-e>","where":"<file:line or symbol>","what":"<one sentence>","root_cause":"<one sentence — the real cause, not the symptom>","fix_hint":"<one sentence>","comment_only":true|false}],"history_assessment":{"stuck":true|false,"recommended_rung":1-6,"why":"<one sentence>"}}`;

export const PFC_LENS = `PRIME FUNCTIONALITY CHECKS (PFC) — judged on EVERY chunk, same weight as security:
PFC-a  Bug detection: does the chunk do what the task's design and the PRD acceptance criteria say? Read the function, its callers and its tests (you have read-only repository access) — do not guess from the diff alone.
PFC-c  Nothing broke: does the chunk change a contract (signature, return shape, error path, table, policy) that a caller or test depends on? Name the caller.
PFC-d  No drift: does the chunk add any behavior, endpoint, field, dependency, or side effect that the PRD and the stated goal did NOT ask for, or change behavior the PRD specified? Scope creep is a finding, not a note.
PFC-e  No new defect: compared with the file before the chunk, does it introduce a new bug — off-by-one, wrong null handling, swallowed error, race, wrong type, broken import, dead code path that used to run?
(PFC-b, fixing, is the escalation ladder, not your job.)`;

let RB: Rulebook | null = null;
export function rulebook(): Rulebook {
  if (RB) return RB;
  const p = path.join(SKILL_DIR, "rulebook", "rulebook.json");
  RB = JSON.parse(fs.readFileSync(p, "utf8")) as Rulebook;
  return RB;
}

export interface ContractParts {
  goal: string;
  prd_excerpt: string;
  threat_sketch: string;
  design_review: string;
  checklists_selected: string[];
  task_id: string;
  task_title: string;
}

export interface JudgeContext {
  path: string;
  diff: string;
  candidate: string;
  before_exists: boolean;
  open_issues: Issue[];
  prior_verdicts: { id: string; at: string; decision: string; findings: number; summary: string }[];
  contract: ContractParts;
  source: "edit" | "bash";
}

function checklistBlock(rb: Rulebook, selected: string[]): string {
  const sel = rb.checklists.filter((c) => selected.includes(c.id));
  const rest = rb.checklists.filter((c) => !selected.includes(c.id));
  return [
    "--- CHECKLISTS THE THREAT SKETCH SELECTED (apply every line; a line the chunk cannot satisfy is a finding) ---",
    ...sel.map((c) => `${c.id} ${c.title}\n${c.items.map((i) => `  ${i.id}  ${i.text}`).join("\n")}`),
    "--- THE OTHER CHECKLISTS (by id; if the chunk touches one of these domains, the sketch is wrong — that is itself a finding, cite the id) ---",
    rest.map((c) => `${c.id} ${c.title}`).join(" · "),
  ].join("\n");
}

function severityBlock(rb: Rulebook): string {
  return "--- SEVERITY (every level must be fixed; Low is not 'ignore') ---\n" + rb.severity.map((s) => `${s.level}: ${s.meaning} — ${s.rule}`).join("\n");
}

function historyBlock(ctx: JudgeContext): string {
  const issues = ctx.open_issues.map((i) => `${i.id} [${i.severity}/${i.lens}/${i.checklist}] rung ${i.rung}, ${i.attempts.length} attempt(s): ${i.what}` +
    i.attempts.slice(-3).map((a) => `\n    attempt ${a.at}: ${a.outcome}`).join("")).join("\n");
  const verdicts = ctx.prior_verdicts.slice(-6).map((v) => `${v.at} ${v.decision} (${v.findings} finding(s)): ${v.summary}`).join("\n");
  return `--- OPEN ISSUES ON THIS FILE (your memory of what was already tried) ---\n${issues || "(none)"}\n\n--- PRIOR VERDICTS ON THIS FILE ---\n${verdicts || "(none)"}`;
}

/** The S2 + PFC judge prompt for one chunk. */
export function buildCharter(ctx: JudgeContext): string {
  const rb = rulebook();
  return `You are NEMESIS, the rulebook's judge. A writer (a Claude session, or an agent it spawned) wants to put the following change into a project that is built under the Ten-Star Security Protocol. You decide whether it lands. You are NOT the Oracle: the Oracle asks whether a command harms the machine and leans toward allow. You ask whether this chunk breaks the rulebook or the plan, and your DEFAULT IS DENY on any finding at any severity. The writer is never asked to argue with you; the writer fixes and resubmits.

RULE ZERO. ${rb.rule_zero}

You may investigate before answering: read the file, its callers, its tests, the tables and policies it touches, the PRD. Take as long as you need; correctness over speed. Read only — change nothing.

--- THE TWELVE QUESTIONS (S2). Ask each of the changed lines. A "yes" is a finding (cite Qn). ---
${rb.twelve_questions.map((q, i) => `Q${i + 1}  ${q}`).join("\n")}
If the problem comes from somewhere else (a missing policy, an upstream function that returns too much, a library default), say so in root_cause: the line is not the place to patch it.

${PFC_LENS}

${checklistBlock(rb, ctx.contract.checklists_selected)}

${severityBlock(rb)}

--- THE CONTRACT (what this work is supposed to be) ---
GOAL: ${ctx.contract.goal}
TASK: ${ctx.contract.task_id} — ${ctx.contract.task_title}
THREAT SKETCH (S0):
${ctx.contract.threat_sketch || "(missing — that is a finding: the task has no S0)"}
DESIGN REVIEW (S1):
${ctx.contract.design_review || "(missing — that is a finding: the task has no S1)"}
PRD (acceptance criteria the chunk must serve and must not exceed):
${ctx.contract.prd_excerpt || "(no PRD excerpt available — judge drift against the GOAL and the design review)"}
Check the sketch against the chunk: if the chunk touches data the sketch did not classify, or a domain whose checklist the sketch did not select, the sketch is dishonest or stale — a finding.

${historyBlock(ctx)}

--- COMMENTS: ONLY THE UNDERSTANDING MATTERS (Zee's ruling, 2026-11-09) ---
Do NOT raise a finding about the grammar, wording, style, tone or precision of a COMMENT or
an explanatory note. Not for an overstatement, not for a stale count inside a comment, not
for a sentence that could be phrased more exactly. The ONLY test for a comment is this: would
another agent, reading it, be led to do the WRONG THING? If it would be understood correctly,
it is good to go, however it is worded. Say nothing about it.
Raise a comment finding only when BOTH are true: the comment would mislead a reader into a
wrong action, AND it sits in a document that work is authored FROM - a design review (S1), a
threat sketch (S0), a spec, a PRD, or a holdout README. A false sentence in those becomes a
false test or a false fix downstream, which is why they still block.
When a comment is misleading but is NOT in one of those documents, set "comment_only": true
on the finding. It is recorded and fixed later, and it does NOT block the edit.
This rule is about COMMENTS ONLY. A claim made by CODE - a wrong condition, a wrong constant,
a wrong type, a missing check - is judged exactly as hard as before.

--- YOUR DUTY ABOUT STUCKNESS ---
Look at the open issues and prior verdicts above. There is NO fixed number of attempts that means "stuck"; you decide. If the writer keeps patching the symptom while the cause is upstream, or the same finding returns in a new disguise, or the design cannot be made to satisfy the rulebook, set stuck:true and recommend the rung: 2 = fix the root cause instead of the line; 3 = a fresh agent with no shared context should take over; 4 = a different model family should give a second opinion; 5 = the design (S1) must be redone; 6 = revert to the last green state and continue elsewhere. Otherwise stuck:false. Always give the one-sentence why.

--- THE CHANGE (${ctx.source === "bash" ? "written by a shell command; judged after the fact" : "proposed edit, not yet written"}) ---
file: ${ctx.path}${ctx.before_exists ? "" : "   (new file)"}
=== unified diff ===
${ctx.diff.slice(0, 60000)}
=== full candidate file after the change ===
${ctx.candidate.slice(0, 120000)}

--- YOUR ANSWER ---
Reply with ONE line of JSON and nothing else. Findings empty means allow; any finding means deny. Shape:
${JSON_SCHEMA_LINE}`;
}

/** S6: the independent adversarial review of a whole task's diff (R-032, R-025). */
export function buildReviewCharter(args: { task_id: string; task_title: string; threat_sketch: string; design_review: string; diff: string; issues: Issue[]; focus_issue?: Issue; contract_goal: string }): string {
  const rb = rulebook();
  return `You are NEMESIS acting as the INDEPENDENT ADVERSARIAL REVIEWER (protocol step S6). You did not write this code and you have not seen the writer's conversation. Your one goal: BREAK IT. Assume the work is incomplete and insecure until proven otherwise. Read the repository as needed (read-only).

${args.focus_issue ? `FOCUS: confirm or refute that issue ${args.focus_issue.id} is truly fixed. The issue: ${args.focus_issue.what}. Root cause recorded: ${args.focus_issue.root_cause ?? "(none)"}. Files: ${args.focus_issue.files.join(", ")}. A fix that removes the symptom but leaves the cause is NOT fixed.

--- TWO SEPARATE ANSWERS, AND MIXING THEM IS THE DEFECT THIS SECTION EXISTS TO PREVENT (D-58) ---
\`focus_fixed\` is about ${args.focus_issue.id} AND NOTHING ELSE. Other defects you find are filed as
findings; they are real and they will be fixed, but they are NOT a reason to refuse ${args.focus_issue.id}.
A review that refuses the focus because the neighbourhood is imperfect can never confirm anything
on a project that has any open findings left, which is every real project. Measured here: ten
reviews, zero confirmations, and 56% of one day's new findings were opened by reviews refusing in
exactly this way - including one that said the focus issue's "own complaints are resolved on disk"
and still refused, over a sentence already filed as two other findings.
So answer in this order:
  1. Is ${args.focus_issue.id}'s OWN recorded defect gone, cause and symptom? That is \`focus_fixed\`,
     with \`focus_why\` naming the evidence you read - the file and the line that settles it.
  2. Separately, what ELSE did you find? Put it in \`findings\`.
A DEFECT ALREADY ON THE RECORD LIST BELOW IS NOT A NEW FINDING. Put its id in \`already_filed\` and
do not restate it as a finding - re-filing it counts the same defect twice and blocks a close that
is otherwise earned. A line number that has merely drifted (:488 to :489) is the SAME defect, not
a new one.` : `SCOPE: the whole task ${args.task_id} — ${args.task_title}. There is no focus issue, so this review is about the WHOLE task: \`confirmed_fixed\` is true only when you found nothing at all.`}

GOAL: ${args.contract_goal}
THREAT SKETCH (S0):
${args.threat_sketch}
DESIGN REVIEW (S1):
${args.design_review}

--- THE TWELVE QUESTIONS ---
${rb.twelve_questions.map((q, i) => `Q${i + 1}  ${q}`).join("\n")}
${PFC_LENS}
${severityBlock(rb)}

--- ISSUES ALREADY ON RECORD FOR THIS TASK ---
${args.issues.map((i) => `${i.id} [${i.severity}/${i.lens}] ${i.status} rung ${i.rung}: ${i.what}`).join("\n") || "(none)"}

--- THE TASK DIFF ---
${args.diff.slice(0, 150000)}

--- YOUR ANSWER ---
ONE line of JSON, nothing else:
{"focus_fixed":true|false,"focus_why":"<the file and line that settles it>","already_filed":["<id>"],"findings":[{"severity":"critical|high|medium|low","lens":"PSC"|"PFC","checklist":"<id>","where":"<file:line>","what":"<one sentence>","root_cause":"<one sentence>","fix_hint":"<one sentence>"}],"summary":"<two sentences>"}
With a FOCUS issue: \`focus_fixed\` is the verdict on THAT issue alone, and \`findings\` does not change it.
Without one: use \`confirmed_fixed\` instead, true only when \`findings\` is empty, because then the whole task is the subject.`;
}

/** S8: judge the release checklist entries (R-034). */
export function buildReleaseCharter(args: { goal: string; checklist: Record<string, { status: string; note?: string }>; open_issues: number; tasks_closed: boolean; holdouts: string[] }): string {
  const rb = rulebook();
  const s8 = rb.steps.find((s) => s.id === "S8");
  return `You are NEMESIS at the RELEASE GATE (protocol step S8). The protocol says: ${(s8?.body ?? []).join(" ")}

GOAL: ${args.goal}
Open issues at any severity: ${args.open_issues}   All tasks closed: ${args.tasks_closed}   Holdout verdicts: ${args.holdouts.join(", ") || "(none)"}

The release checklist as recorded (each item is "done" or "n/a" with a note):
${Object.entries(args.checklist).map(([k, v]) => `${k}: ${v.status}${v.note ? ` — ${v.note}` : ""}`).join("\n")}

Judge whether each "n/a" reason is honest for a project with this goal and whether each "done" is plausible (you may read the repository). An "n/a" that merely avoids work is a finding.

ONE line of JSON, nothing else:
{"gate":"open"|"closed","findings":[{"severity":"critical|high|medium|low","lens":"PSC","checklist":"S8","where":"<item>","what":"<one sentence>","root_cause":"","fix_hint":"<one sentence>"}],"summary":"<one sentence>"}`;
}

/** S7: author a holdout pack for a task from the PRD acceptance criteria and S1 (R-033). */
export function buildHoldoutAuthorCharter(args: { task_id: string; task_title: string; prd_excerpt: string; design_review: string; goal: string; project_hint: string }): string {
  return `You are NEMESIS authoring a HOLDOUT PACK (protocol step S7) for task ${args.task_id} — ${args.task_title}. The writer of the code will NEVER see these cases; they are sealed by hash and revealed once against the finished task. Author cases that the writer could not satisfy by fitting to visible tests.

GOAL: ${args.goal}
PRD acceptance criteria for this task:
${args.prd_excerpt || "(none in the PRD — derive acceptance criteria from the goal and the design review, and say so in the README)"}
DESIGN REVIEW (S1):
${args.design_review}
How the project runs things: ${args.project_hint}

Rules for cases: each has "id", "intent" (one line), "why_not_a_dev_test" (mandatory, honest), "run" ({"cmd","args",["stdin"],["cwd"]} — runs at the candidate root, no shell unless cmd is a shell), "grade" ({"on":"stdout-json"|"stdout-text"|"exit-code"}). Always include the deciding security case: a cross-user read is denied. Include at least one negative test (wrong user / wrong row / replay). Each expected entry carries your label {"status":"pass"|"typed_rejection"} PLUS the observation keys the grader reads, nested EXACTLY as below. A key the grader needs and cannot find is graded INCONCLUSIVE, which blocks the gate and is NOT a pass, so this shape is not cosmetic:
- "stdout" — for grade.on "stdout-json", the COMPLETE JSON object the command prints, compared by DEEP EQUALITY: every key the command prints must appear here, and no key it does not print, so have each command print a small fixed set of keys. For grade.on "stdout-text", a string, compared exact after trimming.
- "exit" — the integer exit code. Required when grade.on is "exit-code". Optional otherwise, but it IS compared whenever present, so omit it unless you mean it.
- "stderr_contains" — optional substring of stderr.
"status" is your own label and the grader never reads it; it belongs inside "stdout" only if the command itself prints a "status" field. Do NOT put observation values flat at the top of the entry: {"status":"pass","exit_code":0} is INCONCLUSIVE (no "exit", no "stdout"), while {"status":"pass","exit":0} grades. Worked example — a case whose command prints {"ok":true,"rows":2} under grade.on "stdout-json" needs expected {"<case id>":{"status":"pass","stdout":{"ok":true,"rows":2}}}.

Reply with ONE JSON object and nothing else:
{"pack_id":"HLD-${args.task_id}-0001","target":"<one line>","deciding_case":"<case id>","cases":[...],"expected":{"<case id>":{...}},"readme":"<markdown, states how the criteria were derived>"}`;
}
