# Data Model — Website Builder (`001-website-builder`)

**Command:** `/preeng.plan` (companion to `plan.md` and `tech_prd.md`)
**Scope:** field-level modelling of every entity named in `spec.md` §4.2, the on-disk file map, the typed-op catalogue, and the state machines. **Markers preserved:** `[V]` read source · `[I]` inference · `[U]` unsourced.

---

## 0. Conventions

| Convention | Rule |
|---|---|
| **Ids** | Node ids are **ULID-derived and never regenerated** (determinism hazard 4). Variant ids are `<family>@<index>` with an **append-only** integer index. Direction ids are stable slugs; **APFS is case-insensitive, so sibling direction directory names must not differ only by case.** |
| **Serialisation** | UTF-8 · LF · trailing newline · no BOM · fixed key sequence per node type then unknown keys sorted lexicographically · 2-space indent · one array element per line · shortest round-trip numbers, no `-0`, no exponents · **absent optional keys omitted entirely, never written `null`** · non-ASCII literal, never `\u`-escaped |
| **Key presence is semantic** | `md`/`sm` entries exist **only** where the user actually overrode something. "Overridden here" is a **key-presence test**, which is why optional keys must never be materialised as `null` |
| **Hashes** | `sha256` everywhere; binaries are **hash-compared, never re-encoded** |
| **Time** | No timestamps in generated output. Frozen `SOURCE_DATE_EPOCH` at generate time. Timestamps exist only in logs, snapshots and provenance |
| **Ownership** | Every file below names exactly one writer. A second writer is a defect, not a configuration |
| **Naming** | The scene graph is `pages/<id>.doc.json` + `site.json` `[V — §12.2, §12.13]`. **`layout.json` is a legacy alias and must be renamed before implementation** (NA-07) |

---

## 1. File map

Session root: `.acos/website-builder/sessions/WB-<ts>-<slug>/` `[V — §12.11; NA-B12]`

| Path | Entity | Writer | Committed? |
|---|---|---|---|
| `00-interview/answers.json` | `InterviewAnswer[]` | Skill | yes |
| `00-interview/concept.md` | `Concept` | Skill | yes |
| `01-prompt/stage-a.md`, `stage-b-<directionId>.md`, `artwork.md` | prompt artifacts (provenance only) | Skill | yes |
| `01-prompt/font-catalog.snapshot.json` | `FontCatalogEntry[]` (hash-pinned copy) | Skill | yes |
| `01-prompt/token-manifest.json` | frozen token-name manifest | Skill (mechanical) | yes |
| `02-system/<directionId>/{tokens.json, tokens.css, components/*, artwork/*}` | `Direction` | Importer | yes |
| `02-system/manifest.json` | `ImportEnvelope` | Skill (emitted with the prompt) | yes |
| `02-system/import-report.json` → mirrored `inbound/import-report.json` | `ImportReport` | Importer only | yes |
| `02-system/system.lock.json` | `SystemLock` | **Importer and `wb migrate` only** | yes |
| `03-selection/{tournament-log.json, picks.json}` | tournament state | Skill (Step 4) | yes |
| `04-site/site.json` | `Site` | Editor process, typed ops only | yes |
| `04-site/pages/<id>.doc.json` | `Doc` (scene graph) | Editor process | yes |
| `04-site/content.json` | `Content` | Editor process (+ content CLI, v2) | yes |
| `04-site/provenance.json` | `Provenance` | Editor process | yes |
| `04-site/assets/manifest.json` | `Asset[]` — **the allowlist every asset reference validates against** | Editor process and importer | yes |
| `04-site/direction-tour-log.json` | `DirectionTourLog` | Skill (Step 4), **written as rounds progress** | yes |
| `04-site/migration-report.json` | `MigrationReport` | `wb migrate` only | yes |
| `04-site/history.jsonl` | `HistoryOp[]` | Editor process (server) | yes |
| `05-variants/`, `06-custom/` | generated variant + custom-component caches | Generator | yes |
| `07-lock/{dist/, lock-manifest.json, gate-report.json, screenshots/, manifest-a.json, manifest-b.json}` | `LockManifest`, `GateResult[]` | `wb lock` only | manifest yes, `dist/` per policy |
| `evidence/` | `EvidenceBundle` | Evidence bundler | yes |
| `audit/config-snapshot.yaml` | config snapshot at init | Skill | yes |
| `.wb/editor.lock` | `EditorLock` | Editor process | no |
| `.wb/editor.token` | bearer token, mode `0600` | Editor process | **no — never** |
| `.wb/inbox.jsonl` (a.k.a. `commands.jsonl`) | `Command[]` | any agent (append-only); server truncates after apply | no |
| `.wb/doc-hashes.json` | `DocHashJournal` | Editor process | no |
| `.wb/session-ui.json` | `SessionUi` | Editor process | no |
| `.wb/conflicts/<iso>/` | preserved divergent versions | Editor process | **no** (git-ignored) |
| `.wb/tmp/**` | scratch, incl. `tmp/gate2/` | any | **no** (git-ignored) |
| `.wb/locks/<iso>/` | per-LOCK snapshot set | `wb lock` only | **yes — this is the durability story** |
| `state.json` | `ServerState` | Server at boot | no |
| `session.json` | `Session` | Skill | yes |
| `events.jsonl` | pipeline event log | Skill + server | yes |
| `ACTIVE` | session marker, removed at close | Skill | no |

