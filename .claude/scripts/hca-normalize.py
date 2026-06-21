#!/usr/bin/env python3
"""hca-normalize.py — Tier-2 NormalizedAnswerRecord derivation (SLICE-HCA-03).

Builds the Tier-2 DERIVED view from a Tier-1 RawApiResponse (data-model.md B2):

    NormalizedAnswerRecord = {
        record_id,
        entity_type,
        fields:         { <field>: <normalized value> },        # typed projection
        field_bindings: { <field>: {raw_response_id, json_field_path} },  # back-pointers
        derived_from:   [ raw_response_id, ... ],               # Tier-1 sources
    }

CORE INVARIANT (slice-03 acceptance — HARD gate):
  Every Tier-2 field carries a back-pointer to its Tier-1 source, and 100% of those
  bindings MUST resolve to a real Tier-1 record at the cited json_field_path. A Tier-2
  field is derived ONLY from a real Tier-1 value — NEVER invented. The provenance engine
  (slice-04) re-verifies these bindings and REFUSES anything that does not resolve.

NORMALIZATION (slice-03 scope = wiring only):
  Unit/currency normalization is fully implemented in SLICE-HCA-05. Here we do an
  identity/typed projection: copy the Tier-1 field value through unchanged and record its
  exact json_field_path. A `_normalization` stub marks each field "passthrough" so slice-05
  can replace the transform without changing the binding contract.

SHAPES HANDLED (matches the live adapter output + fixtures):
  - GraphQL list   : body.data = [ {..}, .. ]   path base "$.body.data[i].<field>"
  - GraphQL single : body.record = {..}         path base "$.body.record.<field>"
  - REST single    : body = {loan_id: ..}        path base "$.body.<field>"

PII MINIMIZATION (data-model.md D): a configurable PII deny-set drops contact PII from the
normalized view by default (the raw stays in Tier-1 only). Numerics/ids/dates pass through.

GROUND RULES: Python 3 stdlib only; no network import; no model calls; no secrets.
"""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Optional


# ---------------------------------------------------------------------------
# PII minimization (derived view drops contact PII by default; raw keeps everything)
# ---------------------------------------------------------------------------

# Contact-PII field names minimized OUT of the Tier-2 view by default (data-model.md A2/D).
# The full value still lives in Tier-1 (need-to-know drill-down only).
DEFAULT_PII_FIELDS = frozenset({
    "email", "mobileNumber", "phone", "phoneNumber", "identificationNumber",
    "firstName", "lastName", "ssn", "taxId", "contact", "address",
})


# ---------------------------------------------------------------------------
# Path resolution (no git dependency)
# ---------------------------------------------------------------------------

def _canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


# ---------------------------------------------------------------------------
# Tier-1 body shape introspection
# ---------------------------------------------------------------------------

def _items_and_base(raw: dict) -> tuple:
    """Return (items, base_path, single). See hca-cache._tier1_items for the shapes."""
    body = raw.get("body")
    if isinstance(body, dict):
        if isinstance(body.get("data"), list):
            return body["data"], "$.body.data", False
        if isinstance(body.get("record"), dict):
            return [body["record"]], "$.body.record", True
        return [body], "$.body", True
    if isinstance(body, list):
        return body, "$.body", False
    return [], None, True


def _field_path(base_path: Optional[str], index: int, field: str, *, single: bool) -> str:
    if base_path is None:
        return f"$.{field}"
    if single:
        return f"{base_path}.{field}"
    return f"{base_path}[{index}].{field}"


def _entity_type(raw: dict, override: Optional[str]) -> str:
    return override or raw.get("entity_type") or "unknown"


def _record_id(raw_response_id: str, entity_type: str, index: int) -> str:
    stem = hashlib.sha256(
        f"{raw_response_id}|{entity_type}|{index}".encode("utf-8")
    ).hexdigest()[:24]
    return f"n2:{stem}"


def _projectable(value: Any) -> bool:
    """Scalars + flat lists/dicts of scalars are projectable into the typed view.

    We keep the projection deliberately shallow in slice-03: nested structures pass
    through as-is (their binding still points at the whole sub-tree) — slice-05 deepens
    typed/unit normalization. Always projectable; this hook is for future selectivity.
    """
    return True


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def normalize_record(raw_api_response: dict, *, entity_type: Optional[str] = None,
                     pii_fields: Optional[frozenset] = None,
                     keep_pii: bool = False) -> dict:
    """Build a Tier-2 NormalizedAnswerRecord (or a list of them for a list response).

    For a SINGLE-record Tier-1 body -> one NormalizedAnswerRecord (dict).
    For a LIST Tier-1 body          -> {"records": [NormalizedAnswerRecord, ...], ...}.

    Every projected field gets a field_bindings entry {raw_response_id, json_field_path}
    pointing back at its EXACT Tier-1 location. Derived ONLY from Tier-1 values.
    """
    if not isinstance(raw_api_response, dict):
        raise TypeError("raw_api_response must be a dict (RawApiResponse shape)")
    rid = raw_api_response.get("raw_response_id")
    if not rid:
        raise ValueError("raw_api_response is missing 'raw_response_id'")
    pii = DEFAULT_PII_FIELDS if pii_fields is None else pii_fields
    et = _entity_type(raw_api_response, entity_type)
    items, base_path, single = _items_and_base(raw_api_response)

    records = []
    for i, item in enumerate(items):
        records.append(_normalize_one(
            item=item, index=i, raw_response_id=rid, entity_type=et,
            base_path=base_path, single=single, pii=pii, keep_pii=keep_pii,
        ))

    if single:
        # single-record body -> return the lone record directly (or an empty stub)
        return records[0] if records else _empty_record(rid, et)
    return {
        "entity_type": et,
        "record_count": len(records),
        "records": records,
        "derived_from": [rid],
    }


