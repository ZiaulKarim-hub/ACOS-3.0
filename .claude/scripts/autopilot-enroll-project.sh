#!/bin/bash
# autopilot-enroll-project.sh
#
# Enrolls a target Claude Code project in ACOS Oracle Autopilot:
#   1. Verifies the target directory exists and looks like a Claude Code project
#   2. Symlinks required autopilot scripts from this ACOS 3.0 source repo (if missing)
#   3. Idempotently registers the autopilot hooks in target's .claude/settings.local.json
#   4. Creates .acos/state/ if missing so SessionEnd cleanup works
#   5. Runs the pre-flight OK/MISS matrix and reports
#
# Usage:
#   autopilot-enroll-project.sh                 # enroll current directory
#   autopilot-enroll-project.sh /path/to/proj   # enroll specific project
#
# Idempotent: safe to re-run. Skips anything already in place.
# Fail-loud: exits non-zero on any pre-flight failure so calling scripts can detect.

set -euo pipefail

TARGET="${1:-$PWD}"

# Resolve ACOS source from this script's own location (.claude/scripts/<me>.sh)
ACOS_SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# ── Validate target ─────────────────────────────────────────────────────────
if [[ ! -d "$TARGET" ]]; then
    echo "ERROR: target path does not exist: $TARGET" >&2
    exit 1
fi
TARGET=$(cd "$TARGET" && pwd)

if [[ ! -f "$ACOS_SRC/.claude/scripts/oracle-evaluate.py" ]]; then
    echo "ERROR: ACOS source not found at expected location: $ACOS_SRC" >&2
    echo "       (script must run from ACOS 3.0 .claude/scripts/ directory)" >&2
    exit 1
fi

echo "Target:     $TARGET"
echo "ACOS src:   $ACOS_SRC"
echo ""

if [[ "$TARGET" = "$ACOS_SRC" ]]; then
    echo "Target IS the ACOS source repo — autopilot is already wired here. Nothing to do."
    exit 0
fi

# ── Symlink autopilot scripts ────────────────────────────────────────────────
mkdir -p "$TARGET/.claude/scripts"
mkdir -p "$TARGET/.acos/state"

SCRIPTS=(
    autopilot-askuserquestion-handler.py
    autopilot-allow-extra-tools.py
    autopilot-context-injector.py
    autopilot-stop-handler.py
    oracle-evaluate.py
    session-cleanup.sh
)

# Detect whether .claude/scripts itself is a symlink to ACOS src's dir
SCRIPTS_DIR="$TARGET/.claude/scripts"
if [[ -L "$SCRIPTS_DIR" ]]; then
    RESOLVED=$(cd "$SCRIPTS_DIR" && pwd -P)
    if [[ "$RESOLVED" = "$ACOS_SRC/.claude/scripts" ]]; then
        echo "Scripts dir is symlinked to ACOS source — all scripts auto-resolved ✓"
    fi
fi

echo "Script symlinks:"
for script in "${SCRIPTS[@]}"; do
    src="$ACOS_SRC/.claude/scripts/$script"
    dst="$SCRIPTS_DIR/$script"
    if [[ ! -f "$src" ]]; then
        echo "  ✗ source missing: $src" >&2
        exit 1
    fi
    if [[ -e "$dst" ]] || [[ -L "$dst" ]]; then
        if [[ -L "$dst" ]] && [[ "$(readlink "$dst")" = "$src" ]]; then
            echo "  ○ $script (already correctly symlinked)"
        elif [[ -L "$dst" ]]; then
            ln -sfn "$src" "$dst"
            echo "  ↻ $script (re-pointed)"
        else
            # Real file or directory already present — leave it
            echo "  ○ $script (file present, not a symlink — left as-is)"
        fi
    else
        ln -s "$src" "$dst"
        echo "  + $script (symlinked from source)"
    fi
done
echo ""

# ── Patch settings.local.json (backup first) ────────────────────────────────
SETTINGS="$TARGET/.claude/settings.local.json"
if [[ -f "$SETTINGS" ]]; then
    BACKUP="$SETTINGS.bak-pre-autopilot-enroll-$(date +%s)"
    cp "$SETTINGS" "$BACKUP"
    echo "Settings backup: $BACKUP"
fi