Cross-project (outside the session): `.acos/website-builder/library/font-catalog.json` · `.acos/website-builder/systems/<name>/{system.json, tokens.css, compliance-report.json, provenance}` · `.acos/design-library/<name>/` (warm-start store) · `.acos/evidence/<date>/website-<session>/` (one-line verdict mirror) · `.acos/metrics/agent-completions.log` (already written by ACOS).

**`site/` is its own git repo and `.acos/website-builder/sessions/*/site/` is in the ACOS `.gitignore`** (A83, NA-B11) — otherwise every milestone commit pollutes ACOS history and every `wb-lock/<n>` tag collides.

---

## 2. Ownership zones

| Zone | Paths | Writer | Rule |
|---|---|---|---|
| Machine-owned | generated sources, `tokens.css` | the generator only | regenerated wholesale; hand-tune only via `extract-override.ts` |
| Human/agent-owned | page wrappers, `src/overrides/**`, `src/lib/**` | Claude and the user | never written after scaffold by the generator |
| **Doc-owned** | `pages/*.doc.json`, `content.json`, `site.json`, `assets/manifest.json`, `provenance.json`, `history.jsonl` | **the editor process only** | **Claude reaches them through `wb op`, never a file write** |
| Snapshot / build output | `dist/published/**`, `.wb/locks/**` | `wb lock` only | never hand-edited, never restored from directly |
| Import record | `inbound/**`, `system.lock.json`, `migration-report.json` | importer and migrate only | `systemLock` is unwritable by any HTTP op |

---

## 3. Entity catalogue

### 3.1 `Session` — `session.json`

| Field | Type | Notes |
|---|---|---|
| `sessionId` | `string` (ULID) | matches the session directory suffix |
| `warmStart` | `"none" \| "system-only" \| "full"` | §15.3 split |
| `sourceSystemId` | `string?` | prior system carried forward |
| `assetLibraryPath` | `string?` | **the binary that decides whether the artwork category is real or theatre** (A2) |
| `minedSources` | `string[]` | prior site trees, token bundles, licence registers used for pre-fill |
| `structuralRtl` | `boolean` | the Tier-1 structural-RTL answer. **RTL layout is not built in v1**; the question is asked |
| `accessNeeds` | `object?` | audience access-needs answer; may only **TIGHTEN** a gate threshold, never loosen one |
| `d1Deviations` | `{at, floorRequested, floorAccepted, reason}[]` | signed-off relaxations of the ~10-direction D1 floor |
| `branchChoice` | `"A+" \| "B"` | **default `A+`** (NA-B01): single page, `pages[]` length 1, every op page-scoped |
| `timeBudgetPolicy` | `"one-sitting" \| "few-sessions" \| "open-ended"` | from `Z1`; sets branching aggressiveness and variant rounds |
| `variantPolicy` | `"ten-per-component" \| "three-per-round"` | from `Z2` |
| `signOffs` | `{row, status: "signed"\|"unsigned"\|"contingent", at?}[]` | the ten sign-off rows in `spec.md` |

### 3.2 `InterviewAnswer` — `00-interview/answers.json`, question-ID-keyed

