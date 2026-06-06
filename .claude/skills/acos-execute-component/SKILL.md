---
name: acos-execute-component
description: Bottom-up execution engine for acos-preeng-unix component trees. Walks the build plan leaves-first — builds each component's observable output, verifies it (pluggable auto-check + human test) in isolation, registers pass/fail in the browsable Component Library, then composes verified children into their parent (itself a testable component) and verifies the parent. On an integration failure it drills DOWN to the likely-culprit children, upgrades them, and re-climbs (the up→down→up repair loop) until the root Product passes its whole-product verifier against the vision. Spawns Builder / Verifier / Integrator general-purpose agents (no new restricted agent files). Use /acos-execute-component planning/preeng-unix/<feature-id> after the planning engine's coverage gate passes.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# ACOS Execute Component (Bottom-Up Runtime)

## Overview

This is the **execution half** of `acos-preeng-unix`. The planning engine produced a tree of
independently testable components, their contracts, pluggable verifiers, a Component Library, and
a bottom-up build plan. This skill **builds it for real**, in the order the rocket gets built:
smallest testable parts first, each proven on its own, then assembled and re-proven at every level.

```
build-plan.json (leaves first)
   │
   ├─ for each LEAF in order:   Builder → produces output artifact
   │                            Verifier → auto-check + human test  ─ fail ▶ Builder reworks (≤max_iter)
   │                            └ pass ▶ status=passed, evidence logged, library refreshed
   │
   └─ when all children of a PARENT pass:
        Integrator → compose children into the parent via contracts
        Verifier   → test the parent (itself a component)
          ├ pass ▶ climb to the next parent
          └ fail ▶ DRILL DOWN: rank children by likelihood of causing the failure,
                   mark suspects failed, rebuild/upgrade, re-verify, re-compose, climb again
   │
   ▼  until the root Product passes its whole-product verifier against the vision.
```

The three roles map onto ACOS's adversarial trust model: **Builder ≈ developer**,
**Verifier ≈ qa-reviewer (zero-trust)**, **Integrator ≈ architect (composition + repair)**.
All three are spawned as **general-purpose** agents carrying embedded prompts from this skill's
`prompts/` dir — no files are added to the human-approval-restricted `.claude/agents/`.

## Usage

```
/acos-execute-component <feature-dir>                 # run the full bottom-up build
/acos-execute-component <feature-dir> --component <C> # build/verify a single component (+ deps)
/acos-execute-component <feature-dir> --status        # print the tree status, render library, stop
/acos-execute-component <feature-dir> --max-iter <N>  # override per-component rework cap (default 5)
```

`<feature-dir>` = `planning/preeng-unix/<feature-id>`.

---

## Protocol

### Step 0: Preconditions

```bash
bash .claude/scripts/acos-preflight.sh
bash .claude/skills/acos-preeng-unix/scripts/verify-artifacts.sh "<feature-dir>"
```

If `verify-artifacts.sh` exits non-zero (missing artifacts, untestable tree, or REJECTED
coverage QA), **stop** — the tree is not ready to build. Send the user back to
`/acos-preeng-unix`.

**Scope-hook guard (B1).** Component execution runs OUTSIDE the slice lifecycle — there is no
active slice. `check-scope.sh` / `check-scope-bash.sh` both **fail open when
`.acos/config/active-slice.yaml` is absent** (and always allow `.acos/evidence/`, `.acos/state/`,
`memory/`), so Builder/Integrator writes under `<feature-dir>/build/` and `<feature-dir>/evidence/`
are unblocked. BUT a **stale** `active-slice.yaml` from a prior `/acos-execute-slice` would scope-gate
those writes to that slice's `files_allowed` and break the build. So check first:

```bash
test -f .acos/config/active-slice.yaml && echo "WARN: an active slice exists — it will scope-block component builds. Run /acos-complete (or finish that slice) before executing components." || echo "OK: no active slice; component writes unrestricted."
```

