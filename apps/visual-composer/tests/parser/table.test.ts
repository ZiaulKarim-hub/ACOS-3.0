// Unit tests for the table extractor + walker dispatch, against
// brad-table.html. SLICE-003-001-04.
//
// Coverage:
//   - Two tables in the fixture map to exactly two 'table' ContainerRecords
//   - Simple 3x4 table: rowCount=3, columnCount=4, all rows section='tbody'
//     (HTML parser injects implicit <tbody>)
//   - Cap-stack table: explicit thead/tbody/tfoot preserved per row
//   - Footer colspan=3 contributes to columnCount=4
//   - Cell textContent matches source values (financial cell-value fidelity)
//   - colSpan/rowSpan default to 1 when attribute absent
//   - Edge case: empty table -> rowCount=0, columnCount=0, rows=[], columns=[]
//   - Walker does NOT descend into table internals: no text records under
//     a <table> ancestor (text.ts SKIP_TEXT_INSIDE handles this; the
//     walker dispatch is the structural enforcement)
//   - Perf gate (P1 from slice 02 perf review): 50-row x 10-col table
//     parses in <200ms as median of 5 runs with one warm-up

import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, it, expect, beforeAll } from 'vitest';

import { extract } from '../../src/parser/index';
import { extractTable } from '../../src/parser/extractors/table';
import type { ContainerRecord } from '../../src/parser/types';

let html: string;
let records: ContainerRecord[];

beforeAll(async () => {
  html = readFileSync(
    join(__dirname, '..', 'fixtures', 'brad-table.html'),
    'utf-8',
  );
  records = await extract(html);
});

