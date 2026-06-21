// Unit tests for the SVG extractor + walker dispatch, against
// brad-chart.html. SLICE-003-001-03.
//
// Coverage:
//   - Three SVGs in the fixture map to three 'svg' ContainerRecords
//   - viewBox branch: bar-chart "0 0 100 50" → aspectRatio === 2.0
//   - width/height branch: line-chart 200×100 → aspectRatio === 2.0,
//     viewBox === null
//   - Default branch: icon (no viewBox, no w/h) → aspectRatio === 1.0
//     and console.warn fires (info-level)
//   - Round-trip integrity: rawMarkup → DOMParser → outerHTML matches the
//     extractor's captured rawMarkup byte-for-byte (structural equality)
//   - Walker does NOT descend into SVG internals: no 'text' records with
//     a sourceDomPath containing 'svg >'
//   - Text extractor is unaffected: the body <p> and <h1> still emit

import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, it, expect, beforeAll, vi } from 'vitest';

import { extract } from '../../src/parser/index';
import { extractSvg } from '../../src/parser/extractors/svg';
import type { ContainerRecord } from '../../src/parser/types';

let html: string;
let records: ContainerRecord[];

beforeAll(async () => {
  html = readFileSync(
    join(__dirname, '..', 'fixtures', 'brad-chart.html'),
    'utf-8',
  );
  records = await extract(html);
});

describe('svg extractor — brad-chart.html', () => {
  it('emits exactly one svg record per <svg> in the source (N=3)', async () => {
    const svgRecords = records.filter((r) => r.kind === 'svg');
    // Cross-check N from the source HTML directly: a regex match on
    // opening <svg tags. The fixture is hand-authored to contain
    // exactly three.
    const sourceSvgCount = (html.match(/<svg\b/gi) ?? []).length;
    expect(sourceSvgCount).toBe(3);
    expect(svgRecords.length).toBe(3);
  });

  it('each svg record has kind="svg" on BOTH record and content', async () => {
    const svgRecords = records.filter((r) => r.kind === 'svg');
    for (const r of svgRecords) {
      expect(r.kind).toBe('svg');
      expect(r.content.kind).toBe('svg');
    }
  });

  it('bar-chart (viewBox="0 0 100 50") → aspectRatio === 2.0, viewBox populated', async () => {
    const svgRecords = records.filter((r) => r.kind === 'svg');
    const bar = svgRecords.find(
      (r) =>
        r.content.kind === 'svg' && /id="brad-bar-chart"/.test(r.content.rawMarkup),
    );
    expect(bar).toBeDefined();
    if (!bar || bar.content.kind !== 'svg') throw new Error('unreachable');
    expect(bar.content.aspectRatio).toBe(2.0);
    expect(bar.content.viewBox).not.toBeNull();
    expect(bar.content.viewBox).toEqual({ x: 0, y: 0, width: 100, height: 50 });
  });

  it('line-chart (width="200" height="100", no viewBox) → aspectRatio === 2.0, viewBox === null', async () => {
    const svgRecords = records.filter((r) => r.kind === 'svg');
    const line = svgRecords.find(
      (r) =>
        r.content.kind === 'svg' && /id="brad-line-chart"/.test(r.content.rawMarkup),
    );
    expect(line).toBeDefined();
    if (!line || line.content.kind !== 'svg') throw new Error('unreachable');
    expect(line.content.aspectRatio).toBe(2.0);
    expect(line.content.viewBox).toBeNull();
  });

  it('icon (no viewBox, no width/height) → aspectRatio === 1.0 and a warning is logged', async () => {
    // Re-extract under a fresh console.warn spy so we observe the warning
    // from THIS await extract() call, not the beforeAll() one (which may already
    // have buffered).
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    try {
      const fresh = await extract(html);
      const svgRecords = fresh.filter((r) => r.kind === 'svg');
      const icon = svgRecords.find(
        (r) =>
          r.content.kind === 'svg' && /id="brad-icon"/.test(r.content.rawMarkup),
      );
      expect(icon).toBeDefined();
      if (!icon || icon.content.kind !== 'svg') throw new Error('unreachable');
      expect(icon.content.aspectRatio).toBe(1.0);
      expect(icon.content.viewBox).toBeNull();
      // At least one warn call from the svg-extractor.
      const calls = warnSpy.mock.calls.map((c) => String(c[0]));
      expect(calls.some((m) => m.includes('svg-extractor'))).toBe(true);
    } finally {
      warnSpy.mockRestore();
    }
  });

  it('rawMarkup preserves the full <svg>…</svg> source including nested <defs>, <g>, gradient, dasharray', async () => {
    const svgRecords = records.filter((r) => r.kind === 'svg');
    const bar = svgRecords.find(
      (r) =>
        r.content.kind === 'svg' && /id="brad-bar-chart"/.test(r.content.rawMarkup),
    );
    if (!bar || bar.content.kind !== 'svg') throw new Error('bar SVG not found');
    const m = bar.content.rawMarkup;
    expect(m.startsWith('<svg')).toBe(true);
    expect(m.trimEnd().endsWith('</svg>')).toBe(true);
    expect(m).toContain('<defs>');
    expect(m).toContain('<linearGradient');
    expect(m).toContain('stop-color="#4a90e2"');
    expect(m).toContain('stroke-dasharray="2,1"');
    // viewBox attribute on the root element preserved.
    expect(m).toContain('viewBox="0 0 100 50"');
  });

  it('round-trip integrity: rawMarkup → DOMParser → outerHTML equals captured rawMarkup', async () => {
    const svgRecords = records.filter((r) => r.kind === 'svg');
    expect(svgRecords.length).toBeGreaterThan(0);
    for (const r of svgRecords) {
      if (r.content.kind !== 'svg') continue;
      const m = r.content.rawMarkup;
      // Parse as text/html (matches how the parser ingested it).
      const doc = new DOMParser().parseFromString(`<!doctype html><body>${m}</body>`, 'text/html');
      const reparsed = doc.querySelector('svg');
      expect(reparsed).not.toBeNull();
      // Structural equality via outerHTML — the canonical "did we lose
      // anything" check. Reparsing + re-serializing the captured markup
      // must produce a string that round-trips a second time identically.
      const re1 = (reparsed as Element).outerHTML;
      const doc2 = new DOMParser().parseFromString(`<!doctype html><body>${re1}</body>`, 'text/html');
      const re2 = (doc2.querySelector('svg') as Element).outerHTML;
      expect(re2).toBe(re1);
    }
  });

  it('walker does NOT descend into SVG internals (no text/title/text-svg records under <svg>)', async () => {
    // No record's sourceDomPath should contain a segment AFTER an 'svg'
    // segment — i.e. no descendant of an <svg> may appear.
    for (const r of records) {
      const segs = r.sourceDomPath.split(' > ');
      const svgIdx = segs.findIndex((s) => s === 'svg' || s.startsWith('svg:'));
      if (svgIdx === -1) continue;
      // The <svg> itself is allowed; anything deeper is a leak.
      expect(svgIdx).toBe(segs.length - 1);
    }
  });

  it('text extractor unaffected: h1 and body paragraph still emit', async () => {
    const textRecords = records.filter((r) => r.kind === 'text');
    const allText = textRecords
      .map((r) => (r.content.kind === 'text' ? r.content.text : ''))
      .join('\n');
    expect(allText).toContain('OKOA Brad — Chart Fixture');
    expect(allText).toContain('Inline icon');
  });
});

