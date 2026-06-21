Resuming session via acos-eternity-protocol auto-resume.

CONTEXT HANDOFF: Read `/Users/zee/Documents/Vibe Coding/ACOS 3.0/memory/handoffs/2026-06-16-emergency-handoff.yaml` for full session state.

Quick summary:
- Working on: acos-guided-reader global skill (~/.claude/skills/acos-guided-reader/). 11 major features shipped this session including Tier C+ language expansion, mnemonic-first keymap, pure-document default view, AI chunk titles, hover synonyms with context-aware AI definitions, prose-flow rendering, paste-to-read pipeline, no-args auto-paste UX, AF_UNIX socket path fix, SSE-reload on view-mode change.
- Last action: Locked the full Tier H (image capture mode) design with the user. Floating tkinter "I" badge widget (~60×60 always-on-top) + two capture paths (right-click → screencapture -i, OR Cmd+Shift+Ctrl+4 → clipboard poll). Every capture runs OCR + Claude vision in parallel. Captures + pastes append as attachments to current reading session (not new sessions). Ephemeral /tmp storage, wipe on session end. ~500 LOC, ~4-6 hr build estimate.
- Next step: IMMEDIATE — start building Tier H. User said "say go and I'll ship it" — they already approved the design. NO confirmation gate needed. Build straight into implementation: floating widget, clipboard poll, OCR + Claude vision pipeline, attachments schema, capture sidebar UI, append-on-paste behavior.
- Blockers: Tier H not started. Live server may be down (last URL was http://127.0.0.1:64254/). If down, kill stale processes + restart paste-starter session via build-page.py --reading-id paste-starter-md-c1bbb4 --serve --auto-paste from project root.

Critical context to NOT lose:
- All work this session is in the GLOBAL skill (~/.claude/skills/acos-guided-reader/), NOT inside the ACOS 3.0 git repo. git status in the project won't show these changes.
- NEVER use ANTHROPIC_API_KEY (memory feedback_subscription_not_api). All claude subprocess calls use /Users/zee/.claude/local/claude CLI binary.
- AI title generation uses 16 parallel workers + 90s timeout (was 8/30s, debugged this session).
- Pool socket path is /tmp/gr-pool-<sha1(reading_id)[:8]>.sock — hash-derived for AF_UNIX 104-char limit safety.
- view_mode field replaces full_mode (legacy mirror still written). Default is 'pure'.
- For Tier H: tkinter widget is stdlib (no install). tesseract needs `brew install tesseract`. Claude vision via `claude --model sonnet -p "describe this image" <image_path>` — verify the exact CLI form before relying on it.

This prompt was auto-injected after /clear ran. The user has not typed anything since. Read the handoff document and continue the prior work seamlessly — start by reading the handoff for the full feature inventory and pending Tier H spec, then begin implementation immediately.
