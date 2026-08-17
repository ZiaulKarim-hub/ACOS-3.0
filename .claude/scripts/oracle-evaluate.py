#!/usr/bin/env python3
"""
The Oracle — Permission Governance Agent for ACOS v3.0

PreToolUse hook that evaluates tool calls on a temperature scale (0-10).
Low-temperature actions are auto-approved; high-temperature ones escalate to user.
Threshold 11 (YOLO) bypasses everything including hard blocks.

Autopilot mode (.acos/state/autopilot-active present):
  - Effective threshold raised to 11 (auto-approve everything by score)
  - BUT a dedicated AUTOPILOT_HARD_BLOCKS list always escalates regardless of threshold
  - Built-in autopilot blocks cover destructive deletes and SQL destructive ops
  - Escalation in autopilot = "ask" (user response triggers panic-stop in UserPromptSubmit hook)

Reads JSON from stdin (tool_name, tool_input, cwd).
Outputs JSON permission decision to stdout wrapped in hookSpecificOutput envelope.

Fail-open: any error defaults to allow.

Usage:
  Normal (hook):   stdin JSON → stdout decision
  Diagnose:        python3 oracle-evaluate.py --diagnose [--config path/to/oracle.yaml]
  Health check:    python3 oracle-evaluate.py --health
"""

import json
import os
import re
import sys
import shlex
from datetime import datetime, timezone
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════════════
# Minimal YAML Parser (stdlib only — no PyYAML dependency)
# Handles the 2-level structure of oracle.yaml: scalars, lists, nested dicts
# ═══════════════════════════════════════════════════════════════════════════════

