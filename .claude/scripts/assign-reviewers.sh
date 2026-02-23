#!/bin/bash
# Reads per-reviewer YAML files from review-rules/ and a JSON manifest from stdin:
# {"slice_id": "SLICE-001", "files_modified": ["src/auth/login.ts"],
#  "code_snippets": ["password", "jwt"], "review_level": "slice"}
#
# Outputs JSON array: ["qa-reviewer", "security-reviewer"]
#
# Falls back to ["qa-reviewer"] on any error (QA is always required)
# Uses stdlib only — no PyYAML dependency.

RULES_DIR="review-rules"

# Check if the directory exists
if [ ! -d "$RULES_DIR" ]; then
  echo '["qa-reviewer"]'
  exit 0
fi

# Read stdin into a variable BEFORE the heredoc takes over stdin
MANIFEST_JSON=$(cat)

# Pass manifest via environment variable to avoid heredoc/stdin conflict
MANIFEST="$MANIFEST_JSON" python3 << 'PYTHON'
import os, json, re, glob

# ── Minimal YAML parser (stdlib only, flat structure) ────────────────────

def _parse_value(s):
    s = s.strip()
    if not s:
        return ""
    if "  #" in s:
        s = s[:s.index("  #")].strip()
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    if s.lower() in ("true", "yes", "on"):
        return True
    if s.lower() in ("false", "no", "off"):
        return False
    if s.lower() in ("null", "~", "none"):
        return None
    try:
        if "." in s:
            return float(s)
        return int(s)
    except ValueError:
        pass
    if s.startswith("[") and s.endswith("]"):
        items = s[1:-1].split(",")
        return [_parse_value(item) for item in items if item.strip()]
    return s

def parse_yaml(text):
    """Parse flat YAML with one level of list nesting."""
    result = {}
    current_key = None
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        list_match = re.match(r'^\s+-\s+(.*)', raw_line)
        if list_match and current_key is not None:
            item = _parse_value(list_match.group(1))
            if current_key in result:
                if not isinstance(result[current_key], list):
                    result[current_key] = []
                result[current_key].append(item)
            continue
        kv_match = re.match(r'^(\w[\w_]*)\s*:\s*(.*)', raw_line)
        if kv_match:
            key = kv_match.group(1)
            value = kv_match.group(2).strip()
            if value == "" or value == "|":
                result[key] = []
                current_key = key
            else:
                result[key] = _parse_value(value)
                current_key = key
    return result

# ── Main logic ───────────────────────────────────────────────────────────

rules_dir = "review-rules"

try:
    manifest = json.loads(os.environ.get("MANIFEST", "{}"))
except Exception:
    print(json.dumps(["qa-reviewer"]))
    raise SystemExit(0)

files = manifest.get("files_modified", [])
snippets = manifest.get("code_snippets", [])
level = manifest.get("review_level", "slice")
file_count = len(files)

reviewers = set()

# ── Read each per-reviewer file ──────────────────────────────────────────

reviewer_files = sorted(glob.glob(os.path.join(rules_dir, "*-reviewer.yaml")))

for filepath in reviewer_files:
    try:
        with open(filepath) as f:
            cfg = parse_yaml(f.read())
    except Exception:
        continue

    reviewer_name = cfg.get("name", "")
    if not reviewer_name:
        continue

    # Strip ACOS- prefix for output (qa-reviewer not ACOS-qa-reviewer)
    short_name = str(reviewer_name).replace("ACOS-", "")

    # Always-required reviewers are included unconditionally
    if cfg.get("always_required"):
        reviewers.add(short_name)
        continue

    # ── Slice-level evaluation ───────────────────────────────────────
    if level == "slice":
        triggered = False

        # File path triggers
        fp_patterns = cfg.get("trigger_file_paths", [])
        if isinstance(fp_patterns, list):
            for pattern in fp_patterns:
                if any(str(pattern) in str(f) for f in files):
                    triggered = True
                    break

        # Code pattern triggers
        if not triggered:
            code_patterns = cfg.get("trigger_code_patterns", [])
            if isinstance(code_patterns, list):
                for pattern in code_patterns:
                    if any(str(pattern) in str(s) for s in snippets):
                        triggered = True
                        break

        # File count trigger
        if not triggered:
            threshold = cfg.get("trigger_file_count_gt")
            if threshold and isinstance(threshold, (int, float)):
                if file_count > threshold:
                    triggered = True

        if triggered:
            reviewers.add(short_name)

    # ── Higher-level evaluation ──────────────────────────────────────
    else:
        level_always_key = f"{level}_always"
        if cfg.get(level_always_key):
            reviewers.add(short_name)
        else:
            # Check if triggered at slice level (inherits upward)
            triggered = False
            fp_patterns = cfg.get("trigger_file_paths", [])
            if isinstance(fp_patterns, list):
                for pattern in fp_patterns:
                    if any(str(pattern) in str(f) for f in files):
                        triggered = True
                        break
            if not triggered:
                code_patterns = cfg.get("trigger_code_patterns", [])
                if isinstance(code_patterns, list):
                    for pattern in code_patterns:
                        if any(str(pattern) in str(s) for s in snippets):
                            triggered = True
                            break
            if not triggered:
                threshold = cfg.get("trigger_file_count_gt")
                if threshold and isinstance(threshold, (int, float)):
                    if file_count > threshold:
                        triggered = True
            if triggered:
                reviewers.add(short_name)

# ── Read global.yaml for custom rules ────────────────────────────────────

try:
    with open(os.path.join(rules_dir, "global.yaml")) as f:
        global_cfg = parse_yaml(f.read())
except Exception:
    global_cfg = {}

custom_rules = global_cfg.get("custom_rules", [])
if isinstance(custom_rules, list):
    for rule in custom_rules:
        if not isinstance(rule, dict):
            continue
        fp_patterns = rule.get("file_path_contains", [])
        code_patterns = rule.get("code_contains", [])
        triggered = False
        if isinstance(fp_patterns, list):
            for p in fp_patterns:
                if any(str(p) in str(f) for f in files):
                    triggered = True
                    break
        if not triggered and isinstance(code_patterns, list):
            for p in code_patterns:
                if any(str(p) in str(s) for s in snippets):
                    triggered = True
                    break
        if triggered:
            assigned = rule.get("assign_reviewers", [])
            if isinstance(assigned, list):
                for r in assigned:
                    reviewers.add(str(r).replace("ACOS-", ""))

# ── Ensure QA is always present ──────────────────────────────────────────

if not reviewers:
    reviewers.add("qa-reviewer")

print(json.dumps(sorted(list(reviewers))))
PYTHON