echo "Hook registration:"
# Guard against set -e: the heredoc python may sys.exit(1) on pre-flight failure,
# which would otherwise abort the script before PY_RC capture + diagnostic block.
set +e
python3 - <<PY
import json, sys
from pathlib import Path

settings_path = Path("$SETTINGS")
if settings_path.is_file():
    s = json.loads(settings_path.read_text(encoding="utf-8"))
else:
    s = {}
hooks = s.setdefault("hooks", {})

def script_already_registered(event, script_basename):
    for e in hooks.get(event, []):
        for h in e.get("hooks", []):
            if script_basename in h.get("command", ""):
                return True
    return False

ALLOW_FALLBACK = (
    "|| printf '{\"hookSpecificOutput\":{\"hookEventName\":"
    "\"PreToolUse\",\"permissionDecision\":\"allow\"}}'"
)
UPS_FALLBACK = (
    "|| printf '{\"hookSpecificOutput\":{\"hookEventName\":\"UserPromptSubmit\"}}'"
)

DESIRED = [
    ("PreToolUse", "Bash|Write|Edit|NotebookEdit|Task", "oracle-evaluate.py",
     f"python3 .claude/scripts/oracle-evaluate.py 2>/dev/null {ALLOW_FALLBACK}", False),
    ("PreToolUse", "AskUserQuestion|ExitPlanMode", "autopilot-askuserquestion-handler.py",
     f"python3 .claude/scripts/autopilot-askuserquestion-handler.py 2>/dev/null {ALLOW_FALLBACK}", False),
    ("PreToolUse", "WebFetch|WebSearch|mcp__.*", "autopilot-allow-extra-tools.py",
     f"python3 .claude/scripts/autopilot-allow-extra-tools.py 2>/dev/null {ALLOW_FALLBACK}", False),
    ("UserPromptSubmit", "*", "autopilot-context-injector.py",
     f"python3 .claude/scripts/autopilot-context-injector.py 2>/dev/null {UPS_FALLBACK}", True),
    ("Stop", "*", "autopilot-stop-handler.py",
     "python3 .claude/scripts/autopilot-stop-handler.py 2>/dev/null || true", False),
    ("SessionEnd", "*", "session-cleanup.sh",
     ".claude/scripts/session-cleanup.sh 2>/dev/null || true", False),
]

added = 0
skipped = 0
for event, matcher, script, command, prepend in DESIRED:
    if script_already_registered(event, script):
        print(f"  ○ {event}[*] {script} (already registered)")
        skipped += 1
        continue
    entries = hooks.setdefault(event, [])
    new = {"matcher": matcher, "hooks": [{"type": "command", "command": command}]}
    if prepend:
        entries.insert(0, new)
    else:
        entries.append(new)
    print(f"  + {event}[{matcher}] {script} (added)")
    added += 1

if added > 0:
    out = json.dumps(s, indent=2)
    json.loads(out)  # validate
    settings_path.write_text(out, encoding="utf-8")
    print(f"\n  → wrote {settings_path}")
elif skipped == len(DESIRED):
    print("\n  (no changes — all autopilot hooks already registered)")

# Pre-flight matrix
print()
print("Pre-flight check:")
required = [
    ("PreToolUse", "oracle-evaluate.py"),
    ("PreToolUse", "autopilot-askuserquestion-handler.py"),
    ("PreToolUse", "autopilot-allow-extra-tools.py"),
    ("UserPromptSubmit", "autopilot-context-injector.py"),
    ("Stop", "autopilot-stop-handler.py"),
    ("SessionEnd", "session-cleanup.sh"),
]
fail = 0
for ev, script in required:
    hit = any(script in h.get("command", "")
              for e in s["hooks"].get(ev, []) for h in e.get("hooks", []))
    status = "OK " if hit else "MISS"
    if not hit:
        fail += 1
    print(f"  [{status}] {ev:18} | {script}")

sys.exit(1 if fail else 0)
PY

PY_RC=$?
set -e  # restore strict mode after capturing the python exit code
echo ""
if [[ $PY_RC -ne 0 ]]; then
    echo "✗ Pre-flight FAILED. Inspect $SETTINGS manually." >&2
    exit 1
fi

echo "✓ Project enrolled: $TARGET"
echo "  Now in a Claude Code session running in this project, activate with:"
echo "    /acos-oracle-protocol autopilot-on <your goal>"
