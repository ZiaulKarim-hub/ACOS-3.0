# Website Builder — Product Requirements Document

**Skill name:** `acos-website-builder`
**Status:** Draft for approval
**Date:** 2026-07-25
**Sources:** 12 independent research lenses + prior swarm report `/Users/zee/Documents/Vibe Coding/ACOS 3.0/.acos/swarm/swarm-20260718-022431/synthesis/report.md`

Throughout this document: **[V]** marks a verified fact with a named source. **[I]** marks inference. **[U]** marks an unsourced claim to be treated as inference. Disagreements between research lenses are footnoted and resolved in §20.

---
## 1. Summary

### What this is

Website Builder is an ACOS skill that turns a conversation into a distinctive, hand-adjustable website. It runs in eight steps:

1. It checks whether you already have a design system or a prior site (warm start).
2. It **interviews you** — about purpose, audience, positioning, taste, accessibility, performance, and constraints.
3. It **writes a prompt** for you to paste into claude.ai on the web, where Claude's design/artifact generation produces a complete design system: typography, colour, motion, artwork, components, and everything else the site needs.
4. You **hand-carry** the result back.
5. It **interviews you again** to select each component, then builds the site as a **live editable design surface** — gridlines you snap to, components you drag, text you edit in place, a component bar for swapping any element for a comparable variant, and a save button.
6. You can ask for **more variants** or a **redesigned system** at any point.
7. You can add **custom components** the standard system doesn't cover (charts, calculators, maps).
8. You say **LOCK** — the design toolbars and gridlines disappear and you get a clean static site with no editor code in it, while the editable version stays beside it. Then it publishes — **automatically if deploy is wired up** (a one-time scoped-token setup, e.g. `wrangler pages deploy`), **or via a stated runbook if it isn't** [see §4 Step 8, which hedges explicitly: "If deploy is not automated in v1, the PRD says so explicitly and emits a runbook" — the same fallback the user's existing FruitSync project already uses]. Either path ends with a licence-and-evidence bundle listing every font and asset. This summary previously implied publish was unconditionally automatic; it does not commit to that — automation of the deploy step is a v1 open question, not a guarantee, and §4 Step 8 is the authoritative statement of which path a given project gets.

The human is the aesthetic judge. There is no AI critic scoring screenshots in a loop. Machines enforce the things machines are good at — contrast ratios, token purity, reflow at 320px, licence completeness, "does the editor runtime actually not ship" — and the human decides everything about how it looks.

### What this is not

- **Not an autonomous site generator.** The prior swarm report designed an award-quality generator that judges its own screenshots and iterates. That architecture is explicitly replaced. Its rubrics, anti-slop lint, stack recommendations, licensing policy, performance gates, and capture protocol are reused; its judge loop is not.
- **Not Webflow.** The pixel canvas is the last thing built, not the first, and the layout model is constraint-based by default (D2), not free x/y.
- **Not a template picker.** Directions are generated per project against the interview answers, not chosen from a fixed gallery.
- **Not a claim of WCAG certification.** Automated accessibility tooling tops out around 57% of real issues [V — Deque Accessibility Coverage Report, 13,000+ pages/page-states]. The evidence bundle will say "passed N automated gates," never "AA compliant."
- **Not a raster art generator.** claude.ai cannot produce bitmap images [V — confirmed by Anthropic, April 2026]. Art comes from code-drawn SVG/CSS/canvas, from an ingested asset library, or from a separately-scoped external generator. See §7.9 and §17-R1.
- **Not award-winning by construction.** A swap-menu builder produces coherent, bespoke, hand-adjustable sites. Award juries recognise assembled output [V — prior swarm report Finding 2]. The one lever that raises the ceiling is the custom code block (§10.7, §14.4), and the PRD says so plainly rather than over-promising.
- **Not a guarantee of one-click automated deploy.** Whether Step 8 ends in a live URL or a manual runbook depends on whether a deploy target and credentials were configured for the project (§4 Step 8). This is an open item requiring a user decision (which host, whether to store a scoped token) rather than a settled default — no known mitigation beyond the runbook fallback exists yet.

---
## 2. Goals, non-goals, and success criteria

### 2.1 Goals

| # | Goal | Why |
|---|---|---|
| G1 | A single human, in one working session, goes from "I need a site" to a locked, publishable site that looks deliberately designed | The whole product |
| G2 | Every visual decision traces to an interview answer or an explicit human pick | Makes the design defensible and re-derivable; operationalises the prior report's concept-gate traceability rule |
| G3 | The design system is coherent by construction — derived values are computed, never picked (D1) | Prevents the clash that ~80 independently-chosen items produces |
| G4 | The site works at 320px and 1440px without the human doing responsive work (D2) | Constraint dragging exists for this reason |
| G5 | LOCK produces a static site with provably zero editor runtime, reversibly (D3) | The export contract |
| G6 | Run N+1 starts warm from run N's reusable assets without inheriting run N's identity | Warm start that doesn't homogenise the user's portfolio |
| G7 | Every font and asset in the shipped site has a recorded licence class | Legal exposure is concentrated here |
| G8 | The tool is used more than twice | The manual hand-carry is the biggest threat to this |

### 2.2 Non-goals

| # | Non-goal | Reason |
|---|---|---|
| NG1 | AI aesthetic judging of any kind | Replaced by the human, per the product brief |
| NG2 | Multi-user real-time collaboration | Single-user product; comment schema is collaboration-ready but no second writer in v1–v3 |
| NG3 | A CMS or backend | Static output; forms use a third-party endpoint or a mailto fallback |
| NG4 | Application-shell UI (dashboards, auth, settings, data tables at scale) | 62 inventory items are app-shell/commerce/exotic-chart [I: figure carried over from the §7/§8 component inventory tally; not independently recounted in this revision pass — treat as approximate until a §7/§8 audit re-confirms the exact count]; gated behind the site-type answer and deferred to v3 |
| NG5 | Raster image generation inside the pipeline | Structurally impossible on the claude.ai leg |
| NG6 | Rewriting existing Python ACOS tooling | Read-only reference; new code is TypeScript per the standing language rule |

### 2.3 Success criteria

Split below into the **v1 ship bar** (every criterion here must pass before v1 is considered done)
and criteria that are legitimately **out of the v1 bar** because the capability they measure is
scoped to a later version elsewhere in this PRD. A criterion never counts as "unmeasured because
it's hard" — it only leaves the v1 bar when another section has already, explicitly, deferred the
underlying feature.

**v1 ship bar**

| # | Criterion | Measurement |
|---|---|---|
| S1 | Interview completes in ≤30 minutes for the common case | Wall-clock, single-language single-surface marketing site, ~35–45 answered questions |
| S2 | Hand-carry completes in ≤3 pastes per chunk, ≤6 chunks total | Count of `pbpaste` ingests per generation cycle. Terminology note: §4 Step 3 names this mechanism the "one-paste protocol," which promises exactly one paste per chunk; this criterion's ≤3 tolerance is the *budget for retries*, not a redefinition of success. A 2nd or 3rd paste within one chunk means a retry happened (e.g. a failed parse or an incomplete clipboard capture) and each such retry should be logged as a near-miss against S2 even though it still counts as a pass at ≤3. Hitting the ≤3 ceiling on a majority of chunks is itself a signal the "one-paste" mechanism in §4 is not working as designed and should be raised as a defect against §4, not just tracked here. §4 should be reconciled to either rename the mechanism (e.g. "bounded-paste protocol") or state this retry semantics explicitly — open as of this revision. |
| S3 | Zero `data-wb-*` strings in `dist/published/**` | Grep assertion, build-failing |
| S4 | Editor-installed build and editor-uninstalled build are byte-identical | `diff -r` of two dist trees |
| S5 | Locked site passes all Tier-1 lock gates (§13.4) | Gate suite exit code |
| S6 | The human can name why they chose their direction | The concept document records it; qualitative |
| S8 | Zero shipped assets or fonts without a recorded licence class | Grep/lint assertion against the evidence bundle (§ evidence-bundle content list — every font-family and asset filename referenced in `dist/published/**` has a matching licence-class entry), build-failing. Closes G7, which previously had no operationalised criterion despite being flagged in its own "Why" column as where legal exposure concentrates. |
| S9 | Repeat use: the same ACOS project shows more than one completed run (warm-start or fresh) within a tracked window | Count of completed LOCK events attributed to the same project identifier. **Open question, no known mitigation yet**: this PRD does not currently specify a telemetry/analytics mechanism, a "project identifier" persistence scheme, or a tracked-window length (the gap suggestion proposed 90 days as an example, not a decision). Until product decides whether any usage telemetry is acceptable for a tool that otherwise has no backend (NG3) and no multi-user tracking (NG2), S9 cannot be measured automatically — it degrades to a qualitative/self-reported proxy (e.g. asking the user in a later session whether this is a repeat run against a warm-started project). Requires user decision on: (a) whether local-only usage logging is in scope at all, (b) the window length, (c) whether this is measured per-machine or per-user. Closes the "G8 has no success criterion" gap by giving it a criterion; does not close the measurement-mechanism gap, which is inherited from the fact that G8 itself was never given an implementation plan elsewhere in the PRD. |

**Deferred to v2 (not part of the v1 ship bar)**

| # | Criterion | Measurement | Deferred because |
|---|---|---|---|
| S7 | A content-only edit six months later requires no dev server | Content mode (§15.5) | §3.3's usage-model table tags Content mode as "(v2)." S7 measures a capability that does not exist in v1, so it cannot be part of the v1 acceptance bar. It remains a real, tracked success criterion for whenever Content mode ships — it is not deleted — but a v1 sign-off checklist that includes S7 unqualified is invalid and should be corrected to check S1–S6 + S8–S9 only. If Content mode is pulled forward into v1 scope (a scope change, not something this section can decide unilaterally), S7 moves back into the v1 ship bar and this row is removed. |

---
## 3. Users and usage model

### 3.1 Primary user

One person — the ACOS owner — building sites for their own projects (FruitSync, OKOA, future ventures). Technically capable, not a trained designer, has strong taste but limited design vocabulary. Owns a Claude subscription with web access. Works on macOS. **[V — established from repo context and the user's own prior work at `/Users/zee/Documents/Vibe Coding/website-design-okoa/`]**

The primary user is the sole *aesthetic judge* in this system (see §3.4): every direction, variant, and layout decision routes through their taste. They are not, however, the only stakeholder this PRD has obligations toward — see §3.2's tertiary class below, which the primary user will never directly interview but for whom the machine still enforces correctness.

### 3.2 Secondary and tertiary users (design for, don't optimise for)

**Secondary — people who touch the editor:**

- A future collaborator reviewing a site before LOCK (read-only preview link, v2).
- The user themselves six months later, making a copy change (content mode, v2).

**Tertiary — the published site's visitors.** *(Added — closes a gap: neither the primary user in §3.1 nor either secondary user above is the person who actually loads the finished, LOCKed website. Every stakeholder named in §3.1–3.2 touches the *editor*; none of them is the audience the *output* is built for.)*

- Never interviewed, never named individually, never given a persona beyond "whoever the ACOS owner is building this site for" (could be OKOA investors, FruitSync players, a future venture's customers — the identity varies per project and is out of scope for this PRD to enumerate).
- They are the reason the machine-enforced correctness gates in §13 (contrast, reflow, keyboard/pointer-alternative dragging, licence attribution, photosensitivity, responsive behaviour) are non-negotiable even though the human is the aesthetic judge and could otherwise wave any of them through. Without a named tertiary class, those gates read as generic compliance boilerplate; with one, they read as this PRD keeping a promise to a real (if unspecified) audience the primary user cannot fully represent on their own — the primary user can tell you a button looks good, not that it is operable for a visitor using a screen reader or a 320px phone.
- **Scope boundary, stated plainly:** this PRD does not run user research, usability testing, or persona work for the tertiary class — that would require a per-project interview the skill does not conduct. Instead it treats the tertiary class as the *justification* for machine correctness rather than a group whose preferences get elicited. This is a deliberate, narrower commitment than full accessibility/UX research, and it is named here so the gap between "gates exist" and "a visitor was actually consulted" is visible rather than implied away.
- **Open question — no known mitigation:** if a given project's tertiary audience has known access needs (e.g., a visually-impaired investor, a specific screen-reader user), nothing in the current interview (§2) surfaces that and routes it into stricter per-project gate thresholds. This PRD does not propose a mechanism for that today; it would need a user decision on whether the Step-1 interview should ask "who is this site for, and do they have access needs you know about?" and, if yes, how that answer tightens §13's gates on a per-project basis.

### 3.3 Usage model

| Mode | Trigger | What happens | Session shape |
|---|---|---|---|
| Cold start | `/acos-website-builder` in a project with no prior site | Full interview → prompt → hand-carry → build → edit → lock | One long session, resumable |
| Warm start | Prior design system detected at Step 0 | "What's changing?" interview (much shorter) → optionally reuse tokens → build | Half a session |
| Return-to-edit | `/acos-website-builder --resume` | Reads `state.json`, recomputes phase from disk, re-attaches to the running server or restarts it | Minutes |
| Content edit | `/acos-website-builder --content` (v2) | Text-only editing path, no dev server, no design layer | Minutes |
| Variant round | User clicks "more variants" in the editor | Deterministic generator produces 5–10 neighbours; no claude.ai hop | Seconds |
| System redesign | User asks for a new/partial design-system prompt | Back to Step 2 with prior parameters as negative constraints | New hand-carry cycle |

None of these six modes is driven by, or informed by, the tertiary visitor class in §3.2 — every trigger and session shape here is authored from the primary/secondary users' actions inside the editor. The tertiary class only enters the system indirectly, via the correctness gates each mode's build/edit/lock step runs against (§13). This is intentional (visitors don't operate the editor) and is noted here so the absence isn't mistaken for an oversight.

### 3.4 The human's role, stated plainly

The human supplies **taste** (which direction, which variant, where things go, what the copy says) and **acceptance** (LOCK). The machine supplies **coherence** (derived tokens, direction hashing, lint), **correctness** (contrast, reflow, licence, export purity), and **labour** (generation, layout, build, publish). The machine never overrides a taste decision; it may refuse to ship a correctness violation.

Restated against §3.2's three-tier user model: the primary and secondary users (§3.2) are who the human's taste judgment serves — they are in the room, they can see the site, they can say "I like this." The tertiary visitor class is who the machine's correctness mandate serves — they are never in the room, so the machine holds the line on their behalf even when no human present would notice or object to a violation (e.g., a contrast ratio that reads fine to the sighted primary user but fails for a low-vision visitor). This is the load-bearing reason "the machine may refuse to ship a correctness violation" is not merely a safety rail on the *product* — it is the only mechanism in this entire usage model that represents the tertiary user's interests at all.

---
## 4. The pipeline — all 8 steps

### Step 0 — Warm start / continuity check

| | |
|---|---|
| **Inputs** | Target project path; glob of `.acos/design-library/*/design-system-spec.yaml`, `.acos/website-builder/systems/*/system.json`, the target project's own `.acos/`, and any asset library (sprite folders, photo folders, existing site trees) |
| **Process** | Scan for prior systems and prior sites. Scan for an **asset library** — this is the binary that decides whether artwork is real or theatre (§17-R1). Detect any existing site to mine for copy/structure. Present findings. Split what's offered into **reusable system assets** (always offered) and **identity** (offered only if the user declares a sibling site). |
| **Outputs** | `session.json` with `{warmStart: none\|system-only\|full, sourceSystemId, assetLibraryPath, minedSources[]}` |
| **Exit criteria** | User has explicitly chosen fresh / reuse-as-is / reuse-and-revise, and the asset-library question is answered |

The split matters. Reusable across projects: token-name schema, component slot contracts, motion-primitive library, font catalog, anti-slop deny-list, editor configuration, user-level interview answers (accessibility posture, device assumptions, decision style). Never reused by default: hue anchors, type pairings, radius/density, motion character, artwork. Prior identities are injected into Step 2 as **negative constraints** unless sibling mode is on. **[I — mitigates the portfolio-homogenisation risk identified in Lens 12]**

### Step 1 — Interview

| | |
|---|---|
| **Inputs** | Warm-start state; any mined sources (repo, old site, deck) |
| **Process** | **Six phases in fixed order: a completed continuity check plus five hard-gated waves.** (0) Continuity — already resolved in Step 0; it is carried forward as context here, not re-gated. (1) Strategy — *hard-gated*. (2) Taste (visual before verbal) — *hard-gated*. (3) Design-system specifics — *hard-gated*. (4) Constraints & admin — *hard-gated*. (5) Success criteria — *hard-gated*. Aggressive branching. Every answer keyed by stable question ID. Three tiers: Tier 1 gates the prompt, Tier 2 asked just-in-time, Tier 3 inferred with a visible overridable default. |
| **Outputs** | `00-interview/answers.json` (question-ID-keyed), `00-interview/concept.md` (200–300 words: point of view, ≥3 abstracted references, restraint budget, what it refuses to do) |
| **Exit criteria** | All Tier-1 questions answered or explicitly defaulted; concept document written and confirmed by the user |

Full question bank: §5.

### Step 2 — Generate the design-system prompt

| | |
|---|---|
| **Inputs** | `answers.json`, `concept.md`, the pinned font catalog, the token-name manifest, prior-identity negative constraints |
| **Process** | Render a multi-stage prompt. **Stage A** asks for lightweight direction capsules — the batch may run larger than the ~10 target (over-generation, to give the shortlist step real headroom) — plus one gallery artifact. A lightweight, capsule-level shortlist pass (machine pre-filter on the self-audit fields, e.g. duplicate hue-anchor collisions and anti-slop-deny-list violations, then a user skim-and-cut if the batch still exceeds ~10) narrows the batch down **to the ~10 directions required by D1** — never below ~10 unless the user explicitly relaxes that floor, and any relaxation is recorded in `session.json` as a deviation from D1 requiring the user's sign-off. **Stage B** (run once per one of those ~10 shortlisted directions — "shortlisted" means "the ~10 directions that survived the capsule-level filter," not a smaller pool that skips D1's target) asks for the full DTCG token expansion, the identity-carrying component instances, and the artwork with affinity tags. Every prompt embeds: the exact return-format schema, a worked micro-example, the closed font vocabulary, the frozen token-name manifest, the CSP constraint, and a self-audit instruction. The skill computes the chunking. |
| **Outputs** | `01-prompt/stage-a.md`, `01-prompt/stage-b-<directionId>.md` (one per shortlisted direction, ~10 files), `01-prompt/artwork.md`, plus a copy-ready display in the terminal |
| **Exit criteria** | Prompts written to disk and displayed; user confirms they have them |

Full prompt spec and return schema: §6.

### Step 3 — Hand-carry (manual)

| | |
|---|---|
| **Inputs** | The generated prompt(s), pasted by the user into claude.ai |
| **Process** | User pastes prompt → claude.ai generates → user copies the response (one `Cmd+A`/`Cmd+C` per chunk under the one-paste protocol) → runs a one-word skill command → skill ingests via `pbpaste`. Tolerant parser splits on fenced blocks with `FILE:` headers, validates against the envelope manifest (file list, line counts, sha256 prefixes, a per-run random terminator token), and runs the deterministic re-verification pass. |
| **Outputs** | `02-system/<directionId>/{tokens.json, tokens.css, components/*.html, artwork/*}`, `02-system/manifest.json`, `02-system/import-report.json`, `02-system/system.lock.json` |
| **Exit criteria** | Manifest present and parseable; declared counts match actual counts; terminator present; zero unquarantined security rejections; all contrast and licence claims independently recomputed |

**Escape hatch, first-class:** if claude.ai is unavailable, lossy, or the user simply doesn't want the round-trip, **Local Regeneration Mode** runs the identical prompt against a Claude Code subagent, producing output in the identical format with zero pastes. The hand-carry is a UX preference, not a technical dependency. **[I — the skill runs on the same model family]**

Full boundary spec: §6.

### Step 4 — Select and build the editable design surface

| | |
|---|---|
| **Inputs** | The ingested system (all ~10 fully-built Stage-B directions); the interview's sitemap and content answers |
| **Process** | Direction selection is a **bracketed tournament over all ~10 Stage-B directions** (D1) — never a 10-up grid, and never more than 3 full-size renders compared side by side at once. **Round 1 (heats):** the ~10 directions are split into heats of 3 (the final heat may hold 2 if 10 doesn't divide evenly — e.g. 3+3+2+2, or the skill's actual split for whatever count survived Step 2's shortlist), each heat shown at full size; the user picks one winner per heat, with a free-text reason captured for each pick. **Round 2 (semifinal):** the heat winners are regrouped into heats of up to 3 and narrowed again, down to 2 finalists. **Round 3 (final):** the 2 finalists go head-to-head; the user's pick and stated reason close the tournament. Every round — which capsules/directions were shown, the order shown, the pick, and the user's stated reason — is written to the **direction tour log** as the rounds progress; it is not reconstructed after the fact. Then per-slot component selection, defaulting to the direction's canonical variant so the user only opens the component bar when dissatisfied. Then the skill generates `layout.json` + `content.json`, renders the site, and launches the editor. **[I — exact heat sizing (3/3/2/2 vs. another split) depends on how many directions survive Step 2's shortlist floor of ~10; the invariant that is NOT inferred is D1 itself: the bracket must cover the full shortlisted set, and "never more than 3 at full size" is the fixed viewing constraint every round obeys]** |
| **Outputs** | `04-site/{layout.json, content.json, provenance.json, direction-tour-log.json}`, a running local editor at a fixed port, `state.json` with `{port, pid, url, sessionId}` |
| **`direction-tour-log.json` schema** | `{rounds: [{roundName: "heat-1" \| "semifinal" \| "final", heats: [{directionsShown: [directionId,...], orderShown: [directionId,...], pick: directionId, reason: string}]}], finalPick: directionId, timestampIso: string}`. This is the artifact Step 8 folds into the evidence bundle under "the direction tour with the user's pick and stated reason" — it is a distinct file from `provenance.json` (which records per-asset generation provenance — generator, model, prompt — not tournament choices); the two are not interchangeable and both are required inputs to Step 8. |
| **Exit criteria** | Editor serves HTTP 200, verified by a curl in a **separate tool call** after the turn boundary (see §16.6); the user can see and edit their site; `direction-tour-log.json` is present and its `finalPick` matches the direction actually rendered |

Full editor spec: §10. Layout model: §11.

### Step 5 — More variants / redesign

| | |
|---|---|
| **Inputs** | The current direction, a component id or a system scope, the current highest variant index per item |
| **Process** | "More like this" generates 5 deterministic neighbours of an approved variant. "More variants" generates the next N for a slot. "Redesign part of the system" re-enters Step 2 with the current parameters as constraints (keep these, change these). Full redesign is a new Step 2 cycle with prior identity as negative constraint. |
| **Outputs** | Appended variants with append-only indices; on redesign, a new `system.lock.json` and a migration report mapping old variant ids to new |
| **Exit criteria** | New variants visible in the component bar; on redesign, every existing node either remapped or explicitly reported as unmappable — never silently dropped |

### Step 6 — Custom components

| | |
|---|---|
| **Inputs** | A user request for a component the system doesn't have (chart, calculator, map, embed, game, signature moment) |
| **Process** | Route to one of three paths: (a) **registry component** — a whitelisted family (table, chart, embed, form) generated against the direction's tokens by a deterministic generator plus the dataviz sub-token set; (b) **agent-authored** — `Task(general-purpose)` returns code as text, main thread writes it, runs the six coherence lints before acceptance; (c) **custom code block** — an opaque draggable container holding hand-written HTML/CSS/JS that the editor positions but never introspects. Path (c) is where the signature moment lives. |
| **Outputs** | `06-custom/<componentId>/`, registration in the component registry, an entry in the coherence ledger if it introduces off-system values |
| **Exit criteria** | Component renders, satisfies the container contract, passes the coherence lints or is recorded as accepted debt |

### Step 7 — LOCK

| | |
|---|---|
| **Inputs** | `layout.json`, `content.json`, `system.lock.json`, the component library |
| **Process** | **Re-render**, never copy-and-strip. Same renderer, `editor: false`. Then: scrub any residual `data-wb-*` in `astro:build:done`; run the ordered lock-time checklist (§13.4); assert zero editor strings; byte-compare against an editor-uninstalled build; snapshot documents into `.wb/locks/<iso>/`; git-tag `wb-lock/<n>`. LOCK writes only to `dist/published/` and `.wb/locks/` — it never mutates the design project, so UNLOCK is simply restarting the design server. |
| **Outputs** | `07-lock/dist/`, `07-lock/lock-manifest.json`, gate report, screenshots at 320/390/768/1440 |
| **Exit criteria** | All Tier-1 gates pass; the two-build byte-equality check passes; the lock manifest records the layout hash so a later unlock can diff against hand-edits |

Full contract: §12.5.

### Step 8 — Publish + evidence bundle

| | |
|---|---|
| **Inputs** | `dist/published/`, the asset manifest, the gate report, **`04-site/direction-tour-log.json`** (produced in Step 4 — see that step's Outputs for its schema) |
| **Process** | Deploy via `wrangler pages deploy ./dist --project-name=<x>` with a stored scoped token (one-time credential setup). Assemble the evidence bundle: per-font `{family, foundry, licenceClass, fileHash, sourceUrl, attributionRequired}`; per-asset `{generator, model, planTier, licenceClass, prompt, alt}`; the gate report; the screenshots; the direction tour — rendered directly from `direction-tour-log.json`'s rounds, including the user's pick and stated reason at every heat, not just the final pick; an explicit "manual accessibility review not performed" disclosure. Mirror a one-line verdict into `.acos/evidence/<date>/website-<session>/`. |
| **Outputs** | A live URL; `evidence/` bundle; a git tag |
| **Exit criteria** | Deploy returns success; evidence bundle is complete with zero unlicensed assets; evidence bundle's direction-tour section is non-empty and traces back to a `direction-tour-log.json` with the same `finalPick` as the shipped direction |

**If deploy is not automated in v1**, the PRD says so explicitly and emits a runbook. It does not leave the boundary ambiguous — the user's existing FruitSync deploy runbook already documents a manual Cloudflare dashboard drag-and-drop **[V — `/Users/zee/fruitsync-animated-variants/_release/DEPLOY-STEPS.md`]**, and silently repeating that is a friction tax on every future edit.

---
## 5. Step 1 — the interview question bank

**Delivery rules.** Chunked into waves of 5–8 questions per screen with a visible, shrinking progress count. Visual tasks alternate with verbal ones.

*Advertised time — revised and reconciled.* The bank is **90 questions** (see the row-count self-audit at the end of this section), not the "78" claimed in earlier drafts — that figure was a miscount that stopped at the end of Wave 4 and never added Wave 5's five questions; the correct original count was 83, and this revision adds 7 more to close gaps recorded below, for 90 total. In **fast mode** (`Z1 = "one sitting"`, see the retiered Wave 0 below), only Tier-1 questions are asked and Tier-3 items are bundled into one end-of-interview review screen; for the common single-language, single-surface, no-forms case this comes to **approximately 45–55 Tier-1 questions asked** plus one bundled 6-item review screen — **not the "~35–45" figure asserted in earlier drafts**, which had no dependency map behind it and could not be checked. At an estimated 25–30 seconds per standard closed-form question plus explicit budgets for the five heavy tasks in the bank (swipe-sort ≈4 min, two written taste sentences ≈1.5 min each, 8-item slider battery ≈2 min, the five-blank positioning statement ≈2 min), the honest estimate is **about 25–35 minutes in fast mode**, rising to **roughly 45–70 minutes in open-ended mode** (`Z1 = "open-ended"`) where every Tier-2 question is also asked. `[Inference — per-question timing budgets are estimated from the closed-vs-open-response shape of each question, not measured]`.
This is **narrower and more honest than, but not yet reconciled with,** two other sections that cite the old numbers: §17-R21 ("the bank is 78 questions; at 30–60s each that is 40–80 minutes") and §18's v1 scope-in line ("Full interview (78 bank …)"). **Flagged — requires cross-section reconciliation, not fixed unilaterally here:** whoever owns §17 and §18 should update both to the 90-question / 45–55-Tier-1-fast-mode / 25–35-minute figures derived here, and §19's acceptance criterion A19-A3 ("interview completes with ≤45 answered questions for a single-language, single-surface, no-forms marketing site") should be revised to **≤55**, which is the number this section can actually deliver — or the bank must be cut further to hit ≤45. This section does not have authority to edit §19's acceptance criteria and does not do so; it records the honest number and defers the reconciliation. **No known mitigation beyond instrumentation:** actual elapsed time must be measured from day one (see AC-5.4 below) because every estimate above is a projection, not a measurement.

**Tier notation — three states, disambiguated.** `[T1]` gates the Step-2 prompt. A Tier-1 question is satisfied by **exactly one of two resolutions**, and Step 1 does not exit until every Tier-1 question is in one of them:
  1. **Answered** — the user supplied a real value.
  2. **Explicitly defaulted** — the user took the visible "I don't know / surprise me" affordance (see Delivery rules note below and 5.1), and the skill recorded a **stated, concrete default value** (not a null) into `00-interview/answers.json` with `"source": "skill-default"`. This is what resolves the earlier contradiction between "Tier-1 must be answered" and "every taste question has a skip path" — Tier-1 is mandatory in the sense that the *question is always resolved*, not that the *user is forced to type an opinion*.

`[T2]` asked just-in-time at the moment the answer is needed; if that moment never arrives in the current build (e.g. because a dependent feature was declined), the question is not asked and is recorded as `"not-applicable"`, not defaulted.

`[T3]` inferred with a stated default and a visible "change this" affordance, presented pre-filled rather than asked open-ended, and in fast mode bundled with all other Tier-3 items into a single end-of-interview review screen. **Every row in the bank below now carries an explicit Default column**, closing the earlier gap where only 6 of 83 rows had a stated default despite Tier-3 being defined as "always has one." Six questions that already carried a stated fallback value in earlier drafts but were mistagged `[T1]` are retagged `[T3]` here for consistency with their own behavior: **C4, X2, M3, H1, H3, Z4**. Tier-3 is now used on 7 questions (was 1); the remaining admin rows either have no safe default (flagged "no default — hard block" below) or are genuinely Tier-2 with a not-applicable fallback.

**ID grammar (new rule, closes a blocking ambiguity).** Every question ID is `<wave-prefix><n>`; prefixes are reserved per wave-section (`C`, `P`, `B`, `A`, `TS`, `D`, `M`, `N`, `X`, `L`, `G`, `H`, `U`, `Z`, `V`) and never collide with the tier labels `T1`/`T2`/`T3`. **Rename notice:** the ten Wave-2 taste questions were previously numbered `T1`–`T10`, which is indistinguishable in prose from tier label `[T1]`/`[T2]`/`[T3]` — a directive citing "T3" was ambiguous between "the negative-reference question" and "an inferred-with-default question," and this collided directly with A4's requirement that every Step-2 directive cite the interview question ID that produced it. They are renumbered **`TS1`–`TS10`** here. **Flagged — compatibility risk this section cannot resolve alone:** any other PRD section, prompt template, or `answers.json` from a prior project (relevant to Step 0 warm-start reuse) that cites bare `T1`–`T10` meaning a taste question must be updated to `TS1`–`TS10`; a cross-section grep pass is required and is out of this section's scope.

**Branch roots — corrected.** Earlier drafts claimed four gates "prune ~10–12 questions each," which was asserted, not computed, and is arithmetically impossible against an 83–90-question bank (four roots at 10–12 each would prune 40–48 questions, but at most ~20 questions in the whole bank are plausibly downstream of any of the four). The real, question-level dependency map is now given per row below (see the **Ask-if** column in every table); the corrected per-root totals are:

| Branch root | Root question | Real questions pruned | Note |
|---|---|---|---|
| Has an existing locked brand identity | **C6** (new — moved to Wave 0; see below) | 1–2 (`B4`, conditionally `D8`) | The root signal previously lived on `N7` in Wave 4, *after* the taste questions (`B4`, `D8`) it was supposed to gate — a genuine sequencing bug, fixed by adding `C6` as a cheap Wave-0 root; `N7`–`N12` remain in Wave 4 to capture the factual specifics (hex values, licences) regardless of `C6`, since those are hard data needed either way, not style-invention questions |
| More than one language at launch | `L1` | 3 (`L2`, `L3`, `L4`) | The one root that actually matches its original billing at this bank's size |
| Collects personal data | `G1` | 1 (`G2`), conditionally, jointly gated with the new `G0` jurisdiction question | `G3` (age-gate/industry) is **not** prunable by `G1` alone — an alcohol or gambling site needs an age-gate regardless of whether it collects personal data |
| Design-system scoped to this site only | `D4` | **0** | **Correction, not a fix-in-place:** this was listed as a question-pruning root in earlier drafts but has no downstream question dependents anywhere in the bank — `D4`'s four answers change *what Step 2/3 export as portable tokens*, a downstream deliverable-scope effect, not further interview questions. It should never have been framed as a branch root that prunes questions. If a future section needs `D4` to gate additional interview questions, those questions must be added there; none are invented here to make the old framing true. |

No-forms cases add one more real prune not previously named as a "root": `D7` (form types) is skipped when no form-bearing component is in scope, which also skips the newly added `D11` (form destination) — see Wave 3 below.

**Ordering principle.** Strategy before taste. Visual before taste within taste. Constraints and admin last — **with one deliberate exception**: `Z1` and `Z2` (time budget and variant-count preference) are promoted into Wave 0 in this revision (see below) because they are global branching policy inputs consumed by every later wave, and a policy input asked *after* the questions it is meant to prune has no effect on them. This is both elite-studio process (brief → references → concept → art direction → build) and standard questionnaire funnel technique arriving at the same answer independently. **[V — prior swarm report Finding 6, Obys/Locomotive/Awwwards Academy sequencing]**

---

### Wave 0 — Continuity & global policy (always first, before anything else)

| ID | Question | Tier | Ask-if | Default | Notes |
|---|---|---|---|---|---|
| C1 | Have you used this skill before on this project, or is there an existing design system or prior site to build on? | T1 | always | no default — root gate, no safe assumption | Root gate. Three branches: fresh / reuse as-is / reuse-and-revise |
| C2 | If reusing — which parts stay locked and which are open for revision? | T1 | `C1 ≠ fresh` | if explicitly defaulted while asked: "all open for revision" (the conservative, maximally flexible choice) | Only if C1 ≠ fresh. Tells Step 2 which tokens are frozen |
| C3 | Is there an existing library of artwork, sprites, photography, or illustration I should use? Where? | T1 | always | "no — code-drawn art only" | **The binary that decides whether the art category is real.** Answering "no" scopes art to code-drawn only. Feeds `N12` (asset licence capture) when answered "yes" |
| C4 | Is this site a sibling of an existing site of yours — should it share that site's identity? | **T3** *(retagged from T1)* | always, bundled into end-of-interview review in fast mode | "no" | Default no. "Yes" is the only path that reuses hue anchors and type pairings |
| C5 | **NEW.** What is the primary language visitors will read this site in? | T1 | always | `[Inference]` the language the interview itself was conducted in | Closes a gap where `L1` only asks about *additional* languages and a single-language project never recorded which language it was in — needed for `<html lang>` (§13.6) on every single-language site, i.e. the common case the whole branching model is tuned for |
| C6 | **NEW.** Do you already have a locked visual identity — logo, and/or fixed brand colours/type — that this site must visually match? | T1 | always | "no" — asking `B4`/`D8` when unsure is safer than wrongly skipping them and defaulting to a generic invented identity | This is the real root for the "has-existing-logo" branch (see Branch roots table above); relocated here from its former implicit home on `N7` in Wave 4 specifically so it can gate `B4` and `D8`, which are asked *before* Wave 4 in question order |
| Z1 | **MOVED from Wave 4.** How much of your time can you give — one sitting / a few short sessions / open-ended? | T1 | always | if explicitly defaulted: "a few short sessions" `[Inference — conservative middle default]` | Sets how aggressively to branch and how many variant rounds to offer. **Concrete effect, previously unstated:** `one sitting` → only Tier-1 questions asked, all Tier-2 auto-deferred/defaulted, Tier-3 bundled into one review screen, variant rounds capped at 1. `a few short sessions` → Tier-1 + Tier-2 asked (can span sessions), Tier-3 shown individually, up to 2 variant rounds by default. `open-ended` → full bank, unlimited variant rounds bounded only by `Z2` and the Step 5/§6/§17 iteration budget |
| Z2 | **MOVED from Wave 4.** Do you want a small number of strong options, or many to compare? | T1 | always | if explicitly defaulted: "many to compare" | Directly sets the D1-settled variant multiplier (§ Settled Decisions D1: 10 variants per swappable component is the standing default). **Concrete effect, previously unstated:** "many to compare" → the full 10-variant-per-component default from D1 applies. "A small number of strong options" → 3 variants per swappable component per round, still computed from the direction's derived values per D1, never hand-picked independently |

*Row-count for this wave: 8 (`C1`–`C6`, `Z1`, `Z2`).*

### Wave 1 — Strategy

**Purpose & Goals**

| ID | Question | Tier | Ask-if | Default | Notes |
|---|---|---|---|---|---|
| P1 | What is this website for — what's the one thing you want a visitor to DO after they arrive? | T1 | always | no default — hard block, this is the single most load-bearing answer in the bank | Drives section grammar and CTA placement |
| P2 | What outcome does this serve — revenue, leads, hiring, portfolio, awareness, other? | T1 | always | no default — hard block | 6 closed options; sets rubric weighting |
| P3 | Is this a brand-new venture, or an existing one getting a new site? | T1 | always | no default — hard block, gates brand-asset questions downstream | 2 options; gates brand-asset questions |
| P4 | Picture this site 12 months from now, succeeding beyond your hopes — what changed? | T2 | `Z1 ≠ "one sitting"` | not-applicable when skipped | JTBD aspirational framing |
| P5 | Why build this now, rather than 6 months ago or 6 months from now? | T2 | `Z1 ≠ "one sitting"` | not-applicable when skipped | JTBD push/pull; surfaces the real trigger |
| P6 | **NEW.** Which of these best describes the site — brochure/marketing site, product/app landing, e-commerce, portfolio, blog/publication, game or app promo, event, nonprofit/cause, documentation/knowledge base, other? | T1 | always | `[Inference]` inferred from `P2`, mapped 1:1 to the schema.org types §13.6 requires (Organization/WebSite for marketing, VideoGame for game promo, WebApplication for app shell, etc.) — always shown for confirmation, never silently applied | Closes a gap where §13.6 required JSON-LD "matched to the site-type answer" and its acceptance criterion A70 had no question to read from; `P2` (business outcome) does not map onto schema.org types and this is a distinct question |

**Positioning & Brand Strategy**

| ID | Question | Tier | Ask-if | Default | Notes |
|---|---|---|---|---|---|
| B1 | Fill in the blank: For [target] who [need], [name] is the [category] that [benefit] — unlike [alternative], we [differentiator]. | T1 | always | no default — hard block, no safe substitute for this answer exists | Geoffrey Moore template **[V — Crossing the Chasm]**. Highest-leverage single question in the bank; seeds hero copy directly |
| B2 | Who are 2–3 direct competitors or alternatives, and what does each do better or worse? | T1 | always | no default — hard block, feeds the ≥3-reference concept gate | Feeds the ≥3-reference concept gate |
| B3 | In one sentence, what makes you different from every alternative? | T2 | always (cheap, low-friction) | if explicitly deferred: derived from `B1`'s differentiator clause | Portable line for hero + meta description |
| B4 | If your brand showed up as a person at a party, how would they act — which of these fits (or none)? | T1 *(previously T3; retagged because it now has a real ask-if, not just a default)* | `C6 == "no"` | when skipped (`C6 == "yes"`): `[Inference]` archetype inferred from the supplied logo's visual language (shape language, colour temperature, line weight), shown with a change-this affordance | 12 Jungian archetypes **[V — Mark & Pearson 2001]**. Explicit skip path required; alienates utilitarian sites |
| B5 | How should this brand sound in writing — pick up to 3 words? | T2 | always | if explicitly deferred: derived from `B1` + `T2`/`TS2` written taste sentences | Seeds voice/tone tokens |

**Audience**

| ID | Question | Tier | Ask-if | Default | Notes |
|---|---|---|---|---|---|
| A1 | Who is the primary visitor — role, context, how technical? | T1 | always | no default — hard block | Core persona |
| A2 | Is there a second audience with meaningfully different needs? | T2 | always | "no" if skipped | Determines parallel sitemap tracks |
| A3 | What do visitors believe before they arrive, and what should they believe after? | T2 | always | not-applicable if skipped, narrative arc left to Step 2 inference from `P1`/`B1` | Narrative arc |
| A4 | What's the single most likely objection that stops a visitor converting? | T2 | always | not-applicable if skipped | Feeds FAQ / trust-signal placement |
| A5 | What device and setting will most visitors be in — mobile-on-the-go / desktop-at-work / tablet-in-store / mix? | T1 | always | no default — hard block, sets responsive priority and the performance budget | 4 options; sets responsive priority and performance budget |

*Row-count for this wave: 16 (Purpose 6, Positioning 5, Audience 5).*

### Wave 2 — Taste (visual first, verbal second — this ordering is load-bearing)

*Renamed from `T1`–`T10` to `TS1`–`TS10` this revision — see the ID Grammar rule above.*

**Visual**

| ID | Question | Tier | Ask-if | Default | Notes |
|---|---|---|---|---|---|
| TS1 | Here are curated reference screenshots — sort each into love / neutral / hate. | T1 | always | no default — hard block; if the user cannot engage with this task at all, fall back to the style-family sort described in 5.1 | 24 images spanning minimal, maximal, brutalist, editorial, corporate, playful, dark-cinematic, retro. **Pre-seeded by the wave-1 vertical answers (`P2`, `P6`)**, not a generic set. **[V — NN/g mood-board + preference-testing research; arXiv 2511.20513 DesignPref]** |
| TS2 | Of the ones you loved, pick your top 3 and say one sentence on what specifically you love. | T1 | always | if the "I don't know / surprise me" affordance is used: skill proposes 2–3 candidate descriptions drawn from the loved images' shared attributes and asks the user to pick or edit one, rather than inventing an unattributed preference | Converts preference into design language; this is the reference-abstraction step |
| TS3 | Of the ones you hated, pick your top 3 and say one sentence on what turns you off. | T1 | always | same surprise-me mechanism as `TS2`, applied to the hated set | Negative references are more diagnostic than positive **[V — wayfront.com branding questionnaire; prior report Finding 4 deny-list mechanism]** |
| TS4 | Move each slider: Minimal↔Maximal, Playful↔Serious, Quiet↔Loud, Classic↔Futuristic, Corporate↔Handmade, Light-first↔Dark-first, Warm↔Cool, Dense↔Airy. | T1 | always | if explicitly deferred per-slider: midpoint, with a note that midpoint defaults reduce directional signal and should be revisited before Step 2 fires | 8 semantic-differential pairs. Research recommends 5–10 per battery |
| TS5 | Is there a competitor or peer site whose visual territory you want to actively avoid, even if it's well-made? | T2 | always | "none named" if skipped | Trade-dress proximity + negative constraint |

**Verbal (asked only after the visual tasks)**

| ID | Question | Tier | Ask-if | Default | Notes |
|---|---|---|---|---|---|
| TS6 | Should imagery lean photography / illustration / 3D render / abstract-generative / mix? | T1 | always | no default — hard block, routes asset generation | 5 options; routes asset generation |
| TS7 | Icons from an existing set restyled to match, or fully custom-drawn? | T2 | always | "existing set, restyled" if skipped (cheaper default) | 2 options |
| TS8 | Custom cursor (dot, ring, magnetic, trail) or plain browser default? | T2 | always | "plain browser default" if skipped | 2 options; user-named item |
| TS9 | Top navigation feel — always visible / hide-on-scroll / transparent-over-hero / minimal corner menu? | T1 | always | no default — hard block, user-named item ("top ribbon") | 4 options; user-named item ("top ribbon") |
| TS10 | Should the background carry its own art/style, or stay a plain surface colour? | T1 | always | no default — hard block, user-named item (FruitSync example) | 5 options: plain / gradient / pattern / illustrated scene / generative particle. User-named item (FruitSync example) |

*Row-count for this wave: 10.*

### Wave 3 — Design-system specifics

**Theming & Density**

| ID | Question | Tier | Ask-if | Default | Notes |
|---|---|---|---|---|---|
| D1 | Light/dark toggle, dark-only, light-only, or follow system with no toggle? | T1 | always | no default — hard block, determines whether every token needs a dual-mode value from day one | 4 options. Determines whether every token needs a dual-mode value from day one |
| D2 | How dense should the UI feel — spacious/editorial or compact/information-dense? | T1 | always | no default — hard block, drives the spacing and type scale base multiplier | 3 options; drives the spacing and type scale base multiplier |
| D3 | How many distinct page templates does this need (landing, article, gallery, pricing, dashboard…)? | T2 | always | `[Inference]` inferred from `P6` site type + `N3` page count | Distinct from how many pages exist today |
| D4 | Will this system extend beyond this site — a future app, email, decks, social? | T2 | always | "no — this site only" | 4 options; changes whether tokens export portably. **See Branch-roots correction above: this question has zero downstream question dependents in this bank; its effect is scoped entirely to Step 2/3 export-format deliverables, not further interview questions** |
| D5 | Full interaction-state coverage everywhere (hover/focus/active/disabled/loading/error), or lighter where non-critical? | T2 | always | "lighter where non-critical" if skipped | 2 options; roughly doubles variant cost per interactive component |

**Component breadth**

| ID | Question | Tier | Ask-if | Default | Notes |
|---|---|---|---|---|---|
| D6 | Which do you need — pricing table, testimonial carousel, FAQ accordion, stat counter, timeline, comparison table, embedded map, gallery/lightbox, newsletter signup, search, tag/filter, rating display? | T1 | always | no default — hard block, unchecked items are simply not built | 12-item checklist. **The single biggest gap between a website brief and a design-system brief.** Unchecked items are simply not built |
| D7 | Form types beyond a simple contact form — multi-step, file upload, payment, booking, survey? | T2 | any form-bearing component selected in `D6`, or `P1`/`U1` implies a form CTA | "simple contact form only, no advanced type" if skipped — this is one of the concrete prunes for the "no-forms" common case named in A19-A3 | Forms concentrate accessibility and validation work |
| D11 | **NEW.** Where should form submissions go — a third-party form endpoint, a mailto fallback, or none? | T1 | same trigger as `D7` (any form in scope) | **no safe silent default** — if a form is in scope and this is explicitly deferred, the only zero-configuration fallback is a `mailto:` to the account holder's contact address, and it is surfaced as a **blocking pre-publish check**, not silently applied | Closes a gap where §2-NG3 names third-party-endpoint-or-mailto as the only two supported destinations, `D7` asked which form *types* were needed but nothing asked *where submissions go*, so a contact form was buildable and unshippable |

**Identity details**

| ID | Question | Tier | Ask-if | Default | Notes |
|---|---|---|---|---|---|
| D8 | Serif, sans, or display/expressive for headlines — or should the system propose? | T1 | `C6 == "no"` | when skipped (`C6 == "yes"`): "use the brand's existing typeface family," confirmed later against the licence captured at `N9` | 4 options; user-named item ("a font") |
| D9 | How much personality should the front-of-site animation carry — signature entrance moment / subtle ambient / none? | T1 | always | no default — hard block, user-named item ("an animation for the front") | 3 options; user-named item ("an animation for the front"). Per Settled Decision D4, this and its variants live in the same draggable art-style containers as static artwork, not a parallel motion subsystem |
| D10 | Primary buttons flat/minimal, with depth, or fully custom/illustrated? | T2 | always | "flat/minimal" if skipped | 3 options; user-named item ("a button") |

**Motion appetite**

| ID | Question | Tier | Ask-if | Default | Notes |
|---|---|---|---|---|---|
| M1 | On a scale from "nothing moves" to "everything moves," how much motion? | T1 | always | no default — hard block, sets the single motion-expressiveness dial | 5-point scale; sets the single motion-expressiveness dial |
| M2 | A specific site whose motion you want to emulate — or specifically avoid? | T2 | always | "none named" if skipped | Motion is hard to describe, easy to point at |
| M3 | Should motion automatically reduce for visitors who've asked for less motion, with a visible toggle as fallback? | **T3** *(retagged from T1)* | always, bundled into end-of-interview review in fast mode | "yes" | Default yes. Asking confirms informed consent and surfaces the rare force-motion case |

*Row-count for this wave: 14 (Theming 5, Component 3, Identity 3, Motion 3).*

### Wave 4 — Constraints & admin

**Content reality**

| ID | Question | Tier | Ask-if | Default | Notes |
|---|---|---|---|---|---|
| N1 | Do you have final copy, or does content need drafting? | T1 | always | no default — hard block | 3 options |
| N2 | Do you have final photography/video, or does imagery need generating or sourcing? | T1 | always | no default — hard block, interacts hard with C3 | 3 options; interacts hard with C3. Feeds `N12` licence capture when "yes" |
| N3 | Roughly how many pages or sections? | T1 | always | no default — hard block | 4 tiers: single / 2–5 / 6–15 / 15+ |
| N4 | Which pages are must-have for launch, which can wait? | T1 | always | no default — hard block, v1 sitemap vs backlog | v1 sitemap vs backlog |
| N5 | Existing material to mine — old site, deck, one-pager? | T2 | always | "none" if skipped | Enables auto-mining |
| N6 | Will content change often after launch, or is it mostly static? | T1 | always | no default — hard block, determines whether the editor needs an ongoing content model | Determines whether the editor needs an ongoing content model |

**Brand assets already owned**

| ID | Question | Tier | Ask-if | Default | Notes |
|---|---|---|---|---|---|
| N7 | Do you have a logo? Is it final, or open to refinement? | T1 | always (factual detail follow-up to `C6`, asked regardless of `C6`'s value) | no default — hard block | 3 branches |
| N8 | Do you have brand colours? Hex values? | T1 | always | no default — hard block, hard constraint on the colour solver | Hard constraint on the colour solver |
| N9 | Do you have a brand typeface? Do you hold a web-embedding licence? | T1 | always | no default — hard block, gates the three-tier font policy | Gates the three-tier font policy |
| N10 | Existing marketing materials the site must stay consistent with? | T2 | always | "none" if skipped | |
| N11 | Do you have a style guide or brand book, even informal? | T1 | always | no default — hard block; short-circuits much of waves 1–2 when "yes" | Short-circuits much of waves 1–2 |
| N12 | **NEW.** For every visual asset you supply (photos, illustrations, sprites, existing marketing art) — who made it, under what licence, and is public-site redistribution permitted? Options per source: own work / commissioned with rights transferred / licensed stock (name the licence + seat count) / unknown. | T1 | `C3` answered "yes" (a library exists) OR `N2` indicates existing final photography/video OR `N10` names existing materials | **"unknown" is an explicit, blocking answer** — it is recorded into `assets/manifest.json` and surfaced as a blocking condition at intake, not discovered later at LOCK | Closes a gap where the only asset class with a licence question was the brand typeface (`N9`); Step 8's evidence bundle (per the user's vision) and gate 26 (§13) require licence completeness for *every* asset, and raster/photo/illustration assets — the more common case — had no supply path for that data at all |

**Accessibility**

| ID | Question | Tier | Ask-if | Default | Notes |
|---|---|---|---|---|---|
| X1 | Legal/organisational accessibility requirement (ADA, Section 508, EN 301 549), or best-effort? | T1 | always | `[Inference]` **pre-answered from `G0`'s jurisdiction derivation where possible** (e.g. an EU-serving business is flagged toward the European Accessibility Act) rather than asking the user to self-assess legal exposure blind; still shown for confirmation | 3 options; sets gate strictness. Closes a gap where the user was expected to already know which accessibility regime applies to them |
| X2 | Target WCAG 2.2 AA (default), or further? | **T3** *(retagged from T1)* | always, bundled into end-of-interview review in fast mode | "AA" | Default AA. Auto-answered "AA" if declined — never silently omitted |
| X3 | For dark/cinematic palettes, also check against APCA in addition to WCAG 2? | T2 | wave-2 (`TS4`/`TS10`) answers point dark | "no" if not triggered | Only surfaced when wave-2 answers point dark |

**Performance & device**

| ID | Question | Tier | Ask-if | Default | Notes |
|---|---|---|---|---|---|
| X4 | Lowest-end device/network you expect — flagship+wifi / mid-range+data / budget+slow? | T1 | always | no default — hard block, sets the performance budget and GPU-tier ladder | 3 options; sets the performance budget and GPU-tier ladder |
| X5 | Any hard performance ceiling (kiosk on venue wifi, expensive-data market)? | T2 | always | "none" if skipped | Can override visual ambition outright |
| X6 | Should heavy visuals (3D, video, particles) degrade on low-end devices, or must the experience be uniform? | T2 | always | "degrade gracefully" if skipped | 2 options; determines whether the tier ladder is built |

**Localisation**

| ID | Question | Tier | Ask-if | Default | Notes |
|---|---|---|---|---|---|
| L1 | More than one language at launch? Which? | T1 | always | "no" | Root; "no" skips the rest of this section (`L2`–`L4`) |
| L2 | Do any read right-to-left (Arabic, Hebrew)? | T1 | `L1 ≠ "no"` | no default when asked — hard block, structural | **Structural, must be known before the grid is built.** This project's own FruitSync Arabic RTL rework is direct first-party evidence of the retrofit cost **[V — repo commits 7dd7544, 060a9af; fruitsync-localization memory]** |
| L3 | Localise currency/date/number formats per region? | T2 | `L1 ≠ "no"` | "no localisation, single format" if skipped | |
| L4 | Who provides translations — professional / MT you'll review / placeholder flagged for review? | T2 | `L1 ≠ "no"` | "MT you'll review, flagged" if skipped — prevents machine translation shipping as final silently | Prevents machine translation shipping as final |

**Legal**

| ID | Question | Tier | Ask-if | Default | Notes |
|---|---|---|---|---|---|
| G0 | **NEW.** Where is the business established, and which regions will visitors come from? | T1 | always, root of the legal branch, asked before `G1` | no default — hard block, no safe assumption of jurisdiction | Closes a gap where `G1`–`G3` asked about data collection, legal pages, and age-gates/regulated industries without ever asking *which regime* governs them — the interview otherwise drafts a privacy policy, terms, and cookie banner that satisfy no regulator, or silently assumes one jurisdiction. **This question records region only; mapping specific regions to specific regimes (GDPR/ePrivacy, UK GDPR, CCPA/CPRA, the EU Accessibility Act, or none) is a legal-accuracy question this PRD cannot answer with certainty — flagged as "requires user/legal sign-off," no known mitigation beyond routing the recorded answer to whatever document-drafting step handles `G2`, which must itself carry the same disclaimer that generated legal text is not a substitute for counsel** |
| G1 | Does this site collect personal data — forms, cookies, analytics, newsletter? | T1 | always | no default — hard block, root of the legal-pages branch | Root of the legal-pages branch |
| G2 | Need privacy policy, terms, cookie banner at launch? | T1 | `G1 == "yes"` OR `G0`'s derived regime mandates disclosures regardless of data collection | "not needed" only when both `G1 == "no"` AND `G0`'s region has no mandatory-disclosure regime; otherwise no default — hard block | 3 options: draft-for-me / I'll-supply / not-needed. Also drives whether a consent banner is a blocking (ePrivacy-style, must block non-essential cookies before load) vs advisory (CCPA-style opt-out) vs absent element — **derived from `G0`, not a free style choice** |
| G3 | Age-gate, region-block, or industry-specific requirement (alcohol, gambling, finance, healthcare)? | T2 | always — **not** prunable by `G1` alone, since an age-gated industry site may need this with zero personal-data collection | "none" if skipped | |

**Hosting & maintenance**

| ID | Question | Tier | Ask-if | Default | Notes |
|---|---|---|---|---|---|
| H1 | Where should the finished site be hosted? | **T3** *(retagged from T1)* | always, bundled into end-of-interview review in fast mode | Cloudflare Pages, static, free bandwidth | Default recommendation: Cloudflare Pages, static, free bandwidth |
| H2 | Do you own a domain? Which? | T1 | always | no default — hard block | |
| H3 | Do you want the site's own git history, or is the ACOS session history enough? | **T3** *(retagged from T1)* | always, bundled into end-of-interview review in fast mode | its own nested repo | Default: its own nested repo |
| H4 | Who maintains it after launch — you in the editor / a developer / nobody? | T1 | always | no default — hard block, calibrates editor investment | 3 options; calibrates editor investment |
| H5 | How often will you come back into the design surface — often / occasionally / rarely? | T2 | always | "occasionally" if skipped | |
| H6 | How much of the page do you expect to hand-edit in code afterwards? | T2 | always | "little to none" if skipped | Calibrates how much wrapper scaffolding to generate |

**Custom & unusual**

| ID | Question | Tier | Ask-if | Default | Notes |
|---|---|---|---|---|---|
| U1 | Anything beyond standard marketing components — live chart, calculator, embedded game, data table, interactive map, booking widget? | T1 | always | "none" if skipped | Scopes Step 6 early |
| U2 | Is there a signature interaction you already have in mind? | T2 | always | "none named — skill may propose one" if skipped | Award-tier sites have exactly one; asking directly can save inventing one |

**Decision process & tooling** *(renamed from "Time & decision process" — `Z1`/`Z2`, the time-budget items, moved to Wave 0; see Ordering principle above)*

| ID | Question | Tier | Ask-if | Default | Notes |
|---|---|---|---|---|---|
| Z3 | Does anyone else need to approve before you say LOCK? | T2 | always | "no" if skipped | Determines whether a shareable review step is needed |
| Z4 | Do you have any image-generation connector active in your claude.ai session? | **T3** *(retagged from T2)* | always, bundled into end-of-interview review in fast mode | assume no | Changes what Stage B can reasonably request. Default assume no |
| Z5 | **NEW.** Do you have access to claude.ai Projects or custom instructions in your session? | T2 | always | assume no | Closes a gap where §17-O27's stated resolution was literally "ask in the interview" and no such question existed; sits beside `Z4` since both gate what the Step-2/Step-3 hand-back can assume about the user's claude.ai environment |

*Row-count for this wave: 37 (Content 6, Brand 6, Accessibility 3, Performance 3, Localisation 4, Legal 4, Hosting 6, Custom 2, Decision process 3).*

### Wave 5 — Negative constraints & success criteria

| ID | Question | Tier | Ask-if | Default | Notes |
|---|---|---|---|---|---|
| V1 | Is there a colour, symbol, font, or visual cliché that must never appear? | T1 | always | "none named" if skipped, but flagged as a weaker deny-list than an explicit answer | Per-project deny-list layered on the standing anti-slop list |
| V2 | Is there a past design — yours or a competitor's — you're actively moving away from? | T1 | always | "none named" if skipped | Concrete "not this" anchor for the concept gate |
| V3 | Are there tone, imagery, or humour lines this brand must never cross? | T2 | always | "none named" if skipped | Brand-safety, distinct from visual constraints |
| V4 | When you look at the finished site, what will tell you it was worth doing this way instead of picking a template? | T1 | always | no default — hard block, this is the qualitative acceptance bar the human applies at LOCK and cannot be safely invented | The qualitative acceptance bar the human applies at LOCK |
| V5 | What would make you say LOCK today, versus asking for one more round of variants? | T1 | always | no default — hard block | Operationalises the Step-5-vs-Step-7 branch |

*Row-count for this wave: 5.*

---

### 5.1 Row-count self-audit (must be re-verified any time a row is added or removed)

| Wave | Rows | Detail |
|---|---|---|
| Wave 0 | 8 | C1–C6 (6) + Z1, Z2 moved in (2) |
| Wave 1 | 16 | Purpose 6 (P1–P6) + Positioning 5 (B1–B5) + Audience 5 (A1–A5) |
| Wave 2 | 10 | TS1–TS10 |
| Wave 3 | 14 | Theming 5 (D1–D5) + Component 3 (D6, D7, D11) + Identity 3 (D8–D10) + Motion 3 (M1–M3) |
| Wave 4 | 37 | Content 6 (N1–N6) + Brand 6 (N7–N12) + Accessibility 3 (X1–X3) + Performance 3 (X4–X6) + Localisation 4 (L1–L4) + Legal 4 (G0–G3) + Hosting 6 (H1–H6) + Custom 2 (U1–U2) + Decision process 3 (Z3–Z5) |
| Wave 5 | 5 | V1–V5 |
| **Total** | **90** | 83 original rows (corrected count; earlier drafts said 78, which under-counted by omitting Wave 5) + 7 new rows added by this revision: `C5`, `C6`, `P6`, `D11`, `G0`, `Z5`, `N12` |

### 5.2 Fallback flows

- **User can't name any reference site they like** — a documented real failure mode. Auto-suggest a curated reference set by detected vertical, and if that fails, run a broader first-pass style-family sort (8 families) before individual-site references. **[V — practitioner reports; the fallback design is inference]**
- **User declines the accessibility questions** — auto-answer "AA, no known legal requirement" unless `G0`'s jurisdiction derivation already flagged a real requirement, in which case that requirement is recorded instead of the generic default. Never silently omit the gate.
- **User gives vague strategy answers** ("I want it to look nice") — the concept gate will produce a generic document and all 10 directions inherit that blandness. Mitigation: the interview pushes with concrete follow-ups ("what would you *not* want it to look like?") and refuses to advance to Step 2 until the concept document names at least one thing the site refuses to do.
- **"I don't know / surprise me" affordance** — present on every Tier-1 and Tier-2 taste question (Wave 2, plus `B4`, `B5`, `D8`–`D10`, `M1`–`M2`). Taking it routes the skill to propose options derived from the reference-swipe results (`TS1`–`TS3`) rather than the user inventing an unattributed preference, and always records a concrete default value per the Tier notation's "explicitly defaulted" state — never a null.

### 5.3 Acceptance criteria (new — closes the untestable-claim gap)

- **AC-5.1 (defaulting is real, not silent).** Every Tier-1 question in a completed interview is either answered by the user or carries a `"source": "skill-default"` entry with a concrete value in `00-interview/answers.json`. No Tier-1 field may be null or absent at Step-1 exit.
- **AC-5.2 (row-count integrity).** A script cross-checks the total row count in this section's tables against the number asserted in the self-audit table (90) on every edit to this file, so the count cannot silently drift the way "78" did.
- **AC-5.3 (common-case count, honestly bounded).** A simulated run with `C1="fresh"`, `C6="no"`, `L1="no"`, no form-bearing component selected, `G1="no"`/no jurisdiction trigger, no dark taste signal, and `Z1="one sitting"` should ask **45–55** Tier-1 questions plus the single 6-item Tier-3 review screen. **This revises A19-A3's "≤45" bound** — flagged for §19's owner to reconcile; this section does not edit §19 directly.
- **AC-5.4 (measured, not estimated, duration).** Median wall-clock interview duration for the common case is instrumented from the first release and compared against the 25–35 minute (fast mode) / 45–70 minute (open-ended mode) estimates above. **No known mitigation besides measurement** — every time figure in this section is a projection until real sessions are logged.

---
## 6. Step 2 — the design-system generation prompt

### 6.0 The prompt itself: template, inputs, and where they come from

Section 6's deliverable is a literal artifact — a piece of text the skill generates and the user pastes into claude.ai (§6.4) or hands to a local subagent (§6.5). Everything below is that artifact's contract: what fills it, what it must contain, and the exact wire shape of what comes back. **This subsection did not exist in the reviewed draft; §6.1's demand list and §6.2's return schema had no template connecting them, no stated source for two artefacts they both assume, and no length target.**

**Two artefacts the prompt depends on, defined:**

| Artefact | What it is | Where it lives | How it's built |
|---|---|---|---|
| `font-catalog.json` | The pinned OFL shortlist referenced by demand 4 — a closed list of licence-cleared typefaces, each entry `{familyId, classification (serif/sans/display/mono/expressive), foundry, oflSourceUrl, fileHash, glyphCoverage, preSubsettedCuts: {latin: base64, latinExtended: base64}}`. The `preSubsettedCuts` are computed **once, ahead of time, by the skill** — not by the web model — via a local subsetting pass (e.g. fonttools `pyftsubset`, already precedented in this project's own font-regeneration work) over each family's Latin/Latin-Extended glyph range. **[I — no subsetting toolchain is fixed elsewhere in the PRD; fonttools is named as the most defensible default because it already appears in this codebase's own localization history, not because it is mandated here]** | `.acos/website-builder/library/font-catalog.json` — a **reusable-across-projects** resource per §4's warm-start split ("font catalog" is explicitly listed there as shared), generated/refreshed by a standalone skill maintenance command, never regenerated per session. A session-scoped, hash-pinned copy is snapshotted into `01-prompt/font-catalog.snapshot.json` at Step-2 start, so a mid-run library refresh can never silently change what a session is judging | Seeded once with a starting shortlist (size TBD by the skill's implementer — **open question, no known mitigation stated here**: how many families constitute the initial shortlist is a product decision outside this section's scope) and grown only through an explicit, licence-checked addition process, never inferred at prompt-generation time |
| `token-manifest.json` (the "frozen token-name manifest" of demand 8) | The complete, closed list of **token name paths** — not values — every direction must populate. Generated **mechanically** from §7's category tables: each of §7's ~85 items (Category A's 26-slot vector plus the derived/semantic items in §7.2–§7.8) expands to 1–40 resolved tokens, landing in §7's own stated budget of **~600–900 resolved tokens per direction** [V — §7, counted programmatically from Carbon/Material/Fluent sources]. `token-manifest.json` is that same expansion done once, structurally, producing the **name** half only (e.g. `--color-surface-raised`, `--motion-duration-fast`) with no per-direction value — directions differ in what each name resolves to, never in what names exist | `.acos/website-builder/sessions/<id>/01-prompt/token-manifest.json`, generated by the skill from §7's item list at the start of Step 2, before any prompt is emitted, and re-pasted verbatim into every chunk per demand 8 | Deterministic expansion script, not an LLM call — the whole point of "frozen" is that no model, local or web, ever gets to invent or rename a key |

Both artefacts are **skill-owned, not model-generated.** This closes the demand-4/demand-5/demand-8 provenance gap directly: the web model never invents a font family or a token key; it only ever selects from, or is constrained by, a list the skill handed it.

**Prompt template — Stage A (worked skeleton, not prose-only).** Slot markers use `{{UPPER_SNAKE}}`. The seven elements A6 requires to be present are marked **[A6-n]** at the point they land, so "the prompt contains X" is verifiable by grep against the emitted text rather than by inspection.

```
You are generating {{DIRECTION_COUNT}} complete, internally consistent design
directions for a website design system, returned as machine-parseable files
plus one visual gallery artifact. Follow every rule below exactly; deviations
break an automated ingest pipeline with no human review step.

## 0. Format contract                                            [A6-1][A6-5]
{{DTCG_WORKED_EXAMPLE}}          <- literal DTCG 2025.10 colour-token JSON,
                                     not a description of the shape
{{CSP_CONSTRAINT_STATEMENT}}     <- "self-contained only, no CDN, no @import,
                                     base64 data:font/woff2 required because—"
{{OKLCH_HUE_WARNING}}                                             [A6-2]
                                     <- "OKLCH hue 0deg = magenta, not red;
                                     red is ~41deg" verbatim

## 1. What you know about this project
{{CONCEPT_BRIEF}}                <- concept.md, itself distilled from
                                     answers.json per the mapping table below
{{TASTE_PROFILE}}                <- T1-T5 distilled: loved/hated reference
                                     abstractions, 8 slider positions
{{NAMED_ITEM_INSTRUCTIONS}}      <- T7-T10, D8-D10, M1-M3 rendered as direct
                                     per-component instructions (see mapping)
{{PRIOR_IDENTITY_NEGATIVE_CONSTRAINTS}}                           [A6-4]
                                     <- only present if C1/C4 != fresh; hue
                                     anchors, type pairings, etc. to avoid
{{DENY_LIST}}                    <- V1, V2: standing anti-slop list + this
                                     project's own additions

## 2. Assets you must use, verbatim                               [A6-3]
{{FONT_SHORTLIST_WITH_BASE64}}   <- entries pulled from font-catalog.json,
                                     already pre-subsetted; paste the given
                                     base64 strings verbatim, never invent one
{{FROZEN_TOKEN_MANIFEST}}                                         [A6-4]
                                     <- token-manifest.json's full name list

## 3. What to produce
Ten direction capsules: {{CAPSULE_SPEC}} (26-slot vector + 40-80 word
manifesto each). One gallery artifact previewing all ten as hero cards, each
rendered at BOTH a desktop frame and a 390px-wide portrait frame.  [A6-6]

## 4. Return format
{{RETURN_FORMAT_SPEC}}           <- §6.2's envelope, verbatim
{{PER_ITEM_COUNTS_TABLE}}        <- see §6.2's revised countsDeclared

## 5. Before you finish
{{SELF_AUDIT_INSTRUCTION}}                                        [A6-7]
                                     <- "recount your manifest against what
                                     you actually emitted; list any gap"
```

Stage B (per-shortlisted-direction deep dive) reuses sections 0, 2, 4, 5 verbatim (this is *why* demands 8 and 9 require verbatim re-pasting — see §6.3's conversation policy) and replaces section 3 with the full DTCG token expansion plus identity-carrying component instances for the one direction, scoped by §6.2's revised per-item `countsDeclared`.

**Length target.** The generated **prompt text itself** (what the user pastes in — distinct from the response budget §6.3 governs) is targeted at **≤ ~1,600 words / ~2,200 tokens for Stage A** and **≤ ~2,400 words / ~3,300 tokens per Stage-B chunk** (the font shortlist and frozen manifest dominate Stage B's length, since both are re-pasted verbatim per demand 8/9). **[I — no external precedent is cited for this figure; it is sized to stay a small fraction of a 200K context so re-pasting the manifest in every chunk per demand 8/9 is affordable, not derived from a measured source]**

**`answers.json` → prompt-slot mapping.** Generated mechanically at the end of Step 1 so no hand-authoring step can silently drop a question's answer.

| `answers.json` source (Wave, IDs) | Prompt slot | Notes |
|---|---|---|
| Wave 0 — C1, C2, C4 | `{{PRIOR_IDENTITY_NEGATIVE_CONSTRAINTS}}` | Only populated when C1 ≠ fresh; C4 = yes instead *removes* the negative-constraint framing and reuses hue/type per §4 |
| Wave 1 — P1–P5, B1–B5, A1–A5 | `{{CONCEPT_BRIEF}}` | Distilled via `concept.md`, not pasted raw — the interview answers are the source, the concept document is the compression step |
| Wave 2 — T1–T5 | `{{TASTE_PROFILE}}` | Loved/hated reference abstractions (attributes only, no reference pixels, per §7's `direction.reference-triangulation` provenance rule) + the 8 semantic-differential slider positions |
| Wave 2 — T6 | `surface.background-art-style` seed, folds into `{{NAMED_ITEM_INSTRUCTIONS}}` | Also gates which art Lane (§6.3) is even in play |
| Wave 2 — T7 | `{{NAMED_ITEM_INSTRUCTIONS}}` → icon-set instructions | Restyle-existing vs custom-drawn |
| Wave 2 — T8 | `{{NAMED_ITEM_INSTRUCTIONS}}` → cursor component instructions | User-named item ("cursor look") |
| Wave 2 — T9 | `{{NAMED_ITEM_INSTRUCTIONS}}` → top-ribbon instructions | User-named item ("top ribbon design") |
| Wave 2 — T10 | `{{NAMED_ITEM_INSTRUCTIONS}}` → background art-style instructions | User-named item (the FruitSync example) |
| Wave 3 — D1, D2 | `{{CONCEPT_BRIEF}}` (theming mode, density) | D1 sets whether every token needs a dual-mode value from Stage B onward |
| Wave 3 — D6 | `{{CAPSULE_SPEC}}` component checklist | Directly gates which §8 items are even asked for — unchecked items are not built |
| Wave 3 — D7 | `{{CAPSULE_SPEC}}` form-type checklist | |
| Wave 3 — D8, D9, D10 | `{{NAMED_ITEM_INSTRUCTIONS}}` → typeface mood, front-animation, button-style | User-named items ("a font", "an animation for the front", "a button") |
| Wave 3 — M1–M3 | `{{NAMED_ITEM_INSTRUCTIONS}}` → `motion.expressiveness` seed | Single 0–1 scalar per §7 |
| Wave 4 — X1–X3 | `{{DENY_LIST}}` / gate-strictness note | X3 adds the APCA instruction only when wave-2 answers point dark |
| Wave 4 — X4–X6 | `{{RETURN_FORMAT_SPEC}}` performance annotations | Feeds the GPU-tier ladder demand on tier-C/immersive items |
| Wave 4 — L1, L2 | `{{CONCEPT_BRIEF}}` locale/RTL note | L2 = yes is a structural constraint the grid must be told about before Stage B, not after |
| Wave 4 — N7–N11 | `{{CONCEPT_BRIEF}}` brand-asset constraints | N8/N9 hard-constrain the colour solver and font tier respectively |
| Wave 5 — V1, V2 | `{{DENY_LIST}}` | Per-project deny-list layered on the standing anti-slop list |
| Z1, Z2 | Not a prompt slot — routes Step-2 delivery mode (§6.5 local vs web) and the Step-5 variant multiplier, not Stage-A content |
| Z4 | Gates whether the Art chunk's Lane C option (§6.3) is even offered | Default assume no per §5's own note |

### 6.1 What the prompt must demand

The **Applies to** column closes the gap between this list and §6.5: a demand written for the web-artifact medium does not automatically transfer to a local subagent, and pretending it does either over-constrains local output or silently drops the constraint. See §6.5 for the full local-envelope contract this column points at.

| # | Demand | Why | Applies to |
|---|---|---|---|
| 1 | **DTCG 2025.10 format verbatim**, with a literal worked example, not a description | The spec changed the colour token shape to an object with `colorSpace`/`components`/`alpha`/`hex`; any model working from pre-2025 examples emits a hex string and the pipeline breaks **[V — designtokens.org/TR/drafts/format/, version 2025.10, dated 17 June 2026]** | Both |
| 2 | **OKLCH hue anchors, chroma ceiling, neutral temperature, scheme strategy — never hex swatches** | The colour solver (Leonardo model: declare target contrast ratios, solve for colours) runs locally. Asking for swatches gets swatches that fail contrast **[V — adobe/leonardo contrast-colors README]** | Both |
| 3 | **An explicit statement that OKLCH hue ≠ HSL hue** — 0° is magenta, red is ≈41° | A prompt that says "hue 0 for red" silently produces a magenta-based palette across every direction **[V — MDN oklch(), Baseline May 2023]** | Both |
| 4 | **Font pairings chosen from an embedded, pinned OFL shortlist** — never open-ended naming | Closes the hallucinated-foundry-licence failure and the off-shortlist-licence failure in one move, and makes the output trivially cross-checkable | Both — for local mode the shortlist is handed to the subagent as a read file (`font-catalog.snapshot.json`), not embedded prose, but the constraint (pick from this closed list only) is identical |
| 5 | **A base64 `data:font/woff2` @font-face for each direction's display face**, subset to the preview glyph set | The artifact CSP permits `fonts.googleapis.com` under `style-src` but restricts `font-src` to `data:` and `claudeusercontent.com` — the CSS loads and the WOFF2 is blocked, so a Google-Fonts direction previews in a system face. **You would pick a look you never saw.** A Latin-subset display WOFF2 is typically 8–20KB, ~11–27KB base64 **[V — content-security-policy.com + claude-artifacts-guide CSP list; size figures are inference]** ¹ | Both — web rationale is the CSP restriction above; local rationale is demand 7 (self-contained output, no CDN dependency in the exported static site). Same outcome, different reason |
| 6 | **Vanilla HTML + inline CSS + optional vanilla JS for every component variant — never React** | Sidesteps the unpublished, unstable React-artifact import allowlist, and vanilla fragments are what the editor's anchored DOM actually needs | Both — web rationale is the React-import allowlist; local rationale is **[I]** keeping one editor-ingestible shape regardless of which path produced the file, so the editor never needs a second parser |
| 7 | **Everything self-contained** — inline `<style>`, data-URI images, no CDN links, no `@import` | The artifact CSP blocks all outbound requests; a `<link>` to Google Fonts silently fails | Both — required for the exported static site (D3) independent of which path generated it |
| 8 | **A frozen token-name manifest, re-pasted verbatim in every chunk** | Across chunks/conversations the model re-invents names (`--color-accent` in chunk 1, `--accent` in chunk 3). Component swaps then resolve to nothing and render unstyled with no error. The ingest **hard-rejects** any key not on the manifest — no fuzzy remapping, which would be a new bug factory | Web: re-pasted as prose text in every prompt (mechanism required by chat statelessness across conversations — see §6.3's conversation policy). Local-equivalent: the subagent reads `token-manifest.json` directly at every invocation; the freeze constraint is identical, the re-pasting mechanism is not needed since there is no chat transport in between |
| 9 | **Prior-direction parameters as negative constraints in every subsequent chunk** | Divergence must be enforced by the skill, not hoped for from the model. "Do not produce a direction whose hue anchor is within 30° of any of these, or that reuses any of these type pairings" | Same web/local split as demand 8 |
| 10 | **A per-item `com.acos.llm` extension block** — `{usage: string[], rules: string, antipatterns: string[]}` on every semantic token | Copied from GitHub Primer's shipped `org.primer.llm` pattern. This is what lets the building agent select the right token without guessing **[V — primer/primitives functional/*/\*.json5, quoted verbatim]** | Both |
| 11 | **A `com.acos.pick` block** — `{pickable, slot, directionId, variantIndex, derivedFrom[]}` | The editor renders a control **only** where `pickable: true`. This is how D1's "derived values are never picked" becomes structurally enforced rather than documented | Both |
| 12 | **A `com.acos.direction` block** — `{id, vectorHash}` | The builder rejects any token whose hash ≠ the active direction. Stops cross-contamination during component swaps | Both |
| 13 | **A root capability manifest declaring expected counts per group, per item** | Makes truncation detectable: the skill compares declared to actual on ingest. **Revised**: counts must be per-item (see §6.2), not just per-group, or a 1-variant response for every component still satisfies a group-level total | Both |
| 14 | **A paired reduced-motion variant for every motion item**, art-directed with WCAG-exempt vocabulary (opacity/colour/blur), never `animation: none` | The editor cannot invent a good reduced variant for an animation it never saw the internals of. If this isn't demanded upstream, every animated element degrades to a generic freeze | Both |
| 15 | **A 390px-wide preview frame inside every direction artifact**, alongside the desktop frame | Directions are otherwise judged only at desktop width; art tied to a 16:9 hero doesn't crop to 390×844 portrait, and the user selects a direction they've never seen at the viewport most visitors use | Web-only — this is specifically about a claude.ai *artifact's* live preview surface. Local mode has no artifact concept; §6.5 substitutes the skill's own local dual-viewport render harness |
| 16 | **A self-audit closing step**: recount the manifest against what was actually emitted and list any gaps | Cheap; reduces how often the ingest validator has work to do | Both |

¹ **Verify before shipping the prompt spec.** Open a claude.ai artifact with a Google Fonts `<link>` and check computed `font-family` in devtools. This is a 60-second test that determines whether typography can be judged on the web side at all. See §17-O1.

### 6.2 The exact return-format schema

**The wire format is a single envelope, not two competing ones.** An earlier draft of this section specified triple-backtick fence-splitting in this subsection and a one-block-per-chunk paste in §6.4 — those are mutually exclusive parsers, and the format most load-bearing to the top adoption risk (§17-R7) cannot be left ambiguous. **This is now one format, defined here, and §6.4 describes the user-facing consequence of it rather than a second format.**

**Envelope shape.** Every chunk's *entire* response is wrapped in **one outer fence of five backticks.** Nothing outside that fence is part of the payload — any prose commentary the model adds must come before the opening fence or after the closing one. Inside the outer fence, ordinary markdown code fences (three backticks, or four if a file's own content needs to contain a three-backtick fence) mark each file, each opening with a `FILE:` comment in that block's own comment syntax. **Rule: no inner fence may use ≥5 backticks; the outer fence is always exactly 5.** This is what makes the nesting unambiguous — an outer parser that looks for the first and last line matching `^`{5}$` cannot be confused by inner blocks of 3 or 4.

Worked example (rendered here inside a 6-backtick documentation fence, one level above the outer 5-backtick protocol fence, purely so this PRD can display it literally):

``````
`````
FILE: manifest.json
{
  "templateVersion": "1.1.0",
  "chunk": { "index": 2, "of": 6, "kind": "direction-deep-dive", "directionIds": ["d03"] },
  "files": [
    { "path": "tokens/d03.tokens.json", "lines": 412, "sha256Prefix": "a91f0c" },
    { "path": "components/d03/button-primary/01.html", "lines": 38, "sha256Prefix": "77bd21" }
  ],
  "countsDeclared": {
    "directions": 1,
    "components": { "button-primary": 10, "marketing-hero": 12, "top-ribbon": 10 },
    "artwork": {}
  },
  "continuation": { "status": "complete" },
  "terminator": "<<<ACOS-END-a7f3>>>"
}

```json
// FILE: tokens/d03.tokens.json
{ ... }
```

```html
<!-- FILE: components/d03/button-primary/01.html -->
<!-- ACOS-COMPONENT id=d03.button-primary.01 item=button-primary direction=d03
     tokens-used=--color-accent,--radius-md,--motion-fast slots=label,icon? -->
<button class="btn-primary">…</button>
<style>…</style>
```

<<<ACOS-END-a7f3>>>
`````
``````

The `manifest.json` block is not itself wrapped in its own inner fence — it is the first thing inside the outer fence, in plain JSON, immediately followed by the per-file inner-fenced blocks. This keeps the outer-fence parse a single dumb split (find the `` ````` `` lines, take everything between) with no risk of the manifest's own braces being mistaken for a fence boundary.

**Ingest contract.** The skill parses the outer 5-backtick envelope first (isolating the full payload text), reads the leading `manifest.json` block, then splits the remainder on inner fenced code blocks and reads each block's `FILE:` line, writes to that path, then validates:

| Check | On failure |
|---|---|
| Outer 5-backtick envelope present, opens and closes | **Hard fail** — nothing outside a well-formed outer fence is trusted, regardless of how plausible it looks |
| Manifest present and parseable | **Hard fail.** Name exactly what's missing; offer re-paste, a continuation prompt (see below), or Local Regeneration |
| Terminator line present as the final line inside the outer fence | **Hard fail** — this is a truncation, and a truncated CSS block is still *valid CSS* that renders. This is the corruption-without-symptom class and the single most expensive failure at this boundary. **On this failure the skill does not write anything into the live session tree (`02-system/`) — see the truncation-and-continuation protocol below for what it does instead** |
| `sha256` of each file's body (bytes after the `FILE:` line, normalised to LF line endings with exactly one trailing newline, hashed before any repair pass) matches the declared `sha256Prefix` (first 6 hex chars) | **Hard fail** on the mismatching file only; auto-draft a repair prompt naming it. This is the check that catches a line-boundary-aligned truncation that a line-count check would pass trivially — see §17-R3 |
| Per-file line counts match declared | Cheap pre-filter only, run before the hash check; a mismatch here short-circuits straight to the hash-check's failure path rather than being treated as a separate signal |
| `countsDeclared` per item == the §8.3 inventory count for that item's tier and the phase's priority gate (v1/v2/v3) | Mark the mismatching item(s) MISSING by name, ingest everything else, draft a targeted repair prompt naming exactly which item is short and by how many variants. **This is the check that makes silent under-delivery — e.g. 1 variant returned where §8 specifies 10 — visible instead of passing** |
| JSON parses strictly | Attempt a **bounded tolerant repair pass** — exactly three transforms and no others: trailing-comma removal, single-quote-to-double-quote conversion, unquoted-key quoting. Any failure the bounded pass doesn't fix is a hard failure, not a wider free-form rewrite (the paste channel is a security boundary per §12.14; an open-ended repair pass would itself be new attack surface). Everything auto-fixed is logged verbatim, before/after, to `import-report.json` | 
| Every token key ∈ frozen manifest | **Hard reject** the offending key. No fuzzy remapping | 
| DTCG schema valid | Reject with the specific path that failed | 
| No `fetch(`, `eval(`, `new Function`, non-local `import(`, `process.`, `child_process`, remote `<script src>`, remote `@import`/`url()`, inline event handlers | Quarantine that item; continue | 
| Every contrast pair recomputed locally (WCAG 2 + APCA) | Auto-nudge OKLCH lightness deterministically: adjust `L` toward the nearest passing value in steps of 0.01, capped at a maximum total shift of ΔL 0.05; if 0.05 is insufficient to pass, stop and flag for human confirm rather than continuing to nudge. Never trust a stated pass | 
| Every font ∈ pinned OFL shortlist | Auto-substitute nearest OFL match in the same classification, log a licensing note, continue non-blocking | 
| Every asset reference resolves inside the bundle | Mark that one variant DEGRADED, exclude it from the swap bar, don't block the rest |

**Truncation-and-continuation protocol.** A hard fail on the terminator check does not mean "ask the user to re-paste and hope." Three mechanisms, in order:

1. **First-run ceiling calibration [I — no measured figure exists anywhere in this PRD; §17-O2 states the real ceiling is unverified and explicitly warns not to design around published estimates].** The *first* Stage-B chunk of every session has an inline marker comment inserted every ~2,000 characters inside the largest file it emits (typically the direction's token file), e.g. `/* ACOS-MARK-14 */`. Whether or not that chunk truncates, the skill counts the highest marker actually received and records `calibratedCeilingChars` in `session.json`. Every subsequent chunk in the session is planned against `calibratedCeilingChars × 0.85` (a fixed safety margin — **[I]**, not empirically tuned). This makes the "difference between 2 conversations and 12" (§17-O2) a measured session property instead of a guess, at the cost of one marker-comment convention the web model must also be told to honour, which is itself one more thing that can go unfollowed — **noted, not eliminated**.
2. **Resume-from-last-complete-file.** On a truncation, the skill does not write into `02-system/`, per A8 — but it *does* stage everything up to and including the last file whose hash validated, into a scratch directory (`01-prompt/staging/`) that is never treated as part of the live system. From that staging state it computes `resumeAfter: "<path of last validated file>"` and auto-drafts a continuation prompt: the same frozen manifest and negative constraints (already required verbatim by demands 8/9), plus an explicit instruction to skip every file up to and including `resumeAfter` and continue from the next one in dependency order. Once a continuation response validates in full, staged + new files are merged into `02-system/` together as one unit — so A8's "does not write a partial system" holds for the canonical tree at all times, while the user is never asked to regenerate work that already arrived intact.
3. **Automatic bisection on repeated truncation.** If the *same* chunk (by `chunk.index`) truncates a second time within roughly the same file (± the file whose emission was in progress at both cutoffs), the skill does not retry the same continuation a third time. It splits that chunk's remaining file list at the midpoint along the dependency order below, and issues two continuation prompts covering the two halves instead of one. This repeats to a maximum of 3 splits per original chunk; past that the skill recommends Local Regeneration Mode (§6.5) explicitly rather than continuing to bisect indefinitely.

**Open question (no known mitigation):** none of the above changes the fact that a chunk sized against an *unmeasured* ceiling can still truncate on the very first try of a session, before calibration has any data. The calibration marker reduces the cost of that first truncation (a targeted resume instead of a blind re-paste) but does not prevent it. This is inherited from §17-O2 and is not resolved here.

**File emission order is dependency order, not size order.** An earlier draft ordered files smallest-first "so a truncation loses the least" while separately stating that a truncation causes nothing to be written — those two claims contradict each other (if nothing is written, order doesn't affect loss; if something is partially kept, as the staging mechanism above now does, smallest-first is actively wrong, since it guarantees the *last* thing emitted — and therefore the *first* thing lost — is the direction's own token file, the one dependency every component in the chunk needs to render at all). **Order is now: tokens first, then components in the order listed in the manifest, then artwork references last.** This maximises how much of a truncated chunk's staged content is actually usable by the continuation protocol above, since the highest-fan-out file is the one most likely to have arrived complete. **This supersedes the "smallest-first" wording carried in §17-R3's mitigation list; that section's wording should be updated to "dependency-ordered emission" in a later editing pass — flagged here, not corrected there, since this section does not own §17.**

### 6.3 Chunking strategy

Hard numbers from the user's own precedent: each FruitSync variant page is 35–43KB of self-contained HTML+CSS (~10–12K tokens); the shipped release index is 92KB **[V — `wc -c` on 6 variant files]**. A full direction at that fidelity is ~40KB minimum. Ten directions plus 20 artworks is ~400KB (~110K tokens) against a 200K claude.ai context that artifacts count against.

| Chunk | Content | Approx size |
|---|---|---|
| A | ~10 direction capsules (26-slot vector + 40–80 word manifesto each) + ONE gallery artifact previewing all 10 as hero cards at desktop AND 390px | See arithmetic below — **not simply "small"** |
| B₁…Bₙ | Full DTCG expansion + identity-carrying component instances for **one shortlisted direction** each, at the §8.3 per-item variant counts declared in that chunk's `countsDeclared` | ~40KB each |
| Art | The artworks with `suitsDirections[]` tags, per the lane split below | Lane-dependent — see below, **not "variable" left unstated** |

**Why Stage A is thin:** it is what the user actually judges. Generating all 10 in full upfront wastes ~90% of the output because 9 expansions are discarded.

**Chunk A's font-byte arithmetic, done explicitly.** Demand 5 requires a base64 display-face cut in every direction artifact, and §6.1's own sizing puts that at ~11–27KB base64 per face. Ten directions in one gallery, naively, is 110–270KB of base64 alone — 30–70K tokens — inside the chunk this table used to call "small" without doing the multiplication. Two mitigations, both applied:

1. **The base64 does not need to round-trip through the paste-back.** Because `font-catalog.json` is skill-owned (§6.0), the Stage-A capsules the model returns for ingestion only need to reference a `familyId` from the catalog, not repeat its bytes — the skill splices the correct pre-subsetted string back in locally when it needs one. This halves the transport problem: the base64 must still appear once, in the **live gallery artifact's rendered HTML** (so the user can actually see the typeface), but it does not also need to appear a second time in the machine-readable files the ingest pipeline reads back.
2. **The gallery's glyph subset is smaller than a full direction's.** A hero-card preview renders a fixed, short piece of text (the direction's name and a few words of its manifesto headline) — not the full alphabet a live component library eventually needs. Subsetting each display face to only the glyphs actually used in its specific hero card, rather than the full Latin range, is expected to shrink the per-face cut well below the 11–27KB figure. **[I — no measured figure exists for a glyph-count-limited subset; this is a directionally sound optimisation, not a verified number. It should be measured on the first real run and the result recorded back into this section]**

Even with both mitigations, this remains the chunk most likely to be tight against an unmeasured ceiling (§17-O2), and it is the chunk the user judges first. **If it truncates, the calibration-and-continuation protocol in §6.2 applies to it exactly as to any other chunk — Chunk A gets no special exemption.**

**The Art chunk's wire format, by lane.** §7.9 defines three honestly-labelled lanes for artwork; this subsection was previously silent on what "the Art chunk" actually transports, which left the ingest with no branch to implement. Each lane is a different wire shape:

- **Lane A — code-drawn art.** Transported exactly like a component: `FILE: artwork/aNN.svg` (or a `<canvas>`/CSS-gradient fragment for non-SVG techniques), token-referencing via `var(--...)` / `currentColor` so it re-skins under a direction swap, inside the same envelope as Chunk B. **Per-artwork size cap: 15KB inline SVG source [I — no external precedent cited; sized to keep 20 pieces well inside a single chunk's budget].** This is the only lane that actually appears inside the paste-back Art chunk.
- **Lane B — asset ingestion.** Transports **zero bytes** through the chat channel. When Step 0's question C3 detects an existing asset library, the Art chunk instead carries a manifest-only reference: `{path: "<user's local asset path>/hero-01.png", suitsDirections: ["d03","d07"], licenceNote: "user-owned, per C3"}`. The skill reads the actual file from disk directly; the web model never sees or transports the pixels.
- **Lane C — external raster generation.** **Explicitly out of scope for this chunk and this envelope.** Per §17-R1's mitigation, this is a separate, clearly-labelled hand-carry with its own licence manifest, run only if Z4's answer indicates an image-generation connector is active in the session (default assumed no). Nothing in §6.2's ingest contract applies to Lane C output; it has its own, not-yet-specified runbook.

**Open question carried forward, not resolved here (§17-O15):** whether "20 artworks" means 20 individual pieces or 20 style **sets** changes the Lane-A size arithmetic by roughly an order of magnitude and is a user decision, not something this section can default. Until O15 resolves, the Art chunk's total budget is stated per-piece above and must be re-derived once O15 is answered.

**claude.ai constraint:** the platform commits to one live-updating artifact per turn — a new reply iterates the *same* artifact in place, and separate artifacts accumulate *across* turns via a panel switcher. There is no documented mechanism for one response to open ten independently-addressable artifacts **[V — support.claude.com/en/articles/9487310 + multiple 2026 guides converging; medium confidence]**. So: at most ONE artifact per response (the gallery, for eyeballing), and the machine-readable payload in ordinary fenced code blocks, which have no such limit.

**Conversation policy.** Because demands 8 and 9 require the frozen manifest and every prior direction's negative constraints to be re-pasted verbatim in *every* chunk, and because §17-O2 leaves the true per-conversation ceiling unmeasured, the default policy is **one claude.ai conversation per chunk.** The skill's generated prompt for each chunk is fully self-contained (it already carries the manifest and constraints per demand 8/9) specifically so this policy is safe — the user is told, in plain words, in the skill's own output: *"Start a new chat for this one."* This removes context-exhaustion-partway-through-a-chunk as a failure mode entirely, at the cost of the conversation-switching overhead already priced into §6.4's operation count. **If §17-O27 resolves that the user's plan includes Projects**, the schema and worked examples could instead live in project instructions and be omitted from each chunk's prompt text — a smaller-prompt variant of this same policy, not evaluated further here pending that answer.

### 6.4 The one-paste protocol

Naive hand-carry is 35–60 discrete copy → switch app → paste → name → file operations at ~60–90s each: **45–90 minutes of the user's hands per generation cycle**, and Step 5 makes it a loop. This is the most likely way the product quietly dies.

The protocol, using the single wire format defined in §6.2: **the model's entire response for a chunk is the one outer 5-backtick envelope; the user does one `Cmd+A` / `Cmd+C` per chunk, full stop.** The skill ingests via `pbpaste` on a one-word command, parses the outer fence, then the inner file blocks, per §6.2. ~40 operations become ~5: paste-and-run per chunk, times the chunk count, plus the "start a new chat" step §6.3's conversation policy adds between chunks. **[I — sized against first-party artifact counts]**

### 6.5 Local Regeneration Mode (first-class, not a fallback of last resort)

The same prompt template (§6.0), the same schema (§6.1's demands, filtered by the **Applies to** column), run against a Claude Code subagent instead of claude.ai. Zero pastes, deterministic filing, schema-validated at write time. The claude.ai hop becomes an opt-in "I want the web model's design sense for this one" path.

**What "the same" and "identical validator" actually mean here — this subsection previously asserted both without defining the boundary, which is a problem because a large fraction of §6.1's demands, and all of §6.2's and §6.3's transport machinery, exist *only* because of the claude.ai artifact CSP and chat-response constraints that do not apply to a subagent writing files directly:**

- **What genuinely carries over unchanged:** the DTCG format, the OKLCH rules, the pinned font/token manifests as closed lists, the `com.acos.*` extension blocks, the reduced-motion pairing, the self-audit step, the per-item variant-count discipline, the sha256/hash-style integrity check (recomputed at write time rather than parsed from a pasted hash, since the subagent's own Write tool calls are the source of truth for what was written), and every content-level check in §6.2's ingest table (contrast, DTCG schema validity, dangerous-pattern scan, asset resolution). **These are the "validated properties" that are genuinely identical across both paths.**
- **What does not carry over, and why:** the outer 5-backtick envelope, the terminator token, the chunking-by-size strategy, the one-conversation-per-chunk policy, and the 390px-preview-inside-an-artifact demand (15) are all solutions to problems specific to a stateless chat response with an unmeasured output ceiling. A subagent invoked by Claude Code writes files directly via repeated tool calls within one turn; there is no single-message ceiling in the same shape, no fence-parsing step, and no "artifact" surface to embed a viewport toggle inside. **§19's A12 ("Local Regeneration Mode produces a bundle that passes the identical validator with zero pastes") should be read as asserting this — equivalence of validated output properties, not literal reuse of the paste-parsing code path. This section recommends that A12's wording be tightened accordingly in a later pass over §19; it is not amended here, since amending another section's acceptance criteria is out of this section's scope.**

**The local envelope contract**, replacing §6.2's paste-oriented one:

| Web-path mechanism | Local-path equivalent |
|---|---|
| Outer 5-backtick envelope, one per chunk | Not needed — files are written by direct `Write` tool calls, one per file, no fence-parsing step exists |
| Terminator token as final line, detecting truncation | Not needed in the same form — a subagent's turn either completes its planned file list or is interrupted, which is a difference in **process status**, not a text-parsing signal; the skill instead compares the `files` it asked the subagent to produce (from `token-manifest.json` + the §8 per-item counts, computed the same way as `countsDeclared`) against what actually landed on disk, file by file |
| Per-file `sha256Prefix` matched against a declared value in the pasted manifest | Recomputed **at write time**: the skill hashes each file immediately after the subagent's `Write` call returns, no declared value to trust or distrust, since there is no untrusted transport step in between |
| Chunking by size against an unmeasured ceiling (§6.2's calibration protocol) | **No-op.** A subagent is not bounded by a single-response character ceiling in the way a chat completion is; it may still be sensible to batch by direction for review-ability, but this is a UX choice, not a truncation-avoidance requirement, and the calibration marker mechanism does not apply |
| One-conversation-per-chunk policy (§6.3) | **No-op** — there is one Claude Code session, and demands 8/9's "re-paste the manifest every chunk" becomes "the subagent re-reads `token-manifest.json` and the running negative-constraints file at the start of each direction it's asked to produce," which is cheaper and cannot silently drift the way re-typed prose could |
| 390px preview frame inside every direction artifact (demand 15) | Substituted by the skill's own local dual-viewport render harness — **[I — no such harness is specified elsewhere in this PRD by name; this is a stated requirement for one to exist, following the same pattern this project has previously used for localization mock-rendering, not a description of a component that has been designed]** |

**If the PRD hard-wires the paste as mandatory, usage frequency is capped by the user's tolerance for clerical work.** Local Regeneration Mode ships in v1.

---
## 7. The design system inventory

**Structure.** A direction is a **24-slot varying identity vector plus 2 invariant records** (§7.1 still lists 26 rows; two of them — `direction.reference-triangulation` and `type.viewport-endpoints` — are declared identical across all directions and therefore cannot vary). Everything else in the system is either (a) a pure function of that vector plus shared seed tables (Utopia multipliers, Carbon/M3 motion matrices, Leonardo contrast targets), or (b) a **direction-bound authored artefact** that carries a `directionId` and is validated against the vector but is not itself a scalar slot (icon family, logo lockup system, voice profile, artwork). This is the shipped USWDS `$theme-*` architecture applied to a generated system, and it is what makes 10 coherent directions tractable instead of 10 × 800 independent decisions. **[V — uswds/uswds `_settings-typography.scss`; adobe/leonardo README; utopia.fyi calculators]**

> **Correction recorded (this pass).** The previous text asserted "a 26-slot identity vector" and "everything else … is a pure function of that vector." Both were wrong as written: two of the 26 rows are invariant, and roughly thirty rows outside Category A carry pickable numbers rather than `derived`. The revision below adds a **Kind** column, a **Scope** column and a **Priority** column to every table in §7 so that neither claim has to be inferred. The architectural consequence — that direction-bound authored artefacts exist outside the hash-bearing vector — is stated explicitly in §7.0.3 and enforced by new lints 7–10 in §7.12.

**Scale reality check.** Real systems ship 250–350 *semantic* tokens, not 80. IBM Carbon v11: 258 named colour tokens + 24 layout + 34 type. Material 3: ~50 colour roles, 15 typescale roles × 5 properties, 16 durations + 10 easings, 12 shape, 6 elevation, 4 state-layer opacities. Fluent 2: ~300 alias tokens. **Budget ~600–900 resolved tokens per complete direction. [V — counted programmatically from carbon-design-system/carbon, material-web, microsoft/fluentui sources]** The user's "~80 items" is an *item* count; each item expands to 1–40 tokens.

---

### 7.0 How to read every table in §7

#### 7.0.1 Variant-count key (**Count** + **Kind**)

The single "Variants" number in the previous draft meant three different things in the same tables, and the key defined only one of them. It is now split into a **Count** and a **Kind**. Every numbered row in §7 carries exactly one Kind:

| Kind | What the number means | What the Step-2 prompt must request | What the editor renders |
|---|---|---|---|
| **`per-direction`** | **One value per direction. The count is 10 by construction** — it is the number of directions, not a menu the user chooses from. Writing 10 here is arithmetic, not a judgement | "Produce one of these for each of the 10 directions" | **No control inside a chosen direction.** The value is whatever this direction's value is |
| **`domain`** | **N mutually exclusive options.** Exactly one is in force at a time. Where N < 10 and the row is a direction slot, **several directions necessarily share a value** — this is expected, not a defect | "Choose one of the following N named options: …" (the N must be enumerated in the prompt) | A control **only** where Scope is `in-direction-repickable`; otherwise none |
| **`set`** | **N members, all delivered together.** Not alternatives. `color.gradient-set` **6** means *emit six gradients*, not *pick one of six* | "Emit all N members, named as follows: …" | A control only if the row is also `in-direction-repickable`, in which case the control picks *which member to use here*, never which members exist |
| **`derived`** | Computed from the direction vector + seed tables; the editor renders **no control** (`com.acos.pick.pickable: false`) | Not requested. Computed locally after ingest | Nothing |
| **`n/a`** | A policy, contract, or coverage checklist, not a choice | Requested as prose/JSON policy, never as options | Nothing |

**Worked disambiguation of the two rows that caused the confusion:**

- `color.gradient-set` **6** is Kind `set` — six named roles (hero wash, card sheen, text gradient, edge fade, radial glow, mesh base) that all ship in every direction. The correct prompt sentence is "emit six gradients".
- `cursor.personality` **6** is Kind `domain` — six mutually exclusive cursor personalities, of which each direction holds one. The correct prompt sentence is "pick one of six".

**Reconciliation with §20.1 (mandatory, was a live contradiction).** §7.1 gives `direction.signature-moment` a count of **10**, while §20.1 explicitly *excludes* "Ten 'signature moment' variants" in favour of 2–3 bespoke concepts. Both are now true and consistent because the Kind is stated: `direction.signature-moment` is **`per-direction`** — one signature moment *per direction*, ten in total because there are ten directions. What §20.1 excludes is a **`domain` of 10** — a catalogue the user picks a signature moment out of. §14.7's "2–3 bespoke concepts" describes how each single per-direction moment is *authored* (concept exploration inside one direction), not how many ship. **No further change required in §20.1; a one-line clarification there would be cheap and is recommended.**

#### 7.0.2 Scope key (**Scope**)

Scope answers the question the previous draft never answered per row: *once a direction is chosen, can the user change this?*

| Scope | Meaning | `$extensions['com.acos.pick'].scope` |
|---|---|---|
| **`direction-slot`** | Fixed by the chosen direction. One value per direction, authored or picked at generation time. **The editor renders no control.** Changing it means changing direction | `"direction-slot"` |
| **`site-global`** | Chosen once for the whole site and identical across all 10 directions. Survives a direction change. Examples: the contrast ladder, breakpoints, the token naming convention | `"site-global"` |
| **`in-direction-repickable`** | The user may re-pick inside a chosen direction, **but only from that direction's validity list**. This is what the Step-4 component/swap bar drives | `"in-direction-repickable"` |
| **`derived`** | Not a scope in the user-facing sense; recorded so the manifest is uniform. No control, ever | `"derived"` |

**The coherence rule (normative, and the thing that keeps D1 true).**

> Any row whose Scope is `in-direction-repickable` **must** ship a per-direction **validity list** in `token.capability-manifest`. Options absent from the active direction's list are **hidden from the editor UI, not merely warned about**. A row that cannot supply a validity list is **demoted to `direction-slot`** — it does not get a control "for now".

This is what stops the failure the audit named: a geometric-mono icon family being dropped onto an editorial-serif direction. `icon.family-spec` is `direction-slot`, so the control never exists; `art.background-scene` is `in-direction-repickable`, so the control exists but only shows pieces tagged for this direction. D1's guarantee ("derived values are computed from the direction, never picked independently") is therefore enforced by two mechanisms rather than one: `pickable: false` for derived values, and the validity list for repickable ones.

#### 7.0.3 Vector membership, and the "27th slot" problem

The audit correctly observed that if `icon.family-spec` is fixed by the direction then it is behaving as a 27th identity slot, and the vector definition is wrong. The resolution adopted here:

- **The hash-bearing identity vector is the 24 varying rows of §7.1.** Nothing else feeds `token.direction-hash`.
- **Direction-bound authored artefacts** (`icon.family-spec`, `mark.logo-lockups`, `mark.decorative-glyphs`, `system.voice-and-microcopy`, every `art.*` piece) are `direction-slot` in Scope, carry a `directionId`, and are **validated against** the vector by lints 7–10 — but they do **not** feed the hash.
- **Reason for the split (stated so it can be challenged):** the hash exists to detect cross-contamination during component swaps, and it must be cheap and stable to compute. Feeding a 6-lockup SVG system or a 40–80 word voice profile into the hash makes it brittle against whitespace, unicode and re-export noise for no detection benefit — the `directionId` already catches the contamination case. **[I — inference; this is a design decision made in this revision, not a cited practice]**

**Consequence to accept explicitly:** the identity of a direction is therefore *larger* than its hash. Two directions could share a vector hash and differ in icon family. Lint 8 (§7.12) catches that, and O34 records the residual risk.

#### 7.0.4 Priority key (**Priority**)

Same vocabulary as §8: **v1 / v2 / v3**. Added because §8 has a phase plan and §7 did not, which meant all 148 §7 items were implicitly v1 and implicitly requested in the Step-2 prompt — against a context budget §6.3 shows is already tight (~400KB / ~110K tokens against a 200K claude.ai context that artifacts count against). The v1 cut list, the resolved-token estimate, and what is deferred to Step-5 regeneration are in **§7.18**.

*Note on numbering: the audit suggested placing the cut list at "§7.14". It lands at §7.18 because three previously-missing categories (K, M and a new P) are restored at §7.14–§7.16 and the volume roll-up at §7.17. No existing §7.x number has moved, so cross-references into §7.1–§7.13 — including §20.1's reference to §7.7 — are unaffected.*

---

### 7.1 Category A — Direction core (the identity vector: 24 varying slots + 2 invariant records)

Every row here is Scope `direction-slot` by definition — that is what "identity vector" means. Kind still varies: `per-direction` rows hold a freely-authored value; `domain` rows hold one of N named options, so with N < 10 several directions necessarily share a value, and the divergence enforcement in §6.1 demand 9 must therefore work on the *combination*, not on any single slot.

| Item | Count | Kind | Scope | Priority | Rationale |
|---|---|---|---|---|---|
| `direction.manifesto` | **10** | per-direction | direction-slot | v1 | 40–80 words naming the point of view, the tension it resolves, what it refuses to do. One per direction — this IS the direction. **10 = the direction count** |
| `direction.mood-tags` | **10** | per-direction | direction-slot | v1 | 3–6 tags from a closed ~30-term vocabulary, so tags are machine-comparable for artwork affinity and Step-5 queries. The closed vocabulary is itself `site-global`; the *selection* is per-direction |
| `direction.reference-triangulation` | **n/a** | n/a | site-global (invariant record) | v1 | ≥3 named references per direction, **abstracted attributes only** (proportion, contrast strategy, rhythm) — no reference pixels retained. Provenance metadata; also the trade-dress safety measure. **Not a varying slot** — it is a record attached to each direction, which is why the vector is 24 varying, not 26 |
| `direction.signature-moment` | **10** | per-direction | direction-slot | v1 | One per direction, specified as intent + trigger + duration budget. Award-tier work has exactly one; three reads as noise **[V — prior report Findings 2, 6]**. **Kind is `per-direction`, which is why this is compatible with §20.1's exclusion of a 10-option catalogue** — see §7.0.1 |
| `typeface.display` | **10** | per-direction | direction-slot | v1 | The loudest identity carrier. If two directions share it they are not two directions. **10 = the direction count**, drawn from the pinned OFL shortlist (§6.1 demand 4) |
| `typeface.body` | **10** | per-direction | direction-slot | v1 | Ten slots that may resolve to as few as 5 distinct faces — directions can legitimately share a body face |
| `typeface.mono` | **5** | domain | direction-slot | v1 | Small, low-identity surface. Five moods span it: grotesque-mono, typewriter, terminal/bitmap, humanist, geometric. **Directions map many-to-one onto these five** (§20.2 #6) |
| `typeface.accent` | **10** | per-direction | direction-slot | v1 | One per direction *including "none"*. Making null explicit stops the generator adding a decorative face reflexively |
| `type.base-size-pair` | **10** | per-direction | direction-slot | v1 | Min/max body size. "Big generous type" vs "small dense type" is identity, and Utopia takes it as explicit input |
| `type.scale-ratio-pair` | **10** | per-direction | direction-slot | v1 | Min-viewport and max-viewport modular ratios. Where hierarchy drama lives; a pair, not a scalar |
| `color.hue-anchors` | **10** | per-direction | direction-slot | v1 | OKLCH angles for primary/secondary/tertiary/accent. Hue *relationships* (analogous/complementary/split/mono+accent) are the defining colour decision |
| `color.chroma-policy` | **10** | per-direction | direction-slot | v1 | Ceiling + curve across the lightness ramp. Separates muted-editorial from neon-arcade at identical hues |
| `color.neutral-temperature` | **4** | domain | direction-slot | v1 | Pure grey / warm / cool / tinted-by-primary. Four genuinely distinct options; more is false precision. **Ten directions draw from four options, so sharing is expected** |
| `color.scheme-strategy` | **10** | per-direction | direction-slot | v1 | Light-first / dark-first / dual-equal, plus which scheme the art was authored against. Determines which gets the hand-tuned solve. *(The three strategy names are a domain of 3; the slot value is the strategy **plus** the authored-against declaration, which is per-direction — hence Kind `per-direction`.)* |
| `density.base-unit` | **4** | domain | direction-slot | v1 | 2, 4, 6 or 8px. Only four are used in practice; 8 with a 4 half-step is the common default. **Ten directions over four options** |
| `space.scale-ratio` | **10** | per-direction | direction-slot | v1 | The multiplier table. Airy vs tight is identity — but only the *ratio* is picked; the 9 values are derived |
| `shape.radius-policy` | **6** | domain | direction-slot | v1 | Sharp-0 / subtle / soft / pill-full / squircle / asymmetric-per-corner. Six distinct corner languages |
| `shape.border-policy` | **5** | domain | direction-slot | v1 | Hairline / heavy rule / none / double-offset / plus base width. Interacts hard with elevation model — validate the pair |
| `elevation.model` | **5** | domain | direction-slot | v1 | Shadow-physical (Fluent two-light) / tint+shadow (M3 dp) / layer-only (Carbon) / border-only / glass-backdrop. **The item whose mismatch causes the most invisible incoherence** — a border-only direction must reference zero shadow tokens, and lint 6 enforces it |
| `motion.expressiveness` | **10** | per-direction | direction-slot | v1 | A single 0–1 scalar plus a productive/expressive flag that scales the whole duration and easing matrix. Carbon ships exactly this axis, which is why 16 durations and 10 easings below are `derived` |
| `grid.personality` | **10** | per-direction | direction-slot | v1 | Column intent, symmetry, whether content breaks the grid, gutter:margin proportion, baseline enforcement. Top-tier identity signal, not derivable. **10 = the direction count** |
| `surface.background-art-style` | **10** | per-direction | direction-slot | v1 | The user's named FruitSync item. Medium (flat/gradient/illustrated/pattern/noise/canvas), density, scroll behaviour, token re-skinnability. Largest continuous surface on any page |
| `texture.grain-policy` | **5** | domain | direction-slot | v1 | None / trace / film / coarse / halftone. Amplitude derived from level. *Distinct from `effect.noise-grain` (§7.6), which is the set of generator recipes this policy selects an amplitude on* |
| `imagery.treatment` | **10** | per-direction | direction-slot | v1 | Grade, duotone mapping, crop rules, subject distance, grain — *including "no photography"*. Making the null explicit prevents stock-photo default behaviour. **Resolves to one of the 8 `art.photo-grade-recipe` chains (§7.9) plus per-direction crop/distance rules — see §7.19** |
| `cursor.personality` | **6** | domain | direction-slot | v1 | **The six (enumerated, was missing):** (1) native-only, (2) custom-static single cursor, (3) custom-static with a hover/pressed cursor set, (4) follower-dot (native hidden, JS-tracked element), (5) follower-with-morph (magnetic snap to interactive targets), (6) hybrid (native cursor retained + decorative trailing layer). **Hard browser limits:** capped at 128×128 in Firefox and Chromium (32×32 recommended), PNG or static SVG 1.1 only, hotspot x/y from top-left, and a native keyword fallback is **mandatory** — a url-only cursor is invalid CSS **[V — MDN cursor]**. Options 4–6 additionally require a pointer-coarse opt-out and a reduced-motion variant |
| `type.viewport-endpoints` | **n/a** | n/a | site-global (invariant record) | v1 | 360 → 1440. Device facts. Must be identical across all directions or they become non-comparable in the editor preview. **Not a varying slot** — second of the two invariant records |

**Vector membership statement (feeds `token.direction-hash`, §7.12):** the 24 rows above excluding `direction.reference-triangulation` and `type.viewport-endpoints`, hashed **in the exact table order above** over a canonical serialisation defined in §7.12. Nothing outside this table feeds the hash.

### 7.2 Category B — Colour tokens (mostly derived)

| Item | Count | Kind | Scope | Priority | Rationale |
|---|---|---|---|---|---|
| `color.primitive-ramps` | derived | derived | derived | v1 | Leonardo model: declare colorKeys + target ratios, **solve** for colours. Picking swatches by eye is the exact failure Leonardo removes |
| `color.ramp-step-count` | derived | derived | derived | v1 | Falls out of the contrast ladder: as many steps as distinct targets plus interpolation headroom (10–13 typical) |
| `color.surface-roles` | derived | derived | derived | v1 | background, surface, surface-dim, surface-bright + a **5-step container ladder** (lowest/low/base/high/highest). The ladder is what makes dark mode readable; a single background+card pair is the #1 amateur tell |
| `color.text-roles` | derived | derived | derived | v1 | 12 roles: primary, secondary, tertiary, placeholder, helper, disabled, inverse, on-color, on-color-disabled, error, link, visited |
| `color.border-roles` | derived | derived | derived | v1 | subtle (per layer 00–03), strong (per layer), interactive, disabled, inverse, tile, focus, divider — ~16, all lightness offsets from their layer |
| `color.icon-roles` | derived | derived | derived | v1 | 7 roles at a fixed +0.5:1 contrast offset from text (thin strokes need more) |
| `color.brand-roles` | derived | derived | derived | v1 | ~20: primary/on-primary/primary-container/on-primary-container × 3, plus M3's `fixed` and `fixed-dim` variants that persist across schemes |
| `color.status-roles` | derived | derived | derived | v1 | error, warning, success, info, caution-major, caution-minor + inverse + container + on-container. Status hues are near-universal; only chroma and temperature adjust |
| `color.state-layer-opacities` | derived | derived | derived | v1 | **4 numbers replace Carbon's ~60 state-suffixed colour tokens.** M3 verified: hover 0.08, focus 0.12, pressed 0.12, dragged 0.16. Seeded from M3, scaled by expressiveness ² |
| `color.focus-ring` | derived | derived | derived | v1 | Outer + inner ring (two-tone so it reads on any surface — Fluent ships `colorStrokeFocus1/2`), width, offset, style, radius-follow, on-image variant. **Geometry fixed by WCAG 2.2 SC 2.4.13**: ≥ the area of a 2px perimeter, ≥3:1 focused-vs-unfocused. Never pickable |
| `color.scheme-declaration` | derived | derived | derived | v1 | **NEW (closes the sixth "invisible surface" — the one still missing after the previous pass).** The root `color-scheme` declaration (`light`, `dark`, or `light dark`) emitted from `color.scheme-strategy`. **It is the token the other five depend on:** `accent-color` on native controls and any `scrollbar-color: auto` fallback resolve against the UA scheme, so without it a dark direction renders light native selects, date pickers and scrollbars — the exact one-second amateur tell `color.scrollbar`/`color.accent-color` were added to prevent. It is also the enabling declaration for `light-dark()`. **Emission form:** `color-scheme` on `:root` always; `light-dark()` used for role values **only** where the compiler target supports it — Style Dictionary/Terrazzo output shape must be checked against `token.compiler-target`, and where it is not safe, per-scheme role values are emitted instead (the existing `color.dark-scheme-values` path) **[I — the dependency chain is inference from how UA scheme resolution works; verify the emitted form against the pinned compiler at pin time, O33]** |
| `color.selection` | derived | derived | derived | v1 | `::selection` bg + fg with **per-scheme alpha**. Primer ships 0.2 light / 0.7 dark — nobody guesses this **[V — primer selection.json5]** |
| `color.caret` | derived | derived | derived | v1 | One value, contrast-checked against field backgrounds. Trivial, universally forgotten |
| `color.scrollbar` | derived | derived | derived | v1 | `scrollbar-color` thumb + track + hover + width. Baseline newly-available Dec 2025; auto-reverts under forced-colors. A default OS scrollbar on a dark cinematic site is an immediate tell **[V — MDN scrollbar-color]** |
| `color.accent-color` | derived | derived | derived | v1 | One declaration themes every unstyled native checkbox/radio/range/progress. **Resolves against `color.scheme-declaration`** |
| `color.overlay-scrim` | derived | derived | derived | v1 | Backdrop colour + alpha + optional blur. Glass model gets blur, flat model gets flat alpha |
| `color.skeleton` | derived | derived | derived | v1 | Base + shimmer. Needed the moment any component has a loading state |
| `color.shadow` | derived | derived | derived | v1 | Ambient + key colours, tinted not pure black. Pure-black shadows are the flattest default and should be impossible to emit |
| `color.gradient-set` | **6** | **set** | direction-slot | v1 | **Six named roles, all six shipped in every direction — not a menu.** hero wash, card sheen, text gradient, edge fade, radial glow, mesh base. Six named roles covers real usage without becoming an unaudited library. Prompt sentence: "emit six gradients, named as above" |
| `color.dark-scheme-values` | derived | derived | derived | v1 | **A full second solve, not an inversion.** M3 ships per-scheme role values; Carbon ships four themes (white/g10/g90/g100), not two inverted ones. Flipping L produces the classic over-saturated halating dark mode |
| `color.high-contrast-scheme` | derived | derived | derived | v2 | Third solve at an elevated contrast multiplier via `prefers-contrast: more`. Literally one parameter change in Leonardo |
| `color.forced-colors-mapping` | **n/a** | n/a | site-global | v1 | Which elements opt out of `forced-color-adjust`, where borders must be re-added, which decorative layers hide. Dictated by OS keywords, but must be an explicit checklist — forced-colors silently deletes background-based affordances. **A forced-colors render check belongs in the LOCK gates (§13); it is a media-query render, not a new tool. Recorded as required §13 addition — see A91** |
| `color.print-scheme` | derived | derived | derived | v2 | Light scheme with chroma flattened, link URLs expanded, page breaks, decorative layers suppressed |
| `color.syntax-highlight` | **4** | domain | direction-slot | v2 | light-classic, light-muted, dark-classic, dark-vivid, mapped from direction hues. Each direction resolves to one light + one dark member of this domain. Carbon ships ~90 syntax tokens; 12 roles suffice for a marketing site |

### 7.3 Category C — Typography

| Item | Count | Kind | Scope | Priority | Rationale |
|---|---|---|---|---|---|
| `type.role-set` | derived | derived | derived | v1 | ~18 roles (display/headline/title/body/label L·M·S + caption, overline, quote, code, lede) × 5 properties = ~90 values, all computable from typeface picks + scale ratio |
| `type.scale-steps` | derived | derived | derived | v1 | Pure Utopia math from 6 inputs. Hand-picking a step is how a scale loses its ratio |
| `type.weight-plan` | derived | derived | derived | v1 | Hard-capped at 4 static weights or 1 variable file per family. A weight exists only if a role references it |
| `type.line-height-map` | derived | derived | derived | v1 | Deterministic inverse function of size. M3 verified: display-large ≈1.12, body-small ≈1.33 |
| `type.tracking-map` | derived | derived | derived | v1 | **Sign flips with size** — M3 verified: display-large −0.015625rem, body-small +0.025rem. One derived curve reproduces the whole map |
| `type.measure` | derived | derived | derived | v1 | 60–75ch body, 45–60ch lede, ~40ch pull quote. Enforceable as a lint on the built page |
| `type.fallback-metrics` | derived | derived | derived | v1 | Local `@font-face` with `size-adjust`, `ascent-override`, `descent-override`, `line-gap-override` from the **real font file's metrics**. **Computed by the skill after the typeface pick, never requested from claude.ai** — it needs the actual file. Highest-leverage invisible token family for CLS |
| `type.loading-strategy` | **3** | domain | site-global (per-face override permitted) | v1 | swap+preload / optional / block-with-100ms-cap. **Chosen once for the site**, because a mixed strategy across faces produces inconsistent first paint. Constrained by licence class: OFL may be self-hosted; Fontshare-class must be CDN-linked and never vendored — so a per-face override is permitted **only** where the licence class forces it, and the override is recorded in `token.license-manifest` |
| `type.text-wrap-policy` | **n/a** | n/a | site-global | v1 | `balance` for headings, `pretty` for prose, `stable` for editable. Baseline Oct 2024, and the correct answer is universal. Hard limits make it non-negotiable: `balance` applies only to ≤6 lines in Chromium / ≤10 in Firefox; `pretty` has a documented performance cost **[V — MDN text-wrap-style]**. **Lint: reject `text-wrap: balance` on any block that renders >6 lines at any of the five breakpoints** — see A92 |
| `type.numeral-style` | **4** | domain | direction-slot | v1 | lining-proportional (prose), lining-tabular (data), oldstyle-proportional (editorial), oldstyle-tabular. The direction holds the *default*; **tabular is forced by context in tables, stat bands and price columns regardless of the direction's default** — that override is derived, not picked. Validate the pick against the chosen face's support |
| `type.emphasis-policy` | **6** | domain | direction-slot | v1 | True italics / small caps / weight shift / colour shift / letterspaced uppercase / forbidden-list. **Declaring the forbidden ones matters more** — faux-italic on a face without an italic is a visible defect. *(The "forbidden-list" member is the policy's escape hatch and is always present alongside whichever of the other five is chosen.)* |
| `type.underline-style` | derived | derived | derived | v1 | thickness, offset, skip-ink, hover/visited transitions, from the body face's stroke weight and x-height. Default browser underlines are one of the most reliable amateur signals |
| `type.list-marker-style` | **6** | domain | direction-slot | v1 | disc, dash, custom glyph, numeral-in-shape, icon, none-with-indent. Lists appear on every content page; default markers undo a lot of typographic work |
| `type.quote-treatment` | **6** | domain | direction-slot | v1 | **The six (enumerated):** (1) hairline rule + indent, (2) oversized quotation mark, (3) plain indent with size bump, (4) colour block / tinted panel, (5) hanging-punctuation editorial, (6) full-bleed display quote. Each carries attribution styling and the quote glyph set for the direction's faces |
| `type.lede-and-dropcap` | **5** | domain | direction-slot | v1 | Lede bump / drop cap / raised cap / none / small-caps-opening. Editorial directions use it; product directions must not |
| `type.prose-rhythm` | derived | derived | derived | v1 | Heading-to-body margins, list spacing, figure/caption spacing. Hand-tuning is how rhythm dies |
| `type.script-and-rtl-coverage` | **n/a** | n/a | site-global | v1 | Declared coverage per face, logical properties (`inline-start`/`end`, never left/right), RTL mirroring rules. A correctness requirement — retrofitting logical properties is expensive, and this project has already paid that bill once. **Extended by Category K (§7.14)** |

### 7.4 Category D — Space, size, layout

| Item | Count | Kind | Scope | Priority | Rationale |
|---|---|---|---|---|---|
| `space.scale-steps` | derived | derived | derived | v1 | 9 fluid steps 3xs…3xl. Utopia default multipliers verified: 0.25 / 0.5 / 0.75 / 1 / 1.5 / 2 / 3 / 4 / 6 relative to base **[V — utopia.fyi/space/calculator]** |
| `space.one-up-pairs` | derived | derived | derived | v1 | 8 pairs that grow one step across the viewport range. What makes *spacing* responsive, not just type |
| `space.custom-pairs` | derived | derived | derived | v1 | Named non-adjacent pairs (e.g. s-l) for section padding. Typically 2–4 per site |
| `space.section-rhythm` | derived | derived | derived | v1 | **The single value most responsible for whether a page reads as composed or as stacked blocks** |
| `layout.breakpoints` | **n/a** | n/a | site-global | v1 | 320 / 390 / 768 / 1280 / 1440 authored; Primer's shipped set (320, 544, 768, 1012, 1280, 1400) as reference. Shared across all directions so the editor preview and D2's constraint model mean the same thing everywhere ³ |
| `layout.container-breakpoints` | **3** | **set** | site-global | v1 | **NEW — closes the container-query hole.** §11.5 mandates `container-type: inline-size` on every block wrapper with component internals written in `@container`, and A46 gates it, but no container-size thresholds existed anywhere. **The three named thresholds, derived from the 12-column module at the 1280 authoring breakpoint** (content 1200px, gap 24px → column 78px; a 3-col slot = 282px, a 6-col slot = 588px, a 12-col slot = 1200px): `cq-narrow` **< 20rem/320px** (≈ a 3-col slot and everything below), `cq-medium` **20rem–37.5rem / 320–600px** (≈ a 4–6-col slot), `cq-wide` **≥ 37.5rem/600px** (≈ 7-col and up). Emitted as literal `rem` in the `@container` conditions. **Constraint:** container-query size conditions do not accept `var()`, so these thresholds cannot be referenced as custom properties inside the condition — the build step must inline them, and `token.raw-value-lint` must **exempt** `@container` preludes or every component will fail the raw-value grep **[I — the `var()` limitation is stated from working knowledge and is load-bearing; verify before implementation, O33]** |
| `layout.container-name-registry` | **n/a** | n/a | site-global | v1 | **NEW.** The closed list of `container-name` values a component may query (`wb-section`, `wb-block`, `wb-media`, `wb-card`, `wb-form`), plus the rule that a component queries only its **nearest named ancestor**. Without a registry, two components pick the same generic name and one silently queries the wrong ancestor — a defect with no error and no visual signal until a drag moves the component. **Lint 10 (§7.12) enforces membership** |
| `layout.container-widths` | derived | derived | derived | v1 | prose (= measure × body size), wide, full-bleed, editorial-narrow — multiples of the column module |
| `layout.grid-definition` | derived | derived | derived | v1 | Columns, gutters, margins per breakpoint + named area templates. **Critical for D2: these are what components SNAP to**, so they must be a real token set the editor reads, not decorative overlay. **The column module here is the basis for `layout.container-breakpoints` above** |
| `layout.gap-scale` | derived | derived | derived | v1 | Subset of the space scale, called out because gap and padding get conflated then drift |
| `layout.aspect-ratio-set` | **8** | **set** | in-direction-repickable (validity list = all 8 in every direction) | v1 | 1:1, 4:3, 3:2, 16:9, 21:9, 4:5, 9:16, golden. **All eight ship in every direction; the per-instance choice of which to use is the repickable part.** Constraining media to a named set is what keeps a gallery from looking hand-assembled |
| `size.icon-sizes` | derived | derived | derived | v1 | From cap-height of the adjacent type role, not from the space scale — so icons optically match text |
| `size.control-heights` | derived | derived | derived | v1 | line-height + padding + border, floor-clamped by the 24×24 target minimum |
| `size.min-target-size` | **n/a** | n/a | site-global | v1 | 24×24 CSS px (WCAG 2.2 SC 2.5.8, AA) with five exceptions: spacing, inline, user-agent control, equivalent, essential. The **spacing** exception (a 24px circle on each target must not intersect another) is what the editor checks after a drag |
| `size.avatar-sizes` | derived | derived | derived | v2 | Diameter steps + overlap offset for groups. Only if the site has people on it |
| `layout.safe-area-and-viewport` | **n/a** | n/a | site-global | v1 | `env(safe-area-inset-*)`, dvh/svh/lvh, scroll-padding for sticky headers. 100vh on mobile and anchor links landing under a sticky header are two of the most common shipped defects |

### 7.5 Category E — Layers & plumbing

| Item | Count | Kind | Scope | Priority | Rationale |
|---|---|---|---|---|---|
| `layout.z-index-scale` | **n/a** | n/a | site-global | v1 | Primer's verified ladder adopted verbatim: behind (−1), default, sticky (100), dropdown (200), overlay (300), modal (400), popover, skipLink (top). **Note the two non-obvious orderings**: dropdowns above sticky headers but below modals, and skipLink outranks everything because accessibility wins **[V — primer z-index.json5, quoted]** |
| `layout.stacking-context-rules` | **n/a** | n/a | site-global | v1 | Which properties create stacking contexts (transform, opacity<1, filter, will-change, backdrop-filter) and the rule that animated/parallax art containers must not enclose overlay-layer content. **This bites hard here specifically because D4 puts animations inside draggable containers** — a transformed art container silently traps every dropdown inside it, and presents as "the menu is behind the picture" with no obvious cause |
| `layout.editor-chrome-band` | **n/a** | n/a | site-global | v1 | A reserved band **above** skipLink for gridlines, drag handles, snap guides, component bar — plus the guarantee that LOCK strips the entire band. If editor chrome shares the site's ladder there is no clean way to *prove* it was removed (D3) |

### 7.6 Category F — Shape, surface, effect

| Item | Count | Kind | Scope | Priority | Rationale |
|---|---|---|---|---|---|
| `shape.radius-scale` | derived | derived | derived | v1 | M3 verified: none 0, xs 4, s 8, m 12, l 16, xl 28, full 9999 + directional variants (top, start, end) for sheets and grouped controls |
| `shape.per-corner-recipes` | **8** | **set** | in-direction-repickable (validity list per direction) | v1 | leaf, ticket, tab-top, notch, chamfer, squircle, single-cut, pill-end. Cheap distinctiveness; more than 8 is an unusable menu. **A sharp-0 direction's validity list will legitimately be short — that is the coherence rule working, not a bug** |
| `shape.border-width-scale` | derived | derived | derived | v1 | Four steps doubling from base. Must be integer px at 1× to avoid sub-pixel hairline blur |
| `shape.stroke-style-set` | **4** | **set** | direction-slot | v1 | **The four (enumerated, was missing):** (1) `solid`, (2) `dash-designed` — an explicit `dashArray` tuned to the direction's radius scale so dashes land on corners rather than being cut by them, (3) `dot-round` — round `lineCap` dot rhythm, (4) `tick-segmented` — long-short repeating rule for technical/editorial directions. DTCG supports a custom `dashArray`/`lineCap` object, which is what makes a *designed* dash possible rather than the browser default |
| `shape.divider-treatment` | **8** | domain | in-direction-repickable (validity list per direction) | v1 | hairline, heavy rule, gradient fade, shape/wave cut, colour-block change, whitespace only, overlap, ticket-notch. **Section transitions are where long pages read as one composition or as a stack.** *This is the CSS/token-level seam treatment. It is a different layer from `art.section-divider-shapes` (the SVG path library it may reference) and from §8's "Section divider / seam" component (the composed block) — see §7.19* |
| `shape.clip-and-mask-shapes` | **10** | **set** | in-direction-repickable (validity list per direction) | v1 | **All ten now named — the previous "+2" TBD is resolved:** blob, arc, angle, wave, torn, circle-reveal, hex, custom-brand, **stadium-slab**, **stepped-stair**. Normalised path data so they scale; directly reusable by D4's art containers |
| `elevation.shadow-scale` | derived | derived | derived | v1 | Multi-layer via the **DTCG shadow ARRAY form** — a realistic 3-layer shadow is ONE token, which is exactly what separates designed depth from `box-shadow` defaults |
| `elevation.inner-shadow` | derived | derived | derived | v1 | Inverted and reduced from the outer scale. Needed for pressed states in physical models |
| `effect.blur-scale` | derived | derived | derived | v1 | From the space scale. **Carries a performance note**: `backdrop-filter` on a large scrolling surface is main-thread cost, and main-thread work is the actual performance failure axis |
| `effect.backdrop-recipe` | **6** | domain | direction-slot | v2 | **The six (enumerated):** (1) clear-glass (blur only), (2) frosted (blur + saturation), (3) tinted-glass (blur + tint alpha), (4) frosted-with-edge (blur + saturation + border highlight), (5) heavy-frost (high blur, low transparency), (6) dark-glass (blur + darkening overlay for light-on-dark chrome). **Lint 6 rejects all six in a border-only or flat direction** |
| `effect.opacity-scale` | derived | derived | derived | v1 | 5–7 steps from the state-layer opacities. Ad-hoc opacity is a top source of contrast failures because it bypasses the solver |
| `effect.noise-grain` | **8** | **set** | in-direction-repickable (validity list per direction) | v2 | **The eight (enumerated, was missing):** fine-film, coarse-film, halftone-dot, halftone-line, riso-speckle, paper-fibre, dust-and-scratch, chroma-noise. Prefer SVG `feTurbulence` over raster tiles — grain re-colours with the direction and costs no bytes. *Amplitude comes from `texture.grain-policy`; this row is the recipe library that policy selects from* |
| `effect.gradient-mesh` | **8** | **set** | in-direction-repickable (validity list per direction) | v2 | **The eight (enumerated, was missing) — named by blob topology, not by colour:** two-pole, three-pole-triangle, corner-wash, radial-core, ribbon-diagonal, aurora-band, orbit-cluster, edge-halo. Specified as **blob positions + hue assignments, not baked images**, so the mesh re-skins when hues change in Step 5 |
| `effect.pattern-tiles` | **12** | **set** | in-direction-repickable (validity list per direction) | v1 | grid, dot, hatch, halftone, isometric, topographic, stripe, chevron, scatter, weave, circuit, custom-brand. SVG using `currentColor`. The cheapest way to make a large empty surface feel authored |
| `effect.blend-mode-policy` | **6** | domain | direction-slot | v2 | **The six (enumerated):** (1) none-permitted, (2) multiply-only (ink/print directions), (3) screen/lighten-only (dark cinematic), (4) overlay-on-imagery-only, (5) difference/exclusion for a single signature moment, (6) luminosity-for-duotone. Must be a POLICY because blend modes create stacking contexts and can silently break the overlay ladder |

### 7.7 Category G — Motion (system items, per D4)

See §9 for the full motion/container treatment. Token-level items:

| Item | Count | Kind | Scope | Priority | Rationale |
|---|---|---|---|---|---|
| `motion.duration-scale` | derived | derived | derived | v1 | Seed from **Carbon's verified 6-step set**: fast01 70ms, fast02 110, moderate01 150, moderate02 240, slow01 400, slow02 700; scale by expressiveness. **Primer's hard lint applies as a build gate**: UI interactions ≤300ms, never >500ms; decorative motion exempt but must be tagged **[V — carbon packages/motion/src/index.ts; primer motion.json5 quoted]** |
| `motion.easing-set` | derived | derived | derived | v1 | **Carbon's 3×2 matrix IS the derivation**: standard/entrance/exit × productive/expressive; one expressiveness flag selects the whole column. Verified values at both endpoints so interpolation is safe |
| `motion.spring-presets` | derived | derived | derived | v2 | Tension/friction/mass + a mapping from each easing token to its nearest spring. **DTCG has no native spring type** — requires a `$extensions.acos.spring` namespace, and every tool in the chain must agree on its shape or springs silently degrade |
| `motion.transition-presets` | derived | derived | derived | v1 | DTCG `transition` composite bundling duration+delay+timingFunction. One token = one CSS declaration, which stops a builder pairing a fast duration with a slow curve |
| `motion.stagger-policy` | derived | derived | derived | v1 | Delay increment as a fraction of base duration, plus **the cap** beyond which stagger becomes a single group animation. The cap is the important part — uncapped stagger on a 40-item grid makes the last item arrive seconds late |
| `motion.distance-tokens` | derived | derived | derived | v1 | **Bound to the spacing scale**, never arbitrary translateY values, so motion moves a visually consistent amount relative to the same grid the layout snaps to. Extends D1's computed-not-picked rule into motion |
| `motion.choreography-rules` | **n/a** | n/a | site-global | v1 | Meta-rules: exits use accelerate and finish faster than entrances use decelerate; stagger follows reading order; only one pinned sequence and one ambient layer per viewport |
| `motion.reduced-motion-variants` | **n/a** | n/a | site-global | v1 | **Mandatory pairing.** Art-directed (cross-fades, poster frames, instant states), not `animation: none`. Must be authored at generation time — the editor cannot invent a good one |

### 7.8 Category H — Iconography & marks

| Item | Count | Kind | Scope | Priority | Rationale |
|---|---|---|---|---|---|
| `icon.family-spec` | **10** | per-direction | **direction-slot** | v1 | **One family spec per direction; 10 = the direction count, not a menu.** Grid size, keyline shapes, stroke weight, terminal style, corner radius, optical-size behaviour, whether strokes scale. Icons appear everywhere so a mismatched family is the most pervasive incoherence available — **which is exactly why Scope is `direction-slot` and the editor renders no re-pick control.** This is a direction-bound authored artefact (§7.0.3): identity-carrying but outside the hash-bearing vector, validated by lint 7. *Reconciles with §8's "Icon set 20" — see §7.19* |
| `icon.style-variants` | derived | derived | derived | v1 | Outline / filled / duotone **plus the selection rule** (filled = active nav, outline = inactive). The rule is the load-bearing part; mixing arbitrarily is a common tell |
| `icon.core-set` | **~50** | **set** | site-global | v1 | **A coverage checklist, not alternatives — all ~50 glyphs ship in every family.** menu, close, chevron ×4, arrow ×4, external-link, search, check, minus, plus, info, warning, error, success, user, mail, phone, location, calendar, clock, download, upload, share, copy, link, play, pause, mute, fullscreen, filter, sort, grid, list, settings, star, heart, cart, bookmark, edit, trash, refresh, lock, eye, eye-off, drag-handle, more-h, more-v + social. **Missing icons are discovered at build time and force an off-system substitution** |
| `icon.alignment-rules` | derived | derived | derived | v1 | Optical centring, cap-height vs x-height alignment, inline gap. The **RTL mirroring list is explicit data** (arrows mirror, clocks do not) and cannot be inferred |
| `mark.logo-lockups` | **10 × 6** | per-direction, each a set of 6 | direction-slot | v1 ⁴ | **Ten lockup *systems*, one per direction; each system ships the same six arrangements:** wordmark, symbol, horizontal, stacked, monogram, mono/inverse — plus clear-space, min-size and mono/inverse rules. Clear-space and min-size derive from the mark's geometry. **This is the reconciliation of §7's "10" with §8's "Logo lockup set 6": 10 systems × 6 members. Neither number was wrong; the axis was unstated** |
| `mark.favicon-set` | derived | derived | derived | v1 | `favicon.svg` with a dark-mode media query **inside the SVG**, 32px ICO, 180px apple-touch, 192/512 maskable (safe zone required), manifest theme colours. Routinely missing from AI-built sites |
| `mark.social-share-image` | **6** | **set** | direction-slot | v1 (3 of 6) / v2 (remaining 3) | 1200×630 OG + Twitter card, **parameterised template not a static file** so per-page images generate automatically. **The six templates:** hero-title, title+mark, quote, stat, product-shot, article-with-author. §8's "OG / social share card template **3**" is the **v1 cut** of these six (hero-title, title+mark, article-with-author) — see §7.19. One generic OG image across a whole site is a visible shortcut |
| `mark.decorative-glyphs` | **10** | **set** | in-direction-repickable (validity list per direction) | v1 | **All ten now named — the previous list stopped at 8:** bullets, section symbols, ornaments, decorative arrows, underline squiggles, highlight strokes, asterisks, corner ticks, **end-of-article mark (colophon)**, **paired quote ornaments**. What makes a page feel drawn rather than assembled, at near-zero cost as inline SVG |

### 7.9 Category I — Imagery & artwork

**Read §17-R1 first.** claude.ai cannot produce raster images **[V — Anthropic, April 2026]**. The user's own cited exemplar (the FruitSync site background) is 231 PNGs exported from Unity by a hand-written batchmode exporter pulling the game's real procedural sprites **[V — `SiteAngryExport.cs`; `ls` of `/Users/zee/fruitsync-animated-variants/assets`]**. That art came from a pre-existing hand-drawn library, not from a chat.

Three honestly-labelled lanes:

- **Lane A — code-drawn art.** SVG scenes, CSS gradient meshes, canvas/WebGL noise fields, generative patterns. claude.ai is genuinely good at this, and it is on-brand-able because it is parameterised by tokens. **Also the only lane that Local Regeneration Mode (§6.5) can produce without any hand-carry**, which is what makes the volume roll-up in §7.17 survivable.
- **Lane B — asset ingestion.** Point the skill at an existing sprite/photo/illustration folder. **This is what actually made the FruitSync site work**, and Step 0 question C3 detects it. Zero hand-carry cost; the artwork already exists on disk.
- **Lane C — external raster generation.** Midjourney / FLUX / Recraft, per the prior report's asset-routing matrix. A **separate** hand-carry with its own licence manifest, explicitly scoped in or out per release. **Out of scope for v1 unless the user opts in (§7.17).**

**Volume warning (do not read this table as a v1 shopping list).** The counts below are the **full library targets**, and they sum to **130 pieces** — against §6.3's chunk budget of "ten directions plus 20 artworks ≈ 400KB" and D1's settled "20 artworks tagged by direction". That contradiction is real, it is quantified in **§7.17**, and its resolution **requires user sign-off (O31)**. Every row therefore carries a Priority and a lane, and the v1 hand-carry quota is fixed at 20 pieces in §7.18.

| Item | Count | Kind | Scope | Lane | Priority | Rationale |
|---|---|---|---|---|---|---|
| `art.container-contract` | **n/a** | n/a | site-global | — | v1 | **THE load-bearing item for D4.** Box sizing, aspect policy, anchor/pin, overflow, mask, scheme-awareness, motion-capable flag, reduced-motion poster, focal point, alt text, licence ref. Because animated pieces live in the same draggable containers as static art, **both must satisfy one contract** — otherwise the editor needs two drag models and the lock/export path forks. Must be specified BEFORE any artwork is generated |
| `art.background-scene` | **20** | **set** (library) | in-direction-repickable (filtered by affinity tag) | A (primary), B | v1 — **quota 8 of 20 hand-carried**; remainder Lane A on demand | Per D1, tagged by direction affinity. Each declares `palette-mode`: **token-referencing** art (`currentColor` / `var(--*)`) suits many directions and re-skins free; **baked-palette** art suits only its tagged directions. **Require ≥60% token-referencing** — that is what makes Step 5 cheap instead of a full art regeneration |
| `art.hero-artwork` | **20** | **set** (library) | in-direction-repickable (filtered by affinity tag) | A, B, C | v1 — **quota 6 of 20 hand-carried** | This asset IS the LCP element on most sites, so each variant carries a **pre-LCP transfer budget** |
| `art.spot-illustrations` | **20** | **set** (library) | in-direction-repickable (filtered by affinity tag) | A, B | v1 — **quota 6 of 20 hand-carried** | Built from a shared component vocabulary (same stroke, same palette slots) so the set reads as one hand. *Same deliverable as §8 Media's "Decorative spot-graphic set 20" — see §7.19* |
| `art.section-divider-shapes` | **12** | **set** | in-direction-repickable (validity list per direction) | A | v1 — Lane A, generated locally | wave, angle, arc, torn, layered, notch, blob, zigzag + flipped/inverted. Normalised SVG paths that stretch; token-coloured for both schemes. *The SVG path library referenced by `shape.divider-treatment`'s "shape/wave cut" option — see §7.19* |
| `art.texture-plates` | **12** | **set** | in-direction-repickable (validity list per direction) | A | v2 | paper, canvas, concrete, film-grain, halftone, riso misregistration, scan-lines, foil, gradient-map, fabric, ink-bleed, dust. **What breaks the flat-vector-gradient look that reads instantly as machine-generated** |
| `art.photo-grade-recipe` | **8** | domain | direction-slot (resolved from `imagery.treatment`) | A (filter chain, no assets) | v1 | CSS/SVG filter chain: exposure, contrast curve, duotone, grain, vignette, hue-shift toward the anchors. **The highest-leverage way to make sourced imagery look commissioned**, and the implementation of the ban on unstyled stock. *Identical deliverable to §8 Media's "Photography treatment 8"* |
| `art.crop-and-focal-policy` | derived | derived | derived | — | v1 | `object-fit`/`object-position` defaults + **per-image focal point** (a single draggable dot, not a crop rectangle — it degrades gracefully across every aspect ratio a reflow system produces) + `<picture>` art direction. Focal metadata is captured in the editor, not designed |
| `art.placeholder-strategy` | **4** | domain | site-global | A | v1 | LQIP / blurhash / dominant-colour / skeleton + reveal transition. **Chosen once for the site** — a mixed placeholder strategy reads as inconsistency during loading, which is exactly when a visitor is watching. **Must reserve the exact final box** via `aspect-ratio` or the placeholder causes the CLS it was meant to prevent |
| `art.avatar-style` | **8** | domain | direction-slot | A, B | v2 | **All eight now named — the previous list stopped at 5:** photo-circle, photo-rounded-square, illustrated, monogram, generated-geometric, silhouette, **ringed/status-bordered**, **duotone-graded photo**. Generated-geometric matters because it needs no assets |
| `art.3d-or-canvas-scene` | **6** | domain | direction-slot | A, C | v3 | **The six (enumerated, was missing):** (1) rotating product/object, (2) ambient particle field, (3) shader gradient plane, (4) scroll-scrubbed camera path, (5) Gaussian-splat capture embed, (6) 2D-canvas generative plane (no WebGL). WebGL/three.js or Gaussian-splat spec with a **mandatory GPU-tier ladder**: full / reduced / static poster via detect-gpu. Without it a 3D hero is a guaranteed gate failure on low-end devices |
| `art.empty-state` | **10** | **set** (art pieces) | in-direction-repickable (filtered by affinity tag) | A | v2 | Cheap once the spot-illustration vocabulary exists; always ships, never designed. *These are 10 **artwork pieces**; §8's "Empty state 8" is 8 **component layouts** that place one — see §7.19* |
| `art.error-state` | **10** | **set** (art pieces) | in-direction-repickable (filtered by affinity tag) | A | v2 | 404 + 500 art plus recovery layout. A real page a visitor will see; the host default undoes the whole system in one view. *§8 ships 404 **6** and 500 **3** as component layouts; these 10 are the art they place — see §7.19* |

### 7.10 Category J — Accessibility & compliance (system-level)

| Item | Count | Kind | Scope | Priority | Rationale |
|---|---|---|---|---|---|
| `color.contrast-ladder` | **3** | domain | **site-global** | v1 | AA-floor / AA-generous / AAA. **Site-level policy chosen once and applied to all directions** — per-direction would let a pretty direction ship illegible text |
| `token.contrast-proof-table` | **n/a** | n/a | site-global | v1 | Every text/surface pairing with WCAG 2 ratio and APCA Lc, pass/fail against the ladder. Because Leonardo solves *to* the targets, this is all-pass by construction — **so any failure means a value was hand-edited, making the table a tamper detector as well as a proof** |
| `system.alt-text-policy` | **n/a** | n/a | site-global | v1 | Decorative (`alt=""`) vs informative rules + a **required alt field on every artwork record**, captured at generation time. Retrofitting at lock time fails because nobody remembers what the illustration was meant to convey |

### 7.11 Category L — Data visualisation

| Item | Count | Kind | Scope | Priority | Rationale |
|---|---|---|---|---|---|
| `color.data-vis-categorical` | **3** | domain | **site-global** | v2 | Hues derive from the direction; the **ordering strategy** is the real pick: harmonic rotation / maximum perceptual distance / brand-first-then-distance. Three strategies, not ten palettes. **Site-global** because charts across a site must order series identically or the same series changes colour between pages |
| `color.data-vis-sequential` | derived | derived | derived | v2 | Monotonic lightness is a mathematical requirement; OKLCH makes it computable from the hue anchor |
| `color.data-vis-diverging` | derived | derived | derived | v2 | Two hues around a neutral midpoint **pinned to the actual surface colour** — that pinning is what stops diverging charts looking pasted on |
| `chart.structural-tokens` | derived | derived | derived | v2 | gridline, axis, tick, axis-label, annotation, reference-line, zero-line, tooltip surface, max-series cap. From border/text roles at reduced emphasis. **Without them charts read as a foreign component** |

**A direction with 3 brand hues cannot yield a 6-series categorical palette that is simultaneously on-brand, distinguishable, and colourblind-safe.** Every direction must therefore carry the dataviz sub-token set **from generation time**, not as a retrofit. The local `dataviz` skill already ships a form heuristic, a colour formula with a runnable validator, and a palette reference — reuse it rather than reinventing.

### 7.12 Category N — Token file contract

| Item | Count | Kind | Scope | Priority | Rationale |
|---|---|---|---|---|---|
| `token.tier-architecture` | **n/a** | n/a | site-global | v1 | Three tiers: **primitive** (raw ramps, never referenced by components), **semantic** (role-named, the only tier components may reference), **component** (overrides only where a component genuinely deviates). Enforceable rule: no component CSS may reference a tier-1 token |
| `token.file-format` | **n/a** | n/a | site-global | v1 | DTCG 2025.10 JSON, `$type` declared or group-inherited, references via `{group.token}`, composite types wherever CSS has a composite property. **JSON-Schema-validatable — which is precisely what makes the Step-3 boundary safe** |
| `token.llm-extension-block` | **n/a** | n/a | site-global | v1 | `$extensions['com.acos.llm'] = {usage[], rules, antipatterns[]}` on every semantic token |
| `token.pick-extension-block` | **n/a** | n/a | site-global | v1 | **Extended this pass.** `$extensions['com.acos.pick'] = {pickable, slot, directionId, variantIndex, derivedFrom[], `**`countKind`**`, `**`scope`**`, `**`validityList`**`}`. `countKind` ∈ {`per-direction`, `domain`, `set`, `derived`, `n/a`} (§7.0.1); `scope` ∈ {`direction-slot`, `site-global`, `in-direction-repickable`, `derived`} (§7.0.2); `validityList` is **required and non-empty whenever `scope === "in-direction-repickable"`** and lists the option ids valid for `directionId`. The editor reads this to decide what to render a control for **and what to put in it** — without `scope` it could not decide at all, which is the defect this closes |
| `token.direction-hash` | **n/a** | n/a | site-global | v1 | `$extensions['com.acos.direction'] = {id, vectorHash}`. Builder rejects mismatches. **Hash input now specified (was undefined):** the **24 varying slots of §7.1 in table order**, excluding `direction.reference-triangulation` and `type.viewport-endpoints`; serialised as a JSON array of `[slotId, value]` pairs with **UTF-8 NFC normalisation, `\n` line endings, leading/trailing whitespace trimmed, internal whitespace runs collapsed to one space, and no case folding** (case is meaningful in a manifesto); numbers serialised with no trailing zeros; hashed with **SHA-256**, recorded as the first 12 hex characters. Direction-bound authored artefacts (§7.0.3) do **not** feed the hash. Without this paragraph two implementations disagree and every ingest fails the mismatch check with an error message that explains nothing |
| `token.naming-convention` | **3** | domain | **site-global** | v1 | Carbon role-state-suffix / Fluent camelCase-compound / Primer dotted-group. **Pick ONE globally**; mixing is why token files stop being greppable |
| `token.theme-structure` | **n/a** | n/a | site-global | v1 | Recommend the per-mode override pattern (Primer's `org.primer.overrides`) over separate files — the selection token proves it handles per-scheme alpha differences a file split makes easy to forget to mirror |
| `token.capability-manifest` | **n/a** | n/a | site-global | v1 | Root manifest: direction id + hash, **expected token count per group**, **expected artefact count per §7 row (Count × Kind, so the validator knows whether to expect 10 members or 1 of 10 options)**, **the per-direction validity list for every `in-direction-repickable` row**, schemes present, breakpoints, container-breakpoints, pickable slot list, artwork index with affinity tags, font licence classes. **The Count/Kind/Scope columns exist so this manifest can be generated mechanically from §7 rather than hand-maintained** |
| `token.compiler-target` | **n/a** | n/a | site-global | v1 | **Pinned explicitly.** Style Dictionary v4 has first-class DTCG support but **not** full 2025.10 (in progress in v5); Terrazzo supports the full format today. Emitting 2025.10 colour objects into v4 will fail **[V — styledictionary.com/info/dtcg; terrazzo.app docs; medium confidence on current version state]**. **Also decides whether `light-dark()` is a safe emission form for `color.scheme-declaration`** |
| `token.raw-value-lint` | **n/a** | n/a | site-global | v1 | `stylelint-declaration-strict-value` + a raw-hex/px grep. Without it every generated component gradually reintroduces literals and the token layer becomes decorative. **Documented exemptions (each must be narrow and listed, or the lint gets disabled wholesale): (1) `@container` size conditions, which cannot take `var()`; (2) `@media` breakpoint conditions, same reason; (3) `0` and `1px` hairlines in the border-width primitive; (4) the base64 font `src` in `@font-face`** |
| `token.coherence-lints` | **n/a** | n/a | site-global | v1 | **Ten purity checks (six existing, four added this pass):** (1) no font-family outside the direction's slots; (2) no raw colour values; (3) every colour resolves to this direction's ramps; (4) every duration/easing from this direction's motion set; (5) every radius from this direction's scale; (6) **if `elevation.model` is border-only or flat, zero shadow tokens referenced**; (7) **the icon family id on every emitted icon equals the active direction's `icon.family-spec` id** — this is what stops a geometric-mono family landing on an editorial-serif direction; (8) **every `in-direction-repickable` pick is present on the active direction's `validityList`** (a pick absent from the list is a hard fail, not a warning); (9) **every referenced artwork carries an affinity tag including the active direction id**; (10) **every `container-name` used is in `layout.container-name-registry` and every `@container` threshold is one of the three in `layout.container-breakpoints`**. Lint 6 is the one that catches the incoherence humans actually notice; lints 7–9 are what make the D1 coherence guarantee structural rather than aspirational |
| `token.license-manifest` | **n/a** | n/a | site-global | v1 | Per-font: family, foundry, licence class, file hash, source URL, attribution. Per-image: generator, model, plan tier, licence class, prompt. **Fonts are where the risk concentrates**: OFL permits self-hosting and bundling; Fontshare-class permits free commercial use but **forbids redistribution** (CDN link only, never vendored); commercial foundry faces are per-project and pageview-metered and must emit a **pre-launch blocker** |

### 7.13 Category O — Voice & delivery

| Item | Count | Kind | Scope | Priority | Rationale |
|---|---|---|---|---|---|
| `system.voice-and-microcopy` | **10** | per-direction | direction-slot | v1 | **One voice profile per direction; 10 = the direction count, not a menu of 10 tones.** Tone descriptors, sentence-length target, **capitalisation rule** (sentence vs title case), button verb pattern, error-message pattern, forbidden-phrase list. Capitalisation alone is a token-level decision no colour system compensates for. Direction-bound authored artefact (§7.0.3) — identity-carrying, outside the hash |
| `system.headline-length-budget` | derived | derived | derived | v1 | Character budgets per type role from measure × role size. **Prevents the classic failure where a beautiful hero breaks the moment real copy replaces the placeholder** |

---

### 7.14 Category K — Internationalisation, locale & content shape (**restored**)

> **Why this subsection exists.** The category letters in §7 skipped **K** and **M**: A, B, C, D, E, F, G, H, I, J, **L**, **N**, O. Neither letter appears anywhere in the PRD and neither is listed in §20.1's deliberate-exclusions table, which exists precisely so that dropped items are *traded, not lost*. Two missing letters in a lettered scheme is direct evidence that two categories were cut during editing without passing through the exclusions table. **This pass cannot recover what K and M originally contained — that information is not in the surviving text, and no source for it exists. What follows is a reconstruction, not a recovery**, populated from the families the audit identified as having no home anywhere in §7. **Requires user sign-off (O35): confirm that internationalisation and sonic identity are the intended contents, or supply what K and M actually were.** Subsection numbers are appended (7.14, 7.15) rather than inserted so no existing §7.x cross-reference moves; the letters are therefore out of numeric order, which is recorded deliberately.

| Item | Count | Kind | Scope | Priority | Rationale |
|---|---|---|---|---|---|
| `i18n.locale-set` | **n/a** | n/a | site-global | v1 | The declared list of locales the site ships, each with script, direction (ltr/rtl), and date/number formats. Everything else in this category is a function of it. Declaring "en only" explicitly is a valid and cheap answer — what is expensive is discovering a second locale after LOCK |
| `i18n.string-expansion-budget` | **n/a** | n/a | site-global | v1 | +35% string expansion allowance applied to every component's text slot, matching §8's pseudolocalisation state. Without a stated budget, "it fits" is measured against English and a German nav breaks the ribbon. This is the token-level counterpart of §8's state |
| `i18n.rtl-mirroring-rules` | **n/a** | n/a | site-global | v1 | Explicit per-icon and per-component mirroring data (arrows mirror, clocks and logos do not), logical-property enforcement, and the rule that a mirrored layout is a **render target in the LOCK gate**, not a CSS afterthought. Overlaps `type.script-and-rtl-coverage` (§7.3) by design: that row owns *font coverage*, this row owns *layout mirroring* |
| `i18n.font-script-coverage` | derived | derived | derived | v1 | Per declared locale, whether the direction's chosen faces cover the script, and the named fallback stack where they do not. Computed from the real font files after the typeface pick, like `type.fallback-metrics`. **A direction whose display face lacks the script must fail loudly at generation time, not render tofu at LOCK** |
| `i18n.content-shape-policy` | **n/a** | n/a | site-global | v2 | Date/number/currency formatting, name-order assumptions, address shape, and the ban on string concatenation for sentences. Cheap to state, expensive to retrofit into generated components |
| `i18n.locale-switching-surface` | **3** | domain | site-global | v2 | header switcher / footer switcher / path-prefix-only-no-switcher. Maps directly onto §8's "Language / region switcher **4**" component variants — the component has four skins; the site has one placement policy |

### 7.15 Category M — Sound & sensory identity (**restored**)

> Same caveat as §7.14: this is a reconstruction of a missing letter, not a recovery. It is included because §8 ships a **Sound toggle (3, v2)** and an **Audio player (3, v3)** with nothing anywhere in §7 defining what they control — sound is currently a component with no system behind it, which is precisely the "component that reads as foreign" failure §7.11 warns about for charts.

| Item | Count | Kind | Scope | Priority | Rationale |
|---|---|---|---|---|---|
| `sound.presence-policy` | **3** | domain | site-global | v2 | none / ambient-optional / interaction-cues. **`none` must be the default and must be a real, first-class option** — most marketing sites should ship silent. Declaring the null explicitly is the same discipline `typeface.accent` and `imagery.treatment` already apply |
| `sound.interaction-cue-set` | **6** | **set** | direction-slot | v3 | If `presence-policy` is `interaction-cues`, the direction ships six cues: hover, press, success, error, open, close. A partial set is worse than none — an unmatched close sound reads as a bug |
| `sound.ambient-bed` | **1 per direction** | per-direction | direction-slot | v3 | If `presence-policy` is `ambient-optional`, one loop per direction with a stated loop length and a documented seam. **Gated on `sound.consent-and-controls` below; autoplay with sound is blocked by every modern browser anyway** |
| `sound.consent-and-controls` | **n/a** | n/a | site-global | v2 | Default-off, persisted preference, a visible control, and no audio before an explicit user gesture. This is what §8's "Sound toggle — must default off and persist" is enforcing; the policy belongs here |
| `sound.reduced-and-assistive-pairing` | **n/a** | n/a | site-global | v2 | Every audio cue must have a non-audio equivalent (the same rule as "status must never be colour-only"), and audio must not be the sole channel for any state change. Also the hook for future haptics if a native shell is ever added — **explicitly out of scope for web v1, recorded so it is traded rather than lost** |

### 7.16 Category P — SEO, metadata & the sharing surface (**new**)

> Added because the audit found metadata had no home: `mark.favicon-set` and `mark.social-share-image` sit in Category H as *marks*, which covers the images but not the document-level metadata contract that determines whether they are ever used. §8 ships an "OG / social share card template" component with nothing specifying the head tags it depends on. The letter continues the existing scheme (O was the last used).

| Item | Count | Kind | Scope | Priority | Rationale |
|---|---|---|---|---|---|
| `seo.head-contract` | **n/a** | n/a | site-global | v1 | The required per-page head set: `<title>` pattern, meta description, canonical, `og:*`, `twitter:*`, `theme-color` per scheme, viewport, and language attributes. **A LOCK gate check, because a static export with no canonical and no OG tags is a shipped defect a visitor never sees and the owner discovers on first share** |
| `seo.title-pattern` | **3** | domain | site-global | v1 | `page — site` / `page \| site` / `site: page`. Trivial, and exactly the kind of inconsistency that appears when each page is generated separately |
| `seo.structured-data-policy` | **n/a** | n/a | site-global | v2 | Which schema.org types the site emits (Organization, WebSite, Article, Product, FAQPage, BreadcrumbList) and the rule that structured data must match visible content. **Emitting a Product schema with invented ratings is the failure mode to ban explicitly** |
| `seo.crawlability-contract` | **n/a** | n/a | site-global | v1 | robots.txt, sitemap.xml, the no-JS/progressive-enhancement requirement (already a §8 state) restated as a build gate, and the rule that reveal-on-enter animations must not hide content from a no-JS client. **Ties directly to §8's note that the no-JS view is the crawler's view** |
| `seo.social-preview-proof` | **n/a** | n/a | site-global | v2 | A rendered proof of the OG card at 1200×630 in the evidence bundle, so the sharing surface is verified rather than assumed. Cheap: it is a render of an existing template |
| `seo.url-and-slug-policy` | **3** | domain | site-global | v2 | flat / sectioned / dated. Chosen once because changing it after publish costs redirects |

---

### 7.17 Artwork and artefact volume roll-up (closes the §6.3 ↔ §7.9 ↔ §8 contradiction)

**The problem, stated numerically.** No total artwork volume was ever stated, and the two places that imply one disagree by roughly an order of magnitude.

| Source | What it implies | Number |
|---|---|---|
| **D1 (settled)** | "20 artworks tagged by direction" | **20** |
| **§6.3 chunk budget** | "Ten directions plus 20 artworks is ~400KB (~110K tokens)" — the sizing behind the whole Step-2/3 hand-carry | **20** |
| **§20.3 U8** | 45–90 minute hand-carry estimate, anchored on that budget | (derived from 20) |
| **§20.3 U10** | ~250-artifact Step-2/3 payload, "inference from D1 arithmetic against the inventory in §7–§8" | (derived from 20) |
| **§7.9 as written** | 20 + 20 + 20 + 12 + 12 + 8 + 8 + 6 + 4 + 10 + 10 | **130 pieces** |
| **§8 #Media artwork tier** | Icon set 20 + Illustration set 20 + Decorative spot-graphic set 20 + Pattern/texture library 20 | **80 more** |
| **Overlap between the two** | `art.spot-illustrations` 20 ≡ §8 "Decorative spot-graphic set" 20; `effect.pattern-tiles` 12 + `art.texture-plates` 12 ≈ §8 "Pattern / texture library" 20 | −20 to −24 |

**§20.2 #14 resolves only the pieces-versus-sets axis, not the volume.** The volume question is untouched anywhere in the PRD.

#### 7.17.1 The full-library roll-up, by lane and phase

Lane assignment follows §7.9's three lanes. **Lane A pieces can be produced by Local Regeneration Mode (§6.5) with zero hand-carry**, which is the only reason the full library is reachable at all.

| Family | Full-library count | Lane | v1 | v2 | v3 |
|---|---|---|---|---|---|
| `art.background-scene` | 20 | A / B | 8 | 8 | 4 |
| `art.hero-artwork` | 20 | A / B / C | 6 | 8 | 6 |
| `art.spot-illustrations` (= §8 spot-graphic set) | 20 | A / B | 6 | 10 | 4 |
| `art.section-divider-shapes` | 12 | A | 12 | — | — |
| `art.texture-plates` | 12 | A | — | 12 | — |
| `effect.pattern-tiles` (§7.6) | 12 | A | 12 | — | — |
| `effect.noise-grain` (§7.6) | 8 | A | — | 8 | — |
| `effect.gradient-mesh` (§7.6) | 8 | A | — | 8 | — |
| `art.photo-grade-recipe` (= §8 photography treatment) | 8 | A (filter chain only, no assets) | 8 | — | — |
| `art.avatar-style` | 8 | A / B | — | 8 | — |
| `art.3d-or-canvas-scene` | 6 | A / C | — | — | 6 |
| `art.placeholder-strategy` | 4 | A | 4 | — | — |
| `art.empty-state` | 10 | A | — | 10 | — |
| `art.error-state` | 10 | A | — | 10 | — |
| `icon.core-set` × `icon.family-spec` (§7.8) | ~50 glyphs × 10 families = **~500 glyphs** | A | ~50 (one family for the chosen direction) | +~200 (4 more families) | +~250 |
| `mark.logo-lockups` (§7.8) | 10 systems × 6 members = **60** | A / B | 6 (chosen direction only) | 24 | 30 |
| `mark.decorative-glyphs` (§7.8) | 10 | A | 10 | — | — |
| `mark.social-share-image` (§7.8) | 6 | A | 3 | 3 | — |
| `shape.clip-and-mask-shapes` (§7.6) | 10 | A | 10 | — | — |
| **Artwork-family total (excluding icon glyphs)** | **~204 artefacts** | | **~85** | **~85** | **~34** |
| **Including icon glyphs** | **~704** | | **~135** | **~285** | **~284** |

**[I — every count above is arithmetic over the §7 rows; the phase split is this revision's proposal and has no external source. The icon-glyph line is what makes the total explode, and it is the number most likely to be wrong in practice because one family is almost certainly enough for v1.]**

#### 7.17.2 Payload estimate, and why the §6.3 budget does not survive contact with it

| Quantity | Value | Basis |
|---|---|---|
| Median size of one code-drawn SVG art piece, inlined | **~8KB** | **[I — no measured basis. This is a placeholder. O32 requires it to be measured against real generator output before any chunk plan depends on it]** |
| Full §7.9 artwork library at that median (130 pieces) | **~1.04MB** | Arithmetic on a placeholder |
| §6.3's entire stated hand-carry budget | **~400KB** | **[V — §6.3, anchored on `wc -c` of first-party FruitSync variant files]** |
| Ratio | **~2.6×** the whole budget, for §7.9 alone | |

**Conclusion: §6.3's "Ten directions plus 20 artworks is ~400KB" is not off by a rounding error.** Three things follow, and they are stated rather than papered over:

1. **§6.3's chunk table needs a real "Art" row.** It currently reads `Art | The 20 artworks with suitsDirections[] tags | Variable`. "Variable" is the entire sizing. **Required §6.3 edit:** replace with the v1 quota below and its byte estimate. Recorded as a cross-section change this revision cannot make.
2. **U8 (45–90 min) and U10 (~250 artifacts) must be re-derived** from whichever volume the user signs off on. Both are explicitly flagged in §20.3 as inference anchored on the 20-artwork reading. **Required §20.3 edit.**
3. **The v1 hand-carry quota is capped at 20 artwork pieces** (§7.18), which is the only reading that keeps D1, §6.3, U8 and U10 mutually consistent. Everything above that quota is Lane A / Local Regeneration Mode or Lane B ingestion, neither of which consumes hand-carry time.

#### 7.17.3 What requires user sign-off

> **O31 — requires user decision (blocking for the Step-2 prompt).** Does "about 20 artworks" mean **20 pieces in total** (the D1 and §6.3 reading, which this revision adopts as the v1 hand-carry quota), or **20 pieces per artwork family** (the §7.9 reading, ≈130 pieces)? If the second, the hand-carry cycle multiplies by roughly 6× and §6.3's one-paste protocol, U8's 45–90 minutes and U10's ~250 artifacts all become wrong by that factor. **No known mitigation other than routing the overage to Lane A / Local Regeneration Mode, which changes who generates the art — and therefore its character — not just how it arrives.**

> **Deviation notice — requires user sign-off.** The user named "arts to use in the website" and "background art/style" as first-class design-system items and cited the FruitSync site, which shipped **231 exported sprites**. Capping v1 hand-carried artwork at **20 pieces** is therefore a real reduction against the cited exemplar. It is proposed only because §6.4 identifies clerical load as "the most likely way the product quietly dies", and because Lane B (ingest an existing folder — exactly what FruitSync did) reaches 231 pieces at zero hand-carry cost. **The user should confirm they are content with: 20 hand-carried pieces + unlimited Lane B ingestion + on-demand Lane A generation, rather than a larger hand-carry.**

### 7.18 The v1 cut list for §7, and the phase policy

*(This is the subsection the audit suggested numbering §7.14; it lands here because §7.14–§7.16 restore the missing categories. Nothing previously numbered has moved.)*

**Rule.** Only `v1` rows are requested in the Step-2 prompt. `v2` and `v3` rows are generated on demand in Step 5 (§14) via Local Regeneration Mode or a targeted follow-up chunk. **A v2/v3 row is not "cut" — it is deferred, and the capability manifest records it as `deferred`, so a later regeneration knows it is missing rather than assuming the system is complete.**

| Measure | v1 | v2 | v3 | Total |
|---|---|---|---|---|
| §7 inventory rows | **~126** | **~32** | **~10** | **168** |
| Of which `derived` (no generation cost, computed locally) | ~63 | ~6 | 0 | ~69 |
| Of which `n/a` policy/contract rows (prose, small) | ~40 | ~9 | ~1 | ~50 |
| Of which carry a Count and must be enumerated in the prompt | **~23** | ~17 | ~9 | ~49 |
| Expected resolved tokens for the chosen direction | **~600–900** | +~80 | +~40 | ~720–1,020 |
| Hand-carried artwork pieces | **20 (quota, O31)** | Lane A on demand | Lane A / C on demand | see §7.17 |

**[I — row counts are counted from the tables in this revision; the resolved-token figure is the §7 preamble's verified 600–900 budget carried forward, and the v2/v3 deltas are inference.]**

**v1 §7 set, stated positively:** all of Category A (26 rows — the direction is not divisible); Category B except `color.high-contrast-scheme`, `color.print-scheme` and `color.syntax-highlight`; all of Category C; all of Category D including the two new container-query rows; all of Category E; Category F except `effect.backdrop-recipe`, `effect.noise-grain`, `effect.gradient-mesh` and `effect.blend-mode-policy`; Category G except `motion.spring-presets`; all of Category H (marks are what a site cannot ship without); Category I limited to `art.container-contract`, the v1 quotas in §7.17.1, `art.photo-grade-recipe`, `art.crop-and-focal-policy`, `art.placeholder-strategy`, `art.section-divider-shapes`; all of Category J; **none** of Category L (charts are v2 per §8); all of Category N; all of Category O; Category K rows marked v1; Category M `sound.presence-policy` and `sound.consent-and-controls` only (both of which will usually resolve to "none", which is the point); Category P rows marked v1.

### 7.19 §7 ↔ §8 ownership reconciliation

**The rule.** For every artefact that appears in both inventories: **§7 owns the system-level specification (`specified-by`), §8 owns the component that renders it (`renders`).** Where the counts differ, the axis is now stated. The Step-2 prompt requests each deliverable **exactly once**, from the §7 side.

| Deliverable | §7 item and count | §8 row and count | Reconciliation | Action required |
|---|---|---|---|---|
| Icon families / sets | `icon.family-spec` **10** (one spec per direction) | #Media "Icon set **20** … 20 candidate SETS" | **10 family *specs*, one per direction. §8's 20 is an artwork-tier candidate library — roughly two drawn sets per direction.** Both survive, but the prompt asks for one spec per direction and then N sets *within* the chosen direction's spec | **§8 edit:** change the rationale to "20 candidate sets **drawn to the active direction's `icon.family-spec`**", so 20 is never read as 20 competing families |
| Logo lockups | `mark.logo-lockups` **10 × 6** | #Media "Logo lockup set **6**" | **10 systems (one per direction) × 6 arrangements each.** §8's 6 = the members of one system | None — §7 now states the axis |
| Social / OG images | `mark.social-share-image` **6** | #Utility "OG / social share card template **3**" | **§8's 3 is the v1 cut of §7's 6.** The remaining 3 are v2 | **§8 edit:** annotate as "3 of 6 (§7.8), v1 cut" |
| Section seams | `shape.divider-treatment` **8** (token/CSS treatment) + `art.section-divider-shapes` **12** (SVG path library) | #Content "Section divider / seam **10**" | **Three layers, not three counts of one thing:** 8 treatments (how the seam is made) × an optional shape from the 12-path library × 10 composed component variants. A component variant selects a treatment and, where the treatment is "shape/wave cut", a path | **§8 edit:** add "composes §7.6 `shape.divider-treatment` + §7.9 `art.section-divider-shapes`" |
| Patterns / textures | `effect.pattern-tiles` **12** + `art.texture-plates` **12** = **24 defined** | #Media "Pattern / texture library **20**" | **24 defined in §7 (12 SVG token-coloured tiles + 12 texture plates); §8's 20 is the v1+v2 shipped library.** The 4-item difference is the v3 tail | **§8 edit:** change 20 → "24 (12 §7.6 tiles + 12 §7.9 plates)", or state which 4 are deferred |
| Photography | `imagery.treatment` **10** (identity slot: grade + crop + distance, one per direction) + `art.photo-grade-recipe` **8** (filter-chain domain) | #Media "Photography treatment **8**" | **Consistent already:** each direction's `imagery.treatment` resolves to one of the 8 chains plus per-direction crop rules. §8's 8 = the same 8 chains | None |
| Empty / error art | `art.empty-state` **10**, `art.error-state` **10** (art pieces) | #Feedback "Empty state **8**", "Error state **6**"; #Page templates "404 **6**", "500 **3**" | **§7 counts art; §8 counts layouts.** A layout places a piece. Neither count is derivable from the other, and both are needed | **§8 edit:** add "places one of §7.9 `art.empty-state` / `art.error-state`" |
| Container widths / gridlines | `layout.container-widths` derived, `layout.grid-definition` derived, `layout.container-breakpoints` **3** | #Utility "Layout container widths — derived" | Consistent; §8 already says "must be data, not decoration". **The new `layout.container-breakpoints` row is the missing half that §11.5 and A46 depend on** | **§11.5 edit:** cross-reference `layout.container-breakpoints` |
| Sound | Category M (§7.15, restored) | #Utility "Sound toggle **3**"; #Media "Audio player **3**" | §8 shipped a control with no system behind it. §7.15 supplies the policy | None beyond §7.15 existing |
| Team page template | — | #Page templates "Team \| **3** \| v3 \| *(empty)*" | **The only wholly blank Rationale cell in either inventory.** Suggested text: *"Photo grid + bio; structurally a recomposition of card grid + avatar, so three arrangements (grid, list-with-bio, feature-lead) exhaust the real variation."* | **§8 edit:** fill the cell |

### 7.20 Open questions and required sign-offs raised by this section

Continuing the existing numbering (§17 ended at O30; §19 ended at A90).

| # | Question / criterion | Status |
|---|---|---|
| **O31** | Does "about 20 artworks" mean 20 total or 20 per family? Determines the hand-carry budget, U8 and U10 (§7.17.3) | **Requires user decision.** Blocking for the Step-2 prompt |
| **O32** | Measure the real median byte size of one generated code-drawn SVG art piece and one full direction's token file, and re-derive §7.17.2 | **Open — currently a placeholder number, explicitly marked as such.** Cheap: one generation run |
| **O33** | Verify (a) that container-query size conditions reject `var()`, and (b) whether the pinned compiler target emits `light-dark()` safely | **Open.** Both are stated from working knowledge in this revision and are load-bearing for `layout.container-breakpoints` and `color.scheme-declaration` |
| **O34** | Residual risk accepted in §7.0.3: two directions can share a `vectorHash` and differ in direction-bound authored artefacts (icon family, voice, lockups). Lint 8 catches misuse, but the hash alone is not a complete identity | **Accepted risk, recorded.** Alternative (hash the artefacts too) is brittle against re-export noise |
| **O35** | What were categories **K** and **M** before they were cut? §7.14/§7.15 are a reconstruction, not a recovery | **Requires user decision, or an explicit §20.1 entry recording the cut.** No known way to recover the original contents |
| **O36** | Should `icon.family-spec`, `mark.logo-lockups` and `system.voice-and-microcopy` be promoted into the hash-bearing vector (making it 27 slots) rather than treated as direction-bound authored artefacts? | **Open design question.** This revision chose the artefact treatment and stated why; the promotion is defensible |
| **A91** | A forced-colors render of every v1 page passes the LOCK gate: no affordance is conveyed by background alone, and every element on `color.forced-colors-mapping`'s opt-out list re-adds a border | **New acceptance criterion — requires a §13 gate row** |
| **A92** | No block that renders more than 6 lines at any of the five breakpoints carries `text-wrap: balance` | **New acceptance criterion** |
| **A93** | Every `$extensions['com.acos.pick']` block carries `countKind` and `scope`; every `scope: "in-direction-repickable"` block carries a non-empty `validityList`. Ingest hard-fails otherwise | **New acceptance criterion** |
| **A94** | Two independent implementations of `token.direction-hash` over the same 24 slots produce the same 12-character prefix (fixture test with a manifesto containing non-ASCII, double spaces and CRLF) | **New acceptance criterion** |
| **A95** | The editor renders **zero** controls for any row whose Scope is `direction-slot` or `derived`, verified by walking the manifest rather than by inspection | **New acceptance criterion** |
| **A96** | Moving a card from a 6-col to a 3-col slot switches it across `cq-medium` → `cq-narrow` with no manual fix, and `grep`ping the built CSS finds no `@media` inside a component stylesheet (the enforcement half of A46) | **New acceptance criterion** |
| **A97** | `token.capability-manifest` is generated mechanically from §7's Count/Kind/Scope columns, and the count it declares for every group matches what was ingested | **New acceptance criterion** |

---
## 8. The component inventory

> **Revision note (this pass).** Section 8 was never audited in the original critic pass (a pipeline bug limited the critics to sections 13–20). This revision closes ten gaps found in a later audit. The substantive changes are: a **Tier** and a **Pick** column on every row so §8.2's "the list cannot drift" claim is checkable; corrected tier sizes (Tier B was understated roughly two-fold); a **[BEH]** marking that gives every keyboard/focus/live-region component a named audited primitive; explicit WCAG gates for hover overlays (1.4.13), auto-moving content (2.2.2), input purpose (1.3.5) and charts (1.1.1); three added states; six added inventory rows; a **mechanically regenerated v1 cut list** with the arithmetic shown; and concrete, testable definitions for "structural distance" and "indistinguishable" in §8.5. Every number below is computed from the tables in this file, not asserted.

### 8.1 Definitional rule (must be in the glossary)

> **A variant is a structurally distinct composition of the same component within one design direction.**
> Size, theme, density, state, icon-slot, and semantic colour are **computed axes** derived from the direction's tokens. They are never generated as picks and never count against the variant budget.

Without this line the budget silently multiplies ~20×. Untitled UI reports "5 button components + 940 variants"; Tailwind Plus reports 8 buttons. Same product category, different definition. **[V — untitledui.com/components and tailwindcss.com/plus/ui-blocks, both fetched 2026-07-25]**

**"Structurally distinct" is now a machine-checkable predicate, not a judgement call.** Every component declares a **variant axis vector** (§8.6); two variants of the same component are structurally distinct if their axis vectors differ in at least one axis. This is what makes §8.5's sort order, its "label the differing axis" caption, and its indistinguishability rule implementable rather than aspirational.

### 8.2 Three-tier variant budget

**The assignment rule (mechanical, applied at inventory time):**

1. **Tier A — identity-carrier.** The component is one a visitor reads as "the brand": high surface area × high frequency, and the direction's voice is legible in it at a glance. Count = **10**, or **12** for the six with the largest surface × frequency product.
2. **Tier C — artwork.** The item is a *set* of pictures rather than a composition ("which picture"). Count = **20**.
3. **Tier B — everything else**, banded by how much structural freedom the component actually has once its contract is fixed:
   - **B1 = 7–8** — high frequency, real but bounded structural freedom (buttons below primary, tabs, accordions, wrappers, split layouts).
   - **B2 = 4–6** — recurs, moderate freedom, usually one dominant axis (position, orientation, or shell).
   - **B3 = 2–3** — rare, or legally/conventionally fixed, or behaviour-dominant.
4. **Not a tier: `derived` and `n/a` rows.** These carry a **Pick** value of `computed` or `n-a`, render no control in the editor (`com.acos.pick.pickable: false`), and contribute zero variants. Same key as §7 uses.

Assign the tier at inventory time; the number then follows mechanically. **The check that the list has not drifted is now runnable:** for every row, `tier(count)` must equal the declared Tier cell, and every row must carry a Pick value. A row whose count does not match its tier band is a lint failure, not a judgement call.

**Actual tier sizes, computed from §8.3 as written in this file:**

| Tier | What | Count rule | Rows | Variants |
|---|---|---|---|---|
| **A** | Identity-carriers | **10**, or **12** for the six largest | **21** | **222** |
| **B1** | Structural, high-frequency | **7–8** | **33** | **262** |
| **B2** | Structural, moderate | **4–6** | **111** | **554** |
| **B3** | Rare / fixed / behaviour-dominant | **2–3** | **38** | **110** |
| **C** | Artwork sets | **20** | **4** | **80** |
| **—** | `derived` / `n/a` policy and contract rows | not picked | **9** | **0** |
| | **§8.3 total** | | **216** | **1228** |

**Correction to the previous figures.** The prior text sized the tiers at "~22 Tier A + ~90 Tier B + artwork" and the ARIA note referred to "~240 items". Two of those three were wrong:

- **Tier A ≈ 22 was right** — it is **21** rows.
- **Tier B ≈ 90 was understated roughly two-fold** — B1 + B2 + B3 is **182** rows carrying **926** variants. **This is a real scope increase against what §18 and §13 were sized on, not a re-labelling — see the sign-off note in §8.4.**
- **"~240 items" was right, but only when §9 is included** — which the previous text never said, so the figure looked unreconcilable against a §8.3 that enumerated 210 rows. Before this revision: 210 §8.3 rows + 31 §9.2/§9.3 rows = **241**. After the six rows added here: **216** + **31** = **247**. The ARIA note now states the arithmetic instead of leaving the reader to guess at it.

**Pick-key reconciliation:** 207 rows are `pick`, 2 are `computed`, 7 are `n-a` — 216 total, with no unmarked rows. This is the per-row marking §7 already had and §8 previously lacked, and it is what makes D1's "identity-carrying-and-picked, or derived-and-not-picked" reviewable against §8 at all.

**Market calibration:** Tailwind Plus (commercially curated) ships Hero 12, Feature 15, CTA 11, Pricing 12, Headers 11, Banners 13, Stats 8, Testimonials 8, FAQs 7, Footers 7, Team 9, Contact 7, Logo Clouds 6, Newsletter 6, 404 5, Bento 3; Application UI: Input Groups 21, Tables 19, Badges 16, Stacked Lists 15, Drawers 12, Radio Groups 12, Avatars 11, Navbars 11, Cards 10. Distribution 3–21, clustered 5–12, median ≈8. **The user's "10" is market-calibrated, not arbitrary. [V — fetched 2026-07-25]**

### 8.3 The variant-count table

**Column key.**

| Column | Values | Meaning |
|---|---|---|
| **Tier** | `A` / `B1` / `B2` / `B3` / `C` / `—` | The §8.2 band. The variant count must fall inside the band or the row is a lint failure |
| **Pick** | `pick` / `computed` / `n-a` | `pick` = the editor renders a variant strip. `computed` = derived from the direction vector, no control (`com.acos.pick.pickable: false`). `n-a` = a policy, contract, or coverage checklist, not a choice. Same key as §7 |
| **Variants** | a number, `derived`, or `n/a` | Distinct pickable options. Never multiplied by size/theme/density/state (§8.1) |
| **Priority** | `v1` / `v2` / `v3` | **§8.4 is generated from this column mechanically.** Editing this cell changes v1 scope |

**ARIA note.** Items marked **[APG]** map to one of the 30 W3C ARIA Authoring Practices Guide patterns **[V — w3.org/WAI/ARIA/apg/patterns/, full list retrieved 2026-07-25]**. Their variants are **skin-only**; behaviour comes from a single audited implementation, identical across all variants. **22 rows** carry it, out of 216 rows here (247 including §9). Free-form items (hero, bento, marquee, CTA band, background layer) are where the design system gets to speak.

**Behavioural-primitive note (new in this revision).** The previous text said where behaviour came from for **[APG]** items and was silent for everything else — leaving roughly a hundred variants of drawers, overlays, toasts, banners, pickers and dropzones with real keyboard, focus-trap and live-region contracts and **no named source of truth**, so each skin would have re-invented them. Items marked **[BEH]** now declare "behaviour comes from a shared audited primitive; variants are skin-only", exactly as **[APG]** does, and name the primitive. **61 rows** carry it. The primitives:

| Primitive | Contract | Used by |
|---|---|---|
| `overlay.dismissible-layer` | Focus trap, Escape, focus return to trigger, background `inert`, scroll lock, `aria-modal` | Mobile drawer, Drawer/sheet, Cart drawer, Search takeover, Command palette, Cookie banner (blocking form), Cookie preferences centre, Age gate, App sidebar (overlay mode), Product gallery zoom |
| `overlay.popup-nonmodal` | Anchored positioning + collision/flip, Escape to close without moving the pointer, hover-intent open/close delays, safe-triangle traversal, **WCAG 1.4.13** | Popover, Hover card, Mega menu, Dropdown/flyout (hover form), Tooltip |
| `live.announcer` | Single page-level polite and assertive regions, message queue, dedupe, `role=status` vs `role=alert` selection, **WCAG 4.1.3** | Toast, Inline alert (injected), Contact form result, Cart drawer, Chip removal, Notification list, Search result counts, Code-block copy, Activity feed |
| `disclosure.dismissible-region` | APG Disclosure + persisted dismissal + defined post-dismiss focus destination | Announcement/promo bar, Removable chip, Notification row, Multi-select tokens |
| `nav.current-location` | `aria-current` value selection, throttled updates, accessible names on numeric links | Scroll-spy rail, Pagination, Stepper, Language switcher |
| `nav.focus-mover` | Viewport moves are paired with programmatic focus moves | Back-to-top, Skip link, in-page anchors under a sticky ribbon |
| `input.text-affordance` | Search semantics, clear control naming, expand-and-focus | Search input control |
| `input.file-dropzone` | **WCAG 2.5.7** — drag is decoration over a real file input; keyboard + single-pointer path; progress via `live.announcer` | File upload / dropzone |
| `input.date-time` | APG Date Picker Dialog grid, arrow-key navigation, typed-entry alternative | Date picker, Time picker, Calendar |
| `input.segmented-code` | Grouped naming, paste-fills-all, backspace traversal | OTP / PIN input |
| `input.two-dimensional` | Arrow-key operation of a 2D area + text alternative (**2.5.7**) | Colour picker |
| `form.validation` | Error summary focus, per-field association, `aria-describedby` wiring, announcement once | Contact form, Form error summary, Multi-step wizard |
| `form.step-sequence` | Focus + announcement on step change, position statement | Multi-step wizard, Checkout |
| `media.player-controls` | Labelled transport controls, captions, no keyboard trap, **2.2.2** satisfied by the transport itself | Video player skin, Audio player, Video testimonial, Background video loop |
| `motion.auto-started` | Registers with the page's **2.2.2** pause registry; exposes pause/stop; honours the site-wide motion toggle | Background video loop, Animated counter (scroll-linked), Marquee (§9), Ambient background motion (§9), Auto-advancing carousel |
| `overlay.sticky-obstruction` | **WCAG 2.4.11** focus-not-obscured check, scroll-padding contribution, form-field non-occlusion | Sticky ribbon, Mobile sticky action bar, Sticky mobile CTA |
| `scroll.pinned-sequence` | §9.4 drag restriction, keyboard-reachable content, works with scroll-driven animation absent | Sticky scroll stack, Horizontal scroll section, Split-screen scroll |
| `table.responsive-strategy` | Per-variant declared reflow strategy; focusable scroll container | Basic table, Data table, Comparison table, Feature comparison matrix |

**A [BEH] row is not a weaker [APG] row.** The rule is identical: behaviour is written once, audited once, and identical across every variant of every component that names the primitive. The distinction is only that **[APG]** points at a published W3C pattern and **[BEH]** points at a primitive this project owns.

**Third-party note.** Items marked **[3P]** contain third-party marks with usage rules — platform CTA badges, social icons, trust/certification badges, press logos, map tiles. **These are not designable.** The variants are arrangement only. Generating a Steam button is a trademark violation. **8 rows** carry it.

#### Navigation

| Component | Tier | Pick | Variants | Priority | Rationale |
|---|---|---|---|---|---|
| Top ribbon / primary navigation **[BEH]** | A | pick | **10** | v1 | Tier A, seen on 100% of pages, user-named. Must satisfy WCAG 2.4.11 — a sticky ribbon must not entirely obscure a focused element. **[BEH] `overlay.sticky-obstruction`** — the 2.4.11 check, the `scroll-padding-top` contribution and the "does not cover the field being typed into" rule are one audited implementation shared with the mobile action bar and the sticky mobile CTA, not re-solved in each of the 10 skins |
| Nav scroll behaviour | B2 | pick | **6** | v1 | static, sticky-solid, sticky-shrink, hide-down/show-up, blur-on-scroll, detach-to-pill. Exactly six exist; more are easing differences (a token) |
| Mega menu panel **[BEH]** | B2 | pick | **6** | v2 | Limited layout freedom (columns × featured slot); minority of sites. **[BEH] `overlay.popup-nonmodal`** — Disclosure-per-top-item, not a Menubar, because the panel contains links and text rather than menu commands. **1.4.13 applies (§8.7-A1): dismissable via Esc without moving the pointer, hoverable across the gap between trigger and panel, persistent until dismissed. Coarse pointer: tap-to-open, tap-outside or an explicit close control to dismiss** |
| Dropdown / flyout menu **[APG]** | B1 | pick | **7** | v1 | Tailwind ships exactly 7; freedom is panel skin + arrow/offset. **[APG] Menu/Menubar or Disclosure depending on trigger.** All 7 carry the WCAG 2.2 SC 1.4.13 contract (§8.7-A1) if any of them opens on hover. **Coarse pointer: opens on tap, never on hover; the trigger is a real button with `aria-expanded`** |
| Mobile drawer / full-screen overlay menu **[BEH]** | A | pick | **10** | v1 | Tier A on award sites — the open/close choreography IS brand. NN/g warns hidden nav halves discoverability, so all 10 bake in a visible-CTA rule. **[BEH] `overlay.dismissible-layer`** — the same audited focus trap, Escape handler, focus return and background `inert` as Modal dialog; identical across all 10 skins |
| Mobile sticky action bar **[BEH]** | B2 | pick | **4** | v2 | Constrained by thumb reach and safe-area insets. **[BEH] `overlay.sticky-obstruction`** — must satisfy WCAG 2.4.11 against focused elements and must not cover the form field being typed into |
| Announcement / promo bar **[BEH]** | B1 | pick | **8** | v2 | Tailwind ships 13 but most differ only by dismissal affordance (a state). **[BEH] `disclosure.dismissible-region`** — APG Disclosure plus a persisted dismissal and a defined focus destination after dismiss (focus moves to the following landmark, never to `<body>`) |
| Breadcrumb **[APG]** | B2 | pick | **4** | v2 | Separator glyph, truncation, chip-vs-text. Genuinely small |
| In-page section rail / scroll-spy **[BEH]** | B2 | pick | **6** | v2 | left rail, right rail, top pills, dot column, numbered ticks, progress-linked. **[BEH] `nav.current-location`** — `aria-current="true"` on the active entry, updated without announcing on every scroll tick (the throttle rule lives in the primitive, not the skin) |
| App sidebar navigation **[BEH]** | B2 | pick | **6** | v3 | App shell; budget deliberately restrained. **[BEH] `overlay.dismissible-layer` in its collapsed/overlay mode**, plain landmark navigation when docked |
| Command palette (⌘K) **[BEH]** | B2 | pick | **4** | v3 | Tailwind ships 8 but they differ by result-row type; ~4 real shells. **[BEH] `overlay.dismissible-layer` + APG Combobox** (dialog-wrapped listbox with `aria-activedescendant`); the keyboard contract is identical across all 4 |
| Skip link **[BEH]** | B3 | pick | **2** | v1 | Compliance requirement, near-zero design surface. **Sits at the top of the z-index ladder.** **[BEH] `nav.focus-mover`** — the target must receive focus, not merely be scrolled to, and it must clear the sticky ribbon's scroll padding |
| Language / region switcher **[BEH]** | B2 | pick | **4** | v2 | Correctness matters far more than skin; forces RTL to be real. **[BEH] `nav.current-location`** — each option carries `lang` and `hreflang`; the current language is programmatically marked |
| Pagination **[BEH]** | B2 | pick | **4** | v2 | Rare and structural. **[BEH] `nav.current-location`** — `<nav aria-label>` + `aria-current="page"`; the accessible name of a bare number link must not be just "3" |
| Back-to-top control **[BEH]** | B2 | pick | **4** | v2 | Trivial surface, but the entrance choreography is a brand micro-moment. **[BEH] `nav.focus-mover`** — moving the viewport must also move focus to the top landmark, or keyboard users are returned visually but not programmatically |
| Reading / scroll progress indicator **[BEH]** | B2 | pick | **5** | v2 | Now cheaply native via CSS scroll-timeline. **[BEH] decorative-by-default: `aria-hidden="true"` unless it doubles as a real `progressbar`, in which case the APG Meter/Progressbar contract applies. A scroll indicator that announces on every frame is a screen-reader denial-of-service** |
| Search overlay + results dropdown **[BEH]** | B2 | pick | **6** | v2 | inline expand, dropdown panel, full-screen takeover, slide-down sheet, modal, sidebar. **[BEH] `overlay.dismissible-layer` (takeover/modal/sheet forms) + APG Combobox (inline/dropdown forms)**; results count announced once via `live.announcer`, not per keystroke |
| Tabs / in-page switcher **[APG]** | B1 | pick | **8** | v1 | underline, pill, enclosed, segmented, boxed, minimal, icon+label, vertical |

#### Hero

| Component | Tier | Pick | Variants | Priority | Rationale |
|---|---|---|---|---|---|
| Marketing hero | A | pick | **12** | v1 | Highest surface on the site; Tailwind ships 12; rubric double-weights the hero crop. **Above baseline is earned here and almost nowhere else** |
| Immersive media hero | B2 | pick | **6** | v2 | Distinct class needing a GPU-tier ladder and poster frame; 6 bounds the render/verification cost |
| Interior page header | B1 | pick | **8** | v1 | Used on every non-home page, so it carries real identity |
| Hero CTA cluster | B1 | pick | **8** | v1 | Recombines across all 12 heroes; the conversion pivot |
| Preloader / intro sequence **[BEH]** | B1 | pick | **8** | v2 | Award signature moment absent from every mainstream library. **Hard-constrained: skippable, ≤2s, never blocking LCP.** An unskippable brand preloader is a pure conversion tax. **[BEH] `live.announcer` + focus parking** — the skip control is the first focusable element; content behind it is not `inert` to crawlers |

#### Content

| Component | Tier | Pick | Variants | Priority | Rationale |
|---|---|---|---|---|---|
| Section header block | A | pick | **10** | v1 | Repeats 6–15× per page — Tier A despite looking trivial |
| Feature grid | A | pick | **12** | v1 | Tailwind ships 15. **The anti-slop lint bans the "three icon-topped cards" tell, so extra variants are needed to route AROUND the cliché** |
| Feature split (alternating) | B1 | pick | **8** | v1 | 50/50, 60/40, offset, overlap, full-bleed media, framed, in-device, bleed-edge |
| Bento grid | B2 | pick | **6** | v1 | Tailwind ships 3, but bento is a saturated-template risk and the anti-slop rule caps simultaneous trend matches; 6 gives room for a non-obvious span pattern |
| Sticky scroll stack **[BEH]** | B2 | pick | **6** | v2 | pin-and-cover, pin-and-scale, pin-and-fade, card-deck, list-sync, image-swap. **[BEH] `scroll.pinned-sequence`** — shares §9.4's drag restriction; content must remain reachable and readable with scroll-driven animation unsupported or disabled |
| Horizontal scroll section **[BEH]** | B2 | pick | **5** | v2 | Scrolljacking constraints (no text-reading in altered scroll, disabled on mobile) prune the space. **[BEH] `scroll.pinned-sequence`** — a horizontally scrolling region needs a keyboard-operable scroll container (`tabindex="0"` + accessible name) or its content is unreachable without a pointer |
| Split-screen scroll section | B2 | pick | **5** | v2 | pin-left, pin-right, both-pin, mirrored, diagonal |
| Generic content card | A | pick | **12** | v1 | Reused by blog, case study, team, product, feature — extra variants amortise across five categories |
| Card grid / collection layout | B1 | pick | **8** | v1 | Separated from the card so skin and rhythm swap independently |
| Stacked list row | A | pick | **10** | v2 | Tailwind's highest application count (15) because row density and meta arrangement genuinely vary |
| Rich text / prose body | B2 | pick | **6** | v1 | measure-narrow serif, measure-wide sans, two-column, marginalia, drop-cap, technical-docs. Measure and rhythm are computed |
| Content + media section | B1 | pick | **8** | v1 | The plain workhorse between marquee sections |
| Process / how-it-works steps | B1 | pick | **8** | v1 | horizontal numbered, vertical connected, zigzag, card row, tabbed, scroll-synced, arc, diagram-anchored |
| Timeline | B2 | pick | **6** | v2 | left rail, centre alternating, horizontal, scroll-driven, milestone-cards, compact list |
| Stat band | B1 | pick | **8** | v1 | Fastest credibility signal. Anti-slop lint flags the generic stat banner, so variants must include non-obvious forms |
| Pull quote | B1 | pick | **8** | v1 | Pure typography — where a direction's display face proves itself. Cheap to render, highly identity-revealing |
| FAQ / accordion **[APG]** | B1 | pick | **8** | v1 | bordered, divided, card, plus-minus, chevron, numbered, two-column, first-open |
| Comparison table **[BEH]** | B2 | pick | **5** | v2 | Heavily constrained by data shape and the mobile-reflow problem; includes the required card-stack fallback. **[BEH] `table.responsive-strategy`** — the reflow strategy is declared per variant and the scroll container is keyboard-focusable |
| Section divider / seam | A | pick | **10** | v1 | **Tier A. Juries read the seam between sections as craft.** Absent from every block library and one of the cheapest to render 10 of |
| Section wrapper | B1 | pick | **8** | v1 | flat, tinted, inverted, gradient, textured, image, video, glass. Padding and width computed |
| CTA band | A | pick | **12** | v1 | Recurs 2–4× per site at the conversion pivot |
| Newsletter block | B2 | pick | **6** | v1 | Form geometry dominates, narrowing layout freedom |
| Footer | A | pick | **10** | v1 | Tier A, second-most-seen component. **Also the mandatory home for the licence/attribution line** the evidence bundle requires |
| Blog index section | B1 | pick | **7** | v2 | featured-hero, three-up, list, magazine, masonry, categorised, minimal |
| Blog post body layout | B2 | pick | **5** | v2 | centred, left-TOC, right-marginalia, full-bleed-editorial, docs-style |
| Team section | B1 | pick | **9** | v2 | Photo shape and hover reveal give genuine variety |
| About / story section | B2 | pick | **6** | v2 | Largely a recomposition of prose + media + timeline |
| Careers / open roles | B2 | pick | **4** | v3 | Data-driven and structurally constrained |
| Contact section | B1 | pick | **7** | v2 | Form/map/detail arrangement genuinely varies |
| Legal / policy body | B3 | pick | **3** | v1 | plain, TOC-sidebar, numbered-clause. **Deliberately un-art-directed** — any more is wasted budget |
| Changelog / release list | B3 | pick | **3** | v3 | Data-shaped and rare |
| Feature callout / inline highlight | B2 | pick | **6** | v2 | Six semantic treatments; colour mapping computed |

#### Social proof

| Component | Tier | Pick | Variants | Priority | Rationale |
|---|---|---|---|---|---|
| Logo wall **[3P]** | B1 | pick | **8** | v1 | Logo normalisation (optical sizing) is computed, not a variant |
| Logo marquee **[3P]** | B2 | pick | **6** | v1 | Shares the marquee container, so cost is low |
| Testimonial card | A | pick | **10** | v1 | **Tier A — the most trust-loaded component on a B2B site**, and the quote typography carries the direction |
| Testimonial wall / masonry | B2 | pick | **6** | v2 | Largely a composition of the card in a grid |
| Testimonial carousel **[APG]** | B2 | pick | **6** | v2 | The APG contract (pause control, no auto-advance without it) constrains the space and must be identical across all six. **WCAG 2.2.2 (Level A) applies to every auto-advancing variant — see §8.7-A2** |
| Video testimonial **[BEH]** | B2 | pick | **4** | v3 | Needs the video facade underneath; own design surface is small. **[BEH] `media.player-controls`** — captions, keyboard-operable controls and a real accessible name on the player |
| Rating / review summary **[3P]** | B2 | pick | **5** | v2 | Source badges are fixed third-party marks |
| Press mentions row **[3P]** | B2 | pick | **5** | v2 | Genuinely low-variance |
| Case-study / result callout | B1 | pick | **8** | v2 | Highest-converting B2B proof unit; combines stat + quote + card |
| Trust / certification badges **[3P]** | B2 | pick | **5** | v2 | Third-party marks with usage rules; variation is layout only |
| Award badge / laurels | B2 | pick | **4** | v2 | Genuine identity moment on studio/portfolio sites |
| Animated counter **[BEH]** | B2 | pick | **6** | v2 | odometer, tabular-tick, blur-in, split-flap, ease-count, scroll-linked. **Must ship a reduced-motion static variant.** **[BEH] `motion.auto-started` (§8.7-A2).** WCAG 2.2.2 (Level A) exempts motion that stops within 5 seconds, so a one-shot count-up under 5s is compliant without a control; **the scroll-linked variant, which can restart on every re-entry, is NOT exempt and must delegate to the Auto-motion pause/stop control.** `prefers-reduced-motion` does not satisfy 2.2.2 — it is an OS preference, not a mechanism on the page |

#### Commerce

| Component | Tier | Pick | Variants | Priority | Rationale |
|---|---|---|---|---|---|
| Pricing section | A | pick | **12** | v1 | Tailwind ships 12 — matching its hero count, which tells you the market treats pricing as hero-grade |
| Plan card | A | pick | **10** | v1 | The emphasised-tier treatment is a real design decision |
| Pricing period toggle | B2 | pick | **4** | v1 | pill switch, segmented, checkbox+label, tab |
| Feature comparison matrix | B2 | pick | **5** | v2 | Includes the mandatory per-plan-column mobile fallback |
| Product card | A | pick | **10** | v2 | Tier A for commerce — it tiles the whole catalogue |
| Product detail / gallery **[BEH]** | B2 | pick | **6** | v3 | Highly constrained by conventions users expect; deviating hurts conversion. **[BEH] `overlay.dismissible-layer` for the zoom/lightbox path; thumbnail rail is a Tablist or a Listbox, never bare divs** |
| Cart drawer / mini cart **[BEH]** | B2 | pick | **4** | v3 | drawer, dropdown, full-page, sheet. **[BEH] `overlay.dismissible-layer` + `live.announcer`** — "added to cart" must be announced; the drawer's focus trap and Escape behaviour are the modal primitive's, not re-invented per skin |
| Checkout layout **[BEH]** | B2 | pick | **4** | v3 | **Novelty here is score-negative.** one-page, accordion, multi-step, express-first. **[BEH] `form.step-sequence`** — step changes move focus to the new step heading and announce position ("Step 2 of 4") |
| Platform CTA badge registry **[3P]** | B2 | pick | **5** | v1 | Steam/App Store/Play/itch/Epic marks are **deterministic embeds, never invented**. The 5 variants are arrangement only. **Present in the v1 set (§8.4) — it was missing from the previous hand-written v1 list** |
| Wishlist / preorder CTA | B2 | pick | **4** | v2 | Hierarchy is fixed (Wishlist → Discord → press); only presentation varies |
| Booking / scheduling block **[BEH]** | B2 | pick | **4** | v3 | Usually a third-party iframe; the surface is the frame and loading state. **[BEH] every iframe carries a `title`; the loading state is announced once. Third-party iframe accessibility is outside our control — record it as an accepted, disclosed limitation in the evidence bundle rather than claiming conformance** |
| Donation / support block | B3 | pick | **3** | v3 | preset-row, preset-grid, slider |
| Promo / coupon field | B3 | pick | **3** | v3 | Known UX trap (a visible coupon field increases abandonment) — one variant is collapsed-by-default |

#### Form

| Component | Tier | Pick | Variants | Priority | Rationale |
|---|---|---|---|---|---|
| Primary button | A | pick | **10** | v1 | Tier A. The 10 are shape/fill/edge/motion treatments; size and state are computed |
| Secondary button | A | pick | **10** | v1 | **Its relationship to the primary is a design decision, not a derivation** — outline, tinted, elevated and ghost all read differently against the same primary |
| Ghost / tertiary button | B1 | pick | **8** | v1 | Risk is that it stops reading as interactive; all 8 checked against a hit-affordance rule |
| Icon button | B1 | pick | **8** | v1 | Touch-target minimum and accessible-name requirement apply to all eight. **Every icon button pairs with a Tooltip, so all eight inherit the 1.4.13 contract (§8.7-A1); the `aria-label` is authoritative and the tooltip is supplementary, never the only carrier of the label** |
| Destructive button | B2 | pick | **4** | v2 | Semantics dominate aesthetics; all 4 must pass contrast against the danger ramp |
| Split button | B3 | pick | **3** | v3 | Rare outside app shells |
| Button group / segmented control | B2 | pick | **6** | v2 | joined, spaced, pill, boxed, underline, icon-only |
| Floating action button | B2 | pick | **4** | v3 | The Material 3 canonical set: mini, standard, extended, speed-dial |
| Inline text link | A | pick | **10** | v1 | **Tier A and consistently underrated** — the link hover animation is one of the cheapest, most-repeated craft signals on an award site. Underline thickness/offset stay tokens |
| Text input | A | pick | **10** | v1 | **Tier A: input chrome defines a system's voice as strongly as the button.** Tailwind ships 21 input groups |
| Textarea | B2 | pick | **5** | v1 | Inherits input chrome; only sizing/resize/counter vary |
| Select **[APG]** | B2 | pick | **6** | v1 | Native-vs-custom is a capability flag, not a variant |
| Combobox / autocomplete **[APG]** | B2 | pick | **5** | v2 | Behaviour dominates and must be identical across skins |
| Multi-select / token field **[BEH]** | B2 | pick | **4** | v3 | Overflow behaviour ("+3 more") is the only real decision beyond chip skin. **[BEH] APG Combobox (multi-select pattern) + `disclosure.dismissible-region` for token removal; each token's remove control needs its own accessible name ("Remove <token>")** |
| Checkbox **[APG]** | B1 | pick | **8** | v1 | The check animation is a small identity moment |
| Radio group **[APG]** | B1 | pick | **8** | v1 | Tailwind ships 12 because card-style and table-style radios are structurally different. **Present in the v1 set (§8.4) — it was missing from the previous hand-written v1 list, which would have shipped a form system with no radio group** |
| Toggle switch **[APG]** | B1 | pick | **8** | v1 | Knob motion and track treatment are visible brand micro-moments. **Present in the v1 set (§8.4) — it was missing from the previous hand-written v1 list** |
| Slider / range **[APG]** | B2 | pick | **6** | v2 | Dual-thumb is a capability flag across all six, not a separate family |
| Number stepper **[APG]** | B2 | pick | **4** | v3 | Low identity surface |
| Date picker **[BEH]** | B2 | pick | **5** | v2 | Locale/RTL correctness matters far more than skin. **[BEH] `input.date-time` — APG Date Picker Dialog: grid role, arrow-key navigation, `aria-selected`, Escape returns focus to the trigger. A text input alternative must always exist (2.5.7 / 1.3.5 `autocomplete="bday"` family where applicable)** |
| Time picker **[BEH]** | B3 | pick | **3** | v3 | Almost never on a marketing site. **[BEH] `input.date-time`; typed entry always available** |
| File upload / dropzone **[BEH]** | B2 | pick | **6** | v2 | The drop-target and the file-row are two design surfaces. **[BEH] `input.file-dropzone` — WCAG 2.5.7 Dragging Movements (AA): the drop target is a decoration on top of a real `<input type=file>`; keyboard and single-pointer upload must work with no drag. Upload progress and completion go through `live.announcer`** |
| OTP / PIN input **[BEH]** | B3 | pick | **3** | v3 | Behaviour (paste, backspace, `autocomplete=one-time-code`) matters more than skin. **[BEH] `input.segmented-code` — the segmented boxes are a presentation over one field or a labelled group; each box needs a name, and paste must fill the whole code** |
| Rating input **[BEH]** | B2 | pick | **4** | v3 | Must expose a real radio group underneath. **[BEH] APG Radio Group; the star glyphs are `aria-hidden` decoration over labelled radios** |
| Colour picker **[BEH]** | B3 | pick | **3** | v3 | Untitled ships 6 but they are mode variations, not designs. **[BEH] `input.two-dimensional` — a 2D saturation/value area needs arrow-key operation and a text entry alternative (2.5.7)** |
| Field group (label / help / error) | B2 | pick | **6** | v1 | **Tier A adjacent: this single decision reshapes every form on the site.** shadcn now ships it as a first-class "Field" |
| Form layout | B2 | pick | **6** | v1 | Tailwind ships only 4 because single-column is near-universally correct; 6 adds sectioned and inline |
| Multi-step form wizard **[BEH]** | B2 | pick | **5** | v3 | Composes stepper + form layout. **[BEH] `form.step-sequence` — focus and announcement on step change; errors from a failed step land in the Form error summary** |
| Inline email capture | B2 | pick | **6** | v1 | The smallest conversion unit; appears 2–4× per site |
| Contact form **[BEH]** | B2 | pick | **6** | v1 | Needs designed success/error/submitting — those are **states, not variants**. **[BEH] `live.announcer` for submit result + `form.validation` for the error path; the failed-submit path renders the Form error summary and moves focus to it. Every field carries its 1.3.5 `autocomplete` token (§8.7-A3)** |
| Form error summary **[BEH]** | B2 | pick | **4** | v1 | The list of errors rendered at the top of a failed form, each entry linking to its field. **Newly added — the inventory previously had only per-field errors (Field group), leaving the form-level error presentation undefined.** The standard remediation for WCAG 3.3.1 Error Identification and 3.3.3 Error Suggestion on multi-field forms, and the one form surface a design system must art-direct because it appears at the top of the page after a failed submit. The 4: bordered banner, inline list, card, sidebar-anchored. **[BEH] `form.validation` — focus moves to the summary on failed submit; each entry is a link to the field; the count is announced once** |
| Required / optional indicator policy | — | n-a | **n/a** | v1 | **Newly added policy row.** Asterisk-on-required vs "(optional)"-on-optional is a system-wide decision, not a per-form one, and it has an accessible-name consequence: a bare `*` must not end up inside the accessible name as "asterisk". The policy fixes the glyph, its `aria-hidden` treatment, the legend text, and the `required`/`aria-required` pairing. Not pickable — one answer applies to every form on the site |
| `autocomplete` field-purpose mapping | — | n-a | **n/a** | v1 | **Newly added policy row.** WCAG 2.2 SC 1.3.5 Identify Input Purpose (Level AA) requires the standard `autocomplete` token on every input collecting information about the user — name, email, tel, organization, street-address, country, postal-code, bday, and the rest of the WCAG-listed input-purpose set. Before this row, `autocomplete` appeared exactly once in the whole inventory (`one-time-code` on the OTP row), so every contact form and newsletter block in the v1 cut list would have shipped non-conformant. The mapping is a table, not a design choice. **The paired token item `interaction.autocomplete-map` is requested from §7 — see §8.8-X1** |
| Consent checkbox | B3 | pick | **3** | v1 | Legally constrained (unchecked by default, explicit, not bundled) |
| Search input control **[BEH]** | B2 | pick | **6** | v2 | Includes the expanding form (Carbon ships `ExpandableSearch` as a distinct component for this reason). **[BEH] `input.text-affordance` — `role="searchbox"` or `<input type=search>` in a labelled `<form role=search>`; the clear button has its own name; the expanded state moves focus into the field. `autocomplete="off"` here is deliberate and is the documented exception to §8.7-A3** |

#### Feedback

| Component | Tier | Pick | Variants | Priority | Rationale |
|---|---|---|---|---|---|
| Toast / snackbar **[BEH]** | B2 | pick | **6** | v2 | Position and stacking are configuration; semantic colour computed. **[BEH] `live.announcer` — `role="status"`/`aria-live="polite"` for informational, `role="alert"` for errors; auto-dismiss timing must satisfy WCAG 2.2.1 Timing Adjustable or not auto-dismiss at all when the toast carries an action** |
| Inline alert **[BEH]** | B2 | pick | **6** | v1 | Semantic colour computed from the ramp; only the shell varies. **[BEH] `live.announcer` when injected after load; a statically rendered alert is not a live region and must not be one** |
| Modal dialog **[APG]** | B1 | pick | **8** | v1 | The enter/exit choreography and scrim treatment are genuine identity choices |
| Confirm / alert dialog **[APG]** | B2 | pick | **4** | v2 | Deliberately constrained — the decision, not the design, is the point |
| Drawer / sheet **[BEH]** | B2 | pick | **6** | v2 | Tailwind ships 12 but half differ only by edge (config, not variant). **[BEH] `overlay.dismissible-layer` — identical focus trap, Escape, focus return and `inert` background as Modal dialog. This is the same primitive as Mobile drawer and Cart drawer; three skins, one audited behaviour** |
| Popover **[BEH]** | B2 | pick | **5** | v2 | arrow, arrow-less, elevated, bordered, glass. Collision logic shared. **[BEH] `overlay.popup-nonmodal` + WCAG 1.4.13 (§8.7-A1) for any hover-triggered instance. Coarse pointer: click/tap-triggered with an explicit close control** |
| Tooltip **[APG]** | B2 | pick | **6** | v1 | High frequency, small surface, low render cost. **A required companion to every icon button.** **WCAG 1.4.13 (AA) governs all 6 (§8.7-A1): dismissable with Escape without moving the pointer, hoverable (the pointer can travel into the tooltip without it vanishing), persistent until dismissed or invalid. Coarse pointer: the tooltip content must also be reachable another way — the icon button keeps its `aria-label`, and any information carried ONLY by the tooltip is a defect, because there is no reliable hover on touch** |
| Hover card **[BEH]** | B2 | pick | **4** | v3 | Desktop-only in origin, but **"degrade" is now defined, not assumed**: under `@media (hover: none)` or `pointer: coarse` the trigger becomes an explicitly tappable control that opens the same content as a dismissible popover with a visible close control; if the content is purely supplementary the variant may instead inline it. **Silently unavailable is not a permitted degradation** (§9 already forbids hover-only affordances). **[BEH] `overlay.popup-nonmodal` + WCAG 1.4.13 (§8.7-A1)** |
| Progress bar **[APG]** | B2 | pick | **5** | v2 | Indeterminate animation must respect reduced-motion |
| Spinner / loader | B1 | pick | **8** | v1 | **Tier A adjacent — one of the few components a visitor stares at.** arc, dots, bars, morph, logo-mark, orbit, pulse, custom-glyph, all with reduced-motion fallbacks |
| Skeleton placeholder **[BEH]** | B2 | pick | **5** | v2 | Per-component shapes derived from component geometry. **[BEH] `aria-busy` on the region being replaced; the shimmer is decorative and respects reduced motion** |
| Empty state | B1 | pick | **8** | v2 | NN/g treats empty states as a design discipline |
| Error state | B2 | pick | **6** | v2 | **Each must include a real recovery action** — that's a gate, not a variant |
| Success / confirmation state | B2 | pick | **5** | v2 | Animated check needs a reduced-motion equivalent |
| Cookie / consent banner **[BEH]** | B2 | pick | **6** | v1 | **The first thing a visitor sees, so it must be art-directed** — but legally constrained (reject as easy as accept) to 6. **[BEH] `overlay.dismissible-layer` in its blocking form / `disclosure.dismissible-region` in its non-blocking form; focus moves into the banner on appearance and returns to the document start on dismissal. It must not trap focus without offering a decision path** |
| Notification list / inbox **[BEH]** | B3 | pick | **3** | v3 | App-shell only. **[BEH] `live.announcer` for new arrivals (polite, batched) + `disclosure.dismissible-region` per row** |
| Badge / tag / pill | A | pick | **12** | v1 | Highest small-element count anywhere (Tailwind 16, Untitled 380 permutations) because it's combinatorially cheap. **12 shape-and-treatment variants; semantic colour and size computed** — this flag alone removes ~40% of a naive budget |
| Removable chip / filter chip **[BEH]** | B2 | pick | **6** | v2 | Material 3's four chip types plus dismiss-glyph treatments. **[BEH] `disclosure.dismissible-region` — each remove control carries "Remove <label>" as its accessible name, and removal announces the new result count through `live.announcer`. Backspace-to-remove is an addition, never the only route** |
| Status indicator dot | B2 | pick | **4** | v2 | **Must never be colour-only** |
| Avatar | B1 | pick | **8** | v2 | 8 shape-and-treatment designs; the rest computed |
| Avatar group / stack | B2 | pick | **4** | v2 | Derives skin from avatar |
| Kbd / keyboard key | B3 | pick | **3** | v3 | Docs and app-shell micro-surface |
| Toolbar **[APG]** | B2 | pick | **4** | v3 | Keyboard contract fixed by APG |

#### Data display

| Component | Tier | Pick | Variants | Priority | Rationale |
|---|---|---|---|---|---|
| Basic table **[APG]** | B1 | pick | **8** | v2 | **Each variant declares its own responsive strategy** (scroll container vs stacked cards) — otherwise this is the one component that breaks 390px |
| Data table **[APG]** | B2 | pick | **5** | v3 | Behaviour-dominant; skin derives from basic table |
| Description / spec list | B2 | pick | **6** | v2 | stacked, inline, two-column, bordered, striped, card-wrapped |
| Stat tile / KPI card | A | pick | **10** | v2 | Tier A for data-heavy sites. **The delta treatment must never be colour-only** — the arrow glyph or the sign is the non-colour carrier, per the same rule as Status indicator dot. **Chart accessible-alternative contract applies where a tile embeds a sparkline (§8.7-A4)** |
| Sparkline | B2 | pick | **4** | v2 | line, area, bar, win-loss — the complete standard set. **Non-text content: each ships an accessible name plus either a visually-hidden value summary or `aria-hidden` when the adjacent number already states the value (§8.7-A4)** |
| Line chart | B2 | pick | **6** | v2 | single, multi-series, stepped, smoothed, confidence-band, annotated |
| Area chart | B2 | pick | **4** | v2 | single, stacked, 100% stacked, stream |
| Bar / column chart | B1 | pick | **8** | v2 | vertical/horizontal × plain/grouped/stacked/100% |
| Pie / donut chart | B2 | pick | **4** | v2 | Deliberately small — only defensible for ≤5 categories and should be discouraged beyond |
| Gauge / progress ring | B2 | pick | **6** | v2 | arc, full ring, segmented, multi-ring, needle, bullet |
| Scatter / bubble | B3 | pick | **3** | v3 | scatter, bubble, with-trendline |
| Heatmap | B3 | pick | **3** | v3 | matrix, calendar, density. Ramp computed and colourblind-checked |
| Funnel chart | B3 | pick | **3** | v3 | tapered, stepped-bar, sankey-lite |
| Radar chart | B3 | pick | **3** | v3 | single, overlaid, filled |
| Waterfall chart | B3 | pick | **3** | v3 | Finance-standard, specialised |
| Treemap | B3 | pick | **2** | v3 | flat, nested-with-headers |
| Map (pin / choropleth) **[3P]** | B2 | pick | **4** | v3 | **Tile-provider licensing is a hard gate, not a design choice.** **[BEH] a map is exempt from 1.4.10 reflow but not from 1.1.1 — a text list of the plotted locations is the required alternative** |
| Chart chrome kit | B2 | pick | **4** | v2 | minimal, gridded, bordered-technical, editorial. **One decision applied across all 12 marks — this is what makes a site's charts read as one system.** **The chrome kit is also where the accessible-alternative slot lives (caption, source line, and the visually-hidden data table container), so it ships once and every mark inherits it (§8.7-A4)** |
| Chart colour ramps | — | computed | derived | v2 | From OKLCH anchors per D1. The `dataviz` skill ships a runnable validator |
| Chart accessible-alternative contract | — | n-a | **n/a** | v2 — ships with the first chart | **Newly added contract row.** WCAG 1.1.1 Non-text Content is Level A and a chart is non-text content by definition, yet §7.11 covers only colour. Every chart mark (the 12 marks + Sparkline + any Step-6 custom chart) must emit: (1) an accessible name and a short description — `role="img"` with `aria-label`/`aria-labelledby` for a static SVG, or a `<figure>`/`<figcaption>` pair; (2) either a visually-hidden data table or a one-sentence text summary carrying the same information as the mark; (3) a non-colour carrier for every distinction the mark makes — series identity, delta sign, threshold crossing — matching the existing stat-tile and status-dot rules. **Because §20.1/§17-O14 put v1 charts on a build-time SVG path, the alternative must be emitted at build time or it does not exist at all.** Gated at LOCK by proposed gate 31 (§8.7-A4). **The user named graphs and charts explicitly (vision step 6), so this is a named feature that was heading for release without its Level A floor** |
| Progress steps / stepper **[BEH]** | B2 | pick | **6** | v2 | Untitled reports 489 permutations, mostly state × orientation; 6 distinct designs. **[BEH] `nav.current-location` — `aria-current="step"`; a numbered circle is not a name** |
| Tree view **[APG]** | B3 | pick | **3** | v3 | Behaviour-dominant, app-shell only |
| Calendar **[BEH]** | B2 | pick | **4** | v3 | month, week, day, agenda-list. **[BEH] `input.date-time` grid contract; the same primitive as Date picker** |
| Kanban board **[BEH]** | B3 | pick | **3** | v3 | App-shell only. **[BEH] WCAG 2.5.7 — every card move available without dragging (a "move to column" menu); this is the clearest 2.5.7 case in the inventory** |
| Code block **[BEH]** | B2 | pick | **5** | v2 | **Highlight theme derived from the direction's palette**, never imported, or it clashes with everything. **[BEH] the copy control announces success through `live.announcer`; the pre/code region is keyboard-scrollable when it overflows** |
| Activity feed **[BEH]** | B2 | pick | **4** | v3 | timeline, compact-list, grouped-by-day, with-comments. **[BEH] `live.announcer` only when the feed streams; a static feed is not a live region** |

#### Media

| Component | Tier | Pick | Variants | Priority | Rationale |
|---|---|---|---|---|---|
| Image figure / frame | A | pick | **10** | v1 | **Tier A** — the frame (bleed, inset, masked, tilted, layered, bordered, shadowed) is where the direction shows on every photo |
| Image gallery grid | B1 | pick | **8** | v2 | Portfolio and case-study sites live on this |
| Lightbox **[APG]** | B2 | pick | **4** | v2 | Focus-trap and keyboard contract fixed; only chrome and transition vary |
| Carousel / slider **[APG]** | B1 | pick | **8** | v2 | peek, full-bleed, centred, coverflow, thumbnail-synced, drag-only, ticker-hybrid, stacked |
| Before/after slider **[BEH]** | B3 | pick | **3** | v3 | All three need a keyboard-accessible fallback. **[BEH] APG Slider + WCAG 2.5.7 — arrow keys move the divider; a drag-only implementation fails at AA** |
| Video player skin **[BEH]** | B2 | pick | **6** | v2 | Captions and keyboard control non-negotiable across all six; **the poster frame is what most visitors actually see**. **[BEH] `media.player-controls` — labelled controls, captions track, no keyboard trap, and 2.2.2 satisfied by the transport controls themselves** |
| Third-party video facade **[BEH]** | B2 | pick | **4** | v2 | **Saves ~500KB–1MB of pre-interaction JS.** Exists for the performance gate as much as for design — the naive embed is a Lighthouse killer. **[BEH] the facade is a real button with an accessible name ("Play <video title>"); activating it must move focus into the loaded player** |
| Background video loop **[BEH]** | B2 | pick | **5** | v2 | Loop engineering and a 4–16s cap constrain all five. **WCAG 2.2.2 Pause, Stop, Hide (Level A) is mandatory on all five (§8.7-A2): a 4–16s auto-playing loop exceeds the 5-second exemption, so every variant ships a visible pause/stop control — placed inside the container's bottom-inline-end safe zone, ≥24×24 CSS px (2.5.8), ≥3:1 against the busiest frame of the loop (1.4.11), and persistent (not hover-revealed, because hover does not exist on touch).** The control may delegate to the site-wide Auto-motion pause/stop control but must be reachable in the tab order near the video. `prefers-reduced-motion` alone does NOT satisfy 2.2.2. **[BEH] `motion.auto-started` + `media.player-controls`** |
| Audio player **[BEH]** | B3 | pick | **3** | v3 | Rare on marketing sites. **[BEH] `media.player-controls`; any auto-playing audio longer than 3 seconds also triggers WCAG 1.4.2 Audio Control (Level A) — default to not autoplaying** |
| Icon set | C | pick | **20** | v1 | Artwork tier. 20 candidate **SETS**, not 20 icons. Recraft V4 is the only true native-SVG generator per the prior report. Grid, stroke width, corner style are tokens shared by all icons in a set |
| Illustration set | C | pick | **20** | v2 | Artwork tier; parallel-scannable as a filtered grid |
| Decorative spot-graphic set | C | pick | **20** | v1 | Artwork tier, **disproportionately high identity return per unit of effort** — the marks that make a page feel hand-made |
| Pattern / texture library | C | pick | **20** | v1 | Artwork tier. **The single cheapest anti-slop move available** — the flat-gradient-card look is an enumerated AI tell |
| Logo lockup set | B2 | pick | **6** | v1 | The standard brand deliverable set; arrangements of a fixed mark |
| Photography treatment | B1 | pick | **8** | v2 | Applied globally — a direction-level decision. **The implementation of the ban on unstyled stock** |
| 3D model / product viewer **[BEH]** | B3 | pick | **3** | v3 | GPU-tier ladder is a gate, not a variant. **[BEH] WCAG 2.5.7 — orbit/zoom must have non-drag equivalents; a static poster image with alt text is the required fallback** |
| Gaussian splat embed | B3 | pick | **2** | v3 | Differentiation lives in the captured content, not the container; bandwidth caps how many can exist |

#### Motion / art containers — see §9

The 16 container kinds and 15 animation kinds live in §9 per **D4** — motion is an ordinary design-system item and animated pieces sit in the same draggable containers as artwork, so they are inventoried there rather than duplicated here. **They are counted in this section's totals wherever a total is stated** (§8.2's ~240 items, §8.4's v1 arithmetic), because the previous text's figures silently included them and the reconciliation failed as a result. Tier and Pick columns apply to §9's rows on the same rule: `motion.expressiveness` and the easing/duration matrices are `computed`, container kinds and animation kinds are `pick`, and the signature moment is deliberately **not** a swap catalogue.

#### Utility

| Component | Tier | Pick | Variants | Priority | Rationale |
|---|---|---|---|---|---|
| Layout container widths | — | computed | derived | v1 | **Also what the editor's gridlines snap to per D2** — must be data, not decoration |
| Editor grid overlay | — | n-a | **n/a** | v1 | Editor chrome, not a site component |
| Theme toggle **[BEH]** | B2 | pick | **6** | v2 | icon switch, segmented tri-state, animated sun/moon, text link, in-menu, auto-with-override. **The transition between themes is a visible craft moment**; needs a no-flash first-paint strategy. **[BEH] a real control with state (`aria-pressed` for binary, radio group for tri-state); the change is announced once. The tri-state variant is what exposes `prefers-contrast: more` where a direction ships the third solve (§7.2)** |
| Motion toggle **[BEH]** | B3 | pick | **3** | v1 | Compliance item, minimal latitude. footer, header, first-visit prompt. **[BEH] persisted preference that overrides `prefers-reduced-motion` in both directions; it is the site-wide half of the 2.2.2 story but does NOT replace per-component pause controls (§8.7-A2)** |
| Auto-motion pause/stop control | B3 | pick | **3** | v1 | **Newly added component.** The single shared control that satisfies WCAG 2.2.2 Pause, Stop, Hide (Level A) for every auto-moving thing on the page: marquee/ticker (§9), background video loop, auto-advancing carousel, scroll-linked counters, ambient background motion. The 3: in-container corner control, section-level control in the section chrome, page-level floating control. Each is ≥24×24 CSS px (2.5.8), ≥3:1 against the busiest frame behind it (1.4.11), keyboard-reachable adjacent to the thing it controls, and persistent rather than hover-revealed. **It is a component, not a token, because its placement is a composition decision — but its behaviour is one audited primitive `motion.auto-started`** |
| Pointer / hover capability policy | — | n-a | **n/a** | v1 | **Newly added policy row.** The site-wide rule for `@media (hover: hover)`, `@media (hover: none)`, `pointer: fine` / `pointer: coarse` and `any-pointer`: which affordances may be hover-only (none that carry information), what each hover-triggered family does on a coarse pointer, and the fact that a hybrid device can report both. Consumed by Tooltip, Popover, Hover card, Dropdown/flyout, Mega menu, the cursor-effect layer and every §9.3 hover micro-reaction. **The paired token item `interaction.pointer-capability-policy` is requested from §7.4 — see §8.8-X1** |
| Sound toggle **[BEH]** | B3 | pick | **3** | v2 | Must default off and persist. **[BEH] state-carrying control; WCAG 1.4.2 for any sound over 3 seconds** |
| Age gate **[BEH]** | B3 | pick | **3** | v2 | Legally shaped; must not block crawlers or LCP unnecessarily. **[BEH] `overlay.dismissible-layer` without an Escape dismissal (the decision is the exit); focus starts inside it** |
| Social links row **[3P]** | B2 | pick | **5** | v1 | Marks must not be redrawn to match the direction |
| Social share row | B2 | pick | **4** | v2 | Privacy-preserving implementation (plain intent URLs, no SDKs) constrains all four |
| Sticky mobile CTA **[BEH]** | B2 | pick | **4** | v2 | Must not obscure the footer or form fields — a gate, not a design choice. **[BEH] `overlay.sticky-obstruction` — the same 2.4.11 contract as the sticky ribbon and the mobile action bar** |
| Cookie preferences centre **[BEH]** | B3 | pick | **3** | v2 | modal, drawer, page. Reject as easy as accept in all three. **[BEH] `overlay.dismissible-layer` for the modal and drawer forms; each category is a labelled group of real switches, and "save" announces the result** |
| OG / social share card template | B3 | pick | **3** | v1 | Generated at build time from the direction's type and colour |
| Favicon / app-icon set | — | n-a | **n/a** | v1 | Derived export from the logo mark. Routinely missing from AI-built sites |
| Anti-spam honeypot / timing check | — | n-a | **n/a** | v2 | A contact form without it is a delivery defect; CAPTCHA is an accessibility and privacy cost |

#### Page templates

| Template | Tier | Pick | Variants | Priority | Rationale |
|---|---|---|---|---|---|
| Home / landing | B2 | pick | **6** | v1 | proof-early, story-led, product-led, comparison-led, single-scroll-narrative, directory-style |
| About | B2 | pick | **4** | v2 | Largely recomposition |
| Product / feature | B2 | pick | **5** | v2 | Most-duplicated on B2B sites; the sequence must survive being repeated 6–10× |
| Pricing | B2 | pick | **4** | v1 | Order (cards → matrix → FAQ → CTA) close to fixed by conversion evidence |
| Blog index | B2 | pick | **4** | v2 | Drives CMS collection wiring |
| Blog post | B2 | pick | **4** | v2 | Prose treatment is a separate component; the template decides furniture placement |
| Case study | B2 | pick | **4** | v2 | Highest-value page type on an agency/B2B site |
| Contact | B2 | pick | **4** | v2 | Conventional by design — visitors arrive with a task |
| Team | B3 | pick | **3** | v3 |  |
| Careers + job detail | B3 | pick | **3** | v3 | Usually ATS-fed, which constrains layout |
| Legal | B3 | pick | **2** | v1 | plain, TOC-sidebar. Required for Play/App Store and GDPR, deliberately un-art-directed |
| 404 | B2 | pick | **6** | v1 | **All six required to carry a working search or nav back to real content** |
| 500 / error | B3 | pick | **3** | v2 | **All self-contained (inline critical CSS)** because the failure may be in the asset pipeline itself |
| Coming soon / waitlist | B2 | pick | **4** | v2 | Often the first thing shipped |
| Press kit | B3 | pick | **3** | v2 | The dopresskit() convention journalists expect; novelty is counterproductive |
| Search results | B3 | pick | **3** | v3 | The zero-result state is what actually matters |
| Auth screens | B2 | pick | **5** | v3 | App-shell only; backend-free via MSW mocking |
| Dashboard shell | B2 | pick | **4** | v3 | Every state must be screenshot-QA'd |
| Settings | B3 | pick | **3** | v3 | tabbed, sidebar-nav, single-scroll |
| Docs | B3 | pick | **3** | v3 | Heavily standardised; deviation costs comprehension |
#### States — not variants, never picked

| State set | Pick | Rationale |
|---|---|---|
| Interactive state matrix (default / hover / active / focus-visible / disabled / loading / selected / error) | n-a | **`focus-visible` is the state AI-generated sites most often omit, and its absence is a WCAG 2.4.7 failure** |
| Full 22-state coverage checklist (adds focus-within, read-only, checked, indeterminate, expanded, current-page, visited, warning, success, dragging, drop-target, empty, skeleton) | n-a | The state layer supplies the VALUES (4 opacities); this supplies the COVERAGE. Missing states are the most common completeness failure in generated systems |
| Data state set (empty / loading / partial / error / success) | n-a | Required for every list, grid, table and chart |
| Chart data states (+ single-data-point) | n-a | Charts fail more often in these states than in the happy path |
| Responsive breakpoint set (320 / 390 / 768 / 1280 / 1440) | n-a | **The enforcement mechanism for D2** |
| Theme state set (light / dark / forced-colors) | n-a | Low-contrast dark mode is an enumerated AI-slop tell |
| **High-contrast state (`prefers-contrast: more`)** — *added in this revision* | n-a | **§7.2 generates a third colour solve at an elevated contrast multiplier, and before this row nothing ever rendered, captured or verified it.** A generated-but-never-viewed scheme is worse than none, because §13's proof tables would report the direction as compliant while no human or gate had ever seen that scheme. Render condition: **spot-checked, not swept** — 2 captures per selected variant (390 and 1280, light-source scheme), plus the full §13.4 gate-7 contrast sweep run against the elevated solve |
| **Text-spacing override state (WCAG 1.4.12, Level AA)** — *added in this revision* | n-a | Line-height 1.5×, paragraph spacing 2×, letter-spacing 0.12em, word-spacing 0.16em applied as a user stylesheet. §13.4 gate 10 already tests it at page level; this row makes it a **component-level** coverage state, because fluid type, computed `size.control-heights` and drag-positioned blocks are all clipping candidates and the page-level gate only catches the ones that happen to be on the page at LOCK. Render condition: **spot-checked** — 2 captures (320 and 1280) |
| **Pointer / hover capability state (`hover: hover` / `hover: none` + `pointer: coarse`)** — *added in this revision* | n-a | Every hover-triggered row in §8 (Tooltip, Popover, Hover card, Dropdown/flyout, Mega menu — 28 variants between them), the custom cursor and the §9.3 hover micro-reactions render differently or must not render at all under a coarse pointer. Without this state nothing ever proves the touch path exists. Render condition: **spot-checked** — 1 capture at 390 with `hover: none, pointer: coarse` emulated, plus a keyboard/tap interaction check for each hover-triggered family |
| Motion state set (full / prefers-reduced-motion) | n-a | The reduced render must **differ** where motion exists AND still look designed |
| RTL / bidi state | n-a | Only if multi-language, but then it must be built with logical properties from the start |
| Long-content / pseudolocalisation (+35% string expansion) | n-a | The cheapest way to catch fragile-layout defects that QA on ideal copy never sees |
| 200% zoom reflow (WCAG 1.4.10) | n-a | Level AA, and a common failure for fluid type scales — which is exactly what Utopia generates |
| Print state | n-a | The alternative is a page that prints unusably on legal and pricing pages |
| No-JS / progressive enhancement | n-a | **Also the crawler's view, so SEO depends on it** — and reveal-on-enter animations are the classic way an AI-built page ships invisible content to a no-JS client |
| State transition map | n-a | Derived. **The instant list matters: focus rings must appear instantly; animating a focus ring is an accessibility defect** |

#### Render-cost arithmetic (corrected and disambiguated)

The previous single line — *"True render cost per selected variant: ~20 captures (5 breakpoints × 2 themes × 2 motion)"* — was read by a later auditor as applying to every **generated** variant, which would put v1 QA at ~11,000 captures. It does not, and the ambiguity was the defect. There are **two** budgets and they are different by an order of magnitude:

| Budget | Formula | v1 figure | Notes |
|---|---|---|---|
| **Generation-time thumbnails** — one per generated variant, per theme, at 200×120 for the component bar | `variants × 2` | **1,348 renders** (674 v1 variants × 2) | Cheap, headless, cached per direction. §17-R29's lazy generation means only opened families are paid for |
| **Generation-time differentiation comparisons** — the §8.5 indistinguishability rule, run pairwise inside each component | `Σ n(n−1)/2` per component | **2,784 comparisons** | Pure image math on thumbnails already rendered above; no extra renders |
| **Lock-time verification captures** — per **selected** variant actually placed on the page | `20 swept + up to 10 conditional` | **≤30 per placed variant** | Swept: 5 breakpoints × 2 themes × 2 motion = 20. Conditional spot-checks added by this revision: high-contrast 2, text-spacing 2, coarse-pointer 1; already present: forced-colors 1, RTL 2 (multi-language only), print 1, no-JS 1, 200% zoom 1 |

**Open question O31 (new): how many distinct selected variants does a real v1 page carry?** The lock-time figure cannot be turned into a total until that number exists, and it depends on the page template. **No known mitigation beyond measuring it on the first real build — do not put a total in §13's budget until it is measured.** [I — inference; the per-variant figures above are arithmetic, the page total is not yet knowable.]

Budget for both, and gate the lock-time set at LOCK, not during editing.

### 8.4 The v1 cut list — **generated from the Priority column, not hand-written**

The previous v1 list was written by hand and drifted from the table it claimed to summarise. It omitted four components that the table itself marks **v1** — **Dropdown / flyout menu (7)**, **Radio group (8)**, **Toggle switch (8)** and **Platform CTA badge registry (5)** — which would have shipped a form system with no radio group and no toggle switch, and a commerce CTA with no badge registry. Its stated totals ("~50 pickable items, ~430 generated variants") were also below what its own named entries summed to.

**The fix is procedural, not editorial: §8.4 is regenerated from the Priority column on every PRD build.** If a row's Priority cell says v1, it is in this list; there is no second place to edit.

**Arithmetic, shown.**

| Family | Pickable v1 items | v1 variants | v1 items |
|---|---|---|---|
| **Navigation** | 6 | 43 | Top ribbon / primary navigation 10; Nav scroll behaviour 6; Dropdown / flyout menu 7; Mobile drawer / full-screen overlay menu 10; Skip link 2; Tabs / in-page switcher 8 |
| **Hero** | 3 | 28 | Marketing hero 12; Interior page header 8; Hero CTA cluster 8 |
| **Content** | 18 | 151 | Section header block 10; Feature grid 12; Feature split (alternating) 8; Bento grid 6; Generic content card 12; Card grid / collection layout 8; Rich text / prose body 6; Content + media section 8; Process / how-it-works steps 8; Stat band 8; Pull quote 8; FAQ / accordion 8; Section divider / seam 10; Section wrapper 8; CTA band 12; Newsletter block 6; Footer 10; Legal / policy body 3 |
| **Social proof** | 3 | 24 | Logo wall 8; Logo marquee 6; Testimonial card 10 |
| **Commerce** | 4 | 31 | Pricing section 12; Plan card 10; Pricing period toggle 4; **Platform CTA badge registry 5** |
| **Form** | 17 | 122 | Primary button 10; Secondary button 10; Ghost / tertiary button 8; Icon button 8; Inline text link 10; Text input 10; Textarea 5; Select 6; Checkbox 8; **Radio group 8**; **Toggle switch 8**; Field group (label / help / error) 6; Form layout 6; Inline email capture 6; Contact form 6; **Form error summary 4**; Consent checkbox 3; *plus two n-a policy rows: Required/optional indicator policy, `autocomplete` field-purpose mapping* |
| **Feedback** | 6 | 46 | Inline alert 6; Modal dialog 8; Tooltip 6; Spinner / loader 8; Cookie / consent banner 6; Badge / tag / pill 12 |
| **Media** | 5 | 76 | Image figure / frame 10; Icon set 20; Decorative spot-graphic set 20; Pattern / texture library 20; Logo lockup set 6 |
| **Utility** | 4 | 14 | Motion toggle 3; **Auto-motion pause/stop control 3**; Social links row 5; OG / social share card template 3; *plus four non-pick rows: Layout container widths (derived), Editor grid overlay (n/a), **Pointer / hover capability policy (n/a)**, Favicon / app-icon set (n/a)* |
| **Page templates** | 4 | 18 | Home / landing 6; Pricing 4; Legal 2; 404 6 |
| **§8.3 subtotal** | **70** | **553** | 76 rows including 6 `computed`/`n-a` rows |
| **§9 motion and art containers (v1 rows in §9.2 + §9.3)** | **17** | **121** | Still container 4; generic CSS/GSAP container 8; background layer 10; marquee container 6; reveal-on-enter 8; cursor-effect layer 5; hover micro-reactions 10; hero entrance 8; section reveal 10; text reveal 10; scroll reveal 6; marquee 6; loading states 6; custom cursor 10; background ambient motion 8; signature moment 2 (concept candidates, not a swap catalogue); smooth-scroll 4 |
| **v1 TOTAL** | **87 pickable items** | **674 variants** | |

`70 + 17 = 87`. `553 + 121 = 674`.

**Everything else is v2/v3:** 93 rows / 508 variants at v2 and 47 rows / 167 variants at v3 in §8.3, plus §9's v2/v3 rows. **Sixty-two items are app-shell, commerce, or exotic-chart and generate only when the interview's site-type answer requires them** (§17-R35).

> **⚠ REQUIRES USER SIGN-OFF — v1 scope correction.**
> The mechanically-generated v1 set is **87 pickable items / 674 variants**. The figure §18's phasing and §13's render budget were built on was **"~50 items / ~430 variants"**. That is a **~74% increase in items and ~57% in variants** — it is a real scope change, not a re-count of the same thing, and it arrives from three sources: (a) four v1-priority components the hand-written list simply missed; (b) §9's 17 v1 motion/art items, which the old list named inline but never counted; (c) three components/policies added by this revision (Form error summary, Auto-motion pause/stop control, plus four non-pick policy rows).
> **Three options, and this is the user's call, not the PRD's:**
> 1. **Accept 87/674 as v1** and re-baseline §18's phase sizing and §13's budget against it.
> 2. **Demote specific rows to v2** — each demotion must be made in the Priority cell with a stated reason, and §8.4 then regenerates itself. The four previously-missing items are the obvious candidates *except* Radio group and Toggle switch, which cannot be demoted without shipping an incomplete form system.
> 3. **Split v1 into v1a/v1b** inside the same Priority column.
> **No option is chosen here.** Until one is, §18 and §13 are sized against a number this section does not support.

### 8.5 Component-bar presentation rules

Choice overload is **not** automatic. Chernev, Böckenholt & Goodman (2015, *Journal of Consumer Psychology* 25:333–358) meta-analysed 99 observations (N=7,202) and found the mean effect of assortment size **not reliably different from zero** — it appears only under four moderators: set complexity, task difficulty, preference uncertainty, and decision goal. **[V]** Every one is engineerable away — **and, as of this revision, each engineering fix is defined precisely enough to build and to test**, which §20.2 #2 records as the condition the whole 10-variant decision rests on:

| Moderator | Engineering fix | How it is measured |
|---|---|---|
| Preference uncertainty | Render variants **in the real page slot at real scale**, with the current copy and neighbours | Binary: the strip renders in-slot or it does not |
| Set complexity | Sort by **structural distance** from the current pick (§8.5.1); **label the differing axis** (§8.6 supplies the axis names); skeleton filter chips at and above 12 items | Distance is a computed integer; the label is the argmax axis. Both are assertable in a unit test |
| Task difficulty | Pre-select the direction's canonical variant; Esc reverts in one key | Binary |
| Decision goal | Not-choosing is free and costless | Binary |

**Under those conditions 10 is safe.** The failure case is real when variants are undifferentiated — Iyengar & Lepper (2000): 24 jams attracted 60% of passers but converted 3%; 6 jams attracted 40% and converted 30%, with higher post-choice satisfaction **[V]**. The mitigation is not fewer options but **more different** options.

#### 8.5.1 Structural distance — defined

Previously "structural distance" was named as the mitigation for the set-complexity moderator and never defined, which made both the sort order and the "label the differing axis" caption unbuildable. It is now a function of the variant axis vector declared in §8.6.

Given two variants `a`, `b` of the same component with axis vector `A = [a₁…aₖ]`:

```
distance(a, b) = Σᵢ wᵢ · dᵢ(aᵢ, bᵢ)

  dᵢ = 0 or 1                      for a NOMINAL axis (media-side, framing, …)
  dᵢ = |rank(aᵢ) − rank(bᵢ)| / (levelsᵢ − 1)   for an ORDINAL axis (density, column-count, …)
  wᵢ = the axis's declared weight, default 1
```

- **Sort order:** the current pick is pinned first; the remainder ascend by distance, so the strip reads left-to-right as "nearly this" → "nothing like this". Ties break by generation index for determinism (§17-R15 requires the strip order to be reproducible).
- **"Label the differing axis":** the caption under each thumbnail names the axis with the largest `wᵢ · dᵢ` contribution, rendered as `axis: value` (e.g. `media: left` / `density: airy`). When two axes tie, both are shown. **This is why §8.6 exists** — without a declared axis vector there is nothing to name.
- **Filter chips** are generated from the axis vector as well: one chip group per axis whose values vary across the set. This is what makes the 20-item artwork tier legal (§17-R34) rather than a wall of thumbnails.

#### 8.5.2 "Indistinguishable at 200×120px" — defined

The hard rule stood as *"if two variants are indistinguishable at 200×120px, one must be regenerated or deleted"* with no metric, no threshold, no judge, and no stated render conditions — so the failure mode the section itself identifies (§17-R33, the jam study) had no enforceable gate. It is now a two-stage check, run **at generation time** (proposed gate 34 below), and deliberately **deterministic**: §20.1 excludes the VLM aesthetic judge, so no model opinion is in this loop.

**Stage 1 — structural (free, exact, runs first).** If two variants of the same component have **identical axis vectors** (§8.6), they are by definition not structurally distinct (§8.1) and one is deleted before rendering. This alone catches the common generator failure of emitting the same composition twice with different copy.

**Stage 2 — perceptual (runs on the pairs that survive stage 1).** Render both thumbnails at exactly **200×120 CSS px, at 2× device pixel ratio, in the light and dark schemes, at the 1280 breakpoint, with identical placeholder copy and identical placeholder imagery** (holding copy and image constant is what makes the comparison about structure rather than content). A pair is **flagged** when, in **both** schemes:

- **SSIM ≥ T_ssim** on the greyscale thumbnails, **and**
- **mean CIEDE2000 ΔE00 ≤ T_colour** across the thumbnail.

**Seed values: `T_ssim = 0.98`, `T_colour = 2.0`. [I — inference, not a validated threshold.]** The ΔE00 side has a conventional anchor (ΔE00 ≈ 1.0 is the commonly cited just-noticeable-difference for a trained observer under controlled viewing, and 2.0 is a conventional "close match" tolerance); **the SSIM figure has no source and is an engineering guess.** Both must be calibrated against a real generated set before the rule can be called enforced — **new open question O32.** Until calibration, the check runs in **advisory** mode (it flags, it does not delete) and the flag is shown in the component bar as a "these two are near-identical" affordance, which is honest and still better than the previous unenforceable prose.

**Judge:** the metric flags; **regeneration is automatic, deletion is not.** A flagged pair triggers one regeneration attempt of the later-indexed variant with a forced axis change (the generator is given the pair's axis vector and told which axis to move). If the regenerated variant flags again, the variant is **dropped from the set and the set ships short** with the shortfall recorded in the direction's provenance record — a set of 9 differentiated variants is worth more than 10 with a twin, and the recorded shortfall is what stops the "cannot drift" claim from quietly becoming false.

#### 8.5.3 Presentation by set size

Hick's law is the **wrong** model for a thumbnail grid and must not be used to justify small sets. Hick–Hyman is robust for random serial search; a grid of visually distinct rendered thumbnails supports **parallel feature-based visual search** — "the one with the image on the left" is found in parallel. A feature-sorted 10-thumbnail grid scans near-constant-time; a 10-item unordered text dropdown does not. **The component bar must be visual and feature-sorted, never a text dropdown. [V — visual-search literature; IxDF on Hick–Hyman limits]**

The previous presentation spec covered only the 10-variant case, leaving the six 12-variant Tier A components sitting exactly on the filter-chip boundary, the four 20-item artwork sets (plus §7.9's 20-piece background/hero artwork) with no spec at all, and the post-append state of "More like this" undefined. The ladder:

| Set size | Presentation | Filter chips | Notes |
|---|---|---|---|
| **2–10** (Tier B, Tier A at 10) | **Strip** — 5 thumbnails visible, arrow/scroll to reach the rest | No | The original spec, unchanged |
| **11–14** (the six Tier A 12s; also a 10-set after one "More like this" append) | **Two-row strip** — 6 visible per row, 12 visible without scrolling | **Yes, from 12** — the boundary is resolved as *chips appear at ≥12*, so all six Tier A 12-variant components get them | Chips are generated from the varying axes (§8.5.1) |
| **15–25** (a 20-set after one append; a 12-set after two) | **Filtered grid**, not a strip — 4 columns × as many rows as needed, scrolls within the panel | Yes | The strip metaphor breaks here; converting to a grid is a mode change the panel makes automatically and announces ("showing 20 of 20") |
| **20** (Tier C artwork: icon sets, illustration sets, spot graphics, patterns, §7.9 artwork) | **Filtered grid from the start** — never a strip. §8.3 #Media already describes artwork as "parallel-scannable as a filtered grid"; this makes it the specified behaviour rather than an aside | **Yes, mandatory** — per §17-R34, *filters are what make 20 legal* | Chips for artwork come from the artwork tags (direction tag per D1, plus subject, technique, density). Hover preview still renders in the real slot |
| **>25** | Not reachable by design | — | See the append cap below |

**Append behaviour ("More like this").** Generates 5 neighbours of the selected variant — neighbours meaning *small* structural distance (one axis moved), which is what "like this" means once §8.5.1 exists — and appends them. Appended items are visually separated by a divider labelled "new", are sorted by distance from the seed, and are subject to the same §8.5.2 differentiation check against the whole existing set, not just against each other. The panel converts strip → grid automatically when the count crosses 15.

**Append cap: a set may not exceed 25 items. [I — inference; the number is an engineering choice, not a researched threshold. Requires user decision if it proves wrong in use.]** At the cap, "More like this" is replaced by "Replace the 5 lowest-distance items" — because the failure being avoided is a set that grows toward the mean, which is exactly the jam-study condition the section exists to prevent.

**Unchanged from the original spec:** hover previews live in the slot, click commits, Esc reverts, the current variant is pinned first and pre-selected, **"Compare 3"** opens a full-width triptych (3 is the number for deliberate comparison — matching the existing `acos-design-variants` skill precedent).

### 8.6 The variant axis schema (new in this revision)

§8.5's sort order, its axis captions, its filter chips and its stage-1 differentiation check all require something the PRD never specified: **a declared, enumerated set of axes per component.** Without it, "structural distance" and "label the differing axis" are prose. With it, both are arithmetic.

**Contract.** Every `pick` row in §8.3 and §9 declares 3–7 axes. Each axis has a name, a type (`nominal` | `ordinal`), an enumerated value list, and an optional weight. The vector is emitted with the variant, stored in the design-system artifact, and is what the editor sorts, filters, captions and dedupes on. **A variant with no axis vector cannot enter the component bar** — this is the mechanical enforcement of §8.1's definition.

**Worked examples** (illustrative; the full per-component schema is a build artifact, not PRD prose):

| Component | Axes |
|---|---|
| Marketing hero (12) | `media-position` {none, left, right, background, below, split} · `column-count` {1,2} *(ordinal)* · `alignment` {left, centre} · `density` {compact, regular, airy} *(ordinal)* · `framing` {flat, framed, bleed} · `cta-arrangement` {inline, stacked, single} |
| Generic content card (12) | `media-position` {none, top, left, background} · `elevation` {flat, bordered, shadowed, layered} *(ordinal)* · `meta-placement` {none, top, bottom, overlay} · `aspect` {from the §7.4 ratio set} · `hover-treatment` {none, lift, reveal, zoom} |
| Primary button (10) | `fill` {solid, gradient, tinted, glass} · `edge` {sharp, soft, pill} *(ordinal)* · `border` {none, hairline, heavy} *(ordinal)* · `motion` {none, lift, sweep, morph} · `icon-slot` — **not an axis: computed per §8.1** |
| Section divider / seam (10) | `geometry` {rule, shape, wave, angle, notch, overlap} · `weight` {hairline, medium, heavy} *(ordinal)* · `bleed` {inset, full} · `texture` {none, grain, pattern} |
| Icon set (20, Tier C) | `stroke-style` {line, solid, duotone, hand} · `corner` {sharp, rounded} · `grid` {16, 20, 24} *(ordinal)* · `weight` {light, regular, bold} *(ordinal)* — *set-level axes, shared by every icon in the set* |

**Open question O33 (new): who writes the axis schema?** Three candidates — (a) hand-authored once per component family in the skill (~90 pickable families at v1, so a real one-time cost); (b) generated by claude.ai as part of the Step-2 design-system prompt, which risks drift between directions and would break cross-direction comparison; (c) inferred post-hoc from the generated variants, which is the least reliable and cannot enforce stage-1 dedupe because the inference would just describe whatever was produced. **The PRD's inference is (a), because determinism matters more here than effort (§17-R15) — but this is a real effort line that §18 does not currently carry, and it requires user decision.**

### 8.7 Accessibility contracts carried by this inventory (new in this revision)

Four WCAG criteria are load-bearing for components specified in §8 and were named nowhere. Each is stated here with the components it binds and the gate that proves it. **Gate numbers continue §13.4's existing sequence (which ends at 28); these are proposed additions to that checklist, not a renumbering of it.**

| Id | Criterion | Binds | Proposed gate |
|---|---|---|---|
| **A1** | **WCAG 2.2 SC 1.4.13 Content on Hover or Focus (Level AA)** — content that appears on hover or focus must be **dismissable** (without moving the pointer), **hoverable** (the pointer can move into it without it vanishing), and **persistent** (until dismissed, invalid, or no longer relevant) | Tooltip 6, Popover 5, Hover card 4, Dropdown/flyout 7, Mega menu 6 — **28 variants**; plus every Icon button, which is specified as always pairing with a tooltip | **Gate 29 (proposed, lock-time):** for every hover/focus overlay family, a Playwright assertion that Escape dismisses without pointer movement, that the pointer can traverse trigger → overlay without dismissal, and that no timed auto-dismiss fires while hovered. **Direct manipulation makes this worse, not better**: a user can drag a tooltip-bearing control against a viewport edge, and the resulting flip/reposition is exactly where dismissability and hoverability break — so the assertion runs against the *edited* layout, not a canonical one |
| **A2** | **WCAG 2.2.2 Pause, Stop, Hide (Level A)** — auto-moving, blinking or scrolling content lasting **more than 5 seconds** and presented in parallel with other content must have a mechanism to pause, stop or hide it | Background video loop 5 (a 4–16s loop is squarely inside the criterion), Animated counter's scroll-linked variant, auto-advancing Testimonial carousel, §9's Marquee/ticker 6 and Background ambient motion 8. **Discharged by the new Auto-motion pause/stop control (§8.3 #Utility)** | **Gate 30 (proposed, lock-time):** enumerate every element on the page registered with the `motion.auto-started` primitive and assert each has a reachable, visible, ≥24×24px, ≥3:1-contrast pause control. **`prefers-reduced-motion` does not discharge 2.2.2** — it is an OS preference, not a mechanism on the page — and the site-wide motion toggle only discharges it for users who find it |
| **A3** | **WCAG 2.2 SC 1.3.5 Identify Input Purpose (Level AA)** — inputs collecting information about the user must expose the purpose programmatically | Every field in Contact form 6, Inline email capture 6, Newsletter block 6, Checkout, Booking. Before this revision `autocomplete` appeared **once** in the whole section (`one-time-code` on the OTP row) | **Gate 32 (proposed, lock-time):** every `input`/`select`/`textarea` whose name matches the WCAG input-purpose list carries the correct `autocomplete` token, with a declared exception list (site search is the documented exception). Backed by the new `autocomplete` field-purpose mapping row |
| **A4** | **WCAG 1.1.1 Non-text Content (Level A)** — charts are non-text content by definition | The 12 chart marks + Sparkline 4 + Chart chrome kit 4, and any Step-6 custom chart. **The user named graphs and charts explicitly (vision step 6)** | **Gate 31 (proposed, lock-time):** every chart in the exported static site has an accessible name, a description or visually-hidden data table, and no colour-only distinction. **Must be emitted at build time**, because §17-O14 puts v1 charts on a build-time SVG path — a client-side alternative would not exist in the exported site at all |

Two further gates fall out of the states added above and the rule defined in §8.5.2:

| Id | What | Proposed gate |
|---|---|---|
| **A5** | The `prefers-contrast: more` third solve from §7.2 is rendered and contrast-swept, not merely generated | **Gate 33 (proposed, lock-time):** run the §13.4 gate-7 contrast sweep a second time against the elevated solve; fail on the same thresholds |
| **A6** | Variant differentiation (§8.5.2) | **Gate 34 (proposed — generation-time, NOT lock-time).** It runs when variants are emitted, not at LOCK, because a twin variant is a generation defect and LOCK is far too late to fix it. Advisory until O32 calibrates the thresholds |

**Not closed here.** WCAG 2.2 SC 2.5.7 Dragging Movements is already gated (§13.4 gate 9) and 1.4.12 Text Spacing at page level (gate 10); this section adds the component-level coverage state for 1.4.12 but does **not** add a second gate for it.

### 8.8 What this section asks of other sections

| Id | Ask | Of |
|---|---|---|
| **X1** | Add two `n/a` token items: **`interaction.pointer-capability-policy`** (hover/pointer media-query rules and the required touch equivalent for every hover-only affordance) and **`interaction.autocomplete-map`** (the WCAG 1.3.5 field-purpose token table). §8 now carries policy rows for both, but the token-side homes belong in §7.4 | §7 |
| **X2** | Add proposed gates **29–34** to the §13.4 ordered checklist (29 hover-overlay 1.4.13; 30 auto-motion 2.2.2 coverage; 31 chart non-text alternative; 32 `autocomplete` audit; 33 high-contrast solve sweep; 34 variant differentiation, generation-time). Numbering continues §13.4's existing 1–28 — **no existing gate is renumbered** | §13 |
| **X3** | Re-baseline phase sizing against **87 v1 items / 674 v1 variants**, or record the demotions that reduce it (see the sign-off note in §8.4) | §18 |
| **X4** | Record new risks **R46** (the axis schema is an unbudgeted one-time authoring cost that §8.5, §8.6 and the differentiation gate all depend on), **R47** (the §8.5.2 thresholds are uncalibrated, so the differentiation rule ships advisory-only at first and §17-R33's jam-study failure is only partly mitigated until O32 closes), and **R48** (four v1-priority components were missing from a hand-written summary for an entire PRD cycle without anyone noticing — the class of defect, not the instance, is what R48 records: any hand-maintained restatement of a machine-checkable table will drift again) | §17 |
| **X5** | Record new open questions **O31** (distinct selected variants per real page — needed before the lock-time capture total is knowable), **O32** (calibrate `T_ssim` / `T_colour`), and **O33** (who authors the variant axis schema) | §17.4 |

---
## 9. Motion and art containers (per D4)

**D4 is settled: motion is an ordinary design-system item, and animated pieces live in the same draggable containers as artwork.** No parallel motion subsystem. The editor manipulates an animated container exactly as it manipulates an art container.

*Revision note (this pass): the earlier draft of this section left the swappable "motion variant" unit undefined, understated the container-kind count, left the video/sprite asset-supply decision unresolved, and understated the touch/keyboard story for hover- and cursor-driven items. All four are closed below. Nothing in D1–D4 or in the settled 8-step vision is reopened.*

### 9.1 The container contract (one contract, both kinds)

Every art/motion container implements:

```
{
  boxSizing, aspectPolicy (from the named ratio set), anchor, overflow, mask,
  schemeAware: bool, motionCapable: bool, reducedMotionPoster,
  reducedMotionVariantRef,               // NEW — see rule 4 below
  focalPoint: {x, y}, altText | decorative: true, licenseRef,
  trigger, viewportThreshold,            // NEW — both now typed, see rule 3
  source: {                              // NEW — see rule 5
    kind: 'raster' | 'vector-lottie' | 'vector-rive' | 'video'
        | 'sprite-sequence' | 'svg' | 'canvas-program' | 'none',
    ref,          // asset id — MUST resolve against assets/manifest.json
    poster        // asset id, optional — distinct from reducedMotionPoster
  },
  playback: {                            // NEW — see rule 6
    autoplay: bool, muted: bool, loop: bool,
    iterationCount: number | 'infinite'
  },
  costClass: 'free' | 'cheap' | 'heavy' | 'gpu',   // NEW — see rule 7
  tokenRefs[]
}
```

Seven rules make this work:

1. **Explicit `aspect-ratio` (or min-block-size from the ratio scale) is mandatory**, so the grid row is reserved before the asset or animation initialises. Otherwise entrance animations and late-loading media produce layout shift, which the CLS gate catches too late.
2. **Animation may only touch `transform`, `opacity`, `filter`** inside the container. It may **never** change the container's grid placement, width, or height. This makes the editor's handling of a WebGL canvas byte-identical to its handling of a JPEG — which is exactly what D4 asks for.
3. **Trigger + viewport-threshold fields, not container TYPE, determine which animation kind a container performs.** `trigger` is a closed enum — **`page-load`, `viewport-enter`, `viewport-scrub`, `pointerenter`, `click`, `always`** — no other value is legal. `viewportThreshold` is a fraction in `[0, 1]`, meaningful only for `viewport-enter` (default **0.2**, i.e. the "~20%" figure used elsewhere in this section is now the stated default, not a stray prose number) and ignored for every other trigger. `viewport-scrub` does not use a single threshold at all — its progress is driven by the pinned/scrubbed sequence's own scroll-range mechanism, defined in §9.4. `page-load`, `click`, and `always` fire without a threshold. The same generic container becomes a hero entrance (trigger: `page-load`), a scroll reveal (trigger: `viewport-enter` at its threshold), or a hover micro-reaction (trigger: `pointerenter`). This is why the container inventory is small and the animation-kind inventory is where the variants live.
4. **`reducedMotionVariantRef` is mandatory whenever `motionCapable: true`.** It is a node/asset id pointing at the tagged reduced-motion treatment in the catalogue — this is the field §10.6's v1 check ("confirm the placed item's catalog includes a tagged reduced variant") actually reads. `reducedMotionPoster` remains a separate, narrower field: a still frame shown only for `source.kind` values that have no meaningful reduced-motion *animation* at all (e.g. a video-loop reduced to a poster frame). A container may carry either or both, but `motionCapable: true` without `reducedMotionVariantRef` fails validation.
5. **`source` is what the generator validates against the asset allowlist.** Every reference resolves against `assets/manifest.json` (§12.2); a container with no distinct asset of its own — e.g. a CSS/GSAP-driven DOM container animating existing child content rather than an image or file — sets `source.kind: 'none'` and omits `ref`. This is also the field the §9.5 asset-supply decision below is written against.
6. **`playback` governs autoplaying/looping media.** `muted` **must** be `true` whenever `source.kind: 'video'` and `autoplay: true` — "muted is browser law, not style" (unchanged from the original text, now enforced as a field-level constraint rather than a prose aside). `iterationCount` is `'infinite'` for true loops and a finite number for anything that plays out and stops (e.g. a hero entrance).
7. **`costClass` is what §9.5's concurrency caps are computed against.** It is assigned per container *kind* in §9.2's new Axis/Cost column, not authored per instance — an instance inherits its kind's class. `gpu`-class containers (Canvas/WebGL, Particle/ambient) are the ones the "max 1 WebGL slot, max 1 particle layer" caps in §9.5 enforce; `heavy`-class containers (video-loop, sprite/frame-sequence, pinned/scrubbed) are what the "max 2 autoplay video loops, max 2–3 pinned sequences" caps enforce.

#### 9.1.1 The motion-variant model — what the component bar actually swaps *(new — closes a blocking gap)*

The layout-node example in §12.3 shows two independent fields on an `ArtContainer` node: `variant` (e.g. `"background-scene@07"`) and `props.motion` (e.g. `"entrance.mask-wipe@03"`). Neither §9.2 nor §9.3, as originally written, stated which of these each section's variant *count* populates, or what the component bar shows. This subsection is the missing definition.

**The rule:**

- **`variant` always selects the container's structural/rendering implementation** — the §9.2 count for that container kind. This is "how the container is built and skinned," and it is present on every container, motion-capable or not.
- **`props.motion`, present only when `motionCapable: true`, selects the choreography/behaviour** — a token of the form `<kind>.<slug>@<version>` drawn from a §9.3 animation kind. Combined with `trigger` (§9.1 rule 3), it determines what plays and when.

**Not every container kind needs both fields independently.** Cross-checking §9.2's per-kind counts against §9.3's per-kind counts surfaces two genuinely different situations, and the original draft did not distinguish them. Every row in the revised §9.2 table now carries an explicit **Axis type**:

| Axis type | Meaning | Component bar behaviour |
|---|---|---|
| **Dual** | `variant` (structural skin) and `props.motion` (behaviour, drawn from one or more compatible §9.3 kinds) are genuinely independent choices that compose | Two tabs: **Style** (lists the §9.2 count) and **Motion** (lists the compatible §9.3 kind(s)' variants). Selecting in one tab never changes the other. |
| **Single** | The container kind's own §9.2 variant list *is* its complete motion catalogue — there is no separate `props.motion` token, or the token namespace is identical to `variant` | One tab: **Style**, labelled as such but understood to set both look and behaviour together, since they were never separable for this kind. |
| **Static** | The container kind is not independently motion-capable (a purely mechanical substrate, or house-curated content that defines its own motion internally) | One tab: **Style**. No **Motion** tab is shown; `motionCapable` defaults to `false` for these unless the hosted content declares otherwise (e.g. Sticky/pin hosting a Sticky/pinned-scroll-sequence timeline authored on a *child* node). |

**Do the §9.2 and §9.3 counts multiply? — answered explicitly, per axis type:**

- **For Dual-axis kinds, yes, in *state-space* terms only.** The number of *reachable look+behaviour combinations* for one container instance is `(§9.2 count) × (sum of variants across its compatible §9.3 kinds)`. This is **never** rendered as one flattened cross-product list in the UI (an 8-structural × 47-eligible-motion container would be a 376-row list, which is unusable) — the bar always presents Style and Motion as two separate, tabbed pickers, and the user makes two independent choices that compose.
- **For Single-axis kinds, no.** Picking the container's one `variant` fully determines both look and behaviour; there is nothing to multiply against.
- **For Static kinds, the question does not apply.**

**Per-kind disposition** (feeds the Axis-type column added to §9.2's table):

| Container kind | Axis type | `props.motion`-eligible §9.3 kind(s) | Reconciliation note |
|---|---|---|---|
| Still-image container | Dual | Hero entrance, Reveal-on-enter (via Section reveal choreography / Scroll reveal), Parallax | `variant` = contain/cover/bleed/masked crop treatment (the only row in §9.2 whose names were already given). `motionCapable` defaults `false` — a still image is not required to move. |
| CSS/GSAP-driven DOM container (generic) | Dual | Hero entrance, Section reveal choreography, Text reveal/kinetics, Scroll reveal, Hover micro-reactions, Loading states, Background ambient motion, Page transitions, Signature moment | Highest-reuse container; its 8 structural variants are generic wrapper shapes, not enumerated by name in this pass (they are derived per direction, not fixed catalogue names — stating specific names here would be fabrication). |
| Decorative background layer | Dual | Background ambient motion, Parallax, Hero entrance (as backdrop), Reveal-on-enter | Tier A, user-named. |
| Marquee / ticker | Single | — (identical list) | The container's 6 structural variants (constant, pause-on-hover, speed-on-scroll, reverse-on-scroll, dual-counter-row, tilted) **are** the "Marquee" animation kind's 6 variants in §9.3, restated once per table for readability. This is the earlier draft's clearest accidental double-count; there is exactly one list of 6, not two lists of 6. |
| Reveal-on-enter | Dual (tightly coupled) | Section reveal choreography, Scroll reveal | `variant` picks the base reveal treatment (fade, rise, mask-wipe, clip-expand, scale, blur-in, stagger-children, split-line); `props.motion` (when set to a Section-reveal-choreography or Scroll-reveal token) picks the ORDER/timing multiple reveal-on-enter instances play in relative to each other. The two are coupled — a choreography token is meaningless without at least one placed reveal-on-enter instance to sequence. |
| Global cursor-effect layer | Dual, AND-composed | Custom cursor (exclusively) | **[I — new synthesis, not independently confirmed]** The 5 structural variants are rendering *mechanisms* (e.g. dot-follow / outline-follow / blend-mode / trail / magnetic-snap — mechanism names are inferred, not sourced); the 10 Custom-cursor variants in §9.3 are behaviour *presets* layered on the chosen mechanism. Both fields are required together when `motionCapable: true`; this is the one kind where Style and Motion are non-optional together rather than independently optional. |
| Animated sprite / frame-sequence | Single | — | `variant` (autoplay-loop / play-on-enter / scroll-scrubbed) fully determines playback. **Asset-supply gap — see §9.5, decided below.** |
| Video-loop container | Single | — | `variant` (autoplay-loop / play-on-enter / hover-play) fully determines playback. Muted is enforced via `playback.muted` (§9.1 rule 6). **Asset-supply gap — decided below.** |
| Vector animation (dotLottie / Rive) | Single | — | `variant` (loop / play-on-enter / interactive-state-machine). When the state-machine variant is chosen, its input trigger may itself resemble a hover micro-reaction, but that binding is authored *inside* the Lottie/Rive file, not exposed as a separate `props.motion` token. |
| Scroll-driven pinned/scrubbed sequence | Single | — (matches "Sticky/pinned scroll sequence" 1:1, 4=4) | See §9.4 for the resimulation rule governing re-anchoring. |
| SVG shape / mask container | Dual | Reveal-on-enter (mask/clip variants), Text reveal/kinetics (path-warp) | `variant` = clip/mask/overlay/seam structural treatment. |
| Canvas / WebGL slot | Single | — | House-curated per the original note; the WebGL program itself defines its motion, so there is no separate catalogue to swap. |
| Particle / ambient canvas layer | Single | — | Same reasoning as Canvas/WebGL; its 5 variants **are** its motion presets. |
| Kinetic type container | Single, with an open mapping question | — | **OPEN QUESTION — no known mitigation in this pass.** The container's 8 named variants (per-char stagger, mask-wipe, variable-axis, path-warp, marquee-type, scramble, 3D-extrude, cursor-repel) plainly overlap with the "Text reveal / kinetics" animation kind's separately-counted 10 variants in §9.3, but no source material establishes whether the kind-level 10 is a superset, a recombination, or an independent list. This requires a build-time reconciliation pass before the component bar can be implemented for this kind; recorded here rather than silently resolved. |
| Cursor-reactive container | Single, with a partial-overlap open question | — | **OPEN QUESTION — no known mitigation in this pass.** Its 5 variants (parallax, tilt, magnetic, spotlight, distortion) partially overlap named entries in Hover micro-reactions ("magnetic," "tilt-3d," "cursor-glow"); the overlap is not reconciled by the source material. |
| Sticky / pin container | Static | Sticky/pinned scroll sequence (hosted, on a child node) | Purely mechanical substrate — matches its original note unchanged. |

This table is additive to, not a replacement for, §9.2's own table below, which now carries the Axis-type column inline for at-a-glance reference.

### 9.2 Container kinds — 16 structural types

*(Corrected: the earlier heading said "11 structural types" while its own table listed 16 rows, with no note explaining the discrepancy. There is no v1-only subset that totals 11 either — the accurate split by Priority is **6 v1 / 8 v2 / 2 v3 = 16**. The heading now matches the table it introduces.)*

| Container | Structural variants | Priority | Axis type | Cost class | Notes |
|---|---|---|---|---|---|
| Still-image container | **4** | v1 | Dual | free | contain, cover, bleed, masked. Visual identity lives in the Image Figure component that skins it |
| CSS/GSAP-driven DOM container (generic) | **8** | v1 | Dual | cheap | The highest-reuse container; hosts most animation kinds interchangeably, so it needs the widest generic preset bank |
| Decorative background layer | **10** | v1 | Dual | cheap (heavy if its Background-ambient-motion `props.motion` selects a particle sub-variant — see §9.3's note) | **Tier A, user-named.** Covers the largest pixel area of any component; still or animated in the same slot per D4 |
| Marquee / ticker | **6** | v1 | Single | cheap | constant, pause-on-hover, speed-on-scroll, reverse-on-scroll, dual-counter-row, tilted. **WCAG 2.2.2 pause/hide is mandatory**; `pause-on-hover`'s touch counterpart is a visible tap-to-pause control (§9.3.1) |
| Reveal-on-enter | **8** | v1 | Dual (coupled) | cheap | fade, rise, mask-wipe, clip-expand, scale, blur-in, stagger-children, split-line. **The most-used motion primitive on the whole site** |
| Global cursor-effect layer | **5** | v1 | Dual, AND-composed | cheap | A page-level singleton, not per-instance. Desktop-only; **must disable on coarse pointers** — see §9.3.1 for the required non-cursor touch signature |
| Animated sprite / frame-sequence | **3** | v2 | Single | heavy | autoplay-loop, play-on-enter, scroll-scrubbed. **Asset-supply gap — DECIDED, see §9.5** |
| Video-loop container | **3** | v2 | Single | heavy | autoplay-loop, play-on-enter, hover-play. Muted is browser law, not style. **Asset-supply gap — DECIDED, see §9.5** |
| Vector animation (dotLottie / Rive) | **3** | v2 | Single | cheap (dotLottie) / heavy (Rive, per §9.5's payload note) | loop, play-on-enter, interactive/state-machine |
| Scroll-driven pinned/scrubbed sequence | **4** | v2 | Single | heavy | element-enters-view, element-pins, container-scroll, whole-page. **The one drag-fragile container — see §9.4** |
| SVG shape / mask container | **4** | v2 | Dual | cheap | clip, mask, overlay, seam |
| Canvas / WebGL slot | **3** | v3 | Single | gpu | inline, section-background, full-viewport-fixed. **House-curated, not model-improvised** |
| Particle / ambient canvas layer | **5** | v3 | Single | gpu | **Only ONE such layer should ever run per page** — continuous main-thread + GPU cost stacks additively |
| Kinetic type container | **8** | v2 | Single (open mapping question, §9.1.1) | cheap | per-char stagger, mask-wipe, variable-axis, path-warp, marquee-type, scramble, 3D-extrude, cursor-repel. **Must declare that accessible text remains in the DOM unsplit** |
| Cursor-reactive container | **5** | v2 | Single (open overlap question, §9.1.1) | cheap | parallax, tilt, magnetic, spotlight, distortion. All five no-op on touch and under reduced-motion — see §9.3.1 for the required substitute |
| Sticky / pin container | **4** | v2 | Static | free | Purely mechanical substrate |

**Cost-class ↔ concurrency-cap linkage (new, closes a §9.5 traceability gap):** the `gpu` row above (Canvas/WebGL, Particle/ambient) is exactly what §9.5's "max 1 WebGL slot, max 1 particle layer" caps enforce; the `heavy` row (sprite, video-loop, pinned/scrubbed, Rive-mode vector) is exactly what "max 2 autoplay video loops, max 2–3 pinned sequences" enforces. A page-level validator sums `costClass` across placed instances and blocks placement past the cap rather than warning after the fact.

### 9.3 Animation kinds — where the variants live

| Kind | Variants | Priority | Touch/keyboard equivalent | Rationale |
|---|---|---|---|---|
| Hover micro-reactions | **10** | v1 | **See §9.3.1 — per-variant table, not "n/a."** | **The highest-FREQUENCY animation kind** — fires hundreds of times per session. lift+shadow, magnetic, underline-draw, fill-sweep, icon-morph, scale-pulse, border-trace, colour-shift, tilt-3d, cursor-glow. Each cheap to build and verify. **Must have a touch equivalent** — a hover-only affordance is a usability defect, not a stylistic choice |
| Hero entrance | **8** | v1 | n/a — `page-load` trigger, device-independent | The most-seen single moment per visit. fade-up, split-text, staggered cascade, mask-wipe, scale-in, parallax-layered, clip-path, typewriter |
| Section reveal choreography | **10** | v1 | n/a — `viewport-enter` trigger, device-independent | **Tier A.** Choreography — the ORDER things arrive in — is what separates directed motion from every-element-fades-up, the single most recognisable AI-generated motion signature |
| Text reveal / kinetics | **10** | v1 | n/a | Tier A. GSAP SplitText became free April 2025 with AI-generated code explicitly permitted, so this is buildable without licence risk. **All 10 must preserve a single accessible text node**. See §9.1.1's open mapping question against the Kinetic type container's 8 |
| Scroll reveal | **6** offered / **1–2** deployed | v1 | n/a | **Catalogue breadth ≠ deployment restraint.** Mixing multiple reveal styles on one page reads as inconsistent — itself an anti-slop tell. The editor flags 3+ distinct reveals as a soft warning |
| Marquee | **6** | v1 | Tap-to-pause control for the `pause-on-hover` variant — WCAG 2.2.2 | Cheap (pure CSS transform loop), commonly reused. **Same 6-item list as the Marquee/ticker container's structural variants — see §9.1.1, this is one catalogue, not two** |
| Loading states | **6** | v1 | n/a | skeleton shimmer, brand-mark pulse, progress bar, custom spinner, placeholder-fade, staged-reveal. **Over-designing fights the purpose** |
| Custom cursor | **10** | v1 | **Disabled entirely on coarse pointers (unchanged) — see §9.3.1 for the required non-cursor touch signature** | Tier A, user-named. Untitled UI ships cursors as a foundation component, confirming they belong in a design system |
| Background ambient motion | **8** | v1 | n/a | User-named. Mirrors the decorative background layer's presets; the heaviest sub-variant (particle field) is v3-gated and inherits `costClass: gpu` when selected |
| Parallax | **5** | v2 | n/a (device-independent trigger; vestibular concern is independent of input device) | Accessibility- and performance-sensitive, so below the 10 default. **35.4% of adults 40+ have vestibular dysfunction** |
| Sticky/pinned scroll sequence | **4** | v2 | n/a — native touch scroll drives the same pin mechanism as wheel scroll | Each architecturally distinct and expensive to verify |
| Page transitions | **6** | v2 | n/a | Feasibility-grounded, architecture-dependent |
| Signature moment | **1 concept per direction (10 total) at Step 2, refined into 2–3 candidate treatments of that single concept for the shortlisted direction only, at Step 4** | v1 | Case-by-case — no default; whatever the chosen concept renders on touch must be specified with it | **NOT a swap catalogue.** Award-tier winners have exactly one, and treating identity-carrying choices as generic catalogue picks is the root mechanism of homogenisation. Handled under Step 6's custom-component allowance. **A lint flags a second one.** *(Reconciled count — see note below.)* |
| Smooth-scroll behaviour | **4** | v1 | n/a — Lenis wraps touch scroll the same as wheel scroll | native, lightly damped, Lenis-wrapped, per-section snap. Lenis wraps native scroll so accessibility survives; **ScrollSmoother is anti-recommended** because it restructures the DOM |
| Parallax depth rules | **5** | v2 | n/a | Picked once and applied everywhere, or layers fight each other |

**Signature-moment count, reconciled *(closes a minor gap)*:** §7's design-system inventory prices `direction.signature-moment` at **10**, "one per direction." This row originally said "2–3 concept candidates" with no stated relationship to that 10. Both are correct at different pipeline stages, restated as one sentence: **Stage A (Step 2) generates one signature-moment concept per direction — 10 total, matching §7's count exactly. Stage B (Step 4) takes only the shortlisted direction's one concept and produces 2–3 candidate treatments of it for the user to choose among.** §7 should be edited to quote this same sentence rather than restating "10" without the two-stage context — **cross-section fix required in §7, not made in this pass**, since this pass is scoped to §9.

#### 9.3.1 Touch and hover-parity requirements *(new subsection — closes a major gap)*

The original text asserted hover micro-reactions "must have a touch equivalent" and that the cursor-effect layer and cursor-reactive containers disable on touch, without defining any of the equivalents or gating them. Two user-named, Tier-A items (custom cursor, hover set) are affected. This subsection makes the requirement checkable.

**Per-variant touch/focus equivalents for the 10 Hover micro-reactions:**

| Hover micro-reaction | Touch/keyboard equivalent |
|---|---|
| lift+shadow | Same treatment retriggered on `:active` (press) plus `:focus-visible` ring for keyboard |
| magnetic | **No direct touch equivalent** — magnetic pull requires continuous pointer position with no touch analogue. Substitute: a brief `:active` scale-down "press" cue, plus `:focus-visible` ring |
| underline-draw | Same draw animation retriggered by `:active`/tap instead of `pointerenter` |
| fill-sweep | Same sweep retriggered on `:active`/tap |
| icon-morph | Same morph retriggered on `:active`/tap |
| scale-pulse | Same pulse retriggered on `:active`/tap |
| border-trace | Same trace retriggered on `:active`/tap |
| colour-shift | Same shift retriggered on `:active`/tap; persists under `:focus-visible` for keyboard users |
| tilt-3d | **No direct touch equivalent.** Substitute: a flat `:active` scale-down cue |
| cursor-glow | Touch **does** have a tap coordinate, so this one has a real equivalent: a radial `:active` flash centred on the touch point, fading over ~200ms |

**Custom cursor / Global cursor-effect layer (touch = fully disabled, unchanged):** because the entire item is desktop-decoration by construction, the direction must nominate a **non-cursor touch signature** so identity isn't solely desktop-borne — recommended default: reuse the direction's `signature-moment` treatment, or retarget one Tier-A hover-set entry to `:active`, as the thing that carries identity on touch. **This pairing is not yet recorded anywhere** — it requires either a new §5 interview question ("what should mobile visitors see in place of the custom cursor?") or a §7 direction-spec field; **cross-section addition required, not made in this pass.**

**Cursor-reactive container (all 5 variants no-op on touch, unchanged):** substitute is the container's base static or reduced-motion pose; the same non-cursor touch signature above is what carries identity in its place.

**Lint 9.T1 (hover-parity, new local id — first use in this document, continue this numbering if more section-9-local checks are added):** every interactive element carrying a hover treatment must also declare a `:focus-visible` treatment and a `:active` treatment (from the table above, or an author override). Elements failing this check are flagged the same way the existing "3+ distinct reveals" soft warning is flagged in the Scroll-reveal row. **[I — general WCAG hover/focus-content awareness informs this row; not independently re-verified against exact Success Criterion text in this pass, so no specific SC number is cited as fact.]**

### 9.4 The pinned/scrubbed exception (important)

Most containers re-target cleanly under drag because their trigger is viewport-intersection-based and their transform origin is relative to their own bounding box. **A scroll-driven pinned/scrubbed sequence is different**: its timeline is a function of absolute scroll distance travelled while pinned, which depends on its position in document flow and the room its parent has to scroll through. Dragging it into a narrow column or a section with different surrounding height silently breaks the composition — pin without room to scroll, or a scrub that completes too fast.

**Rule:** the D2 free-position escape hatch is **disabled by default** for this container kind. It is restricted to anchor reordering (move between sections), and forcing free-position requires an explicit confirmation. Re-anchoring triggers a scroll-length resimulation before the preview is shown accurate.

**What "resimulation" computes *(newly specified — closes a major gap)*:** on any re-anchor (move between sections, or a breakpoint change), the editor:

1. Recomputes the parent's total scrollable height contributed by the sibling sections between the pin's start position and its natural release point, at the current breakpoint.
2. Requires **`pinDuration ≤ availableScroll(breakpoint) × k`**, where `pinDuration` is the scroll distance the sequence's timeline is authored to consume, and `k` is a buffer factor. **`k`'s recommended default is 0.9** — leaving a 10% margin against sub-pixel rounding and dynamic content reflow — but this is a tuning choice made in this pass, not a cited standard; treat it as adjustable, not fixed. **[I]**
3. On failure, the editor **rejects the drop** with a named reason (`insufficient-scroll-room:<nodeId>@<breakpoint>`) and offers a one-click **"extend section to fit"** remediation, which pads the target section's `min-block-size` by the shortfall rather than silently truncating or stretching the animation timeline. This is a decision made in this pass to resolve the previously-unstated failure behaviour (the alternatives — silently shorten the timeline, or warn-and-proceed — were rejected because a pin-without-room failure is otherwise invisible until LOCK, which is exactly the "plays wrong, does not error" failure mode this exception exists to prevent).

**New lock-time gate (extends §13's gate list):** **Gate — pinned-sequence scroll-room.** At LOCK, assert the inequality in step 2 holds for every pinned/scrubbed node at all three reference breakpoints used elsewhere in this PRD — **390 / 768 / 1280** (matching §11.4's free-position gate level of detail). Any violation blocks LOCK with the same named reason as the drop-time check, so a sequence that passed at drop time but was later invalidated by an unrelated edit to a sibling section's height cannot ship silently.

### 9.5 Format and platform rules

| Decision | Rule | Evidence |
|---|---|---|
| Vector animation format | **dotLottie by default** (60KB runtime, ZIP-compressed JSON). **Rive only when a state machine or input-reactive behaviour is required** (200KB WASM runtime, but 50–80% smaller payloads). Threshold: >6 vector animations OR any state-machine requirement ⇒ Rive. **Neither runtime loads for a hover effect** — CSS/GSAP covers micro-interactions | **[V — rive.app blog, unicornicons, pkgpulse 2026; medium confidence on exact figures]** |
| Scroll-driven animation | **Native CSS `animation-timeline: scroll()/view()` as the primary path** (zero main-thread JS — directly serves the finding that main-thread work is the real performance axis), **GSAP ScrollTrigger as the `@supports`-not fallback**. Chrome/Edge 115+, Safari 18+, Firefox behind a flag; ~84% global as of mid-2026, Baseline-blocked pending Firefox. **The fallback must be real and tested, not assumed** | **[V — MDN, web-features-explorer, caniuse]** |
| Page transitions | **CSS `::view-transition-group/-old/-new` choreographies**, progressive-enhancement-safe by construction. Same-document VT is Baseline Newly Available (Chrome 111+, Firefox 133+, Safari 18+); **cross-document ships in Chrome 126+ and Safari 18.2+ but is still absent in Firefox as of mid-2026** — degrade to instant navigation, never a JS router hack that breaks the back button | **[V]** |
| Motion lint | UI interactions ≤300ms, never >500ms (Primer's shipped rule). Compositor-only properties (`transform`/`opacity`/`filter`); animating `width`/`height`/`top`/`left`/`margin` forces layout+paint every frame | **[V — primer motion.json5]** |
| Concurrency caps | Max 1 WebGL slot, max 1 particle/ambient layer, max 2 autoplay video loops, max 2–3 pinned sequences per page. Unlimited transform/opacity-only CSS reveals. **Enforced via the `costClass` field added to the container contract in §9.1 — `gpu` caps the first two, `heavy` caps the latter two** | **[I]** |
| Asset-supply gap | **DECIDED — v1 scope cut, requires explicit user sign-off (see below). This deviates from the breadth the user asked for at Step 2 and is flagged as such, not silently applied.** | **[V — the generation-surface limitation]** |

**Asset-supply decision, resolved *(closes a major gap — the earlier draft posed the question and deferred it to §17-R1 without answering it):**

Video-loop and animated sprite/frame-sequence containers **ship as fully-implemented containers that the generator never fills with a fabricated asset.** Concretely:

- The container kind, its `variant` list (autoplay-loop / play-on-enter / hover-play or scroll-scrubbed), its `trigger`/`playback` fields, and its editor UI are all in scope for v2 as already priced in §9.2.
- **The claude.ai design-system generation leg (Step 2/3) cannot produce the underlying footage, video file, or frame sequence itself** — this is a hard limitation of the generation surface, not a build-effort choice.
- The user must either **supply their own asset** (validated against `assets/manifest.json` exactly like any other asset, per §9.1 rule 5), or leave containers of these kinds unplaced.
- **Routing to an external stock-footage/photo-sequence provider with its own licence-manifest chain is explicitly OUT OF SCOPE for v1.** Building that integration is a separate, larger scope item (a third-party licence chain feeding the Step-8 evidence bundle) and is not undertaken here.
- **Requires a new §5 interview question** ("Do you have existing brand video footage or photo sequences you want animated on the site?"), so the gap is surfaced to the user at Step 1 rather than discovered when a container comes up empty at Step 4 — **cross-section addition required in §5, not made in this pass.**

**Requires user sign-off — naming the deviation:** the user's Step-2 vision named "an animation for the front" among other examples and explicitly said the examples were illustrative, not exhaustive; if the user's intended hero treatment is video-based, this decision means the design-system generation step cannot produce it for them, and they must supply the footage themselves or accept a non-video hero. This is a real scope narrowing relative to the breadth the user asked for, and is called out here for explicit confirmation rather than assumed.

### 9.6 The motion-editing contradiction (stated plainly, mitigated partially)

A draggable container must be measurable. `getBoundingClientRect()` on a GSAP-transformed element returns the **animated** position, not the layout position, so drag maths is wrong mid-tween. Lenis lerps `scrollTop` every frame, so scroll measurement is unreliable while it runs. Every real implementation therefore disables animation in edit mode — which is also what the prior report's capture protocol mandates for screenshots.

**Consequence:** the user arranges an animated hero with all motion frozen, locks, sees the real motion for the first time, finds it wrong, unlocks, and the motion turns off again. **They cannot debug the thing they are trying to fix, in the tool built to fix it.**

**Partial mitigations (a mode toggle, not a fix) — re-prioritised in this pass:**

- **PREVIEW MOTION — moved to v1 priority** *(closes a major gap: the original draft left all three mitigations at v2/§18 while placing eight v1 motion kinds — marquee, reveal-on-enter, hero entrance, hover micro-reactions, custom cursor, background ambient motion, smooth scroll, section reveal choreography — into the editor with no way to see any of them move. §9.6's own claim that the contradiction is "mitigated partially" was not true under that phasing; it is the cheapest of the three mitigations to build (re-enable Lenis/ScrollTrigger/tweens, disable all editing — no new measurement code) and belongs with the v1 motion kinds it exists to debug).* Re-enables Lenis + ScrollTrigger + all tweens and **disables all editing**. The page becomes the locked site in place, one keypress away. **This priority change requires a matching edit in §10.8 and §18, where "Motion preview toggle" currently sits at v2 — not made in this pass, since this pass is scoped to §9, but flagged as a required follow-up so the three sections don't disagree.**
- **Per-container scrub slider** setting the tween to normalised progress 0→1, so start/mid/end poses are visible statically. **Remains v2.**
- **Trigger-point markers** rendered in the overlay showing where the scroll trigger fires. **Remains v2.**

**Open question, explicitly unresolved (unchanged from the prior draft, restated so it isn't lost): does §10.8's v1 "In-editor Preview mode" play motion, or freeze it like edit mode?** No source material in this section answers this — it is a decision that belongs in §10.8, not fabricated here. **Requires a decision in §10.8.**

**There is no known mitigation for judging motion FEEL while editing.** The prior report's Data Gap 2 states motion verification is unvalidated end-to-end anywhere in the industry; the human-in-the-loop design does not change that, it moves the unsolved problem from an AI judge to a human who also has to be in preview mode to see it. This is stated in §17 as a risk with no mitigation.

### 9.7 Cross-check against §8's v1 motion component list *(new — closes a major gap)*

§8 line 319 enumerates a v1 component set that includes: *"still container + background layer + marquee + reveal container + section reveal + text reveal + hover set + custom cursor + smooth scroll + reduced-motion + easing matrix; motion toggle."* This was never mapped onto §9.2/§9.3's ids, so the two inventories were not provably the same set. Row-by-row:

| §8 v1 term | §9.2/§9.3 id | Status |
|---|---|---|
| still container | §9.2 Still-image container | Matched |
| background layer | §9.2 Decorative background layer | Matched |
| marquee | §9.2 Marquee/ticker container **and** §9.3 Marquee animation kind | Matched — confirmed as one 6-item list (§9.1.1) |
| reveal container | §9.2 Reveal-on-enter | Matched |
| section reveal | §9.3 Section reveal choreography | Matched |
| text reveal | §9.3 Text reveal / kinetics | Matched |
| hover set | §9.3 Hover micro-reactions | Matched |
| custom cursor | §9.2 Global cursor-effect layer **and** §9.3 Custom cursor | Matched — AND-composed per §9.1.1 |
| smooth scroll | §9.3 Smooth-scroll behaviour | Matched |
| reduced-motion | §9.1's `reducedMotionPoster` / `reducedMotionVariantRef` fields | Matched, but **cross-cutting, not a container or kind** — it is a field on every motion-capable container, not a separate inventory row. No fix needed, noted for completeness. |
| easing matrix | **Not found in §9.2 or §9.3.** | **OPEN QUESTION — no known mitigation in this pass.** An easing matrix (which easing curve pairs with which trigger/kind) reads as a design-token artifact — most likely it belongs beside the direction's other derived-value scales in §7, not as a container or animation kind here. This section does not have the authority to place it; recorded as unresolved and requiring a decision in §7 or a new token-inventory section. |
| motion toggle | **Not found in §9.2 or §9.3.** | **OPEN QUESTION — no known mitigation in this pass.** Distinct from "reduced-motion" above (which is a per-container field); "motion toggle" reads as a site-facing, visitor-usable control (e.g. a persistent on/off switch overriding `prefers-reduced-motion`), which would be a published-site UI component, not an editor container. Not specified anywhere located in this pass. Requires a decision in §8 or §10 as to whether this is a real v1 deliverable or a mis-transcribed duplicate of "reduced-motion." |

Fourteen of §8's sixteen v1 motion terms are now traceably matched to a §9.2/§9.3 id. The remaining two ("easing matrix," "motion toggle") are real gaps in the inventory, not naming mismatches, and are left open rather than silently assigned a home that isn't backed by this section's source material.

---
## 10. Step 4 — the editor: full feature set

Grouped by function. **One Priority column, and it is now derived mechanically from §18** (see §10.10 for the method and the full count reconciliation) — the pre-reconciliation draft's priority tags disagreed with §18's phase plan on roughly a seventh of the rows, and §18 is the phase plan actually used to scope and staff a build, so §18 wins every disagreement. Every row whose priority changed as a result carries an inline **"Reconciled with §18"** tag naming the old value; rows with no tag were already consistent and are unchanged.

Mechanical recount of the pre-reconciliation draft (before this revision touched it): **113 rows, 71 v1 / 37 v2 / 5 v3.** The draft's own prose claimed "~35 of ~95 items are v1" — off by roughly 2× on the v1 count and ~19% on the total. This revision does not delete or shorten any pre-existing row; it corrects priorities in place and **adds 3 new rows** where a gap could only be closed by splitting a feature into a v1-scoped slice and a v2/v3 full slice (§10.1 per-breakpoint override, §10.3 custom-component insertion, §10.3 chart data). That brings the table to **116 rows**. Under the §18-reconciled priorities: **56 v1 / 55 v2 / 5 v3** — see §10.10 for the per-subsection breakdown and for every row whose priority moved.

Canva — explicitly built for non-designers — ships by default only canvas + snap, layers, undo, basic text/image editing, one-click template swap, and a share link. Grids, rulers, breakpoint cascades, version diffing and comment pins are hidden or absent. **[U — product knowledge, treat as inference]** Under the reconciled v1 scope this comparison reads differently than in the pre-reconciliation draft: v1 here has **no canvas drag, no gridlines, no snapping at all** (§18's explicit v1 cut) — which is *more* restrained than Canva's snap-enabled canvas, not less. The v1/v2 split in this table should be read as "editor-lite first, canvas second," matching §18's own framing, not as "everything in one release."

### 10.1 Layout & placement

**Breakpoint sets used throughout this section** (adopted from §11's own revision, not re-derived here, so the two sections state one set instead of two): **authoring breakpoints 390 / 768 / 1280 / full**, with pinned device heights 390×844 / 768×1024 / 1280×800 whenever the page contains a `vh`/`svh`/`dvh` rule (§11.7); **verification/detection breakpoints 320 / 390 / 768 / 1280 / 1440** (§11.8, §10.8 below); **free-position auto-demotion at ≤390px** (§11.4 rule 4, revised down from the pre-reconciliation draft's 479px, which no switcher, iframe, or gate in the product ever actually renders). §10.8's Hard LOCK gate additionally renders 1440 (§11.4 rule 6: "render at 390/768/1440"). **Open item, no known mitigation beyond what's stated here:** 1440 is checked by the Hard LOCK gate and by the Responsive preflight report (§10.8) but is **not** one of the switcher's own preview options below, so a user cannot live-preview a 1440-only failure while editing — they discover it only via the preflight report or at LOCK itself. Adding 1440 as a fifth switcher option is a plausible fix but is not decided here; **requires user decision.**

| Feature | Priority | Notes |
|---|---|---|
| Real-grid overlay (gridlines) | v2 **(Reconciled with §18 — was v1)** | **Drawn by reading `getComputedStyle(section).gridTemplateColumns`** and painting those exact resolved tracks. Never decorative — it is the snap target, and it lives in the out-of-iframe overlay so it disappears at lock by construction. §18's v1 scope cut states "No canvas drag. No gridlines, no snapping, no free-position, no zoom/pan" outright; §18's v2 scope-in restates it as "the real-grid canvas: gridline overlay read from `getComputedStyle`" |
| Snap engine | v2 **(Reconciled with §18 — was v1)** | Two 1-D interval indexes per section over four prioritised target classes: grid lines > sibling edges/centres > section padding & content rails > spacing-scale increments. Tolerance 6–8 CSS px **divided by zoom** — a classic regression if missed. Moves with the grid overlay per §18's v1 cut |
| Smart alignment guides + distance labels | v2 **(Reconciled with §18 — was v1)** | Dashed guides + live gap measurements in the accent colour; equal-spacing indicators when 3+ siblings match. §18 v2 scope-in names this explicitly: "smart guides with distance labels" |
| Align tools | v2 **(Reconciled with §18 — was v1)** | left/centre/right/top/middle/bottom, relative to siblings or parent. Bundled with Distribute tools (already v2) under §18 v2's "multi-select + align/distribute" |
| Distribute tools | v2 | Equalise gaps across 3+ selections, operating on **grid integers**, not pixels. Unchanged — already consistent with §18 |
| Padding / gap drag handles | v2 **(Reconciled with §18 — was v1)** | Draggable inner edges snapping to **discrete spacing-scale steps only**, showing the token name (`space-6`), never a raw pixel value. **This is the mechanic that stops direct manipulation destroying the token system** — no commercial builder does it. §18 v2 scope-in names it explicitly: "padding/gap handles snapping to the spacing scale" |
| Drag-to-place (grid write) | v2 **(Reconciled with §18 — was v1)** | Ghost preview follows the pointer continuously; commit writes `{col, colSpan, row, rowSpan}` integers for the active breakpoint (per §11.2.1's drop algorithm, once §11's revision ships). Pointer capture on the overlay so the drag survives leaving the iframe. §18 v2 scope-in: "drag-to-place writing grid integers." **v1 has no canvas drag at all**, so v1 layout changes go through §10.2's Navigator tree and this table's Anchor/pin control only |
| Span resize | v2 **(Reconciled with §18 — was v1)** | Edge handles change span in whole cells with a live "6 of 12 · 50%" readout so the user learns the fluid consequence. §18 v2 scope-in: "span resize with the … readout" |
| Section reorder | v1 | Vertical only, via the Navigator or a section rail. Sections are never dragged horizontally. Confirmed v1 by §18's Editor-lite scope-in: "section reorder" |
| Breakpoint switcher | v1 **[I — not itemised by name in §18; kept v1 by inference]** | 390 / 768 / 1280 / full, with **pinned device heights** (390×844, 768×1024, 1280×800) whenever the page contains any vh/svh/dvh rule. §18 does not name a "breakpoint switcher" in either its v1 or v2 lists. Kept v1 on the reasoning that it is a plain iframe resize (no dependency on the real-grid canvas, snap engine, or per-breakpoint override authoring, all of which are v2), and v1 needs *some* way to view the auto-derived 768/390 renders before running the Responsive preflight report (also v1) or acting on one of its findings. This is an inference, not a §18 citation — **flagged for confirmation when §18 is next updated** |
| Per-breakpoint override — scoped exception only, preflight-triggered | v1 **(new row, added to close a gap)** | The one authoring path §18's v1 cut explicitly leaves open: "override only where preflight complains." When the Responsive preflight report (v1, §10.8) flags a specific node at a specific breakpoint, the editor offers a single scoped fix limited to that node/breakpoint pair — not the general cascade UI below. No dot indicator, no "reset to inherited" browsing UI; this is a narrow, gated escape valve, not authoring |
| Per-breakpoint override + reset-to-inherited (full cascade UI) | v2 **(Reconciled with §18 — was v1; split into the scoped-exception row above)** | Desktop-down cascade with sparse overrides, browsable at any breakpoint. Every overridden property shows an "overridden here" dot and a one-click reset. §18's v1 cut: "No per-breakpoint override authoring (author at 1280, auto-derive 768 and 390, override only where preflight complains)" — the general browsing/authoring UI described here is exactly what that cut removes; the exception clause is the new row above |
| Anchor/pin control | v1 | The core D2 primitive. **Three verbs only**: align to (left/centre/right/stretch), space above/below (stepper over the scale), order (up/down among siblings). Confirmed v1 — this is the row §18's v1 scope cut is describing verbatim: "Layout is section reorder + anchor verbs only" |
| Free-position escape hatch | v2 | See §11.4 (as revised: anchor restricted to parent/grid-cell only in v1 scope, auto-demotes at ≤390px). Deliberately v2 so the safe path ships and is proven first. Unchanged — already consistent with §18's "free-position escape hatch as anchored-offset" v2 listing |
| Type-aware resize | v1 **[I — not itemised by name in §18; kept v1 by inference]** | Text reflows at fixed font size; images rescale aspect-locked; inline SVG rescales losslessly; tables scale uniformly with a separate per-column handle. **Reusable prior art from the ACOS HTML-to-PDF Visual Composer vision.** §18 doesn't name this row, but v1's own auto-derive behaviour ("author at 1280, auto-derive 768 and 390") has nothing else in this table governing how content *inside* a block reflows when that auto-derivation resizes it — without this row, v1's auto-derived breakpoints would have undefined content behaviour. Kept v1 on that basis; this is inference, not a §18 citation |
| Canvas zoom + pan | v2 | 25–200%, snap tolerance ÷ zoom, space-drag pan. Deferred because a fixed-viewport iframe is usable without it. Unchanged — already consistent with §18 |
| Drag-resizable canvas frame | v2 | Stress-test reflow at in-between widths (catches breakage at, say, 610px). Unchanged — already consistent with §18 |
| Rulers | v2 | Unchanged — already consistent with §18 |
| Custom drag-out guides | v2 | **Stored as fractions of the content-width rail, not pixels**, so they survive breakpoint switches. Unchanged — already consistent with §18's "fraction-stored guides" |
| Flex/grid container controls | v2 | Direction, gap, wrap, justify/align as icons and steppers, never raw CSS. Unchanged — not named individually by §18 but bundled with the rest of the v2 canvas surface it depends on |
| Keyboard nudge & grid stepping | v2 **(Reconciled with §18 — was v1)** | Arrow = one cell, Shift+arrow = span ±1, Tab walks siblings. §18 v2 scope-in names this explicitly: "keyboard nudge and grid stepping." **This is also the WCAG 2.5.7 single-pointer alternative for drag (§13.2)** — moving it to v2 alongside the canvas drag it is the alternative *for* is actually self-consistent: v1 has no canvas drag at all (anchor verbs are click/stepper-based and need no pointer alternative), so the alternative isn't needed until the drag mechanism it substitutes for ships. **Verify §13.2's gate wording doesn't assume this alternative exists in v1** before v1 ships — that check is outside this section's authority |

### 10.2 Structure & selection

| Feature | Priority | Notes |
|---|---|---|
| Selection overlay + handles | v1 | Drawn **outside the iframe** with `pointer-events: none`, so no editor node ever enters the exported DOM |
| Drill-in / drill-out selection | v1 | Click = nearest top-level block; Enter/double-click descends; Esc ascends. Hit-test via `elementFromPoint` inside the iframe, walking up to the nearest `[data-wb-node]`. **Known edge: `elementsFromPoint` does not return the iframe when something is fullscreened over it — never fullscreen the canvas while editing** |
| Breadcrumb ancestor bar | v2 **(Reconciled with §18 — was v1)** | Ancestor chain under the canvas, selected element rightmost, every entry clickable. §18 v2 scope-in names "breadcrumb navigation" alongside command palette, find/search, rename, group/ungroup — none of which are in v1's Editor-lite list |
| Navigator / layers tree | v1 | **Non-optional.** Canvas clicking provably cannot reach zero-height wrappers, covered elements, `pointer-events: none` decoration, or empty slots. Webflow ships all three selection channels for exactly this reason. A full-bleed background art container will otherwise swallow every click. Confirmed v1 — §18's Editor-lite scope-in names "navigator tree" explicitly |
| Drag-to-reorder / reparent in tree | v2 **[I — not itemised by name in §18; demoted by inference]** | The only reliable way to fix z-order or nesting without canvas gymnastics. §18's v1 cut is "no canvas drag," and while this is tree-UI drag rather than canvas drag, **v1's actual reorder need is already covered by the Section reorder row (§10.1, v1, "via the Navigator or a section rail")** — that only requires list-reorder-by-button/drag within the tree at the section level, not general arbitrary-node reparenting. Demoted the general case to v2; the section-level case remains v1 via the row above. This split is inference, not a §18 citation |
| Hide/show toggle per layer | v1 | Cheap, no canvas-drag dependency |
| Rename layer/component | v2 | Makes the tree navigable at 50+ elements. Unchanged — already consistent with §18's v2 "rename" |
| Multi-select | v2 **(Reconciled with §18 — was v1)** | Shift-click, marquee, select-all-of-type. §18's v1 cut states "no multi-select/align/distribute" outright; §18 v2 scope-in restates it as "multi-select + align/distribute" |
| Group / ungroup | v2 | Unchanged — already consistent with §18's v2 "group/ungroup" |
| Element lock | v1 | Prevents accidental move/resize/delete. **Must use a different verb from the site-wide LOCK** — "Lock Element" vs "Publish" / "Preview as Visitor". Two "lock" concepts sharing vocabulary is a real confusion risk |
| Duplicate with smart offset | v1 | |
| Cut/copy/paste incl. paste-to-replace | v1 | Clipboard round-trip as **`pages/<id>.doc.json`** fragments **[renamed — see §10.4's file-naming note]** **including all breakpoint overrides** |
| Delete with recovery bin | v1 | **Independent of the undo stack** — "I deleted this three edits ago" is common and chaining undo back would revert everything since |
| Global/shared component with instance overrides | v1 | **A prerequisite for safe variant swapping, not optional plumbing.** Without it, either every page-level edit drifts independently or every system-level edit needs manual re-application. Build this data model **before** the component-bar UI |
| Section boundary markers | v1 | Visible wrapper boundaries so "regenerate this section" has an unambiguous target. **Independently justified for v1 even though per-section regeneration itself is now v2** (§10.7): section boundaries are also what Section reorder (v1) and the Navigator tree (v1) need to show the user an unambiguous structure, so the row stays v1 on that separate basis. **A fuzzy boundary lets regeneration leak into neighbouring content** once regeneration does arrive in v2 |
| Per-breakpoint visibility | v2 **[I — not itemised by name in §18; demoted by inference]** | Compiled to a display rule, not duplicate markup. Lint warns if hidden at every breakpoint. §18's v1 cut is a blanket "no per-breakpoint override authoring," and a visibility toggle is a form of per-breakpoint override even though it's cheaper than the full cascade UI. Demoted to v2 on that basis; this is inference, not a §18 citation, and a case could be made for keeping a "hide on mobile" toggle in v1 as a low-cost exception similar to §10.1's scoped-override row — **not decided here, open for reconsideration** |

### 10.3 Content

**Sign-off note — Custom-component insertion and chart data, read before implementing either row below.** §18's v1 scope cut removes "custom-component insertion" entirely, and separately ships "Charts: build-time SVG only, ≤4 mark types" in v1. Taken literally, v1 renders charts nobody has any way to place, because placing a component the base direction doesn't already include is exactly what "custom-component insertion" means. Charts are also the user's own named example for Step 6 ("the user may add custom components not normally included — for example graphs or charts" — see the vision's Step 6). Shipping charts with no insertion path in v1 would silently cut a capability the user named. **This revision proposes closing that hole with a v1 slice narrower than the cut §18 states — see the two new/split rows below — and that narrowing is a deviation from §18's literal text that REQUIRES USER SIGN-OFF before implementation**, distinct from the ordinary priority reconciliations elsewhere in this section.

| Feature | Priority | Notes |
|---|---|---|
| Inline text editing (tier 1) | v1 | **`contenteditable="plaintext-only"`** on headings, eyebrows, buttons, nav items, labels, stat numbers — ~90% of a marketing page's text nodes. Strips all paste formatting, avoids cross-browser Enter-key markup divergence, and prevents Word markup entering an award-grade type system. Baseline newly-available **[V — web.dev, caniuse]** |
| Rich-text block (tier 2) | v2 | ProseMirror/TipTap (MIT) on **long-form prose blocks only**, restricted to an approved mark set (bold, italic, link, list, blockquote) — no font/colour/size controls. Unchanged — already consistent with §18's v2 "rich-text block" |
| Plain-text swap mode | v1 | Editing a token-bound label changes only the string, never the styling |
| Image replace | v1 | Keeps container size/crop/position intact. Confirmed by §18's Editor-lite scope-in: "image replace" |
| Image crop + focal-point picker | v1 | **A single draggable dot, not a crop rectangle.** A single 2D point degrades gracefully across every container aspect ratio a reflow system produces; per-breakpoint manual crops do not. **Direct prior art from the ACOS HTML-to-PDF Visual Composer vision.** Confirmed by §18's Editor-lite scope-in: "focal point" |
| Alt-text field | v1 | Required-nudged; placing any image opens a micro-field for alt text **or an explicit "decorative" toggle**. Blocks the placement, not just the lock. Confirmed by §18's Editor-lite scope-in: "alt gate" |
| Asset/media manager | v1 | Searchable library tagged by which direction each asset suits |
| Component-bar variant swap | v1 | Core Step-4d feature. See §8.5 for presentation rules and §10.8 for the coherence contract. Confirmed by §18's Editor-lite scope-in: "component-bar variant swap with hover-preview and typed slot contracts + content orphanage" |
| Variant hover-preview before commit | v1 | Ghost-previews live in the actual page context (current copy, current neighbours). **Essential, not nice, once there are 10 variants** — an isolated thumbnail can't show fit. Confirmed by §18 (bundled with the row above) |
| Icon picker | v2 | Unchanged |
| Embeddable content blocks | v2 | Video, maps, forms. Unchanged |
| Custom-component insertion — minimal whitelisted registry (table, chart, embed, form) | v1 **(new row — see the sign-off note above this table)** | Placement only, from a **fixed catalog of four component kinds sourced from the system library**, no arbitrary Step-6 code, no free-form "insert anything." This is the minimal path that lets a v1 site actually place the chart component the next row and §14.6 both assume exists. **Requires user sign-off** — see the note above the table |
| Custom-component insertion — full Step-6 authoring | v2 **(renamed from the original "Custom-component insertion" row; Reconciled with §18 — was v1, i.e. undifferentiated)** | Free-form addition of components not in the base registry, arbitrary Step-6 custom code, per-section notes-driven generation of new component types. §18's v1 cut ("no custom-component insertion") applies in full to this row; only the minimal registry row above is proposed as a v1 exception |
| Minimal chart-data field (CSV/table paste bound to a chart node's props) | v1 **(new row — see the sign-off note above this table)** | A single paste-a-table-of-numbers field wired directly to the chart component's data prop. Not a spreadsheet: no formulas, no multi-sheet, no cell formatting — just the minimum surface that lets a v1 SVG chart (§18: "build-time SVG only, ≤4 mark types") receive real data instead of shipping with placeholder numbers. **Requires user sign-off** — see the note above the table |
| Table/data editor for charts (full spreadsheet-grade) | v3 | Lightweight spreadsheet backing any chart. **Relationship to the row above:** this is the eventual replacement for the v1 paste field, not a second unrelated feature — the v1 field's data model should be a strict subset of this editor's, so upgrading doesn't require a migration |
| Link field with validation | v1 | href + URL validation + `target=_blank` toggle |
| Site-wide link manager | v2 | Every internal and external link with destination and status |
| Per-page SEO/meta fields | v1 | Title, description, OG image, favicon. Confirmed by §18's Editor-lite scope-in: "per-page SEO fields" |
| Multi-page manager | v1 | Add, duplicate, delete, reorder. Confirmed by §18's Editor-lite scope-in: "multi-page manager" |
| Site-wide global regions | v1 | Header/footer/nav edited once, reflected everywhere. Confirmed by §18's Editor-lite scope-in: "global regions" |

### 10.4 History & persistence

**File-naming note (applies to every row below and to §10.2's clipboard row above).** The pre-reconciliation draft referred to the persisted scene graph as `layout.json` throughout this subsection. §12.2's file set has no `layout.json` — the canonical scene graph is **`pages/<id>.doc.json`, one file per page** — and §12.13's write allowlist only permits writes to `pages/*.doc.json`, `history.jsonl`, and `.wb/**`. This revision renames every reference in this section to `pages/<id>.doc.json` to match §12.2/§12.13. **§4, §11, §12.6 and §12.10 still say `layout.json` as of this revision** (verified by grep at the time of writing) — those are outside this section's edit authority, so this is flagged here as a required follow-up rather than silently fixed everywhere. **Open question, no known mitigation beyond flagging it:** whether the command stack, op log, and editor lock below are scoped **per-page** (one stack per `doc.json`) or **site-wide** (one stack spanning all pages, keyed by page id) is not stated anywhere in §10 or §12 as of this revision. Since multi-page management is v1 scope (§10.3), "undo an edit on a page I've since navigated away from" is a real v1 scenario with no defined behaviour today. This revision's inference/recommendation (not yet ratified): **a single site-wide command stack keyed by page id**, so cross-page undo has an answer — but ratifying this requires a matching update to §12.9 (which currently describes `history.jsonl` without stating its scope) and is outside this section's authority to make binding.

| Feature | Priority | Notes |
|---|---|---|
| Undo / redo | v1 | **A single JSON-patch command stack** over **`pages/<id>.doc.json`** (renamed — see the file-naming note above), covering canvas drags, inspector edits and text edits alike, so the surfaces cannot desync. Split stacks are a classic confusing regression. Coalesces a continuous drag into one entry. **The client-side stack mirrors, rather than independently computes, the server-authoritative op log**: per §12.9 layer (a), `history.jsonl` holds the `patch`/`inverse` pair the server derives from each typed op, and undo/redo replays those, consistent with §12.13 rule 1 (the client never sends a raw patch, only a typed op) |
| Transactional grouping for multi-mutation actions | v1 | **A component swap or a section regeneration must be ONE undo step.** Naive per-mutation undo leaves a broken hybrid state after one Cmd+Z — a known failure class in AI-editing tools, and it fails exactly when the safety net matters most. **Needs dedicated test coverage** |
| Autosave | v1 **(mechanism rewritten — was described as a raw diff POST, which §12.13 forbids)** | Debounced ~300ms: the client flushes its **pending typed-op queue** to `POST /ops` (the same typed-op channel §12.13 specifies for every write — `{op: 'move-block', node: 'n_hero', …}`, never a raw path or a raw JSON Patch); the server validates each op against its schema and the component library, derives the RFC 6902 patch, applies it to `pages/<id>.doc.json` atomically (write-temp then `fs.rename`), and appends the op + patch + inverse to `history.jsonl`. **This is a deliberate change from the pre-reconciliation draft's "small JSON diff POSTed to the server," which is exactly the "raw-JSON-Patch-over-HTTP" pattern §12.13 rule 1 calls "nearly as dangerous as raw paths"** (an `add`/`replace` on an arbitrary pointer could rewrite `systemLock` or inject an `override` path). Never a base64 blob in localStorage either — the image-builder precedent's `toDataURL` autosave does not scale to a multi-page site |
| Named snapshots | v1 | Explicit "save as milestone" distinct from the autosave stream |
| Save-as-variation / branch | v1 | **The mechanism that makes Step 5 safe** — try a new direction without losing the current one |
| Automatic timestamped version history | v2 | Unchanged — already consistent with §18's v2 "version history: timeline" |
| Visual version diff | v2 | Side-by-side render with changed blocks highlighted, driven by a JSON diff. Unchanged — already consistent with §18's v2 "visual diff" |
| Non-destructive restore | v2 | Restoring creates a new version rather than overwriting the timeline, so restoring is itself undoable. Unchanged — already consistent with §18's v2 "non-destructive restore" |
| Explicit manual save affordance | v2 | For psychological closure even though autosave covers it technically |
| Per-section regeneration log | v2 | Which sections were regenerated, from what note, when. Unchanged — already consistent with §18's v2 "regeneration log," and moves together with §10.7's regeneration rows |
| Crash-recovery draft restore | v2 | Recover the most recent autosave, not the last named snapshot |

### 10.5 Navigation & wayfinding

| Feature | Priority | Notes |
|---|---|---|
| Page navigator | v1 | Thumbnail strip or list |
| Canvas ↔ tree selection sync | v1 | |
| Find/search | v2 | Cmd+F across layer names and text content. Unchanged — already consistent with §18's v2 "find/search" |
| In-edit-mode link-follow | v2 | Modifier+click a link to jump to that page for editing |
| Jump-to-section quick nav | v3 | Unchanged — already consistent with §18's v3 "jump-to-section nav" |

### 10.6 Quality (ambient, non-blocking during editing)

**Reconciliation note for the whole subsection.** §18's v1 scope-in names "Design Health HUD with the v1 live checks" without listing which checks those are, and §18's v2 scope-in separately names "Live a11y/contrast lint inline, motion-property lint, text-spacing stress clone, off-token advisory." Read together, the v1 HUD is fed by **cheap, structural, non-axe heuristics** (bounding-box checks, DOM-order walks, counters), and the v2 HUD gains the **engine-backed checks** (axe-core, the full contrast algorithm suite, motion-property static analysis, the text-spacing stress clone). That split is applied below. One row needed disambiguation rather than a straight move: "Reduced-motion sibling presence" (kept v1) checks that a placed animated `ArtContainer`'s catalog entry *includes* a tagged reduced-motion variant — a catalog-completeness check against v1's own component library, unrelated to "Motion-property lint" (v2), which statically analyses arbitrary CSS/JS for non-compositor properties and is only meaningful once Step-6 custom motion code (v2) exists to lint.

| Feature | Priority | Notes |
|---|---|---|
| Design Health HUD | v1 | **One always-visible, non-modal bottom-corner pill**: three dots (A11y / Perf / SEO), a page-weight bar, and a projected-LCP number from `PerformanceObserver`'s live LCP-candidate entry. Click to expand a grouped issue list. **Never a stream of interrupting toasts.** In v1 the A11y dot is fed by the structural heuristic rows below, not by the axe-core/contrast engine rows, which arrive in v2 — see the reconciliation note above |
| Live contrast checker | v2 **(Reconciled with §18 — was v1)** | WCAG 2 + APCA inline on the selection. Pure two-colour arithmetic — free to run live, which is why it was originally scoped v1, but §18 v2 scope-in groups it explicitly under "Live a11y/contrast lint inline" |
| Touch-target size warning | v1 | Flags <24×24 CSS px unless a WCAG 2.5.8 exception applies. Cheap structural heuristic — kept v1 per the reconciliation note above |
| Overflow/clipping warning | v1 | ResizeObserver + `scrollWidth > clientWidth`. Cheap structural heuristic — kept v1 |
| Broken-link scanner | v1 | Cheap structural heuristic — kept v1 |
| Missing-alt-text badge | v1 | Persistent counter, non-blocking. Cheap structural heuristic — kept v1 |
| Scoped axe-core run | v2 **(Reconciled with §18 — was v1)** | `axe.run(node)` on the touched subtree only after any placement/swap/text edit: color-contrast, image-alt, label, button-name, aria-required-attr, duplicate-id. Page-level rules deferred to lock. §18 v2 scope-in's "Live a11y/contrast lint inline" is read as covering this row together with the Live contrast checker above |
| Focus-not-obscured heuristic | v1 | Bounding-box intersect any placed sticky/fixed element against all focusables. Approximates WCAG 2.4.11. Cheap structural heuristic — kept v1 |
| Reading-order-vs-visual-order heuristic | v1 | After a reorder or free-position, walk the tabbable list and flag non-monotonic DOM-vs-rect pairs. Cheap structural heuristic — kept v1. Once §11's revision ships, this pairs with §11.3.1's `order`-override lint |
| Reduced-motion sibling presence | v1 | Confirm the placed item's catalog includes a tagged reduced variant; auto-apply a generated fallback and flag if missing. **Distinct from "Motion-property lint" (v2) — see the reconciliation note above.** Kept v1 because D4 requires every v1-catalog animated piece to ship with a reduced-motion fallback from day one, and this is a catalog-membership check, not a code-analysis engine |
| Image auto-optimisation on drop | v1 | Any image >~200KB or larger than its render box auto-recompresses to WebP/AVIF + srcset with a **visible undoable confirmation** ("−82% size, visually identical — Undo"). **Not silent** |
| Focus-order overlay | v2 | Optional numbered tab-order overlay |
| Live page-weight indicator | v2 | Running total against a soft budget |
| Off-token / design-drift warning | v2 | Advisory, non-blocking — a human-in-the-loop tool warns rather than mechanically forbids. Unchanged — already consistent with §18's v2 "off-token advisory" |
| Motion-property lint | v2 | Flags non-compositor properties, out-of-band durations, missing reduced-motion query in Step-6 custom animations. Unchanged — already consistent with §18's v2 "motion-property lint," and only meaningful once Step-6 custom code (v2) exists |
| Text-spacing stress clone check | v2 | Off-screen clone with the WCAG 1.4.12 override stylesheet, diffed for overflow. Unchanged — already consistent with §18's v2 "text-spacing stress clone" |
| Responsive-breakage warning | v2 | Flags elements only ever checked at one breakpoint |
| Spell-check | v2 | |

### 10.7 Collaboration & regeneration

**Reconciliation note for the whole subsection.** All seven rows below are v2 after reconciliation — this subsection contributes **zero v1 rows**, which is worth stating plainly since the pre-reconciliation draft had three of its seven rows marked v1. §18's v1 Editor-lite scope-in does not mention notes, regeneration, comments, or activity logs anywhere; §18's v2 scope-in explicitly lists "Per-section notes → scoped regeneration, regeneration log" and, separately, "comment pins" alongside "Share-for-review read-only link." The comment **schema** (distinct from the comment **pins UI**, which was already v2 in the pre-reconciliation draft) is demoted here too: nothing in v1 consumes a comment schema once regeneration-via-notes and comment pins are both v2, so defining the schema early buys nothing user-visible in v1. Implementers may still choose to write the schema at zero marginal cost whenever the v1 data model is being built — that's a scheduling choice, not a phase-gate requirement, and doesn't change its v2 priority tag here.

| Feature | Priority | Notes |
|---|---|---|
| Per-section notes → regeneration | v2 **(Reconciled with §18 — was v1)** | **The human-authored replacement for the rejected VLM critique loop.** A plain-language note ("make this pop more") becomes a scoped regeneration instruction. §18 v2 scope-in: "Per-section notes → scoped regeneration" |
| Regenerate-this-section-only | v2 **(Reconciled with §18 — was v1)** | Replaces in place. **Accuracy depends entirely on clean section boundaries** — design the two together (§10.2's Section boundary markers, kept v1 on an independent basis). Bundled with the row above |
| Collaboration-ready comment schema | v2 **(Reconciled with §18 — was v1)** | Author, timestamp, thread id from day one. Costs almost nothing now; a schema rewrite later costs a lot — but see the subsection note above: nothing consumes it until comment pins (v2) ship, so it moves with them rather than staying v1 alone |
| Canvas-anchored comment pins | v2 | Unchanged |
| Human-readable change/activity log | v2 | Plain-language: what changed, when, via manual edit vs swap vs regeneration |
| Share-for-review read-only link | v2 | Non-editable preview URL before LOCK |
| **Custom code block** | v2 | **An opaque draggable container holding hand-written HTML/CSS/JS that the editor positions but never introspects. The signature moment is built here, outside the menu — this is where the quality ceiling actually lives** (§14.4). Unchanged — already consistent with §18's v2 "Custom code block (the signature moment container)" |

### 10.8 Preview & export

| Feature | Priority | Notes |
|---|---|---|
| In-editor Preview mode | v1 | All chrome hidden, still inside the editor shell. A lighter, reversible rehearsal distinct from LOCK. Confirmed by §18's Editor-lite scope-in: "in-editor preview mode" |
| Interaction preview | v1 | Hover/click states live and testable — needed to verify a v1 component-bar swap actually behaves, not just looks, right |
| Motion preview toggle | v2 | Play / pause / prefers-reduced-motion, per container and globally (§9.6). Unchanged — already consistent with §18's v2 "Motion preview toggle" |
| Reduced-motion preview | v1 | Verify motion-sensitive visitors get a **designed** experience, not a deleted one. Distinct from the Motion preview toggle above (v2) — pairs with §10.6's v1 "Reduced-motion sibling presence" check as the minimum v1 motion-accessibility pair |
| Real-device LAN preview | v2 | QR code / local URL. **Prioritised earlier than a typical v2** because D2 makes responsive correctness a hard constraint and resized-browser preview cannot substitute for real DPR, touch-target feel, font rendering, and scroll physics. Unchanged — already consistent with §18's v2 "Real-device LAN preview" |
| Device-frame preview | v3 | Unchanged — already consistent with §18's v3 "Device-frame preview" |
| Lock / Publish flow | v1 | §12.5. Confirmed by §18's v1 scope-in: "LOCK with all five purity gates" |
| Lock verification gates | v1 | **Five automated purity gates (§12.5), not four** — this row previously undercounted them. In order: (1) forbidden-marker grep across `dist/published/**`, (2) two-build byte-equality (build with the editor integration installed vs. removed, require byte-identical trees), (3) `dist` JS byte-size assertion, (4) screenshot diff between editor-preview-at-1280 and the built page, (5) **the interaction-manifest check** — walks every declared motion/interaction behaviour against `dist/published` to prove it exists in shipped code, which is the gate that verifies D4's motion actually survives LOCK. §13's gate 27 already refers to "LOCK purity gates 1–5," so this row now matches §13 and §12.5 rather than contradicting them |
| Responsive preflight report | v1 | One command renders 320/390/768/1280/1440 (the verification set defined at the top of §10.1) and reports overlap collisions, horizontal overflow, fixed heights on text blocks, free-position counts, blocks with no mobile plan. **Blocking before lock** |
| Long-string reflow fuzz | v1 | Injects a 40-char unbroken token into every text block at 320px; enforces `overflow-wrap: anywhere`; forbids fixed heights on text-containing blocks |
| Evidence bundle export | v1 | §15.6. Confirmed by §18's v1 scope-in: "Evidence bundle" |
| Design-system re-export | v2 | Export current tokens so a future hand-carry starts from the live state |
| Raw code export / eject | v3 | Unchanged — already consistent with §18's v3 "Raw code export / eject" |
| Individual asset export | v3 | Unchanged — already consistent with §18's v3 "individual asset export" |

### 10.9 Command palette & onboarding

| Feature | Priority | Notes |
|---|---|---|
| Command palette (⌘K) | v2 | The standard escape valve for power without menu bloat, once the surface is ~95 features deep. Unchanged — already consistent with §18's v2 "Command palette" |
| Progressive disclosure via selection state | v1 | **The single most load-bearing anti-overwhelm mechanism across every mature editor.** The inspector is empty until something is selected, then shows only type-relevant properties |
| First-run anchor-model walkthrough | v1 | **The highest-value teaching moment is the anchor concept, not a toolbar tour.** Anchoring has no equivalent in Canva or PowerPoint, both of which are free-drag. A short guided "drag this, watch it snap and pin." Teaches exactly the v1 anchor-verb mechanic (§10.1) — nothing in it depends on the v2 canvas |
| Inspector panel (token-only) | v1 | **All non-geometric properties as selects over the design system's scales.** No free-text numerics, no colour picker. The lint wall expressed as UI — an off-token value must be **unreachable**, not merely flagged |

### 10.10 Reconciliation notes for this revision

**Method.** Every row in §10.1–§10.9 was checked against §18's v1 "Scope in" / "Scope cut (explicit)" text and v2/v3 "Scope in" text. A row was reconciled to v1 only where §18 names it (or an unambiguous synonym) in v1's scope-in, or where §18's v1 scope-cut text does not remove it *and* it has no dependency on something §18's cut does remove (e.g., §10.1's Anchor/pin control: verb/stepper-based, not drag, so the "no canvas drag" cut doesn't touch it). Four rows had no §18 citation either way and were kept at their pre-reconciliation value on stated inference, marked **[I]** in their Notes cell — Breakpoint switcher, Type-aware resize, Drag-to-reorder/reparent in tree (partially — see its row), Per-breakpoint visibility. These four should be treated as the first things to re-check the next time §18 itself is revised.

**Count reconciliation, by subsection (rows / v1 / v2 / v3):**

| Subsection | Rows | v1 | v2 | v3 |
|---|---|---|---|---|
| 10.1 Layout & placement | 21 | 5 | 16 | 0 |
| 10.2 Structure & selection | 16 | 10 | 6 | 0 |
| 10.3 Content | 20 | 14 | 5 | 1 |
| 10.4 History & persistence | 11 | 5 | 6 | 0 |
| 10.5 Navigation & wayfinding | 5 | 2 | 2 | 1 |
| 10.6 Quality | 18 | 9 | 9 | 0 |
| 10.7 Collaboration & regeneration | 7 | 0 | 7 | 0 |
| 10.8 Preview & export | 14 | 8 | 3 | 3 |
| 10.9 Command palette & onboarding | 4 | 3 | 1 | 0 |
| **Total** | **116** | **56** | **55** | **5** |

Pre-reconciliation, for comparison: 113 rows, 71 v1 / 37 v2 / 5 v3 (mechanical recount of the draft this revision started from — see §10's opening paragraph). This revision added 3 rows and reassigned 15 rows' priority (14 v1→v2, 1 implicitly v1→v2 split into two rows in §10.3); no row's priority moved to a *lower* number of restrictions (nothing moved v2→v1 or v3→v2), because §18's v1 scope-cut is strictly a removal list, never an addition beyond what its own scope-in already states — except the two rows this revision explicitly proposes as v1 exceptions in §10.3 (custom-component insertion's minimal registry slice, and the minimal chart-data field), both flagged **REQUIRES USER SIGN-OFF** since they deviate from §18's literal text in the direction of restoring a user-named capability.

**Rows whose priority changed (15, all v1→v2 except where noted as a new split):**

| Row | Old | New | Subsection |
|---|---|---|---|
| Real-grid overlay | v1 | v2 | 10.1 |
| Snap engine | v1 | v2 | 10.1 |
| Smart alignment guides + distance labels | v1 | v2 | 10.1 |
| Align tools | v1 | v2 | 10.1 |
| Padding / gap drag handles | v1 | v2 | 10.1 |
| Drag-to-place (grid write) | v1 | v2 | 10.1 |
| Span resize | v1 | v2 | 10.1 |
| Per-breakpoint override + reset-to-inherited | v1 | v2 (+ new v1-scoped-exception row) | 10.1 |
| Keyboard nudge & grid stepping | v1 | v2 | 10.1 |
| Breadcrumb ancestor bar | v1 | v2 | 10.2 |
| Drag-to-reorder / reparent in tree | v1 | v2 (section-level case stays v1 via §10.1's Section reorder) | 10.2 |
| Multi-select | v1 | v2 | 10.2 |
| Per-breakpoint visibility | v1 | v2 | 10.2 |
| Custom-component insertion | v1 (undifferentiated) | split: v1 (minimal registry, new row, sign-off required) / v2 (full) | 10.3 |
| Live contrast checker | v1 | v2 | 10.6 |
| Scoped axe-core run | v1 | v2 | 10.6 |
| Per-section notes → regeneration | v1 | v2 | 10.7 |
| Regenerate-this-section-only | v1 | v2 | 10.7 |
| Collaboration-ready comment schema | v1 | v2 | 10.7 |

(This table has more than 15 lines because the per-breakpoint-override and custom-component-insertion rows each produced two table lines above — one for the old undifferentiated row's disposition, one implied by the new split row's addition — counted once each in the "15" figure by feature, not by resulting row.)

**Open questions this revision could not close, left visible rather than papered over:**

1. **`layout.json` vs `pages/<id>.doc.json`** (§10.4's file-naming note). Renamed within this section; §4, §11, and §12.6/§12.10 still say `layout.json` as of this revision. Whether the command stack, op log, and editor lock are per-page or site-wide is undecided anywhere in the PRD — **requires a §12 update this section cannot make.**
2. **1440 has no live preview surface** (§10.1's breakpoint note). Checked at LOCK and at preflight, never previewable interactively in v1 or v2 as scoped here. **Requires user decision** on whether to add it as a fifth switcher option.
3. **Four rows kept on inference alone** (Breakpoint switcher, Type-aware resize, the section-level/general split on Drag-to-reorder-in-tree, Per-breakpoint visibility) — see the Method paragraph above. **No known mitigation beyond re-confirming against the next §18 revision.**
4. **Custom-component insertion (minimal) and the minimal chart-data field are deviations from §18's literal v1 cut, restoring a user-named Step-6 example (charts) to v1 usability. REQUIRES USER SIGN-OFF** before implementation — see the sign-off note at the top of §10.3. If the user declines, the honest fallback is to also move "Charts: build-time SVG only" out of v1 in §18, since a chart component nobody can populate with data is not a real v1 feature — that fallback would itself need to be written into §18, which is outside this section's authority.
## 11. Layout and dragging model (D2, settled)

### 11.1 The four-level layout contract (normative)

1. **Page** = a vertical list of sections. Reorder-only.
2. **Section** = a real CSS Grid — 12/6/4 tracks with `fr` units.
3. **Block** = integer `grid-column` / `grid-row` placement, per breakpoint.
4. **Inside a block** = flow only (hug / fill / fixed). Never coordinates.

This is Figma's model expressed in CSS, and it gives the best freedom-to-safety ratio of anything surveyed. Figma is explicit that its two positioning systems do not mix: constraints (Left / Right / Left-and-Right / Center / Scale) apply **only** to children of plain frames — *"It's not possible to apply constraints to layers … in an auto layout frame."* Inside auto layout you get direction, wrap, gap, padding, alignment, and per-child Hug/Fill/Fixed with min/max. The escape hatch is a single per-child toggle, **"Ignore auto layout,"** which removes that one child from flow, keeps it inside the parent, and hands it back the constraint system. **[V — help.figma.com, both articles fetched, quote verbatim]** Framer copied the same shape.

**Corollary that §11.3.1 depends on:** level 3's placement is *coordinates*, not *sequence* — moving a block visually never requires moving it in the document's child order. Level 1's "reorder-only" and level 4's "never coordinates" are the same idea applied one level up and one level down. Keep this in mind for the whole section: everywhere a "drag" writes data, ask which of the four levels is actually being edited, because levels 1 and 3 use different mechanisms for what looks like the same gesture.

### 11.2 The grid overlay must BE the grid

Draw the overlay by reading `getComputedStyle(section).gridTemplateColumns` — the browser resolves `fr` → px for you — and render those exact tracks. **Never a hand-authored decorative grid.**

Drag then becomes integer rounding:

```
col = clamp(1, round((x − gridLeft) / (colWidth + gap)) + 1, cols + 1)
```

and the persisted value is `grid-column: 3 / span 6`, which is **inherently fluid** (6-of-12 is 50% at every width). This single choice makes Step-4 dragging and Step-7 export the same data.

Wix Studio validates the approach: it ships a real advanced CSS grid with arbitrary row/column counts, units `fr` / `%` / `px` / `vw-vh` / `auto` / `minmax()` / `calc()`, placement by clicking a cell or typing column+row numbers, and explicit multi-cell spanning **[V — support.wix.com, fetched]**. Squarespace Fluid Engine is a 24-col desktop / 8-col mobile CSS grid **[V]**.

The formula above only ever derives a **column**. That is not an oversight to gloss over — the row axis, the occupied-cell policy, and the cross-section case are the actual hard part of this mechanic (this is Step 4b, the product's headline gesture), and they are specified in full below rather than left to be inferred at implementation time.

#### 11.2.1 Row derivation, span preservation, occupancy, and cross-section drops (normative drop algorithm)

**Row axis.** Section grids get an explicit row axis for placement purposes, sized from the direction's spacing scale (the same derived-value mechanism D1 uses for spacing/radius/shadow, applied to a `--wb-row-unit`) via `grid-auto-rows: var(--wb-row-unit)`. This gives rows discrete, droppable lines exactly the way `colWidth + gap` gives columns discrete lines:

```
row = clamp(1, round((y − gridTop) / (rowUnit + rowGap)) + 1, sanityRowCap)
```

`sanityRowCap` (recommend 200) exists only to reject runaway drags (branch AC8 below); it is not a layout constraint — CSS grid's `grid-auto-rows` already grows the track list as needed, so ordinary drops never hit it.

**Span preservation.** A dragged block keeps its existing `colSpan`/`rowSpan` when moved, with one exception: if the drop target's section has fewer columns than `col + colSpan − 1` requires (e.g. an 8-span block dropped into a 6-col section), `colSpan` clamps to `min(colSpan, targetCols)` anchored at the drop column, and the clamp is shown in the same pre-commit chip §11.3 already specifies for breakpoint-scoped edits, before the drop commits. `rowSpan` is never clamped (rows auto-grow).

**Occupied-cell policy.** When the computed target rectangle `{col, colSpan, row, rowSpan}` overlaps an existing sibling's rectangle:

- **Default: displace-down.** The overlapped sibling(s) shift down by the dragged block's `rowSpan + rowGap`, cascading to any sibling the shift in turn overlaps. A live ghost preview shows every block that will move *before* the pointer is released — this is not a silent side effect.
- **Exception: art/decoration containers may stack instead of displacing**, consistent with D4 (motion/art live in draggable containers, and §11.8 failure #4 already gives every section an integer z paint list). When either the dragged block or the occupied block carries `role: "art"` in its node data, overlap is resolved by z-order rather than displacement.
- **Opt-in stacking for non-art blocks:** a per-drop toggle, "Allow overlap here," lets the user deliberately stack two ordinary blocks (writes an explicit `z`) instead of displacing. This is an intentional escape hatch, not a default, and it is capped and counted by **the same lint family** as free-positioning (§11.4 rule 5) — a visible "N overlapping pairs" counter — precisely so it cannot quietly regrow the Squarespace mess §11.3's table documents.

**Cross-section drops.** Two cases:
- **Drop hovers over a different section than the block's current parent:** this is a re-parent, not a placement edit. The node is removed from the source section's children array and inserted into the target section's children array at the computed `{col, row}`. The vacated cell in the source section is left empty — no auto-compaction runs, because compaction would silently move *other* blocks the user did not touch, which is the same "changed order and position" failure §11.3's table quotes Squarespace for.
- **Drop lands in the boundary zone between two sections** (within one row-unit of a section edge): resolved as an append to the nearer section at that section's near edge row (row 1, or `maxRow + 1`), never as a merge of the two sections' grids.

**Rejected drops (visual: block snaps back with a brief outline flash).** A drop is rejected outright — not resolved by displacement — only when the target is illegal by construction:
- The pointer is over another block's **internal** region (level 4 of §11.1: flow-only, never coordinates). Blocks are never drop targets for other top-level blocks.
- The displacement cascade would have to reflow a step inside a pinned/scrubbed sequence container that forbids child reflow (§9.4).
- `row` would exceed `sanityRowCap`.

**Acceptance criteria — one per branch:**

| AC | Branch | Expected result |
|---|---|---|
| AC1 | Same-section move, no overlap | `col`/`row` update; `colSpan`/`rowSpan` unchanged; no sibling affected |
| AC2 | Same-section move, overlaps a non-art sibling | Sibling(s) displace down by dragged block's `rowSpan + rowGap`; ghost preview shown before release |
| AC3 | Same-section move, overlaps a sibling where either block has `role: "art"` | No displacement; overlap resolved via `z`; no lint counter change (art exception is unconditional) |
| AC4 | Same-section move, "Allow overlap here" used on two ordinary blocks | Overlap kept, explicit `z` written, overlap-lint counter increments and is shown |
| AC5 | Move into a narrower section | `colSpan` clamps to `min(colSpan, targetCols)`; pre-commit chip shows the clamp before commit |
| AC6 | Cross-section move | Node re-parented in the doc; source cell left empty; no auto-compaction anywhere in the doc |
| AC7 | Drop on another block's internal (flow-only) region | Drop rejected; block snaps back with outline flash |
| AC8 | Drop would force reflow inside a reflow-forbidding pinned sequence container (§9.4) | Drop rejected; block snaps back |
| AC9 | Computed `row` exceeds `sanityRowCap` | Drop rejected with an inline message, not a silent clamp |

### 11.3 Breakpoint cascade: desktop-down, one direction

| Builder | Model | Outcome |
|---|---|---|
| Webflow | Base = Desktop 1280; tablet ≤991, mobile-landscape ≤767, mobile-portrait ≤479. Styles inherit downward; a smaller-breakpoint override permanently detaches that property | Works, with documented cascade confusion |
| Wix Studio | *"changes you make on larger breakpoints trickle down to smaller breakpoints, but changes on smaller breakpoints don't affect larger"* | Works |
| Framer | *"Changes made at a smaller breakpoint only affect that breakpoint and below"* | Works |
| **Squarespace Fluid Engine** | **Separate grid for mobile with independent block placement** | **Documented overlap epidemic**: *"Separate text boxes can easily end up overlapping on narrower screens, creating a real mess of unreadable letters"*; blocks *"mix-up or change order and position"*; Squarespace experts publicly campaigned for fixes |

**[V — all four, fetched from help.webflow.com, support.wix.com, framer.com/academy, engineering.squarespace.com + practitioner write-ups]**

**Verdict: desktop-down cascade with sparse per-breakpoint overrides. Never two independent layouts.**

Because the cascade is a documented beginner confusion source, the UI must make the current breakpoint **structurally prominent** — a persistent chrome element, not a dropdown the user can forget they set — and must show a **pre-commit chip** stating exactly which sizes an edit will affect, with a one-click "apply to all sizes instead."

Blocks with **no** small-breakpoint override compile to `grid-column: 1 / -1` in source order. That default alone prevents the *overlap* half of Squarespace's signature failure. The Squarespace quote above names a second, distinct failure — "blocks mix-up or change order and position" — which the overlap default does nothing for. §11.3.1 is that missing half.

#### 11.3.1 Reading order vs. visual order (mobile stacking, focus order, screen readers)

**Invariant (normative): DOM order is always the intended reading order.** Desktop and tablet visual order is achieved *only* by grid placement — explicit `grid-column`/`grid-row` integers, or named areas per §11.6 — never by reordering nodes in the document tree. This is why §11.2.1's drop algorithm never touches the sibling array for an ordinary drag: a same-breakpoint move only ever writes `col`/`row`/`colSpan`/`rowSpan`, so DOM order — and therefore mobile stack order, tab order, and screen-reader order — stays fixed by construction unless a user deliberately overrides it (below).

**The one legitimate exception:** an author sometimes genuinely wants the sequence a phone or a screen reader encounters to differ from where a sighted desktop reader's eye lands first — e.g. a pull-quote placed visually first on desktop but intended to be read last. For that case only, the layout node exposes a **per-breakpoint `order` override**, independent of `grid-column`/`grid-row`:

```
order: { bp: "sm" | "md" | "lg", value: N }
```

Using it has real, named costs, which the editor surfaces rather than hides:

- It desynchronises visual order from reading/tab/screen-reader order at that breakpoint, by definition. The moment `order` is set to a non-default value, the editor shows a **persistent warning chip**: "Reading order will differ from what's shown here."
- It is **blocked by a hard lint on any focusable node** (link, button, form field). CSS `order` moving a focusable control breaks WCAG 2.2 **SC 2.4.3 Focus Order (Level A)** without a `tabindex` remediation strategy this PRD does not take on — the lint refuses the edit outright for those node types rather than merely warning.
- For non-focusable content nodes (text, art, decorative containers) the lint is a warning, not a block — **SC 1.3.2 Meaningful Sequence (Level A)** still applies, but reordering non-interactive content is a judgment call the author is entitled to make deliberately, with the warning as the record that it was deliberate.

**Small-breakpoint stack-order preview.** Before any commit that changes mobile stacking — a small-breakpoint layout override, a new `order` value, or a block moving to/from the `1 / -1` default — the editor renders a numbered list preview of the resulting top-to-bottom mobile sequence, at the same breakpoints §10.1's preflight report already renders (320/390/768/1280/1440), so the user sees the actual read order, not just the visual box layout, before committing. This is the mobile-stacking counterpart to the pre-commit chip already specified above for breakpoint-scoped style edits.

**§10.1's responsive preflight report gains a check as a direct result:** it already can flag a breakpoint where DOM order and computed visual (row-major) order diverge past a heuristic threshold; per the gap this subsection closes, that flag now has a remediation path attached (the `order` override and its lint, above) instead of being a dead-end warning with no fix a user can take.

### 11.4 The free-position escape hatch

Practitioner documentation is blunt about the cost. Framer University: *"Your element won't adjust when the screen resizes. What looked perfect on desktop suddenly overlaps or disappears on mobile"*; Framer *"stops treating that element as part of the stack"*; *"Spacing gets weird. Alignments break. Responsiveness? Gone"*; and animations desync because *"elements no longer share the same reference points"* — which matters directly under D4. GrapesJS is equally explicit that its absolute mode is *"ideal for fixed-layout designs like documents for print, business cards, certificates, or static prototypes where responsiveness isn't required."* **[V — framer.university, app.grapesjs.com, quotes verbatim]**

The mechanics of naive absolute positioning: (1) the element leaves flow, so an auto-height parent collapses and the next section slides up under it; (2) `left: 812px` was measured in a 1512px editor viewport, so at 390px it sits 422px off-screen, creating body `overflow-x` or invisible clipping; (3) at 2560px it floats in dead space. Then the user does it fourteen more times and the site is a 1512px fixed canvas wearing a responsive costume.

**Design rules:**

1. **Not raw absolute.** Implement as **anchored-offset**: the element keeps a declared anchor and the free drag writes a **percentage / `clamp()` offset from that anchor**, so it scales. **v1 restricts the anchor target to `parent` or a grid line/cell** — `anchor: { to: "parent" | { col, row }, edge: ... }`. Anchoring to an arbitrary sibling node is **deferred, not implemented**: CSS anchor positioning is the only zero-JavaScript way to express an offset relative to a non-parent sibling, and §11.5 (below) rules anchor positioning out for load-bearing layout — it is still a carryover Interop 2026 item — while runtime positioning JavaScript is separately forbidden in the locked export by the no-editor-runtime contract (§12.5). Neither implementation path is legal as written, so sibling anchoring cannot ship in v1.
   **This narrows the hatch from what was originally stated ("parent edge, sibling, or grid cell") and is a deviation from the user's Step-4b expectation — it requires explicit user sign-off**, since D2 grants the free-position escape hatch without qualifying which anchors it covers. Two paths forward, neither yet validated:
   *(a)* accept the v1 restriction (parent or grid-cell anchors only) as the shipped scope; or
   *(b)* if sibling anchoring is genuinely required, the only known compile strategy is to promote the anchored pair into a shared CSS subgrid wrapper at generate time — subgrid is universally supported (§11.5) — turning the offset into a track-relative value instead of a JS-measured one. **This has not been prototyped. Open question, no known mitigation beyond the subgrid idea stated here** — do not treat it as a committed design.
   **Coordination requirement:** §12.3's persisted schema currently reads `anchor: { to: "parent" | nodeId, edge: ... }`; whichever path (a)/(b) is chosen, that schema must be updated to match — `nodeId` should be narrowed to the grid-cell form under path (a), or explicitly retained only once path (b)'s compile strategy is proven under path (b). Flagging for §12's owner; this section does not have authority to edit §12.3's text.
2. The parent gets a reserved `min-block-size` at drop time so it cannot collapse.
3. Per-block **and** per-breakpoint.
4. **Auto-demotes to normal flow at ≤390px** — moved down from the originally stated 479px, which is not a breakpoint the editor, the preview iframe, or the lock gate can ever render: §10.1's live breakpoint switcher offers 390/768/1280/full, this section's own Hard LOCK gate (rule 6, below) renders 390/768/1440, and §11.7 pins device heights at 390×844/768×1024/1280×800/1440×900. None of those include 479. 390 is the smallest width any of them actually shows, so it is the only small-screen demotion boundary a user can preview *before* it fires.
   The demotion is **authored into the document, not computed implicitly at render.** Dropping — or later editing — a free-positioned block writes a sibling object on the same node:
   ```
   flowFallback: { col, colSpan, row, order }
   ```
   defaulted at drop time from the element's current visual position (nearest column line; row per §11.2.1; DOM order unchanged unless the user separately sets §11.3.1's `order`), and independently editable afterward in the Navigator — never a value the user has to reverse-engineer from behavior. At ≤390px the compiled CSS switches that node from its anchored-offset rule to ordinary `grid-column`/`grid-row` sourced from `flowFallback`; nothing about where the element lands at that breakpoint is inferred at render time or hidden from the editor.
   The z-stacking a free element had under §11.8 failure #4 is dropped at the same breakpoint by default — an element that overlapped others by design in free-position mode has nothing left to overlap once it's back in flow — unless `flowFallback` also carries an explicit `z`, which the user may set the same way any stacked block's z is set (§11.2.1).
5. **Lint caps free-positioned blocks per section** (~2), with a visible counter ("4 elements are free-positioned"). This is the same lint family §11.2.1 extends to opt-in overlap pairs.
6. **Hard LOCK gate**: render at 390/768/1440 and refuse to lock if any free-positioned element produces document `overflow-x` or leaves its parent's box.
7. Disabled by default for pinned/scrubbed sequence containers (§9.4).

**Honest caveat:** anchored-offset still fails for art whose composition depends on absolute relationships across the whole viewport (a scattered constellation of sprites). For that case the only answer is to treat the whole composition as **one component with its own internal responsive rules** — which means the user cannot drag its parts individually, which is exactly what they asked for. There is no better answer.

### 11.5 Container queries, not viewport media queries, inside components

Step 4(d) lets the user swap a component for a variant, and 4(b) lets them move it between slots of different widths. If component internals key off `@media`, a card that looks right in a 6-col slot breaks the moment it is dragged into a 3-col slot — an unbounded matrix of manual fixes.

**Put `container-type: inline-size` on every block wrapper and write component internals with `@container`.** A component then adapts to *the space it was dropped into*, which is the only sane contract for drag-and-swap.

Platform status as of 2026: container queries, `:has()`, `@property`, cascade layers, nesting, and logical properties are all **Baseline Widely Available**. Subgrid is universally supported (Chrome 117+, Firefox 71+, Safari 16+) and is the right tool for aligning a nested component's internals to the parent section's tracks — and, per §11.4 rule 1 path (b), the only currently-known way sibling-relative free-position offsets could ever be made to work without runtime JS. **Anchor positioning is still a carryover Interop 2026 item — use it only for editor chrome and progressive-enhancement decoration, never load-bearing layout.** This is the platform fact §11.4 rule 1 is reconciled against: it is why sibling anchors are deferred rather than shipped in v1. **[V — web.dev/blog/interop-2026, webkit.org]**

### 11.6 grid-template-areas and integer placement, together

Named areas are the most readable and most mobile-safe form — the entire mobile layout of a section is one property rewrite. Their hard limit is that every area must be a **contiguous rectangle**, so they cannot express arbitrary drag results (an L-shape, or two blocks in one cell).

**Resolution:** the design system ships ~12 section archetypes as `grid-template-areas` per direction. The moment a user drags a block off its area, **that block only** is promoted to explicit `grid-column`/`grid-row` integers on the same grid — the same integers §11.2.1's drop algorithm computes. Both compile to identical CSS Grid, so export is unaffected and the archetype stays readable for every untouched block.

### 11.7 Preview must be a same-origin iframe

A scaled `<div>` cannot evaluate media queries against the simulated width; an iframe can, because the iframe's own viewport is what `@media` sees.

Puck ships exactly this: viewports as `{width, height: 'auto'|number, label, icon}`, defaults Small 360 / Medium 768 / Large 1280 / Full-width, *"rendered in a same-origin iframe that can be resized to simulate different viewports"* **[V — puckeditor.com/docs/integrating-puck/viewports, fetched]**.

**The trap:** all four Puck defaults use `height: 'auto'`, so any hero using `100vh`/`svh`/`dvh` measures the iframe's expanded height, not a phone's. Hero framing looks right in the editor and wrong on device. **Fix: pin device heights (390×844, 768×1024, 1280×800, 1440×900) whenever the page contains a viewport-height rule.** Also note that when Puck's compositional `<Puck.Preview />` is used directly, the viewports API has no effect at all.

### 11.8 Failure-mode catalogue — all fourteen mechanically detectable

| # | Failure | Detector |
|---|---|---|
| 1 | Small-screen overlap (Squarespace's signature failure) | Per-breakpoint rectangle-intersection over resolved grid areas; default any block with no sm override to `1 / -1`. Same-breakpoint overlaps are additionally *prevented at drop time*, not just caught after the fact, by §11.2.1's occupancy rule |
| 2 | Horizontal overflow | Assert `documentElement.scrollWidth <= clientWidth` at 320/390/768/1280/1440 |
| 3 | Text reflow blowout | Fuzz every text block with a 40-char unbroken token at 320px; require `overflow-wrap: anywhere`; forbid fixed heights on text blocks |
| 4 | Z-order confusion | Z-order is an integer paint list per section in `layout.json`, compiled to `z-index` only where needed, with each section establishing a stacking context (`isolation: isolate`) so nothing leaks across sections. §11.2.1's art-stacking and opt-in-overlap branches are the only paths that intentionally write to this list |
| 5 | Nested scroll containers | Forbid `overflow: auto` inside blocks except one explicit "scroller" component |
| 6 | Absolute drift | Cap free-positioned blocks per section; auto-demote to `flowFallback` at ≤390px (§11.4 rule 4) |
| 7 | Unclickable / ghost elements | The Navigator tree is the guaranteed selection path |
| 8 | Zoom-broken snapping | Tolerance ÷ zoom |
| 9 | 100vh lying in the editor | Pin iframe device heights |
| 10 | Font-load measurement drift | `await document.fonts.ready` before **any** `getBoundingClientRect` in editor or capture |
| 11 | Split undo stacks | A single command stack over `layout.json` patches |
| 12 | Drag pointer leaving the iframe | `setPointerCapture` on the overlay; translate coordinates by the iframe rect rather than listening inside |
| 13 | Occupied-cell drop producing silent displacement, or overlap outside the declared art/opt-in exceptions | §11.2.1's drop algorithm resolves overlap *at* drop time (displace-down by default; z-stack only under the `role:"art"` exception or an explicit "Allow overlap here" opt-in, both lint-counted); illegal targets are rejected outright per its AC6–AC9 rather than left ambiguous |
| 14 | Reading order silently diverging from visual order (mobile stack order, tab order, screen-reader order) | §11.3.1's DOM-order-is-reading-order invariant, the hard lint blocking `order` overrides on focusable nodes (WCAG SC 2.4.3), the warning lint on non-focusable nodes (WCAG SC 1.3.2), and the preflight divergence check with an attached remediation path |

### 11.9 Zero DOM injection (architectural constraint, not a note)

The natural implementation of drag is to wrap each component in a `<div data-wb-id>` for hit-testing. **Do not.** Those wrappers get removed at LOCK, and the site uses `.grid > *` for auto-placement, `:first-child` for the hero's top margin, and flex `gap` between direct children. With wrappers the direct children were the wrappers; without them they are the components. Every one of those selectors now matches different elements. The locked site's spacing differs from the design surface by 8px here and a whole grid column there, **and there is no way to explain it to the user because "nothing changed."**

**Constraint:** hit-testing uses `data-wb-node` attributes on elements that **already exist**, plus a **single sibling overlay `<div>` outside the page's layout root**, positioned with `getBoundingClientRect()` + `ResizeObserver`. Handles, selection rings, snap guides and gridlines all live in that overlay. LOCK then removes exactly one element and one `<script>`, and **provably cannot move anything**.

**Corollary for Step 7's "gridlines removed":** the gridlines must visualise a **real CSS Grid** on the page (with named lines). If the grid is only an overlay and snapped positions are baked as margins, removing it is fine — but then "components snap to gridlines" (D2) is decoration, and changing the grid later reflows nothing. **Pick real-grid, and make removal a no-op by construction.**

---
## 12. Document model, persistence, and the LOCK/UNLOCK contract

### 12.1 Two-tier truth (the highest-leverage architectural decision in the PRD)

| Tier | What | Owner | Notes |
|---|---|---|---|
| **Composition** | Which component, which variant, order, slot, anchor, prop values, text | `pages/<id>.doc.json` (+ `content.json`) — **the only thing the editor mutates** | A scene graph |
| **Implementation** | `.astro` component sources, `tokens.json` (DTCG) + compiled `tokens.css`/Tailwind `@theme`, art assets | Real files on disk, versioned, arriving from the Step-3 hand-carry | Claude edits these |
| **Rendered site** | `.astro` page files under `src/generated/**` | Produced by a pure function `render(doc, systemLock, library) -> files` | **Never parsed back into JSON** |

**Rejecting HTML→JSON round-tripping is what makes drift structurally impossible rather than merely managed.** Every product that reconstructs a doc from rendered markup is lossy at exactly the places that matter — anchors, variants, intent. This is also the canonical WYSIWYG failure (Dreamweaver design view, FrontPage, Muse): the editor parses source into a DOM, the user edits, the editor re-serialises, and comments vanish, formatting normalises, hand-tuned CSS is rewritten. **Worse here, because Claude is also writing this source** — the next read sees reformatted markup it did not write, with its own comments gone, and diffs become unreviewable.

It also makes D1 cheap: swapping a variant is a single JSON field change, and "10 more variants" is a library operation, not a page rewrite.

**`render` is total, not partial.** Declaring the doc the only truth and the renderer a pure function creates an obligation the original draft left unstated: **every `component` / `variant` / `motion` / `asset` / token id in the doc must resolve against the library, and the PRD must say what happens when one does not.** This is not a corner case — it is the *normal* consequence of the user's own Step 5 ("if nothing looks good, generate a brand-new design-system prompt"), of restoring an older lock, and of the v2 cross-direction swap in §18. The full resolution and migration policy is **§12.16**, and it is normative: a renderer that silently emits a hole, or an editor that hard-crashes on open, are both failures.

**Prior art split.** Family A (JSON doc + pure render): Puck `{content[], root, zones}`, Craft.js, Builder.io. Family B (files-as-truth + annotation mapping): TinaCMS, Netlify/Stackbit Visual Editor, Onlook. **Anti-patterns:** Webflow export drops CMS collections, forms, site search, password protection and localisation — collection lists render empty, template pages don't generate. Framer ships no HTML export at all. Both are one-way doors, and D3 requires reversibility. **[V — puckeditor.com, builder.io, docs.netlify.com, tina.io, github.com/onlook-dev/onlook; Webflow gaps from brixtemplates/memberstack/thecssagency analyses, consistent across sources]**

### 12.2 The file set

| File | Purpose | Writer |
|---|---|---|
| `site.json` | Project record: formatVersion, projectId (ULID), breakpoints (the key vocabulary of §12.3), grid, page list, per-page SEO/meta, and `systemLock {directionId, systemVersion, tokensSha256, librarySha256, source, importedAt}`. **The systemLock is what makes a re-run of Step 3 unable to silently change what a page renders** | Editor process, via typed ops only (§12.13) |
| `pages/<id>.doc.json` | The scene graph. Node: `{id, component, variant, region, layout, props, slots, text, override, locked, notes, variantMigrated?, orphaned?}`. **Serialised in the canonical form of §12.9** — that formatting decision alone determines whether the git history is useful | Editor process |
| `content.json` | Copy, separated so a content-only edit path exists (§15's "90% of month-six edits are copy changes" path) | Editor process; also the content-only CLI |
| `history.jsonl` | Append-only op log: `{seq, ts, actor: 'user'\|'agent', op, target, patch: [RFC6902], inverse: [RFC6902], label}` | Editor process |
| `system.lock.json` | Pins the imported direction like a package-lock: id, version, per-file hashes of tokens and every component | Importer (Step 3) and `wb migrate` only |
| `assets/manifest.json` | Per-asset provenance and licence. **Also the allowlist the generator validates every asset reference against**, closing the hallucinated-URL class. Records the exact encoder + settings used for each derived asset (§12.8 hazard 5) | Editor process (asset/media manager) and the importer |
| `provenance.json` | Per component instance: direction id, variant id, generation timestamp, prompt hash | Editor process |
| `inbound/import-report.json` | Per-item accept/reject/quarantine with reason and offending snippet | Importer process only |
| `migration-report.json` | Written by `wb migrate` (§12.16): every reference that changed, its old and new value, and the rule that decided it | `wb migrate` only |
| `.wb/inbox.jsonl` | Append-only agent intent channel | Any agent (append-only) |
| `.wb/editor.lock` | Single-writer pid + mtime heartbeat | Editor process |
| `.wb/editor.token` | Per-session bearer token, mode 0600 | Editor process |
| `.wb/doc-hashes.json` | Journal of `{path, sha256, mtimeMs, seq}` for every doc-owned file **as the editor last wrote it**. The reconciliation input that turns an out-of-band write into a visible conflict rather than a silent clobber (§12.10) | Editor process |
| `.wb/session-ui.json` | Selection, scroll position, open panels, active breakpoint key | Editor process |
| `.wb/locks/<iso>/` | Immutable per-LOCK snapshot: every `*.doc.json`, `site.json`, `content.json`, `system.lock.json`, `assets/manifest.json`, the dist hash manifest, the scrub output, `lock-manifest.json`, `gate-report.json` | `wb lock` only |
| `lock-manifest.json` | Written at LOCK; records the layout hash **and a SHA-256 per emitted file in `dist/published/`** so unlock can diff against hand-edits (§12.6 row 6) | `wb lock` only |
| `package.publish.json` + `package-lock.publish.json` | The editor-free dependency set used by purity gate 2, generated by `wb lock` and **committed**, so gate 2 is not itself a network-variable step (§12.5) | `wb lock --refresh-publish-manifest`, reviewed by a human |

### 12.3 The layout node — where D2 lives

**Breakpoint key vocabulary (normative, and shared by §10.1's switcher, §11.3's cascade, §11.4's free-position rules, this schema, and the §13 gates).** The original draft of this section carried an `lg` key that narrowed a 12-column default to 10 — a *mobile-first* base with a *larger*-breakpoint override, which is the exact inverse of §11.3's normative verdict ("desktop-down cascade with sparse per-breakpoint overrides"). §11.3 wins; §12.3 is corrected here, because §12.3 is the save format and an inverted save format inverts every page.

| Key | Compiles to | Grid tracks (§11.1) | Switcher label (§10.1) | Preview width | Notes |
|---|---|---|---|---|---|
| `base` | No media query — emitted unconditionally | 12 | `1280` and `full` | 1280×800 pinned when the page has any `vh`/`svh`/`dvh` rule; `full` previews the same `base` rules at the browser's own width | **The authored default is the desktop layout.** There is no key above `base` in v1 |
| `md` | `@media (max-width: 991px)` | 6 | `768` | 768×1024 | Boundary taken from the Webflow tablet breakpoint cited in §11.3's table; 768 sits inside it |
| `sm` | `@media (max-width: 479px)` | 4 | `390` | 390×844 | Boundary taken from the Webflow mobile-portrait breakpoint cited in §11.3; **identical to the ≤479px auto-demote boundary in §11.4 rule 4**, which is why they are one number and not two |

Emission order is `base`, then `md`, then `sm`, so the narrower rule always wins by source order without `!important` and without specificity games. **A node with no `sm` entry compiles to `grid-column: 1 / -1` at `sm`** — §11.3's single most load-bearing rule, and the one that prevents the documented Squarespace overlap epidemic. That rule is only reachable because overrides attach *downward*.

> **[I — inference, flagged]** The pairing of *boundary* (991/479, from §11.3's cited Webflow row) with *preview width* (768/390, from §10.1's switcher) is a reconciliation this PRD is making, not a figure quoted from a source. It is chosen because it makes both existing statements true simultaneously. If the user prefers the boundaries to equal the preview widths (768/390), that is a one-line change here and in §11.4 rule 4 — but it must be changed in **all four** places at once, and it is **O31** below.

> **Deviation requiring user sign-off.** v1 ships **no wide/`xl` tier** (no override band above 1280). §10.1's switcher has a `full` entry, which previews `base` at the browser width but cannot carry its own overrides. If the user expects to art-direct a distinct ≥1440 layout, that is an added key (`wide`, `@media (min-width: 1440px)`) and the *only* upward override in the system — an explicit exception to the desktop-down rule that would need its own cascade note. **Not assumed. Requires user decision (O32).**

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

Read it as: on desktop the art sits in columns 2–11 of a 12-track grid; at ≤991px it takes all 6 tracks; at ≤479px it has **no entry at all**, so it compiles to `grid-column: 1 / -1` on the 4-track grid. Sparse, downward, and the mobile default is the safe one.

`base` is mandatory on every node. `md`/`sm` are optional and are written **only** when the user actually overrides at that size — which is what makes "every overridden property shows an *overridden here* dot and a one-click reset" (§10.1) implementable as a key-presence test rather than a value comparison.

Free-position escape hatch (§11.4, v2): `{ "mode": "free", "anchor": { "to": "parent"|nodeId, "edge": "top-left" }, "offset": { "x": "12%", "y": "clamp(1rem, 4vw, 3rem)" }, "z": 2 }`. It is a per-key value like any other, so a node may be `free` at `base` and absent at `sm` — which is exactly how §11.4 rule 4's auto-demote is represented: **absence at `sm` means flow at `sm`.**

Per D4, **motion is not a separate structure** — an animated piece is an `ArtContainer` node whose `props.motion` is a token/preset id, manipulated identically to a static art container.

Borrow Puck's proven conventions: a `root` node with its own props, **named slots rather than the deprecated `zones` string-key hack** (`"HeadingBlock-1234:my-content"` — Puck deprecated exactly this in favour of slot fields, so start where they ended up), and ids that encode component type for debuggability.

### 12.4 DOM ↔ doc mapping

Copy Stackbit's annotation scheme **including its scoping rule**. Netlify Visual Editor's annotations are *"HTML data attributes … so that the visual editor can map content in the preview to the correct document and field"*; `data-sb-object-id` identifies the document *"along with all descendants of that element in the DOM tree"*; `data-sb-field-path` gives the path to the field. **Scoping-by-descent is the important detail** — annotate once at the node boundary and inherit. **[V — docs.netlify.com, quotes verbatim]**

Our attributes: `data-wb-node` (scopes descendants), `data-wb-field` (marks inline-editable), `data-wb-slot` (drop region), `data-wb-variant` (what the component bar reads), `data-wb-layout` / `data-wb-anchor` (what the drag handler reads), `data-wb-bp` (which breakpoint key produced the resolved placement, so the "overridden here" dot has a DOM-side source). **All emitted only under `import.meta.env.WB_DESIGN`; all asserted absent from `dist/published`.**

Astro gives DOM→source-file mapping for free: it injects `data-astro-source-file` and `data-astro-source-loc` in development only (a filed issue confirms they appear in dev even when `devToolbar` is disabled — gated on dev, not on the toolbar). **[V — withastro/astro issue #9324; astro-click-to-source integration]** So no Babel instrumentation is needed.

### 12.5 The LOCK/UNLOCK contract (D3, settled)

**LOCK is a re-render, never a copy-and-strip.** Same renderer, `editor: false`. The FruitSync precedent proves what copy-and-strip costs: the release required rewriting every `/a01/` link to `/` and manually excluding the dev variant-chooser and four dev mockup pages from the shipped folder **[V — DEPLOY-STEPS.md]** — which is exactly the leakage D3 exists to prevent.

**Five layered enforcement mechanisms, four of them documented Astro/Vite features:**

1. **Two configs, two commands, two outDirs.** `astro dev --config astro.design.mjs` vs `astro build --config astro.publish.mjs --outDir dist/published`. **Only the design config registers the editor integration**, so the editor is not in the publish build graph at all.
2. **`astro:config:setup` receives `command: 'dev'|'build'|'preview'|'sync'` and `injectScript(stage, content)`.** Gating on `command === 'dev'` is the documented dev-only injection pattern.
3. **`addDevToolbarApp(entrypoint)`** for editor chrome. Astro's docs state the toolbar *"is a development tool only and will not appear on your published site"* — which makes the component bar, grid toggle and save button a class of UI that **physically cannot leak**.
4. **`import.meta.env.WB_DESIGN` guards** for anything inside a component. Vite statically replaces `import.meta.env.*` at build time so the dead branch is eliminated — **but the gotcha is real and filed (vite#15256): if the variable is undefined the branch may NOT be shaken.** `WB_DESIGN` must be explicitly defined as `false` in the publish config's `vite.define`.
5. **`astro:build:done`** receives `dir` (URL), `pages` (`{pathname}[]`) and `assets` (`Map<string, URL[]>`) — enough to post-scrub every emitted HTML file and then assert.

**[V — docs.astro.build integrations reference + dev-toolbar guide, direct quote; vite.dev env-and-mode; vitejs/vite #15256]**

**The gate is an executable assertion, not a claim.** `wb lock` = build → scrub → assert → snapshot. **Gates 1–5 keep their existing numbers** (they are cross-referenced from §13.4 row 27 and from §10.1's "Lock verification gates" row); gates 6–8 are additions.

| Gate | Check |
|---|---|
| 1 | Grep `dist/published/**` for `data-wb-`, `wb-editor`, `astro-dev-toolbar`, `data-astro-source-file`, `data-astro-source-loc`, `/@vite/client`, `import.meta.hot`, the editor token filename. **Any hit fails the build** |
| 2 | **Byte-equality**: build the same doc twice — once with the editor integration installed, once with it removed from `package.json` entirely — and require the two trees to be byte-identical. **This converts "the editor doesn't ship" from an intention into a CI fact.** Mechanism, preconditions and budget are specified below; without them this gate is unbuildable |
| 3 | `dist` JS byte-size assertion (an accidental editor import shows up as a step change) |
| 4 | Screenshot diff between editor-preview-at-1280 (chrome hidden) and built-page-at-1280 — proves LOCK changed nothing visual, and catches the residual case where a `data-wb-*` attribute participated in a CSS selector or affected intrinsic size |
| 5 | **Interaction-manifest check**: walk every declared motion/interaction behaviour against `dist/published` to prove it exists in shipped code. This is the Webflow-export lesson applied to a static target — no behaviour may exist only as editor state |
| 6 | **Zero unresolved references** (§12.16): every `component`, `variant`, `motion`, asset and token id in every doc resolves against `system.lock.json` + the library, and **zero nodes carry an unacknowledged `variantMigrated` or `orphaned` flag**. Fails with the node list, not a count |
| 7 | **Zero design-time origins**: grep `dist/published/**` (including `srcset`, `<meta>` content, inline `style`, CSS `url()` and `@import`, JSON-LD, and sourcemap comments) for `localhost`, `127.0.0.1`, `0.0.0.0`, `file://`, the session port, and the session root path. **A hardcoded `http://localhost:4321/img/hero.png` passes gates 1–5 and 404s for every visitor** — this closes that. Also the enforcement point for §12.6 row 9 |
| 8 | **`wb verify` clean at lock time**: regenerate `src/generated/**` into a temp dir and `diff -r` the text files; hash-compare binary assets separately (§12.8 hazard 5); and re-serialise every doc into canonical form (§12.9) and require a zero diff, so a hand-edited or foreign-serialiser doc cannot be locked |

> **Cross-section amendments this creates** (they belong to §13 and §19, recorded here so they are not lost): §13.4 row 27 becomes "LOCK purity gates 1–8 (§12.5)". §10.1's "Four automated gates (§12.5)" note becomes "Eight automated gates (§12.5)". §18's v1 bullet "all five purity gates" becomes "all eight purity gates". §19 A49 gains the gate-7 origins grep, and new criteria **A91–A99** below are appended.

**Gate 2, mechanically.** The original text asserted the gate without saying how the second build is produced, whether `wb lock` mutates `package.json`, what happens to a running design server sharing `node_modules`, or how long it takes. Normative procedure:

1. **Clean tree, never the working tree.** `git worktree add --detach .wb/tmp/gate2 HEAD` (fallback when the project is not yet committed: `rsync -a --exclude node_modules --exclude dist --exclude .wb`). `wb lock` **never** edits the live `package.json` or the live lockfile, and never touches the live `node_modules`, so a design server running in another terminal is unaffected.
2. **A committed editor-free dependency set.** `package.publish.json` / `package-lock.publish.json` (§12.2) are the live files minus the editor integration and minus design-only devDependencies. They are generated by `wb lock --refresh-publish-manifest`, **human-reviewed and committed** — regenerating them inside every lock run would make the gate depend on the registry and on the day.
3. **Install deterministically.** `npm ci --prefix .wb/tmp/gate2 --ignore-scripts` against that lockfile. Build A uses the live tree's install; build B uses this one.
4. **Pin the environment for both builds.** `SOURCE_DATE_EPOCH` = the HEAD commit timestamp, `TZ=UTC`, `LC_ALL=C`, a fixed `NODE_ENV`, an explicitly pinned Node version (recorded in `gate-report.json`), and `vite.define` supplying `WB_DESIGN=false` in both.
5. **Compare by manifest, not by `diff -r`.** Emit `manifest-a.json` / `manifest-b.json` = sorted relative path list + SHA-256 per file, and require them identical. A manifest diff names the offending file; a raw tree diff on minified bundles does not.

**Preconditions this gate depends on, stated rather than assumed:** no build timestamps in output; deterministic chunk and asset content hashing; no absolute paths in emitted sourcemaps or CSS; stable module graph ordering; and the asset-encoder pinning of §12.8 hazard 5.

> **O33 — open, no verified answer.** *Is an Astro/Vite production build byte-reproducible across two installs of the same lockfile on the same machine?* §12.8 constrains the determinism of **our generator**; it says nothing about the bundler, and **no source consulted for this PRD establishes bundler-level byte reproducibility.** This must be a Phase-0 spike, because §18 makes "a passing two-build byte-equality check" the v1 exit criterion. If the spike fails, the **fallback** is a *normalised* comparison: identical file lists, identical SHA-256 for every file except a named, enumerated exception set recorded in `gate-report.json`, with each exception justified. **That fallback weakens D3's proof from "byte-identical" to "identical except for N declared files" and therefore requires user sign-off before it is adopted.** Do not pretend otherwise. A gate that fails spuriously will be disabled by whoever is trying to ship.

**Budget.** Target ≤3 minutes wall-clock for gate 2 on the reference machine. If it exceeds 5 minutes, gate 2 demotes to pre-release/CI-only and local `wb lock` runs gates 1, 3, 4, 5, 6, 7, 8 with an explicit `gate2: waived-local` entry in `gate-report.json` — a recorded waiver, never a silent skip.

**LOCK is non-mutating.** It writes only `dist/published/` and `.wb/locks/<iso>/` (the snapshot set listed in §12.2), then `git tag wb-lock/<n>`. **The editable project is untouched, so UNLOCK is nothing more than restarting the design server — there is no unlock transformation to get wrong.**

**The one thing that claim does not cover** is hand-edits made *inside* `dist/published/`. LOCK regenerates that tree wholesale, so those edits are overwritten by the next lock no matter what unlock displays. That is handled explicitly in §12.6 row 6 rather than hidden behind the "nothing to get wrong" headline — because a reader who trusts the headline is exactly the reader who loses work.

**Going back to an older lock** is `git checkout wb-lock/<n> -- pages/ site.json system.lock.json content.json` (documents **and the system lock**, never `dist/`). Restoring the docs without the system lock is what manufactures the skew case in §12.16, so the lock file travels with them. If the library files on disk no longer hash-match the restored `system.lock.json`, the restore stops and prints the `wb migrate` command instead of opening a half-resolved project. **§19 A56 is amended accordingly** (it currently names only `pages/ site.json`).

### 12.6 State-loss ledger (what LOCK/UNLOCK must explicitly handle)

The job of this ledger is to make every loss either impossible or **explicitly named**. A row that names a loss and then claims a handling which does not actually preserve anything is worse than no row, so row 6 is rewritten below.

| # | Lost / breaks | Handling |
|---|---|---|
| 1 | Undo/redo history (in-memory) | Persist as `history.jsonl`, the capped append-only op log (§12.9a). **This, not git, is the cross-session undo answer** — see the commit-cadence reconciliation in §12.9c |
| 2 | Selection and scroll position | Persist in `.wb/session-ui.json` (also the active breakpoint key, so reopening does not silently drop the user back to `base`) |
| 3 | Per-breakpoint override provenance if flattened into final CSS | LOCK is a re-render from the doc, so provenance lives in the doc (key presence per §12.3) and is never flattened away |
| 4 | Free-position pixel baselines (the viewport they were authored at) | Anchored-offset stores percentages/`clamp()`, so there is no pixel baseline to lose |
| 5 | Placeholder flags on unfilled slots | Placeholders are a **typed state that blocks LOCK** |
| 6 | Hand-edits to files inside the exported tree `dist/published/` | **Unrecoverable by design, and now said plainly.** `dist/published/` is regenerated wholesale by every LOCK; the restore path is documents-only; `wb extract-override` lifts fragments from `src/generated/**`, not from `dist/`. Three mitigations, none of which is "we keep the edit automatically": (a) every emitted file carries the §15 banner *"generated — do not hand-edit; run /website-builder unlock"*; (b) `lock-manifest.json` records a SHA-256 per emitted file, and both **unlock and the next LOCK** diff the tree — at LOCK it is a **blocking prompt** (*"N files in dist/published were hand-edited and will be overwritten — review / discard / abort"*), not a passive display; (c) `wb extract-override --from-dist <file> [nodeId]` best-effort re-homes a dist-side fragment into `src/overrides/<nodeId>.astro` so the edit becomes legal and permanent. **(c) is best-effort and explicitly fallible** — a dist file is post-bundle output, so the mapping back to a node can be ambiguous or absent, in which case the tool refuses rather than guessing, and the honest answer is "re-make the edit in design mode" |
| 7 | Editor scaffolding leaking into the shipped site | Killed by re-render + purity gates 1–8 (§12.5) |
| 8 | Rich text pasted with `<span style=…>` and `<b>` from the source app | `contenteditable="plaintext-only"`; content stored as plain strings |
| 9 | Absolute `http://localhost:4321/...` URLs baked at design time | Post-ingest and pre-lint pass strips absolute local URLs; **enforced at lock by gate 7**, which is where it actually becomes non-optional |
| 10 | Variant/component references invalidated by a Step-5 regeneration or a new direction | **Not silently dropped.** §12.16's resolution policy: unknown component = hard fail with a named report; unknown variant = canonical-variant fallback carrying a per-node `variantMigrated` flag that is visible in the editor and **blocks LOCK until acknowledged** (gate 6) |
| 11 | Slot content orphaned when a new variant removes a slot | Moved to `node.orphaned` and surfaced in the editor. **Never deleted by a migration** — a migration may relocate content, never destroy it (§12.16) |
| 12 | Prop values orphaned when a prop is renamed or removed between system versions | Applied through the imported system's migration map if it ships one; otherwise reset to the variant default and flagged per node, same acknowledgement path as row 10 |
| 13 | Overrides (`src/overrides/<nodeId>.astro`) whose node no longer exists, or whose component changed shape | `wb doctor` reports orphan overrides; the file is **never auto-deleted** (it is human-owned per §12.7). LOCK warns; it does not block, because a stale override that nothing references cannot ship |
| 14 | Assets referenced by a doc but absent from `assets/manifest.json` | Hard fail at generate time (the manifest is the allowlist, §12.2) — the failure is loud at design time rather than a 404 at publish time |
| 15 | Doc changes made by an out-of-band writer (Claude via Bash, a text editor) after the editor loaded the file | Detected by the `.wb/doc-hashes.json` reconciliation of §12.10 and surfaced as a conflict with both versions retained; **never silently overwritten in either direction** |

### 12.7 Ownership zones and conflict handling

Copy Plasmic's owned/managed split verbatim. Plasmic emits two files per component: `plasmic/PlasmicButton.tsx` is *"owned by Plasmic, and shouldn't be edited by you. As you iterate … these files will be updated when you run plasmic sync"*; `Button.tsx` is the wrapper, for which Plasmic *"generates an initial scaffold"* and *"never touches it again."* **[V — docs.plasmic.app/learn/codegen-components, direct quotes]** This is the mechanism that makes a codegen product a tool rather than a toy.

| Zone | Paths | Writer |
|---|---|---|
| **Machine-owned** (regenerated wholesale) | `src/generated/**`, `src/styles/tokens.css` | The generator only |
| **Human/agent-owned** (never written after scaffold) | `src/pages/*.astro` thin wrappers, `src/overrides/**`, `src/lib/**` | Claude and the user |
| **Doc-owned** | `pages/*.doc.json`, `content.json`, `site.json`, `assets/manifest.json`, `provenance.json`, `history.jsonl` | The editor process only — **and Claude reaches them through `wb op`, never through a file write** |
| **Snapshot / build output** (never hand-edited, never restored from) | `dist/published/**`, `.wb/locks/**` | `wb lock` only |
| **Import record** (append/replace by the importer) | `inbound/**`, `system.lock.json`, `migration-report.json` | The Step-3 importer and `wb migrate` only |

**Claude needs a legal write path, or the guard will be routed around.** The doc-owned row above forbids Claude from writing those files directly, which is correct — but forbidding without providing is how guards get bypassed. `wb op '<typed op JSON>'` is the sanctioned CLI: it posts the same typed semantic op the browser posts (§12.13), through the same server, so it inherits validation, the op log, optimistic concurrency and the SSE push. **The skill's own instructions must state this in the imperative** ("to change a page, run `wb op`; never write `pages/*.doc.json`"), because an instruction the agent follows is cheaper and more reliable than a guard it can accidentally evade.

**Enforcement, in order of how much it is actually worth:**

1. **Reconciliation (authoritative).** `.wb/doc-hashes.json` + an `fs.watch` on the doc-owned set. Any doc-owned file whose on-disk hash differs from the journal without a corresponding server-issued write is treated as an out-of-band mutation: the editor refuses to save over it, shows both versions, and offers reload / keep-mine / merge-by-hand. **This is the only mechanism that holds regardless of *how* the write happened** — Write, Edit, Bash heredoc, `sed -i`, another editor, a script — and it is therefore the normative guarantee. Everything below is defence in depth.
2. **PreToolUse hook, extended to Bash.** Blocks `Write`/`Edit` on doc-owned paths, **and additionally scans `Bash` command text** for those paths (redirection targets, heredoc targets, `cp`/`mv`/`install` destinations, `sed -i`, `tee`, `python -c`/`node -e` payloads). **Stated honestly: a command-text scan is a heuristic and is defeatable** by variable indirection, `cd` plus a relative path, base64, or any interpreter one-liner that constructs the path at runtime. §14.1 already records that "Bash heredoc writes are not blocked" for subagents, and Bash is in the skill's own allowed-tools list — so this hook narrows the hole, it does not close it. Mechanism 1 is what closes it.
3. **File mode while the editor holds the lock.** `chmod 0444` on doc-owned files whenever `.wb/editor.lock` is live, restored on release. This makes a casual `>` redirection fail immediately with a clear error. **Also stated honestly: the Claude process and the editor process run as the same uid, so the owner can `chmod` back.** This is a speed bump against accidents, not a security boundary; a separate uid or a container would be required for that, and neither is in scope for a local ACOS skill (**O34**).
4. **`.gitattributes`** marks `src/generated/** linguist-generated=true -diff` (GitHub collapses those diffs; `-diff` also hides them from the CLI) **[V — github/linguist behaviour]**, so generated churn cannot drown the human-owned changes a reviewer needs to see.
5. **Pre-commit hook** rejects a commit touching `src/generated/**` without a corresponding doc change, and rejects any doc-owned file that is not in the canonical serialisation of §12.9.
6. **The generated banner** names the file to edit instead.

**When an illegal edit happens anyway, do not attempt a three-way merge.** Run `wb extract-override <nodeId>`, which lifts the current generated fragment into `src/overrides/<nodeId>.astro`, sets `node.override` in the doc, and re-points the generator to emit `<Override/>`. That turns an illegal edit into a legal, permanently-surviving one. This is Plasmic's split applied at node granularity. The `--from-dist` form (§12.6 row 6) is the same idea applied to the exported tree, with the ambiguity caveat stated there.

**Overrides accumulate, and that is a real cost.** Each `src/overrides/<nodeId>.astro` is a piece of the page that no longer responds to variant swaps or token changes, so a heavily-overridden page quietly stops being a design-system site. The editor shows a visible override count, and `wb doctor` uses **stated starting numbers, tunable in `site.json`**:

| Signal | Threshold (v1 default) | Behaviour |
|---|---|---|
| Overrides per page | **≥5** | `wb doctor` warns; the editor's override counter turns amber |
| Overrides per page | **≥15** | `wb doctor` escalates to a red finding; LOCK still proceeds but `gate-report.json` records the count so it is visible in the evidence bundle |
| Overrides per site | **≥40** | `wb doctor` prints the "this is no longer a design-system site" finding naming the top offending pages |
| Overridden share of a page's nodes | **≥25%** | Same escalation as ≥15, whichever fires first |

**[I — these numbers are a stated starting point, not a measured or cited figure. They exist so the rule is implementable and testable; expect to tune them after the first real site.]**

### 12.8 Determinism and drift control

Generation must be a **pure function of `(doc, system.lock.json, generator version)`**. Every generated file carries a header banner with `@generated`, `doc-sha256`, `system-lock-sha256`, `generator-version` — and **no timestamp** (a timestamp in the file body destroys determinism and pollutes every diff; put run metadata in a sidecar).

Two checks fall out:

- `wb verify` regenerates into a temp dir and `diff -r`s the **text** files against `src/generated/**`, and **hash-compares binary assets separately** (see hazard 5). **Empty diff proves both determinism and that nobody hand-edited machine-owned files.** Run on editor start, before LOCK (gate 8), and in CI.
- On editor start, a hash mismatch means someone hand-edited generated output.

**Determinism hazards to design out up front:**

| # | Hazard | Design-out |
|---|---|---|
| 1 | Map/object iteration order | Sort keys with a fixed comparator before emission |
| 2 | Absolute paths in output | Relative only — enforced at lock by gate 7 |
| 3 | Locale-dependent sorting | Fixed collator (`Intl.Collator('en', {sensitivity:'variant'})`) or raw code-unit sort; `LC_ALL=C` in build environments |
| 4 | Random ids | Derive node ids from a ULID stored in the doc, never regenerate |
| 5 | **Binary asset pipeline** — the auto-recompression on drop (§13.3, §19 A35) and any generated sprite/derivative | **Pin the exact encoder and its settings**, recorded per asset in `assets/manifest.json` as `{encoder, encoderVersion, settingsHash, outputSha256}`. `wb verify` does **not** re-encode on every run: it hash-compares the on-disk derivative against `outputSha256`, and only re-encodes when the settings hash or the source hash changed. **This is deliberate** — image encoders are not guaranteed bit-stable across versions or platforms, so re-encoding-and-diffing would produce exactly the false positives this subsection warns about. An encoder-version change is surfaced as an explicit "assets need re-derivation" action, not as a mystery diff |
| 6 | **Non-deterministic content sources** — anything that reads the clock, the network, `Math.random`, `process.env`, or the filesystem outside the doc + library at generate time | Forbidden in generated components; the §12.14 AST walk flags them at import time, and the generator runs with a frozen clock (`SOURCE_DATE_EPOCH`) so an accidental one is caught rather than absorbed |

**This is the load-bearing assumption of the whole drift story.** Any nondeterminism makes `wb verify` produce false positives, users learn to ignore it, and the guarantee silently dies. Note that hazards 1–4 and 6 are properties of **our generator**, which we control. Bundler-level reproducibility — which purity gate 2 depends on — is **not** in our control and is the open question **O33** in §12.5.

### 12.9 History: op log + snapshots + git, and NOT a CRDT

Three layers with distinct jobs:

| Layer | Mechanism | Job |
|---|---|---|
| **a** | `history.jsonl`, append-only, one line per user action with `patch` and `inverse` as RFC 6902 JSON Patch | Undo = apply `inverse`; redo = apply `patch`. Plain diffable text; doubles as the agent-vs-human audit trail. **This is the cross-session undo answer** — it survives a browser reload and a machine restart, because it is on disk |
| **b** | Atomic doc writes — write temp then `fs.rename`, debounced ~300ms, followed by a `.wb/doc-hashes.json` journal update in the same critical section | A `kill -9` leaves either the pre-op or post-op file, never a truncated one. The journal update is what makes §12.10's reconciliation trustworthy |
| **c** | Git commits at **milestones only** (LOCK, variant-set import, `wb migrate`, named checkpoint, session end), `git tag wb-lock/<n>` per lock | Durability at meaningful boundaries, and history stays readable |

**Commit-cadence reconciliation (the two policies are now one).** An earlier draft stated milestone-only commits here and "every save is a commit … auto-commit on save to a `design/` branch, squash on lock" in §12.10 — two incompatible policies for the same file, given that §13.1 fires save on every drop/mouseup. **Milestone-only wins**, for three reasons: a commit per drag produces thousands of commits per session and makes `git log` useless exactly when a user needs it; the durability job is already done by layers (a) and (b), which are cheaper and survive a crash mid-drag; and squash-on-lock would rewrite a branch that the `wb-lock/<n>` tags point into. §12.10's table row is rewritten accordingly.

**If per-save git durability is still wanted**, it is an **opt-in** `wb autosave --git` that updates a detached ref `refs/wb/autosave` (not a branch, never merged, dropped at LOCK), coalesced to at most one write every 30 s. Off by default. **[I — inference; no source establishes a required cadence. The reconciliation is a design decision made here to remove a contradiction, and §17's R6 mitigation line, which currently reads "every-save-is-a-commit", must be updated to "op log + atomic writes + reconciliation" so the two sections agree.]**

**The doc serialisation contract (normative, and asserted).** Because layer (c) only commits at milestones, a milestone diff is large — which makes readability *more* important, not less.

- UTF-8, LF line endings, trailing newline, no BOM.
- **Stable key order**: a fixed key sequence per node type (`id, component, variant, region, layout, props, slots, text, override, locked, notes, variantMigrated, orphaned`), then any unknown keys sorted lexicographically so a forward-compatible field never reorders the file.
- **2-space indent, one array element per line** — never a collapsed array, so a reordered section shows as moved lines rather than one rewritten line.
- Numbers emitted in their shortest round-trip form; no `-0`; no exponent notation.
- Booleans and `null` explicit; **omit absent optional keys entirely** rather than writing `null`, so §12.3's key-presence test for "overridden here" stays valid.
- Non-ASCII characters written literally, not `\u`-escaped.

`wb verify` re-serialises every doc-owned JSON file and requires a zero diff (purity gate 8, and the pre-commit hook of §12.7). This is what stops a hand-edit, a different formatter, or a future library upgrade from silently reformatting the file and producing a 4000-line diff that hides the one real change.

**Reject CRDTs (Yjs, Automerge, Loro).** There is one human plus a sequential agent; concurrent multi-writer merge buys nothing and costs an opaque binary doc git cannot diff. Use a single-writer `.wb/editor.lock` (pid + mtime heartbeat) and route agent writes through the inbox instead.

### 12.10 Two writers, one lock

**Failure scenario, near-certain (this is §17's R6):** the editor is open with unsaved drags in memory. The user, in the terminal, asks Claude "make the features section tighter." Claude rewrites the section and, if it touches layout, writes the doc. The browser holds stale state; the user hits Save; the browser clobbers Claude's change — or Claude clobbers the drags on the next reload. **Either way the loser's work vanishes silently.**

| Mitigation | Mechanism |
|---|---|
| **Single writer by file ownership** | §12.7, with `wb op` as Claude's sanctioned path so the ownership rule is followed rather than routed around |
| **Out-of-band-write reconciliation (the authoritative one)** | `.wb/doc-hashes.json` + `fs.watch`. Any doc-owned file whose hash diverges from the journal without a server-issued write raises a conflict in the editor before the next save is accepted, and the divergent on-disk version is copied to `.wb/conflicts/<iso>/` first. **This holds against Bash heredocs, `sed -i`, a second editor, and anything else** — which matters because the PreToolUse hook demonstrably cannot (§12.7 item 2, §14.1) |
| **Optimistic concurrency** | Every save carries the mtime/hash the client loaded; the server rejects a stale write with **409** and the editor shows "the file changed on disk — reload, force, or open the conflict copy" |
| **Durability across sessions** | The `history.jsonl` op log plus atomic writes (§12.9 a, b). **Not a commit per save** — see the cadence reconciliation in §12.9c. Git commits happen at milestones, and `wb autosave --git` is available opt-in |
| **Agent inbox** | Agents append intents to `.wb/inbox.jsonl`; the editor process is the single writer that validates, applies, appends to `history.jsonl` with `actor: 'agent'`, and pushes over SSE. Same typed ops as the UI, so **one code path for both**. When no editor process is running, `wb op` starts a headless one, applies, and exits — so the agent path is never blocked on a browser being open |
| **Loud degradation** | If `fs.watch` is unavailable or unreliable on the platform, the editor falls back to a hash re-check immediately before every save and on window focus, and says so in the status bar. **A silently-degraded conflict detector is the failure this whole subsection exists to prevent** |

The FruitSync precedent gives no help here: that site tree is not under version control at all (`fatal: not a git repository`) **[V]**, so there is no rollback of any kind today. **`git init` at Step 0, no exceptions.**

### 12.11 Session state on disk

```
.acos/website-builder/sessions/WB-<ts>-<slug>/
  00-interview/{answers.json, concept.md}
  01-prompt/{stage-a.md, stage-b-<id>.md, artwork.md}
  02-system/{<directionId>/…, manifest.json, import-report.json, system.lock.json}
  03-selection/{tournament-log.json, picks.json}
  04-site/{site.json, pages/*.doc.json, content.json, provenance.json,
           assets/manifest.json, migration-report.json, direction-tour-log.json}
  05-variants/
  06-custom/
  07-lock/{dist/, lock-manifest.json, gate-report.json, screenshots/,
           manifest-a.json, manifest-b.json}
  evidence/
  audit/config-snapshot.yaml
  .wb/{editor.lock, editor.token, inbox.jsonl, doc-hashes.json, session-ui.json,
       locks/<iso>/…, conflicts/<iso>/…, tmp/gate2/}
  state.json      ← {phase, step, awaiting, nextAction, port, pid, url, sessionId}
  events.jsonl
  ACTIVE          ← marker written at init, removed at close
.acos/website-builder/systems/<name>/{system.json, tokens.css, compliance-report.json, provenance}
.acos/website-builder/sessions/*/site/   ← in ACOS .gitignore, its own nested git repo
```

`.wb/tmp/**` and `.wb/conflicts/**` are in the site repo's own `.gitignore`; `.wb/locks/**` is **not** — the lock snapshots are the durability story and must be committed.

**The phase frontier is recomputed from which directories are populated and which gates passed — never from conversation memory.** The principle is stated best in the in-repo `acos-axiom-synthesis/STATE-MACHINE.md`: frontier is *"Computed purely from on-disk state, so the run is resumable by re-reading the ledger."* **[V — in-repo, line 66]** The `.current-session` pointer convention already exists at `.acos/sessions/loan-doc-finder/.current-session` **[V — verified by `ls`]**.

**`site/` must be its own git repo (or worktree), and the path must be in the ACOS `.gitignore`** — otherwise every milestone commit pollutes ACOS history and every LOCK tag collides with ACOS tags, making the version-history layer unusable within a single session.

### 12.12 Local server security — localhost is NOT a trust boundary

This is the single most under-rated risk in the product.

**CVE-2025-24010 (Vite):** *"Vite allowed any websites to send any requests to the development server and read the response due to default CORS settings and lack of validation on the Origin header for WebSocket connections,"* and the advisory states explicitly that it *"applies to users that only run the Vite dev server on the local machine and does not expose the dev server to the network."* Fixed in 6.0.9 / 5.4.12 / 4.5.6. Separately, **CVE-2025-30208** let `?raw??` bypass `server.fs.deny` for arbitrary file read (that one only affected `--host`-exposed servers — which is why ours never is). Vite's own docs warn that `server.allowedHosts: true` *"allows any website to send requests to your dev server through DNS rebinding attacks, allowing them to download your source code and content."* **[V — GHSA-vg6x-rcgg-rjx6, GHSA-x574-m823-4x7w, vite.dev/config/server-options, quotes verbatim]**

**Required posture:**

| # | Control |
|---|---|
| 1 | Bind `127.0.0.1` explicitly, **never** `0.0.0.0` |
| 2 | Validate `Origin` on **every non-GET and on the SSE/WS upgrade** against a two-entry allowlist |
| 3 | `Access-Control-Allow-Origin` set to the exact editor origin, **never `*`** |
| 4 | **A per-session bearer token** — 32 random bytes, `.wb/editor.token` mode 0600, injected into the editor page at render, sent as `Authorization` on every non-navigation request. **This is what defeats drive-by CSRF from any origin that has never seen the token** |
| 5 | Pin `vite.server.allowedHosts` to the explicit host; pin Vite ≥ 6.2.3 |
| 6 | Heartbeat from the editor page; exit after N idle minutes — **a forgotten dev server left running for days is the realistic exposure, not a targeted attack** |
| 7 | **`Host`-header validation on EVERY request, including the plain `GET /` that bootstraps the editor page.** Reject unless `Host` is exactly `127.0.0.1:<port>` or `localhost:<port>`. **This, not the bearer token, is the anti-DNS-rebinding control** — see the argument below |
| 8 | `Cross-Origin-Resource-Policy: same-origin`, `X-Content-Type-Options: nosniff`, `Cache-Control: no-store` on the bootstrap response, and a strict `Content-Security-Policy` on the editor page. Never reflect a request header into the response |

**Why the token alone does not defeat DNS rebinding, and what does.** The original text claimed the bearer token "is what actually defeats DNS rebinding," while also exempting `GET /` — the very response that carries the token — from validation. That reasoning does not hold, so it is replaced with an auditable one:

1. A **cross-origin** attacker page at `https://evil.example` can *send* a request to `http://127.0.0.1:<port>/` but **cannot read the response body** — the same-origin policy blocks the read, and control 3 (never `*`) prevents CORS from granting it. So the token is not exposed to a plain cross-origin attacker, and control 4 correctly stops drive-by CSRF: the attacker can send but cannot authenticate.
2. **DNS rebinding defeats step 1 by construction.** The attacker serves `evil.example` with a short TTL, then re-resolves it to `127.0.0.1`. The victim's browser now believes `http://evil.example:<port>/` is same-origin with the attacker's page, so **the SOP argument evaporates and the attacker can read the response** — including the token embedded in the bootstrap HTML. An `Origin` check does not help either, because the attacker's origin *is* `evil.example` on both sides.
3. **The header that does not lie is `Host`.** A rebound request still arrives with `Host: evil.example:<port>`, because that is what the browser was navigated to. Rejecting any `Host` that is not literally `127.0.0.1:<port>` or `localhost:<port>` refuses the rebound request **before** any response body exists to be read. This is the same mechanism Vite's `allowedHosts` implements, and the reason its docs name DNS rebinding explicitly.
4. Therefore the correct statement of the layered claim is: **control 7 (Host validation) defeats DNS rebinding; control 4 (bearer token) defeats drive-by CSRF and any residual same-site confusion; control 2 (Origin) defeats cross-origin state-changing requests.** Each has one job, and the bootstrap `GET /` is inside the validated surface rather than outside it.

The cost of extending validation to `GET /` is one header comparison, so there is no bootstrap complexity to trade away. **[I — the reasoning in points 1–4 is inference from the cited Vite advisory and the documented rebinding mechanism; it is not itself a quotation from a source. It is written out so it can be audited or refuted rather than trusted.]**

**In-repo gap to not copy:** `ic-server.py` binds `127.0.0.1` correctly but performs **no Origin check on `do_POST`** **[V — grep, lines 107/156/187]**, and no `Host` check anywhere.

### 12.13 The write endpoint is an arbitrary-file-write primitive unless constrained

Two rules make it safe by construction:

1. **The client never sends a file path or a file body.** It sends a **typed semantic op** (`{op: 'swap-variant', node: 'n_hero', variant: 'hero-split@3'}`) and the server derives the JSON Patch. **Raw-JSON-Patch-over-HTTP is nearly as dangerous as raw paths** because `add`/`replace` on an arbitrary pointer can rewrite `systemLock` or inject an `override` path. Validate every op against a schema **and** against the component library before applying.
2. **The server may write exactly the doc-owned set, and nothing else** — resolved with `realpath`, asserted `startsWith(sessionRoot)`, symlinks rejected, `..` segments rejected, and the resolved path re-checked *after* resolution rather than before. Generated files and `dist/` are written by the generator and `wb lock` from the doc, **never** by an HTTP handler.

**The allowlist, corrected.** The earlier three-shape list (`pages/*.doc.json`, `history.jsonl`, `.wb/**`) contradicted §12.7's zone table and §12.1, and left four **v1** features with no legal write path: per-page SEO/meta fields and the multi-page manager (page list lives in `site.json`), the asset/media manager and image auto-optimisation on drop (`assets/manifest.json`), provenance recording on every variant placement (`provenance.json`), and inline text editing when copy lives in `content.json`. A rule that v1 must violate is not an allowlist.

| Path shape | Which ops may write it | Constraints |
|---|---|---|
| `pages/*.doc.json` | All node/layout/text/slot/variant ops | Canonical serialisation (§12.9); one file per op batch |
| `content.json` | `set-text`, `set-richtext`, content-mode ops | Never touched by layout ops |
| `site.json` | `add-page`, `remove-page`, `rename-page`, `reorder-pages`, `set-page-meta`, `set-breakpoints`, `set-grid`, `set-doctor-thresholds` | **`systemLock` is not writable by any op, ever.** It is written only by the Step-3 importer and by `wb migrate`, and the op validator rejects any patch whose pointer starts `/systemLock` regardless of which op produced it |
| `assets/manifest.json` | `register-asset`, `set-asset-meta`, `set-alt-text`, `record-derivative` | Entries are append-or-update; a delete requires no live doc reference |
| `provenance.json` | `record-placement`, `record-variant-swap` | Append-only in practice |
| `history.jsonl` | Written by the server itself for every applied op | Append-only, never rewritten |
| `.wb/**` | Session/runtime state: `editor.lock`, `session-ui.json`, `doc-hashes.json`, `inbox.jsonl` (read + truncate-after-apply), `conflicts/**` | `.wb/locks/**` is **read-only** to the server; only `wb lock` writes it |

Everything not in that table is rejected. **§19 A78 is amended** from the three-shape assertion to this table, and gains two sub-assertions: (a) an op whose derived patch targets `/systemLock` is rejected with 400; (b) a request naming any path outside the table — including via symlink or `..` — is rejected with 400 and logged.

### 12.14 The Step-3 importer is an unauthenticated code-import channel

Pasting component code and tokens back from claude.ai means arbitrary code lands in `src/`, is evaluated by `astro dev`, and is bundled into the published site. Treat it as untrusted input.

A forgiving parser (fenced-block extraction, per-item) feeds a validator. **The validator is AST-based, not substring-based** — the earlier draft specified a denylist of literal tokens (`fetch(`, `eval(`, `new Function`, `process.`, …) and called it strict, which overstates what a token filter achieves. Bracket-notation property access, string concatenation, unicode escapes, template literals, and indirect eval via `[]["constructor"]["constructor"](…)()` all walk straight through a literal match.

**Validator design:**

| Layer | Mechanism |
|---|---|
| **Parse** | Astro files split with `@astrojs/compiler` into frontmatter, template and style; JS/TS parsed with a real ESTree-producing parser; CSS parsed with PostCSS. **A parse failure is a quarantine, never a pass-through** |
| **Resolve** | Walk the AST with scope tracking. Flag `CallExpression`/`NewExpression` whose callee **resolves** to a denied binding (`eval`, `Function`, `fetch`, `XMLHttpRequest`, `WebSocket`, `import()` of a non-local specifier, `require`, `process`, `child_process`, `fs`, `Worker`, `importScripts`, `navigator.sendBeacon`) — resolution, not spelling |
| **Fail closed on the undecidable** | Any computed member access on a global (`window[x]`), any dynamic import specifier, any `constructor` chain, any string that is assembled and then called, any `with`, any non-literal `srcset`/`href`/`url()` — **quarantine, do not reject-silently and do not pass.** Static analysis of adversarial JavaScript is undecidable in general; the honest posture is "anything I cannot resolve, a human looks at" |
| **Template & CSS** | Remote `<script src>`, remote `<link>`, remote `@import`, remote `url()`, inline event-handler attributes, `javascript:` URLs, `<iframe>`, `<object>`, `<embed>`, `srcdoc` — all quarantined. **Every remote origin is also a determinism and licence-evidence violation** (§12.8, Step 8), so this rule earns its keep twice |
| **Tokens** | Schema check that `tokens.json` is valid DTCG; reject unknown token types; reject values that are not literals |
| **Containment (defence in depth)** | Quarantined and newly-accepted items are first previewed in a **sandboxed iframe** (`sandbox` without `allow-same-origin`) under a strict `Content-Security-Policy` with no `connect-src`, so a first render cannot exfiltrate. The design server ships a CSP; the published site ships one too |
| **Human gate** | The quarantine list is shown as a rendered diff with the offending node highlighted, and nothing leaves quarantine without an explicit per-item accept recorded in `inbound/import-report.json` |

**Honest limit, stated rather than implied.** The paste's author is the user's own claude.ai session, so the realistic threat is a *mistake* (a copied snippet with a CDN font, a component that calls an analytics endpoint) or a *prompt-injection-induced* insertion — not a determined attacker with full control of the input. The validator is sized for that: it is a mistake-catcher and a supply-chain-tamper detector with a fail-closed quarantine, **not a sandbox escape-proof boundary.** If the threat model ever changes, the answer is process isolation, not a longer denylist.

Two secondary reasons this matters beyond security: **(a)** partial or malformed paste-backs will happen on most runs, and a hard-failing importer stalls the pipeline at paste #1, so per-item accept/reject with a "retry just these three" prompt is a **functional requirement**; **(b)** remote font/asset URLs sneaking in breaks offline determinism and the Step-8 licence evidence bundle.

### 12.15 The File System Access API is not a viable persistence path

`showDirectoryPicker()` requires a secure context (localhost qualifies) and a user gesture, but **Safari ships only the Origin Private File System (no directory picker) and Mozilla published a "harmful" position**; the documented Firefox fallback is `<input type="file">` for reads and `<a download>` for writes. A browser-writes-to-disk design would silently be Chrome-only and would still need a server fallback. **[V — MDN showDirectoryPicker, developer.chrome.com, WICG spec]** Keep it as an optional convenience (e.g. "export lock bundle to a folder"); the local server is the single persistence path.

### 12.16 Reference resolution and migration when the design system changes

`render(doc, systemLock, library)` is declared pure and total (§12.1). This subsection says what it does when a reference does not resolve — the case the rest of the PRD makes **routine**, not exceptional:

- **Step 5**, a user-named step in the authoritative vision: *"if nothing looks good, generate more variants, or a brand-new design-system prompt."* A brand-new direction invalidates **every** variant reference on **every** page.
- **Restoring an older lock** whose docs predate a library change (§12.5).
- **Cross-direction swap** (v2, §18).
- A Step-3 re-import that adds, renames or removes a variant.

`system.lock.json` guarantees the imported system cannot change *silently*. It says nothing about what happens when it changes *deliberately*, which is the whole of Step 5.

**Resolution policy (normative).** Applied at editor open, at generate, and at lock (gate 6):

| Case | Detection | Policy |
|---|---|---|
| Unknown **component** id | Not in the library index | **Hard fail.** The editor opens in a read-only "migration required" state listing every affected node and page; generate and LOCK both refuse. A missing component has no honest substitute — a placeholder here is a hole that ships |
| Known component, unknown **variant** id | Component resolves, variant does not | **Fall back to the direction's declared canonical variant**, and write `node.variantMigrated = {from, to, reason, at, auto: true}`. The editor shows a per-node badge and a review queue; **gate 6 blocks LOCK until every flag is acknowledged** (per node, or bulk-acknowledged with one confirmation that names the count) |
| Variant resolves but its **slot contract** changed (a slot was removed or renamed) | Schema diff between old and new variant | Slot content moves to `node.orphaned.<slotName>`, is surfaced in the editor, and is **never deleted by a migration**. A migration may relocate content; it may not destroy it |
| Prop removed or renamed | Schema diff, plus the imported system's optional migration map | Apply the map if present; otherwise reset to the variant default and flag per node, same acknowledgement path as the variant case |
| Unknown **motion** preset id | Not in the motion catalogue | Fall back to `motion.none`, flag, acknowledge before LOCK. Per D4 this is the same code path as a variant fallback, because motion is a prop on an art container, not a parallel subsystem |
| Unknown **token** name | Not in `tokens.json` | **Hard fail at generate time**, naming the token — a missing custom property otherwise degrades to an invalid CSS value and a silently wrong colour |
| Asset id absent from `assets/manifest.json` | Manifest lookup | **Hard fail** (the manifest is the allowlist, §12.2) |
| Doc `formatVersion` newer than the tool | `site.json` | Refuse to open, name the versions. Never best-effort-parse a future format |
| Doc `formatVersion` older than the tool | `site.json` | `wb migrate --format` applies the ordered format migrations, writes a `.wb/locks/pre-migrate-<iso>/` snapshot first |

**`wb migrate [--to <systemLockSha>] [--format]`** is the sanctioned operation:

1. Snapshot the current docs into `.wb/locks/pre-migrate-<iso>/` before touching anything.
2. Diff old vs new `system.lock.json`: components added/removed/renamed, variants added/removed/renamed, slot and prop schema changes, token additions/removals.
3. Produce a **plan** and show it before applying — counts per rule, and the full node list on request.
4. Apply as **typed ops through the same server path** (§12.13), so every change lands in `history.jsonl` with `actor: 'agent'` and is individually undoable. A migration is not a special bypass.
5. Write `migration-report.json` (§12.2) and update `systemLock` in `site.json` — the one write that no HTTP op may perform.
6. Leave the acknowledgement flags in place. **Migration proposes; the human accepts.**

> **Deviation requiring user sign-off.** The v1 policy makes a brand-new-direction regeneration (Step 5) a **reviewed** operation: every node gets a canonical-variant fallback and LOCK is blocked until the user acknowledges. If the user expects "generate a new direction and it just applies," that is a different product — it would mean accepting silent, unreviewed substitution across every page — and it is **not** what this PRD specifies. Bulk-acknowledge exists to make the review cheap (one confirmation naming the count), but the flag-and-block behaviour is deliberate. **Confirm this is what the user wants.**

> **O35 — open, requires user decision.** Whether `wb migrate` should attempt **semantic** variant matching across directions (map `hero-split@3` in direction A to the nearest `hero-split`-shaped variant in direction B by slot signature) rather than always falling back to the canonical variant. Semantic matching preserves more intent and is what makes the v2 cross-direction swap pleasant; it is also a heuristic that can confidently produce a wrong answer. **No known mitigation that removes the risk** — the honest options are (a) canonical fallback only, always reviewed (the v1 choice), or (b) slot-signature matching with the same mandatory review. Not decidable without the user.

### 12.17 Consistency register for this section

Recorded so downstream sections are updated together rather than drifting. Each item is an amendment this section's revision **creates elsewhere**, or a question it cannot close.

| Id | Item | Status |
|---|---|---|
| — | §13.4 row 27: "LOCK purity gates 1–5" → **1–8** | Amendment, mechanical |
| — | §10.1 lock-gates row: "Four automated gates" → **Eight** | Amendment, mechanical |
| — | §18 v1 bullet: "all five purity gates" → **all eight** | Amendment, mechanical |
| — | §19 A49: add the gate-7 design-time-origins grep | Amendment |
| — | §19 A56: restore command gains `system.lock.json` and `content.json` | Amendment |
| — | §19 A78: three-path rule → the §12.13 allowlist table, plus the `/systemLock` and symlink sub-assertions | Amendment |
| — | §17 R6 mitigation line: "every-save-is-a-commit" → "op log + atomic writes + hash reconciliation" | Amendment (§12.9c reconciliation) |
| **O31** | Breakpoint boundaries 991/479 paired with preview widths 768/390 — reconciliation, not a cited figure. Alternative is boundaries = preview widths. Must change in §10.1, §11.3, §11.4 and §12.3 together | Open, inference flagged |
| **O32** | No wide/`xl` override tier in v1. Adding one introduces the only upward override in the cascade | Open, requires user decision |
| **O33** | Astro/Vite build byte-reproducibility across two installs is **not established by any source consulted**. Phase-0 spike; documented fallback weakens D3's proof and needs sign-off | Open, no verified answer |
| **O34** | Same-uid processes mean file-mode enforcement is a speed bump, not a boundary. A separate uid or container is out of scope for a local ACOS skill | Open, no known mitigation in scope |
| **O35** | Semantic cross-direction variant matching vs canonical fallback in `wb migrate` | Open, requires user decision |

**New acceptance criteria created by this section** (append to §19, continuing from A90):

| Id | Criterion |
|---|---|
| A91 | A doc node with a `base` entry and no `sm` entry compiles to `grid-column: 1 / -1` inside `@media (max-width: 479px)`, and the emitted rule order is `base`, `md`, `sm` |
| A92 | A doc containing an `lg`-style upward override key is **rejected** by the doc schema validator with a message naming the desktop-down rule |
| A93 | `grep -rE 'localhost\|127\.0\.0\.1\|0\.0\.0\.0\|file://' dist/published/` returns zero matches, including inside `srcset`, inline `style`, CSS `url()` and JSON-LD (gate 7) |
| A94 | Purity gate 2 runs from a clean `git worktree` with its own `node_modules`; the live `package.json`, lockfile and `node_modules` are unmodified afterwards, and a design server running concurrently is unaffected |
| A95 | A doc-owned file written out-of-band via a Bash heredoc while the editor holds the lock is detected before the next save, the divergent version is preserved under `.wb/conflicts/`, and neither version is silently overwritten |
| A96 | A typed op whose derived JSON Patch targets `/systemLock` is rejected with 400, whichever op produced it |
| A97 | The editor's asset manager, page manager, per-page SEO fields and inline text editing each complete successfully against the §12.13 allowlist with no path outside the table written |
| A98 | Re-serialising every doc-owned JSON file produces a zero diff (canonical form, §12.9); a file with collapsed arrays or reordered keys fails the pre-commit hook and purity gate 8 |
| A99 | After importing a new direction, every node carries a `variantMigrated` flag, the editor lists them, LOCK is refused until they are acknowledged, and `migration-report.json` names every changed reference |
| A100 | A `GET /` carrying `Host: evil.example:<port>` is rejected before any response body is produced; a `GET /` with `Host: 127.0.0.1:<port>` succeeds |
| A101 | An imported component using `window["fe"+"tch"]("…")` is **quarantined** by the AST validator (it is not caught by a literal-substring filter), and a parse failure quarantines rather than passes |

---
## 13. Quality gates

### 13.1 The dividing line

Not "a11y vs performance" but **scoped arithmetic/DOM-read vs whole-document render pass**.

- **LIVE** (sub-100ms, fires on drop/mouseup — **never mid-drag, never per-frame** — scoped to the touched subtree)
- **LOCK-TIME** (seconds to tens of seconds, whole-document, batch)

`axe.run(context)` supports scoped runs natively **[V]**; Lighthouse's throttled multi-second run cannot happen per-frame **[V]**.

**LOCK wall-clock budget (new, closes a recorded gap).** "Seconds to tens of seconds" describes each individual gate, not the full 28(+)-gate LOCK run end to end, and no total budget was previously stated even though LOCK is a synchronous human-waiting moment. Stated target: **p50 ≤ 90s and p95 ≤ 180s for a representative 5-page site** on the reference hardware/network profile used elsewhere in this section (§13.5's throttling profile). This number is an **inference, not a measured or sourced figure** — no vendor benchmark was run to derive it, and it should be validated against a real prototype before being treated as a hard SLA. If the budget can't be met once gate 20 (Lighthouse, median-of-3, per page) is included at real page counts, the mitigation is: run gate 20's full median-of-3 sweep against a **representative sample** of pages (one per distinct template/layout, capped at N pages) rather than every literal page, and re-run the full per-page sweep only for pages the sample flags as different in shape. This sampling fallback is itself unverified against real multi-page sites and should be treated as a design intent, not a proven-sufficient mitigation.

### 13.2 Two WCAG criteria apply to the EDITOR ITSELF — the most product-specific accessibility fact in this PRD

**WCAG 2.2 SC 2.5.7 Dragging Movements (AA, new in 2.2):** *"All functionality that uses a dragging movement for operation can be achieved by a single pointer without dragging, unless dragging is essential."* **[V — w3.org/WAI/WCAG22/Understanding/dragging-movements.html]**

The entire Step-4 design surface **is** a dragging interface. If the only way to move a component, resize it, or reorder it is a mouse drag, **the editor itself fails AA.** The fix is concrete and cheap, and it's already in the v1 feature list: select-then-click-destination, arrow-key nudge over grid cells, `+`/`−` span steppers, and — per D2's anchor model — a "move to: left of X / above Y" menu. This is a requirement for the editor's **own** UI, separate from what the published site does.

**WCAG 2.2 SC 2.5.8 Target Size (AA):** 24×24 CSS px minimum, with four exceptions (Spacing, Equivalent, Inline, Essential). Award-style editor chrome — thin drag handles, tiny corner resize grips, dense component-bar icon rows — violates this by default. **Every editor-chrome element needs a live bounding-rect check on render, not just at lock.**

### 13.3 Live checks (in-browser, scoped)

| Check | What |
|---|---|
| Contrast recompute | WCAG 2 relative-luminance ratio (4.5:1 normal, 3:1 large, 3:1 UI) **and** APCA Lc on every touched pair. Pure arithmetic on two colours — no DOM walk, no network |
| Target size | `getBoundingClientRect()` on every interactive element touched by a drag/resize; flag <24×24 unless an exception applies |
| Scoped axe-core | color-contrast, image-alt, label, button-name, aria-required-attr, duplicate-id on the touched subtree only |
| Overflow / clipping | ResizeObserver + `scrollWidth > clientWidth` |
| Focus-not-obscured | Bounding-box intersect newly-placed sticky/fixed elements against all focusables (SC 2.4.11) |
| Reading-order vs visual-order | Walk the tabbable list, flag non-monotonic DOM-vs-rect pairs (heuristic proxy for SC 2.4.3) |
| Reduced-motion sibling presence | Confirm the item's catalog has a tagged reduced variant; auto-apply a generated fallback and flag |
| Alt-text / decorative gate | **Blocks the placement**, not just the lock |
| Motion-property lint | Non-compositor properties, out-of-band durations, missing reduced-motion query (v2) |
| Text-spacing stress clone | WCAG 1.4.12 override stylesheet on a scoped off-screen clone (v2) |
| Image auto-optimisation | On drop, with a visible undoable confirmation |
| Budget HUD | Page weight vs budget; projected LCP from `PerformanceObserver`'s live LCP-candidate entry |
| **Motion-concurrency running counter (new, closes a recorded gap)** | On every placement/removal of a motion-bearing container, recompute the live count of heavy-cost-class instances (WebGL/canvas scenes, particle/ambient layers, autoplay video loops, pinned/scrubbed sequences) and feed it into the Design Health pill so the human sees the count accumulate turn-by-turn — **not** discovers it for the first time at LOCK. Ambient/Tier-3 while under the caps in §13.4 gate 4a; escalates to a Tier-2 Design Health warning as the count approaches the cap, per §13.7's severity model |

### 13.4 The ordered lock-time checklist

Ordering follows cheapest-and-most-foundational-first: the build must succeed before anything downstream is meaningful; deterministic gates before anything requiring a render pass. The base 28 gates keep their original numbers for cross-reference stability; four gates recorded as missing by the critics are inserted as lettered sub-steps (**4a, 11a, 13a, 23a**) at the ordering position their cost class and dependency actually require, rather than renumbering the table.

| # | Gate | Threshold / pass condition |
|---|---|---|
| 1 | Build/export succeeds | Zero errors |
| 2 | `wb verify` — regenerate to temp, `diff -r` | Empty diff |
| 3 | Token/CSS lint (`stylelint-declaration-strict-value` + raw hex/px grep) | Zero raw values outside the token system |
| 4 | Six coherence lints (§7.12) | All pass; lint 6 (border-only ⇒ zero shadow tokens) is the one that catches human-visible incoherence |
| **4a** | **Motion-concurrency cap check (new, closes a recorded MAJOR gap)** | Purely structural — a count over the container inventory, no render pass needed, so it belongs this early. Caps, carried over from the prior swarm report's Lens 8 finding as an **inference pending user validation**: **max 1 WebGL/canvas scene, max 1 particle/ambient layer, max 2 autoplay video loops, max 2–3 pinned/scrubbed sequences, per page.** Rationale: motion costs are additive (draw calls, texture memory, JS tick overhead compound), so the whole-page `lhci` budget at gate 20 fails late and gives no attribution back to which container caused it. This gate fails the build with a per-container attribution list if any cap is exceeded. **Open question: the exact cap numbers are inherited from research, not independently benchmarked against this product's own render stack — treat as a starting default, not a validated ceiling, until measured against a real prototype.** |
| 5 | Full-page axe-core sweep (adds landmark-unique, region, heading-order, doc-wide duplicate-id) | **Zero critical/serious** |
| 6 | Pa11y cross-check (HTML_CodeSniffer WCAG2AA) | Second ruleset; raises coverage without claiming completeness |
| 7 | WCAG 2 + APCA contrast sweep, text **and** non-text (1.4.3, 1.4.11) | 4.5:1 / 3:1 / 3:1; APCA Lc75 body, Lc60 large-bold, Lc45 large-non-text ⁵ |
| 8 | Target-size sweep on published-site controls (2.5.8) | 24×24 CSS px, exceptions applied |
| 9 | Dragging-alternative audit for widgets built via Step 6 (2.5.7) | Every drag affordance has a documented single-pointer alternative |
| 10 | Reflow at 320 CSS px (1.4.10) + text-spacing stress (1.4.12) | No 2D scroll except exempted content (data tables, images, toolbars, maps). **Free-positioned elements get mandatory extra scrutiny** |
| 11 | Free-position breakpoint audit | Re-project at 320/390/768/1440; auto-demote anything with no narrow-viewport position; **refuse to lock on document `overflow-x` or parent-box escape** |
| **11a** | **Skip-link presence and tab-order (new, closes a recorded BLOCKING gap — WCAG 2.4.1 Bypass Blocks, Level A)** | Every published page has a working "skip to main content" link, present in the DOM and **first in tab order**, that jumps focus past repeated navigation/ribbon chrome into the main content region. Pass condition: skip link exists, is keyboard-reachable as the very first `Tab` stop, and moving focus through it lands inside `<main>` (or the equivalent landmark). **This requires the skip link to exist as a real, selectable v1 component** — it was previously absent from both the gate list and the component inventory. Recommended default: **2 variants** (visible-on-focus text link; icon+text compact variant for dense ribbon designs), consistent with this PRD's general pattern of offering a small number of comparable variants rather than one fixed implementation. **Cross-reference note (requires coordination outside this section):** the v1 component inventory (§8/§18) needs an explicit skip-link entry with this variant count; this section defines the gate that enforces it, but does not itself own the component catalog. Also requires the editor-chrome z-index ladder (§11/§12) to reserve a band **above** skip-link so the purity claim in §12.5 stays provable — flagged here, owned there. |
| 12 | Playwright keyboard tab-walk (2.4.3, 2.4.7, 2.4.11) | Focus order matches visual order; no traps; ring visible at every stop (≥3:1 against adjacent, non-zero outline); nothing obscured. **Runs after 11a so a missing skip link is caught by its own dedicated gate rather than silently passing this walk** — a missing skip link is not a keyboard trap and this gate alone will not flag its absence |
| 13 | Reduced-motion render diff | **Must differ where motion exists AND still look designed** |
| **13a** | **Pause/Stop/Hide affordance audit (new, closes a recorded BLOCKING gap — WCAG 2.2.2, Level A)** | Every marquee, ticker, ambient background-motion layer, or particle layer that moves continuously for more than 5 seconds and runs alongside other content must have a working pause/stop/hide control. Pass condition: every container tagged with a continuous-motion cost class (the same tagging used by gate 4a) resolves a non-null **pause-affordance reference**, and that control is keyboard-operable and does what it claims. **This is a Level A criterion, not stylistic** — unlike 2.3.1 (photosensitivity, gate 14) and 2.5.4 (motion actuation, gate 15) which are conditional on specific triggers, this gate is unconditional wherever qualifying continuous motion exists, because marquee/ticker and decorative-background-layer containers are already in the v1 component set. axe-core does not reliably catch this criterion, so it cannot be folded into gate 5. **Cross-reference note (requires coordination outside this section):** the container contract (§9 motion spec) needs a required `pauseAffordanceRef` field, parallel to its existing trigger and reduced-motion-variant-ref fields, so an unpausable marquee is **structurally unbuildable** rather than merely caught late at LOCK. This section defines the enforcing gate; the schema change is owned by §9 and is flagged here as an open coordination item, not fabricated as already done. |
| 14 | Photosensitivity scan (2.3.1) — **conditional** on strobe/glitch-tagged assets | ≤3 flashes/sec above the size/contrast threshold. Trace Center PEAT-equivalent frame analysis |
| 15 | Motion-actuation check (2.5.4) — **conditional** on device-orientation-driven assets | UI alternative exists and motion-triggering is disableable |
| 16 | Responsive preflight (overlap, overflow, fixed heights, free-position counts, no-mobile-plan blocks) at 320/390/768/1280/1440 | Zero blocking findings. **320 is added below the prior report's capture matrix because that is where text-reflow blowouts actually appear** |
| 17 | Long-string reflow fuzz (40-char unbroken token at 320px) | No overflow |
| 18 | 200% zoom reflow | No horizontal scroll, no content loss |
| 19 | Pseudolocalisation (+35% string expansion) | No overflow or truncation |
| 20 | `lhci` performance budget — median-of-3, mobile, simulated Slow-4G (1.6 Mbps down / 750 Kbps up / 150ms RTT, Lighthouse's documented default) + 4× CPU | **LCP ≤2.5s, CLS ≤0.1** (internal stretch 0.05), **INP ≤200ms** (or TBT ≤600ms floor / 300ms aspirational as proxy), **pre-LCP transfer ≤1.5–2MB** (not total page weight). **This is the canonical threshold statement for this product; §19's acceptance criteria A66/A67 must be read as subordinate to it.** A recorded gap found A66 omitting INP entirely and A67 stating a flat ≤2MB instead of the ≤1.5–2MB range used here — that is a **cross-section inconsistency this subagent cannot fix directly** (A66/A67 live outside §13's file). Flagged as an **open item requiring a §19 edit**: add INP (or the TBT proxy) to A66, and reconcile A67's flat 2MB against this gate's 1.5–2MB range so only one number survives. |
| 21 | Font-loading audit | `font-display: swap` on every `@font-face`; preload only the committed 2–3 families; **blocks a 4th family sneaking in via a late component swap**. **Extended (closes a recorded MAJOR gap): every `@font-face` must also ship a metric-matched local fallback** — `size-adjust`, `ascent-override`, `descent-override`, and `line-gap-override` computed from the real, selected font binary's own metrics, not guessed or copied from a generic system-font table. This computation can only happen **after** the human's typeface pick is final, because it needs the actual font file — the claude.ai design-system generation step cannot produce it. Framed against D1: this is a **derived value**, computed from the chosen direction/typeface rather than picked independently, so it belongs in the same "computed, not picked" family as spacing/radius/shadow scales — not a new kind of decision. Gate 21 fails if any committed `@font-face` lacks a matching local-fallback declaration, or if CLS attributable to font-swap (measured via a layout-shift-source breakdown, not just the aggregate CLS number in gate 20) is not ~0. **Cross-reference note (requires coordination outside this section):** §7/§8's token taxonomy should list "font fallback metrics" explicitly as a derived, non-pickable token family; this section only defines the gate that enforces it once §7/§8 names it. |
| 22 | SEO / structured-data validation | §13.6 |
| 23 | Broken-link + console-error sweep, HTTPS/mixed-content check | Zero |
| **23a** | **Asset-reference resolution (new, closes a recorded MAJOR gap)** | Walk every `url()`, `font-family`, SVG `id` reference, and asset path in the **built output** and assert each one resolves to (a) an entry in `assets/manifest.json` and (b) an actual file on disk. Pass condition: **zero dangling references, zero references to a remote host** (the whole point of the exported, self-contained static site in D3). This closes a distinct failure class from gate 26: licence-manifest completeness (gate 26) confirms every *recorded* asset carries a licence; it does not confirm every *referenced* asset actually exists. Without this gate, a hallucinated or stale asset path (the class of failure documented elsewhere in this research as the "Scale AI lesson") ships as a silently broken image or missing font with no error anywhere in the pipeline. Placed here, between the link/console sweep (23) and the no-JS check (24), because it is deterministic and file-system-local — cheaper than gate 24's rendered crawler view, and logically a precondition for it (no point checking the no-JS render if assets it depends on are already known to be missing). |
| 24 | No-JS render check | Content visible, nav usable, forms submittable. **Also the crawler's view** |
| 25 | Anti-slop advisory pass | **Non-blocking, logged** — see §13.7, §13.8 |
| 26 | Asset licence-manifest completeness | Every font and image has a recorded licence class; commercial foundry faces emit a **pre-launch blocker** |
| 27 | LOCK purity gates 1–5 (§12.5) | All pass |
| 28 | Evidence bundle assembled | §15.6 |

**Total gate count note:** the checklist is now 28 base gates plus 4 lettered insertions (4a, 11a, 13a, 23a) — 32 checks in total. This is reflected in the LOCK wall-clock budget in §13.1, which was sized with these additions in mind rather than against the original 28.

### 13.5 Core Web Vitals as of 2026

| Metric | Good | Poor | Note |
|---|---|---|---|
| LCP | ≤2.5s | >4.0s | |
| CLS | ≤0.1 | >0.25 | Internal stretch target 0.05 ⁶ |
| INP | ≤200ms | >500ms | **Replaced FID in March 2024.** Now the most commonly failed vital (~43% of sites) — meaning main-thread cost from motion is a live risk, not theoretical |

Only ~43% of mobile origins and ~54% of desktop origins pass all three. **[V — web.dev/corewebvitals, 75th-percentile methodology; HTTP Archive Web Almanac 2024 pass rates]**

**A dragged-in unoptimised photo blows LCP single-handedly.** A modern phone shoots 4032×3024 at 2–5MB. Under Lighthouse's documented Slow-4G profile that is roughly **10–25 seconds of transfer alone** — instantly "poor." Since the product is explicitly about a human freely swapping in artwork, this is the **expected common path, not a corner case**. The fix belongs at **drop time**, not lock time. **[V — thresholds and throttling profile; file-size arithmetic is inference]**

### 13.6 SEO / structured-data gate (all mechanically verifiable)

Unique `<title>` per page; meta description 50–160 chars; canonical URL; Open Graph + Twitter Card including an image; `<html lang>` matching the interview language; **single `<h1>` with no skipped heading levels** (an accessibility overlap — screen-reader navigation depends on it); 100% image alt coverage; `robots.txt` + `sitemap.xml` generated from the page tree; **JSON-LD matched to the site-type answer** (Organization/WebSite for marketing, VideoGame for game promo, WebApplication for app shell, FAQPage/BreadcrumbList where those sections exist) validated against schema.org.

### 13.7 Severity tiers — what blocks what

| Tier | Blocks | Examples | Surfacing |
|---|---|---|---|
| **0** | The individual placement/edit from completing | Contrast <3:1 on placed text; target <24px with no valid exception; missing alt/decorative choice on a new image; duplicate ARIA id | Inline, immediate |
| **1** | LOCK only — never interrupts live editing | Full-page axe critical/serious; `lhci` budget miss beyond the floor; 320px reflow breakage; missing required structured-data fields; unresolved asset-licence gap; **missing skip link (11a); missing pause/stop/hide affordance on qualifying motion (13a); dangling asset reference (23a); motion-concurrency cap exceeded (4a)** | The gate report |
| **2** | Nothing — advisory, dismissible | APCA good-but-not-great; non-optimal image format; duration slightly out of band; **the anti-slop advisory**; **motion-variant homogeneity signal (§13.8) — using many distinct motion "kinds" from the catalog on one site**; **motion-concurrency count approaching (but not yet exceeding) a 4a cap, surfaced early via the live counter in §13.3** | Batched into the Design Health pill, **never a toast stream** |
| **3** | Nothing — silent telemetry | Minor spacing deviations under free-position; motion-library usage stats | End-of-session digest |

**Mechanics:** debounce live checks to fire on drop/mouseup (never mid-drag, never per-frame); collapse repeated violations of the same rule into one counted badge; gate all Tier-2 surfacing through the single Design Health pill.

**Ambient badges beat blocking dialogs during editing; hard gates belong only at LOCK.** Most problems are cheaply detectable without a model in the loop, and a non-designer will not tolerate hard blocks mid-edit.

### 13.8 The anti-slop lint changes role (argued both ways, resolved)

**For keeping it strict:** the human only chooses a *direction* among ~10; the editor still auto-places components from that direction before the human touches anything, and the claude.ai-side generation is itself subject to the same distributional-median pressure the prior report documented (Tailwind's 2019 indigo-500 default propagating into "every AI interface is purple"). An unlinted generation can hand the human a pre-homogenised menu where every "direction" still routes through the same three icon-card layouts.

**Against:** a human who saw 10 directions and deliberately picked the purple gradient one is exercising the exact taste-agency this product exists to enable. Mechanically blocking `bg-indigo-500` after a real choice contradicts the premise, and several "tells" (icon-topped 3-col grids, rounded cards) are legitimate patterns for specific content.

**Resolution:** demote to a **Tier-2 advisory at the human-edit layer** with a permanent per-element dismiss, and keep it as a **hard gate only upstream** — linting the claude.ai-generated design-system JSON **before the human ever sees the menu of choices**. The upstream gate is load-bearing, not optional, once the downstream gate is softened.

The 16 machine-detectable tells: purple-to-blue gradients (Tailwind blue-600/purple-500 defaults), Inter everywhere, uniform 16px radii + 24px padding, three-card layouts with tiny icons, badge-above-H1 heroes, serif-italic accents, generic stat banners, low-contrast dark mode, glassmorphism. Analysis of 1,590 Show HN pages: 22% heavy slop, 32% mild, 46% clean; ~75% of commercial pages launched Q1 2026 carry at least one strong signature. **[V — 925studios analysis, Hallmark's 57 detection gates, Developers Digest cataloguing]**

**Motion-consistency signal (new, closes a recorded MAJOR gap).** The static-visual anti-slop lint above has a motion-side blind spot the upstream gate structurally cannot see: it lints the claude.ai-generated design-system JSON *before* the human sees the menu, but the catalog is deliberately broad (D1's "10 variants per swappable component on demand" extends to motion — a component may offer, say, 6–10 scroll-reveal variants). Catalog **breadth** is intentional and good; deployment **restraint** is a separate concern the upstream gate never touches, because mixing many distinct motion "kinds" happens downstream, at the moment a human freely swaps components via the component bar — exactly the frictionless action this product is built around. A site that uses four different section-reveal styles, two different hover-treatment families, and a bespoke cursor animation can pass every static anti-slop tell and still read as visually undisciplined. Resolution, consistent with §13.7's existing severity model: a **Tier-2 Design Health entry**, non-blocking, one-click dismiss, that counts distinct motion "kinds" in active use per site and surfaces a soft warning at **3 or more distinct variants of the same kind** (e.g., 3+ different scroll-reveal treatments) with the framing "sites read as more designed with 1–2." The threshold of 3 is carried over from the prior research as a **reasonable-sounding default, not independently validated against user testing** — treat it as a starting point subject to revision once real usage data exists.

### 13.9 Never claim certification

Deque's own Accessibility Coverage Report (13,000+ pages/page-states, ~300,000 issues) found axe-based automated testing catches **57.38%** of real accessibility issues **[V]**. Running axe + Pa11y + Lighthouse + all the live checks raises the floor meaningfully but does not close the gap. Since this product replaces the AI *aesthetic* judge with a human but does **not** add a human *accessibility* judge, the honest claim is **"passed N automated + structural gates,"** never "WCAG 2.2 AA certified." The evidence bundle carries an explicit named gap for manual/screen-reader review.

### 13.10 APCA posture

APCA models perceived contrast more accurately for the dark, cinematic, large-type palettes award sites favour, but it is a candidate for WCAG 3.0 (still draft as of 2026) and **has no independent legal standing today**. The defensible posture is a **dual gate**: pass WCAG 2 (4.5:1 / 3:1) **and** compute APCA as a stricter internal target. Both are pure two-colour arithmetic, so both run live for free. **[V — APCA draft status, git.apcacontrast.com; the Lc75/60/45 bands are inherited from the prior swarm report and not independently re-verified — see §20.3]**

### 13.11 Open items recorded by this revision (no known mitigation beyond what's stated above, or requiring a decision/edit outside this section)

These are named explicitly rather than silently resolved, per this revision's instructions:

- **LOCK wall-clock budget (§13.1):** the p50 ≤90s / p95 ≤180s figures are an inference sized against the newly-expanded 32-gate list, not a measured result from a working prototype. **Requires validation** once a real multi-page build can be timed end to end; the sampling fallback for gate 20 (representative pages instead of every page) is likewise unproven at scale.
- **Motion-concurrency caps (gate 4a):** the specific numbers (1 WebGL scene / 1 particle layer / 2 autoplay videos / 2–3 pinned sequences) are carried over from prior research, not benchmarked against this product's actual render stack. **Requires a user decision or a benchmarking pass** before being treated as a hard ceiling rather than a working default.
- **Skip-link component ownership (gate 11a):** this section defines the enforcing gate and a recommended 2-variant default, but adding the actual component entry to the v1 inventory is owned by §8/§18, not this section. **Requires a cross-section edit** to close fully.
- **Pause/Stop/Hide schema field (gate 13a):** this section defines the enforcing gate, but the underlying `pauseAffordanceRef` field on the container contract is owned by §9's motion spec. **Requires a cross-section edit** to close fully — without it, gate 13a can only be a post-hoc catch rather than a structurally-unbuildable-otherwise guarantee.
- **Font-metric-override token family (gate 21):** this section defines the enforcing gate and grounds the requirement in D1's "derived, not picked" principle, but §7/§8's token taxonomy does not yet name "font fallback metrics" as an explicit derived family. **Requires a cross-section edit** to close fully.
- **A66/A67 reconciliation (gate 20):** this section states the canonical INP + pre-LCP-transfer thresholds, but §19's acceptance criteria A66 (missing INP) and A67 (flat ≤2MB vs. this gate's ≤1.5–2MB range) were recorded as inconsistent with it. **Requires a §19 edit**, which is out of this subagent's scope; flagged here so it is not silently lost.
- **Motion-consistency threshold (§13.8):** the "3 or more distinct variants of the same kind" trigger is a carried-over default, not independently validated. **No known mitigation beyond stating it as provisional** until real usage data exists.

---
## 14. Steps 5 and 6 — regeneration, more variants, redesign, custom components

### 14.1 More variants (deterministic, no model call)

"Generate 10 variants of this component on demand" must **not** be implemented as parallel subagents writing files. **Subagents are policy-blocked from the `Write` tool in this environment — verified twice** (MEMORY.md `reference_subagent_write_blocked`, 2026-07-07, and a live re-confirmation on 2026-07-18 whose Write call was rejected with *"Subagents should return findings as text, not write report files"*). Bash heredoc writes are not blocked. **[V — first-party]**

**Correct design:** `variants.ts` — a deterministic generator that reads the chosen direction's tokens and emits parameterised component markup. No model call, no Write block, instant, and **it guarantees the variants stay inside the direction, which is D1's whole point**.

| Operation | Behaviour |
|---|---|
| **More variants** | Next N for the slot, using the skill-supplied current highest index so numbering is **append-only** and cannot collide with previously-ingested variants |
| **More like this** | 5 deterministic neighbours of the selected (already-approved) variant, appended to the bar. **Satisfies "ask for more variants" without ever presenting a 30-item wall, and keeps new options anchored to something the user already liked** |
| **Lazy generation** | Generate on first open of a family's swap panel; cache per direction; **never pre-generate families the site does not use**. Ten variants × ~12 families is ~120 component variants per direction — eager generation stalls Step 4 |

### 14.2 Redesign the system, or part of it

| Scope | Behaviour |
|---|---|
| **Partial** (e.g. "new colour, keep the type") | Re-enter Step 2 with the current direction vector, marking which of the 26 slots are frozen and which are open. Because ≥60% of artwork is token-referencing, most art re-skins for free |
| **Full** | A new Step-2 cycle with prior identity as **negative constraint** |

**Migration is mandatory and must never silently drop a node.** A new `system.lock.json` invalidates every variant reference. The migration report: map old variant ids to new; list unmappable nodes explicitly; the user resolves each. This is logged as an explicit operation, not an implicit side effect.

**Layout survives a direction swap** — placement is stored as grid integers and token indices, so a direction change can keep placement and re-resolve tokens, *provided both directions share the same grid spec*. That is why `layout.breakpoints` and `type.viewport-endpoints` are marked `n/a` (identical across all directions) in §7.

### 14.3 Cross-direction component swaps — the unresolvable tension, made visible

The user is in Direction 3 (warm paper, editorial serif, 600ms fades, 2px radius). They see Direction 7's neon pill button in the bar and want it. **Two implementations, both bad:**

| Option | What happens | Why it fails |
|---|---|---|
| **A — Re-skin** (button references roles) | The pill inherits Direction 3's terracotta, 2px radius, slow easing | It is no longer neon, no longer a pill, no longer the thing they pointed at. The swap "worked" and produced something they didn't want; they conclude the bar is broken |
| **B — Transplant** (button carries literal values) | The site now has two accent hues, two radius scales, two motion languages | The token lint fires; and every future direction-level change leaves this button behind, permanently |

**Resolution — make the tension visible rather than pretending it is solved:**

1. The swap UI shows **both renderings side by side**, labelled *"Fitted to your direction"* and *"Kept as designed (adds 6 off-system values)."* The user picks explicitly.
2. Transplants are recorded in a visible **coherence-debt ledger** with a count.
3. A soft cap (≈3 transplants) triggers the genuinely useful move: **"You have transplanted 4 components from Direction 7 — switch the whole site to Direction 7 and transplant these 4 back the other way?"** No existing tool offers this.
4. **Do not block cross-direction swaps.** Blocking is what makes the user abandon the direction model entirely.

### 14.4 Typed slot contracts and the content orphanage

**Failure scenario:** hero variant A has `{headline, subhead, cta}`. The user swaps to variant B with `{eyebrow, headline, subhead, cta_primary, cta_secondary, stat_row[3]}`. Where does their carefully-written CTA label go? What fills the eyebrow and the three stats? **If the tool auto-fills with lorem or an AI guess, the user now has fake statistics on a live page and may not notice.** Swap back to A and the eyebrow and stats are gone permanently. Do it twice and original copy is lost with no undo path across the swaps.

**Contract:**

1. Every component declares a typed slot contract: `{name, type, cardinality, required}`.
2. The component bar **only offers variants whose contract is a superset or exact match**, and states **before** the swap: *"this variant adds 4 slots"* / *"this variant has no place for: [stat_row]"*.
3. **Content orphanage:** anything the target cannot hold moves to a visible parked panel, **never deleted**, and is auto-restored if a later swap re-introduces the slot.
4. Newly-created empty slots render as **visibly-flagged placeholders that BLOCK LOCK** until filled or deleted. **This is what prevents fake stats shipping.**
5. Slot names are part of the component contract and validated on swap.

### 14.5 Custom components (Step 6)

Three paths:

| Path | When | Mechanism |
|---|---|---|
| **Registry** | Whitelisted families: table, chart, embed, form | Deterministic generator against the direction's tokens + the dataviz sub-token set. **v1 caps custom components to this whitelist; everything else is explicitly out of scope** |
| **Agent-authored** | A genuinely novel component | `Task(general-purpose)` with a role prompt from the skill's `prompts/` dir. **Returns code as TEXT; the main thread writes it** (subagent Write is blocked). Runs the six coherence lints before acceptance |
| **Custom code block** | The signature moment, or anything the system shouldn't own | An **opaque draggable container** holding hand-written HTML/CSS/JS. The editor positions it but **never introspects** it. **This is where the quality ceiling actually lives** |

**The `component.custom-slot` registration contract is the gate that makes this safe:** a custom component enters through a door that enforces token usage, or every custom addition is an incoherence vector.

### 14.6 Charts, specifically

A chart is not one component. It decomposes into four parts:

| Part | Content |
|---|---|
| **Marks** | 12 types: line, area, bar/column, pie/donut, gauge, scatter/bubble, heatmap, funnel, radar, waterfall, treemap, map |
| **Chrome kit** | axes, gridlines, ticks, labels, legend, tooltip, annotation/reference line, zero-line — **4 treatments applied across all 12 marks, which is what makes a site's charts read as one system** |
| **Colour ramps** | categorical / sequential / diverging, **derived from the direction's OKLCH anchors, never picked**, validated colourblind-safe in both schemes |
| **Data states** | empty, loading, partial (filter returned nothing), error, single-data-point — **required in the editor** (see scope note immediately below), because charts fail more often here than in the happy path |

**Scope of "required" data states, reconciled with the static build target (closes a recorded gap):** §16.2 commits v1 to a static export that ships **zero runtime JS** to visitors, and §14.6 above commits v1 chart rendering to **build-time SVG** — i.e. charts are pre-rendered once, at publish time, from whatever data was present then. On that architecture there is no live client-side data fetch in the published site, so "loading" and "error" are not states a visitor's browser can ever actually enter — there is nothing to load and nothing to fail at runtime.

These four data states are therefore **editor-only design-time previews, not shipped runtime behaviour, in v1**:

- In design mode, the component bar lets the user preview a chart in each of the five states (empty, loading, partial, error, single-data-point) purely as **static mockup renderings**, so the direction's chart chrome is verified to hold up under bad data before it ever meets real data. This is a design-QA tool, not a live capability.
- **Only two of the five are ever shipped to the static output**, because only two can be true facts about a snapshot of data at publish time: **empty** (the dataset genuinely had zero rows) and **single-data-point** (the dataset genuinely had exactly one row). Both render as ordinary pre-rendered SVG, no different in kind from the happy-path chart.
- **"Loading" and "error" are never shipped in v1.** They exist solely as editor previews so the designer can see and approve the chart chrome's failure-state treatment in advance. If a future version (see below) adds a live data mode, these two states become real, functional, and shipped at that point — not before.
- **"Partial" (filter returned nothing) is v1-shippable only for a build-time, statically-evaluated filter** (e.g. a published page that pre-computes one fixed filtered view) — it is not the same as a visitor interactively filtering client-side, which is out of scope for v1's zero-shipped-JS static architecture and belongs with the "interactive/dashboard-grade" charts explicitly deferred to v3 below.
- This distinction — editor-preview vs shipped-runtime — must be visible in the tool itself: the state-preview control in the swap/preview bar is labelled *"Preview only — not shown to visitors"* for loading and error, so the user does not mistake a design QA aid for a live feature and is not surprised when it is absent from the published site.

shadcn/ui ships "Chart" as a single registry entry; Untitled UI splits Line & bar (8), Pie (3), Radar (3), Gauges (3), Progress circles (1) — **both under-model the chrome. [V — fetched]** The local `dataviz` skill already encodes a form heuristic, a colour formula with a runnable validator, mark specs, interaction rules, and a palette reference at `references/palette.md`. **Reuse it as the chart sub-system spec rather than reinventing.**

**Decide early: build-time SVG or a client library.** A charting library is real client JavaScript on a static marketing page, and 12 marks at v2 may require a runtime that undermines the performance gate. **v1 default: build-time SVG.** Interactive/dashboard-grade charts are v3 and pull in tooltips, brushing, legends-as-filters, and a dependency the performance budget must absorb — this is also where "loading," "error," and interactive "partial" (client-side filtering) become real, shipped, functional states rather than editor previews.

### 14.7 The signature moment is not a variant set

The prior report's Findings 2 and 6 are explicit that award-tier winners have exactly **one** bespoke signature moment, and that treating identity-carrying choices as generic catalogue picks is **the root mechanism of AI-design homogenisation** (Finding 5). If the component bar offers "10 signature-moment variants" the way it offers 10 button styles, **it mechanically reproduces the sameness problem the whole prior research effort diagnosed.**

Correct treatment: 2–3 bespoke **concept** candidates generated at Step 2 tied to the specific brand narrative, chosen and refined at Step 4, and handled thereafter through the custom code block. **A lint flags a second signature moment.** A system that lets the user pick five produces a worse site than one that lets them pick none.

---
## 15. Steps 0 and 8 — warm start, publish, licences

### 15.1 Warm start is a glob, not new infrastructure

`.acos/design-library/okoa-brand/` already holds a complete design system as five files: `design-system-spec.yaml` (883 lines; keys `meta, color, typography, spacing, grid, motion, iconography, components, patterns, data_visualization, globals, quality_control, test_runner, expressive_brand, motion_interaction, generative_parametric, naming_and_scope`), `IMPLEMENTATION.md` (250 lines), `compliance-report.json` (53 tests, per-test `{test_id, status, severity, message, evidence}`, `compliance_score: 0.92`), `source.html`, `design-influences-research.md`. **[V — verified by `ls` + reads]**

Step 0 = glob `.acos/design-library/*/design-system-spec.yaml` + `.acos/website-builder/systems/*/system.json` + the target project's `.acos/`, then offer them.

**The `compliance-report.json` shape is also the right return format for validating the Step-3 hand-carry.**

### 15.2 The user's own prior art is the closest existing thing to this product

`/Users/zee/Documents/Vibe Coding/website-design-okoa/` contains **13 named design lanes** (`ridgeline, stillness, voltage, japandi-dark/warm/sage/mauve/ocean, nordic-tech, studio-nordost, datum-tech, shibuya-light, art-of-zen`) × **3 sub-variants** (v1 institutional / v2 data-dense / v3 coffee-table) × 5 pages = **195 generated HTML files**; a distilled token bundle `_build/tokens/all_variants.json` carrying `bundle 1.2.0` and a sha256 token hash with per-variant keys `{description, display_family, google_font_display, google_font_body, google_font_weights, is_dark, colors{bg, bg_alt, bg_warm, chrome, fg1, fg2, fg_on_dark, border, accent, accent_secondary, tertiary}}`; a per-variant `README.md` acting as a **design + LICENCE REGISTER** with an asset-by-asset source/licence table; and `_build/visual-audit/iteration-1..13/` — thirteen recorded screenshot iterations. **[V — directory listing, JSON parse, `ls`]**

**This validates D1 with the user's own prior behaviour**, and the README licence register is a ready-made template for the Step-8 evidence bundle. It also shows the honest scale of a "direction": ~11 colour roles + 2 font families + a stated intent sentence.

**Mine this before finalising the direction model.**

### 15.3 The warm-start split (restated as a rule)

| Always carry forward | Never carry forward by default |
|---|---|
| Token-name schema | Hue anchors |
| Component slot contracts | Type pairings |
| Motion-primitive library | Radius / density |
| Font catalog | Motion character |
| Anti-slop deny-list | Artwork |
| Editor configuration | Grid personality |
| User-level interview answers (a11y posture, device assumptions, decision style) | Signature moment |

Prior identities are injected into Step 2 as **negative constraints** ("do not produce a direction within 30° of these hues or reusing these type pairings") unless the user answers "yes" to the sibling-site question (C4).

### 15.4 Publish

Default target: **Cloudflare Pages**, static, free bandwidth, via `wrangler pages deploy ./dist --project-name=<x>` with a scoped API token stored once. Cloudflare Pages Direct Upload has a documented CLI path.

**A one-time credential-setup step is part of the PRD.** The user's existing runbook says *"Claude cannot sign in or upload for you (your account + password). You perform steps 1–9"* **[V — DEPLOY-STEPS.md, verbatim]**.

**v1 scope commitment (gap closed — was an unresolved either/or).** An earlier scope-in line described the v1 publish deliverable as "Publish (or an explicit runbook, stated)" — an either/or phrasing that cannot be estimated or tested, and that materially changes the v1 effort line (§17-R18) and the "locked, published" exit criterion depending on which branch is taken. That ambiguity is resolved here as follows:

- **Committed v1 behaviour:** automated publish. After the one-time credential setup (the user's steps 1–9, performed once, not per-publish — creating the Cloudflare account, generating a scoped API token, and storing it locally), every subsequent LOCK-and-publish runs `wrangler pages deploy ./dist --project-name=<x>` non-interactively. This is the deliverable that counts toward the "locked, published" v1 exit criterion.
- **Explicit fallback trigger:** if, at publish time, no valid Cloudflare API token is configured (credential setup was never completed, the stored token is missing/expired/revoked, or the deploy call fails auth), the skill falls back to emitting a runbook (DEPLOY-STEPS.md-style: manual steps 1–9 plus the exact `wrangler` invocation) instead of failing silently or asking the user to debug credentials mid-flow. **This fallback path does NOT satisfy the "locked, published" exit criterion on its own** — a site left at "runbook emitted" is locked but not yet published, and the PRD must not report it as a completed publish.
- **Requires user sign-off:** the choice to make automated publish the hard v1 commitment (rather than shipping runbook-only and deferring automation to v2) is an interpretation made to close this gap, not one of the user's originally settled decisions (D1–D4). [Inference: the 8-step vision names "Publish" as step 8 alongside the evidence bundle, treating it as a completion action rather than documentation, which argues for automation being in-scope for v1. The counter-case — keeping v1 runbook-only and deferring the `wrangler` integration to v2 to reduce v1 build risk — is also defensible and was not ruled out by any prior user statement.] This choice should be confirmed with the user before it is used to size §17-R18 effort or gate the v1 exit criterion.

**It does not leave the ambiguity unresolved for the reader — the ambiguity is now a named decision with a fallback trigger, not an open branch in the scope line.**

### 15.5 Content mode (v2, but high-leverage)

**90% of month-six edits are copy changes.** A text-only editing path that needs no dev server, no design layer, and no `node_modules` — edit `content.json`, re-render statically — is what prevents the failure where a user hand-edits built HTML because launching the design surface is too much friction, and the next unlock silently reverts it.

The precedent already rotted once: `/Users/zee/fruitsync-animated-variants` is **not a git repository**, contains 30 opaque variant directories with **no manifest saying what each one was**, and its 18 Python builder scripts include a deploy note admitting *"the website tree is outside git; the builder source is preserved at `_builders/buildsite.py` (and the working copy in the job tmp)"* — the authoritative copy was in a temp directory. **[V — `git status` failure, `ls`, DEPLOY-STEPS.md]**

Prevention: `git init` at Step 0; `provenance.json`; content mode; a machine-readable *"generated — do not hand-edit; run /website-builder unlock"* banner in the exported tree; unlock diffs against the lock manifest and **refuses to overwrite hand-edits without showing them**; pin exact versions and commit the lockfile.

### 15.6 The evidence bundle

| Section | Contents |
|---|---|
| **Fonts** | Per family: foundry, licence class (OFL / CDN-only / commercial-required), file hash, source URL, attribution requirement. **Commercial foundry faces emit a pre-launch blocker rather than being embedded** |
| **Assets** | Per asset: generator, model, plan tier, licence class, prompt, alt text, source |
| **Third-party marks** | Platform badges, social icons, trust badges, map tiles — with their usage rules recorded and confirmation they were used as supplied, not redrawn |
| **Gate report** | Every lock-time gate with pass/fail, thresholds, and measured values |
| **Contrast proof table** | Every text/surface pairing with WCAG ratio and APCA Lc |
| **Screenshots** | 320/390/768/1280/1440 × light/dark × full/reduced motion |
| **Direction tour** | All directions shown, the user's pick, and their stated reason. **The legal/creative record: "we showed 10 distinct directions; the user chose #5 because [principle]; all code conforms to direction-5 spec." Proof of intentional design** |
| **Reference triangulation** | Which ≥3 references informed which direction, and how they were abstracted ("Direction 4 abstracts Swiss modernism's grid discipline, Japanese minimalism's negative space, and brutalism's weight contrast — reference pixels discarded, attributes recombined") |
| **Disclosure** | *"Automated accessibility gates passed: N. Manual and screen-reader review not performed."* |
| **Substitution log** | Every auto-fix during ingest: font swaps, contrast nudges, image recompressions |
| **Publish record** | Which publish path was actually used at LOCK time — automated `wrangler pages deploy` (with deploy URL, timestamp, Cloudflare project name) or fallback runbook emission (with the reason the fallback triggered, per §15.4) — so the evidence bundle always states plainly whether the site is actually live or only locked-and-ready-to-publish |

**The ≥3-reference rule is the legal boundary.** US copyright/trade-dress law treats look-and-feel as largely not copyrightable absent consumer confusion plus a trade-dress claim requiring integration of multiple nonfunctional elements. The safe pattern is ≥3 references from different eras/genres/cultures, abstracted to principles, recombined. With <3 the "derived from X" risk increases. **[V — UC Law Review, Michigan Studio Space guidance; agency practice at Sagmeister & Walsh, Pentagram]**

Add a post-generation check: **if a direction is >70% overlap with any single reference, regenerate against a different reference.**

---
## 16. Architecture

### 16.1 Shape: thin router skill + TS scripts + one Bun server + a browser editor

**Not** a phase-orchestrator agent pipeline. The loan-doc phase-agent architecture the prior swarm recommended exists to run an autonomous multi-hour generation loop; **this product's expensive loop is a human sitting in a browser**, which the local-server pattern already serves.

The in-repo template is `~/.claude/skills/acos-image-builder/`: 4 files — `SKILL.md` (6.9KB), `app/server.py` (105 lines, stdlib `ThreadingHTTPServer` on 127.0.0.1:8810), `app/index.html` (1,636 lines / 102KB, inline CSS + vanilla JS, no build step), `scripts/imagebuilder.sh`. Five routes: `GET /api/library`, `GET|POST /api/project`, `POST /api/export`, `POST /api/upload`, plus static serving. One global `state = {doc, layers, sel, tool, brush, color}` with `serialize()`/`restore()`, a 40-step undo stack, localStorage autosave, ⌘S → POST. **[V — full read]**

**Every structural element the Website Builder editor needs already exists there in working form.** The one thing that does not transfer is the substrate: image-builder composites raster pixels on a `<canvas>`; a website editor manipulates real DOM nodes with CSS anchors. **Reuse the shell and the server contract; do not reuse the canvas compositor.**

`acos-type-forge` proves the full loop this product needs: one server fronts a hub linking three browser tools; browser edits persist as plain JSON on disk (`glyph-edits.json`, `spacing.json`); a deterministic non-browser script (`vectorize.py`) compiles those edits into the real shipping artifact (a TTF); a separate `rename_export.py` finalizer enforces the licence rule; and a *"review IN THE BROWSER before finalizing"* gate is marked ⚠️ do-not-skip. **[V — full read of SKILL.md, 196 lines]** Map directly: `layout.json` ← browser editor; `build.ts` = `vectorize.py`; LOCK = `rename_export.py`; the licence step is precedent for Step 8.

Its SKILL.md also states the one-origin rule's reason explicitly: *"Web fonts can't load over `file://` in Chrome → always serve over localhost."*

**Status of the process topology (added in revision).** The *skill shape* above — thin router + TS scripts + a local server + a browser editor — is **settled**. The *process topology* underneath it (one origin with a proxy, versus two origins with an iframe + `postMessage`) is **NOT settled**; it is §17-O4 and is resolved by the spike described in §16.6.1. Everything §16.6 says about the two-process arrangement is therefore written as **candidate architecture**, not architecture of record. See §16.6.2 for the invariants that hold under either outcome — those are the parts an engineer may start building today.

### 16.2 Language: TypeScript on Bun

`/Users/zee/CLAUDE.md` lines 25–46 make TS/Rust the mandatory default for **all** new code; Python is allowed only for (1) editing existing Python, (2) a Python-only library, (3) extending an existing Python hook chain. **None covers a new skill's own server or editor.**

Compliance precedent: `.claude/skills/acos-reverse-cleanroom/scripts/` — 16 `.ts` files with `#!/usr/bin/env bun` shebangs, a `scripts/package.json` (`"type": "module"`, `"Run with bun (no build step)"`, one dependency: `playwright@^1.48.0`), pure decision-logic split into `lib/*.ts` so ~90% is unit-testable, and a `bun selftest.ts` harness reporting 67/67 pass. `acos-research-riffs` has 13 more `.ts`. **[V — `ls`, `head`]**

Against that: **122 `.py` files across project skills, 66 across global skills.** The estate is Python-first; **this skill must not be.** Toolchain verified present: bun 1.3.9 at `/Users/zee/.bun/bin/bun`, node v20.19.3, rustc 1.88.0. **Rust is unnecessary** — nothing here is perf-critical or needs a single binary.

**Python-gravity is a real risk** (§17-R12): the path of least resistance is copying `server.py` and violating the rule. **Mitigation: port `server.py` → `server.ts` first, before any other code, so the TS spine exists from day one.** It is ~105 lines mapping 1:1 onto `Bun.serve()`, which gives native static serving, `Bun.file`, WebSocket upgrade, and streaming with zero dependencies. **A one-hour port, not a rewrite.**

**Scope boundary of the language rule as it applies here (added in revision).** The rule governs the code *this skill authors and ships*. Two things are deliberately distinguished, because §16.6.3's fallback ladder turns on the distinction:

- **The server itself** (routes, doc model, ops, SSE, LOCK compiler, gates) — TypeScript on Bun, non-negotiable, no fallback contemplated.
- **The process-launch shim** (the ~20-line wrapper whose only job is to detach a child so it survives the harness's turn boundary) — TypeScript *by default*, but this is the one place where the only **first-party-proven** recipe is Python (§16.6). If the TS path fails re-proof, §16.6.3 defines an escalation ladder that keeps the server in TS even in the worst case. **The worst case still requires explicit user sign-off** because it invokes a language-rule exception that none of the three written exceptions cleanly covers.

### 16.3 Skill files

```
.claude/skills/acos-website-builder/          ← git-tracked, authored here
  SKILL.md                                     ← thin router, 9 phases
  scripts/
    package.json                               ← type: module, bun, no build
    server.ts                                  ← Bun.serve, fixed port 8820
    launch.ts                                  ← detached-daemon launcher (see §16.6.3 ladder)
    lock.ts                                    ← build → scrub → assert → snapshot
    import-system.ts                           ← Step-3 tolerant parser + validator
    variants.ts                                ← deterministic variant generator
    gates.ts                                   ← structured verdicts, never throws on a normal fail
    capture.ts                                 ← Chrome --headless=new wrapper
    evidence.ts                                ← Step-8 bundler
    registry.ts                                ← v2, cross-site component/direction registry
    verify.ts                                  ← regenerate-to-temp + diff -r
    doctor.ts                                  ← hash mismatches, orphaned overrides, stale locks
    extract-override.ts                        ← the sanctioned escape hatch
    install.sh                                 ← SYMLINK to ~/.claude/skills/
    selftest.ts                                ← bun selftest.ts, cleanroom's 67/67 is the bar
    probes/
      probe-turn-boundary.ts                   ← §16.6.3 O5 re-proof harness (run BEFORE v1 build)
      probe-task-availability.md               ← §16.5.1 O31 probe recipe (10 min, manual)
    lib/
      site-model.ts, render.ts, anchors.ts, cascade.ts, snap.ts, tokens.ts,
      slots.ts, coherence.ts, security.ts
  app/
    index.html                                 ← editor shell (3-pane)
    editor/
      anchors.ts, text-edit.ts, component-bar.ts, containers.ts,
      history.ts, request-more.ts, lock-preview.ts, overlay.ts, navigator.ts
  references/
    interview-bank.md                          ← §5, as a reference file not inline prose
    prompt-template.md                         ← §6
    item-inventory.md                          ← §7–§8
    gotchas.md                                 ← §16.11
  prompts/
    interview-synthesizer.md
    custom-component-author.md
```

**Installed globally via symlink**, not a copy. `acos-type-forge` exists in both the ACOS repo and `~/.claude/skills/` with byte-identical SKILL.md — **copies, not symlinks** (`ls -la` shows no symlinks anywhere in `.claude/skills/`) **[V]**. Website Builder must be usable from any project but is real code that must be version-controlled. `install.sh` creates the symlink, breaking the drift pattern rather than repeating it.

*(Revision note: `launch.ts` and `scripts/probes/` are new entries; the `gotchas.md` cross-reference was corrected from §16.6 to §16.11, which is where the gotcha table actually lives. `install.sh` remains a `.sh` because it is a two-line symlink installer that must run before any bun-based tooling is assumed present — that is an intentional, stated exception, not drift.)*

### 16.4 Invocation contract

```yaml
disable-model-invocation: true
user-invocable: true
argument-hint: "[--project <path>] [--resume] [--system <name>] [--port 8820] [--content] [--local-gen]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion
```

Precedent: `acos-reverse-cleanroom` and `acos-design-variants` both set `disable-model-invocation: true` + `user-invocable: true` + an `argument-hint` **[V — frontmatter reads]**. `Bash` is needed to launch the bun server; `AskUserQuestion` for the interview (`acos-interview` runs its Q&A in the main context precisely because it is interactive).

**Do NOT list `Task` in `allowed-tools`.** `acos-skill-maker/SKILL.md` (~line 109) states: *"Sub-agent spawning is NOT a skill-frontmatter tool. Never add `Agent` or `Task` to `allowed-tools` — the framework ignores it… set `context: fork` and `agent: architect`."* The estate contradicts itself here — `acos-reverse-cleanroom/SKILL.md` line 6 lists `Task` — **treat skill-maker as the authority and do not copy that line.** **[V — both reads]**

**Unresolved consequence of that rule — see §16.5.1.** §14.5 and §16.5 both describe `Task(general-purpose)` being invoked *mid-session, on demand*, hours into a live browser-driven editing session (e.g. the user clicks "add a custom chart"). The frontmatter rule above governs what the skill declares; it does **not**, on its own, explain whether a running session can still issue a `Task` call at an arbitrary later point. §16.5.1 states what is actually known, what is inference, and what the v1 design does so that no named feature depends on the unknown.

**Phase 0 is a mandatory Confirmation Gate.** Both `/Users/zee/CLAUDE.md` and `ACOS 3.0/CLAUDE.md` mandate it. Bake the restatement into SKILL.md rather than relying on the ambient rule, and make the interview itself the confirmation artifact: restate the brief, get an explicit yes, then write anything.

Per-project config at `.acos/config/website-builder.yaml`, mirroring `.acos/config/cleanroom.yaml`: version, default port, breakpoints, direction count (10), variants-per-component (10), artwork count (20), gate thresholds, licence policy tier, publish target — snapshotted to `audit/config-snapshot.yaml` at init.

### 16.5 Agents

**Zero new files in `.claude/agents/`.** `ACOS 3.0/CLAUDE.md` Restricted Files: *"`.claude/agents/` — Agent definitions are infrastructure. Modification requires human approval."* The estate shows agents **are** added in approval batches (12 `rc-*`, 17 `dr2-*`, 9 `ic-*`), but `acos-synthesis-protocol` explicitly avoids it by spawning `Task(general-purpose)` with role prompts in the skill's own `prompts/` dir. **[V]**

Website Builder's agentic surface is small and human-paced (interview synthesis, prompt authoring, custom-component generation), so the general-purpose route is right: zero approval events, zero roster churn.

| Prompt | Purpose | Constraint | Execution mode (v1) |
|---|---|---|---|
| `interview-synthesizer` | Raw answers → structured brief for the prompt template | Returns text; main thread writes | **Inline in the main session** by default; `Task(general-purpose)` only as a context-relief optimisation (§16.5.1) |
| `custom-component-author` | Step-6 novel components against the direction's tokens | Returns code as text; main thread writes (Write is blocked in subagents) | **Inline in the main session** by default; `Task(general-purpose)` only as a context-relief optimisation (§16.5.1) |

#### 16.5.1 How the running session actually produces agent-authored work (resolves the §16.4 / §14.5 contradiction)

**The contradiction, stated plainly.** §16.4 forbids `Task` in `allowed-tools`. §14.5 lists "Agent-authored" as the generation path for a genuinely novel component and specifies `Task(general-purpose)` with a role prompt. §16.5's own table names the same mechanism for interview synthesis. Custom components (Step 6) and interview synthesis are **named, in-scope features**, so the PRD must not leave their execution path undefined.

**What is actually known, and what is inference:**

- **Known [V — quoted]:** skill-maker states the framework *ignores* `Task` in `allowed-tools`; sub-agent spawning is configured with `context: fork` / `agent:`, which describes how a skill is *entered*, not how it spawns work later.
- **Known [V]:** `acos-synthesis-protocol` and §14.5's cited precedent both call `Task(general-purpose)` from skill prose without declaring `Task` in frontmatter — i.e. the estate's working pattern is "call it, don't declare it."
- **Inference (NOT verified):** that `allowed-tools` acts as a *ceiling* on the session's tool surface for the duration of the skill, such that declaring a list without `Task` could suppress a later `Task` call. **This is inference. The PRD does not know whether an `allowed-tools` list suppresses `Task`, and no first-party test of this exists in the estate.** Marked as **§17-O31** (new; mirror into §17.4).

**v1 design decision — remove the dependency rather than bet on the unknown.** In v1, both prompt files are used as **rubrics executed inline by the main Claude session**, not as subagent role prompts:

1. The editor appends the request to `commands.jsonl` (custom-component request, or interview-synthesis request).
2. The main session's `tail -f` loop picks it up (§16.6, zero-token wait).
3. The main session reads `prompts/custom-component-author.md`, produces the component, runs the six coherence lints (§14.5), and writes the file itself with `Write` — which it already has.

This path uses **only tools already declared** in §16.4's `allowed-tools`, so it works regardless of how O31 resolves. It costs main-session context; it does not cost a capability.

**Optimisation, gated on O31.** If the O31 probe shows a running skill session *can* issue `Task(general-purpose)`, the same two jobs may be forked to a subagent purely to protect main-session context — the subagent still returns **text**, and the main thread still writes (subagent `Write` is blocked). This is a performance change, not a functional one, so no feature depends on it.

**O31 probe (cheap, ~10 minutes, `scripts/probes/probe-task-availability.md`):** invoke a throwaway skill with an `allowed-tools` list that omits `Task`, then, after the skill has begun executing, attempt one trivial `Task(general-purpose)` call ("return the string OK"). Record whether the call is available, refused, or silently unavailable. Run before v2 planning; **not** a v1 blocker under the design above.

**Deviation flag — requires user sign-off.** If the user wants agent-authored components to *always* run as a subagent (for context economy or parallelism), the only known way to make that explicit is to add `Task` to this skill's `allowed-tools`, which **contradicts the skill-maker authority quoted in §16.4**. That is a deliberate departure from a house rule and **requires user sign-off**; it is not taken unilaterally by this PRD.

### 16.6 Local server and the harness

**FIRST-PARTY VERIFIED: long-running local servers die in this harness** — and the editor's entire premise is a long-running local server.

`acos-guided-reader-server-gotcha.md` documents this being hit and diagnosed on 2026-07-09:

| Attempt | Result |
|---|---|
| Script spawns a detached child and exits | **Orphan reaped instantly.** `server.log` 0 bytes, nothing in `lsof -iTCP -sTCP:LISTEN` |
| Bash `run_in_background: true` | Binds, curls HTTP 200, then **SIGTERM (exit 143) AT THE TURN BOUNDARY** because the harness reaps tracked background tasks |
| `setsid nohup … &` | `setsid: command not found` on macOS |
| **Python double-fork daemon** (fork → setsid → fork → exec) | **WORKS** |

**[V — first-party, four attempts with exit codes]**

**Failure scenario for this product:** the user says "open the design surface," Claude starts the server, replies, the turn ends, the server is SIGTERM'd, and the browser shows `ERR_CONNECTION_REFUSED` — **every single time, appearing intermittent because it depends on turn timing.**

**Mitigation (recipe already proven in-repo):**

1. Double-fork daemon pattern.
2. **FIXED port** (8820) so the URL is known up front — **not** gr-server's random-port design, which orphans the user's open browser tab after an eternity `/clear`.
3. Write `{port, pid, url, sessionId}` into `state.json` at boot.
4. `curl --retry 20 --retry-connrefused` to confirm bind.
5. **A SECOND curl in a SEPARATE tool call** to prove it survived the turn boundary before telling the user to open it.
6. Regenerate-if-stale on startup (gr-server served a frozen `page.html` with no freshness check and showed an old UI after the template changed).

**Language conflict to resolve:** the proven launcher is Python; the standing rule mandates TypeScript. The TS equivalent is `child_process.spawn(cmd, args, {detached: true, stdio: 'ignore'}).unref()`, which is **not proven in this harness and must be re-proven with the same curl-across-turn-boundary test** before the PRD assumes it works. See §17-O5 and §16.6.3.

#### 16.6.1 O4 is OPEN: the process topology is a candidate, not a decision

**Explicit status correction (added in revision).** Everything in §16.6.2's "two-process arrangement" was previously written in the register of a settled design — named processes, exact routes, exact responsibilities — while §17-O4 simultaneously lists *"single-origin proxy vs two-origin iframe + postMessage"* as unresolved, to be settled by *"spike both before locking the architecture."* Both cannot be true. **The correction is: O4 stands. §16.6.2 is the leading candidate, documented in detail so the spike has something concrete to test — it is not the architecture of record.**

**The two candidates:**

| | **Candidate A — two origins** | **Candidate B — single origin** |
|---|---|---|
| Shape | `astro dev` on one port renders the site; `wb-server` (Bun) on another serves the editor chrome; site in an `<iframe>`; `postMessage` with explicit `targetOrigin` | One Bun server on 8820 **proxies** `astro dev`; editor chrome and site preview are same-origin |
| Precedent | Onlook / Stackbit / Tina converged on this **[V — Onlook flow quoted below]** | The proxy is a standard pattern but **no first-party in-estate precedent was verified for this product's exact combination** (proxy + SSE + HMR passthrough) |
| Cost | CORS surface, `postMessage` protocol, `targetOrigin` discipline, two lifecycles to supervise | Proxy complexity: must pass through Astro HMR's websocket and not collide with `wb-server`'s own SSE |
| Benefit | Isolation: the site page stays pristine; editor survives an Astro restart | Zero cross-origin surface: no `postMessage` protocol at all; direct DOM access from editor chrome to preview document |
| Risk if wrong | Protocol churn between chrome and preview | HMR websocket breakage inside the proxy; harder to keep the preview DOM free of editor artifacts |

**Spike definition (must run before locking the architecture — this is the O4 answer procedure):** build the *same* two-page vertical slice on both topologies — load a page, select a node, change one text string, swap one component variant, observe HMR, take a headless screenshot of the preview only. Measure: (i) lines of code in the chrome↔preview channel; (ii) whether a preview-only screenshot is achievable without editor chrome in the frame; (iii) HMR round-trip latency; (iv) behaviour after killing and restarting `astro dev`. **Timebox: one working session per topology.** Record the result as an ADR and update this section and §17-O4 together.

**Until the spike lands, an engineer should build only the invariants in §16.6.2 — those are topology-independent.**

#### 16.6.2 Candidate architecture (Candidate A, described in full) and the topology-independent invariants

**Alternative worth spiking:** the single-origin variant — one Bun server proxying `astro dev` — collapses the CORS/postMessage surface to zero at the cost of proxy complexity. Spike both before locking the architecture (procedure in §16.6.1).

**Two-process arrangement — CANDIDATE A, pending §17-O4 (the shape Onlook, Stackbit and Tina all converged on):** Process 1 is `astro dev` on 127.0.0.1 rendering the site with the editor integration (doc write → generator rewrites `src/generated/**` → HMR reloads, ~100–300ms). Process 2 is `wb-server` (Bun) on 127.0.0.1, the single doc writer, exposing `GET /doc` (ETag), `POST /ops`, `GET /events` (SSE), `POST /variants`, `POST /lock`. The editor chrome is a parent page served by `wb-server`; the site renders in an `<iframe>`; the two talk over `postMessage` with an explicit `targetOrigin`. Onlook's published flow is the same shape: load code into a container, container serves it, *"our editor receives the preview link and displays it in an iFrame,"* then instruments the code to map elements to their place in code **[V — quoted]**.

Three concrete wins **(these are the arguments FOR Candidate A, not a statement that A has won)**: the site page stays pristine so **a screenshot of the iframe is a screenshot of the real site with no toolbar in it**; the editor survives an Astro restart without losing unsaved state; and LOCK preview is literally "point the same iframe at `dist/published`."

**Topology-independent invariants — SETTLED, safe to build now regardless of how O4 resolves:**

| Inv. | Invariant | Why it survives either topology |
|---|---|---|
| **I1** | **One writer.** `wb-server` is the only process that writes `layout.json` / `content.json` / `history.jsonl`. Everything else proposes ops. | True whether the preview is proxied or framed |
| **I2** | **The route contract**: `GET /doc` (ETag), `POST /ops`, `GET /events` (SSE), `POST /variants`, `POST /lock`, plus static serving. | Same routes; only the *origin* they are called from changes |
| **I3** | **Semantic ops, never raw file writes** from the browser. | Security posture is origin-independent |
| **I4** | **Preview isolation as a requirement, not a mechanism**: a capture of the preview must contain zero editor chrome. Candidate A gets this from the iframe; Candidate B must achieve it by rendering the preview in its own document/route. | Stated as an acceptance criterion so the spike can score it |
| **I5** | **The editor must survive a preview-process restart** without losing unsaved state (state lives in `wb-server`, not in the preview document). | Independent of topology |
| **I6** | **The dev-preview substrate is itself open (§17-O8: Astro vs plain generated HTML).** Nothing above names Astro except as the current candidate; if O8 resolves to plain HTML, "Process 1" becomes "a static file watcher + reload" and I1–I5 are unchanged. | Explicit so O8 and O4 do not get silently coupled |

**The SSE + JSONL inbox pattern is house doctrine.** `gr-server.py` (2,000+ lines) and its validated port `ic-server.py` implement stdlib `ThreadingHTTPServer`, port written into `state.json`, `GET /state` (ETag/304), `GET /events` SSE with ~15s keepalive, browser commands appended to `commands.jsonl`, `POST /internal/*` for Claude to write back. The guided-reader SKILL.md is explicit: *"Each `tail -f` blocks the bash thread; Claude does not consume tokens while waiting."* **[V — quoted]** The division of labour is settled: **the server is a dumb byte-mover that NEVER calls `Task()`; the Claude session is the only engine.** `riff-server.ts` documents its own rule: *"Read-only by construction: there is no route that writes to the session."*

This is exactly how Step 5 ("10 more variants of this button") and Step 6 ("add a chart") happen without the user leaving the browser, **at zero token cost while they design.**

#### 16.6.3 O5 is a v1 BLOCKER with a defined fallback ladder (added in revision)

**The dependency, stated plainly.** Every editor feature in v1 — the design surface, autosave, SSE, the agent inbox, the zero-token `tail -f` loop — requires a local server that survives Claude's turn boundary. The **only first-party-proven** way to survive it is the **Python double-fork daemon**. The TS equivalent is unproven (§17-O5). §18's v1 "Scope in" list currently states *"Double-fork server + fixed port + curl-across-turn-boundary verification"* as delivered functionality **without conditioning it on O5**. That is corrected here.

**Gate 16-A (new gate; blocking, run before v1 implementation begins).** `scripts/probes/probe-turn-boundary.ts` must be executed and its result recorded in the evidence bundle **before any server-dependent v1 scope is treated as committed.**

*Procedure (identical to the 2026-07-09 first-party test, so the results are comparable):*
1. Launch `server.ts` via the candidate detached-spawn mechanism.
2. `curl --retry 20 --retry-connrefused` → expect HTTP 200 **in the same turn**.
3. **End the turn.**
4. In a **separate, later tool call**, `curl` again → expect HTTP 200, and confirm the pid in `state.json` is still in `ps`.
5. Repeat 3–4 across at least two further turn boundaries, and once across an eternity-protocol `/clear` if one occurs.
*Pass = HTTP 200 at every post-boundary check with the original pid alive. Anything else is a fail.*

**Fallback ladder — take the first rung that passes Gate 16-A.** Each rung is tested with the exact same procedure. Rungs F1–F3 keep 100% of the shipped server in TypeScript; only the *launch shim* differs.

| Rung | Mechanism | Language impact | Status |
|---|---|---|---|
| **F1** | Node/Bun `child_process.spawn(cmd, args, {detached: true, stdio: 'ignore'}).unref()` | Pure TS | **UNPROVEN in this harness** — the thing O5 asks about. Note the 2026-07-09 log line *"Script spawns a detached child and exits → orphan reaped instantly"* is evidence that a naive detach is insufficient; whether `detached:true` + `unref()` differs materially is exactly what the probe answers |
| **F2** | Bun/Node spawn of a **`setsid`-equivalent double-fork implemented in TS** (fork → new session → fork → exec `bun server.ts`) | Pure TS | Unproven. Note gotcha 3 of the original log: **`setsid` does not exist on this Mac**, so the session-leader step must be achieved another way (e.g. a POSIX call through a TS FFI binding, or F3) — **this may not be reachable in pure TS; no known mitigation if the required syscall is not exposed** |
| **F3** | A ~15-line **POSIX `sh` launcher** that performs the double-fork and `exec`s `bun server.ts` | Server is 100% TS; the launcher is shell. **`install.sh` already establishes shell as acceptable glue in this skill** | Unproven but low-risk; **preferred fallback** because it preserves the language rule's intent (no new Python, all product logic in TS) while using the harness-proven *shape* |
| **F4** | Reuse the **proven Python double-fork daemon** purely as a launcher that `exec`s `bun server.ts` | ~20 lines of Python exist in the repo; **all product logic stays TS** | **PROVEN shape** (this is literally the recipe that worked). **Requires user sign-off** — it is a deliberate deviation from the standing TypeScript-only rule, and none of the three written exceptions (existing-Python edit / Python-only library / Python hook chain) cleanly covers a brand-new launcher file. Naming the deviation is mandatory, per the PRD's own rule |
| **F5** | **Redesign the lifecycle so cross-turn survival is not required**: the user runs `bun scripts/server.ts` in **their own terminal** (outside the harness), and the skill only ever *connects* to it — detecting it via `state.json`, and printing a copy-pasteable start command if absent | Pure TS, zero harness dependency | Always available. **Cost: the "one command and a browser opens" experience degrades to a two-step start**, and any resume after `/clear` depends on the user's terminal still running. This is a **UX regression that requires user sign-off** if it becomes the shipped path |

**v1 scope is explicitly conditional (correction to §18).** Read §18's v1 line *"Double-fork server + fixed port + curl-across-turn-boundary verification"* as: **"a launcher that passes Gate 16-A, selected by the §16.6.3 ladder, plus fixed port and cross-turn verification."** If the selected rung is F4 or F5, the deviation must be signed off before v1 build starts, and §18 should be amended to name the chosen rung. **This is the single sequencing rule of the whole plan: run Gate 16-A first; it costs under an hour and it decides whether v1 is buildable as written.**

**Open question tracked (new; mirror into §17.4):**
- **O32 — If every TS rung (F1–F3) fails Gate 16-A, does the user prefer F4 (a ~20-line Python launcher, language-rule deviation) or F5 (manual terminal start, UX deviation)?** **Requires user decision.** The PRD does not choose on the user's behalf; both are deviations from something the user asked for.

**Honest residual:** if F1–F3 all fail *and* the user rejects both F4 and F5, there is **no known mitigation** — the browser-editor premise is incompatible with the harness under those constraints, and the product would have to be rescoped to a non-live-server form (e.g. generate-then-open-a-static-file, losing autosave, SSE and the inbox). This is stated so the risk is visible, not because it is expected.

### 16.7 Screenshots

**Plain Chrome CLI, zero npm dependencies.** `website-design-okoa/_build/screenshot.sh`:

```
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless=new --disable-gpu --no-sandbox --hide-scrollbars \
  --window-size=1440,3000 --virtual-time-budget=4000 \
  --screenshot=<out> <url>
```

then `[ -s "$out" ]`. **[V — read]**

By contrast, the ACOS Puppeteer path is only reachable via `NODE_PATH=/Users/zee/.npm/_npx/7d92d9a2d2ccc630/node_modules` — an npx cache that can be evicted; ACOS 3.0's root `package.json` declares `puppeteer@^24.39.1` but **`node_modules/` is EMPTY (0 entries)** **[V]**.

**Inherit the capture waits from `.claude/scripts/html-to-pdf.js`** — each encodes a real production bug: `page.goto(fileURL)` not `setContent()`; `networkidle0` with fallback to `load`; **strip `loading="lazy"` before capture** (headless IntersectionObserver never fires below the fold); `await document.fonts.ready` **plus per-image `decode()`**; then a 500ms deferred-CSS settle. Re-express in TS; do not re-derive.

**Device-height pinning applies to capture too (added in revision, ties to gotcha 12).** `--window-size=1440,3000` is a tall capture window chosen to grab a full page in one shot. **Any capture used to judge a viewport-height layout must instead use the pinned device size** (`390×844`, `768×1024`, `1280×800`, `1440×900`), because a 3000px-tall window makes `100vh`/`svh`/`dvh` resolve to 3000px and the hero is judged at a height no device has. Full-page captures remain valid for content review; they are **not** valid evidence for hero framing.

If scripted interaction/hover capture is later needed, follow the cleanroom precedent: `cd <skill>/scripts && bun add playwright && bunx playwright install chromium` — **the dependency lives inside the skill, not in an npx cache.**

### 16.8 Hooks

A skill **can** register its own hook dynamically: `acos-reverse-cleanroom` Phase −1 step 4 says *"Arm the egress guard: add the PreToolUse hook to `.claude/settings.local.json`… Verify with a probe call"*, and Phase 7 removes it at close. The guard is `scripts/egress-guard.ts` — **a TypeScript PreToolUse hook**, so TS hooks are already accepted. **[V — quoted]**

The existing PreToolUse chain has 5 entries, four ending in `|| printf '{"hookSpecificOutput"…allow'` (fail-open); the one hard gate is `block-review-rules-read.sh`. **Any Website Builder hook must be cheap and fail-open.**

| Hook | Purpose | Priority |
|---|---|---|
| **PreToolUse: editor-file-ownership guard** | Blocks Claude's `Write`/`Edit` on `pages/*.doc.json`, `content.json`, `history.jsonl` while the editor lock is held | v1 |
| **PostToolUse: evidence mirror** | One-line verdicts into `.acos/evidence/<date>/website-<session>/` so `/acos-status` sees the build | v3 |

**"No LOCK without gates passing" is better implemented as a script exit code than a hook.**

### 16.9 Reuse-versus-build table

| Item | Decision | Path / source |
|---|---|---|
| One-origin server contract, 5 routes | **Port Python→TS** | `~/.claude/skills/acos-image-builder/app/server.py` (105 lines) |
| Browser-edits-as-JSON → deterministic compiler | **Adopt pattern** | `~/.claude/skills/acos-type-forge/scripts/vectorize.py` flow |
| SSE + `commands.jsonl` + zero-token `tail -f` | **Adopt pattern** | `~/.claude/skills/acos-guided-reader/scripts/gr-server.py`; `.claude/skills/acos-investment-committee/scripts/committee-room/ic-server.py`; `.claude/skills/acos-research-riffs/scripts/riff-server.ts` (already TS) |
| Chrome headless capture recipe | **Adopt as-is** | `/Users/zee/Documents/Vibe Coding/website-design-okoa/_build/screenshot.sh` |
| Capture waits (lazy-strip, fonts.ready, decode, settle) | **Re-express in TS** | `.claude/scripts/html-to-pdf.js` |
| Design-system schema + QA framework | **Adopt** | `~/.claude/skills/acos-design-system-forge/references/01-template.yaml` + `07-qa-framework.md` + extension modules (`motion-interaction.md` is the right source for D4's animation item) |
| Warm-start store | **Adopt as-is** | `.acos/design-library/<name>/` |
| Per-variant licence register format | **Adopt as-is** | `website-design-okoa/okoa-design/*/v1/README.md` |
| Session dir + ACTIVE marker + config snapshot | **Adopt pattern** | `.claude/skills/acos-reverse-cleanroom/SKILL.md` Phase −1 |
| Frontier-recomputed-from-disk principle | **Adopt** | `.claude/skills/acos-axiom-synthesis/STATE-MACHINE.md` line 66 |
| 3-variant side-by-side comparison | **Adopt** | `~/.claude/skills/acos-design-variants/SKILL.md` Phase 2 |
| Chart form heuristic, colour formula, validator, palette | **Adopt** | local `dataviz` skill + `references/palette.md` |
| Puck Data/Render split, viewports config, slot `allow`/`disallow` | **Adopt patterns, not code** | puckeditor.com docs |
| Figma constraint + "Ignore auto layout" model | **Adopt pattern** | help.figma.com |
| Stackbit annotation scheme + descent scoping | **Adopt pattern** | docs.netlify.com |
| Plasmic owned/managed file split | **Adopt pattern** | docs.plasmic.app |
| dnd-kit (MIT, 17,437★, pushed 2026-07-13) | **Adopt as code** | Pointer + keyboard sensors and collision layer **ONLY** — never as the layout model |
| ProseMirror / TipTap (MIT) | **Adopt as code** | One long-form block only |
| Wigum fix-loop exit-code contract | **Port to structured verdicts** | `.claude/skills/acos-ultimate-designer/scripts/wigum-loop.py` → `gates.ts` (cleanroom `lib/gates.ts` is the model: return verdicts, never throw on a normal fail) |
| Genesis registry | **Port Python→TS** | `registry.py` → `registry.ts` over the same `registry.json` (v2) |
| **Detached-daemon launcher (`launch.ts` / rung-dependent)** | **PROVE FIRST, then choose the rung** | Proven shape is the Python double-fork in `acos-guided-reader-server-gotcha.md`; ladder F1→F5 in §16.6.3; **Gate 16-A decides. F4/F5 require user sign-off** |
| **Preview-iframe device-height pinning** | **BUILD NEW (adopt the constraint from Puck's documented default)** | Puck ships all four default viewports at `height: 'auto'` — §11 and gotcha 12; the pinned sizes are 390×844, 768×1024, 1280×800, 1440×900 |
| **Chrome-CLI capture at pinned device sizes** | **Extend the adopted recipe** | §16.7 — `--window-size` must match the pinned device height for any page containing a `vh`/`svh`/`dvh` rule |
| **The VLM judge loop** | **DO NOT PORT** | The human replaced it; porting re-imports the rejected architecture |
| **Autonomous Wigum aesthetic iteration** | **DO NOT PORT** | Same |
| **`.claude/agents/` additions** | **DO NOT ADD** | Human-approval-restricted; `Task(general-purpose)` suffices **where available — v1 does not depend on it, see §16.5.1** |
| **`site.json` model + renderer** | **BUILD NEW** | Nothing in ACOS does DOM-level layout editing |
| **Editor runtime** (anchors, snap, contenteditable, component bar, containers) | **BUILD NEW** | " |
| **Design-system importer + repair-prompt emitter** | **BUILD NEW** | " |
| **Deterministic variant generator** | **BUILD NEW** | " |
| **LOCK/export compiler** | **BUILD NEW** | " |
| **Evidence + licence bundler** | **BUILD NEW** | " |
| **`install.sh` symlink installer** | **BUILD NEW** | Breaks the copy-drift pattern |

### 16.10 Frameworks explicitly rejected

| Candidate | Licence / health | Why rejected |
|---|---|---|
| **GrapesJS** | BSD-3-Clause (npm), 26,067★, pushed 2026-07-24 — healthy | Backbone + underscore era architecture; core `dragMode: 'absolute'` is coordinate dragging with no responsive story; **its own docs scope Absolute Mode to *"fixed-layout designs … where responsiveness isn't required"***; the polished version lives in the commercial Studio SDK, not the open core. **[V — registry.npmjs.org, GitHub API, app.grapesjs.com]** Also note GitHub's API reports NOASSERTION while npm reports BSD-3-Clause — **re-verify against the actual LICENSE file at pin time** |
| **Craft.js** | MIT, 8,700★, **last push 2025-02-14** — ~17 months stale as of 2026-07, 225 open issues | Unacceptable as a foundation for a system that must run for years **[V — GitHub API]** |
| **Plasmic** | SDKs and code components open; **core editor and studio proprietary** | Self-hosting exists, forking the editor does not **[V — forum.plasmic.app]** |
| **Builder.io** | Only Mitosis (the compiler) is open | The visual editor is SaaS |
| **TeleportHQ** | Open component/codegen layer around a hosted editor | Same shape |
| **Puck** | **MIT, 13,018★, pushed 2026-07-24, actively developed** — genuinely the right philosophy and licence, now positioning as *"the agentic visual editor for your design system"* | **Three gaps, each fatal here:** (1) **no grid-cell placement model** — Puck composes flow lists via slots and *"multi-column layouts using nested components,"* so D2's snap-to-gridlines and Step-4(a) gridlines have no home; (2) **no per-breakpoint override cascade** — viewports resize the iframe but the Data document has no breakpoint dimension; (3) **it is React**, whereas the settled build target is Astro static with zero shipped JS, so components would exist twice. **Mine it for API shapes and possibly vendor individual utilities; do not build the product inside it** **[V — GitHub API + docs read; the three gaps are inference from the docs]**. **Fourth, non-fatal but load-bearing:** all four of Puck's default viewports use `height: 'auto'` **[V — Lens 4]**, which is the source of gotcha 12; adopting Puck's viewport *config shape* without pinning heights would import the bug |

**Figma Sites** (open beta, Config 2025) confirms the direction is mainstream and supplies two transferable ideas — name-matched responsive variant binding (breakpoints named Desktop/Tablet/Mobile bind to variant property values with those names), and the fact that Figma treats custom cursors, marquee and parallax as **first-class site primitives**, corroborating the user's Step-2 item list. Nothing else is reusable: closed, hosted, exports no ownable editor. **[V — figma.com/blog, help.figma.com]**

### 16.11 macOS / harness gotchas to encode in `references/gotchas.md`

| # | Gotcha |
|---|---|
| 1 | **No `timeout`/`gtimeout` binary** on this Mac — `timeout 25 cmd` silently yields **EMPTY output**, not an error. Guard long runs with `run_in_background: true` + poll |
| 2 | **Agent-thread cwd resets between Bash calls** — absolute paths everywhere |
| 3 | House rule: open previews with `open -a "Google Chrome" <url>` |
| 4 | Opus subagents stream-idle-timeout on heavy binary reads — keep rendering/screenshotting in the main thread or background Bash |
| 5 | **macOS APFS is case-insensitive** — sibling direction names must not differ only by case |
| 6 | Autosave must be a small JSON diff POSTed to the server, **never a base64 blob in localStorage** (image-builder's own logged gotcha) |
| 7 | The Oracle scores Bash/Write/Edit/Task at threshold 9 fail-open, so ordinary bun/chrome commands auto-approve; **destructive steps score +5 and will prompt** — implement export as **write-to-new-dir-then-swap**, never `rm -rf` |
| 8 | Eternity `/clear` at 400k (project config) / 500k (daemon config — **the daemon's own config wins; hardcode neither**) kills the `tail -f` loop. Fixed port + `state.json` + a resume prompt that says **re-attach, do NOT relaunch** |
| 9 | `session-cleanup.sh` runs at SessionEnd on `.acos/state/` only, so `.acos/website-builder/` artifacts are safe |
| 10 | Astro HMR does not reliably hot-reload when files are **added or removed** under `src/pages/` — a variant swap that changes the import graph may need a full reload. Budget a measured fast path and a hard-reload fallback |
| 11 | `claude-in-chrome` MCP availability inside spawned agents is **unverified** — do not design any capture path that depends on it |
| 12 | **The viewport-height trap.** An auto-height preview iframe makes `100vh`/`svh`/`dvh` measure **the iframe's expanded height, not a device's** — so a hero using viewport units is framed and approved in the editor and is wrong on a real phone. Puck ships all four default viewports with `height: 'auto'` **[V — Lens 4]**, and hero is this product's highest-value swap (12 variants, §20.2). **Rule: whenever a page contains any `vh`/`svh`/`dvh` rule, pin the preview iframe to a real device height — 390×844, 768×1024, 1280×800, 1440×900 — and pin the headless capture window to the same size (§16.7).** **Acceptance criterion (feeds §19): for any page containing a viewport-height rule, the measured preview iframe height at each breakpoint equals the pinned device height, and a device-height capture exists in the evidence bundle.** Related: when Puck's compositional `<Puck.Preview />` is used directly the viewports API has no effect at all (§11) — do not assume a viewport config is being honoured; **assert the measured height** |
| 13 | **Do not assume `Task` is callable mid-skill.** Whether an `allowed-tools` list suppresses a later `Task(general-purpose)` call is **unverified** (§17-O31). Any feature that would depend on it must have an inline main-session path (§16.5.1); run `scripts/probes/probe-task-availability.md` before designing around subagents |
| 14 | **A `run_in_background: true` server is not a server.** It binds, curls 200, and is SIGTERM'd (exit 143) at the turn boundary. Anything that must outlive a turn goes through the §16.6.3 launcher; **always prove survival with a second curl in a separate tool call**, never with a same-turn 200 |

**Cross-reference additions made in this revision (must be mirrored into §17 so the ids stay consistent):**

| New id | Where defined | One-line statement |
|---|---|---|
| **O31** | §16.5.1 | Does an `allowed-tools` declaration that omits `Task` suppress a later `Task(general-purpose)` call from a running skill session? **Unverified; probe defined; v1 designed not to depend on it** |
| **O32** | §16.6.3 | If every pure-TS launcher rung (F1–F3) fails Gate 16-A, does the user choose F4 (small Python launcher, language-rule deviation) or F5 (manual terminal start, UX deviation)? **Requires user decision** |
| **Gate 16-A** | §16.6.3 | Cross-turn-boundary server survival proof; **blocking; must run before v1 server-dependent scope is treated as committed** |

**Sign-off items surfaced by this revision (none may be taken silently):**

1. **§16.6.3 F4** — reusing a ~20-line Python double-fork launcher would deviate from the standing TypeScript-only rule. **Requires user sign-off.**
2. **§16.6.3 F5** — a manual, user-terminal server start would deviate from the "one command and the browser opens" experience. **Requires user sign-off.**
3. **§16.5.1 deviation flag** — mandating subagent execution for custom components would require adding `Task` to `allowed-tools` against the skill-maker authority. **Requires user sign-off.**
4. **§16.6.1** — locking either topology (Candidate A or B) before the spike runs would be a decision the PRD has not earned. **Requires the spike, then an ADR.**

---
## 17. Risks and open questions

Severity-ranked. **Risks with no known mitigation are marked ⛔ and stated plainly.**

### 17.1 Critical

**R1 — Artwork is structurally undeliverable from claude.ai.**
claude.ai has no raster generation **[V — Anthropic, April 2026]**. The user's cited exemplar came from a 231-PNG Unity export, not a chat **[V]**. The failure: the interview asks about background art, the prompt asks for 20 artworks, and 20 flat geometric SVGs come back — the exact AI-slop register the anti-slop lint detects. The user hates all 20 and a whole branch of D1 is dead weight.
**Mitigation:** three honestly-labelled lanes (§7.9). Lane A code-drawn (genuinely good, token-parameterised). Lane B asset ingestion (what actually made FruitSync work; Step-0 question C3 detects it). Lane C external raster generation as a **separate** hand-carry with its own licence manifest, explicitly scoped in or out. **Never let the PRD imply a single paste produces site art.**

**R2 — Directions are selected in a preview that cannot render their typefaces.**
The artifact CSP permits `fonts.googleapis.com` under `style-src` but restricts `font-src` to `data:` and `claudeusercontent.com` — the CSS loads, the WOFF2 is blocked, the artifact falls back to a system face. Typography is the largest identity carrier. **You pick a look you have never seen.**
First-party corroboration that this failure class is already live: the shipped FruitSync site has **zero `@font-face` and zero `fonts.googleapis` references**; its only font token is `--sans: ui-rounded,"SF Pro Rounded","Hiragino Maru Gothic ProN","Quicksand",system-ui,…`. `ui-rounded`/SF Pro Rounded is Apple-only; Quicksand is installed nowhere by default. **Every non-Apple visitor sees Segoe UI or Roboto — a completely different typographic personality from the one the user designed and signed off. The user has almost certainly never seen their own shipped site as a Windows or Android visitor sees it.** **[V — grep of both `index.html` files, 0 matches]**
**Mitigation:** mandate base64 `data:font/woff2` @font-face for the display face in every direction artifact, subset to the preview glyph set, with the pre-subsetted strings supplied by the skill's font catalog so claude.ai pastes rather than invents. **Verify the CSP behaviour in 60 seconds first (§17-O1).**

**R3 — Silent truncation produces valid, wrong CSS.**
A truncated JSON payload throws and is caught. A truncated CSS block, HTML fragment, or SVG path is syntactically fine — the browser drops the last incomplete rule and renders. Direction 6's tokens get cut after 40 of 62 properties; the skill accepts it; the user spends 25 minutes wondering why the footer and secondary buttons look wrong while everything above the fold looks right. **No error anywhere.** Diagnosing requires diffing against a direction they have never seen in full.
**Mitigation:** the envelope with a per-run random terminator, per-file line counts, sha256 prefixes, smallest-first ordering, and a hard ingest refusal (§6.2).

**R4 — If the DOM is the source of truth, this is Dreamweaver 2003.**
The canonical WYSIWYG failure. Worse here because Claude is also writing the source.
**Mitigation:** `layout.json` as the only source of truth; the page is a pure render; the editor never serialises DOM (§12.1). **This must be a hard PRD constraint, not a note.** Zero DOM injection for hit-testing (§11.9).

**R5 — Long-running local servers die at the turn boundary in this harness.**
**[V — first-party, four documented attempts]** The editor's entire premise is a long-running local server, and the failure appears intermittent because it depends on turn timing.
**Mitigation:** fully mitigated by the proven double-fork recipe + fixed port + `state.json` + curl-across-turn-boundary verification (§16.6). **But the proven recipe is Python and the language rule mandates TS — the TS equivalent must be re-proven before the PRD assumes it (§17-O5).**

**R6 — Two writers, no lock, silent work loss.**
Near-certain, not a corner case, because the product design encourages alternating between talking to Claude and dragging things.
**Mitigation:** file ownership + PreToolUse guard + optimistic concurrency with 409 + every-save-is-a-commit (§12.10).

### 17.2 High

**R7 — The hand-carry costs 45–90 minutes per cycle, and Step 5 makes it a loop.**
The most likely way the product quietly dies: the user builds site 1, enjoys it, starts site 2 three weeks later, hits the paste marathon at minute 20, and never finishes.
**Mitigation:** one-paste protocol (~40 ops → ~5), `pbpaste` ingest, and — the strongest lever — **Local Regeneration Mode makes the web hop optional**, not the spine.

**R8 — Constraint dragging: the market ran this experiment and the constraint editor is the one that died.**
Wix Editor X — the closest commercial analogue to D2 — began sunsetting April 2024 and was killed January 2025 with all sites force-migrated to Wix Studio. The Wix **Classic** editor, absolute free positioning, is still shipping in 2026. Adobe Muse was killed 2018/2020. Webflow's cascade runs in both directions from a desktop base and its forum has recurring threads titled *"Break points cascading both up and down."* **[V — support.wix.com transition FAQ, helpx.adobe.com, discourse.webflow.com]**
**Concrete daily friction:** the user wants the hero headline 12px higher. In a free canvas that is one drag. Under D2 they must work out whether the lever is the parent's `align-items`, the element's `margin-block-start`, a `gap` that also moves three siblings, or a grid-row change — and then learn it didn't fix 1440px, or did and broke tablet. **They will hit this on their fifth edit and it is the moment they decide the tool fights them.**
**Mitigation:** never present raw CSS concepts — exactly three verbs (align to / space above-below from the scale / order among siblings); a **persistent pre-commit chip** stating which sizes an edit affects with a one-click "apply to all sizes"; an overrides dot on any element with breakpoint-specific values plus a panel listing them. **Webflow's #1 confusion is invisible overrides — make them visible.**

**R9 — Free position doesn't degrade gracefully; it collapses parents and bakes in the authoring viewport.**
Slow-motion: nothing breaks until the user opens the site on their phone weeks later.
**Mitigation:** anchored-offset, reserved `min-block-size`, per-breakpoint, auto-demote at ≤479, a visible counter, a hard LOCK gate. **⛔ Partial only:** for art whose composition depends on absolute relationships across the whole viewport, the only answer is to treat the composition as one component with internal responsive rules — **which means the user cannot drag its parts individually, which is exactly what they asked for. There is no better answer.**

**R10 — Cross-direction swaps have no good implementation.**
Re-skin destroys what the user liked; transplant destroys the system.
**Mitigation:** make the tension visible — side-by-side, explicit pick, coherence-debt ledger, soft cap, and the switch-the-whole-site offer (§14.3). **Do not block.**

**R11 — Component swaps silently destroy copy.**
Fake AI-invented statistics can ship. Copy is the thing the user hand-wrote and cares most about.
**Mitigation:** typed slot contracts, superset-only offers, the content orphanage, placeholders that block LOCK (§14.4).

**R12 — Python-gravity vs the language rule.**
Every reusable server/QA script in the estate is Python (122 project + 66 global `.py`); the path of least resistance violates the rule.
**Mitigation:** port `server.py` → `server.ts` **first**, before any other code.

**R13 — Multi-viewport edit ambiguity.**
Show one viewport and the user never sees breakage; show several and dragging in the 390 pane is ambiguous.
**Mitigation:** the pre-commit chip + overrides indicator. **⛔ Partial only — the underlying model is genuinely hard and no builder has made it easy.**

**R14 — Editor runtime fights the site runtime, so you never see the motion you're designing.**
Lenis lerps `scrollTop` every frame; GSAP transforms make `getBoundingClientRect` return animated positions. Disabling motion in edit mode is the only workable answer, and it creates the problem.
**⛔ No known mitigation for judging motion FEEL while editing.** The prior report's Data Gap 2 states motion verification is unvalidated end-to-end anywhere in the industry. The human-in-the-loop design does not solve this — **it moves the unsolved problem from an AI judge to a human who also has to be in preview mode to see it.** Partial: PREVIEW MOTION toggle, per-container scrub slider, trigger-point markers (§9.6).

**R15 — Generation determinism is load-bearing and fragile.**
Any nondeterminism makes `wb verify` produce false positives, users learn to ignore it, and the whole drift guarantee silently dies.
**Mitigation:** the four named hazards designed out up front (§12.8).

**R16 — Localhost is not a trust boundary.**
CVE-2025-24010 proves a malicious page in the same browser can reach a localhost dev server. Getting Origin validation and the bearer token wrong turns a design tool into a remote-code-drop.
**Mitigation:** the six-control posture (§12.12) plus the semantic-op wire format (§12.13).

**R17 — Step-3 is an unauthenticated code-import channel.**
Arbitrary code lands in `src/`, is evaluated by `astro dev`, and is bundled into the published site.
**Mitigation:** the validating importer with quarantine (§12.14).

**R18 — Scope: this is four products, and the third one is Webflow.**

| Layer | Effort | Notes |
|---|---|---|
| L1 interview + prompt generator | 2–4 days | A question tree + a template renderer |
| L2 ingest/validate/normalise + token compiler + font catalog + variants | 8–12 days | |
| **L3a editor-lite** (inline text, section reorder, variant swap, save, multi-viewport preview — **no canvas**) | 8–12 days | |
| **L3b editor-full** (canvas drag, anchors, snapping, layers tree, per-breakpoint overrides with provenance, free-position, undo, marquee select, keyboard nudge) | **30–60 days, and it never feels finished** | The Webflow-class layer. GrapesJS, Craft.js and Puck exist precisely because this is hard |
| L4 lock/export/publish/evidence | 3–5 days | |
| L5 custom components | ~5 days per family | |

**[I — anchored on the existence and maturity curves of comparable open-source projects and on Webflow/Framer/Editor X being multi-year multi-team products]**

**Smallest genuinely useful thing: L1 + L2 (single direction, not ten) + L3a + L4 ≈ 3–4 weeks, delivering ~80% of the value** — because the operations the user actually performs on a marketing site are "change this text," "move this section up," "try the other hero," "ship it." **Pixel-dragging is the operation they *think* they want because that is what a design tool looks like.**
**Mitigation:** sequence L3a before L3b with a **real decision gate** — build L3a, use it for one real site end to end, then decide.
**Scope tripwire, flagged not traded:** under schedule pressure the tempting shortcut is to drop the grid model and go flow-only, which **silently deletes Step-4(a) gridlines and Step-4(b) precise placement.**

**R19 — Editor/export divergence is a silent killer.**
Any CSS existing only because the editor is mounted (a wrapper, a stacking context, an overlay-induced scrollbar) makes the locked site differ from what was designed.
**Mitigation:** zero DOM injection + the screenshot-diff gate. **Without that gate it ships undetected.**

**R20 — Month six: the precedent already rotted.**
Unversioned tree, 30 opaque variant directories, no manifest, builder source in a job tmp **[V]**.
**Mitigation:** `git init` at Step 0; `provenance.json`; content mode; do-not-hand-edit banner; unlock diffs against the lock manifest; pinned versions + committed lockfile.

**R21 — The interview is where the user's time is spent worst.**
Enumerated honestly, the bank is 78 questions; at 30–60s each that is 40–80 minutes before a single pixel. Then direction review, then up to 400 potential component decisions. The prior report's own show-don't-MCQ finding and Iyengar/Lepper both argue against a long questionnaire and a 10-up grid.
**Mitigation:** three tiers; aggressive pre-fill from mined sources; the tournament instead of a grid; canonical variants pre-selected so 400 decisions is a ceiling nobody reaches.

**R22 — Undo across AI-driven mutations is where editors fracture.**
A naive per-mutation undo leaves a broken hybrid after one Cmd+Z.
**Mitigation:** single JSON-patch stack + transactional grouping + **dedicated test coverage for undo against AI actions specifically**.

**R23 — Third-party marks will be invented.**
Platform CTA badges, social icons, trust badges, press logos, map tiles.
**Mitigation:** flagged `[3P]` in the inventory as non-designable deterministic embeds; variants are arrangement only. **Generating a Steam button is a trademark violation.**

### 17.3 Medium

**R24 — Charts break coherence by construction.** A direction with 3 brand hues cannot yield a 6-series categorical palette that is on-brand, distinguishable and colourblind-safe. Mitigation: dataviz sub-tokens from generation time, not retrofit; v1 whitelist caps custom components; decide build-time-SVG vs client-library early.

**R25 — No layers panel would be fatal.** A full-bleed background art container sits on top of everything and swallows every click; nested containers cannot be clicked. **Added to v1 with its own effort line.**

**R26 — Step-0 warm start and Step-5 redesign pull in opposite directions.** Anchoring turns site 2 into a recolour of site 1, giving the user a house style they never chose — the prior report's sameness failure reproduced at personal scale, caused by the tool built to prevent it. Invisible until there are three sites. Mitigation: the system/identity split + negative constraints (§15.3).

**R27 — The editor caps the quality ceiling below what the interview promises.** A component bar swapping pre-generated variants into a grid **is** template assembly. The user gets a very good, very coherent, entirely unremarkable page and concludes the design system was bad. Mitigation: calibrate the language ("bespoke, coherent, hand-adjustable" is deliverable; "award-winning" by swap-menu is not); ship the custom code block; reserve one bespoke signature-moment slot.

**R28 — Ten directions do not automatically increase distinctiveness.** Without forced-divergence constraints all 10 regress to the mean and the user picks from a false-choice set. Mitigation: assign opposing-axis positions in advance (minimal↔maximal type, cool↔warm palette, geometric↔organic layout, static↔kinetic motion), make them visible in the pick UI, seed each with ≥3 references from different eras/genres, and enforce per-direction negative constraints.

**R29 — Eager variant generation stalls Step 4.** 10 × ~12 families ≈ 120 variants per direction. Mitigation: lazy on first panel open, cached per direction, never for unused families.

**R30 — Token count drives editor performance.** ~800 CSS custom properties per scheme re-evaluated on every drag is a real reflow cost. Mitigation: compile to a flat CSS-variable layer once per direction change, not resolved at edit time.

**R31 — Motion variants are the least verifiable part of the inventory.** VLM recall of aesthetic animation from frame sequences measured at 0.16. Ten text-reveal variants are ten things a screenshot cannot tell apart. Mitigation: acceptance rests on the human plus deterministic motion lint, **never on an automated visual score**.

**R32 — Two components are legally shaped, not aesthetically shaped.** Six pretty cookie-banner variants whose reject path is harder than accept is a compliance defect that looks like a design success.

**R33 — Undifferentiated variants reproduce the jam study.** Mitigation: the 200×120px indistinguishability rule.

**R34 — Artwork at 20 exceeds the safe presentation ceiling without filters.** Filter chips are not a nice-to-have; **they are what makes 20 legal.**

**R35 — The app-shell tail can colonise the interview and the budget.** 62 v3 items gated behind the site-type answer.

**R36 — Text pasted into contenteditable carries source-app markup**, survives LOCK, violates the token lint, and is invisible in the editor. Mitigated by `plaintext-only`.

**R37 — Skill duplication drift.** `acos-type-forge` already exists as two independent copies. Mitigation: symlink installer.

**R38 — Two servers means two ports, two origins, two things to forget to shut down.** A dev server left running for days is a more likely real-world exposure than a targeted attack. Mitigation: idle shutdown.

**R39 — Spring tokens are outside DTCG.** Every tool in the chain must agree on the extension shape or springs silently degrade to no motion.

**R40 — Native scroll-driven animations have no Firefox support without a flag.** A "native-first" strategy needs a real, tested GSAP fallback, not an assumed one, or a meaningful minority see static or broken reveals.

**R41 — Deploy is a second manual boundary.** If not automated, every future content edit ends in a dashboard drag-and-drop.

**R42 — The prior swarm architecture is seductive.** Phase agents, blind opus reviewers, Wigum loops, judge calibration — all well-documented, and there is a real risk of importing them wholesale and rebuilding the autonomous product the user explicitly rejected.

**R43 — Step-3 output is non-deterministic and the model drifts.** The same prompt in three months produces a different system. **The prompt is not a build artifact; it is a lottery ticket.** Mitigation: persist the RESULT as the artifact of record; store the prompt only for provenance; never plan to re-derive a system from a stored prompt.

**R44 — Transformed art containers trap dropdowns.** Near-certain given D4, presents as "the menu is behind the picture" with no obvious cause. Mitigation: encode the rule in the token file as Primer does, and lint for overlay-layer content nested inside transformed containers.

**R45 — A user can make a bad pick.** They may choose a direction already slipping toward saturation, and the system cannot override taste. Mitigation: freshness-based confidence scores and time-decay warnings ("this aesthetic peaked ~8 months ago"). **Never block.**

**R46 — A claude.ai usage-tier surprise.** Two-stage × N directions consumes meaningfully more messages than a single-prompt mental model implies. Surface it up front.

### 17.4 Open questions

| # | Question | Why it matters | How to answer |
|---|---|---|---|
| **O1** | **Does a claude.ai artifact actually render a Google Font, or does `font-src` block the WOFF2 and fall back silently?** | Determines whether typography can be judged on the web side **at all** | **60-second devtools test. Run before writing the Step-2 prompt spec** |
| **O2** | What is the real per-message and per-conversation output ceiling on the user's plan in practice — how many ~40KB direction artifacts fit before "maximum length"? | Sets the chunk size; the difference between 2 conversations and 12. **The figures found in 2026 SEO "guide" content were unverifiable and some model names appear fabricated — do not design around them** | Empirical test against the real product |
| **O3** | Does the user actually want free pixel dragging, or "move this section up" and "nudge this 12px"? | **A 40× effort difference** | **Build L3a and watch which operations they reach for. Do not answer by assumption in the PRD** |
| **O4** | Single-origin proxy vs two-origin iframe + postMessage — which is less total complexity once auth, SSE and HMR are wired? | Foundational | Spike both before locking the architecture |
| **O5** | Does the TS detached-spawn survive the turn boundary the way the Python double-fork does? | The language rule vs the only proven recipe | Same curl-across-turn-boundary test |
| **O6** | Is LOCK a re-render from `layout.json` or a copy-and-strip of the design surface? | **The single most consequential architectural decision in the eight steps.** The PRD recommends re-render; the FruitSync precedent is copy-and-strip and already required hand-rewriting links and hand-excluding dev pages | Settled here as re-render; confirm with the user |
| **O7** | Where does raster art come from for a project that does **not** own a sprite library? | Decides whether the art category is real or theatre. **Step 0's check should arguably be "does an asset library exist," because that is the binary** | User decision |
| **O8** | Does the built site target Astro, or plain HTML/CSS from a TS renderer? | The user's own estate (`website-design-okoa`) ships plain generated HTML with no framework — **far simpler to make live-editable and to LOCK cleanly** | Spike |
| **O9** | Canonical design-system format: forge's `design-system-spec.yaml` (existing validator, 883-line precedent) or DTCG tokens JSON (W3C-stable 2025.10)? | **Emitting BOTH from one importer is cheap and may be the right answer** | Decide at build |
| **O10** | Is multi-page in scope for v1, or one page? | Section reordering, swapping and LOCK are page-scoped; cross-page shared regions introduce a partials model and a change-once-changes-everywhere contract not in the eight steps. **Roughly doubles editor scope** | User decision |
| **O11** | Does a component appear with **different** variants on different pages, or is a variant choice global? | Per-instance overrides are more powerful **and are also how a design system stops being a system** | User decision |
| **O12** | Should the component bar show only the current direction's variants, or also the same component in the other 9? | The second is more useful for exploration and **directly undermines D1's coherence guarantee.** A product decision, not a technical one | User decision |
| **O13** | How many sites will this really build — one flagship, or a portfolio? | If one, warm-start machinery, provenance and registry are premature and that effort belongs in the editor. If a portfolio, identity-homogenisation becomes the top design problem | User decision |
| **O14** | Charts: static presentation (build-time SVG) or live/interactive (client library)? | The latter pulls in a dependency the performance gate must absorb | v1 default: build-time SVG |
| **O15** | Does "20 artworks" mean 20 individual pieces or 20 candidate **style sets**? | The inventory assumes sets for icons/illustrations/spots/patterns because 20 individual icons is not a design choice — **but 20 individual hero illustrations might be exactly what was meant** | User decision |
| **O16** | Should the skill persist a cross-project **taste profile** so repeat users fast-confirm the swipe-sort? | Speeds run N+1 without inheriting identity | v3 |
| **O17** | Is 24 the right reference-image count for the swipe-sort? | Starting point covering major style families without fatigue; **needs empirical tuning on real projects** | Measure |
| **O18** | Should the interview split across sessions, mirroring the 30–45-min-per-stakeholder multi-session pattern real design-system engagements use? | The user wants award-adjacent quality and might benefit from reflection time between Taste and Design-System waves | Offer as an option |
| **O19** | Is AA the contractual floor only, or should select AAA numbers (2.4.13 Focus Appearance, 2.3.3 Animation from Interactions) be adopted as aspiration? | | User decision, defaults to AA |
| **O20** | When WCAG-2 and APCA disagree on a borderline pair, show both numbers or collapse to one badge — and which is authoritative? | | WCAG 2 is the pass/fail gate; APCA is advisory |
| **O21** | Does "regenerate this section" call back out to claude.ai as another hand-carry, or run inline via the skill's model access? | Materially changes whether the feature is synchronous or another async hand-off | Inline, via Local Regeneration Mode |
| **O22** | Does Step-5 redesign fork the whole project into a variation branch, or replace in place with the old state recoverable only through version history? | Determines whether branching is a first-class user-visible feature | Fork — save-as-variation is v1 |
| **O23** | Should agent ops go through the inbox even when the editor is not running? | Direct writes are simpler but create two write paths and two validation paths | Inbox always |
| **O24** | What happens if the user opens the same session in two browser tabs? | `editor.lock` covers processes, not tabs | Tab claim over SSE, or a read-only second tab |
| **O25** | Ownership of `tokens.css` — machine-owned (regenerate) or hand-tunable? | Machine-owned is cleaner, **but the user will want to nudge a value at 11pm without regenerating the system** | Machine-owned + `extract-override` |
| **O26** | Should lock snapshots include the built `dist/` (large, self-contained, instantly re-servable) or only doc + system lock (small, needs a rebuild to view)? | Affects `.wb/locks` growth over many locks | Doc + lock only; dist is reproducible |
| **O27** | Does the user's claude.ai plan include Projects/custom instructions? | If so, the schema + worked examples could live there persistently instead of being re-stated in every Stage-B prompt, **substantially shrinking prompt bulk** | Ask in the interview |
| **O28** | How should the skill react to a bundle pasted from an **older** prompt-template version? | Schema drift across skill updates | `templateVersion` field checked against a supported range, with a defined upgrade/repair path |
| **O29** | Should snapping offer optical alignment (glyph edges, not box edges)? | Adobe holds patents specifically on snap guides relative to glyphs of editable text, which suggests naive box-edge alignment **looks subtly wrong on large display type — the exact place an award-adjacent site is judged** | v3 |
| **O30** | How and when does filmstrip/interaction-manifest motion QA get built and budgeted, given the prior report states it has no validated end-to-end precedent anywhere? | | Deferred; §17-R14 stands |

---
## 18. Phased delivery plan

### Vision deviations requiring sign-off — read this before approving any phase

The phasing below is **not** a neutral schedule. It cuts features the user named directly in the
authoritative 8-step vision. §17-R18 explains *why* the cut is proposed (a 40× effort difference
between L3a and L3b), but the reasoning was written as a risk note, not as a decision put to the
user. It is put to the user here.

**Nothing in v1 may be built until the sign-off column below is resolved.** Each row marked
**requires user sign-off** is a deviation from a settled brief, not a sequencing detail.

| Vision step | What the user asked for | v1 delivers | Deviation | Sign-off |
|---|---|---|---|---|
| **0** Warm start | Reuse a prior design system if one exists | **Full** — Step-0 warm start + asset-library detection (A2) | none | — |
| **1** Interview | Interview about site + design system | **Full** — 78-question bank, three tiers, ~35–45 answered | none | — |
| **2** Prompt generation | A prompt producing the whole design system (font, front animation, button, colour schema, cursor, background art/style, top ribbon, arts — "only examples") | **Full** — Stage A + Stage B, full return schema, font catalog, frozen token manifest, envelope + terminator | none | — |
| **3** Manual paste on claude.ai | User pastes, generates, hands everything back | **Full** — plus Local Regeneration Mode as a zero-paste alternative (§20.2 disagreement 12) | none | — |
| **4(a)** Gridlines for precise placement, removable later | Visible grid the user places against | **NOT DELIVERED in v1.** Deferred to v2 | **Yes — a named vision feature is absent from the first shipping version** | **requires user sign-off** |
| **4(b)** Drag-movable components | Direct manipulation of position | **PARTIAL — reorder only.** Section reorder + anchor verbs; no pointer-drag placement. Deferred to v2 | **Yes — D2 (constraint dragging) is *inert* in v1: the only version that ships first contains no dragging of any kind** | **requires user sign-off** |
| **4(c)** Editable text | Inline text editing | **Full** — `plaintext-only` inline editing on ~90% of text nodes; the rich-text block is v2 | Rich-text formatting (bold/link/list inside a paragraph) is v2 | **requires user sign-off (minor)** |
| **4(d)** Component bar — swap any component for a comparable variant | Swap surface across the system | **Full within one direction** — 10 variants per component (12 for hero/CTA band/card/badge/feature grid/pricing per §20.2 disagreement 5). **Cross-direction swaps are v2** because only one direction is generated in full in v1 | Only one direction exists in v1, so "swap to a different direction's version of this component" is not reachable | **requires user sign-off** |
| **4(e)** A way to save changes | Save | **Full** — autosave + named snapshots + save-as-variation + every-save-is-a-commit | none | — |
| **4(f)** "Whatever else research says a tool at this level needs" | Open-ended | **Substantially expanded in this revision** — navigator tree, asset library pane, recovery bin, element freeze, duplicate/paste with overrides, per-breakpoint visibility, per-section notes → scoped regeneration (all now v1; see the v1 list) | The v1 editor is still editor-lite: no canvas, no zoom/pan, no rulers, no multi-select | **requires user sign-off** |
| **5** If nothing looks good | Generate more variants, or a brand-new design-system prompt | **Full, plus the middle gear** — per-section notes → scoped regeneration is moved into v1 by this revision so the answer is not only "swap one variant" or "regenerate everything" | none (was a gap; closed below) | — |
| **6** Custom components (graphs, charts) | User-added components the tool would not normally include | **PARTIAL** — build-time SVG charts, ≤4 mark types, whitelist only. Full 12-mark chart kit and the custom code block are v2; exotic and interactive charts are v3 | A user who wants a scatter, heatmap or interactive chart in v1 cannot have one | **requires user sign-off** |
| **7** LOCK / unlock | Toolbars and gridlines removed, visitor view, reversible | **Full** — five purity gates, two-build byte-equality, re-render not copy-strip, reversible (D3). Note: v1 has no gridlines to remove, so the "gridlines disappear" part of the LOCK experience is vacuous until v2 | Consequence of the 4(a) deviation, not a separate one | covered by the 4(a) sign-off |
| **8** Publish + evidence bundle with every font and asset licence | Publish + licence evidence | **Full** — evidence bundle + licence manifest + publish (or an explicit runbook, stated) | none | — |

**R47 (new risk, continuing §17's numbering) — v1 ships without exercising D2 at all.**
D2 was negotiated specifically to make dragging safe. If v1 contains no dragging, the constraint
model's day-to-day usability is **unvalidated at the moment of first ship**, and §17-R8's concrete
friction scenario ("the hero headline 12px higher") is not encountered until v2 — after the
constraint machinery has already been designed around. **Mitigation:** the v1 exit criterion below
requires the user to report which operations they reached for and could not perform; that report is
the empirical input to the v2 canvas design (§17-O3). **This mitigation is partial, not complete —
it detects the problem late by construction, and there is no known way to validate a constraint
drag model without building a drag model. [I]**

---

### Cross-cutting decisions this section resolves (previously open)

Two items were simultaneously listed as committed v1 scope and as unresolved open questions. A PRD
cannot do both. They are resolved here, in the scope section, per the critics' instruction — one by
decision, one by an explicit branch that **requires user decision before build starts**.

**§17-O10 — multi-page in v1? — REQUIRES USER DECISION, and the decision must be made before the
v1 build starts, not during it.** This revision does *not* fabricate an answer. It removes the
contradiction instead: multi-page is listed in the v1 scope below as **PROVISIONAL (O10-gated)**,
and both branches are costed so the decision is a priced choice rather than an open item that
silently defaults to "yes" because it appeared in a bullet list.

| Branch | v1 contains | L3a effort (revising §17-R18) | Consequences |
|---|---|---|---|
| **Branch A — single page (recommended default) [I]** | One page. No multi-page manager. No global regions as a *shared partial* — header/footer are ordinary sections of the one page | **8–12 days** (§17-R18's published L3a figure, unchanged) | A69 (per-page SEO) is satisfied trivially by the single page; A70's `sitemap.xml` contains one URL and `robots.txt` is still generated — **neither acceptance criterion is weakened, they are simply scoped to a one-page tree**. §17-O11 (per-page variant divergence) does not become live at all in v1 |
| **Branch B — multi-page in v1** | Multi-page manager, page tree, global regions as real partials, change-once-changes-everywhere contract, cross-page variant consistency | **16–24 days [I]** — O10's own words are "roughly doubles editor scope"; doubling §17-R18's 8–12 is the only honest reading of that estimate, and it is **inference, not a measured figure** | Requires the global-regions contract to be written (below) **and** forces §17-O11 to be answered in v1, because a global region that renders a different variant on page 3 is not a global region |
| **Branch A+ — single page with a page-tree-ready data model (available at no extra cost) [I]** | Branch A, but `layout.json` carries a `pages[]` array of length 1 and every op is page-scoped from day one | **8–12 days + ~0.5 day** | Makes Branch B a v2 feature addition rather than a v2 data migration. **This is the recommendation if the user does not want to decide now.** |

**Global-regions contract (required only under Branch B, written here so Branch B is not
under-specified):** a global region is a named node subtree stored **once** in `layout.json` under
`regions[]` and referenced by id from each page's tree. Editing it anywhere edits it everywhere.
Per-page *content* overrides are forbidden in v1-Branch-B (that is what a section is for); per-page
*variant* overrides are forbidden pending §17-O11. Deleting a page never deletes a region. LOCK
in-lines each region into every page at export so no runtime include ships.

**§17-O7 — where does raster art come from? — resolved for v1 by lane scoping (below), and only
the residual case remains open.** See the artwork line in the v1 scope.

---

### v1 — "Editor-lite, one direction, provably clean lock"

**Scope in:**
- Full interview (78 bank, three-tiered, ~35–45 answered), concept document, Step-0 warm start with asset-library detection
- **Structural-RTL gate in the interview (new, v1):** one Tier-1 question — "will this site ever be published in Arabic, Hebrew, Farsi or Urdu?" — asked *before* the direction prompt is generated. A "yes" does not pull RTL layout work into v1 (that stays v3), it flips the pseudolocalisation and 200%-zoom state sets to mandatory and records the answer in `session.json` so v3's RTL work has a known starting point. **First-party rationale [V]:** FruitSync shipped an English-fallback Arabic workaround because multi-line RTL was discovered late, then needed a full redo (commits `060a9af`, `7dd7544` in this repo)
- Step-2 prompt generator (Stage A + Stage B) with the full return schema, font catalog, frozen token manifest, envelope + terminator
- **Local Regeneration Mode** (zero-paste path) alongside the claude.ai hand-carry
- Tolerant importer + validator + deterministic re-verification + repair-prompt emitter
- **ONE direction generated in full** (Stage A capsules for ~10 to choose from; deep-dive for the pick only)
- Token compiler → CSS custom properties + Tailwind `@theme`, pinned compiler
- **Logical properties only (new, v1 — hard constraint).** The token compiler and every generated component emit `margin-inline-start` / `padding-block-end` / `inset-inline` / `border-inline-start` and never `left` / `right` / `top` / `bottom` / `margin-left` / `text-align: left` in generated CSS. Enforced by **coherence lint 7 (new)**, which rejects physical direction keywords in generated CSS at ingest and at LOCK. **This amends §7.12 and §13 gate 4, which currently read "six coherence lints" — both must be updated to seven; flagged as a cross-section edit this section requires.** RTL *layout and mirroring* stay in v3 (see the v3 list); this line only makes reaching v3 cheap. **[I — that retrofitting logical properties is substantially more expensive than emitting them from the start is Lens 2's assessment, not a measured figure; the FruitSync redo is corroborating first-party evidence, not a measurement of this specific cost]**
- `layout.json` / `content.json` model + pure renderer
- **Section boundary markers (new, v1).** Every section node carries a stable `sectionId` that survives reorder, variant swap and regeneration. **Scoped regeneration accuracy depends entirely on clean boundaries**, so the markers are listed as their own deliverable rather than assumed
- **Editor-lite**: inline text editing (`plaintext-only`), image replace + focal point + alt gate, section reorder, component-bar variant swap with hover-preview and typed slot contracts + content orphanage, navigator tree, undo/redo with transactional grouping, autosave + named snapshots + save-as-variation, **multi-page manager (PROVISIONAL — O10-gated; present under Branch B, absent under Branch A / A+)**, **global regions (PROVISIONAL — O10-gated, same branch)**, per-page SEO fields, in-editor preview mode, Design Health HUD with the v1 live checks
- **Asset library pane (new, v1).** A left-pane searchable library of every uploaded and generated image, icon, pattern and art container, backed by `assets/manifest.json`, with **direction-affinity filter chips**. D1 tags 20 artworks by direction; that tagging is inert without a surface that reads it, and per-slot replacement gives the user no way to see what exists, reuse one asset across sections, or find the token-referencing subset that survives a direction change (A20/A21). The filter chips are also the mechanism §17-R34 names as "what makes 20 legal." Pattern precedent: the `acos-image-builder` left-pane parts library (§16.1)
- **Recovery bin (new, v1).** A persistent deleted-nodes panel backed by a `trash[]` array in the document, with **restore-in-place**. Undo alone cannot answer "I deleted that three edits ago" without also reverting everything since; §12.9's history model is an op log with inverse patches — a time machine, not a bin. A31/A32 cover swap and regeneration undo but not delete recovery. Cheap, because the op log already carries the inverse patch. Retention: unbounded within a project; the bin is stripped at LOCK by purity gate 1
- **Element freeze (new, v1) + the naming rule.** `node.locked` in the document schema, with a per-element freeze affordance that blocks drag, edit and swap on a settled node. **The UI copy for this action is "Freeze" (never "Lock"), because LOCK is this product's terminal publish verb and the collision is a guaranteed confusion source once both concepts exist in one product.** The rule — *element level says Freeze/Unfreeze; site level says LOCK/Unlock; no string in the product may use "lock" for the element concept* — belongs in §11 and in the glossary. Freeze matters even without a canvas, because reorder and swap can also disturb a settled section
- **Duplicate / copy / paste of a block including all its breakpoint overrides (new, v1).** Standard in every builder; it is what stops the user redoing responsive work on every reused block
- **Per-breakpoint visibility (new, v1).** Hide/show a block at a breakpoint, compiled to a `display` rule, **not** to duplicate markup. §20.1 explicitly rejects the two-independent-layouts (Squarespace Fluid Engine) model; rejecting the alternative without shipping the sanctioned mechanism leaves a hole. A lint warns when a block is hidden at *every* breakpoint
- **Per-section notes → scoped regeneration + regeneration log (moved from v2 into v1).** An in-editor note attached to a section ("this hero is too shouty, keep the type, calm the colour") that drives a scoped regeneration of that section only. This is the human-authored replacement for the autonomous VLM critique loop the user rejected (§20.1). Without it, v1's answer to vision Step 5 is only "swap a variant" or "regenerate the whole system" — **there is no middle gear.** It needs no canvas: it works on the section boundaries that reorder already requires. Mechanism is settled by §17-O21 — inline, via Local Regeneration Mode, not another hand-carry. A32 already requires a section regeneration to be a single undo step
- **Artwork — lane decision stated, not deferred (new, v1; closes the scope list's silence on the user's named "background art/style" category):**
  - **Lane A — code-drawn art: IN v1.** SVG scenes, CSS gradient meshes, canvas noise fields, generative patterns, all token-parameterised. **≥60% of the 20 artworks in a generated set must be token-referencing (`currentColor` / `var(--*)`) per A20**, and changing a direction's hue anchors must re-skin them with no regeneration (A21)
  - **Lane B — asset-library ingestion: IN v1.** Detected at Step 0 (A2, question C3), ingested into `assets/manifest.json` with direction-affinity tags and licence class. **This is the lane that actually made the cited FruitSync exemplar work [V — 231 PNGs exported from Unity by `SiteAngryExport.cs`, not produced in a chat]**
  - **Lane C — external raster generation (Midjourney / FLUX / Recraft): OUT of v1**, explicitly, with a named runbook shipped in the skill at `docs/lane-c-raster-runbook.md` covering the separate hand-carry, the per-asset licence manifest entries, and the ingest path. Lane C art that arrives via the runbook is ingested through Lane B's manifest, so nothing in the editor forks
  - **Residual open item — §17-O32 (new):** *for a project that owns no asset library and whose direction genuinely needs photographic or painterly raster art, who produces it?* Lane A cannot, Lane B has nothing to read, Lane C is out of v1. **Requires user decision per project.** The honest v1 answer is "that project either accepts code-drawn art, licences stock through the photo-grade recipe (§7.9 `art.photo-grade-recipe`), or runs the Lane C runbook manually." **No known mitigation that keeps the paste-only path intact.** §17-O7 is narrowed to this residual case and remains open
- **Component additions to the v1 inventory (four items the critics found with no v1 home).** Three of the four already carry a v1 tier in §8.3/§8.4; the other two need a tier change, which is an amendment to §8.3's tier column and is flagged as such:
  | Component | Variants | §8.3 tier today | v1 status here | Rationale |
  |---|---|---|---|---|
  | Third-party video facade | **4** | v2 | **Promoted to v1, conditional** — ships whenever the interview answers indicate any embedded third-party video | A naive YouTube/Vimeo embed costs ~500KB–1MB of pre-interaction third-party JS and can fail gate 20 by itself. **Amends §8.3 (v2 → v1-conditional); requires sign-off as a scope addition** |
  | Cookie / consent banner | **6** | v1 | v1 (confirmed, and now visible in the phase plan) | Legally required where the interview says personal data is collected; it is the first thing a visitor sees. §17-R32 names the risk that six pretty variants whose reject path is harder than accept is a compliance defect that looks like a design success — **reject-as-easy-as-accept is a hard constraint on all six variants, not a guideline** |
  | Cookie preferences centre | **3** | v2 | **Promoted to v1, conditional** — ships whenever the consent banner ships | A consent banner with no preferences surface is not a consent mechanism. **Amends §8.3 (v2 → v1-conditional); requires sign-off as a scope addition** |
  | Visible motion toggle | **3** | v1 | v1 (confirmed) | Required by the prior report's accessibility position **independent of** `prefers-reduced-motion`, because a visitor whose OS setting is off must still be able to stop motion |
  | Favicon / app-icon manifest set | **n/a — derived** from the logo mark: 16/32 ICO+PNG, `apple-touch-icon` 180, maskable 192 and 512, monochrome mask icon, `theme-color` for light and dark, `site.webmanifest` | v1 | v1 (confirmed) + **gate change** | Missing favicons are a classic AI-built-site tell. **§13.6 / gate 22 currently does not check them — favicon and web-manifest completeness is added to gate 22's checklist by this section** |
- Deterministic `variants.ts` (10 per component within the direction — 12 for hero, CTA band, card, badge, feature grid and pricing per §20.2 disagreement 5 — lazy)
- **LOCK** with all five purity gates including two-build byte-equality, re-render not copy-strip, reversible
- **LOCK also strips, and is gated on stripping:** the recovery bin, `node.locked` freeze flags, per-section notes, the asset-library pane and `assets/manifest.json` (the manifest stays in the project and in the evidence bundle, never in the published output). These are new editor-only state introduced above, and D3 requires no editor runtime or editor state reach a visitor
- Full lock-time gate suite (§13.4) with Tier-0/1 enforcement
- Evidence bundle + licence manifest
- Publish (or an explicit runbook, stated)
- `git init`, provenance, session state, resume
- Security posture: 127.0.0.1, Origin allowlist, bearer token, semantic ops, path allowlist, idle shutdown
- Double-fork server + fixed port + curl-across-turn-boundary verification
- `bun selftest.ts`

**Scope cut (explicit):**
- **No canvas drag.** No gridlines, no snapping, no free-position, no zoom/pan. Layout is section reorder + anchor verbs only. **This is vision Step 4(a) and Step 4(b) — see the sign-off table above. It is a deviation from the brief, not a sequencing detail, and D2 is inert in v1 as a direct consequence**
- No per-breakpoint override *authoring* (author at 1280, auto-derive 768 and 390, override only where preflight complains). **Note the deliberate asymmetry:** v1 *does* ship copy/paste-with-overrides and per-breakpoint visibility, because both operate on overrides the preflight already produced; what v1 lacks is a UI for authoring new ones freely
- No rich-text block, no command palette, no rulers/guides, no multi-select/align/distribute
- No custom components beyond the whitelist
- No app-shell, commerce, or exotic-chart inventory
- No version diff, comment pins, share links, real-device preview
- Charts: build-time SVG only, ≤4 mark types
- **No Lane C external raster generation** (runbook only, per the artwork line above)
- **No cross-direction swaps** — only one direction exists in full
- **No RTL layout or mirroring** — but logical properties are mandatory in v1, so v3's RTL work is an addition rather than a rewrite

**Revised v1 effort (amending §17-R18, which does not yet price the additions above) [I — every figure in this table is inference in the same class as §17-R18's own numbers, anchored on comparable open-source editors; none is measured]:**

| Line | §17-R18 as published | Delta from this section | Revised |
|---|---|---|---|
| L1 interview + prompt generator | 2–4 days | +0.25 day (the structural-RTL gate is one question) | 2.25–4.25 days |
| L2 ingest/validate/normalise + token compiler + font catalog + variants | 8–12 days | +0.5 day (coherence lint 7); +1–2 days (Lane A/B artwork ingest + `assets/manifest.json` with direction tags) | 9.5–14.5 days |
| **L3a editor-lite** — Branch A / A+ (single page) | 8–12 days | +0.5 day recovery bin; +0.5 day freeze; +1 day asset-library pane; +1 day duplicate/paste-with-overrides + per-breakpoint visibility; +1–2 days per-section notes → scoped regeneration + boundary markers; +0.5 day page-tree-ready model (Branch A+ only) | **12.5–17.5 days** |
| **L3a editor-lite** — Branch B (multi-page in v1) | not separately priced | O10's "roughly doubles editor scope" applied to the revised L3a | **~25–35 days** |
| **L3b editor-full** (v2 canvas layer) | 30–60 days, and it never feels finished | unchanged | 30–60 days |
| L4 lock/export/publish/evidence | 3–5 days | +0.5 day (favicon/manifest set into gate 22; stripping the new editor-only state at LOCK) | 3.5–5.5 days |
| L5 custom components | ~5 days per family | unchanged | ~5 days per family |

**Smallest genuinely useful v1 (Branch A+): L1 + L2 + L3a + L4 ≈ 28–42 days of the above lines**,
against §17-R18's published "≈ 3–4 weeks." **The published figure is now understated because this
section added scope; that is stated rather than hidden, and the additions are individually
listed above so any of them can be traded back out by the user.**

**Exit criterion:** *One real site built end to end with editor-lite, locked, published, with a
complete evidence bundle and a passing two-build byte-equality check — and the user reports which
operations they reached for that editor-lite could not do.*

**Additional v1 exit conditions added by this revision:**
- *The user has explicitly signed off, before build start, on every row marked **requires user
  sign-off** in the deviations table — in particular that v1 ships with no gridlines and no
  dragging.*
- *§17-O10 has been answered (Branch A, A+ or B) and the v1 scope list's PROVISIONAL markers have
  been resolved to present or absent.*
- *At least one section has been improved via the per-section note → scoped regeneration loop, so
  the "middle gear" answer to vision Step 5 is demonstrated and not merely listed.*
- *The published site passes gate 22 including the favicon / app-icon / web-manifest completeness
  check, and contains zero physical-direction CSS properties in generated output (coherence lint 7).*

That first clause — "which operations they reached for" — is the decision gate for v2.

---

### v2 — "The canvas, if the gate says yes"

**Scope in (conditional on the v1 exit criterion):**
- **The real-grid canvas**: gridline overlay read from `getComputedStyle`, snap engine with priority ordering and tolerance ÷ zoom, smart guides with distance labels, drag-to-place writing grid integers, span resize with the "6 of 12 · 50%" readout, padding/gap handles snapping to the spacing scale, keyboard nudge and grid stepping — **this is where vision Step 4(a) and 4(b) are actually delivered**
- **Per-breakpoint override cascade** with the persistent pre-commit chip, overrides dots, and reset-to-inherited
- **Free-position escape hatch** as anchored-offset, with the counter, auto-demote, and the hard LOCK gate
- Zoom + pan, drag-resizable frame, rulers, fraction-stored guides, multi-select + align/distribute
- Rich-text block (TipTap/ProseMirror, restricted mark set)
- Motion preview toggle, per-container scrub, trigger markers
- Real-device LAN preview
- **Content mode** (no dev server, no design layer)
- **Multi-page manager + global regions, if §17-O10 resolved to Branch A or A+** (under Branch B they shipped in v1). Branch A+ makes this an addition rather than a data migration
- ~~Per-section notes → scoped regeneration, regeneration log~~ — **moved to v1 by this revision.** What remains in v2: the **regeneration timeline UI** (browsing and comparing past regenerations of the same section) and **batch regeneration** across multiple noted sections in one pass
- Version history: timeline, visual diff, non-destructive restore, crash recovery
- Command palette, find/search, breadcrumb navigation, rename, group/ungroup
- Live a11y/contrast lint inline, motion-property lint, text-spacing stress clone, off-token advisory
- Custom code block (the signature moment container) — **this is where vision Step 6's "components not normally included" becomes fully open-ended**
- **All 10 directions generated** (Stage A ~10 capsules + Stage B for 2–3 shortlisted, tournament selection)
- Cross-direction swaps with the coherence-debt ledger and the switch-the-whole-site offer
- Charts: full 12 marks + chrome kit + data states, build-time SVG
- Video player skin (6) and background video loop (5) — the facade was promoted to v1; these two remain v2
- Registry for cross-site component/direction reuse
- Share-for-review read-only link, comment pins
- Second-ruleset Pa11y cross-check, conditional photosensitivity and motion-actuation gates
- **Freeze extended to the canvas**: `node.locked` blocks drag and marquee selection, not only edit and swap

**Scope cut:**
- No app-shell inventory
- No interactive/client-library charts
- No multi-user editing
- No external raster-generation lane (unless §17-O7 / the new §17-O32 forces it)
- No RTL layout/mirroring (v3) — logical properties continue to be enforced by coherence lint 7

**Exit criterion:** *A site with at least four free-positioned elements and per-breakpoint overrides
passes the responsive preflight at 320/390/768/1280/1440 with zero blocking findings, and the
free-position usage counter shows the user reaching for the escape hatch fewer than 3 times per
section on average.*

That second clause is the instrumentation that tells you whether constraint dragging is actually
working (§17-R8). **It is also the first empirical test D2 ever receives (R47), which is why it must
not be softened when v2 runs late.**

---

### v3 — "Breadth, on demand"

**Scope in:**
- App-shell inventory (62 gated items) generated **only** when the site-type answer requires it
- Commerce inventory beyond pricing
- Exotic charts (scatter, heatmap, funnel, radar, waterfall, treemap, map) and interactive/client-library charts
- Canvas/WebGL and particle containers with the GPU-tier ladder
- Gaussian splat embeds
- 3D product viewer
- Cross-project taste profile
- Raw code export / eject, individual asset export
- Device-frame preview, jump-to-section nav
- PostToolUse evidence-mirror hook
- Optical alignment snapping (§17-O29)
- Print state
- **RTL / bidi layout and mirroring** (unless the interview's structural-RTL gate forces it earlier). **Cheap to reach by construction**, because v1 mandated logical properties and coherence lint 7 has been rejecting physical properties since the first generated component. What v3 adds is bidi text handling, mirrored iconography and directional motion, **not** a CSS retrofit
- **Lane C external raster generation as a first-class lane** (if §17-O32 is answered in its favour), with its own licence manifest lane in the evidence bundle
- Auth/dashboard/settings/docs page templates

**Exit criterion:** *An app-shell site type completes the pipeline with every dashboard view
screenshot-verified in populated, empty, loading and error states, and the performance budget still
passes with the chosen chart runtime.*

---

### New cross-reference ids introduced by this section

Continuing the existing numbering; nothing is renumbered.

| Id | Type | Statement |
|---|---|---|
| **R47** | Risk (§17) | v1 ships without exercising D2 at all; the constraint drag model is unvalidated at first ship. Mitigation is partial and detects the problem late by construction **[I]** |
| **O31** | Open question (§17) | Which O10 branch — A (single page), A+ (single page, page-tree-ready model) or B (multi-page in v1)? **Requires user decision before the v1 build starts.** Both branches are costed above; no default is applied silently |
| **O32** | Open question (§17) | For a project with no asset library whose direction needs photographic or painterly raster art, who produces it in v1? **Requires user decision per project. No known mitigation that keeps the paste-only path intact** |
| **O33** | Open question (§17) | Final UI wording for the element-level freeze — "Freeze", "Pin", or another word. **The constraint is settled** (it must not be "Lock"); the word itself is cosmetic and **requires user preference** |
| **A91** | Acceptance criterion (§19) | The asset library pane lists every ingested and generated asset from `assets/manifest.json` and filters by direction affinity |
| **A92** | Acceptance criterion (§19) | A node deleted three or more edits ago is restorable in place from the recovery bin without reverting any intervening edit |
| **A93** | Acceptance criterion (§19) | A frozen node rejects edit, swap and reorder; and no user-visible string in the product uses the word "lock" for the element-level concept |
| **A94** | Acceptance criterion (§19) | Generated CSS contains zero physical-direction declarations; coherence lint 7 fails a component that emits one |
| **A95** | Acceptance criterion (§19) | A section's `sectionId` is unchanged after reorder, variant swap and scoped regeneration |
| **A96** | Acceptance criterion (§19) | Pasting a copied block reproduces all of its per-breakpoint overrides, not only its 1280 state |
| **A97** | Acceptance criterion (§19) | Per-breakpoint visibility compiles to a `display` rule with no duplicated markup, and a block hidden at every breakpoint raises a lint warning |
| **A98** | Acceptance criterion (§19) | Gate 22 fails a site missing any of: 16/32 favicon, `apple-touch-icon`, maskable 192 and 512, monochrome mask icon, `theme-color` for both schemes, `site.webmanifest` |
| **A99** | Acceptance criterion (§19) | A page containing a third-party video loads zero third-party JS before user interaction |
| **A100** | Acceptance criterion (§19) | In all six consent-banner variants, rejecting is reachable in no more interactions than accepting, and the preferences centre is reachable from the banner |
| **A101** | Acceptance criterion (§19) | No v1 evidence bundle contains a Lane C asset unless the Lane C runbook was invoked and every such asset carries a licence-manifest entry |

**Cross-section edits this section requires (flagged, not silently assumed):** §7.12 and §13 gate 4
change from six coherence lints to seven; §13.6 / gate 22 gains favicon and web-manifest
completeness; §8.3's tier column changes for the third-party video facade and the cookie
preferences centre (v2 → v1-conditional); §11 and the glossary gain the Freeze-vs-LOCK naming
rule; §12 gains `trash[]` and `node.locked`; §17 gains R47 and O31–O33 and marks O10 as branched
rather than open-ended; §19 gains A91–A101.

---
## 19. Acceptance criteria

Testable statements. Each maps to a gate, a script, or an observable behaviour.

### Pipeline

| # | Criterion |
|---|---|
| A1 | Running the skill in a project with an existing `.acos/design-library/*/design-system-spec.yaml` offers it as a warm start within the first three exchanges |
| A2 | Step 0 detects an asset library when one exists at a path the user names, and records `assetLibraryPath` in `session.json` |
| A3 | The interview completes with ≤45 answered questions for a single-language, single-surface, no-forms marketing site |
| A4 | Every emitted design directive in the Step-2 prompt cites the interview question ID that produced it |
| A5 | The concept document names at least one thing the site refuses to do, and the pipeline refuses to advance to Step 2 without it |
| A6 | The generated Stage-A prompt contains: the DTCG worked example, the OKLCH-hue warning, the pinned font shortlist with base64 display cuts, the frozen token manifest, the CSP constraint, the 390px preview requirement, and the self-audit instruction |
| A7 | Pasting a **complete** chunk ingests with zero manual file operations beyond one `pbpaste` command |
| A8 | Pasting a **truncated** chunk fails with a message naming the missing files, and does not write a partial system |
| A9 | Pasting a chunk containing `fetch(` in a component quarantines that item, ingests the rest, and reports it in `import-report.json` |
| A10 | A contrast pair claimed as passing but actually failing is detected, auto-nudged, and logged in the substitution log |
| A11 | A font not on the pinned shortlist is substituted with the nearest OFL match in the same classification and logged |
| A12 | Local Regeneration Mode produces a bundle that passes the identical validator with zero pastes |
| A13 | `--resume` after a context reset reconstructs the phase from disk alone, with no reliance on conversation memory |

### Design system

| # | Criterion |
|---|---|
| A14 | Every token in a direction carries `com.acos.llm`, `com.acos.pick`, and `com.acos.direction` extension blocks |
| A15 | The editor renders **no control** for any token with `com.acos.pick.pickable: false` |
| A16 | A token whose `com.acos.direction.vectorHash` differs from the active direction is rejected by the builder |
| A17 | A direction with `elevation.model: border-only` that references any shadow token fails coherence lint 6 |
| A18 | The contrast proof table is all-pass by construction; any failure is reported as evidence of a hand-edited value |
| A19 | Both light and dark schemes are independently solved, and the proof table covers both |
| A20 | ≥60% of the 20 artworks in a generated set are token-referencing (`currentColor` / `var(--*)`) |
| A21 | Changing a direction's hue anchors re-skins all token-referencing artwork with no regeneration |
| A22 | Every motion item has a paired reduced-motion sibling, and the reduced-motion render diff shows a **difference** where motion exists |
| A23 | No custom cursor exceeds 128×128, and every `cursor: url()` declaration has a native keyword fallback |
| A24 | Spacing, type steps, radius scale, shadow scale, and semantic colour roles are all marked `derived` and have no editor control |

### Editor

| # | Criterion |
|---|---|
| A25 | A component can be selected via canvas click, via the breadcrumb, and via the Navigator tree — including a zero-height wrapper and an element fully covered by a background art container |
| A26 | Every drag operation has a single-pointer equivalent (select + click destination, or arrow-key nudge), satisfying WCAG 2.5.7 for the editor itself |
| A27 | Every editor-chrome control measures ≥24×24 CSS px, or satisfies a documented WCAG 2.5.8 exception |
| A28 | A padding drag commits to a named spacing token and displays the token name, never a raw pixel value |
| A29 | A component swap that removes a slot parks the orphaned content in a visible panel; swapping back restores it |
| A30 | A component swap that adds a slot creates a flagged placeholder that **blocks LOCK** until filled or deleted |
| A31 | A component swap is a **single** undo step; one Cmd+Z restores the prior variant completely with no hybrid state |
| A32 | A "regenerate this section" action is a single undo step |
| A33 | Hovering a variant in the component bar previews it live in the real slot with the current copy and neighbours |
| A34 | No two variants offered in the same bar are indistinguishable at 200×120px |
| A35 | Dropping a 4MB photo triggers auto-recompression with a visible, undoable confirmation |
| A36 | Placing an image without alt text or a decorative toggle **blocks the placement** |
| A37 | The Design Health HUD is the only surfacing channel for Tier-2 findings; no Tier-2 finding produces a toast |
| A38 | A component swap replaces the node **in place** in the DOM tree; the tab order before and after the swap is identical for equivalent content |

### Layout

| # | Criterion |
|---|---|
| A39 | The gridline overlay's track positions match `getComputedStyle(section).gridTemplateColumns` exactly |
| A40 | A drag commits an integer `grid-column` / `grid-row`, and the same block occupies 50% width at both 768px and 1440px when spanning 6 of 12 |
| A41 | A block with no small-breakpoint override compiles to `grid-column: 1 / -1` in source order |
| A42 | An edit made at 390px shows a pre-commit chip naming exactly which sizes it will affect |
| A43 | A free-positioned block auto-demotes to normal flow at ≤479px unless explicitly opted in |
| A44 | A free-positioned block that produces document `overflow-x` at any of 320/390/768/1280/1440 **fails LOCK** |
| A45 | A free-positioned block's parent does not collapse (reserved `min-block-size` applied at drop) |
| A46 | Component internals use `@container`, not `@media`; moving a card from a 6-col to a 3-col slot requires no manual fix |
| A47 | Snap tolerance divided by zoom keeps snapping usable at 25% and 200% |
| A48 | Free-position is unavailable by default on a scroll-driven pinned/scrubbed container, and forcing it requires an explicit confirmation |

### Lock and export

> **Dependency note (added in this revision, tracks gap "19 (A49–A59) vs O6"):** §17.4's open question **O6** — whether LOCK is a re-render from `layout.json` or a copy-and-strip of the live design surface — is recorded there as "**Settled here as re-render; confirm with the user**," i.e. **not yet confirmed by the user as of this PRD revision**. Every criterion in this Lock-and-export table (A49–A59) is written assuming the re-render answer to O6. This is the single most consequential architectural decision in the eight steps (§17.4), and the two answers produce materially different export pipelines (fresh compile of documents/tokens vs. snapshot-and-strip of rendered DOM, as FruitSync's precedent did — which required hand-rewriting links and hand-excluding dev pages). **Open question, no known mitigation short of the user decision: if the user instead chooses copy-and-strip, A49–A54, A56, A58, and A59 (all of which assume a documents-to-build-artifact pipeline that can be re-run losslessly) require rewriting, and A51's byte-identical-tree comparison and A59's write-to-new-dir-then-swap guarantee would need to be re-derived against a copy-and-strip implementation before they can be trusted as gates.** Requires user sign-off on O6 before this table is treated as final; do not build against A49–A59 until that sign-off lands.

| # | Criterion |
|---|---|
| A49 | *(contingent on O6 resolving to re-render — see dependency note above)* `grep -r 'data-wb-' dist/published/` returns zero matches |
| A50 | *(contingent on O6 resolving to re-render)* `grep -rE 'astro-dev-toolbar\|/@vite/client\|import.meta.hot\|data-astro-source' dist/published/` returns zero matches |
| A51 | *(contingent on O6 resolving to re-render)* A build with the editor integration installed and a build with it removed from `package.json` produce **byte-identical** `dist/published/` trees |
| A52 | A screenshot of the editor preview at 1280 with chrome hidden and a screenshot of the built page at 1280 differ by zero pixels |
| A53 | *(contingent on O6 resolving to re-render)* `wb verify` produces an empty diff on a freshly generated project, and on the same project after ten drag operations |
| A54 | *(contingent on O6 resolving to re-render)* LOCK writes only to `dist/published/` and `.wb/locks/<iso>/`; `pages/*.doc.json` mtimes are unchanged |
| A55 | UNLOCK is restarting the design server; no transformation is applied to the design project |
| A56 | *(contingent on O6 resolving to re-render)* `git checkout wb-lock/<n> -- pages/ site.json` restores a prior lock's documents without touching `src/overrides/**` |
| A57 | Every declared motion/interaction behaviour is present in `dist/published` (interaction-manifest check) |
| A58 | *(contingent on O6 resolving to re-render)* Unlocking after a hand-edit to the exported tree **shows the diff** rather than silently overwriting |
| A59 | *(contingent on O6 resolving to re-render)* LOCK produces `dist/` via write-to-new-dir-then-swap; no `rm -rf` is executed |

### Quality

| # | Criterion |
|---|---|
| A60 | The locked site renders at 320 CSS px with no two-dimensional scroll except exempted content |
| A61 | A 40-char unbroken token injected into any text block at 320px produces no overflow |
| A62 | +35% pseudolocalised strings produce no overflow or truncation on any page |
| A63 | 200% zoom produces no horizontal scroll and no content loss |
| A64 | A Playwright tab-walk reaches every interactive element, in visual order, with a visible focus ring at ≥3:1 against adjacent colours, and no trap |
| A65 | Full-page axe-core reports zero critical and zero serious findings |
| A66 | LCP ≤2.5s, CLS ≤0.1, and TBT ≤600ms on a median-of-3 mobile Lighthouse run under the documented Slow-4G profile |
| A67 | Pre-LCP transfer is ≤2MB |
| A68 | Every `@font-face` declares `font-display: swap`; exactly the committed families are preloaded; a fourth family introduced by a late swap **fails the gate** |
| A69 | Every page has a unique title, a 50–160-char description, a canonical URL, OG + Twitter tags with an image, a matching `lang`, a single H1 with no skipped levels, and 100% alt coverage |
| A70 | `robots.txt` and `sitemap.xml` are generated from the page tree, and JSON-LD validates against schema.org for the interview's site type |
| A71 | The site renders usably with JavaScript disabled: content visible, nav operable, forms submittable |
| A72 | The evidence bundle contains a licence class for every font and every asset, and says "passed N automated gates" — **never "WCAG AA compliant"** |
| A73 | The evidence bundle contains an explicit "manual and screen-reader review not performed" line |
| A74 | Any commercial-foundry font emits a pre-launch blocker rather than being embedded |
| A75 | No third-party mark (platform badge, social icon, trust badge, map tile) has been redrawn; all are used as supplied |

### Architecture and safety

| # | Criterion |
|---|---|
| A76 | The server binds `127.0.0.1` only; a request from a non-allowlisted `Origin` is rejected on every non-GET and on the SSE upgrade |
| A77 | A request without the session bearer token is rejected |
| A78 | The server writes only to `pages/*.doc.json`, `history.jsonl`, and `.wb/**`, verified by `realpath` + prefix assertion; a symlinked path is rejected |
| A79 | The wire format carries typed semantic ops; a raw JSON Patch or a file path in a request body is rejected |
| A80 | A `curl` to the server's health endpoint in a **separate tool call after the turn boundary** returns HTTP 200 |
| A81 | Claude's `Write` on `pages/*.doc.json` while the editor lock is held is blocked by the PreToolUse hook |
| A82 | A stale save (mtime/hash mismatch) is rejected with 409 and surfaces "reload or force" in the editor |
| A83 | `site/` is its own git repo, and `.acos/website-builder/sessions/*/site/` is in the ACOS `.gitignore` |
| A84 | All new code is TypeScript run by bun; `find` over the skill's `scripts/` and `app/` returns zero `.py` files |
| A85 | `bun selftest.ts` passes with 100% of assertions |
| A86 | Zero files are added to `.claude/agents/` |
| A87 | `Task` does not appear in the skill's `allowed-tools` |
| A88 | The skill is installed globally as a symlink to the git-tracked repo copy, verified by `ls -la ~/.claude/skills/ | grep acos-website-builder` showing `->` |
| A89 | No subagent calls `Write`; all agent-produced code returns as text and is written by the main thread |
| A90 | Phase 0 restates the understood brief and waits for an explicit confirmation before any file write or server launch |

---
## 20. Appendix

### 20.1 Deliberately excluded items, with justification

| Item | Surfaced by | Why excluded |
|---|---|---|
| **VLM aesthetic judge loop / Wigum iteration** | Prior swarm report; Lens 10 | The human replaces the judge by product definition. Porting it re-imports the rejected architecture (R42) |
| **CRDTs (Yjs, Automerge, Loro)** | Lens 4, Lens 6 | One human + one sequential agent. Concurrent multi-writer merge buys nothing and costs an opaque binary doc git cannot diff (§12.9) |
| **File System Access API as the persistence path** | Lens 6 | Chromium-only; Safari has no directory picker, Mozilla published a "harmful" position. Would silently be Chrome-only and still need a server fallback (§12.15) |
| **Building inside GrapesJS / Craft.js / Plasmic / Builder.io / Puck** | Lens 4 | Five distinct sufficient reasons (§16.10). Puck is closest and still fails on grid placement, breakpoint cascade, and React-vs-Astro |
| **New `.claude/agents/` files** | Lens 10 | Human-approval-restricted; `Task(general-purpose)` with prompts in the skill's own dir is the established zero-approval route (§16.5) |
| **`Task` in `allowed-tools`** | Lens 10 | `acos-skill-maker` doctrine says the framework ignores it. The estate contradicts itself; skill-maker is the authority |
| **Puppeteer via the npx-cache `NODE_PATH`** | Lens 10 | The cache can be evicted; ACOS's root `node_modules/` is empty. Chrome CLI is dependency-free and proven in-repo (§16.7) |
| **Copying `server.py` rather than porting it** | Lens 10 | Violates the standing TS/Rust rule; none of the three Python exceptions applies |
| **Per-state colour tokens (Carbon's ~60)** | Lens 2 | M3's 4 state-layer opacities replace them at ~7% of the generation cost, with equivalent coverage. Documented as a lens disagreement (§20.2) |
| **Carbon's ~90 syntax-highlight tokens** | Lens 2 | 12 roles suffice for a marketing site; the granularity is unnecessary |
| **60 pickable state-suffixed tokens in the editor** | Lens 2 | Replaced by a 22-item coverage checklist plus 4 derived opacities |
| **Ten "signature moment" variants** | Lens 3, Lens 8, Lens 11 | Treating the identity-carrying choice as a catalogue pick is the root homogenisation mechanism. 2–3 bespoke concepts instead (§14.7) |
| **Independent per-item picks for derived values** | D1 (settled) | The whole reason D1 was restructured. Enforced structurally via `pickable: false`, not documented (§7) |
| **A separate motion subsystem** | D4 (settled) | Motion is an ordinary system item; animated pieces share the art container (§9) |
| **App-shell inventory in v1** | Lens 3 | 62 items gated behind the site-type answer; including them makes the interview unbearable and the direction prompt unusable |
| **Interactive/client-library charts in v1** | Lens 3, Lens 5 | A charting runtime is real client JS on a static page and may undermine the performance gate. Build-time SVG in v1 |
| **Hard anti-slop blocking at the human-edit layer** | Lens 9, Lens 11 | Contradicts the product premise once a human has deliberately chosen. Demoted to Tier-2 advisory; the hard gate moves upstream to the design-system JSON (§13.8) |
| **Hick's law as justification for small variant sets** | Lens 3 | The wrong model for a feature-sorted thumbnail grid, which supports parallel visual search (§8.5) |
| **A 10-up direction grid** | Lens 12, Lens 11 | Thumbnail grids systematically favour loud, high-contrast directions over subtle editorial ones. Replaced by a tournament (§4 Step 4) |
| **Raw contenteditable on every text node** | Lens 4 | Browser-divergent Enter-key markup and Word-paste pollution. `plaintext-only` on ~90%, a real editor on one block type |
| **`ScrollSmoother`** | Lens 3 | Restructures the DOM. Lenis wraps native scroll so accessibility survives |
| **Loading a Lottie or Rive runtime for a hover effect** | Lens 3 | CSS/GSAP covers micro-interactions at zero runtime cost |
| **A JS router for page transitions** | Lens 3 | Breaks the back button. CSS `::view-transition` degrading to instant navigation instead |
| **Absolute positioning as the free-position implementation** | Lens 12 | Collapses parents and bakes in the authoring viewport. Anchored-offset instead (§11.4) |
| **Two independent layouts (Squarespace Fluid Engine model)** | Lens 4 | Documented overlap epidemic. Desktop-down cascade with sparse overrides (§11.3) |
| **DOM wrappers for hit-testing** | Lens 12 | Removing them at LOCK silently shifts layout via `>`, `:first-child`, and `gap`. Zero DOM injection (§11.9) |
| **HTML→JSON round-tripping** | Lens 6, Lens 12 | The canonical WYSIWYG failure, worse here because Claude also writes the source (§12.1) |
| **Deriving reduced-motion at build time by zeroing duration** | Lens 8, Lens 9 | Produces a broken-looking experience. Art-directed siblings authored at generation time (§7.7) |
| **Rust** | Lens 10 | Nothing here is performance-critical or needs a single binary; the language rule's own guidance says TypeScript |

### 20.2 Disagreements between lenses, and how they were resolved

| # | Disagreement | Resolution | Note |
|---|---|---|---|
| **1** | **Direction count.** Lens 11 argued 6 (Iyengar & Lepper: 6 outperforms 24 on both satisfaction and selection). D1 settled 10. | **10 generated, 6 surfaced by default in a tournament, 7–10 on "see more."** Respects the working-memory ceiling while honouring the settled decision. The tournament format (3 → pick → 3 → pick → head-to-head) is the actual mitigation, not the count |
| **2** | **Whether 10 variants causes choice overload.** Lens 3 said no — the 2015 Chernev meta-analysis found a near-zero mean effect with four engineerable moderators. Lens 11 said yes, citing the jam study. | **Lens 3's reading is correct and more recent**: the jam study is one of the 99 observations in the meta-analysis, and its effect appears specifically under the four moderators. **10 is safe when the moderators are engineered away** (§8.5) — but the 200×120px indistinguishability rule is Lens 11's insight and is retained |
| **3** | **State tokens: Carbon (~60 named) vs Material 3 (4 opacities).** | **M3's state-layer model.** 4 numbers vs 60 tokens, equivalent coverage, dramatically cheaper to generate. The 22-item coverage checklist supplies what Carbon's naming supplied |
| **4** | **Motion duration count: M3's 16 steps vs Carbon's 6.** | **Carbon's 6, scaled by expressiveness.** Carbon's productive/expressive axis IS the derivation D1 needs; M3's 16 is more granularity than a marketing site can use |
| **5** | **Hero variant count: 12 (Lens 3, market-calibrated to Tailwind Plus) vs 10 (D1 default).** | **12.** Hero, CTA band, card, badge, feature grid and pricing get 12; everything else Tier-A gets 10. The rubric double-weights the hero crop |
| **6** | **Typeface.mono: 5 (Lens 2) vs one-per-direction 10.** | **5.** Mono occupies a small, low-identity surface; five moods span it and directions map many-to-one |
| **7** | **Breakpoint authoring: 4 viewports vs "author at 1280, derive the rest."** | **Author at 1280, auto-derive 768 and 390, override only where preflight complains** — in v1. Full per-breakpoint authoring is v2. Each authored breakpoint multiplies the override surface the user must maintain |
| **8** | **Whether the anti-slop lint should be a hard gate.** Prior report said yes; Lens 9 and Lens 11 argued both sides. | **Split by layer**: hard gate upstream on the generated design-system JSON; Tier-2 advisory downstream at the human-edit layer (§13.8) |
| **9** | **CLS target: 0.1 (official Core Web Vitals "good") vs 0.05 (prior swarm report).** | **0.1 is the pass bar; 0.05 is an internal stretch target.** The prior report's number is stricter than the standard and should not become a failing gate |
| **10** | **Whether to include a layers/Navigator panel.** The product brief's Step-4 list omits it; Lens 4, 5 and 12 all independently said it is mandatory. | **Mandatory, v1, with its own effort line.** Canvas clicking provably cannot reach every node |
| **11** | **Editor server: one process or two.** Lens 6 recommended two (astro dev + wb-server) with a note to spike single-origin; Lens 10 implied one. | **Spike both (O4).** Two-origin is the shape Onlook/Stackbit/Tina converged on; single-origin collapses the CORS and postMessage surface to zero |
| **12** | **Whether the claude.ai hand-carry is mandatory.** The product brief treats it as the spine; Lens 7 and Lens 12 both argued it should be optional. | **Both ship in v1.** The hand-carry is the default because the user asked for it; Local Regeneration Mode is a first-class alternative because the hand-carry is the single biggest threat to the tool being used twice |
| **13** | **Effort estimate for the canvas.** Lens 12 gave 30–60 days for L3b; no other lens estimated. | **Adopted with the L3a-first decision gate.** The estimate is inference, but it is anchored on Webflow/Framer/Editor X being multi-year multi-team products, and on GrapesJS/Craft.js/Puck existing precisely because this layer is hard |
| **14** | **Artwork: 20 individual pieces or 20 style sets.** Lens 2 implied pieces for background/hero/spot; Lens 3 implied sets for icons/illustrations/patterns. | **Sets for icons, illustrations, spot graphics and patterns; individual pieces for background scenes and hero artwork.** Flagged as O15 because 20 individual hero illustrations might be exactly what the user meant |

### 20.3 Unverified claims and inference flags

Claims used in this PRD that were **not** independently verified, listed so they can be checked before implementation depends on them:

| # | Claim | Source status |
|---|---|---|
| **U1** | APCA guideline bands (Lc75 body, Lc60 large/bold, Lc45 large-non-text) | Inherited from the prior swarm report's Agent 01, which cited DesignChecker/APCA documentation. **Not independently re-verified this pass.** Use as a stretch target only; WCAG 2 remains the pass/fail gate |
| **U2** | claude.ai per-message and per-conversation output ceilings | 2026 SEO "guide" content gave specific figures and at least one model name that could not be corroborated and appears fabricated. **Explicitly flagged as low-confidence / possibly invented.** Chunk sizes must be set empirically (O2) |
| **U3** | The claude.ai React-artifact import allowlist contents | Commonly reported to include recharts, lucide-react and a Tailwind-like runtime, but not publicly versioned and subject to change. **Sidestepped entirely by targeting vanilla HTML** |
| **U4** | "One live artifact per turn" | Multiple 2026 third-party guides plus support.claude.com converge on the same description, but this is someone else's product surface and can change. Medium confidence |
| **U5** | Rive vs dotLottie runtime sizes (200KB vs 60KB) and payload deltas (50–80% smaller, 40–70% recovered) | Vendor and third-party comparison posts. Directionally reliable; exact figures medium confidence |
| **U6** | Canva's default vs advanced feature surface | Product knowledge, not independently searched this pass. Used only to support the "~30–35 of ~95 features is v1" argument, which stands on other grounds |
| **U7** | Webflow's reputation as the steepest-learning-curve no-code builder | Widely-repeated community commentary, not a primary source. Used to motivate the curated-property-set recommendation, which is independently supported by Framer's Stack abstraction |
| **U8** | The 45–90 minute hand-carry estimate | Inference, sized against first-party artifact counts (30 variant directories, 47 HTML files, 231 PNGs) and observed ~40KB artifact size. The **direction** is certain; the magnitude is estimated |
| **U9** | Base64 WOFF2 subset sizes (8–20KB raw, 11–27KB encoded) | Inference from typical Latin-subset display-face sizes. Verify against the actual catalog before committing to per-artifact budgets |
| **U10** | The ~250-artifact Step-2/3 payload count | Inference from D1 arithmetic against the inventory in §7–§8 |
| **U11** | The "~80% of value from L1+L2+L3a" claim | Inference from what operations a user performs on a marketing site. **This is the claim the v1 exit criterion is designed to test** |
| **U12** | Effort estimates throughout §17-R18 | Inference. Anchored on comparable-project maturity curves, not on measured work |
| **U13** | Style Dictionary v5 / Terrazzo 2.0 DTCG 2025.10 support status | Fetched from vendor docs; version states move quickly. **Re-verify at pin time** |
| **U14** | GrapesJS licence | GitHub API reports NOASSERTION; npm reports BSD-3-Clause. **Re-verify against the actual LICENSE file at pin time** — this discrepancy class is exactly what bites later |
| **U15** | The claim that jurors "recognise builder output instantly" | Prior swarm report Finding 2. Load-bearing for §17-R27's ceiling argument |
| **U16** | VLM recall of aesthetic animation from frame sequences = 0.16 | Prior swarm report Finding 15 / Data Gap 2. The prior report itself flags this area as unvalidated end-to-end |
| **U17** | 35.4% of adults 40+ have vestibular dysfunction | Prior swarm report. Used to motivate reduced-motion as a first-class requirement, which stands regardless of the exact figure |
| **U18** | "~75% of commercial pages launched Q1 2026 carry at least one strong AI-slop signature" | 925studios / Developers Digest analysis. The 1,590-page Show HN breakdown (22/32/46) is the better-sourced figure |
| **U19** | Adobe dynamic-guides patent details (bin selection, candidate segments) | USPTO 7545392 and 11250607/11967010 exist; the described algorithm shape is a reading of them, and the priority ordering and 1/zoom rule are this PRD's inference |
| **U20** | The specific Astro HMR add/remove-file limitation | Reported behaviour; **measure round-trip latency for a move op end to end before designing the editor's live-preview strategy** |

### 20.4 Things to verify before implementation starts

In priority order, all cheap:

1. **The claude.ai artifact font test** (O1) — 60 seconds, determines whether Step 2 can ask for base64 fonts or whether direction selection needs a different mechanism entirely.
2. **The TS detached-spawn turn-boundary test** (O5) — determines whether the language rule and the only proven server recipe can coexist.
3. **Copy-paste fidelity from claude.ai's rendered chat view** — whether triple-backtick fences survive. The entire `FILE:`-header contract depends on it. Test all three paste paths a real user would use (rendered view, per-block copy button, conversation export).
4. **Empirical claude.ai output ceiling** (O2) — sets chunk sizes.
5. **Astro HMR round-trip latency for a move op** (U20) — determines whether the editor needs an optimistic local preview layer.
6. **Single-origin vs two-origin spike** (O4).
7. **The GrapesJS-class licence re-verification at pin time** for every adopted dependency (dnd-kit, TipTap/ProseMirror) — against the actual LICENSE file, not the marketing page.
