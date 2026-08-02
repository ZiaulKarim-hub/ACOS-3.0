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

See `memory/decisions/`. Four settled decisions, do not reopen:

- **D1** — ~10 coherent whole design *directions*, not independent per-item picks; 20 artworks;
  10 variants per component on demand; derived values computed, never chosen
- **D2** — constraint-based dragging (pin/anchor/stretch), per-component free-position escape
  hatch; gridlines are what components snap to
- **D3** — LOCK **exports** a clean static site with no editor runtime; editable project kept beside it
- **D4** — motion is a design-system item with variants, living in the same draggable art-style
  containers as artwork

## What exists

| Path | What |
|---|---|
| `prd/website-builder-prd.md` | **The PRD.** 635,881 chars, 4,225 lines, 99,380 words, 20 sections |
| `prd/OPEN-ITEMS.md` | 66 deliberately-open items (15+ need Zee's decision) |
| `DECISIONS.md` | The open decisions, each with a recommendation — **start here** |
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

## ⚠ The thing that blocks everything else

`prd/website-builder-prd.md` §18 opens with **"Vision deviations requiring sign-off"**. As
drafted, **v1 does not deliver gridlines (Step 4a) and delivers dragging only as reorder
(Step 4b)** — two of the six editor features named in the brief. D2 is therefore *inert* in
the first shipping version. That table needs Zee's answer before any build starts.

## NEXT ACTION

Settle the open decisions in `DECISIONS.md`, starting with the §18 v1 scope sign-off.
