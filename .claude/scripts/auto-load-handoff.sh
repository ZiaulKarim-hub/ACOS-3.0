#!/bin/bash
# SessionStart hook — auto-loads all active handoffs + recent ADRs into context
# Matcher: startup|resume|compact
# Returns JSON with hookSpecificOutput.additionalContext
# Loads ALL active handoffs (newest first), falls back to mechanical if none active
# Also loads recent ADRs from memory/decisions/
# Token budget: 25,000 estimated tokens (~100k chars at 4 chars/token)

HANDOFF_DIR="memory/handoffs"
DECISIONS_DIR="memory/decisions"
TOKEN_BUDGET=25000
CHARS_BUDGET=$(( TOKEN_BUDGET * 4 ))  # ~100,000 chars

# If no handoff directory, nothing to load
if [ ! -d "$HANDOFF_DIR" ]; then
  exit 0
fi

# Use Python to do all the heavy lifting: collect handoffs + ADRs within budget
JSON_CONTEXT=$(python3 -c "
import json, sys, os, glob

handoff_dir = sys.argv[1]
decisions_dir = sys.argv[2]
chars_budget = int(sys.argv[3])

chars_used = 0
sections = []

# --- Collect handoffs ---
# Get all .yaml files sorted by modification time (newest first)
yaml_files = sorted(
    glob.glob(os.path.join(handoff_dir, '*.yaml')),
    key=lambda f: os.path.getmtime(f),
    reverse=True
)

active_handoffs = []
mechanical_handoffs = []

for fpath in yaml_files:
    # Parse top-level status
    status = 'active'  # default for legacy files without status
    try:
        with open(fpath) as f:
            for line in f:
                if line.startswith('status:'):
                    status = line.split(':', 1)[1].strip().strip('\"').strip(\"'\")
                    break
    except Exception:
        continue

    if status == 'completed':
        continue
    elif status == 'mechanical':
        mechanical_handoffs.append(fpath)
    else:  # active or legacy (no status field)
        active_handoffs.append(fpath)

# Prefer active handoffs; fall back to mechanical if none
handoffs_to_load = active_handoffs if active_handoffs else mechanical_handoffs

for fpath in handoffs_to_load:
    try:
        with open(fpath) as f:
            content = f.read()
    except Exception:
        continue

    # Check budget
    if chars_used + len(content) > chars_budget:
        break  # stop loading handoffs if budget exceeded

    filename = os.path.basename(fpath)
    label = 'Mechanical Handoff' if fpath in mechanical_handoffs else 'Session Handoff'
    sections.append(f'### {label}: {filename}\n\n{content}')
    chars_used += len(content)

# --- Collect ADRs ---
# Load accepted ADRs (skip template files and superseded/proposed ones)
if os.path.isdir(decisions_dir):
    adr_files = sorted(
        [f for f in glob.glob(os.path.join(decisions_dir, '*.md'))
         if not os.path.basename(f).startswith('.')],
        key=lambda f: os.path.getmtime(f),
        reverse=True
    )

    adr_sections = []
    for fpath in adr_files:
        try:
            with open(fpath) as f:
                content = f.read()
        except Exception:
            continue

        # Only load accepted ADRs
        status_line = [l for l in content.split('\n') if '**Status:**' in l]
        if status_line:
            adr_status = status_line[0].lower()
            if 'superseded' in adr_status or 'proposed' in adr_status:
                continue

        # Check budget
        if chars_used + len(content) > chars_budget:
            break

        filename = os.path.basename(fpath)
        adr_sections.append(f'### Decision: {filename}\n\n{content}')
        chars_used += len(content)

    if adr_sections:
        sections.append('---\n## Architecture Decisions (auto-loaded)')
        sections.extend(adr_sections)

# --- Build output ---
if not sections:
    sys.exit(0)

handoff_count = len(handoffs_to_load) if handoffs_to_load else 0
loaded_count = sum(1 for s in sections if s.startswith('### Session Handoff') or s.startswith('### Mechanical Handoff'))
est_tokens = chars_used // 4

header = f'## Session Context (auto-loaded: {loaded_count} handoff(s), ~{est_tokens} tokens)'
footer = '*Auto-loaded by auto-load-handoff.sh. Review this context and continue where the previous session left off.*'

full_context = header + '\n\n' + '\n\n'.join(sections) + '\n\n---\n' + footer
print(json.dumps(full_context))
" "$HANDOFF_DIR" "$DECISIONS_DIR" "$CHARS_BUDGET" 2>/dev/null)

if [ $? -ne 0 ] || [ -z "$JSON_CONTEXT" ]; then
  # Fallback: if python3 fails, skip injection rather than crash
  exit 0
fi

# Output the hook response JSON
cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": $JSON_CONTEXT
  }
}
EOF

exit 0
