// DOM walker — single-pass traversal that yields visible elements with
// parent-chain references for downstream extractors.
//
// SLICE-003-001-02 introduced this module with a recursive visit().
// SLICE-003-001-04 (this revision) replaced the recursion with an
// iterative DFS that maintains a shared parents stack + a parallel
// pathSegments stack + a per-parent tag-counter map. This eliminates
// O(d^2) source-path rebuilds and the O(k^2) per-segment sibling
// re-scan that slice 02's perf review flagged. Public WalkedNode shape
// is preserved (extractors text/image/svg consume it); a new
// `insideSkipZone` flag is added but is purely additive.
//
// Performance characteristics after refactor:
//   - Per node visited: O(1) amortized (push/pop on shared stacks; one
//     tag-counter map lookup; one parents.slice() copy ONLY on emit so
//     text.ts can iterate node.parents without aliasing the live stack).
//   - sourceDomPath built by joining the live pathSegments stack — no
//     per-emit chain rebuild and no per-segment sibling scan.
//   - Walker is O(N) for Brad-shaped documents (shallow depth). Per-emit
//     pathSegments.join + parents.slice remain O(d); total work is
//     O(N*d), effectively O(N) when d is bounded. Verified against the
//     50-row x 10-col table fixture in tests/parser/table.test.ts.

import type { ComputedStyle } from './types';

const SKIP_TAGS = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);

/** A visible element plus enough provenance to build a ContainerRecord. */
export interface WalkedNode {
  element: Element;
  /** CSS-selector-like path from <html> to this element. Deterministic. */
  sourceDomPath: string;
  /** Parent chain, root-most first. Empty for <html>. */
  parents: Element[];
  /** Computed style captured once (per-element, not per-property). */
  computedStyle: CSSStyleDeclaration;
  /**
   * True when this node lies inside a skip-zone subtree (<table> or
   * <svg>). The walker sets this once on subtree entry so downstream
   * dispatch (text-extractor ancestor scan, image-extractor checks) can
   * branch in O(1) instead of an O(d) parents loop. Additive — existing
   * extractors that still loop `parents` continue to work unchanged.
   *
   * Note: the skip-zone ROOT itself (the <table> or <svg> element) has
   * insideSkipZone=false, because dispatch on that root triggers the
   * specialized extractor. Only its descendants are inside the zone.
   * In current policy the walker does NOT descend into <table>/<svg>
   * subtrees (those are leaves from the walker's perspective), so
   * descendants never appear in `out`. The flag is reserved for
   * forward compatibility should the descent policy ever change.
   */
  insideSkipZone: boolean;
  /**
   * Snapshot of the source element's classList at walk time, as a plain
   * string[] (NOT a live DOMTokenList — the walker is the only producer
   * and downstream consumers must see stable values). Added in
   * SLICE-003-001-06 to give the Brad enrichment pass a side-channel
   * read of source classes without touching any frozen extractor.
   *
   * Optional on the type for backward compatibility with hand-constructed
   * WalkedNode stubs in existing test suites (e.g.
   * tests/parser/background.test.ts) that predate slice 06. The walker
   * itself ALWAYS populates this with Array.from(el.classList); only
   * external callers may legitimately omit it. Consumers (orchestrator,
   * enrich()) MUST tolerate undefined and treat it as the empty list.
   */
  domClasses?: string[];
}

/**
 * Walk a parsed Document and yield every visible, non-skipped element in
 * document order. Returns an array (not a generator) so callers can take
 * .length and slice without re-running the walk.
 */
