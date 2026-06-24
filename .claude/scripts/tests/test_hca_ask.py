#!/usr/bin/env python3
"""test_hca_ask.py — stdlib unittest for the smart ask orchestrator (hca-ask.py).

Proves the three-layer routing with INJECTED fakes (no live creds):
  1. a deterministic DELIVERED result passes through untouched;
  2. a funding/investor question ("XL's outstanding on the Beehive loan") resolves investor + loan
     and routes to the funding figure;
  3. a non-funding metric falls through to the confidence-graded explorer (entity resolved via a
     token subset, fields graded);
  4. a funding question whose investor is ambiguous surfaces a disambiguation (never silently picks).
"""

import importlib.util
import os
import sys
import unittest


_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS_DIR = os.path.abspath(os.path.join(_THIS_DIR, os.pardir))


def _load(modname, filename):
    cached = sys.modules.get(modname)
    if cached is not None:
        return cached
    path = os.path.join(_SCRIPTS_DIR, filename)
    spec = importlib.util.spec_from_file_location(modname, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[modname] = mod
    spec.loader.exec_module(mod)
    return mod


ask_mod = _load("hca_ask", "hca-ask.py")


def _resolved(eid, name, score=1.0, status=None):
    m = {"id": eid, "name": name, "score": score}
    if status is not None:
        m["status"] = status
    return {"query": name, "match": m, "resolved": True, "ambiguous": False,
            "candidates": [m], "echo": f"matched -> {name} ({eid})", "reason": "single match"}


def _no_match(name):
    return {"query": name, "match": None, "resolved": False, "ambiguous": False,
            "candidates": [], "echo": None, "reason": "no match"}


def _ambiguous(name, cands):
    return {"query": name, "match": None, "resolved": False, "ambiguous": True,
            "candidates": cands, "echo": None, "reason": "ambiguous"}


class _FakeExplorer:
    def __init__(self, results):
        self._results = results

    def explore_question(self, question, resolved_entity):
        return {"state": "EXPLORED" if self._results else "NO_MATCH",
                "entity_type": resolved_entity["entity_type"], "entity_id": resolved_entity["id"],
                "graphql_type": "FundingEntity", "keywords": ["irr"],
                "results": self._results, "notes": ["best-effort (not a verified figure)"]}


class SmartAskTest(unittest.TestCase):
    def test_deterministic_delivered_passes_through(self):
        det = {"state": "DELIVERED", "answer": "42 loans", "values": [{"value": 42}]}
        out = ask_mod.smart_ask("how many loans are there?",
                                deliver_ask=lambda q: det,
                                resolve_loan=lambda n: _no_match(n),
                                resolve_entity=lambda n, t: _no_match(n),
                                run_funding=lambda *a, **k: None,
                                explorer=_FakeExplorer([]))
        self.assertEqual(out["state"], "DELIVERED")
        self.assertEqual(out["tier"], "deterministic")

    def test_funding_question_routes_to_funding_figure(self):
        def resolve_loan(name):
            return _resolved("134", "Beehive Waldorff", status="Active") \
                if name.strip().lower() == "beehive" else _no_match(name)

        def resolve_entity(name, etype):
            return _resolved("3", "XL") \
                if etype == "fundingEntity" and name.strip().lower() == "xl" else _no_match(name)

        captured = {}

        def run_funding(fig, loan_id, fe_id):
            captured.update(fig=fig, loan_id=loan_id, fe_id=fe_id)
            return {"state": "DELIVERED",
                    "answer": "XL outstanding on loan 134 = 6,922,294.60",
                    "values": [{"value": 6922294.60}], "meta": {}}

        out = ask_mod.smart_ask(
            "What is the XL outstanding amount for beehive senior loan?",
            deliver_ask=lambda q: {"state": "REFUSED", "refusals": [{"reason_code": "UNMAPPABLE"}]},
            resolve_loan=resolve_loan, resolve_entity=resolve_entity,
            run_funding=run_funding, explorer=_FakeExplorer([]))

        self.assertEqual(out["state"], "DELIVERED")
        self.assertEqual(out["tier"], "funding")
        self.assertEqual(captured, {"fig": "funding_outstanding", "loan_id": "134", "fe_id": "3"})
        self.assertEqual(out["meta"]["resolution"]["loan"]["id"], "134")
        self.assertEqual(out["meta"]["resolution"]["investor"]["id"], "3")
        self.assertEqual(out["meta"]["resolution"]["figure"], "funding_outstanding")

    def test_non_funding_metric_falls_through_to_explorer(self):
        # 'irr' is not a funding-figure keyword -> explorer; entity 'XL' resolves via a token subset.
        def resolve_entity(name, etype):
            return _resolved("3", "XL") \
                if etype == "fundingEntity" and name.strip().lower() == "xl" else _no_match(name)

        graded = [{"field": "currentAverageInterestRate", "value": 0.11, "confidence": 0.6,
                   "confidence_label": "medium",
                   "provenance": {"operation": "fundingEntity", "json_field_path": "$.x"}}]
        out = ask_mod.smart_ask(
            "what is the irr for XL?",
            deliver_ask=lambda q: {"state": "REFUSED", "refusals": [{"reason_code": "UNMAPPABLE"}]},
            resolve_loan=lambda n: _no_match(n), resolve_entity=resolve_entity,
            run_funding=lambda *a, **k: None, explorer=_FakeExplorer(graded))
        self.assertEqual(out["state"], "EXPLORED")
        self.assertEqual(out["tier"], "explorer")
        self.assertTrue(out["meta"]["best_effort"])
        self.assertEqual(out["results"][0]["field"], "currentAverageInterestRate")

    def test_funding_investor_ambiguous_surfaces_disambiguation(self):
        def resolve_loan(name):
            return _resolved("134", "Beehive Waldorff") \
                if name.strip().lower() == "beehive" else _no_match(name)

        cands = [{"id": "3", "name": "XL"}, {"id": "9", "name": "XL Capital"}]

        def resolve_entity(name, etype):
            return _ambiguous(name, cands) \
                if etype == "fundingEntity" and name.strip().lower() == "xl" else _no_match(name)

        out = ask_mod.smart_ask(
            "XL outstanding for beehive",
            deliver_ask=lambda q: {"state": "REFUSED", "refusals": [{"reason_code": "UNMAPPABLE"}]},
            resolve_loan=resolve_loan, resolve_entity=resolve_entity,
            run_funding=lambda *a, **k: None, explorer=_FakeExplorer([]))
        self.assertEqual(out["state"], "REFUSED")
        self.assertEqual(out["refusals"][0]["reason_code"], "FUNDING_DISAMBIGUATION")
        self.assertEqual(len(out["refusals"][0]["investor_candidates"]), 2)

    def test_portfolio_question_routes_to_portfolio_figure(self):
        # investor named + funding metric, but NO loan -> the fundingEntity-level portfolio figure.
        def resolve_loan(name):
            return _no_match(name)  # nothing resolves as a loan

        def resolve_entity(name, etype):
            return _resolved("3", "XL") \
                if etype == "fundingEntity" and name.strip().lower() == "xl" else _no_match(name)

        captured = {}

        def run_portfolio(fig, fe_id, name):
            captured.update(fig=fig, fe_id=fe_id, name=name)
            return {"state": "DELIVERED", "answer": "XL portfolio receivable = 27,040,395.55",
                    "values": [{"value": 27040395.55}], "meta": {}}

        out = ask_mod.smart_ask(
            "what is XL's total receivable across the portfolio?",
            deliver_ask=lambda q: {"state": "REFUSED", "refusals": [{"reason_code": "UNMAPPABLE"}]},
            resolve_loan=resolve_loan, resolve_entity=resolve_entity,
            run_funding=lambda *a, **k: None, run_portfolio=run_portfolio,
            explorer=_FakeExplorer([]))

        self.assertEqual(out["state"], "DELIVERED")
        self.assertEqual(out["tier"], "portfolio")
        self.assertEqual(captured, {"fig": "portfolio_receivable", "fe_id": "3", "name": "XL"})
        self.assertEqual(out["meta"]["resolution"]["investor"]["id"], "3")
        self.assertEqual(out["meta"]["resolution"]["figure"], "portfolio_receivable")

    def test_empty_question_refused(self):
        out = ask_mod.smart_ask("   ")
        self.assertEqual(out["state"], "REFUSED")
        self.assertEqual(out["refusals"][0]["reason_code"], "EMPTY_QUESTION")


if __name__ == "__main__":
    unittest.main(verbosity=2)
