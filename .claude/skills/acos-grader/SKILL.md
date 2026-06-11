---
name: acos-grader
description: |
  Multi-agent exam / case submission / assignment grader with adversarial QA and
  dual-axis consensus. Three finance-expert graders (2 Opus + 1 Sonnet) independently
  grade each paper; an Opus QA agent enforces per-criterion consensus on both points
  (±5% relative spread) and reasoning (≥90% LLM-judge similarity). Failed criteria
  re-dispatch blind — graders get zero feedback about why consensus failed. Wigum
  loops per paper up to 5 iterations, then flags disputed criteria. Produces a single
  XLSX workbook with per-paper 3-column grade sheets, z-score-curved cohort grades,
  and full audit trail.

  Subject specialization: CFA, FRM, PE-RE, Corporate Finance, Accounting,
  Investment Management, General. Rubric input: DOCX / PDF / XLSX (parsed via
  acos-pdf-xlsx-converter + acos-data-extractor). Script input: PDF / DOCX / scans
  / images — embedded images inside typed DOCX and PDF submissions are read via
  Claude vision (hand-drawn waterfalls, DCFs, chart screenshots, equation images),
  with tesseract as fallback. Range input: floor–ceiling → per-criterion
  floor/ceiling pro-rata.

  Invocation: wizard by default, CLI args override individual prompts.
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Task(grader-paper), Task(grader-calibrator), Task(grader-rubric-parser), Task(grader-vision-ocr), Task(general-purpose)
---

# ACOS Grader

Multi-agent, finance-expert grading swarm with adversarial consensus gating
and z-score-curved output.

## Architecture

```
                       ┌─────────────────────────┐
                       │    SKILL.MD (Phase 0)   │
                       │  Wizard / CLI dispatch  │
                       └────────────┬────────────┘
                                    │
            ┌───────────────────────┼───────────────────────┐
            │                       │                       │
            ▼                       ▼                       ▼
   ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
   │ Phase 1 Ingest  │     │ Phase 2 Grade   │     │ Phase 3 Aggregate│
   │ (main conv)     │     │ (per-paper)     │     │ (main conv)      │
   │                 │     │                 │     │                  │
   │ • Parse rubric  │     │ Windowed pool:  │     │ • Collect papers │
   │ • OCR scripts   │     │ N papers at a   │     │ • Z-score curve  │
   │ • Derive ranges │     │ time, each in   │     │ • Build XLSX     │
   │ • Build manifest│     │ grader-paper    │     │ • Cohort stats   │
   └─────────────────┘     │ orchestrator    │     └──────────────────┘
                           └─────────┬────────┘
                                     │ Task(grader-paper)
                                     ▼
                          ┌───────────────────────┐
                          │   grader-paper AGENT  │
                          │   (Opus, per paper)   │
                          │   Owns Wigum loop:    │
                          │                       │
                          │   FOR iter in 1..5:   │
                          │     → 3 graders       │
                          │     → 1 QA            │
                          │     → re-dispatch     │
                          │       failing crit    │
                          │       blind           │
                          │   → synthesize        │
                          │   → write artifact    │
                          └───┬──────┬──────┬─────┘
                              │      │      │
           Task(grader-opus)  │      │      │ Task(grader-synth)
           Task(grader-sonnet)│      │
                              ▼      ▼      ▼
                        ┌────────┐┌────┐┌─────────┐
                        │GRADERS ││ QA ││ SYNTHESIZER│
                        │2 Opus  ││Opus││ Opus       │
                        │1 Sonnet││    ││ (per crit) │
                        └────────┘└────┘└─────────────┘
```

## Design Principles

1. **Blind organic convergence.** Re-dispatched graders see zero feedback about
   why prior rounds failed consensus. If three independent experts keep arriving
   at similar numbers, that is the signal. Feedback would leak anchoring.

2. **Cognitive diversity by model class.** 2 Opus + 1 Sonnet breaks correlated
   systematic biases that three instances of the same model would share. Haiku is
   deliberately excluded from the default mix — finance grading demands chained
   reasoning that Haiku truncates.

3. **Dual-axis consensus.** A criterion is locked only when BOTH the numerical
   spread (±5% relative) AND the reasoning similarity (≥90% LLM-judge) pass.
   Points-agreement without reasoning-agreement is suspicious; the reverse is
   uninformative.

