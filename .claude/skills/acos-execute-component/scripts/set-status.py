#!/usr/bin/env python3
"""
set-status.py — the ONE writer of component status for acos-execute-component.

Single source of truth = component-tree.json. This tool flips a component's
`status` (+ optional `evidence_ref`), mirrors it into library-status.json,
optionally records an evidence note, mechanically enforces the parent-gating
invariant, then re-renders library.html. Agents must NEVER hand-edit the JSON.

Usage:
  set-status.py <feature-dir> <component-id> <status>
      [--evidence <relpath>]      # path (relative to feature-dir) of the evidence note
      [--note <text>]             # write this text as the evidence note (creates --evidence path)
      [--source agent|human]      # who produced the verdict (default agent)
      [--observed <text>]         # what was observed (for human/measurement verdicts)
      [--no-render]               # skip re-rendering library.html

status ∈ planned | building | passed | failed | untested

Invariant enforced: a node may be set to `passed` only if ALL its children are
already `passed`. Violation → exit 3 (a parent is pure composition; it cannot be
"done" before its parts are). Other writes (building/failed/…) are unconstrained.

Exit 0 ok · 1 usage/not-found · 2 malformed JSON · 3 invariant violation.
"""
import json
import os
import sys
import subprocess

VALID = {"planned", "building", "passed", "failed", "untested"}


def die(msg, code):
    sys.stderr.write(msg.rstrip() + "\n")
    sys.exit(code)


def load(path, code=2):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        die("MISSING: %s" % path, 1)
    except json.JSONDecodeError as e:
        die("MALFORMED JSON %s: %s" % (path, e), code)


def dump(path, obj):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def main(argv):
    a = [x for x in argv[1:]]
    if len(a) < 3:
        die("usage: set-status.py <feature-dir> <component-id> <status> [opts]", 1)
    feature_dir, cid, status = a[0], a[1], a[2]
    if status not in VALID:
        die("invalid status %r (valid: %s)" % (status, ", ".join(sorted(VALID))), 1)
    if not os.path.isdir(feature_dir):
        die("not a directory: %s" % feature_dir, 1)

    opts, i = {}, 3
    flags = {"--evidence": "evidence", "--note": "note", "--source": "source",
             "--observed": "observed"}
    while i < len(a):
        if a[i] in flags and i + 1 < len(a):
            opts[flags[a[i]]] = a[i + 1]; i += 2
        elif a[i] == "--no-render":
            opts["no_render"] = True; i += 1
        else:
            i += 1
    source = opts.get("source", "agent")

    tree_path = os.path.join(feature_dir, "component-tree.json")
    tree = load(tree_path)
    nodes = {n.get("id"): n for n in tree.get("nodes", [])}
    if cid not in nodes:
        die("component not found in tree: %s" % cid, 1)
    node = nodes[cid]

    # Parent-gating invariant: passed requires all children passed.
    if status == "passed":
        kids = node.get("children", []) or []
        not_passed = [k for k in kids if (nodes.get(k, {}).get("status") != "passed")]
        if not_passed:
            die("INVARIANT: cannot set %s=passed — children not passed: %s"
                % (cid, ", ".join(not_passed)), 3)

    # Optional evidence note.
    ev_rel = opts.get("evidence")
    if opts.get("note") is not None:
        ev_rel = ev_rel or os.path.join("evidence", "%s-%s.md" % (cid, source))
        ev_abs = os.path.join(feature_dir, ev_rel)
        os.makedirs(os.path.dirname(ev_abs), exist_ok=True)
        body = "# %s — %s verdict: %s\n\n" % (cid, source, status)
        if opts.get("observed"):
            body += "Observed: %s\n\n" % opts["observed"]
        body += opts["note"] + "\n"
        with open(ev_abs, "w", encoding="utf-8") as fh:
            fh.write(body)

    node["status"] = status
    if ev_rel:
        node["evidence_ref"] = ev_rel
    dump(tree_path, tree)

    # Mirror into library-status.json.
    ls_path = os.path.join(feature_dir, "library-status.json")
    ls = load(ls_path, code=2) if os.path.isfile(ls_path) else {"feature_id": tree.get("feature_id"), "status": {}}
    ls.setdefault("status", {})[cid] = status
    ls["updated"] = "set-status:%s=%s(%s)" % (cid, status, source)
    dump(ls_path, ls)

    # Re-render library.html unless suppressed.
    if not opts.get("no_render"):
        here = os.path.dirname(os.path.abspath(__file__))
        renderer = os.path.normpath(os.path.join(
            here, "..", "..", "acos-preeng-unix", "scripts", "render-library.py"))
        if os.path.isfile(renderer):
            r = subprocess.run([sys.executable, renderer, feature_dir],
                               capture_output=True, text=True)
            sys.stdout.write(r.stdout)
            if r.returncode != 0:
                sys.stderr.write(r.stderr)

    # Auto-publish to the reuse registry when a reusable component passes.
    # Skip reuse-sourced passes (a linked component points at the original artifact —
    # publishing it again would duplicate the entry).
    if status == "passed" and source != "reuse" and (node.get("reuse", {}) or {}).get("reusable"):
        here = os.path.dirname(os.path.abspath(__file__))
        registry = os.path.normpath(os.path.join(
            here, "..", "..", "acos-preeng-unix", "scripts", "registry.py"))
        if os.path.isfile(registry):
            r = subprocess.run([sys.executable, registry, "publish", feature_dir, cid],
                               capture_output=True, text=True)
            # Best-effort: a publish failure must never block a status write.
            if r.returncode == 0:
                sys.stdout.write("[registry] " + r.stdout)
            else:
                sys.stderr.write("[registry] publish skipped: " + (r.stderr or r.stdout))

    print("OK: %s -> %s (%s)%s" % (cid, status, source,
          "  evidence=" + ev_rel if ev_rel else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
