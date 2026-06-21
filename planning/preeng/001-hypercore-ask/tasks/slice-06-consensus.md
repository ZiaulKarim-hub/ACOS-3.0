# slice-06-consensus — Adversarial multi-model consensus orchestrator (Demo 2)

- **Parent story:** STORY-HCA-06 · **Parent epic:** EPIC-HCA-06 · **Demo:** Demo 2
- **Effort:** L · **Dependency order:** 8 · **Depends on:** slice-07-e2e-thin
- **Lattice refs:** proc-extract, proc-consensus, meth-consensus, ent-consensus, pat-blindredispatch, anti-singletrust, term-substance, meth-subonly, metric-consensus, cq-04, cq-05

## PM Section (Planner / Specifier — LCE)

### Objective
Implement the blind adversarial-consensus engine: dispatch **N blind `general-purpose` agents via `Task()`** (subscription-only — never `ANTHROPIC_API_KEY`), each given only its scoped Tier-1 slice + the question, **no shared context, no sight of each other's output**. Deliver only on **substance consensus** (agreement on the normalized number/name/date) at the configured quorum; disagreement => bounded blind re-dispatch => still no quorum => **ESCALATE**. Never a silent pick. This is **Demo 2**.

### Scope
**In scope:** `hca-consensus.py` (dispatch protocol spec + result aggregation producing a `ConsensusResult`); substance-equality comparison after normalization; quorum evaluation (default 2-of-3 asymmetric from config); bounded re-dispatch (default 1 retry); ESCALATE state; single-source cap interplay with the gate suite.
**Out of scope:** the gate suite itself (slice-05), full report orchestration (slice-08), delivery rendering beyond escalate envelope.

> Dispatch note: the actual blind agents are spawned by the orchestrating skill/architect via `Task()` (subscription-only). `hca-consensus.py` defines the request envelope per agent, collects their structured returns, and computes consensus — it does NOT itself call any model API.

### Guardrails / Allowed files
- `.claude/scripts/hca-consensus.py` (consensus math + dispatch envelope spec; stdlib only; **no model API call**)
- `.claude/skills/acos-hypercore-ask/prompts/blind-extractor.md` (the blind-agent prompt: scoped slice + question + structured-return contract; explicitly no shared context)
- `.claude/skills/acos-hypercore-ask/SKILL.md` (add the consensus dispatch step for the report tier)
- `.claude/skills/acos-hypercore-ask/demos/demo2-consensus.md` (Demo 2 walkthrough)
- tests: `.claude/scripts/tests/test_hca_consensus.py`
- this task file + `.acos/evidence/[DATE]/slice-06-consensus/`
- Prohibited: `ANTHROPIC_API_KEY` or any direct model API call in scripts; sharing agent outputs between blind agents; silently picking a winner on disagreement.

### Definition of Done
- [ ] N blind agents each receive ONLY their scoped Tier-1 slice + the question; **no shared context** (the prompt + dispatch envelope enforce this) — pass-condition: prompt review + envelope test.
- [ ] **Substance consensus** computed on normalized values (not prose); quorum from config (default 2-of-3) — pass-condition: consensus reached when ≥quorum agree on substance; test.
- [ ] Disagreement triggers **bounded blind re-dispatch** (fresh agents, default 1 retry); still no quorum => `agreement_status == escalated` — pass-condition: re-dispatch + escalate test (REQUIRED).
- [ ] Single-source / single-response values are flagged and confidence-capped ≤ 0.7 (interplay with slice-05) — pass-condition: cap test.
- [ ] No silent pick ever: on disagreement the engine NEVER returns an `agreed_value` without quorum — pass-condition: no-silent-pick test (REQUIRED).
- [ ] Subscription-only: scripts contain no `ANTHROPIC_API_KEY` / direct API call — pass-condition: grep gate.
- [ ] `## Dev Learnings` / `## QA Learnings` updated.

## Dev Section (Executor)

### Approach
1. Define the per-agent request envelope (scoped slice + question + return schema `{value, json_field_path, raw_response_id, agent_confidence}`).
2. Author `blind-extractor.md` enforcing independence + structured return.
3. `hca-consensus.py`: normalize each agent value, group by substance, evaluate quorum; on miss, emit a re-dispatch directive (bounded), then ESCALATE.
4. Wire SKILL.md to spawn N agents via `Task()` for the report tier, collect returns, call consensus.
5. Tests using simulated agent returns (agreement, disagreement->redispatch->consensus, disagreement->escalate, single-source).

### Dev Evidence Bundle (7 parts — required)
Summary; Traceability (M3 consensus, M10 subscription-only, metric-consensus, pat-blindredispatch, term-substance, cq-04/05); Code Quality; Functional (4 simulated-return tests); Security (no API key; independence preserved); Operational (bounded retries); Self-assessment.

### Dev Learnings
- **A Python script cannot spawn `Task()` agents — split dispatch from adjudication.** The
  engine (`hca-consensus.py`) is pure Python and takes an INJECTED `agent_runner(question, n)`
  callable; the main Claude (the only context with `Task`) does the blind spawn. This made the
  whole engine unit-testable with simulated runners AND kept it subscription-only by
  construction (no model call lives in the script at all).
