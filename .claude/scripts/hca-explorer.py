#!/usr/bin/env python3
"""hca-explorer.py — CONFIDENCE-GRADED EXPLORER FALLBACK for acos-hypercore-ask.

WHY THIS EXISTS
---------------
Today, when a question does NOT map to a built, verified FIGURE (hca-figures.py), the
skill REFUSES. That is the correct default for any quantity we PROMISE is right — a figure
is reconciled + provenance-bound + consensus-checked. But it leaves a lot of perfectly
answerable "what is X on entity Y" questions on the floor, because no one has hand-built a
figure for every scalar field on every entity type.

This module is the trust-preserving fallback for those. Given a resolved entity (e.g. a
specific fundingEntity, loan, or client) and the keyword(s) in the question, it:

  1. INTROSPECTS that entity's GraphQL type to learn its real field list (cached in-process),
     keeping ONLY scalar fields (Float/Int/String/Boolean/Date/DateTime/ID/Decimal/Long).
     It does NOT auto-traverse nested object fields — that keeps the query bounded and safe.
  2. SCORES each scalar field name against the question keyword(s): an exact / substring
     match (after splitting camelCase into tokens) is HIGH; a difflib close-ratio >= 0.6 is
     MEDIUM; anything weaker is skipped.
  3. Builds ONE read-only GraphQL `query` that fetches the matched scalar fields for that
     entity by id, runs it through the SAME authenticated/TLS/read-only-guarded transport the
     figures use (via hca-figures._call_with_retry for 5xx resilience), and — if the flaky
     single-record resolver 500s — falls back to the entity's LIST query filtered by a
     name_hint and picks the row whose id matches.
  4. Returns each matched field's ACTUAL FETCHED value with a confidence grade + provenance.

NEVER-FABRICATE INVARIANT (the whole point)
-------------------------------------------
The explorer ONLY ever returns values it actually fetched from Hypercore. If nothing
matches the keywords, it returns an EMPTY result list — never a guess, never a placeholder.
The "confidence" grade reflects ONLY how sure we are that the matched FIELD answers the
question; it does NOT reflect whether the value is real. The value is always real (fetched)
or absent (omitted). A field that matched but came back null is reported with value=None and
a clear note — we do not invent a number for it.

Every explorer result is explicitly labelled "best-effort (not a verified figure)" in
`notes`, so a caller can never mistake an explorer answer for a reconciled figure.

CONFIDENCE POLICY
-----------------
  HIGH   (0.85) — exact / substring field-name match on a UNIQUELY-identified, firmly
                  resolved entity.
  MEDIUM (0.60) — fuzzy (difflib ratio >= 0.6) field-name match on a firmly resolved entity.
  LOW    (0.35) — the ENTITY ITSELF was only fuzzily resolved (caller passes
                  entity_fuzzy=True). Every field result is then capped at LOW regardless of
                  how strong the field-name match was — we can't be confident about a field on
                  an entity we're not sure we identified.

GROUND RULES (memory/decisions/2026-06-18-hca-build-ground-rules.md)
  - Python 3 stdlib ONLY (re, difflib, datetime, importlib). No third-party deps.
  - READ-ONLY: the only API touch is a GraphQL `query` (introspection + a by-id field read,
    or a list read for fallback). No mutation is ever constructed. The transport's
    `assert_query_only` guard applies underneath.
  - No model calls; never ANTHROPIC_API_KEY. No PII committed (tests use synthetic fakes).
"""

from __future__ import annotations

import datetime
import difflib
import importlib.util
import os
import re
import sys
from typing import Callable, Optional


# ---------------------------------------------------------------------------
# Sibling module loading (hyphenated filenames -> import by file path, cached).
# Mirrors the seam used by hca-figures.py / hca-adapter.py so every caller and the
# tests share ONE module instance under a stable sys.modules name.
# ---------------------------------------------------------------------------

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))


