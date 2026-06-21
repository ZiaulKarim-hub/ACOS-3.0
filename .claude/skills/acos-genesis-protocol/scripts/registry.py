#!/usr/bin/env python3
"""
registry.py — cross-tree component reuse registry for acos-genesis-protocol.

Operationalizes the Unix promise that a passed, reusable component "can be reused
elsewhere." The registry is a project-level index living ABOVE any feature dir
(default: planning/preeng-unix/_registry/registry.json), because its whole point is
to be shared across trees / products.

Three operations:
  publish  — index a passed+reusable component (called automatically by set-status.py)
  search   — find reusable components by capability tags / verifier type / output kind
  link     — reuse a registered component in a NEW tree: copy its proven artifact into
             the consumer's build dir, mark the consumer component `passed` via
             set-status.py, and record the consumer on the registry entry.

Stdlib only. Exit 0 ok · 1 usage/not-found · 2 malformed/precondition.

USAGE
  registry.py publish <feature-dir> <component-id> [--registry <path>]
  registry.py search  [--tags a,b] [--type T] [--kind K] [--query SUB] [--registry P] [--json]
  registry.py link    <consumer-feature-dir> <consumer-component-id> <registry-id> [--registry P]
"""
import json
import os
import sys
import shutil

DEFAULT_REGISTRY = os.path.join("planning", "preeng-unix", "_registry", "registry.json")


def die(msg, code):
    sys.stderr.write(msg.rstrip() + "\n")
    sys.exit(code)


def load_json(path, default=None, code=2):
    if not os.path.isfile(path):
        return default
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except json.JSONDecodeError as e:
        die("MALFORMED JSON %s: %s" % (path, e), code)


def dump_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def load_registry(path):
    return load_json(path, default={"version": 1, "updated": None, "entries": []})


def next_registry_id(reg):
    n = 0
    for e in reg["entries"]:
        rid = e.get("registry_id", "")
        if rid.startswith("R-"):
            try:
                n = max(n, int(rid[2:]))
            except ValueError:
                pass
    return "R-%04d" % (n + 1)


def find_node(feature_dir, cid):
    tree = load_json(os.path.join(feature_dir, "component-tree.json"))
    if not tree:
        die("no component-tree.json in %s" % feature_dir, 1)
    for n in tree.get("nodes", []):
        if n.get("id") == cid:
            return tree, n
    die("component %s not found in %s" % (cid, feature_dir), 1)


# ── publish ─────────────────────────────────────────────────────────────────
def cmd_publish(args):
    if len(args) < 2:
        die("usage: registry.py publish <feature-dir> <component-id> [--registry P]", 1)
    feature_dir, cid = args[0], args[1]
    reg_path = opt(args, "--registry", DEFAULT_REGISTRY)
    tree, node = find_node(feature_dir, cid)

    if not (node.get("reuse", {}) or {}).get("reusable"):
        die("NOT-REUSABLE: %s is not flagged reuse.reusable — nothing to publish" % cid, 2)
    if node.get("status") != "passed":
        die("NOT-PASSED: %s status=%s — only passed components are published" % (cid, node.get("status")), 2)

    reg = load_registry(reg_path)
    feature_id = tree.get("feature_id") or os.path.basename(feature_dir.rstrip("/"))
    # dedup key: same source component (feature + id) updates in place.
    existing = next((e for e in reg["entries"]
                     if e.get("source_feature") == feature_id and e.get("source_component_id") == cid), None)
    entry = {
        "registry_id": existing["registry_id"] if existing else next_registry_id(reg),
        "name": node.get("name"),
        "capability_tags": (node.get("reuse", {}) or {}).get("tags", []),
        "verifier_type": (node.get("verifier", {}) or {}).get("type"),
        "output_kind": (node.get("output_artifact", {}) or {}).get("kind"),
        "source_feature": feature_id,
        "source_feature_dir": feature_dir,
        "source_component_id": cid,
        "contract": node.get("contract", {}),
        "verifier": node.get("verifier", {}),
        "acceptance_criteria": node.get("acceptance_criteria", []),
        "output_artifact": node.get("output_artifact", {}),
        "artifact_location": (node.get("output_artifact", {}) or {}).get("location_hint"),
        "evidence_ref": node.get("evidence_ref"),
        # Carry the code-hardening guarantee forward: a published code leaf is, by the exit-4
        # invariant, hardened (clean|punchlist|skipped) before it could reach passed. Reusers
        # inherit a component that is functionally AND internally proven.
        "hardening": node.get("hardening", {"state": "skipped"}),
        "consumers": existing.get("consumers", []) if existing else [],
    }
    if existing:
        reg["entries"][reg["entries"].index(existing)] = entry
        action = "updated"
    else:
        reg["entries"].append(entry)
        action = "registered"
    reg["updated"] = "publish:%s/%s" % (feature_id, cid)
    dump_json(reg_path, reg)
    print("OK: %s %s as %s (tags=%s) -> %s"
          % (action, cid, entry["registry_id"], ",".join(entry["capability_tags"]) or "-", reg_path))
    return 0


