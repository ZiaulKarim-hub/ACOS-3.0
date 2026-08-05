#!/bin/bash
# adopt-project.sh — ADOPT-IN-PLACE, SPINE 2 (ACOS Resurrection Protocol).
#
# Interface:
#   adopt-project.sh --project <uuid> [--dry-run]
#                    [--additional-window] [--label <text>]
# Env overrides (tests only):
#   ACOS_REGISTRY_HOME        registry home override (never the real ~ in tests)
#   RESURRECTION_SKIP_CMUX=1  no cmux calls at all (sandbox: decision print only)
#
# WHY THIS EXISTS (user decision 2026-07-26): a resurrect pick must land in the
# tab the user typed in — that tab BECOMES the picked project. launch-project.sh
# (SPINE 1) only focuses an already-open project or creates a new tab; neither
# turns the CURRENT tab into the picked project, so a pick used to strand the
# user in a tab they were not looking at.
#
# HARD PHYSICAL LIMIT, stated once so no caller re-litigates it: a cmux
# workspace's folder CANNOT be changed after creation (`--cwd` exists only on
# `workspace create`; there is no re-point verb), and this Claude session's own
# cwd was fixed at launch. So adoption re-binds IDENTITY (sidebar name +
# [key:<uuid>] tag + registry row), never the tab's shell folder. When the
# picked root differs from the tab's folder the receipt says so LOUDLY and names
# the root all file work must use. That is a reported fact, not a silent fudge.
#
# The three gates, in order (each REFUSES rather than guessing):
#   1. ALREADY-OPEN: if the picked project is live in some OTHER workspace,
#      refuse with exit 4 — the caller jumps there instead. The guard STAYS the
#      default (D11), but the refusal now NAMES the second option instead of
#      pretending there is only one: --additional-window opens a SECOND window
#      on the same project. Zee asked for the choice, not the removal of the
#      guard, so the choice is his and this script never takes it unasked.
#   2. OUTGOING-NOT-CLOSED: the project currently bound to this tab is released
#      by adoption. If it was never closed through the protocol (last_close is
#      null) we refuse with exit 3 rather than orphan unsaved reentry state.
#      A properly-closed outgoing row is flipped active -> parked on release
#      (undoing enroll-project.sh's revive-on-work, which re-actives a row the
#      moment any session starts in its folder).
#   3. TOMBSTONED / MISSING / BROKEN root: refuse, exit 1.
#
# Registry writes go through registry_lib.py ONLY. Nothing here deletes a row.
# The picked row's `root` is NEVER rewritten to the tab's cwd — that would
# silently move a project to another folder.

set -u

AP_PROJECT=""
AP_DRY=0
AP_EXTRA=0
AP_LABEL=""
while [ $# -gt 0 ]; do
  case "$1" in
    --project) AP_PROJECT="${2:-}"; shift 2 ;;
    --dry-run) AP_DRY=1; shift ;;
    # D11: the one-project-one-tab guard STAYS the default. This flag is the
    # answer to the question the skill asks when a pick is already open —
    # "focus that window, or open another?" — and is never taken on its own.
    --additional-window) AP_EXTRA=1; shift ;;
    # D12: window names derive from the project name — "OKOA works *label*".
    # The stem is always the project, so the row identity is never in doubt.
    --label) AP_LABEL="${2:-}"; shift 2 ;;
    *) echo "REFUSED — unknown argument: $1" >&2; exit 2 ;;
  esac
done
export AP_PROJECT AP_DRY AP_EXTRA AP_LABEL
AP_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export AP_LIB_DIR

