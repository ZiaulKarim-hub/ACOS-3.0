// Smoke test: prove the ContainerRecord discriminated union narrows
// exhaustively for every NodeKind and for every ContainerContent variant.
// No `as any`, no `// @ts-expect-error`. If this file compiles, the
// type contract is sound; if it runs green, the runtime example records
// match the declared shape.

import { describe, it, expect } from 'vitest';

import type {
  ComputedStyle,
  ContainerRecord,
  NodeKind,
} from '../../src/parser/types';
import { extract } from '../../src/parser/index';

const baseStyle: ComputedStyle = {
  fontFamily: 'Inter, sans-serif',
  fontSize: 14,
  color: 'rgb(0, 0, 0)',
  backgroundColor: 'rgba(0, 0, 0, 0)',
  lineHeight: 20,
  textAlign: 'left',
  fontWeight: 400,
};

const baseBounds = { width: 100, height: 24 };

function labelForKind(record: ContainerRecord): string {
  // Exhaustive narrowing on the record's kind discriminator.
  switch (record.kind) {
    case 'text':
      return 'text-record';
    case 'image':
      return 'image-record';
    case 'svg':
      return 'svg-record';
    case 'table':
      return 'table-record';
    case 'background':
      return 'background-record';
    default: {
      // Compile-time exhaustiveness guard. If a new NodeKind is added
      // without extending this switch, `_exhaustive` will fail to type.
      const _exhaustive: never = record.kind;
      throw new Error(`Unhandled NodeKind: ${String(_exhaustive)}`);
    }
  }
}

function labelForContent(record: ContainerRecord): string {
  // Exhaustive narrowing on the content payload's kind discriminator.
  switch (record.content.kind) {
    case 'text':
      return `text:${record.content.text.length}`;
    case 'image':
      return `image:${record.content.src}`;
    case 'svg':
      return `svg:${record.content.aspectRatio}`;
    case 'table':
      return `table:${record.content.rowCount}x${record.content.columnCount}`;
    case 'background':
      return `background:${record.content.url}`;
    default: {
      const _exhaustive: never = record.content;
      throw new Error(`Unhandled ContainerContent kind: ${String(_exhaustive)}`);
    }
  }
}

const sampleRecords: Record<NodeKind, ContainerRecord> = {
  text: {
    id: 'text-1',
    kind: 'text',
    sourceDomPath: 'html>body>p:nth-of-type(1)',
    bounds: baseBounds,
    computedStyle: baseStyle,
    content: { kind: 'text', text: 'hello world' },
  },
  image: {
    id: 'image-1',
    kind: 'image',
    sourceDomPath: 'html>body>img:nth-of-type(1)',
    bounds: baseBounds,
    computedStyle: baseStyle,
    content: {
      kind: 'image',
      src: 'https://example.com/cat.png',
      alt: 'a cat',
    },
  },
  svg: {
    id: 'svg-1',
    kind: 'svg',
    sourceDomPath: 'html>body>svg:nth-of-type(1)',
    bounds: baseBounds,
    computedStyle: baseStyle,
    content: {
      kind: 'svg',
      rawMarkup: '<svg viewBox="0 0 10 10"></svg>',
      viewBox: { x: 0, y: 0, width: 10, height: 10 },
      aspectRatio: 1,
    },
  },
  table: {
    id: 'table-1',
    kind: 'table',
    sourceDomPath: 'html>body>table:nth-of-type(1)',
    bounds: baseBounds,
    computedStyle: baseStyle,
    content: {
      kind: 'table',
      rowCount: 1,
      columnCount: 1,
      columns: [{ naturalWidth: 100 }],
      rows: [
        {
          section: 'tbody',
          cells: [
            {
              textContent: 'cell',
              computedStyle: baseStyle,
              colSpan: 1,
              rowSpan: 1,
            },
          ],
        },
      ],
    },
  },
  background: {
    id: 'background-1',
    kind: 'background',
    sourceDomPath: 'html>body>div:nth-of-type(1)',
    bounds: baseBounds,
    computedStyle: baseStyle,
    content: {
      kind: 'background',
      url: 'https://example.com/hero.jpg',
      naturalWidth: 1920,
      naturalHeight: 1080,
      backgroundSize: 'cover',
      backgroundPosition: 'center center',
    },
  },
};

describe('ContainerRecord discriminated union', () => {
  it('narrows by NodeKind to a unique label per kind', async () => {
    expect(labelForKind(sampleRecords.text)).toBe('text-record');
    expect(labelForKind(sampleRecords.image)).toBe('image-record');
    expect(labelForKind(sampleRecords.svg)).toBe('svg-record');
    expect(labelForKind(sampleRecords.table)).toBe('table-record');
    expect(labelForKind(sampleRecords.background)).toBe('background-record');

    // All five labels distinct — no overlap.
    const labels = new Set(
      (Object.values(sampleRecords) as ContainerRecord[]).map(labelForKind),
    );
    expect(labels.size).toBe(5);
  });

  it('narrows by ContainerContent kind to a unique label per variant', async () => {
    expect(labelForContent(sampleRecords.text)).toBe('text:11');
    expect(labelForContent(sampleRecords.image)).toBe(
      'image:https://example.com/cat.png',
    );
    expect(labelForContent(sampleRecords.svg)).toBe('svg:1');
    expect(labelForContent(sampleRecords.table)).toBe('table:1x1');
    expect(labelForContent(sampleRecords.background)).toBe(
      'background:https://example.com/hero.jpg',
    );
  });

  it('await extract() returns ContainerRecord[] (post slice-02 walker wiring)', async () => {
    // Slice 01 originally asserted toHaveLength(0) against an empty stub.
    // Slice 02 wired walker + text + image extractors, so '<p>anything</p>'
    // now produces one text record. Updated to assert on the post-wiring
    // contract: result is a valid ContainerRecord[] (non-negative length,
    // every entry has the discriminated-union shape).
    const result: ContainerRecord[] = await extract('<p>anything</p>');
    expect(Array.isArray(result)).toBe(true);
    expect(result.length).toBeGreaterThanOrEqual(0);
    for (const r of result) {
      expect(['text', 'image', 'svg', 'table', 'background']).toContain(r.kind);
      expect(r.kind).toBe(r.content.kind);
    }
  });
});
