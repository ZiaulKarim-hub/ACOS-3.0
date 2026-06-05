# acos-preeng-classic

A **secondary planning system** for ACOS — a faithful port of the external `preeng`
pre-engineering skill, bridged into the native ACOS lifecycle.

> Primary planning in ACOS is `/acos-plan` (interactive interview + recursive
> Vision→Epic→Story→Slice). This skill is the *alternative* front-end: a single-pass,
> autonomous, artifact-generating pipeline for complex/novel features. When the two
> disagree, `/acos-plan` is authoritative; preeng output is a proposal that the bridge
> converts into normal ACOS slices.

## Invocation

```
/acos-preeng-classic [product description]     # full pipeline from a description
/acos-preeng-classic --from-file <path>        # use an existing brief as context
/acos-preeng-classic --resume <feature-id>     # re-run / update an existing feature
```

## Architecture — a two-stage compiler

```
product context
      │  Step 1 (the only interactive step)
      ▼
[RUNNER / compiler]  (general-purpose agent, opus)   ← prompts/runner.md
      │  normalizes context → deterministic_prompt + feature_config + command_inputs
      ▼
[WORKER / interpreter] (general-purpose agent, opus) ← prompts/worker.md
      │  executes 6 commands in order, honoring ERROR-gates:
      │  specify → research → plan → tasks → analyze → instructions
      ▼
planning/preeng/<feature-id>/   (full artifact set, below)
      │  Step 4 verify-artifacts.sh  (mechanical completeness + QA gate)
      ▼
BRIDGE → planning/slices/ skeletons → /acos-execute-slice
```

Agents are **spawned by the skill as `general-purpose` agents** carrying the embedded
prompts — no files are added to the human-approval-restricted `.claude/agents/` dir.

## Artifact manifest (per feature)

```
planning/preeng/<feature-id>/
  spec.md                  # 13-section PRD (MoSCoW + NFRs + diagnostics + rollout/demos)
  research.md              # research narrative
  domain-brief.md          # domain overview
  domain-cqs.md            # 10–15 competency questions
  domain-lattice.json      # knowledge graph (typed nodes/edges, ≥95% CQ coverage)
  evidence-ledger.json     # claims w/ T1–T5 tiers, confidence, freshness
  research_qa_report.json  # mechanical QA gate for research phase
  plan.md                  # implementation plan (phases, tasks, DoD)
  tech_prd.md              # technical architecture / NFR contracts
  data-model.md            # data structures / schema
  planning_qa_report.json  # mechanical QA gate for planning phase
  stories.json             # epic/story/slice breakdown
  tasks/<slice-id>.md      # per-slice PM/Dev/QA + Dev/QA learnings
  tasks_qa_report.json     # mechanical QA gate for tasks phase
  analysis-report.md       # cross-artifact analysis + canonical-candidate flags
  cage_preeng_nodes.csv    # CAGE decision-trace nodes
  cage_preeng_edges.csv    # CAGE decision-trace edges
  agent_instructions/      # pm.md / dev.md / qa.md onboarding prompts
```

## What's faithful to preeng, and what's adapted

**Faithful (the "classic" character):**
- Two-stage runner→worker compiler.
- "Program, not suggestion" determinism; worker never asks questions.
- Full 6-command pipeline + the 0.1–0.9 protocol stack.
- Canonical schemas (domain lattice, evidence ledger, QA reports).
- Hard precondition ERROR-gates between phases (research-REJECTED blocks plan;
  planning-REJECTED blocks tasks).
- ≥95% CQ coverage target; CAGE decision trace; QAP/TER/UAPS metric formulas.

**Adapted for ACOS (behavior-preserving):**
- Output path `/specs/<id>/` → `planning/preeng/<id>/`.
- Foreign edge-agentic / `/implement` handoff → **ACOS slice bridge** (Step 5) that
  writes `planning/slices/` skeletons and points to `/acos-execute-slice`.
- Optional Step 1.5 grounding pre-seed (RAG + WebSearch) into the *product context*
  only — the worker stays a deterministic offline structurer. Skip it to stay
  byte-faithful.
- Agents run as `general-purpose` (no new `.claude/agents/` files).
- Instrumentation plan points at ACOS's real `.acos/metrics/agent-completions.log`.

## How it differs from `/acos-plan`

| | `/acos-plan` | `/acos-preeng-classic` |
|---|---|---|
| Input | interactive, many rounds | one form, then autonomous |
| Output | vision/epic/story/slice YAML | ~17 preeng artifacts → bridged slices |
| Grounding gate | domain-brief, ≥80% CQ coverage (Step 1.6) | domain lattice, ≥95% CQ coverage |
| Enforcement | prose gate at plan time; hooks at execute time | prose ERROR-gates at plan time; hooks at execute time |
| Knowledge artifact | flat CQ table | JSON knowledge graph + evidence ledger |
| Best for | iterative/evolving scope | complex, novel, research-heavy, regulatory |

Both converge on the same downstream: real ACOS slices executed by
`/acos-execute-slice` under the usual execute → review → learn lifecycle.

## Files

```
.claude/skills/acos-preeng-classic/
  SKILL.md                     # orchestrator (7 steps)
  README.md                    # this file
  prompts/runner.md            # Part Two — runner/compiler system prompt
  prompts/worker.md            # Part One — deterministic worker command spec
  scripts/verify-artifacts.sh  # Step 4 mechanical completeness + QA gate
```
