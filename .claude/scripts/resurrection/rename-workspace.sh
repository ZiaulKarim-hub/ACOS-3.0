#!/bin/bash
# rename-workspace.sh — set a cmux workspace's SIDEBAR name (custom_title) to a
# project name, so the tab visibly shows which project it is.
# Resurrection Protocol Fix 2 (user request 2026-07-20): every project pick
# auto-renames the tab to the picked project's name. Same-root picks call this
# to rename the CURRENT tab; launch-project.sh renames a different-root tab
# itself (see its finalize()).
#
# Interface:
#   rename-workspace.sh --name "<project name>" [--workspace <id|ref|index>]
# Default workspace: $CMUX_WORKSPACE_ID (the tab this session runs in).
#
# Why this is identity-safe: the sidebar name (custom_title, has_custom_title=
# true) is the strongest-after-key-tag join the book uses. Every NAMED registry
# row already stores workspace_name == name, so forcing custom_title = name
# makes the tab agree with its row: the book's name-claim lands on the right row
# and produces NO NAME DRIFT. Folder-level rows (workspace_name None) still
# claim by cwd, unaffected.
#
# Fail-open BY DESIGN: a rename failure is reported, never fatal — the rename is
# a cosmetic + attribution nicety, not a gate. Verified via workspace.list.
set -u
CMUX_BIN="${CMUX_CLAUDE_HOOK_CMUX_BIN:-/Applications/cmux.app/Contents/Resources/bin/cmux}"

RW_NAME=""
RW_WS=""
while [ $# -gt 0 ]; do
  case "$1" in
    --name)      RW_NAME="${2:-}"; shift 2 ;;
    --workspace) RW_WS="${2:-}"; shift 2 ;;
    *) echo "REFUSED — unknown argument: $1" >&2; exit 2 ;;
  esac
done

[ -n "$RW_NAME" ] || { echo "REFUSED — --name <project name> is required"; exit 2; }

# Trim surrounding whitespace AT THE DOOR (2026-08-18). cmux stores custom_title
# byte-for-byte, so a leading/trailing space in --name becomes a permanently
# odd-looking sidebar entry, and the verify step below used to compare a
# STRIPPED read-back against an UNSTRIPPED wanted value — an asymmetry that
# reported a mismatch on a rename that had done exactly what it was told.
# Trimming here kills the whole class at the source; the verify is now
# symmetric as well (belt and braces). A trim is ANNOUNCED, never silent.
RW_NAME_RAW="$RW_NAME"
RW_NAME="$(printf '%s' "$RW_NAME" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')"
if [ "$RW_NAME" != "$RW_NAME_RAW" ]; then
  echo "NOTE — trimmed surrounding whitespace from --name: $(printf '%q' "$RW_NAME_RAW") -> $(printf '%q' "$RW_NAME")"
fi
[ -n "$RW_NAME" ] || { echo "REFUSED — --name was only whitespace"; exit 2; }
[ -n "$RW_WS" ] || RW_WS="${CMUX_WORKSPACE_ID:-}"
[ -n "$RW_WS" ] || { echo "SKIP — no target workspace (no --workspace and \$CMUX_WORKSPACE_ID unset); tab not renamed"; exit 0; }

# The rename itself: workspace-action's `rename` sets custom_title. List-form
# argv (never a shell string) — the name is data, defeats shell injection.
out="$("$CMUX_BIN" workspace-action --action rename --workspace "$RW_WS" --title "$RW_NAME" 2>&1)"
rc=$?
if [ "$rc" -ne 0 ]; then
  echo "WARN — rename rc=$rc: ${out:0:200}; tab left as-is (non-fatal)"
  exit 0
fi

# Verify the sidebar name round-trips: custom_title == name AND has_custom_title.
CMUX_BIN="$CMUX_BIN" RW_WS="$RW_WS" RW_NAME="$RW_NAME" /usr/bin/python3 - <<'PY'
import json, os, subprocess, sys
cmux = os.environ["CMUX_BIN"]; ws = os.environ["RW_WS"]; want = os.environ["RW_NAME"]
try:
    out = subprocess.run([cmux, "rpc", "workspace.list"], capture_output=True, text=True, timeout=5)
    data = json.loads(out.stdout)
except Exception as exc:  # noqa: BLE001 — verify is best-effort, never fatal
    print("RENAMED — issued for %r (verify skipped: %s)" % (want, exc)); sys.exit(0)
for w in data.get("workspaces", []):
    if (w.get("id") or "").casefold() == ws.casefold():
        ct = (w.get("custom_title") or "").strip()
        # Compare TRIMMED to TRIMMED. Stripping only one side made this test
        # asymmetric and produced a false mismatch report (2026-08-18 fix).
        if w.get("has_custom_title") and ct == want.strip():
            print("RENAMED — tab %s sidebar name is now %r (verified)" % (ws, ct))
        else:
            print("RENAMED — issued for %r but read back custom_title=%r has_custom_title=%s"
                  % (want, ct, w.get("has_custom_title")))
        sys.exit(0)
print("RENAMED — issued for %r but workspace %s not present in workspace.list" % (want, ws))
PY
exit 0
