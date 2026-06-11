# Phase 2 — Per-Paper Orchestrator (grader-paper)

This is the Wigum-loop guide for the `grader-paper` agent. One instance runs
per paper; multiple instances run concurrently (windowed parallel from the
main conversation).

## Your input

A session manifest path + a paper ID, delivered by the main conversation:

```
Session manifest: .acos/state/grader-sessions/grader-20261018T143000/manifest.yaml
Paper ID: STUDENT_123
```

## Your job

Drive the paper through the full consensus pipeline and write a finalized
result artifact. You own all re-dispatch logic, all iteration tracking, and
all synthesis for this paper. The main conversation does not see your
iteration chatter — only your final artifact.

## Loop logic

```
iteration = 1
converged_criteria = {}        # criterion_id → {points: float, reasonings: [str, str, str]}
disputed_criteria  = {}        # criterion_id → {points: float, reasonings: [...], reason: "max_iters"}
pending_criteria   = ALL       # all criterion IDs from the rubric

WHILE pending_criteria:

  # STEP A: Dispatch 3 graders IN PARALLEL on pending_criteria
  Task(grader-opus,   prompt=grader_prompt(paper, rubric, pending_criteria, "A"), run_in_background=True)
  Task(grader-opus,   prompt=grader_prompt(paper, rubric, pending_criteria, "B"), run_in_background=True)
  Task(grader-sonnet, prompt=grader_prompt(paper, rubric, pending_criteria, "C"), run_in_background=True)

  # STEP B: Wait for all three, collect grading sheets
  grading_sheets = collect_three_grader_outputs()

  # STEP C: Persist iteration artifacts
  write_yaml(iter_path("grading/{paper_id}/iter-{iteration}-grader-opus-A.yaml"), sheets.A)
  write_yaml(iter_path("grading/{paper_id}/iter-{iteration}-grader-opus-B.yaml"), sheets.B)
  write_yaml(iter_path("grading/{paper_id}/iter-{iteration}-grader-sonnet.yaml"), sheets.C)

  # STEP D: Dispatch QA (ONE agent, paper-level context, per-criterion output)
  qa_verdict = Task(grader-qa, prompt=qa_prompt(paper, rubric, sheets_A, sheets_B, sheets_C, pending_criteria))
  write_yaml(iter_path("grading/{paper_id}/iter-{iteration}-qa-verdict.yaml"), qa_verdict)

  # STEP E: Split verdicts
  FOR criterion IN pending_criteria:
    IF qa_verdict[criterion] == "PASS":
      converged_criteria[criterion] = {
        "name":         rubric[criterion].name,            # criterion name (rendered by cohort-curve)
        "points_total": rubric[criterion].points,          # max points for this criterion (rendered as "Points Total")
        "points":       mean(sheets.A[criterion].points, sheets.B[criterion].points, sheets.C[criterion].points),
        "reasonings":   [sheets.A[criterion].reasoning, sheets.B[criterion].reasoning, sheets.C[criterion].reasoning],
      }
      pending_criteria.remove(criterion)

  # STEP F: Check exit conditions
  IF NOT pending_criteria:
    BREAK                                         # All converged
  IF iteration >= max_iters:
    FOR criterion IN pending_criteria:
      disputed_criteria[criterion] = {
        "name":         rubric[criterion].name,            # criterion name (rendered by cohort-curve)
        "points_total": rubric[criterion].points,          # max points for this criterion (rendered as "Points Total")
        "points":       mean(latest_iter.A[criterion], latest_iter.B[criterion], latest_iter.C[criterion]),
        "reasonings":   [latest three reasonings],
        "reason":       "max_iters_exceeded",
      }
    BREAK

  iteration += 1
  # Loop back — pending_criteria still contains only the failed criteria,
  # so the next iteration only re-grades those.

# STEP G: Synthesize final reasoning per converged criterion
FOR criterion IN converged_criteria:
  synth_output = Task(grader-synth, prompt=synth_prompt(criterion, converged_criteria[criterion].reasonings))
  converged_criteria[criterion]["final_reasoning"] = synth_output.merged_paragraph

# STEP H: Write final artifact
write_yaml(
  path=f"results/{paper_id}.yaml",
  data={
    "paper_id":        paper_id,
    "iterations_used": iteration,
    "criteria":        converged_criteria | disputed_criteria,
    "raw_total":       sum(c.points for c in criteria),
    "disputed_ids":    list(disputed_criteria.keys()),
  },
)

# STEP I: Write audit log
write_yaml(
  path=f"audit/{paper_id}-audit.yaml",
  data={
    "paper_id":       paper_id,
    "total_iters":    iteration,
    "iteration_history": [full trace of every iteration's grades and QA verdicts],
  },
)

RETURN
```

## Grader prompt construction (CRITICAL — blind re-dispatch with entropy)

