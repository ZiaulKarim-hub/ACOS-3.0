#!/usr/bin/env python3
"""hca-catalog-probe.py — Phase 3: turn harvested flat leaf-paths back into LIVE GraphQL selections,
fetch ONE representative entity per domain, and map every active money/rate/value path to its real
fetched value. Deterministic (no agent variance); cheap (a handful of deep fetches per domain cover
thousands of fields).

`paths_to_selection` compiles dotted paths (with `[]` list markers) into a nested GraphQL selection:
    summary.totalOutstanding.principal ; summary.totalExpected.fees[].fee.value
  ->  summary { totalOutstanding { principal } totalExpected { fees { fee { value } } } }

Per domain it fetches BLOCK-BY-BLOCK (group active value paths by their first segment) so no single
query is unbounded, and it is resilient: a block whose query errors is recorded as fetch_error (its
fields stay schema-only) rather than crashing the domain. Faithfully distinguishes real / absent /
empty-list / fetch_error — NEVER fabricates.

CLI:
    # one block (validation)
    ... hca-catalog-probe.py --domain loan --prefix summary --name Beehive --limit 30
    # whole domain -> writes probe-<domain>.json
    ... hca-catalog-probe.py --domain loan --name Beehive --all
"""
import argparse
import datetime
import importlib.util
import json
import os
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS = os.path.abspath(os.path.join(_HERE, os.pardir, os.pardir, os.pardir, "scripts"))

# domain -> (resolver, filter graphql type, root type, default filter dict, label note)
_DOMAIN = {
    "loan": ("loans", "LoansFilterInput", "Loan", {"searchString": "Beehive"}, "by name"),
    "investor": ("loanFundings", "LoanFundingsFilterInput", "LoanFunding",
                 {"loanFundingId": "338"}, "loanFundingId 338 = XL on Lux II"),
    "funding_entity": ("fundingEntities", "FundingEntitiesFilterInput", "FundingEntity",
                       {"searchString": "XL"}, "by name"),
    "borrower": ("clients", "ClientsFilterInput", "ClientExtended", {}, "first page item"),
    "equity": ("equities", "EquitiesFilterInput", "Equity", {}, "first page item"),
}

_VALUE_KINDS = {"money", "rate", "count", "date", "enum", "text", "bool"}


def _load(mod, fname):
    spec = importlib.util.spec_from_file_location(mod, os.path.join(_SCRIPTS, fname))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def paths_to_selection(paths):
    tree = {}
    for p in paths:
        node = tree
        for seg in p.split("."):
            node = node.setdefault(seg.replace("[]", ""), {})

    def render(node):
        out = []
        for k, sub in node.items():
            out.append("%s { %s }" % (k, render(sub)) if sub else k)
        return " ".join(out)
    return render(tree)


def walk_value(obj, dotted):
    cur = obj
    for raw in dotted.split("."):
        is_list = raw.endswith("[]")
        key = raw.replace("[]", "")
        if not isinstance(cur, dict) or key not in cur:
            return ("absent", None)
        cur = cur[key]
        if is_list:
            if not isinstance(cur, list) or not cur:
                return ("empty_list", None)
            cur = cur[0]
    return ("ok", cur)


def _retry(client, query, variables, attempts=4, backoff=0.8):
    last = None
    for i in range(1, attempts + 1):
        try:
            return client.raw_query(query, variables)
        except Exception as e:  # noqa: BLE001
            last = e
            msg = ("%s %s" % (type(e).__name__, e)).lower()
            if "500" in msg or "internal server error" in msg:
                if i < attempts:
                    time.sleep(backoff * i)
                    continue
            raise
    raise last


def _group_blocks(leaves):
    """active value leaves -> {block: [paths]}. Direct (no dot) paths -> '_direct'."""
    blocks = {}
    for e in leaves:
        if e["tier"] != "active" or e["value_kind"] not in _VALUE_KINDS:
            continue
        p = e["path"]
        block = "_direct" if "." not in p else p.split(".")[0]
        blocks.setdefault(block, []).append(p)
    return blocks


def _fetch_entity(client, domain, filt, block_selection):
    resolver, ftype, root, _df, _note = _DOMAIN[domain]
    has_name = root not in ("LoanFunding",)
    namesel = " name" if has_name else ""
    q = ("query CatProbe($filter: %s, $skip: Int, $limit: Int) { "
         "%s(filter: $filter, skip: $skip, limit: $limit) { pageItems { id%s %s } } }"
         % (ftype, resolver, namesel, block_selection))
    data = _retry(client, q, {"filter": filt, "skip": 0, "limit": 5})
    items = ((data or {}).get(resolver) or {}).get("pageItems") or []
    return items