- **Blind re-dispatch is enforced STRUCTURALLY, not by discipline.** The engine re-calls
  `agent_runner(question, n)` with identical args on disagreement; there is no parameter
  through which prior-round info could pass. The test asserts `runner.calls[0] ==
  runner.calls[1]` and also that a strict 2-arg runner works end-to-end — so feedback cannot
  leak even by accident.
- **Substance ≠ prose needed three group rules.** Numbers agree by tolerant numeric match
  (relative `1e-9` OR absolute floor `1e-9`) AND parse out of prose like `"$5,000,000.00"`;
  text by case-folded whitespace-collapsed equality; lists by order-free set membership. A
  `None`/unextractable value gets a sentinel key that never agrees with anything (so it can
  never reach quorum).
- **Consensus is ADDITIVE — reuse, don't re-implement, the binder + gates.** An agreed value
  still runs through `bind_and_verify`/`bind_aggregate` (slice-04) and `GateSuite.run_all`
  (slice-05). I pass `provenance_report={"ok": True}` into the gate suite because provenance
  is verified separately first, so the suite's own provenance check doesn't double-refuse.
- **Confidence is driven by `agreeing_count`, not `n`.** Feeding `source_count=agreeing_count`
  into `confidence_record` means a 1-of-1 path is capped at `<= 0.7` and flagged single-source,
  while a 2/3+ agreement lifts above the cap — the single-source cap interplay (slice-05)
  falls out for free.
- **Grep-gate gotcha:** even a DOCUMENTATION mention of the literal `ANTHROPIC_API_KEY`
  inside the engine trips a strict subscription-only grep gate. Reworded the engine's
  docstring/CLI to "direct model-API key / env secret" so the literal appears ONLY in the
  test that asserts its absence.
- Quorum is ASYMMETRIC: `parse_quorum("2-of-3", n)` returns the threshold `2` and clamps to
  `[1, n]`; 2 agreeing agents deliver regardless of how many returned, and a lone agent never
  constitutes consensus.

## QA Section (Zero-Trust Verifier)

### Verification steps
1. Inspect the blind-agent prompt + dispatch envelope: confirm an agent CANNOT see another agent's output and gets only a scoped slice. Any cross-leak = REJECT.
2. Feed simulated agent returns that disagree; confirm the engine re-dispatches (bounded) and, if still split, returns `escalated` with `agreed_value == null` — confirm **no silent pick**.
3. Feed exactly quorum agreement on substance (different prose, same number); confirm consensus.
4. Grep all scripts for `ANTHROPIC_API_KEY` and direct HTTP-to-model calls — must find none (subscription-only).
5. Confirm single-source path caps confidence ≤ 0.7.

### Evidence gates (all must pass)
- [ ] **No-silent-pick on disagreement (escalate with null agreed_value)** — fail = REJECT (hard).
- [ ] **Blind independence enforced (no shared context / scoped slice only)** — fail = REJECT.
- [ ] Substance (not prose) consensus.
- [ ] **No ANTHROPIC_API_KEY / direct model API call** — fail = REJECT.
- [ ] Single-source cap ≤ 0.7.
- [ ] Learnings updated.

### QA Learnings
- **No-silent-pick (hard gate) is best proven with a NO-budget plurality test.** The
  `test_plurality_below_quorum_never_wins` case gives 1/1/1 with `max_redispatch=0`: group[0]
  IS a plurality of 1, and the engine STILL escalates with `value == null` and exactly one
  dispatch. That pins the invariant that "largest group wins" is NOT the rule — quorum is.
- **Blind independence has two complementary checks.** (1) Behavioral: across a split→
  re-dispatch run, assert `runner.calls[0] == runner.calls[1]` (identical `(question, n)`).
  (2) Structural: a runner declared with exactly `(question, n)` and no `**kwargs` works
  end-to-end — if the engine ever tried to pass feedback it would `TypeError`.
- **Verify substance consensus directly, not only via delivery.** `group_by_substance([5000000.0,
  "$5,000,000.00", "5000000", 4200000.0])` must yield a 3-count group + a 1-count outlier.
  Testing the primitive separately catches prose/number normalization regressions that an
  end-to-end test could mask.
- **Additive verification needs TWO negative tests.** (d) agreement + truncated `gate_source`
  → `GATE_FAIL` naming `pagination_completeness`; (e) agreement on a value that does NOT match
  the cited Tier-1 path → `PROVENANCE_REFUSED`. Both must show `value == null` — consensus
  agreement never bypasses the binder/gates.
- **Subscription-only grep gate must target the ENGINE source, not the test.** The
  subscription-only test reads `hca-consensus.py` and asserts the literal `ANTHROPIC_API_KEY`
  and direct model HTTP/SDK imports are absent; the literal legitimately appears in the test
  file (in the assertion itself). QA greps the engine, not the test.
- All 14 new consensus tests + the 186 pre-existing tests pass (200 total) — no regression.
