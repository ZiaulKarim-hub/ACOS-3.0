#!/usr/bin/env python3
"""ordinal_lib.py — the append-only ordinal ledger (ACOS Resurrection Protocol).

WHY THIS EXISTS (Zee's ruling, 2026-08-19). Pick numbers used to be a
per-render counter: `resurrect-view.py` counted rows down the page and handed
out 1, 2, 3... every time the book was drawn. A number therefore MOVED when a
row changed tier, and a row changes tier when a tagged cmux workspace appears
or disappears — which happens when a human closes a tab BY HAND, with no
registry write at all. A number read off a stale screen resolved to a
different project.

The ruling: a number is assigned ONCE to a row and never changes on its own.
That lives in `pick_ordinal` on the row (registry_lib.ROW_KEYS). This file is
the other half — the record of every ordinal ever issued, so a number freed by
a delete or a renumber is NEVER handed back out automatically.

  row.pick_ordinal   "what number does this row hold RIGHT NOW"
  this ledger        "what numbers have EVER been issued, and to what"

Auto-assignment reads `max_ever_issued() + 1`. It never reads the live rows,
because the live rows have forgotten every number a deleted project took with
it. Precedent for the never-reuse rule: Atlassian documents that reusing Jira
keys means "old issue links... will stop redirecting"; Linux's fix for
recycled process ids was ESRCH — fail loudly rather than act on the wrong
target (pidfd_send_signal(2)).

MANUAL assignment MAY reuse a retired ordinal — `renumber <n> to <m>` warns,
names what previously held `m` and when, and requires explicit confirmation.
Automatic assignment never may. That asymmetry is the whole point: a human
who is told "7 used to be FruitSync, retired 2026-08-19" can decide; a
counter cannot.

Python, not TypeScript, by the standing exception: this extends the existing
registry_lib / knowledge_lib script family, shares their storage root, and
copies audit_append's exact single-write discipline. Re-implementing that in
another language beside them would give two write disciplines over one
directory.

Constraints (shared with registry_lib.py):
  * system /usr/bin/python3 is 3.9.6, stdlib ONLY, no yaml module.
  * Append-only. Nothing here truncates or rewrites the ledger.
  * ONE os.write per line, O_APPEND — concurrent appenders cannot interleave
    bytes within a line on a local filesystem.
  * No blocking lock and no lock that survives SIGKILL. `max+1` therefore has
    a race; it is not prevented here, it is DIAGNOSED by conflict-scan.py's
    ORDINAL-CLASH check. At one human and a few opens a day the race is very
    unlikely, but it must be diagnosable if it happens.
  * Timestamps are timezone-aware UTC ISO-8601.
  * Every function takes `home=None`; tests pass an override so they never
    touch the real ~/.acos.

RESERVED: 0 is never issued. acos-safe-close/SKILL.md:235-241 uses 0 for
"new project", so a row holding 0 would be read as "not a project yet".

Self-test: python3 ordinal_lib.py --selftest [--home DIR]
"""

import argparse
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import registry_lib  # noqa: E402  (shared home/audit/timestamp helpers)

LEDGER_NAME = "ordinal-ledger.jsonl"

# `issue`    a brand-new row took this ordinal
# `retire`   the ordinal stopped being held (delete, tombstone-with-delete,
#            or the vacated side of a renumber). NEVER auto-reissued after.
# `restore`  a deleted row came back and reclaimed its original ordinal
# `renumber` one row moved from `from_ordinal` to `ordinal` (also used by
#            `compact`, marked via="compact", one entry per row moved)
# `swap`     two rows exchanged; one entry, both sides recorded
VERBS = ("issue", "retire", "restore", "renumber", "swap")

# Keys every entry carries. Per-verb extras: `from_ordinal` (renumber, swap),
# `counterpart` (swap), `reason` (retire), `via` (renumber under compact).
BASE_KEYS = ("at", "verb", "ordinal", "project_uuid", "name")


def ledger_path(home=None):
    """The ledger lives BESIDE the row files, in registry.d/."""
    return os.path.join(registry_lib.registry_dir(home), LEDGER_NAME)


