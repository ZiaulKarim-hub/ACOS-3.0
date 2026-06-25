#!/usr/bin/env python3
"""hca-catalog-probe.py — Phase 3 helper: turn harvested flat leaf-paths back into a live GraphQL
selection, fetch ONE representative entity, and map every path to its real fetched value.

This is the mechanism the catalog needs so "live-probe every money/rate field" costs a HANDFUL of
deep fetches (one per value block) instead of one API call per field: select many leaves at once,
read them all from a single response.

`paths_to_selection` compiles dotted paths (with `[]` list markers) into a nested GraphQL selection:
    summary.totalOutstanding.principal
    summary.totalExpected.fees[].fee.value
  ->  summary { totalOutstanding { principal } totalExpected { fees { fee { value } } } }

CLI (validation): probe the loan `summary` block for a named loan and print path -> value.
    doppler run --project hypercore-ask --config dev_personal -- \
        python3 hca-catalog-probe.py --domain loan --prefix summary --name "Beehive" --limit 30
"""
import argparse
import importlib.util
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS = os.path.abspath(os.path.join(_HERE, os.pardir, os.pardir, os.pardir, "scripts"))


def _load(mod, fname, where):
    path = os.path.join(where, fname)
    spec = importlib.util.spec_from_file_location(mod, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def paths_to_selection(paths):
    """Compile dotted leaf-paths (list markers `[]` allowed) into a nested {} selection tree, then
    render GraphQL. Returns the selection string (no outer braces)."""
    tree = {}
    for p in paths:
        node = tree
        for seg in p.split("."):
            key = seg.replace("[]", "")
            node = node.setdefault(key, {})
    def render(node):
        parts = []
        for k, sub in node.items():
            if sub:
                parts.append("%s { %s }" % (k, render(sub)))
            else:
                parts.append(k)
        return " ".join(parts)
    return render(tree)


def walk_value(obj, dotted):
    """Resolve a dotted path against a fetched object; `[]` means 'first element of the list'."""
    cur = obj
    for raw in dotted.split("."):
        is_list = raw.endswith("[]")
        key = raw.replace("[]", "")
        if not isinstance(cur, dict) or key not in cur:
            return ("__ABSENT__", None)
        cur = cur[key]
        if is_list:
            if not isinstance(cur, list) or not cur:
                return ("__EMPTY_LIST__", None)
            cur = cur[0]
    return ("ok", cur)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", default=os.path.join(_HERE, "catalog-candidates.json"))
    ap.add_argument("--domain", required=True)
    ap.add_argument("--prefix", default="", help="only probe active leaves whose path starts here")
    ap.add_argument("--name", required=True, help="entity search string (loan/investor/client name)")
    ap.add_argument("--limit", type=int, default=40)
    args = ap.parse_args(argv)

    cand = json.load(open(args.candidates))
    leaves = cand["domains"][args.domain]["leaves"]
    value_kinds = {"money", "rate", "count", "date", "enum", "text", "bool"}
    paths = [e["path"] for e in leaves
             if e["tier"] == "active" and e["value_kind"] in value_kinds
             and e["path"].startswith(args.prefix)][:args.limit]
    if not paths:
        print("no active value paths under prefix", repr(args.prefix)); return 1
    selection = paths_to_selection(paths)

    ad = _load("hca_adapter", "hca-adapter.py", _SCRIPTS)
    client = ad.LiveBackend().live_client()
    # loan domain rides loans(filter:{searchString}); others would use their own resolver.
    q = ("query CatalogProbe($filter: LoansFilterInput, $skip: Int, $limit: Int) { "
         "loans(filter: $filter, skip: $skip, limit: $limit) { pageItems { id name "
         + selection + " } } }")
    data = client.raw_query(q, {"filter": {"searchString": args.name}, "skip": 0, "limit": 5})
    items = ((data or {}).get("loans") or {}).get("pageItems") or []
    if not items:
        print("no loan matched", repr(args.name)); return 1
    row = items[0]
    print("probed loan:", row.get("id"), row.get("name"))
    print("selection had %d leaf paths" % len(paths))
    ok = 0
    for p in paths:
        status, val = walk_value(row, p)
        if status == "ok":
            ok += 1
        print("  %-58s %s %r" % (p, status, val if status == "ok" else ""))
    print("\nRESOLVED %d/%d paths to a real value" % (ok, len(paths)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
