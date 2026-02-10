#!/bin/bash

# ═══════════════════════════════════════════════════════════════════════════
# ACOS v3.0 - Project Archive Script
# ═══════════════════════════════════════════════════════════════════════════
#
# Usage: ./archive-project.sh [project-name]
#
# Archives completed project memory to a dated archive folder
# Should be run after project completion and learning extraction
#
# ═══════════════════════════════════════════════════════════════════════════

set -e

PROJECT_NAME="${1:-$(basename $(pwd))}"
DATE=$(date +%Y-%m-%d)
TIMESTAMP=$(date +%Y-%m-%dT%H:%M:%S)
ARCHIVE_DIR=".acos/archive/${DATE}-${PROJECT_NAME}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

print_header() {
    echo "═══════════════════════════════════════════════════════════════"
    echo "  ACOS Project Archiver"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${CYAN}ℹ${NC} $1"
}

print_header

# Check if ACOS is initialized
if [ ! -d ".acos" ]; then
    echo -e "${RED}Error: ACOS not initialized in this directory${NC}"
    echo "Run 'acos init' first"
    exit 1
fi

# Check if memory exists
if [ ! -d "memory" ]; then
    echo -e "${RED}Error: No memory directory found${NC}"
    exit 1
fi

echo "Project: $PROJECT_NAME"
echo "Archive: $ARCHIVE_DIR"
echo ""

# Confirm
read -p "Are you sure you want to archive this project? (y/N) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Archive cancelled"
    exit 0
fi

echo ""
print_info "Starting archive process..."
echo ""

# Create archive directory
mkdir -p "$ARCHIVE_DIR"

# ═══════════════════════════════════════════════════════════════════════════
# Archive Memory
# ═══════════════════════════════════════════════════════════════════════════

print_info "Archiving memory..."

if [ -d "memory" ]; then
    cp -r memory "$ARCHIVE_DIR/"
    print_success "Memory archived"

    # Count items
    DECISIONS=$(find memory/decisions -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
    REVIEWS=$(find memory/reviews -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
    HANDOFFS=$(find memory/handoffs -name "*.yaml" 2>/dev/null | wc -l | tr -d ' ')

    echo "    - Decisions: $DECISIONS"
    echo "    - Reviews: $REVIEWS"
    echo "    - Handoffs: $HANDOFFS"
fi

# ═══════════════════════════════════════════════════════════════════════════
# Archive Planning
# ═══════════════════════════════════════════════════════════════════════════

print_info "Archiving planning documents..."

if [ -d "planning" ]; then
    cp -r planning "$ARCHIVE_DIR/"
    print_success "Planning archived"

    EPICS=$(find planning/epics -name "*.yaml" 2>/dev/null | wc -l | tr -d ' ')
    STORIES=$(find planning/stories -name "*.yaml" 2>/dev/null | wc -l | tr -d ' ')
    SLICES=$(find planning/slices -name "*.yaml" 2>/dev/null | wc -l | tr -d ' ')

    echo "    - Epics: $EPICS"
    echo "    - Stories: $STORIES"
    echo "    - Slices: $SLICES"
fi

# ═══════════════════════════════════════════════════════════════════════════
# Archive Evidence
# ═══════════════════════════════════════════════════════════════════════════

print_info "Archiving evidence bundles..."

if [ -d ".acos/evidence" ]; then
    cp -r .acos/evidence "$ARCHIVE_DIR/"
    print_success "Evidence archived"

    BUNDLES=$(find .acos/evidence -type d -mindepth 2 -maxdepth 2 2>/dev/null | wc -l | tr -d ' ')
    echo "    - Evidence bundles: $BUNDLES"
fi

# ═══════════════════════════════════════════════════════════════════════════
# Create Archive Manifest
# ═══════════════════════════════════════════════════════════════════════════

print_info "Creating archive manifest..."

cat > "$ARCHIVE_DIR/MANIFEST.md" << EOF
# Project Archive Manifest

**Project:** $PROJECT_NAME
**Archived:** $TIMESTAMP
**Archive Location:** $ARCHIVE_DIR

## Contents

### Memory
- Source of Truth: $(ls memory/source-of-truth/*.md 2>/dev/null | wc -l | tr -d ' ') files
- Decisions: $DECISIONS files
- Reviews: $REVIEWS files
- Handoffs: $HANDOFFS files

### Planning
- Epics: $EPICS
- Stories: $STORIES
- Slices: $SLICES

### Evidence
- Evidence Bundles: $BUNDLES

## Directory Structure

\`\`\`
$(find "$ARCHIVE_DIR" -type f | sed "s|$ARCHIVE_DIR/||" | head -50)
\`\`\`

## Notes

This archive contains the complete project memory and planning documents.
Use this for reference or to restore the project state.

To restore, copy contents back to a project directory.
EOF

print_success "Manifest created"

# ═══════════════════════════════════════════════════════════════════════════
# Optional: Clear Current Memory (with confirmation)
# ═══════════════════════════════════════════════════════════════════════════

echo ""
read -p "Do you want to clear the current memory? (y/N) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Clearing current memory..."

    # Keep structure but remove content
    find memory/decisions -name "*.md" ! -name ".template.md" -delete 2>/dev/null || true
    find memory/reviews -name "*.md" ! -name ".template.md" -delete 2>/dev/null || true
    find memory/handoffs -name "*.yaml" ! -name ".template.yaml" -delete 2>/dev/null || true
    find memory/code-rationale -name "*.md" ! -name ".template.md" -delete 2>/dev/null || true
    find memory/feedback-history -name "*.md" -delete 2>/dev/null || true
    rm -f memory/source-of-truth/vision-interview.md 2>/dev/null || true
    rm -f memory/source-of-truth/vision-document.md 2>/dev/null || true
    rm -f memory/source-of-truth/user-commands.md 2>/dev/null || true

    # Clear planning
    find planning/epics -name "*.yaml" ! -name ".template.yaml" -delete 2>/dev/null || true
    find planning/stories -name "*.yaml" ! -name ".template.yaml" -delete 2>/dev/null || true
    find planning/slices -name "*.yaml" ! -name ".template.yaml" -delete 2>/dev/null || true
    find planning/vision -name "*.yaml" ! -name ".template.yaml" -delete 2>/dev/null || true

    # Clear evidence
    rm -rf .acos/evidence/*/ 2>/dev/null || true

    print_success "Current memory cleared (templates preserved)"
fi

# ═══════════════════════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════════════════════

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo -e "  ${GREEN}Archive Complete${NC}"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Archive location: $ARCHIVE_DIR"
echo ""
echo "Contents:"
echo "  - memory/"
echo "  - planning/"
echo "  - evidence/"
echo "  - MANIFEST.md"
echo ""

# Calculate size
SIZE=$(du -sh "$ARCHIVE_DIR" | cut -f1)
echo "Archive size: $SIZE"
echo ""
print_success "Project archived successfully!"
