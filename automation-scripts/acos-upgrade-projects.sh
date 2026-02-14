#!/bin/bash

# ═══════════════════════════════════════════════════════════════════════════
# ACOS v3.0 - Upgrade All ACOS Projects
# ═══════════════════════════════════════════════════════════════════════════
#
# Re-runs acos-bootstrap.sh --force in every ACOS project found under the
# given search directory. Defaults to ~/Documents/Vibe Coding.
#
# Usage:
#   acos-upgrade-projects.sh              # Search ~/Documents/Vibe Coding
#   acos-upgrade-projects.sh /some/path   # Search a specific directory
#
# ═══════════════════════════════════════════════════════════════════════════

set -e

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
DIM='\033[2m'
BOLD='\033[1m'
NC='\033[0m'

# Derive ACOS_ROOT from this script's location
ACOS_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BOOTSTRAP="$ACOS_ROOT/.claude/scripts/acos-bootstrap.sh"

if [[ ! -f "$BOOTSTRAP" ]]; then
    echo -e "${YELLOW}Bootstrap script not found at $BOOTSTRAP${NC}"
    exit 1
fi

# Search directory: argument or default
SEARCH_DIR="${1:-$HOME/Documents/Vibe Coding}"

if [[ ! -d "$SEARCH_DIR" ]]; then
    echo -e "${YELLOW}Search directory not found: $SEARCH_DIR${NC}"
    exit 1
fi

echo -e "${BOLD}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  ACOS v3.0 — Upgrading Projects${NC}"
echo -e "${BOLD}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  Source: ${CYAN}$ACOS_ROOT${NC}"
echo -e "  Search: ${CYAN}$SEARCH_DIR${NC}"
echo ""

UPGRADED=0
FAILED=0
SKIPPED=0

# Find directories containing .acos/ (max depth 3 to avoid deep traversal)
for acos_dir in "$SEARCH_DIR"/*/.acos "$SEARCH_DIR"/*/*/.acos; do
    [[ ! -d "$acos_dir" ]] && continue

    project_dir="$(dirname "$acos_dir")"

    # Skip the ACOS framework itself
    if [[ "$project_dir" == "$ACOS_ROOT" ]]; then
        ((SKIPPED++))
        continue
    fi

    echo -e "  ${CYAN}▸${NC} Upgrading ${BOLD}$(basename "$project_dir")${NC}..."

    if (cd "$project_dir" && bash "$BOOTSTRAP" --force --quiet); then
        echo -e "    ${GREEN}✓${NC} Done"
        ((UPGRADED++))
    else
        echo -e "    ${YELLOW}⚠${NC} Failed"
        ((FAILED++))
    fi
done

echo ""
echo -e "${BOLD}═══════════════════════════════════════════════════════════════${NC}"
echo -e "  ${GREEN}${BOLD}Upgrade complete${NC}"
echo -e "  Upgraded: ${GREEN}$UPGRADED${NC}  Failed: ${YELLOW}$FAILED${NC}  Skipped: ${DIM}$SKIPPED${NC}"
echo -e "${BOLD}═══════════════════════════════════════════════════════════════${NC}"
echo ""
