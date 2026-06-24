#!/usr/bin/env python3
"""test_hca_cache.py — stdlib unittest for the two-tier cache (SLICE-HCA-03).

Covers the slice-03 acceptance criteria:
  1. Tier-1 immutability (write-once; re-write same key w/ diff content REJECTED; identical
     re-write = idempotent no-op) + lookup by raw_response_id.
  2. Tier-2 NormalizedAnswerRecord built from Tier-1 with field_bindings -> {raw_response_id,
     json_field_path} + derived_from[]; 100% of bindings resolve to a real Tier-1 source at
     the correct path (any unresolvable = REJECT).
  3. Freshness: a read needing fresher data than the cache holds triggers a refetch via the
     adapter; if it cannot refetch -> NO_LIVE_DATA / STALE_REFUSED (NEVER stale silently).
  4. Durability/resume: a re-run finds prior Tier-1 without re-fetch.
  5. Minimal-slice scoping helper: only the requested fields (no full-cache dump, no extra PII).
  6. Cache dir is git-ignored (no real PII can ever be committed).

Run:
  python3 -m unittest discover -s .claude/scripts/tests -p 'test_hca_*.py' -v
"""

import datetime
import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import unittest


_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS_DIR = os.path.abspath(os.path.join(_THIS_DIR, os.pardir))
_REPO_ROOT = os.path.abspath(os.path.join(_SCRIPTS_DIR, os.pardir, os.pardir))


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
normalize_mod = _load("hca_normalize", "hca-normalize.py")


def _now(iso):
    return cache_mod.parse_iso(iso)


def _make_raw(rid, *, entity_type="loan", timestamp="2026-06-18T08:00:00Z",
              body=None, endpoint="https://api.hypercore.ai/graphql"):
    return {
        "raw_response_id": rid,
        "endpoint": endpoint,
        "request_params": {"graphql_operation": "HCAGetLoan", "variables": {"id": rid}},
        "timestamp": timestamp,
        "http_status": 200,
        "cursor": None,
        "reported_total": None,
        "entity_type": entity_type,
        "body": body if body is not None else {
            "record": {"id": rid, "name": "PLACEHOLDER Loan", "commitment": 5000000.0},
            "provenance": {"operation_name": "HCAGetLoan", "fetched_at": timestamp},
        },
        "backend": "fixture",
    }


def _make_list_raw(rid, items, *, entity_type="loan", timestamp="2026-06-18T08:00:00Z",
                   reported_total=None, complete=True):
    return {
        "raw_response_id": rid,
        "endpoint": "https://api.hypercore.ai/graphql",
        "request_params": {"graphql_operation": "HCAListPaginatedLoans"},
        "timestamp": timestamp,
        "http_status": 200,
        "cursor": None,
        "reported_total": reported_total if reported_total is not None else len(items),
        "entity_type": entity_type,
        "body": {
            "data": items,
            "reported_total": reported_total if reported_total is not None else len(items),
            "fetched": len(items),
            "complete": complete,
            "pages": 1,
            "provenance": {"operation_name": "HCAListPaginatedLoans", "fetched_at": timestamp},
        },
        "backend": "fixture",
    }


