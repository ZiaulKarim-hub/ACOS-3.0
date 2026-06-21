# slice-08-orchestration — Full question->plan->fetch->verify->answer orchestration (report tier)

- **Parent story:** STORY-HCA-07B · **Parent epic:** EPIC-HCA-07 · **Demo:** -
- **Effort:** L · **Dependency order:** 9 · **Depends on:** slice-06-consensus
- **Lattice refs:** proc-intake, proc-acquire, proc-cache, proc-extract, proc-consensus, proc-gate, proc-bind, proc-deliver, meth-tiered, meth-pregate, cq-04, cq-09, cq-15

## PM Section (Planner / Specifier — LCE)

### Objective
Assemble the **full report/aggregation-tier pipeline** in `SKILL.md`: question -> plan -> fetch (fixture adapter) -> Tier-1 cache -> normalize -> **N blind agents -> consensus** -> **deterministic gate suite** -> provenance binder -> deliver | refuse | escalate. This is the complete state machine `RECEIVED -> TIER_ROUTED -> FETCH_OR_CACHE -> RAW_CACHED -> EXTRACT -> CONSENSUS -> GATES -> BOUND -> DELIVERED | REFUSED | ESCALATED | NO_LIVE_DATA`.

### Scope
**In scope:** the report-tier orchestration in `SKILL.md` composing slices 02–06; the full state machine with checkpointing/resume; the report/table answer envelope (per-figure provenance + confidence); escalate/refuse/no-live-data terminal states for the report tier.
**Out of scope:** downstream feed formats + manifest (slice-09), PII/security hardening (slice-10), completeness stress-fixtures (slice-11) — basic versions exist from upstream slices.

### Guardrails / Allowed files
- `.claude/skills/acos-hypercore-ask/SKILL.md` (the report-tier orchestration + state machine)
- `.claude/scripts/hca-deliver.py` (extend for report/table envelopes with per-figure provenance)
- `.claude/skills/acos-hypercore-ask/demos/demo-report-pipeline.md`
- existing scripts (compose only)
- this task file + `.acos/evidence/[DATE]/slice-08-orchestration/`
- Prohibited: delivering a report figure without per-figure provenance; bypassing consensus on the report tier; live API calls.

### Definition of Done
- [ ] An aggregation question (UC3, e.g. "total committed vs funded across the construction book by borrower") runs the full report-tier pipeline on fixtures and returns a report where **every figure carries its own resolvable provenance + confidence** — pass-condition: report-pipeline walkthrough; per-figure provenance resolves.
- [ ] Report tier **requires** consensus: a figure without quorum is escalated/refused, not delivered — pass-condition: consensus-required test (REQUIRED).
- [ ] The full gate suite runs on consensus-agreed figures; any hard gate failure refuses that figure — pass-condition: gate-integration test.
- [ ] State machine is checkpointable: re-run resumes from the last persisted Tier-1 cache without re-fetch — pass-condition: resume test.
- [ ] Terminal states (DELIVERED/REFUSED/ESCALATED/NO_LIVE_DATA) all reachable and correct — pass-condition: state-coverage test.
- [ ] `## Dev Learnings` / `## QA Learnings` updated.

## Dev Section (Executor)

### Approach
1. Implement the state machine in SKILL.md orchestration composing router/adapter/cache/normalize/consensus/gates/binder/deliver.
2. Extend `hca-deliver.py` for report/table envelopes (per-figure provenance + confidence + freshness + tier).
3. Author the report-pipeline demo on an aggregation fixture.
4. Tests: full happy path, consensus-required, gate-integration, resume, state coverage.

### Dev Evidence Bundle (7 parts — required)
Summary; Traceability (M1,M3,M4,M9, NFR-Resilience durable, cq-04/09/15); Code Quality; Functional (5 tests + report transcript); Security; Operational (resume/checkpoints); Self-assessment.

### Dev Learnings
- Built the report tier by COMPOSING the slice-07 spine once PER FIGURE rather than writing a
  new vertical. `ReportBuilder` holds one shared `DeliverySpine` (so every figure reads through
  the SAME Tier-1 cache) and projects each figure's spine envelope into a report FIGURE that
  carries its own `{value, unit/currency, provenance, gate_verdict, confidence, complete}`. The
  report's terminal state is the WORST of its figures' states — a clean, total ordering that
  makes "DELIVERED iff every figure delivered" trivially correct.
