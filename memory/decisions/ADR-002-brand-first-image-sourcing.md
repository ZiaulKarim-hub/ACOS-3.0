# Decision: Brand-First Image Sourcing with Vision-Bootstrapped Manifest

**Date:** 2026-04-23
**Decision Maker:** human (confirmed) + the-architect (proposed)
**Status:** accepted
**Supersedes:** N/A
**ADR ID:** ADR-002
**Related Epic:** EPIC-002 (acos-ultimate-designer), STORY-002

## Context

`acos-ultimate-designer` produces documents whose aesthetic relies heavily on
imagery — full-bleed covers, chapter dividers, mid-content photo bands, and
portfolio-grid photo cards (STORY-001). The v3 reference uses an explicit
brand-asset directory at `/Users/zee/Desktop/Private Credit Capabilities/v3/images/`
with hand-picked OKOA portfolio photos and an `ATTRIBUTION.md` tracking
sources.

Every generated document will have multiple photo slots that need to be
populated with images — ideally brand-appropriate (specific OKOA properties,
locations, construction shots) when relevant content exists, falling back to
internet-sourced generic photos when it doesn't.

## Problem Statement

How should the skill source images for photo slots? The choice affects:

- Output authenticity (does the document feel OKOA-specific or generic?)
- Maintenance cost (how often does the user curate the image selection?)
- Scaling behavior (what happens when content references something new?)
- Cost (LLM vision calls, API usage)

## Options Considered

### Option A: Internet-only sourcing

**Description:** Every photo slot derives a query from content semantics and
pulls from Unsplash/Pexels. No brand assets involved.

**Pros:**
- Zero setup cost. Works immediately without user supplying anything.
- Infinite supply — any content topic can be illustrated.
- No per-image curation or tagging.

**Cons:**
- Output is generic. A document about OKOA's Ascent Park City project gets a
  stock photo of a random park-city-shaped building instead of the actual
  property photo OKOA already has on disk.
- No brand voice in imagery. The difference between 'polished institutional
  PDF' and 'content-marketing tear-sheet' is largely image quality and
  specificity.
- v3's aesthetic is inseparable from its use of actual OKOA property photos.
  Internet-only output will not match v3.

