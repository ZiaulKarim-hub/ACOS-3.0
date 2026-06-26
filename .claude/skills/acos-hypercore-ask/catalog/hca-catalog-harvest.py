#!/usr/bin/env python3
"""hca-catalog-harvest.py — Phase 1 of the Hypercore Data Catalog.

Deterministic, OFFLINE (reads a cached introspection JSON; no network). Walks the READ-side domain
root types to a bounded depth and emits EVERY value-bearing leaf path (scalars + enums), grouped by
domain. This is the work-list the classify/probe workflow fans out over — so the agents never have
to re-walk the schema.

Domain roots = the element types behind the 5 reliable list resolvers:
    loan          -> Loan           via loans(filter){ pageItems{...} }
    investor      -> LoanFunding    via loanFundings(filter){ pageItems{...} }  (2-step assetId->lfId)
    funding_entity-> FundingEntity  via fundingEntities(filter){ pageItems{...} }
    borrower      -> Client         via clients(filter){ pageItems{...} }
    equity        -> Equity         via equities(filter){ pageItems{...} }

Nested objects/lists are traversed (so e.g. LoanFunding.repaymentSchedule.scheduleTable[].due.interest
— the per-diem — is reached). Recursion is depth-bounded and cycle-guarded (a type already on the
current path is recorded as a back-reference, not re-entered).

Usage:
    python3 hca-catalog-harvest.py [--introspection PATH] [--depth N] [--out PATH]
"""
import argparse
import json
import os
import sys
from collections import defaultdict


# Domain root object types + the reliable list resolver that reaches them.
_DOMAIN_ROOTS = [
    ("loan", "Loan", "loans(filter:{searchString}){ pageItems{ ... } }"),
    ("investor", "LoanFunding", "loanFundings(filter:{loanFundingId}){ pageItems{ ... } } (2-step)"),
    ("funding_entity", "FundingEntity", "fundingEntities(filter:{...}){ pageItems{ ... } }"),
    ("borrower", "ClientExtended", "clients(filter:{searchString}){ pageItems{ ... } }"),
    ("equity", "Equity", "equities(filter:{...}){ pageItems{ ... } }"),
]

_SCALAR_KINDS = {"SCALAR", "ENUM"}

# The domain root entity types are STOP BOUNDARIES: when walking one entity and we reach a field
# whose type is ANOTHER root entity (or a list of them), we record the relationship as a `link` and
# do NOT descend — that other entity has its own catalog. This collapses the schema's relationship
# graph (loan -> its fundings -> each funding's entity -> that entity's other loans -> ...) down to
# each entity's OWNED value tree (its scalars + its component sub-objects: summary, repaymentSchedule,
# KPIs, the InstallmentComponents blocks, etc.).
_ROOT_BOUNDARY = {"Loan", "LoanFunding", "FundingEntity", "Client", "Equity"}

# TIERING — split the harvested leaves into the ACTIVE catalog (current-state value blocks an analyst
# asks for) vs an EXTENDED appendix (drafts, what-if/original schedules, transaction & update history,
# audit/workflow/import plumbing, config templates). A leaf is EXTENDED if ANY segment of its path
# matches one of these — so e.g. `draftTerms.*`, `expectedSchedule.*`, `transactions.*`,
# `interestUpdates[].*` all fall to the appendix while `summary.*`, `repaymentSchedule.*`,
# `loanKPIs.*`, the direct scalars, etc. stay active. Nothing is discarded — extended is still emitted.
_DENY_SEGMENTS = {
    "drafttterms", "draftterms", "draft", "expectedschedule", "originalexpectedschedule",
    "scheduerowbydate", "schedulerowbydate", "transactions", "lasttransaction", "workflowcards",
    "oldfundingsources", "changerequest", "importinfo", "audit", "dynamictables", "template",
    "notes", "kpisasyncupdate", "interestupdates", "compoundinginterestupdates",
    "principalindexupdates", "fundingsourcesreconciliationaccount", "broker",
    "expensefees", "incomefees",
}
_DENY_SUBSTR = ("draft", "preview", "reschedule", "history", "import", "workflow", "audit")
_DENY_SUFFIX = ("updates", "settings")


def _tier_for(path):
    for raw in path.split("."):
        seg = raw.replace("[]", "").lower()
        if seg in _DENY_SEGMENTS:
            return "extended"
        if seg.endswith(_DENY_SUFFIX):
            return "extended"
        if any(s in seg for s in _DENY_SUBSTR):
            return "extended"
    return "active"


def _required_args(f):
    """Arg names that are NON_NULL with no default — a field with any is NOT selectable in a generic
    probe selection (it needs an explicit argument), so the walker prunes it (and its subtree)."""
    req = []
    for a in (f.get("args") or []):
        t = a.get("type") or {}
        if t.get("kind") == "NON_NULL" and a.get("defaultValue") in (None, "null"):
            req.append(a.get("name"))
    return req


def _leaf_typeref(tref):
    """Unwrap a NON_NULL/LIST typeref chain. Returns (leaf_name, leaf_kind, is_list)."""
    is_list = False
    cur = tref
    while cur is not None:
        if cur.get("kind") == "LIST":
            is_list = True
        if cur.get("name"):
            return cur.get("name"), cur.get("kind"), is_list
        cur = cur.get("ofType")
    return None, None, is_list


