#!/usr/bin/env python3
"""test_hca_deliver.py — stdlib unittest for the thin end-to-end answer spine (SLICE-HCA-07).

Proves Demo 1 on FIXTURES (no network, no creds): the spine wires
plan -> fetch -> cache -> provenance -> gates -> envelope for the trivial tier and degrades
correctly. Required cases (slice acceptance):

  HAPPY PATH
    - a single-value lookup returns a DELIVERED envelope with value + a RESOLVABLE provenance
      citation (raw_response_id + json_field_path) + confidence + gate verdict `pass` +
      complete=True; QA can re-walk the cited path into Tier-1 and get the same value.
    - count + simple aggregate (total commitment) also deliver with provenance + gate pass.

  REFUSAL / DEGRADATION (REQUIRED — fail = REJECT)
    - unmappable question                  -> REFUSED (UNMAPPABLE_QUESTION), never a guess.
    - a value that FAILS a gate            -> REFUSED naming the failing gate, NEVER a number.
    - adapter not live (no creds)          -> explicit NO_LIVE_DATA envelope, never fabricated.

  NON-BYPASSABLE
    - tamper Tier-1 after fetch so the binding mismatches -> the spine REFUSES (the binder is
      not bypassable); a value never reaches `answer` without a verified binding AND gate pass.

Run:
  python3 -m unittest discover -s .claude/scripts/tests -p 'test_hca_*.py' -v
"""

import datetime
import importlib.util
import os
import shutil
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
deliver_mod = _load("hca_deliver", "hca-deliver.py")


# A fixed "now" inside the loan freshness window (fixtures are stamped 2026-06-18T08:00:00Z;
# loan window is 1 day, so 09:00 same day is fresh).
_NOW = datetime.datetime(2026, 6, 18, 9, 0, 0, tzinfo=datetime.timezone.utc)
_FETCHED_AT = "2026-06-18T08:00:00Z"


# ---------------------------------------------------------------------------
# A fixture read-only backend implementing the adapter CONTRACT (no network).
# Returns live-shaped RawApiResponses (body.record / body.data) but labeled backend="fixture".
# ---------------------------------------------------------------------------

class _FixtureSpineBackend(adapter_mod.HypercoreBackend):
    def __init__(self, *, mixed_currency=False, truncated=False, non_numeric=False):
        self.mixed_currency = mixed_currency
        self.truncated = truncated
        self.non_numeric = non_numeric

    def is_live(self):
        return False  # clearly fixture data (still legitimately served; not NO_LIVE_DATA)

    def get_entity(self, entity_type, id, *, params=None):
        return adapter_mod.make_raw_api_response(
            raw_response_id=f"fixture:{entity_type}:{id}",
            endpoint="https://api.hypercore.ai/graphql",
            request_params={"graphql_operation": "HCAGetLoan", "variables": {"id": id}},
            timestamp=_FETCHED_AT, http_status=200, cursor=None, reported_total=None,
            body={"record": {"id": id, "refId": "REF-0001", "name": "PLACEHOLDER Bridge",
                             "status": "ACTIVE", "commitment": 5000000.0,
                             "startDate": "2025-03-01", "endDate": "2027-03-01"},
                  "provenance": {"fetched_at": _FETCHED_AT}},
            backend="fixture")

    def list_entities(self, entity_type, *, filters=None, cursor=None):
        c2 = "EUR" if self.mixed_currency else "USD"
        rows = [
            {"id": "L-1", "status": "ACTIVE", "commitment": 100.0, "currency": "USD"},
            {"id": "L-2", "status": "ACTIVE", "commitment": 200.0, "currency": c2},
            {"id": "L-3", "status": "CLOSED", "commitment": 300.0, "currency": "USD"},
        ]
        if self.non_numeric:
            rows[1]["commitment"] = "lots"
        fetched = 2 if self.truncated else 3
        return adapter_mod.make_raw_api_response(
            raw_response_id=f"fixture:list:{entity_type}:"
                            f"{'trunc' if self.truncated else 'full'}",
            endpoint="https://api.hypercore.ai/graphql",
            request_params={"graphql_operation": "HCAListPaginatedLoans"},
            timestamp=_FETCHED_AT, http_status=200, cursor=None, reported_total=3,
            body={"data": rows[:fetched], "reported_total": 3, "fetched": fetched,
                  "complete": not self.truncated, "pages": 1,
                  "provenance": {"fetched_at": _FETCHED_AT}},
            backend="fixture")

    def get_schema(self, entity_type):
        raise NotImplementedError

    def subscribe_events(self, entity_type=None, *, callback=None, poll_interval_s=None):
        raise NotImplementedError