export function walkDom(doc: Document): WalkedNode[] {
  const out: WalkedNode[] = [];
  const root = doc.documentElement;
  if (!root) return out;

  // Iterative DFS frame model. We need an explicit POST-visit ('exit')
  // marker so we can pop parents/pathSegments/counter/multiSet bookkeeping
  // when ascending out of a subtree. The canonical iterative-DFS
  // recipe: emit an exit frame BEFORE pushing child frames (LIFO -> child
  // frames run first, then exit pops the bookkeeping).
  type Frame =
    | { kind: 'enter'; el: Element }
    | { kind: 'exit'; wasSkipZoneRoot: boolean };
  const stack: Frame[] = [{ kind: 'enter', el: root }];

  // Shared mutable bookkeeping. Push on entry, pop on exit.
  const parents: Element[] = [];
  const pathSegments: string[] = [];
  // counterStack[depth]: tag -> running count of children seen so far
  // under parents[depth-1] (or under the doc-pseudo-parent at depth 0).
  // Incremented as each child is visited; the post-increment value is
  // this child's 1-based nth-of-type index.
  const counterStack: Map<string, number>[] = [new Map()];
  // multiTagStack[depth]: tags appearing 2+ times among children of
  // parents[depth-1]. Pre-computed once per parent in O(k); decides
  // whether each child's segment needs a :nth-of-type qualifier.
  const multiTagStack: Set<string>[] = [computeMultiTagSet(doc)];

  // Track depth inside skip-zone subtrees. >0 means current node is
  // INSIDE (a descendant of) a skip zone. Skip-zone roots themselves
  // are NOT inside (the depth increments only AFTER emit). In current
  // policy we don't descend, so this stays 0 in practice.
  let skipZoneDepth = 0;

  while (stack.length > 0) {
    const frame = stack.pop()!;

    if (frame.kind === 'exit') {
      parents.pop();
      pathSegments.pop();
      counterStack.pop();
      multiTagStack.pop();
      if (frame.wasSkipZoneRoot) skipZoneDepth -= 1;
      continue;
    }

    const el = frame.el;

    // Tag-level skip (script/style/noscript/template) — also prunes
    // subtree. No bookkeeping was pushed, so nothing to clean up.
    if (SKIP_TAGS.has(el.tagName)) continue;

    // Aria-hidden skip — prune subtree, since aria-hidden cascades.
    if (el.getAttribute('aria-hidden') === 'true') continue;

    // Computed-style hidden skip — prune subtree because display:none
    // cascades and visibility:hidden propagates to descendants unless
    // explicitly reset. Single getComputedStyle call.
    const style = getComputedStyleSafe(el);
    if (isHiddenStyle(style)) continue;

    // Increment the parent's tag counter for THIS element. The
    // "parent" here is the top of parents[] (depth = parents.length)
    // or the pseudo-doc-parent at depth 0.
    const depth = parents.length;
    const parentCounter = counterStack[depth]!;
    const tagUpper = el.tagName;
    const tagCount = (parentCounter.get(tagUpper) ?? 0) + 1;
    parentCounter.set(tagUpper, tagCount);

    // Decide segment string. multiTagStack[depth] is the pre-computed
    // "tags-with-2+-occurrences" set for this parent.
    const multiSet = multiTagStack[depth]!;
    const tagLower = tagUpper.toLowerCase();
    let segment: string;
    if (depth === 0) {
      // Root <html>: no parent context, emit bare tag.
      segment = tagLower;
    } else if (multiSet.has(tagUpper)) {
      segment = tagLower + ':nth-of-type(' + tagCount + ')';
    } else {
      segment = tagLower;
    }

    pathSegments.push(segment);

    // Emit. parents.slice() is the one allocation we cannot avoid
    // without breaking the public WalkedNode shape (text.ts iterates
    // `node.parents`). Keeping it here preserves the frozen API while
    // the rest of the per-node work is O(1).
    const path = pathSegments.join(' > ');
    const insideSkipZone = skipZoneDepth > 0;
    // Snapshot classList eagerly so downstream code (the Brad enrichment
    // pass, slice 06) sees a stable string[] rather than a live
    // DOMTokenList. Array.from is the canonical conversion; element
    // .classList is always a DOMTokenList on real Element nodes (never
    // null in happy-dom / jsdom / browsers).
    const domClasses = Array.from(el.classList);

    out.push({
      element: el,
      sourceDomPath: path,
      parents: parents.slice(),
      computedStyle: style,
      insideSkipZone,
      domClasses,
    });

    // Skip-zone roots: <svg> is a self-contained leaf (slice 03);
    // <table> is also a leaf as of slice 04 (the table extractor
    // captures the entire <table> in one ContainerRecord; walking
    // its children would let text.ts mis-fire on <td> contents).
    // For both: emit the root, do NOT descend, pop the segment now.
    const tagName = el.tagName;
    const isSkipZoneRoot =
      tagName === 'TABLE' || tagName === 'svg' || tagName === 'SVG';
    if (isSkipZoneRoot) {
      pathSegments.pop();
      // No parents/counter/multi push happened — no exit frame needed.
      continue;
    }

    // Push parents/counter/multi bookkeeping for the descent.
    parents.push(el);
    counterStack.push(new Map());
    multiTagStack.push(computeMultiTagSet(el));

    // Queue exit frame BEFORE child frames so it runs AFTER them (LIFO).
    stack.push({ kind: 'exit', wasSkipZoneRoot: false });

    // Queue children in REVERSE order so they pop in document order.
    const children = el.children;
    for (let i = children.length - 1; i >= 0; i--) {
      const child = children[i];
      if (child) stack.push({ kind: 'enter', el: child });
    }
  }

  return out;
}

