Resuming session via acos-eternity-protocol auto-resume.

CONTEXT HANDOFF: Read `memory/handoffs/2026-08-03-emergency-handoff.yaml` for
full session state. (Use THAT file — several same-day handoffs exist; the
2026-08-02 ones are earlier sessions.)

Quick summary:
- Working on: (1) the GLOBAL skill `~/.claude/skills/acos-logo-forge/` (it lives
  in the `~/.claude/skills` repo, NOT in ACOS 3.0) driving the untracked in-repo
  workspace `Logo Builder/brandsync/` via `app/server.py` on 127.0.0.1:8815
  (PID 43272 — check `lsof -i :8815` before starting a second one); and
  (2) `.claude/scripts/git-manager/`, which now has PERMANENT row numbers.
- Last action: pushed rows 4/5/6 to personal — ACOS 3.0 `aa6ea92`,
  `~/.claude/skills` `0f14b3a`, FruitSync `af7d31e`. All verified, 0 unpushed.
- Next step: put the TWO OPEN DECISIONS below in front of Zee. Nothing else is
  blocked; both need his explicit word, not a guess.
- Blockers: none technical.

OPEN DECISION A — row 7 push, NOT done, needs Zee's explicit yes.
Zee said "push 4, 5, 6, & 7 all of them to personal", then "push now" after
interrupting a permission dialog. Rows 4/5/6 are pushed. Row 7 is
`/Users/zee/Documents/OKOA/Rubin_Counsel_Bundle_20260423` — 108M, 96 files, NOT
a git repo, so "push" means git init + first commit + creating a new GitHub
repo. It carries his own recorded ruling in
`.claude/scripts/git-manager/decisions.json`: `"decision": "do-not-track",
"date": "2026-08-02", "reason": "Legal counsel material for an OKOA deal. Zee's
call 2026-08-02: it stays off GitHub entirely, personal or work."` Contents:
borrower entity docs, PFS/SREO, underwriting and LOI files, loan files, "Rubin
Evidance Documents from Ty". His "push now" answered a permission box, NOT this
conflict — he has not yet seen it flagged. Ask once, plainly. If he says yes,
update the ruling in decisions.json to match.

OPEN DECISION B — `ZiaulKarim-hub/ACOS-3.0` is a PUBLIC repo (verified; the
other two are PRIVATE). This session pushed a NEW file into it,
`.claude/scripts/git-manager/ids.json`, holding absolute folder paths — 9 of 38
are under `/Users/zee/Documents/OKOA/`, including `Rubin_Counsel_Bundle_20260423`,
`OKOA_Prospectus`, `Rubin Document Production/audit`. Folder NAMES only, no
documents, but they carry client/matter names. `decisions.json` was already
tracked and already exposed three. Offered, NOT done: make it private via
`gh repo edit ZiaulKarim-hub/ACOS-3.0 --visibility private --accept-visibility-change-consequences`,
or stop tracking ids.json (paths stay in history unless rewritten).

Standing directives: Eden Protocol Level 2 for chat replies (plain language,
sentences <=22 words, define every term, keep all numbers and caveats verbatim).
Verify visual claims by looking at PIXELS, never container boxes or layer counts.
git-manager row numbers are stable now, but ALWAYS resolve a number by re-running
the scan yourself or from a table Zee pastes — never from a `git-manager.html`
found in another session's scratchpad (that mistake cost an exchange this
session). Never a bare `git push`; name the remote. The ACOS 3.0 working tree is
shared by several concurrent Claude sessions — scope commits, never sweep.
Tests forge-test/shapes-test/gallery-test/reject-test are NOT idempotent; each
needs a fresh workspace copy (their headers give the exact commands).

This prompt was auto-injected after /clear ran. The user has not typed anything
since. Read the handoff document and continue the prior work seamlessly.


---
## GIT STATE SNAPSHOT (captured at eternity fire — verify BEFORE trusting the handoff)
At /clear time the repository was:
- branch: `acos-deficiency-fixes-2026-06-04`
- HEAD: `aa6ea927eb92`
- uncommitted changes: 1 file(s)

Uncommitted working-tree files (these are in NO handoff — inspect FIRST):
```
?? memory/handoffs/2026-08-03-emergency-handoff.yaml
```

Recent commits at fire time:
```
aa6ea92 docs(git-manager): document permanent row numbers
b8660c7 fix(git-manager): row numbers are permanent, not positions
5934bc1 chore: snapshot working tree — git-manager, axiom-synthesis, research-riffs, logo-forge workspace
0452552 feat(git-manager): remember what the human ruled out, and fit the browser table
757a414 chore: back up working tree — git-manager skill + accumulated session work
551301a feat(website-builder): promote the PRD out of swarm scratch into a real project
88c1597 feat(resurrection): adopt-in-place — a pick lands in the tab it was typed in
d5f352a feat(research-riffs): live responder — seats answer on their own in ~5-7s
```

**Drift check:** if `git rev-parse --short=12 HEAD` no longer equals `aa6ea927eb92`, or the working tree is dirty, RECONCILE from `git log` / `git status` / `git diff` before trusting any "completed / all committed" claim in the handoff above. (This session learned the hard way: a 2026-06-24 resume arrived 3 commits + 1 uncommitted method stale.)
