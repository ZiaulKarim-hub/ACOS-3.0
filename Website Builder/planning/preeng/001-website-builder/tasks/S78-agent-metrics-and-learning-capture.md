# S78-agent-metrics-and-learning-capture — Agent-metrics scaffolding and the learning-capture loop

| Field | Value |
|---|---|
| Epic / Story | E19 / ST-26 |
| Type · MoSCoW · Size | build · MUST · S `[I]` |
| Phase / Demo | Phase 6 / — |
| Depends on | S77-selftest-and-evidence-bundles |
| Requirements | FR-252, FR-253 |
| Acceptance criteria | SL-S78-1 · SL-S78-2 · SL-S78-3 · SL-S78-4 |
| CQ / evidence | EL-065 |
| Note | **Defined here; computed nowhere.** `AGENT-METRICS.md` is an instrumentation contract — a metrics document that computes a number from inputs that do not exist yet manufactures a measurement |

## PM — slice definition

**Objective.** Define the performance formulas and their logging locations, and **lift the run's learnings into the estate**.

**In scope.** `AGENT-METRICS.md` at the feature root defining — **SPD** (Story Points Delivered: a qualitative approximation of delivered slice weight per agent per run, recorded per slice in the evidence bundle); **QAP** = `(Delivered_Value * Quality_Score) / (1 + Rejection_Count)` where `Rejection_Count` counts the QA rejections that slice absorbed; **TER** (Token Efficiency Ratio: artifacts produced per 1K tokens consumed, where cost data exists); **UAPS** = `0.3*Quality + 0.4*Efficiency + 0.3*CostEffectiveness` — each with its inputs and **the file each input is read from**, and an explicit statement that **no value in the document is computed by this pipeline**; instrumentation pointed at the existing `.acos/metrics/agent-completions.log` (agent_type / agent_id, already written by the framework) plus the per-slice evidence bundles under `.acos/evidence/[DATE]/[SLICE-ID]/`; a checker that every slice in this feature has **non-empty** Dev Learnings **and** QA Learnings, reporting an empty one as **not Done**; and the lift of cross-project patterns into `learning-curve/`.

**Out of scope.** Computing any metric value. Adding telemetry of any kind (NG3 — nothing leaves the machine). Aggregating learnings into a separate document nobody reads; learnings stay where the work happened, in the task files.

**Allowed files / contexts.**
- `AGENT-METRICS.md` (new, feature root), `scripts/learnings-check.ts`, `learning-curve/` (append the lifted patterns).
- **Read-only against `tasks/*.md`** — the checker reads learnings sections and never writes one.

**Steps.**
1. Write `AGENT-METRICS.md`: one section per metric — definition, formula where one exists, each input, and the **absolute** path the input is read from. State once, prominently, that nothing here is computed.
2. Point instrumentation at the two existing sinks; add no new log file, because a metric with a bespoke sink is a metric nobody maintains.
3. Implement `learnings-check.ts`: parse every task file's `## Dev Learnings` and `## QA Learnings`; a section still carrying only its `_Not Done until filled…_` placeholder is **empty**; report the slice as **not Done** and exit non-zero.
4. Capture the three named learning obligations explicitly, because they are the ones most likely to be lost:
   a. **The passing launcher rung** from Gate 16-A — a first-party harness fact, lifted into `references/gotchas.md` and into the estate's memory.
   b. **The measured canvas sub-slice effort** (S41–S43) — the only evidence that can turn the source's ~2× effort contradiction into a number; the +16–24 d delta and the 30–60 d band are carried **verbatim and unaveraged** `[I — every effort figure is inference, EL-065, confidence 0.3]`.
   c. **Every source contradiction found by reading two sections against each other** — the NA items exist because of that reading protocol, and the protocol itself is the reusable pattern.
5. Lift the cross-project patterns into `learning-curve/` with a one-line provenance per entry.

**Definition of Done.**
- Artifacts: `AGENT-METRICS.md`, `learnings-check.ts`, the three captured obligations, the `learning-curve/` entries.
- Validation: the metrics document names four metrics, their inputs and their sources, and computes nothing (grep for a computed numeral in a result position); `learnings-check.ts` exits non-zero against a seeded placeholder section; all three obligations are present with content, not headings.
- `slice.yaml` mapping — `acceptance_criteria: [SL-S78-1, SL-S78-2, SL-S78-3, SL-S78-4]`, `verification_method: grep-assert` (SL-S78-3: `exit-code`; SL-S78-4: `manual-observation`).

**Assumption.** `[I]` `Delivered_Value` and `Quality_Score` have **no defined scale** in any read artifact. `AGENT-METRICS.md` records them as inputs supplied per slice in the evidence bundle and states that their scale is undefined at pre-engineering time — it does **not** invent one, because an invented scale would make QAP and UAPS look computable when they are not.

## Dev — execution contract

Every effort figure in this feature is `[I]` inference, never measurement; the document must say so in its own words. Evidence bundle: (1) summary — four metrics defined, N slices checked, N learnings sections empty; (2) traceability FR-252, FR-253 → file:line; (3) structural quality — one checker, one document, no aggregation layer; (4) functional testing — the checker's output on the real task set plus a seeded placeholder; (5) security/compliance — no telemetry, no network, nothing leaves the machine; (6) operational — how a slice's learnings are recorded and where the lift goes; (7) self-assessment.

## QA — zero-trust verification

- **Run `learnings-check.ts` yourself** across all 78 task files and confirm the count of empty sections matches; then **seed a placeholder** and confirm a non-zero exit.
- **Read `AGENT-METRICS.md` for a computed number** in any result position; one is a rejection, because the whole point is that these are defined and not yet measurable.
- **Confirm each input names an absolute source path** you can open.
- **Check the three obligations by content**, not by heading — an obligation captured as an empty section is not captured.
- **Confirm the effort figures are carried unaveraged**; a single reconciled v1 total is a rejection.
- **Reject** if a new log sink was introduced instead of using the existing completions log.
- **Reject** if this slice wrote into any task file's learnings section.

## Dev Learnings

_Not Done until filled. Required: how many slices reached the end of the run with empty learnings before the checker existed, and which of the three obligations was hardest to reconstruct._

## QA Learnings

_Not Done until filled. Required: whether the metrics document reads as an instrumentation contract or as a scoreboard, and which formula most invited premature computation._
