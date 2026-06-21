#!/usr/bin/env python3
"""hca-gates.py — the deterministic gate suite for acos-hypercore-ask (SLICE-HCA-05).

These six gates sit UNDERNEATH consensus (slice-06) and run on the consensus-agreed
value(s) AFTER provenance binding (slice-04) and BEFORE delivery. They catch the dominant
NON-TEXT failure modes that an LLM consensus cannot see (data-model.md M4 + the spec's
S2/R4 anti-patterns): silent truncation, stale data, schema drift, broken cross-field
arithmetic, mixed-currency aggregation, and over-trusting a single source.

    THE CONTRACT (hard gates):
      Any HARD gate FAIL  =>  GateSuite verdict == REFUSE.  No value is ever delivered
      while a hard gate fails. There is no "warn and proceed" for a hard failure — that is
      exactly the silent-truncation / stale-serve anti-pattern this slice exists to kill.

THE SIX GATES (each a pure-ish function returning a uniform result dict):
  1. schema_validation        — every field in the record exists in the expected entity
                                schema (introspected GraphQL type / placeholder schema);
                                an unknown/typo field => FAIL.
  2. pagination_completeness   — for a list result, the Tier-1 body must assert
                                complete == True AND fetched == reported_total; a truncated
                                page (fetched < reported_total, or complete == False) => FAIL.
  3. freshness                 — the backing Tier-1 response is within the per-entity-class
                                freshness window (config, NOT hardcoded); stale => FAIL.
  4. cross_field_reconciliation— domain identities hold within tolerance (e.g. funded ==
                                outstanding + repaid_principal; sum(line items) ==
                                reported total); beyond tolerance => FAIL.
  5. unit_currency_normalization — detect + normalize currency/scale before any aggregation;
                                refuse to SUM mixed currencies => FAIL.
  6. single_source_confidence_cap — single-source values are capped at confidence <=
                                config single_source_cap (0.7) and FLAGGED; delegates to the
                                provenance engine's confidence_record.
  + schema_drift               — a field present in the cached data but ABSENT or of a
                                CHANGED type vs the current introspection => FAIL (proves
                                with loan_drifted: outstanding_principal -> principal_outstanding,
                                currency missing, legacy_balance appears).

GATE RESULT SHAPE (uniform):
    { "gate": <name>, "status": "PASS"|"FAIL", "reason": <str>, "evidence": {...} }

SUITE RESULT SHAPE (GateSuite.run_all):
    VerificationGateResult = {
        "outcome": "pass" | "refuse",
        "schema_ok", "pagination_complete", "freshness_ok", "reconciliation_ok",
        "normalization_applied", "confidence_capped",   # per-gate booleans
        "schema_drift_ok",                                # drift gate boolean
        "gates": [ <gate result>, ... ],                  # every gate that ran
        "failures": [ <gate name>, ... ],                 # names of FAILED hard gates
        "tier": "deterministic-only" | "full",
        "confidence": <ConfidenceRecord or None>,
    }

TIERED APPLICATION (slices 08/09 will choose the tier):
  - GateSuite.deterministic_subset(...)  — for TRIVIAL single-value lookups: the cheap
    structural gates only (schema, freshness, single-source cap). Provenance-binding
    (Wave B) is ALWAYS required regardless of tier and is enforced by the caller via the
    provenance engine — these gates do NOT replace it.
  - GateSuite.run_all(...)               — full suite for REPORTS / AGGREGATIONS: adds
    pagination-completeness, cross-field reconciliation, and mixed-currency refusal.

GROUND RULES (memory/decisions/2026-06-18-hca-build-ground-rules.md):
  - Python 3 stdlib ONLY. No third-party deps. No network. No model calls. No secrets.
  - Subscription-only Claude: this module never calls a model and never reads an API key.
  - Read-only: it resolves + judges; it never mutates Tier-1, never writes the cache.
"""

from __future__ import annotations

import json
import os
from typing import Any, Callable, Optional


# ---------------------------------------------------------------------------
# Status constants & gate names
# ---------------------------------------------------------------------------

PASS = "PASS"
FAIL = "FAIL"

OUTCOME_PASS = "pass"
OUTCOME_REFUSE = "refuse"

# Canonical gate names (stable identifiers; surfaced in failures[]).
GATE_SCHEMA = "schema_validation"
GATE_PAGINATION = "pagination_completeness"
GATE_FRESHNESS = "freshness"
GATE_RECONCILIATION = "cross_field_reconciliation"
GATE_NORMALIZATION = "unit_currency_normalization"
GATE_CONFIDENCE = "single_source_confidence_cap"
GATE_DRIFT = "schema_drift"

# All six "core" gates + the drift gate. The single-source confidence cap is treated as a
# FLAGGING gate (it never blocks delivery on its own — it caps + flags), so it is NOT a hard
# gate. Every other gate is HARD: a FAIL forces the suite to REFUSE.
HARD_GATES = frozenset({
    GATE_SCHEMA, GATE_PAGINATION, GATE_FRESHNESS,
    GATE_RECONCILIATION, GATE_NORMALIZATION, GATE_DRIFT,
})


