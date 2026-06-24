#!/usr/bin/env python3
"""test_hca_consensus.py — stdlib unittest for the adversarial consensus engine (SLICE-HCA-06).

Proves Demo 2 with SIMULATED agent_runners (no real agents, no network, no model call): the
engine adjudicates N blind agent returns into a verified consensus answer — or a structured
refusal — and NEVER silently picks a winner.

Required scenarios (slice acceptance):
  (a) 3/3 agree (different prose, same number)   -> DELIVERED; confidence reflects 3 sources.
  (b) 2/3 agree                                  -> DELIVERED at quorum (2-of-3).
  (c) 1/1/1 all differ                           -> bounded blind re-dispatch -> NO_CONSENSUS.
  (d) agree but a deterministic gate FAILS       -> REFUSED (GATE_FAIL); no value.
  (e) agree but the value is UNBINDABLE          -> REFUSED (PROVENANCE_REFUSED); no value.
  (f) re-dispatch is BLIND                        -> agent_runner gets NO prior-round feedback.

Plus hard-guarantee guards:
  - NO SILENT PICK: a sub-quorum split returns value == None, agreeing_count < quorum.
  - SUBSTANCE not prose: "$5,000,000.00" / "5000000" / "five million? no — 5000000" agree.
  - SINGLE-SOURCE CAP: a 1-of-1 agreement caps confidence <= 0.7 and flags single_source.
  - MULTI-SOURCE LIFT: a 2/3+ agreement is NOT capped by the single-source rule.
  - SUBSCRIPTION-ONLY: the engine source contains no ANTHROPIC_API_KEY / model API call.

Run:
  python3 -m unittest discover -s .claude/scripts/tests -p 'test_hca_*.py' -v
"""

import importlib.util
import os
import tempfile
import unittest


_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS_DIR = os.path.abspath(os.path.join(_THIS_DIR, os.pardir))