4. **Pre-normalization via prompt-injection.** The user supplies a total grade
   range (e.g., 70–90). The skill derives per-criterion floors/ceilings pro-rata
   by criterion weight and injects those bounds into every grader's prompt, so
   out-of-range scores never arise in the first place.

5. **Paper-level orchestrator, per-criterion re-dispatch.** The QA agent reads
   all three grading sheets holistically (paper-level context) but issues
   per-criterion verdicts. Re-dispatch targets only the failing criteria, not
   the whole paper.

6. **Anonymization by filename convention.** Paper IDs are extracted from
   filenames. The skill does NOT redact names within paper text — that is the
   user's responsibility upstream. No name↔ID mapping table is maintained.

---

## Phase 0: Invocation

The skill supports two invocation modes: **wizard** (default, interactive) and
**CLI args** (non-interactive, scripted). When both are mixed, CLI args override
individual wizard prompts.

### CLI arguments

```bash
/acos-grader \
  --rubric <path-to-rubric.{docx,pdf,xlsx}> \
  --scripts <path-to-folder-of-papers> \
  --range <floor-ceiling>                  # e.g., 70-90
  --subject <CFA|FRM|PE-RE|Corporate Finance|Accounting|Investment Management|General> \
  --questions-file <path>                  # OPTIONAL: the questions / requirements /
                                           # instructions given to the student
                                           # (DOCX/PDF/XLSX/TXT). Injected into every
                                           # grader prompt so graders can verify the
                                           # student is actually answering what was asked.
  --batch-window <N>                       # default 5, windowed parallel papers
  --max-iters <N>                          # default 5, per-criterion Wigum ceiling
  --calibrate <N>                          # optional: grade first N papers, then analyze
                                           # divergence and inject hints before the rest
  --output <path-to-output.xlsx>           # default: ./grader-output-<timestamp>.xlsx
  --per-student-dir <path>                 # OPTIONAL: directory for per-student XLSX
                                           # files, one per paper (e.g., to hand back to
                                           # each student individually). If unset,
                                           # defaults to '<output-parent>/per-student/'.
                                           # Pass 'NONE' to disable per-student output.
```

Any missing arg is prompted via the wizard.

### Wizard flow

Ask questions sequentially in the primary conversation. Collect:

1. **Rubric path** — DOCX, PDF, or XLSX file with criteria + points + description
2. **Scripts folder** — directory containing papers to grade (PDF/DOCX/scans)
3. **Grade range** — floor and ceiling for final grades (e.g., `70-90`)
4. **Subject subtype** — one of the seven specializations
5. **Questions / Requirements file** (optional) — path to a document containing
   the questions, case requirements, or assignment instructions given to the
   student. DOCX / PDF / XLSX / TXT. If provided, it's injected into every
   grader prompt so graders can verify answers against the actual task.
   Skip if the rubric already embeds the questions (common for compact rubrics).
6. **Batch window** (optional) — default 5
7. **Max iterations per criterion** (optional) — default 5
8. **Output path** (optional) — default `./grader-output-<timestamp>.xlsx`

Confirm all inputs before proceeding to Phase 1.

**Terminology note.** Different use cases call this input by different names:
exam → "questions"; assignment → "requirements" or "instructions"; case
submission → "prompt" or "case". The `--questions-file` flag covers all
three — the skill doesn't distinguish internally.

### Preflight checks

- Rubric file exists and has a supported extension
- Scripts folder exists and contains ≥ 1 supported file
- Grade range is two integers, floor < ceiling, both ≤ total points in rubric
- Output path is writable (parent directory exists)
- If `--questions-file` is provided: file exists, supported extension, and
  `grader-ingest-paper.py` can produce non-empty text from it

On any failure, abort with a clear error — do NOT spawn any agents.

---

## Phase 1: Ingest

Main conversation runs Phase 1. Full instructions in
`phases/phase1-ingest.md`. Summary:

1. **Parse rubric** via `.claude/scripts/grader-parse-rubric.py`, which
   dispatches to `acos-pdf-xlsx-converter` (XLSX/PDF) or `acos-data-extractor`
   (DOCX) depending on extension. Output: internal YAML matching
   `templates/rubric-schema.yaml`.

