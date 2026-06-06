# Component Status State Machine (acos-execute-component)

The formal contract for `status` transitions in `component-tree.json`. The only writer is
`scripts/set-status.py`; the only reader-for-scheduling is `scripts/next-ready.py`. This document
is the authority when prose and code disagree — and `set-status.py` enforces the one hard invariant
mechanically (exit 3).

## States

| state | meaning |
|-------|---------|
| `planned` | declared by `/unix.decompose`; not yet started. The initial state of every node. |
| `building` | a Builder (leaf) or Integrator (parent) is actively producing the artifact. |
| `passed` | a Verifier returned `PASS`, **or** a human reported PASS through the verification gate. Terminal-until-reopened. |
| `failed` | a Verifier/human returned FAIL (leaf), or an integration verify failed (parent), or the build hit the iteration cap. Re-enters the frontier. |
| `untested` | reserved: an artifact exists but no verdict has been recorded (e.g. imported/reused without re-verification). Treated as needs-work by the frontier. |

## Legal transitions

```
            ┌────────────────────────────────────────────────┐
            ▼                                                 │ (re-open: repair loop /
   planned ──▶ building ──▶ passed                            │  child upgrade)
      ▲           │                                           │
      │           └──▶ failed ───────────────────────────────┘
      │                  │
      └──────────────────┘   (operator reset)

   untested ──▶ building ──▶ {passed | failed}     (reused/imported artifact path)
```

- `planned → building → passed` — the happy path.
- `building → failed` — verify failed, or rework hit `max_iterations_per_component`.
- `failed → building → {passed|failed}` — rework / upgrade (leaf), or re-compose (parent).
- `passed → failed` — only via the **repair loop**: when a parent fails, its suspect *children* are
  explicitly re-opened (`set-status … failed`), which is a deliberate `passed → failed`. Outside the
  repair loop, do not move a `passed` node backward.
- A parent that fails verification is set `failed` (NOT left `building`) so the frontier can re-block
  it behind its re-opened children — see the up→down→up note below.

## The one hard invariant (enforced in code)

> **A node may be set to `passed` only if ALL its children are already `passed`.**

`set-status.py` checks this and **refuses with exit 3** otherwise. Rationale: a parent is *pure
composition* — it has no behavior beyond wiring verified children. Letting a parent pass over a
non-passed child would assert the whole is sound while a part is unproven, which is the exact failure
mode the Unix Invariant exists to prevent. (`next-ready.py` independently never surfaces a parent
until its children are `passed`, so the invariant is guarded on both the read and write sides.)

## Frontier rules (`next-ready.py`)

A node is **ready** (buildable now) iff: its status ∈ {`planned`, `failed`, `untested`} AND it is a
leaf OR all its children are `passed`. `building` is skipped (in progress). A node with non-passed
children is **blocked** (and lists what it waits on). `done` ⇔ the depth-0 root is `passed`.

Because every status lives on disk, the frontier is a pure function of current state — so an
interrupted run **resumes** exactly by re-running `next-ready.py`; there is no in-memory walk to lose.

## up→down→up (why a parent goes `failed`, not `building`, on integration failure)

1. Parent verify FAILS → `set-status parent failed` (moves it out of `building`).
2. Rank suspect children → `set-status <suspect> failed` (re-opens them).
3. Frontier now: suspects `ready`; parent `blocked` (waiting on them). The bottom-up order is
   automatically restored — no manual sequencing.
4. Suspects rebuilt/upgraded → re-verified → `passed`. Parent re-enters `ready` → re-composed →
   re-verified. Repeat ≤ `max_iterations_per_component`, then escalate.
