# Implementation Plan — acos-hypercore-ask

> Output of `/preeng.plan`. Preconditions verified: `spec.md` ✓, `research.md` ✓,
> `research_qa_report.json.qa_status == "APPROVED"` (not REJECTED) ✓. Companion artifacts:
> `tech_prd.md`, `data-model.md`, `planning_qa_report.json`. Encodes the three-agent pattern
> (Protocol 0.1), vertical slices + demos (0.8), diagnostics (0.3), evidence governance (0.4),
> metrics (0.5), bloat management (0.6), learning capture (0.7), and orchestration constraints (0.9).

## 1. Architecture overview

`acos-hypercore-ask` is an ACOS skill (`.claude/skills/acos-hypercore-ask/`) plus Python 3 stdlib
supporting scripts (`.claude/scripts/`) and optional `general-purpose` agents (dispatched via
`Task()`, subscription-only — no new restricted `.claude/agents/` files without human approval).

**Pipeline (left to right):**

```
NL question
  -> [Intake & Tier Router]              (trivial-lookup | report/aggregation/analysis)
  -> [Hypercore Adapter (CONTRACT)]      read-only; stubbed/TODO live backend; FIXTURE backend now
        |-- (no creds) --> NO_LIVE_DATA state -> explicit "no live data" envelope (never fabricate)
  -> [Raw-Response Cache]                Tier-1 source of truth (RawApiResponse)
  -> [Normalized Answer Layer]           Tier-2 derived view (NormalizedAnswerRecord)
  -> [Blind Extraction Agents x N]       independent, no shared context (Task(), subscription-only)
  -> [Consensus Evaluator]               substance consensus; disagree -> re-dispatch -> escalate
  -> [Deterministic Gate Suite]          schema | pagination-completeness | freshness | reconciliation
                                         | unit/currency normalization | single-source cap <= 0.7
  -> [Provenance Binder]                 bind value -> endpoint+params+timestamp+JSON path; else REFUSE
  -> [Delivery Layer]                    answer envelope (value + provenance + confidence + freshness
                                         + tier) | REFUSED | ESCALATED | feed format + manifest
```

**Five architectural pillars (the distinguishing feature):**
1. **Client/adapter isolation** — the Hypercore client sits behind a stable contract; everything
   else is built/tested against fixtures now; live calls are TODO/stubbed until credentials arrive.
2. **Two-tier data model** — raw cached responses are truth; normalized layer is the derived view.
3. **Provenance-binding** — universal; no citation → refuse.
4. **Adversarial multi-model consensus** — blind agents, quorum, re-dispatch/escalate.
5. **Deterministic gate suite** — layered underneath consensus; tier-routed.

## 2. Architecture constraints (from config, locked)

- Isolate the Hypercore client behind a contract/adapter; fixtures/mocks now; live calls stubbed/TODO.
- **Read-only adapter** — no write/mutate code path against the Hypercore API (structurally enforced).
- **Two-tier data model** — raw cached truth + normalized derived view; each agent gets only its tier.
- **Non-bypassable pre-generation verification gate** between extraction and delivery.
- **Subscription-only Claude** — model work via main-thread Read or `Task()`; never `ANTHROPIC_API_KEY`.
- ACOS skill + Python 3 stdlib scripts + optional `general-purpose` agents; no new restricted agents
  without human approval.
- **Secrets via env/secret store only**; no credentials in repo; honor TLS 1.2+, AES-256, RBAC,
  MFA/SSO, SOC 2, GDPR.
- **Graceful degradation** — explicit "no live data" when credentials/API absent; never fabricate.

### Plan-time decisions (resolving spec Open Questions)
- **OQ5 — Scripting language:** **Python 3 stdlib confirmed** (consistency with existing ACOS
  scripts; no third-party deps; offline-buildable). *Decision.*
- **OQ4 — Consensus quorum N:** **2-of-3 asymmetric** default, **configurable** per tier; trivial
  lookups may run deterministic-only (consensus N=0/1 + gates); reports/aggregations require ≥2-of-3.
  *Decision (Assumption-derived, configurable).*