def parse_yaml(text):
    """Parse the subset of YAML used by oracle.yaml — stdlib only.

    Supports: top-level scalars, nested block mappings (any consistent indent
    width), inline lists ([a, b, c]), block lists of scalars (- x), and block
    lists of flat dicts (- key: value with continuation key: value lines).

    Recursive-descent with lookahead: each block's member indent is discovered
    from its first member, so arbitrary indent widths parse correctly. This
    replaces the previous indentation-stack parser whose (indent+2, <=) frame
    handling silently dropped every nested block mapping — e.g. base_temperatures
    parsed to {} and its keys leaked to the top-level result, so any user-authored
    base_temperatures / modifiers / learning override was ignored and the Oracle
    silently fell back to the in-code DEFAULTS.
    """
    lines = []
    for raw in text.splitlines():
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        lines.append((indent, s))

    pos = 0

    def block(block_indent):
        nonlocal pos
        container = None
        while pos < len(lines):
            indent, content = lines[pos]
            if indent < block_indent:
                break
            if indent > block_indent:
                # Defensive: a deeper line with no opener — skip.
                pos += 1
                continue

            list_m = re.match(r'-\s+(.*)$', content)
            if list_m:
                if container is None:
                    container = []
                item = list_m.group(1).strip()
                pos += 1
                kv = re.match(r'([\w][\w_-]*)\s*:\s*(.*)$', item)
                if kv and not kv.group(2).strip().startswith('['):
                    d = {}
                    k, v = kv.group(1), kv.group(2).strip()
                    if v == "" or v == "|":
                        if pos < len(lines) and lines[pos][0] > indent:
                            d[k] = block(lines[pos][0])
                        else:
                            d[k] = {}
                    else:
                        d[k] = _parse_value(v)
                    # Continuation "key: value" lines for this dict item live at an
                    # indent deeper than the '-' marker and are not list items.
                    while (pos < len(lines) and lines[pos][0] > indent
                           and not re.match(r'-\s+', lines[pos][1])):
                        cind, cont = lines[pos]
                        ckv = re.match(r'([\w][\w_-]*)\s*:\s*(.*)$', cont)
                        if not ckv:
                            pos += 1
                            continue
                        ck, cv = ckv.group(1), ckv.group(2).strip()
                        pos += 1
                        if cv == "" or cv == "|":
                            if pos < len(lines) and lines[pos][0] > cind:
                                d[ck] = block(lines[pos][0])
                            else:
                                d[ck] = {}
                        else:
                            d[ck] = _parse_value(cv)
                    container.append(d)
                else:
                    container.append(_parse_value(item))
                continue

            kv = re.match(r'([\w][\w_-]*)\s*:\s*(.*)$', content)
            if not kv:
                pos += 1
                continue
            if container is None:
                container = {}
            k, v = kv.group(1), kv.group(2).strip()
            pos += 1
            if v == "" or v == "|":
                if pos < len(lines) and lines[pos][0] > indent:
                    container[k] = block(lines[pos][0])
                else:
                    container[k] = {}
            else:
                container[k] = _parse_value(v)
        return container if container is not None else {}

    result = block(0)
    return result if isinstance(result, dict) else {}


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
    """Walk up from cwd to find directory containing .acos/.

    Uses multiple fallback strategies:
      1. Walk up from CWD (provided by hook or os.getcwd())
      2. Walk up from this script's own location (__file__)
      3. Fall back to CWD as last resort
    """
    # Strategy 1: Walk up from CWD
    path = Path(cwd).resolve()
    for parent in [path] + list(path.parents):
        if (parent / ".acos").is_dir():
            return parent

    # Strategy 2: Walk up from script's own location
    # oracle-evaluate.py lives at <project>/.claude/scripts/oracle-evaluate.py
    # so walking up from __file__ should find <project>/.acos/
    try:
        script_dir = Path(__file__).resolve().parent
        for parent in [script_dir] + list(script_dir.parents):
            if (parent / ".acos").is_dir():
                return parent
    except (NameError, OSError):
        pass  # __file__ might not be defined in some execution contexts

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
            # Ceiling raised 11 -> 12 for ORACLE MODE (Zee, 2026-08-15).
            # 11 is YOLO: allow everything, blind. 12 is the rung above: nothing
            # is blind and Zee is still never asked, because Opus judges each
            # call in context. The larger number reads as "looser" but is in fact
            # stricter — 11 allows everything, 12 judges everything.
            val = int(session_threshold_path.read_text().strip())
            config["threshold"] = max(0, min(12, val))
        except (ValueError, OSError):
            pass

    # Note: ORACLE_THRESHOLD env var intentionally removed (security: H3).
    # Use .acos/state/oracle-session-threshold or .acos/config/oracle.yaml only.

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
# Autopilot Mode
# ═══════════════════════════════════════════════════════════════════════════════
#
# Patterns that get HIGH-VISIBILITY LOGGING under autopilot. The op is still
# ALLOWED to proceed (per user spec 2026-06-05) — the log file is the audit
# trail so the user can review what destructive actions autopilot performed.
#
# Explicitly UNBLOCKED per user spec 2026-06-05 (no longer in this list):
#   - find ... -delete  (trusted to Claude's judgment with explicit filters)
#   - DROP TABLE/DATABASE/SCHEMA  (entirely unblocked)
#   - TRUNCATE  (entirely unblocked)
#   - DELETE FROM <table> without WHERE  (entirely unblocked)
#
# What still gets logged (and allowed):
# NOTE: broad-target `rm` detection is handled by _command_is_destructive_rm()
# below (a tokenizer), NOT by these regexes — regex flag/quote handling kept
# leaving gaps (mixed short+long flags `rm -r --force /`, split flags
# `rm -f -r /`, quoted targets `rm -rf "/"`). The tokenizer is order- and
# quote-agnostic. These regexes cover the remaining non-rm destructive shapes.
AUTOPILOT_DESTRUCTIVE_PATTERNS = [
    # xargs rm — almost always mass deletion
    r"\bxargs\s+(-[^|]*\s+)?rm\b",
    # shred — file destruction
    r"\bshred\s+",
    # dd writing to a device or zero/null source on filesystem
    r"\bdd\s+(if|of)=/dev/(zero|null|random|urandom|sd[a-z]|nvme|disk)",
]
_AUTOPILOT_DESTRUCTIVE_REGEXES = [
    re.compile(p, re.IGNORECASE) for p in AUTOPILOT_DESTRUCTIVE_PATTERNS
]

