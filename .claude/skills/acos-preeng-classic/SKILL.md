---
name: acos-preeng-classic
description: Secondary ACOS planning system — a faithful port of the external "preeng" pre-engineering pipeline. Runs a two-stage compiler (runner → deterministic worker) that generates the full pre-engineering artifact set (PRD spec, domain brief + competency questions, domain knowledge lattice, evidence ledger, implementation plan, technical PRD, data model, story/slice breakdown, per-task PM/Dev/QA instructions, cross-artifact analysis, CAGE decision trace) in one autonomous pass, then bridges the output into native ACOS slices. Use /acos-preeng-classic [product description] for complex or novel features before /acos-plan.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, WebSearch, WebFetch
---

# ACOS Pre-Engineering (Classic)

## Overview

`acos-preeng-classic` is a **secondary planning system** for ACOS — a faithful port
of the external `preeng` skill. It is an *alternative front-end* to `acos-plan`, not
a replacement. Where `acos-plan` does interactive elicitation + recursive
Vision→Epic→Story→Slice decomposition, this skill runs `preeng`'s **single-pass,
autonomous, artifact-generating** pipeline and then **bridges its output into the
native ACOS lifecycle**.

It implements `preeng`'s two-stage compiler:

```
product context ──▶ [RUNNER / compiler]  ──▶ deterministic_prompt + feature_config
                                                       │
                                                       ▼
                          [WORKER / deterministic interpreter]
                                                       │
                                                       ▼
              planning/preeng/<feature-id>/  (full artifact set)
                                                       │
                                                       ▼
                       BRIDGE ──▶ planning/slices/ skeletons ──▶ /acos-execute-slice
```

### Relationship to `acos-plan`

| | `acos-plan` (primary) | `acos-preeng-classic` (this, secondary) |
|---|---|---|
| Input | Interactive interview, many rounds | One product-context form, then autonomous |
| Output | Hierarchy of YAML (vision/epic/story/slice) | ~17 preeng artifacts in one pass |
| Grounding | Conversational, asks until satisfied | "Do not ask questions" — defaults marked `Assumption` |
| Best for | Iterative, evolving scope | Complex/novel domains, regulatory work, deep upfront research |

**When the two conflict, `acos-plan` is authoritative.** This skill's output is a
*proposal* that the bridge converts into normal ACOS slices for the usual
execute → review → learn lifecycle.

## Usage

```
/acos-preeng-classic [product description]     # Full pipeline from a description
/acos-preeng-classic --from-file <path>        # Use an existing product spec/brief as context
/acos-preeng-classic --resume <feature-id>     # Re-run/update an existing pre-eng feature
```

## When to use Pre-Eng (Classic)

✅ **Use for:** complex features with many unknowns · new product domains ·
features needing deep upfront research · multi-phase implementations ·
regulatory/compliance-heavy work · when you want a machine-readable knowledge
lattice + evidence ledger.

❌ **Skip for:** simple bug fixes · small additions · well-understood domains ·
quick iterations · maintenance. **Rule:** if the feature needs > 1 week of
implementation, use Pre-Eng; otherwise use `/acos-plan` directly.

---

## Protocol

### Pre-flight: Auto-Bootstrap

Ensure ACOS is initialized (idempotent — exits immediately if already set up):

```bash
bash .claude/scripts/acos-preflight.sh
```

### Step 0: Resolve mode + feature-id

Parse `$ARGUMENTS`:

- `--from-file <path>` → read that file as the primary product context.
- `--resume <feature-id>` → set `FEATURE_ID=<feature-id>`, mode = resume (artifacts
  may already exist under `planning/preeng/<feature-id>/`; the worker overwrites).
- otherwise → treat all of `$ARGUMENTS` as the product description.

Derive a slug and an incrementing feature id:

```bash
mkdir -p planning/preeng
# Next NNN- prefix (001, 002, ...) unless --resume gave one.
NEXT=$(printf '%03d' $(( $(ls -d planning/preeng/[0-9][0-9][0-9]-* 2>/dev/null | wc -l | tr -d ' ') + 1 )))
echo "feature index candidate: $NEXT"
```

The final `FEATURE_ID` is `<NNN>-<slug>` (e.g. `001-dev-task-manager`). Confirm it
with the user only if the description is too thin to slug; otherwise proceed.

### Step 1: Gather Input

If the product context is not already sufficient (from the description or
`--from-file`), present this form and wait for answers. **This is the only
interactive step** — everything after is autonomous.

```
PRODUCT CONTEXT NEEDED
======================
1. Product / Feature Name:
2. Business Objectives:
3. User Problems (ranked):
4. Success Metrics:
5. Constraints (technical / timeline / resource):
6. Dependencies (external systems, APIs, data sources):
7. Known Risks:
8. Optional: existing docs / research / related tickets / code examples
```

For thin descriptions, fill gaps yourself with conservative defaults — but each
default MUST be surfaced later in the runner's `open_questions` as an `Assumption`.

### Step 1.5: Optional ACOS grounding pre-seed (recommended, non-faithful add-on)

`preeng`'s worker is an *offline structurer* ("you cannot fetch external sources").
To keep that determinism while still benefiting from ACOS's memory and the live web,
optionally pre-seed the **product context** (not the worker) with retrieved facts:

```bash
# Internal priors (prior decisions, learnings, handoff gotchas):
bash .claude/scripts/rag-query.sh --query "<feature/domain>" --top-k 8
```