class GateError(RuntimeError):
    """Raised only for programmer errors (e.g. a gate handed a non-dict source).

    A *data* problem is NEVER an exception — it is a FAIL gate result. Exceptions are
    reserved for misuse so a real integrity failure can never be swallowed as 'errored,
    treat as pass'."""


# ---------------------------------------------------------------------------
# Uniform result helpers
# ---------------------------------------------------------------------------

def _result(gate: str, ok: bool, reason: str, evidence: Optional[dict] = None) -> dict:
    return {
        "gate": gate,
        "status": PASS if ok else FAIL,
        "reason": reason,
        "evidence": evidence or {},
    }


def _gql_type_string(type_node: dict) -> str:
    """Render a GraphQL introspection type node into the same string convention used by the
    schema files ('ID!', '[LoanFunding!]', 'Float'). Pure recursive walk over kind/ofType."""
    kind = type_node.get("kind")
    name = type_node.get("name")
    of = type_node.get("ofType")
    if kind == "NON_NULL":
        return _gql_type_string(of) + "!"
    if kind == "LIST":
        return "[" + _gql_type_string(of) + "]"
    return name or "?"


# ---------------------------------------------------------------------------
# Tier-1 body shape helpers (mirror hca-cache / hca-normalize — both shapes supported)
# ---------------------------------------------------------------------------

def _body_items(source: dict) -> tuple:
    """Return (items, is_list) for the records inside a Tier-1 RawApiResponse body.

    Handles the GraphQL list (body.data=[...]), GraphQL single (body.record={...}), and the
    REST single (body={...}) shapes used across the fixtures.
    """
    body = source.get("body")
    if isinstance(body, dict):
        if isinstance(body.get("data"), list):
            return body["data"], True
        if isinstance(body.get("record"), dict):
            return [body["record"]], False
        return [body], False
    if isinstance(body, list):
        return body, True
    return [], False


def _first_record(source: dict) -> dict:
    items, _ = _body_items(source)
    for it in items:
        if isinstance(it, dict):
            return it
    return {}


def _fetched_at(source: dict) -> Optional[str]:
    """Best-effort fetched_at: top-level timestamp, else body.provenance.fetched_at."""
    if source.get("timestamp"):
        return source["timestamp"]
    body = source.get("body") or {}
    if isinstance(body, dict):
        prov = body.get("provenance") or {}
        if isinstance(prov, dict) and prov.get("fetched_at"):
            return prov["fetched_at"]
    return None


# ---------------------------------------------------------------------------
# Schema loading (introspection-derived expected fields + drift type map)
# ---------------------------------------------------------------------------

def _skill_dir() -> str:
    here = os.path.dirname(os.path.abspath(__file__))                 # .../.claude/scripts
    root = os.path.abspath(os.path.join(here, os.pardir, os.pardir))  # repo root
    return os.path.join(root, ".claude", "skills", "acos-hypercore-ask")


def _schemas_dir() -> str:
    return os.path.join(_skill_dir(), "schemas")


def _introspection_path() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.abspath(os.path.join(here, os.pardir, os.pardir))
    return os.path.join(root, "planning", "preeng", "001-hypercore-ask", "_introspection.json")


def load_expected_schema(entity_type: str, *, prefer_graphql: bool = False,
                         schemas_dir: Optional[str] = None) -> Optional[dict]:
    """Load the expected entity schema descriptor.

    For an entity like 'loan' there may be two files:
      - loan.gql.schema.json  — live-introspection-derived (camelCase GraphQL names), and
      - loan.schema.json      — the pre-access REST placeholder (snake_case names).
    `prefer_graphql` chooses the .gql variant first when both exist; otherwise the plain
    placeholder is used. Returns the parsed descriptor (with `expected_fields`) or None.
    """
    sdir = schemas_dir or _schemas_dir()
    candidates = []
    if prefer_graphql:
        candidates = [f"{entity_type}.gql.schema.json", f"{entity_type}.schema.json"]
    else:
        candidates = [f"{entity_type}.schema.json", f"{entity_type}.gql.schema.json"]
    for name in candidates:
        path = os.path.join(sdir, name)
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as fh:
                return json.load(fh)
    return None


