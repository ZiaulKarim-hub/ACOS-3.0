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
        list_match = re.match(r'^\s*-\s+(.*)', raw_line)
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

# ── Robust matching (finding 4.6) + mechanical content extraction (finding 4.5) ──
import fnmatch as _fnmatch

def _matches(pattern, text):
    """Match a trigger pattern against text.
    - glob chars (*?[]) -> fnmatch against path and basename
    - pattern containing '/' -> substring (explicit path fragment, intentional)
    - bare word -> WORD BOUNDARY (so 'key' no longer matches 'monkey.ts',
      'api' no longer matches 'capital.ts', 'role' no longer matches 'controller.ts')
    """
    p, t = str(pattern), str(text)
    if not p:
        return False
    if any(c in p for c in "*?[]"):
        return _fnmatch.fnmatch(t, p) or _fnmatch.fnmatch(os.path.basename(t), p)
    if "/" in p:
        return p in t
    return re.search(r"\b" + re.escape(p) + r"\b", t) is not None

def _matches_code(pattern, content):
    """Match a trigger pattern against a (possibly multiline) code-content blob.

    Distinct from _matches because fnmatch over a whole multiline blob never
    behaves as a substring search ('*' does not span newlines as intended), so a
    glob code pattern like 'api_*_key' would silently NEVER match real file
    contents. Here:
    - glob chars (*?[]) -> translate to a regex (DOTALL so '*' spans newlines)
      and search anywhere in the blob.
    - bare word -> WORD BOUNDARY substring search over the blob.
    """
    p, t = str(pattern), str(content)
    if not p:
        return False
    if any(c in p for c in "*?[]"):
        # Build a substring regex from the glob manually (fnmatch.translate
        # anchors the end with \Z, which would defeat substring matching).
        rx = ""
        i, n = 0, len(p)
        while i < n:
            ch = p[i]
            if ch == "*":
                rx += ".*"
            elif ch == "?":
                rx += "."
            elif ch == "[":
                j = i + 1
                # fnmatch-compatible negation: ONLY a leading '!' negates a class.
                # A leading '^' is LITERAL under fnmatch, so consume it as a class
                # member rather than as a negation marker.
                if j < n and p[j] == "!":
                    j += 1
                if j < n and p[j] == "]":
                    j += 1
                while j < n and p[j] != "]":
                    j += 1
                if j >= n:
                    rx += r"\["
                else:
                    klass = p[i + 1:j].replace("\\", "\\\\")
                    if klass.startswith("!"):
                        # fnmatch '!' -> regex '^' negation
                        klass = "^" + klass[1:]
                    elif klass.startswith("^"):
                        # fnmatch treats a leading '^' as a LITERAL member; escape
                        # it so regex does not interpret it as negation.
                        klass = "\\^" + klass[1:]
                    rx += "[" + klass + "]"
                    i = j
            else:
                rx += re.escape(ch)
            i += 1
        try:
            return re.search(rx, t, re.DOTALL) is not None
        except re.error:
            return False
    return re.search(r"\b" + re.escape(p) + r"\b", t) is not None

def _read_modified_contents(paths, max_bytes=200000):
    """Read modified-file contents so code-pattern triggers fire even when the
    Architect-supplied code_snippets omit them (finding 4.5 — no silent miss)."""
    out = []
    for f in paths:
        try:
            if os.path.isfile(f) and os.path.getsize(f) < max_bytes:
                with open(f, encoding="utf-8", errors="ignore") as fh:
                    out.append(fh.read())
        except Exception:
            continue
    return out

# Code triggers match against BOTH the declared snippets and the ACTUAL file contents,
# so assignment no longer depends on the Architect enumerating patterns correctly.
code_haystack = [str(s) for s in snippets] + _read_modified_contents(files)

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
                if any(_matches(pattern, f) for f in files):
                    triggered = True
                    break

        # Code pattern triggers
        if not triggered:
            code_patterns = cfg.get("trigger_code_patterns", [])
            if isinstance(code_patterns, list):
                for pattern in code_patterns:
                    if any(_matches_code(pattern, h) for h in code_haystack):
                        triggered = True
                        break

        # File count trigger
        if not triggered:
            threshold = cfg.get("trigger_file_count_gt")
            # Test type explicitly so a configured threshold of 0 (fire on any
            # file modification) is honored; `if threshold` would drop a falsy 0.
            # Exclude bool, since bool is a subclass of int.
            if isinstance(threshold, (int, float)) and not isinstance(threshold, bool):
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
                    if any(_matches(pattern, f) for f in files):
                        triggered = True
                        break
            if not triggered:
                code_patterns = cfg.get("trigger_code_patterns", [])
                if isinstance(code_patterns, list):
                    for pattern in code_patterns:
                        if any(_matches_code(pattern, h) for h in code_haystack):
                            triggered = True
                            break
            if not triggered:
                threshold = cfg.get("trigger_file_count_gt")
                # Honor a configured threshold of 0 (falsy); exclude bool.
                if isinstance(threshold, (int, float)) and not isinstance(threshold, bool):
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
                if any(_matches(p, f) for f in files):
                    triggered = True
                    break
        if not triggered and isinstance(code_patterns, list):
            for p in code_patterns:
                if any(_matches_code(p, h) for h in code_haystack):
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

# ── Advisors (finding 4.8): NON-GATING rule files (e.g. legal-analyst.yaml) ───────
# Advisory rules are any *.yaml that is NOT a gating *-reviewer.yaml and not global.yaml.
# They are surfaced as diligence notes, NOT added to the gating reviewer set (so an
# advisor like legal-analyst, which emits findings rather than PASS/REJECT, is never
# forced to gate). Matches are written to a side file the execute-slice skill reads.
slice_id = manifest.get("slice_id", "")
advisors = []
advisor_files = [
    fp for fp in sorted(glob.glob(os.path.join(rules_dir, "*.yaml")))
    if not fp.endswith("-reviewer.yaml") and os.path.basename(fp) != "global.yaml"
]
for filepath in advisor_files:
    try:
        with open(filepath) as f:
            cfg = parse_yaml(f.read())
    except Exception:
        continue
    name = str(cfg.get("name", "")).replace("ACOS-", "") or os.path.splitext(os.path.basename(filepath))[0]
    triggered = False
    fp_patterns = cfg.get("trigger_file_paths", [])
    if isinstance(fp_patterns, list) and any(_matches(p, f2) for p in fp_patterns for f2 in files):
        triggered = True
    if not triggered:
        code_patterns = cfg.get("trigger_code_patterns", [])
        if isinstance(code_patterns, list) and any(_matches_code(p, h) for p in code_patterns for h in code_haystack):
            triggered = True
    if not triggered:
        thr = cfg.get("trigger_file_count_gt")
        # Honor a configured threshold of 0; exclude bool (subclass of int).
        if isinstance(thr, (int, float)) and not isinstance(thr, bool) and file_count > thr:
            triggered = True
    if triggered:
        advisors.append(name)

# Write the advisor side file (even if empty) so execute-slice can read deterministically.
if slice_id:
    try:
        adv_dir = os.path.join(".acos", "state", "review-advisors")
        os.makedirs(adv_dir, exist_ok=True)
        with open(os.path.join(adv_dir, f"{slice_id}.json"), "w") as af:
            json.dump(sorted(set(advisors)), af)
    except Exception:
        pass

# stdout stays a plain reviewer array — execute-slice's Step 6 parsing is unchanged.
print(json.dumps(sorted(list(reviewers))))
PYTHON
