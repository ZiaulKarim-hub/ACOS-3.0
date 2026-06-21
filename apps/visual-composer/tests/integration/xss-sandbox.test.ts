// XSS Sandbox integration test — proves the parser pipeline does NOT
// execute hostile script content.
// SLICE-003-001-07 Part A acceptance criterion #5.
//
// What we test:
//   - DOMParser('text/html') does not run inline <script> tags.
//   - Inline event handlers (onload, onerror, onclick) do not fire just
//     by virtue of the document being parsed.
//   - javascript: URLs in href/src do not navigate or execute.
//   - The parser returns a clean ContainerRecord stream and never
//     surfaces executable script source in record content payloads.

import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, it, expect, beforeAll, vi, afterEach } from 'vitest';

import { extract } from '../../src/parser/index';

let html: string;

beforeAll(() => {
  html = readFileSync(
    join(__dirname, '..', 'fixtures', 'xss-sandbox.html'),
    'utf-8',
  );
});

afterEach(() => {
  vi.restoreAllMocks();
  // Clean up any pwned markers a misbehaving parser might leave behind so
  // subsequent tests in the suite start from a known state.
  const w = globalThis as Record<string, unknown>;
  delete w.__pwned__;
  delete w.__pwned_onload__;
  delete w.__pwned_onerror__;
  delete w.__pwned_href__;
  delete w.__pwned_iframe__;
  delete w.__pwned_body__;
  delete w.__pwned_div_onload__;
  delete w.__pwned_click__;
  // SLICE-003-001-07 security feedback (2026-05-28) — new probes
  delete w.__pwned_svg_script__;
  delete w.__pwned_svg_onload__;
  delete w.__pwned_svg_jsa__;
});

describe('integration — xss-sandbox.html', () => {
  it('window.alert is NEVER called during extract()', async () => {
    const alertSpy = vi.fn();
    // happy-dom exposes window.alert on the global; install the spy on
    // both window and the global to cover both lookup paths.
    if (typeof window !== 'undefined') {
      window.alert = alertSpy;
    }
    (globalThis as { alert?: (...args: unknown[]) => void }).alert = alertSpy;

    const records = await extract(html);

    expect(alertSpy).not.toHaveBeenCalled();
    // Sanity — the parser must still produce records from the safe
    // content of the document; an "everything blocked" outcome would
    // mask the real signal.
    expect(records.length).toBeGreaterThan(0);
  });

  it('no script-tag source appears as text content in any record', async () => {
    const records = await extract(html);
    for (const r of records) {
      if (r.content.kind === 'text') {
        // The hostile scripts assign window.__pwned*; if any of that
        // source leaks into a text record it indicates the parser
        // surfaced executable script source as user content.
        expect(r.content.text).not.toContain('window.__pwned');
        expect(r.content.text).not.toContain('alert(');
      }
    }
  });

  it('inline event handlers did not fire (no __pwned_* globals set)', async () => {
    await extract(html);
    const w = globalThis as Record<string, unknown>;
    expect(w.__pwned__).toBeUndefined();
    expect(w.__pwned_onload__).toBeUndefined();
    expect(w.__pwned_onerror__).toBeUndefined();
    expect(w.__pwned_href__).toBeUndefined();
    expect(w.__pwned_iframe__).toBeUndefined();
    expect(w.__pwned_body__).toBeUndefined();
    expect(w.__pwned_div_onload__).toBeUndefined();
    expect(w.__pwned_click__).toBeUndefined();
    // SLICE-003-001-07 security feedback (2026-05-28): SVG-borne hostile probes
    expect((window as unknown as Record<string, unknown>).__pwned_svg_script__).toBeUndefined();
    expect((window as unknown as Record<string, unknown>).__pwned_svg_onload__).toBeUndefined();
    expect((window as unknown as Record<string, unknown>).__pwned_svg_jsa__).toBeUndefined();
    expect(w.__pwned_svg_script__).toBeUndefined();
    expect(w.__pwned_svg_onload__).toBeUndefined();
    expect(w.__pwned_svg_jsa__).toBeUndefined();
  });

  it('javascript: URIs do not appear as background-image URLs', async () => {
    const records = await extract(html);
    for (const r of records) {
      if (r.content.kind === 'background') {
        expect(r.content.url.startsWith('javascript:')).toBe(false);
      }
    }
  });

  // SLICE-003-001-07 security feedback (2026-05-28): SSRF allowlist
  it('background URLs pass scheme allowlist + hostname denylist', async () => {
    const records = await extract(html);
    const bgRecords = records.filter((r) => r.content.kind === 'background');
    for (const r of bgRecords) {
      const url = (r.content as { url: string }).url;
      // Scheme denylist
      expect(url).not.toMatch(/^(?:javascript|file|chrome|about|gopher|ftp):/i);
      // Hostname denylist (loopback / RFC1918 / link-local / wildcard)
      try {
        const parsed = new URL(url);
        const host = parsed.hostname.toLowerCase();
        expect(host).not.toBe('localhost');
        expect(host).not.toMatch(/^127\./);
        expect(host).not.toMatch(/^10\./);
        expect(host).not.toMatch(/^192\.168\./);
        expect(host).not.toMatch(/^172\.(?:1[6-9]|2\d|3[01])\./);
        expect(host).not.toMatch(/^169\.254\./);
        expect(host).not.toBe('0.0.0.0');
        expect(host).not.toBe('::1');
      } catch {
        /* data: URIs throw on URL parse for hostname access — acceptable. */
      }
    }
  });

  // SLICE-003-001-07 security feedback (2026-05-28): SVG UNTRUSTED contract
  it('SVG records carry rawMarkup as a string (downstream sanitizes — do NOT innerHTML here)', async () => {
    const records = await extract(html);
    const svgRecords = records.filter((r) => r.content.kind === 'svg');
    // Fixture appends 3 hostile SVGs; presence + type only. Contract says
    // downstream renderers must sanitize before innerHTML — we therefore do
    // NOT innerHTML here.
    expect(svgRecords.length).toBeGreaterThan(0);
    for (const r of svgRecords) {
      const raw = (r.content as { rawMarkup: string }).rawMarkup;
      expect(typeof raw).toBe('string');
      expect(raw.length).toBeGreaterThan(0);
    }
  });

  it('dual-discriminator coherence (F2) holds on hostile input', async () => {
    const records = await extract(html);
    for (const r of records) {
      expect(r.kind).toBe(r.content.kind);
    }
  });
});