class _SpineTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="hca-deliver-test-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _spine(self, backend=None):
        backend = backend or _FixtureSpineBackend()
        return deliver_mod.DeliverySpine(
            adapter=adapter_mod.HypercoreAdapter(backend),
            cache=cache_mod.TwoTierCache(cache_dir=tempfile.mkdtemp(dir=self.tmp)),
            gate_suite=gates_mod.GateSuite(now=_NOW),
            now=_NOW)


# ===========================================================================
# HAPPY PATH
# ===========================================================================

class HappyPathTest(_SpineTest):
    def test_lookup_delivers_value_provenance_confidence_gatepass(self):
        env = self._spine().ask("what is the status of loan L-001?")
        self.assertEqual(env["state"], deliver_mod.STATE_DELIVERED)
        self.assertIsNotNone(env["answer"])
        self.assertEqual(len(env["values"]), 1)
        v = env["values"][0]
        self.assertEqual(v["value"], "ACTIVE")
        # >= 1 resolvable provenance citation
        self.assertIn("raw_response_id", v["provenance"])
        self.assertIn("json_field_path", v["provenance"])
        self.assertIsNotNone(v["confidence"])           # freshness/confidence present
        self.assertEqual(env["gate_verdict"]["outcome"], gates_mod.OUTCOME_PASS)
        self.assertEqual(env["gate_verdict"]["tier"], "deterministic-only")
        self.assertTrue(env["complete"])
        self.assertEqual(env["refusals"], [])

    def test_provenance_citation_is_resolvable_into_tier1(self):
        # QA re-walks the cited path into Tier-1 and confirms the SAME value (binding resolves).
        cache = cache_mod.TwoTierCache(cache_dir=tempfile.mkdtemp(dir=self.tmp))
        spine = deliver_mod.DeliverySpine(
            adapter=adapter_mod.HypercoreAdapter(_FixtureSpineBackend()),
            cache=cache, gate_suite=gates_mod.GateSuite(now=_NOW), now=_NOW)
        env = spine.ask("what is the status of loan L-001?")
        prov = env["values"][0]["provenance"]
        value, ok = cache.resolve_binding(prov)
        self.assertTrue(ok)
        self.assertEqual(value, env["values"][0]["value"])

    def test_count_delivers_with_provenance_and_pagination_complete(self):
        env = self._spine().ask("how many loans are there?")
        self.assertEqual(env["state"], deliver_mod.STATE_DELIVERED)
        self.assertEqual(env["values"][0]["value"], 3)
        self.assertEqual(env["values"][0]["provenance"]["json_field_path"],
                         "$.body.reported_total")
        self.assertEqual(env["gate_verdict"]["outcome"], gates_mod.OUTCOME_PASS)
        self.assertTrue(env["gate_verdict"]["pagination_complete"])
        self.assertTrue(env["complete"])

    def test_aggregate_total_commitment_delivers_with_aggregate_binding(self):
        env = self._spine().ask("what is the total commitment across all loans?")
        self.assertEqual(env["state"], deliver_mod.STATE_DELIVERED)
        self.assertEqual(env["values"][0]["value"], 600.0)
        self.assertEqual(env["values"][0]["currency"], "USD")
        self.assertTrue(env["values"][0]["provenance"]["aggregate"])
        # one contributing binding per source row
        self.assertEqual(len(env["values"][0]["provenance"]["contributing"]), 3)
        self.assertEqual(env["gate_verdict"]["outcome"], gates_mod.OUTCOME_PASS)
        # aggregation went through the currency normalization gate
        self.assertTrue(env["gate_verdict"]["normalization_applied"])


