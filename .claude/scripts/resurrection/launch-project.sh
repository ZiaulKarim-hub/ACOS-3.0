#!/bin/bash
# launch-project.sh — focus-or-launch, SPINE 1 (ACOS Resurrection Protocol).
#
# Interface:
#   launch-project.sh --project <uuid> [--dry-run] [--command-override <cmd>]
# Env overrides (tests only):
#   ACOS_REGISTRY_HOME        registry home override (never the real ~ in tests)
#   RESURRECTION_SKIP_CMUX=1  no cmux calls at all (sandbox: decision print only)
#
# SPINE 1: focus, never a second workspace. cmux does NO dedup — a routing bug
# here creates a 5th ACOS 3.0 workspace. If the project is open ANYWHERE, we
# FOCUS its workspace and stop; we only CREATE when no workspace matches.
#
# Delivery contract: the prompt route is argv (--command), never cmux send /
# surface.send_text (they shred multi-line prompts at every \n). The default
# --command is NON-claude (DR-1 defers the real claude launch): a cat of the
# reentry file wrapped in BEGIN/END marker lines so read-screen can verify
# delivery. --command-override substitutes DR-1's real invocation later; the
# {REENTRY} placeholder is replaced with the shell-quoted reentry PATH.
#
# Security guardrail: NO registry-derived string ever enters --command — only
# the reentry file PATH (resolved from the filesystem at open time; the
# registry-recorded path is a said-so fallback). name/next_action go via
# --name/--description in LIST-FORM subprocess argv (attack surface is
# XSS-not-shell; list form defeats shell injection).

set -u

LP_PROJECT=""
LP_DRY=0
LP_OVERRIDE=""
while [ $# -gt 0 ]; do
  case "$1" in
    --project)          LP_PROJECT="${2:-}"; shift 2 ;;
    --dry-run)          LP_DRY=1; shift ;;
    --command-override) LP_OVERRIDE="${2:-}"; shift 2 ;;
    *) echo "REFUSED — unknown argument: $1" >&2; exit 2 ;;
  esac
done
export LP_PROJECT LP_DRY LP_OVERRIDE
LP_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export LP_LIB_DIR

# exec: the python exit status is the script's; nothing runs after the heredoc.
exec /usr/bin/python3 - <<'PYEOF'
"""launch-project.sh embedded body — focus-or-launch (SPINE 1).

Constraints:
  * System /usr/bin/python3 is 3.9.6, stdlib only, NO yaml module.
  * Registry access ONLY via registry_lib.py (same directory).
  * cmux via the ABSOLUTE binary; workspace identity is UUIDs only (refs like
    workspace:8 RENUMBER across lifecycle — never persisted, never trusted).
  * Join rule: [key:<uuid>] description tag; for sidebar-named rows the
    human-set custom_title (cwd-guarded); for folder-level rows a
    realpath(current_directory) match that excludes named siblings' workspaces.
    NEVER the dynamic title (Claude rewrites titles live).
  * Newest .reentry.md is re-resolved AT OPEN TIME under
    <root>/memory/handoffs/closed/ — never a cached filename (Eternity and
    later closes write newer handoffs continuously). The row's recorded
    reentry_path is a loud, last-resort fallback.
  * Delivery is VERIFIED via read-screen + exactly one retry, never assumed.
    The trust gate ('Quick safety check') is detected and reported — untrusted
    dirs look launched but never deliver the prompt.
"""
import json
import os
import shlex
import subprocess
import sys
import time
import uuid as uuid_mod

CMUX_BIN = "/Applications/cmux.app/Contents/Resources/bin/cmux"
TRUST_GATE_TEXT = "Quick safety check"
MARKER_STEM = "RESURRECTION-DELIVERY-"  # split in echo args so the typed command never shows the full marker

PROJECT = os.environ.get("LP_PROJECT", "")
DRY = os.environ.get("LP_DRY", "0") == "1"
OVERRIDE = os.environ.get("LP_OVERRIDE", "")
LIB_DIR = os.environ.get("LP_LIB_DIR", "")
REG_HOME = os.environ.get("ACOS_REGISTRY_HOME") or None
SKIP_CMUX = os.environ.get("RESURRECTION_SKIP_CMUX") == "1"

