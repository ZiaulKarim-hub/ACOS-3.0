#!/bin/bash
# open-picks.sh — open SEVERAL book rows in one go (ACOS Resurrection Protocol).
#
# Interface:
#   open-picks.sh --picks "2, 5, 7, 9" [--dry-run] [--focus-existing]
#                 [--label <text>] [--here] [--include-archived]
#
# Zee's Rule 1 (2026-08-19): a pick may be a LIST. "2, 5, 7, 9" opens all four,
# each in its own window, in the project's own folder, each running
# `claude --dangerously-skip-permissions` (Rule 4). Rule 3 applies per row: a
# row that is already open gets ANOTHER window rather than a question.
#
# --here (Zee, 2026-08-24): THIS TAB becomes the picked project instead of a
# new window opening. It routes to adopt-project.sh, not launch-project.sh.
# A tab hosts ONE project, so --here takes exactly ONE pick and refuses a list.
# It also refuses alongside --focus-existing, which means the opposite thing
# (jump to some other window). The hard physical limit still applies and is
# adopt-project.sh's to report: a cmux workspace's folder cannot be changed
# after creation, so --here works only when the picked row's root IS this
# tab's folder; otherwise adopt exits 5 CROSS-ROOT and the caller opens a
# window instead.
#
# ALL-OR-NOTHING RESOLUTION. Every token is resolved against a FRESH book
# BEFORE any window is created. One unknown number, one ambiguous name, one
# tombstoned row — nothing opens at all. Half-opening a list and then refusing
# would leave the user hunting for which of four windows exists.
#
# STATUS IS TESTED IN THE PRE-CHECK (brief item 4, built 2026-08-24). Every row
# now carries a permanent number, ARCHIVED ones included, so an archived row can
# be named by number for the first time. Before this, a `tombstoned` row was
# refused LATE — inside the sequential loop by launch-project.sh, after earlier
# picks had already opened windows, which broke the all-or-nothing contract —
# and a `completed` row was not refused at all: it opened and was flipped back
# to `active`. Now:
#   * tombstoned -> REFUSED here, always, with no opt-in. Un-tombstoning is a
#     human act performed outside this script.
#   * completed  -> REFUSED here by default, naming --include-archived. The
#     resurrect loop (a finished project genuinely being reopened) is one
#     explicit flag away; a mistyped number can no longer revive it silently.
#
# Numbers are the renderer's own pick_number, never a re-count of printed rows.
# Since 2026-08-19 that number is the row's PERMANENT pick_ordinal, so a number
# means the same row on every render. Names are matched casefolded and must be
# unique among live rows.
#
# Python (not TypeScript) by the standing exception: this extends the existing
# Python resurrection family and reads resurrect-view.py's own JSON rather than
# re-deriving the book, so the renderer stays the single source of pick numbers.

set -u

OP_PICKS=""
OP_DRY=0
OP_FOCUS=0
OP_LABEL=""
OP_HERE=0
OP_ARCHIVED=0
while [ $# -gt 0 ]; do
  case "$1" in
    --picks)            OP_PICKS="${2:-}"; shift 2 ;;
    --dry-run)          OP_DRY=1; shift ;;
    --focus-existing)   OP_FOCUS=1; shift ;;
    --label)            OP_LABEL="${2:-}"; shift 2 ;;
    --here)             OP_HERE=1; shift ;;
    --include-archived) OP_ARCHIVED=1; shift ;;
    *) echo "REFUSED — unknown argument: $1" >&2; exit 2 ;;
  esac
done
export OP_PICKS OP_DRY OP_FOCUS OP_LABEL OP_HERE OP_ARCHIVED
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
HERE = os.environ.get("OP_HERE", "0") == "1"
ARCHIVED_OK = os.environ.get("OP_ARCHIVED", "0") == "1"
LIB_DIR = os.environ.get("OP_LIB_DIR", "")

VIEW = os.path.join(LIB_DIR, "resurrect-view.py")
LAUNCH = os.path.join(LIB_DIR, "launch-project.sh")
ADOPT = os.path.join(LIB_DIR, "adopt-project.sh")


def refuse(reason, code=2):
    print("REFUSED — %s" % reason)
    sys.exit(code)


