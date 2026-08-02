# Cross-Artifact Analysis — acos-eden-protocol

## Artifact presence & QA status
| Artifact | Present | QA |
|---|---|---|
| spec.md | ✅ | — |
| research.md + domain-brief/cqs/lattice/evidence-ledger | ✅ | research_qa = **APPROVED** |
| plan.md + tech_prd.md + data-model.md | ✅ | planning_qa = **APPROVED** |
| stories.json + tasks/ (10) | ✅ | tasks_qa = **APPROVED** |
| analysis-report.md + cage_preeng_*.csv | ✅ (this) | — |
| agent_instructions/{pm,dev,qa}.md | ✅ | — |

No QA report is REJECTED → the bridge to ACOS slices (skill Step 5) is unblocked.

## Coverage & evidence quality
- **CQ coverage:** 14.5/15 = **96.7%** (≥95% target). CQ7/U1 is the single partial (spike-gated).
- **Evidence quality:** 8 ledger entries — R1/R5/R6 **T1** (authoritative/verified repo files),
  R2/R3/R4/R7 **T2** (expert reasoning), U1 **T3** (unverified, spike-attached). ~5/8 at T1/high
  confidence; the load-bearing mechanism decision (R1) is T1 and triple-sourced.
- **Lattice:** 48 nodes / 46 edges; every CQ node connects to ≥1 method/standard/risk path.

## Traceability highlights
- Every MUST (M1–M8) maps to a slice: M1/M7/M8→SL-01; M2/M4→SL-03/04 (gated by SL-02); M3→SL-01/10;
  M5→SL-03 (directive scope) + all engine slices; M6→SL-05/06.
- Every P0 swarm decision is embodied: R1→injector slices; R2→scope statement in SL-03; R3→SL-05/06.

## Canonical-candidate annotations (bloat mgmt §0.6)
- **Canonical (Review):** `research.md` §1 (the mechanism decision table) and the **Fidelity Floor**
  (research.md §3) are exemplary and reusable — flag as canonical examples for future "persistent-mode
  skill" and "fidelity-preserving simplification" work.
- **Active:** all current artifacts. **Burn pile:** none yet (the swarm agent-*/findings.md are the raw
  evidence behind the synthesis — keep as audit trail, not burn).

## Agent performance metrics (define, don't compute — §0.5)
- **SPD:** qualitative per slice (S/M/L effort tags in task files).
- **QAP** = (Delivered_Value × Quality_Score) / (1 + Rejection_Count) — Rejection_Count tracked by the
  Fidelity-Floor QA gate (SL-05).
- **TER:** artifacts per 1K tokens (this pre-eng pass: ~17 artifacts).
- **UAPS** = 0.3·Quality + 0.4·Efficiency + 0.3·CostEffectiveness.
- **Instrumentation:** `.acos/metrics/agent-completions.log` (existing).

## Risks rolled up
CRITICAL fidelity-loss (mitigated: Fidelity Floor + SL-05 gate) · HIGH mis-scoping (M5) · HIGH
false-confidence (invariant #4) · MEDIUM U1 (SL-02 spike) · MEDIUM salience-decay (per-turn re-injection).

## Recommendation
Proceed to bridge → `planning/slices/`, then execute **SL-004-eden-02 (spike) first**, then Demo-1
mechanism slices, holding SL-03's injector contract until the spike verdict lands.
