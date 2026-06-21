// Unit tests for the Brad-class semantic enrichment pass.
//
// SLICE-003-001-06. Verifies the contract documented in
// src/parser/brad-enrichment.ts:
//   - enrich({enabled:true}) tags every known Brad class
//   - enrich({enabled:false}) returns the input array reference unchanged
//   - Multi-class elements resolve to highest priority
//   - Generic HTML (no Brad classes) produces no false positives
//   - Substring overlap (body-paragraph) does NOT match body-default/body-lead
//   - Direct unit tests on enrich() with synthetic ContainerRecord input
//     to lock the algorithm independently of the parser pipeline.

import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, it, expect, beforeAll } from 'vitest';

import { extract } from '../../src/parser/index';
import { enrich } from '../../src/parser/brad-enrichment';
import {
  BRAD_CLASSES,
  BRAD_CLASS_PRIORITY,
  BRAD_CLASS_SET,
} from '../../src/parser/brad-taxonomy';
import type { ContainerRecord } from '../../src/parser/types';

// ---- Fixture loading -----------------------------------------------------

let bradClassedHtml: string;
let bradClassedRecords: ContainerRecord[];

let genericHtml: string;
let genericRecords: ContainerRecord[];

beforeAll(async () => {
  bradClassedHtml = readFileSync(
    join(__dirname, '..', 'fixtures', 'brad-classed.html'),
    'utf-8',
  );
  // SLICE-003-001-07: extract() now folds enrich() into the default
  // pipeline. These tests exercise enrich() in isolation, so opt out of
  // the auto-enrichment by passing { bradEnrichment: false }. The
  // resulting records carry domClasses (slice 06 contract) but no
  // bradClass — enrich() is then applied per-test.
  bradClassedRecords = await extract(bradClassedHtml, { bradEnrichment: false });

  genericHtml = readFileSync(
    join(__dirname, '..', 'fixtures', 'generic-no-brad.html'),
    'utf-8',
  );
  genericRecords = await extract(genericHtml, { bradEnrichment: false });
});

// ---- Taxonomy sanity -----------------------------------------------------

