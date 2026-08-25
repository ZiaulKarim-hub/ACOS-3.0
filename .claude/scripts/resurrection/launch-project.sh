#!/bin/bash
# launch-project.sh — open-a-window (ACOS Resurrection Protocol).
#
# Interface:
#   launch-project.sh --project <uuid> [--dry-run] [--command-override <cmd>]
#                     [--focus-existing] [--tab] [--label <text>]
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
# --tab (Zee, 2026-08-25 — OPT-IN, brief item 2). A second open normally makes
# a second WORKSPACE. With --tab it makes a second TAB inside the workspace
# this project is already open in, so one project keeps one workspace however
# many windows it has. The default is unchanged and stays the workspace route:
# --tab is only ever reached because the caller asked for it by name.
#
# The tab route is three cmux calls, all verified live on 2026-08-25:
#   rpc surface.create {"workspace_id": ...}  -> RETURNS the new surface id, so
#                                               nothing has to be diffed for
#                                               afterwards (the workspace route
#                                               must, and that diff is exactly
#                                               what cannot work here: no new
#                                               workspace appears);
#   respawn-pane --surface <id> --command     -> argv delivery, unchanged
#                                               contract; MEASURED to inherit
#                                               the workspace cwd, so the tab
#                                               starts in the project folder;
#   rename-tab   --surface <id> <title>       -> D12 naming, on the TAB. The
#                                               WORKSPACE is never renamed by
#                                               this route: its name belongs to
#                                               the project, not to one tab.
#
# Delivery is read back with read-screen --surface. WITHOUT --surface a
# workspace-scoped read returns only the SELECTED tab, which after
# surface.create is not necessarily the new one — so the flag is load-bearing,
# not decoration.
#
# A --tab open with NOWHERE to put the tab (the project is not open anywhere)
# falls back to the workspace route and SAYS SO. The first window of a project
# has to be a workspace; refusing would turn a clear "open 20" into an error.
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
LP_TAB=0
LP_LABEL=""
while [ $# -gt 0 ]; do
  case "$1" in
    --project)          LP_PROJECT="${2:-}"; shift 2 ;;
    --dry-run)          LP_DRY=1; shift ;;
    --command-override) LP_OVERRIDE="${2:-}"; shift 2 ;;
    --focus-existing)   LP_FOCUS=1; shift ;;
    --tab)              LP_TAB=1; shift ;;
    --label)            LP_LABEL="${2:-}"; shift 2 ;;
    *) echo "REFUSED — unknown argument: $1" >&2; exit 2 ;;
  esac
done
if [ "$LP_FOCUS" = "1" ] && [ "$LP_TAB" = "1" ]; then
  echo "REFUSED — --focus-existing and --tab ask for opposite things: one JUMPS to the" >&2
  echo "window already open, the other OPENS A NEW TAB beside it. Pick one." >&2
  exit 2
fi
export LP_PROJECT LP_DRY LP_OVERRIDE LP_FOCUS LP_TAB LP_LABEL
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
TAB_ROUTE = os.environ.get("LP_TAB", "0") == "1"
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


def read_screen(ws_id, surface_id=None):
    """read-screen with scrollback (a long reentry scrolls BEGIN off-screen).

    --surface is NOT optional for a tab. MEASURED on a 2-surface workspace:
    the workspace-scoped read md5-matched ONE surface exactly and did not match
    the other, so a workspace-level read of a tab route reads whichever tab
    happens to be selected — which after surface.create is not reliably the new
    one. Reading the wrong tab would report a delivery that never happened.
    """
    base = ["read-screen", "--workspace", ws_id]
    if surface_id:
        base += ["--surface", surface_id]
    out = cmux(base + ["--scrollback"])
    if out.returncode != 0:
        out = cmux(base)  # older builds: no --scrollback
    if out.returncode != 0:
        return None
    return out.stdout


def list_surfaces(ws_id):
    """The tabs currently in one workspace — the LIVENESS list for tab claims.

    Loud on failure rather than empty: an empty list and an unreachable cmux
    look identical to a caller, and one of them means every tab claim is dead.
    """
    out = cmux(["rpc", "surface.list", json.dumps({"workspace_id": ws_id})])
    if out.returncode != 0:
        return None
    try:
        return json.loads(out.stdout).get("surfaces", [])
    except (json.JSONDecodeError, ValueError):
        return None


