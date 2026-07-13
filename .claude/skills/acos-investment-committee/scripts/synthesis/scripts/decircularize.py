#!/usr/bin/env python3
"""
decircularize.py — Phase 2: the citogenesis firewall (PLAN.md §3 Stage 2, §15 finding).

The load-bearing safety property of the whole skill: agreement only counts as
corroboration when sources are genuinely INDEPENDENT. This module collapses
non-independent sources to a single representative BEFORE any corroboration counting,
so correlated agreement (same base model, same upstream doc, verbatim copies) can never
masquerade as independent confirmation.

Deterministic. No model calls. Stdlib only.

A `source` dict describes who asserted a claim and from where:
  {
    "id": "model-x",            # the asserting agent/model instance
    "family": "anthropic",      # model/provider family (for cross-family independence)
    "origin": "docA#p4",        # traced upstream data origin (None/"" = untraceable)
    "context_id": "P1",         # prompt/context/base-model fingerprint
    "text": "verbatim text",    # the asserted text (for fingerprinting)
    "value": 12.0,              # optional structured value (numeric/categorical)
    "is_engine_output": False,  # True if this is the engine's own prior output (self-citation)
  }

collapse(sources) returns:
  {
    "clusters": [[id, ...], ...],   # connected components of non-independent sources
    "independent_sources": int,      # number of clusters that are creditable corroborators
    "families": [fam, ...],          # distinct families across creditable clusters
    "representatives": [id, ...],    # one representative id per creditable cluster
    "flags": [str, ...],             # human-readable notes (no-provenance, self-citation, merges)
  }
"""

import re


def normalize_text(text):
    if not text:
        return ""
    return re.sub(r"\s+", " ", str(text).strip().lower())


def _creditable(src):
    """A source can act as an independent corroborator only if it is traceable and
    not the engine's own prior output."""
    if src.get("is_engine_output"):
        return False, "self-citation (engine's own prior output) — not a corroborator"
    if not src.get("origin"):
        return False, "no traceable provenance — not a corroborator"
    return True, None


def _non_independent(a, b):
    """True if two sources must be treated as ONE (non-independent)."""
    # shared upstream origin
    if a.get("origin") and a.get("origin") == b.get("origin"):
        return True
    # verbatim fingerprint: identical normalized text
    ta, tb = normalize_text(a.get("text")), normalize_text(b.get("text"))
    if ta and ta == tb:
        return True
    # identical structured value reproduced verbatim
    if a.get("value") is not None and a.get("value") == b.get("value") and ta and ta == tb:
        return True
    # same generative origin: same family AND same prompt/context/base-model fingerprint
    if a.get("family") and a.get("family") == b.get("family") \
            and a.get("context_id") and a.get("context_id") == b.get("context_id"):
        return True
    return False


class _UnionFind:
    def __init__(self, items):
        self.parent = {i: i for i in items}

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[ra] = rb


def collapse(sources):
    ids = [s["id"] for s in sources]
    by_id = {s["id"]: s for s in sources}
    uf = _UnionFind(ids)

    # union every non-independent pair
    for i in range(len(sources)):
        for j in range(i + 1, len(sources)):
            if _non_independent(sources[i], sources[j]):
                uf.union(sources[i]["id"], sources[j]["id"])

    # group into connected components
    comps = {}
    for sid in ids:
        comps.setdefault(uf.find(sid), []).append(sid)

    clusters = list(comps.values())
    flags = []
    representatives = []
    families = []

    for cluster in clusters:
        # a cluster is creditable if ANY member is creditable; pick a creditable rep
        rep = None
        for sid in cluster:
            ok, reason = _creditable(by_id[sid])
            if ok:
                rep = sid
                break
            elif reason and reason not in flags:
                flags.append(f"{sid}: {reason}")
        if rep is not None:
            representatives.append(rep)
            fam = by_id[rep].get("family")
            if fam:
                families.append(fam)
            if len(cluster) > 1:
                flags.append(f"collapsed correlated sources {sorted(cluster)} -> 1 independent vote")

    distinct_families = sorted(set(families))
    return {
        "clusters": [sorted(c) for c in clusters],
        "independent_sources": len(representatives),
        "families": distinct_families,
        "representatives": sorted(representatives),
        "flags": flags,
    }
