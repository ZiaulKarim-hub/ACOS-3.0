# Competency Questions — Website Builder (`001-website-builder`)

**Compilation phases 1–2.** Eighteen competency questions, each expanded into a bounded (2-hop) subgraph in `domain-lattice.json` connecting the problem to methods, metrics and standards. **Measured coverage: 18/18 = 100.0%** against the ≥95% target. Coverage is defined as: the CQ node has at least one `method` neighbour, and reaches at least one `metric` node and at least one `standard` node within two hops.

Markers preserved: `[V]` verified, `[I]` inference, `[U]` unsourced. **Every schedule and effort figure is `[I]` with low confidence.**

Each entry records: the question, why a practitioner must answer it, the best answer available at compile time, the residual unknown, and the lattice node ids that carry it.

---

## CQ1 — What distinguishes a site that reads as deliberately designed from one that reads as template-assembled, and which of those properties are machine-checkable versus human-only?

**Why it matters.** This is the product's entire reason to exist. If the distinguishing properties were fully machine-checkable, a generator plus a linter would suffice and no human would need to sit in the browser.

**Best answer at compile time.** The distinction splits cleanly. *Machine-checkable:* the presence of catalogued visual tells (gradient signatures, uniform radii and padding, icon-topped card triads, badge-above-headline heroes, generic stat banners, low-contrast dark mode, glassmorphism); token purity; coherence between elevation model and shadow usage; motion-kind restraint; whether ≥3 references were triangulated and whether any single reference dominates. *Human-only:* whether the result is good. The resolution the PRD reaches is **split by layer** — a hard anti-slop gate upstream on the generated design system, before the human ever sees the menu, and a dismissible Tier-2 advisory downstream after a deliberate human choice, because mechanically blocking a chosen direction contradicts the premise `[V — §13.8]`. A separate, structural mechanism matters more than any lint: the signature moment must be a bespoke concept per direction, not a catalogue of ten, because treating the identity-carrying choice as a generic pick **is** the root homogenisation mechanism `[V — §14.7, §20.1]`.

**Residual unknown.** Whether the tell catalogue stays predictive as generation models change; the claim that observers recognise builder output instantly is `[U — U15]` and is load-bearing for the quality-ceiling argument.

**Lattice:** `cq01` → `m_antislop_upstream_gate`, `m_direction_tournament`, `m_signature_moment_concept`, `m_human_sole_judge`, `m_reference_triangulation` → `k_slop_tell_count`, `k_reason_recorded`, `k_reference_overlap`, `k_directions_surfaced` → `s_trade_dress`, `s_token_interchange`. Contradicted by `ap_catalogue_signature`, `ap_hard_aesthetic_block`, `ap_n_up_grid`.

---

## CQ2 — Which layout model survives 320–1440px with no manual responsive work by the author, and what does the market record say about constraint editors?

**Why it matters.** This is the difference between a site that works on a phone and a fixed canvas wearing a responsive costume.

**Best answer.** A **four-level contract**: page is a reorder-only vertical list of sections; section is a real CSS grid; block is integer `grid-column`/`grid-row` placement per breakpoint; inside a block is flow only, never coordinates `[V — §11.1]`. Breakpoint overrides cascade **desktop-down and one direction only**, with sparse overrides — three shipped builders converge on this and the one that ships two independent per-breakpoint layouts has a documented overlap epidemic `[V — §11.3, four vendor sources fetched]`. The single most load-bearing rule is that a block with **no** small-breakpoint override compiles to full width in source order, which prevents the overlap half of that failure by construction. Component internals key off `@container`, not `@media`, so moving a card between slots of different widths needs no manual fix `[V — §11.5, A46]`.

**Market record.** The constraint editor is the one that died: the closest commercial analogue was sunset, an earlier free-canvas product was discontinued, and the surviving bidirectional cascade is a recurring source of user confusion `[V — §11.3, §17-R8]`. This is a risk the product accepts knowingly, mitigated by exactly three verbs, a pre-commit chip, and visible override indicators.

**Residual unknown.** Whether three verbs plus a chip is enough to keep the tool from feeling like it fights the user. Demo 3 is the test.

**Lattice:** `cq02` → `m_four_level_layout`, `m_desktop_down_cascade`, `m_fullbleed_sm_default`, `m_container_queries`, `m_grid_integer_placement`, `m_named_areas_promotion` → `k_reflow_320`, `k_overflow_x_assert`, `k_grid_track_match`, `k_override_count` → `s_wcag_1_4_10`, `s_baseline_platform`. Contradicted by `ap_two_independent_layouts`.

