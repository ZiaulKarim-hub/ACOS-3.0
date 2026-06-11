#!/bin/bash
# Mechanical reviewer-verdict aggregation — the AUTHORITATIVE review gate.
#
# Removes the Architect's discretion over the pass/fail decision: the Architect
# records each reviewer's raw verdict, this script computes the gate, and its EXIT
# CODE is binding (the skill must obey it, not re-interpret it).
#
# Inputs (under .acos/state/review-verdicts/<slice_id>/):
#   expected.json        — JSON array of reviewer names that were ASSIGNED (Step 6)
#   <reviewer>.json      — {"reviewer": "...", "verdict": "PASS|REJECT|INCONCLUSIVE", ...}
#
# Rule: every EXPECTED reviewer must have a verdict file with verdict == "PASS".
#   - any non-PASS verdict            -> REJECT
#   - any expected reviewer with no file (crashed/missing) -> INCONCLUSIVE -> REJECT
#   - zero expected reviewers / no dir -> REJECT (a review with no reviewers never passes)
#
# Output: JSON decision on stdout.  Exit 0 = PASS (proceed), Exit 2 = blocked.
#
# Usage: bash .claude/scripts/aggregate-verdicts.sh <slice_id>

SLICE_ID="${1:-}"
if [ -z "$SLICE_ID" ]; then
  echo '{"decision":"REJECT","error":"no slice_id argument"}'
  exit 2
fi

SLICE_ID="$SLICE_ID" python3 <<'PY'
import json, os, glob, sys

slice_id = os.environ["SLICE_ID"]
d = os.path.join(".acos", "state", "review-verdicts", slice_id)

if not os.path.isdir(d):
    print(json.dumps({"decision": "REJECT", "reason": f"no verdict directory: {d}"}))
    sys.exit(2)

# Expected (assigned) reviewers.
# We MUST know the assigned set to verify unanimity. If expected.json is missing
# or unparseable, we cannot tell whether an assigned reviewer crashed without
# writing a file — so we block (REJECT) rather than trusting whoever reported.
expected = None  # None = "assigned set unknown -> cannot verify -> block"
exp_path = os.path.join(d, "expected.json")
if os.path.isfile(exp_path):
    try:
        expected = [str(r) for r in json.load(open(exp_path))]
    except Exception:
        expected = None

if expected is None:
    print(json.dumps({
        "decision": "REJECT",
        "reason": "expected.json missing or unparseable — cannot verify the assigned "
                  "reviewer set is unanimous (an assigned-but-crashed reviewer would be invisible)",
    }))
    sys.exit(2)

# Collected verdicts (every *.json except expected.json)
#
# CANONICAL KEY = the verdict FILE basename (without .json). expected.json holds
# the assigned reviewer names, and verdicts are written as "<reviewer>.json", so
# the filename is the single key on which both sides compare. We deliberately do
# NOT key on the in-file 'reviewer' field: a verdict JSON that omits or misspells
# 'reviewer' would otherwise be filed under a name that differs from the assigned
# set, making a genuine PASS look like a missing reviewer (false INCONCLUSIVE).
collected = {}   # canonical_name -> verdict
details = {}      # canonical_name -> {issues, checks_performed}
name_mismatches = []  # non-blocking: in-file 'reviewer' disagrees with filename
for f in glob.glob(os.path.join(d, "*.json")):
    if os.path.basename(f) == "expected.json":
        continue
    name = os.path.splitext(os.path.basename(f))[0]  # canonical key
    try:
        v = json.load(open(f))
        collected[name] = str(v.get("verdict", "")).upper()
        details[name] = {
            "issues": v.get("issues") or [],
            "checks_performed": v.get("checks_performed") or [],
        }
        declared = v.get("reviewer")
        if declared is not None and str(declared) != name:
            name_mismatches.append({
                "file": os.path.basename(f),
                "declared_reviewer": str(declared),
                "canonical_name": name,
                "warning": "verdict file's 'reviewer' field disagrees with its filename; "
                           "gate compares on filename to stay aligned with expected.json",
            })
    except Exception:
        # An unparseable verdict file = INCONCLUSIVE for that reviewer.
        collected[name] = "INCONCLUSIVE"
        details[name] = {"issues": [], "checks_performed": []}

# Which reviewers must we check? Always the assigned set — never fall back to
# "whoever reported", or an assigned-but-crashed reviewer (no file) would be
# invisible and the slice could PASS with a missing reviewer.
check = expected

failures = []
if not check:
    # expected.json present but empty: a review with zero assigned reviewers
    # never passes (cannot establish unanimity of an empty set).
    print(json.dumps({"decision": "REJECT", "reason": "no reviewers assigned (expected.json is empty)"}))
    sys.exit(2)

for r in check:
    if r not in collected:
        failures.append({"reviewer": r, "reason": "no verdict (crashed/missing -> INCONCLUSIVE)"})
    elif collected[r] != "PASS":
        failures.append({"reviewer": r, "reason": collected[r] or "empty verdict"})

decision = "PASS" if not failures else "REJECT"

# ── Review-the-reviewers (finding 4.3, lightweight): flag rubber-stamp PASSes ──
# A PASS with NO issues AND NO recorded checks_performed is indistinguishable from a
# lazy reviewer. Non-blocking — surfaced for the human/architect to spot-check.
warnings = []
for r in check:
    if collected.get(r) == "PASS":
        det = details.get(r, {})
        if not det.get("issues") and not det.get("checks_performed"):
            warnings.append({
                "reviewer": r,
                "warning": "PASS with no issues and no checks_performed recorded — "
                           "possible rubber-stamp; spot-check this review.",
            })

# Surface (non-blocking) any verdict files whose in-file 'reviewer' field
# disagreed with the canonical filename key used for the gate comparison.
warnings.extend(name_mismatches)

print(json.dumps({
    "decision": decision,
    "expected_count": len(check),
    "pass_count": sum(1 for r in check if collected.get(r) == "PASS"),
    "reviewers": {r: collected.get(r, "MISSING") for r in check},
    "failures": failures,
    "warnings": warnings,
}, indent=2))
sys.exit(0 if decision == "PASS" else 2)
PY
