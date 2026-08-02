# acos-okoa-works — Skill Outline & Build Plan

**Status:** PROPOSAL (v1, 2026-07-17) — awaiting Zee's review. Nothing is built yet.
**Working name:** `acos-okoa-works` (confirmed by Zee 2026-07-16; "aqua" in dictation = OKOA).

---

## 1. What this skill is

A **persistent OKOA context pack + task router**. Today, every new session re-discovers where the loan folders are, which deal is which, how a deal sheet is rendered, and which traps to avoid — knowledge that already exists, scattered across 289 handoff/memory files. This skill front-loads that knowledge so any session starts pre-briefed, then routes each task to the right existing skill/playbook with the right facts already in hand.

It is a **router and knowledge base, not a replacement**: heavy work still runs through the existing skills (`acos-hypercore-ask`, `acos-dataroom-v2`, `acos-loan-doc-generator`, `acos-xl-update`, `acos-legal-analysis`, `acos-linkedin-posts`, `acos-fireflies-ask`, `acos-ultimate-designer`, `okoa-design` MCP, …).

## 2. Evidence base (what this outline is built from)

Mined 2026-07-16/17 via a 25-agent workflow + 4 make-up readers + adversarial completeness critic with repair pass:

- **178** handoff files in `ACOS 3.0/memory/handoffs/` (current + archive) — all read
- **111** memory + decision files (auto-memory dir + `memory/decisions/`) — all read
- **~56** handoff files from sibling OKOA repos (okoa-wiki, okoa-loan-intake-system, OKOA Website/dev, website-design-okoa, private-equity-hedge-fund-strategy) — all read
- **Live disk map** of Dropbox-OkoaCapital, ~/Documents/OKOA, and code repos (verified by `ls`, not guessed)

Companion data files (the raw material for the build session):

- `mined-synthesis.json` — 26 task playbooks, 27 folder-map entries, 30 deal-index entries, 25 learnings, 27 formatting rules, 17 open questions, critic report, live folder map
- `mined-delta-batches-4-6-9-11.json` — 52 per-file extracts from the four batches the first pass missed (adds: acos-fireflies-ask, XL-update field rules, LinkedIn privacy blocklist, Tooele/Qelo_T222 water-rights finding, Waxahachie HOT deal, Gonzalez/Albert Ave payoff template, Casa Grande I/II, Ville 9 lien stack, Lakeside Landing PPTX lessons, Rubin bundle-curation rules, Ascent dataroom wave architecture, Wright Thurston note terms)

## 3. Design principles

1. **Progressive disclosure.** `SKILL.md` stays thin (~250–300 lines): folder quick-map, task router, red lines. Everything else lives in `references/` files loaded only when the task needs them. Loading all mined knowledge every session would burn ~40k+ tokens; the router keeps it to a few thousand.
2. **Facts carry dates and provenance.** Every dollar figure, payoff, and status gets an `as-of` date. Live disk beats memory when they conflict (proven necessary: memory said `~/Documents/New deals`, disk also has `~/Documents/OKOA/New deals`).
3. **Red lines always load.** The short list of never-break rules rides in SKILL.md itself, not behind a pointer.
4. **Deal-name resolution first.** Before any file search, resolve the spoken/typed name against the alias table (Waldorf→Tapestry, "409 Hodson"→409 High Point, "Waldorff" spelling, Lux I≠Lux II, "LK OKOA"≠OKOA Capital, "a cent"=Ascent in Fireflies, "aqua"=OKOA in dictation).
5. **Maintenance is part of the design.** A skill like this rots without a feedback loop — see §8.

## 4. Proposed file layout

