#!/usr/bin/env python3
"""test_hca_ask_learning.py — stdlib unittest for the MCQ-selection + learning loop in
hca-ask.py (the learned-routing layer over the smart-ask orchestrator).

Proves: an unmapped metric on a funding-shaped question yields NEEDS_SELECTION (not the junk
explorer); recording the choice makes the SAME question DELIVER via the learned figure; the
learned routing generalizes and the VALUE is always re-fetched live (never cached); an ambiguous
investor yields an entity NEEDS_SELECTION; a learned name->entity makes an otherwise-unresolvable
loan resolve; and with NO store the base behavior is preserved.
"""

import importlib.util
import os
import sys
import tempfile
import unittest


_THIS = os.path.dirname(os.path.abspath(__file__))
_SCR = os.path.abspath(os.path.join(_THIS, os.pardir))


def _load(modname, filename):
    cached = sys.modules.get(modname)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(modname, os.path.join(_SCR, filename))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[modname] = mod
    spec.loader.exec_module(mod)
    return mod


ask = _load("hca_ask", "hca-ask.py")
learned = _load("hca_learned", "hca-learned.py")


def _resolved(eid, name):
    m = {"id": eid, "name": name, "score": 1.0}
    return {"query": name, "match": m, "resolved": True, "ambiguous": False, "candidates": [m]}


def _no(name):
    return {"query": name, "match": None, "resolved": False, "ambiguous": False, "candidates": []}


def _ambiguous(name, cands):
    return {"query": name, "match": None, "resolved": False, "ambiguous": True, "candidates": cands}


class _Explorer:
    def explore_question(self, q, e):
        return {"results": []}


def _refuse(q):
    return {"state": "REFUSED", "refusals": [{"reason_code": "UNMAPPABLE"}]}


# loan "Ascent Pref" -> 149; investor "XL" -> 3
def _resolve_loan(name):
    return _resolved("149", "Ascent Pref Equity") if name.strip().lower() == "ascent pref" else _no(name)


def _resolve_entity(name, etype):
    if etype == "fundingEntity" and name.strip().lower() == "xl":
        return _resolved("3", "XL")
    return _no(name)


class AskLearningTest(unittest.TestCase):
    def setUp(self):
        self.store = learned.LearnedStore(tempfile.mktemp(suffix=".json"))
        self.ran = {}

    def _run_funding(self, value=3313999.99):
        def _r(fig, loan_id, fe_id):
            self.ran.update(fig=fig, loan=loan_id, fe=fe_id)
            return {"state": "DELIVERED", "answer": "ok", "values": [{"value": value}], "meta": {}}
        return _r

    def _ask(self, q, **over):
        kw = dict(deliver_ask=_refuse, resolve_loan=_resolve_loan, resolve_entity=_resolve_entity,
                  run_funding=self._run_funding(), run_portfolio=lambda *a, **k: None,
                  explorer=_Explorer(), learned=self.store)
        kw.update(over)
        return ask.smart_ask(q, **kw)

    Q = "What is the amount due for XL on the Ascent Pref loan?"

    def test_unmapped_metric_offers_selection(self):
        out = self._ask(self.Q)
        self.assertEqual(out["state"], "NEEDS_SELECTION")
        self.assertEqual(out["selection"]["kind"], "metric")
        self.assertEqual(out["selection"]["phrase"], "amount due")
        metrics = [c["record"]["metric"] for c in out["selection"]["candidates"]]
        self.assertEqual(set(metrics), {"outstanding", "receivable", "commitment", "participation"})

    def test_record_then_reask_delivers_via_learned_routing(self):
        out = self._ask(self.Q)
        rec = [c["record"] for c in out["selection"]["candidates"]
               if c["record"]["metric"] == "outstanding"][0]
        self.assertTrue(ask.record_choice(rec, learned=self.store)["ok"])
        out2 = self._ask(self.Q)
        self.assertEqual(out2["state"], "DELIVERED")
        self.assertEqual(out2["tier"], "funding")
        self.assertEqual(self.ran, {"fig": "funding_outstanding", "loan": "149", "fe": "3"})

    def test_value_is_refetched_never_cached(self):
        ask.record_choice({"kind": "metric_alias", "phrase": "amount due", "metric": "outstanding"},
                          learned=self.store)
        out_a = self._ask(self.Q, run_funding=self._run_funding(value=111.0))
        out_b = self._ask(self.Q, run_funding=self._run_funding(value=222.0))
        # the value tracks the LIVE fetch each time — proof nothing is cached in the store
        self.assertEqual(out_a["values"][0]["value"], 111.0)
        self.assertEqual(out_b["values"][0]["value"], 222.0)

    def test_ambiguous_investor_offers_entity_selection(self):
        cands = [{"id": "3", "name": "XL"}, {"id": "9", "name": "XL Capital"}]

        def resolve_entity(name, etype):
            return _ambiguous(name, cands) if etype == "fundingEntity" \
                and name.strip().lower() == "xl" else _no(name)

        out = self._ask("XL outstanding on the Ascent Pref loan", resolve_entity=resolve_entity)
        self.assertEqual(out["state"], "NEEDS_SELECTION")
        self.assertEqual(out["selection"]["kind"], "entity")
        self.assertEqual(len(out["selection"]["candidates"]), 2)
        self.assertEqual(out["selection"]["candidates"][0]["record"]["kind"], "entity_resolution")

    def test_learned_entity_resolution_makes_loan_resolve(self):
        # resolver can't find the loan at all...
        self.store.record_entity_resolution("ascent pref", "loan", "149", "Ascent Pref Equity")
        out = self._ask("XL outstanding on Ascent Pref", resolve_loan=lambda n: _no(n))
        self.assertEqual(out["state"], "DELIVERED")
        self.assertEqual(self.ran["loan"], "149")

    def test_no_store_preserves_base_behavior(self):
        # without a learned store, an unmapped metric does NOT produce NEEDS_SELECTION
        out = ask.smart_ask(self.Q, deliver_ask=_refuse, resolve_loan=_resolve_loan,
                            resolve_entity=_resolve_entity, run_funding=self._run_funding(),
                            run_portfolio=lambda *a, **k: None, explorer=_Explorer())  # learned=None
        self.assertNotEqual(out.get("state"), "NEEDS_SELECTION")


if __name__ == "__main__":
    unittest.main(verbosity=2)