---

## CQ3 — How must a visual editor represent its document so the DOM is never the source of truth, and what specifically breaks when it is?

**Why it matters.** Every product that reconstructs a document from rendered markup is lossy exactly where anchors, variants and intent live — and here it is worse, because an AI agent is also writing that source.

**Best answer.** **Two-tier truth** `[V — §12.1]`: composition (the per-page document plus the content file) is the only thing the editor mutates; implementation files are versioned on disk; the rendered site is produced by a pure function of document, system lock and library and is **never parsed back into JSON**. The renderer must be **total**, not partial: every component, variant, motion, asset and token reference resolves, or the migration policy fires — unknown component is a hard fail with a named report, unknown variant falls back to a canonical variant carrying a per-node flag that blocks LOCK until acknowledged, and orphaned slot content is parked, never deleted. Hit-testing uses attributes on elements that **already exist**, plus one sibling overlay outside the layout root; injected wrappers change what child, first-child and gap selectors match, so removing them at LOCK silently shifts the layout by amounts nobody can explain `[V — §11.9]`.

**What breaks when the DOM is truth.** Comments vanish, formatting normalises, hand-tuned rules are rewritten, and diffs become unreviewable — the canonical WYSIWYG failure, with the agent-authored-source multiplier on top.

**Residual unknown.** None material at the model level; the open work is the naming reconciliation (NA-07) and the per-page-versus-site-wide scope of the command stack.

**Lattice:** `cq03` → `m_two_tier_truth`, `m_pure_render`, `m_typed_semantic_ops`, `m_annotation_by_descent`, `m_zero_dom_injection`, `m_canonical_serialisation` → `k_verify_empty_diff`, `k_unresolved_refs`, `k_canonical_diff_zero`, `k_screenshot_diff_delta` → `s_rfc6902`, `s_token_interchange`, `s_sha256`. Contradicted by `ap_html_json_roundtrip`, `ap_dom_wrappers`.

---

## CQ4 — What does a snap-to-gridline canvas require, and what is the minimum viable version of each part?

**Why it matters.** This is the product's headline gesture and, by DECISION-1 option B, v1 scope.

**Best answer, part by part.**
- **Gridline derivation** — read the resolved template columns from the section and paint those exact tracks. Never a decorative grid; the overlay **is** the snap target, and it lives outside the preview frame so it disappears at LOCK by construction `[V — §11.2, §11.9]`. *Minimum:* columns only, no row rendering.
- **Column derivation** — integer rounding of pointer position against column width plus gap; persist start and span, which is inherently fluid `[V — §11.2]`.
- **Row derivation** — an explicit row axis sized from the direction's spacing scale, with a sanity cap that rejects runaway drags rather than silently clamping `[V — §11.2.1]`.
- **Occupancy** — displace-down by default with a live ghost preview of every block that will move **before** release; z-stacking only for art containers or an explicit per-drop opt-in, both counted by a visible lint `[V — §11.2.1]`.
- **Cross-section drops** — re-parent, leave the vacated cell empty, and run **no auto-compaction anywhere**, because compaction moves blocks the user did not touch `[V — §11.2.1]`.
- **Snap priority** — grid lines, then sibling edges and centres, then padding and content rails, then spacing-scale increments, over two one-dimensional interval indexes per section. *Minimum:* grid lines only.
- **Tolerance** — 6–8 px **divided by zoom**; a classic regression if missed `[V — §10.1, A47]`.
- **Smart guides** — dashed guides with live distance labels and equal-spacing indicators. *Minimum:* alignment guides without labels.
- **Keyboard parity** — arrow nudges one cell, shift-arrow changes span, tab walks siblings. **Not optional:** this is the single-pointer alternative that keeps the editor itself conformant.

**Residual unknown.** The effort figure for this layer (30–60 days, "and it never feels finished") is `[I]`, anchored on comparable products being multi-year multi-team efforts.

**Lattice:** `cq04` → `m_gridline_overlay_computed`, `m_snap_priority_index`, `m_tolerance_div_zoom`, `m_smart_guides`, `m_keyboard_parity`, `m_drop_algorithm`, `m_precommit_chip`, `m_anchored_offset`, `m_flow_fallback` → `k_grid_track_match`, `k_snap_usable_zoom`, `k_target_size_24`, `k_overflow_x_assert`, `k_free_position_count`, `k_override_count` → `s_wcag_2_5_7`, `s_wcag_2_5_8`, `s_wcag_1_3_2`, `s_wcag_2_4_3`, `s_baseline_platform`. Contradicted by `ap_decorative_grid`, `ap_raw_absolute`.

