#!/usr/bin/env python3
"""Distill the full Hypercore GraphQL introspection into a focused, human/agent-readable
digest of the READ-relevant entities. Reads _introspection.json, writes _schema-digest.md.

Extended in SLICE-HCA-02 (LiveBackend upgrade) to also emit, for each key query:
  - the exact ARGUMENT list (now that the full introspection carries field args), and
  - the field shapes of the pagination/filter/sort INPUT_OBJECT types those args reference.
This gives downstream slices the precise variable shapes for `loans`, `clients`, etc.

No network. stdlib only."""
import json, sys

INTRO = "planning/preeng/001-hypercore-ask/_introspection.json"
OUT = "planning/preeng/001-hypercore-ask/_schema-digest.md"

# Read-relevant query fields we care about for the loan-data skill.
KEY_QUERIES = [
    "loan", "loans", "loanTransaction", "loanTransactions", "loanFunding", "loanFundings",
    "client", "clients", "clientsOverview", "clientsTrend",
    "equity", "equities", "fundingEntity", "fundingEntities",
    "statementTemplates", "userNotifications", "clientCustomDocuments",
]

def unwrap(t):
    """Return (named_type_name, rendered) for a GraphQL type ref, unwrapping NON_NULL/LIST."""
    rendered = ""
    name = None
    stack = []
    cur = t
    while cur:
        k = cur.get("kind"); n = cur.get("name")
        if k == "NON_NULL": stack.append("!")
        elif k == "LIST": stack.append("[]")
        else:
            name = n
            break
        cur = cur.get("ofType")
    # render approximately
    base = name or "?"
    out = base
    for s in reversed(stack):
        if s == "[]": out = f"[{out}]"
        elif s == "!": out = f"{out}!"
    return name, out

def main():
    data = json.load(open(INTRO))
    schema = data["data"]["__schema"]
    types = {t["name"]: t for t in schema["types"] if t.get("name")}
    qtype = schema["queryType"]["name"]
    query_fields = {f["name"]: f for f in types[qtype].get("fields") or []}

    lines = []
    lines.append("# Hypercore GraphQL — Read-Relevant Schema Digest\n")
    lines.append(f"queryType=`{qtype}`  mutationType=`{schema.get('mutationType',{}).get('name')}`  "
                 f"total_types={len(schema['types'])}  query_fields={len(query_fields)}\n")
    lines.append("> READ-ONLY: this skill uses ONLY Query fields below. NEVER any Mutation.\n")

    lines.append(f"\n## All Query field names ({len(query_fields)})\n")
    lines.append("`" + "`, `".join(sorted(query_fields)) + "`\n")

    seen_objs = []
    input_types_to_expand = []   # INPUT_OBJECT type names referenced by key-query args
    for qf in KEY_QUERIES:
        f = query_fields.get(qf)
        if not f:
            lines.append(f"\n### query `{qf}` — (not present)\n")
            continue
        ret_name, ret_render = unwrap(f["type"])
        args = ", ".join(f"{a['name']}: {unwrap(a['type'])[1]}" for a in (f.get("args") or [])) if f.get("args") else ""
        lines.append(f"\n### query `{qf}({args})` -> `{ret_render}`")
        # Collect INPUT_OBJECT arg types (filter/sort/period) so we can dump their shapes.
        for a in (f.get("args") or []):
            an, _ = unwrap(a["type"])
            if an and an in types and types[an].get("kind") == "INPUT_OBJECT" \
                    and an not in input_types_to_expand:
                input_types_to_expand.append(an)
        if ret_name and ret_name in types and ret_name not in seen_objs:
            seen_objs.append(ret_name)
    # Now dump fields of every distinct returned object type + nested paginated item types.
    lines.append("\n\n## Returned object types (fields)\n")
    to_expand = list(seen_objs)
    expanded = set()
    while to_expand:
        tn = to_expand.pop(0)
        if tn in expanded or tn not in types: continue
        expanded.add(tn)
        t = types[tn]
        if t.get("kind") != "OBJECT": continue
        lines.append(f"\n### `{tn}`")
        for fl in (t.get("fields") or []):
            fn = fl["name"]; ftn, fr = unwrap(fl["type"])
            lines.append(f"- `{fn}`: `{fr}`")
            # Expand likely container types (Paginated*, *Connection, items/data holders)
            if ftn and ftn in types and (("aginated" in ftn) or ftn.endswith("Connection")) and ftn not in expanded:
                to_expand.append(ftn)

    # Dump the pagination/filter/sort INPUT_OBJECT shapes referenced by the key queries
    # (and any nested INPUT_OBJECT they reference, e.g. PeriodInput). These are the exact
    # `variables` shapes the LiveBackend builds for loans/clients/etc.
    lines.append("\n\n## Query argument INPUT_OBJECT shapes (pagination / filter / sort)\n")
    lines.append("> Pagination model is OFFSET-based: `skip` (Int) + `limit` (Int); "
                 "`Paginated*` returns `{ totalFilteredRecords, pageItems }`. Walk pages by "
                 "incrementing `skip` until accumulated count >= totalFilteredRecords.\n")
    in_expanded = set()
    in_queue = list(input_types_to_expand)
    while in_queue:
        itn = in_queue.pop(0)
        if itn in in_expanded or itn not in types:
            continue
        in_expanded.add(itn)
        it = types[itn]
        if it.get("kind") != "INPUT_OBJECT":
            continue
        lines.append(f"\n### input `{itn}`")
        for inf in (it.get("inputFields") or []):
            inn, inr = unwrap(inf["type"])
            lines.append(f"- `{inf['name']}`: `{inr}`")
            if inn and inn in types and types[inn].get("kind") == "INPUT_OBJECT" \
                    and inn not in in_expanded:
                in_queue.append(inn)

    open(OUT, "w").write("\n".join(lines) + "\n")
    print(f"wrote {OUT}: {len(expanded)} object types expanded, "
          f"{len(in_expanded)} input objects expanded, "
          f"{len(query_fields)} query fields cataloged")

if __name__ == "__main__":
    sys.exit(main())
