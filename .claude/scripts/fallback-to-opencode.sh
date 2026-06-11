#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
# fallback-to-opencode.sh — Seamless fallback from Claude Code to OpenCode
# ═══════════════════════════════════════════════════════════════════════════════
#
# When Claude Code runs out of session/context, this script:
#   1. Finds the latest handoff document
#   2. Formats it as an OpenCode-compatible prompt
#   3. Launches OpenCode with GLM-5, pre-loaded with the handoff context
#
# Usage:
#   ./fallback-to-opencode.sh                  # Auto-detect latest handoff
#   ./fallback-to-opencode.sh <handoff-file>   # Use specific handoff
#   ./fallback-to-opencode.sh --dry-run        # Show what would happen, don't launch
#
# Requirements:
#   - opencode installed (brew install opencode)
#   - doppler configured for this project (doppler setup)
#   - OPENROUTER_API_KEY available (via Doppler or environment)
#
# ═══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────────────
MODEL="${OPENCODE_FALLBACK_MODEL:-openrouter/z-ai/glm-5}"
HANDOFF_DIR=""
DRY_RUN=false
HANDOFF_FILE=""

# ── Resolve project root ─────────────────────────────────────────────────────
# Use current working directory as project root (works from any project)
# Falls back to script location if CWD has no memory/handoffs
PROJECT_ROOT="$(pwd)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# ── Parse arguments ───────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run)  DRY_RUN=true; shift ;;
        --model)    MODEL="$2"; shift 2 ;;
        -h|--help)
            echo "Usage: fallback-to-opencode.sh [options] [handoff-file]"
            echo ""
            echo "Options:"
            echo "  --dry-run      Show what would happen without launching"
            echo "  --model MODEL  Override model (default: openrouter/z-ai/glm-5)"
            echo "  -h, --help     Show this help"
            echo ""
            echo "Examples:"
            echo "  fallback-to-opencode.sh                    # Auto-detect latest handoff"
            echo "  fallback-to-opencode.sh --model openrouter/z-ai/glm-4.7"
            echo "  fallback-to-opencode.sh memory/handoffs/my-handoff.yaml"
            exit 0
            ;;
        *)
            if [[ -f "$1" ]]; then
                HANDOFF_FILE="$1"
            else
                echo "Error: File not found: $1" >&2
                exit 1
            fi
            shift
            ;;
    esac
done

# ── Find latest handoff ──────────────────────────────────────────────────────
find_latest_handoff() {
    local search_dirs=()

    # Check CWD-relative handoffs first (any project)
    if [[ -d "$PROJECT_ROOT/memory/handoffs" ]]; then
        search_dirs+=("$PROJECT_ROOT/memory/handoffs")
    fi

    # If CWD has no handoffs, try the ACOS script's own project as fallback
    if [[ "${#search_dirs[@]}" -eq 0 && -d "$SCRIPT_PROJECT_ROOT/memory/handoffs" ]]; then
        search_dirs+=("$SCRIPT_PROJECT_ROOT/memory/handoffs")
        PROJECT_ROOT="$SCRIPT_PROJECT_ROOT"
    fi

    # Also check auto-memory location for CWD project
    local slug
    slug="$(echo "$PROJECT_ROOT" | sed 's|/|-|g; s| |-|g; s|\.|-|g')"
    local auto_memory_dir="$HOME/.claude/projects/$slug/memory/handoffs"
    if [[ -d "$auto_memory_dir" ]]; then
        search_dirs+=("$auto_memory_dir")
    fi

    local latest=""
    local latest_time=0

    for dir in "${search_dirs[@]}"; do
        [[ -d "$dir" ]] || continue
        while IFS= read -r -d '' file; do
            # Skip completed/archived handoffs. Completed handoffs are written
            # QUOTED (status: "completed"); match both quoted and unquoted forms.
            if grep -Eq 'status:[[:space:]]*"?completed"?' "$file" 2>/dev/null; then
                continue
            fi
            local mtime
            mtime=$(stat -f %m "$file" 2>/dev/null || stat -c %Y "$file" 2>/dev/null || echo 0)
            if (( mtime > latest_time )); then
                latest_time=$mtime
                latest="$file"
            fi
            # 2026-06-11 fix: exclude eternity `.resume.md` siblings — they are
            # resume-PROMPT copies, NOT session handoffs. Including them launches
            # the fallback pre-loaded with a resume template instead of context.
        done < <(find "$dir" -maxdepth 1 \( -name '*.yaml' -o -name '*.yml' -o -name '*.md' \) ! -name '*.resume.md' -print0 2>/dev/null)
    done

    echo "$latest"
}

if [[ -z "$HANDOFF_FILE" ]]; then
    HANDOFF_FILE=$(find_latest_handoff)
fi

if [[ -z "$HANDOFF_FILE" || ! -f "$HANDOFF_FILE" ]]; then
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║  No active handoff found.                                  ║"
    echo "║  Launching OpenCode without context.                       ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    if $DRY_RUN; then
        echo "[DRY RUN] Would run: doppler run -- opencode -m $MODEL"
        exit 0
    fi
    cd "$PROJECT_ROOT"
    exec doppler run -- opencode -m "$MODEL"
fi

# ── Build the handoff prompt ─────────────────────────────────────────────────
HANDOFF_CONTENT=$(cat "$HANDOFF_FILE")
PROMPT="I'm continuing work from a previous Claude Code session that ran out of context. Here is the handoff document from that session:

---
$HANDOFF_CONTENT
---

Please read the handoff above carefully and continue the work described. Start by:
1. Understanding what was accomplished so far
2. Identifying the next steps listed
3. Asking me if I want to proceed with those next steps or do something different"

# ── Display summary ──────────────────────────────────────────────────────────
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  ACOS → OpenCode Fallback                                  ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║  Handoff:  $(basename "$HANDOFF_FILE")"
echo "║  Model:    $MODEL"
echo "║  Project:  $(basename "$PROJECT_ROOT")"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

if $DRY_RUN; then
    echo "[DRY RUN] Would launch OpenCode with the following prompt:"
    echo "---"
    echo "$PROMPT" | head -20
    echo "... (truncated)"
    echo "---"
    exit 0
fi

# ── Launch OpenCode ──────────────────────────────────────────────────────────
cd "$PROJECT_ROOT"
exec doppler run -- opencode -m "$MODEL" --prompt "$PROMPT"