You MAY also run `WebSearch` / `WebFetch` for external domain facts. Fold anything
found into the product-context block under heading `## Pre-seeded research (T-tagged)`
with evidence tiers. This enriches the runner's input; the worker still runs
deterministically on the compiled prompt. Skip this step to stay byte-faithful to
classic preeng.

### Step 2: Run the Runner (compiler)

Spawn a **general-purpose** agent (model **opus** for normalization quality) whose
system prompt is the full contents of this skill's runner spec:

```bash
cat .claude/skills/acos-preeng-classic/prompts/runner.md
```

Pass it: (a) that runner spec, (b) the full contents of the worker spec
(`prompts/worker.md`) as the "Part One Command Spec" it must embed verbatim, and
(c) the product-context block from Step 1 (+ any Step 1.5 pre-seed).

The runner returns a single JSON object: `deterministic_prompt`, `feature_config`,
`command_inputs`, `execution_steps`, `open_questions`. Save it:

```bash
mkdir -p "planning/preeng/$FEATURE_ID"
# write the runner's JSON output to:
#   planning/preeng/$FEATURE_ID/_runner_config.json
```

Surface `open_questions` to the user as a short note (assumptions made) — but do
**not** block on them; preeng proceeds on conservative defaults by design.

### Step 3: Run the Worker (deterministic interpreter)

Spawn a **general-purpose** agent (model **opus**; `sonnet` is the budget option)
whose system prompt is the `deterministic_prompt` produced in Step 2 (which already
embeds `prompts/worker.md` Part One + the normalized config). Instruct it to:

1. Set its working feature dir to `planning/preeng/$FEATURE_ID/`.
2. Execute the six commands **in order**, honoring every precondition ERROR-gate:
   `/preeng.specify → /preeng.research → /preeng.plan → /preeng.tasks →
    /preeng.analyze → /preeng.instructions`.
3. Write every artifact to disk under the feature dir (it has `Write`), following
   the schemas in the worker spec exactly.

The worker writes the full artifact set (see README for the manifest). If it emits
`ERROR: ...`, stop the pipeline and report the failing precondition — do not fabricate
the missing prerequisite.

### Step 4: Verify artifact completeness

Mechanically confirm the expected artifacts exist and no QA report is REJECTED:

```bash
bash .claude/skills/acos-preeng-classic/scripts/verify-artifacts.sh "planning/preeng/$FEATURE_ID"
```

If `verify-artifacts.sh` is absent, inline-check: each of `spec.md research.md
domain-brief.md domain-cqs.md domain-lattice.json evidence-ledger.json plan.md
tech_prd.md data-model.md stories.json analysis-report.md cage_preeng_nodes.csv
cage_preeng_edges.csv` exists and is non-empty; `tasks/` has ≥1 file;
`agent_instructions/{pm,dev,qa}.md` exist; and grep each `*_qa_report.json` for
`"qa_status"` — if any is `REJECTED`, report it and stop.

### Step 5: Bridge to ACOS slices

This is the ACOS-native addition that wires preeng output INTO the lifecycle.
For each `planning/preeng/$FEATURE_ID/tasks/<slice-id>.md`, create a skeleton
ACOS slice using the canonical template:

```bash
cat .claude/skills/acos-plan/templates/slice.yaml   # the ACOS slice schema
```

Mapping (preeng task → ACOS slice.yaml):
- task PM "Objective / scope" → `objective` + `description`
- task PM "Guardrails / allowed files" → `files_allowed`
- task PM "Definition of Done" + QA "evidence gates" → `acceptance_criteria`
  (each criterion names its required artifact / pass-condition)
- task QA "verification steps" → `verification_method`
- derive `effort` (S/M/L) from task size; set `parent` to the originating
  story id from `stories.json`.

Write skeletons to `planning/slices/` (or `planning/slices/backlog/` if that
convention exists in this repo). Do **not** invent acceptance criteria the task
file doesn't support — leave a `# TODO: confirm` marker instead.

### Step 6: Report

Print a preeng-style completion summary:

```
PRE-ENGINEERING (CLASSIC) COMPLETE
==================================
Feature: <FEATURE_ID>
Artifacts: <N> files → planning/preeng/<FEATURE_ID>/

Metrics:
  - CQ coverage:        <X>%  (target ≥ 95%)
  - Evidence quality:   <Y>% T1–T3 sources
  - Lattice:            <nodes> nodes / <edges> edges
  - Slices generated:   <K> (skeletons in planning/slices/)

Assumptions made (from runner open_questions):
  - ...

Next steps:
  1. Review planning/preeng/<FEATURE_ID>/spec.md and plan.md
  2. Review the generated slice skeletons in planning/slices/
  3. Run /acos-execute-slice <SLICE-ID> to begin the ACOS execute→review→learn loop
```

Provide clickable file links to `spec.md`, `plan.md`, and the slices dir.

---

## Determinism contract (do not weaken)

The "classic" character of this skill lives in these rules, inherited verbatim from
the worker spec. Preserve them:

- The worker treats its spec as a **program, not a suggestion**.
- The worker does **not** ask the user questions; missing info → `Assumption` + proceed.
- The worker does **not** invent commands or change schemas.
- Phase preconditions are **hard ERROR-gates**: `/preeng.plan` errors if research QA
  is REJECTED; `/preeng.tasks` errors if planning QA is REJECTED.
- Coverage target for the domain lattice is **≥ 95% CQ coverage** (stricter than
  `acos-plan`'s 80% domain-brief gate — intentional).

---

*ACOS Pre-Engineering (Classic) — preeng's autonomous pipeline, bridged into the ACOS lifecycle.*
