#!/usr/bin/env python3
"""hca-provenance.py — the universal provenance-binding engine (SLICE-HCA-04).

This is the core NO-HALLUCINATION gate of acos-hypercore-ask (data-model.md B3, invariant
1). It binds EVERY delivered value to a ProvenanceBinding that resolves to a cached Tier-1
RawApiResponse, and it REFUSES anything that cannot be resolved AND verified.

    ProvenanceBinding = {
        binding_id, value_ref,
        endpoint, request_params, timestamp,    # pulled from the resolved Tier-1 record
        json_field_path, raw_response_id,        # the back-pointer into Tier-1
        contributing: [ ... ],                   # for aggregates: one binding per source
    }

THE GUARANTEE (proven by NEGATIVE tests — slice-04 hard gate):
  - `bind_and_verify(value, binding)` loads Tier-1 by raw_response_id, walks
    json_field_path, and asserts the value at that path MATCHES the value being bound.
  - Missing binding (no raw_response_id / no path)        -> REFUSED.
  - Binding to a nonexistent raw_response_id              -> REFUSED.
  - Binding whose path does not resolve OR whose value at the path != the bound value
    (value-mismatch)                                       -> REFUSED.
  - A fabricated binding cannot pass: the value is re-read from Tier-1 and compared.
  No value with an unresolvable/mismatched binding is EVER returned in a deliverable state.

AGGREGATES:
  `bind_aggregate(value, contributing_bindings)` collects one resolvable binding per
  contributing source. If ANY contributor is unbindable -> the aggregate is REFUSED.

CONFIDENCE (data-model.md B6, invariant 5):
  `confidence_record(value_ref, source_count, ...)` forces single-source figures to
  confidence <= config `single_source_cap` (0.7) and flags them.

GROUND RULES: Python 3 stdlib only; no network import; no model calls; no secrets. This
module is read-only: it never writes Tier-1, never mutates a record, only RESOLVES + VERIFIES.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Outcomes
# ---------------------------------------------------------------------------

VERIFIED = "VERIFIED"
REFUSED = "REFUSED"

# Machine-readable refusal reason codes.
REASON_NO_BINDING = "NO_BINDING"                  # binding missing required fields
REASON_RAW_NOT_FOUND = "RAW_RESPONSE_NOT_FOUND"   # raw_response_id not in Tier-1
REASON_PATH_UNRESOLVED = "PATH_UNRESOLVED"        # json_field_path does not resolve
REASON_VALUE_MISMATCH = "VALUE_MISMATCH"          # Tier-1 value at path != bound value
REASON_NO_CONTRIBUTORS = "NO_CONTRIBUTORS"        # aggregate with zero bindings
REASON_CONTRIBUTOR_UNBINDABLE = "CONTRIBUTOR_UNBINDABLE"  # any aggregate source unbindable


class ProvenanceRefusal(RuntimeError):
    """Raised by the strict (`*_or_raise`) API when a value cannot be bound+verified.

    Carries the structured REFUSED result so callers can surface a machine-readable reason
    rather than silently delivering or guessing.
    """

    def __init__(self, result: dict):
        self.result = result
        super().__init__(f"{result.get('reason_code')}: {result.get('reason')}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _binding_id(value_ref: str, raw_response_id: str, json_field_path: str) -> str:
    stem = hashlib.sha256(
        f"{value_ref}|{raw_response_id}|{json_field_path}".encode("utf-8")
    ).hexdigest()[:24]
    return f"pb:{stem}"


def _values_match(a: Any, b: Any) -> bool:
    """Strict structural equality used for value-mismatch detection.

    Uses canonical JSON so dict key-order / int-vs-float-equal-int differences don't cause
    false negatives, while genuinely different values (incl. type changes like "5" vs 5)
    are caught. 5 and 5.0 are treated as equal (JSON-numeric), matching how the API emits
    them; everything else must match exactly.
    """
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return float(a) == float(b)
    return _canonical_json(a) == _canonical_json(b)


# ---------------------------------------------------------------------------
# Tier-1 resolution (shared json-path walker from hca-cache.py)
# ---------------------------------------------------------------------------

def _refused(value_ref: str, reason_code: str, reason: str, *,
             raw_response_id: Optional[str] = None,
             json_field_path: Optional[str] = None,
             contributing: Optional[list] = None) -> dict:
    return {
        "outcome": REFUSED,
        "deliverable": False,
        "value_ref": value_ref,
        "reason_code": reason_code,
        "reason": reason,
        "binding": None,
        "raw_response_id": raw_response_id,
        "json_field_path": json_field_path,
        "contributing": contributing or [],
    }


class ProvenanceEngine:
    """Binds + verifies delivered values against the Tier-1 cache.

    Construct with a Tier-1 lookup. Two equivalent ways to supply it:
      - `cache=<TwoTierCache>`   : uses cache.get_raw / cache.resolve_binding, OR
      - `tier1_lookup=callable(raw_response_id)->RawApiResponse-or-None`.
    """

    def __init__(self, *, cache=None, tier1_lookup=None,
                 single_source_cap: Optional[float] = None):
        self._cachelib = _load_cache()
        if cache is None and tier1_lookup is None:
            cache = self._cachelib.TwoTierCache()
        self._cache = cache
        self._lookup = tier1_lookup
        self._cap = (single_source_cap if single_source_cap is not None
                     else _read_single_source_cap())

    # --- Tier-1 fetch ------------------------------------------------------
    def _get_raw(self, raw_response_id: str) -> Optional[dict]:
        if self._lookup is not None:
            return self._lookup(raw_response_id)
        try:
            return self._cache.get_raw(raw_response_id)
        except Exception:
            return None

    # --- core: bind + verify a single value --------------------------------
    def bind_and_verify(self, value: Any, binding: dict, *,
                        value_ref: Optional[str] = None) -> dict:
        """Resolve {raw_response_id, json_field_path} to the exact Tier-1 value and confirm
        it MATCHES `value`. Returns a VERIFIED result (with a full ProvenanceBinding) or a
        structured REFUSED result. NEVER raises on a bad binding (use *_or_raise for that).
        """
        vref = value_ref or _stable_value_ref(value)
        if not isinstance(binding, dict):
            return _refused(vref, REASON_NO_BINDING, "binding is not a dict")
        rid = binding.get("raw_response_id")
        path = binding.get("json_field_path")
        if not rid or not path:
            return _refused(vref, REASON_NO_BINDING,
                            "binding missing raw_response_id and/or json_field_path",
                            raw_response_id=rid, json_field_path=path)
        raw = self._get_raw(rid)
        if raw is None:
            return _refused(vref, REASON_RAW_NOT_FOUND,
                            f"raw_response_id {rid!r} not found in Tier-1 cache",
                            raw_response_id=rid, json_field_path=path)
        resolved = self._cachelib.walk_json_path(raw, path)
        if resolved is self._cachelib._MISSING:
            return _refused(vref, REASON_PATH_UNRESOLVED,
                            f"json_field_path {path!r} does not resolve in Tier-1 record",
                            raw_response_id=rid, json_field_path=path)
        if not _values_match(resolved, value):
            return _refused(vref, REASON_VALUE_MISMATCH,
                            "value at json_field_path does not match the bound value "
                            "(possible fabrication / stale binding) — refusing",
                            raw_response_id=rid, json_field_path=path)
        # VERIFIED: build the full ProvenanceBinding from the resolved Tier-1 record.
        return {
            "outcome": VERIFIED,
            "deliverable": True,
            "value_ref": vref,
            "reason_code": None,
            "reason": "binding resolves to Tier-1 and value matches",
            "binding": self._build_binding(vref, rid, path, raw),
            "raw_response_id": rid,
            "json_field_path": path,
            "contributing": [],
        }

    def bind_and_verify_or_raise(self, value: Any, binding: dict, *,
                                 value_ref: Optional[str] = None) -> dict:
        """Strict variant: raise ProvenanceRefusal instead of returning a REFUSED dict.

        Use this where the surrounding code MUST NOT proceed with an unbound value — the
        invariant that no deliverable value escapes without a resolvable binding is then
        enforced by the type system (an exception, not a falsy flag).
        """
        result = self.bind_and_verify(value, binding, value_ref=value_ref)
        if result["outcome"] != VERIFIED:
            raise ProvenanceRefusal(result)
        return result

    # --- aggregates --------------------------------------------------------
    def bind_aggregate(self, value: Any, contributing_bindings: list, *,
                       value_ref: Optional[str] = None,
                       contributing_values: Optional[list] = None) -> dict:
        """Bind an aggregate value to one resolvable binding PER contributing source.

        `contributing_bindings` is a list of {raw_response_id, json_field_path} (each a
        source that fed the aggregate). If `contributing_values` is provided (aligned by
        index), each contributor's Tier-1 value is ALSO verified to match its declared
        value; otherwise only resolvability (path resolves to a real Tier-1 value) is
        required. ANY unbindable/mismatched contributor => the aggregate is REFUSED.
        """
        vref = value_ref or _stable_value_ref(value)
        if not contributing_bindings:
            return _refused(vref, REASON_NO_CONTRIBUTORS,
                            "aggregate has no contributing bindings — refusing")
        resolved_bindings = []
        for i, b in enumerate(contributing_bindings):
            if not isinstance(b, dict) or not b.get("raw_response_id") or not b.get("json_field_path"):
                return _refused(vref, REASON_CONTRIBUTOR_UNBINDABLE,
                                f"contributor #{i} missing raw_response_id/json_field_path",
                                contributing=resolved_bindings)
            raw = self._get_raw(b["raw_response_id"])
            if raw is None:
                return _refused(vref, REASON_CONTRIBUTOR_UNBINDABLE,
                                f"contributor #{i} raw_response_id "
                                f"{b['raw_response_id']!r} not found in Tier-1",
                                contributing=resolved_bindings)
            resolved = self._cachelib.walk_json_path(raw, b["json_field_path"])
            if resolved is self._cachelib._MISSING:
                return _refused(vref, REASON_CONTRIBUTOR_UNBINDABLE,
                                f"contributor #{i} path {b['json_field_path']!r} "
                                f"does not resolve",
                                contributing=resolved_bindings)
            if contributing_values is not None:
                declared = contributing_values[i] if i < len(contributing_values) else None
                if not _values_match(resolved, declared):
                    return _refused(vref, REASON_CONTRIBUTOR_UNBINDABLE,
                                    f"contributor #{i} value at path != declared value",
                                    contributing=resolved_bindings)
            resolved_bindings.append(
                self._build_binding(vref, b["raw_response_id"], b["json_field_path"], raw)
            )
        return {
            "outcome": VERIFIED,
            "deliverable": True,
            "value_ref": vref,
            "reason_code": None,
            "reason": f"aggregate bound to {len(resolved_bindings)} resolvable source(s)",
            "binding": {
                "binding_id": _binding_id(vref, "AGGREGATE", str(len(resolved_bindings))),
                "value_ref": vref,
                "aggregate": True,
                "contributing": resolved_bindings,
            },
            "raw_response_id": None,
            "json_field_path": None,
            "contributing": resolved_bindings,
        }

    def bind_aggregate_or_raise(self, value: Any, contributing_bindings: list, **kw) -> dict:
        result = self.bind_aggregate(value, contributing_bindings, **kw)
        if result["outcome"] != VERIFIED:
            raise ProvenanceRefusal(result)
        return result

    # --- batch over a NormalizedAnswerRecord (slice-03 bridge) -------------
    def verify_normalized_record(self, normalized: dict) -> dict:
        """Batch verifier: PASS only if EVERY field's binding resolves AND matches Tier-1.

        Walks a Tier-2 NormalizedAnswerRecord (single or list-wrapper) and runs
        bind_and_verify on each field using the record's own field_bindings + projected
        value. Returns {ok, checked, verified, refusals:[...]}. ok is True ONLY when there
        are zero refusals — a single unresolvable/mismatched binding fails the whole record
        (slice-03 hard gate + slice-04 refuse-on-missing).
        """
        normalize = _load_normalize()
        refusals = []
        verified = 0
        checked = 0
        for rec in normalize.iter_normalized_records(normalized):
            bindings = rec.get("field_bindings", {})
            values = rec.get("fields", {})
            for field, binding in bindings.items():
                checked += 1
                res = self.bind_and_verify(values.get(field), binding,
                                           value_ref=f"{rec.get('record_id')}.{field}")
                if res["outcome"] == VERIFIED:
                    verified += 1
                else:
                    refusals.append({"field": field, "record_id": rec.get("record_id"),
                                     "reason_code": res["reason_code"],
                                     "reason": res["reason"]})
        return {"ok": not refusals, "checked": checked, "verified": verified,
                "refusals": refusals}

    # --- confidence (single-source cap) ------------------------------------
    def confidence_record(self, value_ref: str, *, source_count: int,
                          agreement: Optional[float] = None,
                          basis: Optional[str] = None) -> dict:
        """Build a ConfidenceRecord (data-model.md B6).

        Single-source (source_count <= 1) figures are FORCED to confidence <=
        single_source_cap (config 0.7) and flagged `single_source: true`. With >= 2 sources
        confidence defaults to `agreement` (or 1.0) and is NOT capped by the single-source
        rule.
        """
        single = source_count <= 1
        if single:
            base = agreement if agreement is not None else self._cap
            confidence = min(base, self._cap)
        else:
            confidence = agreement if agreement is not None else 1.0
        return {
            "confidence_id": _binding_id(value_ref, "CONF", str(source_count)),
            "value_ref": value_ref,
            "confidence": round(float(confidence), 4),
            "single_source": single,
            "source_count": int(source_count),
            "capped_at": self._cap if single else None,
            "basis": basis or ("single-source figure (capped)" if single
                               else f"{source_count}-source agreement"),
        }

    # --- binding construction ---------------------------------------------
    def _build_binding(self, value_ref: str, raw_response_id: str,
                       json_field_path: str, raw: dict) -> dict:
        """Assemble a ProvenanceBinding, pulling endpoint/request_params/timestamp from the
        resolved Tier-1 record (data-model.md B3). No PII beyond the path is carried."""
        return {
            "binding_id": _binding_id(value_ref, raw_response_id, json_field_path),
            "value_ref": value_ref,
            "endpoint": raw.get("endpoint"),
            "request_params": raw.get("request_params"),
            "timestamp": raw.get("timestamp") or _tier1_fetched_at(raw),
            "json_field_path": json_field_path,
            "raw_response_id": raw_response_id,
            "contributing": [],
        }


# ---------------------------------------------------------------------------
# Module-level convenience (no engine instance needed)
# ---------------------------------------------------------------------------

def bind_and_verify(value: Any, binding: dict, *, cache=None, tier1_lookup=None,
                    value_ref: Optional[str] = None) -> dict:
    """Convenience: one-shot bind_and_verify without constructing an engine."""
    return ProvenanceEngine(cache=cache, tier1_lookup=tier1_lookup).bind_and_verify(
        value, binding, value_ref=value_ref)


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def _stable_value_ref(value: Any) -> str:
    return "val:" + hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()[:16]


def _tier1_fetched_at(raw: dict) -> Optional[str]:
    body = raw.get("body") or {}
    if isinstance(body, dict):
        prov = body.get("provenance") or {}
        if isinstance(prov, dict):
            return prov.get("fetched_at")
    return None


def _read_single_source_cap() -> float:
    """Scan config.yaml `confidence.single_source_cap` (stdlib; no YAML lib)."""
    cfg = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       os.pardir, os.pardir,
                       ".claude", "skills", "acos-hypercore-ask", "config.yaml")
    cfg = os.path.abspath(cfg)
    if not os.path.isfile(cfg):
        return 0.7
    in_block = False
    try:
        with open(cfg, "r", encoding="utf-8") as fh:
            for line in fh:
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                if not line[:1].isspace():
                    in_block = stripped.startswith("confidence:")
                    continue
                if in_block and stripped.startswith("single_source_cap:"):
                    val = stripped.split(":", 1)[1].split("#", 1)[0].strip()
                    try:
                        return float(val)
                    except ValueError:
                        return 0.7
    except OSError:
        return 0.7
    return 0.7


# ---------------------------------------------------------------------------
# Lazy sibling loaders (hyphenated filenames)
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


def _load_normalize():
    import sys
    import importlib.util
    cached = sys.modules.get("hca_normalize")
    if cached is not None:
        return cached
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "hca-normalize.py")
    spec = importlib.util.spec_from_file_location("hca_normalize", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["hca_normalize"] = mod
    spec.loader.exec_module(mod)
    return mod


if __name__ == "__main__":
    print(json.dumps({
        "module": "hca-provenance",
        "single_source_cap": _read_single_source_cap(),
        "refusal_reason_codes": [REASON_NO_BINDING, REASON_RAW_NOT_FOUND,
                                 REASON_PATH_UNRESOLVED, REASON_VALUE_MISMATCH,
                                 REASON_NO_CONTRIBUTORS, REASON_CONTRIBUTOR_UNBINDABLE],
        "guarantee": "no value with an unresolvable/mismatched binding is ever deliverable",
    }, indent=2))
