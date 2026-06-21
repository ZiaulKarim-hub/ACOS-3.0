#!/usr/bin/env python3
"""
set-status.py — the ONE writer of component status for acos-synthesis-protocol.

Single source of truth = component-tree.json. This tool flips a component's
`status` (+ optional `evidence_ref`), mirrors it into library-status.json,
optionally records an evidence note, mechanically enforces the parent-gating
invariant, then re-renders library.html. Agents must NEVER hand-edit the JSON.

Usage:
  set-status.py <feature-dir> <component-id> <status>
      [--evidence <relpath>]      # path (relative to feature-dir) of the evidence note
      [--note <text>]             # write this text as the evidence note (creates --evidence path)
      [--source agent|human|reuse]# who produced the verdict (default agent)
      [--observed <text>]         # what was observed (for human/measurement verdicts)
      [--hardening <state>]       # record the code-hardening gate result on this node:
                                  #   clean | punchlist | skipped | pending
      [--punchlist <relpath>]     # path (rel to feature-dir) of deferred sub-gate findings
      [--no-render]               # skip re-rendering library.html

status ∈ planned | building | passed | failed | untested

Invariants enforced:
  (3) a node may be set to `passed` only if ALL its children are already `passed`
      (a parent is pure composition; it cannot be "done" before its parts are).
  (4) a hardening-ELIGIBLE code leaf (leaf AND verifier.type ∈ the tree's
      hardening.code_verifier_types) may be set to `passed` only if its hardening
      gate state is clean | punchlist | skipped — either already recorded on the
      node or supplied on THIS call via --hardening. This is what makes "every
      code component is hardened before it is integrated" a mechanical guarantee,
      not a prompt request. reuse-sourced passes are exempt (the linked original
      was already hardened when first published).
Other writes (building/failed/…) are unconstrained.

Exit 0 ok · 1 usage/not-found · 2 malformed JSON · 3 parent-gate · 4 hardening-gate.
"""
import json
import os
import sys
import subprocess

VALID = {"planned", "building", "passed", "failed", "untested"}
HARDENING_STATES = {"pending", "clean", "punchlist", "skipped"}
HARDENING_PASS_OK = {"clean", "punchlist", "skipped"}
DEFAULT_CODE_VERIFIER_TYPES = ["software-test", "data-schema"]


def die(msg, code):
    sys.stderr.write(msg.rstrip() + "\n")
    sys.exit(code)


def hardening_eligible(node, tree):
    """A component gets the code-hardening gate iff it is a LEAF whose verifier
    type denotes a code artifact. An explicit node.hardening.enabled overrides
    the derivation either way. Non-code artifacts and composing parents are
    never code-reviewed (preserves the domain-agnostic claim)."""
    h = node.get("hardening") or {}
    if h.get("enabled") is True:
        return True
    if h.get("enabled") is False:
        return False
    if node.get("children"):
        return False  # parents are pure composition — no code of their own
    code_types = ((tree.get("hardening") or {}).get("code_verifier_types")
                  or DEFAULT_CODE_VERIFIER_TYPES)
    vtype = (node.get("verifier") or {}).get("type")
    return vtype in code_types


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
             "--observed": "observed", "--hardening": "hardening",
             "--punchlist": "punchlist"}
    while i < len(a):
        if a[i] in flags and i + 1 < len(a):
            opts[flags[a[i]]] = a[i + 1]; i += 2
        elif a[i] == "--no-render":
            opts["no_render"] = True; i += 1
        else:
            i += 1
    source = opts.get("source", "agent")
    if opts.get("hardening") is not None and opts["hardening"] not in HARDENING_STATES:
        die("invalid --hardening %r (valid: %s)"
            % (opts["hardening"], ", ".join(sorted(HARDENING_STATES))), 1)

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

    # Record the hardening-gate result on the node (if supplied on this call).
    if opts.get("hardening") is not None:
        h = node.setdefault("hardening", {})
        h["state"] = opts["hardening"]
        if opts.get("punchlist") is not None:
            h["punchlist_ref"] = opts["punchlist"]

    # Hardening-gate invariant: an eligible code leaf may pass only once hardened.
    # reuse-sourced passes are exempt — the linked original was hardened on publish.
    if status == "passed" and source != "reuse" and hardening_eligible(node, tree):
        hstate = (node.get("hardening") or {}).get("state")
        if hstate not in HARDENING_PASS_OK:
            die("INVARIANT: cannot set %s=passed — code leaf not hardened "
                "(hardening.state=%r; need clean|punchlist|skipped). Run the "
                "hardening gate first, or pass --hardening <state> on this call."
                % (cid, hstate), 4)

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
            here, "..", "..", "acos-genesis-protocol", "scripts", "render-library.py"))
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
            here, "..", "..", "acos-genesis-protocol", "scripts", "registry.py"))
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
