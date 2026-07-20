#!/bin/bash
# enroll-project.sh — SessionStart enrollment hook (ACOS Resurrection Protocol).
#
# Reads the SessionStart hook JSON ({session_id, cwd, ...}) on stdin and, when
# cwd is a real project root (marker gate), enrolls it in the durable registry:
#   * marker gate: <root>/.acos/ OR <root>/CLAUDE.md OR <root>/memory/handoffs/
#     (root = cwd itself; v1 never walks up, never scans the filesystem)
#   * identity is SIDEBAR-NAME FIRST: a cmux session in a workspace with a
#     human-set custom_title enrolls the (root, sidebar-name) row — several
#     projects share one root. Non-cmux / unnamed sessions use the folder-level
#     path: project_uuid minted ONCE -> <root>/.acos/project-id (git-ignored)
#   * row upserted via registry_lib.py — every field derived, none hand-typed
#   * realpath(cwd) == row.root asserted; mismatch logs LOUDLY (audit + stderr)
#     but NEVER blocks session start (protects the f639310 project-scoped fix)
#
# Contract: O(1)-fast, fail-open — ANY error exits 0 after a best-effort stderr
# note. This script never blocks a session and never touches the token-monitor
# daemon state dir. Registry writes go only to ~/.acos/registry.d/ and
# ~/.acos/registry-audit.jsonl (or $ACOS_REGISTRY_HOME for sandboxed tests).

ENROLL_HOOK_PAYLOAD="$(cat 2>/dev/null || true)"
export ENROLL_HOOK_PAYLOAD
ENROLL_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)"
export ENROLL_LIB_DIR

/usr/bin/python3 - <<'PY' || true
"""SessionStart enrollment body. Constraints: system Python 3.9.6, stdlib only,
JSON only. Fail-open: every exception path prints one stderr note and exits 0."""
import json
import os
import re
import subprocess
import sys
import tempfile
import uuid


def _note(msg):
    sys.stderr.write("[enroll-project] %s\n" % msg)


def _atomic_create_once(path, data):
    """Create `path` with `data` exactly once, crash-safe and race-safe.

    mkstemp(dir=target's own dir) -> write -> fsync -> os.link(tmp, target)
    -> fsync(dir). os.link fails with EEXIST if a concurrent enroller won the
    race, so the file is minted exactly once; the loser reads the winner's
    value. os.replace is deliberately NOT used here — it would clobber a
    concurrent winner, violating mint-once.
    Returns True if this call created the file.
    """
    directory = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".pid-", suffix=".part")
    created = False
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)
    try:
        os.link(tmp, path)
        created = True
    except FileExistsError:
        pass
    finally:
        os.unlink(tmp)
    dir_fd = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)
    return created


def _read_project_id(path):
    """Return the persisted uuid4 if the file holds a valid one, else None."""
    try:
        with open(path, "r") as fh:
            text = fh.read().strip()
        return str(uuid.UUID(text))
    except (OSError, ValueError):
        return None


def _atomic_replace(path, data):
    """Atomically REPLACE `path` (mkstemp -> fsync -> os.replace -> fsync(dir)).

    Used only to heal a project-id file that points at a tombstoned row —
    everywhere else mint-once (_atomic_create_once) still applies.
    """
    directory = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".pid-", suffix=".part")
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)
    os.replace(tmp, path)
    dir_fd = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)


def _workspace_identity():
    """(sidebar_name, tagged_row_uuid) of this session's workspace — either None.

    CMUX_WORKSPACE_ID is inherited env and can be SET-BUT-DEAD (cmux restarts
    while the process keeps the stale id) — the id must appear in a LIVE
    workspace.list before it is trusted. Only the human-set custom_title
    (has_custom_title=true) counts; the dynamic `title` is banned from lookup
    (programs rewrite it live). The [key:<uuid>] description tag is captured
    too — it outranks the name (a renamed tab must not mint a duplicate row).
    Fail-open: any error -> (None, None) (folder-level fallback).
    """
    ws_id = os.environ.get("CMUX_WORKSPACE_ID")
    if not ws_id:
        return None, None
    try:
        out = subprocess.run(
            ["/Applications/cmux.app/Contents/Resources/bin/cmux", "rpc", "workspace.list"],
            capture_output=True, text=True, timeout=5)
        if out.returncode != 0:
            return None, None
        payload = json.loads(out.stdout)
    except (OSError, subprocess.TimeoutExpired, ValueError):
        return None, None
    for ws in payload.get("workspaces", []):
        if ws.get("id") == ws_id:
            name = None
            if ws.get("has_custom_title") and (ws.get("custom_title") or "").strip():
                name = ws["custom_title"].strip()
            m = re.search(r"\[key:([0-9a-fA-F-]{36})\]", ws.get("description") or "")
            return name, (m.group(1).lower() if m else None)
    _note("CMUX_WORKSPACE_ID %s not in workspace.list — set-but-dead env; folder-level fallback" % ws_id)
    return None, None