```
.claude/skills/acos-okoa-works/
├── SKILL.md                        # front door: triggers, quick-map, router, red lines
└── references/
    ├── folder-map.md               # every canonical location + navigation rules
    ├── deal-index.md               # one fact-sheet per deal, aka_traps first-class
    ├── formatting-rules.md         # exact hex/fonts/commands — the "never re-derive" file
    ├── gotchas.md                  # cross-cutting environment + process traps
    ├── open-questions.md           # things only Zee can settle; skill ASKS, never assumes
    └── playbooks/
        ├── hypercore-queries.md        ├── deal-sheets.md
        ├── xl-weekly-update.md         ├── credit-memos-loan-docs.md
        ├── datarooms.md                ├── lender-memos-presos.md
        ├── diligence-doc-hunt.md       ├── counsel-and-legal.md
        ├── loan-lifecycle-docs.md      ├── excel-editing.md
        ├── prospectus.md               ├── marketing-brand.md   (LinkedIn, covers, logos)
        ├── fonts-and-type.md           ├── website.md
        ├── maps-and-locations.md       ├── valuation-arv.md
        ├── underwriting-ic.md          ├── meetings-fireflies.md
        ├── webapps.md                  └── misc.md  (tax forms, intake schemas, PPTX, call-prep)
```

(20 playbook files consolidating the 26 mined playbooks — some merge naturally, e.g. deal sheet + payoff-letter template-match both live on the Ville-7877/PyMuPDF extraction method.)

## 5. SKILL.md contents (the always-loaded core)

### 5.1 Trigger
Any OKOA Capital deal/portfolio/marketing/legal/webapp task: deal names, "payoff", "dataroom", "deal sheet", "prospectus", "XL update", "LinkedIn post", "find the <doc>", "sort the loan folder", counsel emails, etc. Also fires when dictation says "aqua".

### 5.2 Folder quick-map (the 10-second orientation)

| Where | What |
|---|---|
| `/Users/zee/Library/CloudStorage/Dropbox-OkoaCapital` | Company Dropbox — source of truth for deals |
| `…/Okoa Loans - 1. In Process` | Pipeline deals (top level) |
| `…/Okoa Loans - 2. Active/1. In HyperCore` | ~30 active loans — **one level down**; exception: `Warburton_Ville 9` sits at the Active root |
| `…/Okoa Loans - 3. Paid Off/1. In HyperCore` | ~90 paid-off loans |
| `…/Okoa Loans - 4. Archived` | ~60 dead deals (top level) |
| `…/Forms and Templates` | Company doc templates |
| `…/Okoa Marketing` / `…/Okoa Letters` | Brand assets / letterhead + Official Logo PNG |
| `…/Investor Relations/Investor Updates/XL/XL Weekly Update` | XL Ant weekly series (read-only source — output goes to draft folder) |
| `…/External Data Rooms -- EXTERNALLY SHARED` | **Externally visible — never write WIP here** |
| `/Users/zee/Documents/OKOA` | Zee's working dir (~200 flat items — target known subfolders, don't glob); Desktop is TCC-blocked |
| `/Users/zee/Documents/OKOA/.venv-design` | Pinned design venv — all HTML/PDF/PPTX generation |
| `/Users/zee/Documents/OKOA/New deals` (+ `~/Documents/New deals`) | Deal sheets for deals with no Dropbox folder |
| `Vibe Coding/OKOA Website/{dev,stable}`, `okoa-wiki`, `okoa-loan-intake-system` | Code repos |
| `~/okoa-labs/okoa_ops/knowledge-graph/` | Collateral/NOI CSVs (Hypercore is liability-side only) |

### 5.3 Task router (trigger phrase → playbook → underlying skill)

