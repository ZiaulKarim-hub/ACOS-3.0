# Phase 1b — Calibration (optional)

Run only when the user invoked acos-grader with `--calibrate N` (where N is
the calibration sample size, typically 3–8 papers). This phase runs between
Phase 1 (ingest) and Phase 2 (full grading). It exists to tighten grader
alignment on ambiguous rubric criteria before the main batch, reducing the
iteration count and DISPUTED-criteria rate on the remaining papers.

## Goal

Detect criteria where the three graders systematically diverge in the
calibration sample, then produce **calibration hints** — short prompt
addenda injected into grader system context for the remaining papers.

The calibration papers themselves are graded with the UN-augmented prompts
and their grades stand as-is. Only subsequent papers benefit from the
calibration hints.

## Inputs

- `session_dir` — the session directory from Phase 1
- `manifest_path` — the session manifest
- `calibrate_n` — from CLI flag `--calibrate`
- `questions_text_path` (if `--questions-file` was provided) — path to
  `${SESSION_DIR}/questions.txt`. The calibrator reads this to identify
  whether divergence patterns stem from genuinely ambiguous rubric criteria
  vs. graders interpreting the question itself differently. Hints that
  resolve question-interpretation ambiguity should reference the question
  explicitly (e.g., "For question Q2, the rubric's 'explain' should be read
  as 'justify with citations,' not 'describe'").

## Step 1b.1 — Select calibration papers

Take the first N papers (by sorted filename) from the manifest's paper list.
Alternative: random sample. First-N is deterministic and reproducible, which
matters for audit.

```python
calibration_ids = [p.paper_id for p in manifest.papers[:calibrate_n]]
```

Update the manifest with a `calibration_paper_ids` list so Phase 2 knows not
to re-process them later.

## Step 1b.2 — Grade the calibration sample

Run normal Phase 2 dispatch, but only for the calibration papers. Use the
same windowed-parallel pool as the main batch. Wait for all calibration
papers to complete before proceeding.

At this point, `session_dir/results/<calibration-id>.yaml` and audit logs
exist for each calibration paper, just like a normal run.

## Step 1b.3 — Analyze divergence (grader-calibrator agent)

Spawn the `grader-calibrator` agent:

```python
Task(
    subagent_type="grader-calibrator",
    prompt=f"""
Session directory: {session_dir}
Manifest path: {manifest_path}
Rubric path: {session_dir}/rubric.yaml
Calibration paper IDs: {calibration_ids}
""",
)
```

The calibrator:
1. Reads all grading sheets and QA verdicts from the calibration papers
2. Computes per-criterion divergence metrics (avg spread, iteration count,
   reasoning theme variance)
3. Identifies divergent criteria (thresholds in `grader-calibrator.md`)
4. Writes calibration hints to `manifest.calibration_hints[]`
5. Writes a report to `session_dir/audit/calibration-report.yaml`

## Step 1b.4 — Surface calibration results to user

Present a concise summary in the primary conversation:

```
Calibration complete (N = 5 papers).

Divergence analysis:
  criterion_1 (Sharpe ratio identification)   — well-calibrated    spread ≤ 1.2%
  criterion_2 (MVO application)               — well-calibrated    spread ≤ 2.8%
  criterion_3 (Factor tilt justification)     — DIVERGENT          spread 8.4%, avg 2.4 iters → hint added
  criterion_4 (Constraint handling)           — well-calibrated    spread ≤ 1.9%
  criterion_5 (Recommendation conclusion)     — DIVERGENT          spread 6.1%, avg 2.0 iters → hint added

2 of 5 criteria received calibration hints. Proceed with remaining 42 papers
using these hints? (y/n)
```

On `y`: main conversation proceeds to Phase 2 for the non-calibration papers.
Grader prompts now include the calibration hints for relevant criteria.

On `n`: halt. Session directory is preserved. The user can edit the rubric
(to tighten descriptions) and re-run, or adjust the calibration sample size
and re-run.

## Step 1b.5 — Inject hints into subsequent grader prompts

When Phase 2 spawns graders for the remaining papers, the grader prompt
construction in `grader-paper` must include any applicable calibration hints
for each criterion the grader is evaluating. The manifest's
`calibration_hints` block is the source of truth.

Graders do not know a hint is "calibration-derived" vs. "rubric-native" —
from their perspective, it's all just additional guidance on how to apply
the rubric. This preserves the blind re-dispatch rule: graders on iter 1 and
iter 5 see the same hints; no feedback leaked about prior grading.

## Post-conditions

- `session_dir/manifest.yaml` has `calibration_hints[]` populated (possibly
  empty if all criteria were well-calibrated)
- `session_dir/audit/calibration-report.yaml` exists
- `session_dir/results/<calibration-id>.yaml` exists for each calibration
  paper (their grades are final and included in the cohort)
- User has confirmed readiness to proceed with the full batch

Phase 2 then runs on the remaining (non-calibration) papers with hints
injected into grader prompts.
