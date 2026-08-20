#!/bin/bash
# launch-project.sh — open-a-window (ACOS Resurrection Protocol).
#
# Interface:
#   launch-project.sh --project <uuid> [--dry-run] [--command-override <cmd>]
#                     [--focus-existing] [--label <text>]
# Env overrides (tests only):
#   ACOS_REGISTRY_HOME        registry home override (never the real ~ in tests)
#   RESURRECTION_SKIP_CMUX=1  no cmux calls at all (sandbox: decision print only)
#
# ROUTING (Zee's Rule 3, 2026-08-19 — SUPERSEDES the old SPINE 1 focus rule):
# an open ALWAYS creates its own window, even when the project is already open
# somewhere. A repeat open is a new tab on the same project, never a question
# and never a jump. The old behaviour is still available on demand as
# --focus-existing. Every window on one project shares one registry row, one
# knowledge store and one book entry; sidebar names are kept distinct by
# --label, or auto-numbered when no label is given (D12).
#
# Delivery contract: the prompt route is argv (--command), never cmux send /
# surface.send_text (they shred multi-line prompts at every \n). The default
# --command IS the real claude launch (Zee's Rule 4, 2026-08-19): the shell
# prints the reentry file wrapped in BEGIN/END marker lines, then execs
# `claude --dangerously-skip-permissions` with a prompt naming the reentry
# PATH. MEASURED 2026-08-19: Claude Code renders inline (no alternate screen),
# so the markers survive in scrollback and read-screen still proves delivery.
# --command-override still replaces the whole command; its {REENTRY}
# placeholder is replaced with the shell-quoted reentry PATH.
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
LP_FOCUS=0
LP_LABEL=""
while [ $# -gt 0 ]; do
  case "$1" in
    --project)          LP_PROJECT="${2:-}"; shift 2 ;;
    --dry-run)          LP_DRY=1; shift ;;
    --command-override) LP_OVERRIDE="${2:-}"; shift 2 ;;
    --focus-existing)   LP_FOCUS=1; shift ;;
    --label)            LP_LABEL="${2:-}"; shift 2 ;;
    *) echo "REFUSED — unknown argument: $1" >&2; exit 2 ;;
  esac
done
export LP_PROJECT LP_DRY LP_OVERRIDE LP_FOCUS LP_LABEL
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
CLAUDE_BIN = "claude"           # resolved from the login shell's PATH inside the new window
CLAUDE_FLAGS = "--dangerously-skip-permissions"  # Zee's Rule 4, 2026-08-19

PROJECT = os.environ.get("LP_PROJECT", "")
DRY = os.environ.get("LP_DRY", "0") == "1"
OVERRIDE = os.environ.get("LP_OVERRIDE", "")
FOCUS_EXISTING = os.environ.get("LP_FOCUS", "0") == "1"
LABEL = (os.environ.get("LP_LABEL") or "").strip()
LIB_DIR = os.environ.get("LP_LIB_DIR", "")
REG_HOME = os.environ.get("ACOS_REGISTRY_HOME") or None
SKIP_CMUX = os.environ.get("RESURRECTION_SKIP_CMUX") == "1"

sys.path.insert(0, LIB_DIR)
import bundles_lib
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
    """The newest UNREAD .reentry.md OWNED BY THIS ROW, resolved NOW.

    Returns (path_or_None, source_note, notes).

    FIXED 2026-08-19. This used to take the newest .reentry.md anywhere under
    <root>/memory/handoffs/closed/, with no ownership check at all. One folder
    hosts many projects — ACOS 3.0 alone holds 72 close bundles — so opening
    'OKOA Works' handed back the newest bundle in the folder, which was
    'Research to Portfolio'. Passive before (the window only cat'd it); under
    Rule 4 the window now RESUMES from that note, so a mis-owned note would
    set claude working on the wrong project. bundles_lib.resolve_reentry is
    the ownership-filtered resolver adopt-project.sh already uses: the
    .project-uuid marker first, the registry's own recorded path second, a
    slug-name match last and only when that name is not shared."""
    return bundles_lib.resolve_reentry(root, row, home=REG_HOME)


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
    """Default delivery command — the REAL claude launch (Zee's Rule 4).

    2026-08-19. Every open now runs `claude --dangerously-skip-permissions`
    in the project's own folder; the old default dropped the window into a
    bare interactive shell and started no session at all.

    The RECEIPT survives the change (option (a), Zee's ruling 2026-08-19).
    The BEGIN/END markers and the cat are printed by the SHELL, before claude
    is exec'd. MEASURED in a sandboxed workspace on 2026-08-19: Claude Code
    renders inline (no alternate screen buffer), so those lines stay in
    scrollback and read-screen still proves the note arrived.

    Only the shell-quoted reentry PATH and generated literals enter the
    command — never registry-derived text. The marker is split across echo
    args so the full marker string never appears in the typed command line;
    read-screen can only match it in actual OUTPUT."""
    nonce = uuid_mod.uuid4().hex[:12]
    begin = MARKER_STEM + "BEGIN-" + nonce
    prompt = ("Resume this project. Read the reentry note at %s first, follow its "
              "'Read first' order, then continue from its NEXT ACTION." % reentry)
    cmd = ("echo '%s''BEGIN-%s'; cat %s; echo '%s''END-%s'; exec %s %s %s"
           % (MARKER_STEM, nonce, shlex.quote(reentry), MARKER_STEM, nonce,
              CLAUDE_BIN, CLAUDE_FLAGS, shlex.quote(prompt)))
    return cmd, begin


