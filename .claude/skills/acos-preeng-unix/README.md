# acos-preeng-unix

A **tertiary planning system** for ACOS — a component-decomposition pre-engineering pipeline
inspired by the **Unix philosophy** ("do one thing well; compose small pieces through clean
interfaces"). It is the planning half; `acos-execute-component` is the execution half.

> ACOS planning front-ends, in order of authority:
> 1. `/acos-plan` — primary, interactive Vision→Epic→Story→Slice. **Authoritative.**
> 2. `/acos-preeng-classic` — secondary, faithful preeng port → bridged slices.
> 3. `/acos-preeng-unix` — tertiary, component tree → own execution engine. **(this)**

## The thesis — the Unix Invariant

> **Every node in the plan — leaf AND intermediate — is an independently human-testable,
> output-generating component.**

No "mindless parts." You decompose **top-down** (*"what testable components, wired together,
fulfill this?"*) to a **variable depth** (Product → Modules → Parts → Sub-parts → …, as deep as
each branch needs), and build **bottom-up** (leaves first → verify each → compose upward → on
failure drill back down to the culprit children and re-climb). Each component is a real functional
unit, so it is **reusable**.

### The rocket, concretely
```
Rocket (root, testable: full mission profile)
└─ Engine (testable: thrust/ISP on a stand)
   └─ Gimbal system (testable: deflection vs command)
      └─ Servo motor (LEAF, testable: RPM @ load, current draw)
```
Build the servo motor and prove it spins to spec. Then the gimbal, then the engine, then the
rocket — each proven before it becomes a part of the next. If the engine underperforms, drill down:
upgrade the suspect child (maybe the motor), re-prove it, re-assemble, re-test.

## Invocation

```
/acos-preeng-unix [vision description]    # full pipeline from a description
/acos-preeng-unix --from-file <path>      # use an existing vision/brief
/acos-preeng-unix --resume <feature-id>   # re-run / update an existing tree
```

## Architecture — a two-stage compiler

```
vision context
      │  Step 1 (the only interactive step)
      ▼
[RUNNER / compiler]  (general-purpose, opus)   ← prompts/runner.md
      │  normalizes vision → deterministic_prompt + feature_config + command_inputs
      ▼
[WORKER / interpreter] (general-purpose, opus) ← prompts/worker.md
      │  7 commands in order, honoring ERROR-gates + the Unix Invariant:
      │  envision → decompose → contract → verify-spec → library → buildplan → coverage
      ▼
planning/preeng-unix/<feature-id>/   (artifact set, below)
      │  Step 3.5 render-library.py   (browsable Component Library HTML)
      │  Step 4   verify-artifacts.sh (completeness + coverage gate)
      ▼
/acos-execute-component   (bottom-up build → verify → compose → repair)
```

Agents are **spawned as `general-purpose`** carrying embedded prompts — no files added to the
human-approval-restricted `.claude/agents/` dir.

## Artifact manifest (per feature)

```
planning/preeng-unix/<feature-id>/
  vision.md                 # restated vision + domain + testable success criteria + verifier vocab
  success-criteria.json     # discrete testable criteria; covered_by[] filled at coverage time
  component-tree.json        # THE master artifact (schema: templates/component-tree.schema.json)
  components/<id>.md         # per-component human spec: what it is / must do / how to test / linkage
  integration-map.json       # child→parent wiring (the 'pipes')
  build-plan.json            # leaves-first order + levels + up→down→up repair protocol
  library.html               # browsable, self-contained Component Library (rendered)
  library-status.json        # live id→status the runtime updates
  coverage-report.md         # criteria→components matrix + 3 gate results + reuse summary
  coverage_qa_report.json    # mechanical gate (REJECTED blocks execution)
  analysis-report.md         # reuse map, canonical candidates, bloat annotations
  cage_unix_nodes.csv / cage_unix_edges.csv   # decision trace for the decomposition
  agent_instructions/{builder,verifier,integrator}.md
```

## The Component Library (your spot-test surface)

`library.html` is self-contained (no runtime deps) and rendered by `scripts/render-library.py`
from `component-tree.json` + `library-status.json`. Each component is a card showing **identity,
purpose, single responsibility, the output you can see, how to test it (auto-check command +
by-hand procedure + pass criteria), how it connects upward, children, reuse tags**, and a live
**status badge** (planned / building / passed / failed / untested). A **"🎲 Test a random
component"** button lets a human audit the build at random — re-run the renderer to refresh status
as the execution engine works.

## Pluggable, domain-agnostic verifiers

Not software-only. Each node declares a `verifier.type` from the feature's `verifier_vocabulary`:
`software-test`, `document-render`, `blueprint-constraint`, `data-schema`, `visual-diff`,
`measurement`, `manual-only` (extend per domain). The type drives both the machine auto-check and
the human-test panel — so a designed document, a blueprint, or a dataset is a first-class component
right alongside code.

## How it differs from the other planners

| | `/acos-plan` | `/acos-preeng-classic` | `/acos-preeng-unix` |
|---|---|---|---|
| Unit | slice (work chunk) | task → bridged slice | **component (testable output unit)** |
| Shape | Vision→Epic→Story→Slice | ~17 preeng artifacts | **variable-depth component tree** |
| Build order | slice-first toward vision | bridged into slice lifecycle | **bottom-up, compose upward** |
| Failure handling | re-plan / re-slice | reviewer reject → rework | **up→down→up drill-and-repair** |
| Reuse | — | — | **first-class (tagged, shared)** |
| Domain | software | software | **agnostic (sw / doc / hardware / data)** |
| Execution | `/acos-execute-slice` | `/acos-execute-slice` | **`/acos-execute-component`** |

## Files

```
.claude/skills/acos-preeng-unix/
  SKILL.md                          # orchestrator (planning, 6 steps + 3.5 render)
  README.md                         # this file
  prompts/runner.md                 # compiler — normalizes vision → deterministic prompt
  prompts/worker.md                 # deterministic worker — the 7-command spec + schemas
  templates/component-tree.schema.json   # canonical node schema (the spine)
  templates/library.html            # self-contained library shell (injection tokens)
  scripts/render-library.py         # stdlib-only renderer: tree+status → library.html
  scripts/verify-artifacts.sh       # completeness + coverage gate (blocks execution)
  scripts/registry.py               # cross-tree reuse registry (publish / search / link)
```

Execution half lives in `.claude/skills/acos-execute-component/`.

## Cross-tree reuse (operationalized)

The Unix promise — *a proven component can be reused elsewhere* — is real, not just metadata.
`scripts/registry.py` maintains a project-level index at `planning/preeng-unix/_registry/registry.json`
(above any feature dir, because reuse is inherently cross-tree):

- **publish** — when a `reuse.reusable` component reaches `passed`, `set-status.py` auto-indexes it
  (capability tags, verifier, contract, the proven artifact location). The index never silently rots.
- **search** — at plan time, Step 1.5 runs `registry.py search` and folds matches into the worker's
  context, so decomposition prefers an existing proven part over inventing a new one.
- **link** — at execution time, when a reusable leaf matches a registry entry, `/acos-execute-component`
  runs `registry.py link` to copy the proven artifact into the new tree and mark the leaf `passed`
  (source `reuse`) — no rebuild, no re-verification of already-proven work. The consumer is recorded
  on the registry entry (`consumers[]`).

So a "Clock provider" proven in one product is found and reused by the next, exactly as a Unix tool
is reused across pipelines.