# ── search ──────────────────────────────────────────────────────────────────
def cmd_search(args):
    reg_path = opt(args, "--registry", DEFAULT_REGISTRY)
    want_tags = [t.strip() for t in (opt(args, "--tags", "") or "").split(",") if t.strip()]
    vtype = opt(args, "--type", None)
    kind = opt(args, "--kind", None)
    query = (opt(args, "--query", "") or "").lower()
    as_json = "--json" in args
    reg = load_registry(reg_path)

    scored = []
    for e in reg["entries"]:
        if vtype and e.get("verifier_type") != vtype:
            continue
        if kind and e.get("output_kind") != kind:
            continue
        if query and query not in (e.get("name", "") + " " + " ".join(e.get("capability_tags", []))).lower():
            continue
        overlap = len(set(want_tags) & set(e.get("capability_tags", []))) if want_tags else 0
        if want_tags and overlap == 0:
            continue
        scored.append((overlap, e))
    scored.sort(key=lambda x: -x[0])

    results = [{"registry_id": e["registry_id"], "name": e["name"],
                "capability_tags": e["capability_tags"], "verifier_type": e.get("verifier_type"),
                "output_kind": e.get("output_kind"), "source": "%s/%s" % (e["source_feature"], e["source_component_id"]),
                "tag_overlap": ov, "reused_by": len(e.get("consumers", []))}
               for ov, e in scored]
    if as_json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return 0
    if not results:
        print("no reusable components match (registry: %s)" % reg_path); return 0
    print("REUSABLE COMPONENTS (rank by tag overlap):")
    for r in results:
        print("  %-8s %-26s tags=%-22s %-13s overlap=%d reused=%d  [%s]"
              % (r["registry_id"], (r["name"] or "")[:26], ",".join(r["capability_tags"])[:22],
                 r["verifier_type"] or "?", r["tag_overlap"], r["reused_by"], r["source"]))
    return 0


# ── link ────────────────────────────────────────────────────────────────────
def cmd_link(args):
    if len(args) < 3:
        die("usage: registry.py link <consumer-feature-dir> <consumer-component-id> <registry-id> [--registry P]", 1)
    cons_dir, cons_id, rid = args[0], args[1], args[2]
    reg_path = opt(args, "--registry", DEFAULT_REGISTRY)
    reg = load_registry(reg_path)
    entry = next((e for e in reg["entries"] if e.get("registry_id") == rid), None)
    if not entry:
        die("registry id %s not found in %s" % (rid, reg_path), 1)
    tree, node = find_node(cons_dir, cons_id)
    if node.get("children"):
        die("REFUSE: %s is not a leaf — only leaf components may be satisfied by reuse" % cons_id, 2)

    # Copy the proven artifact into the consumer build dir if it is a real file/dir.
    src = entry.get("artifact_location")
    copied = "no-artifact-copied (reference only)"
    if src and os.path.exists(src):
        dst = (node.get("output_artifact", {}) or {}).get("location_hint") \
            or os.path.join(cons_dir, "build", os.path.basename(src))
        os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
        if os.path.isdir(src):
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
        copied = "copied %s -> %s" % (src, dst)

    # Record consumer on the registry entry.
    cons_feature = tree.get("feature_id") or os.path.basename(cons_dir.rstrip("/"))
    ckey = "%s/%s" % (cons_feature, cons_id)
    if ckey not in entry.get("consumers", []):
        entry.setdefault("consumers", []).append(ckey)
    reg["updated"] = "link:%s<-%s" % (ckey, rid)
    dump_json(reg_path, reg)

    # Mark the consumer passed via set-status.py (source=reuse → it will NOT re-publish).
    here = os.path.dirname(os.path.abspath(__file__))
    setter = os.path.normpath(os.path.join(here, "..", "..", "acos-synthesis-protocol", "scripts", "set-status.py"))
    note = "Reused %s (%s) from %s. %s" % (rid, entry.get("name"), entry.get("source_feature"), copied)
    if os.path.isfile(setter):
        import subprocess
        r = subprocess.run([sys.executable, setter, cons_dir, cons_id, "passed",
                            "--source", "reuse", "--note", note], capture_output=True, text=True)
        sys.stdout.write(r.stdout)
        if r.returncode != 0:
            sys.stderr.write(r.stderr)
            die("set-status failed while linking", 2)
    else:
        die("set-status.py not found at %s" % setter, 2)
    print("OK: %s now reuses %s (%s); %s" % (cons_id, rid, entry.get("name"), copied))
    return 0


def opt(args, flag, default):
    if flag in args:
        i = args.index(flag)
        if i + 1 < len(args):
            return args[i + 1]
    return default


def main(argv):
    if len(argv) < 2:
        die(__doc__, 1)
    cmd, rest = argv[1], argv[2:]
    if cmd == "publish":
        return cmd_publish(rest)
    if cmd == "search":
        return cmd_search(rest)
    if cmd == "link":
        return cmd_link(rest)
    die("unknown command %r (publish|search|link)" % cmd, 1)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
