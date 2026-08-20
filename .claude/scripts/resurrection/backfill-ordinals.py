#!/usr/bin/env python3
"""backfill-ordinals.py — give every existing registry row its permanent number.

WHY (Zee's ruling, 2026-08-19). Pick numbers stopped being a per-render
counter and became a permanent label on the row (`pick_ordinal`). Every row
written before that ruling has no number. This assigns them, ONCE.

ORDER: `enrolled_at` ascending, with `project_uuid` as tiebreaker. Two
reasons. First, `enrolled_at` is already a ROW_KEY (registry_lib.py) — no new
field, no guesswork. Second, it means the oldest project gets 1, which is the
one ordering a human can predict without reading anything.

DETERMINISTIC AND RE-RUNNABLE. A row that already holds a number is never
touched. A second full run therefore does nothing. A run interrupted halfway
resumes to exactly the assignment a single clean run would have produced,
because the sort is stable and the unnumbered rows keep their relative order.

Every assignment also appends an `issue` entry to the ordinal ledger, so
`max_ever_issued` is correct immediately afterwards and the next new project
takes N+1 rather than colliding with row 1.

Python, not TypeScript, by the standing exception: it calls registry_lib and
ordinal_lib writers directly, so the schema gate, the atomic-write pattern and
the append-only ledger discipline all still apply rather than being
re-implemented beside them.

Usage:
    python3 backfill-ordinals.py                # dry run — prints the plan
    python3 backfill-ordinals.py --apply        # write it
    python3 backfill-ordinals.py --selftest     # fixture test, own home
"""

import argparse
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ordinal_lib  # noqa: E402
import registry_lib  # noqa: E402


def plan(home=None):
    """Return (assignments, already_numbered, start_at).

    `assignments` is [(row, ordinal), ...] in the order they will be written.
    Nothing is written here — the caller decides.
    """
    rows = list(registry_lib._iter_rows(home))
    numbered = [r for r in rows if r.get("pick_ordinal") is not None]
    unnumbered = [r for r in rows if r.get("pick_ordinal") is None]

    # Start above BOTH the ledger high-water mark and any ordinal already on a
    # row. The row check matters when a row was written by hand or by a crashed
    # earlier run that never reached its ledger append.
    highest_on_disk = max((r["pick_ordinal"] for r in numbered), default=0)
    start_at = max(ordinal_lib.max_ever_issued(home), highest_on_disk) + 1

    unnumbered.sort(key=lambda r: (r["enrolled_at"], r["project_uuid"]))
    assignments = [(row, start_at + i) for i, row in enumerate(unnumbered)]
    return assignments, numbered, start_at


def apply_plan(assignments, home=None):
    """Write each ordinal to its row, then record the issue in the ledger."""
    for row, ordinal in assignments:
        registry_lib.set_pick_ordinal(row["project_uuid"], ordinal, home)
        ordinal_lib.append_event(
            "issue", ordinal, row["project_uuid"], row["name"], home,
            reason="backfill")
    return len(assignments)


def _describe(row):
    name = row["name"]
    status = row["status"]
    return "%-28s %-11s %s  %s" % (name[:28], status, row["enrolled_at"][:19],
                                   row["project_uuid"])


def run(home=None, apply=False):
    assignments, numbered, start_at = plan(home)
    total = len(assignments) + len(numbered)

    print("registry: %s" % registry_lib.registry_dir(home))
    print("rows: %d total — %d already numbered, %d to assign"
          % (total, len(numbered), len(assignments)))
    if numbered:
        print("ledger high-water before this run: %d" % (start_at - 1))

    if not assignments:
        print("\nnothing to do — every row already holds a pick_ordinal.")
        return 0

    print("\nplan (sorted by enrolled_at, then project_uuid):")
    for row, ordinal in assignments:
        print("  %4d  %s" % (ordinal, _describe(row)))

    if not apply:
        print("\nDRY RUN — nothing written. Re-run with --apply to write.")
        return 0

    written = apply_plan(assignments, home)
    print("\nwrote %d ordinal(s). ledger max is now %d; the next new project "
          "takes %d." % (written, ordinal_lib.max_ever_issued(home),
                         ordinal_lib.next_ordinal(home)))
    return 0


# --------------------------------------------------------------------------
# self-test — builds a fixture registry, never touches the real ~/.acos
# --------------------------------------------------------------------------

def _mkrow(home, uuid, name, enrolled_at, status="active"):
    """Write a fixture row directly, bypassing upsert_row's minting."""
    root = os.path.join(home, "roots", name)
    os.makedirs(root, exist_ok=True)
    st = os.stat(root)
    row = {
        "project_uuid": uuid, "root": root,
        "root_casefold": os.path.realpath(root).casefold(),
        "dev_ino": [st.st_dev, st.st_ino], "name": name,
        "workspace_name": name, "status": status,
        "enrolled_at": enrolled_at, "last_verified_at": enrolled_at,
        "last_close": None, "last_session_id_hint": None, "git": None,
        "tombstoned_at": None, "pick_ordinal": None,
    }
    registry_lib.atomic_write_json(registry_lib.row_path(uuid, home), row)
    return row


