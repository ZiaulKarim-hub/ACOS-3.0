#!/usr/bin/env python3
"""windows_lib.py — several windows working ONE project, coherently.
(ACOS Resurrection Protocol, user brief 2026-08-04, workstream MW.)

D9   several context windows on one project is a FIRST-CLASS supported mode.
D10  the book still shows ONE row per project, with a live-window count.
D11  the one-project-one-tab guard STAYS as the default. But picking an
     already-open project now ASKS: focus the existing window, or open another.
     Zee wants the choice, not the removal of the guard.
D12  window names derive from the project name — "OKOA works *label*".
D13  on safe close a labelled window's learnings fold back into the SINGLE
     per-project knowledge store; the label survives as provenance on each
     fact, never as a separate store.
D14  closing ONE window does not park the project. The row stays active while
     any window is open; it parks only when the LAST window closes.

WHAT THIS FILE HOLDS: the per-window manifest — who is open on this project
right now and what each one is working on. That is what MW-C reads so a new
window does not silently duplicate another's work.

THIS IS RUNTIME STATE, NOT KNOWLEDGE. It lives at
  ~/.acos/windows/<project_uuid>/<workspace_id>.json
deliberately apart from ~/.acos/knowledge/<project_uuid>/, because it is true
only while a window is open. Knowledge is append-only and permanent; this is
neither. Mixing them would let a closed window's scratch state masquerade as a
durable fact.

LIVENESS IS NEVER TRUSTED FROM THE FILE. A manifest entry proves a window once
claimed the project, not that it still exists — cmux can restart under a live
process (the SET-BUT-DEAD case the adopt gates already guard). So every read
takes the caller's LIVE workspace-id set and filters against it. A stale entry
is reported as stale, never counted as an open window.

Constraints: stdlib only, python 3.9.6, same atomic-write discipline as
registry_lib.py. Python (not TypeScript/Rust) because it is imported by the
embedded python bodies of adopt-project.sh and close-project.sh, which are
fixed to the system interpreter — the existing-code exception.

Self-test: python3 windows_lib.py --selftest --home DIR
"""

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timezone


def _home(home=None):
    return home if home else os.path.expanduser("~")


def windows_dir(project_uuid, home=None):
    return os.path.join(_home(home), ".acos", "windows", project_uuid)


def _entry_path(project_uuid, workspace_id, home=None):
    safe = "".join(ch for ch in (workspace_id or "") if ch.isalnum() or ch in "-_")
    return os.path.join(windows_dir(project_uuid, home), "%s.json" % (safe or "unknown"))


def utc_now_iso():
    return datetime.now(timezone.utc).isoformat()


def _atomic_write(path, obj):
    d = os.path.dirname(path)
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp-", suffix=".swap")
    try:
        with os.fdopen(fd, "w") as fh:
            json.dump(obj, fh, indent=2, sort_keys=True)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def claim_window(project_uuid, workspace_id, label=None, session_id=None,
                 working_on=None, home=None):
    """Record that THIS window is open on this project.

    Idempotent: re-claiming updates the entry in place and preserves the
    original claimed_at, so a re-adopt does not look like a new window.
    """
    path = _entry_path(project_uuid, workspace_id, home)
    prior = _read(path) or {}
    entry = {
        "project_uuid": project_uuid,
        "workspace_id": workspace_id,
        "label": label,
        "session_id": session_id,
        "working_on": working_on if working_on is not None else prior.get("working_on"),
        "claimed_at": prior.get("claimed_at") or utc_now_iso(),
        "updated_at": utc_now_iso(),
    }
    _atomic_write(path, entry)
    return entry


def set_working_on(project_uuid, workspace_id, working_on, home=None):
    """Update what this window is doing, so the next window can read it.

    Refuses to invent an entry: a window that never claimed the project has
    nothing to update, and silently creating one would report a window as open
    that never was.
    """
    path = _entry_path(project_uuid, workspace_id, home)
    entry = _read(path)
    if entry is None:
        return None
    entry["working_on"] = working_on
    entry["updated_at"] = utc_now_iso()
    _atomic_write(path, entry)
    return entry


