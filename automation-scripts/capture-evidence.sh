#!/bin/bash

# ═══════════════════════════════════════════════════════════════════════════
# ACOS v3.0 - Evidence Capture Script
# ═══════════════════════════════════════════════════════════════════════════
#
# Usage: ./capture-evidence.sh <SLICE-ID>
#
# Captures the "after" state for an evidence bundle
#
# ═══════════════════════════════════════════════════════════════════════════

set -e

SLICE_ID="${1:-UNKNOWN}"
DATE=$(date +%Y-%m-%d)
TIMESTAMP=$(date +%Y-%m-%dT%H:%M:%S)

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Find evidence path
EVIDENCE_PATH=".acos/evidence/${DATE}/${SLICE_ID}"

if [ ! -d "${EVIDENCE_PATH}" ]; then
    echo -e "${YELLOW}Evidence bundle not found for today. Searching...${NC}"
    EVIDENCE_PATH=$(find .acos/evidence -type d -name "${SLICE_ID}" 2>/dev/null | head -1)
fi

if [ ! -d "${EVIDENCE_PATH}" ]; then
    echo "Error: No evidence bundle found for ${SLICE_ID}"
    echo "Run ./create-evidence-bundle.sh ${SLICE_ID} first"
    exit 1
fi

echo "═══════════════════════════════════════════════════════════════"
echo "  ACOS Evidence Capture"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Evidence path: ${EVIDENCE_PATH}"
echo ""

# Capture modified files
echo -e "${CYAN}Capturing modified files...${NC}"
{
    echo "# Modified Files - ${SLICE_ID}"
    echo "# Captured: ${TIMESTAMP}"
    echo ""
    git status --porcelain 2>/dev/null || echo "Not a git repository"
} > "${EVIDENCE_PATH}/after/modified-files.txt"

# Capture git diff
echo -e "${CYAN}Capturing git diff...${NC}"
{
    git diff HEAD 2>/dev/null || echo "No diff available"
} > "${EVIDENCE_PATH}/after/git-diff.patch"

# Capture test results if tests exist
echo -e "${CYAN}Checking for test results...${NC}"
if [ -f "package.json" ]; then
    if grep -q '"test"' package.json; then
        echo "Found test script in package.json"
        echo "Run 'npm test' manually and save output to:"
        echo "  ${EVIDENCE_PATH}/after/test-results.log"
    fi
fi

# Capture build results if build exists
echo -e "${CYAN}Checking for build...${NC}"
if [ -f "package.json" ]; then
    if grep -q '"build"' package.json; then
        echo "Found build script in package.json"
        echo "Run 'npm run build' manually and save output to:"
        echo "  ${EVIDENCE_PATH}/after/build-results.log"
    fi
fi

echo ""
echo -e "${GREEN}✓ Evidence captured${NC}"
echo ""
echo "Files created/updated:"
echo "  - ${EVIDENCE_PATH}/after/modified-files.txt"
echo "  - ${EVIDENCE_PATH}/after/git-diff.patch"
echo ""
echo "Remaining steps:"
echo "  1. Run tests and save to: ${EVIDENCE_PATH}/after/test-results.log"
echo "  2. Run build and save to: ${EVIDENCE_PATH}/after/build-results.log"
echo "  3. Update verify.log with verification results"
echo "  4. Update Summary.md"
echo "  5. Create handoff to reviewer"
echo ""
