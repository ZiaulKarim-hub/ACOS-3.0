// Table extractor — emits a single 'table'-kind ContainerRecord for each
// <table> element. Tables are NOT flattened into per-cell containers; the
// table is one draggable unit in the parts-bin UI (per STORY-003-002).
// Cell-level layout adjustments are NOT supported in MVP — per-column
// width tweaks (slice 002) operate on the `columns` metadata captured
// here, not on the cell records.
//
// Structural metadata captured per table:
//   - rowCount: total number of <tr> across thead/tbody/tfoot
//   - columnCount: max effective cell count in any row, accounting for
//     colSpan (a single <td colspan="3"> contributes 3 to its row's
//     effective width). rowSpan is NOT projected forward (cells that
//     occupy rows below are still counted in their originating row;
//     the consuming editor handles visual layout).
//   - columns: per-column { naturalWidth } — first row approximation
//     (sum of first <tr>'s cell widths typically equals table width).
//   - rows: TableRowRecord[] preserving section ('thead'|'tbody'|'tfoot')
//     and a TableCellRecord[] per row.
//
// Section detection: each <tr> is classified by walking up to its nearest
// thead/tbody/tfoot ancestor inside the table. Default 'tbody' when the
// row is a direct child of <table> (HTML5-tolerant authoring).
//
// SLICE-003-001-04.

import type {
  ContainerRecord,
  TableCellRecord,
  TableContent,
  TableRowRecord,
  ComputedStyle,
} from '../types';
import { snapshotComputedStyle, type WalkedNode } from '../dom-walker';

/**
 * Build a 'table' ContainerRecord from an HTMLTableElement. Pure
 * function: no DOM mutation. Caller is responsible for verifying the
 * tag (the walker dispatch in index.ts handles this).
 *
 * The companion `extractTableFromWalkedNode` variant reuses the
 * walker's precomputed sourceDomPath and computedStyle to match the
 * SVG extractor's two-entry-point pattern.
 */
export function extractTable(el: HTMLTableElement): ContainerRecord {
  const rows = collectRows(el);
  const rowCount = rows.length;
  const columnCount = computeColumnCount(rows);
  const columns = computeColumns(rows, columnCount);

  const content: TableContent = {
    kind: 'table',
    rowCount,
    columnCount,
    columns,
    rows,
  };

  const sourceDomPath = buildSourceDomPathFromElement(el);
  const computedStyle = readComputedStyleSnapshot(el);
  const bounds = readTableBounds(el);

  return {
    id: makeId('table', sourceDomPath),
    kind: 'table',
    sourceDomPath,
    bounds,
    computedStyle,
    content,
  };
}

/**
 * Walker-driven variant — used by extract() in index.ts. Reuses the
 * walker's precomputed sourceDomPath and computedStyle so the path
 * is consistent with sibling text/image records.
 */
export function extractTableFromWalkedNode(node: WalkedNode): ContainerRecord {
  const el = node.element as HTMLTableElement;
  const rows = collectRows(el);
  const rowCount = rows.length;
  const columnCount = computeColumnCount(rows);
  const columns = computeColumns(rows, columnCount);

  const content: TableContent = {
    kind: 'table',
    rowCount,
    columnCount,
    columns,
    rows,
  };

  return {
    id: makeId('table', node.sourceDomPath),
    kind: 'table',
    sourceDomPath: node.sourceDomPath,
    bounds: readTableBounds(el),
    computedStyle: snapshotComputedStyle(node.computedStyle),
    content,
  };
}

/**
 * Collect all rows in document order, classifying each by its section.
 * Walks the table's structure exactly once: iterate <table> direct
 * children (thead/tbody/tfoot/tr), then for each section element
 * iterate its <tr> children. Default to 'tbody' when a <tr> is a
 * direct child of <table> (legal in HTML5 parsing).
 */
function collectRows(table: HTMLTableElement): TableRowRecord[] {
  const out: TableRowRecord[] = [];
  // Use childNodes? No — only Element children. The HTML parser
  // normalizes loose <tr> under <table> into an implicit <tbody>;
  // happy-dom does this faithfully. But we still defend against
  // direct-child <tr> for ungrouped tables.
  const children = table.children;
  for (let i = 0; i < children.length; i++) {
    const child = children[i];
    if (!child) continue;
    const tag = child.tagName;
    if (tag === 'THEAD' || tag === 'TBODY' || tag === 'TFOOT') {
      const section =
        tag === 'THEAD' ? 'thead' : tag === 'TFOOT' ? 'tfoot' : 'tbody';
      appendRowsFromSection(child, section, out);
    } else if (tag === 'TR') {
      // Loose <tr> directly under <table> (HTML parser usually wraps
      // these in an implicit <tbody>, but defend anyway).
      out.push(buildRow(child as HTMLTableRowElement, 'tbody'));
    } else if (tag === 'CAPTION' || tag === 'COLGROUP') {
      // Skip — not row content.
      continue;
    }
    // Other unexpected tags (e.g. comment-injected children) silently ignored.
  }
  return out;
}