| Field | Type | Notes |
|---|---|---|
| `questionId` | `string` | grammar `<wave-prefix><n>`; reserved prefixes `C, P, B, A, TS, D, M, N, X, L, G, H, U, Z, V`. **The ten Wave-2 taste questions are `TS1`–`TS10`, never `T1`–`T10`** (which collide with the tier labels and break A4) |
| `tier` | `1 \| 2 \| 3` | T1 gates the Step-2 prompt; T2 is just-in-time; T3 is inferred with a visible overridable default |
| `value` | `unknown` | typed per question |
| `source` | `"asked" \| "pre-filled" \| "inferred-default" \| "skill-default"` | `skill-default` is the "I don't know / surprise me" path and **must record a stated concrete default value, never a null** |
| `overridden` | `boolean` | true when the user changed an inferred/pre-filled value |
| `notApplicable` | `boolean` | a T2 question whose moment never arrived |
| `askedAtMs`, `answeredAtMs` | `number?` | **instrumented from day one**; every published duration figure is a projection until these exist |

**Bank volume of record: 90 questions** `[V — §5 row-count self-audit; NA-01]`. Fast mode asks ~45–55 Tier-1 items plus one bundled review screen `[I]`. **A3 ("≤45 answered") is unachievable as written**; §5 says move it to ≤55 or cut the bank.

### 3.3 `Concept` — `00-interview/concept.md`

200–300 words, containing: a point of view · **≥3 abstracted references from different eras/genres/cultures** · a restraint budget · **at least one thing the site refuses to do**. The pipeline **refuses to advance to Step 2 without the refusal** (A5). This document plus `direction-tour-log.json` is how S6 ("the human can name why") is evidenced.

### 3.4 `DirectionCapsule` (Stage A) and `Direction` (Stage B)

| Entity | Fields |
|---|---|
| `DirectionCapsule` | `{id, manifesto (40–80 words), vector: 26 slots, selfAudit: {hueAnchors[], typePairing, motionCharacter, forcedDivergenceAxisPosition, antiSlopDenyListHits[]}}` — over-generated, **machine pre-filtered** on the self-audit fields, then user-cut to the ~10 D1 floor |
| `Direction` | `02-system/<directionId>/{tokens.json (DTCG), tokens.css (machine-owned), components/*.html, artwork/*}` plus the mirrored forge `design-system-spec.yaml`. Identity = a **24-slot varying identity vector plus 2 invariant records**; `layout.breakpoints` and `type.viewport-endpoints` are **invariant across directions**, which is exactly why grid-integer placement survives a direction swap |

### 3.5 `DesignToken` (DTCG + extensions)

| Field | Type | Notes |
|---|---|---|
| `$value`, `$type` | DTCG | standard |
| `com.acos.llm` | object | generation-side metadata |
| `com.acos.pick` | `{pickable: boolean, scope: "direction-slot" \| "in-direction-repickable" \| "derived"}` | **the editor renders no control when `pickable:false`** (A15) |
| `com.acos.direction` | `{directionId, vectorHash}` | a token whose `vectorHash` differs from the active direction is **rejected by the builder** (A16) |
| `capability-manifest` | `{validOptions[]}` | required on every `in-direction-repickable` row; options absent from the active direction's list are **hidden from the UI**, not merely warned about. A row that cannot supply one is **demoted to `direction-slot`** |
| `provenance` | `"anchor" \| "derived"` | derived families: spacing, type steps, radius scale, shadow scale, semantic colour roles, **and font-fallback metrics** (`size-adjust`, `ascent-override`, `descent-override`, `line-gap-override`) computed from the real font binary — a family the taxonomy does not yet name (research F17) |
| spring/motion extension | out-of-standard | **every consumer must agree one extension shape or springs silently degrade to no motion** (R39) |

Volume: **~600–900 resolved tokens per complete direction** `[V — counted programmatically from three published systems]`.

### 3.6 `SystemLock` — `02-system/system.lock.json`

`{directionId, systemVersion, tokensSha256, librarySha256, perFileHashes: {path: sha256}, source, importedAt, migrationMap?}`. Pins the imported direction like a package lock. **Written only by the importer and `wb migrate`.** `site.json.systemLock` mirrors `{directionId, systemVersion, tokensSha256, librarySha256, source, importedAt}` and **no typed op may ever write it** — the validator rejects any derived patch whose pointer starts `/systemLock` with 400 (§12.17-A96).

### 3.7 `ImportEnvelope` and `ImportReport`

| Entity | Fields |
|---|---|
| `ImportEnvelope` (`02-system/manifest.json`) | `{runId, terminator (per-run random), files: [{path, lineCount, sha256Prefix, orderIndex}], ordering: "smallest-first", templateVersion}` |
| `ImportReport` (`inbound/import-report.json`) | `{items: [{path, status: "accepted"\|"rejected"\|"quarantined", reason, offendingSnippet?, acceptedBy?: "human", at}], substitutions: [{kind: "font"\|"contrast", from, to, reason}], templateVersionCheck, chunkCount, pasteCount}` |

