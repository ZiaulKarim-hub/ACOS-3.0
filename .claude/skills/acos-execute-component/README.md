# acos-execute-component

The **execution half** of `acos-preeng-unix`. The planning engine produced a tree of
independently testable components; this engine **builds it bottom-up**, the way you'd actually
build a rocket: prove the smallest parts first, then assemble and re-prove at every level.

## What it does

```
build-plan.json (leaves first)
   ├─ LEAF:   Builder → output artifact ;  Verifier (zero-trust) → auto-check + human test
   │            fail ▶ Builder reworks (≤ max_iter) ;  pass ▶ status=passed, library refreshed
   └─ PARENT (all children passed): Integrator → compose via contracts ;  Verifier → test parent
              fail ▶ up→down→up repair: rank suspect children, upgrade, re-verify, re-compose, climb
   ▼  until the root Product passes its whole-product verifier against the vision.
```

The three roles map onto ACOS's adversarial trust model:
**Builder ≈ developer**, **Verifier ≈ qa-reviewer (zero-trust, fresh agent)**,
**Integrator ≈ architect (composition + repair)**. All spawned as **general-purpose** agents with
embedded prompts (`prompts/{builder,verifier,integrator}.md`) — no new `.claude/agents/` files.

## Invocation

```
/acos-execute-component <feature-dir>                 # full bottom-up build
/acos-execute-component <feature-dir> --component <C> # one component (+ its deps)
/acos-execute-component <feature-dir> --status        # render + print status, stop
/acos-execute-component <feature-dir> --max-iter <N>  # rework cap (default 5)
```

`<feature-dir>` = `planning/preeng-unix/<feature-id>` (must pass
`acos-preeng-unix/scripts/verify-artifacts.sh` first).

## Guarantees

- **Independent verification** — the Verifier never sees the Builder's self-assessment.
- **No silent assembly** — a parent can't be `passed` while any child isn't `passed`.
- **Evidence-backed** — `passed` requires a recorded Verifier `PASS`; notes land in
  `<feature-dir>/evidence/`.
- **Bounded repair** — `max_iterations_per_component` caps each loop; exhaustion escalates.
- **Drill-down, not patch-over** — a parent failure is fixed by correcting wiring or upgrading the
  culprit child, never by hiding behavior in the (composition-only) parent.
- **Reuse-aware** — an already-`passed` reusable component may be reused rather than rebuilt.

## Status & the Component Library

Status lives in `<feature-dir>/library-status.json` and is reflected in `library.html` after each
change (the runtime re-runs `acos-preeng-unix/scripts/render-library.py`). Open the library and use
**🎲 Test a random component** to audit the build yourself at any point.

## Runtime helpers (the deterministic glue)

The SKILL prose is driven by two stdlib-only scripts so no agent ever hand-edits state:

- **`scripts/next-ready.py <feature-dir>`** — the resumable build frontier. Reads on-disk status and
  reports `ready[]` (buildable now: a leaf, or a parent whose children all `passed` — in build
  order), `building[]`, `blocked[]` (waiting on a child), `done`, and a status histogram. Each ready
  component is flagged `needs_human` when its `auto_check.runnable == false`. Because state lives on
  disk, re-running this after any interruption recomputes the exact frontier — that's the resume.
- **`scripts/set-status.py <feature-dir> <id> <status>`** — the ONLY status writer. Mirrors
  `component-tree.json` ↔ `library-status.json`, writes an evidence note (`--note` / `--observed` /
  `--source human|agent`), **enforces the parent-gating invariant** (refuses `parent=passed` while a
  child isn't — exit 3), and re-renders `library.html`.

The **human-verification gate** falls out of these two: `next-ready.py` flags `needs_human`; the
SKILL pauses and asks the *user* to report the observed result; `set-status.py … --source human`
records it. An LLM Verifier is spawned only for machine-/agent-checkable components — it never
fabricates a physical measurement.

## Files

```
.claude/skills/acos-execute-component/
  SKILL.md                 # the bottom-up runtime protocol (next-ready → dispatch → set-status loop)
  README.md                # this file
  STATE-MACHINE.md         # formal status states, legal transitions, the hard invariant
  prompts/builder.md       # build one component's output (scope-bounded)
  prompts/verifier.md      # zero-trust per-component verdict (machine/agent-observable only)
  prompts/integrator.md    # compose children → parent + up→down→up repair loop
  scripts/next-ready.py    # resumable build frontier + needs_human flags
  scripts/set-status.py    # sole status writer; enforces parent-gating invariant; re-renders
```

## ACOS integration (SHOULD tier)

- **Scope hooks (B1):** execution runs with no active slice, so `check-scope.sh` /
  `check-scope-bash.sh` fail open. SKILL Step 0 warns if a stale `active-slice.yaml` exists (it would
  scope-block builds) and tells the user to `/acos-complete` it first.
- **Model profiles (B2):** the three roles resolve through `resolve-agent-model.sh` — Builder≈
  `developer`, Verifier≈`qa-reviewer`, Integrator≈`architect` — so the active model profile governs
  them (external models fall back to Claude for the tool-using roles).
- **Evidence (B3):** canonical per-verdict notes are feature-local (`<feature-dir>/evidence/`,
  referenced by each node's `evidence_ref`); an optional `.acos/evidence/<date>/preeng-unix-<id>/`
  mirror + `.acos/metrics/agent-completions.log` keep builds visible to ACOS tooling.
- **State machine (B4):** see `STATE-MACHINE.md`.