# Broad/catastrophic rm targets (after quote-stripping). Specific subpaths like
# /tmp/x or ./build are intentionally NOT flagged — only whole-root / whole-home
# / current-or-parent-dir wipes reach the morning-review audit trail.
_BROAD_RM_TARGETS = {"/", "/*", "~", ".", ".."}
_SHELL_SEPARATORS = {";", "&&", "||", "|", "&"}


def _is_broad_rm_target(tok):
    """True if an rm argument names a catastrophic target (/, ~, $HOME, ., ..,
    or any whole-top-level-home subdir ~/x / $HOME/x). Quote-agnostic."""
    if len(tok) >= 2 and tok[0] == tok[-1] and tok[0] in ("'", '"'):
        tok = tok[1:-1]
    t = tok.strip()
    if t in _BROAD_RM_TARGETS:
        return True
    if t == "~" or t.startswith("~/"):
        return True
    if t in ("$HOME", "${HOME}") or t.startswith("$HOME/") or t.startswith("${HOME}/"):
        return True
    # bare root with trailing slashes (e.g. "//"), or "/*"
    if t and t.rstrip("/") == "":
        return True
    return False


def _command_is_destructive_rm(command):
    """Order- and quote-agnostic detection of `rm` with a recursive (or
    --no-preserve-root) flag against a broad/catastrophic target. Replaces the
    prior regex set, which missed mixed/split short+long flags and quoted
    targets. Log-and-allow (per spec) — this just ensures the audit trail is
    complete. Scans every `rm` occurrence in a compound command."""
    if "rm" not in command:
        return False
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        tokens = command.split()
    i, n = 0, len(tokens)
    while i < n:
        base = tokens[i].rsplit("/", 1)[-1]
        if base == "rm":
            recursive = False
            broad = False
            j = i + 1
            while j < n and tokens[j] not in _SHELL_SEPARATORS:
                a = tokens[j]
                if a == "--":
                    pass
                elif a.startswith("--"):
                    if a in ("--recursive", "--no-preserve-root"):
                        recursive = True
                elif a.startswith("-") and len(a) > 1:
                    if "r" in a or "R" in a:
                        recursive = True
                elif _is_broad_rm_target(a):
                    broad = True
                j += 1
            if recursive and broad:
                return True
            i = j
        else:
            i += 1
    return False

# Kept for backward-compat with anything reading the old name; same content.
AUTOPILOT_HARD_BLOCKS = AUTOPILOT_DESTRUCTIVE_PATTERNS
_AUTOPILOT_HARD_BLOCK_REGEXES = _AUTOPILOT_DESTRUCTIVE_REGEXES


