// Integration tests for the background extractor's real-browser Image()
// code path. SLICE-003-001-07 plan_addenda BG4 + BG5 (+ BG2 dedup verify).
//
// happy-dom's built-in Image is inert: assigning .src does not trigger
// onload/onerror and naturalWidth stays at 0. To exercise the production
// `new Image()` path against a non-data URL we install a controllable
// Image stub. The parser's pickImageConstructor() prefers
// doc.defaultView.Image — and DOMParser('text/html') in happy-dom returns
// a Document whose defaultView is a FRESH Window per call, NOT the
// global window. We therefore wrap DOMParser.prototype.parseFromString
// to patch defaultView.Image on every newly-created document.

import { describe, it, expect, vi, afterEach, beforeEach } from 'vitest';

import { extract } from '../../src/parser/index';

let restoreParser: (() => void) | null = null;

function withImageCtor(ctor: new () => unknown): void {
  const originalParse = DOMParser.prototype.parseFromString;
  DOMParser.prototype.parseFromString = function patched(
    this: DOMParser,
    str: string,
    type: DOMParserSupportedType,
  ): Document {
    const doc = originalParse.call(this, str, type);
    // Override Image on the parsed document's window so the extractor's
    // pickImageConstructor picks up the stub instead of happy-dom's
    // inert built-in.
    if (doc.defaultView) {
      (doc.defaultView as unknown as { Image: unknown }).Image = ctor;
    }
    return doc;
  } as typeof DOMParser.prototype.parseFromString;
  restoreParser = (): void => {
    DOMParser.prototype.parseFromString = originalParse;
  };
}

beforeEach(() => {
  restoreParser = null;
});

afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
  if (restoreParser) {
    restoreParser();
    restoreParser = null;
  }
});

// ---- BG4 — Image() general-path simulation -------------------------------

interface StubImage {
  src: string;
  naturalWidth: number;
  naturalHeight: number;
  onload: (() => void) | null;
  onerror: (() => void) | null;
}

function installSuccessImageStub(
  naturalWidth: number,
  naturalHeight: number,
): StubImage[] {
  const instances: StubImage[] = [];
  class FakeImage {
    public _src = '';
    public naturalWidth = 0;
    public naturalHeight = 0;
    public onload: (() => void) | null = null;
    public onerror: (() => void) | null = null;
    constructor() {
      instances.push(this as unknown as StubImage);
    }
    get src(): string {
      return this._src;
    }
    set src(v: string) {
      this._src = v;
      if (v === '') return;
      queueMicrotask(() => {
        this.naturalWidth = naturalWidth;
        this.naturalHeight = naturalHeight;
        this.onload?.();
      });
    }
  }
  withImageCtor(FakeImage as unknown as new () => unknown);
  return instances;
}

describe('BG4 — Image() general path (real-browser simulation)', () => {
  it('extract() decodes a non-data background URL via the new Image() path', async () => {
    const instances = installSuccessImageStub(640, 480);

    const html = `
      <!DOCTYPE html>
      <html><body>
        <div style="background-image: url('https://example.com/hero.png'); background-size: cover;"
             id="hero-with-remote-bg">hero</div>
      </body></html>
    `;
    const records = await extract(html);
    const bg = records.find((r) => r.content.kind === 'background');
    expect(bg).toBeDefined();
    if (!bg || bg.content.kind !== 'background') throw new Error('unreachable');
    expect(bg.content.url).toBe('https://example.com/hero.png');
    expect(bg.content.naturalWidth).toBe(640);
    expect(bg.content.naturalHeight).toBe(480);
    const target = instances.find(
      (i) => i.src === 'https://example.com/hero.png',
    );
    expect(target).toBeDefined();
    expect(target!.onload).toBeNull();
    expect(target!.onerror).toBeNull();
  });
});

// ---- BG5 — 5-second timeout settles to null (+ BG1 cancellation) ---------

describe('BG5 — 5s timeout branch resolves to null (with BG1 src-cancel)', () => {
  it('extract() returns no background record when Image() never fires', async () => {
    const srcAssignments: string[] = [];
    class InertImage {
      public _src = '';
      public naturalWidth = 0;
      public naturalHeight = 0;
      public onload: (() => void) | null = null;
      public onerror: (() => void) | null = null;
      get src(): string {
        return this._src;
      }
      set src(v: string) {
        this._src = v;
        srcAssignments.push(v);
      }
    }
    withImageCtor(InertImage as unknown as new () => unknown);

    vi.useFakeTimers();

    const html = `
      <!DOCTYPE html>
      <html><body>
        <div style="background-image: url('https://example.com/never-loads.png'); background-size: cover;">x</div>
      </body></html>
    `;
    const promise = extract(html);
    // Flush the synchronous parser + walker work so the extractor reaches
    // the new Image() construction and sets src before we advance time.
    await Promise.resolve();
    await Promise.resolve();
    await vi.advanceTimersByTimeAsync(5001);
    const records = await promise;

    const bg = records.find((r) => r.content.kind === 'background');
    expect(bg).toBeUndefined();

    const urlIdx = srcAssignments.indexOf(
      'https://example.com/never-loads.png',
    );
    const cancelIdx = srcAssignments.lastIndexOf('');
    expect(urlIdx).toBeGreaterThanOrEqual(0);
    expect(cancelIdx).toBeGreaterThan(urlIdx);
  });
});

// ---- BG2 — URL-level dedup memoization -----------------------------------

describe('BG2 — URL-level dedup within a single extract() call', () => {
  it('repeated background URL only triggers ONE Image() instance', async () => {
    const instances = installSuccessImageStub(200, 100);

    const html = `
      <!DOCTYPE html>
      <html><body>
        <div style="background-image: url('https://example.com/hero.png'); background-size: cover;">a</div>
        <div style="background-image: url('https://example.com/hero.png'); background-size: cover;">b</div>
        <div style="background-image: url('https://example.com/hero.png'); background-size: cover;">c</div>
      </body></html>
    `;
    const records = await extract(html);
    const bgs = records.filter((r) => r.content.kind === 'background');
    expect(bgs.length).toBe(3);
    const hits = instances.filter(
      (i) => i.src === 'https://example.com/hero.png',
    );
    expect(hits.length).toBe(1);
  });
});
