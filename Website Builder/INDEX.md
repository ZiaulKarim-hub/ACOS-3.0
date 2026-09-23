# Website Builder — project index

**One screen. Read this before anything else in this folder.**

Moved here 2026-07-26 from `ACOS 3.0/.acos/swarm/swarm-20260718-022431` (a swarm research
scratch folder, git-ignored). This is now the project root.

---

## What this project is

A Claude Code skill — will ship as **`/acos-website-forge`** (decided 2026-07-26; PRD prose
still uses the old working name `acos-website-builder`) — that builds a website through a
**human-in-the-loop** loop, not an autonomous one. The human is the aesthetic judge at every
step. Eight steps:

| Step | What happens | Who |
|---|---|---|
| 0 | Warm start — reuse a prior design system if one exists | skill |
| 1 | Interview the user about the site and the design system | skill |
| 2 | Generate a prompt that produces the whole design system | skill |
| 3 | User pastes that prompt into Claude on the web, generates the items | **user, by hand** |
| 4 | User hands the bundle back; skill interviews for picks, then builds a **live editable site** | both |
| 5 | If nothing looks good: more variants, or a fresh design-system prompt | user |
| 6 | Add custom components (charts, graphs) not normally included | user |
| 7 | LOCK — toolbars and gridlines vanish, visitor view, reversible | skill |
| 8 | Publish + licence/evidence bundle | skill |

Step 4's editable site must have: gridlines, drag-movable components, editable text, a
component bar for swapping variants, saving — plus everything research says a tool at this
level needs.

## What is decided and NOT open

See `memory/decisions/`. **Six** settled decisions, do not reopen:

- **D1** — ~10 coherent whole design *directions*, not independent per-item picks; 20 artworks;
  10 variants per component on demand; derived values computed, never chosen
- **D2** — constraint-based dragging (pin/anchor/stretch), per-component free-position escape
  hatch; gridlines are what components snap to
- **D3** — LOCK **exports** a clean static site with no editor runtime; editable project kept beside it
- **D4** — motion is a design-system item with variants, living in the same draggable art-style
  containers as artwork
- **D5** (2026-08-20) — layers are a real document tier between Section and Block; editing one
  layer never disturbs the layers below. Five levels, not four; sections own layer stacks
- **D6** (2026-09-22) — a **URL** is a valid way to start a website. The faithful copy it produces
  is an intermediate step that may **never** ship; the fan-out is what earns publication, and
  gate 35 is what proves it (PRD §21)

## What exists