- **OQ3 — Freshness window:** **configurable per entity class**, default conservative (e.g.,
  servicing/balances short window, static reference data longer); concrete numeric defaults set in
  `tech_prd.md` config; **never serve stale silently**. *Decision (values configurable).*
- **OQ2 — Secret provisioning:** **env var / secret store**, read at runtime; no creds in repo;
  finalize exact store at provisioning. *Decision (Assumption).*
- **OQ1 — Hypercore API specifics:** remain `TBD` (partner-gated); all live calls stubbed behind the
  adapter; fixtures stand in. *Carried.*

## 3. Three-agent pattern mapping (Protocol 0.1)

| Role | ACOS agent | Responsibility in this plan |
|---|---|---|
| **PM (Planner/Specifier)** | architect | Defines each slice with LCE: single objective, in/out-of-scope, allowed files, steps, DoD + evidence-bundle expectations. |
| **Dev (Executor)** | developer | Implements the slice exactly within scope; produces a 7-part Evidence Bundle per slice. |
| **QA (Zero-Trust Verifier)** | qa-reviewer / security-reviewer / integration-reviewer | Assumes Dev erred; independently verifies scope, evidence authenticity, acceptance criteria + gates; can reject. |

The blind extraction/consensus agents are **`general-purpose` agents spawned via `Task()`**, distinct
from the PM/Dev/QA roles; they run with no shared context to preserve independence.

## 4. Vertical slice plan + demos (Protocol 0.8)

Each slice delivers a demo-able increment, carries PM/Dev/QA sections + `## Dev Learnings` /
`## QA Learnings`, and is not Done until learnings are updated and evidence gates pass. (Detailed
task files are authored later by `/preeng.tasks`; epics/priority below are the plan-level skeleton.)

| # | Slice (epic) | Demo | Delivers |
|---|---|---|---|
| 0 | Diagnostic + validation | **Demo 0** | Confirm symptoms/unknowns; lock Python 3 stdlib; stubbed-access ground rules |
| 1 | Skill scaffold + ACOS integration | — | Skill loader, command surface, evidence-bundle wiring |
| 2 | Hypercore client/adapter contract + fixture/mock backend | — | Read-only contract; fixtures; live backend stubbed/TODO |
| 3 | Two-tier data model + raw-response cache | — | RawApiResponse (truth) + NormalizedAnswerRecord (derived) |
| 4 | Provenance-binding engine (refuse-on-missing) | — | ProvenanceBinding; refuse path |
| 5 | Deterministic gate suite | — | schema/pagination/freshness/reconciliation/normalization/confidence-cap |
| 6 | Thin end-to-end verified-answer path | **Demo 1** | NL → stubbed client → provenance-bound value → gates → display (zero live API) + no-live-data path |
| 7 | Adversarial consensus orchestrator | **Demo 2** | Blind N agents → substance consensus → re-dispatch/escalate on a report/aggregation |
| 8 | Completeness/freshness/schema-drift hardening | — | Pagination-complete, fresh, drift-detected reports |
| 9 | Downstream trusted-input feed formats + provenance/confidence display | **Demo 3** | Verified dataset consumed by a downstream skill via feed + manifest |
| 10 | Security/PII/GDPR + secret handling + read-only enforcement hardening | — | PII scrub, env secrets, read-only structural guard |

**Demo discipline:** Demo 1 proves a *verified* answer with **zero live API**; Demo 2 proves
*consensus catches substance disagreement*; Demo 3 proves a *verified dataset is consumed as a
trusted input*. The post-access milestone (swap fixtures for the live adapter behind the unchanged
contract) is deferred until credentials arrive.

## 5. Diagnostics (Protocol 0.3)

Slice 0 is the diagnostic slice. It must confirm: hypothesis H1 (aggregation/units/currency/
truncation dominate the trust failure, not raw text fabrication) before locking gate priorities;
the Python 3 stdlib decision; and the stubbed-access ground rules. Until H1 is confirmed, gate
weighting beyond the mandatory set is marked `Assumption` and validated in Slice 8.

