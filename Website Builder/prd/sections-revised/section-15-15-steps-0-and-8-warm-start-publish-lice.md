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