describe('table extractor — brad-table.html', () => {
  it('emits exactly one table record per <table> in the source (N=2)', async () => {
    const tableRecords = records.filter((r) => r.kind === 'table');
    const sourceTableCount = (html.match(/<table\b/gi) ?? []).length;
    expect(sourceTableCount).toBe(2);
    expect(tableRecords.length).toBe(2);
  });

  it('each table record has kind="table" on BOTH record and content', async () => {
    const tableRecords = records.filter((r) => r.kind === 'table');
    for (const r of tableRecords) {
      expect(r.kind).toBe('table');
      expect(r.content.kind).toBe('table');
    }
  });

  it('simple sources-uses table: 3 rows x 4 cols, all tbody (implicit)', async () => {
    const tableRecords = records.filter((r) => r.kind === 'table');
    // First table in document order is the simple one.
    const simple = tableRecords[0];
    expect(simple).toBeDefined();
    if (!simple || simple.content.kind !== 'table') throw new Error('unreachable');
    expect(simple.content.rowCount).toBe(3);
    expect(simple.content.columnCount).toBe(4);
    for (const row of simple.content.rows) {
      expect(row.section).toBe('tbody');
    }
    // Header row's first cell is "Source", body row 1 first cell "Senior Loan".
    expect(simple.content.rows[0]!.cells[0]!.textContent).toBe('Source');
    expect(simple.content.rows[1]!.cells[0]!.textContent).toBe('Senior Loan');
    expect(simple.content.rows[1]!.cells[1]!.textContent).toBe('$10,000,000');
    expect(simple.content.rows[2]!.cells[0]!.textContent).toBe('Sponsor Equity');
  });

  it('cap-stack table: thead/tbody/tfoot sections preserved per row', async () => {
    const tableRecords = records.filter((r) => r.kind === 'table');
    const cap = tableRecords[1];
    expect(cap).toBeDefined();
    if (!cap || cap.content.kind !== 'table') throw new Error('unreachable');
    // 1 thead row + 3 tbody rows + 1 tfoot row = 5
    expect(cap.content.rowCount).toBe(5);
    const sections = cap.content.rows.map((r) => r.section);
    expect(sections).toEqual(['thead', 'tbody', 'tbody', 'tbody', 'tfoot']);
  });

  it('cap-stack columnCount accounts for footer colspan=3 (effective=4)', async () => {
    const tableRecords = records.filter((r) => r.kind === 'table');
    const cap = tableRecords[1];
    if (!cap || cap.content.kind !== 'table') throw new Error('unreachable');
    expect(cap.content.columnCount).toBe(4);
    // The footer row has 2 literal cells but effective 4 columns due to colspan=3.
    const footer = cap.content.rows[cap.content.rows.length - 1]!;
    expect(footer.cells.length).toBe(2);
    expect(footer.cells[0]!.colSpan).toBe(3);
    expect(footer.cells[0]!.textContent).toBe('Total Capitalization');
    expect(footer.cells[1]!.colSpan).toBe(1);
    expect(footer.cells[1]!.textContent).toBe('$13,500,000');
  });

  it('cells without colspan/rowspan default to 1/1', async () => {
    const tableRecords = records.filter((r) => r.kind === 'table');
    const cap = tableRecords[1];
    if (!cap || cap.content.kind !== 'table') throw new Error('unreachable');
    const headerRow = cap.content.rows[0]!;
    for (const cell of headerRow.cells) {
      expect(cell.colSpan).toBe(1);
      expect(cell.rowSpan).toBe(1);
    }
  });

  it('each cell carries a ComputedStyle snapshot', async () => {
    const tableRecords = records.filter((r) => r.kind === 'table');
    for (const r of tableRecords) {
      if (r.content.kind !== 'table') continue;
      for (const row of r.content.rows) {
        for (const cell of row.cells) {
          expect(typeof cell.computedStyle.fontFamily).toBe('string');
          expect(typeof cell.computedStyle.fontSize).toBe('number');
          expect(typeof cell.computedStyle.color).toBe('string');
          expect(typeof cell.computedStyle.backgroundColor).toBe('string');
          expect(typeof cell.computedStyle.textAlign).toBe('string');
        }
      }
    }
  });

  it('columns array length matches columnCount', async () => {
    const tableRecords = records.filter((r) => r.kind === 'table');
    for (const r of tableRecords) {
      if (r.content.kind !== 'table') continue;
      expect(r.content.columns.length).toBe(r.content.columnCount);
      for (const col of r.content.columns) {
        expect(typeof col.naturalWidth).toBe('number');
      }
    }
  });

  it('walker does NOT descend into table internals (no records under a <table> ancestor)', async () => {
    for (const r of records) {
      const segs = r.sourceDomPath.split(' > ');
      const tableIdx = segs.findIndex((s) => s === 'table' || s.startsWith('table:'));
      if (tableIdx === -1) continue;
      // The <table> itself is allowed at the end of the path; deeper
      // descendants would indicate a leak.
      expect(tableIdx).toBe(segs.length - 1);
    }
  });

  it('text extractor unaffected: h1 and intro paragraph still emit', async () => {
    const textRecords = records.filter((r) => r.kind === 'text');
    const allText = textRecords
      .map((r) => (r.content.kind === 'text' ? r.content.text : ''))
      .join('\n');
    expect(allText).toContain('OKOA Brad — Table Fixture');
    expect(allText).toContain('finance-style tables');
    // The two <h2> section headings are also visible.
    expect(allText).toContain('Sources & Uses (Simple)');
    expect(allText).toContain('Cap Stack Waterfall');
  });

  it('table record id is stable across re-extracts', async () => {
    const second = await extract(html);
    const firstIds = records.filter((r) => r.kind === 'table').map((r) => r.id);
    const secondIds = second.filter((r) => r.kind === 'table').map((r) => r.id);
    expect(secondIds).toEqual(firstIds);
  });

  it('sourceDomPaths are deterministic across re-extracts', async () => {
    const second = await extract(html);
    const firstPaths = records.map((r) => r.sourceDomPath);
    const secondPaths = second.map((r) => r.sourceDomPath);
    expect(secondPaths).toEqual(firstPaths);
  });
});