# ===========================================================================
# UNMAPPABLE -> REFUSE (never guess)
# ===========================================================================

class UnmappableTest(_SpineTest):
    def test_unknown_entity_is_refused(self):
        env = self._spine().ask("how many giraffes are there?")
        self.assertEqual(env["state"], deliver_mod.STATE_REFUSED)
        self.assertEqual(env["refusals"][0]["reason_code"], deliver_mod.REASON_UNMAPPABLE)
        self.assertIsNone(env["answer"])
        self.assertEqual(env["values"], [])

    def test_unsupported_question_is_refused(self):
        env = self._spine().ask("who is the CEO of the company?")
        self.assertEqual(env["state"], deliver_mod.STATE_REFUSED)
        self.assertEqual(env["refusals"][0]["reason_code"], deliver_mod.REASON_UNMAPPABLE)

    def test_lookup_without_record_id_is_refused(self):
        # names an entity + field but no record id -> not a supported lookup -> REFUSE
        env = self._spine().ask("what is the status of the loan?")
        self.assertEqual(env["state"], deliver_mod.STATE_REFUSED)
        self.assertEqual(env["refusals"][0]["reason_code"], deliver_mod.REASON_UNMAPPABLE)


# ===========================================================================
# GATE FAIL -> REFUSAL NAMING THE GATE, NEVER A NUMBER
# ===========================================================================

class GateFailTest(_SpineTest):
    def test_mixed_currency_aggregate_refuses_naming_the_gate(self):
        env = self._spine(_FixtureSpineBackend(mixed_currency=True)).ask(
            "what is the total commitment across all loans?")
        self.assertEqual(env["state"], deliver_mod.STATE_REFUSED)
        self.assertEqual(env["refusals"][0]["reason_code"], deliver_mod.REASON_GATE_FAIL)
        # the refusal NAMES the failing gate ...
        self.assertIn("unit_currency_normalization", env["refusals"][0]["failed_gates"])
        # ... and NEVER delivers a number
        self.assertIsNone(env["answer"])
        self.assertEqual(env["values"], [])
        self.assertEqual(env["gate_verdict"]["outcome"], gates_mod.OUTCOME_REFUSE)

    def test_truncated_count_refuses_on_pagination_gate(self):
        env = self._spine(_FixtureSpineBackend(truncated=True)).ask(
            "how many loans are there?")
        self.assertEqual(env["state"], deliver_mod.STATE_REFUSED)
        self.assertEqual(env["refusals"][0]["reason_code"], deliver_mod.REASON_GATE_FAIL)
        self.assertIn("pagination_completeness", env["refusals"][0]["failed_gates"])
        self.assertIsNone(env["answer"])
        self.assertEqual(env["values"], [])

    def test_no_number_appears_anywhere_in_a_gate_refusal(self):
        # Belt-and-suspenders: a gate refusal must carry no delivered value at all.
        env = self._spine(_FixtureSpineBackend(truncated=True)).ask(
            "how many loans are there?")
        self.assertEqual(env["values"], [])
        self.assertIsNone(env["answer"])
        # the structured refusal references a gate, not a count.
        self.assertTrue(any("gate" in (r.get("reason", "").lower())
                            for r in env["refusals"]))


# ===========================================================================
# NO_LIVE_DATA -> explicit envelope, NEVER a fabricated number (REQUIRED)
# ===========================================================================