If an active slice exists, stop and tell the user to clear it (do not silently delete it — it's
another workflow's state). The Oracle (PreToolUse) still scores Bash/Write/Task but file writes and
test runs score low; at the default threshold (9) they auto-approve.

**Model resolution (B2).** Resolve each role's model through the Model Profile System instead of
hardcoding, mapping the three execution roles onto the closest profiled ACOS agents:

```bash
BUILDER_MODEL=$(bash .claude/scripts/resolve-agent-model.sh developer)      # Builder  ≈ developer
VERIFIER_MODEL=$(bash .claude/scripts/resolve-agent-model.sh qa-reviewer)   # Verifier ≈ qa-reviewer
INTEGRATOR_MODEL=$(bash .claude/scripts/resolve-agent-model.sh architect)   # Integrator ≈ architect
```

Spawn each agent with its resolved model (a bare name → Claude `Task()`; a `provider:model` →
external runner per the Model Profile System). If resolution yields an external model for the
Builder/Integrator, prefer the Claude fallback — these roles need tool access to write artifacts.

Read `component-tree.json`, `integration-map.json`, `build-plan.json`. The build plan's `order`
is authoritative; `repair_protocol` governs failure handling. See `STATE-MACHINE.md` for the
formal status transitions and invariants (B4), and `## Evidence convention` below (B3).

### Step 1: Initialize status + render

Ensure `library-status.json` exists with every component id set to its current status (`planned`
for a fresh run; statuses are preserved on disk, so resume is automatic). Render the library once
so the user has a live view:

```bash
python3 .claude/skills/acos-preeng-unix/scripts/render-library.py "<feature-dir>"
```

**The runtime is driven by two deterministic helpers — never hand-edit the JSON:**
- `scripts/next-ready.py <feature-dir>` → the build frontier: which components are buildable now
  (leaf, or parent whose children all `passed`), each flagged `needs_human` when its auto-check
  can't run; plus `building`, `blocked` (waiting on a child), and `done` (root passed).
- `scripts/set-status.py <feature-dir> <id> <status> [--evidence … | --note … | --source human|agent --observed …]`
  → the ONLY writer of status. It mirrors `component-tree.json` ↔ `library-status.json`, writes the
  evidence note, **enforces the parent-gating invariant** (refuses to set a parent `passed` while a
  child isn't — exit 3), and re-renders the library.

### Step 2: The build loop (next-ready → dispatch → set-status, repeat)

Loop until `next-ready.py` reports `done: true`:

```bash
python3 .claude/skills/acos-execute-component/scripts/next-ready.py "<feature-dir>"
```

Take the next `ready` component (they are already in build order). Branch on `is_leaf` and, for
verification, on `needs_human`. After every build/verify, record the outcome with `set-status.py`
(which re-renders the library automatically). Then re-run `next-ready.py`. Because all state lives
on disk, an interrupted run resumes exactly where it stopped — just re-invoke the skill.

> Independent `ready` leaves may be built **concurrently** (spawn their Builders in parallel); a
> parent only appears in `ready` once `next-ready.py` confirms all its children `passed`, so the
> bottom-up ordering is enforced by the helper, not by you tracking it.

For each component, branch on whether it is a **leaf** (`is_leaf: true`) or an
**intermediate/root**.

#### 2a. Leaf — build then verify
1. `set-status.py <feature-dir> <id> building` (this refreshes the library).
2. **Spawn a Builder** (general-purpose, `$BUILDER_MODEL` from Step 0) with `prompts/builder.md` + the component's
   `components/<id>.md` spec + its `contract`. Scope is **only** this component's output
   artifact. It writes the artifact to `output_artifact.location_hint` (or a sensible default
   under the feature dir) and an evidence note.
3. **Verify — branch on `needs_human` from `next-ready.py`:**
   - **`needs_human: false`** (auto-check runnable, or an artifact an agent can inspect — e.g.
     `software-test`, `document-render`, `data-schema`, `visual-diff`): **spawn a fresh Verifier**
     (general-purpose, `$VERIFIER_MODEL` — does NOT see the Builder's self-assessment) with `prompts/verifier.md`
     + the component's `verifier`. It runs `auto_check.method` (Bash) and asserts `expected`,
     follows the `human_test` procedure against the artifact, checks every acceptance criterion,
     and returns `PASS`/`FAIL` + reasons.
   - **`needs_human: true`** (`auto_check.runnable == false` — `measurement`, `manual-only`, or any
     physical/real-world test an agent cannot perform): **DO NOT let an agent fabricate a verdict.**
     PAUSE and present to the user, verbatim, the component's `human_test.procedure`,
     `expected_observation`, and `pass_criteria`, then **wait** for the user to report what they
     observed and whether it passed. This is the human-verification gate — it is what makes the
     domain-agnostic claim real (an LLM cannot read a thrust gauge).
4. **Record the verdict with `set-status.py`** (it writes the evidence note + re-renders):
   - agent PASS: `set-status.py <dir> <id> passed --source agent --note "<verifier summary>"`
   - human PASS: `set-status.py <dir> <id> passed --source human --observed "<what they saw>" --note "<criteria met>"`
   - FAIL: re-spawn the Builder with the FAIL reasons (≤ `repair_protocol.max_iterations_per_component`).
     Still failing at the cap → `set-status.py <dir> <id> failed --note "<blocker>"`, then **continue**
     to other independent `ready` leaves (one stuck component must not stall the rest); surface it in
     the final report.
5. After recording, re-run `next-ready.py` for the new frontier.

#### 2b. Intermediate / root — compose then verify
`next-ready.py` only surfaces a parent once **all** its children are `passed` (the helper enforces
this; `set-status.py` independently refuses to mark a parent `passed` while a child isn't).
1. `set-status.py <feature-dir> <id> building`.
2. **Spawn an Integrator** (general-purpose, `$INTEGRATOR_MODEL` from Step 0) with `prompts/integrator.md` + the parent's
   `contract` + the `integration-map.json` edges for its children + the children's built
   artifacts. It wires the children's outputs into the parent's inputs and produces the parent's
   composed output artifact.
3. **Verify the composed parent** — same `needs_human` branch as 2a step 3 (a parent whose verifier
   is `measurement`/`manual-only` — e.g. the rocket's whole-product launch test — goes through the
   human-verification gate, not an agent verdict).
4. On `PASS`: `set-status.py <dir> <id> passed --source <agent|human> --note "…"` and climb (re-run
   `next-ready.py`).
5. On `FAIL` → **the up→down→up repair loop** (per `repair_protocol.on_integration_fail`):
   - First, move the parent out of `building` so the frontier stays correct across the (multi-cycle)
     repair: `set-status.py <dir> <parent> failed --note "integration fail: <reasons>"`. A `failed`
     parent with non-passed children shows as `blocked` in `next-ready.py` and re-enters `ready` only
     after its children re-pass — exactly the desired up→down→up sequencing.
   - The Integrator ranks the parent's children by likelihood of causing the failure, using
     contract mismatches (a child output that doesn't satisfy what the parent needed) and
     acceptance gaps revealed by the failure.
   - For each top suspect: `set-status.py <dir> <suspect> failed --note "<why suspected>"`, which
     re-opens it (it re-appears in `next-ready.py`). Rebuild or **upgrade** it (a stronger spec, not
     just a retry), re-verify, then the parent re-enters `ready` and you re-compose + re-verify.
   - Repeat up to `max_iterations_per_component`; then escalate to the user with the evidence.

> Why drill down instead of patching the parent? Per the thesis, a parent has no behavior of its
> own beyond composing its children — so a parent failure is, by construction, either a wiring
> error (Integrator fixes) or a child that doesn't really meet its contract (drill down). Patching
> the parent in place would smuggle hidden, untested behavior into a node that is supposed to be
> pure composition.

### Step 3: Converge at the root

When the depth-0 root Product reaches `passed`, its whole-product verifier has been satisfied
against the vision's success criteria. Do a final library render and confirm every
`success-criteria.json` criterion's `covered_by` components are all `passed`.

### Step 4: Report

```
COMPONENT BUILD COMPLETE
========================
Feature: <feature-id>
Components: <passed>/<total> passed   (<failed> failed, <untested> untested)
Max depth reached: <D>
Repairs triggered: <count>  (up→down→up loops)
Library: <feature-dir>/library.html

Vision coverage:
  - SC-01  ✔ covered by C-003, C-007 (all passed)
  - ...

[If any component failed at the iteration cap, list it with its blocker and the evidence ref.]

Next:
  - Open library.html and spot-test any component at random.
  - For a failed component: /acos-execute-component <feature-dir> --component <C>
```

Provide clickable links to `library.html` and any failing components' specs.

---

## Evidence convention (B3)

Two layers, reconciled with ACOS's existing evidence + metrics machinery:

1. **Canonical, feature-local** — `set-status.py` writes each verdict to
   `<feature-dir>/evidence/<component-id>-<source>.md` and records the path in the node's
   `evidence_ref`. This is the source of truth because it travels *with* the component tree and the
   Component Library references it; the tree is self-describing and portable.
2. **ACOS-visible mirror (optional)** — for parity with `/acos-execute-slice`, the runtime MAY also
   append a one-line completion record per component to
   `.acos/evidence/<YYYY-MM-DD>/preeng-unix-<feature-id>/<component-id>.log` (always-allowed by the
   scope hooks) and log agent identity to `.acos/metrics/agent-completions.log` (the same sink the
   preeng worker's instrumentation plan points at). This keeps component builds visible to ACOS
   status/metrics tooling without making the tree depend on `.acos/`.

Rule: never set a component `passed` without a recorded Verifier `PASS` (or a human `--source human`
verdict) in layer 1. Layer 2 is a convenience mirror, not the gate.

---

## Guarantees & guardrails

- **Independence of verification:** the Verifier is always a fresh agent that does not see the
  Builder's self-assessment — zero-trust, mirroring ACOS reviewers.
- **Evidence-backed:** every build/verify writes an evidence note; status in the library is never
  set to `passed` without a recorded Verifier `PASS`.
- **No silent assembly:** a parent can never be `passed` while any child is not `passed`.
- **Bounded repair:** `max_iterations_per_component` (default 5) caps each rework loop; exhaustion
  escalates to the user rather than looping forever.
- **Reuse-aware:** if a component marked `reuse.reusable` is already `passed` in this (or a linked)
  tree, the runtime may reuse its artifact rather than rebuild — recorded in `reuse.known_consumers`.

---

*ACOS Execute Component — build the leaves, prove each one, compose upward, repair downward.*