sys.path.insert(0, LIB_DIR)
import registry_lib


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
        newest = candidates[-1][1]
        return newest, "scan of closed/ at open time (newest of %d candidate%s by mtime)" % (
            len(candidates), "" if len(candidates) == 1 else "s")
    recorded = (row.get("last_close") or {}).get("reentry_path")
    if recorded and os.path.isfile(recorded):
        return recorded, ("FALLBACK: scan of %s found NO .reentry.md — using the registry-recorded "
                          "reentry_path (may be stale; the scan is the truth source)" % closed_dir)
    return None, "no .reentry.md found by scan and no usable registry-recorded reentry_path"


def workspace_matches(workspaces, row, key_tag):
    """Join for THIS row. Evidence accepted, strongest first:
      * the [key:<uuid>] description tag;
      * for sidebar-named rows: the human-set custom_title (has_custom_title),
        casefolded, cwd-guarded — NEVER the dynamic title;
      * for folder-level rows: realpath(cwd) match, EXCLUDING workspaces whose
        sidebar name belongs to a different registered row at the same root
        (a folder launch must never steal a named project's workspace)."""
    root_key = os.path.realpath(row["root"]).casefold()
    wn = row.get("workspace_name")
    sibling_names = set()
    if wn is None:
        for r in registry_lib.rows_for_root(row["root"], home=REG_HOME):
            if r["workspace_name"] and r["project_uuid"] != row["project_uuid"]:
                sibling_names.add(r["workspace_name"].casefold())
    matches = []
    for w in workspaces:
        why = []
        desc = w.get("description") or ""
        custom = (w.get("custom_title") or "").strip()
        if not w.get("has_custom_title"):
            custom = ""
        cwd = w.get("current_directory") or ""
        cwd_ok = bool(cwd) and os.path.realpath(cwd).casefold() == root_key
        if key_tag in desc:
            why.append("key-tag")
        if wn and custom and custom.casefold() == wn.casefold() and (not cwd or cwd_ok):
            why.append("sidebar-name")
        if wn is None and cwd_ok and custom.casefold() not in sibling_names:
            why.append("cwd-realpath")
        if why:
            matches.append((w, "+".join(why)))
    return matches


def pick_most_recent(matches):
    """Among duplicate matches, focus the most recently active workspace."""
    def keyfn(pair):
        return pair[0].get("latest_submitted_at") or ""
    return max(matches, key=keyfn)


def build_command(reentry):
    """Default NON-claude delivery command (DR-1 substitutes claude later).

    Only the shell-quoted reentry PATH and generated literals enter the
    command. The marker is split across echo args so the full marker string
    never appears in the typed command line — read-screen can only match it
    in actual OUTPUT."""
    nonce = uuid_mod.uuid4().hex[:12]
    begin = MARKER_STEM + "BEGIN-" + nonce
    cmd = ("echo '%s''BEGIN-%s'; cat %s; echo '%s''END-%s'; exec /bin/zsh -i"
           % (MARKER_STEM, nonce, shlex.quote(reentry), MARKER_STEM, nonce))
    return cmd, begin


def read_screen(ws_id):
    """read-screen with scrollback (a long reentry scrolls BEGIN off-screen)."""
    out = cmux(["read-screen", "--workspace", ws_id, "--scrollback"])
    if out.returncode != 0:
        out = cmux(["read-screen", "--workspace", ws_id])  # older builds: no --scrollback
    if out.returncode != 0:
        return None
    return out.stdout


def finalize(project_uuid, root, mode, ws_id, desc, delivered, trust_gate):
    """Step 6 — only after a successful focus-or-launch: activate the row,
    write the durable [key:<uuid>] description tag, append the audit event."""
    row = registry_lib.upsert_row(
        {"project_uuid": project_uuid, "root": root, "status": "active"}, home=REG_HOME)
    back = registry_lib.load_row(project_uuid, home=REG_HOME)
    if back is None or back["status"] != "active":
        refuse("registry read-back failed: row not active after launch upsert")
    print("registry: status -> active (read back: %s)" % back["status"])

    tag_ok = None
    if not SKIP_CMUX:
        out = cmux(["workspace-action", "--action", "set-description",
                    "--workspace", ws_id, "--description", desc])
        if out.returncode != 0:
            print("WARN: set-description rc=%d stderr=%s — join tag NOT durable"
                  % (out.returncode, out.stderr.strip()[:200]))
            tag_ok = False
        else:
            key_tag = "[key:%s]" % project_uuid
            listed = [w for w in list_workspaces() if w.get("id") == ws_id]
            tag_ok = bool(listed) and key_tag in (listed[0].get("description") or "")
            print("description tag round-trip: %s" % ("OK — %r on workspace %s" % (key_tag, ws_id)
                                                      if tag_ok else "FAILED — tag not read back"))
    registry_lib.audit_append(
        {"event": "launch", "project_uuid": project_uuid, "mode": mode,
         "workspace_id": ws_id, "delivered": delivered, "trust_gate": trust_gate,
         "description_tag_ok": tag_ok}, home=REG_HOME)
    print("audit: launch event appended (mode=%s workspace=%s)" % (mode, ws_id))


