#!/usr/bin/env python3
"""
The Oracle — Permission Governance Agent for ACOS v3.0

PreToolUse hook that evaluates tool calls on a temperature scale (0-10).
Low-temperature actions are auto-approved; high-temperature ones escalate to user.

Reads JSON from stdin (tool_name, tool_input, cwd).
Outputs JSON permission decision to stdout.

Fail-open: any error defaults to {"permissionDecision": "allow"}.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════════════
# Minimal YAML Parser (stdlib only — no PyYAML dependency)
# Handles the 2-level structure of oracle.yaml: scalars, lists, nested dicts
# ═══════════════════════════════════════════════════════════════════════════════

def parse_yaml(text):
    """Parse simple 2-level YAML. Handles scalars, lists, and one level of nesting."""
    result = {}
    current_key = None
    current_dict = result
    indent_stack = [(0, result)]

    for raw_line in text.splitlines():
        # Skip comments and blank lines
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = len(raw_line) - len(raw_line.lstrip())

        # Pop back to correct nesting level
        while len(indent_stack) > 1 and indent <= indent_stack[-1][0]:
            indent_stack.pop()
        current_dict = indent_stack[-1][1]

        # List item: "- value" or "- key: value"
        list_match = re.match(r'^(\s*)-\s+(.*)', raw_line)
        if list_match:
            item_content = list_match.group(2).strip()
            if current_key and current_key in current_dict:
                target = current_dict[current_key]
                if not isinstance(target, list):
                    current_dict[current_key] = []
                    target = current_dict[current_key]
                # Check if item is a dict "key: value"
                kv = re.match(r'^(\w[\w_]*)\s*:\s*(.+)', item_content)
                if kv:
                    # Start a dict item — collect subsequent indented lines too
                    item_dict = {kv.group(1): _parse_value(kv.group(2))}
                    target.append(item_dict)
                    # Store reference so subsequent indented kv pairs add to this dict
                    indent_stack.append((indent + 2, item_dict))
                else:
                    target.append(_parse_value(item_content))
            continue

        # Key-value pair
        kv_match = re.match(r'^(\s*)([\w][\w_]*)\s*:\s*(.*)', raw_line)
        if kv_match:
            key = kv_match.group(2)
            value = kv_match.group(3).strip()
            if value == "" or value == "|":
                # Start of nested dict or list
                current_dict[key] = {}
                current_key = key
                indent_stack.append((indent + 2, current_dict[key]))
            else:
                current_dict[key] = _parse_value(value)
                current_key = key

    return result


def _parse_value(s):
    """Parse a YAML scalar value."""
    s = s.strip()
    if not s:
        return ""
    # Remove inline comments
    if "  #" in s:
        s = s[:s.index("  #")].strip()
    # Quoted strings
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    # Booleans
    if s.lower() in ("true", "yes", "on"):
        return True
    if s.lower() in ("false", "no", "off"):
        return False
    # Null
    if s.lower() in ("null", "~", "none"):
        return None
    # Numbers
    try:
        if "." in s:
            return float(s)
        return int(s)
    except ValueError:
        pass
    # Inline list [a, b, c]
    if s.startswith("[") and s.endswith("]"):
        items = s[1:-1].split(",")
        return [_parse_value(item) for item in items if item.strip()]
    return s


# ═══════════════════════════════════════════════════════════════════════════════
# Default Configuration (used when oracle.yaml is missing or incomplete)
# ═══════════════════════════════════════════════════════════════════════════════

DEFAULTS = {
    "enabled": True,
    "threshold": 5,
    "base_temperatures": {
        "Read": 0, "Glob": 0, "Grep": 0, "LSP": 0,
        "WebSearch": 2, "WebFetch": 2,
        "Task": 2,
        "Edit": 3, "NotebookEdit": 3,
        "Write": 4,
        "Bash": 5,
    },
    "hard_blocks": [
        r"git\s+push",
        r"rm\s+-rf\s+/\s*$",
        r"rm\s+-rf\s+~/?\s*$",
        r"rm\s+-rf\s+\.\s*$",
        r"git\s+reset\s+--hard\s+(origin/)?(main|master)",
        r"DROP\s+(TABLE|DATABASE)",
        r"git\s+branch\s+-D\s+(main|master)",
    ],
}


# ═══════════════════════════════════════════════════════════════════════════════
# Configuration Loading
# ═══════════════════════════════════════════════════════════════════════════════

def find_project_root(cwd):
    """Walk up from cwd to find directory containing .acos/."""
    path = Path(cwd).resolve()
    for parent in [path] + list(path.parents):
        if (parent / ".acos").is_dir():
            return parent
    return Path(cwd).resolve()


def load_config(project_root):
    """Load oracle.yaml config with fallback to defaults."""
    config_path = project_root / ".acos" / "config" / "oracle.yaml"
    config = dict(DEFAULTS)
    config["base_temperatures"] = dict(DEFAULTS["base_temperatures"])
    config["hard_blocks"] = list(DEFAULTS["hard_blocks"])

    if config_path.is_file():
        try:
            raw = config_path.read_text(encoding="utf-8")
            parsed = parse_yaml(raw)

            # Top-level scalars
            if "enabled" in parsed:
                config["enabled"] = parsed["enabled"]
            if "threshold" in parsed:
                config["threshold"] = int(parsed["threshold"])

            # Base temperatures override
            if "base_temperatures" in parsed and isinstance(parsed["base_temperatures"], dict):
                for tool, temp in parsed["base_temperatures"].items():
                    config["base_temperatures"][tool] = int(temp)

            # Hard blocks — extend defaults
            if "hard_blocks" in parsed and isinstance(parsed["hard_blocks"], list):
                for block in parsed["hard_blocks"]:
                    if isinstance(block, str) and block not in config["hard_blocks"]:
                        config["hard_blocks"].append(block)

            # Modifiers
            if "modifiers" in parsed and isinstance(parsed["modifiers"], dict):
                config["modifiers"] = parsed["modifiers"]

            # Learning patterns
            if "learning" in parsed and isinstance(parsed["learning"], dict):
                config["learning"] = parsed["learning"]

        except Exception:
            pass  # Fail-open: use defaults on parse error

    # Session threshold override
    session_threshold_path = project_root / ".acos" / "state" / "oracle-session-threshold"
    if session_threshold_path.is_file():
        try:
            val = int(session_threshold_path.read_text().strip())
            config["threshold"] = max(0, min(10, val))
        except (ValueError, OSError):
            pass

    # Environment variable override
    env_threshold = os.environ.get("ORACLE_THRESHOLD")
    if env_threshold is not None:
        try:
            config["threshold"] = max(0, min(10, int(env_threshold)))
        except ValueError:
            pass

    return config


# ═══════════════════════════════════════════════════════════════════════════════
# Hard Block Detection
# ═══════════════════════════════════════════════════════════════════════════════

def check_hard_blocks(tool_name, tool_input, config):
    """Return True if the action matches a hard-block pattern."""
    if tool_name != "Bash":
        return False
    command = tool_input.get("command", "")
    for pattern in config["hard_blocks"]:
        try:
            if re.search(pattern, command, re.IGNORECASE):
                return True
        except re.error:
            continue
    return False


# ═══════════════════════════════════════════════════════════════════════════════
# Temperature Computation
# ═══════════════════════════════════════════════════════════════════════════════

# Compiled modifier patterns (defaults)
SENSITIVE_PATH_PATTERNS = re.compile(
    r'(\.env|credentials|secrets?|\.pem|\.key|\.p12|\.pfx|id_rsa|\.secret|password|token)',
    re.IGNORECASE
)
RESTRICTED_PATH_PATTERNS = re.compile(
    r'(node_modules|\.git/|\.git$|vendor/|__pycache__)',
    re.IGNORECASE
)
FRAMEWORK_PATH_PATTERNS = re.compile(
    r'(\.acos/|memory/|planning/|learning-curve/)',
    re.IGNORECASE
)
DESTRUCTIVE_BASH = re.compile(
    r'(rm\s+-r|git\s+checkout\s+\.|git\s+clean|git\s+reset\s+--hard|git\s+stash\s+drop)',
    re.IGNORECASE
)
INSTALL_BASH = re.compile(
    r'(npm\s+install|yarn\s+add|pnpm\s+(add|install)|pip\s+install|cargo\s+add|brew\s+install)',
    re.IGNORECASE
)
TEST_BASH = re.compile(
    r'(npm\s+test|npx\s+vitest|npx\s+jest|yarn\s+test|pnpm\s+test|bun\s+test|pytest|cargo\s+test|go\s+test|npm\s+run\s+test)',
    re.IGNORECASE
)
LINT_BASH = re.compile(
    r'(eslint|biome|prettier|ruff|clippy|golangci-lint|npm\s+run\s+lint|npx\s+biome)',
    re.IGNORECASE
)
INFO_BASH = re.compile(
    r'^(git\s+(status|log|diff|branch|remote|show|tag)|ls|pwd|echo|cat|head|tail|wc|which|type|env|printenv|whoami|date|uname)',
    re.IGNORECASE
)


def extract_path(tool_name, tool_input):
    """Extract the file path from a tool input, if any."""
    if tool_name in ("Read", "Write", "Edit"):
        return tool_input.get("file_path", "")
    if tool_name == "Glob":
        return tool_input.get("pattern", "") + " " + tool_input.get("path", "")
    if tool_name in ("Grep",):
        return tool_input.get("path", "")
    if tool_name == "NotebookEdit":
        return tool_input.get("notebook_path", "")
    return ""


def compute_temperature(tool_name, tool_input, config, project_root):
    """Compute temperature score (0-10) for a tool call."""
    base_temps = config["base_temperatures"]
    base = base_temps.get(tool_name, 3)  # Unknown tools default to 3
    modifier = 0
    reasons = []

    path = extract_path(tool_name, tool_input)
    command = tool_input.get("command", "") if tool_name == "Bash" else ""

    # ── Path-based modifiers ───────────────────────────────────────────────
    if path:
        if SENSITIVE_PATH_PATTERNS.search(path):
            modifier += 4
            reasons.append("sensitive_path +4")
        if RESTRICTED_PATH_PATTERNS.search(path):
            modifier += 3
            reasons.append("restricted_path +3")
        if FRAMEWORK_PATH_PATTERNS.search(path):
            modifier -= 2
            reasons.append("framework_path -2")

    # ── Bash command modifiers ────────────────────────────────────────────
    if tool_name == "Bash" and command:
        if DESTRUCTIVE_BASH.search(command):
            modifier += 3
            reasons.append("destructive_cmd +3")
        if INSTALL_BASH.search(command):
            modifier += 2
            reasons.append("install_cmd +2")
        if TEST_BASH.search(command):
            modifier -= 2
            reasons.append("test_cmd -2")
        if LINT_BASH.search(command):
            modifier -= 2
            reasons.append("lint_cmd -2")
        if INFO_BASH.match(command.strip()):
            modifier -= 3
            reasons.append("info_cmd -3")

    # ── In-scope file modifier ────────────────────────────────────────────
    if path:
        active_slice = project_root / ".acos" / "state" / "active-slice.yaml"
        if active_slice.is_file():
            try:
                slice_text = active_slice.read_text(encoding="utf-8")
                if path in slice_text:
                    modifier -= 2
                    reasons.append("in_scope -2")
            except OSError:
                pass

    # ── Learned patterns from config ──────────────────────────────────────
    learning = config.get("learning", {})
    if isinstance(learning, dict) and learning.get("enabled", False):
        patterns = learning.get("patterns", [])
        if isinstance(patterns, list):
            for pat in patterns:
                if not isinstance(pat, dict):
                    continue
                pat_tool = pat.get("tool", "")
                pat_pattern = pat.get("pattern", "")
                pat_modifier = pat.get("modifier", 0)
                if not pat_tool or not pat_pattern:
                    continue
                try:
                    pat_modifier = int(pat_modifier)
                except (ValueError, TypeError):
                    continue
                if pat_tool == tool_name:
                    match_text = command if tool_name == "Bash" else path
                    try:
                        if re.search(pat_pattern, match_text, re.IGNORECASE):
                            modifier += pat_modifier
                            reasons.append(f"learned:{pat_pattern} {pat_modifier:+d}")
                    except re.error:
                        continue

    # ── Custom modifiers from config ──────────────────────────────────────
    custom_modifiers = config.get("modifiers", {})
    if isinstance(custom_modifiers, dict):
        # sensitive_paths, restricted_paths, etc. can override defaults
        # (already handled above via compiled patterns — custom ones extend)
        custom_patterns = custom_modifiers.get("custom", [])
        if isinstance(custom_patterns, list):
            for cp in custom_patterns:
                if not isinstance(cp, dict):
                    continue
                cp_tool = cp.get("tool", "")
                cp_pattern = cp.get("pattern", "")
                cp_mod = cp.get("modifier", 0)
                if not cp_pattern:
                    continue
                try:
                    cp_mod = int(cp_mod)
                except (ValueError, TypeError):
                    continue
                if cp_tool and cp_tool != tool_name:
                    continue
                match_text = command if tool_name == "Bash" else path
                try:
                    if re.search(cp_pattern, match_text, re.IGNORECASE):
                        modifier += cp_mod
                        reasons.append(f"custom:{cp_pattern} {cp_mod:+d}")
                except re.error:
                    continue

    temperature = max(0, min(10, base + modifier))
    return temperature, base, modifier, reasons


# ═══════════════════════════════════════════════════════════════════════════════
# Audit Logging
# ═══════════════════════════════════════════════════════════════════════════════

def audit_log(project_root, tool_name, decision, temperature, reasons, detail=""):
    """Append to oracle-audit.log for escalations and denials."""
    if decision == "allow":
        return  # Only log escalations and denials to keep log manageable
    log_path = project_root / ".acos" / "state" / "oracle-audit.log"
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        reason_str = ", ".join(reasons) if reasons else "none"
        line = f"[{ts}] {decision.upper():5s} | temp={temperature:2d} | tool={tool_name} | reasons=[{reason_str}]"
        if detail:
            line += f" | detail={detail}"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass  # Non-critical — don't break the hook


# ═══════════════════════════════════════════════════════════════════════════════
# Main Entry Point
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            # No input — allow by default
            json.dump({"permissionDecision": "allow"}, sys.stdout)
            return

        data = json.loads(raw)
        tool_name = data.get("tool_name", "")
        tool_input = data.get("tool_input", {})
        cwd = data.get("cwd", os.getcwd())

        project_root = find_project_root(cwd)
        config = load_config(project_root)

        # Oracle disabled — allow everything
        if not config.get("enabled", True):
            json.dump({"permissionDecision": "allow"}, sys.stdout)
            return

        # Check hard blocks first (always deny, regardless of threshold)
        if check_hard_blocks(tool_name, tool_input, config):
            command = tool_input.get("command", "")
            audit_log(project_root, tool_name, "deny", 10, ["hard_block"], command)
            json.dump({
                "permissionDecision": "deny",
                "reason": f"Hard-blocked by The Oracle: pattern matched in command"
            }, sys.stdout)
            return

        # Compute temperature
        temperature, base, modifier, reasons = compute_temperature(
            tool_name, tool_input, config, project_root
        )
        threshold = config["threshold"]

        if temperature <= threshold:
            json.dump({"permissionDecision": "allow"}, sys.stdout)
        else:
            detail = tool_input.get("command", "") or extract_path(tool_name, tool_input)
            audit_log(project_root, tool_name, "ask", temperature, reasons, detail)
            json.dump({"permissionDecision": "ask"}, sys.stdout)

    except Exception:
        # Fail-open: any error allows the action
        json.dump({"permissionDecision": "allow"}, sys.stdout)


if __name__ == "__main__":
    main()