# exec: the python exit status is the script's; nothing runs after the heredoc.
exec /usr/bin/python3 - <<'PYEOF'
"""adopt-project.sh embedded body — adopt-in-place (SPINE 2).

Constraints (identical to launch-project.sh):
  * System /usr/bin/python3 is 3.9.6, stdlib only, NO yaml module.
  * Registry access ONLY via registry_lib.py (same directory).
  * cmux via the ABSOLUTE binary; workspace identity is UUIDs only (refs like
    workspace:8 RENUMBER across lifecycle — never persisted, never trusted).
  * CMUX_WORKSPACE_ID is inherited env and can be SET-BUT-DEAD (cmux restarted
    under a live process). It is trusted only after it appears in a LIVE
    workspace.list.
  * Reentry notes are re-resolved AT ADOPT TIME under
    <root>/memory/handoffs/closed/ — never a cached filename — and are
    FILTERED TO THIS PROJECT, then merged (MW-A, user brief 2026-08-04).
    The old newest-by-mtime scan was folder-scoped, which broke two ways:
    (a) 19 projects share this repo's root, so the newest note in the folder
    routinely belonged to a DIFFERENT project (observed live: adopting
    'Resurrection Protocol' served the 'OKOA Works' note); (b) when several
    windows closed one project, only the last note written was ever surfaced
    and the rest went silently unread. The row's recorded reentry_path is a
    loud, last-resort fallback.
"""
import json
import os
import re
import subprocess
import sys

CMUX_BIN = "/Applications/cmux.app/Contents/Resources/bin/cmux"

PROJECT = os.environ.get("AP_PROJECT", "")
DRY = os.environ.get("AP_DRY", "0") == "1"
EXTRA_WINDOW = os.environ.get("AP_EXTRA", "0") == "1"
LABEL = (os.environ.get("AP_LABEL") or "").strip()
LIB_DIR = os.environ.get("AP_LIB_DIR", "")
REG_HOME = os.environ.get("ACOS_REGISTRY_HOME") or None
SKIP_CMUX = os.environ.get("RESURRECTION_SKIP_CMUX") == "1"

sys.path.insert(0, LIB_DIR)
import registry_lib
import bundles_lib

KEY_RE = re.compile(r"\[key:([0-9a-fA-F-]{36})\]")


def refuse(reason, code=1):
    print("REFUSED — %s" % reason)
    sys.exit(code)