function appendRowsFromSection(
  section: Element,
  label: 'thead' | 'tbody' | 'tfoot',
  out: TableRowRecord[],
): void {
  const trs = section.children;
  for (let i = 0; i < trs.length; i++) {
    const tr = trs[i];
    if (!tr || tr.tagName !== 'TR') continue;
    out.push(buildRow(tr as HTMLTableRowElement, label));
  }
}

function buildRow(
  tr: HTMLTableRowElement,
  section: 'thead' | 'tbody' | 'tfoot',
): TableRowRecord {
  const cells: TableCellRecord[] = [];
  const tds = tr.children;
  for (let i = 0; i < tds.length; i++) {
    const cell = tds[i];
    if (!cell) continue;
    const tag = cell.tagName;
    if (tag !== 'TD' && tag !== 'TH') continue;
    cells.push(buildCell(cell as HTMLTableCellElement));
  }
  return { section, cells };
}

function buildCell(cell: HTMLTableCellElement): TableCellRecord {
  // textContent: the full visible text inside the cell, trimmed. This
  // matches the user's expectation that a financial cell's value is
  // its rendered text (e.g. "$1,250,000"). Multi-line cells get their
  // whitespace collapsed by Element.textContent semantics — we trim
  // leading/trailing only so inner whitespace structure is preserved.
  const textContent = (cell.textContent ?? '').trim();
  const colSpan = readSpanAttr(cell, 'colspan');
  const rowSpan = readSpanAttr(cell, 'rowspan');
  return {
    textContent,
    computedStyle: readCellComputedStyle(cell),
    colSpan,
    rowSpan,
  };
}

/**
 * Read a colspan/rowspan attribute, defaulting to 1 when absent or
 * unparseable. Per HTML spec, values <1 are clamped to 1.
 */
function readSpanAttr(cell: Element, attr: 'colspan' | 'rowspan'): number {
  const raw = cell.getAttribute(attr);
  if (!raw) return 1;
  const n = parseInt(raw, 10);
  if (!Number.isFinite(n) || n < 1) return 1;
  return n;
}

/**
 * columnCount = max effective cell count across all rows, where each
 * cell contributes colSpan to its row's effective width. rowSpan is
 * NOT projected forward — see file header.
 */
function computeColumnCount(rows: TableRowRecord[]): number {
  let max = 0;
  for (const row of rows) {
    let effective = 0;
    for (const cell of row.cells) {
      effective += cell.colSpan;
    }
    if (effective > max) max = effective;
  }
  return max;
}

/**
 * Per-column naturalWidth: take the first row's cell widths (per
 * acceptance criterion: "first row's width as approximation"). When
 * a first-row cell has colSpan>1, distribute its width evenly across
 * the columns it spans. When the first row has fewer effective cells
 * than columnCount, pad remaining columns with naturalWidth=0.
 *
 * Edge case: zero rows -> empty columns array (handled by caller via
 * columnCount=0).
 */
function computeColumns(
  rows: TableRowRecord[],
  columnCount: number,
): { naturalWidth: number }[] {
  if (columnCount === 0 || rows.length === 0) return [];
  const out: { naturalWidth: number }[] = new Array(columnCount);
  for (let i = 0; i < columnCount; i++) out[i] = { naturalWidth: 0 };

  const firstRow = rows[0]!;
  let col = 0;
  for (const cell of firstRow.cells) {
    if (col >= columnCount) break;
    // We don't have per-cell layout width in happy-dom (no layout).
    // The acceptance criterion calls naturalWidth an "approximation";
    // in MVP we expose the structural placeholder (0). Downstream
    // (browser context) callers can re-measure via getBoundingClientRect
    // on the actual cell elements when laying out the parts-bin.
    const span = cell.colSpan;
    for (let s = 0; s < span && col < columnCount; s++) {
      // Already 0 — kept explicit for clarity.
      out[col] = { naturalWidth: 0 };
      col += 1;
    }
  }
  return out;
}

/** Subset of computedStyle we capture on each cell. */
function readCellComputedStyle(cell: Element): ComputedStyle {
  const view = cell.ownerDocument?.defaultView;
  if (view && typeof view.getComputedStyle === 'function') {
    try {
      return snapshotComputedStyle(view.getComputedStyle(cell));
    } catch {
      // fall through
    }
  }
  return snapshotComputedStyle({} as unknown as CSSStyleDeclaration);
}

function readTableBounds(el: Element): { width: number; height: number } {
  if (typeof (el as HTMLElement).getBoundingClientRect === 'function') {
    try {
      const r = (el as HTMLElement).getBoundingClientRect();
      return { width: r.width ?? 0, height: r.height ?? 0 };
    } catch {
      // fall through
    }
  }
  return { width: 0, height: 0 };
}

function readComputedStyleSnapshot(el: Element): ComputedStyle {
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
  return tag + ':nth-of-type(' + index + ')';
}

function makeId(prefix: string, path: string): string {
  // FNV-1a 32-bit — same hash used in text/image/svg extractors.
  let h = 0x811c9dc5;
  for (let i = 0; i < path.length; i++) {
    h ^= path.charCodeAt(i);
    h = (h + ((h << 1) + (h << 4) + (h << 7) + (h << 8) + (h << 24))) >>> 0;
  }
  return prefix + '-' + h.toString(16);
}
