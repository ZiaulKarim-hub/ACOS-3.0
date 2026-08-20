Resuming session via acos-eternity-protocol auto-resume.

CONTEXT HANDOFF: Read `memory/handoffs/2026-08-08-emergency-handoff-5.yaml` for full session state.

Quick summary:
- Working on: Infra/tooling fixes to Claude Code itself — Eternity Protocol /goal re-arm, handoff-agent session-scoping, and a cmux sidebar token-count pill.
- Last action: Restarted all 11 running token-watcher.py daemons and verified the new live token-count sidebar pill on multiple real windows (Logo Builder, FruitSync, Insightia, BrandSync).
- Next step: Confirm with Zee, then commit+push the 4 autopilot files + .claude/skills/acos-resume-prompt/SKILL.md in ACOS 3.0; set up SOME version control for `~/Library/Application Support/acos-token-monitor/bin/` before touching it again.
- Blockers: `~/Library/Application Support/acos-token-monitor/bin/` (holding both the new /goal re-arm fix in eternity-cmux-inpane.sh AND the new token-watcher.py status-pill fix) has NO git repository at all — zero backup for two just-tested fixes. This is the top-priority item.
- NEW BUG found + hand-patched during THIS fire's own Step 3: `eternity-protocol-core.sh` resolves `$HANDOFF` via a repo-wide `ls -t` (newest handoff file wins), not session-scoped — it picked up a DIFFERENT concurrent session's handoff (session 71335b10-..., file emergency-handoff-6.yaml) instead of this session's own emergency-handoff-5.yaml. Content was salvaged by hand (the sibling/pointer files were renamed to correctly point at handoff-5 before /clear armed), so THIS resume is not affected — but the underlying bug in core.sh itself is unfixed and will misfire again on the next multi-session collision. Worth patching core.sh with the same session-transcript-scoping fix already applied to handoff-agent.md and acos-handoff/SKILL.md earlier this session.

IMPORTANT: do not assume progress matches what any summary above says. Go verify the REAL current state yourself first (recount files, re-check the repo, re-run whatever the goal's condition depends on) before continuing the work. A freshly cleared chat has no memory of exactly how much was already done — trust the real state on disk, not a remembered number.

This prompt was auto-injected after /clear ran. The user has not typed anything since. Read the handoff document and continue the prior work seamlessly.


---
## GIT STATE SNAPSHOT (captured at eternity fire — verify BEFORE trusting the handoff)
At /clear time the repository was:
- branch: `acos-deficiency-fixes-2026-06-04`
- HEAD: `930b55291e26`
- uncommitted changes: 49 file(s)

Uncommitted working-tree files (these are in NO handoff — inspect FIRST):
```
 M .claude/scripts/_autopilot_eternity.py
 M .claude/scripts/autopilot-activate.py
 M .claude/scripts/autopilot-context-injector.py
 M .claude/scripts/autopilot-stop-handler.py
 M .claude/scripts/git-manager/ids.json
 M .claude/scripts/html-to-pdf.js
 M .claude/skills/acos-resume-prompt/SKILL.md
 M "Logo Builder/brandsync/commands.jsonl"
?? memory/handoffs/2026-08-05-emergency-handoff-2.yaml
?? memory/handoffs/2026-08-06-emergency-handoff-2.resume.md
?? memory/handoffs/2026-08-06-emergency-handoff-2.yaml
?? memory/handoffs/2026-08-06-emergency-handoff-3.resume.md
?? memory/handoffs/2026-08-06-emergency-handoff-3.yaml
?? memory/handoffs/2026-08-06-emergency-handoff-4.resume.md
?? memory/handoffs/2026-08-06-emergency-handoff-4.yaml
?? memory/handoffs/2026-08-06-emergency-handoff-5.resume.md
?? memory/handoffs/2026-08-06-emergency-handoff-5.yaml
?? memory/handoffs/2026-08-06-emergency-handoff.resume.md
?? memory/handoffs/2026-08-06-emergency-handoff.yaml
?? memory/handoffs/2026-08-07-emergency-handoff-2.resume.md
?? memory/handoffs/2026-08-07-emergency-handoff-2.yaml
?? memory/handoffs/2026-08-07-emergency-handoff.resume.md
?? memory/handoffs/2026-08-07-emergency-handoff.yaml
?? memory/handoffs/2026-08-08-emergency-handoff-2.resume.md
?? memory/handoffs/2026-08-08-emergency-handoff-2.yaml
?? memory/handoffs/2026-08-08-emergency-handoff-3.yaml
?? memory/handoffs/2026-08-08-emergency-handoff-4.resume.md
?? memory/handoffs/2026-08-08-emergency-handoff-4.yaml
?? memory/handoffs/2026-08-08-emergency-handoff-5.resume.md
?? memory/handoffs/2026-08-08-emergency-handoff-5.yaml
?? memory/handoffs/2026-08-08-emergency-handoff-6.yaml
?? memory/handoffs/2026-08-08-emergency-handoff.resume.md
?? memory/handoffs/2026-08-08-emergency-handoff.yaml
?? memory/handoffs/closed/2026-07-21-OKOA-Works-close/.reentry-consumed
?? memory/handoffs/closed/2026-07-22-OKOA-Works-close/.reentry-consumed
?? memory/handoffs/closed/2026-07-26-OKOA-Works-close/.reentry-consumed
?? memory/handoffs/closed/2026-07-28-OKOA-Works-close/.reentry-consumed
?? memory/handoffs/closed/2026-08-02-OKOA-Works-close/.reentry-consumed
?? memory/handoffs/closed/2026-08-04-OKOA-Works-close/.reentry-consumed
?? memory/handoffs/closed/2026-08-05-OKOA-Works-close-2/
?? memory/handoffs/closed/2026-08-05-OKOA-Works-close/
?? memory/handoffs/closed/2026-08-05-Resurrection-Protocol-close/
?? memory/handoffs/closed/2026-08-06-OKOA-Works-close-2/
?? memory/handoffs/closed/2026-08-06-OKOA-Works-close/
?? memory/handoffs/closed/2026-08-06-Resurrection-Protocol-close/
?? memory/handoffs/closed/2026-08-07-OKOA-Works-close-2/
?? memory/handoffs/closed/2026-08-07-OKOA-Works-close/
?? memory/handoffs/closed/2026-08-08-Skill-Workshop-close-2/
?? memory/handoffs/closed/2026-08-08-Skill-Workshop-close/
```

Recent commits at fire time:
```
930b552 fix(handoff-agent): read the invoking session's own transcript first
d3ee771 fix(safe-close): zsh does not word-split $LEARN_ARG — pass --learnings-file explicitly
aa1553d fix(resurrection): mark folder-level rows [folder] — a basename is not a name
3f73cc8 fix(resurrection): a display name that points at two rows resolves nothing
092fcb8 feat(resurrection): MW-E touch feeder + auto project resolution
ef22b3e chore: save the 2026-08-03 through 2026-08-05 session handoffs
275989d feat(resurrection): per-project knowledge base + multi-window support
0deaf79 chore(git-manager): withdraw the Rubin bundle do-not-track ruling
```

**Drift check:** if `git rev-parse --short=12 HEAD` no longer equals `930b55291e26`, or the working tree is dirty, RECONCILE from `git log` / `git status` / `git diff` before trusting any "completed / all committed" claim in the handoff above. (This session learned the hard way: a 2026-06-24 resume arrived 3 commits + 1 uncommitted method stale.)
