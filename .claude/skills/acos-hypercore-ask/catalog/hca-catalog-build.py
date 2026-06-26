#!/usr/bin/env python3
"""hca-catalog-build.py — Phase 4: merge harvest (paths) + probe (real example values) + optional
enrichment overlay (human names / synonyms / gotchas from the annotation workflow) into the two
durable catalog artifacts:

  hypercore-catalog.yaml   machine source of truth — every active value-bearing leaf, by domain.
  HYPERCORE-FIELD-MAP.md   human-browsable — the askable financial values, by domain -> block.

Stdlib only (manual YAML emission — no third-party deps, per skill rules). Deterministic: re-run
anytime after a harvest / probe / enrichment refresh.
"""
import argparse
import datetime
import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))

_DOMAIN_ORDER = ["loan", "investor", "funding_entity", "borrower", "equity"]
_DOMAIN_TITLE = {
    "loan": "Loan", "investor": "Investor position (LoanFunding)",
    "funding_entity": "Funding entity / investor (portfolio)",
    "borrower": "Borrower (ClientExtended)", "equity": "Equity",
}
_RELIABILITY = {
    "loan": "RELIABLE — loans(filter:{searchString}){ pageItems{ … summary{…} } }",
    "investor": "RELIABLE — loanFundings 2-step (assetId→loanFundingId); dual-filter 500s",
    "funding_entity": "RELIABLE — fundingEntities(filter:{searchString}){ pageItems{…} }",
    "borrower": "DEGRADED — clients resolver HTTP 500 (2026-06-26); schema-mapped, probe deferred",
    "equity": "FORBIDDEN — equities resolver HTTP 403 (out of read-scope); schema-mapped only",
}
# kinds shown in the human FIELD-MAP (the askable numbers/facts). bool/text/id stay in the YAML only.
_MD_KINDS = ("money", "rate", "count", "date", "enum")
_VALUE_KINDS = {"money", "rate", "count", "date", "enum", "bool", "text"}


def _yaml_scalar(v):
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    s = str(v)
    if s == "" or any(c in s for c in ":#{}[],&*?|<>=!%@`\"'\n") or s.strip() != s:
        return '"%s"' % s.replace("\\", "\\\\").replace('"', '\\"')
    return s


def _fmt_example(v, status):
    if status != "ok":
        return "(%s)" % status
    if isinstance(v, float):
        return ("{:,.2f}".format(v) if abs(v) >= 1 else repr(v))
    if isinstance(v, int):
        return "{:,}".format(v)
    return str(v)


def load_domain(domain, candidates, enrich):
    leaves = candidates["domains"][domain]["leaves"]
    probe_path = os.path.join(_HERE, "probe-%s.json" % domain)
    probe = json.load(open(probe_path)) if os.path.exists(probe_path) else {"values": {}, "entity": None}
    pv = probe.get("values", {})
    entries = []
    for e in leaves:
        if e["tier"] != "active" or e["value_kind"] not in _VALUE_KINDS:
            continue
        p = e["path"]
        block = "_direct" if "." not in p else p.split(".")[0]
        pr = pv.get(p, {})
        ann = enrich.get(domain, {}).get(p, {})
        entries.append({
            "path": p, "kind": e["value_kind"], "type": e["leaf_type"], "block": block,
            "example": pr.get("value"), "example_status": pr.get("status", "no_probe"),
            "name": ann.get("name"), "synonyms": ann.get("synonyms") or [],
            "gotchas": ann.get("gotchas"), "high_value": ann.get("high_value", False),
            "figure": ann.get("figure"),
            "enum_values": e.get("enum_values"),
        })
    entries.sort(key=lambda x: (x["block"], x["path"]))
    return entries, probe.get("entity")


def emit_yaml(domains_data, candidates, stamp):
    L = []
    L.append("# Hypercore Data Catalog — machine source of truth (generated; do not hand-edit).")
    L.append("# Regenerate: python3 hca-catalog-build.py   (after harvest/probe/enrich refresh)")
    L.append("generated_at: %s" % _yaml_scalar(stamp))
    L.append("depth: %s" % candidates.get("depth"))
    L.append("domains:")
    for domain in _DOMAIN_ORDER:
        entries, entity = domains_data[domain]
        L.append("  %s:" % domain)
        L.append("    title: %s" % _yaml_scalar(_DOMAIN_TITLE[domain]))
        L.append("    root_type: %s" % _yaml_scalar(candidates["domains"][domain]["root_type"]))
        L.append("    access: %s" % _yaml_scalar(candidates["domains"][domain]["access"]))
        L.append("    reliability: %s" % _yaml_scalar(_RELIABILITY[domain]))
        L.append("    probe_entity: %s" % _yaml_scalar(json.dumps(entity) if entity else None))
        L.append("    value_field_count: %d" % len(entries))
        L.append("    fields:")
        for e in entries:
            L.append("      - path: %s" % _yaml_scalar(e["path"]))
            L.append("        kind: %s" % e["kind"])
            L.append("        type: %s" % _yaml_scalar(e["type"]))
            L.append("        example: %s" % _yaml_scalar(e["example"]))
            L.append("        example_status: %s" % _yaml_scalar(e["example_status"]))
            if e["name"]:
                L.append("        name: %s" % _yaml_scalar(e["name"]))
            if e["synonyms"]:
                L.append("        synonyms: [%s]" % ", ".join(_yaml_scalar(s) for s in e["synonyms"]))
            if e["gotchas"]:
                L.append("        gotchas: %s" % _yaml_scalar(e["gotchas"]))
            if e["high_value"]:
                L.append("        high_value: true")
            if e["figure"]:
                L.append("        figure: %s" % _yaml_scalar(e["figure"]))
            if e["enum_values"]:
                L.append("        enum_values: [%s]"
                         % ", ".join(_yaml_scalar(s) for s in e["enum_values"][:20]))
    return "\n".join(L) + "\n"


