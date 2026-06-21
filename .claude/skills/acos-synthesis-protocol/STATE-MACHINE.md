# Component Status State Machine (acos-synthesis-protocol)

The formal contract for `status` transitions in `component-tree.json`. The only writer is
`scripts/set-status.py`; the only reader-for-scheduling is `scripts/next-ready.py`. This document
is the authority when prose and code disagree — and `set-status.py` enforces two hard invariants
mechanically: the parent-gate (exit 3) and the hardening-gate (exit 4).

## States

| state | meaning |
|-------|---------|
| `planned` | declared by `/unix.decompose`; not yet started. The initial state of every node. |
| `building` | a Builder (leaf) or Integrator (parent) is actively producing the artifact. |
| `passed` | a Verifier returned `PASS`, **or** a human reported PASS through the verification gate — AND, for a hardening-eligible code leaf, the hardening gate reached `clean`/`punchlist`/`skipped`. Terminal-until-reopened. |
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

## The second hard invariant — the hardening gate (exit 4)

> **A hardening-ELIGIBLE code leaf may be set to `passed` only if its `hardening.state` ∈
> {`clean`, `punchlist`, `skipped`}.**

`set-status.py` checks this and **refuses with exit 4** otherwise (reuse-sourced passes are exempt —
the linked original was hardened when first published). A leaf is *eligible* iff it is a leaf AND its
`verifier.type` ∈ the tree's `hardening.code_verifier_types` (default `software-test`, `data-schema`),
unless `hardening.enabled` explicitly overrides. This makes "every code component is hardened before
it is composed upward" a mechanical fact: the parent-gate already blocks a parent until its children
are `passed`, and this gate blocks a code child from `passed` until it is hardened — so the
composition can never absorb un-hardened code.

`hardening.state` is an **orthogonal attribute**, not a `status` value — the five `status` states are
unchanged. The lifecycle of `state` (written by `set-status.py --hardening`):

| state | meaning |
|-------|---------|
| (absent)/`pending` | gate not yet satisfied — a bare `passed` on an eligible leaf is refused. |
| `clean` | zero findings at any severity. The goal state. |
| `punchlist` | zero findings at/above the severity gate; lower findings deferred to `punchlist_ref` for user approval. |
| `skipped` | not eligible (non-code artifact, a parent, or `--no-harden`) — recorded for audit; never blocks. |

A leaf that cannot clear *blocking* findings within `HARDEN_ROUNDS` is set `failed` (not forced to
`passed`), and re-enters the frontier exactly like a functional FAIL.

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