On every iteration, the grader receives:
- The paper text
- The rubric (with per-criterion floor/ceiling)
- The subject subtype
- The criteria to grade (on iter 1: all; on iter >1: only failed criteria)
- **Calibration hints** (if session was run with `--calibrate` AND the current
  paper is NOT a calibration paper) — inject the full `calibration_hints[]`
  list from the manifest. Graders see this as additional rubric guidance.
  Calibration papers themselves are graded WITHOUT hints (hints are derived
  from their divergence; injecting them back would be circular).
- **An iteration nonce** — a fresh UUID generated per iteration, prepended to
  the prompt as: `Session marker: <UUID>` with no further explanation.

### Why the nonce matters (entropy injection)

Claude's prompt caching + deterministic sampling (temperature=0 default for
most agent contexts) can make a re-dispatched grader produce the *exact same*
output as the prior iteration — the prompts are bit-identical, the cache hit
is complete, and there is no organic convergence, only deterministic looping.
If iteration 1 diverged, iterations 2–5 would diverge identically and the
criterion would hit max_iters with no real re-evaluation.

The iteration nonce:
1. **Breaks the prompt cache.** The UUID prefix changes every iteration, so
   the cache doesn't hit and the model re-reasons from first principles.
2. **Is semantically null.** "Session marker: abc123" carries no information
   about grades, correctness, or prior output — the grader has no anchor to
   a previous answer.
3. **Preserves the blind re-dispatch rule.** No feedback is leaked; no "you
   got this wrong" signal; the grader genuinely re-approaches the criterion.

Without this entropy, the Wigum loop is effectively a no-op — deterministic
sampling will produce the same grade forever.

### Grader prompt template (on every iteration)

```
Session marker: <fresh UUID — ignore this line, it is for session bookkeeping>

<QUESTIONS / REQUIREMENTS / INSTRUCTIONS GIVEN TO THE STUDENT>
  (Include the full text of questions.txt if it exists in the session dir.
   Omit this section entirely if --questions-file was not supplied.)

<STUDENT'S SUBMISSION — paper text>
<RUBRIC YAML with per-criterion floor/ceiling>
<SUBJECT SUBTYPE: e.g., "Investment Management">
<CALIBRATION HINTS (if applicable)>
<CRITERIA TO GRADE: list of criterion IDs, each with optional question_id
  mapping from the rubric (hybrid mapping — Option C)>
<OUTPUT PATH: where to write your grading sheet>
```

**Hybrid question-to-criterion mapping.** When a rubric criterion has an
explicit `question_id` field (optional per criterion), include that mapping
in the grader's criteria list:

```
Criteria to grade:
  - id: criterion_3
    question_id: Q2         # explicit mapping — grader should focus on Q2
  - id: criterion_5
    question_id: null       # implicit — grader infers from full questions
                             # text and rubric description
```

Graders with explicit mapping cite evidence from the mapped question's
answer specifically. Graders without explicit mapping use the full questions
text as context and their domain expertise to match criterion to answer.

Do NOT include:
- Any prior iteration's grades (theirs or others')
- Any QA verdict or rejection reason
- Any hint that consensus failed
- The iteration number itself

Construct the prompt **identically** across iterations except for the fresh
nonce and the list of criteria to grade. The grader has no memory of prior
runs because each Task() call is a fresh context; the nonce ensures no cached
path is taken.

**On iterations > 1, graders MUST NOT receive:**
- Any prior iteration's grades (theirs or others')
- Any QA verdict or rejection reason
- Any hint that consensus failed

Construct the prompt **identically** across iterations except for the list of
criteria to grade. The grader agent has no memory of prior runs because each
Task() call is a fresh context. Do not leak re-grade context via the prompt.

The grader does not know this is a re-grade. From its perspective, it is
grading a fresh paper.

## Parallelism inside the orchestrator

Spawn all three graders in a single message with `run_in_background=True`.
Wait for all three to complete before dispatching QA. The QA call is
sequential (depends on the three grading sheets).

Synthesis is parallelizable across criteria — you can spawn one `grader-synth`
per converged criterion simultaneously if desired. For simplicity and token
economy, sequential synthesis is acceptable.

## Near-zero consensus guardrail

The QA agent handles numerical consensus. You do NOT compute consensus yourself
— the QA agent is the authority. Simply forward its verdict.

## Error handling inside the loop

- **Grader crash** — retry that grader ONCE in-place; if still failing, mark
  the paper INCONCLUSIVE, write a partial result artifact, and return.
- **QA crash** — retry ONCE; if still failing, abort with all grader output
  preserved. Mark paper INCONCLUSIVE.
- **Synthesizer crash** — fall back to concatenating the three reasonings
  verbatim separated by ` | ` — never abort a paper over synthesis failure.

## Exit contract

Your return message to the main conversation should be a single line:

```
DONE paper_id=STUDENT_123 status=OK iterations=3 disputed=0
```

or:

```
DONE paper_id=STUDENT_123 status=INCONCLUSIVE iterations=5 disputed=2 reason="qa_crash_after_retry"
```

The main conversation reads the result artifact from disk — not your chat
output. Keep your return terse.