def _gitignore_covers(root):
    """True if project-id is already git-ignored by either .gitignore layer.

    Literal-line check only (no git invocation — must stay O(1) and dependency
    free): <root>/.gitignore covering .acos or .acos/project-id, or
    <root>/.acos/.gitignore covering project-id.
    """
    root_covers = {".acos", ".acos/", "/.acos", "/.acos/", ".acos/*",
                   ".acos/project-id", "/.acos/project-id"}
    acos_covers = {"project-id", "/project-id", "*"}
    for path, covers in ((os.path.join(root, ".gitignore"), root_covers),
                         (os.path.join(root, ".acos", ".gitignore"), acos_covers)):
        try:
            with open(path, "r") as fh:
                lines = {ln.strip() for ln in fh}
        except OSError:
            continue
        if lines & covers:
            return True
    return False


def _append_gitignore_line(path, line):
    """Append one line via O_APPEND + a single os.write (same discipline as the
    audit log): concurrent appenders cannot interleave bytes within the line."""
    payload = (line + "\n").encode("utf-8")
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
    try:
        os.write(fd, payload)
    finally:
        os.close(fd)


def _git_facts(root):
    """Captured git attributes {branch, head, dirty_count} — NEVER identity.

    Returns None when root is not a git repo or any probe fails/times out
    (nullable attribute per the registry schema). Absolute binary: /usr/bin/git.
    """
    if not os.path.exists(os.path.join(root, ".git")):
        return None

    def probe(args):
        return subprocess.run(
            ["/usr/bin/git", "-C", root] + args,
            capture_output=True, text=True, timeout=5,
        )
    try:
        branch = probe(["rev-parse", "--abbrev-ref", "HEAD"])
        head = probe(["rev-parse", "HEAD"])
        status = probe(["status", "--porcelain"])
        if branch.returncode or head.returncode or status.returncode:
            return None
        return {
            "branch": branch.stdout.strip(),
            "head": head.stdout.strip(),
            "dirty_count": len([ln for ln in status.stdout.splitlines() if ln.strip()]),
        }
    except (subprocess.TimeoutExpired, OSError):
        return None