def cmux(args, timeout=15):
    """Run the absolute cmux binary in LIST FORM (never a shell string)."""
    try:
        return subprocess.run([CMUX_BIN] + args, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        refuse("cmux call failed: %s (%s: %s)" % (" ".join(args[:2]), type(exc).__name__, exc))


def list_workspaces():
    """rpc workspace.list — PROVEN verb on 0.64.19. Loud on unparseable output."""
    out = cmux(["rpc", "workspace.list"])
    if out.returncode != 0:
        refuse("rpc workspace.list rc=%d stderr=%s" % (out.returncode, out.stderr.strip()[:300]))
    try:
        payload = json.loads(out.stdout)
    except (json.JSONDecodeError, ValueError):
        refuse("rpc workspace.list returned unparseable JSON: %r" % out.stdout[:200])
    return payload.get("workspaces", [])


def ws_key_tag(ws):
    """The [key:<uuid>] binding on a workspace description, lowercased, or None."""
    m = KEY_RE.search(ws.get("description") or "")
    return m.group(1).lower() if m else None


def ws_custom_title(ws):
    """The HUMAN-set sidebar name only. The dynamic `title` is banned from
    lookup — programs (Claude included) rewrite it live."""
    ct = (ws.get("custom_title") or "").strip()
    return ct if (ws.get("has_custom_title") and ct) else None


def ws_cwd_key(ws):
    """realpath-casefold of a workspace's reported folder, or None."""
    cd = ws.get("current_directory")
    if not cd:
        return None
    try:
        return os.path.realpath(cd).casefold()
    except OSError:
        return None


def binds_row(ws, row):
    """Does `ws` currently claim `row`? Strongest evidence first:
      * the [key:<uuid>] tag (explicit binding — folder-independent BY DESIGN,
        which is exactly what makes an adopted tab honest);
      * for sidebar-named rows: human-set custom_title == workspace_name,
        cwd-guarded (a same-named tab in another folder is NOT this row).
    Folder-only claims are deliberately NOT used here: after an adoption the
    tab's folder no longer identifies its project, so a cwd match would hand
    the tab back to whatever row owns that folder.
    """
    tag = ws_key_tag(ws)
    if tag:
        return tag == row["project_uuid"].lower()
    wn = row["workspace_name"]
    ct = ws_custom_title(ws)
    if wn and ct and wn.casefold() == ct.casefold():
        ck = ws_cwd_key(ws)
        return ck is None or ck == row["root_casefold"]
    return False


def outgoing_row(ws):
    """The registry row this tab currently represents, or None.

    Resolution order mirrors enroll-project.sh so adoption releases exactly the
    row a fresh SessionStart in this tab would have re-enrolled:
      1. the [key:<uuid>] tag (any root — an adopted tab is tagged, not rooted);
      2. (folder, sidebar name) named row;
      3. the folder-level row for this tab's cwd.
    Tombstoned rows resolve to None — they are already out of the book.
    """
    tag = ws_key_tag(ws)
    if tag:
        row = registry_lib.load_row(tag, home=REG_HOME)
        if row is not None and row["status"] != "tombstoned":
            return row
    cd = ws.get("current_directory")
    ct = ws_custom_title(ws)
    if cd and ct:
        row = registry_lib.find_row(cd, ct, home=REG_HOME)
        if row is not None and row["status"] != "tombstoned":
            return row
    if cd:
        row = registry_lib.find_by_root(cd, home=REG_HOME)
        if row is not None and row["status"] != "tombstoned":
            return row
    return None


# MW-A ownership + merge live in bundles_lib.py — three callers need the same
# answer (adopt, backfill, merge), and two copies of that ladder would drift.
# A drifted ownership rule silently mis-files someone's work.
CONSUMED_MARKER = bundles_lib.CONSUMED_MARKER
resolve_reentry = bundles_lib.resolve_reentry
collect_reentries = bundles_lib.collect_reentries
bundle_owner = bundles_lib.bundle_owner
mark_consumed = bundles_lib.mark_consumed


def window_name_for(project_name, label, taken_names):
    """D12 — this window's sidebar name: the project name is ALWAYS the stem,
    with the label appended. "OKOA Works" + "Golden East" -> "OKOA Works Golden
    East", so the row a window belongs to is never in doubt.

    With no label given for an additional window, the stem is numbered rather
    than left to collide: two tabs both reading "OKOA Works" would be
    indistinguishable in the sidebar, which is the confusion D12 exists to
    prevent. A number is a weak label, so the caller SAYS it was auto-assigned.
    """
    if label:
        return "%s %s" % (project_name, label)
    taken = {str(t).casefold() for t in taken_names if t}
    if project_name.casefold() not in taken:
        return project_name
    n = 2
    while ("%s %d" % (project_name, n)).casefold() in taken:
        n += 1
    return "%s %d" % (project_name, n)


def window_label_of(window_name, project_name):
    """The inverse of window_name_for: the label carried by a window name.
    None for the plain window named exactly the project (D12)."""
    wn = (window_name or "").strip()
    stem = (project_name or "").strip()
    if not stem or wn.casefold() == stem.casefold():
        return None
    if wn.casefold().startswith(stem.casefold()):
        return wn[len(stem):].strip(" -–—:·") or None
    return wn


def print_other_windows(project_uuid, ws_id, live_ids):
    """MW-C — the shared project brief.

    What the OTHER live windows on this project are doing, read before this one
    starts. This is the thing that stops two windows silently duplicating work:
    without it, the second window's only signal is that the first one exists.

    Liveness comes from the FRESH workspace list passed in, never from the
    manifest files — a claim proves a window once opened the project, not that
    it still exists. Never fatal: an unreadable manifest must not block a pick.
    """
    try:
        import windows_lib
    except ImportError as exc:
        print("other windows: manifest unavailable (%s) — pick continues" % exc)
        return []
    try:
        reaped = windows_lib.reap_stale(project_uuid, live_ids, home=REG_HOME)
        if reaped:
            print("other windows: cleared %d claim%s whose window no longer exists"
                  % (len(reaped), "" if len(reaped) == 1 else "s"))
        others = windows_lib.other_windows(project_uuid, ws_id, live_ids, home=REG_HOME)
        if not others:
            print("other windows on this project: none — this is the only one open")
            return []
        print("OTHER WINDOWS ON THIS PROJECT (%d) — read this before starting, so two "
              "windows do not do the same work:" % len(others))
        for o in others:
            print("  - %s" % windows_lib.describe(o))
        # MW-E, only when the switch is on. Off by default on purpose: a
        # warning that fires on partial data trains you to ignore warnings.
        if windows_lib.collision_warning_enabled(home=REG_HOME):
            clashes = windows_lib.collisions(project_uuid, ws_id, live_ids, home=REG_HOME)
            if clashes:
                print("  COLLISION WARNING — files another live window has also touched:")
                for cl in clashes:
                    print("    ! %s (%s): %s" % (cl["label"], cl["working_on"] or "not stated",
                                                 ", ".join(cl["files"][:5])))
                    if len(cl["files"]) > 5:
                        print("        ... and %d more" % (len(cl["files"]) - 5))
        return others
    except (OSError, ValueError) as exc:
        print("other windows: could not be read (%s: %s) — pick continues"
              % (type(exc).__name__, exc))
        return []


def claim_this_window(project_uuid, ws_id, label, session_id, next_action):
    """Register THIS window in the project's manifest, so the NEXT window can
    read it (MW-C). Seeded with the reentry's next action — a truthful default
    that beats an empty 'not stated' on the very first read."""
    try:
        import windows_lib
        windows_lib.claim_window(project_uuid, ws_id, label=label,
                                 session_id=session_id, working_on=next_action,
                                 home=REG_HOME)
        print("window manifest: this window registered as %r on this project"
              % (label or "(no label)"))
    except (ImportError, OSError, ValueError) as exc:
        print("window manifest: NOT registered (%s: %s) — other windows will not see "
              "this one; the pick itself is unaffected" % (type(exc).__name__, exc))


def release_window_claim(project_uuid, ws_id):
    """Drop this window's claim on the project it is leaving, so a released
    project does not keep reporting a window that moved on."""
    try:
        import windows_lib
        if windows_lib.release_window(project_uuid, ws_id, home=REG_HOME):
            print("window manifest: released this window's claim on the outgoing project")
    except (ImportError, OSError) as exc:
        print("window manifest: could not release the outgoing claim (%s)" % exc)


def print_knowledge(root, project_uuid, dry=False):
    """KB-B — what this project KNOWS, shown on reopen.

    D8: print the INDEX plus the 'learned since you were last here' digest,
    NEVER the whole base. Context cost is real — the OKOA base alone is 156,622
    characters — so deeper files open only on request.

    D5d: review AFTER, not before. Zee reads this and strikes any line he
    disagrees with; he is an editor here, not a gatekeeper. That is what makes
    D4's silent auto-writing survivable.

    KB-C runs here too: every stored count/path/date claim is re-verified NOW.
    A stale fact is worse than a missing one, because it reads as confident.

    Never fatal. A knowledge store that cannot be read must not block a pick.
    """
    try:
        import knowledge_lib
    except ImportError as exc:
        print("knowledge: unavailable (%s) — pick continues" % exc)
        return
    try:
        facts = knowledge_lib.live_facts(project_uuid, home=REG_HOME)
        if not facts:
            print("knowledge: nothing stored for this project yet (it fills up as you close)")
            return
        idx = knowledge_lib.build_index(project_uuid, home=REG_HOME)
        top = ", ".join("%s (%d)" % (s, n) for s, n in idx["subjects"][:6])
        print("knowledge: %d facts live of %d written, %d things known, %d fact%s checkable"
              % (idx["live_fact_count"], idx["total_fact_count"], idx["entity_count"],
                 idx["checked_fact_count"], "" if idx["checked_fact_count"] == 1 else "s"))
        if top:
            print("  subjects: %s" % top)

        last_seen = knowledge_lib.get_last_seen(project_uuid, home=REG_HOME)
        new = knowledge_lib.digest(project_uuid, since=last_seen, home=REG_HOME)
        if new:
            print("  learned since you were last here (%d) — strike any line you disagree with:"
                  % len(new))
            for f in new[:10]:
                print("    - [%s] %s" % (f["kind"], f["claim"]))
                print("        because: %s %s" % (f["evidence"]["type"], f["evidence"]["value"]))
            if len(new) > 10:
                print("    ... and %d more (ask to see them)" % (len(new) - 10))
        else:
            print("  nothing new since you were last here")

        drift = [d for d in knowledge_lib.recheck(project_uuid, root, home=REG_HOME)
                 if d["status"] == "DRIFTED"]
        unver = [d for d in knowledge_lib.recheck(project_uuid, root, home=REG_HOME)
                 if d["status"] == "unverifiable"]
        if drift:
            print("  STALE — %d stored fact%s no longer matches the disk:"
                  % (len(drift), "" if len(drift) == 1 else "s"))
            for d in drift:
                print("    ! %s  ->  %s" % (d["claim"], d["detail"]))
            print("    (nothing was auto-corrected — a stale fact is flagged, never silently "
                  "rewritten)")
        if unver:
            print("  %d fact%s carries a check only a person can settle"
                  % (len(unver), "" if len(unver) == 1 else "s"))

        # KB-E — a trap learned in ANOTHER project that touches something this
        # one also works with. Shown with the shared term, so the reason for the
        # suggestion is visible and a weak link is obvious as a weak link.
        try:
            hits = knowledge_lib.cross_project_hits(project_uuid, home=REG_HOME, limit=4)
        except (OSError, ValueError):
            hits = []
        if hits:
            print("  from your OTHER projects (%d) — same tool or file, learned elsewhere:"
                  % len(hits))
            for h in hits:
                src = registry_lib.load_row(h["project_uuid"], home=REG_HOME)
                print("    ~ [%s] %s" % (", ".join(h["shared"]), h["claim"][:110]))
                print("        learned in: %s"
                      % ((src or {}).get("name") or h["project_uuid"]))

        if not dry:
            knowledge_lib.set_last_seen(project_uuid, home=REG_HOME)
    except (OSError, ValueError, KeyError) as exc:
        print("knowledge: could not be read (%s: %s) — pick continues"
              % (type(exc).__name__, exc))



def main():
    if not PROJECT:
        refuse("--project <uuid> is required")

    row = registry_lib.load_row(PROJECT, home=REG_HOME)
    if row is None:
        refuse("no registry row for %s" % PROJECT)
    if row["status"] == "tombstoned":
        refuse("row %s ('%s') is tombstoned — un-tombstoning is a human act" % (PROJECT, row["name"]))
    root = row["root"]
    if not os.path.isdir(root):
        refuse("row root does not exist: %r (BROKEN row — fix the folder before adopting)" % root)

    print("row: %s name=%r status=%s" % (PROJECT, row["name"], row["status"]))
    print("root: %s (exists)" % root)

    if SKIP_CMUX:
        print("RESURRECTION_SKIP_CMUX=1 — decision only: ADOPT %r into the current tab" % row["name"])
        return 0

    ws_id = os.environ.get("CMUX_WORKSPACE_ID")
    if not ws_id:
        refuse("$CMUX_WORKSPACE_ID is unset — adopt-in-place needs a cmux tab to re-bind; "
               "this session is not running in one")

    workspaces = list_workspaces()
    me = None
    for ws in workspaces:
        if (ws.get("id") or "").casefold() == ws_id.casefold():
            me = ws
            break
    if me is None:
        refuse("$CMUX_WORKSPACE_ID %s is not in a live workspace.list — SET-BUT-DEAD env "
               "(cmux restarted under this process); cannot adopt into a tab that is gone" % ws_id)
    print("this tab: %s custom_title=%r cwd=%s"
          % (ws_id, ws_custom_title(me), me.get("current_directory")))

    # ---- gate 1: ALREADY-OPEN elsewhere ------------------------------------
    # D11: the guard STAYS the default — a bare adopt of an already-open project
    # still refuses with exit 4, exactly as before. What changed is that the
    # refusal now NAMES the second option instead of pretending there is only
    # one. Zee asked for the choice, not the removal of the guard, so the choice
    # is his: the skill asks, and --additional-window carries his answer back.
    others = [w for w in workspaces
              if (w.get("id") or "").casefold() != ws_id.casefold() and binds_row(w, row)]
    if others and not EXTRA_WINDOW:
        o = others[0]
        print("ALREADY OPEN — %r is open in workspace %s (%r)."
              % (row["name"], o.get("id"), ws_custom_title(o) or o.get("title")))
        print("  option 1 (default): jump to that window and continue there.")
        print("  option 2: open a SECOND window on the same project — re-run with "
              "--additional-window. Both windows share one row, one knowledge store, "
              "and one book entry (D9/D10).")
        print("ASK ZEE WHICH — do not choose for him.")
        return 4
    if others and EXTRA_WINDOW:
        print("ADDITIONAL WINDOW — %d other window%s already open on %r; adopting anyway "
              "because --additional-window was given (D11: Zee's choice, not a default)"
              % (len(others), "" if len(others) == 1 else "s", row["name"]))
        for o in others:
            print("  also open: %s (%r)" % (o.get("id"), ws_custom_title(o) or o.get("title")))

    # ---- gate 2: OUTGOING project must have been closed properly ----------
    out_row = outgoing_row(me)
    if out_row is not None and out_row["project_uuid"] == row["project_uuid"]:
        print("outgoing: none — this tab is ALREADY bound to %r (re-adopt is idempotent)" % row["name"])
        out_row = None
    elif out_row is not None:
        lc = out_row["last_close"]
        if not lc:
            print("OUTGOING NOT-CLOSED — this tab currently holds %r (%s, status=%s) and it has NO "
                  "close record (last_close is null). Adopting would release it with its reentry "
                  "state unsaved. Run /acos-safe-close on it first, or pick it instead."
                  % (out_row["name"], out_row["project_uuid"], out_row["status"]))
            return 3
        print("outgoing: %r closed at %s — releasing this tab (status: %s -> parked)"
              % (out_row["name"], lc.get("at"), out_row["status"]))
    else:
        print("outgoing: none — this tab is bound to no live registry row")

    reentry, reentry_src, notes = resolve_reentry(root, row)
    unread = [n for n in notes if not n["consumed"]]
    print("reentry: %s" % (reentry or "(none)"))
    print("reentry source: %s" % reentry_src)
    if notes:
        print("owned reentry notes: %d total, %d unread — ALL listed below; none is hidden "
              "by recency" % (len(notes), len(unread)))
        for n in notes:
            print("  [%s] %s" % ("UNREAD" if not n["consumed"] else " seen ",
                                 os.path.relpath(n["path"], root)))
            print("           owner evidence: %s" % n["evidence"])
        if len(unread) > 1:
            print("MERGE — %d unread notes were left by different windows of this project. "
                  "Read every UNREAD path above, not just the first." % len(unread))

    # KB-B — what the project knows, index + digest only (D8). Placed after all
    # gates, so a refused adopt never marks knowledge as seen. dry=DRY keeps a
    # --dry-run from advancing the "since you were last here" watermark.
    print_knowledge(root, PROJECT, dry=DRY)

    # MW-C — the shared project brief, read BEFORE this window starts work.
    live_ws_ids = [w.get("id") for w in workspaces if w.get("id")]
    print_other_windows(PROJECT, ws_id, live_ws_ids)

    if DRY:
        print("DRY RUN — decision: rename tab %s -> %r, tag [key:%s], status %s -> active; "
              "would stamp %d unread note%s as seen; no writes performed"
              % (ws_id, row["name"], PROJECT, row["status"], len(unread),
                 "" if len(unread) == 1 else "s"))
        return 0

    # ---- re-bind the tab: sidebar name + durable [key:<uuid>] tag ----------
    next_action = (row.get("last_close") or {}).get("next_action") or ""
    desc = ("%s [key:%s]" % (next_action, PROJECT)).strip()
    tag_ok = False
    sd = cmux(["workspace-action", "--action", "set-description",
               "--workspace", ws_id, "--description", desc])
    if sd.returncode != 0:
        print("WARN: set-description rc=%d stderr=%s — join tag NOT durable; the book may "
              "re-claim this tab by folder" % (sd.returncode, sd.stderr.strip()[:200]))
    else:
        listed = [w for w in list_workspaces()
                  if (w.get("id") or "").casefold() == ws_id.casefold()]
        key_tag = "[key:%s]" % PROJECT
        tag_ok = bool(listed) and key_tag in (listed[0].get("description") or "")
        print("description tag round-trip: %s"
              % ("OK — %r on workspace %s" % (key_tag, ws_id) if tag_ok
                 else "NOT-VERIFIED — %r did not read back" % key_tag))

    # D12: the sidebar name is the project name plus this window's label. The
    # REGISTRY row keeps workspace_name == the project name regardless — one row
    # per project (D10) — and the [key:<uuid>] tag is what binds this tab to it,
    # so a labelled tab is still unambiguously the same project.
    taken = [ws_custom_title(w) for w in workspaces
             if (w.get("id") or "").casefold() != ws_id.casefold()]
    my_name = window_name_for(row["name"], LABEL, taken)
    if my_name != row["name"] and not LABEL:
        print("WINDOW NAME — %r was already taken by another window, so this one is %r. "
              "Pass --label <name> to give it a meaningful label instead (D12)."
              % (row["name"], my_name))
    rn = cmux(["workspace-action", "--action", "rename",
               "--workspace", ws_id, "--title", my_name])
    if rn.returncode != 0:
        print("WARN: rename rc=%d stderr=%s — tab not renamed to %r (non-fatal, cosmetic)"
              % (rn.returncode, rn.stderr.strip()[:200], my_name))
    else:
        print("tab renamed: sidebar name -> %r (workspace %s)" % (my_name, ws_id))

    # ---- registry: release the outgoing row, activate the picked row -------
    # root is taken from the ROW, never from the tab's cwd — adoption re-binds
    # identity, and must never relocate a project to the tab's folder.
    if out_row is not None and out_row["status"] == "active":
        registry_lib.upsert_row({"project_uuid": out_row["project_uuid"],
                                 "root": out_row["root"], "status": "parked"}, home=REG_HOME)
        registry_lib.audit_append({"event": "adopt-released", "project_uuid": out_row["project_uuid"],
                                   "workspace": ws_id, "to_project_uuid": PROJECT}, home=REG_HOME)
        print("registry: outgoing %r -> parked (read back: %s)"
              % (out_row["name"], registry_lib.load_row(out_row["project_uuid"], home=REG_HOME)["status"]))

    fields = {"project_uuid": PROJECT, "root": root, "workspace_name": row["name"]}
    if row["status"] in ("parked", "completed"):
        fields["status"] = "active"
    new_row = registry_lib.upsert_row(fields, home=REG_HOME)
    print("registry: status -> %s (read back: %s)" % (new_row["status"], new_row["status"]))

    registry_lib.audit_append(
        {"event": "adopt-in-place", "project_uuid": PROJECT, "root": root,
         "workspace": ws_id, "description_tag_ok": tag_ok,
         "released_project_uuid": out_row["project_uuid"] if out_row else None,
         "reentry_notes_owned": len(notes), "reentry_notes_unread": len(unread),
         "tab_cwd": me.get("current_directory")}, home=REG_HOME)

    # ---- stamp the notes we just surfaced ----------------------------------
    # Only AFTER the re-bind succeeded: a refused adopt must never consume a
    # note it did not show. The stamp is a marker file beside the note; the
    # note is never moved and never deleted (append-only, per the brief's D5b).
    # MW-C — register THIS window so the next one can read it, and drop the
    # claim on the project this tab just left.
    if out_row is not None:
        release_window_claim(out_row["project_uuid"], ws_id)
    claim_this_window(PROJECT, ws_id, window_label_of(my_name, row["name"]),
                      os.environ.get("CLAUDE_CODE_SESSION_ID"),
                      (row.get("last_close") or {}).get("next_action"))

    stamped = mark_consumed(unread, PROJECT, ws_id)
    if stamped:
        print("stamped %d note%s as seen (%s written in each bundle — the note files are "
              "NEVER moved or deleted; delete a marker to un-see it)"
              % (len(stamped), "" if len(stamped) == 1 else "s", CONSUMED_MARKER))

    # ---- the loud folder caveat -------------------------------------------
    tab_cwd = me.get("current_directory") or ""
    same = False
    try:
        same = bool(tab_cwd) and os.path.realpath(tab_cwd).casefold() == row["root_casefold"]
    except OSError:
        same = False
    print("ADOPTED — this tab is now %r" % row["name"])
    if same:
        print("working root: %s (tab folder MATCHES — relative paths are safe)" % root)
    else:
        print("working root: %s" % root)
        print("FOLDER CAVEAT — this tab's shell folder is still %r and CANNOT be changed "
              "(cmux has no re-point verb; the session cwd was fixed at launch). Identity is "
              "re-bound, the folder is not. Every file operation for this project MUST use "
              "absolute paths under the working root above." % tab_cwd)
    return 0


try:
    sys.exit(main())
except SystemExit:
    raise
except BaseException as exc:  # loud, never silent — adoption is a state change
    print("REFUSED — unhandled %s: %s" % (type(exc).__name__, exc))
    sys.exit(1)
PYEOF