def _classify(leaf_name, leaf_kind, field_name):
    """Coarse value-kind for prioritization. money/rate/count/date/id/bool/text/enum."""
    fn = (field_name or "").lower()
    if leaf_kind == "ENUM":
        return "enum"
    if leaf_name in ("ID",):
        return "id"
    if leaf_name in ("Boolean",):
        return "bool"
    if leaf_name in ("Date", "DateTime", "Time"):
        return "date"
    if leaf_name in ("Int", "Long"):
        return "count"
    if leaf_name in ("Float", "Decimal", "BigDecimal", "Money"):
        if any(k in fn for k in ("rate", "percent", "ltv", "dscr", "yield", "ratio", "apr", "apy")):
            return "rate"
        return "money"
    if leaf_name in ("String",):
        return "text"
    return "scalar"


def walk(byname, root_type, max_depth):
    """Yield dicts {path, leaf_type, leaf_kind, value_kind, enum_values} for every scalar/enum leaf
    reachable from root_type within max_depth. Cycle-guarded on the type path."""
    out = []

    def recur(type_name, path, depth, type_stack):
        t = byname.get(type_name)
        if not t or t.get("kind") not in ("OBJECT", "INTERFACE"):
            return
        for f in (t.get("fields") or []):
            fname = f["name"]
            leaf_name, leaf_kind, is_list = _leaf_typeref(f["type"])
            if leaf_name is None:
                continue
            seg = fname + ("[]" if is_list else "")
            fpath = path + "." + seg if path else seg
            req = _required_args(f)
            if req:                                  # not selectable without args -> prune subtree
                out.append({"path": fpath, "leaf_type": leaf_name, "leaf_kind": leaf_kind,
                            "value_kind": "needs_args", "required_args": req})
                continue
            if leaf_kind in _SCALAR_KINDS:
                entry = {"path": fpath, "leaf_type": leaf_name, "leaf_kind": leaf_kind,
                         "value_kind": _classify(leaf_name, leaf_kind, fname)}
                if leaf_kind == "ENUM":
                    et = byname.get(leaf_name) or {}
                    entry["enum_values"] = [e["name"] for e in (et.get("enumValues") or [])][:40]
                out.append(entry)
            elif leaf_kind == "OBJECT":
                # STOP at a link to ANOTHER root entity (record the relationship, don't expand).
                if leaf_name in _ROOT_BOUNDARY and leaf_name != root_type:
                    out.append({"path": fpath, "leaf_type": leaf_name, "leaf_kind": "ENTITY_LINK",
                                "value_kind": "link"})
                    continue
                if leaf_name in type_stack:          # cycle guard: record as back-ref, don't recurse
                    out.append({"path": fpath, "leaf_type": leaf_name, "leaf_kind": "OBJECT_REF",
                                "value_kind": "ref"})
                    continue
                if depth + 1 > max_depth:
                    out.append({"path": fpath, "leaf_type": leaf_name, "leaf_kind": "OBJECT_TRUNCATED",
                                "value_kind": "truncated"})
                    continue
                recur(leaf_name, fpath, depth + 1, type_stack + [leaf_name])

    recur(root_type, "", 0, [root_type])
    return out


def main(argv=None):
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser()
    ap.add_argument("--introspection", default=os.path.join(here, "_introspection_current.json"))
    ap.add_argument("--depth", type=int, default=5)
    ap.add_argument("--out", default=os.path.join(here, "catalog-candidates.json"))
    args = ap.parse_args(argv)

    d = json.load(open(args.introspection))
    types = d["data"]["__schema"]["types"]
    byname = {t["name"]: t for t in types}

    catalog = {}
    summary = {}
    for domain, root, access in _DOMAIN_ROOTS:
        if root not in byname:
            catalog[domain] = {"root_type": root, "access": access, "absent": True, "leaves": []}
            continue
        leaves = walk(byname, root, args.depth)
        for e in leaves:
            e["tier"] = _tier_for(e["path"])
        # value-bearing = real values (exclude id/ref/link/truncated/scalar plumbing).
        valuey = {"money", "rate", "count", "date", "enum", "text", "bool"}
        active = [e for e in leaves if e["tier"] == "active"]
        active_val = [e for e in active if e["value_kind"] in valuey]
        vk = defaultdict(int)
        for e in active_val:
            vk[e["value_kind"]] += 1
        catalog[domain] = {"root_type": root, "access": access,
                           "leaf_count": len(leaves),
                           "active_value_count": len(active_val),
                           "active_by_value_kind": dict(vk),
                           "leaves": leaves}
        summary[domain] = {"root_type": root, "total_leaves": len(leaves),
                           "active_values": len(active_val), "active_by_value_kind": dict(vk)}

    json.dump({"depth": args.depth, "summary": summary, "domains": catalog},
              open(args.out, "w"), indent=2)

    # human-readable summary to stdout
    print("=== Hypercore catalog candidates (depth %d) — ACTIVE value leaves ===" % args.depth)
    g_active = 0
    g_total = 0
    for domain, s in summary.items():
        g_active += s["active_values"]
        g_total += s["total_leaves"]
        kinds = ", ".join("%s=%d" % (k, v) for k, v in sorted(s["active_by_value_kind"].items()))
        print("  %-14s root=%-14s active_values=%4d  (of %5d total leaves)  [%s]"
              % (domain, s["root_type"], s["active_values"], s["total_leaves"], kinds))
    print("  TOTAL active value leaves: %d   (of %d total)" % (g_active, g_total))
    print("written to", args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