def _load(modname: str, filename: str):
    cached = sys.modules.get(modname)
    if cached is not None:
        return cached
    path = os.path.join(_THIS_DIR, filename)
    spec = importlib.util.spec_from_file_location(modname, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[modname] = mod
    spec.loader.exec_module(mod)
    return mod


def _adapter():
    return _load("hca_adapter", "hca-adapter.py")


def _live():
    return _load("hca_live", "hca-live.py")


def _figures():
    # We reuse hca-figures._call_with_retry for bounded 5xx resilience (single source of
    # truth for retry policy — no duplicated backoff constants here).
    return _load("hca_figures", "hca-figures.py")


# ---------------------------------------------------------------------------
# Confidence policy (single source of truth)
# ---------------------------------------------------------------------------

CONFIDENCE_HIGH = 0.85
CONFIDENCE_MEDIUM = 0.60
CONFIDENCE_LOW = 0.35

LABEL_HIGH = "high"
LABEL_MEDIUM = "medium"
LABEL_LOW = "low"

# difflib close-ratio threshold for a MEDIUM (fuzzy) field-name match.
FUZZY_RATIO_THRESHOLD = 0.6

# State vocabulary (mirrors the skill's terminal-state style; explorer is best-effort).
STATE_EXPLORED = "EXPLORED"          # at least one scalar field matched + was fetched
STATE_NO_MATCH = "NO_MATCH"          # introspection ok, but no field matched the keywords
STATE_NO_LIVE_DATA = "NO_LIVE_DATA"  # credentials absent — degrade, never fabricate
STATE_REFUSED = "REFUSED"            # a hard error (unknown entity / introspection failed)

# The explorer is ALWAYS best-effort. This banner is stamped into every result's notes so a
# caller can never confuse an explorer answer with a reconciled, verified figure.
BEST_EFFORT_NOTE = "best-effort (not a verified figure)"


# GraphQL SCALAR type names we keep. We do NOT auto-traverse nested OBJECT/LIST fields — that
# bounds the generated query and avoids fetching arbitrarily deep graphs. (Custom scalars the
# Hypercore schema uses — Date, DateTime, Decimal, Long — are included alongside the built-ins.)
_SCALAR_TYPE_NAMES = frozenset({
    "Float", "Int", "String", "Boolean", "Date", "DateTime", "ID", "Decimal", "Long",
})


# Stopwords dropped when extracting keyword tokens from a free-text question. Kept small and
# domain-agnostic — we only strip words that carry no field-matching signal.
_STOPWORDS = frozenset({
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "what", "whats", "what's", "which", "who", "whom", "whose", "how", "much", "many",
    "of", "for", "on", "in", "at", "to", "from", "by", "with", "and", "or", "as",
    "this", "that", "these", "those", "it", "its", "do", "does", "did", "has", "have",
    "had", "can", "could", "would", "should", "will", "shall", "me", "my", "our", "their",
    "show", "tell", "give", "get", "find", "value", "current", "total", "amount", "number",
    "please", "about", "any", "all", "there", "here", "now", "today",
})


# ---------------------------------------------------------------------------
# Tokenization helpers
# ---------------------------------------------------------------------------

# Splits a camelCase / PascalCase / snake_case identifier into lowercase tokens.
#   "totalCommitment"   -> ["total", "commitment"]
#   "activeLoansCount"  -> ["active", "loans", "count"]
#   "numOfActiveLoans"  -> ["num", "of", "active", "loans"]
#   "isActive"          -> ["is", "active"]
#   "refId"             -> ["ref", "id"]
#   "annual_interest"   -> ["annual", "interest"]
_CAMEL_BOUNDARY_RE = re.compile(
    r"[A-Z]+(?=[A-Z][a-z])"   # an acronym run before a TitleCase word (e.g. "ID" in "IDValue")
    r"|[A-Z]?[a-z0-9]+"       # a normal lowercase/number run, optionally led by one capital
    r"|[A-Z]+"                # a trailing all-caps run
)


def tokenize_identifier(name: str) -> list:
    """Split a field/identifier name into lowercase word tokens.

    Handles camelCase, PascalCase, snake_case, kebab-case and digit boundaries. Pure stdlib
    regex; deterministic. Returns a list of lowercase tokens (no empties).
    """
    if not name:
        return []
    # Normalize snake/kebab separators to spaces first, then split camelCase runs.
    spaced = re.sub(r"[_\-]+", " ", name)
    tokens: list = []
    for chunk in spaced.split():
        for m in _CAMEL_BOUNDARY_RE.finditer(chunk):
            tok = m.group(0).lower()
            if tok:
                tokens.append(tok)
    return tokens


def extract_keywords(question: str) -> list:
    """Extract lowercase keyword tokens from a free-text question, dropping stopwords.

    Splits on non-alphanumeric boundaries, lowercases, removes stopwords and 1-char tokens.
    Order-preserving + de-duplicated. Used by explore_question().
    """
    if not question:
        return []
    raw = re.findall(r"[A-Za-z0-9]+", question.lower())
    out: list = []
    seen = set()
    for w in raw:
        if len(w) <= 1:
            continue
        if w in _STOPWORDS:
            continue
        if w in seen:
            continue
        seen.add(w)
        out.append(w)
    return out


# ---------------------------------------------------------------------------
# GraphQL type-ref helpers (unwrap NON_NULL / LIST to the underlying named type)
# ---------------------------------------------------------------------------

def _unwrap_type(type_ref: Optional[dict]) -> tuple:
    """Unwrap a GraphQL type reference to (named_name, named_kind, is_list).

    Walks ofType through NON_NULL / LIST wrappers to the underlying named type.
    Returns (name, kind, is_list) where is_list is True if any LIST wrapper was seen.
    """
    is_list = False
    cur = type_ref
    name = None
    kind = None
    # bounded walk (GraphQL wrappers are shallow: NON_NULL[LIST[NON_NULL[Named]]] etc.)
    for _ in range(8):
        if not cur:
            break
        k = cur.get("kind")
        if k == "LIST":
            is_list = True
            cur = cur.get("ofType")
            continue
        if k == "NON_NULL":
            cur = cur.get("ofType")
            continue
        name = cur.get("name")
        kind = k
        break
    return name, kind, is_list


def _is_scalar_field(field: dict) -> bool:
    """True if a GraphQL field's underlying named type is a (non-list) SCALAR/ENUM we keep.

    We keep SCALAR kinds whose name is in _SCALAR_TYPE_NAMES. We deliberately SKIP:
      - LIST fields (a field returning a list — bounded-query discipline),
      - OBJECT / INTERFACE / UNION fields (nested objects — no auto-traversal),
      - scalars whose name is not in our allow-list (unknown custom scalars).
    """
    name, kind, is_list = _unwrap_type(field.get("type"))
    if is_list:
        return False
    if name is None:
        return False
    # Trust the introspected kind when present; otherwise fall back to the name allow-list.
    if kind == "SCALAR":
        return name in _SCALAR_TYPE_NAMES
    if kind in ("OBJECT", "INTERFACE", "UNION", "INPUT_OBJECT"):
        return False
    # kind == "ENUM" or kind is None (older/partial introspection) -> use the name allow-list.
    return name in _SCALAR_TYPE_NAMES


# ---------------------------------------------------------------------------
# Field scoring (keyword -> field-name match)
# ---------------------------------------------------------------------------

def score_field(field_name: str, keywords: list) -> tuple:
    """Score a single scalar field name against the question keyword(s).

    Returns (label, confidence, matched_keyword) or (None, 0.0, None) if no match.

      HIGH   — a keyword exactly equals a field token, OR a keyword is a substring of the
               whole (lowercased) field name, OR a field token is a substring of a keyword.
      MEDIUM — difflib SequenceMatcher ratio (keyword vs any field token, or vs the whole
               field name) >= FUZZY_RATIO_THRESHOLD.
      none   — otherwise (skip the field; NEVER fetch a field we can't justify).

    The tokenizer splits camelCase first so "commitment" matches "totalCommitment" exactly
    (token match) rather than only fuzzily.
    """
    if not field_name or not keywords:
        return None, 0.0, None
    whole = field_name.lower()
    tokens = tokenize_identifier(field_name)
    token_set = set(tokens)

    best_fuzzy = 0.0
    best_fuzzy_kw = None
    for kw in keywords:
        k = (kw or "").strip().lower()
        if not k:
            continue
        # --- HIGH: exact token match -------------------------------------------------
        if k in token_set:
            return LABEL_HIGH, CONFIDENCE_HIGH, kw
        # --- HIGH: substring either direction (whole field name <-> keyword) ---------
        if k in whole or whole in k:
            return LABEL_HIGH, CONFIDENCE_HIGH, kw
        # --- HIGH: keyword contains a field token, or a token contains the keyword ---
        for tok in tokens:
            if tok and (tok in k or k in tok):
                return LABEL_HIGH, CONFIDENCE_HIGH, kw
        # --- track best fuzzy ratio for a possible MEDIUM ----------------------------
        r_whole = difflib.SequenceMatcher(None, k, whole).ratio()
        if r_whole > best_fuzzy:
            best_fuzzy, best_fuzzy_kw = r_whole, kw
        for tok in tokens:
            r_tok = difflib.SequenceMatcher(None, k, tok).ratio()
            if r_tok > best_fuzzy:
                best_fuzzy, best_fuzzy_kw = r_tok, kw

    if best_fuzzy >= FUZZY_RATIO_THRESHOLD:
        return LABEL_MEDIUM, CONFIDENCE_MEDIUM, best_fuzzy_kw
    return None, 0.0, None


def _cap_for_fuzzy_entity(label: str, confidence: float) -> tuple:
    """If the ENTITY was only fuzzily resolved, cap every field result at LOW.

    We can't be confident about a field on an entity we're not sure we identified, so a
    fuzzy-entity flag overrides even a HIGH field-name match down to LOW.
    """
    return LABEL_LOW, CONFIDENCE_LOW


# ---------------------------------------------------------------------------
# Time helper (provenance)
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# The explorer
# ---------------------------------------------------------------------------

class EntityExplorer:
    """Confidence-graded explorer fallback over the live (or fake) read-only GraphQL client.

    Construct with a `client` exposing `raw_query(query, variables) -> data` (the live
    LiveGraphQLClient satisfies this; tests inject a fake). If no client is supplied, one is
    built lazily from the adapter's LiveBackend (creds from env) on first use.

    Public surface
    --------------
      explore(entity_type, entity_id, keywords, *, name_hint=None, entity_fuzzy=False,
              fetched_at=None) -> result dict
      explore_question(question, resolved_entity) -> result dict

    Result shape (both methods)
    ---------------------------
      {
        "state": EXPLORED | NO_MATCH | NO_LIVE_DATA | REFUSED,
        "entity_type": str,
        "entity_id": str,
        "graphql_type": str,            # the introspected type name (single_return)
        "keywords": [str, ...],
        "results": [
          {
            "field": str,
            "value": <fetched scalar | None>,
            "graphql_type": str,        # the field's scalar type name
            "confidence": float,        # 0..1
            "confidence_label": "high"|"medium"|"low",
            "matched_keyword": str,
            "provenance": {
              "operation": str,         # the GraphQL query field used (single_query or list_query)
              "json_field_path": str,   # e.g. "$.fundingEntity.totalCommitment"
              "fetched_at": str|None,
            },
          }, ...
        ],
        "notes": [str, ...],            # always includes BEST_EFFORT_NOTE
      }
    """

    def __init__(self, *, client=None,
                 sleep: Optional[Callable[[float], None]] = None):
        self._client = client
        self._sleep = sleep
        # in-process cache: graphql_type_name -> [ {name, scalar_type, raw_field}, ... ]
        self._field_cache: dict = {}

    # --- live client (lazy) ------------------------------------------------
    def _ensure_client(self):
        if self._client is not None:
            return self._client
        ad = _adapter()
        self._client = ad.LiveBackend().live_client()
        return self._client

    # --- registry lookup ---------------------------------------------------
    def _registry_entry(self, entity_type: str) -> Optional[dict]:
        return _live().ENTITY_REGISTRY.get(entity_type)

    # --- retry wrapper -----------------------------------------------------
    def _raw_query(self, client, query: str, variables: dict):
        """Run a read-only query with bounded 5xx retry (reusing hca-figures._call_with_retry).

        Returns the `data` dict (the retry helper returns (data, attempts, errors); we keep
        only the data here). Raises on an exhausted 5xx or a hard error — the caller classifies.
        """
        figs = _figures()
        kwargs = {}
        if self._sleep is not None:
            kwargs["sleep"] = self._sleep
        data, _attempts, _errors = figs._call_with_retry(client, query, variables, **kwargs)
        return data

    # --- step 1: introspect the entity's GraphQL type ----------------------
    def introspect_type(self, type_name: str) -> list:
        """Introspect a GraphQL type and return its SCALAR fields (cached in-process).

        Returns a list of {"name": str, "scalar_type": str} for the scalar fields only
        (nested objects/lists are excluded). Caches per type_name so repeated explores of the
        same entity type issue the introspection query at most once.

        Uses the bounded introspection query from the brief:
            query{ __type(name:"<TypeName>"){ fields{ name type{ name kind
                   ofType{ name kind ofType{ name } } } } } }
        """
        if type_name in self._field_cache:
            return self._field_cache[type_name]
        client = self._ensure_client()
        query = (
            'query { __type(name: "%s") { '
            "fields { name type { name kind "
            "ofType { name kind ofType { name kind ofType { name kind } } } } } "
            "} }" % type_name
        )
        data = self._raw_query(client, query, {})
        type_block = (data or {}).get("__type") or {}
        fields = type_block.get("fields") or []
        scalars: list = []
        for fl in fields:
            if not isinstance(fl, dict):
                continue
            if _is_scalar_field(fl):
                name, _kind, _is_list = _unwrap_type(fl.get("type"))
                scalars.append({"name": fl.get("name"), "scalar_type": name})
        self._field_cache[type_name] = scalars
        return scalars

    # --- main: explore -----------------------------------------------------
    def explore(self, entity_type: str, entity_id: str, keywords, *,
                name_hint: Optional[str] = None,
                entity_fuzzy: bool = False,
                fetched_at: Optional[str] = None) -> dict:
        """Explore `entity_type`/`entity_id` for scalar fields matching `keywords`.

        Steps: introspect the type -> score each scalar field against the keywords -> build ONE
        read-only query fetching the matched fields by id (falling back to the list query +
        name_hint on a flaky single-record 500) -> return each matched field's ACTUAL value with
        confidence + provenance. Sorted by confidence descending.

        `entity_fuzzy=True` caps EVERY field result at LOW (the entity itself was only fuzzily
        resolved). `name_hint` feeds the list-query fallback filter. `fetched_at` is stamped into
        provenance (defaults to None — caller may pass the resolve-time timestamp).

        NEVER fabricates: only fields actually returned by the query appear; an unmatched-keyword
        case yields an EMPTY results list (state NO_MATCH).
        """
        kws = [k for k in (keywords or []) if (k or "").strip()]
        notes = [BEST_EFFORT_NOTE]
        reg = self._registry_entry(entity_type)
        base = {
            "state": STATE_REFUSED,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "graphql_type": None,
            "keywords": kws,
            "results": [],
            "notes": notes,
        }
        if reg is None:
            notes.append(
                f"unknown entity_type {entity_type!r} — not in ENTITY_REGISTRY "
                f"(known: {sorted(_live().ENTITY_REGISTRY)}); refusing (never invent fields)"
            )
            return base
        if not entity_id:
            notes.append("no entity_id supplied — cannot fetch fields; refusing")
            return base
        if not kws:
            notes.append("no keywords supplied — nothing to match; returning empty result")
            base["state"] = STATE_NO_MATCH
            base["graphql_type"] = reg.get("single_return")
            return base

        type_name = reg.get("single_return")
        base["graphql_type"] = type_name

        # 1) Introspect the entity's GraphQL type (scalar fields only; cached).
        try:
            scalar_fields = self.introspect_type(type_name)
        except Exception as e:  # NoLiveDataError or transport/5xx failure
            return self._classify_failure(base, e,
                                          context=f"introspecting type {type_name!r}")

        if not scalar_fields:
            notes.append(
                f"type {type_name!r} exposed no scalar fields via introspection — "
                "nothing to explore; returning empty result"
            )
            base["state"] = STATE_NO_MATCH
            return base

        # 2) Score each scalar field against the keyword(s); keep only matches.
        matched: list = []  # list of (field_name, scalar_type, label, confidence, matched_kw)
        for sf in scalar_fields:
            fname = sf.get("name")
            label, conf, mk = score_field(fname, kws)
            if label is None:
                continue
            if entity_fuzzy:
                label, conf = _cap_for_fuzzy_entity(label, conf)
            matched.append((fname, sf.get("scalar_type"), label, conf, mk))

        if not matched:
            notes.append(
                "no scalar field matched the keyword(s) "
                f"{kws} on type {type_name!r}; returning empty result (no fabrication)"
            )
            base["state"] = STATE_NO_MATCH
            return base

        # De-duplicate field names (keep the strongest score per field) and order the selection.
        best_by_field: dict = {}
        for fname, stype, label, conf, mk in matched:
            prev = best_by_field.get(fname)
            if prev is None or conf > prev[2]:
                best_by_field[fname] = (stype, label, conf, mk)
        match_fields = sorted(best_by_field.keys())

        # 3) Fetch the matched scalar fields LIVE for this entity (single-by-id, list fallback).
        try:
            fetch = self._fetch_fields(reg, entity_id, match_fields, name_hint=name_hint)
        except Exception as e:
            return self._classify_failure(base, e, context="fetching matched fields")

        record = fetch.get("record")
        operation = fetch.get("operation")
        json_path_prefix = fetch.get("json_path_prefix")
        if fetch.get("fallback_used"):
            notes.append(
                f"single-record query was unavailable/flaky; fell back to the {operation!r} "
                f"list query filtered by name_hint and matched the row by id"
            )

        if not isinstance(record, dict):
            notes.append(
                f"entity {entity_type}:{entity_id} returned no record from {operation!r} — "
                "returning empty result (never invent an entity)"
            )
            base["state"] = STATE_NO_MATCH
            return base

        # 4) Assemble per-field results with the ACTUAL fetched value + provenance.
        ts = fetched_at if fetched_at is not None else None
        results: list = []
        for fname in match_fields:
            stype, label, conf, mk = best_by_field[fname]
            # Only report a field the record actually carries. A field that is present but
            # null is reported with value=None + a note; a field entirely absent is skipped
            # (it was requested but the backend returned nothing for it — never fabricate).
            if fname not in record:
                continue
            value = record.get(fname)
            entry = {
                "field": fname,
                "value": value,
                "graphql_type": stype,
                "confidence": conf,
                "confidence_label": label,
                "matched_keyword": mk,
                "provenance": {
                    "operation": operation,
                    "json_field_path": f"{json_path_prefix}.{fname}",
                    "fetched_at": ts,
                },
            }
            if value is None:
                entry["note"] = "field matched but returned null (reported as-is; not fabricated)"
            results.append(entry)

        if not results:
            notes.append(
                "matched field(s) were not present on the fetched record; "
                "returning empty result (no fabrication)"
            )
            base["state"] = STATE_NO_MATCH
            return base

        # Sort by confidence descending (stable: then by field name for determinism).
        results.sort(key=lambda r: (-r["confidence"], r["field"]))
        if entity_fuzzy:
            notes.append(
                "entity was only fuzzily resolved — every field result capped at LOW confidence"
            )
        notes.append(
            f"explored {len(results)} field(s) on {type_name} via {operation!r}; "
            "values are fetched live and reported as-is"
        )
        base["state"] = STATE_EXPLORED
        base["results"] = results
        return base

    # --- step 3 helper: build + run the fetch query ------------------------
    def _fetch_fields(self, reg: dict, entity_id: str, fields: list, *,
                      name_hint: Optional[str] = None) -> dict:
        """Fetch the requested scalar `fields` for one entity by id.

        Primary path: the single-record query `<single_query>(id: $id){ id <fields...> }`.
        Fallback (when the single-record resolver 500s after retries, or the entity has no
        single query): the list query filtered by `name_hint`, picking the row whose id matches.

        Returns {"record": <dict|None>, "operation": <query field used>,
                 "json_path_prefix": "$.<operation>", "fallback_used": bool}.
        """
        client = self._ensure_client()
        single_query = reg.get("single_query")
        # Always include id in the selection so the fallback can match by id, and so the
        # provenance path is anchored on a real key.
        sel_fields = list(dict.fromkeys(["id"] + list(fields)))
        selection = " ".join(sel_fields)

        # --- primary: single-record by id ----------------------------------
        if single_query:
            query = (
                "query HCAExplore($id: ID!) { "
                f"{single_query}(id: $id) {{ {selection} }} "
                "}"
            )
            try:
                data = self._raw_query(client, query, {"id": entity_id})
                record = (data or {}).get(single_query)
                return {
                    "record": record,
                    "operation": single_query,
                    "json_path_prefix": f"$.{single_query}",
                    "fallback_used": False,
                }
            except Exception as e:
                # Only fall back on the flaky 5xx (or when we can attempt a list query);
                # a non-5xx hard error with no list fallback re-raises to the caller.
                if not self._is_retryable_or_500(e) or not reg.get("list_query"):
                    raise

        # --- fallback: list query filtered by name_hint, match by id -------
        list_query = reg.get("list_query")
        if not list_query:
            # No single AND no list query -> we cannot fetch; surface an empty record.
            return {
                "record": None,
                "operation": single_query or "(none)",
                "json_path_prefix": f"$.{single_query or 'unknown'}",
                "fallback_used": False,
            }
        record = self._list_fallback(client, reg, entity_id, sel_fields, name_hint)
        return {
            "record": record,
            "operation": list_query,
            "json_path_prefix": f"$.{list_query}.pageItems",
            "fallback_used": True,
        }

    def _list_fallback(self, client, reg: dict, entity_id: str, sel_fields: list,
                       name_hint: Optional[str]):
        """Run the entity's list query filtered by name_hint and return the row matching id.

        Uses a single small page filtered by searchString=name_hint (most selective). The
        returned Paginated* shape is { totalFilteredRecords, pageItems }. We pick the row whose
        id == entity_id; if none matches we return None (never fabricate a row).
        """
        list_query = reg.get("list_query")
        selection = " ".join(sel_fields)
        # Build a filter input. Hypercore list filters accept `searchString`; if no name_hint
        # is given we send an empty filter (still bounded to one small page).
        filt = {"searchString": name_hint} if name_hint else {}
        query = (
            "query HCAExploreList($filter: JSON, $skip: Int, $limit: Int) { "
            f"{list_query}(filter: $filter, skip: $skip, limit: $limit) {{ "
            f"totalFilteredRecords pageItems {{ {selection} }} "
            "} }"
        )
        # NOTE: the real schema types the filter as e.g. LoansFilterInput; the live transport
        # validates the operation as read-only but does not require us to name the exact input
        # type for a fallback. We keep the page small (bounded) and match by id.
        variables = {"filter": filt, "skip": 0, "limit": 50}
        data = self._raw_query(client, query, variables)
        page = (data or {}).get(list_query) or {}
        items = page.get("pageItems") or []
        for it in items:
            if isinstance(it, dict) and str(it.get("id")) == str(entity_id):
                return it
        return None

    # --- failure classification --------------------------------------------
    def _is_retryable_or_500(self, exc: Exception) -> bool:
        """Reuse hca-figures._is_http_500 to detect the flaky server-error signal."""
        try:
            return bool(_figures()._is_http_500(exc))
        except Exception:
            return False

    def _classify_failure(self, base: dict, exc: Exception, *, context: str) -> dict:
        """Turn an exception into a terminal NO_LIVE_DATA or REFUSED result (never fabricate).

        Missing credentials -> NO_LIVE_DATA (graceful degradation). Anything else (introspection
        failure, exhausted 5xx, transport error) -> REFUSED with a structured note. No value is
        ever invented.
        """
        ad = _adapter()
        no_live = getattr(ad, "NoLiveDataError", None)
        if no_live is not None and isinstance(exc, no_live):
            base["state"] = STATE_NO_LIVE_DATA
            base["notes"].append(
                f"no live data while {context}: {str(exc)[:160]} "
                "(Hypercore access not provisioned; degrading, not fabricating)"
            )
            return base
        base["state"] = STATE_REFUSED
        base["notes"].append(
            f"explorer failed while {context}: {type(exc).__name__}: {str(exc)[:200]} "
            "(refusing rather than fabricating)"
        )
        return base

    # --- higher-level helper -----------------------------------------------
    def explore_question(self, question: str, resolved_entity: dict, *,
                         fetched_at: Optional[str] = None) -> dict:
        """Explore from a free-text question + a resolved entity descriptor.

        `resolved_entity` = {"entity_type": str, "id": str, "name": str|None,
                             "fuzzy": bool (optional)}.

        Extracts keyword tokens from the question (stopwords dropped), then calls explore().
        The entity's name is passed as the list-query fallback name_hint; `fuzzy=True` on the
        resolved entity caps every field result at LOW.
        """
        resolved_entity = resolved_entity or {}
        entity_type = resolved_entity.get("entity_type")
        entity_id = resolved_entity.get("id")
        name = resolved_entity.get("name")
        entity_fuzzy = bool(resolved_entity.get("fuzzy", False))
        keywords = extract_keywords(question)
        return self.explore(
            entity_type, entity_id, keywords,
            name_hint=name, entity_fuzzy=entity_fuzzy, fetched_at=fetched_at,
        )


# ---------------------------------------------------------------------------
# Tiny smoke surface (no network). Prints the confidence policy + a tokenization demo.
# The real CLI / routing is owned by SKILL.md / hca-deliver.py.
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json
    demo = {
        "confidence_policy": {
            "high": {"confidence": CONFIDENCE_HIGH, "basis": "exact/substring field-name match "
                     "on a uniquely-identified, firmly resolved entity"},
            "medium": {"confidence": CONFIDENCE_MEDIUM,
                       "basis": f"difflib ratio >= {FUZZY_RATIO_THRESHOLD} fuzzy field-name match"},
            "low": {"confidence": CONFIDENCE_LOW,
                    "basis": "the entity itself was only fuzzily resolved (caps all fields)"},
        },
        "scalar_types_kept": sorted(_SCALAR_TYPE_NAMES),
        "tokenize_examples": {
            "totalCommitment": tokenize_identifier("totalCommitment"),
            "activeLoansCount": tokenize_identifier("activeLoansCount"),
            "numOfActiveLoans": tokenize_identifier("numOfActiveLoans"),
        },
        "best_effort_note": BEST_EFFORT_NOTE,
    }
    print(json.dumps(demo, indent=2))
