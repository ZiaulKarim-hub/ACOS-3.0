#!/bin/bash
# Reads review-rules.yaml and a JSON manifest from stdin:
# {"slice_id": "SLICE-001", "files_modified": ["src/auth/login.ts"],
#  "code_snippets": ["password", "jwt"], "review_level": "slice"}
#
# Outputs JSON array: ["qa-reviewer", "security-reviewer"]
#
# Falls back to ["qa-reviewer"] on any error (QA is always required)

python3 << 'PYTHON'
import sys, json, yaml

try:
    manifest = json.load(sys.stdin)
except Exception:
    print(json.dumps(["qa-reviewer"]))
    sys.exit(0)

files = manifest.get("files_modified", [])
snippets = manifest.get("code_snippets", [])
level = manifest.get("review_level", "slice")

try:
    with open("review-rules.yaml") as f:
        rules = yaml.safe_load(f)
except Exception:
    print(json.dumps(["qa-reviewer"]))
    sys.exit(0)

reviewers = set()

# QA is always required (global setting)
if rules.get("global", {}).get("qa_reviewer_required") == "always":
    reviewers.add("qa-reviewer")

# Check level-specific rules
level_key = f"{level}_level_rules"
for rule in rules.get(level_key, []):
    triggered = False
    triggers = rule.get("triggers", {})

    # File path triggers
    for pattern in triggers.get("file_path_contains", []):
        if any(pattern in f for f in files):
            triggered = True
            break

    # Code content triggers
    if not triggered:
        for pattern in triggers.get("code_contains", []):
            if any(pattern in s for s in snippets):
                triggered = True
                break

    # File count triggers
    threshold = triggers.get("files_modified_count_greater_than")
    if not triggered and threshold and len(files) > threshold:
        triggered = True

    # Always triggers
    if not triggered and triggers.get("always"):
        triggered = True

    if triggered:
        for r in rule.get("assign_reviewers", []):
            reviewers.add(r)

# Ensure QA is always present
if not reviewers:
    reviewers.add("qa-reviewer")

print(json.dumps(sorted(list(reviewers))))
PYTHON