class _TmpCacheTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="hca-cache-test-")
        self.cache = cache_mod.TwoTierCache(cache_dir=self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


# ===========================================================================
# 1. Tier-1 immutability + lookup
# ===========================================================================

class Tier1ImmutabilityTest(_TmpCacheTest):
    def test_put_then_get_round_trips(self):
        raw = _make_raw("hca:abc")
        rid = self.cache.put_raw(raw)
        self.assertEqual(rid, "hca:abc")
        got = self.cache.get_raw("hca:abc")
        self.assertEqual(got["body"]["record"]["id"], "hca:abc")

    def test_rewrite_with_different_content_is_rejected(self):
        self.cache.put_raw(_make_raw("hca:imm"))
        mutated = _make_raw("hca:imm")
        mutated["body"]["record"]["commitment"] = 9999999.0  # attempt to mutate Tier-1
        with self.assertRaises(cache_mod.ImmutableCacheError):
            self.cache.put_raw(mutated)
        # original is untouched
        self.assertEqual(self.cache.get_raw("hca:imm")["body"]["record"]["commitment"],
                         5000000.0)

    def test_identical_rewrite_is_idempotent_noop(self):
        raw = _make_raw("hca:idem")
        self.cache.put_raw(raw)
        # identical content re-put -> no error, no change (resume)
        rid = self.cache.put_raw(_make_raw("hca:idem"))
        self.assertEqual(rid, "hca:idem")
        self.assertEqual(len(self.cache.store.ids()), 1)

    def test_missing_id_get_raises(self):
        with self.assertRaises(cache_mod.CacheMissError):
            self.cache.get_raw("hca:nope")

    def test_put_without_id_rejected(self):
        with self.assertRaises(ValueError):
            self.cache.put_raw({"endpoint": "x", "body": {}})

    def test_store_exposes_no_mutating_method(self):
        # Tier-1 store is append-only: no update/delete/mutate verb on it.
        import inspect
        forbidden = ("update", "delete", "mutate", "remove", "drop", "set", "modify")
        names = [n for n, _ in inspect.getmembers(cache_mod.RawResponseStore,
                                                  predicate=callable)
                 if not n.startswith("_")]
        for n in names:
            low = n.lower()
            for v in forbidden:
                self.assertFalse(low == v or low.startswith(v + "_"),
                                 msg=f"forbidden mutating method {n!r} on RawResponseStore")

    def test_content_addressed_id_is_stable(self):
        # Same operation+variables -> same id (durable across re-fetch / re-run).
        a = cache_mod.compute_raw_response_id("HCAGetLoan", {"id": "L-1"})
        b = cache_mod.compute_raw_response_id("HCAGetLoan", {"id": "L-1"})
        c = cache_mod.compute_raw_response_id("HCAGetLoan", {"id": "L-2"})
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)
        self.assertTrue(a.startswith("hca:"))


# ===========================================================================
# 2. Tier-2 derivation + back-pointers (HARD gate: 100% of bindings resolve)
# ===========================================================================

class Tier2DerivationTest(_TmpCacheTest):
    def test_single_record_derivation_has_bindings_and_derived_from(self):
        raw = _make_raw("hca:t2")
        self.cache.put_raw(raw)
        n2 = self.cache.read_tier2("hca:t2", entity_type="loan")
        self.assertEqual(n2["entity_type"], "loan")
        self.assertIn("commitment", n2["fields"])
        self.assertIn("commitment", n2["field_bindings"])
        b = n2["field_bindings"]["commitment"]
        self.assertEqual(b["raw_response_id"], "hca:t2")
        self.assertEqual(b["json_field_path"], "$.body.record.commitment")
        self.assertEqual(n2["derived_from"], ["hca:t2"])

    def test_every_binding_resolves_to_tier1_at_correct_path(self):
        raw = _make_list_raw("hca:list", [
            {"id": "L-1", "commitment": 100.0, "status": "ACTIVE"},
            {"id": "L-2", "commitment": 200.0, "status": "CLOSED"},
        ])
        self.cache.put_raw(raw)
        n2 = self.cache.read_tier2("hca:list", entity_type="loan")
        report = normalize_mod.verify_bindings_against_tier1(
            n2, tier1_lookup=self.cache.store.get_or_none)
        self.assertTrue(report["ok"], msg=f"binding failures: {report['failures']}")
        self.assertGreaterEqual(report["checked"], 6)  # 2 records x 3 fields

    def test_tier2_is_derived_only_from_tier1_never_invented(self):
        raw = _make_raw("hca:der", body={
            "record": {"id": "L-9", "commitment": 42.0},
            "provenance": {"fetched_at": "2026-06-18T08:00:00Z"},
        })
        self.cache.put_raw(raw)
        n2 = self.cache.read_tier2("hca:der", entity_type="loan")
        # Every projected field value equals the exact Tier-1 value at its path.
        for field, binding in n2["field_bindings"].items():
            val, ok = self.cache.resolve_binding(binding)
            self.assertTrue(ok)
            self.assertEqual(val, n2["fields"][field])

    def test_an_altered_binding_path_fails_resolution(self):
        # Sanity: a deliberately-wrong path is caught by the verifier (REJECT).
        raw = _make_raw("hca:bad")
        self.cache.put_raw(raw)
        n2 = self.cache.read_tier2("hca:bad", entity_type="loan")
        n2["field_bindings"]["commitment"]["json_field_path"] = "$.body.record.NOPE"
        report = normalize_mod.verify_bindings_against_tier1(
            n2, tier1_lookup=self.cache.store.get_or_none)
        self.assertFalse(report["ok"])

    def test_tier2_excludes_raw_body_token_efficiency(self):
        # The Tier-2 view must NOT carry the full raw body (token efficiency).
        raw = _make_raw("hca:eff")
        self.cache.put_raw(raw)
        n2 = self.cache.read_tier2("hca:eff", entity_type="loan")
        self.assertNotIn("body", n2)
        self.assertNotIn("query", json.dumps(n2))  # no raw GraphQL query string smuggled in