def wrap_for_tab(command):
    """Re-run a command under the user's LOGIN shell, for the tab route only.

    MEASURED 2026-08-25, and the reason the first live tab launch died:

      workspace create --command  ->  $0 is `-/bin/zsh`, and PATH is the full
                                      login PATH — /Users/zee/.nvm/.../bin
                                      included, so `node` resolves.
      respawn-pane   --command    ->  $0 is `-/bin/sh`, and PATH is
                                      cmux-shims + /usr/bin:/bin:/usr/sbin:/sbin
                                      ONLY. No node.

    `claude` is a Node CLI. Under the second PATH it starts, fails to find
    node, exits — and a tab whose process exits CLOSES. The symptom was not a
    missing binary but a vanished tab: `rename-tab` then said "Tab not found"
    and read-screen said "Surface is not a terminal", both of them true, and
    neither of them naming the cause.

    So the tab route re-enters a login shell. -l reads the login files, -i
    reads the interactive ones, and PATH is set in either depending on the
    user's setup, so both are needed and neither is a guess. The command
    itself is passed as ONE shell-quoted argument, which keeps the argv
    delivery contract intact — the prompt is still an argument, never typed.

    The WORKSPACE route is untouched: cmux already gives it a login shell.
    """
    shell = os.environ.get("SHELL") or "/bin/zsh"
    return "exec %s -lic %s" % (shell, shlex.quote(command))


def create_tab(ws_id):
    """Make a new tab in an EXISTING workspace and return its id.

    The id comes back in surface.create's own reply, so the join-back diff the
    workspace route needs does not exist here at all. That matters: the diff
    works by spotting a NEW workspace carrying the key tag, and a tab creates
    no workspace, so under the tab route that diff would find nothing and
    refuse a window that had in fact been created.

    `workspace_id` is the param name, VERIFIED 2026-08-25 — passing `workspace`
    is accepted silently and creates the tab in the FOCUSED workspace instead,
    which is the wrong project. It is checked on the way out for that reason.
    """
    out = cmux(["rpc", "surface.create",
                json.dumps({"workspace_id": ws_id, "type": "terminal"})])
    if out.returncode != 0:
        refuse("rpc surface.create rc=%d stderr=%s" % (out.returncode, out.stderr.strip()[:300]))
    try:
        payload = json.loads(out.stdout)
    except (json.JSONDecodeError, ValueError):
        refuse("rpc surface.create returned unparseable JSON: %r" % out.stdout[:200])
    sf_id = payload.get("surface_id")
    landed = payload.get("workspace_id")
    if not sf_id:
        refuse("rpc surface.create returned no surface_id: %r" % out.stdout[:200])
    if landed and str(landed).casefold() != str(ws_id).casefold():
        cmux(["close-surface", "--workspace", landed, "--surface", sf_id])
        refuse("surface.create put the tab in workspace %s, not the %s asked for — the tab "
               "was closed again and NOTHING was opened. cmux ignored the target; do not "
               "retry blind." % (landed, ws_id))
    return sf_id


def claim_windows(project_uuid, ws_id, sf_id, win_name, host):
    """Record the new TAB, and the workspace window it was opened beside.

    Why both. D14 says a close parks the row only when the LAST window closes,
    and it answers that from the window manifest. Under the tab route the
    manifest must therefore know about the tab, or closing it would park a
    project whose original window is still open and working.

    The HOST is claimed too, and that is not an invention: workspace_matches
    just PROVED this workspace is a live window on this project, by the same
    evidence the focus route acts on. Claiming records what was verified. A
    host that already holds a claim keeps it — claim_window is idempotent and
    preserves claimed_at, so an existing window is never re-dated or re-labelled
    into looking new.

    Non-fatal by design. A manifest that cannot be written is a D14 degradation
    (a later close may park early), not a reason to fail a window that opened.
    """
    try:
        sys.path.insert(0, LIB_DIR)
        import windows_lib
    except ImportError as exc:
        print("WARN: windows_lib unimportable (%s) — the tab opened, but D14 cannot see it; "
              "closing it may park the project while the other window is still open" % exc)
        return
    try:
        windows_lib.claim_window(project_uuid, ws_id, label=win_name,
                                 home=REG_HOME, surface_id=sf_id)
        print("window manifest: claimed tab %s (key %s)"
              % (sf_id, windows_lib.window_key(ws_id, sf_id)))
        existing = {windows_lib.claim_key(c).casefold()
                    for c in windows_lib.all_claims(project_uuid, home=REG_HOME)}
        if str(ws_id).casefold() not in existing:
            host_name = (host.get("custom_title") or "").strip() if host.get("has_custom_title") else ""
            windows_lib.claim_window(project_uuid, ws_id, label=host_name or None,
                                     home=REG_HOME)
            print("window manifest: also claimed the HOST window %s — it was verified open on "
                  "this project but held no claim, and D14 must be able to see it" % ws_id)
    except (OSError, ValueError) as exc:
        print("WARN: window manifest not written (%s) — the tab opened; D14 may park early" % exc)