| You say… | Playbook | Delegates to |
|---|---|---|
| "what's the payoff on…", "per diem", "how much does XL have on…" | hypercore-queries | `acos-hypercore-ask` (Doppler `hypercore-ask/dev_personal`) |
| "roll the XL update", "weekly investor report" | xl-weekly-update | `acos-xl-update` + fireflies + hypercore |
| "build a dataroom", "include/exclude" | datarooms | `acos-dataroom-v2` |
| "find the <doc>", "is the executed X in the folder", "prove it's absent" | diligence-doc-hunt | `acos-data-extractor` / main-thread OCR sweep |
| "deal sheet", "loan submission" | deal-sheets | Ville-7877 house format + `html-to-pdf.js --no-footer` |
| "credit memo", "term sheet" | credit-memos-loan-docs | `acos-loan-doc-generator` |
| "rebuild the memo", "design audit the deck" | lender-memos-presos | brad-build + `acos-doc-design-qa` |
| "email to counsel", "evidence bundle" | counsel-and-legal | curation rules + `acos-legal-analysis` |
| "NOD", "extension letter", "payoff letter", "lease renewal" | loan-lifecycle-docs | python-docx / PyMuPDF template-match |
| "prospectus", "update the mgmt fee" | prospectus | Python exact-match edits + waterfall model |
| "LinkedIn post" | marketing-brand | `acos-linkedin-posts` + recency gate + privacy blocklist |
| "what happened on <deal> lately", "meeting notes" | meetings-fireflies | `acos-fireflies-ask` (765+ cached transcripts) |
| "sort the loan folder" | diligence-doc-hunt | `acos-loan-doc-sorter` / `acos-sort-fixer` |
| "underwrite this deal", "run the IC" | underwriting-ic | underwriting pipeline / `acos-investment-committee` |
| "rent roll", "sales report", "pro forma" | excel-editing | openpyxl + extLst surgery rules |
| "loan map", "where are our loans" | maps-and-locations | verified CSVs + map build scripts |
| "ARV", "comps", "what's it worth" | valuation-arv | swarm-research + named-case rule |
| "custom font", "Xyntax" | fonts-and-type | `acos-type-forge` |
| "OKOA website", "loan maps page" | website | Astro/Node 22 rules |
| "fix the wiki", "loan intake", "deploy" | webapps | repo-specific stacks + secure-Convex patterns |

### 5.4 Red lines (always in context)

1. **Boss cold-look rule.** No intermediate review exists; every deliverable must survive first cold look. "Mostly right" = dismissed.
2. **Folder/file names are NOT facts.** 3 independent source-document confirmations for any brand/party/asset claim; grep triangulation.
3. **Copies only.** Never move/rename/delete Dropbox originals; never write WIP into `External Data Rooms -- EXTERNALLY SHARED`; final datarooms nest INSIDE the loan folder.
4. **Public-content privacy blocklist.** Never reveal: active book scale (~30 loans), AUM, deal counts, loss rate, target returns, named deals/borrowers/investors, OKOA loan pricing. Only public stat: "deployed over $500M in 3 years." "OKOA = Hawaiian for creative and flexible" is UNVERIFIED — don't assert.
5. **Subscription, not API.** Never ANTHROPIC_API_KEY; all model work via main-thread Read or Task(). Never Z.ai/GLM endpoints for confidential OKOA/borrower data.
6. **Verified figures only.** Deliver Hypercore's own value with an as-of date; payoff in default notices always "not less than $X"; LOI-dependent fields stay TBD, never fabricated.
7. **Clickable links.** Full percent-encoded `file://` URLs, short labels; open browser deliverables with `open -a "Google Chrome"`.
8. **Confirmation gate.** Restate + confirm before interpretive tasks; when Zee names a skill, run the whole skill.

### 5.5 Deal-name resolver (aliases table, always loaded)
The 8–10 highest-risk aliases inline (Waldorf/Tapestry, Waldorff spelling, Lux I/II/2 variants, 409 Hodson, LK OKOA, "a cent", Wright vs Wright Thurston, aqua=OKOA); full table in deal-index.md.

## 6. Reference file contents (what goes in each)

### 6.1 `references/deal-index.md` — ~32 deal fact-sheets
From `mined-synthesis.json → deal_index` (30 entries) **plus** delta additions: Tooele (Qelo_T222 — final PSA disclaims water rights), Grantsville_Commercial 246, Waxahachie (OKOA Waxahachie LLC, Fairfield Inn, ~$327,604 HOT judgment resolved via escrow), Gonzalez/Albert Ave (payoff-template deal, loan 173), Casa Grande I ($5.5M) & II ($700K), Ville 9 lien stack (junior ~5th, OKOA foreclosing). Each sheet: canonical paths → Hypercore IDs → verified figures with as-of dates → aka_traps. Ascent first (largest trap surface).