class PiiMinimizationInTier2Test(_TmpCacheTest):
    def test_contact_pii_dropped_from_derived_view_but_kept_in_tier1(self):
        raw = _make_raw("hca:pii", entity_type="client", body={
            "record": {"id": "C-1", "displayName": "PLACEHOLDER Holdings LLC",
                       "email": "placeholder@example.invalid",
                       "mobileNumber": "+10000000000", "numOfActiveLoans": 2},
            "provenance": {"fetched_at": "2026-06-18T08:00:00Z"},
        })
        self.cache.put_raw(raw)
        n2 = self.cache.read_tier2("hca:pii", entity_type="client")
        # PII minimized OUT of the derived view ...
        self.assertNotIn("email", n2["fields"])
        self.assertNotIn("mobileNumber", n2["fields"])
        self.assertIn("email", n2["_pii_minimized"])
        # ... but still present in Tier-1 (need-to-know drill-down only)
        raw_back = self.cache.get_raw("hca:pii")
        self.assertEqual(raw_back["body"]["record"]["email"], "placeholder@example.invalid")


# ===========================================================================
# 3. Freshness: refetch on stale; refuse (never serve stale silently)
# ===========================================================================

class FreshnessTest(_TmpCacheTest):
    def test_fresh_record_is_returned(self):
        fresh_ts = (datetime.datetime.now(datetime.timezone.utc)
                    ).strftime("%Y-%m-%dT%H:%M:%SZ")
        raw = _make_raw("hca:fresh", entity_type="loan", timestamp=fresh_ts)
        self.cache.put_raw(raw)
        got = self.cache.read_fresh("hca:fresh", "loan")
        self.assertEqual(got["raw_response_id"], "hca:fresh")

    def test_stale_loan_without_refetch_refuses_never_serves_stale(self):
        # loan = balances_servicing -> 1-day window; 2024 timestamp is far stale.
        raw = _make_raw("hca:stale", entity_type="loan", timestamp="2024-01-01T00:00:00Z")
        self.cache.put_raw(raw)
        with self.assertRaises(cache_mod.StaleRefusedError) as ctx:
            self.cache.read_fresh("hca:stale", "loan")  # no adapter/refetcher
        env = ctx.exception.envelope
        self.assertEqual(env["state"], cache_mod.STALE_REFUSED)
        self.assertIsNone(env["data"])  # the stale value is NEVER returned
        self.assertFalse(env["refetch_attempted"])

    def test_stale_triggers_refetch_when_refetcher_available(self):
        raw = _make_raw("hca:re", entity_type="loan", timestamp="2024-01-01T00:00:00Z")
        self.cache.put_raw(raw)
        fresh_ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        fresh_raw = _make_raw("hca:re-fresh", entity_type="loan", timestamp=fresh_ts)

        def refetcher():
            return fresh_raw

        got = self.cache.read_fresh("hca:re", "loan", refetcher=refetcher)
        self.assertEqual(got["raw_response_id"], "hca:re-fresh")
        # the refetched record is now cached (durable)
        self.assertTrue(self.cache.has_raw("hca:re-fresh"))

    def test_absent_record_without_refetch_is_no_live_data(self):
        with self.assertRaises(cache_mod.StaleRefusedError) as ctx:
            self.cache.read_fresh("hca:never", "loan")
        self.assertEqual(ctx.exception.envelope["state"], cache_mod.NO_LIVE_DATA)

    def test_adapter_not_live_still_refuses(self):
        raw = _make_raw("hca:al", entity_type="loan", timestamp="2024-01-01T00:00:00Z")
        self.cache.put_raw(raw)

        class _NotLiveAdapter:
            def is_live(self):
                return False

        with self.assertRaises(cache_mod.StaleRefusedError):
            self.cache.read_fresh("hca:al", "loan", adapter=_NotLiveAdapter())

    def test_freshness_window_classes_resolve(self):
        # reference_static (client) is far longer than balances_servicing (loan)
        self.assertGreater(cache_mod.freshness_window_days("client"),
                           cache_mod.freshness_window_days("loan"))
        # unknown entity falls back to the SHORTEST window (err toward refetch)
        self.assertEqual(cache_mod.freshness_window_days("totally_unknown"),
                         cache_mod.freshness_window_days("loan"))

    def test_unparseable_timestamp_is_treated_as_stale(self):
        self.assertFalse(cache_mod.is_fresh("not-a-date", "loan"))