---

## CQ5 — Which design-system values MUST be derived rather than picked, and what does the token standard cover?

**Why it matters.** D1 exists because ~80 independently-picked items cannot stay coherent.

**Best answer.** A direction is a **24-slot varying identity vector plus 2 invariant records** `[V — §7.0]`. Everything else is either a pure function of that vector plus shared seed tables, or a direction-bound authored artefact that carries a direction id and is validated against the vector without feeding its hash. **Derived, never picked:** spacing scale, type steps, radius scale, shadow scale, semantic colour roles, state-layer opacities, motion durations and easings scaled by expressiveness, and font fallback metrics computed from the actual selected font binary `[V — §7, §13.4 gate 21, A24]`. Enforcement is **structural, not documentary**: derived tokens carry a non-pickable flag and render no editor control, and repickable rows must ship a per-direction validity list whose absent options are **hidden from the UI**, not merely warned about — a row that cannot supply one is demoted rather than given a control "for now" `[V — §7.0.2]`.

**Volume.** Real systems ship 250–350 semantic tokens; the budget here is **~600–900 resolved tokens per direction** `[V — counted programmatically from three shipped systems]`. The user's "~80 items" is an item count, each expanding to 1–40 tokens.

**Residual unknown.** Springs sit **outside** the interchange standard, so every tool in the chain must agree one extension shape or motion silently degrades to none `[I — R38]`. And re-resolving hundreds of custom properties per drag is a real reflow cost, which is why they compile to a flat variable layer once per direction change `[I — R30]`.

**Lattice:** `cq05` → `m_derived_value_computation`, `m_frozen_token_manifest`, `m_validity_list`, `m_flat_variable_layer`, `m_motion_token_extension`, `m_coherence_lints` → `k_pickable_false_coverage`, `k_resolved_token_count`, `k_core_web_vitals`, `k_motion_kind_count` → `s_token_interchange`, `s_baseline_platform`. Contradicted by `ap_independent_picks`.

---

## CQ6 — What mechanism makes a local server survive this harness's turn boundary, and which pure-TypeScript candidates are proven?

**Why it matters.** The editor's entire premise is a long-running local server, and this is the single blocking unknown of the product.

**Best answer.** **None of the pure-TypeScript candidates is proven.** First-party evidence across four documented attempts shows detached children reaped and backgrounded servers terminated at the turn boundary; only a double-fork daemon in another language has been observed to work `[V — first-party, R5]`. The response is procedural, not architectural: run the turn-boundary probe **first**, walk the ladder — detached spawn with unref, double fork (noting that the usual session-detach binary does not exist on this machine), a short shell launcher, a sign-off-gated shim, and finally a user-run terminal — and take the first passing rung `[V — §16.6.3]`. Liveness is proven only by a health request **in a separate later tool call** plus confirmation that the recorded process is still present; a same-turn success proves binding, not survival. The server binds a fixed loopback port, records port, pid, url and session id at boot, regenerates if stale, and shuts down when idle.

**Residual unknown.** If the pure-language rungs all fail and both sign-off-gated rungs are refused, **there is no known mitigation** and the browser-editor premise must be rescoped. That statement is deliberate and is not softened anywhere in this pipeline.

**Lattice:** `cq06` → `m_gate16a_probe`, `m_launcher_ladder`, `m_fixed_port_state_json`, `m_second_curl_separate_call`, `m_idle_shutdown`, `m_reattach_not_relaunch` → `k_post_boundary_200`, `k_pid_alive` → `s_acos_harness`, `s_language_rule`. Contradicted by `ap_background_task_server`, `ap_same_turn_liveness`.

---

## CQ7 — Which concurrency protocol prevents silent work loss between an AI session and a browser editor writing the same documents?

**Why it matters.** The product actively encourages alternating between conversation and dragging, which makes two-writer loss near-certain rather than a corner case.

**Best answer.** Layered, with the layers explicitly ranked by how much they are worth `[V — §12.7]`:
1. **Reconciliation is authoritative.** A journal of path, hash, mtime and sequence plus a filesystem watch; any document-owned file whose on-disk hash differs from the journal without a corresponding server-issued write is an out-of-band mutation — the editor refuses to save over it, shows both versions, and offers reload, keep-mine or manual merge. **This is the only mechanism that holds regardless of how the write happened.**
2. **A pre-tool guard** blocking writes on document-owned paths and scanning shell command text — **stated honestly as a defeatable heuristic**, not a boundary.
3. **Read-only file modes while the lock is held** — a speed bump against accidents, since both processes run as the same user.
4. **Repository hygiene** — generated-file attributes, a pre-commit hook, and a banner naming the file to edit instead.