def main():
    try:
        payload = json.loads(os.environ.get("ENROLL_HOOK_PAYLOAD", ""))
        if not isinstance(payload, dict):
            raise ValueError("hook payload is not a JSON object")
    except (json.JSONDecodeError, ValueError) as exc:
        _note("unparseable hook payload (%s) — skipping enrollment" % exc)
        return 0

    cwd = payload.get("cwd")
    session_id = payload.get("session_id")
    if not cwd or not os.path.isdir(cwd):
        _note("no usable cwd in hook payload — skipping enrollment")
        return 0
    root = os.path.abspath(cwd)

    # Marker gate — root is cwd itself; no walk-up, no filesystem scan (v1).
    if not (os.path.isdir(os.path.join(root, ".acos"))
            or os.path.isfile(os.path.join(root, "CLAUDE.md"))
            or os.path.isdir(os.path.join(root, "memory", "handoffs"))):
        return 0

    lib_dir = os.environ.get("ENROLL_LIB_DIR", "")
    sys.path.insert(0, lib_dir)
    import registry_lib

    # $ACOS_REGISTRY_HOME sandboxes the registry side for tests; unset in
    # production so registry_lib resolves the real ~.
    home = os.environ.get("ACOS_REGISTRY_HOME") or None

    # Identity — SIDEBAR-NAME FIRST (several projects share one root):
    #   * cmux session in a NAMED workspace -> the (root, sidebar-name) row,
    #     minting a new uuid when none exists. The project-id file is NOT
    #     consulted (it is the folder-level identity only).
    #   * non-cmux / unnamed session -> folder-level path: persisted
    #     project-id, else the folder row for this exact root, else mint once.
    #     A project-id pointing at a TOMBSTONED row is healed (re-derived +
    #     rewritten) — never silently re-enrolled, never auto-revived.
    acos_dir = os.path.join(root, ".acos")
    pid_path = os.path.join(acos_dir, "project-id")
    ws_name, ws_key = _workspace_identity()

    # The workspace's [key:<uuid>] tag outranks its name: a RENAMED tab adopts
    # its tagged row (and the upsert below heals workspace_name to the new
    # name) instead of minting a duplicate. The tag is ignored when its row is
    # missing, tombstoned, or rooted elsewhere.
    tagged = None
    if ws_key:
        try:
            tagged = registry_lib.load_row(ws_key, home=home)
        except Exception:  # corrupt tagged row: fall back to name/folder paths
            tagged = None
        if tagged is not None and (
                tagged["status"] == "tombstoned"
                or tagged["root_casefold"] != os.path.realpath(root).casefold()):
            tagged = None

    if tagged is not None:
        project_uuid = tagged["project_uuid"]
    elif ws_name:
        existing = registry_lib.find_row(root, ws_name, home=home)
        if existing is not None and existing["status"] == "tombstoned":
            _note("row for (%s, %r) is tombstoned — enrollment skipped; un-tombstoning is a human act"
                  % (root, ws_name))
            registry_lib.audit_append(
                {"event": "enroll-skipped-tombstoned", "project_uuid": existing["project_uuid"],
                 "workspace_name": ws_name, "session_id": session_id}, home=home)
            return 0
        project_uuid = existing["project_uuid"] if existing else str(uuid.uuid4())
    else:
        project_uuid = _read_project_id(pid_path)
        stale_pointer = None
        if project_uuid is not None:
            pointed = registry_lib.load_row(project_uuid, home=home)
            if pointed is not None and pointed["status"] == "tombstoned":
                stale_pointer = project_uuid
                project_uuid = None
        if project_uuid is None:
            existing = registry_lib.find_by_root(root, home=home)
            if existing is not None and existing["status"] != "tombstoned":
                project_uuid = existing["project_uuid"]
            else:
                project_uuid = str(uuid.uuid4())
            os.makedirs(acos_dir, exist_ok=True)
            if stale_pointer:
                _atomic_replace(pid_path, (project_uuid + "\n").encode("utf-8"))
                registry_lib.audit_append(
                    {"event": "project-id-healed", "old_project_uuid": stale_pointer,
                     "project_uuid": project_uuid, "root": root, "session_id": session_id},
                    home=home)
                _note("project-id healed -> %s (was tombstoned row %s)" % (project_uuid, stale_pointer))
            elif not _atomic_create_once(pid_path, (project_uuid + "\n").encode("utf-8")):
                project_uuid = _read_project_id(pid_path) or project_uuid  # lost race

    if not _gitignore_covers(root):
        os.makedirs(acos_dir, exist_ok=True)
        _append_gitignore_line(os.path.join(acos_dir, ".gitignore"), "project-id")

    fields = {"project_uuid": project_uuid, "root": root}
    if ws_name:
        fields["workspace_name"] = ws_name
    if session_id:
        fields["last_session_id_hint"] = str(session_id)
    git = _git_facts(root)
    if git is not None:
        fields["git"] = git
    # Revive-on-work: a session STARTING here means the project is being worked
    # on, so completed/parked rows flip back to active (status is derived from
    # behavior, never hand-maintained). Tombstoned is a HUMAN act — never
    # auto-revived. Pairs with /acos-complete's auto-finish book sync.
    prior = registry_lib.load_row(project_uuid, home=home)
    revived_from = None
    if prior is not None and prior["status"] in ("completed", "parked"):
        fields["status"] = "active"
        revived_from = prior["status"]
    row = registry_lib.upsert_row(fields, home=home)
    if revived_from:
        registry_lib.audit_append(
            {"event": "revived-by-session", "project_uuid": project_uuid,
             "from_status": revived_from, "session_id": session_id},
            home=home,
        )

    # cwd==root assertion (risk #7 / f639310): loud, never blocking.
    real_cwd = os.path.realpath(cwd)
    if real_cwd != row["root"]:
        msg = ("ROOT MISMATCH: realpath(cwd)=%r != registry row.root=%r "
               "(project_uuid=%s) — enrollment recorded, session NOT blocked; "
               "investigate before resuming cross-project work" % (real_cwd, row["root"], project_uuid))
        _note(msg)
        registry_lib.audit_append(
            {"event": "enroll-root-mismatch", "project_uuid": project_uuid,
             "cwd_realpath": real_cwd, "row_root": row["root"],
             "session_id": session_id},
            home=home,
        )
    return 0


try:
    sys.exit(main())
except SystemExit:
    raise
except BaseException as exc:  # fail-open: enrollment must never block a session
    _note("fail-open: %s: %s" % (type(exc).__name__, exc))
    sys.exit(0)
PY
exit 0