## 6. Evidence governance + CAGE (Protocol 0.4)

- Each slice produces an **Evidence Bundle** under `.acos/evidence/[DATE]/[SLICE-ID]/` (7 parts per
  0.1). The verification/consensus ledger and gate-result records are part of the bundle (PII-scrubbed).
- The CAGE pre-eng session trace (`cage_preeng_nodes.csv`, `cage_preeng_edges.csv`) is authored by
  `/preeng.analyze` (later invocation), including the required chain
  BLOCKER→TOOL→FINDING→DECISION→ARTIFACT→OUTCOME→PATTERN.

## 7. Agent performance metrics (Protocol 0.5)

Formulas defined (not computed): SPD, QAP = `(Delivered_Value*Quality_Score)/(1+Rejection_Count)`,
TER (artifacts/1K tokens), UAPS = `0.3*Quality + 0.4*Efficiency + 0.3*CostEffectiveness`.
**Instrumentation:** agent identity → `.acos/metrics/agent-completions.log`; skill run + verification
outcomes → `AGENT-METRICS.md` + per-slice evidence bundles.

## 8. Bloat management (Protocol 0.6)

Evidence grouped into per-slice bundles. Pre-eng artifacts categorized Active / Review (canonical-
example candidates) / Burn Pile in `analysis-report.md` (authored by `/preeng.analyze`). Nothing
deleted; only annotated.

## 9. Learning capture (Protocol 0.7)

Every task file carries `## Dev Learnings` and `## QA Learnings`; a slice is not Done until both are
updated. Agent instructions (authored by `/preeng.instructions`) state this explicitly.

## 10. Orchestration & edge constraints (Protocol 0.9)

- **Target orchestration:** the ACOS skill + agent + hook system; eventual executor is
  `/acos-execute-slice`. Slice DoD/evidence sections map to `slice.yaml` `acceptance_criteria` +
  `verification_method`.
- **Durable execution / resume:** the pipeline is checkpoint-able at each stage (raw-cached →
  extracted → consensus → gated → bound → delivered); re-running resumes from the last persisted
  Tier-1 cache rather than re-fetching. Subscription-only `Task()` dispatch for blind agents.
- **Human-in-the-loop:** PM (architect) and QA (reviewers) approval pauses gate slice progression;
  consensus ESCALATED state pauses for user decision.
- **Observability:** per-agent/slice logs/traces/metrics; consensus + gate outcomes recorded
  (PII-scrubbed) to the evidence bundle.

## 11. Risks → plan mitigations (cross-ref spec Risks)

| Risk | Plan mitigation (slice) |
|---|---|
| R1 unknown API | Adapter contract + fixtures (Slice 2); live backend stubbed |
| R2 stale data | Freshness gate + invalidation (Slice 5, hardened Slice 8) |
| R3 silent truncation | Pagination-completeness gate (Slice 5, hardened Slice 8) |
| R4 schema drift | Schema validation + drift detect (Slice 5, hardened Slice 8) |
| R5 aggregation errors | Reconciliation + normalization (Slice 5) + adversarial recompute (Slice 7) |
| R6 PII/GDPR | PII scrub + env secrets + RBAC (Slice 10) |
| R7 over-trust | Provenance + confidence display + cap ≤0.7 (Slices 4–6) |
| R8 consensus cost/instability | Tiered routing + bounded re-dispatch then escalate (Slices 1,7) |
| R9 fabricate-on-missing | Refuse-on-missing-citation (Slice 4) + no-live-data (Slice 6) |

## 12. Definition of Done (plan-level)

The plan is Done when `plan.md`, `tech_prd.md`, and `data-model.md` exist and encode: the five
architectural pillars; the read-only + subscription-only + stubbed-adapter + PII/GDPR constraints;
the two-tier data model + all subject and internal entities; the vertical-slice/demo plan; the
three-agent mapping; metrics, evidence, learning, and orchestration scaffolding — and
`planning_qa_report.json` is not REJECTED.
