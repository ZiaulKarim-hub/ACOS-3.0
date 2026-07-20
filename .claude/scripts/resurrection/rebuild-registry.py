#!/usr/bin/env python3
"""rebuild-registry.py — reconstruct the project registry from disk artifacts alone.

ACOS Resurrection Protocol, v1 requirement (design.md Vision 1): a derived
index must never dangle. This script reads NO registry file; it re-derives
every candidate project row from the filesystem, so the registry can always
be rebuilt from scratch (the proven 16/16 pattern). Also the DP5 seeder.

Hard constraints honored here:
  * stdlib only, Python 3.9.6; JSON only (no yaml module on system python).
  * DRY-RUN BY DEFAULT. --apply is the only mode that writes anything, and
    it writes registry rows ONLY through registry_lib.upsert_row (atomic
    mkstemp write path, append-only audit). Nothing here ever tombstones
    or deletes a row.
  * Enumeration signals, in authority order:
      (a) <parent>/*/memory/handoffs        — authoritative
      (b) <parent>/*/CLAUDE.md, <parent>/*/.acos — corroborating markers
      (c) ~/.claude.json projects{} paths   — LOSSY HINT ONLY. A hint can
          annotate or disambiguate a marker-found candidate; it can NEVER
          mint a candidate, and a path-mangled key is NEVER decoded into
          an identity.
  * Anomalies are FLAGGED, never auto-enrolled: a parent directory that
    itself carries project markers (the known "Vibe Coding" root anomaly)
    is listed under anomalies and excluded from --apply. Enrolling it is
    a human decision.
  * Identity: project_uuid is uuid4, minted ONCE. An existing
    <root>/.acos/project-id is ALWAYS reused — never re-minted. Candidates
    without one get a fresh uuid only under --apply (dry-run mints nothing
    and writes nothing). Git facts are captured attributes, never identity.
    BANNED as identity: sanitize(cwd), git remote, cmux workspace UUID,
    session UUID, tab title.
  * Absolute binary paths (git is /usr/bin/git; `claude`/`cmux` are
    shadowed on PATH and not needed here).

Output: human table on stderr; machine JSON on stdout (or --out FILE).

Usage:
  python3 rebuild-registry.py                 # dry-run against the real disk
  python3 rebuild-registry.py --out scan.json # dry-run, JSON to a file
  python3 rebuild-registry.py --apply         # upsert rows via registry_lib
  python3 rebuild-registry.py --parents P1 P2 --home DIR --claude-json F
                                              # fixture/testing overrides
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import registry_lib  # the ONLY permitted registry write path

DEFAULT_PARENTS = (
    "/Users/zee/Documents/Vibe Coding",
    "/Users/zee/Documents/OKOA",
)
GIT = "/usr/bin/git"


# ---------------------------------------------------------------------------
# Derivation helpers — every row field is derived from disk, none hand-typed.
# ---------------------------------------------------------------------------

def _git(root, *args):
    """Run one git plumbing command under `root`; None on any failure."""
    try:
        out = subprocess.run(
            [GIT, "-C", root] + list(args),
            capture_output=True, text=True, timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if out.returncode != 0:
        return None
    return out.stdout.rstrip("\n")


def git_facts(root):
    """Captured git attributes {branch, head, dirty_count} — NEVER identity.

    Returns None when `root` is not a git work tree (only 14/31 candidate
    dirs are repos — non-repo is a normal, first-class state).
    """
    inside = _git(root, "rev-parse", "--is-inside-work-tree")
    if inside != "true":
        return None
    head = _git(root, "rev-parse", "HEAD")  # None on an unborn HEAD
    branch = _git(root, "rev-parse", "--abbrev-ref", "HEAD")
    status = _git(root, "status", "--porcelain")
    dirty = len(status.splitlines()) if status is not None else None
    return {"branch": branch, "head": head, "dirty_count": dirty}


def newest_handoff(root):
    """Newest file (mtime) anywhere under <root>/memory/handoffs, incl.
    archive/ and any other subdirectory. None when the dir is absent/empty."""
    base = os.path.join(root, "memory", "handoffs")
    best = None
    for dirpath, _dirnames, filenames in os.walk(base):
        for fn in filenames:
            if fn == ".DS_Store":
                continue
            path = os.path.join(dirpath, fn)
            try:
                mtime = os.stat(path).st_mtime
            except OSError:
                continue
            if best is None or mtime > best[0]:
                best = (mtime, path)
    if best is None:
        return None
    mtime, path = best
    return {
        "basename": os.path.basename(path),
        "relpath": os.path.relpath(path, base),
        "mtime": mtime,
        "mtime_iso": datetime.fromtimestamp(mtime, timezone.utc).isoformat(timespec="seconds"),
        "age_days": round((time.time() - mtime) / 86400.0, 1),
    }


def markers(root):
    """Presence of the three enumeration markers at `root`."""
    return {
        "handoffs": os.path.isdir(os.path.join(root, "memory", "handoffs")),
        "claude_md": os.path.isfile(os.path.join(root, "CLAUDE.md")),
        "acos_dir": os.path.isdir(os.path.join(root, ".acos")),
    }


def read_project_id(root):
    """Read an existing <root>/.acos/project-id.

    Returns (uuid_str, note). A well-formed uuid is ALWAYS reused — never
    re-minted. A malformed file returns (None, note) and is surfaced as a
    per-candidate issue rather than silently replaced.
    """
    path = os.path.join(root, ".acos", "project-id")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            raw = fh.read().strip()
    except FileNotFoundError:
        return None, None
    except OSError as exc:
        return None, "project-id unreadable: %s" % exc
    try:
        return str(uuid.UUID(raw)), None
    except ValueError:
        return None, "project-id file exists but is not a UUID (%r) — human review required" % raw[:60]


def load_hint_paths(claude_json_path, parents):
    """projects{} paths from ~/.claude.json that live under a parent.

    Hints are corroboration only: they can annotate a marker-found candidate
    or be reported as hint-only paths for the human, but they never create a
    candidate and are never treated as identity.
    """
    try:
        with open(claude_json_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return []
    projects = data.get("projects")
    if not isinstance(projects, dict):
        return []
    out = []
    for path in projects:
        for parent in parents:
            if path == parent or path.startswith(parent.rstrip(os.sep) + os.sep):
                out.append(path)
                break
    return sorted(set(out))


# ---------------------------------------------------------------------------
# Enumeration
# ---------------------------------------------------------------------------

def enumerate_candidates(parents):
    """Candidate roots = each parent's depth-1 subdirectories carrying at
    least one marker, PLUS any parent root that itself carries markers
    (that one is an anomaly requiring human confirmation, never auto-
    enrolled). Depth is deliberately shallow: project roots live directly
    under the two parents; nested paths (e.g. .claude/worktrees) are not
    projects."""
    seen = {}
    order = []
    for parent in parents:
        parent = os.path.abspath(parent)
        roots = [parent]
        try:
            entries = sorted(os.scandir(parent), key=lambda e: e.name.casefold())
        except OSError:
            entries = []
        for entry in entries:
            if entry.name.startswith("."):
                continue
            try:
                if not entry.is_dir(follow_symlinks=False):
                    continue
            except OSError:
                continue
            roots.append(entry.path)
        for root in roots:
            m = markers(root)
            if not any(m.values()):
                continue
            key = os.path.realpath(root).casefold()
            if key in seen:
                continue
            is_parent = root in (os.path.abspath(p) for p in parents)
            cand = build_candidate(root, m, is_parent_root=is_parent)
            seen[key] = cand
            order.append(cand)
    return order


def build_candidate(root, m, is_parent_root):
    """Derive one candidate record from disk. Reads only; mints nothing."""
    pid, pid_note = read_project_id(root)
    issues = [pid_note] if pid_note else []
    anomaly_reason = None
    if is_parent_root:
        anomaly_reason = (
            "candidate root IS an enumeration parent — known 'Vibe Coding'-root "
            "anomaly; requires human confirmation, excluded from --apply"
        )
    return {
        "name": os.path.basename(root.rstrip(os.sep)),
        "root": root,
        "root_casefold": os.path.realpath(root).casefold(),
        "markers": m,
        "newest_handoff": newest_handoff(root),
        "git": git_facts(root),
        "project_uuid": pid,          # reused when present; minted only under --apply
        "project_id_source": "existing-file" if pid else None,
        "claude_json_hint": False,    # filled in by annotate_hints
        "anomaly": bool(anomaly_reason),
        "anomaly_reason": anomaly_reason,
        "issues": issues,
    }


def annotate_hints(candidates, hint_paths):
    """Mark candidates corroborated by a ~/.claude.json path; return the
    hint paths that matched no candidate (informational only)."""
    by_key = {c["root_casefold"]: c for c in candidates}
    unmatched = []
    for path in hint_paths:
        key = os.path.realpath(path).casefold()
        cand = by_key.get(key)
        if cand is not None:
            cand["claude_json_hint"] = True
        else:
            unmatched.append(path)
    return unmatched


# ---------------------------------------------------------------------------
# Apply (seeding) — the only writing mode; rows go through registry_lib only.
# ---------------------------------------------------------------------------

def _write_text_atomic(path, text):
    """Atomic plain-text write with the mandated mkstemp pattern (project-id
    and .gitignore are text, not JSON, so registry_lib's JSON writer does
    not apply — same crash-safety discipline though)."""
    path = os.path.abspath(path)
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".rebuild-", suffix=".part")
    fd_open = True
    try:
        os.write(fd, text.encode("utf-8"))
        os.fsync(fd)
        os.close(fd)
        fd_open = False
        os.replace(tmp, path)
    except BaseException:
        if fd_open:
            os.close(fd)
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
    dir_fd = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)


def ensure_project_id(root, existing):
    """Reuse the existing project_uuid or mint one (uuid4, once, at
    enrollment) and persist it at <root>/.acos/project-id, git-ignored."""
    if existing:
        return existing, "reused"
    minted = str(uuid.uuid4())
    _write_text_atomic(os.path.join(root, ".acos", "project-id"), minted + "\n")
    gi_path = os.path.join(root, ".acos", ".gitignore")
    try:
        with open(gi_path, "r", encoding="utf-8") as fh:
            lines = [ln.strip() for ln in fh.read().splitlines()]
    except (FileNotFoundError, OSError):
        lines = []
    if "project-id" not in lines and "*" not in lines:
        _write_text_atomic(gi_path, "\n".join(lines + ["project-id"]) + "\n")
    return minted, "minted"


def apply_candidates(candidates, home):
    """Upsert every non-anomaly candidate via registry_lib. NEVER tombstones,
    NEVER deletes, NEVER enrolls a flagged anomaly, and NEVER overwrites a
    malformed project-id file (issue-flagged candidates need a human)."""
    results = []
    for cand in candidates:
        if cand["anomaly"]:
            results.append({"root": cand["root"], "action": "skipped-anomaly"})
            continue
        if cand["issues"]:
            results.append({"root": cand["root"], "action": "skipped-issues",
                            "issues": cand["issues"]})
            continue
        pid, how = ensure_project_id(cand["root"], cand["project_uuid"])
        cand["project_uuid"] = pid
        cand["project_id_source"] = "existing-file" if how == "reused" else "minted-at-apply"
        # git facts are attribute-only; omit when underivable so a re-apply
        # never nulls facts a prior enrollment captured (verifier finding #1).
        fields = {"project_uuid": pid, "root": cand["root"]}
        if cand["git"] is not None:
            fields["git"] = cand["git"]
        row = registry_lib.upsert_row(fields, home=home)
        results.append({
            "root": cand["root"],
            "project_uuid": pid,
            "project_id": how,
            "status": row["status"],
            "action": "upserted",
        })
    return results


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def human_table(candidates, hint_only, mode, out=sys.stderr):
    def p(line=""):
        print(line, file=out)

    p("rebuild-registry — %s — %d candidate(s)" % (mode.upper(), len(candidates)))
    p("=" * 100)
    p("%-42s %-8s %-34s %-5s %s" % ("NAME", "MARKERS", "NEWEST HANDOFF", "HINT", "FLAGS"))
    p("-" * 100)
    for c in candidates:
        m = c["markers"]
        mk = ("H" if m["handoffs"] else "-") + ("C" if m["claude_md"] else "-") + ("A" if m["acos_dir"] else "-")
        nh = c["newest_handoff"]
        nh_s = "%s (%.1fd)" % (nh["basename"][:26], nh["age_days"]) if nh else "(none)"
        flags = []
        if c["anomaly"]:
            flags.append("ANOMALY:parent-root")
        if c["project_uuid"]:
            flags.append("id:%s" % c["project_uuid"][:8])
        flags.extend(c["issues"])
        p("%-42s %-8s %-34s %-5s %s" % (
            c["name"][:42], mk, nh_s[:34], "yes" if c["claude_json_hint"] else "-",
            " ".join(flags) if flags else "-",
        ))
    p("-" * 100)
    anomalies = [c for c in candidates if c["anomaly"]]
    p("markers: H=memory/handoffs (authoritative)  C=CLAUDE.md  A=.acos   hint=~/.claude.json corroboration")
    p("anomalies requiring human confirmation (NEVER auto-enrolled): %d" % len(anomalies))
    for c in anomalies:
        p("  !! %s — %s" % (c["root"], c["anomaly_reason"]))
    if hint_only:
        p("hint-only paths (in ~/.claude.json, NO disk markers — informational, NOT candidates): %d" % len(hint_only))
        for path in hint_only:
            p("     %s" % path)
    if mode == "dry-run":
        p("DRY-RUN: nothing written. Re-run with --apply to seed the registry (anomalies stay excluded).")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--apply", action="store_true",
                        help="upsert rows via registry_lib (default is dry-run: no writes at all)")
    parser.add_argument("--out", help="write the JSON report to FILE instead of stdout")
    parser.add_argument("--parents", nargs="+", default=list(DEFAULT_PARENTS),
                        help="parent directories to enumerate (testing override)")
    parser.add_argument("--home", default=None,
                        help="registry home-root override (tests never touch the real ~/.acos)")
    parser.add_argument("--claude-json", default=os.path.expanduser("~/.claude.json"),
                        help="hint-source override (read-only; hints never mint candidates)")
    args = parser.parse_args(argv)

    parents = [os.path.abspath(p) for p in args.parents]
    candidates = enumerate_candidates(parents)
    hint_only = annotate_hints(candidates, load_hint_paths(args.claude_json, parents))
    mode = "apply" if args.apply else "dry-run"

    report = {
        "generated_at": registry_lib.utc_now_iso(),
        "mode": mode,
        "parents": parents,
        "counts": {
            "candidates": len(candidates),
            "anomalies": sum(1 for c in candidates if c["anomaly"]),
            "enrollable": sum(1 for c in candidates if not c["anomaly"]),
            "hint_only_paths": len(hint_only),
        },
        "candidates": candidates,
        "anomalies": [c["root"] for c in candidates if c["anomaly"]],
        "hint_only_paths": hint_only,
    }

    if args.apply:
        report["applied"] = apply_candidates(candidates, home=args.home)

    human_table(candidates, hint_only, mode)
    text = json.dumps(report, indent=2) + "\n"
    if args.out:
        _write_text_atomic(args.out, text)
        print("JSON report written: %s" % os.path.abspath(args.out), file=sys.stderr)
    else:
        sys.stdout.write(text)
    return 0 if candidates else 1


if __name__ == "__main__":
    sys.exit(main())