def _normalize_one(*, item: Any, index: int, raw_response_id: str, entity_type: str,
                   base_path: Optional[str], single: bool, pii: frozenset,
                   keep_pii: bool) -> dict:
    fields: dict = {}
    field_bindings: dict = {}
    normalization: dict = {}
    minimized: list = []
    if isinstance(item, dict):
        for key, value in item.items():
            if (not keep_pii) and key in pii:
                minimized.append(key)
                continue  # PII dropped from the derived view (raw retains it in Tier-1)
            if not _projectable(value):
                continue
            path = _field_path(base_path, index, key, single=single)
            fields[key] = value                       # identity/typed projection (slice-03)
            field_bindings[key] = {
                "raw_response_id": raw_response_id,
                "json_field_path": path,
            }
            normalization[key] = "passthrough"        # slice-05 replaces with unit/currency
    return {
        "record_id": _record_id(raw_response_id, entity_type, index),
        "entity_type": entity_type,
        "fields": fields,
        "field_bindings": field_bindings,
        "derived_from": [raw_response_id],
        "_normalization": normalization,
        "_pii_minimized": minimized,
    }


def _empty_record(raw_response_id: str, entity_type: str) -> dict:
    return {
        "record_id": _record_id(raw_response_id, entity_type, 0),
        "entity_type": entity_type,
        "fields": {},
        "field_bindings": {},
        "derived_from": [raw_response_id],
        "_normalization": {},
        "_pii_minimized": [],
    }


def iter_normalized_records(normalized: dict):
    """Yield individual NormalizedAnswerRecords whether `normalized` is one record or a
    list-result wrapper. Convenience for callers/tests that don't care about the shape."""
    if "records" in normalized and isinstance(normalized["records"], list):
        for r in normalized["records"]:
            yield r
    else:
        yield normalized


def verify_bindings_against_tier1(normalized: dict, tier1_lookup) -> dict:
    """Verify EVERY field_binding of a NormalizedAnswerRecord resolves to a real Tier-1
    value at its cited json_field_path AND that the projected value matches.

    `tier1_lookup(raw_response_id) -> RawApiResponse-or-None`.

    Returns {"ok": bool, "checked": int, "failures": [ {record_id, field, reason}, ... ]}.
    This is the slice-03 hard gate (100% of bindings must resolve); the slice-04 provenance
    engine builds on the SAME resolution logic for refuse-on-missing. ANY unresolvable or
    mismatched binding => ok=False (REJECT).
    """
    cache = _load_cache()
    failures = []
    checked = 0
    for rec in iter_normalized_records(normalized):
        bindings = rec.get("field_bindings", {})
        values = rec.get("fields", {})
        for field, binding in bindings.items():
            checked += 1
            rid = binding.get("raw_response_id")
            path = binding.get("json_field_path")
            raw = tier1_lookup(rid) if rid else None
            if raw is None:
                failures.append({"record_id": rec.get("record_id"), "field": field,
                                 "reason": f"raw_response_id {rid!r} not found in Tier-1"})
                continue
            resolved = cache.walk_json_path(raw, path)
            if resolved is cache._MISSING:
                failures.append({"record_id": rec.get("record_id"), "field": field,
                                 "reason": f"json_field_path {path!r} does not resolve"})
                continue
            if _canonical_json(resolved) != _canonical_json(values.get(field)):
                failures.append({"record_id": rec.get("record_id"), "field": field,
                                 "reason": "Tier-1 value at path != normalized value"})
    return {"ok": not failures, "checked": checked, "failures": failures}


# ---------------------------------------------------------------------------
# Lazy sibling loader (hca-cache.py shares the json-path walker)
# ---------------------------------------------------------------------------

def _load_cache():
    import sys
    import importlib.util
    cached = sys.modules.get("hca_cache")
    if cached is not None:
        return cached
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "hca-cache.py")
    spec = importlib.util.spec_from_file_location("hca_cache", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["hca_cache"] = mod
    spec.loader.exec_module(mod)
    return mod


if __name__ == "__main__":
    print(json.dumps({
        "module": "hca-normalize",
        "default_pii_minimized_fields": sorted(DEFAULT_PII_FIELDS),
        "note": "Tier-2 derivation: identity projection + per-field back-pointers (slice-03).",
    }, indent=2))
