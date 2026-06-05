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

Read `component-tree.json`, `integration-map.json`, `build-plan.json`. The build plan's `order`
is authoritative; `repair_protocol` governs failure handling.

### Step 1: Initialize status

Ensure `library-status.json` exists with every component id set to its current status (`planned`
for a fresh run; preserve prior statuses on resume). Render the library once so the user has a
live view:

```bash
python3 .claude/skills/acos-preeng-unix/scripts/render-library.py "<feature-dir>"
```

### Step 2: Walk the build plan (leaves first)

Iterate `build-plan.json.order`. For each component, branch on whether it is a **leaf**
(`children == []`) or an **intermediate/root**.

#### 2a. Leaf — build then verify
1. Set status `building`; refresh library.
2. **Spawn a Builder** (general-purpose, opus) with `prompts/builder.md` + the component's
   `components/<id>.md` spec + its `contract`. Scope is **only** this component's output
   artifact. It writes the artifact to `output_artifact.location_hint` (or a sensible default
   under the feature dir) and an evidence note.
3. **Spawn a Verifier** (general-purpose, opus — a *fresh* agent that does NOT see the Builder's
   self-assessment) with `prompts/verifier.md` + the component's `verifier`. It:
   - runs `verifier.auto_check.method` if `runnable` (Bash) and asserts `expected`;
   - performs / documents the `human_test` procedure and judges `pass_criteria`;
   - returns `PASS` or `FAIL` + reasons.
4. On `FAIL`: re-spawn the Builder with the Verifier's reasons (≤ `max_iterations_per_component`).
   Still failing at the cap → mark `failed`, record the blocker, and **continue** to other
   independent leaves (do not let one component stall the rest); surface it in the final report.
5. On `PASS`: set status `passed`, write `evidence_ref`, refresh library.

#### 2b. Intermediate / root — compose then verify
Reached only after **all** its children are `passed`.
1. Set status `building`; refresh library.
2. **Spawn an Integrator** (general-purpose, opus) with `prompts/integrator.md` + the parent's
   `contract` + the `integration-map.json` edges for its children + the children's built
   artifacts. It wires the children's outputs into the parent's inputs and produces the parent's
   composed output artifact.
3. **Spawn a Verifier** on the parent (its verifier tests the *composed* component).
4. On `PASS`: status `passed`; climb.
5. On `FAIL` → **the up→down→up repair loop** (per `repair_protocol.on_integration_fail`):
   - The Integrator ranks the parent's children by likelihood of causing the failure, using
     contract mismatches (a child output that doesn't satisfy what the parent needed) and
     acceptance gaps revealed by the failure.
   - Mark the top suspect(s) `failed`, re-open them as leaf/sub-builds (rebuild or **upgrade** —
     a stronger spec, not just a retry), re-verify each, then re-compose the parent and re-verify.
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