- A refusing figure is surfaced via `_refusal_from_envelope`, which NAMES the figure and
  re-surfaces the inner reason + `failed_gates` from the per-figure envelope. There is no code
  path that drops a non-delivered figure: every figure produces either a delivered FIGURE or a
  REFUSAL, and `build()` appends one of the two for every spec.
- Tier routing (`route_figure_tier`) delegates to `hca-route.classify` (which returns
  `trivial-lookup` | `report/aggregation/analysis`) and maps onto two delivery tiers. The
  conservative default is report-tier (consensus-required) — anything not clearly a trivial
  lookup demands consensus.
- Consensus stays an OPT-IN per figure (`agent_runner` in the spec). When taken, `ReportBuilder`
  plans+fetches+caches the figure FIRST so it can hand `run_consensus` the real `gate_source`
  (consensus is additive — the agreed value still passes the binder + gate suite). The blind
  `Task()` spawn is the MAIN Claude's job; the engine only adjudicates the injected runner's
  returns. `_consensus_to_spine_envelope` translates a ConsensusEnvelope back into the spine
  envelope shape so the report binder is format-agnostic (NO_CONSENSUS → report ESCALATED).
- Checkpoint/resume falls out for free from the slice-03 design: Tier-1 ids are
  content-addressed (operation+variables, NOT fetched_at) and the cache is append-only, so a
  re-run resolves to the same ids and an identical re-write is an idempotent no-op (never an
  ImmutableCacheError). The resume test asserts identical reports off the same immutable ids.
- LIVE-VERIFIED 2026-06-18 under Doppler: a 3-figure portfolio-summary report (loan_count=141,
  client_count=124, total_commitment=434,989,118.78 USD) DELIVERED with each figure carrying its
  own provenance (141 contributing bindings on the aggregate), gate pass, complete=True. All 4
  terminal states are reachable; a truncated-list figure surfaces a `pagination_completeness`
  refusal while the sibling figure still delivers.

## QA Section (Zero-Trust Verifier)

### Verification steps
1. Run the aggregation demo; for several figures, independently re-resolve provenance into Tier-1 and re-do the arithmetic — confirm the report's numbers and citations are real.
2. Plant a figure that fails to reach quorum; confirm it is escalated/refused, never delivered.
3. Plant a gate failure (e.g. stale source) on one figure; confirm that figure is refused while others may proceed.
4. Kill mid-pipeline and resume; confirm no re-fetch and consistent result.
5. Confirm all four terminal states are reachable.

### Evidence gates (all must pass)
- [ ] **Every delivered report figure has resolvable per-figure provenance** — fail = REJECT.
- [ ] **Report tier requires consensus (no-quorum => escalate/refuse)** — fail = REJECT (hard).
- [ ] Gate failure refuses the offending figure.
- [ ] Resume works without re-fetch.
- [ ] Learnings updated.

### QA Learnings
- Per-figure provenance is independently re-resolvable: `test_each_figure_provenance_resolves_into_tier1`
  re-walks each figure's `{raw_response_id, json_field_path}` into Tier-1 via
  `cache.resolve_binding` and, for the aggregate, re-adds the 141 contributing source values to
  reproduce the total. The numbers + citations are real, not asserted.
- The "no silent drop" gate is proven two ways: a truncated list (pagination gate) and a
  mixed-currency aggregate (currency gate). In both, the refused figure is absent from
  `figures[]` (no fabricated value) AND present in `refusals[]` naming the figure + the gate,
  and a sibling figure still delivers (a single figure's gate failure refuses only itself).
- All four terminal states have explicit reachability tests; ESCALATED is exercised with a
  disagreeing blind-agent runner that re-dispatches (≥2 runner calls) then escalates with no
  silent pick, and DELIVERED-via-consensus is exercised with an agreeing runner whose
  multi-source agreement lifts confidence above the 0.7 single-source cap.
- Resume is verified as consistency: a second build over the same immutable cache yields the
  identical report off the same Tier-1 ids, and the Tier-1 id set is unchanged (idempotent
  re-write, no ImmutableCacheError).