def probe_domain(domain, candidates, *, filt=None, kind_by_path=None, type_by_path=None):
    resolver, ftype, root, default_filter, note = _DOMAIN[domain]
    filt = filt if filt is not None else dict(default_filter)
    leaves = candidates["domains"][domain]["leaves"]
    kind_by_path = {e["path"]: e["value_kind"] for e in leaves}
    type_by_path = {e["path"]: e["leaf_type"] for e in leaves}
    blocks = _group_blocks(leaves)

    client = _load("hca_adapter", "hca-adapter.py").LiveBackend().live_client()
    values = {}
    block_status = {}
    entity = None
    for block, paths in sorted(blocks.items()):
        sel_paths = paths if block == "_direct" else paths
        selection = paths_to_selection(sel_paths)
        try:
            items = _fetch_entity(client, domain, filt, selection)
        except Exception as e:  # noqa: BLE001 — record + continue, never crash the domain
            block_status[block] = {"status": "fetch_error", "n": len(paths),
                                   "error": "%s: %s" % (type(e).__name__, str(e)[:160])}
            for p in paths:
                values[p] = {"status": "fetch_error", "value": None,
                             "value_kind": kind_by_path.get(p), "leaf_type": type_by_path.get(p)}
            continue
        if not items:
            block_status[block] = {"status": "no_entity", "n": len(paths)}
            for p in paths:
                values[p] = {"status": "no_entity", "value": None,
                             "value_kind": kind_by_path.get(p), "leaf_type": type_by_path.get(p)}
            continue
        row = items[0]
        if entity is None:
            entity = {"id": row.get("id"), "name": row.get("name")}
        ok = 0
        for p in paths:
            status, val = walk_value(row, p)
            if status == "ok":
                ok += 1
            values[p] = {"status": status, "value": val,
                         "value_kind": kind_by_path.get(p), "leaf_type": type_by_path.get(p)}
        block_status[block] = {"status": "ok", "n": len(paths), "resolved": ok}
    return {"domain": domain, "root_type": root, "resolver": resolver, "filter": filt,
            "note": note, "entity": entity, "blocks": block_status, "values": values}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", default=os.path.join(_HERE, "catalog-candidates.json"))
    ap.add_argument("--domain", required=True, choices=list(_DOMAIN))
    ap.add_argument("--name", default=None, help="override searchString")
    ap.add_argument("--lf-id", default=None, help="override loanFundingId (investor domain)")
    ap.add_argument("--prefix", default=None, help="single-block validation mode")
    ap.add_argument("--limit", type=int, default=40)
    ap.add_argument("--all", action="store_true", help="probe the whole domain -> probe-<domain>.json")
    args = ap.parse_args(argv)

    cand = json.load(open(args.candidates))
    filt = None
    if args.name is not None:
        filt = {"searchString": args.name}
    if args.lf_id is not None:
        filt = {"loanFundingId": args.lf_id}

    if args.prefix is not None and not args.all:
        # single-block validation
        leaves = cand["domains"][args.domain]["leaves"]
        paths = [e["path"] for e in leaves if e["tier"] == "active"
                 and e["value_kind"] in _VALUE_KINDS and e["path"].startswith(args.prefix)][:args.limit]
        client = _load("hca_adapter", "hca-adapter.py").LiveBackend().live_client()
        items = _fetch_entity(client, args.domain, filt or dict(_DOMAIN[args.domain][3]),
                              paths_to_selection(paths))
        if not items:
            print("no entity matched"); return 1
        row = items[0]
        print("probed:", row.get("id"), row.get("name"))
        ok = 0
        for p in paths:
            s, v = walk_value(row, p)
            ok += s == "ok"
            print("  %-58s %s %r" % (p, s, v if s == "ok" else ""))
        print("\nRESOLVED %d/%d" % (ok, len(paths)))
        return 0

    res = probe_domain(args.domain, cand, filt=filt)
    out = os.path.join(_HERE, "probe-%s.json" % args.domain)
    res["probed_at"] = datetime.datetime.now().isoformat(timespec="seconds")
    json.dump(res, open(out, "w"), indent=2, default=str)
    tot = len(res["values"])
    okc = sum(1 for v in res["values"].values() if v["status"] == "ok")
    err = sum(1 for b in res["blocks"].values() if b["status"] == "fetch_error")
    print("domain=%s entity=%s  resolved %d/%d active value paths  (blocks=%d, fetch_error=%d)"
          % (args.domain, res["entity"], okc, tot, len(res["blocks"]), err))
    print("written to", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
