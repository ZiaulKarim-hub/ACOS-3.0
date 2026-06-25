#!/usr/bin/env python3
"""hca-learned.py — the LEARNED-ROUTING store for acos-hypercore-ask.

The skill learns from confirmed user selections so the SAME kind of question routes correctly
next time WITHOUT asking again. The cardinal rule, enforced by this module's shape:

    LEARN THE ROUTING, NEVER THE VALUE.

A figure's value (an outstanding balance, a receivable, ...) changes daily; replaying a cached
number would serve a STALE/fabricated answer and break the skill's core guarantee. So this store
holds ONLY structural routing decisions — there is deliberately NO parameter anywhere here that
accepts a money value:

  1. metric_aliases     phrase  -> canonical metric word   ("amount due" -> "outstanding")
  2. entity_resolutions name    -> {entity_type, id, name}  ("ascent pref" -> loan 149)

On replay the orchestrator applies these to ROUTE the question, then RE-FETCHES the live number
through the full reconcile + provenance + gate pipeline. The routing is consistent; the value is
always fresh and cited.

Persistence: a single JSON file (atomic writes). Default location is a stable per-user app-data
path (one Hypercore portfolio -> one store, independent of cwd); override with HCA_LEARNED_PATH.
Stdlib only. Fail-open reads (a missing/corrupt file yields an empty store, never an exception).
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from typing import Optional


SCHEMA_VERSION = 1

# The canonical metric words the funding/portfolio figure selectors understand. A learned alias
# MUST map to one of these (anything else is rejected — we never invent a routing target).
CANONICAL_METRICS = ("outstanding", "receivable", "commitment", "participation")

# The name-resolvable entity types (mirrors hca-resolve.RESOLVABLE_ENTITY_TYPES).
ENTITY_TYPES = ("loan", "client", "equity", "fundingEntity")

_WS_RE = re.compile(r"\s+")
_PUNCT_RE = re.compile(r"[?.,:;!%'\"()]+")


def _default_path() -> str:
    env = os.environ.get("HCA_LEARNED_PATH")
    if env:
        return env
    return os.path.join(
        os.path.expanduser("~"), "Library", "Application Support",
        "acos-hypercore-ask", "learned.json")


def _norm(s: str) -> str:
    """Normalize a phrase/name for stable keying: lowercase, strip punctuation, collapse spaces."""
    if not isinstance(s, str):
        return ""
    s = _PUNCT_RE.sub(" ", s.lower())
    return _WS_RE.sub(" ", s).strip()


def _empty_store() -> dict:
    return {"version": SCHEMA_VERSION, "metric_aliases": {}, "entity_resolutions": {}, "audit": []}


class LearnedStore:
    """JSON-backed learned-routing store. All reads fail-open to an empty store."""

    def __init__(self, path: Optional[str] = None, *, now: Optional[str] = None):
        self.path = path or _default_path()
        # `now` is an injectable timestamp string for audit entries (tests pass a fixed value);
        # this module never calls datetime itself so it stays deterministic + import-safe.
        self._now = now

    # --- persistence -------------------------------------------------------
    def load(self) -> dict:
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return _empty_store()
            base = _empty_store()
            base.update({k: data.get(k, base[k]) for k in base})
            # defensive: ensure the sub-objects are the right shape
            if not isinstance(base["metric_aliases"], dict):
                base["metric_aliases"] = {}
            if not isinstance(base["entity_resolutions"], dict):
                base["entity_resolutions"] = {}
            if not isinstance(base["audit"], list):
                base["audit"] = []
            return base
        except (OSError, ValueError):
            return _empty_store()

    def _save(self, data: dict) -> None:
        d = os.path.dirname(self.path)
        if d:
            os.makedirs(d, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=".hca-learned-", suffix=".json", dir=d or None)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, sort_keys=True)
            os.replace(tmp, self.path)
        finally:
            try:
                os.unlink(tmp)
            except OSError:
                pass

    def _audit(self, data: dict, kind: str, **fields) -> None:
        entry = {"kind": kind}
        entry.update(fields)
        if self._now:
            entry["at"] = self._now
        data["audit"].append(entry)
        # keep the audit bounded (most-recent 500)
        if len(data["audit"]) > 500:
            data["audit"] = data["audit"][-500:]

    # --- record (the ONLY mutators — note: no value/number parameter exists) ----
    def record_metric_alias(self, phrase: str, metric: str) -> dict:
        """Learn 'phrase' -> a canonical metric word. Rejects unknown metrics."""
        phrase = _norm(phrase)
        metric = _norm(metric)
        if not phrase or metric not in CANONICAL_METRICS:
            return {"ok": False, "reason": f"invalid metric alias {phrase!r}->{metric!r} "
                                           f"(metric must be one of {CANONICAL_METRICS})"}
        data = self.load()
        data["metric_aliases"][phrase] = metric
        self._audit(data, "metric_alias", phrase=phrase, metric=metric)
        self._save(data)
        return {"ok": True, "phrase": phrase, "metric": metric}

    def record_entity_resolution(self, name: str, entity_type: str, entity_id: str,
                                 display_name: Optional[str] = None) -> dict:
        """Learn a name query -> a concrete entity (type + id). Rejects unknown entity types or a
        missing id. Stores the display name only as a human label; the id is what routes."""
        key = _norm(name)
        if not key or entity_type not in ENTITY_TYPES or not str(entity_id or "").strip():
            return {"ok": False, "reason": f"invalid entity resolution {name!r}->"
                                           f"{entity_type!r}:{entity_id!r}"}
        data = self.load()
        data["entity_resolutions"][key] = {
            "entity_type": entity_type, "id": str(entity_id), "name": display_name}
        self._audit(data, "entity_resolution", name=key, entity_type=entity_type, id=str(entity_id))
        self._save(data)
        return {"ok": True, "name": key, "entity_type": entity_type, "id": str(entity_id)}

    # --- lookup (replay) ---------------------------------------------------
    def alias_phrases(self) -> list:
        """Learned alias phrases, longest-first (so a specific phrase wins over a shorter one)."""
        return sorted(self.load()["metric_aliases"].keys(), key=len, reverse=True)

    def metric_for(self, question_lower: str) -> Optional[str]:
        """The canonical metric a learned alias maps this question to, or None. Longest match wins."""
        q = _norm(question_lower)
        aliases = self.load()["metric_aliases"]
        for phrase in sorted(aliases.keys(), key=len, reverse=True):
            if phrase and phrase in q:
                return aliases[phrase]
        return None

    def matched_alias_phrase(self, question_lower: str) -> Optional[str]:
        """The learned alias phrase that matched (so the caller can STRIP it from name tokens)."""
        q = _norm(question_lower)
        for phrase in self.alias_phrases():
            if phrase and phrase in q:
                return phrase
        return None

    def entity_for(self, name_query: str) -> Optional[dict]:
        """A learned {entity_type, id, name} for this exact (normalized) name query, or None."""
        return self.load()["entity_resolutions"].get(_norm(name_query))


_DEFAULT_STORE: Optional[LearnedStore] = None


def default_store() -> LearnedStore:
    global _DEFAULT_STORE
    if _DEFAULT_STORE is None:
        _DEFAULT_STORE = LearnedStore()
    return _DEFAULT_STORE


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Inspect/seed the hca-learned routing store.")
    p.add_argument("--path", default=None)
    p.add_argument("--show", action="store_true", help="print the current store")
    p.add_argument("--learn-metric", metavar="PHRASE=METRIC", help="e.g. 'amount due=outstanding'")
    p.add_argument("--learn-entity", metavar="NAME|TYPE|ID|LABEL",
                   help="e.g. 'ascent pref|loan|149|Ascent Pref Equity'")
    a = p.parse_args()
    store = LearnedStore(a.path)
    if a.learn_metric and "=" in a.learn_metric:
        ph, mt = a.learn_metric.split("=", 1)
        print(json.dumps(store.record_metric_alias(ph, mt)))
    if a.learn_entity and "|" in a.learn_entity:
        parts = a.learn_entity.split("|")
        nm, ty, idv = parts[0], parts[1], parts[2]
        label = parts[3] if len(parts) > 3 else None
        print(json.dumps(store.record_entity_resolution(nm, ty, idv, label)))
    if a.show or not (a.learn_metric or a.learn_entity):
        print(json.dumps(store.load(), indent=2, sort_keys=True))
