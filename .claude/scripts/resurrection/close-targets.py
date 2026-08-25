#!/usr/bin/env python3
"""close-targets.py — where should THIS tab's close be parked? (Zee, 2026-08-24)

  close-targets.py                 the SHORT menu: likely rows, then the two
                                   standing choices (new row / whole book)
  close-targets.py --resolve <n>   one book number -> the confirm line
                                   `parking to: <name> @ <folder>`
  close-targets.py --json          same facts, machine-readable

WHY THIS EXISTS. `/acos-safe-close` used to print the WHOLE book every time and
ask "park this tab's work where?". Zee's ruling 2026-08-24: he does not need the
whole book each time. A number given on the command line settles it outright
(`/acos-safe-close 20` parks at row 20). With no number, he wants the LIKELY
rows plus a way to make a new row and a way to see the whole book anyway.

WHY IT IS A SCRIPT AND NOT SKILL PROSE. Both resurrection skills carry the same
hard rule: the skill routes and relays, it computes NOTHING. Ranking candidate
rows is a computation over the registry and live cmux, so it lives here and the
skill prints what this prints.

THE RANKING, strongest evidence first (Zee's ask: "likely rows", plural):
  1. KEY-TAG   — the row named by this workspace's durable [key:<uuid>]
                 description tag. This is the same evidence close-project.sh
                 itself resolves first, so rank 1 IS today's default target.
  2. SAME-ROOT — rows whose root is this tab's folder. Several projects legally
                 share one folder (user rule, restated 2026-08-05), so these are
                 real candidates, not duplicates.
  3. RECENT    — otherwise-plausible rows by the book's own ref_time, newest
                 first, so a tab opened for something unrelated still gets a
                 short list rather than an empty one.
Capped at MAX_LIKELY. The cap is PRINTED whenever it bites — a silent
truncation would read as "these are all the candidates" when it is not.

ARCHIVED ROWS ARE NEVER OFFERED. close-project.sh already refuses a tombstoned
--park-to target ("parking into a hidden row would put this work out of reach
too"); this never proposes one in the first place. `--resolve` refuses both
tombstoned and completed rows with a stated reason.

NUMBERS ARE THE BOOK'S OWN. Every number printed here is the row's permanent
pick_ordinal, read from resurrect-view.py --json, never a re-count of printed
lines. So a number typed here means the same row as the same number typed at
`/acos-resurrect`. That equivalence is the whole point of Zee's ruling: one
number, one row, both commands.

Python, not TypeScript, by the standing exception: it extends the existing
Python resurrection family and reads resurrect-view.py's own JSON rather than
re-deriving the book.

Exit codes: 0 = done, 1 = refused (a stated reason), 2 = could not run.
"""

import argparse
import json
import os
import subprocess
import sys

HERE_DIR = os.path.dirname(os.path.abspath(__file__))
VIEW = os.path.join(HERE_DIR, "resurrect-view.py")
CMUX_BIN = "/Applications/cmux.app/Contents/Resources/bin/cmux"
MAX_LIKELY = 3
SKIP_CMUX = os.environ.get("RESURRECTION_SKIP_CMUX") == "1"
REG_HOME = os.environ.get("ACOS_REGISTRY_HOME") or None


def next_number():
    """The number a brand-new row would take, or None if it cannot be read.

    It is the LOWEST number no row holds (Zee's ruling 2026-08-24: "A freed
    number can be assigned"). A row waiting in registry.d/deleted/ still counts
    as holding its number, so this can never quietly take a number that
    `restore` is going to want back."""
    try:
        sys.path.insert(0, HERE_DIR)
        import ordinal_lib
        return ordinal_lib.next_ordinal(REG_HOME)
    except Exception:
        return None


def die(reason, code=2):
    print("REFUSED — %s" % reason)
    sys.exit(code)


def fresh_book():
    """The book, computed NOW — same source of numbers as /acos-resurrect."""
    argv = [sys.executable, VIEW, "--json"]
    if SKIP_CMUX:
        argv.append("--no-cmux")  # see open-picks.sh fresh_book(): fixture isolation
    out = subprocess.run(argv, capture_output=True, text=True, timeout=120)
    if out.returncode != 0:
        die("resurrect-view.py --json rc=%d stderr=%s"
            % (out.returncode, out.stderr.strip()[:300]))
    try:
        return json.loads(out.stdout)
    except (json.JSONDecodeError, ValueError):
        die("resurrect-view.py --json returned unparseable JSON: %r" % out.stdout[:200])


