#!/usr/bin/env python3
"""test_hca_readonly_guard.py — Read-only contract guard (SLICE-HCA-10 missing test).

Proves the structural read-only invariant that the instructions require:

  1. FixtureBackend, LiveBackend, and HypercoreAdapter expose ZERO public method
     names that contain a forbidden mutating verb
     (create/update/delete/insert/post/patch/put/mutate/write/set/remove).

  2. A GraphQL mutation operation string is REFUSED at the operation level by the
     live client guard (assert_query_only in hca-live.py), BEFORE any network call.

These are belt-and-suspenders tests that complement the adapter's own
assert_read_only() helper and the READ_ONLY_CONTRACT_METHODS allow-list.

Run:
  python3 -m unittest discover -s .claude/scripts/tests -p 'test_hca_*.py' -v
"""

import importlib.util
import inspect
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


hca = _load("hca_adapter", "hca-adapter.py")
live = _load("hca_live", "hca-live.py")

# Independently authored forbidden-verb list (QA re-authors; do NOT import from module).
_MUTATING_VERBS = frozenset({
    "create", "update", "delete", "insert", "post", "patch", "put",
    "mutate", "write", "set", "remove",
})


def _public_method_names(cls):
    """Return the list of public (non-dunder) callable names on a class."""
    return [
        name for name, _ in inspect.getmembers(cls, predicate=callable)
        if not name.startswith("_")
    ]


def _contains_mutating_verb(method_name: str) -> str | None:
    """Return the first forbidden verb found in the method name, or None."""
    lo = method_name.lower()
    for verb in _MUTATING_VERBS:
        # Match verb as a standalone word component (full name, prefix, suffix, or infix).
        if (lo == verb
                or lo.startswith(verb + "_")
                or lo.endswith("_" + verb)
                or ("_" + verb + "_") in lo):
            return verb
    return None


# ===========================================================================
# 1. FixtureBackend — zero mutating method names
# ===========================================================================

class FixtureBackendReadOnlyTest(unittest.TestCase):
    """FixtureBackend must have no public method whose name contains a mutating verb."""

    def test_no_mutating_methods_on_fixture_backend(self):
        violations = []
        for name in _public_method_names(hca.FixtureBackend):
            verb = _contains_mutating_verb(name)
            if verb is not None:
                violations.append((name, verb))
        self.assertEqual(
            violations, [],
            msg=(f"FixtureBackend exposes mutating method(s): {violations} "
                 f"— read-only contract violated"),
        )

    def test_assert_read_only_utility_passes_fixture_backend(self):
        """The adapter's own assert_read_only() must not raise on FixtureBackend."""
        try:
            hca.assert_read_only(hca.FixtureBackend)
        except hca.ReadOnlyViolationError as e:
            self.fail(f"assert_read_only raised on FixtureBackend: {e}")


# ===========================================================================
# 2. LiveBackend — zero mutating method names
# ===========================================================================

class LiveBackendReadOnlyTest(unittest.TestCase):
    """LiveBackend must have no public method whose name contains a mutating verb."""

    def test_no_mutating_methods_on_live_backend(self):
        violations = []
        for name in _public_method_names(hca.LiveBackend):
            verb = _contains_mutating_verb(name)
            if verb is not None:
                violations.append((name, verb))
        self.assertEqual(
            violations, [],
            msg=(f"LiveBackend exposes mutating method(s): {violations} "
                 f"— read-only contract violated"),
        )

    def test_assert_read_only_utility_passes_live_backend(self):
        """The adapter's own assert_read_only() must not raise on LiveBackend."""
        try:
            hca.assert_read_only(hca.LiveBackend)
        except hca.ReadOnlyViolationError as e:
            self.fail(f"assert_read_only raised on LiveBackend: {e}")


# ===========================================================================
# 3. HypercoreAdapter — zero mutating method names
# ===========================================================================

class AdapterReadOnlyTest(unittest.TestCase):
    """HypercoreAdapter public surface must have no mutating method name."""

    def test_no_mutating_methods_on_hypercore_adapter(self):
        violations = []
        for name in _public_method_names(hca.HypercoreAdapter):
            verb = _contains_mutating_verb(name)
            if verb is not None:
                violations.append((name, verb))
        self.assertEqual(
            violations, [],
            msg=(f"HypercoreAdapter exposes mutating method(s): {violations} "
                 f"— read-only contract violated"),
        )

    def test_assert_read_only_utility_passes_hypercore_adapter(self):
        """The adapter's own assert_read_only() must not raise on HypercoreAdapter."""
        try:
            hca.assert_read_only(hca.HypercoreAdapter)
        except hca.ReadOnlyViolationError as e:
            self.fail(f"assert_read_only raised on HypercoreAdapter: {e}")

    def test_contract_base_has_no_mutating_methods(self):
        """The abstract base HypercoreBackend must itself be clean."""
        violations = []
        for name in _public_method_names(hca.HypercoreBackend):
            verb = _contains_mutating_verb(name)
            if verb is not None:
                violations.append((name, verb))
        self.assertEqual(violations, [],
                         msg=f"HypercoreBackend contract has mutating method(s): {violations}")