2. **OCR scripts + embedded-image extraction** — for any script file that is a
   scan or handwritten image, run OCR via Claude vision (model: `claude-sonnet-4-6`)
   with tesseract as fallback. For typed DOCX / PDF, the text layer is used AND
   every embedded image (charts, hand-drawn diagrams, equation screenshots,
   spreadsheet captures) is also passed through Claude vision so the grader sees
   what the student drew — not just what they typed. Vision uses
   `ANTHROPIC_AUTH_TOKEN` (Claude subscription) OR `ANTHROPIC_API_KEY`, with a
   Task()-based `grader-vision-ocr` fallback and tesseract as the final fallback
   — no API key is strictly required. Output: text files in
   `.acos/state/grader-sessions/<session-id>/papers/`.

3. **Derive per-criterion ranges** — for each rubric criterion, compute:
   ```
   criterion_floor   = (total_floor   / total_points) × criterion_points
   criterion_ceiling = (total_ceiling / total_points) × criterion_points
   ```
   Round to 0.5-point increments.

4. **Build session manifest** at
   `.acos/state/grader-sessions/<session-id>/manifest.yaml` using the
   `templates/session-manifest.yaml` template. This is the single source of
   truth that all downstream agents read.

---

## Phase 1b: Calibration (optional)

Runs only when `--calibrate N` is set. Full instructions in
`phases/phase1b-calibrate.md`. Summary:

1. Select the first N papers as a calibration sample
2. Grade them via the normal Phase 2 pipeline (they are final — their grades
   stand)
3. Spawn the `grader-calibrator` agent to analyze per-criterion divergence
4. Calibrator writes hints into `manifest.calibration_hints[]` for divergent
   criteria
5. Surface a summary to the user, confirm before proceeding with the
   remaining batch
6. Phase 2 then dispatches remaining papers with calibration hints injected
   into grader prompts

Calibration is purely additive — it never weakens the blind-re-dispatch rule
or changes the rubric.

---

## Phase 2: Grade

Main conversation dispatches one `grader-paper` orchestrator per paper, in
**windowed parallel**: up to N papers in flight simultaneously (default N=5).
As each orchestrator completes, a new one is spawned until the pool is drained.

### Dispatch pattern (batch-wait, no polling)

Claude Code does NOT expose a `task_done()` primitive; background Task() calls
deliver completion via a notification in the next tool-result cycle. Use the
batch-wait pattern — spawn a window of orchestrators in ONE message, wait for
all to complete via notifications, then spawn the next window:

```
manifest = load_manifest(session_id)
eligible = [p for p in manifest.papers if p.status == "ingested"]
              # CRITICAL: skip papers with status ocr_failed / ingest_error /
              # skipped. Dispatching graders on empty/missing text produces
              # fake floor-scored grades indistinguishable from real ones.

skipped = [p for p in manifest.papers if p.status != "ingested"]
for p in skipped:
    write_ungraded_artifact(p)     # cohort summary will show them as UNGRADED

# Process eligible papers in windows
for window in chunked(eligible, manifest.batch_window):
    # Single message spawns N orchestrators with run_in_background=True
    spawn_window(window)
    # Main conversation waits — notifications arrive as each orchestrator
    # completes. Collect ALL notifications before spawning the next window.
    wait_for_all_in_window(window)
```

Concretely, `spawn_window()` is a single message containing N Task() calls
(one per paper, all `run_in_background=True`). `wait_for_all_in_window()` is
the natural flow of receiving N completion notifications from the runtime.

**Non-ingested papers must not be spawned.** Graders will silently award
floor scores for empty text, which is indistinguishable in the output from
a legitimate low-scoring submission.

Each `grader-paper` writes its result to
`.acos/state/grader-sessions/<session-id>/results/<paper-id>.yaml` before
returning. Main conversation does not parse grader-paper output directly —
it reads the artifact files after each window completes.

Full per-paper loop instructions in `phases/phase2-paper-orchestrator.md`.
Individual agent instructions in `phases/phase3-grader.md`,
`phases/phase4-qa.md`, `phases/phase5-synth.md`.

---

## Phase 3: Aggregate

After all per-paper artifacts are written, main conversation runs Phase 3. Full
instructions in `phases/phase6-aggregate.md`. Summary:

1. **Load all per-paper artifacts** from results directory
2. **Compute cohort stats** — raw mean, median, min, max, stdev, distribution
3. **Apply z-score curve** with:
   - `target_mean = (total_floor + total_ceiling) / 2`
   - `target_stdev = (total_ceiling - total_floor) / 4`