def main():
    # ---- step 1: load the row; refuse tombstoned / BROKEN-critical ---------
    if not PROJECT:
        refuse("--project <uuid> is required", code=2)
    try:
        row = registry_lib.load_row(PROJECT, home=REG_HOME)
    except (ValueError, json.JSONDecodeError) as exc:
        refuse("registry row for %s is corrupt (BROKEN): %s" % (PROJECT, exc))
    if row is None:
        refuse("no registry row for project_uuid %s (home=%s)" % (PROJECT, REG_HOME or "~"), code=2)
    if row["status"] == "tombstoned":
        refuse("row %s is tombstoned (at %s) — launch refused; un-tombstoning is a human act"
               % (PROJECT, row["tombstoned_at"]))
    root = row["root"]
    name = row["name"]
    print("row: %s name=%r status=%s" % (PROJECT, name, row["status"]))

    # ---- step 2: [ -d root ] pre-check — exact reason + heal hint ----------
    if not os.path.isdir(root):
        refuse("BROKEN — root directory is GONE: %s. Recorded dev_ino=%s. If the project "
               "was MOVED (not deleted), run registry_lib.find_by_root('<new path>') — the "
               "(st_dev, st_ino) re-link heals the row in place without minting a new identity."
               % (root, row["dev_ino"]))
    print("root: %s (exists)" % root)

    next_action = (row.get("last_close") or {}).get("next_action") or ("resume %s" % name)
    desc = "%s [key:%s]" % (next_action, PROJECT)
    key_tag = "[key:%s]" % PROJECT

    # ---- reentry re-resolution AT OPEN TIME (needed by create + dry-run) ---
    reentry, reentry_note = resolve_reentry(root, row)
    print("reentry: %s" % (reentry or "(none)"))
    print("reentry source: %s" % reentry_note)

    # ---- step 3: focus-or-launch decision ----------------------------------
    if SKIP_CMUX:
        print("SANDBOX (RESURRECTION_SKIP_CMUX=1) — no cmux calls; decision undeterminable "
              "without workspace.list. Would FOCUS a workspace matching realpath(root)/%s, "
              "else CREATE with --name %r --description %r --cwd %r." % (key_tag, name, desc, root))
        if DRY:
            print("DRY RUN — no writes performed")
        else:
            print("no mutation performed in sandbox mode (registry untouched)")
        return 0

    workspaces = list_workspaces()
    matches = workspace_matches(workspaces, row, key_tag)

    if matches:
        w, why = pick_most_recent(matches)
        ws_id = w.get("id")
        if DRY:
            print("DRY RUN — decision: FOCUS existing workspace %s (matched by %s; %d match%s "
                  "of %d workspaces). No cmux mutation, no registry write."
                  % (ws_id, why, len(matches), "" if len(matches) == 1 else "es", len(workspaces)))
            return 0
        out = cmux(["workspace", "select", ws_id])
        if out.returncode != 0:
            refuse("workspace select %s failed rc=%d stderr=%s"
                   % (ws_id, out.returncode, out.stderr.strip()[:300]))
        print("focused existing workspace %s — no second workspace created" % ws_id)
        if len(matches) > 1:
            print("NOTE: %d workspaces match this project (duplicate pile-up) — focused the most "
                  "recently active; the others were left untouched: %s"
                  % (len(matches), ", ".join(m[0].get("id", "?") for m in matches if m[0].get("id") != ws_id)))
        print("matched by: %s" % why)
        # Trust-gate check on the focused screen too — report, never assume.
        screen = read_screen(ws_id)
        trust = bool(screen) and TRUST_GATE_TEXT in screen
        if trust:
            print("TRUST GATE DETECTED on focused workspace ('%s') — the session is waiting on "
                  "the safety prompt; nothing is delivered past it" % TRUST_GATE_TEXT)
        finalize(PROJECT, root, "focus", ws_id, desc, None, trust)
        return 0

    # ---- step 4: CREATE (no workspace matches anywhere) --------------------
    if OVERRIDE:
        if "{REENTRY}" in OVERRIDE:
            if not reentry:
                refuse("--command-override uses {REENTRY} but no reentry file could be resolved: %s"
                       % reentry_note)
            command = OVERRIDE.replace("{REENTRY}", shlex.quote(reentry))
            sub_note = "{REENTRY} replaced with the shell-quoted reentry PATH (the only substitution)"
        else:
            command = OVERRIDE
            sub_note = "used verbatim (no {REENTRY} placeholder)"
        needle = None  # override supplies no marker contract; verification below stays LOUD
        print("command: OVERRIDE (%d chars) — %s" % (len(command), sub_note))
    else:
        if not reentry:
            refuse("nothing to deliver: %s — close the project first (close-project.sh writes "
                   "closed/<slug>/<slug>.reentry.md) or pass --command-override" % reentry_note)
        command, needle = build_command(reentry)
        print("command: default non-claude delivery (cat reentry wrapped in BEGIN/END markers; "
              "DR-1 substitutes the real claude invocation via --command-override)")

    if DRY:
        print("DRY RUN — decision: CREATE workspace --name %r --description %r --cwd %r "
              "--command <%d chars%s>. No cmux mutation, no registry write."
              % (name, desc, root, len(command), "; marker " + needle if needle else ""))
        return 0

    count_before = len(workspaces)
    out = cmux(["workspace", "create", "--name", name, "--description", desc,
                "--cwd", root, "--command", command], timeout=30)
    if out.returncode != 0:
        refuse("workspace create failed rc=%d stderr=%s" % (out.returncode, out.stderr.strip()[:300]))

    # Join back to the created workspace by the [key:<uuid>] tag (durable),
    # never by title. Brief retry: the list may lag creation.
    ws_id = None
    for _ in range(5):
        time.sleep(1)
        listed = list_workspaces()
        tagged = [w for w in listed if key_tag in (w.get("description") or "")]
        if tagged:
            ws_id = tagged[-1].get("id")
            break
    if not ws_id:
        refuse("workspace was created (rc=0) but no workspace carrying %s appeared in "
               "workspace.list within 5s — cannot verify anything about it" % key_tag)
    print("created workspace %s (workspace count %d -> %d)" % (ws_id, count_before, len(listed)))

    # ---- step 5: VERIFY delivery via read-screen + exactly one retry -------
    delivered = False
    trust = False
    screen = None
    for attempt in (1, 2):
        time.sleep(2)
        screen = read_screen(ws_id)
        if screen is None:
            print("read-screen attempt %d: FAILED (no output)" % attempt)
            continue
        trust = trust or (TRUST_GATE_TEXT in screen)
        if needle and needle in screen:
            delivered = True
            print("read-screen attempt %d: BEGIN marker %r FOUND" % (attempt, needle))
            break
        print("read-screen attempt %d: %s not found yet"
              % (attempt, ("marker %r" % needle) if needle else "(no marker contract)"))
    if trust:
        print("TRUST GATE DETECTED ('%s') — the workspace LOOKS launched but the prompt is NOT "
              "delivered past the safety check; act on the gate before trusting delivery"
              % TRUST_GATE_TEXT)
    if needle is None:
        print("DELIVERY NOT-VERIFIED — --command-override provides no marker contract; "
              "verify delivery yourself (loud by design, never assumed)")
        finalize(PROJECT, root, "create", ws_id, desc, False, trust)
        return 3
    if delivered:
        print("DELIVERED — reentry content verified on screen via BEGIN marker")
        finalize(PROJECT, root, "create", ws_id, desc, True, trust)
        return 0
    print("DELIVERY NOT-VERIFIED — marker %r absent after 2 read-screen attempts%s"
          % (needle, "; trust gate present (likely cause)" if trust else ""))
    finalize(PROJECT, root, "create", ws_id, desc, False, trust)
    return 3


sys.exit(main())
PYEOF
