// Public entry point for the HTML parts-bin extractor.
//
// SLICE-003-001-02 wired the DOM walker + text + image extractors.
// SLICE-003-001-03 added the SVG extractor dispatch.
// SLICE-003-001-04 added the TABLE extractor dispatch.
// SLICE-003-001-05 added the BACKGROUND extractor and flipped extract()
// from sync to async — the first slice whose extractor requires I/O.
// SLICE-003-001-06 added the Brad-class enrichment pass (post-walk).
// SLICE-003-001-07 (this revision) is the story-closing slice. It:
//   - locks the public API surface (only extract + ContainerRecord +
//     NodeKind + supporting type re-exports + the Brad helpers from
//     slice 06 cross the module boundary)
//   - accepts an optional opts argument enabling generic-HTML fallback
//     mode via { bradEnrichment: false }
//   - folds the slice-06 enrich() pass into the default pipeline so
//     callers receive Brad-tagged records without a second call
//   - adds a runtime dual-discriminator invariant check (F2) that
//     catches future parser-slice bugs where ContainerRecord.kind and
//     ContainerRecord.content.kind desync

import type { ContainerRecord } from './types';
import { walkDom } from './dom-walker';
import { extractText } from './extractors/text';
import { extractImage } from './extractors/image';
import { extractSvgFromWalkedNode } from './extractors/svg';
import { extractTableFromWalkedNode } from './extractors/table';
import { extractBackground } from './extractors/background';
import { enrich } from './brad-enrichment';

// Brad-class semantic enrichment helpers (slice 06). Re-exported so
// downstream stories that want to inspect or override the taxonomy can
// import the canonical names + priority list without reaching across
// the parser module boundary. extract() itself folds enrich() into the
// default pipeline (see ExtractOptions below), so most callers will
// never need to import enrich() directly.
export { enrich } from './brad-enrichment';
export type { EnrichOptions } from './brad-enrichment';
export {
  BRAD_CLASSES,
  BRAD_CLASS_SET,
  BRAD_CLASS_PRIORITY,
  type BradClass,
} from './brad-taxonomy';

// Public type re-exports — the ContainerRecord shape is the canonical
// contract STORY-003-002 (canvas) and every downstream story consumes.
// All other parser internals (walker, individual extractors, helpers)
// stay private to the module.
export type { ContainerRecord } from './types';
export type {
  NodeKind,
  ComputedStyle,
  ContainerContent,
  TextContent,
  ImageContent,
  SvgContent,
  TableContent,
  TableRowRecord,
  TableCellRecord,
  BackgroundContent,
} from './types';

/**
 * Options bag for {@link extract}. Optional argument; defaults are tuned
 * for OKOA Brad documents (the primary consumer).
 */
export interface ExtractOptions {
  /**
   * When true (default), the Brad-class enrichment pass runs after
   * extraction so records bearing a known Brad class are tagged with
   * `bradClass`. When false, the enrichment pass is skipped entirely —
   * use this for generic-HTML inputs (news articles, third-party docs)
   * where Brad class names are not expected and false-positive matches
   * would be misleading. See brad-enrichment.ts for the contract.
   */
  bradEnrichment?: boolean;
}

/**
 * Extract a flat list of {@link ContainerRecord} entries from an HTML
 * document.
 *
 * Pipeline (fixed order, documented for slice-07 acceptance criterion):
 *   1. Parse  — DOMParser parseFromString('text/html'); scripts do NOT
 *               execute (XSS sandbox proof — see xss-sandbox.test.ts).
 *   2. Walk   — single-pass DFS, capturing computed style + provenance.
 *   3. Extract per kind — img -> image, svg -> svg, table -> table,
 *               everything else -> text (when visible).
 *   4. Background pass on every walked element (a styled <div> with
 *               background-image AND text emits TWO records by design).
 *   5. Await   — Promise.all on background loads, preserving order.
 *   6. Enrich  — Brad-class tagging on records carrying domClasses;
 *               skipped when opts.bradEnrichment === false.
 *   7. Invariant — every returned record satisfies the dual-discriminator
 *               coherence rule record.kind === record.content.kind (F2).
 *   8. Return.
 *
 * Same-element-two-kinds: a styled <div> with `background-image` AND
 * direct text content produces BOTH a 'text' record AND a 'background'
 * record (distinct ids, same sourceDomPath). This is deliberate — the
 * user must be able to drag the typography and the photo independently.
 *
 * @param html Raw HTML markup.
 * @param opts Optional options bag. Defaults to Brad-enrichment ON.
 * @returns A flat array of extracted containers.
 */