def finalize(project_uuid, root, mode, ws_id, desc, delivered, trust_gate, window_name=None,
             surface_id=None, tag_present=False):
    """Step 6 — only after a successful focus-or-launch: activate the row,
    write the durable [key:<uuid>] description tag, append the audit event.

    A TAB differs in exactly two places, and both follow from what a tab IS:
      * the description is written only when the key tag is not already there.
        A tab shares its workspace's description with every sibling, so
        rewriting it on every tab open would keep overwriting one project's
        next_action with another open's — same text today, noise tomorrow.
      * the TAB is renamed, never the workspace. The workspace name belongs to
        the project; renaming it to this one tab's D12 name would rename the
        project in the sidebar every time a second window opened.
    """
    row = registry_lib.upsert_row(
        {"project_uuid": project_uuid, "root": root, "status": "active"}, home=REG_HOME)
    back = registry_lib.load_row(project_uuid, home=REG_HOME)
    if back is None or back["status"] != "active":
        refuse("registry read-back failed: row not active after launch upsert")
    print("registry: status -> active (read back: %s)" % back["status"])

    tag_ok = None
    if not SKIP_CMUX:
        if surface_id and tag_present:
            tag_ok = True
            print("description tag: left alone — workspace %s already carries [key:%s], and "
                  "every tab in it shares that one description" % (ws_id, project_uuid))
        else:
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
        if surface_id:
            rn = cmux(["rename-tab", "--workspace", ws_id, "--surface", surface_id, proj_name])
            where = "tab %s in workspace %s" % (surface_id, ws_id)
        else:
            rn = cmux(["workspace-action", "--action", "rename",
                       "--workspace", ws_id, "--title", proj_name])
            where = "workspace %s" % ws_id
        if rn.returncode != 0:
            print("WARN: rename rc=%d stderr=%s — %s not renamed to %r (non-fatal)"
                  % (rn.returncode, rn.stderr.strip()[:200], where, proj_name))
        else:
            print("renamed: %s -> %r" % (where, proj_name))
    registry_lib.audit_append(
        {"event": "launch", "project_uuid": project_uuid, "mode": mode,
         "workspace_id": ws_id, "surface_id": surface_id, "delivered": delivered,
         "trust_gate": trust_gate, "description_tag_ok": tag_ok,
         "window_name": window_name}, home=REG_HOME)
    print("audit: launch event appended (mode=%s workspace=%s%s)"
          % (mode, ws_id, " tab=%s" % surface_id if surface_id else ""))


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
        if TAB_ROUTE:
            print("SANDBOX --tab: the tab route needs workspace.list to know WHICH workspace "
                  "to tab into, and there is none here. A real run would put the tab in the "
                  "matching workspace, or fall back to creating one if the project is open "
                  "nowhere.")
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
              "project (Zee's Rule 3, 2026-08-19: a repeat open is a new window, never a "
              "question and never a jump)."
              % (len(matches), "" if len(matches) == 1 else "s"))
        for w, why in matches:
            print("  already open: %s (matched by %s)" % (w.get("id"), why))
        print("  route: %s" % ("TAB — the new window goes INSIDE workspace %s (--tab)"
                               % pick_most_recent(matches)[0].get("id") if TAB_ROUTE
                               else "WORKSPACE — a second workspace (the default; pass --tab "
                                    "for a tab inside the one already open)"))
        print("  to jump to one of those instead, re-run with --focus-existing.")
    elif TAB_ROUTE:
        print("--tab was asked for, but this project is open in NO workspace, so there is "
              "nowhere to put a tab. Falling back to the WORKSPACE route — the first window "
              "of a project has to be a workspace. Re-run with --tab once it is open and the "
              "second window will be a tab inside this one.")

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

    if DRY and TAB_ROUTE and matches:
        host = pick_most_recent(matches)[0]
        print("DRY RUN — decision: CREATE TAB in workspace %s (matched by %s) --command "
              "<%d chars%s>, then rename the tab to %r. The workspace is NOT renamed and no "
              "second workspace is created. No cmux mutation, no registry write."
              % (host.get("id"), pick_most_recent(matches)[1], len(command),
                 "; marker " + needle if needle else "", win_name))
        return 0
    if DRY:
        print("DRY RUN — decision: CREATE workspace --name %r --description %r --cwd %r "
              "--command <%d chars%s>. No cmux mutation, no registry write."
              % (win_name, desc, root, len(command), "; marker " + needle if needle else ""))
        return 0

    # ---- step 4b: the TAB route (opt-in) ----------------------------------
    if TAB_ROUTE and matches:
        host, why = pick_most_recent(matches)
        ws_id = host.get("id")
        tag_present = key_tag in (host.get("description") or "")
        before = list_surfaces(ws_id)
        sf_id = create_tab(ws_id)
        print("created tab %s in workspace %s (matched by %s; tabs %s -> %d)"
              % (sf_id, ws_id, why,
                 len(before) if before is not None else "?", len(list_surfaces(ws_id) or [])))

        tab_command = wrap_for_tab(command)
        out = cmux(["respawn-pane", "--workspace", ws_id, "--surface", sf_id,
                    "--command", tab_command], timeout=30)
        if out.returncode != 0:
            cmux(["close-surface", "--workspace", ws_id, "--surface", sf_id])
            refuse("respawn-pane failed rc=%d stderr=%s — the empty tab was closed again, so "
                   "nothing was left half-open" % (out.returncode, out.stderr.strip()[:300]))
        print("command delivered by argv to tab %s (respawn-pane rc=0; re-entered through "
              "%s -lic so the tab gets the same login PATH the workspace route gets)"
              % (sf_id, os.environ.get("SHELL") or "/bin/zsh"))

        # STRUCTURED proof, read BEFORE the screen proof and independent of it:
        # surface.list reports the tab's own initial_command, so the command
        # being ON the tab is verifiable without racing a repaint. It proves
        # cmux accepted the command, NOT that anything ran — the screen check
        # below is still what proves delivery, and neither is skipped.
        cmd_on_tab = None
        after = list_surfaces(ws_id) or []
        for sfc in after:
            if str(sfc.get("id", "")).casefold() == str(sf_id).casefold():
                cmd_on_tab = sfc.get("initial_command") or ""
        if cmd_on_tab is None:
            print("tab command round-trip: TAB IS GONE — surface.list no longer lists %s. A "
                  "tab closes when its process EXITS, so this means the command ran and died "
                  "rather than that nothing was created. Read the command back by hand before "
                  "re-running; a repeat open will only kill another tab." % sf_id)
        elif needle and needle in cmd_on_tab:
            print("tab command round-trip: OK — the tab's own initial_command carries the "
                  "marker contract")
        else:
            print("tab command round-trip: initial_command is %d chars%s"
                  % (len(cmd_on_tab), "" if needle else " (no marker contract to check)"))

        delivered = False
        trust = False
        for attempt in (1, 2):
            time.sleep(2)
            screen = read_screen(ws_id, sf_id)
            if screen is None:
                print("read-screen attempt %d: FAILED (no output)" % attempt)
                continue
            trust = trust or (TRUST_GATE_TEXT in screen)
            if needle and needle in screen:
                delivered = True
                print("read-screen attempt %d: BEGIN marker %r FOUND on tab %s"
                      % (attempt, needle, sf_id))
                break
            print("read-screen attempt %d: %s not found yet on tab %s"
                  % (attempt, ("marker %r" % needle) if needle else "(no marker contract)", sf_id))
        if trust:
            print("TRUST GATE DETECTED ('%s') — the tab LOOKS launched but the prompt is NOT "
                  "delivered past the safety check; act on the gate before trusting delivery"
                  % TRUST_GATE_TEXT)

        claim_windows(PROJECT, ws_id, sf_id, win_name, host)

        if needle is None:
            print("DELIVERY NOT-VERIFIED — --command-override provides no marker contract; "
                  "verify delivery yourself (loud by design, never assumed)")
            finalize(PROJECT, root, "create-tab", ws_id, desc, False, trust, win_name,
                     surface_id=sf_id, tag_present=tag_present)
            return 3
        if delivered:
            print("DELIVERED — reentry content verified on tab %s via BEGIN marker" % sf_id)
            finalize(PROJECT, root, "create-tab", ws_id, desc, True, trust, win_name,
                     surface_id=sf_id, tag_present=tag_present)
            return 0
        print("DELIVERY NOT-VERIFIED — marker %r absent from tab %s after 2 read-screen "
              "attempts. The tab EXISTS and carries the command (see the round-trip above); "
              "what is unproven is that its output reached the screen in time." % (needle, sf_id))
        finalize(PROJECT, root, "create-tab", ws_id, desc, False, trust, win_name,
                 surface_id=sf_id, tag_present=tag_present)
        return 3

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