Two further pieces are load-bearing: the agent must be given a **legal write path** (post the same typed op through the same server), because forbidding without providing is how guards get routed around; and writes use optimistic concurrency with a conflict status plus a reload-or-force choice.

**Residual unknown.** Whether a separate user or container is ever justified for a local skill (recorded as an open item, out of scope).

**Lattice:** `cq07` → `m_one_writer`, `m_hash_journal_reconciliation`, `m_optimistic_concurrency_409`, `m_editor_lock_tab_claim`, `m_wb_op_cli`, `m_ownership_guard_hook` → `k_conflict_surfaced`, `k_stale_save_409` → `s_http_etag_409`, `s_sha256`, `s_rfc6902`, `s_acos_harness`.

---

## CQ8 — What controls stop a localhost design server from being a remote-code-drop?

**Why it matters.** A recorded vulnerability class establishes that loopback services are reachable from hostile pages, and this server accepts imported code that a development server then evaluates and bundles into the published site.

**Best answer.** Six controls, all required together: loopback-only binding; an Origin allowlist enforced on every non-GET **and on the event-stream upgrade**; a per-session bearer token stored with restrictive permissions; a **typed semantic-op wire format** (a raw patch or a file path in a request body is rejected — an arbitrary pointer operation could rewrite the system lock or inject an override path); a path allowlist verified by resolving the real path and asserting the prefix, with symlinks rejected; and idle shutdown. On the import side: validate against the envelope, walk the syntax tree for forbidden interfaces, quarantine offending items and ingest the rest, and never partially apply `[V — §16, §12.13, A76–A79]`.

**Residual unknown.** None material; the controls are conventional and the failure mode is well documented. The residual is discipline — the guard is cheap and fail-open by design, so it must not be treated as a security boundary.

**Lattice:** `cq08` → `m_six_control_posture`, `m_realpath_prefix_assert`, `m_typed_semantic_ops`, `m_idle_shutdown`, `m_ast_forbidden_api_walk` → `k_origin_token_reject`, `k_symlink_reject`, `k_quarantine_count` → `s_cve_dns_rebind`, `s_rfc6902`, `s_http_etag_409`. Contradicted by `ap_raw_patch_over_http`.

---

## CQ9 — How does a build PROVE zero editor runtime shipped, and is byte-reproducibility achievable?

**Why it matters.** D3 promises a provably clean export, reversibly. A promise without an executable assertion is a claim.

**Best answer.** LOCK is `build → scrub → assert → snapshot`, a **re-render with the editor disabled**, never a copy-and-strip — the first-party copy-and-strip precedent required hand-rewriting every link and hand-excluding development pages `[V — §12.5]`. Five layered mechanisms keep the editor out of the publish graph entirely, and **eight purity gates** assert it: editor-string grep; two-build equality; published script size step; screenshot diff between the chrome-hidden preview and the built page; interaction-manifest check; zero unresolved references and zero unacknowledged migration flags; **zero design-time origins** (a hardcoded loopback image URL passes gates 1–5 and 404s for every visitor); and a verify-clean check that also re-serialises every document into canonical form.

**Byte reproducibility.** **No consulted source establishes that the bundler produces byte-identical output across two installs of the same lockfile** `[V — recorded as an open question in §12.5]`. The generator's own determinism is controlled (frozen clock, sorted keys, relative paths, fixed collator, stable ids, pinned asset encoder); the bundler's is not. The documented fallback is a normalised comparison with a named, enumerated, individually justified exception set — which **weakens D3's proof from "byte-identical" to "identical except for N declared files" and therefore requires sign-off**. A gate that fails spuriously gets disabled by whoever is trying to ship, which is why the fallback exists at all.

**Residual unknown.** The reproducibility spike's outcome, and the toolchain reconciliation recorded as NA-11.

**Lattice:** `cq09` → `m_lock_rerender`, `m_two_config_two_outdir`, `m_purity_gates`, `m_two_build_manifest_compare`, `m_normalised_comparison_fallback`, `m_deterministic_generation`, `m_verify_regenerate_diff`, `m_write_new_dir_then_swap` → `k_zero_editor_strings`, `k_byte_manifest_equal`, `k_design_time_origins`, `k_dist_js_size`, `k_screenshot_diff_delta`, `k_verify_empty_diff`, `k_unresolved_refs`, `k_lock_wallclock` → `s_source_date_epoch`, `s_sha256`. Contradicted by `ap_copy_and_strip`.

---