class NoLiveDataTest(_SpineTest):
    def _no_cred_spine(self):
        # A real LiveBackend with an EMPTY env => is_live() False => degrade, do not fabricate.
        lb = adapter_mod.LiveBackend(env={})
        return deliver_mod.DeliverySpine(
            adapter=adapter_mod.HypercoreAdapter(lb),
            cache=cache_mod.TwoTierCache(cache_dir=tempfile.mkdtemp(dir=self.tmp)),
            gate_suite=gates_mod.GateSuite(now=_NOW), now=_NOW)

    def test_count_with_no_creds_returns_no_live_data(self):
        env = self._no_cred_spine().ask("how many loans are there?")
        self.assertEqual(env["state"], deliver_mod.STATE_NO_LIVE_DATA)
        self.assertIsNone(env["answer"])
        self.assertEqual(env["values"], [])             # NEVER a fabricated number
        self.assertIn("no live data", env["meta"]["message"])

    def test_lookup_with_no_creds_returns_no_live_data(self):
        env = self._no_cred_spine().ask("what is the status of loan L-001?")
        self.assertEqual(env["state"], deliver_mod.STATE_NO_LIVE_DATA)
        self.assertIsNone(env["answer"])
        self.assertEqual(env["values"], [])

    def test_no_live_data_never_fabricates_for_aggregate(self):
        env = self._no_cred_spine().ask("what is the total commitment across all loans?")
        self.assertEqual(env["state"], deliver_mod.STATE_NO_LIVE_DATA)
        self.assertEqual(env["values"], [])


# ===========================================================================
# NON-BYPASSABLE — the binder cannot be skipped (tampered Tier-1 => REFUSE)
# ===========================================================================

class NonBypassableTest(_SpineTest):
    def test_tampered_tier1_makes_binding_mismatch_and_refuses(self):
        # The spine captures the value from its FIRST Tier-1 read, then the provenance engine
        # RE-READS Tier-1 to verify. We tamper only the engine's (later) reads so the bound
        # value no longer matches what Tier-1 reports at the cited path -> the binder must
        # REFUSE. This proves the binder is non-bypassable: a value that ceases to match its
        # source can never be delivered.
        class _TamperingCache(cache_mod.TwoTierCache):
            def __init__(self, *a, **k):
                super().__init__(*a, **k)
                self._reads = 0

            def get_raw(self, rid):
                raw = super().get_raw(rid)
                self._reads += 1
                if self._reads >= 2:  # spine read = 1st; engine re-read = 2nd+ -> tamper
                    body = raw.get("body") or {}
                    rec = body.get("record")
                    if isinstance(rec, dict) and "status" in rec:
                        rec["status"] = "TAMPERED-DOES-NOT-MATCH"
                return raw
        tampered = _TamperingCache(cache_dir=tempfile.mkdtemp(dir=self.tmp))
        spine = deliver_mod.DeliverySpine(
            adapter=adapter_mod.HypercoreAdapter(_FixtureSpineBackend()),
            cache=tampered, gate_suite=gates_mod.GateSuite(now=_NOW), now=_NOW)
        env = spine.ask("what is the status of loan L-001?")
        # delivery is impossible because the binder re-verifies value-against-Tier-1
        self.assertEqual(env["state"], deliver_mod.STATE_REFUSED)
        self.assertEqual(env["refusals"][0]["reason_code"], deliver_mod.REASON_PROVENANCE)
        self.assertIsNone(env["answer"])
        self.assertEqual(env["values"], [])

    def test_delivery_requires_both_binder_and_gates(self):
        # Sanity: the only DELIVERED envelopes in this suite carry BOTH a verified binding and
        # a gate verdict of `pass`. Assert the invariant structurally on a happy path.
        env = self._spine().ask("what is the status of loan L-001?")
        self.assertEqual(env["state"], deliver_mod.STATE_DELIVERED)
        self.assertEqual(env["gate_verdict"]["outcome"], gates_mod.OUTCOME_PASS)
        self.assertTrue(env["gate_verdict"]["provenance_ok"])
        for v in env["values"]:
            self.assertIn("raw_response_id", v["provenance"])


# ===========================================================================
# NO NETWORK — the spine + its imports never import a socket library
# ===========================================================================

class NoNetworkImportTest(unittest.TestCase):
    def test_deliver_module_imports_no_network_library(self):
        src_path = os.path.join(_SCRIPTS_DIR, "hca-deliver.py")
        with open(src_path, "r", encoding="utf-8") as fh:
            src = fh.read()
        for forbidden in ("import urllib", "import http", "import socket", "import ssl",
                          "import requests"):
            self.assertNotIn(forbidden, src,
                             msg=f"hca-deliver.py must not {forbidden} (no network in the spine)")


if __name__ == "__main__":
    unittest.main(verbosity=2)