A **truncated** chunk fails naming the missing files and **writes no partial system** (A8). A quarantined item **never leaves quarantine without an explicit per-item human accept**.

### 3.8 `Site` — `04-site/site.json`

| Field | Type | Notes |
|---|---|---|
| `formatVersion` | `number` | **newer than the tool ⇒ refuse to open, naming both versions. Never best-effort-parse a future format** |
| `projectId` | ULID | |
| `breakpoints` | `{base: {tracks: 12}, md: {maxWidth: 991, tracks: 6}, sm: {maxWidth: 479, tracks: 4}}` | normative vocabulary; **no key above `base` in v1** — an upward key is rejected by the schema validator (§12.17-A92) |
| `preview` | `{devices: [{w:390,h:844},{w:768,h:1024},{w:1280,h:800},{w:1440,h:900}], fifthSwitcher: 1440 (preview-only, carries no overrides)}` | |
| `grid` | `{rowUnitToken, gapToken, sanityRowCap: 200}` | the row axis is explicit: `grid-auto-rows: var(--wb-row-unit)` |
| `pages` | `{id, path, title, order, seo: {...}}[]` | **length 1 under Branch A+**, but the array and page-scoped ops exist from day one |
| `systemLock` | see 3.6 | **not writable by any op, ever** |
| `doctorThresholds` | `{overridesPerPageAmber: 5, overridesPerPageRed: 15, overridesPerSite: 40, overridesPctOfNodes: 0.25}` | `[I — stated starting numbers, tunable; NA-14]` |
| `freePositionPolicy` | `{perSectionCap: 2, demoteAtMaxWidth: 390}` | **NA-06: the demote trigger (390) and the `sm` boundary (479) are NOT the same number** |

### 3.9 `Doc` — `04-site/pages/<id>.doc.json`

`{formatVersion, pageId, root: Node, sectionOrder: string[]}` in canonical serialisation.

### 3.10 `Node`

| Field | Type | Notes |
|---|---|---|
| `id` | ULID-derived | never regenerated |
| `sectionId` | `string` | **stable across reorder, swap and regeneration** |
| `component` | `string` | must resolve in the library or LOCK/generate **hard-fail** |
| `variant` | `string` (`family@index`) | unresolved ⇒ canonical fallback + `variantMigrated` |
| `region` | `"header" \| "main" \| "footer" \| "art"?` | |
| `role` | `"content" \| "art"?` | `art` resolves overlap by **z-order** instead of displace-down |
| `layout` | `{base: LayoutEntry, md?: LayoutEntry, sm?: LayoutEntry}` | `base` mandatory; `md`/`sm` **only where overridden** |
| `props` | object | includes `motion` (a token id), `aspect`, `focalPoint`, container-contract fields |
| `slots` | `{[slotName]: NodeRef[]}` | typed by `SlotContract` |
| `text` | `{[key]: contentRef}` | copy lives in `content.json` |
| `locked` | `boolean` | **UI word is "Freeze", never "Lock"** (A-freeze rule) |
| `notes` | `SectionNote[]` | stripped at LOCK |
| `variantMigrated` | `{from, to, reason, at, auto}?` | **blocks LOCK until acknowledged** (gate 6) |
| `orphaned` | `{[slotName]: unknown}?` | parked content — **never deleted by a migration** |

### 3.11 `LayoutEntry` (per breakpoint key)

**Flow mode:** `{mode: "flow", col: {start, span}, row?: {start, span}, align: "start"|"center"|"end"|"stretch", spaceBefore: <space token>, spaceAfter: <space token>, order?: number}`

**Free mode:** `{mode: "free", anchor: {target: "parent" | "grid-cell", edge, cell?}, offset: {x: "clamp()|%", y: "clamp()|%"}, z?: number, minBlockSizeReserved: <length>, flowFallback: {col, colSpan, row, order, z?}}`

Rules: absence of a key at `sm` **means flow at `sm`** — that is exactly how auto-demotion is represented. `order` is **hard-blocked on focusable nodes** (WCAG 2.4.3) and warned on others (1.3.2); any commit changing mobile stacking first renders a **numbered mobile-sequence preview**. Persisted placement is **integers only** — never pixel coordinates.

### 3.12 `Content` — `04-site/content.json`

