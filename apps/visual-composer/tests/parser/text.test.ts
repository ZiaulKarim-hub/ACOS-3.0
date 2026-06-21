// Unit tests for the text extractor + DOM walker, against brad-minimal.html.
//
// SLICE-003-001-02. Verifies:
//   - Every visible <p> in the fixture produces at least one 'text' record
//   - Every visible <h1>/<h2> produces a 'text' record
//   - Hidden paragraphs (display:none, visibility:hidden, aria-hidden,
//     opacity:0) produce ZERO records
//   - <script>, <style>, <noscript>, <template> contents are never emitted
//   - Walker perf smoke: brad-minimal.html walks in <50ms

import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, it, expect, beforeAll } from 'vitest';

import { extract } from '../../src/parser/index';
import type { ContainerRecord } from '../../src/parser/types';

let html: string;
let records: ContainerRecord[];

beforeAll(async () => {
  html = readFileSync(
    join(__dirname, '..', 'fixtures', 'brad-minimal.html'),
    'utf-8',
  );
  records = await extract(html);
});

describe('text extractor — brad-minimal.html', () => {
  it('produces at least 3 text records (one per visible <p>)', async () => {
    const textRecords = records.filter((r) => r.kind === 'text');
    // Three visible <p> + two <h1>/<h2> headings minimum.
    expect(textRecords.length).toBeGreaterThanOrEqual(3);
  });

  it('emits text records for both headings (h1 + h2)', async () => {
    const headingTexts = records
      .filter((r) => r.kind === 'text')
      .map((r) => (r.content.kind === 'text' ? r.content.text : ''));
    expect(headingTexts.some((t) => t.includes('OKOA Brad — Minimal Fixture'))).toBe(true);
    expect(headingTexts.some((t) => t.includes('Section One'))).toBe(true);
  });

  it('emits text records for all three visible paragraphs', async () => {
    const paragraphTexts = records
      .filter((r) => r.kind === 'text')
      .map((r) => (r.content.kind === 'text' ? r.content.text : ''));
    expect(paragraphTexts.some((t) => t.startsWith('First visible paragraph.'))).toBe(true);
    expect(paragraphTexts.some((t) => t.startsWith('Second visible paragraph.'))).toBe(true);
    expect(paragraphTexts.some((t) => t.startsWith('Third visible paragraph'))).toBe(true);
  });

  it('does NOT emit any of the four hidden paragraphs', async () => {
    const allText = records
      .filter((r) => r.kind === 'text')
      .map((r) => (r.content.kind === 'text' ? r.content.text : ''))
      .join('\n');
    expect(allText).not.toMatch(/Hidden via display:none/);
    expect(allText).not.toMatch(/Hidden via visibility:hidden/);
    expect(allText).not.toMatch(/Aria-hidden paragraph/);
    expect(allText).not.toMatch(/Opacity-zero paragraph/);
  });

  it('does NOT emit text from <script>, <style>, <noscript>, or <template>', async () => {
    const paths = records.map((r) => r.sourceDomPath);
    expect(paths.some((p) => p.includes('script'))).toBe(false);
    expect(paths.some((p) => p.includes('style'))).toBe(false);
    expect(paths.some((p) => p.includes('noscript'))).toBe(false);
    expect(paths.some((p) => p.includes('template'))).toBe(false);

    const allText = records
      .filter((r) => r.kind === 'text')
      .map((r) => (r.content.kind === 'text' ? r.content.text : ''))
      .join('\n');
    expect(allText).not.toMatch(/__brad_should_not_run/);
    expect(allText).not.toMatch(/__brad_inline_script_two/);
    expect(allText).not.toMatch(/Inside template/);
    expect(allText).not.toMatch(/scripts are disabled/);
  });

  it('captures a CSS-selector-like sourceDomPath for each record', async () => {
    for (const r of records) {
      expect(r.sourceDomPath).toMatch(/^html( > .+)+$/);
    }
  });

  it('produces deterministic sourceDomPaths (idempotent re-extract)', async () => {
    const second = await extract(html);
    const firstPaths = records.map((r) => r.sourceDomPath);
    const secondPaths = second.map((r) => r.sourceDomPath);
    expect(secondPaths).toEqual(firstPaths);
  });

  it('captures computed-style fields on every record', async () => {
    for (const r of records) {
      expect(typeof r.computedStyle.fontFamily).toBe('string');
      expect(typeof r.computedStyle.fontSize).toBe('number');
      expect(typeof r.computedStyle.color).toBe('string');
      expect(typeof r.computedStyle.backgroundColor).toBe('string');
      expect(typeof r.computedStyle.lineHeight).toBe('number');
      expect(typeof r.computedStyle.textAlign).toBe('string');
      expect(typeof r.computedStyle.fontWeight).toBe('number');
    }
  });

  it('walker performance smoke: brad-minimal.html parses in <50ms (median of 5 with warm-up)', async () => {
    // P4 retrofit (SLICE-003-001-04 plan_addenda): single-sample smoke
    // tests flake under CI load. Median of 5 runs with one warm-up
    // call is robust against transient JIT / GC noise while still
    // catching genuine regressions. Warm-up primes module / JIT caches.
    await extract(html);
    const samples: number[] = [];
    for (let i = 0; i < 5; i++) {
      const start = performance.now();
      await extract(html);
      samples.push(performance.now() - start);
    }
    samples.sort((a, b) => a - b);
    const median = samples[2]!;
    expect(median).toBeLessThan(50);
  });

  it('edge: empty HTML string returns empty array', async () => {
    expect(await extract('')).toEqual([]);
  });

  it('edge: HTML with only hidden elements returns empty array', async () => {
    const hiddenOnly = `
      <html><body>
        <p style="display:none">A</p>
        <p style="visibility:hidden">B</p>
        <p aria-hidden="true">C</p>
        <p style="opacity:0">D</p>
      </body></html>
    `;
    const result = await extract(hiddenOnly);
    // <html> and <body> themselves have no direct text; nothing emits.
    const textOnly = result.filter((r) => r.kind === 'text');
    expect(textOnly).toEqual([]);
  });
});
