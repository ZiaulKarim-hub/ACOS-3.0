#!/usr/bin/env python3
"""hca-catalog-lookup.py — Phase 5: make the catalog ACTIONABLE.

Given a natural phrase ("per diem", "outstanding principal", "maturity date"), find the matching
Hypercore field(s): domain, exact path, value kind, a real example, the existing figure that
delivers it (if any), and the reliable working query. Importable (`lookup(query)`) for the skill
and a CLI for humans. Reads the committed `catalog-index.json` (no network).

    python3 hca-catalog-lookup.py --query "per diem"
    python3 hca-catalog-lookup.py --query "outstanding principal" --domain loan --top 5
"""
import argparse
import json
import os
import re

_HERE = os.path.dirname(os.path.abspath(__file__))
_INDEX = os.path.join(_HERE, "catalog-index.json")


def _tokens(s):
    return [t for t in re.split(r"[^a-z0-9]+", (s or "").lower()) if t]


def load_index(path=_INDEX):
    return json.load(open(path))


def lookup(query, *, index=None, domain=None, top=8):
    index = index or load_index()
    q = set(_tokens(query))
    if not q:
        return []
    results = []
    for d, dom in index["domains"].items():
        if domain and d != domain:
            continue
        for f in dom["fields"]:
            hay_name = set(_tokens(f.get("name") or ""))
            hay_syn = set(_tokens(" ".join(f.get("synonyms") or [])))
            hay_path = set(_tokens(f["path"]))
            score = 0
            score += 6 * len(q & hay_name)
            score += 5 * len(q & hay_syn)
            score += 2 * len(q & hay_path)
            # exact phrase in name/synonyms is a strong signal
            ql = query.strip().lower()
            if ql and (ql == (f.get("name") or "").lower()
                       or ql in [s.lower() for s in (f.get("synonyms") or [])]):
                score += 12
            if f.get("high_value"):
                score += 2
            if score <= 0:
                continue
            results.append((score, {
                "domain": d, "path": f["path"], "kind": f["kind"], "name": f.get("name"),
                "synonyms": f.get("synonyms") or [], "example": f.get("example"),
                "example_status": f.get("example_status"), "figure": f.get("figure") or None,
                "gotchas": f.get("gotchas") or None, "high_value": f.get("high_value", False),
                "root_type": dom["root_type"], "access": dom["access"],
                "reliability": dom["reliability"],
            }))
    results.sort(key=lambda r: -r[0])
    return [r[1] for r in results[:top]]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True)
    ap.add_argument("--domain", default=None)
    ap.add_argument("--top", type=int, default=8)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    if not os.path.exists(_INDEX):
        print("FAIL: catalog-index.json not found — build the catalog (hca-catalog-build.py).")
        return 2
    hits = lookup(args.query, domain=args.domain, top=args.top)
    if args.json:
        print(json.dumps(hits, indent=2, default=str))
        return 0 if hits else 1
    if not hits:
        print("No catalog match for %r." % args.query)
        return 1
    print("Matches for %r:\n" % args.query)
    for h in hits:
        fig = " [figure: %s]" % h["figure"] if h["figure"] else ""
        ex = (" e.g. %s" % h["example"]) if h["example_status"] == "ok" else ""
        print("  %-14s %s%s" % (h["domain"], h["name"] or h["path"], fig))
        print("      path: %s  (%s)%s" % (h["path"], h["kind"], ex))
        if h["gotchas"]:
            print("      ! %s" % h["gotchas"])
        print("      access: %s" % h["access"])
        print()
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