## CQ10 — What licence classes and per-asset metadata must be recorded for every shipped font and asset?

**Why it matters.** Legal exposure concentrates in fonts and assets, and a build-failing completeness gate is one of the eight v1 ship criteria.

**Best answer.** Per font: family, foundry, licence class (open / delivery-restricted / commercial-required), file hash, source URL, attribution requirement — and a **commercial foundry face emits a pre-launch blocker rather than being embedded** `[V — §15.6, A74]`. Per asset: generator, model, plan tier, licence class, prompt, alt text and source. Per third-party mark: the usage rules and confirmation it was **used as supplied, not redrawn** — a generated platform badge is a trademark violation, not a design choice `[V — A75, R23]`. The manifest doubles as the **reference allowlist**: every referenced url, family, vector identifier and asset path in built output must resolve to a manifest entry **and** to a real file on disk, with zero remote hosts — which closes a distinct failure class from licence completeness, because completeness confirms every *recorded* asset carries a licence and says nothing about whether every *referenced* asset exists `[V — §13.4 gate 23a]`. Open-licence terms govern what may be embedded, subsetted and redistributed, which is what makes the pre-subsetted base64 catalog legal as well as necessary.

**Residual unknown.** Third-party licence strings decay and disagree across sources — one adopted dependency reports different licences on two registries and must be re-verified **against the actual licence file at pin time** `[U — U14]`.

**Lattice:** `cq10` → `m_licence_manifest_allowlist`, `m_font_catalog_presubset`, `m_commercial_foundry_blocker`, `m_third_party_as_supplied` → `k_licence_coverage`, `k_asset_ref_resolution`, `k_font_fallback_cls` → `s_ofl`, `s_trademark_practice`, `s_csp_artifact`.

---

## CQ11 — Which accessibility properties are reliably machine-checkable, what fraction does automation catch, and how must claims be worded?

**Why it matters.** The product replaces the AI *aesthetic* judge with a human but does **not** add a human *accessibility* judge.

**Best answer.** Reliably machine-checkable: contrast ratios on both text and non-text; target sizes via bounding rectangles; rule-engine findings on a scoped subtree and on the full page; overflow and clipping; focus-not-obscured intersections; reading-order-versus-visual-order divergence as a heuristic; reduced-motion sibling presence; alt/decorative presence; reflow at the narrowest width; text-spacing stress; 200% zoom; skip-link presence and first-tab-order; pause affordance resolution on continuous motion; and keyboard tab-walk order, traps and ring visibility.

**Two criteria apply to the editor itself**, which is the most product-specific accessibility fact in the source: dragging movements must have a single-pointer alternative — *the entire design surface is a dragging interface, so without select-then-click, arrow nudge and span steppers the editor itself fails* — and every piece of editor chrome must meet the minimum target size, checked live on render `[V — §13.2, quoted from the specification]`.

**The coverage number.** Automated testing catches **57.38%** of real issues across 13,000+ page-states and roughly 300,000 issues `[V — vendor coverage report]`. Running several engines raises the floor but does not close the gap. **Therefore the only honest claim is "passed N automated + structural gates," never a conformance claim**, and the evidence bundle carries an explicit "manual and screen-reader review not performed" line. The perceptual contrast model is advisory only — a draft with no independent legal standing — so the gate is dual: pass the legally standing ratios, compute the perceptual value as a stricter internal target `[V — §13.10]`; the specific perceptual bands are `[U — U1, inherited and not re-verified]`.

**Residual unknown.** Nothing about the *fraction*; the residual is organisational — never letting a marketing sentence promote a gate count into a conformance claim.

**Lattice:** `cq11` → `m_scoped_axe`, `m_second_ruleset_crosscheck`, `m_dual_contrast_gate`, `m_tab_walk`, `m_disclosure_statement`, `m_keyboard_parity`, `m_pause_affordance` → `k_axe_critical_serious`, `k_contrast_ratio`, `k_apca_lc`, `k_automated_coverage`, `k_skip_link_first_tab`, `k_target_size_24`, `k_pause_affordance_resolved` → `s_wcag22_aa`, `s_wcag_2_5_7`, `s_wcag_2_5_8`, `s_wcag_2_4_1`, `s_wcag_2_4_3`, `s_wcag_1_4_11`, `s_wcag_1_4_12`, `s_wcag_4_1_3`, `s_wcag_2_2_2`, `s_apca_draft`. Contradicted by `ap_conformance_claim`.

---

## CQ12 — How can motion quality be judged when the editor runtime fights the site runtime?

