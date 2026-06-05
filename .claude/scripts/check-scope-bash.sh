#!/bin/bash
# PreToolUse hook for Bash — best-effort scope enforcement for file-writing commands.
#
# Companion to check-scope.sh (which guards Write|Edit via tool_input.file_path).
# Bash calls carry only tool_input.command, so the file_path guard cannot see them —
# this script parses the command for common write idioms and blocks any that target
# a repo path outside the active slice's files_allowed.
#
# DESIGN: defense-in-depth, NOT airtight. Arbitrary Bash can write via idioms no
# heuristic catches (e.g. a python -c open(...,'w')). This closes the common vectors
# (>, >>, tee, cp, mv, sed -i, dd of=, install, ln, touch). The airtight containment
# is isolation:worktree on the developer agent (separate change).
#
# Only enforces on paths INSIDE the repo. Absolute paths outside the repo (/tmp, /etc)
# are left to the Oracle — scope is about repo containment.
#
# Exit 0 = allow, Exit 2 = block. Fail-open (allow + log to stderr) on parse failure.

ACTIVE_SLICE=".acos/config/active-slice.yaml"

# No active slice = no scope restrictions.
[ ! -f "$ACTIVE_SLICE" ] && exit 0

# Read the hook JSON from stdin into a variable, then hand both the JSON and the
# slice path to Python via the environment. (Python's own stdin is consumed by the
# heredoc below, so the JSON must NOT come through stdin.)
HOOK_INPUT=$(cat)

ACTIVE_SLICE="$ACTIVE_SLICE" HOOK_INPUT="$HOOK_INPUT" python3 <<'PY'
import sys, os, re, json, fnmatch

active = os.environ["ACTIVE_SLICE"]

try:
    cmd = json.loads(os.environ.get("HOOK_INPUT", "")).get("tool_input", {}).get("command", "")
except Exception:
    print("check-scope-bash: FAIL-OPEN — could not parse hook input", file=sys.stderr)
    sys.exit(0)

if not cmd or not cmd.strip():
    sys.exit(0)

# Always-allowed prefixes (runtime data + memory), mirrors check-scope.sh.
ALLOW_PREFIX = (".acos/evidence/", ".acos/state/", "memory/")

# Parse files_allowed from the active slice (stdlib only — no PyYAML).
try:
    text = open(active).read()
    m = re.search(r'files_allowed:\s*\n((?:\s+-\s+.*\n?)*)', text)
    allowed = []
    if m:
        for line in m.group(1).strip().split("\n"):
            line = line.strip()
            if line.startswith("- "):
                v = line[2:].strip().strip('"').strip("'")
                if v:
                    allowed.append(v)
except Exception:
    print("check-scope-bash: FAIL-OPEN — could not parse files_allowed", file=sys.stderr)
    sys.exit(0)

repo_root = os.getcwd()

# ── Heuristic extraction of write-target tokens from the command ──
targets = set()

# 1) Redirections:  > path  /  >> path   (skip >&2, >&1, >/dev/...)
for mo in re.finditer(r'(?<![0-9&])>>?\s*([^\s;|&>]+)', cmd):
    targets.add(mo.group(1))

# 2) tee [opts] path...
for mo in re.finditer(r'\btee\b((?:\s+-\S+)*)((?:\s+[^\s;|&]+)+)', cmd):
    for p in mo.group(2).split():
        targets.add(p)

# 3) sed -i ... <file> (in-place edit; file is typically the trailing token)
for mo in re.finditer(r'\bsed\b[^;|&]*\s-i\S*\s+([^;|&]+)', cmd):
    toks = [t for t in mo.group(1).split() if not t.startswith("-")]
    if toks:
        targets.add(toks[-1])

# 4) dd of=path
for mo in re.finditer(r'\bof=([^\s;|&]+)', cmd):
    targets.add(mo.group(1))

# 5) cp / mv / install / ln  → destination is the last non-flag token
for mo in re.finditer(r'\b(cp|mv|install|ln)\b([^;|&]*)', cmd):
    toks = [t for t in mo.group(2).split() if not t.startswith("-")]
    if toks:
        targets.add(toks[-1])

# 6) touch <files...>  → every non-flag token is a write target
for mo in re.finditer(r'\btouch\b([^;|&]*)', cmd):
    for t in mo.group(1).split():
        if not t.startswith("-"):
            targets.add(t)


def to_repo_relative(p):
    """Return repo-relative path if p is inside the repo, else None (out of repo)."""
    p = p.strip().strip('"').strip("'")
    if not p:
        return None
    if os.path.isabs(p):
        ap = os.path.normpath(p)
        if ap == repo_root or ap.startswith(repo_root + os.sep):
            return os.path.relpath(ap, repo_root)
        return None  # absolute path outside the repo — not a scope concern
    if p.startswith("./"):
        p = p[2:]
    return os.path.normpath(p)


def in_scope(rel):
    if any(rel.startswith(pre) for pre in ALLOW_PREFIX):
        return True
    for pat in allowed:
        if rel == pat or fnmatch.fnmatch(rel, pat):
            return True
    return False


violations = []
for t in targets:
    # Skip obvious non-file tokens: shell vars, fds, flags, device files.
    if not t or t.startswith("$") or t.startswith("-") or t.startswith("&") or t.startswith("/dev/"):
        continue
    rel = to_repo_relative(t)
    if rel is None:
        continue  # outside repo → Oracle's domain, not scope's
    if not in_scope(rel):
        violations.append(rel)

if violations:
    uniq = ", ".join(sorted(set(violations)))
    print(f"BLOCKED (Bash scope): command writes to out-of-scope repo path(s): {uniq}. "
          f"Add to the slice's files_allowed or use Write/Edit on an allowed file.",
          file=sys.stderr)
    sys.exit(2)

sys.exit(0)
PY