# ===========================================================================
# 4. Durability / resume (re-run finds prior Tier-1 without re-fetch)
# ===========================================================================

class DurabilityResumeTest(_TmpCacheTest):
    def test_second_cache_instance_finds_prior_tier1(self):
        self.cache.put_raw(_make_raw("hca:durable"))
        # simulate a fresh process: a brand-new TwoTierCache over the same dir
        resumed = cache_mod.TwoTierCache(cache_dir=self.tmp)
        self.assertTrue(resumed.has_raw("hca:durable"))
        got = resumed.get_raw("hca:durable")
        self.assertEqual(got["raw_response_id"], "hca:durable")

    def test_resume_does_not_refetch_when_fresh(self):
        fresh_ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.cache.put_raw(_make_raw("hca:nofetch", entity_type="loan", timestamp=fresh_ts))
        resumed = cache_mod.TwoTierCache(cache_dir=self.tmp)
        calls = {"n": 0}

        def refetcher():
            calls["n"] += 1
            return _make_raw("should-not-be-used")

        got = resumed.read_fresh("hca:nofetch", "loan", refetcher=refetcher)
        self.assertEqual(got["raw_response_id"], "hca:nofetch")
        self.assertEqual(calls["n"], 0)  # fresh -> NO refetch


# ===========================================================================
# 5. Minimal-slice scoping helper (no full-cache dump, no extra PII)
# ===========================================================================

