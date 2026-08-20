#!/bin/bash
# open-picks.sh — open SEVERAL book rows in one go (ACOS Resurrection Protocol).
#
# Interface:
#   open-picks.sh --picks "2, 5, 7, 9" [--dry-run] [--focus-existing]
#                 [--label <text>]
#
# Zee's Rule 1 (2026-08-19): a pick may be a LIST. "2, 5, 7, 9" opens all four,
# each in its own window, in the project's own folder, each running
# `claude --dangerously-skip-permissions` (Rule 4). Rule 3 applies per row: a
# row that is already open gets ANOTHER window rather than a question.
#
# ALL-OR-NOTHING RESOLUTION. Every token is resolved against a FRESH book
# BEFORE any window is created. One unknown number, one ambiguous name, one
# tombstoned row — nothing opens at all. Half-opening a list and then refusing
# would leave the user hunting for which of four windows exists.
#
# Numbers are the renderer's own pick_number, never a re-count of printed rows.
# Names are matched casefolded and must be unique among live rows.
#
# Python (not TypeScript) by the standing exception: this extends the existing
# Python resurrection family and reads resurrect-view.py's own JSON rather than
# re-deriving the book, so the renderer stays the single source of pick numbers.

set -u

OP_PICKS=""
OP_DRY=0
OP_FOCUS=0
OP_LABEL=""
while [ $# -gt 0 ]; do
  case "$1" in
    --picks)          OP_PICKS="${2:-}"; shift 2 ;;
    --dry-run)        OP_DRY=1; shift ;;
    --focus-existing) OP_FOCUS=1; shift ;;
    --label)          OP_LABEL="${2:-}"; shift 2 ;;
    *) echo "REFUSED — unknown argument: $1" >&2; exit 2 ;;
  esac
done
export OP_PICKS OP_DRY OP_FOCUS OP_LABEL
OP_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export OP_LIB_DIR

exec /usr/bin/python3 - <<'PYEOF'
"""open-picks.sh embedded body — resolve a pick LIST, then open each row."""
import json
import os
import re
import subprocess
import sys

PICKS = os.environ.get("OP_PICKS", "")
DRY = os.environ.get("OP_DRY", "0") == "1"
FOCUS = os.environ.get("OP_FOCUS", "0") == "1"
LABEL = (os.environ.get("OP_LABEL") or "").strip()
LIB_DIR = os.environ.get("OP_LIB_DIR", "")

VIEW = os.path.join(LIB_DIR, "resurrect-view.py")
LAUNCH = os.path.join(LIB_DIR, "launch-project.sh")


def refuse(reason, code=2):
    print("REFUSED — %s" % reason)
    sys.exit(code)


def fresh_book():
    """The book, computed NOW. Never a cached render, never a stored file."""
    out = subprocess.run(["/usr/bin/python3", VIEW, "--json"],
                         capture_output=True, text=True, timeout=120)
    if out.returncode != 0:
        refuse("resurrect-view.py --json rc=%d stderr=%s" % (out.returncode, out.stderr.strip()[:300]))
    try:
        return json.loads(out.stdout)
    except (json.JSONDecodeError, ValueError):
        refuse("resurrect-view.py --json returned unparseable JSON: %r" % out.stdout[:200])


def tokens(raw):
    """Split on commas and whitespace; keep order, keep repeats (Rule 3)."""
    return [t for t in re.split(r"[,\s]+", raw.strip()) if t]


def main():
    if not PICKS.strip():
        refuse('--picks "2, 5, 7, 9" is required')
    book = fresh_book()
    rows = book.get("projects", [])
    by_number = {}
    by_name = {}
    for r in rows:
        pn = r.get("pick_number")
        if pn is not None:
            by_number[int(pn)] = r
        key = (r.get("name") or "").casefold()
        by_name.setdefault(key, []).append(r)

    resolved, problems = [], []
    for t in tokens(PICKS):
        if t.isdigit():
            r = by_number.get(int(t))
            if r is None:
                problems.append("%r is not a pick number in this book (numbered rows: %s)"
                                % (t, "1-%d" % max(by_number) if by_number else "none"))
            else:
                resolved.append((t, r))
            continue
        hits = by_name.get(t.casefold(), [])
        if not hits:
            problems.append("%r matches no row name in this book" % t)
        elif len(hits) > 1:
            problems.append("%r is ambiguous — %d rows carry that name: %s"
                            % (t, len(hits), ", ".join("%s @ %s" % (h["project_uuid"], h["root"])
                                                       for h in hits)))
        else:
            resolved.append((t, hits[0]))

    # ALL-OR-NOTHING: a bad token opens nothing at all.
    if problems:
        print("REFUSED — %d of %d picks could not be resolved; NOTHING was opened:"
              % (len(problems), len(tokens(PICKS))))
        for p in problems:
            print("  - %s" % p)
        return 2

    print("resolved %d pick%s (all-or-nothing check passed):"
          % (len(resolved), "" if len(resolved) == 1 else "s"))
    for t, r in resolved:
        print("  %-4s -> %-34s %s  [%s]" % (t, r.get("name"), r.get("root"), r.get("tier")))
    print("")

    results = []
    for i, (t, r) in enumerate(resolved, 1):
        uuid = r["project_uuid"]
        print("=" * 72)
        print("OPEN %d/%d — pick %s = %r (%s)" % (i, len(resolved), t, r.get("name"), uuid))
        print("=" * 72)
        cmd = ["/bin/bash", LAUNCH, "--project", uuid]
        if DRY:
            cmd.append("--dry-run")
        if FOCUS:
            cmd.append("--focus-existing")
        if LABEL:
            cmd += ["--label", LABEL]
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        sys.stdout.write(out.stdout)
        if out.stderr.strip():
            sys.stdout.write(out.stderr)
        print("exit=%d" % out.returncode)
        results.append((t, r.get("name"), out.returncode))

    print("")
    print("SUMMARY — %d pick%s" % (len(results), "" if len(results) == 1 else "s"))
    for t, nm, rc in results:
        if DRY:
            verdict = {0: "DRY RUN — decision printed, nothing opened"}.get(
                rc, "DRY RUN — REFUSED (exit %d)" % rc)
        elif FOCUS:
            verdict = {0: "focused an existing window",
                       3: "opened but DELIVERY NOT-VERIFIED"}.get(rc, "FAILED (exit %d)" % rc)
        else:
            verdict = {0: "opened + delivery VERIFIED",
                       3: "opened but DELIVERY NOT-VERIFIED"}.get(rc, "FAILED (exit %d)" % rc)
        print("  %-4s %-34s %s" % (t, nm, verdict))
    bad = [r for r in results if r[2] != 0]
    if bad:
        print("%d of %d need your eyes — see the block above each." % (len(bad), len(results)))
        return 3
    return 0


sys.exit(main())
PYEOF