/**
 * Pre-compute, for a given parent, the set of child tagNames that have
 * 2+ occurrences. We use this set when deciding whether each child's
 * segment needs :nth-of-type. One O(k) scan per parent — amortized
 * O(1) per child — replaces the prior O(k) scan per emitted segment.
 */
function computeMultiTagSet(parent: Element | Document): Set<string> {
  const out = new Set<string>();
  const counts = new Map<string, number>();
  const children = parent.children;
  if (!children) return out;
  for (let i = 0; i < children.length; i++) {
    const c = children[i];
    if (!c) continue;
    const t = c.tagName;
    const n = (counts.get(t) ?? 0) + 1;
    counts.set(t, n);
    if (n === 2) out.add(t);
  }
  return out;
}

/** True when computed style marks the element as visually hidden. */
function isHiddenStyle(style: CSSStyleDeclaration): boolean {
  if (style.display === 'none') return true;
  if (style.visibility === 'hidden' || style.visibility === 'collapse') return true;
  // opacity is a string in computed style — parseFloat tolerates 0/0.0/etc.
  const opacity = parseFloat(style.opacity);
  if (!Number.isNaN(opacity) && opacity === 0) return true;
  return false;
}

/**
 * getComputedStyle on a detached document (DOMParser output) returns a
 * meaningful style in happy-dom / jsdom / real browsers when the element
 * is inside a document. We still wrap in try/catch as a defensive measure
 * for environments where the implementation throws on disconnected nodes.
 */
function getComputedStyleSafe(el: Element): CSSStyleDeclaration {
  const view = el.ownerDocument?.defaultView;
  if (view && typeof view.getComputedStyle === 'function') {
    try {
      return view.getComputedStyle(el);
    } catch {
      // fall through
    }
  }
  // Synthesized fallback — never hit in happy-dom or browsers. Returns an
  // object shaped like CSSStyleDeclaration for the properties we read.
  return EMPTY_STYLE as unknown as CSSStyleDeclaration;
}

// Fallback computed-style proxy: every property reads as ''.
const EMPTY_STYLE = new Proxy(
  {},
  {
    get(_t, prop) {
      if (prop === 'getPropertyValue') return () => '';
      return '';
    },
  },
);

/** Snapshot the subset of computed styles we expose on ContainerRecord. */
export function snapshotComputedStyle(style: CSSStyleDeclaration): ComputedStyle {
  return {
    fontFamily: style.fontFamily || '',
    fontSize: pxToNumber(style.fontSize),
    color: style.color || '',
    backgroundColor: style.backgroundColor || '',
    lineHeight: pxToNumber(style.lineHeight),
    textAlign: style.textAlign || '',
    fontWeight: weightToNumber(style.fontWeight),
  };
}

function pxToNumber(value: string): number {
  if (!value) return 0;
  // Strip 'px' / whitespace; tolerate 'normal' (line-height) by returning 0.
  const n = parseFloat(value);
  return Number.isFinite(n) ? n : 0;
}

function weightToNumber(value: string): number {
  if (!value) return 400;
  const n = parseInt(value, 10);
  if (Number.isFinite(n)) return n;
  // Named weights — happy-dom usually resolves to numbers; this is defensive.
  if (value === 'bold') return 700;
  if (value === 'normal') return 400;
  return 400;
}