def window_name_for(project_name, label, taken_names):
    """This window's sidebar name (D12, mirrored from adopt-project.sh).

    The project name is ALWAYS the stem, with the label appended, so the row a
    window belongs to is never in doubt. With no label, the stem is NUMBERED
    rather than left to collide — two tabs both reading "To Do Tree" would be
    indistinguishable in the sidebar, which is exactly what Rule 3 makes
    common. A number is a weak label, so the caller SAYS it was auto-assigned.
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


def live_sidebar_names(workspaces):
    """Human-set sidebar names currently in use (dynamic titles excluded)."""
    out = set()
    for w in workspaces:
        if w.get("has_custom_title"):
            t = (w.get("custom_title") or "").strip()
            if t:
                out.add(t)
    return out


def read_screen(ws_id):
    """read-screen with scrollback (a long reentry scrolls BEGIN off-screen)."""
    out = cmux(["read-screen", "--workspace", ws_id, "--scrollback"])
    if out.returncode != 0:
        out = cmux(["read-screen", "--workspace", ws_id])  # older builds: no --scrollback
    if out.returncode != 0:
        return None
    return out.stdout


def finalize(project_uuid, root, mode, ws_id, desc, delivered, trust_gate, window_name=None):
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

        # Auto-rename the tab (Fix 2, user request 2026-07-20) — covers BOTH
        # focus and create (finalize runs on both). Named rows already store
        # workspace_name == name, so custom_title=name keeps tab and row in
        # agreement (no NAME DRIFT). Since Rule 3 (2026-08-19) several windows
        # can share one project, so the caller passes THIS window's name —
        # renaming a second window back to the bare project name would undo
        # the very distinction D12 exists to create. Non-fatal by design.
        proj_name = window_name or back["name"]
        rn = cmux(["workspace-action", "--action", "rename",
                   "--workspace", ws_id, "--title", proj_name])
        if rn.returncode != 0:
            print("WARN: rename rc=%d stderr=%s — tab not renamed to %r (non-fatal)"
                  % (rn.returncode, rn.stderr.strip()[:200], proj_name))
        else:
            print("tab renamed: sidebar name -> %r (workspace %s)" % (proj_name, ws_id))
    registry_lib.audit_append(
        {"event": "launch", "project_uuid": project_uuid, "mode": mode,
         "workspace_id": ws_id, "delivered": delivered, "trust_gate": trust_gate,
         "description_tag_ok": tag_ok, "window_name": window_name}, home=REG_HOME)
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
    reentry, reentry_note, reentry_notes = resolve_reentry(root, row)
    print("reentry: %s" % (reentry or "(none)"))
    print("reentry source: %s" % reentry_note)
    unread = [n for n in reentry_notes if not n["consumed"]]
    if len(unread) > 1:
        print("owned reentry notes: %d unread of %d owned — MORE THAN ONE window left work "
              "behind; the newest is delivered, the rest are listed here and none is hidden:"
              % (len(unread), len(reentry_notes)))
        for n in unread:
            print("  UNREAD %s  (%s)" % (n["path"], n["evidence"]))

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

    if matches and FOCUS_EXISTING:
        w, why = pick_most_recent(matches)
        ws_id = w.get("id")
        if DRY:
            print("DRY RUN — decision: FOCUS existing workspace %s (matched by %s; %d match%s "
                  "of %d workspaces; --focus-existing given). No cmux mutation, no registry write."
                  % (ws_id, why, len(matches), "" if len(matches) == 1 else "es", len(workspaces)))
            return 0
        out = cmux(["workspace", "select", ws_id])
        if out.returncode != 0:
            refuse("workspace select %s failed rc=%d stderr=%s"
                   % (ws_id, out.returncode, out.stderr.strip()[:300]))
        print("focused existing workspace %s — no second workspace created "
              "(--focus-existing)" % ws_id)
        if len(matches) > 1:
            print("NOTE: %d workspaces match this project — focused the most recently active; "
                  "the others were left untouched: %s"
                  % (len(matches), ", ".join(m[0].get("id", "?") for m in matches if m[0].get("id") != ws_id)))
        print("matched by: %s" % why)
        # Trust-gate check on the focused screen too — report, never assume.
        screen = read_screen(ws_id)
        trust = bool(screen) and TRUST_GATE_TEXT in screen
        if trust:
            print("TRUST GATE DETECTED on focused workspace ('%s') — the session is waiting on "
                  "the safety prompt; nothing is delivered past it" % TRUST_GATE_TEXT)
        # A focused window keeps the sidebar name it already carries when that
        # name is this project's (possibly labelled) name — Rule 3 makes second
        # windows normal, and renaming one back to the bare stem erases D12.
        cur = (w.get("custom_title") or "").strip() if w.get("has_custom_title") else ""
        keep = cur if cur.casefold().startswith(name.casefold()) else None
        finalize(PROJECT, root, "focus", ws_id, desc, None, trust, keep)
        return 0

    if matches:
        print("ALREADY OPEN in %d workspace%s — opening an ADDITIONAL window on the SAME "
              "project (Zee's Rule 3, 2026-08-19: a repeat open is a new tab, never a "
              "question and never a jump)."
              % (len(matches), "" if len(matches) == 1 else "s"))
        for w, why in matches:
            print("  already open: %s (matched by %s)" % (w.get("id"), why))
        print("  to jump to one of those instead, re-run with --focus-existing.")

    # ---- step 4: CREATE the window ----------------------------------------
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
        print("command: default claude delivery — reentry cat wrapped in BEGIN/END markers, "
              "then `%s %s` with a prompt naming the reentry path"
              % (CLAUDE_BIN, CLAUDE_FLAGS))

    # Sidebar name for THIS window. Several windows on one project is normal
    # under Rule 3, so a name already in use is numbered rather than repeated.
    taken = live_sidebar_names(workspaces)
    win_name = window_name_for(name, LABEL, taken)
    if win_name != name:
        print("window name: %r (%s)"
              % (win_name, "from --label" if LABEL
                 else "AUTO-NUMBERED — %r is already a live sidebar name; pass --label <text> "
                      "for a meaningful one (D12)" % name))

    if DRY:
        print("DRY RUN — decision: CREATE workspace --name %r --description %r --cwd %r "
              "--command <%d chars%s>. No cmux mutation, no registry write."
              % (win_name, desc, root, len(command), "; marker " + needle if needle else ""))
        return 0

    count_before = len(workspaces)
    # Which workspaces ALREADY carry this key tag. Under Rule 3 the tag is no
    # longer unique, so the join-back below must find the one that is NEW —
    # taking the last tagged workspace would happily return a sibling window.
    tagged_before = {w.get("id") for w in workspaces if key_tag in (w.get("description") or "")}
    out = cmux(["workspace", "create", "--name", win_name, "--description", desc,
                "--cwd", root, "--command", command], timeout=30)
    if out.returncode != 0:
        refuse("workspace create failed rc=%d stderr=%s" % (out.returncode, out.stderr.strip()[:300]))

    # Join back to the created workspace by the [key:<uuid>] tag (durable),
    # never by title. Brief retry: the list may lag creation.
    ws_id = None
    for _ in range(5):
        time.sleep(1)
        listed = list_workspaces()
        tagged = [w for w in listed
                  if key_tag in (w.get("description") or "") and w.get("id") not in tagged_before]
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
        finalize(PROJECT, root, "create", ws_id, desc, False, trust, win_name)
        return 3
    if delivered:
        print("DELIVERED — reentry content verified on screen via BEGIN marker")
        finalize(PROJECT, root, "create", ws_id, desc, True, trust, win_name)
        return 0
    print("DELIVERY NOT-VERIFIED — marker %r absent after 2 read-screen attempts%s"
          % (needle, "; trust gate present (likely cause)" if trust else ""))
    finalize(PROJECT, root, "create", ws_id, desc, False, trust, win_name)
    return 3


sys.exit(main())
PYEOF
