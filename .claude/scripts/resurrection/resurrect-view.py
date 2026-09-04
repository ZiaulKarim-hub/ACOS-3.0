#!/usr/bin/env python3
"""resurrect-view.py — the Resurrection Protocol book, computed FRESH per request.

SLICE-RES-30. The way IN (Demo 1 + Demo 3): an honest menu over the registry.

Hard rules honored here (design.md Vision 1/3 + house rules):
  * The book is computed fresh on EVERY invocation. This script NEVER writes a
    cache, never persists a rendered file, and never mutates the registry or
    the audit log (read-only by construction: no upsert/tombstone/find_by_root
    calls — find_by_root can heal-write, so it is deliberately not used).
  * Liveness is computed live, never a stored flag:
      - claude processes enumerated via pgrep -f (absolute claude install path
        + the cmux cli-shim wrapper), verified against clean argv from ps
        (basename of argv[0] must be claude/claude.exe), one live session per
        distinct --session-id (helper procs — daemon/bg-spare — carry none);
      - each PID's cwd via `lsof -p <pids> -a -d cwd -Fn`, joined to registry
        roots by realpath().casefold();
      - cmux workspaces via `cmux rpc workspace.list`, joined to rows by a
        3-pass claim (each workspace joins AT MOST one row): [key:<uuid>]
        description tag first, then the human-set SIDEBAR name (custom_title,
        has_custom_title=true, cwd-guarded), then folder cwd for folder-level
        rows. NEVER the dynamic `title` (Claude rewrites it live; display
        only). Unclaimed workspaces render as UNMATCHED — never dropped.
  * Tiers: OPEN NOW / RECENT / COLD (>30 days) / NO HANDOFF / ARCHIVED
    (tombstoned + completed). Rows that fail a link check render BROKEN with
    the reason — never hidden, never dropped. An unreadable row FILE still
    renders (BROKEN ROWS section). Dirty is a COUNT. No green, no checkmark,
    no health stamp of any kind — facts only; red/amber only.
  * Every capped list prints "listed N of M".

Interface:
  resurrect-view.py [--json] [--home <override>] [--no-cmux] [--no-procs]
                    [--color {auto,always,never}]

stdlib only, python 3.9. Registry access only via registry_lib.
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.parse
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import registry_lib  # noqa: E402

CLAUDE_BIN = "/Users/zee/.claude/local/claude"
CMUX_BIN = "/Applications/cmux.app/Contents/Resources/bin/cmux"

# pgrep -f patterns: the absolute claude install tree + the cmux wrapper shim.
PGREP_PATTERNS = (
    r"/Users/zee/\.claude/local/.*claude",
    r"cmux-cli-shims/.*/claude",
)

TIER_ORDER = ("OPEN NOW", "RECENT", "COLD", "NO HANDOFF", "ARCHIVED")
COLD_DAYS = 30
AMBER_DAYS = 7
WS_LIST_CAP = 3

RED = "\x1b[31m"
AMBER = "\x1b[33m"
BOLD = "\x1b[1m"
DIM = "\x1b[2m"
RESET = "\x1b[0m"


def _run(cmd, timeout):
    """Run argv (list form, no shell), capture text. Returns (rc, out, err)."""
    try:
        p = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout
        )
        return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")
    except subprocess.TimeoutExpired:
        return -1, "", "timeout after %ss" % timeout
    except FileNotFoundError as exc:
        return -1, "", str(exc)


def _now():
    return datetime.now(timezone.utc)


def _parse_iso(ts):
    try:
        return datetime.fromisoformat(ts)
    except (TypeError, ValueError):
        return None


def _casefold_real(path):
    return os.path.realpath(path).casefold()


def _file_url(path):
    return "file://" + urllib.parse.quote(os.path.abspath(path))


# ---------------------------------------------------------------- liveness ---

def _ancestor_pids():
    """PIDs of this process's ancestors. macOS pgrep -f silently excludes the
    caller's own ancestors (measured live 2026-07-18: the claude session
    hosting this renderer never appears in pgrep output while identical
    sibling sessions do). Without this walk, the very session you are sitting
    in undercounts its own project. Non-claude ancestors (shells etc.) are
    discarded later by the clean-argv filter."""
    pids = []
    pid = os.getpid()
    for _ in range(32):
        rc, out, _err = _run(["ps", "-o", "ppid=", "-p", str(pid)], timeout=5)
        if rc != 0 or not out.strip().isdigit():
            break
        pid = int(out.strip())
        if pid <= 1:
            break
        pids.append(pid)
    return pids


def live_claude_sessions():
    """Enumerate live claude sessions: pgrep -f candidates (+ ancestry walk,
    see _ancestor_pids) -> clean-argv verify -> dedupe by --session-id -> cwd
    via one lsof call. Returns (sessions, error) where
    sessions = [{pid, session_id, cwd, cwd_key}]."""
    pids = set()
    for pat in PGREP_PATTERNS:
        rc, out, _err = _run(["pgrep", "-f", pat], timeout=10)
        if rc == 0:
            for line in out.split():
                if line.strip().isdigit():
                    pids.add(int(line.strip()))
    pids.update(_ancestor_pids())
    pids.discard(os.getpid())
    if not pids:
        return [], None

    # Verify against clean argv (ps without env), not pgrep's env-polluted view.
    rc, out, err = _run(
        ["ps", "-o", "pid=,command=", "-p", ",".join(str(p) for p in sorted(pids))],
        timeout=10,
    )
    if rc not in (0, 1):  # ps exits 1 when some pids already died — fine
        return [], "ps failed: %s" % err.strip()
    by_session = {}
    for line in out.splitlines():
        line = line.strip()
        m = re.match(r"^(\d+)\s+(.*)$", line)
        if not m:
            continue
        pid, cmd = int(m.group(1)), m.group(2)
        argv0 = cmd.split(None, 1)[0] if cmd else ""
        base = os.path.basename(argv0)
        if base not in ("claude", "claude.exe"):
            continue  # npm/mcp children whose PATH env merely mentions claude
        sid_m = re.search(r"--session-id[ =]([0-9a-fA-F][0-9a-fA-F-]{34}[0-9a-fA-F])", cmd)
        if not sid_m:
            continue  # daemon / bg-spare helpers: real sessions carry --session-id
        sid = sid_m.group(1).lower()
        by_session.setdefault(sid, pid)  # one row per session (fork/pty wrappers dedupe)

    if not by_session:
        return [], None
    sessions = []
    pid_list = ",".join(str(p) for p in sorted(set(by_session.values())))
    rc, out, err = _run(["lsof", "-p", pid_list, "-a", "-d", "cwd", "-Fn"], timeout=15)
    cwd_by_pid = {}
    cur = None
    for line in out.splitlines():
        if line.startswith("p"):
            cur = int(line[1:])
        elif line.startswith("n") and cur is not None:
            cwd_by_pid[cur] = line[1:]
    for sid, pid in sorted(by_session.items()):
        cwd = cwd_by_pid.get(pid)
        sessions.append(
            {
                "pid": pid,
                "session_id": sid,
                "cwd": cwd,
                "cwd_key": _casefold_real(cwd) if cwd else None,
            }
        )
    return sessions, None


def cmux_workspaces():
    """cmux rpc workspace.list -> ([{id, title, ref, cwd_key, key_tag}], error).
    Titles are captured for DISPLAY only — joining never uses them."""
    rc, out, err = _run([CMUX_BIN, "rpc", "workspace.list"], timeout=10)
    if rc != 0:
        return [], "cmux workspace.list failed: %s" % (err.strip() or "rc=%d" % rc)
    try:
        payload = json.loads(out)
    except ValueError as exc:
        return [], "cmux returned unparseable JSON: %s" % exc
    result = []
    for ws in payload.get("workspaces", []):
        desc = ws.get("description") or ""
        tag = re.search(r"\[key:([0-9a-fA-F-]{36})\]", desc)
        cwd = ws.get("current_directory")
        custom = (ws.get("custom_title") or "").strip()
        result.append(
            {
                "id": ws.get("id"),
                "ref": ws.get("ref"),  # hint only; refs renumber across lifecycle
                "title": ws.get("custom_title") or ws.get("title"),  # display only
                # The human-set sidebar name — the ONLY title field allowed to
                # join (the dynamic `title` is rewritten live by programs).
                "custom_title": custom if (ws.get("has_custom_title") and custom) else None,
                "cwd": cwd,
                "cwd_key": _casefold_real(cwd) if cwd else None,
                "key_tag": tag.group(1).lower() if tag else None,
                "selected": bool(ws.get("selected")),
            }
        )
    return result, None


def git_dirty_count(root):
    """Dirty COUNT for a repo root; None when not a repo / git failed / timed out."""
    if not os.path.isdir(root):
        return None
    rc, out, _err = _run(["git", "-C", root, "status", "--porcelain"], timeout=5)
    if rc != 0:
        return None
    return sum(1 for line in out.splitlines() if line.strip())


# ------------------------------------------------------------------- facts ---

def handoff_facts(row):
    """Link-check last_close. Returns (facts dict, broken_reasons list)."""
    lc = row.get("last_close")
    if not lc:
        return {"present": False}, []
    reasons = []
    handoff_path = lc.get("handoff_path")
    reentry_path = lc.get("reentry_path")
    sha_ok = None
    if handoff_path and not os.path.isfile(handoff_path):
        reasons.append("handoff file missing: %s" % handoff_path)
    elif handoff_path and lc.get("sha256"):
        digest = hashlib.sha256()
        try:
            with open(handoff_path, "rb") as fh:
                for chunk in iter(lambda: fh.read(65536), b""):
                    digest.update(chunk)
            sha_ok = digest.hexdigest() == lc["sha256"]
            if not sha_ok:
                reasons.append("handoff sha256 mismatch (row %s… vs file %s…)"
                               % (lc["sha256"][:12], digest.hexdigest()[:12]))
        except OSError as exc:
            sha_ok = False
            reasons.append("handoff unreadable: %s" % exc)
    if reentry_path and not os.path.isfile(reentry_path):
        reasons.append("reentry file missing: %s" % reentry_path)
    reentry_exists = bool(reentry_path) and os.path.isfile(reentry_path)
    handoff_exists = bool(handoff_path) and os.path.isfile(handoff_path)
    facts = {
        "present": True,
        "at": lc.get("at"),
        "handoff_path": handoff_path,
        "reentry_path": reentry_path,
        "sha256_ok": sha_ok,
        "reentry_exists": reentry_exists,
        "handoff_exists": handoff_exists,
        # Links only ever point at files that exist RIGHT NOW — a clickable
        # link to a missing file would be its own small lie.
        "reentry_link": _file_url(reentry_path) if reentry_exists else None,
        "handoff_link": _file_url(handoff_path) if handoff_exists else None,
    }
    return facts, reasons


def claim_workspaces(rows, workspaces):
    """Global workspace->row claim pass — each workspace joins AT MOST one row.

    Strongest evidence first:
      1. the durable [key:<uuid>] description tag (explicit binding, any status);
      2. the human-set SIDEBAR name: custom_title casefold == row.workspace_name
         casefold, guarded by cwd==root when the workspace reports a cwd.
         Tombstoned rows never claim by name (a grave must not look alive);
      3. folder cwd -> the folder-level row (workspace_name null, not tombstoned).
    Anything still unclaimed is UNMATCHED — surfaced, never dropped.
    Returns (claims: ws_index -> row_uuid, drift: row_uuid -> [notes]).
    """
    claims = {}
    drift = {}
    by_uuid = {r["project_uuid"].lower(): r for r in rows}

    for i, ws in enumerate(workspaces):
        tag = ws["key_tag"]
        if tag and tag in by_uuid:
            claims[i] = tag
            row = by_uuid[tag]
            wn = row["workspace_name"]
            ct = ws["custom_title"]
            if wn and ct and ct.casefold() != wn.casefold():
                drift.setdefault(tag, []).append(
                    "sidebar name is now %r but the row says %r (joined by key tag)" % (ct, wn))

    for i, ws in enumerate(workspaces):
        if i in claims or not ws["custom_title"]:
            continue
        ct = ws["custom_title"].casefold()
        named = [r for r in rows
                 if r["workspace_name"] and r["workspace_name"].casefold() == ct
                 and r["status"] != "tombstoned"]
        exact = [r for r in named if ws["cwd_key"] is None or ws["cwd_key"] == r["root_casefold"]]
        if exact:
            claims[i] = exact[0]["project_uuid"].lower()
        else:
            for r in named:
                drift.setdefault(r["project_uuid"].lower(), []).append(
                    "a workspace named %r is open at %s — NOT this row's folder; not joined"
                    % (ws["custom_title"], ws["cwd"] or "(unknown cwd)"))

    for i, ws in enumerate(workspaces):
        if i in claims or ws["cwd_key"] is None:
            continue
        for r in rows:
            if (r["workspace_name"] is None and r["status"] != "tombstoned"
                    and r["root_casefold"] == ws["cwd_key"]):
                claims[i] = r["project_uuid"].lower()
                break
    return claims, drift


def window_label(custom_title, project_name):
    """The LABEL part of a window name (MW-B, D12).

    D12 fixes window naming as the project name plus a label — Zee's wording,
    "OKOA works *label*" — so "OKOA Works Golden East" labels as "Golden East".
    Keeping the project name as the stem is what makes the row identity
    unambiguous while several windows are open at once.

    A window named exactly the project name has no label (it is the plain one).
    A window whose name does not start with the stem is shown whole, unaltered —
    guessing a label out of an unrelated name would invent a fact.
    """
    if not custom_title:
        return None
    ct = custom_title.strip()
    stem = (project_name or "").strip()
    if stem and ct.casefold() == stem.casefold():
        return None
    if stem and ct.casefold().startswith(stem.casefold()):
        tail = ct[len(stem):].strip(" -–—:·")
        return tail or None
    return ct


def derive(row, my_sessions, my_ws, folder_sessions, drift_notes, now):
    """All facts for one registry row -> plain dict (json-ready)."""
    handoff, reasons = handoff_facts(row)
    if not os.path.isdir(row["root"]):
        reasons.insert(0, "root directory missing: %s" % row["root"])

    ref_ts = _parse_iso(handoff.get("at")) if handoff["present"] else None
    if ref_ts is None:
        ref_ts = _parse_iso(row["enrolled_at"]) or now
    age_days = max((now - ref_ts).total_seconds() / 86400.0, 0.0)

    live = bool(my_sessions) or bool(my_ws)
    if row["status"] in ("tombstoned", "completed"):
        tier = "ARCHIVED"
    elif live:
        tier = "OPEN NOW"
    elif not handoff["present"]:
        tier = "NO HANDOFF"
    elif age_days > COLD_DAYS:
        tier = "COLD"
    else:
        tier = "RECENT"

    return {
        "name": row["name"],
        "workspace_name": row["workspace_name"],
        # A row with NO sidebar name was enrolled from a folder, and its display
        # name is only the folder basename (registry_lib's fallback). That name
        # is a PLACEHOLDER, not an identity — several projects can live in one
        # folder (user rule, restated 2026-08-05). The renderer marks these so
        # a folder name can never masquerade as a real project name.
        "folder_level": row["workspace_name"] is None,
        "project_uuid": row["project_uuid"],
        "root": row["root"],
        "status": row["status"],
        "tier": tier,
        # The PERMANENT number, read off the row — never counted here.
        # Null only on a row that predates the backfill.
        "pick_ordinal": row.get("pick_ordinal"),
        "broken": "; ".join(reasons) if reasons else None,
        "name_drift": drift_notes or None,
        "next_action": (row.get("last_close") or {}).get("next_action"),
        "age_days": round(age_days, 2),
        "ref_time": ref_ts.isoformat(),
        "dirty_count": git_dirty_count(row["root"]),
        "live": {
            "session_count": len(my_sessions),
            "sessions": [
                {"pid": s["pid"], "session_id": s["session_id"], "cwd": s["cwd"]}
                for s in my_sessions
            ],
            # Sessions in a root shared by SEVERAL rows cannot be split per
            # project from cwd alone — counted here, attributed to no row.
            "folder_session_count": folder_sessions,
            "workspace_count": len(my_ws),
            "workspaces": [
                {"id": w["id"], "title": w["title"], "ref_hint": w["ref"],
                 "custom_title": w.get("custom_title"),
                 # MW-B: the label this window carries within the project. None
                 # for the plain window (named exactly the project).
                 "label": window_label(w.get("custom_title"), row["name"])}
                for w in my_ws
            ],
            # D10: ONE row per project carrying a window COUNT — splitting a
            # project into several rows was explicitly rejected, because that
            # defeats the point of one accumulating project.
            "window_labels": [
                lbl for lbl in
                (window_label(w.get("custom_title"), row["name"]) for w in my_ws)
                if lbl
            ],
        },
        "handoff": handoff,
    }


def build_book(home, no_cmux, no_procs):
    """The whole book, computed fresh right now. Read-only everywhere."""
    now = _now()
    sessions, proc_err = ([], None) if no_procs else live_claude_sessions()
    workspaces, cmux_err = ([], None) if no_cmux else cmux_workspaces()

    rows = []
    unreadable = []
    reg_dir = registry_lib.registry_dir(home)
    try:
        names = sorted(n for n in os.listdir(reg_dir) if n.endswith(".json"))
    except FileNotFoundError:
        names = []
    for fname in names:
        uuid = fname[: -len(".json")]
        try:
            row = registry_lib.load_row(uuid, home)
        except Exception as exc:  # noqa: BLE001 — a corrupt row must RENDER, not crash the book
            unreadable.append(
                {
                    "row_file": os.path.join(reg_dir, fname),
                    "broken": "row file unreadable: %s: %s" % (type(exc).__name__, exc),
                }
            )
            continue
        if row is None:
            continue
        rows.append(row)

    claims, drift = claim_workspaces(rows, workspaces) if not no_cmux else ({}, {})

    # Session attribution: a session carries only its cwd. When exactly ONE
    # non-archived row lives at that root the session is attributed to it;
    # when several rows share the root the split is unknowable from cwd alone —
    # counted per root, attributed to no row (facts stay honest).
    rows_by_key = {}
    for r in rows:
        if r["status"] not in ("tombstoned", "completed"):
            rows_by_key.setdefault(r["root_casefold"], []).append(r)
    attributed = {}
    folder_counts = {}
    if not no_procs:
        for s in sessions:
            cands = rows_by_key.get(s["cwd_key"], [])
            if len(cands) == 1:
                attributed.setdefault(cands[0]["project_uuid"].lower(), []).append(s)
            elif len(cands) > 1:
                folder_counts[s["cwd_key"]] = folder_counts.get(s["cwd_key"], 0) + 1

    projects = []
    for row in rows:
        u = row["project_uuid"].lower()
        my_ws = [] if no_cmux else [workspaces[i] for i in sorted(claims) if claims[i] == u]
        projects.append(
            derive(row, attributed.get(u, []), my_ws,
                   folder_counts.get(row["root_casefold"], 0), drift.get(u), now)
        )

    unmatched = [] if no_cmux else [
        {"id": w["id"], "title": w["title"], "custom_title": w["custom_title"],
         "cwd": w["cwd"], "ref_hint": w["ref"]}
        for i, w in enumerate(workspaces) if i not in claims
    ]

    # Inside a tier, rows run in PICK-NUMBER order (Zee, 2026-08-25: "show each
    # of the rows in chronological order in its category"). The page was already
    # sorted by time — newest activity first — so what he was missing was his
    # own numbering. He had just assigned every number by hand, and the numbers
    # jumped around the page, which made a book he had ordered look unordered.
    #
    # Time has NOT been thrown away. The tier itself is the time signal: OPEN NOW
    # / RECENT / COLD are cut by age, COLD at more than 30 days, and every line
    # still prints its own age. So the page reads "how stale is this group" down
    # the page, and "which project is this" inside a group.
    #
    # ref_time DESC stays as the tie-break beneath it, for rows carrying no pick
    # number — an unnumbered row cannot be ordered by a number it does not have.
    projects.sort(key=lambda p: p["ref_time"], reverse=True)
    projects.sort(key=lambda p: (TIER_ORDER.index(p["tier"]),
                                 p.get("pick_ordinal") is None,
                                 p.get("pick_ordinal") or 0))

    # Pick numbers: READ off the row, never counted (Zee's ruling, 2026-08-19).
    #
    # This used to be a 1-based counter over the pickable tiers in render order.
    # That made a number MOVE whenever a row changed tier — and a row changes
    # tier when a tagged cmux workspace appears or disappears, which happens
    # when a human closes a tab BY HAND, with no registry write at all. In one
    # session 11 was "Resurrection Protocol" in one render and "OKOA Works" in
    # the next. A number read off a stale screen resolved to a different
    # project.
    #
    # Now `pick_ordinal` lives on the row (registry_lib.ROW_KEYS) and this only
    # copies it to `pick_number`. The gutter integer and the book.json
    # `pick_number` therefore still cannot disagree — in fact more strongly than
    # before, because one PERSISTED value cannot drift from itself.
    #
    # EVERY row gets a number now, ARCHIVED included. Previously archived rows
    # got None and could not be referred to at all, so `restore`, `renumber` and
    # `purge` had nothing to name them by. Being NUMBERED is not being PICKABLE:
    # `pickable` below is the separate flag, and open-picks.sh must test it in
    # its pre-check BEFORE anything opens.
    for p in projects:
        p["pick_number"] = p["pick_ordinal"]
        p["pickable"] = p["tier"] != "ARCHIVED"

    unnumbered = [p for p in projects if p["pick_number"] is None]

    counts = {t: 0 for t in TIER_ORDER}
    for p in projects:
        counts[p["tier"]] += 1
    return {
        "generated_at": now.isoformat(),
        "registry_dir": reg_dir,
        "fresh": "computed fresh on this invocation; nothing cached, nothing persisted",
        "liveness": {
            "procs_skipped": no_procs,
            "cmux_skipped": no_cmux,
            "proc_error": proc_err,
            "cmux_error": cmux_err,
            "live_session_total": len(sessions),
            "cmux_workspace_total": len(workspaces),
        },
        "tier_counts": counts,
        # Rows the backfill has not reached. Surfaced rather than silently
        # rendered blank: an unnumbered row cannot be picked, restored or
        # renumbered, so it is invisible to every verb that names a number.
        "unnumbered_count": len(unnumbered),
        "broken_count": sum(1 for p in projects if p["broken"]) + len(unreadable),
        "listed": len(projects),
        "total": len(projects) + len(unreadable),
        "projects": projects,
        "unreadable_rows": unreadable,
        "unmatched_workspaces": unmatched,
    }


# ------------------------------------------------------------------ render ---

def _age_str(days):
    if days < 1:
        return "today"
    return "%dd" % int(days)


# ---------------------------------------------------------------------------
# The verb sheet (Zee's ask, 2026-09-04). The book listed the projects and
# nothing else, so every verb this system has — route words, account words,
# finish, curate, the number sheet — was reachable only by already knowing it.
# Discoverability now rides on the RENDER, not on a skill remembering to
# mention it: the short sheet is printed with every book, verbatim like the
# rows, and `help` (--verbs) prints the full one. Facts only; it names verbs,
# it never badges or judges a row.
VERBS_SHORT = """WHAT YOU CAN DO — type a pick, or a verb
  13              open row 13 in its own new window, in its own folder
  2, 5, 7         open all three at once — one bad token and NOTHING opens
  13 here         THIS window becomes row 13 (only if row 13's folder is this folder)
  13 tab          a new tab inside the workspace row 13 is already open in
  13 window       a new workspace — the default, so you rarely type it
  13 jason        the new window signs in as Jason's Claude account
  13 personal     ...as your own account (no word = the account door decides)
say `help` for the rest — adopt, finish, tombstone, curate, strike, merge,
the number sheet, delete/restore/purge, conflicts, dry run"""

VERBS_FULL = """RESURRECT — EVERY VERB
The book lists the projects. This lists what you can type at it.

PICKING A PROJECT
  13                  open row 13 in its own new window, in its own folder
  2, 5, 7             open all three at once, each in its own window
  13, 13              two windows on one project — repeats are legal
  13 here             THIS window becomes row 13; no new window opens.
                      Works only when row 13's folder IS this window's folder —
                      a window's folder is fixed when it is created, so a
                      different folder is refused as CROSS-ROOT.
                      Takes exactly ONE pick, never a list.
  13 tab              a new TAB inside the workspace row 13 is already open in.
                      If it is open nowhere, this falls back to a new
                      workspace and says so. A list is fine here.
  13 window           a new workspace. This is the default; the word only
                      lets you say it out loud.
  13 jason            the new window signs in as Jason's Claude account
  13 personal         ...as your own account
                      With NO account word the account door decides silently:
                      Jason when both his meters are below 65%, else personal;
                      if the meters cannot be read, personal.
                      An account word with `here` is refused — this window's
                      Claude is already running and already signed in.
  A LIST IS ALL-OR-NOTHING. One number or name that does not resolve and
  nothing opens at all. Half a list is worse than a refusal, because then
  you have to work out which windows exist.

  Same words work on the command line, with no menu at all:
    /acos-resurrect 13              opens row 13
    /acos-resurrect 13 here         this window becomes row 13
    /acos-resurrect 2, 5, 7 jason   all three, all on Jason's account

TAKING THIS WINDOW
  adopt 7             the same thing as `7 here` — THIS tab becomes project 7

FINISHING AND HIDING
  finish <project>    it is done. The row moves to ARCHIVED on the next
                      render. The row file is never deleted, and a finished
                      project can still be reopened later.
  tombstone <project> hide it for good; the launcher then refuses to open it.
                      Only ever run when you name the row yourself.
  curate              walk the curation report one row at a time — keep or
                      tombstone, your call on each

THE NUMBERS (permanent per project)
  numbers             list every number and the row that holds it
  number 44 to 7      move one row to another number
  swap 4 9            exchange two rows' numbers
  compact             renumber every row 1..N. This INVALIDATES every number
                      you have memorised, so it must be confirmed in full.
  numbers sheet       a spreadsheet for bulk changes. Fill new_number:
                      blank = leave that row alone, a number = move it there,
                      0 = DELETE that row, the same number typed on 2+ rows
                      = MERGE them into one row.
  delete <n>          take a row out of the book. Its number is freed at once,
                      its close bundles are archived, its knowledge facts are
                      kept. Undoable with restore.
  restore <uuid>      bring a deleted row back — its original number if that
                      is still free, otherwise the lowest free one
  purge <uuid>        end the undo window. Archived bundles and knowledge
                      facts both stay; only the undo goes away.

KNOWLEDGE AND WINDOWS
  strike <the line>   drop a wrong line from "learned since you were last
                      here". It is an edge, not a delete — the line stays on
                      disk, so a wrong strike is undoable.
  merge <a> into <b>  fold two windows of one project into one
  conflicts           read-only scan for clashes: BLEED, NAME-CLASH,
                      ROOT-GONE, ROOT-UNREACHABLE, SESSION-SHARED.
                      It reports and repairs nothing.

SEEING BEFORE DOING
  dry run 2, 5, 7     resolve the picks and print what would happen,
                      opening nothing
  13 label <text>     name the new window `<project> <text>` instead of
                      letting it auto-number
  go to the open one  jump to a window already open on that project,
                      instead of opening another"""


def render_human(book, use_color):
    def c(code, text):
        return "%s%s%s" % (code, text, RESET) if use_color else text

    lines = []
    lines.append(c(BOLD, "RESURRECTION BOOK") + "  " + book["generated_at"])
    lines.append("registry: %s — %s" % (book["registry_dir"], book["fresh"]))
    lv = book["liveness"]
    facts = []
    facts.append("live claude sessions: %s" % ("skipped" if lv["procs_skipped"] else lv["live_session_total"]))
    facts.append("cmux workspaces: %s" % ("skipped" if lv["cmux_skipped"] else lv["cmux_workspace_total"]))
    if lv["proc_error"]:
        facts.append(c(RED, "process scan error: %s" % lv["proc_error"]))
    if lv["cmux_error"]:
        facts.append(c(RED, lv["cmux_error"]))
    lines.append(" · ".join(facts))
    lines.append("")

    by_tier = {t: [] for t in TIER_ORDER}
    for p in book["projects"]:
        by_tier[p["tier"]].append(p)

    # Numbered, one-line-per-row menu. The gutter is the pick number (digits
    # wide enough for the highest number); names cap at 34 (ellipsis past
    # that); the next-action is trimmed to one line. Full next-action, dirty
    # count, liveness detail and handoff links all remain in --json — this is a
    # DISPLAY trim, never a data trim. BROKEN + NAME DRIFT stay (hard rules:
    # facts are never hidden), rendered as indented sub-notes under their row.
    # MW-B / D10: a project with live windows shows its COUNT on its ONE row,
    # e.g. "OKOA Works (2 open)". The count is part of the display name so it
    # sits where Zee reads the project, not in a separate column he has to scan
    # for. Labels go on a sub-line — they are variable-length and must never be
    # truncated into ambiguity.
    def _disp_parts(p):
        """(base, tag) — the tag is appended AFTER truncation so a long folder
        name can never push its own [folder] marker off the row. A marker that
        sometimes vanishes behind the ellipsis is a marker that lies."""
        n = p["live"]["workspace_count"] if p.get("live") else 0
        base = "%s (%d open)" % (p["name"], n) if n else p["name"]
        # Folder-level rows display their folder basename — a placeholder, not
        # a project name. Say so on the row itself, every time.
        tag = "  [folder]" if p.get("folder_level") else ""
        return base, tag

    def _disp(p):
        base, tag = _disp_parts(p)
        return base + tag

    # Numbered vs pickable are now two different things. Every row carries a
    # permanent number (ARCHIVED included, so it can be named by `restore` /
    # `renumber` / `purge`); only non-ARCHIVED rows may be opened.
    numbered = [p for p in book["projects"] if p.get("pick_number")]
    pickable = [p for p in numbered if p.get("pickable")]
    # Width over EVERY number, not just the pickable ones, so the ARCHIVED
    # gutter lines up with the rest instead of hanging off the column.
    num_w = max((len(str(p["pick_number"])) for p in numbered), default=1)
    name_w = min(max([len(_disp(p)) for p in book["projects"]] + [12]), 40)
    next_w = 52

    def _fit(text, width):
        return text if len(text) <= width else text[: width - 1] + "…"

    if numbered:
        # Deliberately NOT "(1–N)". Numbers are permanent per row, so the gutter
        # no longer ascends down the page and gaps are real once a row is
        # deleted or renumbered. Promising a dense range here would be a lie the
        # moment the first delete lands.
        highest = max(p["pick_number"] for p in numbered)
        lines.append(c(DIM, "pick a project by its number · rows run in NUMBER order inside "
                            "each group, and the group itself is the age signal · numbers are "
                            "PERMANENT per project, so gaps are normal "
                            "(highest in use: %d)" % highest))
        lines.append(c(DIM, "ARCHIVED rows keep their number but cannot be opened"))
        if book.get("unnumbered_count"):
            lines.append(c(AMBER, "%d row%s carr%s NO number and cannot be picked, restored or "
                                  "renumbered — run backfill-ordinals.py --apply"
                           % (book["unnumbered_count"],
                              "" if book["unnumbered_count"] == 1 else "s",
                              "ies" if book["unnumbered_count"] == 1 else "y")))
        fl_count = sum(1 for p in book["projects"] if p.get("folder_level"))
        if fl_count:
            lines.append(c(DIM, "[folder] = %d row%s enrolled from a folder with NO project name — "
                                "the folder name is a placeholder, not an identity (several "
                                "projects can live in one folder); retire or rename via curation"
                          % (fl_count, "" if fl_count == 1 else "s")))
        lines.append("")

    for tier in TIER_ORDER:
        rows = by_tier[tier]
        lines.append(c(BOLD, "%s (%d)" % (tier, len(rows))))
        for p in rows:
            num = p.get("pick_number")
            gutter = ("%*d." % (num_w, num)) if num else (" " * num_w + " ")
            base, tag = _disp_parts(p)
            name = (_fit(base, name_w - len(tag)) + tag).ljust(name_w)
            nxt = ("next: %s" % p["next_action"]) if p["next_action"] else "next: —"
            nxt = _fit(nxt, next_w).ljust(next_w)
            age = _age_str(p["age_days"])
            age_s = c(AMBER, "age %s" % age) if p["age_days"] >= AMBER_DAYS else "age %s" % age
            lines.append("  %s %s  %s  %s" % (gutter, name, nxt, age_s))
            sub_indent = " " * (num_w + 4)
            # MW-B: name the windows so two open threads are distinguishable at
            # a glance. Only when there is something to distinguish — a single
            # plain window adds no information and would just be noise.
            labels = (p.get("live") or {}).get("window_labels") or []
            wcount = (p.get("live") or {}).get("workspace_count") or 0
            if labels and wcount > 1:
                lines.append(sub_indent + "windows: %s" % " · ".join(labels))
            elif labels and wcount == 1:
                lines.append(sub_indent + "window: %s" % labels[0])
            if p.get("name_drift"):
                lines.append(sub_indent + c(AMBER, "NAME DRIFT: %s" % "; ".join(p["name_drift"])))
            if p["broken"]:
                lines.append(sub_indent + c(RED, "BROKEN: %s" % p["broken"]))
        lines.append("")

    if book["unreadable_rows"]:
        lines.append(c(BOLD, "BROKEN ROWS (%d) — unreadable row files, shown not hidden" % len(book["unreadable_rows"])))
        for u in book["unreadable_rows"]:
            lines.append("  " + c(RED, "BROKEN: %s (%s)" % (u["broken"], u["row_file"])))
        lines.append("")

    if book.get("unmatched_workspaces"):
        um = book["unmatched_workspaces"]
        lines.append(c(BOLD, "UNMATCHED WORKSPACES (%d) — live cmux workspaces matching no row "
                             "(candidates to add to the book)" % len(um)))
        for w in um:
            lines.append("  %s  cwd %s  id %s"
                         % ((w["custom_title"] or w["title"] or (w["id"] or "?")[:8]),
                            w["cwd"] or "(unknown)", w["id"]))
        lines.append("")

    tc = book["tier_counts"]
    lines.append(
        "listed %d of %d projects — %s · BROKEN %d · UNMATCHED WORKSPACES %d"
        % (
            book["listed"], book["total"],
            " · ".join("%s %d" % (t, tc[t]) for t in TIER_ORDER),
            book["broken_count"],
            len(book.get("unmatched_workspaces") or []),
        )
    )
    # Discoverability footer (Zee's ask 1, 2026-08-24). The number verbs lived
    # only in manage-ordinals.py and were named by no skill and no render, so
    # the only way in was already knowing the file path. A number is a label
    # the user OWNS; a label you cannot change is not really yours. One line,
    # facts only — it names verbs, it does not badge or judge any row.
    lines.append(
        "numbers are permanent — say `numbers` to list them, `number <n> to <m>` to move one, "
        "`swap <a> <b>` to exchange two"
    )
    # The verb sheet rides on the render itself, so it can never be trimmed,
    # forgotten or paraphrased by a caller. `help` prints the full one.
    vs = VERBS_SHORT.strip("\n").split("\n")
    lines.append("")
    lines.append(c(BOLD, vs[0]))
    lines.extend(vs[1:])
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", action="store_true", help="machine-readable book (same facts)")
    ap.add_argument("--home", default=None,
                    help="home-root override (default: $ACOS_REGISTRY_HOME or the real ~)")
    ap.add_argument("--no-cmux", action="store_true", help="skip the cmux workspace join")
    ap.add_argument("--no-procs", action="store_true", help="skip the claude process join")
    ap.add_argument("--color", choices=("auto", "always", "never"), default="auto")
    ap.add_argument("--verbs", action="store_true",
                    help="print the full verb sheet (what `help` shows) and exit")
    args = ap.parse_args(argv)

    if args.verbs:
        # No registry read, no cmux join — the sheet is static text.
        print(VERBS_FULL)
        return 0

    home = args.home or os.environ.get("ACOS_REGISTRY_HOME") or None
    book = build_book(home, args.no_cmux, args.no_procs)

    if args.json:
        print(json.dumps(book, indent=2))
    else:
        use_color = (args.color == "always") or (args.color == "auto" and sys.stdout.isatty())
        print(render_human(book, use_color))
    return 0


if __name__ == "__main__":
    sys.exit(main())