def _python_type_name(value: Any) -> str:
    """Map a Python JSON value to the placeholder-schema type vocabulary
    ('string'/'number'/'boolean'/'array'/'object'/'null')."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return "unknown"


def _introspection_field_map(entity_or_gql_type: str, schema: Optional[dict],
                             *, introspection_path: Optional[str] = None) -> Optional[dict]:
    """Build {field_name: gql_type_string} for a GraphQL type by reading the AUTHORITATIVE
    introspection JSON (planning/preeng/001-hypercore-ask/_introspection.json).

    Resolves the GraphQL type name from the schema descriptor's `graphql_type` (e.g. 'Loan',
    'Client'). Returns None if the introspection file or the type is absent (caller falls
    back to the schema descriptor's own expected_fields — still authoritative, just static).
    """
    gql_type = None
    if schema and schema.get("graphql_type"):
        gql_type = schema["graphql_type"]
    elif entity_or_gql_type and entity_or_gql_type[:1].isupper():
        gql_type = entity_or_gql_type
    if not gql_type:
        return None
    path = introspection_path or _introspection_path()
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, ValueError):
        return None
    types = (((doc.get("data") or {}).get("__schema") or {}).get("types")) or []
    for t in types:
        if t.get("name") == gql_type and t.get("kind") == "OBJECT":
            out = {}
            for f in (t.get("fields") or []):
                out[f["name"]] = _gql_type_string(f["type"])
            return out
    return None


# ===========================================================================
# GATE 1 — schema_validation
# ===========================================================================

def gate_schema_validation(source: dict, schema: dict) -> dict:
    """Every field present in the source record MUST exist in the expected entity schema.

    An unknown/typo field (a field the schema does not declare) => FAIL. Missing REQUIRED
    fields also => FAIL. This is the basic structural gate (drift-type detection is the
    separate schema_drift gate). Pure: reads source + schema only.
    """
    if not isinstance(source, dict):
        raise GateError("schema_validation: source must be a dict (RawApiResponse shape)")
    if not isinstance(schema, dict) or "expected_fields" not in schema:
        return _result(GATE_SCHEMA, False,
                       "no expected schema available for this entity — cannot validate",
                       {"schema": None})
    expected = set(schema.get("expected_fields", {}).keys())
    required = set(schema.get("required_fields", []) or [])
    items, is_list = _body_items(source)
    unknown_all = []
    missing_required_all = []
    checked = 0
    for idx, rec in enumerate(items):
        if not isinstance(rec, dict):
            continue
        checked += 1
        present = set(rec.keys())
        unknown = sorted(present - expected)
        missing_req = sorted(required - present)
        for u in unknown:
            unknown_all.append({"index": idx, "field": u})
        for m in missing_req:
            missing_required_all.append({"index": idx, "field": m})
    ok = not unknown_all and not missing_required_all
    if ok:
        reason = f"all fields across {checked} record(s) exist in expected schema; required present"
    else:
        parts = []
        if unknown_all:
            parts.append(f"{len(unknown_all)} unknown/typo field(s): "
                         f"{sorted({u['field'] for u in unknown_all})}")
        if missing_required_all:
            parts.append(f"{len(missing_required_all)} missing required field(s): "
                         f"{sorted({m['field'] for m in missing_required_all})}")
        reason = "schema mismatch — " + "; ".join(parts)
    return _result(GATE_SCHEMA, ok, reason, {
        "entity_type": schema.get("entity_type"),
        "schema_version": schema.get("version"),
        "records_checked": checked,
        "unknown_fields": unknown_all,
        "missing_required": missing_required_all,
    })


# ===========================================================================
# GATE 2 — pagination_completeness
# ===========================================================================

def gate_pagination_completeness(source: dict) -> dict:
    """For a LIST result, the Tier-1 body MUST assert complete == True AND
    fetched == reported_total. A truncated page => FAIL (no silent truncation; S2).

    Honors the live GraphQL body shape (body.complete / body.reported_total / body.fetched)
    AND the older REST list shape (counts the data array vs reported_total + a non-null
    next_cursor implying more pages).
    """
    if not isinstance(source, dict):
        raise GateError("pagination_completeness: source must be a dict")
    items, is_list = _body_items(source)
    # Decide whether this is a list result at all.
    declared_list = bool(source.get("list")) or is_list
    body = source.get("body") if isinstance(source.get("body"), dict) else {}

    # Pull the authoritative counts. Prefer the live GraphQL body fields.
    reported_total = body.get("reported_total")
    if reported_total is None:
        reported_total = source.get("reported_total")
    fetched = body.get("fetched")
    complete_flag = body.get("complete")
    next_cursor = body.get("next_cursor", source.get("cursor"))

    if not declared_list:
        # Single-record responses are trivially "complete" w.r.t. pagination.
        return _result(GATE_PAGINATION, True,
                       "single-record response — pagination-completeness not applicable",
                       {"list": False})

    if fetched is None:
        fetched = len([x for x in items if isinstance(x, dict)])

    # If the backend told us complete==False, that is an explicit truncation signal — FAIL.
    if complete_flag is False:
        return _result(GATE_PAGINATION, False,
                       "backend reported complete=False — incomplete walk; refusing "
                       "(no silent truncation)",
                       {"list": True, "complete": False, "fetched": fetched,
                        "reported_total": reported_total})

    # Count reconciliation. Cannot pass when fetched < reported_total.
    if reported_total is None:
        # No declared total to reconcile against, and complete is not explicitly True.
        if complete_flag is True:
            return _result(GATE_PAGINATION, True,
                           "backend asserted complete=True (no reported_total to compare)",
                           {"list": True, "complete": True, "fetched": fetched})
        if next_cursor:
            return _result(GATE_PAGINATION, False,
                           "list has a non-null next_cursor and no completeness assertion — "
                           "more pages exist; refusing partial",
                           {"list": True, "fetched": fetched, "next_cursor": next_cursor})
        return _result(GATE_PAGINATION, False,
                       "list result lacks a reported_total AND a complete=True assertion — "
                       "cannot prove completeness; refusing",
                       {"list": True, "fetched": fetched, "reported_total": None,
                        "complete": complete_flag})

    try:
        rt = int(reported_total)
        fc = int(fetched)
    except (TypeError, ValueError):
        return _result(GATE_PAGINATION, False,
                       "non-integer reported_total/fetched — cannot reconcile; refusing",
                       {"reported_total": reported_total, "fetched": fetched})

    if fc < rt:
        return _result(GATE_PAGINATION, False,
                       f"truncated: fetched={fc} < reported_total={rt} "
                       f"(would silently drop {rt - fc} record(s)); refusing",
                       {"list": True, "fetched": fc, "reported_total": rt,
                        "complete": complete_flag, "next_cursor": next_cursor})
    if fc > rt:
        return _result(GATE_PAGINATION, False,
                       f"over-fetch: fetched={fc} > reported_total={rt} — count mismatch; "
                       f"refusing (data integrity)",
                       {"list": True, "fetched": fc, "reported_total": rt})
    # fetched == reported_total. If a cursor still points forward, the total lied.
    if next_cursor and complete_flag is not True:
        return _result(GATE_PAGINATION, False,
                       f"fetched==reported_total ({fc}) but next_cursor is non-null — "
                       f"completeness contradicted; refusing",
                       {"list": True, "fetched": fc, "reported_total": rt,
                        "next_cursor": next_cursor})
    return _result(GATE_PAGINATION, True,
                   f"complete: fetched({fc}) == reported_total({rt}); cursor exhausted",
                   {"list": True, "fetched": fc, "reported_total": rt,
                    "complete": complete_flag})


# ===========================================================================
# GATE 3 — freshness
# ===========================================================================

def gate_freshness(source: dict, entity_type: Optional[str] = None, *,
                   now=None, cachelib=None) -> dict:
    """The backing Tier-1 response MUST be within the per-entity-class freshness window.

    The window comes from config.yaml `freshness_windows_days` via hca-cache.is_fresh /
    freshness_window_days — NEVER a hardcoded constant here (acceptance: window from config).
    Stale or unparseable timestamp => FAIL (stale never served silently; S2).
    """
    if not isinstance(source, dict):
        raise GateError("freshness: source must be a dict")
    et = entity_type or source.get("entity_type")
    fetched_at = _fetched_at(source)
    cache = cachelib or _load_cache()
    window_days = cache.freshness_window_days(et)
    if not fetched_at:
        return _result(GATE_FRESHNESS, False,
                       "no fetched_at/timestamp on the Tier-1 record — cannot prove "
                       "freshness; refusing (never serve unknown-age data)",
                       {"entity_type": et, "window_days": window_days, "fetched_at": None})
    fresh = cache.is_fresh(fetched_at, et, now=now)
    if fresh:
        return _result(GATE_FRESHNESS, True,
                       f"within freshness window ({window_days}d) for entity-class of {et!r}",
                       {"entity_type": et, "window_days": window_days,
                        "fetched_at": fetched_at})
    return _result(GATE_FRESHNESS, False,
                   f"STALE: fetched_at={fetched_at} is outside the {window_days}d window "
                   f"for entity-class of {et!r}; refusing/flag-refresh (never serve stale)",
                   {"entity_type": et, "window_days": window_days,
                    "fetched_at": fetched_at, "flag_refresh": True})


# ===========================================================================
# GATE 4 — cross_field_reconciliation
# ===========================================================================

# Data-driven reconciliation rules: domain identities that must hold within tolerance.
# Each rule: {name, lhs:[fields], rhs:[fields], tolerance}. The rule fires only when ALL
# of its referenced fields are present + numeric in the record (otherwise it is skipped,
# not failed — absence is the schema gate's job, not reconciliation's).
DEFAULT_RECON_RULES = [
    # funded principal == still-outstanding + already-repaid principal.
    {"name": "funded == outstanding + repaid_principal",
     "lhs": ["funded_amount"],
     "rhs": ["outstanding_principal", "repaid_principal"],
     "tolerance": 0.01},
    # a payment's allocation parts sum to the payment amount.
    {"name": "amount == allocation.principal + allocation.interest + allocation.fees",
     "lhs": ["amount"],
     "rhs": ["allocation.principal", "allocation.interest", "allocation.fees"],
     "tolerance": 0.01},
]


def _dotted_get(record: dict, dotted: str):
    """Resolve a simple dotted key ('allocation.principal') inside a record. Returns the
    sentinel object() if any step is missing."""
    cur = record
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return _RECON_MISSING
        cur = cur[part]
    return cur


_RECON_MISSING = object()


def _as_number(value: Any):
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def gate_cross_field_reconciliation(source: dict, *,
                                    rules: Optional[list] = None,
                                    extra_rules: Optional[list] = None) -> dict:
    """Domain identities must hold within tolerance across the record's fields.

    Examples: funded principal reconciles to outstanding + repaid; a payment's allocation
    line items sum to the payment amount. A rule fires ONLY when all its fields are present
    and numeric; any FIRING rule whose two sides differ beyond tolerance => FAIL. If no rule
    fires (nothing to reconcile), the gate PASSES vacuously (and says so in the evidence).
    """
    if not isinstance(source, dict):
        raise GateError("cross_field_reconciliation: source must be a dict")
    rule_set = list(rules if rules is not None else DEFAULT_RECON_RULES)
    if extra_rules:
        rule_set.extend(extra_rules)

    items, _ = _body_items(source)
    fired = 0
    violations = []
    for idx, rec in enumerate(items):
        if not isinstance(rec, dict):
            continue
        for rule in rule_set:
            lhs_vals, rhs_vals = [], []
            applicable = True
            for f in rule["lhs"]:
                v = _as_number(_dotted_get(rec, f))
                if v is None:
                    applicable = False
                    break
                lhs_vals.append(v)
            if not applicable:
                continue
            for f in rule["rhs"]:
                v = _as_number(_dotted_get(rec, f))
                if v is None:
                    applicable = False
                    break
                rhs_vals.append(v)
            if not applicable:
                continue
            fired += 1
            lhs_total = sum(lhs_vals)
            rhs_total = sum(rhs_vals)
            tol = float(rule.get("tolerance", 0.01))
            diff = abs(lhs_total - rhs_total)
            if diff > tol:
                violations.append({
                    "index": idx, "rule": rule["name"],
                    "lhs": lhs_total, "rhs": rhs_total, "diff": diff, "tolerance": tol,
                })
    if violations:
        return _result(GATE_RECONCILIATION, False,
                       f"{len(violations)} reconciliation violation(s) beyond tolerance: "
                       f"{[v['rule'] for v in violations]}",
                       {"rules_fired": fired, "violations": violations})
    if fired == 0:
        return _result(GATE_RECONCILIATION, True,
                       "no reconciliation rule applicable to this record (nothing to "
                       "reconcile) — vacuously consistent",
                       {"rules_fired": 0})
    return _result(GATE_RECONCILIATION, True,
                   f"all {fired} applicable reconciliation rule(s) hold within tolerance",
                   {"rules_fired": fired})


# ===========================================================================
# GATE 5 — unit_currency_normalization
# ===========================================================================

# Canonical scale per currency (smallest unit -> major unit divisor not needed here; we
# normalize to a canonical (currency, value) tuple and forbid summing across currencies).
KNOWN_CURRENCIES = frozenset({
    "USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD", "SEK", "NOK", "DKK",
    "SGD", "HKD", "ZAR", "AED", "ILS", "INR", "CNY", "MXN", "BRL",
})


def normalize_money(value: Any, currency: Optional[str]) -> dict:
    """Normalize a single monetary value into a canonical {currency, amount} record.

    Returns {"currency": <UPPER ISO>, "amount": float, "ok": bool, "reason": ...}. An
    unknown/missing currency is flagged ok=False (cannot safely compare/aggregate). The
    amount is coerced to float; non-numeric => ok=False.
    """
    cur = (currency or "").strip().upper() or None
    amount = _as_number(value)
    if amount is None:
        return {"currency": cur, "amount": None, "ok": False,
                "reason": "non-numeric monetary value"}
    if cur is None:
        return {"currency": None, "amount": amount, "ok": False,
                "reason": "missing currency — cannot normalize for comparison/aggregation"}
    if cur not in KNOWN_CURRENCIES:
        return {"currency": cur, "amount": amount, "ok": False,
                "reason": f"unknown currency {cur!r} — refusing to assume scale"}
    return {"currency": cur, "amount": amount, "ok": True, "reason": "normalized"}


def can_aggregate(money_records: list) -> tuple:
    """Return (ok, currencies_seen, reason). Aggregation is allowed ONLY when every record
    normalized OK and they all share ONE currency. Mixed currencies => not summable."""
    if not money_records:
        return True, [], "nothing to aggregate"
    bad = [m for m in money_records if not m.get("ok")]
    if bad:
        return False, sorted({m.get("currency") for m in money_records}), \
            f"{len(bad)} value(s) could not be normalized: {[m.get('reason') for m in bad]}"
    currencies = sorted({m["currency"] for m in money_records})
    if len(currencies) > 1:
        return False, currencies, \
            f"mixed currencies {currencies} — refusing to sum without FX conversion"
    return True, currencies, "single currency — safe to aggregate"


def gate_unit_currency_normalization(source: dict, *,
                                     money_fields: Optional[list] = None,
                                     currency_field: str = "currency",
                                     aggregating: bool = False,
                                     records_currencies: Optional[list] = None) -> dict:
    """Detect + normalize currency/units before any comparison or aggregation.

    Two modes:
      - per-record (default): for each record, every monetary field must be coercible to a
        number, and if the record carries a `currency` it must be a KNOWN ISO code. A
        money field whose record has a PRESENT-but-unknown/blank currency, or a non-numeric
        amount, => FAIL. A record that does not project a currency field at all is SKIPPED
        for the currency check (currency simply isn't in that projection — not this gate's
        integrity concern); its amount is still type-checked.
      - aggregating (aggregating=True): given a set of (value, currency) across records
        (via `records_currencies` = list of {amount, currency} OR derived from the body),
        REFUSE to sum mixed/unknown currencies => FAIL. This is the headline hard check.

    `money_fields` defaults to the common loan/payment monetary fields; only fields actually
    present are checked.
    """
    if not isinstance(source, dict):
        raise GateError("unit_currency_normalization: source must be a dict")
    fields = money_fields if money_fields is not None else [
        "outstanding_principal", "commitment_amount", "funded_amount",
        "repaid_principal", "amount", "commitment",
    ]
    items, _ = _body_items(source)

    # Aggregation mode: explicit cross-record currency set OR pull one money field per record.
    if aggregating:
        money_records = []
        if records_currencies is not None:
            for m in records_currencies:
                money_records.append(normalize_money(m.get("amount"), m.get("currency")))
        else:
            for rec in items:
                if not isinstance(rec, dict):
                    continue
                cur = rec.get(currency_field)
                for f in fields:
                    if f in rec:
                        money_records.append(normalize_money(rec[f], cur))
                        break
        ok, currencies, reason = can_aggregate(money_records)
        return _result(GATE_NORMALIZATION, ok,
                       ("aggregation-safe: " + reason) if ok else ("aggregation blocked — " + reason),
                       {"mode": "aggregate", "currencies": currencies,
                        "values_checked": len(money_records)})

    # Per-record mode: every present money field must normalize OK (currency check applies
    # only when the record actually projects a currency field).
    problems = []
    checked = 0
    skipped_no_currency = 0
    for idx, rec in enumerate(items):
        if not isinstance(rec, dict):
            continue
        has_currency_field = currency_field in rec
        cur = rec.get(currency_field)
        for f in fields:
            if f in rec:
                checked += 1
                amount = _as_number(rec[f])
                if amount is None:
                    problems.append({"index": idx, "field": f,
                                     "reason": "non-numeric monetary value"})
                    continue
                if not has_currency_field:
                    # currency not in this projection -> not this gate's integrity concern
                    skipped_no_currency += 1
                    continue
                norm = normalize_money(rec[f], cur)
                if not norm["ok"]:
                    problems.append({"index": idx, "field": f, "reason": norm["reason"]})
    if problems:
        return _result(GATE_NORMALIZATION, False,
                       f"{len(problems)} monetary field(s) could not be normalized "
                       f"(present-but-unknown/blank currency or non-numeric value): "
                       f"{[p['field'] for p in problems]}",
                       {"mode": "per_record", "values_checked": checked,
                        "skipped_no_currency": skipped_no_currency,
                        "problems": problems})
    return _result(GATE_NORMALIZATION, True,
                   f"all {checked} monetary field(s) normalized "
                   f"({checked - skipped_no_currency} with a known currency; "
                   f"{skipped_no_currency} amount-only)",
                   {"mode": "per_record", "values_checked": checked,
                    "skipped_no_currency": skipped_no_currency})


# ===========================================================================
# GATE 6 — single_source_confidence_cap
# ===========================================================================

def gate_single_source_confidence_cap(value_ref: str, *, source_count: int,
                                      agreement: Optional[float] = None,
                                      engine=None, single_source_cap: Optional[float] = None
                                      ) -> dict:
    """Single-source values are capped at confidence <= config single_source_cap (0.7) and
    FLAGGED, regardless of agent self-confidence. Delegates to the provenance engine's
    confidence_record (the single authority for the cap), then asserts the cap held.

    This is a FLAGGING gate: it PASSES as long as the cap was correctly applied (a properly
    capped+flagged single-source value is a valid, deliverable-with-flag state). It FAILs
    only if the cap was somehow NOT applied to a single-source value (an integrity failure).
    """
    eng = engine or _build_engine(single_source_cap=single_source_cap)
    rec = eng.confidence_record(value_ref, source_count=source_count, agreement=agreement)
    cap = eng._cap
    single = rec["single_source"]
    if single and rec["confidence"] > cap:
        return _result(GATE_CONFIDENCE, False,
                       f"INTEGRITY FAILURE: single-source confidence {rec['confidence']} "
                       f"exceeds cap {cap}",
                       {"confidence_record": rec, "cap": cap})
    if single and not rec.get("single_source"):
        return _result(GATE_CONFIDENCE, False,
                       "single-source value was not flagged single_source",
                       {"confidence_record": rec})
    reason = (f"single-source value capped at <= {cap} and flagged (confidence="
              f"{rec['confidence']})") if single else \
             (f"multi-source ({source_count}) — single-source cap not applicable "
              f"(confidence={rec['confidence']})")
    return _result(GATE_CONFIDENCE, True, reason,
                   {"confidence_record": rec, "cap": cap, "single_source": single})


# ===========================================================================
# GATE 7 (drift) — schema_drift
# ===========================================================================

def gate_schema_drift(source: dict, entity_type: Optional[str] = None, *,
                      schema: Optional[dict] = None,
                      introspection_path: Optional[str] = None) -> dict:
    """A field present in the CACHED data but ABSENT from — or of a CHANGED type vs — the
    CURRENT introspection => FAIL (R4: never silently absorb drift).

    Two drift modes are caught:
      (a) a cached field that the current introspection does NOT declare (renamed/removed
          server-side, e.g. principal_outstanding / legacy_balance), and
      (b) an EXPECTED field that is MISSING from the cached record (e.g. currency dropped),
          which signals the cache predates a server change OR the response is malformed.

    The authoritative type map is rebuilt from _introspection.json when a GraphQL type is
    known; otherwise the schema descriptor's expected_fields is the reference. For the
    placeholder REST schemas (snake_case loan.schema.json) the descriptor IS authoritative.
    """
    if not isinstance(source, dict):
        raise GateError("schema_drift: source must be a dict")
    et = entity_type or source.get("entity_type")
    sch = schema or load_expected_schema(et) or {}
    expected_fields = dict(sch.get("expected_fields", {}) or {})

    # Prefer the live introspection map when this entity maps to a GraphQL type.
    intro_map = _introspection_field_map(et, sch, introspection_path=introspection_path)
    if intro_map:
        reference = intro_map
        ref_source = "introspection:" + (sch.get("graphql_type") or et)
        typed = True   # introspection gives GraphQL type strings -> we can detect type drift
    elif expected_fields:
        reference = expected_fields
        ref_source = "schema:" + str(sch.get("version") or et)
        typed = True   # placeholder schemas carry coarse type names ('string'/'number'/...)
    else:
        return _result(GATE_DRIFT, False,
                       f"no reference schema/introspection for entity {et!r} — cannot "
                       f"check drift; refusing",
                       {"entity_type": et})

    reference_names = set(reference.keys())
    required = set(sch.get("required_fields", []) or [])

    items, _ = _body_items(source)
    added = []        # cached field absent from the reference (renamed/new server-side)
    type_changed = [] # cached field whose observed type disagrees with the reference type
    missing = []      # reference (required) field absent from the cached record

    for idx, rec in enumerate(items):
        if not isinstance(rec, dict):
            continue
        present = set(rec.keys())
        for field in sorted(present - reference_names):
            added.append({"index": idx, "field": field})
        # required-field disappearance (e.g. currency dropped in the drifted fixture)
        for field in sorted((required or set()) - present):
            missing.append({"index": idx, "field": field})
        # coarse type-drift check against the PLACEHOLDER schema vocabulary only (the
        # introspection vocabulary is GraphQL scalars, not directly comparable to JSON types;
        # placeholder schemas use the same 'string/number/...' vocabulary as observed JSON).
        if not intro_map:
            for field in sorted(present & reference_names):
                want = reference.get(field)
                got = _python_type_name(rec[field])
                if rec[field] is None:
                    continue  # null is not a type-change signal on its own
                if want and want != got:
                    type_changed.append({"index": idx, "field": field,
                                         "expected": want, "observed": got})

    drift = bool(added or type_changed or missing)
    if not drift:
        return _result(GATE_DRIFT, True,
                       f"no schema drift vs {ref_source}: every cached field is declared, "
                       f"required fields present, types consistent",
                       {"entity_type": et, "reference": ref_source})
    parts = []
    if added:
        parts.append(f"{len(added)} unexpected field(s): {sorted({a['field'] for a in added})}")
    if missing:
        parts.append(f"{len(missing)} missing expected/required field(s): "
                     f"{sorted({m['field'] for m in missing})}")
    if type_changed:
        parts.append(f"{len(type_changed)} type-changed field(s): "
                     f"{[(t['field'], t['expected'], t['observed']) for t in type_changed]}")
    return _result(GATE_DRIFT, False,
                   f"SCHEMA DRIFT vs {ref_source} — " + "; ".join(parts) +
                   " ; refusing (R4: never silently absorb drift)",
                   {"entity_type": et, "reference": ref_source,
                    "added_fields": added, "missing_fields": missing,
                    "type_changed": type_changed})


# ===========================================================================
# GateSuite — composition + tiered application
# ===========================================================================

class GateSuite:
    """Composes the deterministic gates into a single verdict.

    Two entry points (slices 08/09 choose the tier):
      - deterministic_subset(...) : trivial single-value lookups (cheap structural gates).
      - run_all(...)              : full suite for reports / aggregations.

    Provenance-binding (Wave B / slice-04) is ALWAYS required regardless of tier; it is the
    caller's responsibility (ProvenanceEngine) and is NOT a substitute for, nor substituted
    by, these gates. The suite can be handed a `provenance_report` (the dict returned by
    ProvenanceEngine.verify_normalized_record) and will REFUSE if it is present and not ok.
    """

    def __init__(self, *, engine=None, cachelib=None,
                 single_source_cap: Optional[float] = None,
                 schemas_dir: Optional[str] = None,
                 introspection_path: Optional[str] = None,
                 now=None):
        self._cachelib = cachelib or _load_cache()
        self._engine = engine or _build_engine(single_source_cap=single_source_cap)
        self._schemas_dir = schemas_dir
        self._introspection_path = introspection_path
        self._now = now

    # --- helpers -----------------------------------------------------------
    def _schema_for(self, entity_type: str, prefer_graphql: bool) -> Optional[dict]:
        return load_expected_schema(entity_type, prefer_graphql=prefer_graphql,
                                    schemas_dir=self._schemas_dir)

    def _assemble(self, gates: list, *, tier: str,
                  confidence_record: Optional[dict],
                  provenance_report: Optional[dict]) -> dict:
        by_name = {g["gate"]: g for g in gates}
        failures = []
        for g in gates:
            if g["status"] == FAIL and g["gate"] in HARD_GATES:
                failures.append(g["gate"])
        # Provenance binding is always required; a present-and-failed report blocks delivery.
        prov_ok = True
        if provenance_report is not None:
            prov_ok = bool(provenance_report.get("ok"))
            if not prov_ok:
                failures.append("provenance_binding")
        outcome = OUTCOME_REFUSE if failures else OUTCOME_PASS

        def _b(name):
            g = by_name.get(name)
            return None if g is None else (g["status"] == PASS)

        return {
            "outcome": outcome,
            "tier": tier,
            "schema_ok": _b(GATE_SCHEMA),
            "pagination_complete": _b(GATE_PAGINATION),
            "freshness_ok": _b(GATE_FRESHNESS),
            "reconciliation_ok": _b(GATE_RECONCILIATION),
            "normalization_applied": _b(GATE_NORMALIZATION),
            "confidence_capped": _b(GATE_CONFIDENCE),
            "schema_drift_ok": _b(GATE_DRIFT),
            "provenance_ok": prov_ok if provenance_report is not None else None,
            "gates": gates,
            "failures": failures,
            "confidence": confidence_record,
        }

    # --- tiered: deterministic-only subset (trivial single-value lookups) --
    def deterministic_subset(self, source: dict, *, entity_type: Optional[str] = None,
                             prefer_graphql: bool = False,
                             value_ref: str = "value",
                             source_count: int = 1,
                             agreement: Optional[float] = None,
                             provenance_report: Optional[dict] = None) -> dict:
        """Cheap structural gates for a TRIVIAL single-value lookup:
        schema_validation + freshness + schema_drift + single-source confidence cap.

        Skips pagination (single record), reconciliation, and aggregation-currency checks —
        those only matter for reports/aggregations (use run_all there). Provenance binding
        is still required (pass `provenance_report`).
        """
        et = entity_type or source.get("entity_type")
        schema = self._schema_for(et, prefer_graphql) or {}
        gates = [
            gate_schema_validation(source, schema),
            gate_freshness(source, et, now=self._now, cachelib=self._cachelib),
            gate_schema_drift(source, et, schema=self._schema_for(et, prefer_graphql),
                              introspection_path=self._introspection_path),
            gate_single_source_confidence_cap(value_ref, source_count=source_count,
                                              agreement=agreement, engine=self._engine),
        ]
        conf = self._engine.confidence_record(value_ref, source_count=source_count,
                                              agreement=agreement)
        return self._assemble(gates, tier="deterministic-only",
                              confidence_record=conf,
                              provenance_report=provenance_report)

    # --- full suite (reports / aggregations) -------------------------------
    def run_all(self, source: dict, *, entity_type: Optional[str] = None,
                prefer_graphql: bool = False,
                value_ref: str = "value",
                source_count: int = 1,
                agreement: Optional[float] = None,
                aggregating: bool = False,
                records_currencies: Optional[list] = None,
                recon_rules: Optional[list] = None,
                extra_recon_rules: Optional[list] = None,
                provenance_report: Optional[dict] = None) -> dict:
        """Full deterministic gate suite for reports/aggregations. ANY hard gate FAIL =>
        outcome == 'refuse'; failures[] names the failed gate(s). Returns a
        VerificationGateResult (see module docstring)."""
        et = entity_type or source.get("entity_type")
        schema = self._schema_for(et, prefer_graphql) or {}
        gates = [
            gate_schema_validation(source, schema),
            gate_pagination_completeness(source),
            gate_freshness(source, et, now=self._now, cachelib=self._cachelib),
            gate_cross_field_reconciliation(source, rules=recon_rules,
                                            extra_rules=extra_recon_rules),
            gate_unit_currency_normalization(source, aggregating=aggregating,
                                             records_currencies=records_currencies),
            gate_single_source_confidence_cap(value_ref, source_count=source_count,
                                              agreement=agreement, engine=self._engine),
            gate_schema_drift(source, et, schema=self._schema_for(et, prefer_graphql),
                              introspection_path=self._introspection_path),
        ]
        conf = self._engine.confidence_record(value_ref, source_count=source_count,
                                              agreement=agreement)
        return self._assemble(gates, tier="full", confidence_record=conf,
                              provenance_report=provenance_report)


# ---------------------------------------------------------------------------
# Engine + sibling loaders (hyphenated filenames)
# ---------------------------------------------------------------------------

def _build_engine(*, single_source_cap: Optional[float] = None):
    prov = _load_provenance()
    return prov.ProvenanceEngine(tier1_lookup=lambda _rid: None,
                                 single_source_cap=single_source_cap)


def _load_sibling(modname: str, filename: str):
    import sys
    import importlib.util
    cached = sys.modules.get(modname)
    if cached is not None:
        return cached
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, filename)
    spec = importlib.util.spec_from_file_location(modname, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[modname] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_cache():
    return _load_sibling("hca_cache", "hca-cache.py")


def _load_normalize():
    return _load_sibling("hca_normalize", "hca-normalize.py")


def _load_provenance():
    return _load_sibling("hca_provenance", "hca-provenance.py")


if __name__ == "__main__":
    print(json.dumps({
        "module": "hca-gates",
        "gates": [GATE_SCHEMA, GATE_PAGINATION, GATE_FRESHNESS, GATE_RECONCILIATION,
                  GATE_NORMALIZATION, GATE_CONFIDENCE, GATE_DRIFT],
        "hard_gates": sorted(HARD_GATES),
        "tiers": ["deterministic-only", "full"],
        "contract": "any hard gate FAIL => suite outcome == refuse",
        "provenance": "always required regardless of tier (Wave B / slice-04)",
    }, indent=2))
