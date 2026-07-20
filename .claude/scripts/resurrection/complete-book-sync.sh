#!/bin/bash
# complete-book-sync.sh — /acos-complete pipeline step: auto-finish the
# resurrect-book row for the project /acos-complete just archived.
#
# Policy (user decision 2026-07-18, "Auto-finish always"): every /acos-complete
# run flips this project's registry row to status=completed (ARCHIVED tier in
# /acos-resurrect). No prompt. The reverse door is enroll-project.sh's
# revive-on-work: the next session started in this project flips the row back
# to active automatically. Tombstoned rows are never touched (human act only).
# Rows are never deleted.
#
# Usage: complete-book-sync.sh [--root <project_root>]
# Env (tests): ACOS_REGISTRY_HOME sandboxes the registry side.
# Fail-open: any error prints a note and exits 0 — /acos-complete must never
# be blocked by book sync.
set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${2:-$PWD}"
[ "${1:-}" = "--root" ] && ROOT="$2"

COMPLETE_LIB_DIR="$SCRIPT_DIR" COMPLETE_ROOT="$ROOT" /usr/bin/python3 - <<'PY' || echo "book sync: non-fatal error — /acos-complete unaffected"
import json, os, subprocess, sys
sys.path.insert(0, os.environ["COMPLETE_LIB_DIR"])
import registry_lib

root = os.path.realpath(os.environ["COMPLETE_ROOT"])
home = os.environ.get("ACOS_REGISTRY_HOME") or None


def _sidebar_name():
    """This session's cmux sidebar name (custom_title), or None. Fail-open;
    the id must appear in a live workspace.list (set-but-dead guard)."""
    ws_id = os.environ.get("CMUX_WORKSPACE_ID")
    if not ws_id:
        return None
    try:
        out = subprocess.run(
            ["/Applications/cmux.app/Contents/Resources/bin/cmux", "rpc", "workspace.list"],
            capture_output=True, text=True, timeout=5)
        if out.returncode != 0:
            return None
        for w in json.loads(out.stdout).get("workspaces", []):
            if (w.get("id") == ws_id and w.get("has_custom_title")
                    and (w.get("custom_title") or "").strip()):
                return w["custom_title"].strip()
    except (OSError, subprocess.TimeoutExpired, ValueError):
        pass
    return None


# Sidebar-name first (several projects share one root): finish the row of THE
# WORKSPACE this session runs in; folder-level row only as fallback.
ws_name = _sidebar_name()
row = registry_lib.find_row(root, ws_name, home=home) if ws_name else None
if row is None:
    row = registry_lib.find_by_root(root, home=home)
if row is None:
    print("book sync: no registry row for %s%s — nothing to finish"
          % (root, (" (sidebar %r)" % ws_name) if ws_name else ""))
    sys.exit(0)
if row["status"] == "tombstoned":
    print("book sync: row is tombstoned (human act) — left untouched")
    sys.exit(0)
if row["status"] == "completed":
    print("book sync: %s already completed in the book" % row["name"])
    sys.exit(0)
registry_lib.upsert_row(
    {"project_uuid": row["project_uuid"], "root": row["root"], "status": "completed"},
    home=home,
)
registry_lib.audit_append(
    {"event": "finished-by-acos-complete", "project_uuid": row["project_uuid"],
     "from_status": row["status"]},
    home=home,
)
back = registry_lib.load_row(row["project_uuid"], home=home)
print("book sync: %s -> completed (ARCHIVED in /acos-resurrect; read back). "
      "Auto-revives on your next session here." % back["name"])
PY
exit 0
