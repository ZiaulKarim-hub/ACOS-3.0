#!/usr/bin/env python3
"""
next-ready.py — compute the build frontier for acos-synthesis-protocol.

Given the current component-tree.json (+ library-status.json overlay), reports:
  - ready[]   : components buildable NOW, in build order. A component is ready if it
                still needs work (status planned|failed|untested) AND it is a leaf OR
                all its children are passed. Each carries needs_human + verifier_type
                so the runtime knows whether to spawn a Verifier agent (machine-runnable)
                or PAUSE for a human verdict (auto_check.runnable == false).
  - building[]: in progress.
  - blocked[] : needs work but waiting on a non-passed child (with the offending child).
  - done      : true when the depth-0 root is passed.
  - counts    : status histogram.

This is what makes the pipeline RESUMABLE: status lives on disk, so re-running this
after any interruption recomputes the exact frontier — no in-memory walk state.

Usage: next-ready.py <feature-dir> [--json | --human]   (default --human)
Exit 0 always (it's a query), 1 on usage/parse error.
"""
import json
import os
import sys


DEFAULT_CODE_VERIFIER_TYPES = ["software-test", "data-schema"]


def die(msg):
    sys.stderr.write(msg.rstrip() + "\n")
    sys.exit(1)


def hardening_eligible(node, tree):
    """Leaf whose verifier type is a code artifact ⇒ gets the hardening gate.
    Explicit node.hardening.enabled overrides. Kept in sync with set-status.py."""
    h = node.get("hardening") or {}
    if h.get("enabled") is True:
        return True
    if h.get("enabled") is False:
        return False
    if node.get("children"):
        return False
    code_types = ((tree.get("hardening") or {}).get("code_verifier_types")
                  or DEFAULT_CODE_VERIFIER_TYPES)
    return ((node.get("verifier") or {}).get("type")) in code_types


def main(argv):
    a = [x for x in argv[1:]]
    if not a:
        die("usage: next-ready.py <feature-dir> [--json|--human]")
    feature_dir = a[0]
    as_json = "--json" in a
    tree_path = os.path.join(feature_dir, "component-tree.json")
    try:
        tree = json.load(open(tree_path, encoding="utf-8"))
    except Exception as e:
        die("cannot read %s: %s" % (tree_path, e))

    nodes = tree.get("nodes", [])
    by_id = {n.get("id"): n for n in nodes}

    # status overlay from library-status.json wins over node.status
    overlay = {}
    ls_path = os.path.join(feature_dir, "library-status.json")
    if os.path.isfile(ls_path):
        try:
            overlay = (json.load(open(ls_path, encoding="utf-8")) or {}).get("status", {})
        except Exception:
            overlay = {}

    def st(n):
        return overlay.get(n.get("id"), n.get("status", "planned"))

    def order(n):
        bi = n.get("build_order_index")
        return bi if isinstance(bi, int) else 10**9

    ready, building, blocked, counts = [], [], [], {}
    for n in nodes:
        s = st(n)
        counts[s] = counts.get(s, 0) + 1
    for n in sorted(nodes, key=order):
        nid = n.get("id"); s = st(n)
        if s == "building":
            building.append(nid); continue
        if s == "passed":
            continue
        kids = n.get("children", []) or []
        unmet = [k for k in kids if st(by_id.get(k, {})) != "passed"]
        if unmet:
            blocked.append({"id": nid, "waiting_on": unmet})
            continue
        v = n.get("verifier", {}) or {}
        ac = v.get("auto_check", {}) or {}
        ready.append({
            "id": nid,
            "name": n.get("name"),
            "is_leaf": not kids,
            "kind": "leaf-build" if not kids else "integrate",
            "verifier_type": v.get("type"),
            "needs_human": not bool(ac.get("runnable")),
            "hardening_eligible": hardening_eligible(n, tree),
            "depth": n.get("depth"),
        })

    root = next((n for n in nodes if n.get("depth") == 0), None)
    done = bool(root) and st(root) == "passed"
    out = {"feature_id": tree.get("feature_id"), "done": done,
           "root": (root or {}).get("id"), "counts": counts,
           "ready": ready, "building": building, "blocked": blocked}

    if as_json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0

    # human-readable
    print("feature: %s   counts: %s" % (out["feature_id"],
          " ".join("%s=%d" % (k, v) for k, v in sorted(counts.items()))))
    if done:
        print("DONE — root %s is passed. Vision realized." % out["root"]); return 0
    if ready:
        print("READY (build in this order):")
        for r in ready:
            tag = " [HUMAN VERDICT REQUIRED]" if r["needs_human"] else ""
            if r.get("hardening_eligible"):
                tag += " +HARDEN"
            print("  - %-8s %-28s %-10s %s%s" % (r["id"], (r["name"] or "")[:28],
                  r["kind"], r["verifier_type"] or "?", tag))
    else:
        print("READY: (none)")
    if building:
        print("BUILDING: %s" % ", ".join(building))
    if blocked:
        print("BLOCKED:")
        for b in blocked:
            print("  - %s waiting on %s" % (b["id"], ", ".join(b["waiting_on"])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
