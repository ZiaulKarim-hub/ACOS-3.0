# Vision ↔ Research Deltas

Every point where the confirmed vision (2026-07-16) and the research evidence disagree, with the proposed resolution. Agreements (e.g., the user's instinct that `/acos-resume-prompt` serves a different purpose — Change 5 confirms it and sharpens it to pane-durable vs pane-independent) are not listed.

## D1 — "One master document" vs. sharded storage
- **Vision said:** one master document ("the book") listing every active project.
- **Report says:** a single shared mutable file is the worst substrate — without a lock only 3/25 concurrent writes survive *and the file stays valid JSON* (silently wrong); the advisory lock is cooperative-only; verdict is one file per project (`~/.acos/registry.d/<project_uuid>.json`), which deletes the lost-update/lock/reaper problem by construction. YAML and SQLite are separately disqualified.
- **Resolution:** the BOOK is preserved as the user-facing concept — one unified view, rendered FRESH on every invocation of the menu — while storage is sharded per project. No persisted master file exists to go stale ("a stale registry is a lying registry").

## D2 — Close "adds or updates" the book vs. close never creates
- **Vision said:** the safe-close step writes the handoff and updates the book (implying close populates it).
- **Report says:** the stated failure mode is force-quit, and in a force-quit the close step never runs — a close-populated registry is empty at exactly the moment it exists to serve (DR-8). Close also fires when context is nearly exhausted — the moment fidelity matters most is when the session can least deliver it. The rebuild-from-disk alternative is proven (16/16 rows).
- **Resolution:** membership by **enrollment on first sight** (marker-gated: `.acos/` OR `CLAUDE.md` OR `memory/handoffs/`; never a naive scan); the close step **enriches** the existing row with the one thing no scan recovers — the reasoning, traps, rejected alternatives, and the next-action headline. User-visible behavior is unchanged: after every close, the book is current.

## D3 — "Details" per project vs. no hand-written descriptions
- **Vision said:** the book lists every project by name **with details**.
- **Report says:** humans do not fill in description fields (native fields measured 3/42 and 2/6 populated); a static blurb is written once and never read again ("he knows what FruitSync is; he does not know what he was doing"); the row's payload must be a **generated** next-action headline ≤90 chars — and this is the single highest-risk dependency in the design (real Next-step fields run 400–800 chars; truncation yields noise; it must be generated at close, never truncated).
- **Resolution:** "details" = the generated `next_action` line plus derived facts (dirty file count, staleness amber, clickable handoff link) — never a typed description, never a verdict, never a green badge. Any static description survives only as search fodder.

## D4 — Menu inside Claude Code vs. browser window
- **Vision said:** run the Resurrection Protocol inside Claude Code; the book appears as a menu there.
- **Report says:** it designed a localhost browser window (view + focus/launch, port 8820) — but it was never asked to compare against an in-terminal menu, and all its binding evidence (per-project rows, focus-not-launch, generated headline, facts-not-verdicts) is surface-independent.
- **Resolution:** genuine user decision — **DP1**. One shared engine (`resurrect-view.py`, `launch-project.sh`) powers either surface; recommendation is menu-first (matches the confirmed vision, no server security surface), browser as an optional later phase.

## D5 — "Open Claude Code anywhere" vs. cwd-identity coupling
- **Vision said:** later, open Claude Code **anywhere**, pick a project, and work continues where it left off.
- **Report says:** the registry key and Eternity's `sanitize(cwd)` key must not disagree (risk #7): continuing project X inside a session whose cwd is project Y either silently loses the resume (fails safe) or merges two projects' scopes (fails open — un-doing the f639310 cross-contamination fix by construction). `sanitize(cwd)` is proven non-injective.
- **Resolution:** you can *invoke the menu* anywhere, but the **work always lands at the project's own root**: same-root picks load the reentry inline; anything else routes through focus (existing workspace) or launch (new workspace at exactly `realpath(registry.root)`), with a SessionStart assertion that `realpath(cwd) == registry.root`, logging loudly on mismatch.

## D6 — "Zero loss" vs. what actually dies, and silent failure as the base rate
- **Vision said:** after safe close, the window closes with zero loss; never lose work to a crash again.
- **Report says:** files/git/memory survive close regardless — what dies is the *reasoning*; a true force-quit still loses reasoning not yet captured. And silent failure is this machine's base rate (10+ instances: the ALL-GREEN doctor over 2,000+ failures; `head -40` hiding 34 of 74 files inside the "inspect FIRST" block — confirmed live today at `eternity-protocol-core.sh:139`; valid-but-wrong JSON; fail-open liveness probes). A "zero loss" promise that is ever silently wrong kills trust permanently.
- **Resolution:** zero-loss is delivered as a **verified receipt, not a promise**: every receipt line read back from disk; `listed N of M` on every list; a blind round-trip agent quoting the reconstructed next step; `SAFE TO CLOSE THIS TAB` printed only by the script on full pass; the tab staying open IS the failure signal. Crash protection (no ritual ran) comes from enrollment + Claude Code's native transcripts (`claude --resume`) + untouched Eternity emergency handoffs — and the residual honesty: uncaptured reasoning still dies in a force-quit, which is exactly why closing must be cheap enough to do daily.

## D7 — "The loop repeats" vs. the graveyard evidence
- **Vision said:** every stop updates handoff + book; the loop is the workflow.
- **Report says:** the existing durable-handoff archive shows no filesystem evidence of ever being read to resume later work (17/17 dangling siblings unnoticed for five weeks; ~10/17 never read after writing); agent 12's unsoftened verdict: ~30% odds of routine use at day 60; "deliberate-with-deferred-payoff is dead." Counter-evidence: 147 hand-run `/acos-complete` invocations prove the user performs rituals with immediate payoff.
- **Resolution:** keep the loop, but invert its economics: the **menu is the way IN** (immediate, felt payoff on every open — including repairing the lying tab bar with real titles), closing becomes the safe byproduct; no nagger; DR-1 (one demonstrated restore, recorded) gates shipping; the audit log + close/resume events provide the one measurement the system most needs (correlating handoff quality with resume success). Provenance of the 147 runs is checked in Phase 0 (if hook-fired, expectations drop further and DR-1 matters even more).

## D8 — "Fewer open windows = fewer freezes" vs. the duplicate problem and hibernation
- **Vision said:** closing windows is the cure for pile-ups and freezes.
- **Report says:** the strongest finding in the swarm (6 agents) is that this is a **duplicate problem, not a switcher problem** — 21 live sessions were ~7 projects, 13 of them ACOS 3.0 alone (and TODAY workspaces 4 and 5 both sit on ACOS 3.0); cmux does no dedup, so opening from anywhere multiplies tabs. Separately, cmux 0.64's Agent Hibernation (UNVERIFIED doc-claim) attacks the RAM/CPU cost without closing anything.
- **Resolution:** both cures, correctly aimed: **focus-never-launch** (one row per project; a click on an open project focuses the existing workspace and can never create a second) kills the duplicate pile-up at its source; closing handles count and clarity; hibernation is adopted opt-in only after the hook-firing test passes (DP4). The report's one-line summary stands: the focus rule "is worth more than every other feature in the window."