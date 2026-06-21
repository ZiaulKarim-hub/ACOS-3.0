# slice-06-swarm-synthesizer — Embedded blind swarm + between-rounds synthesizer

- **Parent story:** STORY-APS-06 · **Parent epic:** EPIC-APS-06 · **Demo:** Demo 2
- **Effort:** L · **Dependency order:** 7 · **Depends on:** slice-05-channels-arcgis-assessor-recorder
- **Lattice refs:** cq-10, cq-11, meth-blindswarm, meth-corroboration, meth-synthesizer, meth-conflictpreserve, proc-loop, term-verified, anti-harmonize, ent-roundsynth, metric-corrob, metric-prunect

## PM Section (Planner / Specifier — LCE)

### Objective
Implement the embedded **blind isolated swarm** + the **between-rounds synthesizer**. `swarm_dispatch.py`
builds the **channel × jurisdiction × entity** agent matrix for a round; each agent runs **isolated/blind**
(no shared context), dispatched **subscription-only via `Task()`**, and writes
`workspace/<sid>/round-NN/agent-NN/findings.md`. `synthesize_round.py` cross-references findings →
confidence (**Verified = 2+ INDEPENDENT isolated agents**), **PRESERVES conflicts** as manual-review flags
(never harmonize), **hub-prunes + enforces the hop limit** (it holds the stop-list + hop counter), and
emits next-round seeds; the loop stops when a round yields **no new high-confidence nodes**.

### Scope
**In scope:** `scripts/swarm_dispatch.py` (round agent matrix; isolation contract; `Task()` dispatch
plan); `scripts/synthesize_round.py` (cross-ref/confidence; conflict preservation; hub-prune + hop-limit;
next-seed emission; loop-stop signal).
**Out of scope:** dedup (slice-08); scoring (slice-09); the full SKILL.md wiring (slice-07).

### Guardrails / Allowed files
- `.claude/skills/acos-property-search/scripts/swarm_dispatch.py` (stdlib only)
- `.claude/skills/acos-property-search/scripts/synthesize_round.py` (stdlib only)
- `.claude/skills/acos-property-search/scripts/tests/test_synthesize_round.py`
- this task file + `.acos/evidence/[DATE]/slice-06-swarm-synthesizer/`
- Prohibited: any `ANTHROPIC_API_KEY` / direct model API call (subscription-only via `Task()`); letting
  agents share context (breaks corroboration); silently harmonizing conflicts; expanding past the hop limit.

### Definition of Done
- [ ] Two INDEPENDENT isolated agents landing on the same parcel mark it Verified; a single agent does not — pass-condition: **corroboration test (REQUIRED)**.
- [ ] Conflicting owner names are PRESERVED as a manual-review flag, never harmonized — pass-condition: **conflict-preservation test (REQUIRED; a silent merge = REJECT)**.
- [ ] The synthesizer hub-prunes + enforces the hop limit before seeding the next round; prunes logged — pass-condition: prune/hop test.
- [ ] The loop stops when a round yields no new high-confidence nodes — pass-condition: loop-termination test.
- [ ] Agents are isolated (no shared context) and dispatched subscription-only via Task() — pass-condition: **isolation + no-API-key test (REQUIRED)**.
- [ ] `## Dev Learnings` / `## QA Learnings` updated.

## Dev Section (Executor)

### Approach
1. `swarm_dispatch.py`: from the worklist, build the channel×jurisdiction×entity matrix; specify the
   per-agent isolation contract + `Task()` dispatch plan (no API key).
2. `synthesize_round.py`: cross-reference `findings.md` outputs; mark Verified at ≥2 independent agents;
   collect conflicts into review flags; hub-prune + hop-limit; emit next seeds; return
   `new_high_confidence_count` (0 => stop).
3. Tests: corroboration, conflict preservation, prune/hop, loop termination, isolation + no-API-key.

### Dev Evidence Bundle (7 parts — required)
Summary; Traceability (meth-blindswarm/corroboration/synthesizer/conflictpreserve, term-verified,
anti-harmonize, EV-010/011, metric-corrob); Quality (stdlib); Functional (the five DoD tests); Security
(subscription-only; no key); Operational (round artifacts = observability/resumability); Self-assessment.

### Dev Learnings
- (fill at execution) How isolation is enforced; how loop termination is detected deterministically.

## QA Section (Zero-Trust Verifier)

### Verification steps
1. Re-author a conflicting-owner fixture; confirm BOTH names survive as a review flag — any silent merge = REJECT.
2. Re-author one-agent vs. two-independent-agents fixtures; confirm Verified only at 2+ independent.
3. Grep the swarm scripts for `ANTHROPIC_API_KEY` / direct model HTTP — must find none.
4. Confirm agents cannot see each other's findings (isolation) and the loop halts at no-new-nodes.

### Evidence gates (all must pass)
- [ ] **Corroboration requires 2+ independent isolated agents** (hard; fail = REJECT).
- [ ] **Conflicts preserved, never harmonized** (hard; fail = REJECT).
- [ ] **Isolation + subscription-only (no API key)** (hard; fail = REJECT).
- [ ] Hub-prune + hop-limit + loop termination hold.
- [ ] Learnings updated.

### QA Learnings
- (fill at execution) Any cross-leak between agents or silent harmonization.
