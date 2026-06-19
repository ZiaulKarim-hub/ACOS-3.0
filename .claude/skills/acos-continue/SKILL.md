---
name: acos-continue
description: Manual session-continuation handoff for Warp terminals — the manual counterpart to the automatic /acos-eternity-protocol (cmux) flow. MANUAL-ONLY (no auto-fire at 400k). You invoke /acos-continue when ready to hand off across a context reset; the skill generates a handoff + resume prompt, writes the handoff-paired `.resume.md` sibling + per-claude-PID pointer, and DISPLAYS them in the conversation as a visible block. You then manually type /clear and /acos-eternity-protocol-resume to pick up where you left off. Formerly acos-eternity-protocol-warp; auto-fire was disabled 2026-06-04 because the AXTitle marker race makes daemon-driven keystroke injection fail in multi-Warp-window setups.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Skill
---

# ACOS Continue — Manual Session-Continuation Handoff (Warp, MANUAL-ONLY)

> Formerly `acos-eternity-protocol-warp`. Renamed to `acos-continue` 2026-06-19.
> Behavior is unchanged — this is the manual counterpart to the automatic
> `/acos-eternity-protocol` (cmux) flow.

## Overview

`/acos-continue` solves the "I'm at 400k and need to hand off NOW" problem
without depending on the broken AXTitle marker injection path. **You invoke
this skill manually** when you decide to hand off; it generates the handoff
+ resume-prompt artifacts, writes the handoff-paired `.resume.md` sibling
and per-claude-PID pointer, displays everything prominently in this
conversation, then exits. You then manually type `/clear` and
`/acos-eternity-protocol-resume`.

**Auto-fire was disabled 2026-06-04.** The daemon used to fire this skill
automatically at the 400k threshold via CGEventPost+AXRaise, but the
AXTitle marker race made that injection fail rc=4 in multi-Warp-window
setups (which is the user's reality — 14+ alive claude PIDs across many
windows). Instead of theatrical failed injections, the daemon now just
logs "manual invocation required" when threshold is crossed, and you
invoke this skill yourself. See `feedback_eternity_protocol_handoff_pointer`
for context.

This is the right variant when:
- You are in a Warp pane (not cmux)
- You want artifacts generated NOW and the resume mechanism to remain
  reliable across days (handoff-paired sibling + per-PID pointer)
- You're comfortable typing `/clear` and `/acos-eternity-protocol-resume`
  manually when you see the visible block appear

For the fully-automated experience, use the cmux variant
(`/acos-eternity-protocol`) inside a cmux surface where the
Unix-socket IPC eliminates the AXTitle race.

## Execution Policy

Autonomous — invoking IS authorization. Steps run end-to-end without
confirmation prompts. The skill **does NOT** keystroke-inject anything.

## Architecture

```
SKILL.md (this file)                    THE USER (after the visible block prints)
──────────────────────────────────      ─────────────────────────────────────────
1. acos-handoff   → writes handoff      6. Reads the visible block at end of
2. acos-resume-prompt → writes              conversation, copies resume prompt
   pending-resume-<sid>.txt                 if needed.
3. eternity-protocol-core.sh:           7. Types `/clear` into Warp pane.
   - verify both artifacts             8. Once /clear lands, types
   - capture pre_clear_total              `/acos-eternity-protocol-resume`.
   - write .resume-pending-<sid>       9. Resume skill auto-locates the
4. Print visible block with:               pending-resume file (project-scoped
   - handoff path                          fallback) and injects it into the
   - resume prompt verbatim                fresh session.
   - manual instructions
5. EXIT
```

**No daemon-driven keystroke injection happens in this variant — period.**
2026-06-04 update: auto-fire was disabled entirely. The daemon's
`dispatch_threshold_fire()` only logs a heads-up at threshold-cross for
warp sessions; you invoke this skill manually when ready. The May 21
cross-session-misfire fix (OK_SOLE_WINDOW removal) stays active across
the whole daemon — no warp-variant exception is needed since there's no
warp auto-fire to worry about.

## Configuration

Threshold and other config live at
`~/Library/Application Support/acos-token-monitor/config.yaml`. Change via
`/acos-eternity-protocol-threshold N`. Defaults: threshold 400k.

## Protocol

### Step 0: Pre-flight + opt-out check

```bash
SESSION_DIR="$HOME/.claude/projects/$(pwd | tr '/' '-' | tr ' ' '-' | tr '.' '-')"
JSONL=$(ls -t "$SESSION_DIR"/*.jsonl 2>/dev/null | head -1)
SESSION_ID=$(basename "$JSONL" .jsonl 2>/dev/null)
test -n "$SESSION_ID" || { echo "ERROR: could not determine session_id"; exit 1; }

STATE="$HOME/Library/Application Support/acos-token-monitor/state"

# Self-write PID file (idempotent — same pattern as the legacy skill)
echo "{\"session_id\":\"$SESSION_ID\"}" | \
    "$HOME/Library/Application Support/acos-token-monitor/bin/register-session-pid.sh" 2>/dev/null || true

# Opt-out marker present? Refuse silently — the user explicitly opted out
# via /acos-eternity-protocol-stop, and a manual invocation should still
# respect that. To override, delete state/stop-<sid> first.
if [[ -f "$STATE/stop-${SESSION_ID}" ]]; then
    echo "Eternity protocol is disabled for this session (stop marker present)."
    echo "  Remove: rm \"$STATE/stop-${SESSION_ID}\""
    exit 0
fi

# Handoffs dir must exist (same as legacy)
# Auto-create memory/handoffs if missing — makes this skill work in any
# project, not just ones with ACOS infrastructure already in place.
mkdir -p memory/handoffs 2>/dev/null || { echo "ERROR: could not create memory/handoffs in $(pwd)"; exit 1; }
```