class MinimalSliceTest(_TmpCacheTest):
    def test_minimal_slice_returns_only_requested_fields(self):
        raw = _make_raw("hca:slice", entity_type="client", body={
            "record": {"id": "C-1", "displayName": "PLACEHOLDER Holdings LLC",
                       "email": "placeholder@example.invalid",
                       "numOfActiveLoans": 2, "identificationNumber": "PLACEHOLDER-ID"},
            "provenance": {"fetched_at": "2026-06-18T08:00:00Z"},
        })
        self.cache.put_raw(raw)
        sl = self.cache.minimal_slice("hca:slice", ["id", "numOfActiveLoans"])
        picked = sl["slice"][0]["fields"]
        self.assertEqual(set(picked.keys()), {"id", "numOfActiveLoans"})
        # PII fields not requested are ABSENT (not dumped)
        self.assertNotIn("email", picked)
        self.assertNotIn("identificationNumber", picked)

    def test_minimal_slice_is_not_a_full_cache_dump(self):
        # multiple records cached; a slice over one must not leak the others
        self.cache.put_raw(_make_raw("hca:s1", entity_type="loan"))
        self.cache.put_raw(_make_raw("hca:s2", entity_type="loan"))
        sl = self.cache.minimal_slice("hca:s1", ["id"])
        blob = json.dumps(sl)
        self.assertNotIn("hca:s2", blob)
        # carries provenance pointer so the agent can still cite source
        self.assertEqual(sl["raw_response_id"], "hca:s1")
        self.assertIn("field_paths", sl["slice"][0])

    def test_minimal_slice_caps_records(self):
        items = [{"id": f"L-{i}", "commitment": float(i)} for i in range(5)]
        self.cache.put_raw(_make_list_raw("hca:slist", items))
        sl = self.cache.minimal_slice("hca:slist", ["id"], max_records=2)
        self.assertEqual(len(sl["slice"]), 2)  # capped, not the whole list

    def test_minimal_slice_field_paths_resolve_across_all_tier1_shapes(self):
        # HARD provenance gate: every emitted field_path MUST re-resolve into Tier-1.
        # The blind-extractor pipeline REFUSES any cited path that does not resolve, so a
        # bogus path (e.g. the REST-single `$.body[0].<field>` regression) would falsely
        # refuse a legitimately-extracted value. Cover all three supported body shapes.
        cases = {
            # REST single: body = {<id>: {...fields...}} directly (no data/record wrapper).
            "hca:rest-single": _make_raw("hca:rest-single", entity_type="loan", body={
                "loan_id": "L-REST", "commitment": 750000.0, "status": "ACTIVE",
            }),
            # GraphQL single: body.record = {...}
            "hca:record-single": _make_raw("hca:record-single", entity_type="loan", body={
                "record": {"id": "L-REC", "commitment": 250000.0, "status": "CLOSED"},
                "provenance": {"fetched_at": "2026-06-18T08:00:00Z"},
            }),
            # GraphQL list: body.data = [...]
            "hca:data-list": _make_list_raw("hca:data-list", [
                {"id": "L-1", "commitment": 100.0, "status": "ACTIVE"},
                {"id": "L-2", "commitment": 200.0, "status": "CLOSED"},
            ]),
        }
        fields = ["commitment", "status"]
        for rid, raw in cases.items():
            self.cache.put_raw(raw)

        for rid in cases:
            tier1 = self.cache.get_raw(rid)
            sl = self.cache.minimal_slice(rid, fields, max_records=5)
            emitted = 0
            for entry in sl["slice"]:
                for field, path in entry["field_paths"].items():
                    resolved = cache_mod.walk_json_path(tier1, path)
                    self.assertIsNot(
                        resolved, cache_mod._MISSING,
                        msg=f"{rid}: emitted field_path {path!r} does NOT resolve into Tier-1",
                    )
                    self.assertEqual(
                        resolved, entry["fields"][field],
                        msg=f"{rid}: field_path {path!r} resolved to a different value",
                    )
                    emitted += 1
            self.assertGreater(emitted, 0, msg=f"{rid}: no field_paths were emitted")

        # Explicit regression assertion for the REST-single shape: path is $.body.<field>
        # (NOT the broken $.body[0].<field> the endswith('record') heuristic produced).
        rest_slice = self.cache.minimal_slice("hca:rest-single", fields, max_records=5)
        self.assertEqual(
            rest_slice["slice"][0]["field_paths"]["commitment"], "$.body.commitment")


# ===========================================================================
# 6. Cache dir is git-ignored (no real PII can ever be committed)
# ===========================================================================

class CacheDirGitIgnoredTest(unittest.TestCase):
    def test_default_cache_dir_is_under_acos_state(self):
        d = cache_mod.default_cache_dir()
        self.assertTrue(d.endswith(os.path.join(".acos", "state", "hca-cache")),
                        msg=f"cache dir not under .acos/state/: {d}")

    def test_cache_dir_is_git_ignored(self):
        # git check-ignore must report a probe path inside the cache dir as ignored.
        probe = os.path.join(cache_mod.default_cache_dir(), "tier1", "probe.json")
        proc = subprocess.run(
            ["git", "check-ignore", probe],
            cwd=_REPO_ROOT, capture_output=True, text=True,
        )
        # rc 0 => the path IS ignored. (rc 1 => NOT ignored => fail.)
        self.assertEqual(proc.returncode, 0,
                         msg=f"cache path is NOT git-ignored: {probe} (stderr={proc.stderr})")

    def test_defensive_gitignore_written_into_cache_dir_on_first_write(self):
        tmp = tempfile.mkdtemp(prefix="hca-cache-gi-")
        try:
            c = cache_mod.TwoTierCache(cache_dir=tmp)
            c.put_raw(_make_raw("hca:gi"))
            gi = os.path.join(tmp, ".gitignore")
            self.assertTrue(os.path.isfile(gi), "defensive .gitignore not written")
            with open(gi, "r", encoding="utf-8") as fh:
                self.assertIn("*", fh.read())
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
