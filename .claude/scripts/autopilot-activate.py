#!/usr/bin/env python3
"""
Deterministic Oracle autopilot activation / deactivation / status.

Replaces the prose-interpreted steps in acos-oracle-protocol/SKILL.md
Phase 0 with a single command that any caller (skill, CLI, or hook) can
invoke and get identical behavior every time.

Subcommands:
  on  <goal text...>  [--goal-file PATH] [--max-iter N] [--force]
      Pre-flight, write sentinel, log, report. Refuses if already active
      unless --force. Refuses if pre-flight fails.

      Goal sources (any one of these works; combine to override):
        positional args      → used as the summary "goal" text in sentinel
        --goal-file PATH     → stores PATH as 'goal_file' sentinel field;
                               if no positional goal given, auto-extracts a
                               summary from the first ~500 chars of the file
        both                 → positional text is the summary; PATH is the
                               persistent source-of-truth reference
  off
      Delete sentinel + loop state, log deactivation, report summary.
  status
      Report current state. Exit 0 if active, 1 if not.
  preflight
      Run pre-flight checks only (no state changes). Exit 0 if ready.

Exit codes:
  0 success
  1 pre-flight failed / not active / already active without --force
  2 invalid arguments

Designed to be invoked by SKILL.md Phase 0 via a single Bash line per
subcommand, eliminating Claude latitude during activation.
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_MAX_ITER = 150


def find_project_root(cwd):
    path = Path(cwd).resolve()
    for parent in [path] + list(path.parents):
        if (parent / ".acos").is_dir():
            return parent
    try:
        script_dir = Path(__file__).resolve().parent
        for parent in [script_dir] + list(script_dir.parents):
            if (parent / ".acos").is_dir():
                return parent
    except (NameError, OSError):
        pass
    return Path(cwd).resolve()


def utcnow():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def audit(project_root, line):
    log = project_root / ".acos" / "state" / "oracle-audit.log"
    try:
        log.parent.mkdir(parents=True, exist_ok=True)
        with open(log, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


# ── Pre-flight ────────────────────────────────────────────────────────────────

REQUIRED_HOOKS = [
    ("PreToolUse", "oracle-evaluate.py"),
    ("PreToolUse", "autopilot-askuserquestion-handler.py"),
    ("PreToolUse", "autopilot-allow-extra-tools.py"),
    ("UserPromptSubmit", "autopilot-context-injector.py"),
    ("Stop", "autopilot-stop-handler.py"),
    ("SessionEnd", "session-cleanup.sh"),
]

REQUIRED_SCRIPTS = [
    "oracle-evaluate.py",
    "autopilot-askuserquestion-handler.py",
    "autopilot-allow-extra-tools.py",
    "autopilot-context-injector.py",
    "autopilot-stop-handler.py",
    "session-cleanup.sh",
]


def preflight(project_root, verbose=False):
    """Return (ok, findings). findings is a list of (status, label, detail) tuples."""
    findings = []

    # Oracle config
    oracle_yaml = project_root / ".acos" / "config" / "oracle.yaml"
    if not oracle_yaml.is_file():
        findings.append(("FAIL", "Oracle config", f"missing: {oracle_yaml}"))
    else:
        text = oracle_yaml.read_text(encoding="utf-8")
        if re.search(r"^\s*enabled\s*:\s*false\b", text, re.MULTILINE | re.IGNORECASE):
            findings.append(("FAIL", "Oracle enabled", "enabled: false in oracle.yaml"))
        else:
            findings.append(("OK ", "Oracle enabled", str(oracle_yaml)))

    # Settings file + hooks
    settings = project_root / ".claude" / "settings.local.json"
    if not settings.is_file():
        findings.append(("FAIL", "settings.local.json", f"missing: {settings}"))
        return False, findings

    try:
        s = json.loads(settings.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        findings.append(("FAIL", "settings.local.json", f"invalid JSON: {e}"))
        return False, findings

    hooks = s.get("hooks", {}) or {}
    for event, script in REQUIRED_HOOKS:
        hit = any(script in h.get("command", "")
                  for e in hooks.get(event, [])
                  for h in e.get("hooks", []))
        findings.append(("OK " if hit else "FAIL",
                         f"{event}[{script}]",
                         "registered" if hit else "MISSING"))

    # Scripts reachable
    for script in REQUIRED_SCRIPTS:
        path = project_root / ".claude" / "scripts" / script
        ok = path.exists() and (path.is_file() or path.is_symlink())
        findings.append(("OK " if ok else "FAIL",
                         f"script {script}",
                         str(path) if ok else "MISSING or unreachable"))

    # State dir writable
    state = project_root / ".acos" / "state"
    try:
        state.mkdir(parents=True, exist_ok=True)
        ok = os.access(str(state), os.W_OK)
    except OSError:
        ok = False
    findings.append(("OK " if ok else "FAIL", "state dir writable", str(state)))

    ok = all(f[0] == "OK " for f in findings)
    return ok, findings


def print_findings(findings):
    for status, label, detail in findings:
        print(f"  [{status}] {label:<55s} {detail}")


# ── Subcommands ───────────────────────────────────────────────────────────────

SENTINEL_PREFIX = "autopilot-active-"
LOOP_STATE_PREFIX = "autopilot-loop-state-"
LOOP_STATE_SUFFIX = ".json"


def get_session_id(cli_override=None):
    """Resolve the ONE session this autopilot command scopes to.

    2026-08-07 incident: autopilot was keyed per PROJECT FOLDER, so any window
    opened on the same folder inherited another window's goal. Autopilot must
    be keyed per SESSION instead. Source order: --session (explicit, for
    deliberate cross-session admin like `off` on a window you're not in) ->
    CLAUDE_CODE_SESSION_ID (the session this command is actually running in).
    """
    if cli_override:
        return cli_override
    sid = os.environ.get("CLAUDE_CODE_SESSION_ID", "").strip()
    if not sid:
        print(
            "ERROR: CLAUDE_CODE_SESSION_ID is not set in this shell.\n"
            "Autopilot is scoped per-session and needs to know which one this is.\n"
            "Run this from inside a Claude Code session (its Bash calls inherit "
            "the variable), or pass --session <id> explicitly.",
            file=sys.stderr,
        )
        sys.exit(2)
    return sid


def sentinel_path(project_root, sid):
    return project_root / ".acos" / "state" / f"{SENTINEL_PREFIX}{sid}"


def loop_state_path(project_root, sid):
    return project_root / ".acos" / "state" / f"{LOOP_STATE_PREFIX}{sid}{LOOP_STATE_SUFFIX}"


def find_cross_project_paths(texts, project_root, max_extra_words=12):
    """Scan free text for absolute paths that exist but sit OUTSIDE project_root.

    Catches the exact 2026-08-07 mistake: a goal describing another project's
    work, activated while cwd resolved to this project. Advisory only -- never
    blocks activation, since a session can legitimately work on files outside
    its own project root.

    Folder names can contain spaces (e.g. "Vibe Coding"), so a plain
    whitespace-delimited token regex misses them -- this walks the RAW text
    and extends each candidate word-by-word, keeping the longest span that
    still resolves to a real path, instead of splitting on spaces first.
    """
    found = []
    for text in texts:
        if not text:
            continue
        n = len(text)
        i = 0
        while i < n:
            if text[i] == "/" and (i == 0 or text[i - 1] in " \t\n(\"'"):
                end = i
                words_seen = 0
                best_end = None
                while True:
                    nxt = text.find(" ", end)
                    if nxt == -1:
                        nxt = n
                    candidate = text[i:nxt].rstrip(".,;:()\"'")
                    try:
                        p = Path(candidate)
                        if p.is_absolute() and p.exists():
                            best_end = nxt
                    except (OSError, ValueError):
                        pass
                    if nxt >= n or words_seen >= max_extra_words:
                        break
                    end = nxt + 1
                    words_seen += 1
                if best_end is not None:
                    candidate = text[i:best_end].rstrip(".,;:()\"'")
                    p = Path(candidate).resolve()
                    if p != project_root and project_root not in p.parents:
                        s = str(p)
                        if s not in found:
                            found.append(s)
                    i = best_end
                    continue
            i += 1
    return found


def auto_summarize(text, max_chars=500):
    """Extract a short summary from a long vision document.

    Strategy: prefer the first non-empty paragraph (up to max_chars). Falls
    back to the first max_chars of stripped content if no paragraph break.
    """
    # Normalize CRLF (and bare CR) so the LF-anchored frontmatter/paragraph
    # parsing below works on Windows-authored vision files; otherwise raw YAML
    # frontmatter leaks into the summary.
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.strip()
    if not text:
        return ""
    # Skip yaml frontmatter
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            text = text[end + 5:].strip()
    # Skip markdown headers at the very top
    lines = text.splitlines()
    while lines and lines[0].lstrip().startswith("#"):
        lines.pop(0)
    text = "\n".join(lines).strip()
    # First non-empty paragraph
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if paragraphs:
        first = paragraphs[0]
        if len(first) <= max_chars:
            return first
        return first[:max_chars].rstrip() + "..."
    return text[:max_chars].rstrip() + ("..." if len(text) > max_chars else "")


def cmd_on(args):
    cwd = os.getcwd()
    project_root = find_project_root(cwd)
    sid = get_session_id(args.session)
    sentinel = sentinel_path(project_root, sid)

    goal = " ".join(args.goal).strip()
    goal_file_abs = None

    if args.goal_file:
        goal_file_path = Path(args.goal_file)
        if not goal_file_path.is_absolute():
            goal_file_path = (project_root / goal_file_path).resolve()
        if not goal_file_path.is_file():
            print(f"ERROR: --goal-file path does not exist: {goal_file_path}", file=sys.stderr)
            sys.exit(2)
        goal_file_abs = str(goal_file_path)
        if not goal:
            try:
                content = goal_file_path.read_text(encoding="utf-8")
                goal = auto_summarize(content)
            except OSError as e:
                print(f"ERROR: could not read --goal-file: {e}", file=sys.stderr)
                sys.exit(2)

    if not goal:
        print("ERROR: empty goal text. Provide as positional args OR via --goal-file.",
              file=sys.stderr)
        sys.exit(2)

    if sentinel.is_file() and not args.force:
        try:
            existing = json.loads(sentinel.read_text(encoding="utf-8"))
            existing_goal = existing.get("goal", "<unknown>")
            existing_iter = existing.get("iteration_count", "?")
            print(
                f"ERROR: autopilot is already active for this session ({sid}).\n"
                f"  goal: {existing_goal}\n"
                f"  iteration: {existing_iter}/{existing.get('max_iterations', '?')}\n"
                f"Use --force to replace, or run `autopilot-activate.py off` first.",
                file=sys.stderr,
            )
        except Exception:
            print("ERROR: autopilot sentinel exists. Use --force to replace.", file=sys.stderr)
        sys.exit(1)

    print("Pre-flight check:")
    ok, findings = preflight(project_root)
    print_findings(findings)
    if not ok:
        print(
            "\nPre-flight FAILED. Cannot activate autopilot.\n"
            "If hooks are MISSING in settings.local.json, run:\n"
            f"  bash {project_root}/.claude/scripts/autopilot-enroll-project.sh\n",
            file=sys.stderr,
        )
        sys.exit(1)

    cross_project = find_cross_project_paths([goal, goal_file_abs], project_root)

    max_iter = max(1, min(1000, int(args.max_iter)))
    sentinel_data = {
        "activated_at": utcnow(),
        "session_id": sid,
        "goal": goal,
        "max_iterations": max_iter,
        "iteration_count": 0,
        "recent_iter_tool_counts": [],
        "activated_by": "autopilot-activate.py",
    }
    if goal_file_abs:
        sentinel_data["goal_file"] = goal_file_abs
    if cross_project:
        sentinel_data["cross_project_paths"] = cross_project
    sentinel.parent.mkdir(parents=True, exist_ok=True)
    sentinel.write_text(json.dumps(sentinel_data, indent=2), encoding="utf-8")
    loop_state = loop_state_path(project_root, sid)
    loop_state.write_text(json.dumps(sentinel_data, indent=2), encoding="utf-8")

    audit_extra = f" | goal_file={goal_file_abs}" if goal_file_abs else ""
    audit(project_root,
          f"[{utcnow()}] AUTOPILOT_ON | sid={sid} | max_iter={max_iter} | "
          f"goal={goal[:120]}{audit_extra}")

    print()
    print("✓ Autopilot ACTIVATED")
    print(f"  session:        {sid}  (scoped to THIS window only)")
    print(f"  goal:           {goal}")
    if goal_file_abs:
        print(f"  goal_file:      {goal_file_abs}")
    print(f"  max_iterations: {max_iter}")
    print(f"  sentinel:       {sentinel}")
    if cross_project:
        print()
        print("⚠ WARNING: this goal references a path OUTSIDE the current project folder:")
        for p in cross_project:
            print(f"    {p}")
        print(f"  Current project folder: {project_root}")
        print("  If that's not intended, you likely ran this from the wrong folder.")
        print("  This is exactly the 2026-08-07 mistake — double-check before continuing.")
    print()
    print("Termination conditions:")
    print("  • Claude emits the marker phrase  AUTOPILOT_GOAL_COMPLETE  (graceful)")
    print(f"  • Iteration count reaches {max_iter}  (cap exit)")
    print("  • Five consecutive iterations with zero tool calls  (idle exit)")
    print("  • You send any non-resume user message  (panic-stop)")
    print()
    print("Deactivate manually:")
    print(f"  python3 {Path(__file__).name} off")
    print("Status:")
    print(f"  python3 {Path(__file__).name} status")
    sys.exit(0)


def cmd_off(args):
    cwd = os.getcwd()
    project_root = find_project_root(cwd)
    sid = get_session_id(args.session)
    sentinel = sentinel_path(project_root, sid)
    loop_state = loop_state_path(project_root, sid)

    if not sentinel.is_file():
        # Already off: deactivation is idempotent, so the desired post-state is
        # satisfied. Exit 0 so a defensive `off` under `set -e` does not abort.
        # Reserve non-zero exits for genuine failures.
        print(f"Autopilot is already OFF for session {sid} (no sentinel).")
        sys.exit(0)

    try:
        state = json.loads(sentinel.read_text(encoding="utf-8"))
    except Exception:
        state = {}
    goal = state.get("goal", "<unknown>")
    iters = state.get("iteration_count", 0)
    max_iter = state.get("max_iterations", "?")
    activated = state.get("activated_at", "?")

    try:
        sentinel.unlink()
    except OSError:
        pass
    try:
        if loop_state.is_file():
            loop_state.unlink()
    except OSError:
        pass

    audit(project_root,
          f"[{utcnow()}] AUTOPILOT_OFF_MANUAL | sid={sid} | iter={iters}/{max_iter} | "
          f"goal={goal[:120]}")

    print("✓ Autopilot DEACTIVATED")
    print(f"  session:    {sid}")
    print(f"  goal:       {goal}")
    print(f"  iterations: {iters}/{max_iter}")
    print(f"  activated:  {activated}")
    sys.exit(0)


def cmd_status(args):
    cwd = os.getcwd()
    project_root = find_project_root(cwd)
    sid = get_session_id(args.session)
    sentinel = sentinel_path(project_root, sid)

    if not sentinel.is_file():
        print(f"Autopilot: OFF for session {sid}")
        # Show most recent autopilot session from audit log if any
        log = project_root / ".acos" / "state" / "oracle-audit.log"
        if log.is_file():
            try:
                lines = [l for l in log.read_text().splitlines()
                         if "AUTOPILOT_" in l]
                if lines:
                    print(f"  most recent: {lines[-1]}")
            except OSError:
                pass
        other = sorted(p.name[len(SENTINEL_PREFIX):]
                        for p in (project_root / ".acos" / "state").glob(f"{SENTINEL_PREFIX}*")
                        ) if (project_root / ".acos" / "state").is_dir() else []
        if other:
            print(f"  note: {len(other)} OTHER session(s) have autopilot ON in this "
                  f"project folder. Run `autopilot-activate.py list` to see them.")
        sys.exit(1)

    try:
        state = json.loads(sentinel.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"Autopilot: sentinel present but unreadable: {e}")
        sys.exit(1)

    print(f"Autopilot: ON for session {sid}")
    print(f"  goal:                  {state.get('goal', '?')}")
    if state.get("goal_file"):
        print(f"  goal_file:             {state['goal_file']}")
    print(f"  activated_at:          {state.get('activated_at', '?')}")
    print(f"  iteration:             {state.get('iteration_count', '?')}/{state.get('max_iterations', '?')}")
    print(f"  recent tool counts:    {state.get('recent_iter_tool_counts', state.get('last_two_iter_tool_counts', []))}")

    print()
    print("Pre-flight check:")
    ok, findings = preflight(project_root)
    print_findings(findings)
    if not ok:
        print()
        print("WARNING: autopilot is ON but pre-flight has FAILs — hooks may not fire correctly.")
    sys.exit(0)


def cmd_list(args):
    """List every autopilot-active session sentinel found in THIS project folder.

    Scoped to project_root only -- there is no machine-wide registry of every
    ACOS-enabled project, so this cannot show sessions on OTHER project folders.
    """
    cwd = os.getcwd()
    project_root = find_project_root(cwd)
    state_dir = project_root / ".acos" / "state"
    current_sid = os.environ.get("CLAUDE_CODE_SESSION_ID", "").strip()

    rows = []
    if state_dir.is_dir():
        for f in sorted(state_dir.glob(f"{SENTINEL_PREFIX}*")):
            sid = f.name[len(SENTINEL_PREFIX):]
            try:
                s = json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                rows.append({"sid": sid, "goal": "<unreadable sentinel>",
                             "iters": "?", "activated": "?", "warn": False})
                continue
            goal = s.get("goal", "?")
            rows.append({
                "sid": sid,
                "goal": goal if len(goal) <= 70 else goal[:70] + "...",
                "iters": f"{s.get('iteration_count', '?')}/{s.get('max_iterations', '?')}",
                "activated": s.get("activated_at", "?"),
                "warn": bool(s.get("cross_project_paths")),
            })

    print(f"Project root: {project_root}")
    print("(This lists sessions scoped to THIS project folder only -- there is no "
          "machine-wide registry across other project folders.)")
    print()
    if not rows:
        print("No active autopilot sessions in this project.")
        sys.exit(1)

    for r in rows:
        marker = "  <- THIS session" if r["sid"] == current_sid else ""
        warn = "  ⚠ goal references a path outside this project" if r["warn"] else ""
        print(f"  session {r['sid']}{marker}{warn}")
        print(f"    iter:      {r['iters']}")
        print(f"    activated: {r['activated']}")
        print(f"    goal:      {r['goal']}")
        print()
    sys.exit(0)


def cmd_preflight(args):
    cwd = os.getcwd()
    project_root = find_project_root(cwd)
    print(f"Project root: {project_root}")
    print("Pre-flight check:")
    ok, findings = preflight(project_root)
    print_findings(findings)
    print()
    print(f"Result: {'READY ✓' if ok else 'NOT READY ✗'}")
    sys.exit(0 if ok else 1)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="Oracle autopilot activation/deactivation/status")
    sub = p.add_subparsers(dest="subcommand")
    sub.required = True

    p_on = sub.add_parser("on", help="Activate autopilot")
    p_on.add_argument("goal", nargs="*",
                      help="Goal text (positional, multi-word). Optional if --goal-file given.")
    p_on.add_argument("--goal-file", type=str, default=None,
                      help="Path to the vision/goal file. Stored as goal_file in "
                           "sentinel; if no positional goal given, auto-extracts a "
                           "summary from the file (first paragraph or 500 chars).")
    p_on.add_argument("--max-iter", type=int, default=DEFAULT_MAX_ITER,
                      help=f"Max continuation iterations (default {DEFAULT_MAX_ITER})")
    p_on.add_argument("--force", action="store_true",
                      help="Overwrite existing autopilot sentinel")
    p_on.add_argument("--session", type=str, default=None,
                      help="Explicit session id to scope to (default: "
                           "CLAUDE_CODE_SESSION_ID of the running shell)")
    p_on.set_defaults(func=cmd_on)

    p_off = sub.add_parser("off", help="Deactivate autopilot for one session")
    p_off.add_argument("--session", type=str, default=None,
                       help="Explicit session id to deactivate (default: "
                            "CLAUDE_CODE_SESSION_ID of the running shell). Use "
                            "this to turn off a DIFFERENT window's autopilot on "
                            "purpose -- it never happens by default.")
    p_off.set_defaults(func=cmd_off)

    p_st = sub.add_parser("status", help="Show current autopilot state for one session")
    p_st.add_argument("--session", type=str, default=None,
                      help="Explicit session id to check (default: "
                           "CLAUDE_CODE_SESSION_ID of the running shell)")
    p_st.set_defaults(func=cmd_status)

    p_ls = sub.add_parser("list", help="List every autopilot session active in this project folder")
    p_ls.set_defaults(func=cmd_list)

    p_pf = sub.add_parser("preflight", help="Run pre-flight checks (no state changes)")
    p_pf.set_defaults(func=cmd_preflight)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