def fresh_book():
    """The book, computed NOW. Never a cached render, never a stored file.

    RESURRECTION_SKIP_CMUX=1 is passed THROUGH as --no-cmux. Without this a
    fixture test still reached live cmux for the workspace join, which breaks
    the isolation the fixture exists for: rows would go LIVE (and change tier)
    because of whatever happens to be open on the machine running the test."""
    argv = ["/usr/bin/python3", VIEW, "--json"]
    if os.environ.get("RESURRECTION_SKIP_CMUX") == "1":
        argv.append("--no-cmux")
    out = subprocess.run(argv, capture_output=True, text=True, timeout=120)
    if out.returncode != 0:
        refuse("resurrect-view.py --json rc=%d stderr=%s" % (out.returncode, out.stderr.strip()[:300]))
    try:
        return json.loads(out.stdout)
    except (json.JSONDecodeError, ValueError):
        refuse("resurrect-view.py --json returned unparseable JSON: %r" % out.stdout[:200])


def tokens(raw):
    """Split on commas and whitespace; keep order, keep repeats (Rule 3)."""
    return [t for t in re.split(r"[,\s]+", raw.strip()) if t]


def status_problem(tok, row):
    """The pre-check status test (brief item 4). None = this row may open."""
    st = row.get("status")
    if st == "tombstoned":
        return ("%s = %r is TOMBSTONED — refused before anything opened. "
                "Un-tombstoning is a human act performed outside this script."
                % (tok, row.get("name")))
    if st == "completed" and not ARCHIVED_OK:
        return ("%s = %r is COMPLETED (ARCHIVED) — refused before anything opened. "
                "Re-run with --include-archived to reopen a finished project on purpose."
                % (tok, row.get("name")))
    return None


def main():
    if not PICKS.strip():
        refuse('--picks "2, 5, 7, 9" is required')
    if HERE and FOCUS:
        refuse("--here and --focus-existing mean opposite things (this tab becomes the "
               "project vs jump to some other window) — pass exactly one")
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
                sp = status_problem(t, r)
                if sp:
                    problems.append(sp)
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
            sp = status_problem(t, hits[0])
            if sp:
                problems.append(sp)
            else:
                resolved.append((t, hits[0]))

    # ALL-OR-NOTHING: a bad token opens nothing at all.
    if problems:
        print("REFUSED — %d of %d picks could not be resolved; NOTHING was opened:"
              % (len(problems), len(tokens(PICKS))))
        for p in problems:
            print("  - %s" % p)
        return 2

    # --here adopts THIS tab, and a tab hosts one project. A list has no
    # meaning here, and silently taking the first pick would strand the rest.
    if HERE and len(resolved) != 1:
        print("REFUSED — --here takes exactly ONE pick; %d were given (%s). This tab can "
              "become one project, not several. Drop --here to open them as windows."
              % (len(resolved), ", ".join(t for t, _ in resolved)))
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
        print("%s %d/%d — pick %s = %r (%s)"
              % ("ADOPT HERE" if HERE else "OPEN", i, len(resolved), t, r.get("name"), uuid))
        print("=" * 72)
        cmd = ["/bin/bash", ADOPT if HERE else LAUNCH, "--project", uuid]
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
        if DRY and rc == 0:
            verdict = "DRY RUN — decision printed, nothing opened"
        elif DRY and not HERE:
            verdict = "DRY RUN — REFUSED (exit %d)" % rc
        elif HERE:
            # adopt-project.sh's own codes: 3 OUTGOING NOT-CLOSED, 4 ALREADY
            # OPEN, 5 CROSS-ROOT. Each is a REFUSAL with a stated reason, never
            # a silent fallback to opening a window — that choice is the user's.
            verdict = {0: "THIS TAB is now the project",
                       3: "REFUSED — OUTGOING NOT-CLOSED (close this tab's project first)",
                       4: "REFUSED — ALREADY OPEN in another window",
                       5: "REFUSED — CROSS-ROOT (that row's folder is not this tab's folder; "
                          "drop `here` to open it as its own window)"}.get(rc, "FAILED (exit %d)" % rc)
            # A dry --here that refuses used to print only "REFUSED (exit 5)",
            # because the DRY branch ran first and never reached this map. The
            # exit code alone is the one thing the reader cannot act on.
            if DRY:
                verdict = "DRY RUN — " + verdict
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