# ===========================================================================
# 4. GraphQL mutation operation string refused at operation level
# ===========================================================================

class GraphQLMutationRefusedTest(unittest.TestCase):
    """A GraphQL mutation string must be REFUSED at the operation level by the live
    client guard (live.assert_query_only / ReadOnlyViolation) — before any network call.

    This is the belt-and-suspenders operation-level guard described in hca-adapter.py's
    docstring (section: 'Read-only is enforced THREE ways').
    """

    def test_mutation_refused_at_operation_level(self):
        """A mutation document must raise ReadOnlyViolation."""
        with self.assertRaises(live.ReadOnlyViolation):
            live.assert_query_only("mutation M { deleteLoan(id: 1) { id } }")

    def test_subscription_refused_at_operation_level(self):
        """A subscription document must raise ReadOnlyViolation."""
        with self.assertRaises(live.ReadOnlyViolation):
            live.assert_query_only("subscription S { loanUpdated { id } }")

    def test_query_passes_operation_level_guard(self):
        """An explicit query document must pass the guard."""
        try:
            live.assert_query_only("query Q { loans { id } }")
        except live.ReadOnlyViolation as e:
            self.fail(f"ReadOnlyViolation raised for a valid query: {e}")

    def test_anonymous_query_passes(self):
        """An anonymous (shorthand) query passes — it implies a query operation."""
        try:
            live.assert_query_only("{ loans { id } }")
        except live.ReadOnlyViolation as e:
            self.fail(f"ReadOnlyViolation raised for anonymous query: {e}")

    def test_mutation_keyword_inside_string_literal_is_not_refused(self):
        """'mutation' as a string literal value must NOT trigger the guard."""
        try:
            live.assert_query_only('query Q { search(term: "mutation") { id } }')
        except live.ReadOnlyViolation as e:
            self.fail(f"False-positive: ReadOnlyViolation on a string literal: {e}")

    def test_mixed_query_and_mutation_document_refused(self):
        """A document with BOTH a query and a mutation operation must be refused."""
        doc = "query A { loan(id:1){id} }\nmutation B { updateLoan(id:1){id} }"
        with self.assertRaises(live.ReadOnlyViolation):
            live.assert_query_only(doc)

    def test_mutation_refused_before_any_network_call(self):
        """The transport guard must fire BEFORE any HTTP call (no token fetch)."""
        import json as _json

        calls = []

        def recording_opener(*, url, data, headers, method, timeout):
            calls.append(url)
            return 200, _json.dumps({})

        tm = live.TokenManager(
            token_url="https://auth/api-token",
            refresh_url="https://auth/api-token/token/refresh",
            client_id="fake-id", client_secret="fake-secret",
            opener=recording_opener,
        )
        tx = live.GraphQLTransport(
            gql_url="https://api/graphql",
            token_manager=tm,
            opener=recording_opener,
        )
        with self.assertRaises(live.ReadOnlyViolation):
            tx.execute("mutation M { deleteLoan(id: 1) { id } }")

        # Guard fires BEFORE any HTTP call — calls list must be empty.
        self.assertEqual(
            calls, [],
            msg="ReadOnlyViolation must block BEFORE any HTTP call (no network on mutation)",
        )


# ===========================================================================
# 5. FreshnessInvalidationHook — also read-only (SLICE-HCA-11 hook)
# ===========================================================================

class FreshnessHookReadOnlyTest(unittest.TestCase):
    """FreshnessInvalidationHook must have no public method containing a mutating verb."""

    def test_no_mutating_methods_on_freshness_hook(self):
        violations = []
        for name in _public_method_names(hca.FreshnessInvalidationHook):
            verb = _contains_mutating_verb(name)
            if verb is not None:
                violations.append((name, verb))
        self.assertEqual(
            violations, [],
            msg=(f"FreshnessInvalidationHook exposes mutating method(s): {violations}"),
        )

    def test_assert_read_only_utility_passes_freshness_hook(self):
        try:
            hca.assert_read_only(hca.FreshnessInvalidationHook)
        except hca.ReadOnlyViolationError as e:
            self.fail(f"assert_read_only raised on FreshnessInvalidationHook: {e}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
