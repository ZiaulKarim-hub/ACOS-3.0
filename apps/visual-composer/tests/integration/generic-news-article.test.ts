// Integration test: parse a generic (non-Brad) HTML5 news article.
// SLICE-003-001-07 Part A acceptance criterion #6 — verifies that
// opts.bradEnrichment=false produces a clean record stream with NO
// bradClass values, suitable for non-OKOA inputs.

import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, it, expect, beforeAll } from 'vitest';

import { extract } from '../../src/parser/index';

let html: string;

beforeAll(() => {
  html = readFileSync(
    join(__dirname, '..', 'fixtures', 'generic-news-article.html'),
    'utf-8',
  );
});

describe('integration — generic-news-article.html (bradEnrichment off)', () => {
  it('parses successfully and returns a non-empty record set', async () => {
    const records = await extract(html, { bradEnrichment: false });
    expect(records.length).toBeGreaterThan(0);
  });

  it('produces zero bradClass values when enrichment is off', async () => {
    const records = await extract(html, { bradEnrichment: false });
    for (const r of records) {
      expect(r.bradClass).toBeUndefined();
    }
  });

  it('still extracts text and image kinds from the article', async () => {
    const records = await extract(html, { bradEnrichment: false });
    const kinds = new Set(records.map((r) => r.kind));
    expect(kinds.has('text')).toBe(true);
    expect(kinds.has('image')).toBe(true);
  });

  it('dual-discriminator coherence (F2) holds in fallback mode too', async () => {
    const records = await extract(html, { bradEnrichment: false });
    for (const r of records) {
      expect(r.kind).toBe(r.content.kind);
    }
  });

  it('fixture contains ZERO Brad class names anywhere in the source', () => {
    // Belt-and-suspenders: the fixture itself must not accidentally smuggle
    // a Brad class. If a future edit adds one, this test catches it before
    // the bradEnrichment=false contract test downstream.
    const bradClasses = [
      'heading-display',
      'heading-subhead',
      'body-lead',
      'body-default',
      'metric-grid',
      'metric-card',
      'chapter-divider',
      'pull-quote',
      'caption',
      'footnote',
      'data-table',
      'photo-break',
    ];
    for (const c of bradClasses) {
      expect(html).not.toContain(`"${c}"`);
      expect(html).not.toContain(`'${c}'`);
      // Also catch unquoted class attributes that begin with the class name.
      expect(html).not.toMatch(new RegExp(`class\\s*=\\s*"[^"]*\\b${c}\\b`));
    }
  });
});
