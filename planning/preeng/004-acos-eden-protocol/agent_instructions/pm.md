# PM Instructions — acos-eden-protocol (maps to ACOS architect)

## Role
Own slice definition using Lean Context Engineering: one narrow objective, explicit in/out-of-scope,
allowed files, step-by-step, and a testable Definition of Done per slice.

## Inputs
`spec.md`, `plan.md`, `tech_prd.md`, `data-model.md`, `stories.json`, `tasks/*.md`, and the swarm
synthesis (`.acos/swarm/swarm-20260707-eden-protocol/synthesis/report.md`).

## Workflow
1. Bridge each `tasks/SL-004-eden-*.md` into a `planning/slices/` skeleton (skill Step 5).
2. Enforce sequencing: **SL-02 spike before SL-03 injector**; **Demo 2 fidelity before Demo 3 engine**.
3. For each slice, confirm scope is one objective and DoD names its evidence gate.
4. On ambiguous user input to the eventual skill, require a Confirmation-Gate clarification — never a
   silent default (this is both a product rule and a build rule).

## Definition of Done (per slice)
Required artifact(s) exist; required validation runs; evidence bundle present; Dev + QA learnings updated.

## Prohibited
- Do NOT let a slice expand scope. Do NOT allow the injector to finalize before the U1 spike.
- Do NOT weaken the Fidelity Floor or the top-level-chat-only scope to make a slice easier.

## Evidence expectations
Each slice's DoD maps cleanly to `slice.yaml` `acceptance_criteria` + `verification_method`.

## Learning capture
A slice is not Done until `## Dev Learnings` and `## QA Learnings` are updated in its task file.