`{ [contentKey]: {value: string, kind: "plaintext"|"richtext"(v2), orphaned?: true, parkedFrom?: {nodeId, slot}} }`. Inline editing is `contenteditable="plaintext-only"` on ~90% of text nodes so source-app markup cannot survive (R36). The **content orphanage** lives here and is auto-restored when a later swap re-introduces the slot.

### 3.13 `SlotContract` and `Variant`

| Entity | Fields |
|---|---|
| `SlotContract` | `{name, type, cardinality, required}` — the bar offers **only** superset-or-exact matches and states "this variant adds N slots" / "this variant has no place for: [x]" before the swap |
| `Variant` | `{componentFamily, index (append-only), axisValues: {axis: value}, directionId, generatedAt, indistinguishabilityCheck: {against: index[], passed: boolean, method: "200x120px"}}` |
| `VariantAxisVector` | hand-authored per component in the skill (OQ-11). **Two variants are distinct iff their vectors differ in ≥1 axis** — computed axes (size, theme, density, state, icon slot, semantic colour) never count against the budget |

### 3.14 `Asset` — `04-site/assets/manifest.json` (**the allowlist**)

`{id, lane: "A"|"B"|"C", path, tokenReferencing: boolean, directionAffinity: string[], licenceClass, sourceUrl?, fileHash, generator?, model?, planTier?, prompt?, alt|decorative, derivatives: [{encoder, encoderVersion, settingsHash, outputSha256}]}`

Two distinct gates read this (research F16): **licence completeness** (every recorded asset has a class) and **reference resolution** (every referenced asset exists). A hallucinated path passes the first and ships a broken page.

### 3.15 `FontCatalogEntry` — `.acos/website-builder/library/font-catalog.json`

`{familyId, classification, role, foundry, licenceClass, oflSourceUrl, fileHash, glyphCoverage, preSubsettedCuts: {latin, latinExtended}, attributionRequired}`. Base64 cuts are computed **once, locally, ahead of time — never by the web model**. 24–32 families `[I — a starting number, OQ-09]`. A hash-pinned snapshot is taken per session so a mid-run library refresh cannot change what a session is judging. **Commercial-foundry faces emit a pre-launch blocker rather than being embedded** (A74).

---

### 3.16 `Provenance` — `04-site/provenance.json`

Per component instance: `{nodeId, directionId, variantId, generatedAt, promptHash}`. **Distinct from, and not interchangeable with, `direction-tour-log.json`** — provenance answers "where did this instance come from", the tour log answers "why did the human choose this direction".

### 3.17 `DirectionTourLog` — `04-site/direction-tour-log.json`

```jsonc
{ "rounds": [ { "roundName": "heat-1" | "semifinal" | "final",
                "heats": [ { "directionsShown": ["d3","d7","d9"],
                             "orderShown": ["d7","d3","d9"],
                             "pick": "d7",
                             "reason": "…the human's stated words…" } ] } ],
  "finalPick": "d7", "timestampIso": "…" }
```

**Written as rounds progress; never reconstructed after the fact.** Never more than 3 full-size renders side by side (a bracketed tournament, never an N-up grid — thumbnail grids systematically favour loud, high-contrast directions over subtle editorial ones). This file is the evidence for S6 and G2.

### 3.18 `HistoryOp` — `04-site/history.jsonl` (append-only)

`{seq, ts, actor: "human"|"agent", op, target, patch (RFC 6902), inverse, label, txn}`. A continuous drag coalesces into **one** entry. `txn` groups a swap or a section regeneration into **one undo step** (A31, A32). The undo stack is a **single command stack over the doc**, mirroring this log — canvas drags, inspector edits and text edits alike.

### 3.19 `TrashEntry` (recovery bin)

`{nodeSubtree, restoreAnchor: {parentId, index, sectionId}, deletedAt, deletedBy}`. **Independent of the undo stack**, retained unbounded within a project, **restore-in-place**, and **stripped at LOCK**.

### 3.20 `SectionNote`

`{sectionId, note, status: "open"|"applied"|"dismissed", regenerationId?}`. Drives **scoped regeneration of that section only**, executed **inline via Local Regeneration Mode** (not another hand-carry), as **one undo step**. Stripped at LOCK. This is the human-authored replacement for the rejected autonomous critique loop — the "middle gear" between swapping one variant and regenerating everything.

### 3.21 `CoherenceLedger`

