# Phase 6 — Aggregate + Curve + XLSX Build

Run in the primary conversation after all `grader-paper` orchestrators have
returned. No agent spawning. This phase collects per-paper artifacts, applies
the z-score curve, and produces the final deliverable.

## Inputs

- Session manifest at `${SESSION_DIR}/manifest.yaml`
- Per-paper result artifacts in `${SESSION_DIR}/results/*.yaml`
- Audit logs in `${SESSION_DIR}/audit/*.yaml`

## Step 6.1 — Collect results

```bash
find "${SESSION_DIR}/results" -name "*.yaml" | sort
```

Verify that every paper in the manifest has a corresponding result file. If
any are missing (e.g., paper orchestrator crashed and did not write an
artifact), log the gap and include it in the cohort summary as `UNGRADED`.

## Step 6.2 — Compute raw cohort stats

For each paper, compute raw total:
```python
raw_total = sum(criterion.points_awarded for criterion in paper.criteria)
```

Compute cohort-level:
- `n_papers`
- `n_graded` (paper has raw_total)
- `n_ungraded` (missing artifact)
- `n_disputed_criteria` total
- `raw_mean`, `raw_median`, `raw_min`, `raw_max`, `raw_stdev`
- Raw distribution by 5-point buckets

## Step 6.3 — Apply z-score curve

```python
target_mean   = (total_floor + total_ceiling) / 2
target_stdev  = (total_ceiling - total_floor) / 4

for paper in graded_papers:
    z = (paper.raw_total - raw_mean) / raw_stdev  if raw_stdev > 0 else 0
    paper.curved = target_mean + z * target_stdev
    paper.curved = clamp(paper.curved, total_floor, total_ceiling)
```

If `raw_stdev == 0` (all papers tied — vanishingly unlikely), set every
curved grade to `target_mean`.

Compute post-curve stats: `curved_mean`, `curved_median`, `curved_stdev`,
`curved_distribution`.

## Step 6.4 — Build the XLSX

Dispatch to the cohort curve + build script:

```bash
python3 .claude/scripts/grader-cohort-curve.py \
  --session-dir "${SESSION_DIR}" \
  --output "${output_path}" \
  [--per-student-dir "${per_student_dir}"]   # optional; defaults to
                                             # '<output_path>/../per-student/'
```

The script writes two deliverables:

1. **Cohort workbook** (`--output`) — multi-sheet XLSX described below.
2. **Per-student workbooks** — one XLSX per paper, written to `--per-student-dir`
   (defaults to a `per-student/` subdirectory next to the cohort XLSX). Each
   file contains a single `Grade Report` sheet: header block with raw total,
   curved grade, iterations used, and disputed count; per-criterion table with
   merged reasoning and CONVERGED/DISPUTED status; and a mini audit trail
   showing each grader's points and the QA verdict for every criterion. Pass
   `--per-student-dir NONE` to disable per-student output entirely.

See `.claude/scripts/grader-cohort-curve.py` for full formatting logic.

## XLSX structure

### Sheet 1..N: Per-paper grade sheets (one per paper)

Sheet name: `<paper_id>` (truncated to 31 chars, XLSX limit)

Columns:
| A | B | C | D | E |
|---|---|---|---|---|
| Criterion | Points Awarded | Points Total | Reasoning | Status |

Row structure:
- Header row 1: paper_id, raw total, curved grade
- Header row 2: DISPUTED flags summary (if any)
- Blank row
- Column headers
- One row per criterion with the merged reasoning
- Footer: "Raw total: X / Y" and "Curved grade: Z" (formatted)

Status column values:
- `CONVERGED` — all graders agreed within consensus rules
- `DISPUTED (max_iters)` — hit the 5-iteration ceiling, best-available used
- `UNGRADED` — orchestrator failed, no grade produced

Disputed rows get yellow cell shading; ungraded rows get red.

### Cohort Summary sheet

Columns:
| A | B | C | D |
|---|---|---|---|
| Paper ID | Raw Total | Curved Grade | Disputed Count |

Footer block:
- n_papers, n_graded, n_ungraded, n_disputed_criteria total
- Raw stats: mean, median, min, max, stdev
- Curved stats: mean, median, stdev
- Grade distribution table (5-point buckets: <70, 70–74, 75–79, 80–84, 85–89, 90–94, 95+)

### Audit Log sheet

Columns:
| A | B | C | D | E | F | G |
|---|---|---|---|---|---|---|
| Paper ID | Criterion | Iteration | Grader A Points | Grader B Points | Grader C Points | QA Verdict |

One row per criterion per iteration per paper. This sheet can be large on big
batches — 40 papers × 8 criteria × avg 2.3 iterations = ~735 rows.

## Step 6.5 — Deliver

Emit a clickable link to the output XLSX:

```
Grading complete. Output: [grades.xlsx](file:///Users/zee/exams/fall-2026/grades.xlsx)

Summary:
- 47 papers graded, 0 ungraded
- 3 disputed criteria across 2 papers (flagged in output)
- Raw mean: 78.2, stdev 6.4
- Curved mean: 80.0, stdev 5.0 (target: mean 80, stdev 5)
```

## Cleanup

Leave the session directory intact. Do NOT delete grading artifacts — they are
the audit trail. Session directories are git-ignored via `.acos/` convention,
so they do not pollute the repo.

If the user wants to reclaim disk space later, they can delete
`.acos/state/grader-sessions/` manually or archive individual sessions.