def this_workspace_key():
    """The [key:<uuid>] tag on THIS tab's workspace, or None.

    Fail-soft on purpose: no cmux, no CMUX_WORKSPACE_ID, or an unparseable
    reply drops rank 1 and keeps ranks 2 and 3. A close menu that refuses to
    render because cmux hiccuped would be worse than a shorter menu, and the
    reason is always printed rather than swallowed."""
    ws_id = os.environ.get("CMUX_WORKSPACE_ID", "").strip()
    if SKIP_CMUX or not ws_id or not os.path.exists(CMUX_BIN):
        return None, ws_id, ("sandbox (RESURRECTION_SKIP_CMUX=1)" if SKIP_CMUX
                             else "no CMUX_WORKSPACE_ID in this environment" if not ws_id
                             else "cmux binary not found at %s" % CMUX_BIN)
    try:
        out = subprocess.run([CMUX_BIN, "rpc", "workspace.list"],
                             capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, ws_id, "cmux rpc workspace.list failed (%s)" % type(exc).__name__
    if out.returncode != 0:
        return None, ws_id, "cmux rpc workspace.list rc=%d" % out.returncode
    try:
        payload = json.loads(out.stdout)
    except (json.JSONDecodeError, ValueError):
        return None, ws_id, "cmux rpc workspace.list returned unparseable JSON"
    for w in payload.get("workspaces", []):
        if w.get("id") != ws_id:
            continue
        desc = w.get("description") or ""
        if "[key:" in desc:
            tag = desc.split("[key:", 1)[1].split("]", 1)[0].strip()
            return (tag or None), ws_id, "read from this workspace's description tag"
        return None, ws_id, "this workspace carries no [key:<uuid>] tag yet"
    return None, ws_id, "this workspace id is not in cmux's workspace list"


def rank(book, key_uuid, cwd_real):
    """Likely park targets, strongest evidence first. Never an ARCHIVED row.

    Returns (strong, filler). STRONG is evidence about THIS tab: the [key:<uuid>]
    tag, then the folder. FILLER is only "recently active", which is true of
    every row in the book and is therefore not evidence about this tab at all.

    They are kept apart so the truncation notice can be honest. Ranking them in
    one list made the notice read "52 more candidate rows not listed", which is
    literally the whole registry and tells the reader nothing. The cap now bites
    on STRONG candidates only; filler exists to keep the menu non-empty in a
    scratch tab, and is labelled as the weak evidence it is."""
    seen = set()

    def take(bucket, row, why):
        u = row.get("project_uuid")
        if u in seen or row.get("status") in ("tombstoned", "completed"):
            return
        seen.add(u)
        bucket.append((row, why))

    rows = book.get("projects", [])
    strong, filler = [], []
    if key_uuid:
        for r in rows:
            if r.get("project_uuid") == key_uuid:
                take(strong, r, "this tab's own row ([key:<uuid>] tag)")
    for r in rows:
        root = r.get("root") or ""
        if root and os.path.realpath(root).casefold() == cwd_real:
            take(strong, r, "same folder as this tab")
    for r in sorted(rows, key=lambda x: x.get("ref_time") or "", reverse=True):
        take(filler, r, "recently active (no link to this tab — weak)")
    return strong, filler


def fmt_row(row, why):
    return "  %-4s %-32s %s\n       %s" % (
        row.get("pick_number"), row.get("name"), row.get("root"), why)


def cmd_menu(args, book):
    key_uuid, ws_id, key_note = this_workspace_key()
    cwd_real = os.path.realpath(os.getcwd()).casefold()
    strong, filler = rank(book, key_uuid, cwd_real)
    shown = strong[:MAX_LIKELY]
    dropped = max(len(strong) - MAX_LIKELY, 0)
    if len(shown) < MAX_LIKELY:
        shown = shown + filler[:MAX_LIKELY - len(shown)]

    own = None
    for row, _why in strong:
        if key_uuid and row.get("project_uuid") == key_uuid:
            own = row
            break

    if args.json:
        print(json.dumps({
            "workspace_id": ws_id,
            "key_uuid": key_uuid,
            "key_note": key_note,
            "cwd": os.getcwd(),
            "max_likely": MAX_LIKELY,
            "next_number": next_number(),
            "dropped": dropped,
            "strong_count": len(strong),
            "own_row": ({"pick_number": own.get("pick_number"),
                         "project_uuid": own.get("project_uuid"),
                         "name": own.get("name"), "root": own.get("root")}
                        if own else None),
            "likely": [{"pick_number": r.get("pick_number"),
                        "project_uuid": r.get("project_uuid"),
                        "name": r.get("name"), "root": r.get("root"),
                        "tier": r.get("tier"), "status": r.get("status"),
                        "why": why} for r, why in shown],
        }, indent=2))
        return 0

    print("Park this tab's work where? Type ONE of:")
    print("")
    if shown:
        print("1. A LIKELY ROW — type its number:")
        for row, why in shown:
            print(fmt_row(row, why))
        if dropped > 0:
            print("   (%d more row%s linked to this tab not listed — capped at %d; type "
                  "`all` to see every row)"
                  % (dropped, "" if dropped == 1 else "s", MAX_LIKELY))
    else:
        print("1. A LIKELY ROW — none could be ranked (%s)" % key_note)
    print("")
    # Choice 2 is Zee's "create a new row", and it MEANS create — a fresh row
    # taking a fresh number, with nothing replaced. It routes to
    # close-project.sh --park-to-new, which never orphans and never retires.
    # This tab's own row is not a separate choice: when it exists it is choice
    # 1's top entry, ranked by the [key:<uuid>] tag, so picking it is just
    # typing its number.
    nxt = next_number()
    print("2. `new <name>` — CREATE A NEW ROW for this work%s"
          % ("" if nxt is None else ", which takes number %d" % nxt))
    if nxt is None:
        print("       (the ordinal ledger could not be read, so the number is not shown here; "
              "the close itself still prints the number it minted)")
    print("       Nothing is replaced. Whatever row this tab already owns keeps its number, "
          "its knowledge and its closes.")
    if own is not None:
        print("       (to file onto this tab's own row instead, type its number %s above)"
              % own.get("pick_number"))
    print("       It is the lowest free number, so gaps get filled. A row waiting in "
          "deleted/ still holds its number until it is purged.")
    print("")
    print("3. `all` — show the whole book, then pick from it")
    print("")
    print("(the number you type is the book's own permanent number — the same number "
          "`/acos-resurrect` uses for that row)")
    return 0


def cmd_resolve(args, book):
    tok = str(args.resolve).strip()
    if not tok.isdigit():
        die("--resolve takes a book NUMBER; got %r" % tok, code=1)
    want = int(tok)
    for r in book.get("projects", []):
        if r.get("pick_number") != want:
            continue
        st = r.get("status")
        if st == "tombstoned":
            die("row %d = %r is TOMBSTONED — parking into a hidden row would put this "
                "work out of reach too" % (want, r.get("name")), code=1)
        if st == "completed":
            die("row %d = %r is COMPLETED (ARCHIVED) — pick a live row, or reopen that "
                "project first" % (want, r.get("name")), code=1)
        if args.json:
            print(json.dumps({"pick_number": want, "project_uuid": r.get("project_uuid"),
                              "name": r.get("name"), "root": r.get("root"),
                              "tier": r.get("tier"), "status": st}, indent=2))
            return 0
        print("parking to: %s @ %s" % (r.get("name"), r.get("root")))
        print("row number %d  ·  %s  ·  status %s  ·  uuid %s"
              % (want, r.get("tier"), st, r.get("project_uuid")))
        return 0
    numbered = [p["pick_number"] for p in book.get("projects", []) if p.get("pick_number")]
    die("%d is not a number in this book (numbered rows: %s)"
        % (want, "1-%d" % max(numbered) if numbered else "none"), code=1)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="close-targets.py", add_help=True)
    ap.add_argument("--resolve", metavar="N",
                    help="resolve ONE book number to its confirm line")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args(sys.argv[1:] if argv is None else argv)
    book = fresh_book()
    return cmd_resolve(args, book) if args.resolve is not None else cmd_menu(args, book)


if __name__ == "__main__":
    sys.exit(main())