`{entries: [{at, nodeId?, tokenPath?, acceptedValue, systemValue, reason, kind: "off-system-value"|"cross-direction-transplant"(v2), debtScore}]}`. Records accepted off-system values. Cross-direction swap debt is a **v2** consumer; the ledger ships in v1 because the inline-authored custom path can already create debt.

### 3.22 `EditorLock`, `TabClaim`, `ServerState`, `DocHashJournal`, `SessionUi`

| Entity | Shape | Notes |
|---|---|---|
| `EditorLock` (`.wb/editor.lock`) | `{pid, startedAt, heartbeatAt}` | covers **processes** |
| `TabClaim` (over SSE) | `{tabId, claimedAt}` | covers the **two-tab case**; the second tab is **read-only** |
| `ServerState` (`state.json`) | `{phase, step, awaiting, nextAction, port, pid, url, sessionId}` | `[V — §12.11]`; **a superset of the carried four-field shape (NA-B03)**. `--resume` reads it and re-attaches |
| `DocHashJournal` (`.wb/doc-hashes.json`) | `{path, sha256, mtimeMs, seq}[]` | **the authoritative anti-clobber input.** Divergence without a server-issued write ⇒ conflict raised before the next save; the divergent version is copied to `.wb/conflicts/<iso>/` **first** |
| `SessionUi` (`.wb/session-ui.json`) | `{selection, scroll, openPanels, activeBreakpointKey}` | ephemeral |

### 3.23 `Command` — `.wb/inbox.jsonl` (a.k.a. `commands.jsonl`)

`{id, ts, actor, intent, payload, status: "pending"|"applied"|"rejected"}`. Append-only. The Claude session watches it with a **blocking `tail -f`** (zero token cost while the user designs). **Agent ops go through the inbox always**, even when the editor is not running — one write path, one validation path. When no editor process is running, `wb op` starts a headless one, applies, and exits.

### 3.24 `GateResult` and `gate-report.json`

`{gateId, tier: 0|1|2|3, status: "pass"|"fail"|"inconclusive", measured, threshold, evidenceRef, waiver?: {reason, at, by}}`. **Never a thrown exception on a normal fail. INCONCLUSIVE blocks exactly like a fail.** `gate-report.json` = `{runId, at, gates: GateResult[], waivers: [...], summary}` — and it is where `gate2: waived-local` is recorded if gate 2 exceeds 5 minutes (**a recorded waiver, never a silent skip**).

### 3.25 `LockManifest` — `07-lock/lock-manifest.json`

`{lockIndex, at, docSha256PerPage: {}, siteSha256, systemLockSha256, gateReportRef, screenshotRefs: [], distFileHashes: {path: sha256}, gitTag: "wb-lock/<n>"}`. The **per-file SHA-256 map** is what makes a hand-edit inside the exported tree detectable at unlock and at the next LOCK (A58).

### 3.26 `MigrationReport` — `04-site/migration-report.json`

`{at, fromSystemLockSha, toSystemLockSha, changes: [{nodeId, kind: "variant"|"slot"|"prop"|"motion"|"token", from, to, rule, auto}], unmappable: [{nodeId, reason}], counts: {}}`. **Every reference that changed, old and new value, and the rule that decided it. Never silently drops a node** — unmappable nodes are listed explicitly and the human resolves each.

### 3.27 `EvidenceBundle` — `evidence/`

`{fonts: FontRecord[], assets: AssetRecord[], thirdPartyMarks: [{mark, usageRule, usedAsSupplied: true}], gateReport, contrastProofTable: [{pairing, wcagRatio, apcaLc, scheme}], screenshots: [{breakpoint, scheme, motion, devicePinned}], directionTour, referenceTriangulation, substitutionLog, publishRecord: {method: "automated"|"runbook", live: boolean, url?}, disclosure: "Automated accessibility gates passed: N. Manual and screen-reader review not performed."}`

**The disclosure wording is fixed.** Never "WCAG AA compliant", never "conformant", never "certified".

### 3.28 `Registry` (v2)

`registry.json` for cross-site component/direction reuse. Out of v1 scope; modelled only so v1 does not foreclose it.

---

## 4. Typed-op catalogue (payload schemas)

Every op carries `{op, etag, txn?, label?}` plus its own fields. The server validates against the op schema **and** against the component library, derives the RFC 6902 patch, applies atomically (write-temp → `fs.rename`), and appends `{op, patch, inverse}` to `history.jsonl`.

