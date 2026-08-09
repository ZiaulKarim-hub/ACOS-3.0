#!/usr/bin/env python3
"""
Autopilot UserPromptSubmit hook — guidance-injection model.

When autopilot is active, this hook NEVER deactivates the run. User messages
are treated as mid-course guidance: Claude reads the message, responds, and
keeps autopiloting. Only explicit deactivation paths end autopilot:
  - /acos-oracle-protocol autopilot-off (via Claude's normal slash-command flow)
  - python3 .claude/scripts/autopilot-activate.py off (any shell)
  - Goal-complete marker / iteration cap / 5-turn idle exit (Stop hook)

Three branches:

1. **Autopilot OFF**: pass through with no extra context.

2. **Eternity-protocol resume injection** (project-scoped pending-resume
   marker armed): pass through silently. eternity-resume-prepend.sh runs
   next in the hook chain and prepends the resume content. No autopilot
   directive — Claude is mid-context-recovery and the resume content
   itself contains everything needed to continue.

3. **Autopilot ON + ordinary user message**: prepend a guidance directive
   reminding Claude the autopilot regime is active, the user message is
   guidance (not a stop signal), and to respond + continue. Audit log
   records AUTOPILOT_USER_GUIDANCE.

Fail-open: any error → silent allow (no context, prompt passes through).
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


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


def _eternity_check(cwd):
    """Return True if ANY in-flight eternity-protocol marker for this project's
    sessions is currently armed. Uses the shared _autopilot_eternity module
    so all hooks agree on what 'eternity active' means.

    Marker types covered (was only pending-resume-*.txt prior to 2026-06-15):
      pending-resume-<sid>.txt, .resume-pending-<sid>, .compact-fired-<sid>,
      .clear-requested-<sid>.
    """
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from _autopilot_eternity import is_eternity_protocol_active
        return is_eternity_protocol_active(cwd)
    except Exception:
        return False


def audit(project_root, line):
    log = project_root / ".acos" / "state" / "oracle-audit.log"
    try:
        log.parent.mkdir(parents=True, exist_ok=True)
        with open(log, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def emit(additional_context=None):
    out = {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit"}}
    if additional_context:
        out["hookSpecificOutput"]["additionalContext"] = additional_context
    json.dump(out, sys.stdout)


def build_guidance_directive(goal, iter_count, max_iter, sid):
    return (
        "─────────────────────────────────────────────────\n"
        f"AUTOPILOT MODE IS STILL ACTIVE — iteration {iter_count}/{max_iter}\n"
        f"SESSION: {sid}  (this goal belongs ONLY to this session)\n"
        f"GOAL: {goal}\n"
        "─────────────────────────────────────────────────\n"
        "The user has sent the message above. Treat it as MID-COURSE GUIDANCE, "
        "not as a stop signal. Specifically:\n"
        "  • Read and address the user's message in your response.\n"
        "  • Adjust your approach based on their guidance if applicable.\n"
        "  • Then CONTINUE working toward the original goal — autopilot will "
        "re-inject a continuation directive after your turn ends.\n"
        "  • Do NOT emit AUTOPILOT_GOAL_COMPLETE unless the goal is genuinely "
        "complete; user guidance alone does not constitute completion.\n"
        "  • If the user is explicitly asking you to STOP autopilot, they should "
        "use `/acos-oracle-protocol autopilot-off` or run "
        "`python3 .claude/scripts/autopilot-activate.py off` in a shell. If they "
        "type a free-text request like 'stop autopilot' or 'turn off autopilot', "
        "run the deactivation command for them via Bash before your turn ends.\n"
        "  • All other autopilot rules still apply: no free-text confirmation "
        "questions; auto-pick (Recommended) options on AskUserQuestion; do not "
        "stop to clarify minor decisions.\n"
        "─────────────────────────────────────────────────\n"
    )


def main():
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
        cwd = data.get("cwd", os.getcwd())
        sid = (data.get("session_id") or os.environ.get("CLAUDE_CODE_SESSION_ID", "")).strip()
        project_root = find_project_root(cwd)

        if not sid:
            # Can't safely scope without knowing which session this is — fail open.
            emit()
            return

        sentinel = project_root / ".acos" / "state" / f"autopilot-active-{sid}"

        if not sentinel.is_file():
            # Autopilot is OFF for THIS session — pass through with no extra
            # context, even if another session has its own sentinel active.
            emit()
            return

        # ── Eternity-protocol subordination (precedence over autopilot) ──────
        # Per user spec 2026-06-15: any in-flight eternity marker (not just
        # pending-resume) means eternity owns the right-of-way. Pass through
        # silently — no guidance directive, no panic-stop. The sentinel is
        # preserved so autopilot resumes after eternity's markers clear.
        if _eternity_check(cwd):
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            try:
                state_obj = json.loads(sentinel.read_text(encoding="utf-8"))
                iters = state_obj.get("iteration_count", 0)
            except Exception:
                iters = "?"
            audit(project_root,
                  f"[{ts}] AUTOPILOT_ETERNITY_SUBORDINATE | hook=UserPromptSubmit | "
                  f"sid={sid} | iter={iters} | sentinel preserved")
            emit()
            return

        # ── Ordinary user message during autopilot → guidance injection ───
        try:
            state_obj = json.loads(sentinel.read_text(encoding="utf-8"))
            goal = state_obj.get("goal", "<no goal recorded>")
            iters = state_obj.get("iteration_count", 0)
            max_iter = state_obj.get("max_iterations", "?")
        except Exception:
            goal, iters, max_iter = "<unreadable>", "?", "?"

        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        audit(project_root,
              f"[{ts}] AUTOPILOT_USER_GUIDANCE | sid={sid} | iter={iters}/{max_iter} | "
              f"goal={goal[:80]}")

        emit(additional_context=build_guidance_directive(goal, iters, max_iter, sid))

    except Exception:
        emit()


if __name__ == "__main__":
    main()
