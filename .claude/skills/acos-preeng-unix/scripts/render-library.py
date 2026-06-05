#!/usr/bin/env python3
"""
render-library.py — render the Component Library HTML for acos-preeng-unix.

Single source of truth: planning/preeng-unix/<feature-id>/component-tree.json
Live status overlay:    planning/preeng-unix/<feature-id>/library-status.json
Presentation shell:     <skill>/templates/library.html  (with injection tokens)

Pure Python 3 stdlib — NO external packages, NO API calls. Deterministic templating only.
Re-run after any status change (the execution runner calls this) to refresh badges.

Usage:
  render-library.py <feature-dir> [--template <path>] [--out <path>]

Exit 0 = rendered. Exit 1 = usage / missing input. Exit 2 = malformed JSON.
"""
import json
import sys
import os
from datetime import datetime, timezone

TOKENS = ("__PRODUCT_NAME__", "__FEATURE_ID__", "__GENERATED_AT__",
          "__COMPONENT_DATA__", "__STATUS_DATA__")


def die(msg, code):
    sys.stderr.write(msg.rstrip() + "\n")
    sys.exit(code)


def load_json(path, required=True):
    if not os.path.isfile(path):
        if required:
            die("MISSING: %s" % path, 1)
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except json.JSONDecodeError as e:
        die("MALFORMED JSON in %s: %s" % (path, e), 2)


def main(argv):
    args = [a for a in argv[1:] if a]
    if not args:
        die("usage: render-library.py <feature-dir> [--template P] [--out P]", 1)

    feature_dir = args[0]
    if not os.path.isdir(feature_dir):
        die("not a directory: %s" % feature_dir, 1)

    template = None
    out = os.path.join(feature_dir, "library.html")
    i = 1
    while i < len(args):
        if args[i] == "--template" and i + 1 < len(args):
            template = args[i + 1]; i += 2
        elif args[i] == "--out" and i + 1 < len(args):
            out = args[i + 1]; i += 2
        else:
            i += 1

    if template is None:
        # default: templates/library.html next to this script's skill dir
        here = os.path.dirname(os.path.abspath(__file__))
        template = os.path.normpath(os.path.join(here, "..", "templates", "library.html"))
    if not os.path.isfile(template):
        die("template not found: %s" % template, 1)

    tree = load_json(os.path.join(feature_dir, "component-tree.json"), required=True)
    status = load_json(os.path.join(feature_dir, "library-status.json"), required=False) or {}

    nodes = tree.get("nodes", [])
    if not isinstance(nodes, list):
        die("component-tree.json: 'nodes' must be a list", 2)

    product_name = tree.get("product_name") or tree.get("feature_id") or "Untitled Product"
    feature_id = tree.get("feature_id") or os.path.basename(feature_dir.rstrip("/"))
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    with open(template, "r", encoding="utf-8") as fh:
        html = fh.read()

    # JSON is injected inside <script type="application/json"> — escape only the
    # sequence that could close the script element early.
    def safe_json(obj):
        return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")

    replacements = {
        "__PRODUCT_NAME__": product_name,
        "__FEATURE_ID__": feature_id,
        "__GENERATED_AT__": generated_at,
        "__COMPONENT_DATA__": safe_json(tree),
        "__STATUS_DATA__": safe_json(status),
    }
    # Replace data tokens first (they may legitimately contain other token-like text
    # only as data, which is fine because JSON is injected as a single replace each).
    for tok in ("__COMPONENT_DATA__", "__STATUS_DATA__"):
        html = html.replace(tok, replacements[tok])
    for tok in ("__PRODUCT_NAME__", "__FEATURE_ID__", "__GENERATED_AT__"):
        # plain-text tokens: minimal HTML escaping
        val = (replacements[tok].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
        html = html.replace(tok, val)

    with open(out, "w", encoding="utf-8") as fh:
        fh.write(html)

    n_pass = sum(1 for x in nodes if (status.get("status", {}).get(x.get("id"), x.get("status")) == "passed"))
    print("RENDERED: %s  (%d components, %d passed)" % (out, len(nodes), n_pass))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