| Op | Payload | Writes | Rejects with |
|---|---|---|---|
| `place-node` | `{parent, index, component, variant, layout}` | doc | 422 unknown component/variant |
| `move-node` | `{node, toParent?, bp, col, row, span?}` | doc | 400 non-integer placement; 409 stale etag |
| `set-span` | `{node, bp, colSpan, rowSpan?}` | doc | 400 span ≤ 0 |
| `reorder-siblings` | `{parent, order: nodeId[]}` | doc | — |
| `set-align` / `set-space` | `{node, bp, value}` | doc | 400 value not on the spacing scale / not a token |
| `set-free-position` | `{node, bp, anchor, offset, flowFallback, z?}` | doc | 400 anchor target ∉ {parent, grid-cell}; 422 section cap exceeded; 422 pinned/scrubbed container without explicit confirmation |
| `clear-free-position` | `{node, bp}` | doc | — |
| `set-order-override` | `{node, bp, value}` | doc | **403 on a focusable node** (WCAG 2.4.3 hard block) |
| `reset-to-inherited` | `{node, bp, property}` | doc | — |
| `delete-node` / `restore-node` | `{node}` / `{trashId}` | doc | — |
| `duplicate-node` / `paste-fragment` | `{node, target}` / `{fragment, target}` | doc | **must carry all breakpoint overrides** |
| `set-text` | `{contentKey, value}` | content | 400 non-plaintext payload on a `plaintext-only` node |
| `swap-variant` | `{node, variant}` | doc (+ content orphanage) | 422 contract not a superset; **placeholders created here block LOCK** |
| `regenerate-section` | `{sectionId, noteId}` | doc + content | one `txn` ⇒ **one undo step** |
| `acknowledge-migration` | `{nodes: []|"all", count}` | doc | bulk requires a confirmation naming the count |
| `freeze-node` / `unfreeze-node` | `{node}` | doc | UI word is **Freeze** |
| `add-page` … `set-doctor-thresholds` | page/site fields | `site.json` | **400 if the derived patch touches `/systemLock`** |
| `register-asset` … `record-derivative` | asset fields | `assets/manifest.json` | 400 missing licence class |
| `record-placement` / `record-variant-swap` | provenance fields | `provenance.json` | — |

**Universally rejected:** a raw JSON Patch body · a file path in a request body · any path outside the allowlist (including via symlink or `..`) · any patch pointer starting `/systemLock` · any request failing `Host`, `Origin` or bearer-token validation.

---

## 5. State machines

**Pipeline phase** (recomputed from disk, never from memory; each transition evidenced by a file):
`init → warm-start → interview → prompt-emitted → awaiting-ingest → ingested → direction-tournament → direction-selected → editing → regenerating → locking → locked → published`

**Server lifecycle:**
`not-started → launching (rung F1..F5) → bound (same-turn 200) → survived-boundary (second curl, separate tool call) → serving → idle → shut-down`
**A same-turn 200 is never proof of life.**

**Node lifecycle:**
`placed → edited → overridden(bp) → frozen → migrated(flagged) → orphaned(parked) → trashed(recoverable) → restored`

**Import item lifecycle:**
`parsed → envelope-validated → ast-validated → {accepted | quarantined} → (human per-item accept) → applied`
A parse failure **quarantines**; it never passes through.

**Lock states:**
`unlocked (design server running) → gates-running → locked (dist + snapshot + tag) → published | runbook-emitted`
**UNLOCK = restart the design server.**

**Gate verdicts:** `pass | fail | inconclusive`. **INCONCLUSIVE blocks like a fail.**

---

## 6. Cross-entity invariants (each is testable)

