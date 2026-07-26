#!/bin/bash
# adopt-project.sh — ADOPT-IN-PLACE, SPINE 2 (ACOS Resurrection Protocol).
#
# Interface:
#   adopt-project.sh --project <uuid> [--dry-run]
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
#   1. ALREADY-OPEN (SPINE 1 still wins): if the picked project is live in some
#      OTHER workspace, refuse with exit 4 — the caller jumps there instead.
#      Adoption never creates a second tab for one project.
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
while [ $# -gt 0 ]; do
  case "$1" in
    --project) AP_PROJECT="${2:-}"; shift 2 ;;
    --dry-run) AP_DRY=1; shift ;;
    *) echo "REFUSED — unknown argument: $1" >&2; exit 2 ;;
  esac
done
export AP_PROJECT AP_DRY
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
  * Newest .reentry.md is re-resolved AT ADOPT TIME under
    <root>/memory/handoffs/closed/ — never a cached filename. The row's
    recorded reentry_path is a loud, last-resort fallback.
"""
import json
import os
import re
import subprocess
import sys

CMUX_BIN = "/Applications/cmux.app/Contents/Resources/bin/cmux"

PROJECT = os.environ.get("AP_PROJECT", "")
DRY = os.environ.get("AP_DRY", "0") == "1"
LIB_DIR = os.environ.get("AP_LIB_DIR", "")
REG_HOME = os.environ.get("ACOS_REGISTRY_HOME") or None
SKIP_CMUX = os.environ.get("RESURRECTION_SKIP_CMUX") == "1"

sys.path.insert(0, LIB_DIR)
import registry_lib

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


def resolve_reentry(root, row):
    """Newest .reentry.md under <root>/memory/handoffs/closed/, resolved NOW.

    Returns (path_or_None, source_note). The registry-recorded reentry_path is
    only a fallback when the scan finds nothing — and we SAY so."""
    closed_dir = os.path.join(root, "memory", "handoffs", "closed")
    candidates = []
    for dirpath, _dirnames, filenames in os.walk(closed_dir):
        for fn in filenames:
            if fn.endswith(".reentry.md"):
                p = os.path.join(dirpath, fn)
                try:
                    candidates.append((os.stat(p).st_mtime, p))
                except OSError:
                    pass
    if candidates:
        candidates.sort()
        return candidates[-1][1], "scan of closed/ at adopt time (newest of %d candidate%s by mtime)" % (
            len(candidates), "" if len(candidates) == 1 else "s")
    recorded = (row.get("last_close") or {}).get("reentry_path")
    if recorded and os.path.isfile(recorded):
        return recorded, ("FALLBACK: scan of %s found NO .reentry.md — using the registry-recorded "
                          "reentry_path (may be stale; the scan is the truth source)" % closed_dir)
    return None, "no .reentry.md found by scan and no usable registry-recorded reentry_path"


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

    # ---- gate 1: ALREADY-OPEN elsewhere (SPINE 1 still wins) ---------------
    others = [w for w in workspaces
              if (w.get("id") or "").casefold() != ws_id.casefold() and binds_row(w, row)]
    if others:
        o = others[0]
        print("REFUSED — %r is already open in workspace %s (%r) — jump to that tab instead of "
              "adopting a second one (SPINE 1: one project, one tab)"
              % (row["name"], o.get("id"), ws_custom_title(o) or o.get("title")))
        return 4

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

    reentry, reentry_src = resolve_reentry(root, row)
    print("reentry: %s" % (reentry or "(none)"))
    print("reentry source: %s" % reentry_src)

    if DRY:
        print("DRY RUN — decision: rename tab %s -> %r, tag [key:%s], status %s -> active; "
              "no writes performed" % (ws_id, row["name"], PROJECT, row["status"]))
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

    rn = cmux(["workspace-action", "--action", "rename",
               "--workspace", ws_id, "--title", row["name"]])
    if rn.returncode != 0:
        print("WARN: rename rc=%d stderr=%s — tab not renamed to %r (non-fatal, cosmetic)"
              % (rn.returncode, rn.stderr.strip()[:200], row["name"]))
    else:
        print("tab renamed: sidebar name -> %r (workspace %s)" % (row["name"], ws_id))

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
         "tab_cwd": me.get("current_directory")}, home=REG_HOME)

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