### Step 1: Create the handoff

Invoke the `acos-handoff` skill via the `Skill` tool. After it returns,
mechanically verify a fresh handoff was written:

```bash
# 2026-06-11 fix: accept BOTH .md and .yaml handoffs (mirrors the Jun-10
# core.sh fix — acos-handoff emits .md now; a .yaml-only glob aborts the
# skill before core.sh ever runs).
# The .resume.md exclusion is REQUIRED: the resume sibling is written right
# after the handoff, so without it ls -t binds $HANDOFF to the .resume.md.
HANDOFF=$(ls -t memory/handoffs/*.md memory/handoffs/*.yaml 2>/dev/null | grep -v '\.resume\.md$' | head -1)
test -s "$HANDOFF" || { echo "ERROR: no handoff produced"; exit 1; }
```

### Step 2: Generate the resume prompt

Invoke the `acos-resume-prompt` skill via the `Skill` tool. It writes the
resume prompt to `state/pending-resume-<session_id>.txt`.

### Step 3: Arm the daemon via the shared core script

```bash
export ETERNITY_PROTOCOL_VARIANT="warp"
# Source the core script from the user-global location so this works in
# ANY project (not just ACOS 3.0). The script is a symlink to the ACOS 3.0
# source — single source of truth, but reachable from anywhere.
CORE_SCRIPT="$HOME/Library/Application Support/acos-token-monitor/bin/eternity-protocol-core.sh"
if [[ ! -f "$CORE_SCRIPT" ]]; then
    # Fallback to the project-relative path if the global symlink is missing
    # (e.g., fresh install, ACOS 3.0 not at expected path).
    CORE_SCRIPT="$(pwd)/.claude/scripts/eternity-protocol-core.sh"
fi
source "$CORE_SCRIPT" \
    || { echo "ERROR: eternity-protocol-core.sh failed (path: $CORE_SCRIPT)"; exit 1; }
# After source: $RESUME_FILE, $PRE_CLEAR_TOTAL, $HANDOFF, $RESUME_PENDING,
# $SESSION_ID, $RESUME_SIBLING, $HANDOFF_BASENAME, and (when the PID file
# exists) $ETERNITY_POINTER are exported for use below.
```

### Step 4: Display the visible block (the whole point of the warp variant)

```bash
RESUME_CONTENT=$(cat "$RESUME_FILE")
RESUME_LINES=$(wc -l < "$RESUME_FILE" | tr -d ' ')

cat <<EOF

╔═══════════════════════════════════════════════════════════════════════╗
║  ETERNITY PROTOCOL — WARP VARIANT (manual /clear required)            ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║  Artifacts generated:                                                 ║
║    handoff:           ${HANDOFF}
║    resume prompt:     ${RESUME_FILE}
║    resume sibling:    ${RESUME_SIBLING:-(none)}
║    per-PID pointer:   ${ETERNITY_POINTER:-(none)}
║    daemon arm:        ${RESUME_PENDING}
║                                                                       ║
║  RESUME LOOKUP: the resume skill uses the per-PID pointer first;      ║
║    if missing, falls back to the legacy state/pending-resume path.    ║
║    Resume works even days later — the pointer + sibling never expire  ║
║    until you fire another warp/cmux variant in this same pane.        ║
║                                                                       ║
║  Resume prompt (${RESUME_LINES} lines) — preview only; full text below:    ║
║                                                                       ║
EOF

# Show first 6 lines of resume prompt as inline preview
head -6 "$RESUME_FILE" | sed 's/^/║    /'

cat <<EOF
║                                                                       ║
╠═══════════════════════════════════════════════════════════════════════╣
║  WHAT TO DO NEXT (manual steps — daemon will NOT inject these):       ║
║                                                                       ║
║    1. Type:  /clear                                                   ║
║    2. Wait for the fresh session prompt.                              ║
║    3. Type:  /acos-eternity-protocol-resume                           ║
║                                                                       ║
║  If the resume skill says "no pending resume found":                  ║
║    Open ${RESUME_FILE}
║    Copy its contents and paste into the fresh session.                ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝

──── FULL RESUME PROMPT (copy if you need to paste manually) ────
$RESUME_CONTENT
──── END OF RESUME PROMPT ────

EOF
```

### Step 5: Exit cleanly

The skill is done. **Do NOT** continue tool calls or reasoning after the
visible block prints — the user needs the block to be the last thing in
the conversation so it's easy to find / copy from. The user takes over.

---

*ACOS Eternity Protocol — Warp Variant. Artifacts auto-generated; manual `/clear` + resume by the user.*