def emit_md(domains_data, candidates, stamp):
    M = []
    M.append("# Hypercore Field Map")
    M.append("")
    M.append("_Browsable index of the askable numbers & facts in Hypercore, by domain → block._  ")
    M.append("_Generated %s from live introspection + probe. Machine source: `hypercore-catalog.yaml`._" % stamp)
    M.append("")
    M.append("## Access reality")
    M.append("")
    M.append("| Domain | Root type | Access |")
    M.append("|---|---|---|")
    for d in _DOMAIN_ORDER:
        M.append("| %s | `%s` | %s |" % (_DOMAIN_TITLE[d],
                 candidates["domains"][d]["root_type"], _RELIABILITY[d]))
    M.append("")
    for domain in _DOMAIN_ORDER:
        entries, entity = domains_data[domain]
        md_entries = [e for e in entries if e["kind"] in _MD_KINDS]
        skipped = len(entries) - len(md_entries)
        M.append("## %s" % _DOMAIN_TITLE[domain])
        M.append("")
        M.append("- Root: `%s` · %s" % (candidates["domains"][domain]["root_type"], _RELIABILITY[domain]))
        if entity:
            M.append("- Probe entity: `%s`" % json.dumps(entity))
        M.append("- %d askable value fields shown (%d bool/text fields in YAML only)"
                 % (len(md_entries), skipped))
        M.append("")
        by_block = {}
        for e in md_entries:
            by_block.setdefault(e["block"], []).append(e)
        for block in sorted(by_block):
            M.append("### `%s`" % block)
            M.append("")
            M.append("| Field | Kind | Example | Name / notes |")
            M.append("|---|---|---|---|")
            for e in by_block[block]:
                label = e["name"] or ""
                if e["high_value"]:
                    label = "**%s**" % label if label else "**(key)**"
                if e["gotchas"]:
                    label = (label + " — " + e["gotchas"]) if label else e["gotchas"]
                ex = _fmt_example(e["example"], e["example_status"])
                M.append("| `%s` | %s | %s | %s |"
                         % (e["path"], e["kind"], ex.replace("|", "\\|"), label.replace("|", "\\|")))
            M.append("")
    return "\n".join(M) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", default=os.path.join(_HERE, "catalog-candidates.json"))
    ap.add_argument("--enrich", default=os.path.join(_HERE, "enrichment.json"),
                    help="optional {domain: {path: {name,synonyms,gotchas,high_value,figure}}}")
    ap.add_argument("--stamp", default=None, help="generation timestamp (default: now)")
    args = ap.parse_args(argv)

    candidates = json.load(open(args.candidates))
    enrich = json.load(open(args.enrich)) if os.path.exists(args.enrich) else {}
    stamp = args.stamp or datetime.datetime.now().isoformat(timespec="seconds")

    domains_data = {d: load_domain(d, candidates, enrich) for d in _DOMAIN_ORDER}

    yaml_out = os.path.join(_HERE, "hypercore-catalog.yaml")
    md_out = os.path.join(_HERE, "HYPERCORE-FIELD-MAP.md")
    index_out = os.path.join(_HERE, "catalog-index.json")
    open(yaml_out, "w").write(emit_yaml(domains_data, candidates, stamp))
    open(md_out, "w").write(emit_md(domains_data, candidates, stamp))

    # compact machine index (the lookup tool + skill consume this — no YAML parser needed).
    index = {"generated_at": stamp, "depth": candidates.get("depth"), "domains": {}}
    for d in _DOMAIN_ORDER:
        entries, entity = domains_data[d]
        index["domains"][d] = {
            "title": _DOMAIN_TITLE[d], "root_type": candidates["domains"][d]["root_type"],
            "access": candidates["domains"][d]["access"], "reliability": _RELIABILITY[d],
            "probe_entity": entity,
            "fields": [{"path": e["path"], "kind": e["kind"], "type": e["type"],
                        "example": e["example"], "example_status": e["example_status"],
                        "name": e["name"], "synonyms": e["synonyms"], "gotchas": e["gotchas"],
                        "high_value": e["high_value"], "figure": e["figure"]}
                       for e in entries],
        }
    json.dump(index, open(index_out, "w"), separators=(",", ":"))

    # committed path snapshot (small) so hca-catalog-refresh.py can detect schema drift without
    # parsing the big YAML or committing the gitignored candidate/probe JSONs.
    paths_out = os.path.join(_HERE, "catalog-paths.json")
    snapshot = {"generated_at": stamp, "depth": candidates.get("depth"),
                "domains": {d: sorted(e["path"] for e in domains_data[d][0]) for d in _DOMAIN_ORDER}}
    json.dump(snapshot, open(paths_out, "w"), indent=0)

    total = sum(len(domains_data[d][0]) for d in _DOMAIN_ORDER)
    print("catalog built: %d value fields across %d domains" % (total, len(_DOMAIN_ORDER)))
    for d in _DOMAIN_ORDER:
        ents = domains_data[d][0]
        probed = sum(1 for e in ents if e["example_status"] == "ok")
        named = sum(1 for e in ents if e["name"])
        print("  %-14s %4d fields  (%4d probed, %4d named)" % (d, len(ents), probed, named))
    print("written: %s , %s" % (yaml_out, md_out))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
