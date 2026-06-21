// SVG extractor — emits an 'svg'-kind ContainerRecord for inline <svg>
// elements. The raw markup is preserved verbatim via el.outerHTML so the
// downstream editor + Puppeteer PDF export pipeline can re-render the
// chart at any size without quality loss. ZERO traversal of internal
// <path>/<g>/<text> nodes — that's the entire point of this extractor.
//
// SLICE-003-001-03.

import type { ContainerRecord, SvgContent } from '../types';
import { snapshotComputedStyle, type WalkedNode } from '../dom-walker';

/**
 * SECURITY: rawMarkup is preserved verbatim from the source HTML for
 * lossless chart fidelity. DOMParser blocks script execution at parse
 * time, but downstream consumers that re-render rawMarkup via innerHTML
 * (e.g., the canvas in STORY-003-002) MUST sanitize first. Recommended
 * sanitizers: DOMPurify with the SVG profile, OR re-parse via DOMParser
 * and strip <script>, <foreignObject>, all on* attributes, and
 * javascript:/data:text URIs in href/xlink:href before insertion.
 *
 * The parser does NOT sanitize because:
 *   1. Faithful capture is required for chart rendering quality
 *   2. Sanitization is a render-time concern, not a parse-time concern
 *   3. Different consumers may need different sanitizer profiles
 */
/**
 * Build an 'svg' ContainerRecord from an SVGSVGElement. The caller is
 * responsible for verifying the tag (the dispatch in dom-walker / extract()
 * handles this). Pure function: no DOM mutation, no side effects beyond a
 * single `console.warn` when neither viewBox nor width/height attributes
 * are available to derive an aspect ratio.
 */
export function extractSvg(el: SVGSVGElement): ContainerRecord {
  // rawMarkup MUST be el.outerHTML (NOT innerHTML) so the root <svg>
  // attributes — xmlns, viewBox, preserveAspectRatio, width/height,
  // class, style — are preserved. innerHTML would silently drop them.
  // UNTRUSTED — see SECURITY note above.
  const rawMarkup = el.outerHTML;

  const viewBox = parseViewBox(el);
  const aspectRatio = computeAspectRatio(el, viewBox);

  const content: SvgContent = {
    kind: 'svg',
    rawMarkup,
    viewBox,
    aspectRatio,
  };

  const sourceDomPath = buildSourceDomPathFromElement(el);
  const computedStyle = readComputedStyleSnapshot(el);
  const bounds = readSvgBounds(el, viewBox);

  return {
    id: makeId('svg', sourceDomPath),
    kind: 'svg',
    sourceDomPath,
    bounds,
    computedStyle,
    content,
  };
}

/**
 * SECURITY: rawMarkup is preserved verbatim from the source HTML for
 * lossless chart fidelity. DOMParser blocks script execution at parse
 * time, but downstream consumers that re-render rawMarkup via innerHTML
 * (e.g., the canvas in STORY-003-002) MUST sanitize first. Recommended
 * sanitizers: DOMPurify with the SVG profile, OR re-parse via DOMParser
 * and strip <script>, <foreignObject>, all on* attributes, and
 * javascript:/data:text URIs in href/xlink:href before insertion.
 *
 * The parser does NOT sanitize because:
 *   1. Faithful capture is required for chart rendering quality
 *   2. Sanitization is a render-time concern, not a parse-time concern
 *   3. Different consumers may need different sanitizer profiles
 */
/**
 * Walker-driven variant: when extract() already has a WalkedNode, reuse
 * the precomputed sourceDomPath and computedStyle. Consistent with
 * extractText/extractImage which both take a WalkedNode.
 */
export function extractSvgFromWalkedNode(node: WalkedNode): ContainerRecord {
  const el = node.element as unknown as SVGSVGElement;
  // UNTRUSTED — see SECURITY note above.
  const rawMarkup = el.outerHTML;
  const viewBox = parseViewBox(el);
  const aspectRatio = computeAspectRatio(el, viewBox);

  const content: SvgContent = {
    kind: 'svg',
    rawMarkup,
    viewBox,
    aspectRatio,
  };

  return {
    id: makeId('svg', node.sourceDomPath),
    kind: 'svg',
    sourceDomPath: node.sourceDomPath,
    bounds: readSvgBounds(el, viewBox),
    computedStyle: snapshotComputedStyle(node.computedStyle),
    content,
  };
}

/**
 * Parse the SVG viewBox. Returns null when the attribute is absent,
 * unparseable, or has width/height === 0 (effectively absent).
 *
 * Prefers the live SVGSVGElement.viewBox.baseVal SVGRect when available,
 * with a manual string-parse fallback for environments where the SVG
 * DOM API is not fully implemented.
 */
