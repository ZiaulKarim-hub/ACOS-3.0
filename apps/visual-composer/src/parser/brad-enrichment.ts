// Brad-class semantic enrichment pass.
//
// SLICE-003-001-06. A deliberately separate post-processing stage that
// tags ContainerRecord entries with a `bradClass` metadata field when the
// source DOM element bears a recognized OKOA Brad design-system class.
//
// WHY A SEPARATE PASS (not inlined into extractors):
//   - Slices 02–05 (text/image/svg/table/background extractors) stay
//     Brad-agnostic. They never grow knowledge of the Brad taxonomy.
//   - Generic-HTML fallback mode becomes a single flag flip — pass
//     { enabled: false } and you get a Brad-class-free record stream
//     suitable for non-OKOA documents (e.g., a third-party article HTML).
//   - The taxonomy lives in ONE file (brad-taxonomy.ts) so future Brad
//     additions touch exactly one place, never the five extractors.
//
// CONTRACT:
//   enrich(records, { enabled: true })
//     -> Returns a NEW array. Records bearing a known Brad class are
//        replaced by a structurally cloned record with bradClass set;
//        records without a known class are referentially identical to
//        their input entries (no defensive clone — pure pass-through).
//   enrich(records, { enabled: false })
//     -> Returns the input array reference unchanged. NO clone. The
//        off-mode test asserts `result === records` strict-equality.
//        This is the proof that toggling enrichment is a zero-cost,
//        zero-mutation no-op for downstream consumers.
//
// MULTI-CLASS RESOLUTION:
//   An element bearing multiple known Brad classes resolves to the
//   highest-priority match per BRAD_CLASS_PRIORITY (see brad-taxonomy.ts).
//   Implementation: scan the priority list top-to-bottom and pick the
//   FIRST class also present on the element's class list. No substring
//   matching — Set.has() is the only lookup primitive used.
//
// FALSE-POSITIVE GUARD:
//   Lookup is exact-match via Set.has() on individual class names from
//   the element's classList. A class like "body-paragraph" (NOT in the
//   taxonomy) cannot accidentally match "body-default" or "body-lead".
//   Regex / substring / startsWith are NOT used.

import type { ContainerRecord } from './types';
import {
  BRAD_CLASS_PRIORITY,
  BRAD_CLASS_SET,
  type BradClass,
} from './brad-taxonomy';

/** Options bag for enrich(). Keyed by name for forward compatibility. */
export interface EnrichOptions {
  /**
   * When true, scan each record's domClasses for known Brad classes and
   * tag the highest-priority match as bradClass. When false, return the
   * input array reference unchanged — see contract note above.
   */
  enabled: boolean;
}

/**
 * Semantic enrichment pass. See file header for full contract.
 *
 * @param records ContainerRecord array from the extract() pipeline.
 * @param opts    Enrichment options. Only `enabled` is consulted in v1.
 * @returns       The original array (off-mode) or a new array with Brad-
 *                tagged records (on-mode).
 */
export function enrich(
  records: ContainerRecord[],
  opts: EnrichOptions,
): ContainerRecord[] {
  // Off-mode: preserve referential equality. This is asserted by the
  // off-mode test (`result === records`) and is the proof that the
  // generic-HTML fallback path adds zero overhead and zero mutation.
  if (!opts.enabled) return records;

  // On-mode: scan each record's domClasses. Records without domClasses
  // (older callers that haven't been migrated, or records whose source
  // element bore no class attribute) pass through untouched and
  // referentially identical.
  return records.map((record) => {
    const classes = record.domClasses;
    if (!classes || classes.length === 0) return record;

    const matched = pickHighestPriority(classes);
    if (matched === undefined) return record;

    // Spread-clone the record so we never mutate the input. The clone is
    // shallow — content/computedStyle/etc. are shared by reference, which
    // is safe because they're treated as immutable downstream.
    return { ...record, bradClass: matched };
  });
}

/**
 * Resolve a class list to its highest-priority Brad class match.
 *
 * Algorithm: build a Set from the candidate class list (O(k)), then walk
 * BRAD_CLASS_PRIORITY top-to-bottom and return the first class also
 * present in the set. Total work: O(k + p) where k = element class count
 * and p = priority list length (12).
 *
 * @param classList Element class names, e.g. ['body-default', 'narrow'].
 * @returns         The matched BradClass, or undefined when no match.
 */
function pickHighestPriority(classList: readonly string[]): BradClass | undefined {
  // Build the lookup set. Includes ALL classes from the element, even
  // those not in the Brad taxonomy — they simply won't be hit by the
  // priority-list scan below. This is intentional: it keeps the
  // matching surface narrow (only BRAD_CLASS_PRIORITY entries can
  // match) and immune to false positives from substring overlap.
  const present = new Set<string>(classList);

  for (const candidate of BRAD_CLASS_PRIORITY) {
    // Use Set.has() for the exact-match guarantee required by AC #10.
    // `present.has('body-paragraph')` -> true does NOT cause a match
    // for 'body-default' because the candidate string is 'body-default',
    // not a substring search against the set.
    if (present.has(candidate)) return candidate;
  }

  return undefined;
}

/**
 * Defensive utility: filter a class list down to entries known to be in
 * the Brad taxonomy. Not used by enrich() itself (which only needs the
 * highest-priority single match) but exported for potential future
 * callers that want the full known-class set on an element. Kept
 * here so the taxonomy stays accessible via this module's public surface.
 */
export function knownBradClasses(classList: readonly string[]): BradClass[] {
  const out: BradClass[] = [];
  for (const c of classList) {
    if (BRAD_CLASS_SET.has(c)) out.push(c as BradClass);
  }
  return out;
}
