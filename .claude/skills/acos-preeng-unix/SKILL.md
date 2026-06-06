---
name: acos-preeng-unix
description: Tertiary ACOS planning system — a component-decomposition pre-engineering pipeline inspired by the Unix philosophy. Instead of Vision→Epic→Story→Slice, it recursively decomposes a product vision into a variable-depth tree of independently human-testable, output-generating components (Product → Modules → Parts → Sub-parts → … as deep as each branch needs), where every node — leaf AND intermediate — produces an observable output a human can test in isolation. Runs a two-stage compiler (runner → deterministic worker) to emit a typed component tree, per-component contracts, pluggable per-component verifiers, a browsable self-contained Component Library (HTML), a bottom-up build/integration plan with an up→down→up repair protocol, and a coverage gate. Hands off to /acos-execute-component for bottom-up build → auto+human verify → compose-up → repair-down execution. Use /acos-preeng-unix [product description] for products best built as composable, individually testable, reusable parts. Domain-agnostic (software, designed documents, blueprints, hardware specs, data, media).
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, WebSearch, WebFetch
---

# ACOS Pre-Engineering (Unix)

## Overview

`acos-preeng-unix` is a **tertiary planning system** for ACOS. It sits beside `acos-plan`
(primary, interactive Vision→Epic→Story→Slice) and `acos-preeng-classic` (secondary, faithful
preeng port). Where those decompose work into *slices/tasks*, this skill decomposes a vision
into a **tree of independently human-testable, output-generating components**.

### The thesis (the Unix Invariant)

> **Every node in the plan — leaf AND intermediate — must be a component that produces an
> observable output a human can test in isolation, against its own acceptance criteria,
> before the rest of the product exists.**

There are no "mindless parts." Decompose top-down (*"what testable components, wired together,
fulfill this?"*), build bottom-up (leaves first → verify → compose upward → on failure drill
back down to the culprit children and re-climb). Because each component is a real functional
unit with a clean contract, it is **reusable** elsewhere.

```
vision ──▶ [RUNNER]──▶ deterministic_prompt
                          │
                          ▼
            [WORKER]  envision → decompose → contract → verify-spec → library → buildplan → coverage
                          │
                          ▼
   planning/preeng-unix/<id>/  (component-tree.json · library.html · build-plan.json · …)
                          │  verify-artifacts.sh  (completeness + coverage gate)
                          ▼
            /acos-execute-component   (bottom-up build → verify → compose → repair)
```

### When to use

✅ Products best expressed as **composable, individually testable, reusable parts** ·
hardware/physical systems · multi-artifact deliverables (a publication = cover + chapters +
figures, each testable) · anything where you want to **see each piece work before assembly** ·
when reuse of parts across the product (or future products) matters.

❌ Simple linear work, quick fixes, or scope that doesn't naturally factor into standalone
testable units → use `/acos-plan` (or `/acos-preeng-classic` for research-heavy single features).

**When skills conflict, `acos-plan` remains authoritative.** This skill's output is a proposal
realized by its own execution engine (`/acos-execute-component`).

## Usage

```
/acos-preeng-unix [product/vision description]   # full pipeline from a description
/acos-preeng-unix --from-file <path>             # use an existing vision/brief as context
/acos-preeng-unix --resume <feature-id>          # re-run / update an existing component tree
```

---

## Protocol

### Pre-flight: Auto-Bootstrap

Ensure ACOS is initialized (idempotent — exits immediately if already set up):

```bash
bash .claude/scripts/acos-preflight.sh
```

### Step 0: Resolve mode + feature-id

Parse arguments:
- `--from-file <path>` → read that file as the primary vision context.
- `--resume <feature-id>` → set `FEATURE_ID=<feature-id>`, mode = resume (the worker overwrites
  artifacts under `planning/preeng-unix/<feature-id>/`).
- otherwise → treat all arguments as the product/vision description.

Derive a slug and an incrementing feature id:

```bash
mkdir -p planning/preeng-unix
NEXT=$(printf '%03d' $(( $(ls -d planning/preeng-unix/[0-9][0-9][0-9]-* 2>/dev/null | wc -l | tr -d ' ') + 1 )))
echo "feature index candidate: $NEXT"
```

Final `FEATURE_ID` = `<NNN>-<slug>`. Confirm only if the description is too thin to slug.

### Step 1: Gather Input (the only interactive step)

If the vision context is not already sufficient, present this form and wait. Everything after
is autonomous.

```
PRODUCT VISION NEEDED
=====================
1. Product / Vision Name:
2. What is the finished thing, in one paragraph?
3. Domain (software / document / hardware / data / mixed / …):
4. Success signals (how YOU will know it's done & good — be concrete):
5. Constraints (technical / timeline / resource / physical):
6. Dependencies (external systems, materials, data, APIs):
7. Known risks:
8. Optional: existing docs / references / a part you already know you need
```

For thin descriptions, fill gaps with conservative defaults — each surfaced later as an
`Assumption` in the runner's `open_questions`.

### Step 1.5: Optional ACOS grounding pre-seed (recommended, non-faithful add-on)

Pre-seed the **vision context** (not the worker) with retrieved facts so the worker stays a
deterministic offline structurer:

```bash
bash .claude/scripts/rag-query.sh --query "<product/domain>" --top-k 8
```

You MAY also run `WebSearch` / `WebFetch` for domain facts. Fold findings into the vision
context under `## Pre-seeded research (T-tagged)` with evidence tiers. Skip to stay lean.