def _selftest(home):
    fails = []

    def check(label, cond):
        print(("  ok   " if cond else "  FAIL ") + label)
        if not cond:
            fails.append(label)

    os.makedirs(registry_lib.registry_dir(home), exist_ok=True)
    # Deliberately created out of order, so a bug that uses file order or
    # creation order instead of enrolled_at shows up.
    _mkrow(home, "uuid-charlie", "Charlie", "2026-03-03T00:00:00+00:00")
    _mkrow(home, "uuid-alpha", "Alpha", "2026-01-01T00:00:00+00:00")
    _mkrow(home, "uuid-delta", "Delta", "2026-04-04T00:00:00+00:00", "tombstoned")
    _mkrow(home, "uuid-bravo", "Bravo", "2026-02-02T00:00:00+00:00", "parked")

    assignments, numbered, start = plan(home)
    check("nothing numbered yet", numbered == [])
    check("starts at 1 on an empty ledger", start == 1)
    order = [(r["name"], n) for r, n in assignments]
    check("oldest enrolled_at gets 1", order[0] == ("Alpha", 1))
    check("order follows enrolled_at, not file order",
          order == [("Alpha", 1), ("Bravo", 2), ("Charlie", 3), ("Delta", 4)])
    check("tombstoned rows are numbered too", ("Delta", 4) in order)

    apply_plan(assignments, home)
    check("ledger max is 4 after apply", ordinal_lib.max_ever_issued(home) == 4)
    check("next new project takes 5", ordinal_lib.next_ordinal(home) == 5)
    check("no ordinal is retired by a backfill",
          ordinal_lib.retired_ordinals(home) == {})

    # idempotence
    again, numbered2, _ = plan(home)
    check("second run assigns nothing", again == [])
    check("second run sees all 4 numbered", len(numbered2) == 4)
    before = registry_lib.load_row("uuid-alpha", home)["pick_ordinal"]
    run(home, apply=True)
    after = registry_lib.load_row("uuid-alpha", home)["pick_ordinal"]
    check("re-run leaves an existing ordinal untouched", before == after == 1)
    check("re-run appends no duplicate ledger lines",
          len(ordinal_lib.read_events(home)) == 4)

    # resume-after-interruption: a fresh row joins at the high-water mark
    _mkrow(home, "uuid-echo", "Echo", "2026-01-15T00:00:00+00:00")
    resumed, _, start3 = plan(home)
    check("a later-discovered row does NOT displace existing numbers",
          start3 == 5 and [(r["name"], n) for r, n in resumed] == [("Echo", 5)])

    # a new row created through upsert_row mints from the ledger
    apply_plan(resumed, home)
    newroot = os.path.join(home, "roots", "Foxtrot")
    os.makedirs(newroot, exist_ok=True)
    fresh = registry_lib.upsert_row(
        {"project_uuid": "uuid-foxtrot", "root": newroot,
         "workspace_name": "Foxtrot"}, home)
    check("upsert_row mints max+1 for a brand-new row", fresh["pick_ordinal"] == 6)
    again2 = registry_lib.upsert_row(
        {"project_uuid": "uuid-foxtrot", "root": newroot, "status": "parked"}, home)
    check("upsert_row does NOT re-mint on update", again2["pick_ordinal"] == 6)

    # tombstoning must not move or free the number
    registry_lib.tombstone_row("uuid-foxtrot", home)
    tomb = registry_lib.load_row("uuid-foxtrot", home)
    check("tombstone keeps the ordinal on the row", tomb["pick_ordinal"] == 6)
    check("tombstone alone does not retire the ordinal",
          6 not in ordinal_lib.retired_ordinals(home))
    check("next new project still takes 7", ordinal_lib.next_ordinal(home) == 7)

    print("\n%d check(s) failed" % len(fails) if fails else "\nall checks passed")
    return 1 if fails else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--apply", action="store_true", help="write (default is a dry run)")
    ap.add_argument("--home", default=None, help="override ~ (tests only)")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--json", action="store_true", help="machine-readable plan")
    args = ap.parse_args(argv)

    if args.selftest:
        tmp = args.home or tempfile.mkdtemp(prefix="backfill-selftest-")
        print("selftest home: %s" % tmp)
        try:
            return _selftest(tmp)
        finally:
            if not args.home:
                shutil.rmtree(tmp, ignore_errors=True)

    if args.json:
        assignments, numbered, start = plan(args.home)
        print(json.dumps({
            "start_at": start,
            "already_numbered": len(numbered),
            "assignments": [{"project_uuid": r["project_uuid"], "name": r["name"],
                             "enrolled_at": r["enrolled_at"], "pick_ordinal": n}
                            for r, n in assignments],
        }, indent=2))
        return 0

    return run(args.home, apply=args.apply)


if __name__ == "__main__":
    raise SystemExit(main())
