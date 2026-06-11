#!/usr/bin/env python3
"""
Autopilot blanket auto-allow for tools Oracle doesn't evaluate.

Targets WebFetch, WebSearch, and MCP server tools (mcp__<server>__<tool>).
Under autopilot, these auto-approve silently. When autopilot is OFF, the
hook passes through unchanged so normal harness consent prompts still fire.

Caveats — DOCUMENTED, not fixable here:
  * MCP server tools: permissionDecision:"deny" is NOT enforced on MCP calls
    (anthropics/claude-code#33106). So we can auto-allow MCP, but a future
    hard-block list for MCP would not actually block. Don't add destructive
    MCP tools to a future autopilot blocklist expecting enforcement.
  * Any permissions.deny rule in settings.local.json still wins over our
    allow (Anthropic docs: hook decisions do not bypass deny rules).

Fail-open: any error → silent allow.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


TOOL_PREFIXES_OR_NAMES = ("WebFetch", "WebSearch")
MCP_PREFIX = "mcp__"


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


def emit(decision, reason=None):
    inner = {"hookEventName": "PreToolUse", "permissionDecision": decision}
    if reason:
        inner["permissionDecisionReason"] = reason
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
        cwd = data.get("cwd", os.getcwd())
        project_root = find_project_root(cwd)

        if not autopilot_active(project_root):
            emit("allow")  # silent pass-through; normal harness behavior
            return

        is_target = (
            tool_name in TOOL_PREFIXES_OR_NAMES
            or tool_name.startswith(MCP_PREFIX)
        )
        if not is_target:
            emit("allow")
            return

        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        audit(project_root,
              f"[{ts}] AUTOPILOT_EXTRA_ALLOW | tool={tool_name}")
        emit("allow", reason=f"Autopilot auto-approved {tool_name}.")
    except Exception:
        emit("allow")


if __name__ == "__main__":
    main()