**Why it matters.** Motion is a first-class design-system item by D4, and it is the one dimension the product cannot verify.

**Best answer, honestly bounded.** Smooth-scroll wrappers interpolate scroll position and transform-based animation poisons measured rectangles, so the editor's measurement layer and the site's motion layer cannot share a page. **Motion is therefore disabled in edit mode and judged in preview — and that is not a solution, it is the problem restated** `[V — R14, recorded as having no known mitigation]`. What *can* be enforced deterministically: a closed trigger enum with a typed viewport threshold; a mandatory reduced-motion sibling reference whenever a container is motion-capable, art-directed at generation time rather than derived by zeroing durations; a mandatory pause affordance reference on continuous motion, which makes an unpausable ticker structurally unbuildable rather than caught late; per-kind cost classes with concurrency caps checked structurally before any render pass, plus a **live counter so the count accumulates visibly instead of surfacing at LOCK**; and a static motion lint for non-compositor properties, out-of-band durations and missing preference queries.

**What must not be done.** Automated recall of aesthetic animation is measured low `[U — U16, and the source itself flags the area as unvalidated end to end]`, so acceptance rests on the human plus deterministic lint and **never** on an automated visual score. Porting a scoring loop re-imports the rejected architecture.

**Residual unknown.** The concurrency caps are carried from prior research and **not benchmarked against this render stack** — a starting default, not a validated ceiling. The motion-kind homogeneity threshold is likewise a carried-over default `[I]`.

**Lattice:** `cq12` → `m_motion_disabled_in_edit`, `m_motion_lint`, `m_reduced_motion_sibling`, `m_motion_concurrency_counter`, `m_pause_affordance`, `m_container_contract` → `k_vlm_motion_recall`, `k_motion_kind_count`, `k_motion_concurrency`, `k_capture_matrix`, `k_pause_affordance_resolved` → `s_prefers_reduced_motion`, `s_wcag_2_2_2`, `s_wcag_2_3_1`, `s_wcag_2_5_4`, `s_wcag_4_1_3`, `s_core_web_vitals`.

---

## CQ13 — What ingest protocol makes a manual copy-paste channel safe against BOTH silent truncation and code injection?

**Why it matters.** A truncated payload is syntactically valid and renders, so a partial design system is accepted with no error anywhere in the pipeline; and the same channel is an unauthenticated code-import path whose payload gets evaluated and bundled.

**Best answer.** **Against truncation:** an envelope manifest declaring the file list, per-file line counts and hash prefixes, ordered smallest-first, closed by a **per-run random terminator**; a tolerant fenced-block parser that validates against the envelope rather than trusting the channel; and a **hard refusal** that names the missing files and writes nothing partial `[V — R3, A8]`. **Against injection:** a syntax-tree walk for forbidden interfaces (network, clock, randomness, environment), per-item quarantine that ingests the remainder and reports the offender with its snippet, and an emitted repair prompt `[V — A9]`. **Against dishonest claims:** deterministic local re-verification of every claimed contrast pair and every font licence, with auto-nudges and substitutions logged — the payload's own assertions are never trusted `[V — A10, A11]`. And a supported template-version range with a defined upgrade path.

**The structural escape.** Local regeneration runs the identical prompt with zero pastes and must pass the **identical validator** `[V — A12]`. That is what makes the manual channel a preference rather than a dependency.

**Residual unknown.** Whether fenced blocks survive all three realistic paste paths from the rendered chat view — named as a cheap pre-implementation check, because the entire file-header contract depends on it.

**Lattice:** `cq13` → `m_envelope_manifest`, `m_tolerant_block_parser`, `m_quarantine_repair`, `m_ast_forbidden_api_walk`, `m_deterministic_reverification`, `m_local_regeneration_mode` → `k_ingest_refusal`, `k_quarantine_count`, `k_contrast_ratio`, `k_licence_coverage`, `k_pastes_per_chunk` → `s_sha256`, `s_cve_dns_rebind`, `s_wcag_1_4_11`, `s_generation_surface_limits`.

---

## CQ14 — How do variant systems avoid choice overload and indistinguishability, and what selection UI beats an N-up grid?

**Why it matters.** D1 sets ten variants per swappable component and ~10 directions per project; presented badly, that is a wall.

