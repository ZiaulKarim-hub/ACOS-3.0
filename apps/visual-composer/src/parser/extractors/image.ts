// Image extractor — emits an 'image'-kind ContainerRecord for <img> elements.
// Pure function; does not load the image (use new Image() in caller for that).

import type { ContainerRecord, ImageContent } from '../types';
import { snapshotComputedStyle, type WalkedNode } from '../dom-walker';

/**
 * Build an 'image' ContainerRecord from a walker node whose element is an
 * HTMLImageElement. Caller is responsible for verifying tagName === 'IMG'.
 *
 * Bounds use naturalWidth/naturalHeight when available (data: URIs in
 * happy-dom resolve synchronously); otherwise fall back to width/height
 * attributes, then to layout rect.
 */
export function extractImage(node: WalkedNode): ContainerRecord {
  const el = node.element as HTMLImageElement;
  const src = el.getAttribute('src') ?? '';
  const alt = el.getAttribute('alt') ?? '';

  const content: ImageContent = { kind: 'image', src, alt };
  const computedStyle = snapshotComputedStyle(node.computedStyle);
  const bounds = readImageBounds(el);

  return {
    id: makeId('image', node.sourceDomPath),
    kind: 'image',
    sourceDomPath: node.sourceDomPath,
    bounds,
    computedStyle,
    content,
  };
}

function readImageBounds(el: HTMLImageElement): { width: number; height: number } {
  // Prefer naturalWidth/naturalHeight when populated.
  const nw = el.naturalWidth ?? 0;
  const nh = el.naturalHeight ?? 0;
  if (nw > 0 || nh > 0) return { width: nw, height: nh };

  // Declared attributes.
  let width = 0;
  let height = 0;
  const wAttr = el.getAttribute('width');
  if (wAttr) {
    const n = parseFloat(wAttr);
    if (Number.isFinite(n)) width = n;
  }
  const hAttr = el.getAttribute('height');
  if (hAttr) {
    const n = parseFloat(hAttr);
    if (Number.isFinite(n)) height = n;
  }
  if (width || height) return { width, height };

  // Last-resort: layout rect (zero in happy-dom).
  if (typeof el.getBoundingClientRect === 'function') {
    const r = el.getBoundingClientRect();
    return { width: r.width ?? 0, height: r.height ?? 0 };
  }
  return { width: 0, height: 0 };
}

function makeId(prefix: string, path: string): string {
  let h = 0x811c9dc5;
  for (let i = 0; i < path.length; i++) {
    h ^= path.charCodeAt(i);
    h = (h + ((h << 1) + (h << 4) + (h << 7) + (h << 8) + (h << 24))) >>> 0;
  }
  return `${prefix}-${h.toString(16)}`;
}