**Effort:** Low (just STORY-002 slice SLICE-002-03)
**Risk:** High (aesthetic mismatch with stated success criterion #5)

### Option B: Manual manifest — user hand-curates tags per image

**Description:** User drops images in a directory and hand-authors a
manifest.yaml with tags, descriptions, and deal_match entries per image.
Matcher uses these tags. Fallback to internet for gaps.

**Pros:**
- Maximum curation quality — human picks exactly what each image is about.
- Deterministic — manifest doesn't change unless user edits it.
- No LLM cost for manifest upkeep.

**Cons:**
- User explicitly said they do NOT want to hand-maintain a manifest. Hard
  constraint from planning.
- High friction to add new images — every drop requires a manifest edit.
- Tagging quality varies with user discipline; forgotten tags silently
  degrade matching.

**Effort:** Low build cost, high ongoing maintenance cost
**Risk:** Blocked by user constraint — not an option.

### Option C: Auto-bootstrapped manifest via Claude vision, hashed + cached

**Description:** On first run (or when user adds new images), a bootstrap
script scans the asset directory, hashes each image with SHA-256, spawns a
Claude vision agent per new/changed image to generate a description + rich
tag set (subject, setting, mood, colors, real-estate category, named entity),
and writes manifest.yaml keyed by file hash. Idempotent — subsequent runs
skip unchanged files. Matcher uses manifest tags + named-entity bonus when
content references a specific property/location. Falls back to Unsplash/Pexels
when no brand entry exceeds the similarity threshold (default 0.6). User
feedback ('swap the image on page 5') appends to `user_rejected_for` on the
offending entry so it's excluded from future matches in similar contexts.

**Pros:**
- Zero ongoing user maintenance — drop new images, next run picks them up.
- Quality tagging without user discipline — the vision model produces rich,
  consistent tags.
- Named-entity extraction (e.g., 'Ascent Park City') enables content-to-image
  binding for specific properties — the key feature that makes the output
  feel OKOA-specific.
- Cost is one-time per image: ~$0.01 × N images = a few dollars for a 50–100
  image library, zero ongoing cost for unchanged images.
- User feedback loop creates a system that LEARNS per user — bad matches get
  permanently excluded for similar contexts.
- Fallback to Unsplash/Pexels handles gaps gracefully; skill never refuses
  to produce output due to missing brand assets.

**Cons:**
- Complexity: bootstrap + matcher + fallback + feedback persistence = 5 slices
  in STORY-002 (vs. 1 slice for internet-only).
- Cost, though small, is non-zero for first-run against a new library.
- Vision model tagging has some variance — two runs against the same image
  produce slightly different tags. Cache by hash masks this.
- Security consideration: user-supplied images are fed to vision model —
  prompt must be framed defensively against image-embedded injection.

**Effort:** Medium–High (5 slices in STORY-002; SLICE-002-01 is M-effort, plus 4 more)
**Risk:** Medium (complexity + cost, but well-understood failure modes)

## Decision

**Chosen Option:** Option C — Auto-bootstrapped manifest via Claude vision,
hashed + cached, with Unsplash/Pexels fallback and user feedback persistence.

## Rationale

Option B is off the table (user constraint). The choice is between A (generic,
cheap) and C (brand-authentic, one-time cost).

The success criterion for the epic is that regenerating the v3 Private Credit
Capabilities document produces ≥90% visual fidelity to the reference. v3's
fidelity depends on OKOA-specific imagery. Option A cannot meet this criterion
by construction — it has no mechanism to surface brand assets. Option C does.

The cost concern is real but bounded. A ~$1 one-time cost per 100 new images
is acceptable in exchange for never hand-maintaining the manifest. After the
first run, incremental cost is near-zero (text matching + occasional API
fallback).

The user-feedback loop is what makes this a SYSTEM rather than a one-shot
match engine. Over time, per-user curation emerges organically from use —
rejections accumulate, the matcher improves, the document quality compounds.

## Implications

### Immediate

- STORY-002 is 5 slices instead of 1. Acknowledged in planning effort
  estimate (`L` for the whole story).
- Manifest format must be defined up-front (SLICE-002-01) because subsequent
  slices all consume it. Schema decisions now lock in downstream behavior.
- Matcher v1 is token-overlap + named-entity bonus. Embedding-based matching
  deferred to Phase 2 — token overlap with rich tags handles ~90th-percentile
  cases, and complexity is not justified at MVP.
- File-hash caching is non-negotiable. Without it, every run re-tags every
  image and costs escalate.
- ATTRIBUTION.md auto-generation per run is required — both for the skill's
  own outputs (brand attribution to OKOA as source, photographer credit for
  Unsplash/Pexels) and for parity with v3 reference.

### Long-term

- Manifest format is schema-versioned (implicit v1; migrate logic needed if
  v2 adds fields). Plan for schema migration before changing anything in the
  `manifest-schema.yaml`.
- User-feedback data accumulates over time. Periodic review may surface
  systematic match problems (e.g., a whole category of content that always
  fails to match brand assets) pointing at tagging gaps.
- Cross-project manifest sharing is not supported at MVP but may become a
  Phase 2 feature if multiple users start building their own manifests.

### Dependencies

- Depends on: Anthropic API access (for vision bootstrap). Already available
  via Claude Code.
- Depends on: Unsplash API key + Pexels API key (optional; degrades gracefully).
- Depends on: HTML emitter marking photo slots with semantic tags
  (SLICE-001-05 outputs `data-photo-slot='tag1,tag2'`).
- Enables: Story 3 (PDF pipeline — needs images populated).
- Enables: Story 4 (PPTX pipeline — needs image paths resolved).
- Enables: Story 5 (visual verification — 'photo quality' category checks
  rely on photo slots being populated).

## Related Decisions

- ADR-001 — Page-as-canvas composition (defines the photo slot shapes this
  decision must fill).
- (future) ADR-003 — Visual reviewer model hard-pinned to opus
- (future) ADR-004 — Zero loan-doc design-library content loads

## Review Notes

User approved this decision during 2026-04-23 planning session after
explicitly clarifying:

> User: "(b) prefer brand assets, fall back to internet."
> User: "I don't want to hand-maintain a manifest."

The vision-bootstrap approach was proposed as a way to satisfy both
constraints without user effort. Captured in
`memory/handoffs/2026-04-23-081259-plan-approved-pending.yaml` decisions_made
section.

Cost model was reviewed: ~$0.01 per image × ~50 images = ~$0.50 one-time;
near-zero thereafter. Accepted as reasonable.

---

*Recorded by The Architect*