def release_window(project_uuid, workspace_id, home=None):
    """Drop this window's claim (its tab closed, or it adopted another project).

    Returns True if a claim was removed. Removing runtime state is correct here
    and is NOT in tension with the append-only rule — that rule governs
    KNOWLEDGE, which is permanent. A claim that outlives its window is a lie.
    """
    path = _entry_path(project_uuid, workspace_id, home)
    try:
        os.unlink(path)
        return True
    except OSError:
        return False


def _read(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def all_claims(project_uuid, home=None):
    """Every claim on disk, live or not. Unparseable entries are skipped."""
    d = windows_dir(project_uuid, home)
    out = []
    try:
        names = sorted(os.listdir(d))
    except OSError:
        return out
    for fn in names:
        if not fn.endswith(".json"):
            continue
        e = _read(os.path.join(d, fn))
        if e:
            out.append(e)
    return out


def live_windows(project_uuid, live_workspace_ids, home=None):
    """(live, stale) — claims split by whether their workspace still exists.

    `live_workspace_ids` comes from a FRESH cmux workspace.list at the call
    site. Passing None means liveness is unknown; then everything is returned
    as live and the caller must say so rather than imply it verified anything.
    """
    claims = all_claims(project_uuid, home)
    if live_workspace_ids is None:
        return claims, []
    alive = {str(w).casefold() for w in live_workspace_ids}
    live = [c for c in claims if str(c.get("workspace_id", "")).casefold() in alive]
    stale = [c for c in claims if str(c.get("workspace_id", "")).casefold() not in alive]
    return live, stale


def other_windows(project_uuid, my_workspace_id, live_workspace_ids, home=None):
    """MW-C: the OTHER live windows on this project — what a new window must
    read before it starts, so two windows do not duplicate work."""
    live, _stale = live_windows(project_uuid, live_workspace_ids, home)
    mine = str(my_workspace_id or "").casefold()
    return [c for c in live if str(c.get("workspace_id", "")).casefold() != mine]


def reap_stale(project_uuid, live_workspace_ids, home=None):
    """Remove claims whose workspace is gone. Returns the removed entries.

    Never called with live_workspace_ids=None — reaping on unknown liveness
    would delete every claim the moment cmux is unreachable.
    """
    if live_workspace_ids is None:
        return []
    _live, stale = live_windows(project_uuid, live_workspace_ids, home)
    for c in stale:
        release_window(project_uuid, c.get("workspace_id"), home)
    return stale


def is_last_window(project_uuid, my_workspace_id, live_workspace_ids, home=None):
    """D14: is this the LAST window open on the project?

    True means a close should park the row. False means other windows are still
    working and the row must stay active. Unknown liveness returns True — the
    conservative answer, because it preserves today's behaviour (a close parks)
    rather than silently leaving rows active forever when cmux cannot be read.
    """
    if live_workspace_ids is None:
        return True
    return not other_windows(project_uuid, my_workspace_id, live_workspace_ids, home)


# --------------------------------------------------------------------------
# MW-E — collision warning (OFF by default, behind a switch)
# --------------------------------------------------------------------------

TOUCH_CAP = 200
SWITCH_FILE = "collision-warning.enabled"


def switch_path(home=None):
    return os.path.join(_home(home), ".acos", "windows", SWITCH_FILE)


def collision_warning_enabled(home=None):
    """MW-E is OFF unless the switch file exists.

    Zee approved all five MW items; Claude costed this one high and advised
    deferring it, and the brief's own guidance was to build it LAST and behind
    a switch. So it ships complete but dormant: a warning that fires on stale
    or partial data is worse than none, because it trains you to ignore
    warnings. Turn it on with: touch ~/.acos/windows/collision-warning.enabled
    """
    return os.path.isfile(switch_path(home))


def set_collision_warning(on, home=None):
    p = switch_path(home)
    if on:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as fh:
            fh.write("MW-E collision warning: on\nenabled_at: %s\n" % utc_now_iso())
        return True
    try:
        os.unlink(p)
    except OSError:
        pass
    return False


def record_touch(project_uuid, workspace_id, paths, home=None):
    """Note that THIS window touched these files.

    HONEST SCOPE: nothing records touches automatically. Wiring a PostToolUse
    hook to feed this is the expensive, watch-heavy part Claude costed high and
    advised deferring; this is the ledger and the query, not the watcher. A
    caller (a hook, a skill step, or a session) must call this, and until one
    does, `collisions` correctly reports nothing rather than guessing.

    Capped at TOUCH_CAP most-recent paths so a long session cannot grow the
    manifest without bound.
    """
    path = _entry_path(project_uuid, workspace_id, home)
    entry = _read(path)
    if entry is None:
        return None
    touched = list(entry.get("touched") or [])
    for p in paths or []:
        p = os.path.abspath(p)
        if p in touched:
            touched.remove(p)
        touched.append(p)
    entry["touched"] = touched[-TOUCH_CAP:]
    entry["updated_at"] = utc_now_iso()
    _atomic_write(path, entry)
    return entry


def collisions(project_uuid, my_workspace_id, live_workspace_ids, home=None):
    """Files THIS window touched that another LIVE window also touched.

    Only live windows count — a closed window's ledger is history, not a
    conflict, and reporting it would be a false alarm every time.
    """
    mine = _read(_entry_path(project_uuid, my_workspace_id, home)) or {}
    my_paths = set(mine.get("touched") or [])
    if not my_paths:
        return []
    out = []
    for other in other_windows(project_uuid, my_workspace_id, live_workspace_ids, home):
        shared = sorted(my_paths & set(other.get("touched") or []))
        if shared:
            out.append({"label": other.get("label") or other.get("workspace_id"),
                        "workspace_id": other.get("workspace_id"),
                        "working_on": other.get("working_on"),
                        "files": shared})
    return out


def merge_window(project_uuid, from_ws, into_ws, home=None):
    """MW-D — fold one window's thread into another when the work converges.

    Two windows on one project often start apart and end up on the same thing.
    Merging says so explicitly instead of leaving a stale second claim that
    reads, to the next window, as work still in flight somewhere.

    What it does, and deliberately what it does NOT:
      * the source's `working_on` is APPENDED to the target's, so neither
        thread's description is lost;
      * the source's claim is released — it is runtime state, and a claim that
        outlives its thread is a lie;
      * KNOWLEDGE IS NOT TOUCHED. Both windows already write into the SAME
        per-project store (D13) with their label as provenance, so there is
        nothing to move and nothing to deduplicate. A merge that also rewrote
        facts would be destroying provenance to solve a problem that does not
        exist.

    Returns a receipt dict, or None if either window has no claim — merging a
    window that never claimed the project would invent a thread.
    """
    src = _read(_entry_path(project_uuid, from_ws, home))
    dst = _read(_entry_path(project_uuid, into_ws, home))
    if src is None or dst is None:
        return None
    src_label = src.get("label") or from_ws
    parts = [p for p in (dst.get("working_on"), src.get("working_on")) if p]
    combined = " + ".join(parts) if parts else None
    if src.get("working_on"):
        combined = "%s (merged in from %s)" % (combined, src_label)
    dst["working_on"] = combined
    dst["updated_at"] = utc_now_iso()
    dst.setdefault("merged_in", []).append(
        {"label": src_label, "workspace_id": from_ws,
         "working_on": src.get("working_on"), "at": utc_now_iso()})
    _atomic_write(_entry_path(project_uuid, into_ws, home), dst)
    release_window(project_uuid, from_ws, home)
    return {"from": src_label, "into": dst.get("label") or into_ws,
            "working_on": dst["working_on"]}


def describe(entry):
    """One plain line for a window claim — used in receipts, so it must read
    as a fact, not a guess."""
    label = entry.get("label") or "(no label)"
    doing = entry.get("working_on") or "not stated"
    return "%s — working on: %s (since %s)" % (label, doing,
                                               (entry.get("updated_at") or "?")[:19])


def _selftest(home):
    if not home:
        print("REFUSED: selftest must run under a --home override, never the real ~")
        return 1
    u = "22222222-3333-4444-8555-666666666666"
    failures = []

    def ck(label, cond, detail=""):
        if cond:
            print("  PASS  %s" % label)
        else:
            print("  FAIL  %s %s" % (label, detail))
            failures.append(label)

    print("claim + read back")
    claim_window(u, "WS-A", label="Golden East", session_id="s1",
                 working_on="the outparcel pricing", home=home)
    claim_window(u, "WS-B", label="Flyer", session_id="s2",
                 working_on="the broker flyer", home=home)
    ck("both claims stored", len(all_claims(u, home)) == 2)

    print("MW-C — a new window sees the others")
    others = other_windows(u, "WS-B", ["WS-A", "WS-B"], home)
    ck("one other window seen", len(others) == 1, others)
    ck("and what it is doing", others[0]["working_on"] == "the outparcel pricing")
    ck("never itself", all(o["workspace_id"] != "WS-B" for o in others))

    print("liveness is never trusted from the file")
    live, stale = live_windows(u, ["WS-A"], home)
    ck("a vanished workspace is stale, not live", len(live) == 1 and len(stale) == 1)
    ck("unknown liveness returns everything", len(live_windows(u, None, home)[0]) == 2)

    print("D14 — park only on the LAST window")
    ck("not last while another is open", not is_last_window(u, "WS-B", ["WS-A", "WS-B"], home))
    ck("last when alone", is_last_window(u, "WS-B", ["WS-B"], home))
    ck("unknown liveness is conservative", is_last_window(u, "WS-B", None, home))

    print("update + release")
    set_working_on(u, "WS-A", "now the sales report", home=home)
    ck("working_on updates", other_windows(u, "WS-B", ["WS-A", "WS-B"], home)[0]["working_on"]
       == "now the sales report")
    ck("no entry is invented for an unknown window",
       set_working_on(u, "WS-NOPE", "x", home=home) is None)
    claimed_at = all_claims(u, home)[0]["claimed_at"]
    claim_window(u, "WS-A", label="Golden East", home=home)
    ck("re-claim keeps the original claimed_at",
       all_claims(u, home)[0]["claimed_at"] == claimed_at)
    ck("release removes the claim", release_window(u, "WS-A", home) and
       len(all_claims(u, home)) == 1)

    print("MW-D — merge one thread into another")
    claim_window(u, "WS-X", label="Flyer", working_on="the flyer", home=home)
    claim_window(u, "WS-Y", label="Golden East", working_on="the pricing", home=home)
    r = merge_window(u, "WS-X", "WS-Y", home=home)
    ck("merge returns a receipt", r is not None and r["from"] == "Flyer", r)
    ck("neither thread's description is lost",
       "the pricing" in r["working_on"] and "the flyer" in r["working_on"], r)
    ck("the merged-from claim is released",
       _read(_entry_path(u, "WS-X", home)) is None)
    ck("the target records what it absorbed",
       _read(_entry_path(u, "WS-Y", home))["merged_in"][0]["label"] == "Flyer")
    ck("merging an unknown window is refused",
       merge_window(u, "WS-NOPE", "WS-Y", home=home) is None)
    release_window(u, "WS-Y", home)

    print("MW-E — collision warning, off by default")
    ck("off unless the switch file exists", not collision_warning_enabled(home))
    set_collision_warning(True, home=home)
    ck("the switch turns it on", collision_warning_enabled(home))
    claim_window(u, "WS-P", label="One", working_on="edit A", home=home)
    claim_window(u, "WS-Q", label="Two", working_on="edit B", home=home)
    record_touch(u, "WS-P", ["/tmp/shared.py", "/tmp/only-p.py"], home=home)
    record_touch(u, "WS-Q", ["/tmp/shared.py", "/tmp/only-q.py"], home=home)
    col = collisions(u, "WS-P", ["WS-P", "WS-Q"], home=home)
    ck("a shared file is reported", len(col) == 1 and col[0]["files"] == ["/tmp/shared.py"], col)
    ck("files only one window touched are not reported",
       "/tmp/only-q.py" not in col[0]["files"])
    ck("a DEAD window is never a collision",
       collisions(u, "WS-P", ["WS-P"], home=home) == [])
    ck("no ledger means no guess", collisions(u, "WS-Q", ["WS-Q"], home=home) == [])
    ck("touching an unknown window is refused",
       record_touch(u, "WS-NOPE", ["/tmp/x"], home=home) is None)
    set_collision_warning(False, home=home)
    ck("the switch turns it off again", not collision_warning_enabled(home))
    release_window(u, "WS-P", home); release_window(u, "WS-Q", home)

    print("reaping")
    claim_window(u, "WS-C", label="Ghost", home=home)
    reaped = reap_stale(u, ["WS-B"], home)
    ck("a dead window's claim is reaped", len(reaped) == 1 and reaped[0]["label"] == "Ghost")
    ck("reaping is refused on unknown liveness", reap_stale(u, None, home) == [])

    print()
    if failures:
        print("FAILED: %d — %s" % (len(failures), "; ".join(failures)))
        return 1
    print("windows_lib selftest: ALL PASSED")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="per-project window manifest")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--home", default=None)
    ap.add_argument("--project", default=None)
    ap.add_argument("--workspace", default=None, help="workspace id (default $CMUX_WORKSPACE_ID)")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--working-on", default=None, help="say what this window is doing (MW-C)")
    ap.add_argument("--touch", nargs="+", default=None, help="record files this window touched (MW-E)")
    ap.add_argument("--collisions", action="store_true", help="files another live window also touched")
    ap.add_argument("--live", default=None, help="comma-separated live workspace ids")
    ap.add_argument("--merge-from", default=None, help="fold that window's thread into this one (MW-D)")
    ap.add_argument("--enable-collision-warning", action="store_true")
    ap.add_argument("--disable-collision-warning", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        return _selftest(args.home)
    if args.enable_collision_warning:
        set_collision_warning(True, args.home)
        print("MW-E collision warning: ON (%s)" % switch_path(args.home))
        return 0
    if args.disable_collision_warning:
        set_collision_warning(False, args.home)
        print("MW-E collision warning: OFF")
        return 0

    ws = args.workspace or os.environ.get("CMUX_WORKSPACE_ID")
    live = [x.strip() for x in (args.live or "").split(",") if x.strip()] or None

    if args.project and args.list:
        print(json.dumps(all_claims(args.project, args.home), indent=2))
        return 0
    if args.project and args.working_on is not None:
        e = set_working_on(args.project, ws, args.working_on, args.home)
        print("updated" if e else "REFUSED — this window has no claim on that project")
        return 0 if e else 1
    if args.project and args.touch:
        e = record_touch(args.project, ws, args.touch, args.home)
        print("recorded %d path(s)" % len(args.touch) if e
              else "REFUSED — this window has no claim on that project")
        return 0 if e else 1
    if args.project and args.merge_from:
        r = merge_window(args.project, args.merge_from, ws, args.home)
        print(json.dumps(r, indent=2) if r
              else "REFUSED — one of those windows has no claim on that project")
        return 0 if r else 1
    if args.project and args.collisions:
        if not collision_warning_enabled(args.home):
            print("MW-E is OFF — enable with --enable-collision-warning")
        print(json.dumps(collisions(args.project, ws, live, args.home), indent=2))
        return 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