def load_autopilot_state(project_root):
    """Return parsed autopilot state dict, or None if autopilot is OFF."""
    sentinel = project_root / ".acos" / "state" / "autopilot-active"
    if not sentinel.is_file():
        return None
    try:
        return json.loads(sentinel.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def check_autopilot_hard_blocks(tool_name, tool_input):
    """Return (matched, pattern) for patterns that warrant high-visibility logging
    under autopilot. Patterns no longer DENY — they log + allow per user spec."""
    if tool_name != "Bash":
        return False, None
    command = tool_input.get("command", "")
    if not command:
        return False, None
    # Tokenizer-based broad-rm detection (order/quote-agnostic) first.
    if _command_is_destructive_rm(command):
        return True, "rm-recursive-broad-target"
    for pat, regex in zip(AUTOPILOT_DESTRUCTIVE_PATTERNS, _AUTOPILOT_DESTRUCTIVE_REGEXES):
        try:
            if regex.search(command):
                return True, pat
        except re.error:
            continue
    return False, None


def log_destructive_op(project_root, autopilot_state, command, pattern):
    """Append a high-visibility line to requested-destructive.log."""
    log_path = project_root / ".acos" / "state" / "requested-destructive.log"
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        goal = autopilot_state.get("goal", "<unknown>") if autopilot_state else "<unknown>"
        iters = autopilot_state.get("iteration_count", "?") if autopilot_state else "?"
        max_i = autopilot_state.get("max_iterations", "?") if autopilot_state else "?"
        line = (
            f"[{ts}] iter={iters}/{max_i} | pattern={pattern[:50]} | "
            f"goal={goal[:80]} | cmd={command}"
        )
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


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
# Trailing (\s|$|;|\||&) boundary prevents prefix matches: without it,
# "catalog" matched "cat", "lshw" matched "ls", "datetime" matched "date" —
# all wrongly receiving the info_cmd -3 discount.
INFO_BASH = re.compile(
    r'^(git\s+(status|log|diff|branch|remote|show|tag)|ls|pwd|echo|cat|head|tail|wc|which|type|env|printenv|whoami|date|uname)(\s|$|;|\||&)',
    re.IGNORECASE
)
# A write redirection (`>`, `>>`, `1>`, `2>>`, `&>`, `>|`, `| tee`/`|tee`) means the
# command performs a write even if it leads with a "safe" info verb — used to
# suppress the info_cmd discount. An OPTIONAL leading fd digit is allowed so that
# `ls 1>out` / `echo a 2> err.txt` (real file writes) are counted, matching what
# check-scope-bash.sh treats as a write. The trailing `(?![&])` still excludes the
# fd-dup form `N>&M` (`>&`, `2>&1`) which redirects to a descriptor, not a file.
WRITE_REDIRECT_BASH = re.compile(
    r'(?<![&])\d?>>?(?![&])|&>>?|>\||\|\s*tee\b',
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
            # Suppress the safe-command discount when the command also performs a
            # write — a leading safe verb (echo/cat/head/...) followed by a write
            # redirection (`>`, `>>`, `| tee`) or a destructive op is NOT safe.
            if not (WRITE_REDIRECT_BASH.search(command) or DESTRUCTIVE_BASH.search(command)):
                modifier -= 3
                reasons.append("info_cmd -3")

    # ── In-scope file modifier ────────────────────────────────────────────
    if path:
        active_slice = project_root / ".acos" / "config" / "active-slice.yaml"
        if active_slice.is_file():
            try:
                slice_text = active_slice.read_text(encoding="utf-8")
                # Hook inputs carry ABSOLUTE paths while active-slice.yaml
                # stores repo-relative ones — test both forms or the discount
                # never applies in practice.
                rel_path = None
                if os.path.isabs(path):
                    try:
                        rel_path = os.path.relpath(path, project_root)
                    except ValueError:
                        rel_path = None
                if path in slice_text or (rel_path and rel_path in slice_text):
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
    """Append to oracle-audit.log for escalations, denials, YOLO bypasses, and
    autopilot destructive-logged events."""
    if decision == "allow":
        return  # Only log escalations, denials, YOLO bypasses, and destructive_logged
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

def evaluate(tool_name, tool_input, cwd, context=""):
    """Evaluate a tool call. Returns (decision, reason, temperature, threshold, reasons)."""
    project_root = find_project_root(cwd)
    config = load_config(project_root)

    # Oracle disabled — allow everything
    if not config.get("enabled", True):
        return "allow", None, 0, config["threshold"], []

    threshold = config["threshold"]

    # ── Oracle's own judging session (recursion guard) ─────────────────────────
    # In Oracle mode the judge IS a Claude Code session, and it loads this very
    # hook. Its first Read would ask the Oracle, which would spawn another judge,
    # forever. The child carries a secret matching a 0600 file only the daemon
    # writes, so this is not a flag anything can set (security: H3).
    try:
        import sys as _sys
        _sys.path.insert(0, str(Path(__file__).resolve().parent))
        from _oracle_judge import is_oracle_child
        if is_oracle_child():
            return "allow", None, 0, threshold, ["oracle_judge_session"]
    except Exception:
        pass

    # ── Eternity-protocol subordination (precedence over Oracle) ───────────────
    # Per user spec 2026-06-15: Oracle Protocol is NEVER above Eternity Protocol.
    # When any project-scoped in-flight eternity marker exists (daemon arming,
    # pending-resume, clear-requested, compact-fired), Oracle stands down
    # entirely — no threshold scoring, no autopilot logic, no destructive
    # logging. Tool calls pass through with a plain allow. Oracle resumes its
    # normal behavior as soon as the markers clear.
    try:
        import sys as _sys
        _sys.path.insert(0, str(Path(__file__).resolve().parent))
        from _autopilot_eternity import is_eternity_protocol_active
        if is_eternity_protocol_active(cwd):
            return "allow", None, 0, threshold, ["eternity_subordinate"]
    except Exception:
        # Fail-open: if subordination check itself errors, proceed with
        # normal Oracle logic. Better than locking out tool calls.
        pass

    # ── ORACLE MODE (threshold 12) ─────────────────────────────────────────────
    # Opus judges the call in context. Placed ABOVE the hard-block list on
    # purpose: Zee's whole point is that a hardcoded list cannot tell a needed
    # `rm` from a harmful one, so at 12 the list does not get a vote. There is
    # also no scoring here — temperature is the old regex Oracle, and this rung
    # replaces it rather than layering on top.
    #
    # Deliberately NOT fail-open. Zee, 2026-08-15: "fall back to yolo is not good
    # because in that case, having the oracle mode would be useless." _oracle_judge
    # walks socket -> autostart -> direct -> retry, and only refuses when every
    # one of those failed — a refusal that names exactly what broke.
    # Oracle mode is a SWITCH, not rung 12 (Zee, 2026-08-16: "12 is actually the
    # wrong number for this"). The dial measures LOOSENESS and the Oracle is not
    # looser than anything, so putting it on the dial would have mis-taught the
    # one thing the dial is for. It now sits in its own state file, and 12 goes
    # back to meaning YOLO.
    _mode = None
    try:
        import sys as _sys
        _sys.path.insert(0, str(Path(__file__).resolve().parent))
        from _oracle_judge import load_mode
        _mode = load_mode(project_root)
    except Exception:
        _mode = None

    if _mode:
        try:
            from _oracle_judge import consult
            decision, why, layer = consult(
                tool_name, tool_input, cwd, context,
                str(Path(__file__).resolve().parent),
                _mode.get("goal", ""),
            )
            reasons = [f"oracle:{layer}"]
            if decision == "deny":
                audit_log(project_root, tool_name, "deny", 0, reasons,
                          tool_input.get("command", ""))
                return "deny", f"The Oracle: {why}", 0, threshold, reasons
            return "allow", None, 0, threshold, reasons
        except Exception as e:
            # Importing or calling the judge blew up — which is itself an
            # unreachable Oracle. Refuse rather than wave it through, and say why.
            return (
                "deny",
                f"The Oracle could not be consulted ({type(e).__name__}: {str(e)[:120]}). "
                "Oracle mode allows nothing it has not judged. "
                "Set threshold <= 11 to leave Oracle mode.",
                0, threshold, ["oracle_error"],
            )

    # ── Autopilot short-circuit ────────────────────────────────────────────────
    # When autopilot is active: log high-impact destructive patterns to
    # requested-destructive.log (audit trail for morning review) but still
    # ALLOW them to proceed per user spec 2026-06-05. Auto-approve everything
    # else regardless of base threshold.
    autopilot = load_autopilot_state(project_root)
    if autopilot:
        matched, pattern = check_autopilot_hard_blocks(tool_name, tool_input)
        if matched:
            command = tool_input.get("command", "")
            log_destructive_op(project_root, autopilot, command, pattern)
            reasons = [f"autopilot_destructive_logged:{pattern[:40]}"]
            audit_log(project_root, tool_name, "destructive_logged", 10, reasons, command)
            # ALLOW per user spec — log is the safeguard, not denial
            return "allow", None, 0, 11, reasons
        # Everything else under autopilot: allow silently
        return "allow", None, 0, 11, ["autopilot_allow"]

    # Check hard blocks (deny unless YOLO mode — threshold 11)
    if check_hard_blocks(tool_name, tool_input, config):
        command = tool_input.get("command", "")
        # YOLO moved 11 -> 12 (Zee, 2026-08-16). 11 is now AUTOPILOT: allow, but
        # write the truly destructive ones down. 12 is the only rung that allows
        # everything and records nothing, so it is the only one that may bypass
        # a hard block. The ladder stays honest: higher is looser, all the way up.
        if threshold >= 12:
            # YOLO mode: bypass hard blocks, warn on stderr, log the override
            print(
                f"⚠ YOLO MODE: hard block bypassed for '{command[:80]}'. "
                "All safety guardrails are off. Set threshold <= 11 to re-enable.",
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
            print(f"  Threshold:   {parsed.get('threshold', DEFAULTS['threshold'])}")
        except Exception as e:
            print(f"  Parseable:   FAILED — {e}")
    else:
        print(f"  oracle.yaml: NOT FOUND at {yaml_path}")
        print("  Using built-in defaults.")
    print()

    config = load_config(project_root)
    threshold = config["threshold"]

    # ── Session override check ───────────────────────────────────────────
    # NOTE: ORACLE_THRESHOLD env var was intentionally removed from load_config
    # (security fix) — it has NO effect, so it is NOT reported here as an override.
    session_path = project_root / ".acos" / "state" / "oracle-session-threshold"
    if session_path.is_file():
        print(f"  Session override: {session_path.read_text().strip()} (from file)")
    else:
        print(f"  Session override: none")
    print(f"  Effective threshold: {threshold}")

    yolo_active = threshold >= 11

    # Autopilot short-circuits evaluate() to allow for everything (see evaluate()),
    # so every diagnose case is EXPECTED to be 'allow' while autopilot is active.
    # Without this, the 'Bash destructive (rm)' case (expected 'ask') reports a
    # false FAIL even though the Oracle is behaving per autopilot spec.
    autopilot_active = load_autopilot_state(project_root) is not None

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
    if autopilot_active:
        print()
        print("  ┌─────────────────────────────────────────────────────────┐")
        print("  │  ⚠  AUTOPILOT ACTIVE (.acos/state/autopilot-active)     │")
        print("  │                                                         │")
        print("  │  evaluate() short-circuits to ALLOW for every call.      │")
        print("  │  All sample cases are expected to 'allow' accordingly.   │")
        print("  │  Escalations surface as 'ask' → panic-stop in autopilot. │")
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
        if yolo_active or autopilot_active:
            effective_expected = "allow"  # YOLO/autopilot auto-approve everything
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
    if autopilot_active:
        print(f"  ⚠ Autopilot is active — every call auto-approves (expected 'allow')")
    print()

    if failed > 0 or conflicts:
        overall = "ISSUES DETECTED"
    elif autopilot_active:
        overall = "HEALTHY (⚠ AUTOPILOT — all calls auto-approved)"
    elif yolo_active:
        overall = "HEALTHY (⚠ YOLO — no guardrails)"
    else:
        overall = "HEALTHY"
    print(f"  Overall: {overall}")
    print()

    return failed == 0 and not conflicts


# ═══════════════════════════════════════════════════════════════════════════════
# Health Check Mode
# ═══════════════════════════════════════════════════════════════════════════════

def run_health():
    """Quick health check — verifies all Oracle dependencies are available."""
    cwd = os.getcwd()
    root = find_project_root(cwd)
    checks = []

    # Check 1: Project root found
    acos_dir = root / ".acos"
    checks.append(("Project root (.acos/)", acos_dir.is_dir(), str(root)))

    # Check 2: Oracle config
    config_path = root / ".acos" / "config" / "oracle.yaml"
    checks.append(("Oracle config", config_path.is_file(), str(config_path)))

    # Check 3: State directory writable
    state_dir = root / ".acos" / "state"
    writable = False
    try:
        state_dir.mkdir(parents=True, exist_ok=True)
        writable = os.access(str(state_dir), os.W_OK)
    except OSError:
        pass
    checks.append(("State dir writable", writable, str(state_dir)))

    # Check 4: Config parseable
    config_ok = True
    config_detail = "N/A (no config file)"
    if config_path.is_file():
        try:
            raw = config_path.read_text(encoding="utf-8")
            parsed = parse_yaml(raw)
            config_detail = f"threshold={parsed.get('threshold', '?')}, enabled={parsed.get('enabled', '?')}"
        except Exception as e:
            config_ok = False
            config_detail = f"parse error: {e}"
    checks.append(("Config parseable", config_ok, config_detail))

    # Check 5: Hook command will work (no git dependency)
    settings_path = root / ".claude" / "settings.local.json"
    hook_ok = True
    hook_detail = "settings.local.json not found"
    if settings_path.is_file():
        try:
            content = settings_path.read_text(encoding="utf-8")
            if "git rev-parse" in content:
                hook_ok = False
                hook_detail = "STILL has git rev-parse dependency — hooks will fail outside git repos"
            else:
                hook_detail = "no git dependency (good)"
        except OSError as e:
            hook_ok = False
            hook_detail = f"read error: {e}"
    checks.append(("Hook resilience", hook_ok, hook_detail))

    all_ok = all(ok for _, ok, _ in checks)

    print("Oracle Health Check")
    print("=" * 40)
    for name, ok, detail in checks:
        status = "OK" if ok else "FAIL"
        print(f"  [{status:4s}] {name}: {detail}")
    print()
    print(f"Status: {'HEALTHY' if all_ok else 'ISSUES DETECTED'}")

    return all_ok


# ═══════════════════════════════════════════════════════════════════════════════
# Main Entry Point
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    # Handle --health mode (quick dependency check)
    if "--health" in sys.argv:
        success = run_health()
        sys.exit(0 if success else 1)

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

        # The recent conversation, so the Oracle judges the command IN CONTEXT
        # rather than as a bare string (Zee: "command plus the recent chat").
        # Only read when Oracle mode could actually use it — an ordinary session
        # must not pay transcript I/O on every single tool call.
        context = ""
        try:
            tpath = data.get("transcript_path", "")
            if tpath and os.path.isfile(tpath):
                with open(tpath, "r", encoding="utf-8", errors="replace") as f:
                    tail = f.readlines()[-40:]
                parts = []
                for line in tail:
                    try:
                        ev = json.loads(line)
                    except ValueError:
                        continue
                    msg = ev.get("message", {})
                    role = msg.get("role", "")
                    if role not in ("user", "assistant"):
                        continue
                    content = msg.get("content", "")
                    if isinstance(content, list):
                        content = " ".join(
                            c.get("text", "") for c in content if isinstance(c, dict)
                        )
                    if content:
                        parts.append(f"{role}: {str(content)[:1200]}")
                context = "\n".join(parts[-12:])
        except Exception:
            context = ""  # context is a nicety; never let it break the hook

        decision, reason, _, _, _ = evaluate(tool_name, tool_input, cwd, context)
        emit_decision(decision, reason)

    except Exception:
        # Fail-open: any error allows the action
        emit_decision("allow")


if __name__ == "__main__":
    main()
