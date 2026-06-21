# Demo 2 — Adversarial multi-model consensus (SLICE-HCA-06)

The second demo-able vertical of `acos-hypercore-ask`: a report / aggregation / high-stakes
question is answered by **N blind, independent agents** and delivered ONLY when `>= quorum`
of them agree on the **substance** of the answer — otherwise a bounded **blind re-dispatch**,
then an **ESCALATE** that is a structured refusal. **Never a silent pick.** This WRAPS the
deterministic spine (Demo 1) — it does not replace it.

Engine: `.claude/scripts/hca-consensus.py` (`run_consensus(...)`).
Blind-agent prompt: `prompts/blind-extractor.md`. Orchestration: `SKILL.md` →
"Adversarial consensus orchestration".

## The wrap (left → right)

```
NL question (report / aggregation / high-stakes)
  -> [plan + scope]   hca-deliver.plan_question + TwoTierCache.minimal_slice(rid, fields)
                        one PII-minimized scoped Tier-1 slice; the SAME slice + SAME question
                        go to every agent in a round.
  -> [dispatch x N]   N = config consensus.agent_count (3) BLIND general-purpose Task() agents
                        (subscription-only). IDENTICAL prompt (prompts/blind-extractor.md).
                        No shared context, no sight of peers, no prior-round feedback.
  -> [consensus]      hca-consensus.run_consensus(question, agent_runner, ...)
                        normalize each value -> substance key; group; the largest agreeing
                        group >= quorum (config 2-of-3, ASYMMETRIC: 2 agreeing deliver) => agreed.
  -> [re-dispatch]    < quorum => bounded BLIND re-dispatch (config redispatch_retries = 1):
                        agent_runner is re-called with IDENTICAL args — no feedback can reach
                        the agents. Still split => ESCALATE.
  -> [bind + gates]   an agreed value STILL passes the non-bypassable provenance binder
                        (bind_and_verify / bind_aggregate) + the deterministic gate suite
                        (when a gate_source is supplied). A failure => REFUSE (pass-through).
  -> [confidence]     confidence_record(source_count = agreeing_count): >= 2 agreeing lifts
                        above the single-source 0.7 cap; a lone source is capped + flagged.
  -> [envelope]       { state ∈ {DELIVERED, REFUSED}, answer, value, agreeing_count, quorum,
                        n, provenance, gate_verdict, confidence, redispatches,
                        disagreement:{values_seen, spread, distinct_groups}, refusals[] }
```

### No silent pick (the headline guarantee)
On unresolved disagreement the engine ESCALATES with `state == REFUSED`,
`reason_code == NO_CONSENSUS`, `value == null`, and `agreeing_count < quorum`. It never
returns a plurality / first / most-confident answer. Escalation IS a structured refusal.

### Additive verification (consensus never bypasses the binder/gates)
Agreement is necessary but not sufficient. An agreed value is re-bound to Tier-1 and
gate-checked exactly like the spine's single-path value. Unanimous agents agreeing on a
number that does not match its cited Tier-1 path are REFUSED (`PROVENANCE_REFUSED`); an agreed
count over a truncated page is REFUSED (`GATE_FAIL`, naming `pagination_completeness`).

## Worked scenarios (the simulated-runner tests prove each)

| # | Agent returns | Outcome | Why |
|---|---|---|---|
| a | 3/3 agree on 5,000,000 (different prose: `5000000.0`, `"$5,000,000.00"`, `"5000000"`) | **DELIVERED**, `agreeing_count=3`, confidence > 0.7 | substance consensus; 3 sources lift above the single-source cap |
| b | 2 agree on 5,000,000, 1 dissents (4,200,000) | **DELIVERED** at quorum 2-of-3 | the dissenter is recorded in `disagreement` but loses |
| c | 1/1/1 all differ, then re-dispatch still 1/1/1 | **REFUSED** `NO_CONSENSUS`, `value=null`, `redispatches=1` | bounded blind re-dispatch then ESCALATE — no silent pick |
| c′ | round 0 splits, re-dispatch 2/3 agree | **DELIVERED** at quorum, `redispatches=1` | a fresh blind cohort reached consensus |
| d | 2 agree on count=3 but the list is truncated (fetched 2 < reported 3) | **REFUSED** `GATE_FAIL` (`pagination_completeness`) | agreed but a hard gate fails — never deliver a number |
| e | 2 agree on 9,999,999 but Tier-1 commitment is 5,000,000 at the cited path | **REFUSED** `PROVENANCE_REFUSED` | agreed but unbindable — the binder is non-bypassable |
| f | split → re-dispatch | runner received the **identical** `(question, n)` both rounds | re-dispatch is structurally blind (no feedback channel) |

## How the orchestrator drives it (subscription-only)

```python
# main Claude conversation (the only context with Task()) — pseudo-code
def agent_runner(question, n):
    # spawn N BLIND general-purpose Task() agents IN PARALLEL with the IDENTICAL
    # prompts/blind-extractor.md prompt (same question + same scoped slice). Subscription-only
    # — NO model-API key. Collect each agent's strict-JSON return.
    return [task_spawn_blind_extractor(question, scoped_slice) for _ in range(n)]

env = run_consensus(question, agent_runner,
                    quorum=None,             # config default 2-of-3
                    n=None,                  # config agent_count 3
                    max_redispatch=None,     # config redispatch_retries 1
                    binder=ProvenanceEngine(cache=cache),
                    gate_suite=GateSuite(now=now),
                    gate_source=tier1_raw,   # the cached Tier-1 the gates inspect
                    entity_type="loan")
# env["state"] is DELIVERED (value bound + gated) or REFUSED (NO_CONSENSUS / GATE_FAIL /
# PROVENANCE_REFUSED). The orchestrator renders the envelope; it NEVER invents a value.
```

The engine itself spawns nothing and makes no model call — it only adjudicates the returns
the injected `agent_runner` provides. That separation is what makes the consensus logic fully
unit-testable (the tests inject simulated runners) AND keeps the engine subscription-only.

## Run the tests

```bash
python3 -m unittest discover -s .claude/scripts/tests -p 'test_hca_*.py' -v
# or just the consensus module:
cd .claude/scripts/tests && python3 -m unittest test_hca_consensus -v
```
