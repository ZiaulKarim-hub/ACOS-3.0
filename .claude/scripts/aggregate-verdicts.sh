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

# Expected (assigned) reviewers
expected = []
exp_path = os.path.join(d, "expected.json")
if os.path.isfile(exp_path):
    try:
        expected = [str(r) for r in json.load(open(exp_path))]
    except Exception:
        expected = []

# Collected verdicts (every *.json except expected.json)
collected = {}   # name -> verdict
details = {}      # name -> {issues, checks_performed}
for f in glob.glob(os.path.join(d, "*.json")):
    if os.path.basename(f) == "expected.json":
        continue
    try:
        v = json.load(open(f))
        name = str(v.get("reviewer") or os.path.splitext(os.path.basename(f))[0])
        collected[name] = str(v.get("verdict", "")).upper()
        details[name] = {
            "issues": v.get("issues") or [],
            "checks_performed": v.get("checks_performed") or [],
        }
    except Exception:
        # An unparseable verdict file = INCONCLUSIVE for that reviewer.
        name = os.path.splitext(os.path.basename(f))[0]
        collected[name] = "INCONCLUSIVE"
        details[name] = {"issues": [], "checks_performed": []}

# Which reviewers must we check? Assigned set if known, else whoever reported.
check = expected if expected else sorted(collected.keys())

failures = []
if not check:
    print(json.dumps({"decision": "REJECT", "reason": "no reviewers ran"}))
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