describe('table extractor — extractTable() direct unit tests', () => {
  it('empty <table> -> rowCount=0, columnCount=0, rows=[], columns=[]', async () => {
    const doc = new DOMParser().parseFromString(
      `<!doctype html><body><table></table></body>`,
      'text/html',
    );
    const el = doc.querySelector('table') as HTMLTableElement;
    const rec = extractTable(el);
    expect(rec.content.kind).toBe('table');
    if (rec.content.kind !== 'table') return;
    expect(rec.content.rowCount).toBe(0);
    expect(rec.content.columnCount).toBe(0);
    expect(rec.content.rows).toEqual([]);
    expect(rec.content.columns).toEqual([]);
  });

  it('table with only <thead>: section labeled thead', async () => {
    const doc = new DOMParser().parseFromString(
      `<!doctype html><body><table><thead><tr><th>A</th><th>B</th></tr></thead></table></body>`,
      'text/html',
    );
    const el = doc.querySelector('table') as HTMLTableElement;
    const rec = extractTable(el);
    if (rec.content.kind !== 'table') throw new Error('unreachable');
    expect(rec.content.rows.length).toBe(1);
    expect(rec.content.rows[0]!.section).toBe('thead');
    expect(rec.content.columnCount).toBe(2);
  });

  it('rowSpan attribute is captured on cells', async () => {
    const doc = new DOMParser().parseFromString(
      `<!doctype html><body><table><tr><td rowspan="2">X</td><td>Y</td></tr><tr><td>Z</td></tr></table></body>`,
      'text/html',
    );
    const el = doc.querySelector('table') as HTMLTableElement;
    const rec = extractTable(el);
    if (rec.content.kind !== 'table') throw new Error('unreachable');
    expect(rec.content.rows[0]!.cells[0]!.rowSpan).toBe(2);
    expect(rec.content.rows[0]!.cells[1]!.rowSpan).toBe(1);
  });

  it('cell textContent is trimmed (leading/trailing whitespace stripped)', async () => {
    const doc = new DOMParser().parseFromString(
      `<!doctype html><body><table><tr><td>   spaced value   </td></tr></table></body>`,
      'text/html',
    );
    const el = doc.querySelector('table') as HTMLTableElement;
    const rec = extractTable(el);
    if (rec.content.kind !== 'table') throw new Error('unreachable');
    expect(rec.content.rows[0]!.cells[0]!.textContent).toBe('spaced value');
  });

  it('<caption> and <colgroup> are ignored (not classified as rows)', async () => {
    const doc = new DOMParser().parseFromString(
      `<!doctype html><body><table>
        <caption>The Caption</caption>
        <colgroup><col /><col /></colgroup>
        <tr><td>only-row</td></tr>
      </table></body>`,
      'text/html',
    );
    const el = doc.querySelector('table') as HTMLTableElement;
    const rec = extractTable(el);
    if (rec.content.kind !== 'table') throw new Error('unreachable');
    expect(rec.content.rowCount).toBe(1);
    expect(rec.content.rows[0]!.cells[0]!.textContent).toBe('only-row');
  });
});

describe('table extractor — walker performance gate (P1 addendum)', () => {
  // The perf gate: 50-row x 10-col table parses in <200ms median of
  // 5 runs with one warm-up. Without the walker refactor in this
  // slice, wide same-tag sibling fanout (500 <td>s under 50 <tr>s
  // under <tbody>) trips the O(d^2/k^2) trap empirically benchmarked
  // by slice 02's perf reviewer at >500ms.
  it('50x10 table parses in <200ms (median of 5 with warm-up)', async () => {
    const cells = (cols: number, rowIdx: number): string => {
      let s = '';
      for (let c = 0; c < cols; c++) {
        s += '<td>r' + rowIdx + 'c' + c + '</td>';
      }
      return s;
    };
    const rows = 50;
    const cols = 10;
    let body = '';
    for (let r = 0; r < rows; r++) body += '<tr>' + cells(cols, r) + '</tr>';
    const big = '<!doctype html><body><table id="big"><tbody>' + body + '</tbody></table></body>';

    // Warm-up: prime JIT + module caches.
    await extract(big);

    const samples: number[] = [];
    for (let i = 0; i < 5; i++) {
      const start = performance.now();
      await extract(big);
      samples.push(performance.now() - start);
    }
    samples.sort((a, b) => a - b);
    const median = samples[2]!;
    // eslint-disable-next-line no-console
    console.log(
      '[table-perf] 50x10 samples (ms):',
      samples.map((s) => s.toFixed(2)).join(', '),
      '| median:',
      median.toFixed(2),
    );
    expect(median).toBeLessThan(200);
  });

  it('verifies the 50x10 table extracts as one record with 50 rows and 10 cols', async () => {
    let body = '';
    for (let r = 0; r < 50; r++) {
      let cellsHtml = '';
      for (let c = 0; c < 10; c++) cellsHtml += '<td>r' + r + 'c' + c + '</td>';
      body += '<tr>' + cellsHtml + '</tr>';
    }
    const big = '<!doctype html><body><table><tbody>' + body + '</tbody></table></body>';
    const result = await extract(big);
    const tables = result.filter((r) => r.kind === 'table');
    expect(tables.length).toBe(1);
    if (tables[0]!.content.kind !== 'table') throw new Error('unreachable');
    expect(tables[0]!.content.rowCount).toBe(50);
    expect(tables[0]!.content.columnCount).toBe(10);
  });
});