def _check_ordinal(value, field="ordinal"):
    """Ordinals are positive integers. 0 is reserved; bools are not ints here."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("%s must be an int, got %r" % (field, value))
    if value <= 0:
        raise ValueError("%s must be >= 1 (0 is reserved for 'new project'), got %d"
                         % (field, value))
    return value


def append_event(verb, ordinal, project_uuid, name, home=None, **extra):
    """Append ONE ledger line with a SINGLE os.write.

    `name` is the row's display name AT THE TIME — deliberately a snapshot,
    not a live lookup, so a later rename does not rewrite history. That is
    what makes "7 used to be FruitSync" answerable after FruitSync is gone.
    """
    if verb not in VERBS:
        raise ValueError("unknown ledger verb %r (allowed: %s)" % (verb, "/".join(VERBS)))
    _check_ordinal(ordinal)
    if not project_uuid or not isinstance(project_uuid, str):
        raise ValueError("project_uuid must be a non-empty string, got %r" % (project_uuid,))
    if not isinstance(name, str):
        raise ValueError("name must be a string, got %r" % (name,))

    record = {
        "at": registry_lib.utc_now_iso(),
        "verb": verb,
        "ordinal": ordinal,
        "project_uuid": project_uuid,
        "name": name,
    }
    if "from_ordinal" in extra and extra["from_ordinal"] is not None:
        _check_ordinal(extra["from_ordinal"], "from_ordinal")
    cp = extra.get("counterpart")
    if cp is not None:
        if not isinstance(cp, dict):
            raise ValueError("counterpart must be a dict, got %r" % (cp,))
        _check_ordinal(cp.get("ordinal"), "counterpart.ordinal")
        if cp.get("from_ordinal") is not None:
            _check_ordinal(cp["from_ordinal"], "counterpart.from_ordinal")
    record.update({k: v for k, v in extra.items() if v is not None})

    line = (json.dumps(record, separators=(",", ":")) + "\n").encode("utf-8")
    path = ledger_path(home)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
    try:
        os.write(fd, line)  # exactly one write per line
    finally:
        os.close(fd)
    return record


def read_events(home=None):
    """Every ledger entry, oldest first. Missing ledger -> [].

    A malformed line raises. The ledger is the source of truth for what a
    number means; a silently skipped line would let a retired ordinal look
    free, which is the exact failure this file exists to prevent.
    """
    path = ledger_path(home)
    try:
        with open(path, "rb") as fh:
            raw = fh.read().decode("utf-8")
    except FileNotFoundError:
        return []
    events = []
    for lineno, line in enumerate(raw.splitlines(), 1):
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except ValueError as exc:
            raise ValueError("%s line %d is not valid JSON: %s" % (path, lineno, exc))
        if not isinstance(rec, dict):
            raise ValueError("%s line %d is not a JSON object" % (path, lineno))
        missing = [k for k in BASE_KEYS if k not in rec]
        if missing:
            raise ValueError("%s line %d missing keys: %s"
                             % (path, lineno, ", ".join(missing)))
        events.append(rec)
    return events


def _ordinals_in(rec):
    """Every ordinal an entry touches — the basis for 'ever issued'."""
    seen = [rec["ordinal"]]
    if rec.get("from_ordinal") is not None:
        seen.append(rec["from_ordinal"])
    cp = rec.get("counterpart")
    if isinstance(cp, dict):
        if cp.get("ordinal") is not None:
            seen.append(cp["ordinal"])
        if cp.get("from_ordinal") is not None:
            seen.append(cp["from_ordinal"])
    return [n for n in seen if isinstance(n, int) and not isinstance(n, bool)]


def max_ever_issued(home=None, events=None):
    """Highest ordinal that has EVER appeared in the ledger. 0 if empty.

    Counts tombstoned AND deleted AND renumbered-away ordinals. That is the
    point — a freed number must never come back automatically.
    """
    evs = read_events(home) if events is None else events
    high = 0
    for rec in evs:
        for n in _ordinals_in(rec):
            if n > high:
                high = n
    return high


def next_ordinal(home=None, events=None):
    """The ordinal an automatically-created row takes: max ever issued + 1.

    RACE, on the record: registry_lib documents no blocking lock and none
    surviving SIGKILL, so two simultaneous creations can both read the same
    max. Not prevented here. conflict-scan.py's ORDINAL-CLASH check is the
    detector.
    """
    return max_ever_issued(home, events) + 1


def retired_ordinals(home=None, events=None):
    """Ordinals whose LATEST event left them unheld -> {ordinal: last_retire_rec}.

    Replayed in order, because a number can be retired and then restored:
      issue    -> held
      retire   -> retired
      restore  -> held again
      renumber -> the new ordinal is held, `from_ordinal` is retired
      swap     -> both sides end up held
    """
    evs = read_events(home) if events is None else events
    retired = {}
    for rec in evs:
        verb = rec["verb"]
        if verb in ("issue", "restore"):
            retired.pop(rec["ordinal"], None)
        elif verb == "retire":
            retired[rec["ordinal"]] = rec
        elif verb == "renumber":
            retired.pop(rec["ordinal"], None)
            if rec.get("from_ordinal") is not None:
                retired[rec["from_ordinal"]] = rec
        elif verb == "swap":
            retired.pop(rec["ordinal"], None)
            cp = rec.get("counterpart") or {}
            if cp.get("ordinal") is not None:
                retired.pop(cp["ordinal"], None)
    return retired


def history_for(ordinal, home=None, events=None):
    """Every entry that touched `ordinal`, oldest first.

    Feeds the `renumber` warning: "7 previously held FruitSync, retired
    2026-08-19". Without this the human confirmation would be a bare yes/no
    with nothing to judge.
    """
    _check_ordinal(ordinal)
    evs = read_events(home) if events is None else events
    return [rec for rec in evs if ordinal in _ordinals_in(rec)]


def live_holders(home=None):
    """{pick_ordinal: [row, ...]} over rows currently on disk (any status).

    Reads the ROWS, not the ledger — this answers "who holds this number
    now", which is what refuses a colliding renumber or restore. Rows with no
    ordinal yet (pre-backfill) are skipped. A list, not a single row, because
    a clash is exactly what conflict-scan.py must be able to see.
    """
    holders = {}
    for row in registry_lib._iter_rows(home):
        n = row.get("pick_ordinal")
        if n is None:
            continue
        holders.setdefault(n, []).append(row)
    return holders


# --------------------------------------------------------------------------
# self-test
# --------------------------------------------------------------------------

def _selftest(home):
    """Exercise the ledger against a throwaway home. Raises on any failure."""
    os.makedirs(registry_lib.registry_dir(home), exist_ok=True)
    fails = []

    def check(label, cond):
        print(("  ok   " if cond else "  FAIL ") + label)
        if not cond:
            fails.append(label)

    check("empty ledger -> max 0", max_ever_issued(home) == 0)
    check("empty ledger -> next 1", next_ordinal(home) == 1)
    check("empty ledger -> no retired", retired_ordinals(home) == {})

    append_event("issue", 1, "uuid-a", "Alpha", home)
    append_event("issue", 2, "uuid-b", "Beta", home)
    check("two issues -> max 2", max_ever_issued(home) == 2)
    check("two issues -> next 3", next_ordinal(home) == 3)

    append_event("retire", 2, "uuid-b", "Beta", home, reason="delete")
    check("retire does not lower max", max_ever_issued(home) == 2)
    check("retire keeps next at 3", next_ordinal(home) == 3)
    check("retired set has 2", set(retired_ordinals(home)) == {2})

    append_event("restore", 2, "uuid-b", "Beta", home)
    check("restore clears retired", retired_ordinals(home) == {})

    append_event("renumber", 9, "uuid-a", "Alpha", home, from_ordinal=1)
    check("renumber raises max to 9", max_ever_issued(home) == 9)
    check("renumber retires the vacated 1", set(retired_ordinals(home)) == {1})
    check("renumber moves next to 10", next_ordinal(home) == 10)

    append_event("swap", 2, "uuid-a", "Alpha", home, from_ordinal=9,
                 counterpart={"ordinal": 9, "project_uuid": "uuid-b",
                              "name": "Beta", "from_ordinal": 2})
    check("swap leaves both held", set(retired_ordinals(home)) == {1})
    check("swap keeps max at 9", max_ever_issued(home) == 9)

    hist = history_for(1, home)
    check("history_for(1) sees issue + renumber", len(hist) == 2)
    check("history_for(1) is oldest first", hist[0]["verb"] == "issue")

    # replay is pure: reading twice must not change anything
    check("read_events is stable", read_events(home) == read_events(home))

    for bad, label in ((0, "zero"), (-3, "negative"), (True, "bool")):
        try:
            append_event("issue", bad, "uuid-x", "X", home)
            check("rejects %s ordinal" % label, False)
        except ValueError:
            check("rejects %s ordinal" % label, True)

    try:
        append_event("nonsense", 5, "uuid-x", "X", home)
        check("rejects unknown verb", False)
    except ValueError:
        check("rejects unknown verb", True)

    # a torn/garbage line must be LOUD, never silently skipped
    with open(ledger_path(home), "a") as fh:
        fh.write("{not json\n")
    try:
        read_events(home)
        check("garbage line raises", False)
    except ValueError:
        check("garbage line raises", True)

    print("\n%d check(s) failed" % len(fails) if fails else "\nall checks passed")
    return 1 if fails else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--home", default=None, help="override ~ (tests only)")
    ap.add_argument("--max", action="store_true", help="print max ever issued")
    ap.add_argument("--next", action="store_true", help="print the next auto ordinal")
    ap.add_argument("--retired", action="store_true", help="list retired ordinals")
    args = ap.parse_args(argv)

    if args.selftest:
        home = args.home
        if home is None:
            tmp = tempfile.mkdtemp(prefix="ordinal-selftest-")
            print("selftest home: %s" % tmp)
            return _selftest(tmp)
        return _selftest(home)
    if args.max:
        print(max_ever_issued(args.home))
        return 0
    if args.next:
        print(next_ordinal(args.home))
        return 0
    if args.retired:
        for n, rec in sorted(retired_ordinals(args.home).items()):
            print("%d  retired %s  last held by %s (%s)"
                  % (n, rec["at"], rec["name"], rec["project_uuid"]))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