| # | Invariant | Test |
|---|---|---|
| 1 | Every `node.variant` resolves in the library, or carries `variantMigrated` | gate 6 — fails with the **node list, not a count** |
| 2 | Every `node.component` resolves, always | hard fail; editor opens read-only "migration required" |
| 3 | Every asset reference resolves to a manifest entry **and** a file on disk | gate 23a (distinct from licence completeness) |
| 4 | Every token referenced by a generated file exists in `tokens.json` | hard fail at generate time, naming the token |
| 5 | `base` exists on every node; `md`/`sm` only where overridden | schema validator; A41 / §12.17-A91 |
| 6 | No upward breakpoint key exists | schema validator (§12.17-A92) |
| 7 | `systemLock` is never modified by an op-derived patch | 400 (§12.17-A96) |
| 8 | Re-serialising any doc-owned JSON yields a zero diff | purity gate 8 (§12.17-A98) |
| 9 | Every `motionCapable:true` container has `reducedMotionVariantRef` | container validation (A22) |
| 10 | Every `source.kind:'video'` + `autoplay:true` container has `muted:true` | field-level constraint |
| 11 | Every container has an explicit aspect reservation | container validation |
| 12 | No `order` override exists on a focusable node | 403 at op time + lock-time re-check |
| 13 | Free-position blocks carry `flowFallback` and a reserved `min-block-size` | op validation + A44/A45 at LOCK |
| 14 | Free-position count per section ≤ cap, with a visible counter | live counter + gate |
| 15 | No two variants offered in one bar are indistinguishable at 200×120px | generator check (A34) |
| 16 | Every shipped font and asset has a licence class | build-failing (S8, A72) |
| 17 | Zero `data-wb-*`, zero dev-runtime strings, zero design-time origins in `dist/published/**` | purity gates 1 and 7 |
| 18 | Editor-installed and editor-uninstalled builds match | purity gate 2 — **or the signed-off normalised fallback** |
| 19 | Every placed image has alt text or an explicit decorative toggle | **blocks the placement**, not just the lock (A36) |
| 20 | Every doc-owned write came from the server | hash journal; conflicts preserved in `.wb/conflicts/` (§12.17-A95) |

---

## 7. Volumes of record (all `[I]` unless marked)

| Quantity | Value |
|---|---|
| Component inventory | **216 rows / 1,228 variants** `[V — §8.2/§8.3]`; **v1 target 88 rows / 675 variants** (87/674 + the skip-link row gate 11a requires; NA-B08) |
| Editor feature rows | **116 total** `[V — §10 recount]`; **v1 target 66** `[I]` (56 editor-lite + 10 promoted canvas rows; NA-B09) |
| Interview questions | **90** `[V]`; ~45–55 asked in fast mode `[I]` |
| Directions per project | ~10 (D1 floor; relaxations recorded as signed-off deviations) |
| Artworks per direction | 20 total `[OQ-02]`; ≥60% token-referencing |
| Variants per component | 10 (12 for hero, CTA band, card, badge, feature grid, pricing); ~120 per direction if all families opened `[I]` |
| Tokens per direction | ~600–900 resolved `[V]` |
| Font families in the catalog | 24–32 `[I]` |
| Purity gates | **8** `[V]` |
| Lock-time checks | **32** `[V]` |
| Acceptance criteria | **A1–A90** `[V]`; two disjoint A91–A101 sets (§12.17 and §18) — **unstable ids** |
| Security controls | **8** `[V — §12.12]` |

---

## 8. Assumptions specific to this data model

1. **NA-B12** — the on-disk tree follows §12.11 verbatim, with `04-site/` holding `site.json` + `pages/*.doc.json` (NA-07's rename applied). `layout.json` appears nowhere in new code.
2. **NA-B03** — `state.json` uses the §12.11 eight-field superset.
3. **NA-B01** — `pages[]` exists with length 1 under Branch A+; page-scoped ops ship in v1 so multi-page is a v2 *feature*, not a v2 *migration*. The multi-page **manager UI** and global regions are v2 (sign-off row).
4. **NA-B08** — the skip-link component is added as one row with a **single canonical variant** (not a 10-variant family). Flagged for confirmation at the inventory audit.
5. **NA-B04** — `wb migrate` uses **canonical fallback only**; semantic slot-signature matching (`§12.16-O35`) is a v2 question with no risk-removing mitigation.
6. **NA-B07** — durability is the op log + atomic writes + hash reconciliation; **git commits at milestones**, `wb autosave --git` opt-in. "Every-save-is-a-commit" is superseded.
7. `Assumption` (new, this document) — **`content.json` is a single flat file in v1.** Per-page content splitting is deferred; under Branch A+ there is one page, so the split buys nothing and would create a second migration surface. Revisit when Branch B lands.
8. `Assumption` (new, this document) — **`trash[]` is retained unbounded within a project** (per §12.6's recovery-bin behaviour) and pruned only at LOCK. If a project's trash growth ever becomes a problem, the fix is a `doctor.ts` finding, not a silent eviction — a silent eviction would violate "a migration may relocate content; it may not destroy it".
9. `Assumption` (new, this document) — **`sanityRowCap = 200`** is carried as the runaway-drag reject value; it is a sanity bound, not a layout constraint, and is stored in `site.json.grid` so it is tunable without a code change.

---

**End of `data-model.md`.**
