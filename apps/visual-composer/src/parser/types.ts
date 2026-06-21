// ContainerRecord — the canonical type contract for EPIC-003 (HTML-to-PDF
// Visual Composer). This is the public API surface every downstream slice
// in stories 003-001 through 003-005 consumes; do NOT mutate the shape
// after this slice ships.
//
// Defined in SLICE-003-001-01 per STORY-003-001 technical_notes.

/** The kind of source-DOM node this container originated from. */
export type NodeKind = 'text' | 'image' | 'svg' | 'table' | 'background';

/** A flat subset of CSSStyleDeclaration we resolve eagerly at extract time. */
export interface ComputedStyle {
  fontFamily: string;
  fontSize: number; // px
  color: string;
  backgroundColor: string;
  lineHeight: number; // px
  textAlign: string;
  fontWeight: number;
}

// --- Discriminated content payloads ---------------------------------------

export interface TextContent {
  kind: 'text';
  text: string;
}

export interface ImageContent {
  kind: 'image';
  src: string;
  alt: string;
}

export interface SvgContent {
  kind: 'svg';
  /**
   * Verbatim SVG markup captured via element.outerHTML. UNTRUSTED — if
   * downstream consumers re-render this via innerHTML, they MUST sanitize
   * first. See extractSvg() in extractors/svg.ts for guidance.
   */
  rawMarkup: string;
  viewBox: { x: number; y: number; width: number; height: number } | null;
  aspectRatio: number;
}

export interface TableCellRecord {
  textContent: string;
  computedStyle: ComputedStyle;
  colSpan: number;
  rowSpan: number;
}

export interface TableRowRecord {
  section: 'thead' | 'tbody' | 'tfoot';
  cells: TableCellRecord[];
}

export interface TableContent {
  kind: 'table';
  rowCount: number;
  columnCount: number;
  columns: { naturalWidth: number }[];
  rows: TableRowRecord[];
}

export interface BackgroundContent {
  kind: 'background';
  url: string;
  naturalWidth: number;
  naturalHeight: number;
  /** 'cover' | 'contain' | 'auto' | other CSS background-size value. */
  backgroundSize: string;
  backgroundPosition: string;
}

/** Union of all per-kind content payloads. */
export type ContainerContent =
  | TextContent
  | ImageContent
  | SvgContent
  | TableContent
  | BackgroundContent;

// --- The container record itself -----------------------------------------

/**
 * A single extracted container from the source HTML document. The `kind`
 * field on the record and the `kind` field on `content` are populated
 * together by the parser (slices 02–05) and must agree at runtime; this
 * structural relationship is not enforced by TypeScript on its own. The
 * smoke test in tests/parser/types.test.ts exercises exhaustive narrowing
 * on both sides of the relationship.
 */
export interface ContainerRecord {
  id: string;
  kind: NodeKind;
  sourceDomPath: string;
  bounds: { width: number; height: number };
  computedStyle: ComputedStyle;
  content: ContainerContent;
  /**
   * Source-element class list as captured by the DOM walker (slice 06).
   * Carried as an additive side-channel so the Brad enrichment pass
   * (brad-enrichment.ts) can run without re-walking the DOM and without
   * forcing every extractor (slices 02-05, all FROZEN) to grow knowledge
   * of class names. Populated by the orchestrator in index.ts after the
   * per-kind extractor returns its record. Optional + backward-compatible:
   * pre-slice-06 callers and any future record produced without walker
   * provenance simply leave it undefined.
   */
  domClasses?: string[];
  /** Set by the Brad enrichment pass (slice 06); undefined until then. */
  bradClass?: string;
}