**Best answer.** First, **define the unit**: a variant is a *structurally distinct composition of the same component within one direction*; size, theme, density, state, icon slot and semantic colour are computed axes and never count against the budget — without that line the budget silently multiplies by roughly twenty, which is exactly why two commercial libraries report "5 buttons" and "940 variants" for the same product category `[V — §8.1, both sources fetched]`. Distinctness is then machine-checkable via a per-component **axis vector**. Second, **cap what is simultaneously visible**: a bracketed tournament rather than an N-up grid, because thumbnail grids systematically favour loud high-contrast directions over subtle editorial ones; roughly six surfaced by default with the rest on demand `[V — §20.2]`. Third, **enforce distinguishability**: no two variants in the same bar may be indistinguishable at thumbnail size. Fourth, **preview in context**: an isolated thumbnail cannot show fit, so hovering ghosts the variant into the real slot with the current copy and neighbours. Fifth, **generate lazily** on first panel open, cached per direction, never for unused families — eager generation stalls selection at the exact moment the user is waiting.

**The literature disagreement, resolved.** An older single-study reading argues fewer options always win; the 2015 meta-analysis finds a near-zero mean effect with four engineerable moderators. The meta-analysis reading is adopted — **ten is safe when the moderators are engineered away** — while the indistinguishability rule from the opposing lens is retained `[V — §20.2 row 2]`.

**Residual unknown.** Whether affinity filter chips are sufficient to make a twenty-piece artwork set usable; recorded as the mechanism that "makes twenty legal" `[I]`.

**Lattice:** `cq14` → `m_direction_tournament`, `m_lazy_variant_generation`, `m_variant_axis_vector`, `m_indistinguishability_rule`, `m_hover_preview_in_context`, `m_filter_chips`, `m_typed_slot_contract` → `k_indistinguishable_pairs`, `k_variants_per_family`, `k_directions_surfaced`, `k_unresolved_refs` → `s_aria_apg`, `s_wcag_1_4_13`, `s_wcag_2_5_8`, `s_core_web_vitals`. Contradicted by `ap_n_up_grid`.

---

## CQ15 — How is undo kept coherent across AI-driven bulk mutations, and where does delete-recovery belong?

**Why it matters.** This is where AI-editing tools fracture, and it fails precisely when the safety net matters most.

**Best answer.** **One** command stack over the document, covering canvas drags, inspector edits and text edits alike — split stacks are a classic confusing regression — with a continuous drag coalesced into a single entry `[V — §10.4]`. The client stack **mirrors** rather than independently computes the server-authoritative op log: each entry carries the forward patch and its inverse, so undo survives a reload and doubles as an agent-versus-human audit trail. **Transactional grouping is mandatory**: a component swap or a section regeneration is *one* undo step, because naive per-mutation undo leaves a broken hybrid after a single keystroke; this needs dedicated test coverage. Durability is layered — the op log plus atomic write-then-rename plus a journal update in the same critical section — with version-control commits at **milestones only**, because a commit per drag produces thousands per session and makes history useless exactly when it is needed.

**Delete-recovery does not belong in undo.** "I deleted this three edits ago" is common, and chaining undo back would revert everything since — so the recovery bin is an independent store with restore-in-place `[V — §10.2]`.

**Residual unknown.** Whether the command stack is per-page or site-wide is **not stated anywhere in the source**, and multi-page is v1 scope, so "undo an edit on a page I have since navigated away from" has no defined behaviour. The recommendation on record is a single site-wide stack keyed by page id; adopting it requires a matching update to the persistence section `[I]`.

**Lattice:** `cq15` → `m_single_command_stack`, `m_transactional_grouping`, `m_op_log_inverse`, `m_recovery_bin`, `m_milestone_commits` → `k_single_undo_step`, `k_canonical_diff_zero` → `s_rfc6902`, `s_sha256`. Contradicted by `ap_per_save_commit`, `ap_localstorage_blob`.

---

## CQ16 — What warm-start split preserves reuse without homogenising a portfolio?

**Why it matters.** Warm start and redesign pull in opposite directions; the failure is invisible until there are three sites.

**Best answer.** A named split `[V — §15.3]`. **Always carried forward:** token-name schema, component slot contracts, motion-primitive library, font catalog, anti-slop deny-list, editor configuration, and user-level interview answers (accessibility posture, device assumptions, decision style). **Never carried forward by default:** hue anchors, type pairings, radius and density, motion character, artwork, grid personality, and the signature moment. Prior identities are then injected into generation as **negative constraints** — do not produce a direction within a stated angular neighbourhood of these hues, or reusing these type pairings — unless the user explicitly declares the new site a sibling of an existing one. Discovery itself is a glob over known library paths, not new infrastructure. Divergence is additionally forced by assigning each generated direction a position on a divergence axis, because ten directions generated without that constraint converge on the mean.

**Residual unknown.** The angular threshold and the single-reference overlap threshold are stated defaults, not measured `[I]`. Homogenisation is only observable across three or more sites, so the first real test of this answer is a year out.

