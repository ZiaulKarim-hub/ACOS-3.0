// Unit tests for the image extractor, against brad-minimal.html.
//
// SLICE-003-001-02. Verifies:
//   - Every visible <img> in the fixture produces exactly one 'image' record
//   - The record carries src + alt + bounds + computed-style snapshot
//   - Hidden <img> would NOT be emitted (negative case via inline fixture)

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

describe('image extractor — brad-minimal.html', () => {
  it('emits exactly one image record (the single visible <img>)', async () => {
    const imageRecords = records.filter((r) => r.kind === 'image');
    expect(imageRecords).toHaveLength(1);
  });

  it('captures src + alt verbatim from the <img> element', async () => {
    const img = records.find((r) => r.kind === 'image');
    expect(img).toBeDefined();
    if (!img || img.content.kind !== 'image') throw new Error('missing image');
    expect(img.content.src.startsWith('data:image/gif;base64,')).toBe(true);
    expect(img.content.alt).toBe('visible-pixel');
  });

  it('captures a CSS-selector-like sourceDomPath ending in img', async () => {
    const img = records.find((r) => r.kind === 'image');
    expect(img?.sourceDomPath).toMatch(/img/);
    expect(img?.sourceDomPath.startsWith('html')).toBe(true);
  });

  it('captures bounds (width/height) as numbers', async () => {
    const img = records.find((r) => r.kind === 'image');
    expect(img).toBeDefined();
    expect(typeof img!.bounds.width).toBe('number');
    expect(typeof img!.bounds.height).toBe('number');
    // The fixture declares width="1" height="1"; bounds should be ≥ 0.
    expect(img!.bounds.width).toBeGreaterThanOrEqual(0);
    expect(img!.bounds.height).toBeGreaterThanOrEqual(0);
  });

  it('attaches a ComputedStyle snapshot to the image record', async () => {
    const img = records.find((r) => r.kind === 'image');
    expect(img).toBeDefined();
    expect(typeof img!.computedStyle.fontFamily).toBe('string');
    expect(typeof img!.computedStyle.fontSize).toBe('number');
    expect(typeof img!.computedStyle.fontWeight).toBe('number');
  });

  it('does NOT emit hidden <img> elements', async () => {
    const hidden = `
      <html><body>
        <img src="data:image/gif;base64,R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw==" alt="hidden-display" style="display:none" />
        <img src="data:image/gif;base64,R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw==" alt="hidden-aria" aria-hidden="true" />
      </body></html>
    `;
    const result = await extract(hidden);
    const imageRecords = result.filter((r) => r.kind === 'image');
    expect(imageRecords).toHaveLength(0);
  });

  it('image record id is stable across re-extracts', async () => {
    const second = await extract(html);
    const firstId = records.find((r) => r.kind === 'image')?.id;
    const secondId = second.find((r) => r.kind === 'image')?.id;
    expect(firstId).toBeDefined();
    expect(secondId).toBe(firstId);
  });
});
