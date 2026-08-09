#!/usr/bin/env python3
"""gather-candidate-learnings.py — mechanically collects `candidate_learnings`
entries left behind in this project's still-open emergency handoffs
(memory/handoffs/*.yaml|*.md — the same non-recursive top-level glob
eternity-protocol-core.sh and acos-complete already use), so a later
/acos-safe-close can fold in learnings from EVERY Eternity Protocol /clear
cycle since the last close — not just what the closing session personally
remembers from its own context window.

Two modes:

  --root <path> --out <path> [--sources-out <path>]
      Scan every top-level handoff, SKIP any already marked harvested,
      write the collected candidates (JSON array of {claim, evidence})
      to --out, and the list of basenames just read to --sources-out
      (default: <out>.sources.json — read back by --mark-harvested).

  --mark-harvested --root <path> --sources <path>
      Mark every basename listed in --sources as harvested, so a future
      gather never re-reads it (and, critically, never re-asks Zee the
      same Kind-2 ruling question twice). Call this ONLY after the
      candidates have actually been written into the knowledge store by
      a SUCCESSFUL close — never speculatively.

Harvested state lives at memory/handoffs/.harvested/<basename>.marker —
sibling marker files. This NEVER mutates the handoff itself: handoffs are
sha256-verified elsewhere in the close/round-trip gates, and a mutated
handoff would fail those checks.

No yaml library exists on system python3 (3.9.6) — this reuses the same
line-prefix parsing convention as close-project.sh's own parse_handoff().
"""
import argparse
import glob
import json
import os
import re
import sys


def parse_candidate_learnings(path):
    """Extract the candidate_learnings: list from one handoff file. Each
    source line is either:
      - "<claim> (evidence: <evidence>)"
      - "<claim>"   (evidence falls back to "from <basename>")
    Returns a list of {claim, evidence, _source} dicts. Never raises —
    a malformed or unreadable handoff just yields no candidates."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            lines = fh.read().splitlines()
    except OSError:
        return []
    items = []
    in_block = False
    for ln in lines:
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):(.*)$", ln)
        if m:
            in_block = (m.group(1) == "candidate_learnings")
            continue
        if in_block and ln.strip().startswith("- "):
            raw = ln.strip()[2:].strip()
            if raw.startswith('"') and raw.endswith('"') and len(raw) >= 2:
                raw = raw[1:-1]
            mm = re.match(r"^(.*?)\s*\(evidence:\s*(.*)\)\s*$", raw)
            if mm:
                claim, evidence = mm.group(1).strip(), mm.group(2).strip()
            else:
                claim, evidence = raw, "from %s" % os.path.basename(path)
            if claim:
                items.append({"claim": claim, "evidence": evidence,
                              "_source": os.path.basename(path)})
        elif in_block and ln.strip() and not ln.startswith(" "):
            in_block = False
    return items


def harvested_dir(root):
    return os.path.join(root, "memory", "handoffs", ".harvested")


def is_harvested(root, basename):
    return os.path.exists(os.path.join(harvested_dir(root), basename + ".marker"))


def cmd_gather(args):
    handoffs_dir = os.path.join(args.root, "memory", "handoffs")
    files = sorted(glob.glob(os.path.join(handoffs_dir, "*.yaml")) +
                    glob.glob(os.path.join(handoffs_dir, "*.md")))
    scanned = len(files)
    new_files = []
    candidates = []
    for f in files:
        base = os.path.basename(f)
        if is_harvested(args.root, base):
            continue
        new_files.append(base)
        candidates.extend(parse_candidate_learnings(f))
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(candidates, fh, indent=2)
    sources_out = args.sources_out or (args.out + ".sources.json")
    with open(sources_out, "w", encoding="utf-8") as fh:
        json.dump(new_files, fh, indent=2)
    print("gather-candidate-learnings: %d handoff(s) on disk, %d not yet harvested, "
          "%d candidate learning(s) found" % (scanned, len(new_files), len(candidates)))
    print("  candidates -> %s" % args.out)
    print("  sources    -> %s" % sources_out)


def cmd_mark_harvested(args):
    with open(args.sources, "r", encoding="utf-8") as fh:
        basenames = json.load(fh)
    if not isinstance(basenames, list):
        print("STOP: --sources file must be a JSON array of basenames", file=sys.stderr)
        sys.exit(1)
    d = harvested_dir(args.root)
    os.makedirs(d, exist_ok=True)
    marked = 0
    for base in basenames:
        marker = os.path.join(d, base + ".marker")
        if not os.path.exists(marker):
            with open(marker, "w", encoding="utf-8") as fh:
                fh.write("harvested\n")
            marked += 1
    print("gather-candidate-learnings: marked %d handoff(s) harvested (of %d listed, "
          "%d were already marked)" % (marked, len(basenames), len(basenames) - marked))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=".")
    ap.add_argument("--out")
    ap.add_argument("--sources-out")
    ap.add_argument("--mark-harvested", action="store_true")
    ap.add_argument("--sources")
    args = ap.parse_args()
    args.root = os.path.abspath(args.root)
    if args.mark_harvested:
        if not args.sources:
            print("STOP: --mark-harvested requires --sources <path>", file=sys.stderr)
            sys.exit(1)
        cmd_mark_harvested(args)
    else:
        if not args.out:
            print("STOP: gather mode requires --out <path>", file=sys.stderr)
            sys.exit(1)
        cmd_gather(args)


if __name__ == "__main__":
    main()
