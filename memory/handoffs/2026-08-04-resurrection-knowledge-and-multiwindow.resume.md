Resuming the Resurrection Protocol project to implement an agreed design.

CONTEXT HANDOFF: Read `/Users/zee/Documents/Vibe Coding/ACOS 3.0/memory/handoffs/2026-08-04-resurrection-knowledge-and-multiwindow.yaml` IN FULL before writing any code. It is a complete design brief, not a status note. Every open decision was settled by Zee across four /restate rounds, and several of them overrule Claude's own proposed default — do not quietly reinstate what he rejected.

Quick summary:
- This work was designed in the OKOA Works window on 2026-08-04 and moved here on Zee's instruction. NOTHING has been built. No script changed, no directory created.
- Two workstreams. `KB-A..KB-E` = per-project knowledge bases that accumulate across resurrections. `MW-A..MW-E` = several context windows working one project coherently. Zee approved all ten items.
- Start with `MW-A`. It is a LIVE DATA-LOSS BUG, not a feature.

THE BUG, FIRST:
`adopt-project.sh` resolves the reentry note by scanning `memory/handoffs/closed/` and taking the NEWEST by file modification time. Observed live this session:
  `reentry source: scan of closed/ at adopt time (newest of 24 candidates by mtime)`
With one window per project that is harmless. With several windows on one project, the last window to close SILENTLY HIDES every other one. No warning, no error, nothing in the book. Multi-window support is unsafe until this is a merge of all unconsumed notes for the project uuid.

THE TWO IDEAS THAT ARE EASY TO LOSE:
1. A handoff and a knowledge base are DIFFERENT JOBS. A handoff answers "where was I". A knowledge base answers "what do I know". Zee had been expecting the first to do the second; it never will, by design. Do not merge them.
2. An approval gate only works if the approver can judge the item. Zee said plainly he does not read these and cannot evaluate the technical ones. So machine-verifiable facts get written SILENTLY, and only his own rulings are asked about — capped at two questions per session, phrased about the decision and never the mechanism. Safety comes from four rules, not from a prompt: evidence-or-no-write, append-only, staleness re-check, and an after-the-fact digest he can strike lines from.

WHY THE AUDIT SAYS THIS IS NEEDED (all figures verbatim, all reproducible):
- Six OKOA Works closes since 2026-07-21. intent_core sizes 3050 / 2167 / 2585 / 5612 / 3828 / 5943 chars — session-sized, never cumulative. The newest handoff retains nothing from any earlier session.
- The OKOA knowledge base holds 156,622 characters across 28 .md files, but 23 of 28 are frozen since before 2026-07-18.
- The mining watermark `references/.last-mined` still reads `2026-07-17T14:09:09-0600 initial-mine` — unmoved for 18 days.
- `references/.rejected-learnings.md` is 0 lines. Zee has never declined a learning, meaning he was almost never offered one.
- Stored facts have drifted: `deal-index.md` says the Kohan folder holds "1,305 files"; the live count is 1,594. It names one sale data room; three exist.

BUILD ORDER:
1. `MW-A` — merge every window's reentry at pick (the bug above).
2. `KB-A` + `KB-C` together — the capture loop AND the staleness re-check. They ship as one unit: once writes are silent, the staleness check is what makes silent writing safe. Do not split them.
3. `KB-B` (knowledge index + digest on adopt), `MW-B` (window labels in the book), `MW-C` (shared project brief so windows do not duplicate work).
4. `KB-D` (backfill from the 24 closed bundles), `KB-E` (cross-project tagging), `MW-D` (merge verb), `MW-E` (collision warning — build last, behind a switch; Claude costed it high and advised deferring, Zee said do all five).

KEY DECISIONS YOU MUST NOT REOPEN (full list is D1-D16 in the yaml):
- Store at `~/.acos/knowledge/<project_uuid>/`, keyed by project uuid NOT folder root — OKOA Works, ACOS 3.0 and Resurrection Protocol all share the root `/Users/zee/Documents/Vibe Coding/ACOS 3.0`, so folder-keyed storage would merge them.
- Window names derive from the project name — Zee's wording: `OKOA works *label*`. So "OKOA Works Golden East". The project name stays the stem.
- On safe close, a labelled window's learnings fold back into the single per-project store. The label survives as provenance on each fact, not as a separate store.
- The book keeps ONE row per project with a live-window count, e.g. `7. OKOA Works (2 open)`. Splitting into several rows was explicitly rejected.
- The one-project-one-tab guard STAYS. But picking an already-open project now ASKS: focus the existing window, or open another. Zee wants the choice, not the removal of the guard.
- Closing one window does not park the project. It parks when the LAST window closes.

RESTRICTED — do not touch without Zee present: `review-rules/` (human-editable only) and `.claude/agents/` (modification requires human approval).

HONEST RISK ON THE RECORD: silent auto-writing means a wrong fact can enter without Zee seeing it. The four safety rules shrink that risk but do not remove it. It was accepted because the status quo fails worse — today nothing is captured at all, and what was captured has already gone stale unchecked.

Next step: read the yaml, then fix `MW-A`.
