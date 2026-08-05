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
        "project_uuid": row["project_uuid"],
        "root": row["root"],
        "status": row["status"],
        "tier": tier,
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

    projects.sort(key=lambda p: (TIER_ORDER.index(p["tier"]), p["ref_time"]), reverse=False)
    # recency DESC inside each tier:
    projects.sort(key=lambda p: p["ref_time"], reverse=True)
    projects.sort(key=lambda p: TIER_ORDER.index(p["tier"]))

    # Pick numbers: a global 1-based counter over the PICKABLE tiers only, in
    # exactly the sorted order the human render walks (tier, then recency). The
    # same integer is the printed gutter AND the book.json `pick_number` the
    # menu skill resolves a typed number against — assigned ONCE, here, so the
    # two can never disagree. ARCHIVED rows (sorted last) are not pickable ->
    # pick_number None (no gutter number in the render).
    pick_no = 0
    for p in projects:
        if p["tier"] == "ARCHIVED":
            p["pick_number"] = None
        else:
            pick_no += 1
            p["pick_number"] = pick_no

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
    def _disp(p):
        n = p["live"]["workspace_count"] if p.get("live") else 0
        return "%s (%d open)" % (p["name"], n) if n else p["name"]

    pickable = [p for p in book["projects"] if p.get("pick_number")]
    num_w = max((len(str(p["pick_number"])) for p in pickable), default=1)
    name_w = min(max([len(_disp(p)) for p in book["projects"]] + [12]), 40)
    next_w = 52

    def _fit(text, width):
        return text if len(text) <= width else text[: width - 1] + "…"

    if pickable:
        lines.append(c(DIM, "pick a project by its number (1–%d) · ARCHIVED rows are not numbered"
                             % len(pickable)))
        lines.append("")

    for tier in TIER_ORDER:
        rows = by_tier[tier]
        lines.append(c(BOLD, "%s (%d)" % (tier, len(rows))))
        for p in rows:
            num = p.get("pick_number")
            gutter = ("%*d." % (num_w, num)) if num else (" " * num_w + " ")
            name = _fit(_disp(p), name_w).ljust(name_w)
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
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", action="store_true", help="machine-readable book (same facts)")
    ap.add_argument("--home", default=None,
                    help="home-root override (default: $ACOS_REGISTRY_HOME or the real ~)")
    ap.add_argument("--no-cmux", action="store_true", help="skip the cmux workspace join")
    ap.add_argument("--no-procs", action="store_true", help="skip the claude process join")
    ap.add_argument("--color", choices=("auto", "always", "never"), default="auto")
    args = ap.parse_args(argv)

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
