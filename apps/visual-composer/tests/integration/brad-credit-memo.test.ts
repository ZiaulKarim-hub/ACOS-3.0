// Integration test: parse a shorter Brad-shaped credit memo document.
// SLICE-003-001-07 Part A acceptance criterion #5.
//
// This document is intentionally distinct from brad-full-10pg.html — same
// design system, different doc type — to prove extract() handles a
// different Brad-shaped layout cleanly.

import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, it, expect, beforeAll } from 'vitest';

import { extract } from '../../src/parser/index';

let html: string;

beforeAll(() => {
  html = readFileSync(
    join(__dirname, '..', 'fixtures', 'brad-credit-memo.html'),
    'utf-8',
  );
});

describe('integration — brad-credit-memo.html', () => {
  it('parses successfully and returns a non-empty record set', async () => {
    const records = await extract(html);
    expect(records.length).toBeGreaterThan(0);
  });

  it('contains text, table, and svg records at minimum', async () => {
    const records = await extract(html);
    const kinds = new Set(records.map((r) => r.kind));
    expect(kinds.has('text')).toBe(true);
    expect(kinds.has('table')).toBe(true);
    expect(kinds.has('svg')).toBe(true);
  });

  it('dual-discriminator coherence (F2)', async () => {
    const records = await extract(html);
    for (const r of records) {
      expect(r.kind).toBe(r.content.kind);
    }
  });

  it('Brad enrichment tags multiple distinct Brad families', async () => {
    const records = await extract(html);
    const bradTagged = new Set<string>();
    for (const r of records) {
      if (r.bradClass) bradTagged.add(r.bradClass);
    }
    // The credit memo carries: heading-display (h1), heading-subhead
    // (h2 x4), body-lead, body-default, chapter-divider, data-table,
    // caption, photo-break, footnote. We assert at least 5 distinct
    // Brad classes get tagged across the doc.
    expect(bradTagged.size).toBeGreaterThanOrEqual(5);
    expect(bradTagged.has('heading-display')).toBe(true);
    expect(bradTagged.has('heading-subhead')).toBe(true);
    expect(bradTagged.has('data-table')).toBe(true);
  });
});