4. **Build XLSX workbooks** via `.claude/scripts/grader-cohort-curve.py`:
   - **Cohort workbook** (`--output`):
     - Cohort summary sheet: raw + curved grades, mean, min, max, stdev, distribution
     - One sheet per paper: 3-column grade sheet, raw total, curved grade, disputed flags
     - Audit log sheet: per-criterion iteration history for every paper
   - **Per-student workbooks** (one file per paper, written to `--per-student-dir`
     or defaulting to `<cohort-xlsx-parent>/per-student/`):
     - Single-sheet report suitable for handback to the student: header block
       (raw total, curved grade, iterations used), per-criterion table with
       merged reasoning, and a mini audit trail showing each grader's points
       and the QA verdict for every criterion.
     - Pass `--per-student-dir NONE` to disable this output entirely.
5. **Deliver** both the cohort XLSX and (unless disabled) the per-student
   directory; emit clickable links to each.

---

## Session State Layout

```
.acos/state/grader-sessions/<session-id>/
  manifest.yaml                        # Session source of truth
  rubric.yaml                          # Parsed rubric (internal format)
  papers/                              # OCR'd text per paper
    <paper-id-1>.txt
    <paper-id-2>.txt
    ...
  grading/                             # Per-iteration grading sheets
    <paper-id>/
      iter-1-grader-opus-A.yaml
      iter-1-grader-opus-B.yaml
      iter-1-grader-sonnet.yaml
      iter-1-qa-verdict.yaml
      iter-2-grader-opus-A.yaml
      ...
  synthesis/                           # Post-convergence merged reasonings
    <paper-id>.yaml
  results/                             # Final per-paper artifacts
    <paper-id>.yaml
  audit/                               # Full iteration history
    <paper-id>-audit.yaml
```

All session data is git-ignored via `.acos/` convention.

---

## Defaults and configuration

| Setting | Default | Override |
|---|---|---|
| Model mix | 2 Opus + 1 Sonnet | `.acos/config/model-profile.yaml` |
| QA model | Opus | `grader-qa` agent in model-profile.yaml |
| Synthesizer model | Opus | `grader-synth` agent in model-profile.yaml |
| Numerical consensus | ±5% relative spread | CLI `--consensus-pct` |
| Near-zero guardrail | Absolute ±0.5 tolerance floor, ALWAYS applied (PASS if relative ≤5% OR absolute ≤0.5) | Hardcoded |
| Reasoning similarity | ≥90% LLM-judge | CLI `--similarity-pct` |
| Max iterations / criterion | 5 | CLI `--max-iters` |
| Batch window | 5 papers in flight | CLI `--batch-window` |
| Curve method | Z-score rescale | Hardcoded (future: CLI flag) |
| Target mean | `(floor + ceiling) / 2` | Hardcoded |
| Target stdev | `(ceiling - floor) / 4` | Hardcoded |

---

## Error handling

- **Rubric parse failure** → abort Phase 1, report the specific file + parser error
- **Paper OCR failure** → skip the paper, log to session audit, continue the batch
- **Grader agent crash** → retry once in-place; if still failing, mark paper
  INCONCLUSIVE and skip
- **QA agent crash** → retry once; if still failing, abort the paper with all
  grader output preserved
- **Hit max iterations on a criterion** → flag DISPUTED, use best-available
  average, capture all iteration history in audit log
- **Hit max iterations on ALL criteria of a paper** → paper graded with all-
  disputed flags, still included in cohort summary but marked prominently

---

## Invocation examples

### Full wizard
```
/acos-grader
```

### Fully specified
```
/acos-grader \
  --rubric ~/exams/fall-2026-portfolio-theory/rubric.docx \
  --scripts ~/exams/fall-2026-portfolio-theory/submissions/ \
  --range 70-90 \
  --subject "Investment Management" \
  --batch-window 5 \
  --output ~/exams/fall-2026-portfolio-theory/grades.xlsx
```

### Wizard with partial CLI
```
/acos-grader --subject CFA --range 65-95
# Prompts for rubric, scripts, output; uses CFA + 65-95 without asking
```

---

*ACOS Grader — finance-expert grading swarm with adversarial consensus.*
