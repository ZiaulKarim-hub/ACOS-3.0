#!/usr/bin/env python3
"""manage-ordinals.py — the row-management verbs (Zee's request, 2026-08-19).

  status              what every number is, what is retired, what is free
  delete <n>          row moves to the trash, its number is FREED, its close
                      bundles are archived, its knowledge facts stay
  restore <uuid>      bring a deleted row back — its original number if still
                      free, otherwise the lowest free one; bundles come back too
  purge <uuid>        unlink the row from the trash. Irreversible for the ROW.
                      Knowledge facts and archived bundles are NOT erased.
  swap <a> <b>        two rows exchange numbers
  renumber <n> <m>    one row moves to a different number
  compact             close every gap, 1..N. LOUD, opt-in, never automatic.

EVERY VERB HERE IS HUMAN-INITIATED ONLY. Never invoke one on your own
initiative, never batch them, never "tidy up" with them. The user must name
the row themselves in the conversation, exactly as the existing `tombstone`
verb already requires.

WHY delete AND tombstone BOTH EXIST. `finish` and `tombstone` only HIDE a row:
it stays in registry.d/, keeps its number forever, and stays visible under
ARCHIVED. That is the right default, because a hidden row is recoverable by
anyone who can read the book. `delete` is for the other case — a row that
should not be in the book at all (a mis-enrolment, a stray worktree row) —
and it still does not unlink anything. Only `purge` unlinks, only from
deleted/, and only when a human types the name a second time.

WHAT A DELETE DOES AND DOES NOT MOVE (Zee's rulings, 2026-08-24). He asked why
delete and purge both existed if delete did not actually free anything. Answer:
the two-step is a trash can, and it earns its keep for the row's CONTENTS, not
for its number — a row carries knowledge facts and close history that git does
not back up. So the contents keep an undo window, and the number does not:

  the NUMBER      freed the instant the row is deleted, so the book goes clean
                  at once. `restore` takes it back only if still free.
  CLOSE BUNDLES   archived — "treat it as /acos-complete" (his words). Each
                  handoff inside is stamped `status: completed` and the bundle
                  moves to memory/handoffs/archive/closed/. `.resume.md` files
                  never move; the eternity protocol needs them in place. Only
                  bundles PROVEN by the .project-uuid marker are moved; a guess
                  is reported and left alone.
  KNOWLEDGE FACTS never touched, by delete OR purge. Nothing else on this
                  machine backs them up.

CONFIRMATION IS ACTIVE, NOT PASSIVE — you must type the project's NAME, not
`y`, not Enter. Evidence: Akhawe & Felt, USENIX Security 2013 (>25M
impressions) found extra clicks do not deter — 84% of Firefox users who did
the first two clicks did the third. Habituation work (Vance et al., MIS
Quarterly 42(2) 2018; Anderson et al., CHI 2015) shows attention drops sharply
after the SECOND exposure. Bravo-Lillo et al., SOUPS 2014 found prompts that
"forced the user to interact with the text field containing the change"
resisted habituation — flagged MEDIUM confidence, since the paper sites
returned 403 and it came via a search index. Precedent: GitHub makes you "type
the name of the repository you want to delete" despite having a stable id.

HONEST LIMIT OF THAT GUARD, on the record. When this script runs from a skill
rather than a terminal, the name arrives as --confirm-name and the script
cannot tell a name the human typed from a name a model copied off the screen.
The guard is PROCEDURAL there, not mechanical. It is mechanical only at an
interactive terminal, where the prompt reads from a tty. The receipt always
prints which route was used, so the weaker case is never silent.

`delete --no-cmux` SKIPS the open-window check. It exists for fixture tests and
for a human who is certain nothing is open. A SKILL MUST NEVER PASS IT: the
check is what stops a row being deleted out from under a live window, and an
assistant is exactly the caller that cannot know whether a window is open. The
receipt prints the skip in full whenever it is used.

THE ORDINAL LEDGER records every issue, retire, restore, swap and renumber
(ordinal_lib.py). It is the answer to "what has number 7 ever been".

REUSE RULE, REVERSED 2026-08-24 — Zee: "A freed number can be assigned, change
that rule." A freed number used to be retired forever and never auto-reissued.
Now automatic assignment takes the LOWEST FREE number, and `renumber` onto a
previously-held number needs no extra flag. `renumber` still PRINTS what that
number used to hold and when, because the fact is worth knowing; it just no
longer blocks. A row sitting in deleted/ still HOLDS its number, so `restore`
keeps working — only `purge` truly frees one.

Python, not TypeScript, by the standing exception: it calls registry_lib,
ordinal_lib and windows_lib writers directly, so the schema gate, the
atomic-write pattern and the append-only ledger discipline all still apply.

Exit codes: 0 = done, 1 = refused (a stated reason), 2 = could not run.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ordinal_lib  # noqa: E402
import registry_lib  # noqa: E402
import windows_lib  # noqa: E402

CMUX_BIN = os.environ.get("CMUX_CLAUDE_HOOK_CMUX_BIN",
                          "/Applications/cmux.app/Contents/Resources/bin/cmux")
KEY_RE = re.compile(r"\[key:([0-9a-fA-F-]{36})\]")


class Refused(Exception):
    """A stated refusal. Printed plainly; exit 1. Never a traceback."""


# --------------------------------------------------------------------------
# paths
# --------------------------------------------------------------------------

def deleted_dir(home=None):
    return os.path.join(registry_lib.registry_dir(home), "deleted")


def deleted_row_path(project_uuid, home=None):
    return os.path.join(deleted_dir(home), "%s.json" % project_uuid)


def deleted_bundles_manifest(project_uuid, home=None):
    """Where a delete records which close bundles it archived, so restore can
    put every one of them back. Lives beside the deleted row, in the trash."""
    return os.path.join(deleted_dir(home), "%s.bundles.json" % project_uuid)


def archived_closed_dir(root):
    """Where a deleted row's close bundles go (Zee, 2026-08-24: "treat it as
    /acos-complete"). That skill archives SESSION handoffs from
    memory/handoffs/ into memory/handoffs/archive/. A row's own history is a
    different set — the CLOSE BUNDLES under memory/handoffs/closed/ — so they
    land in a `closed` subfolder of the same archive. Two kinds of history,
    one archive, never mixed together in one directory."""
    return os.path.join(root, "memory", "handoffs", "archive", "closed")


def owned_bundles(row, home=None):
    """(proven, guessed) close-bundle dirs for this row.

    PROVEN means the bundle carries a `.project-uuid` marker naming this row.
    GUESSED is anything bundles_lib matched some weaker way. Only PROVEN ones
    are ever archived: moving a bundle is moving a project's history, and a
    resemblance is not a reason to move it. stamp-bundle-owners.py is the tool
    that converts a guess into proof — it stamped 26 bundles on 2026-08-24.
    """
    import bundles_lib
    root = row["root"]
    cdir = os.path.join(root, "memory", "handoffs", "closed")
    proven, guessed = [], []
    if not os.path.isdir(cdir):
        return proven, guessed
    shared = bundles_lib.ambiguous_names(home)
    for name in sorted(os.listdir(cdir)):
        bundle = os.path.join(cdir, name)
        if not os.path.isdir(bundle):
            continue
        owns, evidence = bundles_lib.bundle_owner(bundle, row, shared)
        if not owns:
            continue
        # Proof is the MARKER FILE, checked directly — never a substring of the
        # evidence prose. Caught by test_a_guessed_bundle_is_left_alone: the
        # HEURISTIC message is "slug name match (HEURISTIC — bundle predates
        # .project-uuid)", which contains the marker's own name, so a substring
        # test called every guess proven and archived it. Read the file.
        is_proven = os.path.exists(os.path.join(bundle, bundles_lib.OWNER_MARKER))
        (proven if is_proven else guessed).append((bundle, evidence))
    return proven, guessed


def _stamp_completed(bundle):
    """Mark a bundle's handoff `status: completed`, the same stamp
    /acos-complete writes. Fail-soft and REPORTED: the move is the archiving,
    the stamp is the label on it, and an unwritable label must not abort a
    delete half-way through moving files."""
    notes = []
    for name in sorted(os.listdir(bundle)):
        if not (name.endswith(".yaml") or name.endswith(".md")):
            continue
        if name.endswith(".resume.md"):
            continue          # the eternity protocol's; /acos-complete protects these too
        path = os.path.join(bundle, name)
        try:
            with open(path, "r") as fh:
                text = fh.read()
        except OSError as exc:
            notes.append("%s: unreadable (%s)" % (name, exc.__class__.__name__))
            continue
        if re.search(r"(?m)^status:\s*[\"']?completed", text):
            continue
        new, n = re.subn(r"(?m)^status:\s*.*$", "status: completed", text, count=1)
        if n == 0:
            continue          # no status field: nothing to relabel, and never invent one
        try:
            with open(path, "w") as fh:
                fh.write(new)
        except OSError as exc:
            notes.append("%s: unwritable (%s)" % (name, exc.__class__.__name__))
    return notes


def registry_lib_read_manifest(project_uuid, home=None):
    """The bundle moves a delete recorded, or [] — a missing or unreadable
    manifest means "nothing to put back", never an abort. A restore that
    refused over a manifest would strand the row itself in the trash."""
    path = deleted_bundles_manifest(project_uuid, home)
    try:
        with open(path, "r") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return []
    entries = data.get("bundles") if isinstance(data, dict) else None
    return [e for e in (entries or [])
            if isinstance(e, dict) and e.get("from") and e.get("to")]


def deleted_windows_dir(project_uuid, home=None):
    """Window manifests travel WITH the row, so a restore brings them back."""
    return os.path.join(deleted_dir(home), "windows", project_uuid)


def load_deleted_row(project_uuid, home=None):
    path = deleted_row_path(project_uuid, home)
    if not os.path.exists(path):
        return None
    with open(path, "rb") as fh:
        return json.loads(fh.read().decode("utf-8"))


def list_deleted(home=None):
    d = deleted_dir(home)
    if not os.path.isdir(d):
        return []
    out = []
    for name in sorted(os.listdir(d)):
        if name.endswith(".json"):
            row = load_deleted_row(name[: -len(".json")], home)
            if row:
                out.append(row)
    return out


# --------------------------------------------------------------------------
# liveness — a row with a workspace open on it is never deleted or displaced
# --------------------------------------------------------------------------

def live_workspaces_by_uuid(skip=False):
    """{project_uuid: [workspace line, ...]} from the [key:<uuid>] tag.

    Returns (mapping, error_or_None). A non-None error means the answer is
    UNKNOWN, and delete treats unknown as unsafe — deleting a row out from
    under an open window is exactly the damage this check exists to prevent.

    `skip` is different from an error, and conflating the two was a real bug:
    --no-cmux returned a reason string, _assert_not_live read any reason as
    "could not run", and the flag that was supposed to bypass the check
    refused every delete instead. A deliberate human override yields ({}, None)
    — the human has asserted nothing is open — and the caller says so in the
    receipt so the weaker guarantee is never silent.
    """
    if skip:
        return {}, None
    try:
        out = subprocess.run([CMUX_BIN, "list-workspaces", "--id-format", "both"],
                             capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.SubprocessError) as exc:
        return {}, "cmux could not be run: %s" % exc
    if out.returncode != 0:
        return {}, "cmux list-workspaces failed rc=%d: %s" % (
            out.returncode, out.stderr.strip()[:200])
    by_uuid = {}
    for line in out.stdout.splitlines():
        m = KEY_RE.search(line)
        if m:
            by_uuid.setdefault(m.group(1).lower(), []).append(line.strip())
    return by_uuid, None


def _assert_not_live(row, live, live_err, verb):
    uuid = row["project_uuid"].lower()
    if live_err:
        raise Refused(
            "cannot %s %r (%s): the open-window check could not run — %s.\n"
            "  Refusing rather than guessing: %s-ing a row while a window is "
            "open on it would leave that window bound to a row the book no "
            "longer lists.\n"
            "  Close the window and retry, or pass --no-cmux if you are certain "
            "nothing is open." % (verb, row["name"], row["project_uuid"], live_err, verb))
    open_ws = live.get(uuid) or []
    if open_ws:
        raise Refused(
            "cannot %s %r (%s): %d cmux workspace%s still open on it:\n%s\n"
            "  Close %s first, then retry."
            % (verb, row["name"], row["project_uuid"], len(open_ws),
               "" if len(open_ws) == 1 else "s",
               "\n".join("    " + w for w in open_ws),
               "it" if len(open_ws) == 1 else "them"))


# --------------------------------------------------------------------------
# confirmation
# --------------------------------------------------------------------------

def confirm_name(expected, supplied, what, home_note=""):
    """Active confirmation: the exact NAME, typed. Never y/Enter.

    Interactive terminal -> read from the tty (mechanical guard).
    Otherwise -> require --confirm-name (procedural guard; see the module
    docstring). Either way the receipt records which route was used.
    """
    if supplied is None:
        if not sys.stdin.isatty():
            raise Refused(
                "refusing %s without confirmation.\n"
                "  Type the project's name to confirm: --confirm-name %r\n"
                "  A bare yes is not accepted. This must be the name the USER "
                "typed, never one copied off the screen by an assistant.%s"
                % (what, expected, home_note))
        try:
            supplied = input("Type the project's name to confirm %s (%r): " % (what, expected))
        except EOFError:
            raise Refused("refusing %s: no confirmation given." % what)
        route = "typed at an interactive terminal"
    else:
        route = "supplied as --confirm-name (procedural guard, not mechanical)"

    if supplied.strip() != expected:
        raise Refused(
            "refusing %s: confirmation %r does not match the project name %r.\n"
            "  The name must match exactly, character for character."
            % (what, supplied.strip(), expected))
    return route


def confirm_word(word, supplied, what):
    """Same idea, for a verb with no project name — `compact`."""
    if supplied is None:
        if not sys.stdin.isatty():
            raise Refused("refusing %s without confirmation. Pass --confirm %s" % (what, word))
        try:
            supplied = input("Type %r in full to confirm %s: " % (word, what))
        except EOFError:
            raise Refused("refusing %s: no confirmation given." % what)
        route = "typed at an interactive terminal"
    else:
        route = "supplied as --confirm (procedural guard, not mechanical)"
    if supplied.strip() != word:
        raise Refused("refusing %s: expected %r, got %r." % (what, word, supplied.strip()))
    return route


# --------------------------------------------------------------------------
# lookup
# --------------------------------------------------------------------------

def row_by_ordinal(n, home=None):
    holders = ordinal_lib.live_holders(home).get(n) or []
    if not holders:
        raise Refused(
            "no row holds number %d.\n"
            "  Run `manage-ordinals.py status` to see what is in use, what is "
            "retired, and what is free." % n)
    if len(holders) > 1:
        raise Refused(
            "ORDINAL-CLASH: %d rows hold number %d:\n%s\n"
            "  Refusing to guess which one you meant. Give all but one a "
            "different number with `renumber ... --uuid <project_uuid>`."
            % (len(holders), n,
               "\n".join("    %r  %s  %s" % (r["name"], r["project_uuid"], r["root"])
                         for r in holders)))
    return holders[0]


def resolve_target(ordinal=None, uuid=None, home=None):
    """A row named either by its number or, when a clash blocks that, by uuid."""
    if uuid:
        row = registry_lib.load_row(uuid, home)
        if row is None:
            raise Refused("no registry row for project_uuid %s.\n"
                          "  (A deleted row lives in registry.d/deleted/ — see "
                          "`status --deleted`.)" % uuid)
        return row
    if ordinal is None:
        raise Refused("name the row by its number, or by --uuid <project_uuid>.")
    return row_by_ordinal(ordinal, home)


# --------------------------------------------------------------------------
# verbs
# --------------------------------------------------------------------------

def v_status(args, home=None):
    holders = ordinal_lib.live_holders(home)
    retired = ordinal_lib.retired_ordinals(home)
    deleted = list_deleted(home)
    high = ordinal_lib.max_ever_issued(home)

    if args.json:
        print(json.dumps({
            "max_ever_issued": high,
            "next_auto": ordinal_lib.next_ordinal(home),
            "in_use": {str(n): [r["project_uuid"] for r in rs] for n, rs in sorted(holders.items())},
            "retired": {str(n): {"at": rec["at"], "name": rec["name"],
                                 "project_uuid": rec["project_uuid"]}
                        for n, rec in sorted(retired.items())},
            "deleted": [{"project_uuid": r["project_uuid"], "name": r["name"],
                         "pick_ordinal": r.get("pick_ordinal")} for r in deleted],
            "clashes": {str(n): len(rs) for n, rs in holders.items() if len(rs) > 1},
        }, indent=2))
        return 0

    print("ORDINALS — highest ever issued: %d · next new project takes: %d"
          % (high, ordinal_lib.next_ordinal(home)))
    print()
    print("in use (%d):" % sum(len(v) for v in holders.values()))
    for n, rows in sorted(holders.items()):
        for r in rows:
            flag = "  <-- CLASH" if len(rows) > 1 else ""
            print("  %4d  %-30s %-11s %s%s"
                  % (n, r["name"][:30], r["status"], r["project_uuid"], flag))

    if retired:
        print("\nretired (%d) — HISTORY, not a lock (rule reversed 2026-08-24). A "
              "number here is free to be reissued unless a row still holds it:" % len(retired))
        for n, rec in sorted(retired.items()):
            print("  %4d  last held by %-24s  retired %s  (%s)"
                  % (n, rec["name"][:24], rec["at"][:19], rec["verb"]))

    if deleted:
        print("\ndeleted (%d) — recoverable with `restore <uuid>`, "
              "unlinked only by `purge <uuid>`:" % len(deleted))
        for r in deleted:
            print("  %4s  %-30s %s" % (r.get("pick_ordinal") or "—",
                                       r["name"][:30], r["project_uuid"]))

    used = set(holders) | set(retired)
    gaps = [n for n in range(1, high + 1) if n not in used]
    if gaps:
        print("\nfree below the high-water mark (%d): %s" % (len(gaps), gaps))
        print("  These were never issued. `renumber` may take one with no warning.")
    return 0


def v_delete(args, home=None):
    row = resolve_target(args.ordinal, args.uuid, home)
    live, live_err = live_workspaces_by_uuid(args.no_cmux)
    _assert_not_live(row, live, live_err, "delete")

    route = confirm_name(row["name"], args.confirm_name, "deleting %r" % row["name"])
    uuid = row["project_uuid"]
    ordinal = row.get("pick_ordinal")

    proven, guessed = owned_bundles(row, home)
    adir = archived_closed_dir(row["root"])

    if not args.apply:
        print("DRY RUN — nothing moved. Would delete:")
        print("  %r (%s), number %s" % (row["name"], uuid, ordinal))
        print("  row      -> %s" % deleted_row_path(uuid, home))
        wd = windows_lib.windows_dir(uuid, home)
        print("  windows  -> %s%s" % (deleted_windows_dir(uuid, home),
                                      "" if os.path.isdir(wd) else "   (none to move)"))
        print("  close bundles -> %s" % adir)
        if proven:
            for bundle, _ev in proven:
                print("      %s" % os.path.basename(bundle))
        else:
            print("      (none owned by this row)")
        if guessed:
            print("  NOT MOVED — ownership is a guess, not the %s marker:"
                  % __import__("bundles_lib").OWNER_MARKER)
            for bundle, ev in guessed:
                print("      %-46s [%s]" % (os.path.basename(bundle)[:46], ev[:60]))
            print("      Run stamp-bundle-owners.py to settle these, then delete.")
        print("  knowledge store: LEFT IN PLACE (facts survive delete AND purge).")
        print("  number %s becomes FREE immediately (Zee, 2026-08-24). `restore` takes it "
              "back if still free, otherwise the lowest free number." % ordinal)
        print("\nRe-run with --apply to move it.")
        return 0

    os.makedirs(deleted_dir(home), exist_ok=True)
    src = registry_lib.row_path(uuid, home)
    dst = deleted_row_path(uuid, home)
    if os.path.exists(dst):
        raise Refused("a deleted row already exists at %s — refusing to overwrite "
                      "it. Purge or restore that one first." % dst)
    os.replace(src, dst)  # MOVE, never unlink

    moved_windows = None
    wsrc = windows_lib.windows_dir(uuid, home)
    if os.path.isdir(wsrc):
        wdst = deleted_windows_dir(uuid, home)
        os.makedirs(os.path.dirname(wdst), exist_ok=True)
        shutil.move(wsrc, wdst)
        moved_windows = wdst

    # Archive this row's close bundles — Zee's "treat it as /acos-complete".
    # Order matters: the row file is already in the trash, so a failure here
    # leaves a deleted row whose bundles are partly moved. The manifest is
    # written after EACH move, so restore can always undo exactly what landed.
    moved_bundles, bundle_notes = [], []
    if proven:
        os.makedirs(adir, exist_ok=True)
    for bundle, _ev in proven:
        # NOT `dst` — that name already holds the ROW's trash path, and
        # shadowing it made the receipt print a bundle path on the "row moved
        # to" line. Caught by reading a real receipt on 2026-08-24.
        bdst = os.path.join(adir, os.path.basename(bundle))
        if os.path.exists(bdst):
            bundle_notes.append("%s: already in the archive — LEFT IN PLACE"
                                % os.path.basename(bundle))
            continue
        bundle_notes.extend(_stamp_completed(bundle))
        shutil.move(bundle, bdst)
        moved_bundles.append({"from": bundle, "to": bdst})
        registry_lib.atomic_write_json(
            deleted_bundles_manifest(uuid, home), {"bundles": moved_bundles})

    if ordinal is not None:
        ordinal_lib.append_event("retire", ordinal, uuid, row["name"], home, reason="delete")
    registry_lib.audit_append(
        {"event": "row_delete", "project_uuid": uuid, "name": row["name"],
         "pick_ordinal": ordinal, "confirmation": route,
         "bundles_archived": len(moved_bundles)}, home)

    kdir = os.path.join(registry_lib._home(home), ".acos", "knowledge", uuid)
    print("DELETED %r (%s)" % (row["name"], uuid))
    print("  confirmation: %s" % route)
    if args.no_cmux:
        print("  open-window check: SKIPPED at your instruction (--no-cmux). "
              "Nothing verified that no window was open on this row.")
    print("  row moved to     : %s" % dst)
    print("  windows moved to : %s" % (moved_windows or "(none existed)"))
    if moved_bundles:
        print("  close bundles    : %d archived to %s" % (len(moved_bundles), adir))
        for b in moved_bundles:
            print("      %s" % os.path.basename(b["to"]))
        print("                     Each handoff inside is stamped `status: completed`, "
              "the same stamp /acos-complete writes. A `.resume.md` sibling travels "
              "with its own bundle but is never relabelled — /acos-complete protects "
              "those by name and so does this.")
    else:
        print("  close bundles    : none owned by this row were archived")
    if guessed:
        print("  NOT ARCHIVED     : %d bundle(s) whose ownership is a guess, not the "
              "%s marker. Moving a project's history on a resemblance is not something "
              "this does." % (len(guessed), __import__("bundles_lib").OWNER_MARKER))
        for bundle, ev in guessed:
            print("      %-46s [%s]" % (os.path.basename(bundle)[:46], ev[:60]))
        print("                     Run stamp-bundle-owners.py to settle them.")
    for note in bundle_notes:
        print("  NOTE             : %s" % note)
    print("  knowledge store  : LEFT IN PLACE at %s" % kdir)
    print("                     Facts survive delete AND purge (Zee, 2026-08-24). "
          "The store is addressed by project_uuid, independently of the row.")
    print("  number %s is FREE now — a new project may take it. `restore` takes it back "
          "if it is still free, otherwise the lowest free number."
          % (ordinal if ordinal is not None else "(none)"))
    print("  Nothing was unlinked. `restore %s` brings back the row, its windows and "
          "its archived bundles; only `purge` removes the row for good." % uuid)
    return 0


def v_restore(args, home=None):
    uuid = args.uuid
    row = load_deleted_row(uuid, home)
    if row is None:
        raise Refused("no deleted row for %s. See `status --deleted`." % uuid)
    if registry_lib.load_row(uuid, home) is not None:
        raise Refused("a LIVE row already exists for %s — nothing to restore." % uuid)

    # Zee's ruling 2026-08-24: "restore brings back with old number if free but
    # if not free bring back with a number that is available." So a taken
    # original is NOT a refusal any more — delete frees the number immediately,
    # which makes losing it the normal case rather than an error. It still never
    # DISPLACES the holder; the returning row takes the lowest free number and
    # the receipt says which, and what took the old one.
    ordinal = row.get("pick_ordinal")
    original = ordinal
    taken_by = []
    if ordinal is not None:
        taken_by = ordinal_lib.live_holders(home).get(ordinal) or []
        if taken_by:
            ordinal = ordinal_lib.next_ordinal(home)
    elif ordinal is None:
        ordinal = ordinal_lib.next_ordinal(home)

    def _why():
        if not taken_by and original is not None:
            return "its original number %d, still free" % original
        if original is None:
            return "number %d (it held none when deleted)" % ordinal
        return ("number %d — its original %d is now held by %s"
                % (ordinal, original,
                   ", ".join("%r" % h["name"] for h in taken_by)))

    if not args.apply:
        print("DRY RUN — nothing moved. Would restore:")
        print("  %r (%s) with %s" % (row["name"], uuid, _why()))
        man = registry_lib_read_manifest(uuid, home)
        if man:
            print("  and move %d archived close bundle(s) back to memory/handoffs/closed/"
                  % len(man))
        print("\nRe-run with --apply.")
        return 0

    os.replace(deleted_row_path(uuid, home), registry_lib.row_path(uuid, home))
    wsrc = deleted_windows_dir(uuid, home)
    restored_windows = None
    if os.path.isdir(wsrc):
        wdst = windows_lib.windows_dir(uuid, home)
        os.makedirs(os.path.dirname(wdst), exist_ok=True)
        shutil.move(wsrc, wdst)
        restored_windows = wdst

    # The row file was written with its ORIGINAL number. If that number went to
    # someone else, move the returning row onto the free one — after the file is
    # back in place, so a failure leaves a restored row rather than a lost one.
    if ordinal != original:
        registry_lib.set_pick_ordinal(uuid, ordinal, home)

    restored_bundles, bundle_notes = [], []
    for entry in registry_lib_read_manifest(uuid, home):
        src, dst = entry["to"], entry["from"]
        if not os.path.isdir(src):
            bundle_notes.append("%s: not in the archive any more — LEFT"
                                % os.path.basename(src))
            continue
        if os.path.exists(dst):
            bundle_notes.append("%s: already back in closed/ — LEFT"
                                % os.path.basename(dst))
            continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.move(src, dst)
        restored_bundles.append(dst)
    try:
        os.unlink(deleted_bundles_manifest(uuid, home))
    except OSError:
        pass

    ordinal_lib.append_event("restore", ordinal, uuid, row["name"], home,
                             from_ordinal=original if ordinal != original else None)
    registry_lib.audit_append(
        {"event": "row_restore", "project_uuid": uuid, "name": row["name"],
         "pick_ordinal": ordinal, "original_ordinal": original}, home)

    print("RESTORED %r (%s)" % (row["name"], uuid))
    print("  number: %s" % _why())
    print("  windows restored : %s" % (restored_windows or "(none were stored)"))
    if restored_bundles:
        print("  close bundles    : %d moved back to memory/handoffs/closed/"
              % len(restored_bundles))
        for b in restored_bundles:
            print("      %s" % os.path.basename(b))
        print("                     Their `status: completed` stamp is NOT reverted — "
              "the close really did happen, and archiving was the only thing undone.")
    for note in bundle_notes:
        print("  NOTE             : %s" % note)
    return 0


def v_purge(args, home=None):
    uuid = args.uuid
    row = load_deleted_row(uuid, home)
    if row is None:
        raise Refused(
            "no deleted row for %s.\n"
            "  `purge` only ever operates on rows already in registry.d/deleted/. "
            "A live row must be `delete`d first — that is deliberate, so an "
            "unlink always takes two separate human acts." % uuid)

    route = confirm_name(
        row["name"], args.confirm_name, "PURGING %r" % row["name"],
        home_note="\n  This is IRREVERSIBLE. The row file is unlinked. "
                  "`delete` is the recoverable verb; this one is not.")

    man = registry_lib_read_manifest(uuid, home)
    kdir = os.path.join(registry_lib._home(home), ".acos", "knowledge", uuid)
    if not args.apply:
        print("DRY RUN — nothing unlinked. Would PERMANENTLY remove:")
        print("  %s" % deleted_row_path(uuid, home))
        if os.path.isdir(deleted_windows_dir(uuid, home)):
            print("  %s" % deleted_windows_dir(uuid, home))
        print("  This cannot be undone.")
        print("  KEPT — knowledge facts at %s" % kdir)
        print("         Zee's ruling 2026-08-24: purge does NOT erase knowledge facts. "
              "Nothing else on this machine backs them up.")
        if man:
            print("  KEPT — %d archived close bundle(s) stay in memory/handoffs/archive/"
                  "closed/. Purging the row does not erase the project's history; it "
                  "only stops the row from coming back." % len(man))
        print("  Number %s was already freed by `delete`, so purging changes nothing "
              "about it." % row.get("pick_ordinal"))
        print("\nRe-run with --apply.")
        return 0

    os.unlink(deleted_row_path(uuid, home))
    wdir = deleted_windows_dir(uuid, home)
    if os.path.isdir(wdir):
        shutil.rmtree(wdir)
    registry_lib.audit_append(
        {"event": "row_purge", "project_uuid": uuid, "name": row["name"],
         "pick_ordinal": row.get("pick_ordinal"), "confirmation": route}, home)

    print("PURGED %r (%s) — unlinked, not recoverable." % (row["name"], uuid))
    print("  confirmation: %s" % route)
    print("  KEPT — knowledge facts at %s (Zee's ruling 2026-08-24: purge never "
          "erases them)." % kdir)
    if man:
        print("  KEPT — %d archived close bundle(s) remain in memory/handoffs/archive/"
              "closed/, with the manifest naming where each came from." % len(man))
    print("  the ledger keeps every event for number %s. It is append-only, so what "
          "that number used to mean is still answerable." % row.get("pick_ordinal"))
    return 0


def v_swap(args, home=None):
    a = row_by_ordinal(args.a, home)
    b = row_by_ordinal(args.b, home)
    if a["project_uuid"] == b["project_uuid"]:
        raise Refused("both numbers name the same row (%r). Nothing to swap." % a["name"])
    for r, n in ((a, args.a), (b, args.b)):
        if load_deleted_row(r["project_uuid"], home) is not None:
            raise Refused("row %d (%r) is deleted — restore it before swapping." % (n, r["name"]))

    if not args.apply:
        print("DRY RUN — nothing written. Would swap:")
        print("  %4d  %r  ->  %d" % (args.a, a["name"], args.b))
        print("  %4d  %r  ->  %d" % (args.b, b["name"], args.a))
        print("\nRe-run with --apply.")
        return 0

    # No lock exists (registry_lib.py:10-13 documents none, and none that
    # survives SIGKILL), so this cannot be atomic. Write both, then RE-READ
    # both and verify. A partial write is reported LOUDLY and named as an
    # ORDINAL-CLASH — never retried silently, because a silent retry over a
    # half-applied swap is how one number ends up on two rows.
    registry_lib.set_pick_ordinal(a["project_uuid"], args.b, home)
    registry_lib.set_pick_ordinal(b["project_uuid"], args.a, home)

    a2 = registry_lib.load_row(a["project_uuid"], home)
    b2 = registry_lib.load_row(b["project_uuid"], home)
    ok = a2["pick_ordinal"] == args.b and b2["pick_ordinal"] == args.a
    if not ok:
        print("PARTIAL WRITE — the swap did not fully land.", file=sys.stderr)
        print("  %r now holds %s (wanted %d)" % (a2["name"], a2["pick_ordinal"], args.b),
              file=sys.stderr)
        print("  %r now holds %s (wanted %d)" % (b2["name"], b2["pick_ordinal"], args.a),
              file=sys.stderr)
        print("  Diagnose with `conflict-scan.py` — expect ORDINAL-CLASH.", file=sys.stderr)
        print("  NOT retrying. Fix it deliberately with `renumber --uuid ...`.",
              file=sys.stderr)
        registry_lib.audit_append(
            {"event": "swap_partial", "a": a["project_uuid"], "b": b["project_uuid"],
             "a_got": a2["pick_ordinal"], "b_got": b2["pick_ordinal"]}, home)
        return 1

    ordinal_lib.append_event(
        "swap", args.b, a["project_uuid"], a["name"], home, from_ordinal=args.a,
        counterpart={"ordinal": args.a, "project_uuid": b["project_uuid"],
                     "name": b["name"], "from_ordinal": args.b})
    print("SWAPPED — verified by re-reading both rows.")
    print("  %r is now %d (was %d)" % (a["name"], args.b, args.a))
    print("  %r is now %d (was %d)" % (b["name"], args.a, args.b))
    print("  Neither number is retired: both are still held.")
    return 0


def v_renumber(args, home=None):
    m = args.to_ordinal
    if m <= 0:
        raise Refused(
            "refusing number %d. Numbers start at 1 — 0 is reserved for "
            "'new project' (acos-safe-close/SKILL.md:235-241), and a negative "
            "number is not a number a human can type at the menu." % m)
    row = resolve_target(args.ordinal, args.uuid, home)
    n = row.get("pick_ordinal")
    if n == m:
        raise Refused("%r already holds %d. Nothing to do." % (row["name"], m))

    holders = ordinal_lib.live_holders(home).get(m) or []
    if holders:
        raise Refused(
            "cannot renumber to %d: it is held by %s.\n"
            "  Refusing to displace a live row silently. Use `swap %s %d` to "
            "exchange them, or pick a free number — `status` lists what is free."
            % (m, ", ".join("%r (%s)" % (h["name"], h["project_uuid"]) for h in holders),
               n if n is not None else "<this row's number>", m))

    retired = ordinal_lib.retired_ordinals(home)
    reuse_note = None
    if m in retired:
        rec = retired[m]
        reuse_note = ("%d previously held %r (%s) and was retired %s by a %s"
                      % (m, rec["name"], rec["project_uuid"], rec["at"][:19], rec["verb"]))
        # REVERSED 2026-08-24 — Zee: "A freed number can be assigned, change
        # that rule." Reuse used to REFUSE here unless --reuse-retired was
        # passed. Auto-assignment now fills the lowest free number by itself
        # (ordinal_lib.next_ordinal), so a hard gate on the manual verb would
        # forbid by hand exactly what the machine does unasked.
        #
        # The WARNING stays, because the fact is still worth knowing: anything
        # that still refers to m — a note, a screenshot, your memory — will now
        # point at a different project. Telling is not the same as blocking.
        print("NOTE — number %d was previously held: %s" % (m, reuse_note))
        print("       Anything still referring to %d now points at this row instead." % m)

    if not args.apply:
        print("DRY RUN — nothing written. Would renumber:")
        print("  %r: %s -> %d" % (row["name"], n, m))
        if reuse_note:
            print("  REUSING A RETIRED NUMBER: %s" % reuse_note)
        if n is not None:
            print("  %d would be RETIRED (vacated, not freed)." % n)
        # NOT a high-water statement any more: a new row takes the LOWEST free
        # number, so moving one row up does not decide what the next row gets.
        _after = set(ordinal_lib.held_ordinals(home))
        if n is not None:
            _after.discard(n)
        _after.add(m)
        _next = 1
        while _next in _after:
            _next += 1
        print("  %d would then be free, and the next new project would take %d."
              % (n, _next) if n is not None else
              "  The next new project would take %d." % _next)
        print("\nRe-run with --apply.")
        return 0

    registry_lib.set_pick_ordinal(row["project_uuid"], m, home)
    ordinal_lib.append_event(
        "renumber", m, row["project_uuid"], row["name"], home,
        from_ordinal=n, reused_retired=bool(reuse_note) or None)

    print("RENUMBERED %r: %s -> %d" % (row["name"], n, m))
    if reuse_note:
        print("  reused a retired number: %s" % reuse_note)
    if n is not None:
        print("  %d is now RETIRED — vacated, not freed. It will never be "
              "handed out automatically." % n)
    print("  next new project takes %d." % ordinal_lib.next_ordinal(home))
    return 0


def v_compact(args, home=None):
    holders = ordinal_lib.live_holders(home)
    clashes = {n: rs for n, rs in holders.items() if len(rs) > 1}
    if clashes:
        raise Refused(
            "refusing to compact while %d number%s held by more than one row.\n"
            "  Compacting over a clash would silently pick a winner. Resolve "
            "them first — `conflict-scan.py` names them."
            % (len(clashes), " is" if len(clashes) == 1 else "s are"))

    ordered = [rs[0] for _, rs in sorted(holders.items())]
    moves = [(r, i + 1) for i, r in enumerate(ordered) if r["pick_ordinal"] != i + 1]

    if not moves:
        print("Nothing to compact — numbers already run 1..%d with no gaps."
              % len(ordered))
        return 0

    print("COMPACT would renumber %d of %d rows:" % (len(moves), len(ordered)))
    for r, new in moves:
        print("  %4d -> %-4d  %s" % (r["pick_ordinal"], new, r["name"]))

    route = confirm_word("compact", args.confirm, "compacting %d row(s)" % len(moves))

    if not args.apply:
        print("\nDRY RUN — nothing written. Re-run with --apply.")
        return 0

    for r, new in moves:
        registry_lib.set_pick_ordinal(r["project_uuid"], new, home)
        ordinal_lib.append_event("renumber", new, r["project_uuid"], r["name"], home,
                                 from_ordinal=r["pick_ordinal"], via="compact")
    registry_lib.audit_append(
        {"event": "compact", "moved": len(moves), "confirmation": route}, home)

    print("\nCOMPACTED %d row(s). Numbers now run 1..%d." % (len(moves), len(ordered)))
    print("  confirmation: %s" % route)
    print("  EVERY NUMBER YOU HAD MEMORISED FROM BEFORE IS NOW WRONG.")
    print("  Precedent and known cost: this is tmux's `renumber-windows`, which "
          "ships OFF by default. In tmux issue #3214 renumbering silently "
          "cleared a stored reference to a window; the maintainer replied "
          "\"Yes, this is not ideal...\" and fixed it. Assume the same class of "
          "breakage here — anything holding an old number now points elsewhere.")
    return 0


# --------------------------------------------------------------------------

def build_parser():
    ap = argparse.ArgumentParser(
        description=__doc__.splitlines()[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Every verb here is HUMAN-INITIATED ONLY. Never run one on your "
               "own initiative.")
    ap.add_argument("--home", default=None, help="override ~ (tests only)")
    sub = ap.add_subparsers(dest="verb", required=True)

    p = sub.add_parser("status", help="what every number is; what is retired; what is free")
    p.add_argument("--json", action="store_true")
    p.add_argument("--deleted", action="store_true", help="(included in the default output)")
    p.set_defaults(fn=v_status)

    p = sub.add_parser("delete", help="soft delete — moves the row, unlinks nothing")
    p.add_argument("ordinal", type=int, nargs="?")
    p.add_argument("--uuid", default=None, help="name the row by uuid (use when numbers clash)")
    p.add_argument("--confirm-name", default=None, help="the project's exact name")
    p.add_argument("--apply", action="store_true")
    p.add_argument("--no-cmux", action="store_true", help="skip the open-window check")
    p.set_defaults(fn=v_delete)

    p = sub.add_parser("restore", help="bring a deleted row back with its original number")
    p.add_argument("uuid")
    p.add_argument("--apply", action="store_true")
    p.set_defaults(fn=v_restore)

    p = sub.add_parser("purge", help="true unlink, from deleted/ only. IRREVERSIBLE.")
    p.add_argument("uuid")
    p.add_argument("--confirm-name", default=None, help="the project's exact name, again")
    p.add_argument("--apply", action="store_true")
    p.set_defaults(fn=v_purge)

    p = sub.add_parser("swap", help="two rows exchange numbers")
    p.add_argument("a", type=int)
    p.add_argument("b", type=int)
    p.add_argument("--apply", action="store_true")
    p.set_defaults(fn=v_swap)

    p = sub.add_parser("renumber", help="one row moves to a different number")
    p.add_argument("ordinal", type=int, nargs="?")
    p.add_argument("to_ordinal", type=int, metavar="TO")
    p.add_argument("--uuid", default=None)
    p.add_argument("--reuse-retired", action="store_true",
                   help="accepted and ignored — reuse needs no flag since 2026-08-24")
    p.add_argument("--apply", action="store_true")
    p.set_defaults(fn=v_renumber)

    p = sub.add_parser("compact", help="close every gap, 1..N. LOUD, opt-in, never automatic.")
    p.add_argument("--confirm", default=None, help="the word `compact`, in full")
    p.add_argument("--apply", action="store_true")
    p.set_defaults(fn=v_compact)
    return ap


def _normalise(argv):
    """Accept the two orderings a human actually types.

    `--home` is a top-level option, so argparse only sees it BEFORE the verb.
    Written after the verb — `delete 3 --apply --home /tmp/x`, which is the
    natural way to type it and the way every other script here accepts it —
    argparse would reject the whole command. Hoist it to the front instead of
    failing on a difference that carries no meaning.

    Same for `renumber 7 to 9`: that is how the brief writes it and how a
    human says it, so it must work alongside `renumber 7 9`.
    """
    argv = list(argv)
    hoisted = []
    i = 0
    rest = []
    while i < len(argv):
        if argv[i] == "--home" and i + 1 < len(argv):
            hoisted = ["--home", argv[i + 1]]
            i += 2
            continue
        if argv[i].startswith("--home="):
            hoisted = [argv[i]]
            i += 1
            continue
        rest.append(argv[i])
        i += 1
    argv = hoisted + rest
    v = len(hoisted)
    if len(argv) >= v + 4 and argv[v] == "renumber" and argv[v + 2] == "to":
        argv = argv[: v + 2] + [argv[v + 3]] + argv[v + 4:]
    return argv


def main(argv=None):
    argv = _normalise(sys.argv[1:] if argv is None else argv)
    args = build_parser().parse_args(argv)
    try:
        return args.fn(args, args.home)
    except Refused as exc:
        print("REFUSED — %s" % exc, file=sys.stderr)
        return 1
    except (OSError, ValueError, KeyError) as exc:
        print("could not run: %s: %s" % (type(exc).__name__, exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
