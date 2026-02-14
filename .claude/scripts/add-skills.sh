#!/bin/bash

# ═══════════════════════════════════════════════════════════════════════════
# ACOS v3.0 - Add Skills to Current Project
# ═══════════════════════════════════════════════════════════════════════════
#
# Usage:
#   add-skills.sh [skill1] [skill2] ...   # Link specific skills by name
#   add-skills.sh --list                  # Show available (unlinked) skills
#   add-skills.sh --all                   # Link all available skills
#
# If no arguments given, shows an interactive numbered menu.
# Reads ACOS source path from .acos/config/project.yaml.
#
# ═══════════════════════════════════════════════════════════════════════════

set -e

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
DIM='\033[2m'
BOLD='\033[1m'
NC='\033[0m'

# ── Resolve ACOS source ────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# If this script is a symlink (running from a project), resolve the real path
if [[ -L "${BASH_SOURCE[0]}" ]]; then
    REAL_SCRIPT="$(readlink "${BASH_SOURCE[0]}")"
    # Handle relative symlinks
    if [[ "$REAL_SCRIPT" != /* ]]; then
        REAL_SCRIPT="$SCRIPT_DIR/$REAL_SCRIPT"
    fi
    ACOS_ROOT="$(cd "$(dirname "$REAL_SCRIPT")/../.." && pwd)"
else
    ACOS_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
fi

PROJECT_DIR="$(pwd)"

if [[ ! -d "$ACOS_ROOT/.claude/skills" ]]; then
    echo -e "${YELLOW}Cannot find ACOS source at $ACOS_ROOT${NC}"
    exit 1
fi

# ── Collect available (unlinked) skills ─────────────────────────────────

AVAILABLE=()
AVAILABLE_DESCS=()

for skill_dir in "$ACOS_ROOT/.claude/skills"/*/; do
    name="$(basename "$skill_dir")"
    dest="$PROJECT_DIR/.claude/skills/$name"

    # Skip skills that are already linked or exist locally
    [[ -e "$dest" ]] && continue

    # Read description from SKILL.md frontmatter
    desc=$(sed -n 's/^description: *//p' "$skill_dir/SKILL.md" 2>/dev/null | head -1)
    AVAILABLE+=("$name")
    AVAILABLE_DESCS+=("$desc")
done

if [[ ${#AVAILABLE[@]} -eq 0 ]]; then
    echo -e "${GREEN}All available skills are already linked.${NC}"
    exit 0
fi

# ── Handle arguments ────────────────────────────────────────────────────

link_skill() {
    local name="$1"
    local src="$ACOS_ROOT/.claude/skills/$name"
    local dest="$PROJECT_DIR/.claude/skills/$name"

    if [[ ! -d "$src" ]]; then
        echo -e "  ${YELLOW}⚠${NC} Unknown skill: $name"
        return 1
    fi

    if [[ -e "$dest" ]]; then
        echo -e "  ${DIM}·${NC} $name ${DIM}(already linked)${NC}"
        return 0
    fi

    mkdir -p "$PROJECT_DIR/.claude/skills"
    ln -s "$src" "$dest"
    echo -e "  ${GREEN}✓${NC} Linked $name"

    # Update .gitignore
    if [[ -f "$PROJECT_DIR/.gitignore" ]]; then
        if ! grep -qF ".claude/skills/$name" "$PROJECT_DIR/.gitignore" 2>/dev/null; then
            if grep -qF "# End ACOS 3.0" "$PROJECT_DIR/.gitignore" 2>/dev/null; then
                sed -i '' "s|# End ACOS 3.0|.claude/skills/$name\n# End ACOS 3.0|" "$PROJECT_DIR/.gitignore"
            else
                echo ".claude/skills/$name" >> "$PROJECT_DIR/.gitignore"
            fi
        fi
    fi
}

case "${1:-}" in
    --list)
        echo -e "${BOLD}Available skills (not yet linked):${NC}"
        echo ""
        for i in "${!AVAILABLE[@]}"; do
            printf "  ${BOLD}%-28s${NC} %s\n" "${AVAILABLE[$i]}" "${AVAILABLE_DESCS[$i]}"
        done
        echo ""
        exit 0
        ;;
    --all)
        echo -e "${BOLD}Linking all available skills...${NC}"
        for name in "${AVAILABLE[@]}"; do
            link_skill "$name"
        done
        echo ""
        exit 0
        ;;
    "")
        # Interactive mode — show numbered menu
        echo -e "${BOLD}Available skills (not yet linked):${NC}"
        echo ""
        for i in "${!AVAILABLE[@]}"; do
            printf "  ${CYAN}%2d${NC}) ${BOLD}%-28s${NC} %s\n" "$((i+1))" "${AVAILABLE[$i]}" "${AVAILABLE_DESCS[$i]}"
        done
        echo ""
        read -r -p "  Enter numbers to add (e.g. 1,3,5), 'all', or Enter to skip: " SELECTION
        [[ -z "$SELECTION" ]] && exit 0

        if [[ "$SELECTION" == "all" ]]; then
            for name in "${AVAILABLE[@]}"; do
                link_skill "$name"
            done
        else
            IFS=',' read -ra NUMS <<< "$SELECTION"
            for num in "${NUMS[@]}"; do
                num=$(echo "$num" | tr -d ' ')
                if [[ "$num" =~ ^[0-9]+$ ]] && (( num >= 1 && num <= ${#AVAILABLE[@]} )); then
                    link_skill "${AVAILABLE[$((num-1))]}"
                else
                    echo -e "  ${YELLOW}⚠${NC} Invalid selection: $num"
                fi
            done
        fi
        echo ""
        exit 0
        ;;
    *)
        # Direct mode — link named skills
        for name in "$@"; do
            link_skill "$name"
        done
        echo ""
        exit 0
        ;;
esac
