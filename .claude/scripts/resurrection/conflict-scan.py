#!/usr/bin/env python3
"""conflict-scan.py — name the crossed wires, and name the fix for each.

Zee's Rule 3 (2026-08-18): "if there is any conflict, the system should notify
me and let me know what I need to do to resolve it." This is that notifier.

It is READ-ONLY. It repairs nothing, it moves nothing, it deletes nothing. Its
whole job is to turn a silent crossing into a named finding with a named fix.

Python (not TypeScript) by the standing exception: this extends the existing
Python resurrection family and imports registry_lib directly.

The five conflict classes Zee defined, in his own words plus the mechanism:

  BLEED         one project's content can reach another's pane. Detected as
                two sessions of DIFFERENT projects sharing one cmux surface
                inside one folder — the exact 2026-08-18 condition.
  NAME-CLASH    two live rows carry one name. A name-keyed lookup cannot
                choose between them.
  ROOT-GONE     a row points at a folder that no longer exists.
  ROOT-UNREACHABLE
                a tab is bound to a row whose root is not the tab's folder. A
                cmux tab's folder is fixed at creation, so this tab can never
                become that root.
  SESSION-SHARED
                one session id is the recorded hint of more than one row.
  ORDINAL-CLASH two live rows hold one pick_ordinal, so a typed number is
                ambiguous. Added 2026-08-19 with the permanent-number ruling:
                auto-assignment is `max(ever issued) + 1` with no lock, so two
                simultaneous creations can take the same number.
  ORDINAL-MISSING
                a live row has no pick_ordinal, so no verb can name it — every
                verb names a row by its number.

Several windows on ONE project is NOT a conflict — that is a supported mode
(one row, one book entry with a live-window count, one knowledge store), and
this scanner stays silent about it by design.

Usage:
    python3 conflict-scan.py [--json]
Exit: 0 = no conflicts, 1 = conflicts found, 2 = scanner could not run.
"""

import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import registry_lib  # noqa: E402

STATE = os.path.join(os.path.expanduser("~"), "Library", "Application Support",
                     "acos-token-monitor", "state")
CMUX_BIN = os.environ.get("CMUX_CLAUDE_HOOK_CMUX_BIN",
                          "/Applications/cmux.app/Contents/Resources/bin/cmux")
KEY_RE = re.compile(r"\[key:([0-9a-fA-F-]{36})\]")


def _live_rows(home=None):
    rows = []
    for row in registry_lib._iter_rows(home=home):
        if row.get("status") != "tombstoned":
            rows.append(row)
    return rows


def _workspaces():
    """Live cmux workspaces. Absent cmux is not an error — those checks skip."""
    try:
        out = subprocess.run([CMUX_BIN, "rpc", "workspace.list"],
                             capture_output=True, text=True, timeout=5)
        return json.loads(out.stdout).get("workspaces", [])
    except Exception:
        return None


def _read_binding(prefix, sid):
    try:
        with open(os.path.join(STATE, prefix + sid), "r") as fh:
            return fh.readline().strip()
    except Exception:
        return None


def _session_ids():
    try:
        return [n[len("project-"):] for n in os.listdir(STATE)
                if n.startswith("project-")]
    except Exception:
        return []