| Path | What |
|---|---|
| `prd/website-builder-prd.md` | **The PRD.** 23 sections. §§21–23 appended 2026-09-22: the clone-and-fan-out route (D6), holdout verification imported from R2P, and the Logo Forge absorption map. Was 635,881 chars / 4,225 lines / 99,380 words / 20 sections before that pass |
| `prd/OPEN-ITEMS.md` | 66 deliberately-open items (15+ need Zee's decision). **Does not yet carry O36–O46**, added 2026-09-22 by §§21–23 and registered in §19's roll-up |
| `DECISIONS.md` | The open decisions, each with a recommendation — **start here.** Items 1 and 2 settled; 14 open |
| `planning/slices/` | 78 ACOS slices, ids `S01`–`S78` carried verbatim from preeng. **77 MUST / 1 COULD** — exactly one trade-back lever if the schedule slips |
| `prd/sections/` · `prd/sections-revised/` | Per-section originals and patched versions |
| `prd/critic-gaps.json` · `prd/audit-gaps-run2.json` | 41 + 74 = 115 recorded gaps |
| `prd/website-builder-prd-v1-preharden.md` | Pre-audit PRD (286,861 chars) kept for diffing |
| `research/swarm-report-2026-07-18.md` | The original 20-agent research report |
| `research/swarm-plan-2026-07-18.md` | That swarm's research plan |
| `memory/handoffs/closed/` | Close records from 2026-07-20 and 2026-07-26 |

Raw per-agent findings stay behind at `ACOS 3.0/.acos/swarm/swarm-20260718-022431/agent-*/`.

## PRD inventory sizes (verified row counts)

| Section | Rows |
|---|---|
| §5 Interview question bank | 122 |
| §7 Design system inventory | 261 |
| §8 Component inventory | 324 |
| §9 Motion & art containers | 84 |
| §10 Editor feature set | 155 |
| §12 Document model / LOCK | 139 |
| §16 Architecture | 89 |
| §19 Acceptance criteria | 96 |

## How it was built

Two agent workflows, 38 agents total, 3,937,989 subagent tokens, 588 tool uses, 0 errors.

1. `wf_f28130f3-9ce` — 12 research lenses across Opus/Sonnet/Haiku, one Opus author, two
   critics, one reviser. Found 41 gaps.
2. `wf_598627af-92b` — 4 auditors over the never-reviewed sections 1–12, then one patcher per
   gapped section writing to disk. Found 74 more gaps; 120 closures recorded, 66 deferred.

A truncation bug in run 1 meant the critics only ever saw sections 13–20; run 2 exists to
close that hole. The full PRD was recovered from the author's transcript, not regenerated.

## ☑ The thing that used to block everything else — RESOLVED

`prd/website-builder-prd.md` §18 opens with **"Vision deviations requiring sign-off"** and the
rule *"Nothing in v1 may be built until the sign-off column below is resolved."* **Every row now
carries a resolution and that precondition is satisfied** — see §18.0.1. It was the gate for 58
days.

- **4(a) gridlines and 4(b) dragging** — resolved 2026-07-26 by DECISIONS.md item 1, option B.
  Both are **in v1**, so D2 is **active** in the first shipping version, not inert. R47 retired.
- **4(c), 4(d), 4(f), 6** — signed 2026-09-22, with three carve-outs: **inline links** in v1,
  **minimal multi-select** in v1, and charts signed **conditional on** the two §10.3 rows
  (a minimal insertion registry and a chart-data field), which are signed with them.
- **7 LOCK** — follows 4(a).

## 🔨 Build run — started 2026-09-22 (autopilot)

Driven by `planning/BUILD-CHARTER.md` (78 slices `S01`–`S78`, dependency graph derived not
asserted, 22 waves, 0 cycles). Wave 1 is the E0 phase-0 spikes.

| Slice | What it answers | Status | ADR |
|---|---|---|---|
| `S01` | Gate 16-A turn boundary, launcher rung | **INCOMPLETE** — ordinary boundary MET, the `/clear` crossing NOT tested | — |
| `S02` | Font policy: does `document.fonts.check` tell the truth? | **PARTIAL** — local control settled; the generation-surface observation needs Zee at a browser | `ADR-02` PARTIAL |
| `S03` | Framework versus plain generated HTML | layer 1 COMPLETE | `ADR-03` **NON-DECISION**, invariant I6 stands |
| `S04` | Single origin versus two origins | layer 1 COMPLETE, charter only partly executed | `ADR-04` **NON-DECISION**, §17-O4 stands |
| `S05` | §12-O33 build byte-reproducibility | layer 1 COMPLETE, **question ANSWERED: yes** | `ADR-05` measured, 6 limits |
| `S06` | Channel fidelity, output ceiling, latency, licences | **PARTIAL** — only part (d), licences, is done | — |
| `S79`/`S80` | Holdout tooling imported from R2P (§22) | self-test **89/89 exit 0** incl. a 2000-document property test against ground truth; concurrency stress **300 rounds, every check held**; **17 defects** found and fixed (5 self-found, 12 by QA review across six REJECTs); **QA reviewer PASSED at round 8**, with its own uncovered list preserved; layer 4 NOT run; security/performance/integration reviewers have never seen it | — |
| `S81` | The §18.0.2 re-baseline | **DONE** — counts verified 87/674, day figures resolve to a band of **27.8–68.6 days**; `planning/REBASELINE-18.0.2.md` | — |
| `S82` | O36 capture-fidelity spike | **not started.** The charter says it *"is not a prerequisite for anything in this charter's scope"* — listed so it is not forgotten | — |

Evidence bundles: `.acos/evidence/2026-09-22/<slice>/`. Four ADRs: `docs/adr/`.

**The critical path is the holdout tooling, not the slices.** `S79`/`S80` are hard prerequisites
for `S01`. They were REJECTED six times before the QA reviewer PASSED them at round 8.
Seventeen defects were found on the way; five were self-found and twelve came from review, and
twice a fix that had already been regression-tested AND mutation-tested was defeated on the next
pass. **One PASS from one reviewer is not clearance**: layer 4 has not run, and the security,
performance and integration reviewers have never seen this code.

**Scope note worth a ruling.** The build goal as worded asks for *"every slice S01-S78 …
each gated by a revealed holdout pack that passes."* The PRD is narrower: §22.3 says **not all
78 get a pack** — *"a process that heavy is abandoned, and an abandoned gate reads as protection
that is not there"* — and the charter's §3.1 names which slices earn one. The PRD governs here,
since the goal's own first clause is *"Build the Website Builder to its PRD"*. Flagged rather
than resolved silently.

**Three of the four ADRs decline to decide.** That is deliberate — each names the open
`DECISIONS.md` item or PRD open question that owns the choice, rather than quietly picking a
default. The build charter forbids picking: *"Do not pick. Do not pick 'provisionally'. Do not
record a default and move on."*

## ⚠ What blocks things now

1. **☑ The re-baseline HAS now been run** (§18.0.2) — result in `planning/REBASELINE-18.0.2.md`.
   §8.4's counts were parsed and re-added mechanically and are **correct**: 87 pickable items /
   674 variants, every family's internal arithmetic matching. The day figures resolve to a
   **band, not a point**, because no per-item day cost is measured anywhere in the PRD and
   §18.0.2 forbids inventing one. The Branch A+ spine is **27.8–41.8 days if nothing scales**,
   **41.5–62.3** if the three build lines scale with variants, **45.7–68.6** if they scale with
   items. The old instruction to treat every §18 figure as a floor is **confirmed and
   quantified**. Still open, and deliberately not folded in: item 1's ~16–24 days, D5's further
   16–24 days (both inference, and they stack), and C1–C3 which are unbudgeted. §13's gate
   budgets are **not** re-baselined — §13.1 is sized against the 32-gate list, not the item
   catalogue, so scaling it against 87/674 would be the wrong operation on the wrong variable.
2. **O36 — capture fidelity is unmeasured** (§21.10, now item 0 of §20.4). §21's whole drift
   machinery is computed against a copy whose completeness nobody has measured. The only figure
   available, **~83–87%**, is another skill's ceiling for one capture layer.
3. **Fourteen decisions remain open** in `DECISIONS.md` (items 3–16).
4. **The review gate cannot currently be trusted, and the reviewers stall.** Two separate faults,
   both found 2026-09-22:
   - *Isolation is void.* ACOS spawns reviewers in git worktrees, and a worktree only contains
     **tracked** files. Every file in this build is new and uncommitted, so
     `.claude/worktrees/agent-*/Website Builder/` is **empty**. The reviewers do not fail — they
     silently read the live project root instead. Consequence: no edit may touch a reviewed file
     while a review is in flight, or the findings cite lines that have moved.
   - *Parallel fan-out hangs; sequential works.* Three reviewers froze mid-command within 48
     seconds of each other and wrote nothing for the following hour; one ignored a direct message
     for 240 seconds. All three were stopped. **A single sequential reviewer then ran to
     completion** and returned **REJECT** with two further defects, both since fixed and
     regression-tested. It does hit a 30-turn cap and must be resumed by message, which is a
     budgeting problem, not a hang. Match: `reference_subagent_fanout_stall_watchdog`
     (2026-09-10, 14 parallel sub-agents all died the same way).
5. **A PRD contradiction, found by `S04` and referred rather than resolved.** §11.7 is titled
   *"Preview must be a same-origin iframe"* while §16.6.1 says the single-origin-versus-two-origin
   choice is **open**. If §11.7's title binds, `S04` was unnecessary. See `ADR-04`.

## NEXT ACTION

Zee decides four things, in this order:

1. **§11.7 versus §16.6.1** — does §11.7's title bind? If yes, §17-O4 closes and `S04` need not
   be redone.
2. **Commit before reviewing?** Committing the build would make worktree isolation real. Nothing
   has been committed or pushed yet.
3. **`DECISIONS.md` item 5** — `S05` measured byte-reproducibility as **achievable**, so
   §12-O33's fallback is not needed on that evidence. Item 5 is still formally Zee's to close.
4. **Accept the non-git pid-injection chain as a documented limitation?** The QA reviewer
   recommends yes. The route is closed for any repository with a resolvable `HEAD`; what remains
   needs a machine outside any git repository, **plus** a human deleting a live lock, **plus**
   knowledge of its real pid. It has never been live-tested. Nothing has been accepted in code,
   and the reviewer asked explicitly that this not be assumed from its silence.

Then: `DECISIONS.md` item 3. (The §18.0.2 re-baseline is done — see blocker 1 above.)
