#!/bin/bash

# ═══════════════════════════════════════════════════════════════════════════
# ACOS v3.0 - Evidence Bundle Validator
# ═══════════════════════════════════════════════════════════════════════════
#
# Usage: ./validate-evidence.sh <SLICE-ID> [evidence-path]
#
# Validates that an evidence bundle is complete before submission to review
#
# ═══════════════════════════════════════════════════════════════════════════

set -e

SLICE_ID="${1:-}"
EVIDENCE_PATH="${2:-}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

print_header() {
    echo "═══════════════════════════════════════════════════════════════"
    echo "  ACOS Evidence Bundle Validator"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
}

print_pass() {
    echo -e "${GREEN}✓ PASS:${NC} $1"
}

print_fail() {
    echo -e "${RED}✗ FAIL:${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}⚠ WARN:${NC} $1"
}

# Check arguments
if [ -z "$SLICE_ID" ]; then
    print_header
    echo "Usage: ./validate-evidence.sh <SLICE-ID> [evidence-path]"
    echo ""
    echo "Examples:"
    echo "  ./validate-evidence.sh SLICE-001"
    echo "  ./validate-evidence.sh SLICE-001 .acos/evidence/2026-01-31/SLICE-001"
    exit 1
fi

# Find evidence path if not provided
if [ -z "$EVIDENCE_PATH" ]; then
    EVIDENCE_PATH=$(find .acos/evidence -type d -name "$SLICE_ID" 2>/dev/null | head -1)
fi

if [ -z "$EVIDENCE_PATH" ] || [ ! -d "$EVIDENCE_PATH" ]; then
    print_header
    echo -e "${RED}Error: Evidence bundle not found for ${SLICE_ID}${NC}"
    echo ""
    echo "Run ./create-evidence-bundle.sh ${SLICE_ID} first"
    exit 1
fi

print_header
echo "Validating: $EVIDENCE_PATH"
echo ""

# Counters
PASS=0
FAIL=0
WARN=0

# ═══════════════════════════════════════════════════════════════════════════
# Check Required Files
# ═══════════════════════════════════════════════════════════════════════════

echo -e "${CYAN}Checking required files...${NC}"
echo ""

# before/baseline-status.log
if [ -f "$EVIDENCE_PATH/before/baseline-status.log" ]; then
    print_pass "before/baseline-status.log exists"
    ((PASS++))
else
    print_fail "before/baseline-status.log missing"
    ((FAIL++))
fi

# after/modified-files.txt
if [ -f "$EVIDENCE_PATH/after/modified-files.txt" ]; then
    print_pass "after/modified-files.txt exists"
    ((PASS++))

    # Check if it has content
    if [ -s "$EVIDENCE_PATH/after/modified-files.txt" ]; then
        print_pass "after/modified-files.txt has content"
        ((PASS++))
    else
        print_warn "after/modified-files.txt is empty (no files modified?)"
        ((WARN++))
    fi
else
    print_fail "after/modified-files.txt missing"
    ((FAIL++))
fi

# after/git-diff.patch
if [ -f "$EVIDENCE_PATH/after/git-diff.patch" ]; then
    print_pass "after/git-diff.patch exists"
    ((PASS++))
else
    print_fail "after/git-diff.patch missing"
    ((FAIL++))
fi

# verify.log
if [ -f "$EVIDENCE_PATH/verify.log" ]; then
    print_pass "verify.log exists"
    ((PASS++))

    # Check if verification was completed
    if grep -q "Status: PENDING" "$EVIDENCE_PATH/verify.log" 2>/dev/null; then
        print_warn "verify.log shows PENDING status - verification not complete"
        ((WARN++))
    else
        print_pass "verify.log appears complete"
        ((PASS++))
    fi
else
    print_fail "verify.log missing"
    ((FAIL++))
fi

# Summary.md
if [ -f "$EVIDENCE_PATH/Summary.md" ]; then
    print_pass "Summary.md exists"
    ((PASS++))

    # Check if summary was completed
    if grep -q "TODO" "$EVIDENCE_PATH/Summary.md" 2>/dev/null; then
        print_warn "Summary.md contains TODO items - not complete"
        ((WARN++))
    else
        print_pass "Summary.md appears complete"
        ((PASS++))
    fi

    # Check Ready for Review
    if grep -q "Ready for Review" "$EVIDENCE_PATH/Summary.md" 2>/dev/null; then
        if grep -q "YES" "$EVIDENCE_PATH/Summary.md" 2>/dev/null; then
            print_pass "Summary.md indicates ready for review"
            ((PASS++))
        else
            print_warn "Summary.md does not indicate ready for review"
            ((WARN++))
        fi
    fi
else
    print_fail "Summary.md missing"
    ((FAIL++))
fi

echo ""

# ═══════════════════════════════════════════════════════════════════════════
# Check Optional Files
# ═══════════════════════════════════════════════════════════════════════════

echo -e "${CYAN}Checking optional files...${NC}"
echo ""

# after/test-results.log
if [ -f "$EVIDENCE_PATH/after/test-results.log" ]; then
    print_pass "after/test-results.log exists"
    ((PASS++))
else
    print_warn "after/test-results.log not found (tests may not apply)"
    ((WARN++))
fi

# after/build-results.log
if [ -f "$EVIDENCE_PATH/after/build-results.log" ]; then
    print_pass "after/build-results.log exists"
    ((PASS++))
else
    print_warn "after/build-results.log not found (build may not apply)"
    ((WARN++))
fi

echo ""

# ═══════════════════════════════════════════════════════════════════════════
# Check Content Quality
# ═══════════════════════════════════════════════════════════════════════════

echo -e "${CYAN}Checking content quality...${NC}"
echo ""

# Check baseline has git info
if [ -f "$EVIDENCE_PATH/before/baseline-status.log" ]; then
    if grep -q "Git Status" "$EVIDENCE_PATH/before/baseline-status.log" 2>/dev/null; then
        print_pass "Baseline includes git status"
        ((PASS++))
    else
        print_warn "Baseline may be incomplete"
        ((WARN++))
    fi
fi

# Check git diff has content (if file modified)
if [ -f "$EVIDENCE_PATH/after/git-diff.patch" ]; then
    if [ -s "$EVIDENCE_PATH/after/git-diff.patch" ]; then
        LINES=$(wc -l < "$EVIDENCE_PATH/after/git-diff.patch" | tr -d ' ')
        print_pass "Git diff has $LINES lines"
        ((PASS++))
    else
        print_warn "Git diff is empty (no changes?)"
        ((WARN++))
    fi
fi

echo ""

# ═══════════════════════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════════════════════

echo "═══════════════════════════════════════════════════════════════"
echo "  Validation Summary"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo -e "  ${GREEN}Passed:${NC}   $PASS"
echo -e "  ${RED}Failed:${NC}   $FAIL"
echo -e "  ${YELLOW}Warnings:${NC} $WARN"
echo ""

if [ $FAIL -eq 0 ]; then
    if [ $WARN -eq 0 ]; then
        echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
        echo -e "${GREEN}  RESULT: VALID - Ready for review submission${NC}"
        echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
        exit 0
    else
        echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
        echo -e "${YELLOW}  RESULT: VALID WITH WARNINGS - Review warnings before submitting${NC}"
        echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
        exit 0
    fi
else
    echo -e "${RED}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${RED}  RESULT: INVALID - Fix failures before submitting${NC}"
    echo -e "${RED}═══════════════════════════════════════════════════════════════${NC}"
    exit 1
fi