### 6.2 `references/folder-map.md`
The 27 mined entries + delta paths (XL Weekly Update source dir, `~/.fireflies-cache/`, `Rubin_Counsel_Bundle_20260423`, SpringVille/Lakeside). Flags: live-verified vs handoff-only (`Okoa Taxes` — location never captured verbatim, ask Zee). Junk-artifact list (conflicted copies, `maxdesk.ini2`). TCC workarounds (Finder-copy staging, Documents-not-Desktop).

### 6.3 `references/playbooks/*.md` — 20 files
Each: trigger phrases → inputs → numbered steps → outputs → gotchas, from the 26 mined playbooks + delta enrichments (XL field rules: Utah Shoe via `--loan-id 88` direct, Riverdale is a formula cell — set date only, Lux II = manifest balance + 7×per-diem; Rubin counsel-bundle curation: cut anything you wouldn't cite in a brief; Lakeside PPTX: install LibreOffice before building, exact Unsplash URLs, 1:1 page-to-slide; Wright Thurston note: sections 16–27 hand-typed, locate by content search).

### 6.4 `references/formatting-rules.md`
All 27 mined rules verbatim (deal-sheet tokens, prospectus palette/typography, render command lines with `NODE_PATH`/`--no-footer`, Puppeteer `@page margin:0`, screenshot-QA DPI budget, memo banned-terms, DOCX/PPTX rules, waterfall math, venv invocations) + delta: okoa-design quality gate (font-weight ceiling 650, spacing tokens {1,2,3,5,8,13,21}mm, ≥7 columns → landscape exhibit).

### 6.5 `references/gotchas.md`
The 25 mined learnings + delta traps (Fireflies mishears "Ascent" as "a cent"; speaker ID unreliable on phone joins; pypdf five-box page cropping; PyMuPDF soft-mask loss on logo extraction; verify agent self-reports against on-disk JSON; stale memory vs live file — live wins).

### 6.6 `references/open-questions.md`
17 mined questions (website ports conflict, canonical sage hex #465D53 vs #455D52, mgmt fee currency, which loan-count figure where, Ascent trustee-sale outcome post-2026-07-22, Okoa Taxes path, Albert Ave principal figure, New deals canonical dir, webapp scope, Google Drive Shared drives, …). Rule: when a task touches one, the skill ASKS instead of assuming.

## 7. Runtime behavior (what a session does)

1. **Resolve** the deal name against the alias table.
2. **Route** the ask via the router table; load only that playbook + that deal's fact-sheet.
3. **Verify** the 1–3 load-bearing paths live (`ls`) before acting — facts carry dates, disks change.
4. **Execute**, delegating to the named underlying skill (whole skill, never a stripped version).
5. **Capture** any new fact/gotcha discovered (see §8).

## 8. Continuous-learning loop (keeps it growing, not just current)

The skill treats every new task as future training data. Four layers, ordered from automatic to manual:

**Layer 1 — Raw capture is already automatic (zero new discipline needed).**
Every session already produces handoffs (autopilot/eternity pipeline) and auto-memory files. These are exactly the sources this outline was mined from. So the raw feed of new learnings never stops — the gap is only in *distilling* it into the skill. Layers 2–4 close that gap.

**Layer 2 — In-session capture, made mechanical AND user-approved.**
Every playbook file ends with a mandatory final step: `LEARN-CHECK — did this task surface (a) a new/changed fact, (b) a new trap, (c) a wrong line in a reference file?` If yes, the session does NOT write silently. It presents each candidate learning to Zee as a **learning brief** via AskUserQuestion — one learning per question, fully self-contained (per the standing approval-question rule):

> *Proposed learning:* <the exact dated line to be added/changed>
> *Goes into:* <reference file + section>
> *How it changes the skill:* <e.g. "future deal-sheet runs will use the new reserve figure" / "this replaces the old path, struck with a dated note">
> *Source:* <what in this session produced it>

Options: **Add it** / **Add with my edit** / **Skip this time** / **Never suggest this again**. Only approved items are written. "Never again" entries land in `references/.rejected-learnings.md` so the same proposal is not re-raised (mirrors the ADR-002 persisted-rejections pattern). One carve-out: reading/verifying live state (e.g. `ls` before acting) needs no approval — the gate is on **writes to the skill's files**, not on looking.

**Layer 3 — `/acos-okoa-works-learn` (the incremental distiller).**
A companion command that re-runs the mining pipeline **incrementally**:
1. Reads `references/.last-mined` (a watermark timestamp stored in the skill).
2. Collects only handoffs/memory/decision files newer than the watermark (cheap — dozens of files, not 289).
3. Runs the saved mining workflow on just those files (same extract schema, same critic).
4. Diffs candidate facts against the reference files and builds a **change brief**: every proposed add/change, its target file, and its effect on future behavior — contradictions shown with both versions side by side.
5. Walks Zee through the brief with the same per-item approve/edit/skip/never-again flow as Layer 2 (batched, one item per question). Only approved items merge; nothing is ever written without sign-off.
6. Advances the watermark.
Run it weekly, after any heavy deal stretch, or on a schedule (a cron routine can invoke it). The full-corpus workflow script stays available for a from-scratch re-mine if the references ever feel drifted.

**Layer 4 — Staleness discipline (learning includes forgetting).**
Figures carry as-of dates; anything older than ~2 weeks is re-verified via Hypercore before delivery. Deal statuses (e.g. Ascent trustee sale, scheduled 2026-07-22) are unknown-until-checked. Answered open-questions move from `open-questions.md` into the proper reference file with a date; superseded facts are struck with a dated note, not deleted (audit trail).

Together: Layer 1 guarantees nothing is lost, Layer 2 catches the obvious in the moment, Layer 3 sweeps up everything Layer 2 missed, Layer 4 keeps old knowledge from masquerading as current. **And across all layers: the skill proposes, Zee approves — no learning enters the skill without an explicit yes.** (Handoffs/memory in Layer 1 keep flowing automatically as raw material; the approval gate sits on what gets promoted into the skill's reference files.)

## 9. Build plan (proposed, ~3 sessions)

| Phase | What | Output |
|---|---|---|
| 1 | Scaffold + SKILL.md + folder-map.md + deal-index.md (highest value density) | invocable skill, core loaded |
| 2 | 20 playbooks (each ending in the LEARN-CHECK step) + formatting-rules.md + gotchas.md + open-questions.md (batch-generated from the two JSON companions, then hand-tightened) + `/acos-okoa-works-learn` incremental distiller with `.last-mined` watermark | full reference set + learning loop |
| 3 | QA: live-verify every path; test every command line against current scripts; adversarial review agent hunts stale/contradictory facts; 3 dry runs (a payoff query, a deal sheet, a doc hunt) | shippable skill |

**Decision points for Zee before Phase 1:**
1. **Scope:** include the webapps playbook (okoa-wiki / loan-intake / FlexCade engineering) as first-class, or defer those to per-repo CLAUDE.md files? (Mined data supports either.)
2. **Home:** project skill in `ACOS 3.0/.claude/skills/` (current plan) vs global `~/.claude/skills/` (works from any directory — likely better, since OKOA work happens outside this repo).
3. **Open questions:** the 17 in §6.6 — answering even the top 5 (ports, sage hex, mgmt fee, New deals dir, Okoa Taxes path) before the build removes most known ambiguity.

---
*Sources: mined-synthesis.json + mined-delta-batches-4-6-9-11.json (this folder). Mining run wf_f8fbbfae-2d7, 2026-07-16/17; 25 workflow agents + 4 make-up readers; adversarial critic + repair pass; coverage verified file-by-file.*