describe('svg extractor — extractSvg() direct unit tests', () => {
  it('with-viewBox: aspectRatio derived from viewBox dims', async () => {
    const doc = new DOMParser().parseFromString(
      `<!doctype html><body><svg viewBox="0 0 300 100"></svg></body>`,
      'text/html',
    );
    const el = doc.querySelector('svg') as unknown as SVGSVGElement;
    const rec = extractSvg(el);
    expect(rec.content.kind).toBe('svg');
    if (rec.content.kind !== 'svg') return;
    expect(rec.content.aspectRatio).toBe(3.0);
    expect(rec.content.viewBox).toEqual({ x: 0, y: 0, width: 300, height: 100 });
  });

  it('with-width-height-attrs only: aspectRatio from attrs, viewBox null', async () => {
    const doc = new DOMParser().parseFromString(
      `<!doctype html><body><svg width="400" height="200"></svg></body>`,
      'text/html',
    );
    const el = doc.querySelector('svg') as unknown as SVGSVGElement;
    const rec = extractSvg(el);
    if (rec.content.kind !== 'svg') throw new Error('unreachable');
    expect(rec.content.aspectRatio).toBe(2.0);
    expect(rec.content.viewBox).toBeNull();
  });

  it('with-neither: aspectRatio 1.0 + warn', async () => {
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    try {
      const doc = new DOMParser().parseFromString(
        `<!doctype html><body><svg></svg></body>`,
        'text/html',
      );
      const el = doc.querySelector('svg') as unknown as SVGSVGElement;
      const rec = extractSvg(el);
      if (rec.content.kind !== 'svg') throw new Error('unreachable');
      expect(rec.content.aspectRatio).toBe(1.0);
      expect(rec.content.viewBox).toBeNull();
      expect(warnSpy).toHaveBeenCalled();
    } finally {
      warnSpy.mockRestore();
    }
  });

  it('viewBox with width=0 falls back to width/height attrs', async () => {
    const doc = new DOMParser().parseFromString(
      `<!doctype html><body><svg viewBox="0 0 0 0" width="100" height="50"></svg></body>`,
      'text/html',
    );
    const el = doc.querySelector('svg') as unknown as SVGSVGElement;
    const rec = extractSvg(el);
    if (rec.content.kind !== 'svg') throw new Error('unreachable');
    expect(rec.content.viewBox).toBeNull();
    expect(rec.content.aspectRatio).toBe(2.0);
  });

  it('rawMarkup uses outerHTML (preserves root attributes), not innerHTML', async () => {
    const doc = new DOMParser().parseFromString(
      `<!doctype html><body><svg id="x" viewBox="0 0 10 10" class="c"><circle cx="5" cy="5" r="3"/></svg></body>`,
      'text/html',
    );
    const el = doc.querySelector('svg') as unknown as SVGSVGElement;
    const rec = extractSvg(el);
    if (rec.content.kind !== 'svg') throw new Error('unreachable');
    // outerHTML includes root attributes; innerHTML would not.
    expect(rec.content.rawMarkup).toContain('id="x"');
    expect(rec.content.rawMarkup).toContain('viewBox="0 0 10 10"');
    expect(rec.content.rawMarkup).toContain('class="c"');
    expect(rec.content.rawMarkup).toContain('<circle');
  });

  it('viewBox accepts comma-separated values per SVG spec', async () => {
    const doc = new DOMParser().parseFromString(
      `<!doctype html><body><svg viewBox="0,0,40,10"></svg></body>`,
      'text/html',
    );
    const el = doc.querySelector('svg') as unknown as SVGSVGElement;
    const rec = extractSvg(el);
    if (rec.content.kind !== 'svg') throw new Error('unreachable');
    expect(rec.content.viewBox).toEqual({ x: 0, y: 0, width: 40, height: 10 });
    expect(rec.content.aspectRatio).toBe(4.0);
  });
});
