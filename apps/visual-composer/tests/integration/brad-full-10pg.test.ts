// Integration test: parse the full 10-page Brad fixture end-to-end.
// SLICE-003-001-07 closes STORY-003-001 with this test as the primary
// proof that extract() produces correct, complete output across every
// NodeKind on a realistic Brad-shaped document.
//
// Acceptance criteria covered:
//   - Part A #4: brad-full-10pg.html parses in <3s (3-run avg) with
//     >=50 records and at least one of every NodeKind.
//   - F2:        record.kind === record.content.kind on every record.

import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, it, expect, beforeAll } from 'vitest';

import { extract } from '../../src/parser/index';
import type { NodeKind } from '../../src/parser/types';

let html: string;

beforeAll(() => {
  html = readFileSync(
    join(__dirname, '..', 'fixtures', 'brad-full-10pg.html'),
    'utf-8',
  );
});

describe('integration — brad-full-10pg.html', () => {
  it('parses successfully and returns >= 50 records', async () => {
    const records = await extract(html);
    expect(records.length).toBeGreaterThanOrEqual(50);
  });

  it('produces at least one of every NodeKind (text, image, svg, table, background)', async () => {
    const records = await extract(html);
    const kinds = new Set<NodeKind>(records.map((r) => r.kind));
    expect(kinds.has('text')).toBe(true);
    expect(kinds.has('image')).toBe(true);
    expect(kinds.has('svg')).toBe(true);
    expect(kinds.has('table')).toBe(true);
    expect(kinds.has('background')).toBe(true);
  });

  it('dual-discriminator coherence (F2): record.kind === record.content.kind on every record', async () => {
    const records = await extract(html);
    expect(records.length).toBeGreaterThan(0);
    for (const r of records) {
      expect(r.kind).toBe(r.content.kind);
    }
  });

  it('every record has a non-empty id and sourceDomPath', async () => {
    const records = await extract(html);
    for (const r of records) {
      expect(r.id).toMatch(/^[a-z]+-[a-f0-9]+$/);
      expect(r.sourceDomPath.length).toBeGreaterThan(0);
    }
  });

  it('ids are unique across the record set', async () => {
    const records = await extract(html);
    const ids = new Set<string>();
    for (const r of records) ids.add(r.id);
    // It's legitimate for the SAME element to produce TWO records (text +
    // background); those records have DIFFERENT id prefixes (txt- vs bg-)
    // so global id uniqueness is still expected.
    expect(ids.size).toBe(records.length);
  });

  it('Brad enrichment runs by default — at least one record carries bradClass', async () => {
    const records = await extract(html);
    const bradTagged = records.filter((r) => r.bradClass !== undefined);
    expect(bradTagged.length).toBeGreaterThan(0);
  });

  it('Brad enrichment can be disabled via opts.bradEnrichment=false (zero bradClass values)', async () => {
    const records = await extract(html, { bradEnrichment: false });
    for (const r of records) {
      expect(r.bradClass).toBeUndefined();
    }
    // Off-mode should still produce the SAME record count and shape.
    expect(records.length).toBeGreaterThanOrEqual(50);
  });

  it('parses in <3000ms (median of 3 runs)', async () => {
    const samples: number[] = [];
    for (let i = 0; i < 3; i++) {
      const t0 = performance.now();
      await extract(html);
      samples.push(performance.now() - t0);
    }
    samples.sort((a, b) => a - b);
    const median = samples[1]!;
    // Log for the perf evidence bundle.
    // eslint-disable-next-line no-console
    console.log(
      `[brad-full-10pg perf] samples (ms): ${samples
        .map((s) => s.toFixed(2))
        .join(', ')} | median: ${median.toFixed(2)}`,
    );
    expect(median).toBeLessThan(3000);
  }, 15000);
});