describe('brad-taxonomy', () => {
  it('exports at least 12 Brad classes', () => {
    expect(BRAD_CLASSES.length).toBeGreaterThanOrEqual(12);
  });

  it('includes every required v1 class name', () => {
    const required = [
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
    for (const c of required) {
      expect(BRAD_CLASS_SET.has(c)).toBe(true);
    }
  });

  it('priority list contains exactly the same members as BRAD_CLASSES', () => {
    expect(new Set(BRAD_CLASS_PRIORITY)).toEqual(new Set(BRAD_CLASSES));
  });

  it('priority list orders families heading > metric > chapter > data > body > caption > footnote', () => {
    const idx = (c: string) => BRAD_CLASS_PRIORITY.indexOf(c as never);
    expect(idx('heading-display')).toBeLessThan(idx('metric-grid'));
    expect(idx('metric-card')).toBeLessThan(idx('chapter-divider'));
    expect(idx('chapter-divider')).toBeLessThan(idx('data-table'));
    expect(idx('data-table')).toBeLessThan(idx('body-default'));
    expect(idx('body-default')).toBeLessThan(idx('caption'));
    expect(idx('caption')).toBeLessThan(idx('footnote'));
    // Within-family specificity: -display before -subhead, -lead before -default.
    expect(idx('heading-display')).toBeLessThan(idx('heading-subhead'));
    expect(idx('body-lead')).toBeLessThan(idx('body-default'));
    expect(idx('metric-grid')).toBeLessThan(idx('metric-card'));
  });
});

// ---- enrich() — Brad-classed fixture (on-mode) ---------------------------

describe('enrich({enabled:true}) — brad-classed.html', () => {
  it('returns a new array (not the input reference) when enabled', () => {
    const result = enrich(bradClassedRecords, { enabled: true });
    expect(result).not.toBe(bradClassedRecords);
    expect(result.length).toBe(bradClassedRecords.length);
  });

  it('tags at least 8 distinct Brad classes across the fixture (AC #7)', () => {
    const result = enrich(bradClassedRecords, { enabled: true });
    const tagged = new Set<string>();
    for (const r of result) {
      if (r.bradClass) tagged.add(r.bradClass);
    }
    expect(tagged.size).toBeGreaterThanOrEqual(8);
  });

  it('covers every key Brad family in the priority table', () => {
    const result = enrich(bradClassedRecords, { enabled: true });
    const tagged = new Set<string>();
    for (const r of result) {
      if (r.bradClass) tagged.add(r.bradClass);
    }
    // At minimum one of each family must appear.
    expect(tagged.has('heading-display')).toBe(true);
    expect(tagged.has('metric-grid') || tagged.has('metric-card')).toBe(true);
    expect(tagged.has('chapter-divider')).toBe(true);
    expect(tagged.has('data-table')).toBe(true);
    expect(
      tagged.has('body-lead') || tagged.has('body-default'),
    ).toBe(true);
    expect(tagged.has('caption')).toBe(true);
    expect(tagged.has('footnote')).toBe(true);
  });

  it('does NOT mutate the input records (originals stay untagged)', () => {
    const beforeBrad = bradClassedRecords.map((r) => r.bradClass);
    enrich(bradClassedRecords, { enabled: true });
    const afterBrad = bradClassedRecords.map((r) => r.bradClass);
    expect(afterBrad).toEqual(beforeBrad);
  });

  it('multi-class element (heading-subhead + body-lead) resolves to heading-subhead', () => {
    const result = enrich(bradClassedRecords, { enabled: true });
    // The fixture's <h3 class="heading-subhead body-lead"> emits exactly
    // one text record. Find any record bearing both classes in its
    // domClasses snapshot and verify the priority pick.
    const multi = result.filter(
      (r) =>
        (r.domClasses?.includes('heading-subhead') ?? false) &&
        (r.domClasses?.includes('body-lead') ?? false),
    );
    expect(multi.length).toBeGreaterThanOrEqual(1);
    for (const r of multi) {
      expect(r.bradClass).toBe('heading-subhead');
    }
  });

  it('false-positive guard: body-paragraph does NOT match body-default or body-lead (AC #10)', () => {
    const result = enrich(bradClassedRecords, { enabled: true });
    const paragraphRecords = result.filter(
      (r) =>
        (r.domClasses?.includes('body-paragraph') ?? false) &&
        !(r.domClasses?.includes('body-default') ?? false) &&
        !(r.domClasses?.includes('body-lead') ?? false),
    );
    // The fixture has one such <p class="body-paragraph"> — it MUST
    // exist (otherwise the fixture is wrong) and its bradClass must be
    // undefined.
    expect(paragraphRecords.length).toBeGreaterThanOrEqual(1);
    for (const r of paragraphRecords) {
      expect(r.bradClass).toBeUndefined();
    }
  });

  it('record with no Brad classes (only "narrow custom-thing") has bradClass undefined', () => {
    const result = enrich(bradClassedRecords, { enabled: true });
    const target = result.find(
      (r) =>
        (r.domClasses?.includes('narrow') ?? false) &&
        (r.domClasses?.includes('custom-thing') ?? false),
    );
    expect(target).toBeDefined();
    expect(target!.bradClass).toBeUndefined();
  });
});

// ---- enrich() — off-mode (referential equality) -------------------------

describe('enrich({enabled:false})', () => {
  it('returns the input array reference unchanged (===)', () => {
    const result = enrich(bradClassedRecords, { enabled: false });
    expect(result).toBe(bradClassedRecords);
  });

  it('all records carry bradClass undefined when enrichment is off', () => {
    const result = enrich(bradClassedRecords, { enabled: false });
    for (const r of result) {
      expect(r.bradClass).toBeUndefined();
    }
  });
});

// ---- enrich() — generic HTML (no false positives) ------------------------

describe('enrich({enabled:true}) — generic-no-brad.html', () => {
  it('produces records (parser still works on non-Brad HTML)', () => {
    expect(genericRecords.length).toBeGreaterThan(0);
  });

  it('every record has bradClass undefined (AC #9 — no false positives)', () => {
    const result = enrich(genericRecords, { enabled: true });
    for (const r of result) {
      expect(r.bradClass).toBeUndefined();
    }
  });
});

// ---- enrich() — direct unit tests on synthetic records -------------------

function syntheticRecord(domClasses: string[]): ContainerRecord {
  return {
    id: 'test-' + domClasses.join('-'),
    kind: 'text',
    sourceDomPath: 'html > body > p',
    bounds: { width: 100, height: 20 },
    computedStyle: {
      fontFamily: 'Inter',
      fontSize: 14,
      color: 'rgb(0,0,0)',
      backgroundColor: 'rgba(0,0,0,0)',
      lineHeight: 20,
      textAlign: 'left',
      fontWeight: 400,
    },
    content: { kind: 'text', text: 'hello' },
    domClasses,
  };
}

describe('enrich() — synthetic record contract checks', () => {
  it('each Brad class tags its corresponding synthetic record', () => {
    const records = BRAD_CLASSES.map((c) => syntheticRecord([c]));
    const result = enrich(records, { enabled: true });
    for (let i = 0; i < records.length; i++) {
      expect(result[i]!.bradClass).toBe(BRAD_CLASSES[i]);
    }
  });

  it('multi-class synthetic resolves to highest-priority match', () => {
    // Pair every class with the one immediately AFTER it in priority
    // order. The first-listed (higher-priority) class must win.
    for (let i = 0; i < BRAD_CLASS_PRIORITY.length - 1; i++) {
      const high = BRAD_CLASS_PRIORITY[i]!;
      const low = BRAD_CLASS_PRIORITY[i + 1]!;
      const rec = syntheticRecord([low, high]); // order-independent
      const result = enrich([rec], { enabled: true });
      expect(result[0]!.bradClass).toBe(high);
    }
  });

  it('records with empty domClasses pass through untouched', () => {
    const rec = syntheticRecord([]);
    const result = enrich([rec], { enabled: true });
    expect(result[0]).toBe(rec);
    expect(result[0]!.bradClass).toBeUndefined();
  });

  it('records with missing domClasses field pass through untouched', () => {
    const rec = syntheticRecord(['heading-display']);
    delete (rec as Partial<ContainerRecord>).domClasses;
    const result = enrich([rec], { enabled: true });
    expect(result[0]).toBe(rec);
    expect(result[0]!.bradClass).toBeUndefined();
  });

  it('substring overlap does NOT match (body-paragraph stays untagged)', () => {
    const rec = syntheticRecord(['body-paragraph', 'narrow']);
    const result = enrich([rec], { enabled: true });
    expect(result[0]!.bradClass).toBeUndefined();
  });

  it('performance: 200 records in <5ms', () => {
    const records: ContainerRecord[] = [];
    for (let i = 0; i < 200; i++) {
      records.push(syntheticRecord(['body-default']));
    }
    const start = performance.now();
    enrich(records, { enabled: true });
    const elapsed = performance.now() - start;
    expect(elapsed).toBeLessThan(5);
  });
});
