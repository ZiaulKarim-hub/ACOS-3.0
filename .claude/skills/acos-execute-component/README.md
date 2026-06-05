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

## Files

```
.claude/skills/acos-execute-component/
  SKILL.md                 # the bottom-up runtime protocol
  README.md                # this file
  prompts/builder.md       # build one component's output (scope-bounded)
  prompts/verifier.md      # zero-trust per-component verdict (auto + human)
  prompts/integrator.md    # compose children → parent + up→down→up repair loop
```
