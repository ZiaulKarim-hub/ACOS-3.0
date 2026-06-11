#!/usr/bin/env python3
"""
Autopilot AskUserQuestion / ExitPlanMode auto-pickup handler (PreToolUse hook).

When .acos/state/autopilot-active exists:
  AskUserQuestion → auto-pick the (Recommended) option per question, else first option
  ExitPlanMode    → auto-approve

When autopilot is OFF, this hook silently allows (no interference).

Uses the documented `permissionDecision: "allow"` + `updatedInput` envelope to
pass synthesized answers back to the harness so the prompt never shows.

Fail-open: any error → allow with no updatedInput (falls back to normal prompt).
"""

import json
import os
import re
import sys
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


def autopilot_active(project_root):
    return (project_root / ".acos" / "state" / "autopilot-active").is_file()


def strip_recommended_suffix(label):
    # Strip "(Recommended)" from ANYWHERE in the label (start/middle/end), since
    # pick_option detects the marker via substring match anywhere. Collapse the
    # resulting whitespace so the cleaned answer matches the real option text.
    cleaned = re.sub(r"\s*\(Recommended\)\s*", " ", label)
    return re.sub(r"\s+", " ", cleaned).strip()


def pick_option(options, multi):
    """Return the answer for a question. Pick (Recommended) labels first, else first option."""
    # Guard non-dict options on EVERY path (not just the recommended scan): a
    # malformed option element would otherwise raise AttributeError in the
    # fallback branches, and the outer except would drop the auto-pick entirely —
    # stalling an unattended autopilot run on the resulting consent prompt.
    dict_opts = [o for o in options if isinstance(o, dict)] if options else []
    if not dict_opts:
        return [] if multi else ""
    recommended = [o for o in dict_opts if "(Recommended)" in o.get("label", "")]
    if multi:
        chosen = recommended if recommended else dict_opts[:1]
        return [strip_recommended_suffix(o.get("label", "")) for o in chosen]
    chosen = recommended[0] if recommended else dict_opts[0]
    return strip_recommended_suffix(chosen.get("label", ""))


def synthesize_answers(questions):
    """Build the answers object for AskUserQuestion's updatedInput."""
    answers = {}
    if not isinstance(questions, list):
        return answers
    for q in questions:
        if not isinstance(q, dict):
            continue
        question_text = q.get("question", "")
        options = q.get("options", []) or []
        multi = bool(q.get("multiSelect", False))
        answers[question_text] = pick_option(options, multi)
    return answers


def emit(decision, *, reason=None, updated_input=None):
    inner = {
        "hookEventName": "PreToolUse",
        "permissionDecision": decision,
    }
    if reason:
        inner["permissionDecisionReason"] = reason
    if updated_input is not None:
        inner["updatedInput"] = updated_input
    json.dump({"hookSpecificOutput": inner}, sys.stdout)


def audit(project_root, line):
    log = project_root / ".acos" / "state" / "oracle-audit.log"
    try:
        log.parent.mkdir(parents=True, exist_ok=True)
        with open(log, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            emit("allow")
            return
        data = json.loads(raw)
        tool_name = data.get("tool_name", "")
        tool_input = data.get("tool_input", {}) or {}
        cwd = data.get("cwd", os.getcwd())
        project_root = find_project_root(cwd)

        if not autopilot_active(project_root):
            emit("allow")
            return

        from datetime import datetime, timezone
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        if tool_name == "AskUserQuestion":
            questions = tool_input.get("questions", []) or []
            answers = synthesize_answers(questions)
            updated = {"questions": questions, "answers": answers}
            picks = "; ".join(f"{k[:40]}={v if isinstance(v, str) else ','.join(v)}"
                              for k, v in answers.items())
            audit(project_root,
                  f"[{ts}] AUTOPILOT_ASKUQ | tool=AskUserQuestion | picked=[{picks}]")
            emit("allow",
                 reason=f"Autopilot auto-picked Recommended/first option(s): {picks}",
                 updated_input=updated)
            return

        if tool_name == "ExitPlanMode":
            audit(project_root, f"[{ts}] AUTOPILOT_EXITPLAN | tool=ExitPlanMode | auto-accepted")
            emit("allow",
                 reason="Autopilot auto-accepted plan.",
                 updated_input=tool_input)
            return

        # Not our concern — let it pass through
        emit("allow")

    except Exception:
        emit("allow")


if __name__ == "__main__":
    main()
