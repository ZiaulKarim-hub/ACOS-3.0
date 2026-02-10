#!/bin/bash

# ═══════════════════════════════════════════════════════════════════════════
# ACOS v3.0 - Evidence Bundle Creator
# ═══════════════════════════════════════════════════════════════════════════
#
# Usage: ./create-evidence-bundle.sh <SLICE-ID>
#
# Creates the evidence bundle structure for a slice and captures baseline
#
# ═══════════════════════════════════════════════════════════════════════════

set -e

SLICE_ID="${1:-UNKNOWN}"
DATE=$(date +%Y-%m-%d)
TIMESTAMP=$(date +%Y-%m-%dT%H:%M:%S)

# Colors
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

# Determine evidence path
EVIDENCE_PATH=".acos/evidence/${DATE}/${SLICE_ID}"

echo "═══════════════════════════════════════════════════════════════"
echo "  ACOS Evidence Bundle Creator"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Create directory structure
echo -e "${CYAN}Creating evidence bundle structure...${NC}"
mkdir -p "${EVIDENCE_PATH}/before"
mkdir -p "${EVIDENCE_PATH}/after"

# Capture baseline status
echo -e "${CYAN}Capturing baseline status...${NC}"

{
    echo "# Baseline Status - ${SLICE_ID}"
    echo "# Captured: ${TIMESTAMP}"
    echo ""
    echo "## Git Status"
    git status 2>/dev/null || echo "Not a git repository"
    echo ""
    echo "## Current Branch"
    git branch --show-current 2>/dev/null || echo "N/A"
    echo ""
    echo "## Recent Commits"
    git log --oneline -5 2>/dev/null || echo "N/A"
} > "${EVIDENCE_PATH}/before/baseline-status.log"

# Create summary template
cat > "${EVIDENCE_PATH}/Summary.md" << EOF
# Evidence Bundle - ${SLICE_ID}

**Date:** ${DATE}
**Developer:** ACOS-developer
**Slice:** ${SLICE_ID}

## Implementation Summary

[TODO: Describe what was implemented]

## Key Decisions

- **[Decision 1]**: [Rationale]

## Files Modified

| File | Purpose |
|------|---------|
| [path] | [What changed] |

## Acceptance Criteria

| Criterion | Status | How Addressed |
|-----------|--------|---------------|
| [Criterion] | DONE | [Details] |

## Quality Gates

| Gate | Status |
|------|--------|
| Functionality | PENDING |
| Tests | PENDING |
| Build | PENDING |
| Scope Compliance | PENDING |

## Known Limitations

- [Any caveats]

## Ready for Review

NO - Complete this summary and run verification steps first
EOF

# Create verify.log template
cat > "${EVIDENCE_PATH}/verify.log" << EOF
# Verification Log - ${SLICE_ID}
# Started: ${TIMESTAMP}

## Verification Steps

### 1. Code Compiles/Builds
Command: [build command]
Result: PENDING

### 2. Tests Pass
Command: [test command]
Result: PENDING

### 3. Functionality Verified
Steps:
1. [Step 1]
2. [Step 2]
Result: PENDING

### 4. Scope Verified
- Only modified allowed files: PENDING
- No scope creep: PENDING

## Verification Complete
Status: PENDING
Verified By: ACOS-developer
Verified At: [timestamp]
EOF

echo ""
echo -e "${GREEN}✓ Evidence bundle created at: ${EVIDENCE_PATH}${NC}"
echo ""
echo "Next steps:"
echo "  1. Implement the slice"
echo "  2. Run ./capture-evidence.sh ${SLICE_ID} when done"
echo "  3. Update Summary.md and verify.log"
echo "  4. Create handoff to reviewer"
echo ""
