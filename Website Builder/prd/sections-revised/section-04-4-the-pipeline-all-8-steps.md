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
