// Brad design-system class taxonomy — the single source of truth for the
// semantic class names the Brad enrichment pass (slice 06) recognizes on
// source-DOM elements. Centralized here intentionally: future additions to
// the OKOA Brad design system land in THIS file and nowhere else.
//
// The taxonomy is exported in two complementary forms:
//   - BRAD_CLASSES: a const tuple for type derivation (BradClass union).
//   - BRAD_CLASS_SET: a ReadonlySet<string> for O(1) exact-match lookup.
//
// Exact-match-only is enforced via Set.has(); substring or regex matches
// are explicitly NOT permitted (per slice AC #10: "class 'body-paragraph'
// does NOT match 'body-default' or 'body-lead'"). The Set encodes that
// guarantee at the data-structure level.
//
// BRAD_CLASS_PRIORITY encodes the multi-class resolution rule documented
// in slice 06 (heading > metric > chapter > data > body > caption > footnote;
// ties broken by taxonomy order). enrich() iterates the priority list and
// returns the FIRST class present on the element — so ordering here is
// load-bearing, not cosmetic.

/** Canonical list of Brad design-system class names. v1 — 12 entries. */
export const BRAD_CLASSES = [
  'heading-display',
  'heading-subhead',
  'body-lead',
  'body-default',
  'metric-grid',
  'metric-card',
  'chapter-divider',
  'pull-quote',
  'caption',
  'footnote',
  'data-table',
  'photo-break',
] as const;

/** Union of literal Brad class names — derived from BRAD_CLASSES. */
export type BradClass = (typeof BRAD_CLASSES)[number];

/**
 * Set lookup table for exact-match class detection. Using Set.has() (rather
 * than Array.includes() / regex / substring) is required by the slice
 * acceptance criteria — see AC #10 false-positive guard.
 */
export const BRAD_CLASS_SET: ReadonlySet<string> = new Set<string>(BRAD_CLASSES);

/**
 * Priority order for resolving multi-class elements.
 *
 * When a single element bears multiple known Brad classes, enrich() walks
 * this list top-to-bottom and selects the FIRST class also present on the
 * element. The order reflects the documented Brad rule:
 *
 *   heading > metric > chapter > data > body > caption > footnote
 *
 * Within each family the more-specific variant precedes the more-generic
 * one (heading-display before heading-subhead, metric-grid before
 * metric-card, body-lead before body-default).
 *
 * This list MUST be kept in sync with BRAD_CLASSES — every entry here
 * must also be in BRAD_CLASSES. A lint-style runtime check is unnecessary
 * because the type annotation `readonly BradClass[]` makes drift impossible
 * without a corresponding edit to BRAD_CLASSES.
 */
export const BRAD_CLASS_PRIORITY: readonly BradClass[] = [
  'heading-display',
  'heading-subhead',
  'metric-grid',
  'metric-card',
  'chapter-divider',
  'data-table',
  'photo-break',
  'pull-quote',
  'body-lead',
  'body-default',
  'caption',
  'footnote',
];