**Lattice:** `cq16` → `m_warm_start_glob`, `m_system_identity_split`, `m_negative_constraints`, `m_forced_divergence_axis` → `k_hue_distance`, `k_directions_surfaced` → `s_token_interchange`, `s_trade_dress`, `s_acos_skill_contract`.

---

## CQ17 — Which capture protocol produces valid evidence for viewport-height-dependent layouts?

**Why it matters.** A hero approved at a height no device has is the single most reliable way to ship a broken first impression.

**Best answer.** The preview must be a **same-origin frame**, because a scaled element cannot evaluate media queries against a simulated width while a frame's own viewport is exactly what those queries see `[V — §11.7, vendor documentation fetched]`. The trap is that every shipped default uses automatic height, so any viewport-height rule measures the expanded frame rather than a phone. **Fix: pin real device sizes** — the four named width-by-height pairs — for both the preview frame and the capture window whenever the page contains any viewport-height rule, and **assert the measured height** rather than assuming a configuration was honoured. Capture itself is dependency-free headless browser CLI with a non-empty-output assertion, using the inherited wait recipe: navigate rather than set content; wait for network idle with a load fallback; strip lazy loading; await fonts ready **plus** per-image decode; allow a deferred-style settle. And `await document.fonts.ready` before **any** measurement, in the editor as well as in capture, or font-load drift poisons the numbers.

**What makes a capture invalid as evidence.** A full-page tall capture is valid for content review **only** — it cannot evidence hero framing, because the framing question is precisely what a real device height determines.

**Residual unknown.** None material. This is the best-evidenced answer in the set.

**Lattice:** `cq17` → `m_device_height_pinning`, `m_iframe_height_assert`, `m_chrome_cli_capture`, `m_capture_wait_recipe`, `m_same_origin_iframe` → `k_capture_matrix`, `k_iframe_height_measured` → `s_wcag_1_4_10`, `s_core_web_vitals`, `s_baseline_platform`, `s_acos_harness`. Contradicted by `ap_autoheight_preview`.

---

## CQ18 — What is the real output ceiling on the generation channel, and how does it set the chunking strategy?

**Why it matters.** Chunking is what makes the hand-carry survivable, and a wrong ceiling silently produces truncation.

**Best answer.** **Unknown, and deliberately not designed against.** The figures circulating in 2026 guide content were unverifiable and at least one referenced model name appears fabricated `[U — U2, explicitly flagged as low-confidence and possibly invented]`. A separate vendor-described limit (one live artifact per turn) is corroborated across several third-party sources plus vendor support material, but it is someone else's product surface and can change `[U — U4, medium confidence]`. The design response is therefore procedural: **compute chunk sizes from measured artifact sizes at runtime**, order chunks smallest-first, validate every chunk against the envelope, and surface the plan-tier cost up front so a two-stage generation across many directions is not a billing surprise. The paste count is a *retry budget* over a one-paste-per-chunk mechanism, with every extra paste logged as a near-miss, so the metric degrades gracefully instead of silently.

**Residual unknown.** The ceiling itself, and the naming inconsistency between the mechanism ("one paste") and its budget (up to three) — recorded as requiring either a rename or explicit retry semantics.

**Lattice:** `cq18` → `m_empirical_chunk_sizing`, `m_bounded_paste_protocol`, `m_local_regeneration_mode`, `m_usage_tier_disclosure` → `k_chunks_per_cycle`, `k_pastes_per_chunk` → `s_generation_surface_limits`.

---

## Coverage summary

| Measure | Value |
|---|---|
| Competency questions | 18 |
| CQs with a method neighbour | 18 |
| CQs reaching a metric within 2 hops | 18 |
| CQs reaching a standard within 2 hops | 18 |
| **CQ coverage** | **100.0% (target ≥95%)** |
| Lattice nodes | 334 |
| Lattice edges | 546 |
| Dangling edge endpoints | 0 |
| Orphan nodes | 0 |
| Node types used | entity, process, method, standard, metric, risk, pattern, anti_pattern, term, cq (all 10) |
| Edge relations used | uses, measured_by, constrained_by, mitigates, depends_on, part_of, implements, contradicts (all 8) |

**Answer confidence is deliberately uneven and recorded per node.** The weakest answers are CQ18 (0.25), CQ12 (0.35) and CQ6 (0.45) — the generation-channel ceiling, motion judgement, and server survival. Two of those three are the reason the Phase-0 spike suite exists; the third has no known mitigation and is stated as such rather than papered over.
