#!/usr/bin/env python3
"""
The Oracle — Permission Governance Agent for ACOS v3.0

PreToolUse hook that evaluates tool calls on a temperature scale (0-10).
Low-temperature actions are auto-approved; high-temperature ones escalate to user.
Threshold 11 (YOLO) bypasses everything including hard blocks.

Reads JSON from stdin (tool_name, tool_input, cwd).
Outputs JSON permission decision to stdout wrapped in hookSpecificOutput envelope.

Fail-open: any error defaults to allow.

Usage:
  Normal (hook):   stdin JSON → stdout decision
  Diagnose:        python3 oracle-evaluate.py --diagnose [--config path/to/oracle.yaml]
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
    "threshold": 9,
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

            # Hard blocks — replace defaults when explicitly set in config
            if "hard_blocks" in parsed:
                if isinstance(parsed["hard_blocks"], list):
                    config["hard_blocks"] = [b for b in parsed["hard_blocks"] if isinstance(b, str)]
                else:
                    # Explicit empty value (e.g. hard_blocks: []) clears all blocks
                    config["hard_blocks"] = []

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
            config["threshold"] = max(0, min(11, val))
        except (ValueError, OSError):
            pass

    # Environment variable override
    env_threshold = os.environ.get("ORACLE_THRESHOLD")
    if env_threshold is not None:
        try:
            config["threshold"] = max(0, min(11, int(env_threshold)))
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
            modifier += 5
            reasons.append("sensitive_path +5")
        if RESTRICTED_PATH_PATTERNS.search(path):
            modifier += 3
            reasons.append("restricted_path +3")
        if FRAMEWORK_PATH_PATTERNS.search(path):
            modifier -= 2
            reasons.append("framework_path -2")

    # ── Bash command modifiers ────────────────────────────────────────────
    if tool_name == "Bash" and command:
        if DESTRUCTIVE_BASH.search(command):
            modifier += 5
            reasons.append("destructive_cmd +5")
        if INSTALL_BASH.search(command):
            modifier += 3
            reasons.append("install_cmd +3")
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
        active_slice = project_root / ".acos" / "config" / "active-slice.yaml"
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
    """Append to oracle-audit.log for escalations, denials, and YOLO bypasses."""
    if decision == "allow":
        return  # Only log escalations, denials, and YOLO bypasses
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
# Output Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def emit_decision(decision, reason=None):
    """Emit a PreToolUse hook decision in the required hookSpecificOutput envelope."""
    inner = {
        "hookEventName": "PreToolUse",
        "permissionDecision": decision,
    }
    if reason:
        inner["permissionDecisionReason"] = reason
    json.dump({"hookSpecificOutput": inner}, sys.stdout)


# ═══════════════════════════════════════════════════════════════════════════════
# Evaluate a Single Tool Call
# ═══════════════════════════════════════════════════════════════════════════════

def evaluate(tool_name, tool_input, cwd):
    """Evaluate a tool call. Returns (decision, reason, temperature, threshold, reasons)."""
    project_root = find_project_root(cwd)
    config = load_config(project_root)

    # Oracle disabled — allow everything
    if not config.get("enabled", True):
        return "allow", None, 0, config["threshold"], []

    threshold = config["threshold"]

    # Check hard blocks (deny unless YOLO mode — threshold 11)
    if check_hard_blocks(tool_name, tool_input, config):
        command = tool_input.get("command", "")
        if threshold >= 11:
            # YOLO mode: bypass hard blocks, warn on stderr, log the override
            print(
                f"⚠ YOLO MODE: hard block bypassed for '{command[:80]}'. "
                "All safety guardrails are off. Set threshold <= 10 to re-enable.",
                file=sys.stderr,
            )
            audit_log(project_root, tool_name, "yolo", 10, ["hard_block_bypassed"], command)
            return "allow", None, 10, threshold, ["hard_block_bypassed"]
        audit_log(project_root, tool_name, "deny", 10, ["hard_block"], command)
        return "deny", "Hard-blocked by The Oracle: pattern matched in command", 10, threshold, ["hard_block"]

    # Compute temperature
    temperature, base, modifier, reasons = compute_temperature(
        tool_name, tool_input, config, project_root
    )

    if temperature <= threshold:
        return "allow", None, temperature, threshold, reasons
    else:
        detail = tool_input.get("command", "") or extract_path(tool_name, tool_input)
        audit_log(project_root, tool_name, "ask", temperature, reasons, detail)
        reason_str = ", ".join(reasons) if reasons else "base"
        reason = f"Oracle temp={temperature} > threshold={threshold}: {reason_str}"
        return "ask", reason, temperature, threshold, reasons


# ═══════════════════════════════════════════════════════════════════════════════
# Diagnose Mode
# ═══════════════════════════════════════════════════════════════════════════════

DIAGNOSE_CASES = [
    ("Read safe file",          "Read",  {"file_path": "src/index.ts"},                      "allow"),
    ("Edit source file",        "Edit",  {"file_path": "src/app.ts", "old_string": "a", "new_string": "b"}, "allow"),
    ("Write new file",          "Write", {"file_path": "src/new.ts", "content": "x"},        "allow"),
    ("Bash safe (git status)",  "Bash",  {"command": "git status"},                          "allow"),
    ("Bash install (npm i)",    "Bash",  {"command": "npm install express"},                 "allow"),
    ("Bash destructive (rm)",   "Bash",  {"command": "rm -rf ./build"},                      "ask"),
    ("Task spawn",              "Task",  {"prompt": "do something", "subagent_type": "Explore"}, "allow"),
    ("Edit sensitive (.env)",   "Edit",  {"file_path": ".env", "old_string": "a", "new_string": "b"}, "allow"),
    ("Bash risky (git push)",   "Bash",  {"command": "git push origin main"},                "allow"),
]


def run_diagnose(config_path=None):
    """Run diagnostic checks and print a health report."""
    cwd = os.getcwd()
    project_root = find_project_root(cwd)
    yaml_path = config_path or (project_root / ".acos" / "config" / "oracle.yaml")

    print("=" * 60)
    print("  The Oracle — Diagnostic Report")
    print("=" * 60)
    print()

    # ── Config check ─────────────────────────────────────────────────────
    print("[Config]")
    if Path(yaml_path).is_file():
        print(f"  oracle.yaml: {yaml_path} ✓")
        try:
            raw = Path(yaml_path).read_text(encoding="utf-8")
            parsed = parse_yaml(raw)
            print(f"  Parseable:   yes ✓")
            print(f"  Enabled:     {parsed.get('enabled', True)}")
            print(f"  Threshold:   {parsed.get('threshold', 5)}")
        except Exception as e:
            print(f"  Parseable:   FAILED — {e}")
    else:
        print(f"  oracle.yaml: NOT FOUND at {yaml_path}")
        print("  Using built-in defaults.")
    print()

    config = load_config(project_root)
    threshold = config["threshold"]

    # ── Session override check ───────────────────────────────────────────
    session_path = project_root / ".acos" / "state" / "oracle-session-threshold"
    env_override = os.environ.get("ORACLE_THRESHOLD")
    if session_path.is_file():
        print(f"  Session override: {session_path.read_text().strip()} (from file)")
    elif env_override:
        print(f"  Session override: {env_override} (from ORACLE_THRESHOLD env)")
    else:
        print(f"  Session override: none")
    print(f"  Effective threshold: {threshold}")

    yolo_active = threshold >= 11
    if yolo_active:
        print()
        print("  ┌─────────────────────────────────────────────────────────┐")
        print("  │  ⚠  YOLO MODE ACTIVE (threshold=11)                    │")
        print("  │                                                         │")
        print("  │  ALL guardrails are disabled, including hard blocks.     │")
        print("  │  Commands like git push, rm -rf /, and DROP TABLE       │")
        print("  │  will be auto-approved without any prompt.              │")
        print("  │                                                         │")
        print("  │  To restore safety: set threshold to 10 or lower.       │")
        print("  └─────────────────────────────────────────────────────────┘")
    print()

    # ── Sample tool calls ────────────────────────────────────────────────
    print("[Sample Tool Calls]")
    print(f"  {'Test Case':<28s} {'Tool':<6s} {'Temp':>4s} {'Decision':<6s} {'Expected':<8s} {'Status'}")
    print(f"  {'-'*28} {'-'*6} {'-'*4} {'-'*6} {'-'*8} {'-'*6}")

    passed = 0
    failed = 0
    results = []

    for label, tool_name, tool_input, expected in DIAGNOSE_CASES:
        decision, reason, temperature, _, reasons = evaluate(tool_name, tool_input, cwd)
        # Adjust expectations for current threshold
        effective_expected = expected
        if yolo_active:
            effective_expected = "allow"  # YOLO auto-approves everything
        # For expected "ask", also accept "deny" (threshold might be very low)
        # For expected "deny", only accept "deny"
        if effective_expected == "deny":
            ok = decision == "deny"
        elif effective_expected == "ask":
            ok = decision in ("ask", "deny")
        else:
            ok = decision == effective_expected

        status = "✓" if ok else "FAIL"
        if ok:
            passed += 1
        else:
            failed += 1
        print(f"  {label:<28s} {tool_name:<6s} {temperature:>4d} {decision:<6s} {expected:<8s} {status}")
        results.append((label, tool_name, decision, expected, ok, reasons))

    print()

    # ── Permissions.allow conflict check ─────────────────────────────────
    print("[Permission Conflicts]")
    settings_path = project_root / ".claude" / "settings.local.json"
    conflicts = []
    if settings_path.is_file():
        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
            allow_list = settings.get("permissions", {}).get("allow", [])
            for entry in allow_list:
                if entry == "Bash(git:*)" or entry == "Bash(bash:*)":
                    conflicts.append(f"  ⚠ '{entry}' bypasses Oracle hard blocks (git push, rm -rf, etc.)")
                elif entry.startswith("Bash") and "*" in entry and ":" not in entry:
                    conflicts.append(f"  ⚠ '{entry}' is overly broad — may bypass Oracle")
        except Exception:
            pass

    if conflicts:
        for c in conflicts:
            print(c)
    else:
        print("  No conflicts detected ✓")
    print()

    # ── Summary ──────────────────────────────────────────────────────────
    print(f"[Summary]")
    print(f"  Passed: {passed}/{passed + failed}")
    if failed > 0:
        print(f"  Failed: {failed}/{passed + failed}")
        for label, tool_name, decision, expected, ok, reasons in results:
            if not ok:
                print(f"    → {label}: got '{decision}' expected '{expected}'")
    if conflicts:
        print(f"  Warnings: {len(conflicts)} permission conflict(s)")
    if yolo_active:
        print(f"  ⚠ YOLO mode is active — all hard blocks are bypassed")
    print()

    if failed > 0 or conflicts:
        overall = "ISSUES DETECTED"
    elif yolo_active:
        overall = "HEALTHY (⚠ YOLO — no guardrails)"
    else:
        overall = "HEALTHY"
    print(f"  Overall: {overall}")
    print()

    return failed == 0 and not conflicts


# ═══════════════════════════════════════════════════════════════════════════════
# Main Entry Point
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    # Handle --diagnose mode
    if "--diagnose" in sys.argv:
        config_path = None
        if "--config" in sys.argv:
            idx = sys.argv.index("--config")
            if idx + 1 < len(sys.argv):
                config_path = sys.argv[idx + 1]
        success = run_diagnose(config_path)
        sys.exit(0 if success else 1)

    # Normal hook mode: read from stdin, emit decision
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            emit_decision("allow")
            return

        data = json.loads(raw)
        tool_name = data.get("tool_name", "")
        tool_input = data.get("tool_input", {})
        cwd = data.get("cwd", os.getcwd())

        decision, reason, _, _, _ = evaluate(tool_name, tool_input, cwd)
        emit_decision(decision, reason)

    except Exception:
        # Fail-open: any error allows the action
        emit_decision("allow")


if __name__ == "__main__":
    main()
