// Text extractor — emits a 'text'-kind ContainerRecord for elements that
// carry direct text content (not nested-children text). Returns null when
// the element should not become a text container.
//
// Eligible tags: <p>, <h1>–<h6>, and <div>/<span> with non-empty direct
// text content. <table>/<svg> internals are excluded — those have dedicated
// extractor slices.

import type { ContainerRecord, TextContent } from '../types';
import { snapshotComputedStyle, type WalkedNode } from '../dom-walker';

const TEXT_TAGS = new Set(['P', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6']);
const TEXT_LEAF_CANDIDATE_TAGS = new Set(['DIV', 'SPAN']);
const SKIP_TEXT_INSIDE = new Set(['TABLE', 'SVG', 'THEAD', 'TBODY', 'TFOOT', 'TR', 'TD', 'TH']);

/**
 * Build a 'text' ContainerRecord from a walker node, or return null when
 * the element should not become a text container.
 *
 * Pure function: does not mutate the input element or walker node.
 */
export function extractText(node: WalkedNode): ContainerRecord | null {
  const el = node.element;
  const tag = el.tagName;

  // Inside table/svg sub-trees: defer to those extractors.
  for (const ancestor of node.parents) {
    if (SKIP_TEXT_INSIDE.has(ancestor.tagName)) return null;
  }

  const isHeadingOrParagraph = TEXT_TAGS.has(tag);
  const isLeafCandidate = TEXT_LEAF_CANDIDATE_TAGS.has(tag);
  if (!isHeadingOrParagraph && !isLeafCandidate) return null;

  // Direct text content only — filter to Node.TEXT_NODE children, trim.
  const directText = getDirectText(el);
  if (!directText) return null;

  // For <div>/<span> leaves we additionally require: no element children
  // that themselves would emit text (heuristic: if the element has any
  // element children, we let those children own the text and skip this one).
  if (isLeafCandidate && el.children.length > 0) return null;

  const content: TextContent = { kind: 'text', text: directText };
  const computedStyle = snapshotComputedStyle(node.computedStyle);
  const bounds = readBounds(el);

  return {
    id: makeId('text', node.sourceDomPath),
    kind: 'text',
    sourceDomPath: node.sourceDomPath,
    bounds,
    computedStyle,
    content,
  };
}

/** Direct-child text content, joined and trimmed. Empty string => no text. */
function getDirectText(el: Element): string {
  const TEXT_NODE = 3; // Node.TEXT_NODE — avoids importing Node type
  let buf = '';
  const children = el.childNodes;
  for (let i = 0; i < children.length; i++) {
    const c = children[i];
    if (c && c.nodeType === TEXT_NODE) {
      buf += c.nodeValue ?? '';
    }
  }
  return buf.trim();
}

function readBounds(el: Element): { width: number; height: number } {
  // happy-dom returns zero-valued ClientRects (no layout). Fall back to
  // declared width/height attributes when present. Real-browser callers
  // get the layout rect.
  const rect = typeof (el as HTMLElement).getBoundingClientRect === 'function'
    ? (el as HTMLElement).getBoundingClientRect()
    : null;
  let width = rect?.width ?? 0;
  let height = rect?.height ?? 0;
  if (!width) {
    const w = (el as HTMLElement).getAttribute?.('width');
    if (w) {
      const n = parseFloat(w);
      if (Number.isFinite(n)) width = n;
    }
  }
  if (!height) {
    const h = (el as HTMLElement).getAttribute?.('height');
    if (h) {
      const n = parseFloat(h);
      if (Number.isFinite(n)) height = n;
    }
  }
  return { width, height };
}

function makeId(prefix: string, path: string): string {
  // Stable, derived from source-DOM path. Hash-light: just FNV-1a 32-bit
  // for a short token. Determinism > cryptographic strength here.
  let h = 0x811c9dc5;
  for (let i = 0; i < path.length; i++) {
    h ^= path.charCodeAt(i);
    h = (h + ((h << 1) + (h << 4) + (h << 7) + (h << 8) + (h << 24))) >>> 0;
  }
  return `${prefix}-${h.toString(16)}`;
}
