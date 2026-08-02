# Overview

**Feature id:** `001-website-builder`
**Product:** Website Builder (ACOS skill `acos-website-builder`)
**Project:** ACOS 3.0 / Website Builder
**Source of record:** `Website Builder/prd/website-builder-prd.md` (641,327 bytes / 4,224 lines / 20 sections — never read whole; section line map carried in `_deterministic_prompt.md`), `Website Builder/DECISIONS.md` (16 items; item 1 DECIDED 2026-07-26 option B), `Website Builder/memory/decisions/` (D1–D4), `Website Builder/prd/OPEN-ITEMS.md` (51 deferred items, section B), `Website Builder/research/` (12 lenses).
**Evidence marking convention (inherited, normative):** `[V]` verified against a named source, `[I]` inference, `[U]` unsourced. Markers are never silently promoted. **Every schedule, effort and volume estimate in this document is `[I]`.**

### What this is

Website Builder turns a conversation into a distinctive, hand-adjustable, publishable website in eight steps, executed by a thin router skill plus TypeScript scripts on Bun, one local server, and a browser editor:

0. Warm start / continuity check, including asset-library detection.
1. A three-tier, hard-gated interview producing `answers.json` and a 200–300 word `concept.md`.
2. Generation of a two-stage design-system prompt (Stage A direction capsules; Stage B full DTCG token expansion per shortlisted direction) with a frozen token-name manifest, a closed font vocabulary, a worked micro-example, a CSP constraint, an envelope manifest and a per-run random terminator.
3. Hand-carry of the result from claude.ai via a bounded-paste protocol ingested with `pbpaste`, with **Local Regeneration Mode** (identical prompt, run by a Claude Code path, zero pastes) as a first-class escape hatch so the web hop is a UX preference and not a technical dependency.
4. Bracketed-tournament direction selection (never more than 3 full-size renders side by side; every round logged to `direction-tour-log.json` with the user's stated reason), per-slot component selection, then a live editable design surface.
5. Deterministic variant generation, scoped and system-level regeneration.
6. Custom components via a whitelisted registry, an inline-authored path, and (v2) an opaque custom-code-block container.
7. **LOCK** — re-render with `editor: false`, scrub, purity gates, two-build equality, snapshot, git tag.
8. Publish plus a licence-and-evidence bundle.

### Fixed decisions (not open to re-litigation)

| Id | Decision | Consequence carried into this spec |
|---|---|---|
| **D1** | ~10 coherent whole design directions per project; 20 artworks per direction; 10 variants per component on demand (12 for hero, CTA band, card, badge, feature grid, pricing); **derived values are COMPUTED from anchors, never independently picked** | Every derived token carries `com.acos.pick.pickable: false` and renders no editor control (§7.0.2, A24, A15) |
| **D2** | Constraint-based dragging is the layout model, with a per-component free-position escape hatch. **Gridlines are what components snap to.** Not free x/y coordinate layout | The four-level layout contract of §11.1; grid-integer writes; anchored-offset free position |
| **D3** | LOCK exports a clean static site with provably zero editor runtime, **reversibly**. Re-render from documents with `editor:false`; never copy-and-strip | Purity gates; two-build equality; UNLOCK = restart the design server |
| **D4** | Motion is a design-system item living inside draggable art-style containers, not a bolt-on | One container contract for art and motion (§9.1); `props.motion` is a token on an `ArtContainer` node |
| **DECISION-1 (2026-07-26, option B)** | **v1 ships gridlines AND full constraint dragging.** §18's editor-lite v1 scope is REJECTED | The canvas epic is v1 scope; R47 is retired; §18's timeline, §18's v1 scope-in list and §13's gate budgets are stale and must be re-baselined `[I]` |

**Standing product law:** the human is the sole aesthetic judge. There is no AI critic scoring screenshots and no autonomous judge/Wigum aesthetic loop (NG1). Machines enforce only machine-checkable correctness — contrast, reflow, token purity, licence completeness, export purity, keyboard/pointer-alternative parity — and those the human may **not** wave through.

### Non-goals (v1)

- **NG1** No AI aesthetic judging of any kind; the VLM judge loop and autonomous Wigum aesthetic iteration are not ported.
- **NG2** No multi-user real-time collaboration (v1–v3). The comment schema may be collaboration-ready; no second writer ships.
- **NG3** No CMS and no backend. Static output only; forms use a third-party endpoint or a `mailto` fallback. Success measurement uses local session files only — no telemetry, nothing leaves the machine.
- **NG4** No application-shell UI in v1 (dashboards, auth, settings, data tables at scale). ~62 app-shell/commerce/exotic-chart inventory items are gated behind the site-type answer and deferred to v3. **`[I]` — the 62 figure is carried from the §7/§8 tally and is explicitly not independently recounted; see NA-02.**
- **NG5** Zero new files in `.claude/agents/` — agent definitions are human-approval-restricted ACOS infrastructure.
- **NG6** No new Python. All new code is TypeScript run by Bun. The single contemplated exception is the ~20-line process-launch shim at rung F4 of the launcher ladder, which requires explicit user sign-off.

---

## Diagnostics

Per protocol §0.3, the problem is characterised **before** solution requirements are locked. Nothing below is a solution statement; every hypothesis carries a validating slice.

### Symptoms — what is going wrong today

| # | Symptom | Observed where |
|---|---|---|
| SY1 | A technically-capable non-designer cannot produce a distinctive site. Template pickers yield sameness; free-canvas tools require design vocabulary the user does not have; hiring a designer per venture is not viable. Ventures ship undesigned sites, or no site | P1 |
| SY2 | Design coherence collapses when ~80 design-system items are picked independently — nothing forces scales, states, tints and motion timing to be computed from anchors | P2 |
| SY3 | Responsive work is manual and its overrides are invisible. A layout approved at 1440 breaks at 320. An auto-height preview iframe makes `100vh`/`svh`/`dvh` resolve to the iframe height, so a hero is approved at a height no device has | P3; §11.7 trap `[V — puckeditor.com viewports, fetched]` |
| SY4 | The exact operation the user asked for — gridlines plus drag — is ambiguous under constraint layout: "move the hero headline 12px up" is one drag on a free canvas and a four-way CSS puzzle under D2 | P4; §11.1 |
| SY5 | WYSIWYG editors leak their own runtime into published output, with no proof the shipped site is clean and no way to unlock and keep editing without divergence | P5; §12.1 anti-patterns |
| SY6 | The claude.ai hand-carry costs 45–90 minutes per cycle `[I — U8, sized against first-party artifact counts]` and Step 5 turns it into a loop | P6; §20.3 U8 |
| SY7 | Typography — the largest identity carrier — cannot be judged where directions are chosen, because the artifact CSP admits the Google Fonts stylesheet but blocks the WOFF2 under `font-src`, so a system fallback renders | P7; O1 (unverified, assumed blocking) |
| SY8 | Silent truncation of a pasted design system produces syntactically valid, semantically wrong CSS/HTML/SVG with no error anywhere | P8 |
| SY9 | Warm start homogenises the portfolio: site 2 becomes a recolour of site 1. Invisible until there are three sites | P9 |
| SY10 | Legal exposure concentrates in fonts and assets; without a recorded licence class per shipped item the user cannot answer what they may ship | P10 |
| SY11 | The editor's premise — a long-running local server — is incompatible with the harness by default. Detached children are reaped; `run_in_background` servers are SIGTERM'd (exit 143) at the turn boundary; the failure looks intermittent because it depends on turn timing | P11; R5 `[V — first-party, four documented attempts]` |
| SY12 | Two writers, no lock. The product encourages alternating between talking to Claude and dragging in the browser, so silent work loss is near-certain rather than a corner case | P12; §12.7 |
| SY13 | Raster artwork is structurally undeliverable from the claude.ai leg; a project with no asset library gets 20 flat geometric SVGs — the exact AI-slop register | P13; R1 `[V — confirmed Anthropic, April 2026]` |
| SY14 | Month six: the precedent already rotted — an unversioned tree, ~30 opaque variant directories, no manifest, builder source in a job tmp | P14; §15.5 `[V — git status failure, ls, DEPLOY-STEPS.md]` |
| SY15 | The user cannot articulate why a direction was chosen, so design decisions are un-re-derivable | P15 |
| SY16 | The interview is where the user's time is spent worst | P16; §5 |
| SY17 | Localhost is not a trust boundary (CVE-2025-24010 class), and Step 3 is an unauthenticated code-import channel whose payload is evaluated by the dev server and bundled into the published site | P17 |
| SY18 | Motion cannot be judged while editing: the editor runtime fights the site runtime (Lenis lerps `scrollTop`; GSAP transforms poison `getBoundingClientRect`) | P18; R14 — **no known mitigation** |
| SY19 | Undo fractures across AI-driven bulk mutations; a naive per-mutation stack leaves a broken hybrid after one Cmd+Z | P19; §10.4 |
| SY20 | Deploy is a second manual boundary; if publish is not automated every future content edit ends in a dashboard drag-and-drop | P20; §15.4 `[V — DEPLOY-STEPS.md]` |

### Affected roles

- **The ACOS owner (primary).** Bears SY1–SY20 directly. Sole aesthetic judge, sole LOCK authority, and the only person who can sign off the F4/F5 launcher deviations.
- **A future collaborator (secondary, v2).** Bears SY15 (cannot reconstruct why) and the read-only preview gap.
- **The same user six months later (secondary, v2).** Bears SY14 and SY20 hardest; Content mode is the answer and it is **not** in the v1 bar.
- **Visitors (tertiary).** Never interviewed. They are the justification for the non-negotiable machine gates: contrast, reflow, keyboard/pointer-alternative dragging, licence attribution, photosensitivity, responsive behaviour.

### Current vs desired behaviour

| Dimension | Current | Desired |
|---|---|---|
| Path from intent to site | No repeatable path; ad-hoc generation, hand-assembled trees | One session, eight steps, resumable from disk alone |
| Coherence | ~80 independent picks | 24 varying identity slots + 2 invariant records; everything else derived or direction-bound `[V — §7.0/§7.1]` |
| Responsive | Manual, per-breakpoint, invisible | Author at 1280, auto-derive 768/390, override only where preflight complains; no-override blocks compile to `grid-column: 1 / -1` |
| Direct manipulation | Absent or coordinate-based and unsafe | Snap to a **real** CSS grid; drags write integers; every drag has a single-pointer equivalent |
| Export | Copy-and-strip with hand-fixed links | Re-render with `editor:false`; purity gates assert the claim |
| Provenance | None | `concept.md` + `direction-tour-log.json` + `provenance.json` + evidence bundle |
| Server lifecycle | Dies at the turn boundary, intermittently by appearance | Gate 16-A-proven launcher rung; fixed port; re-attach, never relaunch |
| Concurrency | Two writers, no lock | One writer (`wb-server`); hash-journal reconciliation; 409 on stale ETag |

### Hypotheses (each carries a validating slice)

| # | Hypothesis | Validating slice | Status |
|---|---|---|---|
| H1 | A pure-TypeScript detached spawn can keep a local server alive across this harness's turn boundary | **Gate 16-A probe** (`scripts/probes/probe-turn-boundary.ts`), F1→F5 ladder | **Unproven. Blocking.** `[I]` |
| H2 | A single-origin Bun server proxying the preview is no worse than the two-origin iframe + postMessage shape Onlook/Stackbit/Tina converged on | O4 topology spike: same two-page vertical slice on both topologies, one working session each, scored on channel LOC, preview-only screenshot achievability, HMR round-trip latency, and behaviour after killing/restarting the preview process; recorded as an ADR | Open (§17-O4) |
| H3 | A claude.ai artifact silently falls back to a system font because `font-src` blocks the WOFF2 | O1 60-second devtools test, **before** the Step-2 prompt spec is written | Assumed true; unverified |
| H4 | Plain generated HTML from a TypeScript renderer is a better substrate than Astro for live-editability and clean LOCK | O8 substrate spike | Open (§17-O8) |
| H5 | Two installs of the same lockfile produce a byte-identical production build | Byte-reproducibility spike | **No consulted source establishes this** (§12.5 O33). Fallback = normalised comparison, which weakens D3's proof and needs sign-off |
| H6 | A skill whose `allowed-tools` omits `Task` can still call `Task(general-purpose)` mid-session | O31 probe (~10 min) | Unverified; v1 is designed so nothing depends on it |
| H7 | The user's chosen direction survives contact with real typography and real artwork | Demo 1 (one direction rendered as a static page) | Untested |
| H8 | Constraint dragging with three verbs plus a pre-commit chip does not feel like the tool fighting the user | Demo 3 | Untested; R8 says the market's constraint editor died |

### Unknowns carried into the plan (not resolved here)

Bundler-level byte reproducibility (O33/§12.5); the real claude.ai per-message and per-conversation output ceilings (O2/U2 — **the figures found in 2026 SEO "guide" content were unverifiable and at least one model name appears fabricated; do not design against them**); whether sibling-anchored free positioning can be compiled at all (subgrid promotion, unprototyped); whether motion feel can ever be judged in-editor (R14, no known mitigation); the true v1 component-set volume (NA-02).

**Diagnostic slice requirement (§0.3 satisfied):** the Phase-0 spike suite — Gate 16-A, O4 topology, O1 CSP font, O8 substrate, byte-reproducibility, O31 `Task` availability — **is** the diagnostic slice, it runs first, and nothing server-dependent is treated as committed until Gate 16-A passes.

---

## Users & Use Cases

### Personas

| # | Persona | Description | Authority |
|---|---|---|---|
| U-1 **PRIMARY** | The ACOS owner | A single technically-capable non-designer on macOS with a Claude subscription and web access, building distinctive sites for their own ventures (FruitSync, OKOA, future ventures). Strong taste, limited design vocabulary | **Sole aesthetic judge. Sole LOCK authority.** Sole signer of the F4/F5 launcher deviation, the normalised-comparison fallback, and the remaining §18 sign-off rows |
| U-2 secondary (v2) | A future collaborator | Reviews a site before LOCK via a read-only preview link | None in v1 |
| U-3 secondary (v2) | The same user, six months later | Makes a copy-only change via Content mode with no dev server | None in v1 (S7 is **not** in the v1 bar) |
| U-4 tertiary | Visitors | OKOA investors, FruitSync players, a future venture's customers. Never interviewed, never given a persona | They are why the machine gates are non-negotiable |

### Use cases

| # | Use case | Primary actor | Success condition |
|---|---|---|---|
| UC1 | Cold start: "I need a site for X" → locked, published site in one working session | U-1 | Site is locked, published, and the evidence bundle is complete |
| UC2 | Warm start from a prior system: reuse token schema, slot contracts, motion primitives, font catalog, deny-list and editor configuration **without** inheriting hue anchors, type pairings, radius/density, motion character, artwork, grid personality or the signature moment | U-1 | Prior identity is injected as negative constraints; the new site is not a recolour |
| UC3 | Direction selection: choose among ~10 generated directions via a bracketed tournament, never more than 3 full-size renders side by side, with the pick and stated reason logged every round | U-1 | `direction-tour-log.json` records every heat's `directionsShown`, `orderShown`, `pick` and `reason`, written as rounds progress |
| UC4 | Hand-carry: paste a two-stage design-system generation result back from claude.ai and have it ingested with envelope validation, or run Local Regeneration Mode and skip the pastes entirely | U-1 | Bounded pastes; a truncated chunk is refused, not partially applied |
| UC5 | Direct manipulation: drag a block onto a gridline, resize its span, adjust padding to a named spacing step, and nudge it with the keyboard | U-1 | Grid integers are written; the pre-commit chip names affected sizes; a single-pointer alternative exists for every drag |
| UC6 | Variant exploration: "10 more variants of this button", "more like this" | U-1 | Deterministic, no model call, append-only indices, lazy per family |
| UC7 | Scoped regeneration: attach a note to a section and regenerate that section only, inline, as one undo step | U-1 | Single undo step; regeneration log records the note |
| UC8 | LOCK and publish: re-render clean, pass the gates, snapshot, tag, deploy, and produce the licence-and-evidence bundle | U-1 | Zero editor strings in the published tree; the bundle states "passed N automated gates" and never claims WCAG conformance |
| UC9 | Resume after a context reset or an eternity `/clear` | U-1 | Phase is recomputed from disk; the resume instruction says **re-attach** to the fixed port via `state.json`, never relaunch |
| UC10 | Recover from a mistake: undo, restore from the recovery bin, or roll back to a prior lock | U-1 | Recovery bin is independent of the undo stack; `git checkout wb-lock/<n> -- pages/ site.json system.lock.json content.json` restores documents **and** the system lock together |

---

## Requirements

Requirement ids are stable. Each carries a source: a PRD section, a technical requirement (TR), a settled decision, or an explicit `Assumption`. MoSCoW is against **v1 as re-baselined by DECISION-1 option B**.

### 4.1 Functional Requirements (MoSCoW)

#### Phase 0 — spikes and blocking gates (epic E0)

| Id | Requirement | MoSCoW | Source |
|---|---|---|---|
| FR-001 | Run **Gate 16-A** first: launch via the candidate detached-spawn mechanism, `curl --retry 20 --retry-connrefused` for 200 in the same turn, end the turn, and in a **separate later tool call** curl again and confirm the pid in `state.json` is still in `ps`; repeat across at least two further turn boundaries and once across an eternity `/clear`. Pass = 200 at every post-boundary check with the original pid alive | MUST | R5, A80, runtime guardrail 1 |
| FR-002 | Walk the launcher ladder in order and stop at the first passing rung: F1 TS detached spawn + `unref` → F2 TS double-fork (**note: `setsid` does not exist on this Mac**) → F3 ~15-line POSIX `sh` launcher (preferred fallback; keeps 100% of the server in TypeScript) → F4 ~20-line Python double-fork launcher (**requires user sign-off**, standing-language-rule deviation) → F5 user starts the server in their own terminal (**requires user sign-off**, UX regression) | MUST | §16.6.3, O32(§16.6.3) |
| FR-003 | Run the **O4 topology spike** (single-origin proxy vs two-origin iframe + postMessage) as the same two-page vertical slice on both topologies, scored on channel LOC, preview-only screenshot achievability, HMR round-trip latency and post-restart behaviour, and record an ADR that updates §16.6 and §17-O4 together | MUST | §17-O4, §20.2 row 11 |
| FR-004 | Run the **O1 CSP font test** (60 seconds, devtools) **before** the Step-2 prompt spec is written | MUST | R2, §20.4 item 1 |
| FR-005 | Run the **O8 substrate spike** (Astro vs plain generated HTML from a TypeScript renderer) and build only against invariant I6 until it lands | MUST | §17-O8 |
| FR-006 | Run the **byte-reproducibility spike** before treating two-build byte-equality as achievable; if it fails, adopt the normalised comparison (identical file list, identical SHA-256 for every file except a named, enumerated, individually justified exception set recorded in `gate-report.json`) and **obtain explicit sign-off that D3's proof is weakened** | MUST | §12.5 O33, DECISIONS item 5 |
| FR-007 | Run the **O31 `Task`-availability probe** (~10 minutes). Not a v1 blocker | SHOULD | §16.5.1 O31 |
| FR-008 | Also verify, per §20.4: copy-paste fidelity from claude.ai's rendered chat view across all three paste paths (rendered view, per-block copy button, conversation export); the empirical claude.ai output ceiling; HMR round-trip latency for a move op; and re-verify every adopted dependency's licence **against the actual LICENSE file at pin time** (GrapesJS shows NOASSERTION on the GitHub API vs BSD-3-Clause on npm — U14) | MUST | §20.4, U14 |

#### Skill scaffold and TypeScript spine (E1)

| Id | Requirement | MoSCoW | Source |
|---|---|---|---|
| FR-010 | `SKILL.md` is a thin router with frontmatter exactly `disable-model-invocation: true`, `user-invocable: true`, `argument-hint: "[--project <path>] [--resume] [--system <name>] [--port 8820] [--content] [--local-gen]"`, `allowed-tools: Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion`. **`Task` is NOT listed** | MUST | A87, NG5 |
| FR-011 | Phase 0 of the skill is a mandatory **Confirmation Gate**: restate the understood brief and wait for an explicit confirmation before any file write or server launch | MUST | A90; both CLAUDE.md files |
| FR-012 | Port `acos-image-builder/app/server.py` (105 lines) to `server.ts` **first**, before any other code, to establish the TypeScript spine | MUST | R12 mitigation |
| FR-013 | `install.sh` creates a **symlink** into `~/.claude/skills/`, never a copy | MUST | A88, R37 |
| FR-014 | Per-project config `.acos/config/website-builder.yaml` (version, default port, breakpoints, direction count, variants per component, artwork count, gate thresholds, licence policy tier, publish target), snapshotted to `audit/config-snapshot.yaml` at init | MUST | Constraint "PROJECT CONFIG" |
| FR-015 | `bun selftest.ts` harness, held to the cleanroom bar (67/67 there; **100% of assertions** here per A85) | MUST | A85 |
| FR-016 | `git init` at Step 0; session directory plus an ACTIVE marker | MUST | §15.5, A83 |

#### Step 0 — warm start (E2)

| Id | Requirement | MoSCoW | Source |
|---|---|---|---|
| FR-020 | Glob `.acos/design-library/*/design-system-spec.yaml`, `.acos/website-builder/systems/*/system.json` and the target project's `.acos/`, and offer any hit **within the first three exchanges** | MUST | §15.1, A1 |
| FR-021 | Detect an asset library at a path the user names and record `assetLibraryPath` in `session.json` — **the binary that decides whether the artwork category is real or theatre** | MUST | A2, C3 |
| FR-022 | Apply the warm-start split: always carry forward token-name schema, component slot contracts, motion-primitive library, font catalog, anti-slop deny-list, editor configuration and user-level interview answers; **never** carry forward hue anchors, type pairings, radius/density, motion character, artwork, grid personality or the signature moment | MUST | §15.3 |
| FR-023 | Inject prior identities into Step 2 as **negative constraints** ("do not produce a direction within 30° of these hues or reusing these type pairings") unless the user answers yes to the sibling-site question C4 | MUST | §15.3, §6.0 mapping |
| FR-024 | Mine prior sources (existing site trees, token bundles, licence registers) to pre-fill interview answers | SHOULD | §15.2 |

#### Step 1 — interview (E3)

| Id | Requirement | MoSCoW | Source |
|---|---|---|---|
| FR-030 | Ship the question bank as `references/interview-bank.md`. **The bank is 90 questions `[V — §5 row-count self-audit]`, not the 78 asserted in §17-R21 and §18** — see Assumption NA-01 | MUST | §5 |
| FR-031 | Three tiers with disambiguated semantics: `[T1]` gates the Step-2 prompt and is satisfied by **either** a real answer **or** an explicit "I don't know / surprise me" that records a **stated concrete default value** (never a null) with `"source": "skill-default"`; `[T2]` is asked just-in-time and recorded `"not-applicable"` when its moment never arrives; `[T3]` is inferred with a stated default plus a visible "change this" affordance, bundled into one end-of-interview review screen in fast mode | MUST | §5 tier notation |
| FR-032 | Deliver in waves of 5–8 questions per screen with a visible shrinking progress count, alternating visual and verbal tasks; Wave 0 (continuity and global policy) is always first and carries `C1`–`C6`, `Z1`, `Z2` | MUST | §5 delivery rules, Wave 0 |
| FR-033 | Enforce the ID grammar `<wave-prefix><n>` with reserved prefixes (`C, P, B, A, TS, D, M, N, X, L, G, H, U, Z, V`); the ten Wave-2 taste questions are `TS1`–`TS10`, **never** `T1`–`T10` (which collide with the tier labels and break A4) | MUST | §5 ID grammar |
| FR-034 | Honour the real branch map: `C6` gates `B4` and conditionally `D8`; `L1` prunes `L2`–`L4`; `G1` (jointly with the new `G0` jurisdiction question) prunes `G2` but **not** `G3`; `D4` prunes **no** questions and is not a branch root; no-forms skips `D7` and `D11` | MUST | §5 branch roots |
| FR-035 | `Z1` sets branching aggressiveness and variant rounds (`one sitting` → Tier-1 only, Tier-3 bundled, 1 variant round; `a few short sessions` → Tier-1+Tier-2, Tier-3 individual, 2 rounds; `open-ended` → full bank, unbounded rounds within budget). `Z2` sets the D1 variant multiplier (10 per component, or 3 per round for "a small number of strong options") | MUST | §5 Wave 0 |
| FR-036 | Ask the primary-language question `C5` (needed for `<html lang>` on the single-language common case) and the site-type question `P6` mapped 1:1 to the schema.org types §13.6 requires — always shown for confirmation, never silently applied | MUST | §5 C5/P6, A70 |
| FR-037 | Ask a structural-RTL Tier-1 question and an audience-access-needs question whose answer may only **TIGHTEN** a §13 gate threshold, never loosen one | MUST | DECISIONS item 16 |
| FR-038 | Emit `00-interview/answers.json` (question-ID-keyed, tier-tagged, with `source ∈ {asked, pre-filled, inferred-default, skill-default}` and an override flag) and a 200–300 word `00-interview/concept.md` naming a point of view, ≥3 abstracted references, a restraint budget, and **at least one thing the site refuses to do** — the pipeline refuses to advance to Step 2 without that last item | MUST | A5, data model |
| FR-039 | Instrument actual elapsed interview time from day one; every published duration figure is a projection, not a measurement | MUST | §5 `[I]` note |

#### Step 2 — prompt generation (E4)

| Id | Requirement | MoSCoW | Source |
|---|---|---|---|
| FR-040 | Build `font-catalog.json` as a skill-owned, cross-project resource at `.acos/website-builder/library/font-catalog.json`, entries `{familyId, classification, foundry, oflSourceUrl, fileHash, glyphCoverage, preSubsettedCuts:{latin, latinExtended}}` with base64 cuts computed **once, locally, ahead of time** — never by the web model. Snapshot a hash-pinned copy into `01-prompt/font-catalog.snapshot.json` at Step-2 start so a mid-run library refresh cannot change what a session is judging | MUST | §6.0 |
| FR-041 | Generate `token-manifest.json` **mechanically** from §7's item list — names only, no values — before any prompt is emitted, and re-paste it verbatim into every chunk | MUST | §6.0 demand 8 |
| FR-042 | Stage A prompt contains, greppable: the DTCG worked example `[A6-1]`, the OKLCH hue warning verbatim ("hue 0deg = magenta, not red; red is ~41deg") `[A6-2]`, the pinned font shortlist with base64 display cuts `[A6-3]`, the frozen token manifest and prior-identity negative constraints `[A6-4]`, the CSP constraint `[A6-5]`, the 390px preview requirement `[A6-6]`, and the self-audit instruction `[A6-7]` | MUST | A6, §6.0 template |
| FR-043 | Stage A requests direction capsules (26-slot vector + 40–80 word manifesto each) plus one gallery artifact previewing all directions as hero cards rendered at **both** a desktop frame and a 390px-wide portrait frame | MUST | §6.0 §3 |
| FR-044 | Over-generate capsules, machine pre-filter on the self-audit fields (hue-anchor collisions, anti-slop deny-list violations), then let the user skim-and-cut down to the ~10 D1 floor; any relaxation of that floor is recorded in `session.json` as a signed-off D1 deviation | MUST | TR9 |
| FR-045 | Stage B reuses prompt sections 0, 2, 4, 5 verbatim and replaces section 3 with the full DTCG token expansion plus identity-carrying component instances for one direction | MUST | §6.0 |
| FR-046 | Every emitted design directive cites the interview question ID that produced it | MUST | A4 |
| FR-047 | The skill computes chunking from **measured artifact sizes at runtime**, not from any published ceiling, and surfaces the claude.ai usage-tier cost up front | MUST | O2/U2, R46 |
| FR-048 | Emit an envelope manifest (declared file list, per-file line counts, sha256 prefixes, smallest-first ordering, per-run random terminator) with the prompt | MUST | R3 |

#### Step 3 — ingest (E5)

| Id | Requirement | MoSCoW | Source |
|---|---|---|---|
| FR-050 | Tolerant parser splitting on fenced `FILE:` blocks; a **complete** chunk ingests with zero manual file operations beyond one `pbpaste` | MUST | A7 |
| FR-051 | A **truncated** chunk fails with a message naming the missing files and **writes no partial system** | MUST | A8, R3 |
| FR-052 | A chunk containing a forbidden API (e.g. `fetch(`) in a component quarantines that item, ingests the rest, and reports it in `inbound/import-report.json` with reason and offending snippet | MUST | A9, §12.14 |
| FR-053 | Deterministically re-verify every claimed contrast pair; auto-nudge failures and log them in the substitution log | MUST | A10 |
| FR-054 | Substitute any font not on the pinned shortlist with the nearest OFL match in the same classification and log it | MUST | A11 |
| FR-055 | Check `templateVersion` against a supported range with a defined upgrade path | MUST | TR10 |
| FR-056 | **Local Regeneration Mode** produces a bundle that passes the identical validator with **zero pastes** | MUST | A12 |
| FR-057 | Run the anti-slop lint as a **hard gate upstream**, on the generated design-system JSON, before the human sees the menu of choices | MUST | §13.8 resolution |

#### Token compiler and design-system emission (E6)

| Id | Requirement | MoSCoW | Source |
|---|---|---|---|
| FR-060 | Emit DTCG token JSON **and** the design-system-forge `design-system-spec.yaml` from one importer | MUST | TR11 |
| FR-061 | Compile to CSS custom properties plus a Tailwind `@theme`; pin the compiler version and commit the lockfile | MUST | TR11 |
| FR-062 | Compile the full custom-property set to a **flat variable layer once per direction change**, never resolved per drag | MUST | R30 |
| FR-063 | **Logical CSS properties only** — `margin-inline-start`, `padding-block-end`, `inset-inline`, `border-inline-start`; never `left`/`right`/`top`/`bottom`/`margin-left`/`text-align: left`. Enforced by a coherence lint at ingest **and** at LOCK | MUST | Constraint; A-new |
| FR-064 | Every token carries `com.acos.llm`, `com.acos.pick` and `com.acos.direction` extension blocks; the editor renders **no control** for any token with `com.acos.pick.pickable: false`; a token whose `com.acos.direction.vectorHash` differs from the active direction is **rejected by the builder** | MUST | A14, A15, A16 |
| FR-065 | Spacing, type steps, radius scale, shadow scale and semantic colour roles are marked `derived` and have no editor control. **Font fallback metrics** (`size-adjust`, `ascent-override`, `descent-override`, `line-gap-override`, computed from the real selected font binary) are a derived family too | MUST | A24, §13.4 gate 21 |
| FR-066 | Any row whose Scope is `in-direction-repickable` ships a per-direction **validity list** in `token.capability-manifest`; options absent from the active direction's list are **hidden from the UI**, not merely warned about. A row that cannot supply a validity list is demoted to `direction-slot` | MUST | §7.0.2 coherence rule |
| FR-067 | `tokens.css` is machine-owned; `extract-override.ts` is the sanctioned hand-tune path | MUST | §17-O25 |
| FR-068 | Both light and dark schemes are independently solved and the contrast proof table covers both | MUST | A19 |

#### Document model and renderer (E7)

| Id | Requirement | MoSCoW | Source |
|---|---|---|---|
| FR-070 | **Two-tier truth.** Composition (`pages/<id>.doc.json` + `content.json`) is the only thing the editor mutates; implementation files are versioned on disk; the rendered site is produced by a pure function `render(doc, systemLock, library) → files` and is **never parsed back into JSON** | MUST | §12.1, R4 |
| FR-071 | `render` is **total**: every `component`/`variant`/`motion`/asset/token id in the doc resolves against the library, and §12.16's resolution policy applies when one does not — unknown component = hard fail with a named report; unknown variant = canonical-variant fallback carrying a per-node `variantMigrated` flag visible in the editor that **blocks LOCK until acknowledged**; orphaned slot content moves to `node.orphaned` and is **never deleted by a migration** | MUST | §12.1, §12.6 rows 10–11, gate 6 |
| FR-072 | Breakpoint key vocabulary is normative and shared by the switcher, the cascade, the free-position rules, the save format and the gates: `base` (no media query, 12 tracks, previewed at 1280 and full), `md` (`max-width: 991px`, 6 tracks, previewed at 768), `sm` (`max-width: 479px`, 4 tracks, previewed at 390). Emission order `base → md → sm`, so the narrower rule wins by source order with no `!important`. **The authored default is the desktop layout; there is no key above `base` in v1** | MUST | §12.3 |
| FR-073 | `base` is mandatory on every node; `md`/`sm` are written **only** where the user actually overrides, so "overridden here" is a key-presence test. **A node with no `sm` entry compiles to `grid-column: 1 / -1`** | MUST | §12.3, §11.3 |
| FR-074 | Canonical doc serialisation: UTF-8, LF, trailing newline, no BOM; fixed key sequence per node type then unknown keys sorted lexicographically; 2-space indent, one array element per line; shortest round-trip numbers, no `-0`, no exponents; absent optional keys omitted entirely rather than written `null` | MUST | §12.9 |
| FR-075 | Generation is a pure function of `(doc, system.lock.json, generator version)`. Every generated file carries `@generated`, `doc-sha256`, `system-lock-sha256`, `generator-version` and **no timestamp**. Design out the six determinism hazards: fixed key comparator; relative paths only; fixed collator / `LC_ALL=C`; ULID-derived node ids never regenerated; pinned asset encoder recorded per asset as `{encoder, encoderVersion, settingsHash, outputSha256}` with hash comparison rather than re-encoding; and no clock/network/`Math.random`/`process.env`/outside-filesystem reads at generate time, with a frozen `SOURCE_DATE_EPOCH` | MUST | §12.8 |
| FR-076 | Identical renderer for the design surface and for LOCK, switched by `editor: false` | MUST | D3 |

#### Editor shell and core operations (E8)

| Id | Requirement | MoSCoW | Source |
|---|---|---|---|
| FR-080 | Selection is reachable three ways — canvas click, breadcrumb, Navigator tree — including for a zero-height wrapper and an element fully covered by a background art container | MUST | A25 |
| FR-081 | The **Navigator / layers tree is non-optional in v1**. Canvas clicking provably cannot reach zero-height wrappers, covered elements, `pointer-events: none` decoration or empty slots | MUST | §10.2, §20.2 row 10 |
| FR-082 | Selection overlay and handles are drawn **outside the iframe** with `pointer-events: none`; hit-testing uses `data-wb-node` on elements that **already exist** plus a **single sibling overlay `<div>` outside the page's layout root**. **Zero DOM injection for hit-testing** | MUST | §11.9, R4 |
| FR-083 | Inline text editing uses `contenteditable="plaintext-only"` on ~90% of text nodes (headings, eyebrows, buttons, nav items, labels, stat numbers) | MUST | §10.3, R36 |
| FR-084 | Image replace preserves container size/crop/position; crop uses a **single draggable focal-point dot**, not a crop rectangle; placing any image without alt text or an explicit decorative toggle **blocks the placement**, not just the lock; dropping an oversized photo triggers auto-recompression with a visible, undoable confirmation | MUST | A35, A36, §10.3 |
| FR-085 | Undo/redo is a **single command stack** over the doc covering canvas drags, inspector edits and text edits alike, mirroring the server-authoritative op log; a continuous drag coalesces into one entry | MUST | §10.4, §12.9a |
| FR-086 | Transactional grouping: a component swap or a section regeneration is **ONE** undo step, with dedicated test coverage | MUST | A31, A32, R22 |
| FR-087 | Autosave flushes a **pending typed-op queue** to `POST /ops` debounced ~300ms; the server validates each op, derives the RFC 6902 patch, applies it atomically (write-temp then `fs.rename`) and appends op + patch + inverse to `history.jsonl`. **Never a raw JSON Patch over HTTP; never a base64 blob in localStorage** | MUST | §10.4, §12.13 rule 1 |
| FR-088 | Named snapshots and save-as-variation/branch; delete uses a **recovery bin independent of the undo stack**, with restore-in-place | MUST | §10.4, A-new |
| FR-089 | Element freeze prevents accidental move/resize/delete and **must not use the word "Lock"** in any user-visible string — LOCK is the terminal publish verb. Default UI word: **Freeze** | MUST | §10.2, §17-O33 |
| FR-090 | Duplicate, cut/copy/paste and paste-to-replace round-trip doc fragments **including all breakpoint overrides** | MUST | §10.2 |
| FR-091 | Multi-page manager (add, duplicate, delete, reorder), site-wide global regions (header/footer/nav edited once), page navigator, canvas↔tree selection sync, hide/show per layer, section boundary markers, per-page SEO/meta fields | MUST | §10.3, §10.5 |
| FR-092 | Global/shared component with instance overrides — **a prerequisite for safe variant swapping**; build the data model before the component-bar UI | MUST | §10.2 |
| FR-093 | Design Health HUD: one always-visible, non-modal bottom-corner pill with three dots (A11y / Perf / SEO), a page-weight bar and a projected LCP from `PerformanceObserver`'s live LCP-candidate entry; click to expand a grouped issue list. **Tier-2 findings surface only here — never as a toast stream** | MUST | §10.6, A37 |
| FR-094 | In-editor preview mode ("preview as visitor") | MUST | §10.6 |

#### The canvas (E9) — v1 by DECISION-1 option B

| Id | Requirement | MoSCoW | Source |
|---|---|---|---|
| FR-100 | The gridline overlay is drawn by reading `getComputedStyle(section).gridTemplateColumns` and painting those exact resolved tracks. **Never a hand-authored decorative grid** — it is the snap target, and it lives in the out-of-iframe overlay so it disappears at LOCK by construction | MUST | §11.2, A39 |
| FR-101 | Column derivation is integer rounding: `col = clamp(1, round((x − gridLeft) / (colWidth + gap)) + 1, cols + 1)`; the persisted value is `grid-column: <start> / span <n>`, inherently fluid | MUST | §11.2 |
| FR-102 | Row derivation uses an explicit row axis sized from the direction's spacing scale via `grid-auto-rows: var(--wb-row-unit)`: `row = clamp(1, round((y − gridTop) / (rowUnit + rowGap)) + 1, sanityRowCap)` with `sanityRowCap` ≈ 200 as a runaway-drag reject, not a layout constraint | MUST | §11.2.1 |
| FR-103 | Span preservation: a dragged block keeps `colSpan`/`rowSpan`, except that `colSpan` clamps to `min(colSpan, targetCols)` anchored at the drop column when the target section is narrower, shown in the pre-commit chip **before** commit. `rowSpan` is never clamped | MUST | §11.2.1 |
| FR-104 | Occupancy policy: **displace-down by default** (overlapped siblings shift by the dragged block's `rowSpan + rowGap`, cascading), with a live ghost preview of every block that will move **before** pointer release; `role: "art"` blocks resolve by z-order instead; a per-drop "Allow overlap here" opt-in writes an explicit `z` and increments a visible overlap counter | MUST | §11.2.1 |
| FR-105 | Cross-section drops re-parent the node with **no auto-compaction anywhere in the document**; boundary-zone drops append to the nearer section's near edge and never merge grids | MUST | §11.2.1 |
| FR-106 | Reject (snap back with an outline flash) only structurally illegal drops: onto another block's internal flow-only region; where the displacement cascade would reflow a step inside a reflow-forbidding pinned/scrubbed container; or where `row` would exceed `sanityRowCap` (inline message, not a silent clamp) | MUST | §11.2.1 AC7–AC9 |
| FR-107 | Snap engine: two 1-D interval indexes per section over four prioritised target classes — grid lines > sibling edges/centres > section padding and content rails > spacing-scale increments — with tolerance 6–8 CSS px **divided by zoom** | MUST | §10.1, A47 |
| FR-108 | Smart alignment guides with live distance labels in the accent colour, plus equal-spacing indicators when 3+ siblings match | MUST | §10.1 |
| FR-109 | Span resize by whole cells with a live "6 of 12 · 50%" readout | MUST | §10.1 |
| FR-110 | Padding/gap drag handles snap to **discrete spacing-scale steps only** and display the token name (`space-6`), never a raw pixel value. **This is the mechanic that stops direct manipulation destroying the token system** | MUST | §10.1, A28 |
| FR-111 | Keyboard nudge and grid stepping: Arrow = one cell, Shift+Arrow = span ±1, Tab walks siblings — **and this is the WCAG 2.5.7 single-pointer alternative for every drag** | MUST | §10.1, A26, §13.2 |
| FR-112 | Anchor/pin control with **exactly three verbs**: align to (left/centre/right/stretch), space above/below (stepper over the scale), order (up/down among siblings) | MUST | §10.1, R8 mitigation |
| FR-113 | Per-breakpoint override cascade: desktop-down only, sparse overrides, a **structurally prominent** persistent breakpoint indicator (not a forgettable dropdown), a **pre-commit chip** naming exactly which sizes an edit affects with one-click "apply to all sizes instead", an "overridden here" dot per overridden property, and one-click reset-to-inherited | MUST | §11.3, A42, §10.1 |
| FR-114 | DOM order **is** the reading order. Visual order is achieved only by grid placement, never by reordering the document tree. The one exception is a per-breakpoint `order: {bp, value}` override that (a) raises a persistent "Reading order will differ from what's shown here" chip, (b) is **hard-blocked on any focusable node** (WCAG 2.4.3), and (c) warns on non-focusable nodes (WCAG 1.3.2) | MUST | §11.3.1 |
| FR-115 | Before any commit that changes mobile stacking, render a **numbered list preview** of the resulting top-to-bottom mobile sequence | MUST | §11.3.1 |
| FR-116 | Free-position escape hatch as **anchored offset**, not raw absolute: the element keeps a declared anchor and the drag writes a percentage/`clamp()` offset. **v1 restricts the anchor target to `parent` or a grid line/cell**; sibling anchoring is deferred (CSS anchor positioning is a carryover Interop 2026 item and is ruled out for load-bearing layout; runtime positioning JS is forbidden in the locked export) | MUST | §11.4 rule 1, DECISIONS item 6 |
| FR-117 | Free position also: reserves `min-block-size` on the parent at drop time; is per-block **and** per-breakpoint; auto-demotes to normal flow at the small breakpoint using an **authored** `flowFallback: {col, colSpan, row, order}` written at drop time and independently editable in the Navigator; drops its z-stacking at that breakpoint unless `flowFallback` carries an explicit `z`; is capped per section (~2) with a visible counter; is **disabled by default on pinned/scrubbed containers**; and **fails LOCK** if it produces document `overflow-x` or leaves its parent's box at any checked width | MUST | §11.4 rules 2–7, A43–A45, A48 |
| FR-118 | Component internals use `@container` (with `container-type: inline-size` on every block wrapper), never `@media`, so moving a card from a 6-col to a 3-col slot needs no manual fix | MUST | §11.5, A46 |
| FR-119 | Ship ~12 section archetypes as `grid-template-areas` per direction; the moment a user drags a block off its area, **that block only** is promoted to explicit integer placement on the same grid | SHOULD | §11.6 |
| FR-120 | The preview is a **same-origin iframe** (a scaled `<div>` cannot evaluate media queries), and device heights are **pinned** (390×844, 768×1024, 1280×800, 1440×900) whenever the page contains any `vh`/`svh`/`dvh` rule | MUST | §11.7 |
| FR-121 | Canvas zoom/pan (25–200%, tolerance ÷ zoom, space-drag), rulers, fraction-stored drag-out guides, marquee/multi-select and align/distribute are the **tail** of this epic and the first candidates to trade back out | COULD | §10.1, slice strategy |

#### Component bar and variants (E10)

| Id | Requirement | MoSCoW | Source |
|---|---|---|---|
| FR-130 | A **variant** is a structurally distinct composition of the same component within one direction. Size, theme, density, state, icon-slot and semantic colour are **computed axes** and never count against the variant budget | MUST | §8.1 |
| FR-131 | "Structurally distinct" is machine-checkable: every component declares a **variant axis vector**, and two variants are distinct if their vectors differ in at least one axis | MUST | §8.1, §8.6 |
| FR-132 | The variant-axis schema is **hand-authored in the skill** for determinism, with an explicit effort line | MUST | DECISIONS item 12 |
| FR-133 | `variants.ts` is a deterministic generator over the direction's tokens — **no model call, no subagent writes** (subagents are policy-blocked from `Write`; verified twice, first-party) | MUST | §14.1 `[V]` |
| FR-134 | "More variants" appends the next N using the skill-supplied current highest index (append-only, collision-free); "more like this" appends **5 deterministic neighbours** of an already-approved variant | MUST | §14.1 |
| FR-135 | Variants generate **lazily on first open** of a family's swap panel, cached per direction, never pre-generated for unused families | MUST | §14.1, R29 |
| FR-136 | **No two variants offered in the same bar may be indistinguishable at 200×120px** | MUST | A34, §8.5 |
| FR-137 | Hover-preview ghosts the variant live in the real slot with current copy and neighbours | MUST | A33 |
| FR-138 | Typed slot contracts `{name, type, cardinality, required}`; the bar offers **only** variants whose contract is a superset or exact match, and states before the swap "this variant adds N slots" / "this variant has no place for: [x]" | MUST | §14.4 |
| FR-139 | **Content orphanage:** anything the target cannot hold moves to a visible parked panel, is **never deleted**, and is auto-restored if a later swap re-introduces the slot | MUST | §14.4, A29 |
| FR-140 | Newly created empty slots render as visibly flagged placeholders that **BLOCK LOCK** until filled or deleted — this is what prevents fake statistics shipping | MUST | §14.4, A30 |
| FR-141 | A component swap replaces the node **in place** in the tree; tab order before and after is identical for equivalent content | MUST | A38 |
| FR-142 | Cross-direction swaps are **out of v1** (only one direction is generated in full). When they arrive (v2) they must show both renderings side by side ("Fitted to your direction" / "Kept as designed (adds N off-system values)"), record transplants in a visible coherence-debt ledger, offer the whole-site direction switch at a soft cap of ~3, and **never block** | WON'T (v1) / MUST (v2) | §14.3, §18 |

#### Artwork lanes and asset library (E11)

| Id | Requirement | MoSCoW | Source |
|---|---|---|---|
| FR-150 | **Lane A** — code-drawn, token-parameterised artwork: ≥60% of a 20-artwork set is token-referencing (`currentColor` / `var(--*)`), and changing a direction's hue anchors re-skins all token-referencing artwork **with no regeneration** | MUST | A20, A21 |
| FR-151 | **Lane B** — asset-library ingestion into `assets/manifest.json` with direction-affinity tags and a licence class per asset | MUST | TR14 |
| FR-152 | **Lane C** — external raster generation is **out of v1**; ship a runbook at `docs/lane-c-raster-runbook.md` whose output ingests through Lane B's manifest | WON'T (v1) | Constraint; DECISIONS item 13 |
| FR-153 | Asset-library pane with **direction-affinity filter chips** — the chips are what makes presenting 20 artworks legal | MUST | R34 |
| FR-154 | Warn at **interview time** when a project has no asset library, before generating a design system the pipeline cannot fully deliver. There is no known mitigation that preserves the paste-only path | MUST | DECISIONS item 13 |
| FR-155 | Custom cursors never exceed 128×128 and every `cursor: url()` has a native keyword fallback | MUST | A23 |

#### Motion and art containers (E11/E13, per D4)

| Id | Requirement | MoSCoW | Source |
|---|---|---|---|
| FR-160 | One container contract covers art and motion, carrying `boxSizing, aspectPolicy, anchor, overflow, mask, schemeAware, motionCapable, reducedMotionPoster, reducedMotionVariantRef, focalPoint, altText|decorative, licenseRef, trigger, viewportThreshold, source{kind, ref, poster}, playback{autoplay, muted, loop, iterationCount}, costClass, tokenRefs[]` | MUST | §9.1 |
| FR-161 | Explicit `aspect-ratio` (or `min-block-size` from the ratio scale) is mandatory so the grid row is reserved before the asset initialises | MUST | §9.1 rule 1 |
| FR-162 | Animation inside a container may only touch `transform`, `opacity`, `filter`, and may **never** change the container's grid placement, width or height | MUST | §9.1 rule 2 |
| FR-163 | `trigger` is a closed enum — `page-load`, `viewport-enter`, `viewport-scrub`, `pointerenter`, `click`, `always` — and `viewportThreshold ∈ [0,1]` (default 0.2) is meaningful only for `viewport-enter` | MUST | §9.1 rule 3 |
| FR-164 | `reducedMotionVariantRef` is **mandatory whenever `motionCapable: true`**; validation fails without it. Every motion item has a paired reduced-motion sibling and the reduced-motion render diff must **differ** where motion exists — and still look designed | MUST | §9.1 rule 4, A22 |
| FR-165 | `source.ref` **must** resolve against `assets/manifest.json`; a container with no asset of its own sets `source.kind: 'none'` | MUST | §9.1 rule 5 |
| FR-166 | `muted` **must** be true whenever `source.kind: 'video'` and `autoplay: true` — enforced as a field-level constraint | MUST | §9.1 rule 6 |
| FR-167 | `costClass ∈ {free, cheap, heavy, gpu}` is assigned per container **kind**, not per instance, and is what the concurrency caps are computed against | MUST | §9.1 rule 7 |
| FR-168 | The component bar presents Style and Motion as **two tabbed pickers** for dual-axis container kinds — never a flattened cross-product list | MUST | §9.1.1 |
| FR-169 | The container contract must gain a **`pauseAffordanceRef`** field so an unpausable marquee/ticker/ambient layer is structurally unbuildable rather than caught late at LOCK (open cross-section coordination item owned by §9) | MUST | §13.4 gate 13a |
| FR-170 | Motion is **disabled in edit mode** (the editor runtime fights the site runtime); motion feel is judged in preview mode. **R14 has no known mitigation** — this is stated, not solved | MUST | R14, P18 |

#### Step 5 — regeneration (E12)

| Id | Requirement | MoSCoW | Source |
|---|---|---|---|
| FR-180 | Per-section notes drive a **scoped regeneration of that section only**, executed inline via Local Regeneration Mode (not another hand-carry), as a single undo step, with a regeneration log | MUST | §17-O21, A32 |
| FR-181 | Partial redesign re-enters Step 2 with the current direction vector, marking which slots are frozen and which are open; full redesign is a new Step-2 cycle with prior identity as a negative constraint. Redesign **forks** (save-as-variation), it does not replace in place | MUST | §14.2, §17-O22 |
| FR-182 | Migration is **mandatory and never silently drops a node**: map old variant ids to new, list unmappable nodes explicitly, and have the user resolve each. Logged as an explicit operation into `migration-report.json` | MUST | §14.2, §12.16 |
| FR-183 | Applying a new direction is a **REVIEWED** operation: per-node flags, LOCK blocked until acknowledged, bulk-acknowledge available | MUST | DECISIONS item 7 |
| FR-184 | Layout survives a direction swap because placement is stored as grid integers and token indices — **provided both directions share the same grid spec** (which is why `layout.breakpoints` and `type.viewport-endpoints` are invariant) | MUST | §14.2, §7.1 |

#### Step 6 — custom components (E13)

| Id | Requirement | MoSCoW | Source |
|---|---|---|---|
| FR-190 | v1 caps custom components to a **whitelisted registry** — table, chart, embed, form — generated deterministically against the direction's tokens plus dataviz sub-tokens. Everything else is explicitly out of scope | MUST | §14.5 |
| FR-191 | v1 ships a **minimal placement path** for those four kinds plus a **minimal chart-data field** (paste a table of numbers bound to the chart node's data prop; no formulas, no multi-sheet, no cell formatting), because shipping charts with no insertion path would silently cut a capability the user named. **Both rows require user sign-off as a deviation from §18's literal cut** | MUST (with sign-off) | §10.3 sign-off note |
| FR-192 | Charts decompose into marks, a chrome kit (axes, gridlines, ticks, labels, legend, tooltip, annotation/reference line, zero-line — **4 treatments applied across all mark types, which is what makes a site's charts read as one system**), colour ramps **derived from the direction's OKLCH anchors and validated colourblind-safe in both schemes**, and data states | MUST | §14.6 |
| FR-193 | v1 charts are **build-time SVG with ≤4 mark types**; no chart runtime ships. Of the five data states, only **empty** and **single-data-point** are ever shipped; **loading and error are editor-only previews** labelled "Preview only — not shown to visitors"; interactive "partial" is v3 | MUST | §14.6, §17-O14 |
| FR-194 | The inline-authored path runs the full coherence lint set before acceptance and enters through the `component.custom-slot` registration contract that enforces token usage | MUST | §14.5 |
| FR-195 | The opaque custom-code-block container — positioned but never introspected by the editor — is **v2**, and is where the quality ceiling actually lives | WON'T (v1) | §14.5, §18 |
| FR-196 | The **signature moment is not a variant set**: 2–3 bespoke concept candidates per direction, generated at Step 2, chosen and refined at Step 4, handled thereafter through the custom code block. **A lint flags a second signature moment** | MUST | §14.7 |
| FR-197 | No third-party mark (platform badge, social icon, trust badge, map tile) may be redrawn; `[3P]` items are deterministic embeds used as supplied | MUST | A75, R23 |

#### Step 7 — LOCK (E14)

| Id | Requirement | MoSCoW | Source |
|---|---|---|---|
| FR-200 | LOCK is `build → scrub → assert → snapshot`, a **re-render with `editor: false`**, never a copy-and-strip | MUST | D3, §12.5 |
| FR-201 | Enforce editor absence with five layered mechanisms: two configs / two commands / two out-dirs so the editor is not in the publish build graph at all; dev-only injection gated on the build command; dev-toolbar-class chrome that physically cannot leak; `import.meta.env.WB_DESIGN` guards **explicitly defined as `false` in the publish config** (an undefined variable may not be tree-shaken — filed bug); and a post-build hook that scrubs every emitted HTML file and then asserts | MUST | §12.5 |
| FR-202 | Purity gates: (1) grep the published tree for editor strings — any hit fails the build; (2) **two-build equality** by sorted-path + SHA-256 manifest comparison, built in a clean `git worktree`, against a committed editor-free dependency set, with `SOURCE_DATE_EPOCH`/`TZ=UTC`/`LC_ALL=C`/pinned runtime version pinned for both builds; (3) published JS byte-size assertion; (4) screenshot diff between editor-preview-at-1280 (chrome hidden) and the built page at 1280; (5) interaction-manifest check proving every declared motion/interaction behaviour exists in shipped code; (6) **zero unresolved references and zero unacknowledged `variantMigrated`/`orphaned` flags**, failing with the node list not a count; (7) **zero design-time origins** (grep `localhost`, `127.0.0.1`, `0.0.0.0`, `file://`, the session port and the session root path across `srcset`, `<meta>`, inline `style`, CSS `url()`/`@import`, JSON-LD and sourcemap comments); (8) **`wb verify` clean at lock time** — regenerate to temp, `diff -r` the text files, hash-compare binaries separately, and re-serialise every doc into canonical form requiring a zero diff. **There are EIGHT purity gates, not five (see NA-03)** | MUST | §12.5 |
| FR-203 | Gate 2 **never** edits the live `package.json`, the live lockfile or the live dependency tree, so a design server running in another terminal is unaffected; budget ≤3 minutes, and above 5 minutes it demotes to CI-only with an explicit `gate2: waived-local` entry in `gate-report.json` — **a recorded waiver, never a silent skip** | MUST | §12.5 |
| FR-204 | Run the ordered lock-time checklist — **32 checks: 28 base gates plus lettered insertions 4a (motion-concurrency caps), 11a (skip-link presence and first-tab-order), 13a (pause/stop/hide affordance), 23a (asset-reference resolution)** — cheapest-and-most-foundational first | MUST | §13.4 |
| FR-205 | LOCK is **non-mutating**: it writes only `dist/published/` and `.wb/locks/<iso>/`, then tags `wb-lock/<n>`. **UNLOCK is restarting the design server.** The one uncovered case — hand-edits inside the exported tree — is named explicitly, carries a generated-do-not-hand-edit banner, is diffed against the per-file SHA-256 manifest at both unlock and the next LOCK as a **blocking prompt**, and has a best-effort, explicitly fallible `extract-override --from-dist` re-homing path that refuses rather than guessing | MUST | §12.5, §12.6 row 6 |
| FR-206 | LOCK strips the recovery bin, freeze flags, per-section notes and asset-library pane state from published output; `assets/manifest.json` stays in the project and in the evidence bundle | MUST | Architecture constraint |
| FR-207 | Snapshot into `.wb/locks/<iso>/`: every doc, `site.json`, `content.json`, `system.lock.json`, `assets/manifest.json`, the dist hash manifest, the scrub output, `lock-manifest.json` and `gate-report.json`. **`dist/` is excluded — it is reproducible** | MUST | §12.2, §17-O26 |
| FR-208 | Going back to an older lock restores **documents and the system lock together**; if library files no longer hash-match the restored `system.lock.json` the restore stops and prints the migrate command rather than opening a half-resolved project | MUST | §12.5 |
| FR-209 | Export is **write-to-new-dir-then-swap**; no `rm -rf` is executed anywhere in the export path | MUST | A59, Oracle guardrail |

#### Step 8 — publish and evidence (E15)

| Id | Requirement | MoSCoW | Source |
|---|---|---|---|
| FR-210 | **Committed v1 behaviour is automated publish**: after a one-time credential setup performed by the user, every subsequent lock-and-publish runs the static deploy non-interactively | MUST | §15.4 (with sign-off) |
| FR-211 | If no valid credential is configured, or the deploy call fails auth, fall back to **emitting a runbook** — and record that the site is locked but **not** published. The fallback does **not** satisfy the "locked, published" exit criterion | MUST | §15.4 |
| FR-212 | The evidence bundle carries: per-font `{family, foundry, licenceClass, fileHash, sourceUrl, attributionRequired}`; per-asset `{generator, model, planTier, licenceClass, prompt, alt, source}`; third-party marks with usage rules and confirmation they were used as supplied; the gate report with thresholds and measured values; the contrast proof table (WCAG ratio **and** APCA Lc per pairing); screenshots across the breakpoint matrix × light/dark × full/reduced motion; the **direction tour** rendered from `direction-tour-log.json` including every heat's pick and stated reason; reference triangulation; the substitution log; the publish record; and the disclosure line | MUST | §15.6 |
| FR-213 | Disclosure wording is fixed: **"Automated accessibility gates passed: N. Manual and screen-reader review not performed."** Never "WCAG AA compliant" or any conformance claim | MUST | §13.9, A72, A73 |
| FR-214 | Commercial-foundry faces emit a **pre-launch blocker** rather than being embedded | MUST | A74, §15.6 |
| FR-215 | Apply the **≥3-reference rule**: each direction abstracts ≥3 references from different eras/genres/cultures, recombined; if a direction is >70% overlap with any single reference, regenerate against a different reference | MUST | §15.6 |
| FR-216 | Mirror a one-line verdict into `.acos/evidence/<date>/website-<session>/` | SHOULD | Architecture constraint |

#### Security, concurrency, lifecycle (E16)

| Id | Requirement | MoSCoW | Source |
|---|---|---|---|
| FR-220 | Six-control posture: bind `127.0.0.1` only; Origin allowlist on every non-GET **and on the SSE upgrade**; per-session bearer token (`.wb/editor.token`, mode 0600); typed semantic-op wire format; path allowlist verified by `realpath` + prefix assertion with symlinked paths rejected; idle shutdown | MUST | A76–A79 |
| FR-221 | **One writer.** `wb-server` is the only process that writes the doc-owned set. The browser proposes semantic ops and never performs raw file writes; a raw JSON Patch or a file path in a request body is rejected | MUST | A79, §12.13 |
| FR-222 | **Reconciliation is the authoritative anti-clobber mechanism**: `.wb/doc-hashes.json` plus a watch on the doc-owned set; any doc-owned file whose on-disk hash differs from the journal without a corresponding server-issued write is treated as an out-of-band mutation — the editor refuses to save over it, shows both versions, and offers reload / keep-mine / merge-by-hand | MUST | §12.7 mechanism 1 |
| FR-223 | Defence in depth, **each with its stated limit**: a PreToolUse guard blocking Write/Edit on doc-owned paths and scanning Bash command text (a heuristic, defeatable by indirection); `chmod 0444` while the editor lock is held (a speed bump — same uid can chmod back); `.gitattributes` marking generated output; a pre-commit hook; and the generated banner | MUST | §12.7 |
| FR-224 | Claude gets a **legal write path**: `wb op '<typed op JSON>'` posts the same typed op the browser posts, through the same server, inheriting validation, the op log, optimistic concurrency and the SSE push. The skill's instructions state this in the imperative | MUST | §12.7 |
| FR-225 | Optimistic concurrency: a stale save (mtime/hash mismatch) is rejected with **409** and the editor surfaces "reload or force" | MUST | A82 |
| FR-226 | `editor.lock` covers processes; a **tab claim over SSE** covers the two-tab case, with the second tab read-only | MUST | §17-O24 |
| FR-227 | Fixed port **8820** on `127.0.0.1` — never a random port; `state.json` carries `{port, pid, url, sessionId}` at boot; confirm bind with retrying curl; prove turn-boundary survival with a **second curl in a separate tool call**; regenerate-if-stale on startup | MUST | Constraint SERVER |
| FR-228 | Human-in-the-loop channel: SSE plus a `commands.jsonl` inbox picked up by a blocking `tail -f` in the Claude session (zero token cost while the user designs). **The server NEVER calls `Task()`; the Claude session is the only engine.** Agent ops go through the inbox **always**, even when the editor is not running, to avoid two write paths | MUST | Guardrail; §17-O23 |
| FR-229 | Any hook the skill registers is cheap and **fail-open**, registered dynamically and removed at close. "No LOCK without gates passing" lives in a script exit code, not a hook | MUST | Guardrail |

#### Quality gates and capture (E17)

| Id | Requirement | MoSCoW | Source |
|---|---|---|---|
| FR-230 | The dividing line is **scoped arithmetic/DOM-read vs whole-document render pass**, not "a11y vs performance": LIVE checks are sub-100ms, fire on drop/mouseup (**never mid-drag, never per-frame**) and are scoped to the touched subtree; LOCK-TIME checks are whole-document and batch | MUST | §13.1 |
| FR-231 | Live checks: contrast recompute (WCAG 2 ratio **and** APCA Lc on every touched pair); target size via `getBoundingClientRect()` flagging <24×24 unless an exception applies; scoped accessibility-engine run on the touched subtree; overflow/clipping via `ResizeObserver` + `scrollWidth > clientWidth`; focus-not-obscured intersection; reading-order-vs-visual-order walk; reduced-motion sibling presence; **alt/decorative gate that blocks the placement**; image auto-optimisation on drop; budget HUD; and a **motion-concurrency running counter** so the human watches the count accumulate turn-by-turn rather than discovering it at LOCK | MUST | §13.3 |
| FR-232 | **Two WCAG criteria apply to the editor itself** — 2.5.7 Dragging Movements (every drag has a single-pointer alternative) and 2.5.8 Target Size (24×24 CSS px minimum with the four documented exceptions, checked by a live bounding-rect check on render, not just at lock) | MUST | §13.2, A26, A27 |
| FR-233 | Severity tiers: Tier 0 blocks the individual placement/edit; Tier 1 blocks LOCK only and never interrupts live editing; Tier 2 is advisory, dismissible and batched into the Design Health pill; Tier 3 is silent end-of-session telemetry. Debounce to drop/mouseup, collapse repeated violations into one counted badge | MUST | §13.7 |
| FR-234 | The anti-slop lint is a **hard gate upstream** on the generated design-system JSON and a **Tier-2 advisory with permanent per-element dismiss** at the human-edit layer. Motion-kind homogeneity is a Tier-2 entry warning at 3+ distinct variants of the same kind `[I — carried-over default, not validated]` | MUST | §13.8 |
| FR-235 | Capture uses plain Chrome CLI headless with zero npm dependencies, asserting a non-empty output file, with the inherited wait recipe re-expressed in TypeScript (navigate rather than set content; network-idle with a load fallback; strip `loading="lazy"`; `document.fonts.ready` **plus** per-image `decode()`; a deferred-CSS settle). **`await document.fonts.ready` before ANY `getBoundingClientRect`** in editor or capture | MUST | Constraint CAPTURE; §11.8 row 10 |
| FR-236 | Any capture used to judge a viewport-height layout pins the window **and** the preview iframe to a real device size and **asserts the measured iframe height** rather than assuming a viewport config was honoured. Full-page tall captures are valid for content review only | MUST | Guardrail; §11.7 |
| FR-237 | `gates.ts` returns **structured verdicts** `{gateId, tier, status: pass|fail|inconclusive, measured, threshold, evidenceRef}` and never throws on a normal fail | MUST | Guardrail |

#### Durability and diagnostics (E18)

| Id | Requirement | MoSCoW | Source |
|---|---|---|---|
| FR-240 | `--resume` reconstructs the phase **from disk alone**, with no reliance on conversation memory | MUST | A13, axiom-synthesis principle |
| FR-241 | On an eternity `/clear`, the resume prompt says **RE-ATTACH** to the fixed port via `state.json`, never relaunch | MUST | Guardrail |
| FR-242 | `verify.ts` regenerates to temp and diffs; `doctor.ts` reports hash mismatches, orphaned overrides and stale locks, and escalates override accumulation at the stated starting thresholds (≥5 per page amber, ≥15 red, ≥40 per site, ≥25% of a page's nodes) `[I — stated starting numbers, tunable in `site.json`]` | MUST | §12.8, §12.7 |
| FR-243 | `references/gotchas.md` carries every harness gotcha: cwd resets between Bash calls; no `timeout`/`gtimeout` binary (it yields **empty output**, not an error); open previews with Chrome explicitly; APFS case-insensitivity means sibling direction names must not differ only by case; destructive commands score high with the Oracle | MUST | Constraint AGENT/HARNESS |
| FR-244 | Persist the **RESULT** of a generation as the artifact of record; store the prompt for provenance only. Never plan to re-derive a system from a stored prompt | MUST | Guardrail; R44 |
| FR-245 | Keep durable artifacts under `.acos/website-builder/` and the project's own tree; `session-cleanup.sh` touches `.acos/state/` only | MUST | Guardrail |

#### Acceptance, demos, learning capture (E19)

| Id | Requirement | MoSCoW | Source |
|---|---|---|---|
| FR-250 | Map every §19 acceptance criterion to a gate, a script or an observable behaviour. **§19 as written contains A1–A90 (90 criteria) `[V — read]`; the "96" figure carried into the normalized config is not supported by the section text (NA-20)**, and A91+ additions are proposed by two different sections with colliding numbers (NA-19) | MUST | §19 |
| FR-251 | `bun selftest.ts` passes 100% of assertions before any release claim | MUST | A85 |
| FR-252 | Every slice carries `## Dev Learnings` and `## QA Learnings`, and is not Done until they are updated | MUST | §0.7 |
| FR-253 | `AGENT-METRICS.md` defines (does not compute) SPD, QAP, TER and UAPS, and points instrumentation at `.acos/metrics/agent-completions.log` | MUST | §0.5 |

### 4.2 APIs, Data & States

#### Server route contract (topology-independent invariant I2)

| Route | Method | Contract |
|---|---|---|
| `/doc` | GET | Returns the composition document with an **ETag**; supports 304 |
| `/ops` | POST | Accepts **typed semantic ops only**; validates each against its schema and the component library; derives the RFC 6902 patch; applies atomically (write-temp then rename); appends `{op, patch, inverse}` to the op log; **409 on stale ETag** |
| `/events` | GET | SSE stream with ~15s keepalive; carries doc updates, gate results and the tab claim |
| `/variants` | POST | Lazy variant generation for one family in the active direction |
| `/lock` | POST | Runs the LOCK pipeline and returns a structured gate report |
| `/internal/*` | POST | The Claude session's write-back channel (same validation path as `/ops`) |
| static | GET | Serves the design surface and the preview |
| health | GET | Used by Gate 16-A's post-turn-boundary curl |

Bearer token **and** Origin allowlist are enforced on every mutating route and on the SSE upgrade. **Wire format is typed ops; a raw JSON Patch or a file path in a request body is rejected** (an `add`/`replace` on an arbitrary pointer could rewrite the system lock or inject an override path).

#### Topology-independent invariants (build only these until the O4 ADR lands)

- **I1** one writer — the server is the only process that writes the doc-owned set.
- **I2** the route contract above.
- **I3** semantic ops, never raw file writes from the browser.
- **I4** preview isolation as a **requirement, not a mechanism** — a capture of the preview contains zero editor chrome.
- **I5** the editor survives a preview-process restart without losing unsaved state.
- **I6** the preview substrate is open — **nothing may hard-depend on any one framework**; if the substrate spike resolves to plain generated HTML, "process 1" collapses to a static file watcher plus reload.

#### File set (writers are normative)

| File | Purpose | Writer |
|---|---|---|
| `site.json` | Project record: formatVersion, projectId (ULID), breakpoints, grid, page list, per-page SEO/meta, and `systemLock {directionId, systemVersion, tokensSha256, librarySha256, source, importedAt}` | Editor process, via typed ops only |
| `pages/<id>.doc.json` | The scene graph, in canonical serialisation | Editor process |
| `content.json` | Copy, separated so a content-only edit path exists | Editor process; also the content-only CLI (v2) |
| `history.jsonl` | Append-only op log `{seq, ts, actor, op, target, patch, inverse, label}` | Editor process |
| `system.lock.json` | Pins the imported direction like a package lock: id, version, per-file hashes | Importer and migrate only |
| `assets/manifest.json` | Per-asset provenance, licence class, and the **allowlist every asset reference is validated against**; records `{encoder, encoderVersion, settingsHash, outputSha256}` per derived asset | Editor process and importer |
| `provenance.json` | Per component instance: direction id, variant id, generation timestamp, prompt hash | Editor process |
| `direction-tour-log.json` | `{rounds:[{roundName, heats:[{directionsShown[], orderShown[], pick, reason}]}], finalPick, timestampIso}` — written as rounds progress, **never reconstructed after the fact** | Skill (Step 4) |
| `inbound/import-report.json` | Per-item accept/reject/quarantine with reason and offending snippet | Importer only |
| `migration-report.json` | Every reference that changed, old and new value, and the rule that decided it | Migrate only |
| `.wb/inbox.jsonl` / `commands.jsonl` | Append-only agent/browser intent channel | Any agent (append-only) |
| `.wb/editor.lock`, `.wb/editor.token` | Single-writer pid + heartbeat; per-session bearer token (0600) | Editor process |
| `.wb/doc-hashes.json` | `{path, sha256, mtimeMs, seq}` journal — the reconciliation input | Editor process |
| `.wb/session-ui.json` | Selection, scroll, open panels, **active breakpoint key** | Editor process |
| `.wb/locks/<iso>/` | Immutable per-LOCK snapshot set | Lock only |
| `lock-manifest.json` | Layout hash **plus a SHA-256 per emitted file** so unlock can diff hand-edits | Lock only |
| `state.json` | `{port, pid, url, sessionId}` | Server at boot |
| `session.json` | `{warmStart, sourceSystemId, assetLibraryPath, minedSources[], structuralRtl, d1Deviations[], branchChoice}` | Skill |
| `gate-report.json` | Structured verdicts per gate, plus any recorded waiver | Gate suite |

> **NA-07 (naming).** The canonical scene graph is `pages/<id>.doc.json` + `site.json` `[V — §12.2, §12.13 write allowlist]`. Sections §4, §11, §12.6 and §12.10 of the PRD — and the technical requirements carried into this pipeline — still say `layout.json`. This spec treats `layout.json` as a **legacy alias** for the doc set and requires the rename to be completed before implementation.

#### Ownership zones

| Zone | Paths | Writer |
|---|---|---|
| Machine-owned (regenerated wholesale) | generated sources, `tokens.css` | The generator only |
| Human/agent-owned (never written after scaffold) | page wrappers, `src/overrides/**`, `src/lib/**` | Claude and the user |
| Doc-owned | `pages/*.doc.json`, `content.json`, `site.json`, `assets/manifest.json`, `provenance.json`, `history.jsonl` | The editor process only — **and Claude reaches them through `wb op`, never a file write** |
| Snapshot / build output (never hand-edited, never restored from) | `dist/published/**`, `.wb/locks/**` | Lock only |
| Import record | `inbound/**`, `system.lock.json`, `migration-report.json` | Importer and migrate only |

#### Core entities

`Session`, `InterviewAnswer`, `Concept`, `DirectionCapsule`, `Direction`, `DesignToken` (anchor vs derived provenance; spring/motion extension shape), `SystemLock`, `ImportEnvelope`, `Layout`/`Doc`, `Content`, `Node` (`{id, component, variant, region, layout, props, slots, text, override, locked, notes, variantMigrated?, orphaned?}`), `SlotContract`, `Variant`, `Artwork/Asset`, `FontCatalogEntry`, `Provenance`, `DirectionTourLog`, `HistoryOp`, `TrashEntry`, `SectionNote`, `CoherenceLedger`, `EditorLock`/`TabClaim`, `ServerState`, `Command`, `GateResult`, `LockManifest`, `EvidenceBundle`, `Registry` (v2). Full field-level modelling belongs in `data-model.md` (produced by `/preeng.plan`).

#### Layout node shape (where D2 lives)

```json
{
  "id": "n_hero_art",
  "component": "ArtContainer",
  "variant": "background-scene@07",
  "layout": {
    "base": { "mode": "flow", "col": { "start": 2, "span": 10 },
              "align": "stretch", "spaceBefore": "space-l", "spaceAfter": "space-xl" },
    "md":   { "col": { "start": 1, "span": 6 } }
  },
  "props": { "motion": "entrance.mask-wipe@03", "aspect": "16:9",
             "focalPoint": { "x": 0.5, "y": 0.4 } },
  "text": {}, "slots": {}, "locked": false
}
```

Free position is a per-key value like any other — `{ "mode": "free", "anchor": {...}, "offset": {...}, "z": 2 }` — so **absence at the small key means flow at the small key**, which is exactly how auto-demotion is represented. Per D4, motion is not a separate structure: an animated piece is an `ArtContainer` node whose `props.motion` is a token id.

#### States

**Pipeline phase (recomputed from disk, never from memory):** `init → warm-start → interview → prompt-emitted → awaiting-ingest → ingested → direction-tournament → direction-selected → editing → regenerating → locking → locked → published`. Each transition is evidenced by a file on disk; `--resume` reads the frontier.

**Server lifecycle:** `not-started → launching (rung F1..F5) → bound (same-turn 200) → survived-boundary (second curl, separate call) → serving → idle → shut-down`. **A same-turn 200 is never proof of life.**

**Node lifecycle:** `placed → edited → overridden(bp) → frozen → migrated(flagged) → orphaned(parked) → trashed(recoverable) → restored`.

**Gate verdicts:** `pass | fail | inconclusive` (never a thrown exception on a normal fail). **INCONCLUSIVE blocks like a fail.**

**Lock states:** `unlocked (design server running) → gates-running → locked (dist + snapshot + tag) → published | runbook-emitted`. UNLOCK = restart the design server.

### 4.3 Non-Functional Requirements (NFRs)

| Id | NFR | Threshold / statement | Source |
|---|---|---|---|
| NFR-01 | Live-check latency | Sub-100ms, on drop/mouseup only, scoped to the touched subtree; never mid-drag, never per-frame | §13.1 |
| NFR-02 | LOCK wall-clock | **p50 ≤ 90s, p95 ≤ 180s** for a representative 5-page site on the reference profile. `[I — inference sized against the 32-gate list; not measured. Validate against a real prototype before treating as an SLA]` | §13.1 |
| NFR-03 | Gate 2 budget | ≤3 minutes target; >5 minutes demotes to CI-only with a recorded waiver | §12.5 |
| NFR-04 | Core Web Vitals | **LCP ≤2.5s, CLS ≤0.1** (internal stretch 0.05), **INP ≤200ms** (or TBT ≤600ms floor / 300ms aspirational as proxy), **pre-LCP transfer ≤1.5–2MB** (not total page weight), median-of-3, mobile, simulated Slow-4G + 4× CPU. **This is the canonical threshold statement; A66/A67 are subordinate to it and are recorded as inconsistent with it (A66 omits INP; A67 states a flat ≤2MB)** | §13.4 gate 20, §13.5 |
| NFR-05 | Accessibility floor | WCAG 2.2 **AA as the contractual floor**, WCAG 2 as the pass/fail gate, APCA advisory (Lc75 body / Lc60 large-bold / Lc45 large-non-text `[U — U1, inherited, not re-verified]`). Selected AAA items (2.4.13, 2.3.3) are aspiration, not gates | §13.10, §17-O19/O20 |
| NFR-06 | Accessibility claim ceiling | Automated tooling catches **57.38%** of real issues `[V — Deque Accessibility Coverage Report, 13,000+ page-states, ~300,000 issues]`. Therefore the only honest claim is "passed N automated + structural gates" | §13.9 |
| NFR-07 | Reflow | No two-dimensional scroll at 320 CSS px except exempted content; 40-char unbroken token produces no overflow; +35% pseudolocalisation produces no overflow or truncation; 200% zoom produces no horizontal scroll and no content loss | §13.4 gates 10, 17, 18, 19 |
| NFR-08 | Motion concurrency caps | max 1 GPU-class scene, max 1 particle/ambient layer, max 2 autoplay video loops, max 2–3 pinned/scrubbed sequences **per page**, enforced structurally with per-container attribution. `[I — carried from prior research, not benchmarked against this render stack; a starting default, not a validated ceiling]` | §13.4 gate 4a |
| NFR-09 | Motion verification ceiling | VLM recall of aesthetic animation measured **0.16** `[U — U16, prior report, flagged unvalidated end-to-end]`; acceptance therefore rests on the human plus deterministic motion lint, **never** an automated visual score | §20.3 |
| NFR-10 | Token volume | ~600–900 resolved tokens per complete direction `[V — counted programmatically from Carbon/Material/Fluent sources]`; the user's "~80 items" is an item count, each expanding to 1–40 tokens | §7 |
| NFR-11 | Reflow cost | The custom-property set compiles to a flat variable layer **once per direction change**; never re-resolved per drag | R30 |
| NFR-12 | Determinism | `verify` produces an empty diff on a freshly generated project **and** after ten drag operations; any nondeterminism makes verify a false-positive machine, users learn to ignore it, and the drift guarantee dies silently | A53, §12.8 |
| NFR-13 | Byte reproducibility | Two-build byte-equality is the target; **no consulted source establishes bundler-level byte reproducibility across two installs**. Fallback = normalised comparison with an enumerated, justified exception set, which **weakens D3's proof and requires sign-off** | §12.5 O33 |
| NFR-14 | Export purity | Zero editor strings, zero design-time origins, zero unresolved references in the published tree — asserted, not claimed | §12.5 gates 1, 6, 7 |
| NFR-15 | Security posture | Localhost is not a trust boundary (CVE-2025-24010 class). Six controls, all enforced; Step-3 ingest is a validating importer with quarantine and nothing is partially applied | §16, R16/R17 |
| NFR-16 | Concurrency safety | No silent overwrite in either direction, ever; conflicts surface with both versions retained | §12.7 |
| NFR-17 | Licence completeness | Zero shipped assets or fonts without a recorded licence class; build-failing. Every referenced `url()`, `font-family`, SVG id and asset path in the built output resolves to a manifest entry **and** a file on disk, with zero remote-host references | S8, §13.4 gates 23a, 26 |
| NFR-18 | SEO/structured data | Unique title per page; 50–160 char description; canonical URL; OG + Twitter with image; `<html lang>` matching the interview language; **single `<h1>` with no skipped levels**; 100% alt coverage; robots.txt + sitemap.xml generated from the page tree; JSON-LD matched to the site-type answer and validating against schema.org | §13.6 |
| NFR-19 | No-JS | Content visible, nav usable, forms submittable with JavaScript disabled — also the crawler's view | §13.4 gate 24 |
| NFR-20 | Font loading | `font-display: swap` on every `@font-face`; exactly the committed families preloaded; a fourth family introduced by a late swap fails the gate; every `@font-face` ships a **metric-matched local fallback computed from the real selected font binary**, and font-swap-attributable CLS must be ~0 | §13.4 gate 21 |
| NFR-21 | Harness compatibility | Absolute paths everywhere (cwd resets between Bash calls); no `timeout`/`gtimeout` binary — it yields **empty output**, not an error; never `rm -rf` in the export path; never treat a same-turn 200 as proof of life; do not assume `Task` is callable mid-skill | Guardrails |
| NFR-22 | Language | All new code is TypeScript run by Bun; a scan of the skill's scripts and app directories returns **zero** Python files. The only contemplated exception is the sign-off-gated F4 launcher rung | A84, NG6 |
| NFR-23 | Distribution | The skill is installed globally as a **symlink** to the git-tracked copy, verified by an `ls -la` showing the arrow | A88 |
| NFR-24 | Overrides ceiling | Override accumulation escalates at ≥5 per page (amber), ≥15 (red finding, LOCK proceeds but the count is recorded in the gate report), ≥40 per site, or ≥25% of a page's nodes. `[I — stated starting numbers, not measured]` | §12.7 |
| NFR-25 | Interview duration | Fast mode ≈ **25–35 minutes**; open-ended ≈ **45–70 minutes** `[I — per-question timing budgets estimated, not measured; instrument from day one]` | §5 |
| NFR-26 | Evidence integrity | Every gate emits a structured verdict with measured value and threshold; the evidence bundle records the publish path actually used, so it always states plainly whether the site is live or only locked | §15.6, §13 |
| NFR-27 | Learning capture | No slice is Done until `## Dev Learnings` and `## QA Learnings` are updated | §0.7 |

---

## Prioritization & Scope Cut

### v1 scope-in (as re-baselined by DECISION-1 option B)

1. **Phase-0 spikes** — Gate 16-A + launcher rung, O4 topology ADR, O1 CSP font test, O8 substrate, byte-reproducibility, O31 probe.
2. **Skill scaffold + TypeScript spine** — router SKILL.md, Confirmation Gate, server port, symlink installer, config + snapshot, selftest harness.
3. **Steps 0–3** — warm start with asset-library detection; the full interview; the two-stage prompt generator with font catalog and frozen manifest; the importer with envelope validation, quarantine, repair prompts and Local Regeneration Mode.
4. **Token compiler** — DTCG + forge YAML, flat variable layer, logical-properties lint, machine-owned `tokens.css` + extract-override.
5. **Document model + pure renderer** — doc set, canonical serialisation, determinism hazards designed out, one renderer for surface and LOCK.
6. **Editor core** — three-pane shell, Navigator, inline plaintext editing, image replace + focal point + alt gate, section reorder, undo/redo with transactional grouping, autosave via typed ops, named snapshots, save-as-variation, recovery bin, freeze, duplicate/copy/paste with overrides, per-page SEO, multi-page manager, global regions, preview mode, Design Health HUD.
7. **THE CANVAS (DECISION-1 B)** — gridline overlay, snap engine, smart guides, drag-to-place writing grid integers, span resize, padding/gap handles, keyboard parity, the per-breakpoint override cascade with pre-commit chip and overridden-here dots, and the free-position escape hatch (parent-edge and grid-cell anchors only).
8. **Component bar + deterministic variants** — typed slot contracts, superset-only offers, hover preview, content orphanage, LOCK-blocking placeholders, lazy generation, indistinguishability rule.
9. **Artwork lanes A and B + asset-library pane with filter chips.**
10. **Step 5 regeneration** — more variants, more like this, per-section-note scoped regeneration inline, reviewed direction application with migration report.
11. **Step 6 minimal registry** (table, chart, embed, form) with build-time SVG charts ≤4 mark types and the minimal chart-data field — **both require sign-off**.
12. **LOCK** — re-render, scrub, eight purity gates, the 32-check lock-time list, two-build equality (or the signed-off normalised fallback), snapshots, tag.
13. **Publish + licence/evidence bundle** — automated deploy with runbook fallback.
14. **Security/concurrency/lifecycle, gates + capture, durability + diagnostics, acceptance + demos.**

### v1 scope-out (cuts kept in force)

No rich-text block (v2); no command palette; no rulers/guides beyond the canvas tail; no multi-select/align/distribute beyond the canvas tail; no custom components beyond the whitelist; **no app-shell/commerce/exotic charts**; no version diff, comment pins, share links or real-device preview; no Lane C raster generation (runbook only); **no cross-direction swaps** (only one direction is generated in full); no RTL layout or mirroring (the structural-RTL **question** is asked; RTL layout is not built); no `xl`/wide override tier (1440 is preview-only and carries no overrides); no Content mode (**S7 is not in the v1 bar**); no read-only collaborator preview link; no CRDT; no File System Access API persistence path; no building inside a third-party editor framework; no interactive/client-library charts.

> **Superseded cuts.** §18's v1 cut list "no canvas drag, no gridlines, no snapping, no free-position, no per-breakpoint override authoring" is **rejected by DECISION-1 option B** for the canvas-related lines. All other §18 cuts stand until the user says otherwise.

### Sign-off rows still open before build start

| # | Row | Status |
|---|---|---|
| 1 | Canvas in v1 (gridlines + full constraint dragging) | **RESOLVED** by DECISION-1 option B |
| 2 | Rich-text block is v2 | **Unsigned** |
| 3 | One direction only / no cross-direction swaps | **Unsigned** |
| 4 | Editor still lacks zoom/pan/rulers/multi-select at v1 | **Unsigned** (they are the canvas tail) |
| 5 | Charts partial (build-time SVG, ≤4 marks, two shipped data states) | **Unsigned** |
| 6 | Minimal custom-component registry + chart-data field as a v1 exception to §18's literal cut | **Unsigned** |
| 7 | Automated publish as the v1 commitment (rather than runbook-only) | **Unsigned** |
| 8 | Normalised-comparison fallback if the byte-reproducibility spike fails | **Unsigned, contingent** |
| 9 | Launcher rung F4 (Python shim) or F5 (manual terminal) if F1–F3 fail | **Unsigned, contingent** |
| 10 | Free-position anchors restricted to parent/grid-cell (sibling anchoring deferred) | **Unsigned** — a deviation from the D2 escape-hatch wording |

§18's own precondition is that nothing in v1 may be built until every sign-off row is resolved. **This spec does not ask the user; it records the rows and proceeds under the conservative defaults.**

### Trade-back-out order (if the canvas overruns)

Canvas tail first (zoom/pan → rulers → fraction-stored guides → marquee/multi-select → align/distribute), then free-position escape hatch, then smart-guide distance labels, then padding/gap handles. **Gridlines, snap, drag-to-place, keyboard parity and the override cascade are the irreducible core of DECISION-1 B and are not tradable** — trading them re-creates R47.

---

## Metrics & Analytics

### Product success criteria (the v1 ship bar)

| Id | Criterion | Measurement | Status |
|---|---|---|---|
| **S1** | Interview completes in ≤30 minutes for the common case | Wall clock, instrumented from day one | **At risk** — §5's own honest estimate is 25–35 min fast mode; the ≤30 target sits inside the estimate band, not above it `[I]` |
| **S2** | ≤3 pastes per chunk and ≤6 chunks per generation cycle | Count of ingest invocations per cycle; each extra paste logged as a near-miss | ≤3 is a **retry budget**, not the mechanism; hitting ≤3 on a majority of chunks is a defect against the one-paste protocol |
| **S3** | Zero editor attribute strings in the published tree | Build-failing grep | Binary |
| **S4** | Editor-installed and editor-uninstalled builds are byte-identical | Sorted-path + SHA-256 manifest comparison | **Contingent** on the reproducibility spike; normalised comparison weakens the claim |
| **S5** | The locked site passes all Tier-1 lock gates | Gate-suite exit code | Binary |
| **S6** | The human can name why they chose their direction | `concept.md` + `direction-tour-log.json` record the stated reason per heat | Qualitative |
| **S7** | A content-only edit six months later needs no dev server | — | **Deferred to v2 with Content mode. A v1 sign-off checklist containing S7 unqualified is invalid** |
| **S8** | Zero shipped assets or fonts without a recorded licence class | Grep/lint against the evidence bundle, build-failing | Binary |
| **S9** | Repeat use | More than one completed LOCK event attributed to the same ACOS project, counted from **local session files** inside a 90-day window — no telemetry, no backend, nothing leaves the machine | The PRD marks automatic measurement of intent as having no known mitigation |

### Gate metrics (measured, recorded in `gate-report.json`)

Contrast ratio per pairing (WCAG 2 and APCA Lc); target-size violations; axe critical/serious counts; reflow findings at 320/390/768/1280/1440; overflow-x assertions; free-position count per section; overlap-pair count; override count per page and per site; motion-concurrency count per cost class; distinct motion-kind count; LCP/CLS/INP and pre-LCP transfer; published JS byte size; screenshot-diff pixel delta; dangling asset references; licence-class coverage; unresolved reference count; canonical-serialisation diff; two-build manifest equality.

### Agent performance metrics (defined, not computed — §0.5)

- **SPD — Story Points Delivered.** A qualitative approximation of delivered slice weight per agent per run. Recorded per slice in the evidence bundle.
- **QAP — Quality-Adjusted Productivity.** `QAP = (Delivered_Value * Quality_Score) / (1 + Rejection_Count)` where `Rejection_Count` is the number of QA rejections that slice absorbed.
- **TER — Token Efficiency Ratio.** Artifacts produced per 1K tokens consumed; and artifact volume per unit cost where cost information exists.
- **UAPS — Universal Agent Performance Score.** `UAPS = 0.3*Quality + 0.4*Efficiency + 0.3*CostEffectiveness`.

**Instrumentation plan.** Agent identity is already logged by ACOS to `.acos/metrics/agent-completions.log` (agent_type / agent_id); the formulas, their inputs and their per-slice recording locations live in `AGENT-METRICS.md` at the feature root. **This spec defines the formulas and the logging locations; it computes nothing.**

### Analytics posture

There is **no product telemetry**. Every metric above is derived from local session files, the gate report and the evidence bundle. NG3 (no backend) is what makes this non-negotiable, and S9's measurement design is the direct consequence.

---

## UX & Content

### The interview (Step 1)

Waves of 5–8 questions with a visible shrinking progress count; visual tasks alternate with verbal ones; strategy before taste, visual before taste within taste, constraints and admin last — with the deliberate exception that the time-budget and variant-count policy questions are promoted into Wave 0, because a policy input asked after the questions it prunes has no effect on them. Every Tier-1 question offers a visible "I don't know / surprise me" affordance that records a **stated concrete default**, never a null. Tier-3 items are presented **pre-filled with a "change this" affordance**, never asked open-ended, and in fast mode are bundled into a single end-of-interview review screen.

The interview is also the **Confirmation Gate artifact**: Phase 0 restates the understood brief and waits for an explicit yes before anything is written.

### Direction selection (Step 4a)

A **bracketed tournament**, never an N-up grid: 3 shown → pick → 3 shown → pick → head-to-head final. Never more than 3 full-size renders side by side. Roughly 6 of ~10 directions are surfaced by default with a "see more" path to the rest — this respects the working-memory ceiling while honouring D1's count. Thumbnail grids systematically favour loud, high-contrast directions over subtle editorial ones, which is why the grid is rejected. **Every round writes the directions shown, the order shown, the pick and the user's stated reason to the tour log as it happens** — never reconstructed afterwards.

### The editor surface (Step 4c)

Three panes: Navigator/layers on one side, canvas with an out-of-iframe overlay in the middle, inspector and component bar on the other. The breakpoint indicator is **structurally prominent chrome**, not a dropdown the user can forget they set. Every breakpoint-scoped edit raises a **pre-commit chip** naming exactly which sizes it affects, with one-click "apply to all sizes instead". Every overridden property shows an "overridden here" dot with a one-click reset. Padding and gap handles always display a **token name**, never a pixel value. Span resize shows "6 of 12 · 50%" so the user learns the fluid consequence rather than memorising a number.

**Ambient badges beat blocking dialogs during editing; hard gates belong only at LOCK.** Tier-2 findings surface only through the Design Health pill — never a toast stream. Tier-0 findings (contrast below the floor on placed text, a target below 24px with no valid exception, a missing alt/decorative choice, a duplicate ARIA id) block the individual placement inline and immediately.

### Content and copy rules

- Inline editing is `plaintext-only` on ~90% of text nodes, so source-app markup cannot survive into an award-grade type system.
- Slot content the target variant cannot hold is **parked visibly, never deleted**, and auto-restored if a later swap re-introduces the slot.
- Newly created empty slots are **visibly flagged placeholders that block LOCK** — this is the mechanism that prevents fake statistics shipping.
- The element-level freeze verb is **"Freeze"**, never "Lock": LOCK is the terminal publish verb and two lock concepts sharing vocabulary is a real confusion risk. The constraint is settled; only the word is cosmetic.
- Charts previewed in loading or error states are labelled **"Preview only — not shown to visitors"**, because on a static build those states can never occur for a visitor.
- The evidence bundle says **"Automated accessibility gates passed: N. Manual and screen-reader review not performed."** It never says compliant, conformant or certified.
- Generated files carry a machine-readable banner naming the file to edit instead.
- Warnings never block on aesthetic grounds. The system may warn about a stale or low-confidence pick; it may not refuse it.

### Accessibility of the tool itself

The editor is a dragging interface, so **the editor's own UI must satisfy WCAG 2.5.7**: select-then-click-destination, arrow-key nudge over grid cells, `+`/`−` span steppers, and a "move to: left of X / above Y" menu. Editor chrome must satisfy **2.5.8** (24×24 CSS px, four exceptions), checked live on render — thin drag handles, tiny corner grips and dense icon rows violate this by default.

---

## Rollout Plan

Vertical slices only: every slice produces a working, demo-able increment. No slice delivers only a schema or only a stub.

### Phase 0 — Diagnostics (blocking)

The spike suite. Gate 16-A first; nothing server-dependent is committed until it passes. Outputs: the launcher rung decision, the topology ADR, the CSP font answer, the substrate answer, the reproducibility answer, and the `Task`-availability answer. **If F1–F3 all fail and both F4 and F5 are refused, there is no known mitigation and the browser-editor premise must be rescoped** — this is the single sequencing rule of the whole plan.

### Phase 1 — Generative pipeline

Skill scaffold and the TypeScript spine (server port first), warm start, interview, prompt generator, importer, token compiler, document model and pure renderer.

> **DEMO 1 — interview → prompt → ingest → one direction rendered as a static page.** Demonstrates that a conversation becomes a real, coherent, licence-clean design system and a page a human can look at.

### Phase 2 — Editor core

Editor shell, Navigator, inline editing, image handling, reorder, undo with transactional grouping, autosave over typed ops, recovery bin, freeze, multi-page, global regions, SEO fields, Design Health HUD — with the security posture, one-writer enforcement and the file-ownership guard landing **with** the first live editor, not after it.

> **DEMO 2 — a live editable surface (inline text, reorder, variant swap, autosave) proven to survive at least two turn boundaries.** The proof is a curl in a separate tool call after each boundary, not a same-turn 200.

### Phase 3 — The canvas (DECISION-1 option B)

Sub-sliced in dependency order: gridline overlay → snap engine → drag-to-place writing grid integers → span/padding/gap handles → keyboard parity → override cascade with the pre-commit chip → free-position escape hatch. Zoom/pan, rulers, guides and multi-select are the tail.

> **DEMO 3 — gridlines + constraint drag + per-breakpoint overrides + the free-position escape hatch.** This is D2's first real exercise and the moment R8 is either survived or diagnosed.

### Phase 4 — Variants, artwork, regeneration, custom components

Component bar and deterministic variants; artwork lanes A and B with the asset-library pane and its filter chips; Step-5 regeneration with the migration report; the minimal Step-6 registry with build-time SVG charts.

### Phase 5 — LOCK, publish, evidence

Gate suite and capture at pinned device heights; LOCK with the eight purity gates and two-build equality; publish; the licence-and-evidence bundle.

> **DEMO 4 — LOCK with two-build byte-equality, published, evidence-complete.** The bundle is the deliverable, not a by-product.

### Phase 6 — Durability, acceptance, learning

Resume across a context reset and an eternity `/clear`; verify and doctor; the gotchas reference; the acceptance-criteria sweep; selftest at 100% of assertions; demo evidence; metrics scaffolding; Dev and QA learnings recorded on every slice.

### Schedule posture

Every figure carried from §18 and §17-R18 is **`[I]` inference, not measurement**: L1 interview+prompt 2–4 days; L2 ingest/tokens/variants 8–12; L3a editor-lite 8–12; L3b editor-full **30–60 days "and it never feels finished"**; L4 lock/export/publish/evidence 3–5; L5 custom components ~5 per family. DECISION-1 option B pulls L3b into v1, adding roughly +16–24 days and putting the revised v1 baseline at roughly 25–35 days **against a baseline that is itself stale**. §18's timeline, its v1 scope-in list and §13's gate budgets must all be re-baselined; no figure in this paragraph is a measurement and none should be quoted as one.

---

## Risks & Mitigations

| # | Risk | Severity | Mitigation | Residual |
|---|---|---|---|---|
| R1 | Artwork is structurally undeliverable from the claude.ai leg (no raster generation), so a 20-artwork ask returns 20 flat geometric SVGs in the exact AI-slop register | Critical | Three honestly-labelled lanes: A code-drawn, B asset ingestion, C external with its own licence manifest. Never imply a single paste produces site art; warn at interview time when no asset library exists | **No known mitigation that preserves the paste-only path** |
| R2 | Directions are selected in a preview that cannot render their typefaces, so the user picks a look they have never seen | Critical | Mandate base64 `data:font/woff2` @font-face for the display face, subset to the preview glyph set, supplied by the skill's catalog; verify the CSP behaviour in a 60-second test **before** writing the Step-2 prompt spec | Assumed blocking until O1 runs |
| R3 | Silent truncation produces valid, wrong CSS — tokens cut at 40 of 62 properties are accepted with no error anywhere | Critical | Envelope with per-run random terminator, per-file line counts, sha256 prefixes, smallest-first ordering, hard ingest refusal, quarantine | Low once implemented |
| R4 | If the DOM is the source of truth this is a 2003 WYSIWYG, and worse because Claude also writes the source | Critical | Doc as the only source of truth; pure render; zero DOM serialisation; zero DOM injection for hit-testing | Structural once enforced |
| R5 | Long-running local servers die at the harness turn boundary; the editor's entire premise is a long-running local server, and the failure appears intermittent | Critical | Gate 16-A plus the F1→F5 ladder, run first | **The TS equivalent is UNPROVEN.** If F1–F3 fail and F4/F5 are refused, the premise must be rescoped |
| R6 | Two writers, no lock, silent work loss — near-certain, because the design encourages alternating between talking and dragging | Critical | One writer + hash-journal reconciliation (authoritative) + optimistic concurrency with 409 + defence-in-depth guards with stated limits + op log and atomic writes | Reconciliation holds regardless of how the write happened |
| R7 | The hand-carry costs 45–90 minutes per cycle and Step 5 makes it a loop — the most likely quiet death of the product | High | Bounded-paste protocol, `pbpaste` ingest, and Local Regeneration Mode making the web hop optional | Real; threatens S9 |
| R8 | Constraint dragging is the experiment the market ran, and the constraint editor is the one that died | High | Exactly three verbs; a persistent pre-commit chip with one-click apply-to-all; overrides dots and a panel making invisible overrides visible; keyboard parity | Demo 3 is the test |
| R9 | Free position does not degrade gracefully: it collapses parents and bakes in the authoring viewport | High, partial | Anchored offset, reserved `min-block-size`, per-breakpoint, authored `flowFallback`, auto-demote, visible counter, hard LOCK gate | **For art whose composition depends on absolute cross-viewport relationships the only answer is one component with internal responsive rules — i.e. the user cannot drag its parts individually. No better answer exists** |
| R10–R13 | Cross-direction swaps have no good implementation; component swaps silently destroy hand-written copy; Python-gravity fights the language rule; multi-viewport edit ambiguity is genuinely hard | High | Swaps out of v1 with the coherence-debt design ready for v2; typed slot contracts + content orphanage + LOCK-blocking placeholders; port the server to TypeScript first; desktop-down cascade with sparse overrides | R13 partially mitigable only |
| R14 | Editor runtime fights site runtime, so motion FEEL cannot be judged while editing | High | Disable motion in edit mode; judge in preview | **No known mitigation.** Human-in-the-loop does not solve it; it relocates it |
| R15–R17 | Generation determinism is load-bearing and fragile; localhost is not a trust boundary; Step 3 is an unauthenticated code-import channel | High | Six determinism hazards designed out and verify run at start/lock/CI; six security controls; validating importer with quarantine and an AST walk for forbidden APIs | A false-positive verify kills the guarantee silently — that is the risk to watch |
| R18 | Scope: this is four products and the third one is a full visual builder | High | Phase gating, demo checkpoints, an explicit trade-back-out order, and the canvas sub-sliced | **DECISION-1 B front-loads the highest-risk unproven mechanic; all effort figures are inference** |
| R19–R23 | Editor/export divergence without a screenshot-diff gate; month-six rot; the interview is where time is spent worst; undo fractures across AI bulk mutations; third-party marks will be invented by a generator | High | Purity gate 4 (screenshot diff); git init + provenance + banners + doctor; instrumented interview with fast mode; single command stack with transactional grouping; `[3P]` items are deterministic embeds used as supplied | Trademark exposure is legal, not aesthetic |
| R24–R35 | Charts break coherence by construction; no layers panel would be fatal; warm start homogenises the portfolio; the editor caps the quality ceiling below what the interview promises; ten directions without forced divergence regress to the mean; eager variant generation stalls Step 4; ~800 custom properties re-evaluated per drag; motion variants are the least verifiable inventory; two components are legally shaped not aesthetically shaped; undifferentiated variants reproduce the jam study; 20 artworks exceed the safe presentation ceiling without filter chips; the app-shell tail can colonise the interview and the budget | Medium | Dataviz sub-tokens derived from the direction's anchors and validated colourblind-safe; Navigator mandatory in v1; system/identity split with negative constraints; calibrate the promise to "bespoke, coherent, hand-adjustable" and ship the custom code block plus one signature-moment slot; forced-divergence axis assignment; lazy generation; flat variable layer per direction change; human judgement plus deterministic motion lint; consent-banner reject-parity as a hard gate; the 200×120px indistinguishability rule; direction-affinity filter chips; site-type gating with app-shell deferred to v3 | R27's ceiling argument rests on U15 |
| R36–R46 | Pasted source-app markup survives LOCK; skill duplication drift; two servers means two things to forget to shut down; spring tokens are outside the token standard; scroll-driven animations lack universal support; deploy is a second manual boundary; the prior swarm architecture is seductive; Step-3 output is non-deterministic and the model drifts; transformed art containers trap dropdowns; a user can make a bad pick; a usage-tier surprise | Medium | `plaintext-only`; symlink installer; idle shutdown; agree one spring extension shape or degrade to no motion; test the fallback rather than assuming it; automated publish with a runbook fallback; **do not port the judge loop under any circumstances**; **persist the RESULT as the artifact of record — the prompt is a lottery ticket, not a build artifact**; z-index ladder per section with `isolation: isolate`; warn but never block; surface the cost up front | R44 is a discipline requirement, not a code change |
| R47 | Under §18's original plan v1 would ship without exercising D2 at all | — | **RETIRED by DECISION-1 option B** | Replaced by the front-loading objection: the highest-risk mechanic now runs before the pipeline around it is proven, which is why Gate 16-A and the Phase-0 spikes must precede canvas work |
| SCHEDULE | §18's timeline, v1 scope-in list and §13's gate budgets were written against editor-lite and are stale | High | Re-baseline explicitly and tag every resulting figure as inference | Unresolved until re-baselined |
| COMPONENT-SET | The v1 component set volume is contested three ways | High | See NA-02; adopt §8.3's computed figures as the volume of record and treat 87/674 as a v1 cut candidate | **Open** |
| BUILD-REPRO | No consulted source establishes bundler byte reproducibility | High | Phase-0 spike; documented normalised fallback | Fallback weakens D3 and needs sign-off |
| SIBLING-ANCHOR | The subgrid-promotion compile strategy behind sibling-anchored free positioning is unprototyped | Medium | Parent/grid-cell anchors only in v1 | **No known mitigation beyond the idea as stated** |
| ID-COLLISION | The PRD reuses open-question ids across sections | Medium | Disambiguate every id by section; recommend a renumbering pass | See NA-08 — the collision set is larger than previously recorded |

---

## Dependencies & Stakeholders

### Stakeholders

| Role | Who | Decision rights |
|---|---|---|
| Product owner / sole aesthetic judge / LOCK authority | The ACOS owner (U-1) | Every sign-off row; the launcher-rung deviation; the normalised-comparison fallback; direction selection; LOCK |
| Executing agents | ACOS architect / developer / reviewers under hook enforcement | Slice execution, evidence bundles, zero-trust verification |
| Downstream consumer | `/acos-execute-slice` and the bridge step | Consumes task DoDs as `slice.yaml` acceptance criteria + verification methods |

### External dependencies

| Dependency | Why | Risk if absent |
|---|---|---|
| claude.ai on the web + the user's subscription | The hand-carry leg where the design system is generated | Mitigated but not removed by Local Regeneration Mode |
| macOS `pbpaste`; Bun; Node | Clipboard ingest and the TypeScript runtime | Hard dependency for the paste path |
| Google Chrome (headless CLI) | Screenshot capture with zero npm dependencies | The evidence bundle loses its screenshots |
| The preview substrate | Open (O8) — nothing may hard-depend on one framework | Invariant I6 exists precisely for this |
| dnd-kit (MIT) | Pointer + keyboard sensors and collision detection **only**, never the layout model | Replaceable |
| A rich-text engine (MIT) | The v2 long-form block only | v2 only |
| A static deploy target + a stored scoped token | Automated publish | Falls back to an emitted runbook, which does **not** satisfy the "locked, published" criterion |
| Font sources and licence metadata | `font-catalog.json` with pre-subsetted base64 cuts | Directions cannot be judged (R2) and S8 cannot be met |
| An asset library, where one exists | Decides whether the artwork category is real or theatre | Lane A only; warn at interview time |
| The ACOS framework | Skill runtime and precedence, the PreToolUse hook chain (Oracle at threshold 9, fail-open), evidence bundles, the design-library warm-start store, session cleanup scoped to `.acos/state/`, and the eternity protocol's `/clear` behaviour | Structural |

### In-estate patterns adopted rather than rebuilt

The image-builder server contract (ported to TypeScript); type-forge's browser-edits-as-JSON → deterministic compiler → licence-enforcing finalizer; the SSE + JSONL-inbox + zero-token `tail -f` pattern from three existing servers; the screenshot capture recipe and the HTML-to-PDF wait recipe; design-system-forge's schema, QA framework and motion-interaction extension; reverse-cleanroom's TypeScript script layout, selftest bar, session dir + ACTIVE marker + config snapshot and dynamically-registered TypeScript hook; the Wigum exit-code contract re-expressed as structured gate verdicts; axiom-synthesis's frontier-recomputed-from-disk principle; design-variants' 3-up comparison. **Built new:** the site model and renderer, the editor runtime, the importer, the variant generator, the LOCK compiler, the evidence bundler, the symlink installer.

### Prohibited dependencies

The VLM judge loop and autonomous aesthetic iteration; new files in `.claude/agents/`; building inside GrapesJS / Craft.js / Plasmic / Builder.io / Puck; dnd-kit as the layout model; a chart runtime in v1; CRDTs; the File System Access API as the persistence path; Puppeteer via an evictable cache; Rust (nothing here is performance-critical); any new Python outside the sign-off-gated F4 rung.

---

## Open Questions

Every item below was already resolved to a conservative default during normalization or during this pass. **They are recorded, not re-decided.** Ids OQ-01…OQ-42 carry the normalized set; NA-01…NA-20 are new assumptions this pass was forced to make against the source PRD.

### Carried forward (defaults already adopted)

| Id | Question | Adopted default |
|---|---|---|
| OQ-01 | v1 component set — 87 items / 674 variants vs the ~50 / ~430 the timeline and gate budgets were sized against | Re-baseline to 87/674, then demote per project only what the interview says the project does not need. **Radio group and Toggle switch are non-demotable.** The most load-bearing open item after DECISION 1; the "pairs with option C" note is moot because option B was chosen. **Superseded in volume by NA-02** |
| OQ-02 | "20 artworks" — total or per style family | 20 total per direction for v1, stating plainly that a game-style site (231 sprites in the exemplar) needs a different artwork path (item 13) |
| OQ-03 | Multi-page in v1 vs single page | **Branch A+**: single page, but the doc carries a `pages[]` array of length 1 and every op is page-scoped from day one (~+0.5 day), so multi-page becomes a v2 feature addition rather than a v2 data migration. **Needs clarification:** the recommendation labels A+ but its prose argues for multi-page global regions, which is Branch B behaviour. The label was followed, not the prose. If B was intended, v1 effort roughly doubles and per-page variant divergence must also be answered in v1 |
| OQ-04 | Is two-build byte reproducibility achievable | Run the Phase-0 spike first; if it fails, accept normalised comparison and say so explicitly rather than claiming a guarantee the toolchain cannot give. S4 is written against the spike's outcome |
| OQ-05 | Does sibling-anchored free positioning ship at all | Parent-edge and grid-cell anchors only in v1; sibling anchoring behind an unprototyped subgrid-promotion prototype |
| OQ-06 | Step-5 regeneration — silent apply or reviewed | Reviewed: per-node flag, LOCK blocked until acknowledged, bulk-acknowledge available. Flagged because the vision may have assumed a new direction simply applies |
| OQ-07 | Is there a wide/xl override tier in v1 | **No** — it would introduce the only upward override in an otherwise desktop-down cascade |
| OQ-08 | Should 1440 be a fifth live-switcher option | Yes, **preview-only**, carrying no overrides, which keeps OQ-07 intact |
| OQ-09 | How many typefaces seed the font catalog | 24–32 OFL families curated by role, a starting number to revise after the first real run |
| OQ-10 | Motion-concurrency caps — carry over or benchmark | Ship the carried-over caps as **provisional** and benchmark against this product's own render stack during v1 |
| OQ-11 | Who authors the variant-axis schema | Hand-authored in the skill for determinism, **plus** an explicit effort line the timeline does not currently carry |
| OQ-12 | Raster artwork when the project has no asset library | Accept as a per-project limitation and warn at interview time, before generating a system the pipeline cannot fully deliver. **No known mitigation preserves the paste-only path** |
| OQ-13 | Confirm the reconstruction of two design-system categories | Treat those subsections as a **reconstruction, not a recovery**: any requirement derived from them is provisional and flagged for human confirmation |
| OQ-14 | How is S9 measured | Completed LOCK events in local session files against the same ACOS project inside a 90-day window. No telemetry, no backend, nothing leaves the machine |
| OQ-15 | Should the interview ask about the audience's access needs | Ask it, and let the answer only ever **TIGHTEN** a gate threshold, never loosen one |
| OQ-16 | Single-origin proxy vs two-origin iframe + postMessage | Build only invariants I1–I6 and run the defined spike before locking anything; record an ADR that updates the architecture section and the open-question register together. Candidate A is documented so the spike has something concrete to test; it is **not** the architecture of record |
| OQ-17 | Does a pure-TypeScript detached spawn survive the turn boundary | Run Gate 16-A **first** and take the first passing rung, preferring F3 because it keeps 100% of the server in TypeScript. If every pure-TS rung fails, F4 or F5 each require explicit sign-off. **If both are refused there is no known mitigation** |
| OQ-18 | Does a claude.ai artifact render a web font or silently fall back | Assume it **blocks**, therefore mandate pre-subsetted base64 `data:font/woff2`; run the 60-second test before writing the Step-2 prompt spec |
| OQ-19 | Which build substrate | Substrate-agnostic construction (invariant I6); nothing may hard-depend on one framework. The user's own estate ships plain generated HTML |
| OQ-20 | Does omitting `Task` from `allowed-tools` suppress a later `Task` call | Design v1 so **nothing depends on it**: both role prompts execute inline in the main session using already-declared tools. Probe before v2 planning |
| OQ-21 | The real claude.ai output ceilings | Unknown; the figures found in 2026 SEO "guide" content were unverifiable with at least one fabricated model name. Compute chunking from measured artifact sizes at runtime and surface the usage-tier cost up front |
| OQ-22 | Is LOCK a re-render or a copy-and-strip | **Re-render**, against the first-party precedent of copy-and-strip which already required hand-rewriting links and hand-excluding dev pages. Described as the single most consequential architectural decision in the eight steps; **A49–A59 are all written assuming re-render** |
| OQ-23 | Charts: build-time SVG or a client library | Build-time SVG with ≤4 mark types in v1, keeping the performance gate free of a chart runtime |
| OQ-24 | Does "regenerate this section" hand-carry back out | No — inline, via Local Regeneration Mode, so the middle gear is synchronous |
| OQ-25 | Does Step-5 redesign fork or replace in place | Fork; save-as-variation is v1 |
| OQ-26 | Should agent ops go through the inbox even when the editor is not running | **Inbox always**, to avoid two write paths and two validation paths |
| OQ-27 | Two browser tabs on one session | Tab claim over SSE with the second tab read-only, since the process lock covers processes and not tabs |
| OQ-28 | Ownership of the compiled token stylesheet | Machine-owned plus a sanctioned extract-override hand-tune path |
| OQ-29 | What goes into a lock snapshot | Documents and the system lock only; the built tree is reproducible and is excluded to bound growth |
| OQ-30 | Accessibility floor and the WCAG-2-vs-APCA disagreement | AA as the contractual floor, WCAG 2 as the pass/fail gate, APCA advisory; selected AAA items are aspiration, not gates |
| OQ-31 | Final UI wording for element-level freeze | **"Freeze"**. The constraint is settled (it must never be "Lock"); only the word is cosmetic |
| OQ-32 | Is Step-8 deploy automation a guarantee | Runbook fallback unless a deploy target and stored scoped token are already configured. **Superseded in emphasis by NA-09**, which records that the publish section commits automated publish as the v1 behaviour with the runbook as an explicit fallback trigger |
| OQ-33 | Is the phased-delivery timeline stale | Yes — written against editor-lite. Re-baseline; the canvas epic is v1 scope; R47 is retired; every resulting figure is inference |
| OQ-34 | Which v1 scope cuts survive DECISION 1 | The canvas-related cuts are superseded; all other cuts remain in force until the user says otherwise |
| OQ-35 | The v1 sign-off table | DECISION 1 resolves the canvas rows and consequentially one more; rich-text-is-v2, one-direction-only, editor-lacks-zoom/pan/rulers/multi-select, and charts-partial **remain unsigned** |
| OQ-36 | Open-question ID collisions | Always disambiguate by section; recommend a renumbering pass. **Enlarged by NA-08** |
| OQ-37 | S2's "one-paste protocol" naming vs its ≤3 budget | Treat ≤3 as a pass with each extra paste logged as a near-miss; hitting ≤3 on a majority of chunks is a defect. Rename the mechanism or state the retry semantics explicitly |
| OQ-38 | The "62 app-shell items" figure | Approximate, carried from the tally, pending a real audit |
| OQ-39 | The ACOS vision document referenced by the session hook | Not consulted; the signed-off PRD, DECISIONS.md and the settled decisions are the authoritative product input |
| OQ-40 | Which PRD sections the normalization pass read | §1–§4, §16, §17, §18 plus DECISIONS.md in full. **This pass additionally read §5 (head), §6 (head), §7 (head), §8 (head), §9 (head), §10.1–§10.6, §11 in full, §12.1–§12.9, §13 in full, §14 in full, §15 in full, §19 in full, §20 in full.** Anything not on a read page is not asserted here |
| OQ-41 | Effort, count and schedule figures throughout | Preserve `[V]`/`[I]`/`[U]` markers; tag every schedule figure as inference with low confidence |
| OQ-42 | Was the target feature directory empty at compile time | Yes — treated as a clean start, not a resume |

### New assumptions recorded this pass

| Id | Finding | Adopted default |
|---|---|---|
| **NA-01** | **The interview bank is 90 questions `[V — §5 row-count self-audit]`, not 78.** Fast mode asks ~45–55 Tier-1 questions plus one bundled review screen, taking ~25–35 minutes; open-ended mode is ~45–70 minutes. §17-R21 ("78 questions, 40–80 minutes"), §18's v1 scope line and acceptance criterion A3 ("≤45 answered") all carry the old numbers, and §5 states plainly that A3 should be revised to ≤55 **or the bank must be cut further** | Adopt 90 / 45–55 / 25–35 min as the working figures; keep A3 as written but record it as unachievable-as-stated; require cross-section reconciliation. All timing is `[I]` |
| **NA-02** | **The component inventory computes to 216 rows / 1,228 variants `[V — §8.2, computed from §8.3 as written]`** (21 Tier A / 33 B1 / 111 B2 / 38 B3 / 4 C / 9 policy rows; 207 `pick`, 2 `computed`, 7 `n-a`), and §8 states explicitly that Tier B was understated roughly two-fold and that **this is a real scope increase, not a re-labelling**. This is a third, larger figure than either 87/674 (DECISIONS item 2) or ~50/~430 (what §18 and §13 were sized against) | Treat **216/1,228 as the inventory volume of record**, 87/674 as the v1 cut candidate, and ~50/~430 as stale. The v1 cut list must be regenerated mechanically from the priority column, not asserted. This is now the largest open scope discrepancy in the product |
| **NA-03** | **There are EIGHT LOCK purity gates, not five `[V — §12.5]`.** Gates 6 (zero unresolved references), 7 (zero design-time origins), 8 (verify clean at lock time) were added, and §12.5 records the consequential edits it cannot make itself: the lock-time checklist row must read "gates 1–8", the editor section's "four automated gates" note must read eight, and the phase plan's "all five purity gates" bullet must read eight | Adopt eight everywhere in this pipeline's artifacts |
| **NA-04** | **The lock-time checklist is 32 checks `[V — §13.4]`** — 28 base gates plus lettered insertions 4a (motion-concurrency caps), 11a (skip-link presence and first-tab-order, a Level A gap), 13a (pause/stop/hide affordance, Level A), 23a (asset-reference resolution) | Adopt 32; carry the three cross-section coordination items 11a/13a/21 name (skip-link component entry, `pauseAffordanceRef` field, font-fallback-metrics token family) as build prerequisites |
| **NA-05** | The coherence-lint count is unstable across sections: the lock-time checklist says "six coherence lints", the carried constraint says seven (adding logical-properties-only), and §7 records **new lints 7–10** added in its own revision | Treat the coherence lint set as **versioned, not a fixed count**; require by name at minimum: the elevation-model lint (border-only ⇒ zero shadow tokens), the logical-properties-only lint, and §7's lints 7–10 validating direction-bound authored artefacts against the identity vector |
| **NA-06** | **Free-position auto-demotion boundary contradiction.** §11.4 rule 4 revises the demotion boundary **down to ≤390px**, arguing 479 is a width no switcher, iframe or gate ever renders; §12.3 defines the small breakpoint key as `max-width: 479px` and calls it "identical to the ≤479px auto-demote boundary in §11.4 rule 4" | Adopt **≤390px as the demotion trigger** (it is the only small width a user can preview before it fires) and keep the small media-query boundary at 479 unless the user prefers boundaries to equal preview widths — in which case all four call sites change together. Recorded as a required cross-section fix |
| **NA-07** | **The canonical scene-graph filename is `pages/<id>.doc.json` + `site.json`, not `layout.json` `[V — §12.2 file set, §12.13 write allowlist]`.** §4, §11, §12.6 and §12.10 still say `layout.json`, as do the technical requirements carried into this pipeline | Adopt the doc-set naming; treat `layout.json` as a legacy alias; require the rename before implementation |
| **NA-08** | **The open-question ID collision set is larger than recorded.** Beyond O31 (mid-skill `Task` vs the branch choice) and O32 (launcher ladder vs no-asset-library raster): **§12.3 uses O31 for the breakpoint-boundary-vs-preview-width reconciliation and O32 for the wide/xl tier decision**; **§12.5 uses O33 for bundler byte reproducibility while §17/§18 use O33 for the freeze wording**; **§12.7 uses O34 for uid separation while §7.0.3 uses O34 for the direction-identity-larger-than-hash residual** | Cite every open-question id **as `§<section>-O<n>`**, never bare. A renumbering pass is a prerequisite for trustworthy traceability |
| **NA-09** | **Publish: §15.4 commits automated deploy as v1 behaviour**, with the runbook as an explicit fallback trigger that **does not satisfy the "locked, published" exit criterion** — and states that this commitment is an interpretation requiring user sign-off. The normalized default was runbook-first | Adopt §15.4's resolution (FR-210/FR-211) and carry the sign-off row |
| **NA-10** | §14.5's agent-authored custom-component path names a subagent call, which conflicts with the architecture rule that nothing may depend on unverified mid-skill subagent availability | Adopt inline main-session execution of the role prompt; treat subagent forking as a later context-economy optimisation only |
| **NA-11** | §12.5's gate-2 procedure is written against an npm/Node install and a committed publish manifest pair, while the skill's own code is Bun TypeScript | Adopt: skill code is Bun TypeScript; the **site build toolchain is whatever the substrate spike selects**, and gate 2's installer invocation and publish-manifest filenames must be re-derived from that outcome rather than copied verbatim |
| **NA-12** | The editor feature table is **116 rows — 56 v1 / 55 v2 / 5 v3 — under editor-lite `[V — §10, mechanically recounted]`**, and its own prose notes the pre-reconciliation draft's "~35 of ~95" claim was off by roughly 2× on the v1 count | DECISION-1 B promotes the canvas rows (real-grid overlay, snap engine, smart guides, align tools, padding/gap handles, drag-to-place, span resize, keyboard nudge, the full cascade UI and the free-position hatch) into v1, putting v1 at roughly **65–70 rows** `[I — arithmetic on the promoted rows, not a recount]` |
| **NA-13** | §13.1 states a **LOCK wall-clock budget of p50 ≤90s / p95 ≤180s** for a representative 5-page site, explicitly an inference, with a sampling fallback for the performance gate that is itself unverified at scale | Carry as NFR-02 with low confidence; validate against a real prototype before treating it as an SLA |
| **NA-14** | §12.7's override-accumulation thresholds (≥5 / ≥15 / ≥40 / ≥25%) are explicitly stated starting numbers, not measured | Carry as NFR-24, tunable in the project record |
| **NA-15** | §13.8's motion-kind homogeneity trigger ("3 or more distinct variants of the same kind") is a carried-over default, not validated against user testing | Carry as a Tier-2 advisory threshold, revisable once real usage data exists |
| **NA-16** | §13.4 gate 20 is declared **the canonical performance threshold statement**, and records that acceptance criteria A66 (omits INP) and A67 (flat ≤2MB vs the ≤1.5–2MB range) are inconsistent with it | Adopt gate 20's numbers as canonical (NFR-04); record the A66/A67 edit as required |
| **NA-17** | §11.2.1 supplies a **normative drop algorithm** — row derivation, span preservation, displace-down occupancy with ghost preview, art/opt-in stacking exceptions, cross-section re-parenting with no auto-compaction, and nine acceptance branches AC1–AC9 — that was not represented in the carried technical requirements | Adopt AC1–AC9 as canvas acceptance criteria (FR-102–FR-106) |
| **NA-18** | §11.3.1 supplies a **normative reading-order invariant** (DOM order is always the intended reading order) plus a per-breakpoint `order` override that is **hard-blocked on focusable nodes** and warned on non-focusable ones, and a numbered mobile stack-order preview before commit — none of which was in the carried requirements | Adopt as FR-114/FR-115 |
| **NA-19** | **Acceptance-criterion id collision:** §12.5 appends "new criteria A91–A99" while the carried config records "A91–A101 added by §18" | Renumber before either set is cited; treat A91+ as unstable ids until reconciled |
| **NA-20** | **§19 as written contains A1–A90 (90 criteria) `[V — read in full]`.** The "96 criteria" figure carried into the normalized config is not supported by the section text | Adopt 90 as the count of record; the additional criteria proposed by §12.5 and §18 are unmerged |

---

## Appendix

### A. Glossary

**Direction** — a complete, internally consistent design system identity: a 24-slot varying identity vector plus 2 invariant records, with everything else derived from it or bound to it. **Variant** — a structurally distinct composition of the same component **within one direction**; size, theme, density, state, icon slot and semantic colour are computed axes and never count against the budget. **Derived value** — computed from the direction vector plus seed tables; carries `pickable: false`; renders no editor control. **Anchor** — a hue, type or spacing seed from which derived values are computed. **Capsule** — a Stage-A lightweight direction proposal with self-audit fields. **Envelope** — the manifest (file list, per-file line counts, sha256 prefixes, per-run terminator) that makes truncation detectable. **Semantic op** — a typed, validated mutation the browser or the Claude session proposes; never a raw patch or a path. **Freeze** — element-level protection against accidental edit; deliberately **not** called "Lock". **LOCK** — the terminal re-render-and-verify step producing the published tree. **UNLOCK** — restarting the design server. **Gate 16-A** — the blocking cross-turn-boundary server-survival probe. **Coherence debt** — recorded off-system values accepted deliberately. **Content orphanage** — the visible parked panel holding copy a swapped-in variant cannot host. **Lane A/B/C** — code-drawn / asset-ingested / externally-generated artwork.

### B. Evidence-marker key

`[V]` verified against a named, fetched or read source. `[I]` inference — a reasoned position with no external source. `[U]` unsourced or explicitly low-confidence. **Every schedule, effort, count-estimate and duration figure in this document is `[I]` unless a `[V]` counted source is named.**

### C. Source map (what was read, at what offset)

| Section | Lines | Read this pass |
|---|---|---|
| 1 summary / 2 goals / 3 users / 4 pipeline | 11–236 | Absorbed during normalization |
| 5 interview bank | 236–509 | Head (delivery rules, tiers, ID grammar, branch roots, Wave 0, Wave 1) |
| 6 design-system prompt | 509–764 | Head (§6.0 template, both dependent artefacts, the answers→slot mapping) |
| 7 design-system inventory | 764–1230 | Head (§7.0 keys, vector membership, the scale reality check) |
| 8 component inventory | 1230–1779 | Head (§8.1 definition, §8.2 tier budget and computed totals, primitives) |
| 9 motion and art containers | 1779–2014 | Head (§9.1 container contract and its seven rules, §9.1.1 axis model) |
| 10 editor feature set | 2014–2246 | §10.1–§10.6 |
| 11 layout and dragging | 2246–2431 | Full |
| 12 document model, persistence, LOCK | 2431–2874 | §12.1–§12.9 |
| 13 quality gates | 2874–3016 | Full |
| 14 regeneration and variants | 3016–3113 | Full |
| 15 warm start, publish, licences | 3113–3188 | Full |
| 16 architecture / 17 risks / 18 phased delivery | 3188–4000 | Absorbed during normalization |
| 19 acceptance criteria | 4000–4132 | Full |
| 20 appendix | 4132–4224 | Full |

**The PRD was never read whole.** Anything not on a read page is not asserted here.

### D. ID-collision register (must be resolved before traceability is trustworthy)

| Colliding id | Meaning A | Meaning B |
|---|---|---|
| O31 | Mid-skill subagent availability (§16.5.1, §16.11) | The branch choice (§18); **and** the breakpoint-boundary-vs-preview-width reconciliation (§12.3) |
| O32 | The launcher-ladder decision (§16.6.3) | The no-asset-library raster question (§18); **and** the wide/xl override tier (§12.3) |
| O33 | Bundler byte reproducibility (§12.5) | Element-freeze UI wording (§17/§18) |
| O34 | Separate-uid enforcement (§12.7) | Direction identity larger than its hash (§7.0.3) |
| A91–A99 | Appended by §12.5 | A91–A101 appended by §18 |
| T1–T10 | Wave-2 taste questions (renamed `TS1`–`TS10` by §5) | Tier labels `[T1]`/`[T2]`/`[T3]` |

### E. Cross-section amendments this spec depends on

The lock-time checklist row for purity gates must read "1–8"; the editor section's automated-gate count must read eight; the phase plan's purity-gate bullet must read eight; A56 must name the system lock alongside the documents; A49 gains the design-time-origins grep; A66 must add INP (or the TBT proxy) and A67 must reconcile to the ≤1.5–2MB range; A3 must move to ≤55 or the bank must be cut; §17-R21 and §18 must adopt the 90-question figure; the skip-link component must be added to the inventory with its variant count; the container contract must gain `pauseAffordanceRef`; the token taxonomy must name font-fallback metrics as a derived family; the free-position anchor schema must be narrowed to the grid-cell form; every `layout.json` reference must become the doc set; and the coherence-lint count must be stated once, in one place.

---

## PRD Summary (One-Page Digest)

**What.** An ACOS skill that turns a conversation into a distinctive, hand-adjustable, publishable static website in eight steps, with the human as the sole aesthetic judge and machines enforcing only machine-checkable correctness.

**Why.** A technically-capable non-designer cannot produce a distinctive site: template pickers give sameness, free canvases demand design vocabulary, and a designer per venture is not viable. The result is ventures that ship undesigned sites or no site at all.

**How.** Warm start → hard-gated interview → two-stage design-system prompt → validated hand-carry ingest (or zero-paste local regeneration) → bracketed direction tournament → a live editable canvas over a real CSS grid → deterministic variants and scoped regeneration → LOCK as a clean re-render → publish with a licence-and-evidence bundle.

**Fixed.** D1 coherence by computation (derived values are never picked). D2 constraint layout with an anchored-offset escape hatch. D3 LOCK is a reversible re-render with provably zero editor runtime. D4 motion is a design-system item in draggable containers. **DECISION-1 option B: v1 ships gridlines and full constraint dragging.**

**Hard architecture.** The document is the only source of truth and the page is a pure render; the DOM is never serialised back. One writer (`wb-server`); the browser proposes typed semantic ops. Logical CSS properties only. Fixed port on loopback with `state.json` re-attach. All new code is TypeScript on Bun. Zero new agent files. The server never calls `Task()`.

**The blocking unknown.** Long-running local servers die at this harness's turn boundary. **Gate 16-A runs first**, and the launcher ladder's last two rungs each require the user's signature. If they are refused, the browser-editor premise must be rescoped.

**The v1 bar.** ≤30-minute interview (at risk — the honest estimate is 25–35), bounded pastes, zero editor strings in the published tree, two-build equality (contingent on a spike), all Tier-1 gates passing, the human able to say why they chose their direction, zero unlicensed shipped assets, and repeat use. **S7 — a content-only edit six months later — is v2 and is not in the bar.**

**The honest limits.** Motion feel cannot be judged while editing (no known mitigation). Raster artwork is undeliverable from the hand-carry leg. Sibling-anchored free positioning is unprototyped. Bundler byte reproducibility is unestablished. Automated accessibility tooling catches ~57% of real issues, so the product never claims conformance — it reports "passed N automated gates" and discloses that manual and screen-reader review were not performed.

**The biggest open number.** The component inventory computes to 216 rows / 1,228 variants against a timeline sized for roughly a quarter of that. Nothing in the schedule is a measurement.