def scan(home=None):
    findings = []
    rows = _live_rows(home)
    by_uuid = {r["project_uuid"]: r for r in rows}

    # ── NAME-CLASH ───────────────────────────────────────────────────────
    by_name = {}
    for r in rows:
        name = (r.get("workspace_name") or r.get("name") or "").strip()
        if name:
            by_name.setdefault(name.casefold(), []).append(r)
    for _, group in sorted(by_name.items()):
        if len(group) > 1:
            findings.append({
                "type": "NAME-CLASH",
                "detail": "%d live rows are named %r: %s" % (
                    len(group), group[0].get("workspace_name") or group[0].get("name"),
                    ", ".join("%s @ %s (%s)" % (g["project_uuid"], g["root"], g["status"])
                              for g in group)),
                "fix": "Rename or tombstone all but one, so a name-keyed lookup "
                       "has exactly one answer: "
                       "/acos-resurrect then `tombstone <project>`, or edit the "
                       "row's workspace_name via registry_lib.upsert_row.",
            })

    # ── ROOT-GONE ────────────────────────────────────────────────────────
    for r in rows:
        if not os.path.isdir(r["root"]):
            findings.append({
                "type": "ROOT-GONE",
                "detail": "row %s (%r) points at %r, which does not exist" % (
                    r["project_uuid"], r.get("workspace_name") or r.get("name"), r["root"]),
                "fix": "Restore the folder, or tombstone the row via "
                       "/acos-resurrect `tombstone <project>`. The row file is "
                       "never deleted either way.",
            })

    # ── SESSION-SHARED ───────────────────────────────────────────────────
    hint_map = {}
    for r in rows:
        h = r.get("last_session_id_hint")
        if h:
            hint_map.setdefault(h, []).append(r)
    for sid, group in sorted(hint_map.items()):
        if len(group) > 1:
            findings.append({
                "type": "SESSION-SHARED",
                "detail": "session %s is the recorded hint of %d rows: %s" % (
                    sid, len(group),
                    ", ".join("%s (%r @ %s)" % (g["project_uuid"],
                                                g.get("workspace_name") or g.get("name"),
                                                g["root"]) for g in group)),
                "fix": "One session can only belong to one project. Decide which "
                       "row owns it, then let the others be re-stamped by their "
                       "own next session — or tombstone a row that should not exist.",
            })

    # ── ROOT-UNREACHABLE ─────────────────────────────────────────────────
    workspaces = _workspaces()
    if workspaces is not None:
        for w in workspaces:
            desc = w.get("description") or ""
            m = KEY_RE.search(desc)
            if not m:
                continue
            row = by_uuid.get(m.group(1))
            if row is None:
                findings.append({
                    "type": "ROOT-UNREACHABLE",
                    "detail": "tab %r (%s) is tagged [key:%s], but no live row has "
                              "that uuid" % (w.get("custom_title"), w.get("ref"), m.group(1)),
                    "fix": "Re-pick the project with /acos-resurrect so adopt-project.sh "
                           "rewrites the tag to a real row.",
                })
                continue
            cwd = w.get("current_directory") or ""
            if cwd and os.path.realpath(cwd) != os.path.realpath(row["root"]):
                findings.append({
                    "type": "ROOT-UNREACHABLE",
                    "detail": "tab %r (%s) sits in %r but its row %s is rooted at %r" % (
                        w.get("custom_title"), w.get("ref"), cwd,
                        row["project_uuid"], row["root"]),
                    "fix": "A cmux tab's folder is fixed when the tab is created, so "
                           "this tab can never become that root. Open a NEW window "
                           "with --cwd %r and pick the project there; then close this "
                           "tab with /acos-safe-close." % row["root"],
                })

    # ── BLEED ────────────────────────────────────────────────────────────
    # Two sessions of DIFFERENT projects claiming ONE cmux surface. That is the
    # condition under which the resume chain's last-resort pick could serve the
    # wrong project's handoff (fixed 2026-08-18 by the project-key gate in
    # eternity-resume-prepend.sh — but the crossing itself still deserves a name).
    by_surface = {}
    for sid in _session_ids():
        surf = _read_binding("cmux-surface-", sid)
        proj = _read_binding("project-", sid)
        if surf and proj:
            by_surface.setdefault(surf, {}).setdefault(proj, []).append(sid)
    for surf, projects in sorted(by_surface.items()):
        if len(projects) > 1:
            named = []
            for puuid, sids in sorted(projects.items()):
                row = by_uuid.get(puuid)
                label = (row.get("workspace_name") or row.get("name")) if row else puuid
                named.append("%r (%d session%s)" % (label, len(sids),
                                                    "" if len(sids) == 1 else "s"))
            findings.append({
                "type": "BLEED",
                "detail": "cmux surface %s is claimed by %d different projects: %s" % (
                    surf, len(projects), ", ".join(named)),
                # The file is .ts and runs under bun, not .sh under bash. As
                # printed before 2026-08-19 this fix line could not be run at
                # all: `bash ...prune-state-bindings.sh` names a file that has
                # never existed.
                "fix": "Prune the stale surface bindings with "
                       "`bun .claude/scripts/resurrection/prune-state-bindings.ts --apply` "
                       "(dry run first: drop --apply). "
                       "Bindings are rewritten at every SessionStart and were never "
                       "pruned, so dead sessions keep claiming a live surface.",
            })

    # ── ORDINAL-CLASH ────────────────────────────────────────────────────
    # Two live rows holding one pick_ordinal. This is the detector for the
    # `max+1` race: registry_lib documents no blocking lock and none surviving
    # SIGKILL, so two simultaneous creations can both read the same ledger max
    # and both take it. At one human and a few opens a day that is very
    # unlikely — but an undetected clash means a typed number opens whichever
    # row the scan happens to reach first, silently, which is precisely the
    # ambiguity permanent numbers were introduced to remove.
    by_ordinal = {}
    unnumbered = []
    for r in rows:
        n = r.get("pick_ordinal")
        if n is None:
            unnumbered.append(r)
        else:
            by_ordinal.setdefault(n, []).append(r)
    for n, group in sorted(by_ordinal.items()):
        if len(group) > 1:
            findings.append({
                "type": "ORDINAL-CLASH",
                "detail": "%d live rows hold pick_ordinal %d: %s" % (
                    len(group), n,
                    ", ".join("%r %s @ %s (%s)" % (
                        g.get("workspace_name") or g.get("name"), g["project_uuid"],
                        g["root"], g["status"]) for g in group)),
                "fix": "Give all but one a different number — a typed number "
                       "must resolve to exactly one row: "
                       "`python3 .claude/scripts/resurrection/manage-ordinals.py "
                       "renumber %d to <free-number> --uuid <project_uuid> --apply`. "
                       "Pick the free number from `manage-ordinals.py status`; "
                       "the ledger will not auto-reissue a retired one." % n,
            })
    if unnumbered:
        findings.append({
            "type": "ORDINAL-MISSING",
            "detail": "%d live row%s carr%s no pick_ordinal: %s" % (
                len(unnumbered), "" if len(unnumbered) == 1 else "s",
                "ies" if len(unnumbered) == 1 else "y",
                ", ".join("%r %s" % (u.get("workspace_name") or u.get("name"),
                                     u["project_uuid"]) for u in unnumbered)),
            # An unnumbered row is not merely cosmetic: every verb that names a
            # row names it BY NUMBER, so an unnumbered row cannot be picked,
            # renumbered, deleted or restored. It is invisible to the interface.
            "fix": "Assign the missing numbers: "
                   "`python3 .claude/scripts/resurrection/backfill-ordinals.py` "
                   "to see the plan, then re-run with --apply. Existing numbers "
                   "are never moved by a backfill.",
        })

    return findings


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    as_json = "--json" in argv
    try:
        findings = scan()
    except Exception as exc:  # noqa: BLE001 — a scanner must not become the outage
        sys.stderr.write("conflict-scan: could not run: %s: %s\n"
                         % (type(exc).__name__, exc))
        return 2

    if as_json:
        print(json.dumps({"conflicts": findings, "count": len(findings)}, indent=2))
        return 1 if findings else 0

    if not findings:
        print("CONFLICT SCAN — none found.")
        print("(several windows on ONE project is a supported mode, not a conflict)")
        return 0

    print("CONFLICT SCAN — %d finding%s. Nothing was changed; each fix is yours to run."
          % (len(findings), "" if len(findings) == 1 else "s"))
    for i, f in enumerate(findings, 1):
        print("")
        print("%2d. %s" % (i, f["type"]))
        print("    what: %s" % f["detail"])
        print("    fix:  %s" % f["fix"])
    return 1


if __name__ == "__main__":
    sys.exit(main())