def _load(modname, filename):
    import sys
    cached = sys.modules.get(modname)
    if cached is not None:
        return cached
    path = os.path.join(_SCRIPTS_DIR, filename)
    spec = importlib.util.spec_from_file_location(modname, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[modname] = mod
    spec.loader.exec_module(mod)
    return mod


cache_mod = _load("hca_cache", "hca-cache.py")
adapter_mod = _load("hca_adapter", "hca-adapter.py")
prov_mod = _load("hca_provenance", "hca-provenance.py")
gates_mod = _load("hca_gates", "hca-gates.py")
consensus_mod = _load("hca_consensus", "hca-consensus.py")


# ===========================================================================
# Simulated agent_runners (INJECTED — no real agents, no model call).
# ===========================================================================

class _ScriptedRunner:
    """An agent_runner that yields a pre-scripted list of returns per round.

    `rounds` is a list of round-result-lists. Each call returns the next round's list (the
    last round repeats if called again). CRUCIALLY, the runner RECORDS every call's args so a
    test can ASSERT that re-dispatch passed NO prior-round feedback — `__call__` accepts ONLY
    (question, n); there is no channel for feedback and we prove it stays that way.
    """

    def __init__(self, rounds):
        self.rounds = rounds
        self.calls = []  # list of (question, n) tuples — exactly what the engine passed

    def __call__(self, question, n):
        self.calls.append((question, n))
        idx = min(len(self.calls) - 1, len(self.rounds) - 1)
        return self.rounds[idx]


def _envelope_return(value, rid, path, *, agent_confidence=0.9):
    """A blind-extractor-style structured return {value, json_field_path, raw_response_id,
    agent_confidence}."""
    return {"value": value, "json_field_path": path, "raw_response_id": rid,
            "agent_confidence": agent_confidence}


def _deliver_envelope_return(value, rid, path, *, confidence=0.9):
    """An hca-deliver-style envelope return (values[0].value + values[0].provenance)."""
    return {
        "state": "DELIVERED",
        "answer": f"the value is {value}",
        "values": [{"value": value,
                    "provenance": {"raw_response_id": rid, "json_field_path": path},
                    "confidence": confidence}],
    }


# ===========================================================================
# A Tier-1 cache seeded so that agreeing values BIND (binder is non-bypassable).
# ===========================================================================

class _ConsensusTestBase(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="hca-consensus-test-")
        self.cache = cache_mod.TwoTierCache(cache_dir=self.tmpdir)
        # Seed Tier-1 with a record whose commitment == 5000000 at a known path.
        raw = adapter_mod.make_raw_api_response(
            raw_response_id="r:loan:L-1",
            endpoint="https://api.hypercore.ai/graphql",
            request_params={"graphql_operation": "HCAGetLoan"},
            timestamp="2026-06-18T08:00:00Z", http_status=200, cursor=None,
            reported_total=None,
            body={"record": {"id": "L-1", "commitment": 5000000.0, "currency": "USD"},
                  "provenance": {"fetched_at": "2026-06-18T08:00:00Z"}},
            backend="fixture")
        self.rid = self.cache.put_raw(raw)
        self.path = "$.body.record.commitment"
        self.binder = prov_mod.ProvenanceEngine(cache=self.cache)

    def _binding_returns(self, value):
        """A return whose binding resolves to the seeded Tier-1 commitment (5000000)."""
        return _envelope_return(value, self.rid, self.path)


# ===========================================================================
# (a) 3/3 agree -> DELIVERED with confidence reflecting 3 sources
# ===========================================================================

class ThreeOfThreeTest(_ConsensusTestBase):
    def test_unanimous_agreement_delivers_with_three_source_confidence(self):
        # Same SUBSTANCE (5000000), DIFFERENT prose per agent (proves substance-not-prose).
        runner = _ScriptedRunner([[
            self._binding_returns(5000000.0),
            self._binding_returns("$5,000,000.00"),
            self._binding_returns("5000000"),
        ]])
        env = consensus_mod.run_consensus(
            "what is the commitment of loan L-1?", runner,
            quorum="2-of-3", n=3, binder=self.binder)
        self.assertEqual(env["state"], consensus_mod.STATE_DELIVERED)
        self.assertEqual(env["agreeing_count"], 3)
        self.assertEqual(env["n"], 3)
        self.assertEqual(env["quorum"], 2)
        self.assertEqual(env["redispatches"], 0)              # agreed on the first round
        self.assertIsNotNone(env["value"])
        # confidence reflects THREE agreeing sources -> NOT single-source, NOT capped at 0.7.
        self.assertEqual(env["confidence"]["source_count"], 3)
        self.assertFalse(env["confidence"]["single_source"])
        self.assertGreater(env["confidence"]["confidence"], 0.7)
        # delivered value is still provenance-bound (non-bypassable).
        self.assertIsNotNone(env["provenance"]["raw_response_id"])
        self.assertEqual(env["refusals"], [])


# ===========================================================================
# (b) 2/3 agree -> DELIVERED at quorum
# ===========================================================================

class TwoOfThreeTest(_ConsensusTestBase):
    def test_quorum_met_with_two_of_three_delivers(self):
        # Two agree on 5000000, one dissents with 4200000 (no Tier-1 path needed; it loses).
        runner = _ScriptedRunner([[
            self._binding_returns(5000000.0),
            self._binding_returns("5,000,000"),
            _envelope_return(4200000.0, "r:other", "$.body.record.commitment"),
        ]])
        env = consensus_mod.run_consensus(
            "what is the commitment of loan L-1?", runner,
            quorum="2-of-3", n=3, binder=self.binder)
        self.assertEqual(env["state"], consensus_mod.STATE_DELIVERED)
        self.assertEqual(env["agreeing_count"], 2)
        self.assertEqual(env["quorum"], 2)
        self.assertEqual(env["redispatches"], 0)
        # multi-source (2) -> not single-source capped
        self.assertFalse(env["confidence"]["single_source"])
        self.assertEqual(env["confidence"]["source_count"], 2)
        # the dissenter is recorded in the disagreement summary but did NOT win
        self.assertGreaterEqual(env["disagreement"]["distinct_groups"], 2)


# ===========================================================================
# (c) 1/1/1 all differ -> re-dispatch then NO_CONSENSUS refusal (no silent pick)
# ===========================================================================

class AllDifferEscalateTest(_ConsensusTestBase):
    def test_all_differ_redispatches_then_escalates_no_silent_pick(self):
        # Round 0: three DIFFERENT substances. Round 1 (re-dispatch): still three different.
        round0 = [
            self._binding_returns(5000000.0),
            _envelope_return(4200000.0, "r:b", "$.x"),
            _envelope_return(6100000.0, "r:c", "$.y"),
        ]
        round1 = [
            self._binding_returns(5050000.0),
            _envelope_return(4250000.0, "r:b2", "$.x"),
            _envelope_return(6150000.0, "r:c2", "$.y"),
        ]
        runner = _ScriptedRunner([round0, round1])
        env = consensus_mod.run_consensus(
            "what is the commitment of loan L-1?", runner,
            quorum="2-of-3", n=3, max_redispatch=1, binder=self.binder)
        # ESCALATE == structured REFUSAL, NEVER a silent pick.
        self.assertEqual(env["state"], consensus_mod.STATE_REFUSED)
        self.assertEqual(env["refusals"][0]["reason_code"], consensus_mod.REASON_NO_CONSENSUS)
        # NO SILENT PICK: value is None and agreeing_count is below quorum.
        self.assertIsNone(env["value"])
        self.assertLess(env["agreeing_count"], env["quorum"])
        # bounded re-dispatch happened exactly once (round 0 + 1 retry = 2 dispatches).
        self.assertEqual(len(runner.calls), 2)
        self.assertEqual(env["redispatches"], 1)
        self.assertTrue(env["meta"].get("escalated"))

    def test_disagreement_then_consensus_on_redispatch_delivers(self):
        # Round 0: split. Round 1 (fresh blind cohort): 2-of-3 now agree -> DELIVERED.
        round0 = [
            self._binding_returns(5000000.0),
            _envelope_return(4200000.0, "r:b", "$.x"),
            _envelope_return(6100000.0, "r:c", "$.y"),
        ]
        round1 = [
            self._binding_returns(5000000.0),
            self._binding_returns("5,000,000.00"),
            _envelope_return(6100000.0, "r:c2", "$.y"),
        ]
        runner = _ScriptedRunner([round0, round1])
        env = consensus_mod.run_consensus(
            "what is the commitment of loan L-1?", runner,
            quorum="2-of-3", n=3, max_redispatch=1, binder=self.binder)
        self.assertEqual(env["state"], consensus_mod.STATE_DELIVERED)
        self.assertEqual(env["agreeing_count"], 2)
        self.assertEqual(env["redispatches"], 1)             # delivered on the re-dispatch
        self.assertEqual(len(runner.calls), 2)


# ===========================================================================
# (d) agree but a deterministic gate FAILS -> REFUSED (GATE_FAIL); no value
# ===========================================================================

class AgreeButGateFailsTest(_ConsensusTestBase):
    def test_agreement_but_pagination_gate_fail_refuses(self):
        # The cohort agrees on the count, but the gate_source is a TRUNCATED list
        # (fetched < reported_total) -> the pagination gate FAILS -> consensus REFUSES.
        truncated = adapter_mod.make_raw_api_response(
            raw_response_id="r:list:trunc",
            endpoint="https://api.hypercore.ai/graphql",
            request_params={"graphql_operation": "HCAListPaginatedLoans"},
            timestamp="2026-06-18T08:00:00Z", http_status=200, cursor=None, reported_total=3,
            body={"data": [{"id": "L-1", "commitment": 1.0, "currency": "USD"},
                           {"id": "L-2", "commitment": 2.0, "currency": "USD"}],
                  "reported_total": 3, "fetched": 2, "complete": False, "pages": 1,
                  "provenance": {"fetched_at": "2026-06-18T08:00:00Z"}},
            backend="fixture")
        trid = self.cache.put_raw(truncated)
        # agents agree the count is 3 (reported_total path), but the gate sees truncation.
        runner = _ScriptedRunner([[
            _envelope_return(3, trid, "$.body.reported_total"),
            _envelope_return("3", trid, "$.body.reported_total"),
        ]])
        import datetime
        now = datetime.datetime(2026, 6, 18, 9, 0, 0, tzinfo=datetime.timezone.utc)
        env = consensus_mod.run_consensus(
            "how many loans are there?", runner, quorum="2-of-3", n=2, binder=self.binder,
            entity_type="loan", gate_source=self.cache.get_raw(trid),
            gate_suite=gates_mod.GateSuite(now=now), gate_mode="run_all")
        self.assertEqual(env["state"], consensus_mod.STATE_REFUSED)
        self.assertEqual(env["refusals"][0]["reason_code"], consensus_mod.REASON_GATE_FAIL)
        self.assertIn("pagination_completeness", env["refusals"][0]["failed_gates"])
        # agreed but NEVER delivered a number
        self.assertIsNone(env["value"])
        self.assertEqual(env["gate_verdict"]["outcome"], gates_mod.OUTCOME_REFUSE)


# ===========================================================================
# (e) agree but UNBINDABLE -> REFUSED (PROVENANCE_REFUSED); no value
# ===========================================================================

class AgreeButUnbindableTest(_ConsensusTestBase):
    def test_agreement_but_value_does_not_bind_refuses(self):
        # Agents agree on 9999999, but it does NOT match the Tier-1 commitment (5000000) at
        # the cited path -> the binder cannot verify it -> PROVENANCE_REFUSED.
        runner = _ScriptedRunner([[
            _envelope_return(9999999.0, self.rid, self.path),   # mismatches Tier-1 value
            _envelope_return("9,999,999", self.rid, self.path),
        ]])
        env = consensus_mod.run_consensus(
            "what is the commitment of loan L-1?", runner,
            quorum="2-of-3", n=2, binder=self.binder)
        self.assertEqual(env["state"], consensus_mod.STATE_REFUSED)
        self.assertEqual(env["refusals"][0]["reason_code"], consensus_mod.REASON_PROVENANCE)
        self.assertIsNone(env["value"])

    def test_agreement_with_no_binding_at_all_refuses(self):
        # Agents agree but carry NO provenance binding -> cannot bind -> REFUSE (never deliver
        # an unbound value, even with unanimous agreement).
        runner = _ScriptedRunner([[
            {"value": 5000000.0},   # bare value, no raw_response_id / json_field_path
            {"value": "5,000,000"},
        ]])
        env = consensus_mod.run_consensus(
            "what is the commitment of loan L-1?", runner,
            quorum="2-of-3", n=2, binder=self.binder)
        self.assertEqual(env["state"], consensus_mod.STATE_REFUSED)
        self.assertEqual(env["refusals"][0]["reason_code"], consensus_mod.REASON_PROVENANCE)
        self.assertIsNone(env["value"])


# ===========================================================================
# (f) re-dispatch is BLIND — no feedback passed to the runner
# ===========================================================================

class BlindRedispatchTest(_ConsensusTestBase):
    def test_redispatch_passes_identical_args_no_feedback_leaked(self):
        # Round 0 splits; round 1 splits -> escalate. Across BOTH dispatches the runner must
        # have received the IDENTICAL (question, n) — proving no prior-round feedback leaked.
        round0 = [
            self._binding_returns(5000000.0),
            _envelope_return(4200000.0, "r:b", "$.x"),
            _envelope_return(6100000.0, "r:c", "$.y"),
        ]
        round1 = [
            _envelope_return(1.0, "r:1", "$.a"),
            _envelope_return(2.0, "r:2", "$.b"),
            _envelope_return(3.0, "r:3", "$.c"),
        ]
        runner = _ScriptedRunner([round0, round1])
        question = "what is the commitment of loan L-1?"
        env = consensus_mod.run_consensus(
            question, runner, quorum="2-of-3", n=3, max_redispatch=1, binder=self.binder)
        self.assertEqual(env["state"], consensus_mod.STATE_REFUSED)
        # exactly two dispatches, BOTH with the identical (question, n) — no feedback channel.
        self.assertEqual(len(runner.calls), 2)
        self.assertEqual(runner.calls[0], (question, 3))
        self.assertEqual(runner.calls[1], (question, 3))
        self.assertEqual(runner.calls[0], runner.calls[1])

    def test_agent_runner_signature_has_no_feedback_channel(self):
        # Structural proof: a runner that ONLY accepts (question, n) works end-to-end. If the
        # engine tried to pass prior-round feedback it would raise a TypeError here.
        seen = []

        def strict_runner(question, n):       # exactly two positional params, no **kwargs
            seen.append((question, n))
            # always split -> forces a re-dispatch (round 1 must ALSO be a 2-arg call)
            return [_envelope_return(1.0, "r1", "$.a"),
                    _envelope_return(2.0, "r2", "$.b"),
                    _envelope_return(3.0, "r3", "$.c")]

        env = consensus_mod.run_consensus(
            "q?", strict_runner, quorum="2-of-3", n=3, max_redispatch=1, binder=self.binder)
        self.assertEqual(env["state"], consensus_mod.STATE_REFUSED)
        self.assertEqual(len(seen), 2)        # initial + 1 blind re-dispatch, both 2-arg


# ===========================================================================
# Hard guarantees: no silent pick, single-source cap, substance-not-prose
# ===========================================================================

class NoSilentPickTest(_ConsensusTestBase):
    def test_plurality_below_quorum_never_wins(self):
        # 1 vs 1 vs 1 with NO re-dispatch budget: even though group[0] has a plurality of 1,
        # the engine must NEVER pick it -> escalate with value None.
        runner = _ScriptedRunner([[
            self._binding_returns(5000000.0),
            _envelope_return(4200000.0, "r:b", "$.x"),
            _envelope_return(6100000.0, "r:c", "$.y"),
        ]])
        env = consensus_mod.run_consensus(
            "q?", runner, quorum="2-of-3", n=3, max_redispatch=0, binder=self.binder)
        self.assertEqual(env["state"], consensus_mod.STATE_REFUSED)
        self.assertEqual(env["refusals"][0]["reason_code"], consensus_mod.REASON_NO_CONSENSUS)
        self.assertIsNone(env["value"])
        self.assertEqual(len(runner.calls), 1)   # no re-dispatch when budget is 0


    def test_none_group_never_picked_even_at_quorum_one(self):
        # Regression for the silent-None pick: a ('none',) return must NEVER be selected as the
        # agreed group, even when quorum resolves to 1 (which would otherwise let a count-1
        # group satisfy `agreeing_count >= threshold`). Tier-1 stores null at the cited path so
        # even the binder would not save us — the guard must be STRUCTURAL.
        raw_null = adapter_mod.make_raw_api_response(
            raw_response_id="r:loan:L-null",
            endpoint="https://api.hypercore.ai/graphql",
            request_params={"graphql_operation": "HCAGetLoan"},
            timestamp="2026-06-18T08:00:00Z", http_status=200, cursor=None,
            reported_total=None,
            body={"record": {"id": "L-null", "x": None},
                  "provenance": {"fetched_at": "2026-06-18T08:00:00Z"}},
            backend="fixture")
        null_rid = self.cache.put_raw(raw_null)
        null_path = "$.body.record.x"
        # Two agents: one returns None (bound to the null Tier-1 path), one returns 5.
        runner = _ScriptedRunner([[
            _envelope_return(None, null_rid, null_path),
            _envelope_return(5, "r:other", "$.body.record.x"),
        ]])
        env = consensus_mod.run_consensus(
            "what is x of loan L-null?", runner,
            quorum=1, n=2, max_redispatch=0, binder=self.binder)
        # The None group must NOT be delivered. With quorum 1, the real-substance group (5)
        # has count 1 and is bound to r:other (which is NOT in Tier-1) so provenance refuses;
        # either way the engine must REFUSE with value None — NEVER DELIVER None.
        self.assertEqual(env["state"], consensus_mod.STATE_REFUSED)
        self.assertIsNone(env["value"])
        self.assertIn(env["refusals"][0]["reason_code"],
                      (consensus_mod.REASON_NO_CONSENSUS, consensus_mod.REASON_PROVENANCE))
        self.assertNotEqual(env["state"], consensus_mod.STATE_DELIVERED)

    def test_two_blank_returns_do_not_form_delivering_consensus(self):
        # Regression for the blank-substance bug: two whitespace-only answers must NOT agree on
        # substance and reach quorum — a blank is non-substantive (collapses to the none
        # sentinel), so the engine must REFUSE (never deliver an empty-string "consensus").
        runner = _ScriptedRunner([[
            _envelope_return("", self.rid, self.path),
            _envelope_return("   ", self.rid, self.path),
        ]])
        env = consensus_mod.run_consensus(
            "what is the commitment of loan L-1?", runner,
            quorum="2-of-3", n=2, max_redispatch=0, binder=self.binder)
        self.assertEqual(env["state"], consensus_mod.STATE_REFUSED)
        self.assertEqual(env["refusals"][0]["reason_code"], consensus_mod.REASON_NO_CONSENSUS)
        self.assertIsNone(env["value"])

    def test_blank_substance_key_is_none_sentinel(self):
        # Direct unit proof that blank/whitespace text maps to the non-agreeing none sentinel.
        self.assertEqual(consensus_mod._substance_key(""), ("none",))
        self.assertEqual(consensus_mod._substance_key("   "), ("none",))
        # Two blanks therefore do NOT cluster into an agreeing group.
        groups = consensus_mod.group_by_substance(["", "  "])
        for g in groups:
            self.assertEqual(g["count"], 1)


class SingleSourceCapTest(_ConsensusTestBase):
    def test_single_agent_agreement_caps_confidence_at_0_7(self):
        # quorum 1-of-1 with a single agent: the lone agreeing source is capped at <= 0.7.
        runner = _ScriptedRunner([[self._binding_returns(5000000.0)]])
        env = consensus_mod.run_consensus(
            "what is the commitment of loan L-1?", runner,
            quorum=1, n=1, binder=self.binder)
        self.assertEqual(env["state"], consensus_mod.STATE_DELIVERED)
        self.assertTrue(env["confidence"]["single_source"])
        self.assertLessEqual(env["confidence"]["confidence"], 0.7)
        self.assertEqual(env["confidence"]["source_count"], 1)


class SubstanceNotProseTest(_ConsensusTestBase):
    def test_grouping_clusters_by_substance(self):
        # Direct unit test of the grouping primitive: prose variants of the SAME number
        # cluster, a genuinely different number does not.
        groups = consensus_mod.group_by_substance(
            [5000000.0, "$5,000,000.00", "5000000", 4200000.0])
        self.assertEqual(groups[0]["count"], 3)              # the three 5M variants
        self.assertEqual(groups[1]["count"], 1)              # the 4.2M outlier
        self.assertEqual(len(groups), 2)

    def test_quorum_parsing_variants(self):
        self.assertEqual(consensus_mod.parse_quorum("2-of-3", 3), 2)
        self.assertEqual(consensus_mod.parse_quorum("2of3", 3), 2)
        self.assertEqual(consensus_mod.parse_quorum(2, 3), 2)
        # threshold clamps to the actual cohort size n
        self.assertEqual(consensus_mod.parse_quorum("5-of-5", 3), 3)
        self.assertEqual(consensus_mod.parse_quorum(0, 3), 1)


# ===========================================================================
# SUBSCRIPTION-ONLY — no API key / no model call in the engine source
# ===========================================================================

class SubscriptionOnlyTest(unittest.TestCase):
    def test_engine_source_has_no_api_key_or_model_call(self):
        src_path = os.path.join(_SCRIPTS_DIR, "hca-consensus.py")
        with open(src_path, "r", encoding="utf-8") as fh:
            src = fh.read()
        # No API key reference (the WORD ANTHROPIC_API_KEY must not appear as a usage).
        self.assertNotIn("ANTHROPIC_API_KEY", src,
                         msg="consensus engine must never reference ANTHROPIC_API_KEY")
        for forbidden in ("import urllib", "import http.client", "import socket",
                          "import requests", "openai", "anthropic.", "api.anthropic.com"):
            self.assertNotIn(forbidden, src,
                             msg=f"consensus engine must not {forbidden} (no model API call)")


if __name__ == "__main__":
    unittest.main(verbosity=2)