export async function extract(
  html: string,
  opts?: ExtractOptions,
): Promise<ContainerRecord[]> {
  if (!html || typeof html !== 'string') return [];

  // DOMParser is available in browsers, happy-dom, and jsdom test envs.
  // If we ever run in a pure-node context without DOM, return early.
  if (typeof DOMParser === 'undefined') return [];

  const doc = new DOMParser().parseFromString(html, 'text/html');
  const walked = walkDom(doc);

  // Synchronous records (text/image/svg/table) accumulate here in
  // document order.
  const syncRecords: ContainerRecord[] = [];
  // Background extraction is async; queue the promises and await them
  // in parallel at the end of the walk. Awaiting per-node would
  // serialize image loads and destroy the perf budget (acceptance
  // criterion #10: 5 backgrounds load in parallel in <500ms).
  const bgPromises: Promise<ContainerRecord | null>[] = [];

  for (const node of walked) {
    const tag = node.element.tagName;
    // Post-construction domClass attachment helper. The extractors
    // (text/image/svg/table/background) are FROZEN by slice 06 — they
    // cannot grow a domClasses field. Instead, the orchestrator owns
    // the wiring: every record emitted in this loop is tagged with
    // node.domClasses BEFORE being pushed downstream. The mutation is
    // safe because the record was just constructed by the extractor
    // and is not yet observable by any external caller.
    // Walker-produced nodes always carry domClasses; pre-slice-06
    // hand-built WalkedNode stubs in existing tests may not. Coalesce
    // to [] so downstream record.domClasses is always a defined array
    // (matches the type widening done on the WalkedNode side).
    const nodeClasses = node.domClasses ?? [];
    const attach = (rec: ContainerRecord): ContainerRecord => {
      rec.domClasses = nodeClasses;
      return rec;
    };

    if (tag === 'IMG') {
      syncRecords.push(attach(extractImage(node)));
    } else if (tag === 'svg' || tag === 'SVG') {
      // Tag comparison is case-insensitive: HTML parsing gives 'IMG' but
      // inline <svg> parsed as an SVGSVGElement reports tagName === 'svg'
      // (lower-case) in both happy-dom and real browsers.
      syncRecords.push(attach(extractSvgFromWalkedNode(node)));
    } else if (tag === 'TABLE') {
      // The walker emits the <table> node itself but does NOT descend
      // into its children (see dom-walker.ts skip-zone roots). The
      // table extractor walks the table's structure directly and
      // produces ONE ContainerRecord for the whole table.
      syncRecords.push(attach(extractTableFromWalkedNode(node)));
    } else {
      const textRecord = extractText(node);
      if (textRecord) syncRecords.push(attach(textRecord));
    }

    // Background pass runs on EVERY walked element regardless of kind
    // dispatch above. A <div class="hero"> can be a text record AND a
    // background record simultaneously; an <img> with a CSS background
    // would emit two records (rare but legal). Skip-zone roots (<svg>,
    // <table>) are intentionally included — a chart container with a
    // background watermark is a real Brad pattern.
    //
    // Wrap the async background result so the same domClasses snapshot
    // gets attached when it resolves. The snapshot is captured in the
    // closure so iteration mutation of `node` (there is none, but the
    // capture is defensive) cannot affect it.
    const bgDomClasses = nodeClasses;
    bgPromises.push(
      extractBackground(node).then((r) => {
        if (r !== null) r.domClasses = bgDomClasses;
        return r;
      }),
    );
  }

  // Promise.all preserves order — bgPromises[i] resolves to the
  // background record (or null) for walked[i]. Filter out the nulls.
  const bgResults = await Promise.all(bgPromises);
  const bgRecords: ContainerRecord[] = [];
  for (const r of bgResults) {
    if (r !== null) bgRecords.push(r);
  }

  const merged: ContainerRecord[] = [...syncRecords, ...bgRecords];

  // Brad-class enrichment. The slice-06 contract guarantees that when
  // enabled=false the input array reference is returned unchanged
  // (zero overhead, zero mutation) — so we always route through
  // enrich() and let it short-circuit. The bradEnrichment default is
  // TRUE: Brad documents are the dominant input. Pass enabled=false
  // for generic-HTML fallback.
  const bradEnrichmentEnabled = opts?.bradEnrichment !== false;
  const enriched = enrich(merged, { enabled: bradEnrichmentEnabled });

  // F2 (slice 07): dual-discriminator runtime invariant. ContainerRecord
  // carries `kind` on BOTH the outer record AND its content payload;
  // TypeScript cannot enforce structural agreement between them, so a
  // buggy parser slice (02-05 are FROZEN, but a future regression could
  // still desync the two fields) would silently emit malformed records.
  // We assert coherence on every record before returning. The cost is
  // O(N) with N = record count — negligible (<0.1ms typical) and well
  // worth the early-fail safety it gives downstream stories.
  for (const r of enriched) assertKindCoherent(r);

  return enriched;
}

/**
 * Runtime invariant — every ContainerRecord must carry the same `kind`
 * on its outer envelope AND on its inner content payload. Throws an
 * explicit Error when the two discriminators disagree so the failing
 * record's identity is visible in the stack trace.
 *
 * Not exported: this is an internal correctness check, not part of the
 * public API. Tests reach into it indirectly via extract().
 */
function assertKindCoherent(r: ContainerRecord): void {
  if (r.kind !== r.content.kind) {
    throw new Error(
      `[visual-composer/parser] dual-discriminator desync: ` +
        `record.kind="${r.kind}" but record.content.kind="${r.content.kind}" ` +
        `on record id="${r.id}" path="${r.sourceDomPath}". ` +
        `This indicates an internal parser bug — please file an issue.`,
    );
  }
}