function parseViewBox(
  el: SVGSVGElement,
): { x: number; y: number; width: number; height: number } | null {
  const attr = el.getAttribute('viewBox');
  if (!attr) return null;

  // Try DOM API first.
  try {
    const baseVal = (el.viewBox as unknown as {
      baseVal?: { x: number; y: number; width: number; height: number };
    })?.baseVal;
    if (
      baseVal &&
      Number.isFinite(baseVal.width) &&
      Number.isFinite(baseVal.height) &&
      baseVal.width > 0 &&
      baseVal.height > 0
    ) {
      return {
        x: baseVal.x,
        y: baseVal.y,
        width: baseVal.width,
        height: baseVal.height,
      };
    }
  } catch {
    // fall through to attribute string parse
  }

  // Manual parse — SVG spec allows comma and/or whitespace separators.
  const parts = attr.trim().split(/[\s,]+/).map(parseFloat);
  if (parts.length !== 4) return null;
  const [x, y, width, height] = parts as [number, number, number, number];
  if (
    !Number.isFinite(x) ||
    !Number.isFinite(y) ||
    !Number.isFinite(width) ||
    !Number.isFinite(height)
  ) {
    return null;
  }
  if (width <= 0 || height <= 0) return null;
  return { x, y, width, height };
}

/**
 * Compute aspectRatio per the slice's strict fallback order:
 *   1. viewBox.width / viewBox.height if both > 0
 *   2. width attr / height attr if both > 0
 *   3. fallback 1.0 + console.warn (info-level)
 */
function computeAspectRatio(
  el: SVGSVGElement,
  viewBox: { width: number; height: number } | null,
): number {
  if (viewBox && viewBox.width > 0 && viewBox.height > 0) {
    return viewBox.width / viewBox.height;
  }

  const widthAttr = parseNumericAttr(el, 'width');
  const heightAttr = parseNumericAttr(el, 'height');
  if (widthAttr > 0 && heightAttr > 0) {
    return widthAttr / heightAttr;
  }

  // eslint-disable-next-line no-console
  console.warn(
    '[visual-composer/svg-extractor] SVG has neither viewBox nor width/height attributes; defaulting aspectRatio to 1.0',
  );
  return 1.0;
}

function parseNumericAttr(el: Element, name: string): number {
  const raw = el.getAttribute(name);
  if (!raw) return 0;
  const n = parseFloat(raw);
  return Number.isFinite(n) && n > 0 ? n : 0;
}

function readSvgBounds(
  el: SVGSVGElement,
  viewBox: { width: number; height: number } | null,
): { width: number; height: number } {
  const widthAttr = parseNumericAttr(el, 'width');
  const heightAttr = parseNumericAttr(el, 'height');
  if (widthAttr > 0 || heightAttr > 0) {
    return { width: widthAttr, height: heightAttr };
  }
  if (viewBox && viewBox.width > 0 && viewBox.height > 0) {
    return { width: viewBox.width, height: viewBox.height };
  }
  // happy-dom has no layout — falls through to zero.
  const anyEl = el as unknown as { getBoundingClientRect?: () => DOMRect };
  if (typeof anyEl.getBoundingClientRect === 'function') {
    try {
      const r = anyEl.getBoundingClientRect();
      return { width: r.width ?? 0, height: r.height ?? 0 };
    } catch {
      // fall through
    }
  }
  return { width: 0, height: 0 };
}

function buildSourceDomPathFromElement(el: Element): string {
  const chain: Element[] = [];
  let cur: Element | null = el;
  while (cur) {
    chain.unshift(cur);
    cur = cur.parentElement;
  }
  const segments: string[] = [];
  for (let i = 0; i < chain.length; i++) {
    const node = chain[i]!;
    const parent = i === 0 ? null : chain[i - 1]!;
    segments.push(segmentFor(node, parent));
  }
  return segments.join(' > ');
}

function segmentFor(el: Element, parent: Element | null): string {
  const tag = el.tagName.toLowerCase();
  if (!parent) return tag;
  let total = 0;
  let index = 0;
  const siblings = parent.children;
  for (let i = 0; i < siblings.length; i++) {
    const s = siblings[i];
    if (!s) continue;
    if (s.tagName === el.tagName) {
      total += 1;
      if (s === el) index = total;
    }
  }
  if (total <= 1) return tag;
  return `${tag}:nth-of-type(${index})`;
}

function readComputedStyleSnapshot(el: Element) {
  const view = el.ownerDocument?.defaultView;
  if (view && typeof view.getComputedStyle === 'function') {
    try {
      return snapshotComputedStyle(view.getComputedStyle(el));
    } catch {
      // fall through
    }
  }
  return snapshotComputedStyle({} as unknown as CSSStyleDeclaration);
}

function makeId(prefix: string, path: string): string {
  // FNV-1a 32-bit — same hash used in text/image extractors.
  let h = 0x811c9dc5;
  for (let i = 0; i < path.length; i++) {
    h ^= path.charCodeAt(i);
    h = (h + ((h << 1) + (h << 4) + (h << 7) + (h << 8) + (h << 24))) >>> 0;
  }
  return `${prefix}-${h.toString(16)}`;
}