**Reuse pre-seed (recommended).** Surface already-proven, reusable components from prior trees so
the worker can plan to **reuse rather than reinvent** (the cross-tree half of §0.5):

```bash
python3 .claude/skills/acos-preeng-unix/scripts/registry.py search --json   # or --tags "<domain capabilities>"
```

Fold any relevant hits into the vision context under `## Available reusable components (registry)`
listing each `registry_id`, name, capability tags, verifier type, and source. Instruct the worker
(via `command_inputs.decompose.reuse_candidates`) that when a needed leaf matches one of these, it
should name the `registry_id` in that node's `reuse.known_consumers` / notes so the execution engine
reuses it (`registry.py link`) instead of building. The registry lives at
`planning/preeng-unix/_registry/registry.json` and starts empty on a fresh project.

### Step 2: Run the Runner (compiler)

Spawn a **general-purpose** agent (model **opus**) whose system prompt is this skill's runner
spec:

```bash
cat .claude/skills/acos-preeng-unix/prompts/runner.md
```

Pass it: (a) the runner spec, (b) the full worker spec (`prompts/worker.md`) as the "Part One
Command Spec" to embed **verbatim**, (c) the vision context from Step 1 (+ any Step 1.5
pre-seed), (d) the `FEATURE_ID`.

The runner returns one JSON object: `deterministic_prompt`, `feature_config`, `command_inputs`,
`execution_steps`, `open_questions`. Save it:

```bash
mkdir -p "planning/preeng-unix/$FEATURE_ID"
# write the runner JSON to: planning/preeng-unix/$FEATURE_ID/_runner_config.json
```

Surface `open_questions` (assumptions made) as a short note — do not block on them.

### Step 3: Run the Worker (deterministic interpreter)

Spawn a **general-purpose** agent (model **opus**; `sonnet` = budget) whose system prompt is the
`deterministic_prompt` from Step 2. Instruct it to:

1. Set its feature dir to `planning/preeng-unix/$FEATURE_ID/`.
2. Execute the seven commands in order, honoring every precondition ERROR-gate and the **Unix
   Invariant**:
   `/unix.envision → /unix.decompose → /unix.contract → /unix.verify-spec → /unix.library →
    /unix.buildplan → /unix.coverage`.
3. Write every artifact to disk per the worker schemas.

If it emits `ERROR: ...` (e.g. `untestable or overloaded node <id>`), stop and report the
failing precondition — do not fabricate the missing prerequisite.

### Step 3.5: Render / refresh the Component Library

Deterministically (re)render `library.html` from the tree + status:

```bash
python3 .claude/skills/acos-preeng-unix/scripts/render-library.py "planning/preeng-unix/$FEATURE_ID"
```

(The worker writes valid `component-tree.json` + `library-status.json`; this script produces the
self-contained browsable HTML. The execution engine re-runs it after every status change.)

### Step 4: Verify artifact completeness + coverage

```bash
bash .claude/skills/acos-preeng-unix/scripts/verify-artifacts.sh "planning/preeng-unix/$FEATURE_ID"
```

Exit 2 (missing artifact, malformed/untestable tree, or REJECTED coverage QA) **blocks** the
handoff to execution. Fix and re-run before proceeding.

### Step 5: Hand off to the execution engine

Unlike `acos-preeng-classic` (which bridges to `planning/slices/`), this skill uses its **own**
execution model. Once Step 4 passes, the plan is ready for:

```
/acos-execute-component planning/preeng-unix/<FEATURE_ID>
```

which walks the build plan bottom-up: build each leaf → auto + human verify → register status in
the Component Library → compose verified children into their parent → verify the parent → on
failure drill down to the likely-culprit children, upgrade, and re-climb — until the root Product
passes its whole-product verifier against the vision.

> Optional interop: if you also want ACOS reviewer coverage on a software component, you may
> additionally generate a thin `planning/slices/` skeleton for that one component and run it
> through `/acos-execute-slice`. The native path is `/acos-execute-component`.

### Step 6: Report

```
PRE-ENGINEERING (UNIX) COMPLETE
===============================
Feature: <FEATURE_ID>
Artifacts: <N> files → planning/preeng-unix/<FEATURE_ID>/

Component tree:
  - Components:        <total>  (<leaves> leaves / <intermediate> intermediate)
  - Max depth:         <D>      (variable per branch)
  - Reusable units:    <R>      (tagged for reuse)
  - Coverage:          <X>%     of vision success criteria (target 100%)
  - Build order:       <K> steps (leaves-first)

Assumptions made (from runner open_questions):
  - ...

Next steps:
  1. Open the Component Library:  planning/preeng-unix/<FEATURE_ID>/library.html
  2. Skim component-tree.json + build-plan.json
  3. Run /acos-execute-component planning/preeng-unix/<FEATURE_ID> to build bottom-up
```

Provide clickable file links to `library.html`, `component-tree.json`, `build-plan.json`, and the
feature dir.

---

## Determinism contract (do not weaken)

- The worker treats its spec as a **program, not a suggestion**; it never asks questions.
- Missing info → `Assumption` + proceed.
- The worker does **not** invent commands or change schemas.
- The **Unix Invariant** is hard: every node must be independently human-testable with an
  observable output; an untestable/overloaded node is an `ERROR`, not a warning.
- Coverage gate target is **100% of vision success criteria** (a REJECTED coverage QA blocks
  execution).
- Decomposition prefers **shared/reused components** over duplicates.

---

*ACOS Pre-Engineering (Unix) — decompose into testable components, build bottom-up, compose to the vision.*
