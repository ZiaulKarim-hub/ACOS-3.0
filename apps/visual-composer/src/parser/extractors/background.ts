// Background-image extractor — emits a 'background'-kind ContainerRecord
// for any element whose computed `background-image` resolves to a `url(...)`
// reference. Distinct from the <img> 'image' extractor: gestures over a
// background container use cover-fit + focal-point positioning (driven by
// the captured backgroundSize + backgroundPosition fields) instead of the
// aspect-locked scale used by inline images.
//
// SLICE-003-001-05.
//
// Asynchrony rationale:
//   Natural image dimensions are NOT available from `getComputedStyle()` —
//   the browser only knows them after the bitmap has been decoded. We
//   construct a transient `new Image()`, attach the URL, and await the
//   load event. Failures (404, CORS, malformed URL, timeout) resolve to
//   null with a warning; they MUST NOT throw, because a single bad
//   background image must not block the rest of the parts-bin extraction.
//
// happy-dom quirk (discovered during slice implementation):
//   happy-dom's `new Image()` constructor exists but its load/error events
//   never fire — even for `data:` URIs — and `naturalWidth/naturalHeight`
//   stay at 0 indefinitely. To make tests deterministic without spinning
//   up a real browser, we implement an in-process decoder for `data:` URI
//   PNG / GIF / JPEG headers, which reads the bitmap dimensions directly
//   from the encoded header bytes. Real browsers continue to use the
//   `new Image()` path. The decoder fallback also helps real Node-side
//   integration tests run without a network round-trip.
//
// Multi-background policy: CSS allows comma-separated background-image
// layers. The MVP takes only the FIRST layer. A TODO is left for future
// multi-layer support (would emit N records per element, or a single
// record carrying an array of layer URLs).

import type { BackgroundContent, ContainerRecord } from '../types';
import { snapshotComputedStyle, type WalkedNode } from '../dom-walker';

/** Maximum time we wait for `new Image()` to fire load/error. */
const IMAGE_LOAD_TIMEOUT_MS = 5000;

/**
 * Build a 'background' ContainerRecord from a walker node, or return null
 * when the element has no background-image (computed value 'none' or '').
 *
 * Async: resolves after the underlying bitmap has been decoded (real
 * browser) or after the data: URI header has been parsed (happy-dom /
 * Node test path). On any failure we return null and emit a single
 * `console.warn` — we never throw.
 */
export async function extractBackground(
  node: WalkedNode,
): Promise<ContainerRecord | null> {
  const el = node.element;

  // The walker already captured a computedStyle reference; re-using it
  // here keeps us aligned with the snapshot the rest of the record will
  // carry, and avoids a second getComputedStyle() call.
  const style = node.computedStyle;
  const rawBgImage = (style.backgroundImage || '').trim();
  if (!rawBgImage || rawBgImage === 'none') return null;

  // Multi-background support is future work. Take the first comma-
  // separated layer only.
  // TODO(SLICE-003-001-future): emit one ContainerRecord per background
  // layer, or extend BackgroundContent with a `layers` array.
  const firstLayer = splitFirstBackgroundLayer(rawBgImage);
  const rawUrl = extractUrlFromBackground(firstLayer);
  if (!rawUrl) return null;

  // Resolve relative URLs against the document base. data: URIs and
  // absolute URLs are returned unchanged by the URL constructor.
  const resolvedUrl = resolveUrl(rawUrl, el.ownerDocument);
  if (!resolvedUrl) {
    warn(`extractBackground: could not resolve URL "${rawUrl}"`);
    return null;
  }

  // SECURITY (CWE-918 SSRF mitigation, slice 07 security feedback 2026-05-28):
  // Reject dangerous schemes (javascript:, file:, chrome:, ...) and hostnames
  // pointing at loopback / RFC1918 / link-local addresses. A malicious source
  // document could otherwise probe internal services or local files via the
  // browser's background-image fetcher. Allowlist is enforced AFTER URL
  // resolution so relative paths can be resolved before their absolute form
  // is judged.
  if (!isSafeBackgroundUrl(resolvedUrl)) {
    return null;
  }

  const dims = await loadNaturalDimensions(resolvedUrl, el.ownerDocument);
  if (!dims) return null;

  const backgroundSize = (style.backgroundSize || '').trim() || 'auto';
  const backgroundPosition = (style.backgroundPosition || '').trim() || '0% 0%';

  const content: BackgroundContent = {
    kind: 'background',
    url: resolvedUrl,
    naturalWidth: dims.width,
    naturalHeight: dims.height,
    backgroundSize,
    backgroundPosition,
  };

  return {
    id: makeId('bg', node.sourceDomPath),
    kind: 'background',
    sourceDomPath: node.sourceDomPath,
    bounds: { width: dims.width, height: dims.height },
    computedStyle: snapshotComputedStyle(style),
    content,
  };
}

// --- internals ------------------------------------------------------------

/**
 * Split off the first comma-separated background-image layer. We CANNOT
 * use a naive split(',') because url(...) values may themselves contain
 * commas (rare for data URIs, but legal). Walk the string tracking
 * paren depth and quote state.
 *
 * BG3 (slice 07 TODO): MVP returns the FIRST url() layer only. Multi-
 * layer backgrounds (texture-over-photo, common in magazine grids)
 * silently drop every layer past the first. A future epic-level
 * decision will choose between:
 *   (a) emitting one ContainerRecord per layer with id suffix
 *       `bg-<hash>-l0`, `bg-<hash>-l1`, ...
 *   (b) extending BackgroundContent with `layers: string[]` (TYPE
 *       CONTRACT CHANGE — requires a fresh STORY-003-001 minor bump).
 * Until then this behaviour is documented as a known limitation.
 */
function splitFirstBackgroundLayer(input: string): string {
  let depth = 0;
  let quote: '"' | "'" | null = null;
  for (let i = 0; i < input.length; i++) {
    const ch = input[i]!;
    if (quote) {
      if (ch === quote && input[i - 1] !== '\\') quote = null;
      continue;
    }
    if (ch === '"' || ch === "'") {
      quote = ch;
      continue;
    }
    if (ch === '(') depth += 1;
    else if (ch === ')') depth -= 1;
    else if (ch === ',' && depth === 0) {
      return input.slice(0, i).trim();
    }
  }
  return input.trim();
}

/**
 * Pull the URL out of a single background-image layer string such as
 *   url("https://x/y.png")
 *   url('https://x/y.png')
 *   url(https://x/y.png)
 *   url(data:image/png;base64,...)
 * Returns null when the layer is a gradient or any non-`url()` value.
 */
function extractUrlFromBackground(layer: string): string | null {
  // Match url( ... ) with optional matched quotes around the inner value.
  // Use a non-greedy capture so trailing characters after the close paren
  // (e.g. background-size keywords concatenated in some serializers) do
  // not leak into the URL.
  const m = layer.match(/url\(\s*(?:"([^"]*)"|'([^']*)'|([^)]*))\s*\)/);
  if (!m) return null;
  const raw = (m[1] ?? m[2] ?? m[3] ?? '').trim();
  return raw || null;
}

/**
 * Resolve a CSS background URL against the document base URL. Returns
 * null on malformed inputs. data: URIs and absolute URLs pass through
 * unchanged via the URL constructor's two-argument form.
 */
function resolveUrl(rawUrl: string, doc: Document | null): string | null {
  if (!rawUrl) return null;
  // data: URIs never need base resolution; short-circuit to avoid the
  // URL constructor's percent-encoding nudges on base64 payloads.
  if (rawUrl.startsWith('data:')) return rawUrl;
  const base = doc?.baseURI || 'about:blank';
  try {
    return new URL(rawUrl, base).toString();
  } catch {
    return null;
  }
}

// --- SSRF / scheme allowlist (slice 07 security feedback 2026-05-28) ------
//
// CWE-918: a malicious source HTML document could embed a background-image
// URL pointing at loopback (http://localhost:5432/probe), RFC1918 ranges
// (http://192.168.1.1/admin), link-local metadata services
// (http://169.254.169.254/), or a local file (file:///etc/passwd) and use
// the browser's automatic background-image fetcher as an SSRF primitive.
// The mitigation is a scheme allowlist + hostname denylist applied after
// the URL has been resolved to its absolute form.
//
// Scheme policy:
//   ALLOWED   data: blob: http: https:
//   REJECTED  javascript: file: chrome: chrome-extension: about: ftp:
//             gopher: view-source: ws: wss: (and anything else)
//
// Hostname denylist (http:/https: only; data:/blob: have no hostname):
//   localhost, 127.0.0.0/8, ::1, 10.0.0.0/8, 172.16.0.0/12,
//   192.168.0.0/16, 169.254.0.0/16, 0.0.0.0
//
// On rejection we console.warn (with scheme + truncated URL prefix for
// debuggability) and return false; the caller then drops the background
// record entirely.

const SAFE_SCHEMES = new Set(['data:', 'blob:', 'http:', 'https:']);

function isSafeBackgroundUrl(url: string): boolean {
  let parsed: URL;
  try {
    parsed = new URL(url);
  } catch {
    warnRejected('unparseable', url);
    return false;
  }
  const scheme = parsed.protocol.toLowerCase();
  if (!SAFE_SCHEMES.has(scheme)) {
    warnRejected(scheme, url);
    return false;
  }
  // data: and blob: have no hostname to test; allow them at this point.
  if (scheme === 'data:' || scheme === 'blob:') return true;
  const host = parsed.hostname.toLowerCase();
  if (isDeniedHostname(host)) {
    warnRejected(`${scheme} (denied host: ${host})`, url);
    return false;
  }
  return true;
}

function warnRejected(reason: string, url: string): void {
  const trunc = url.length > 80 ? url.slice(0, 80) + '…' : url;
  warn(`extractBackground: rejected URL (scheme/host: ${reason}) "${trunc}"`);
}

function isDeniedHostname(host: string): boolean {
  if (!host) return true;
  if (host === 'localhost') return true;
  if (host === '::1') return true;
  if (host === '0.0.0.0') return true;
  // Strip surrounding brackets that URL.hostname leaves on IPv6 literals.
  // (URL.hostname does NOT include the brackets in modern engines, but a
  // belt-and-braces strip is harmless.)
  const stripped = host.startsWith('[') && host.endsWith(']')
    ? host.slice(1, -1)
    : host;
  // IPv4 dotted-quad?
  const ipv4 = parseIPv4(stripped);
  if (ipv4) {
    const [a, b /* , c, d */] = ipv4;
    // 127.0.0.0/8 (loopback)
    if (a === 127) return true;
    // 10.0.0.0/8 (RFC1918)
    if (a === 10) return true;
    // 172.16.0.0/12 (RFC1918): 172.16.x.x through 172.31.x.x
    if (a === 172 && b >= 16 && b <= 31) return true;
    // 192.168.0.0/16 (RFC1918)
    if (a === 192 && b === 168) return true;
    // 169.254.0.0/16 (link-local, incl. AWS/GCE metadata 169.254.169.254)
    if (a === 169 && b === 254) return true;
    // 0.0.0.0/8 (wildcard / unspecified)
    if (a === 0) return true;
  }
  return false;
}

function parseIPv4(host: string): [number, number, number, number] | null {
  const parts = host.split('.');
  if (parts.length !== 4) return null;
  const out: number[] = [];
  for (const p of parts) {
    if (!/^\d+$/.test(p)) return null;
    const n = parseInt(p, 10);
    if (!Number.isFinite(n) || n < 0 || n > 255) return null;
    out.push(n);
  }
  return [out[0]!, out[1]!, out[2]!, out[3]!];
}


// BG2 (slice 07): URL-level dedup memoization. Brad documents often reuse
// the same hero background across cover + TOC + back-cover sections. Without
// this cache each repeated url() triggers an independent decode + dimension
// probe. We key the cache by the owner Document, which means the cache
// lifetime is exactly one extract() call (DOMParser produces a fresh
// Document each invocation). Documents are not GC-rooted by the cache —
// WeakMap entries die when the parsed Document is unreferenced.
type DimResult = { width: number; height: number } | null;
const dimCache: WeakMap<Document, Map<string, Promise<DimResult>>> = new WeakMap();

function getDocCache(doc: Document | null): Map<string, Promise<DimResult>> | null {
  if (!doc) return null;
  let m = dimCache.get(doc);
  if (!m) {
    m = new Map();
    dimCache.set(doc, m);
  }
  return m;
}

/**
 * Load `url` and resolve to { width, height } on success, null on
 * any failure (404, CORS, timeout, decoder failure). Never throws.
 *
 * BG2 (slice 07): same-URL repeats within one extract() share an
 * in-flight Promise via a per-Document Map cache.
 */
async function loadNaturalDimensions(
  url: string,
  doc: Document | null,
): Promise<{ width: number; height: number } | null> {
  const cache = getDocCache(doc);
  if (cache) {
    const hit = cache.get(url);
    if (hit) return hit;
  }
  const p = loadNaturalDimensionsInner(url, doc);
  if (cache) cache.set(url, p);
  return p;
}

async function loadNaturalDimensionsInner(
  url: string,
  doc: Document | null,
): Promise<{ width: number; height: number } | null> {
  // Fast path #1: data: URIs we can decode directly from the header.
  // This is the path that exercises happy-dom in unit tests, where
  // `new Image()` never fires load/error.
  if (url.startsWith('data:')) {
    const decoded = decodeDataUriDimensions(url);
    if (decoded) return decoded;
    // Fall through to the Image() path — a real browser can still
    // decode data: URIs of types we don't sniff (e.g. WebP).
  }

  // General path: use `new Image()` against the document's window. We
  // prefer the document's own window (defaultView) so we share the
  // browsing-context, which matters for CORS in real browsers. In Node
  // / happy-dom test envs without a global Image, this returns null.
  const ImgCtor = pickImageConstructor(doc);
  if (!ImgCtor) {
    warn(`extractBackground: no Image() constructor available for "${url}"`);
    return null;
  }

  return new Promise<{ width: number; height: number } | null>((resolve) => {
    const img = new ImgCtor();
    let settled = false;
    const settle = (value: { width: number; height: number } | null): void => {
      if (settled) return;
      settled = true;
      // Detach handlers defensively. Some happy-dom builds reuse Image
      // instances under high test pressure; null-ing the handlers
      // ensures no late-firing event mutates the resolver state.
      try {
        img.onload = null;
        img.onerror = null;
      } catch {
        /* noop */
      }
      resolve(value);
    };

    const timer = setTimeout(() => {
      warn(`extractBackground: timeout loading "${url}" after ${IMAGE_LOAD_TIMEOUT_MS}ms`);
      // BG1 (slice 07): cancel the underlying bitmap decode before
      // settling. Real browsers free decoder bandwidth + GPU memory when
      // src is cleared on an in-flight Image. No-op in happy-dom (Image
      // is inert), but the assignment is harmless there.
      try {
        (img as HTMLImageElement).src = '';
      } catch {
        /* noop */
      }
      settle(null);
    }, IMAGE_LOAD_TIMEOUT_MS);
    // unref() so the timer never keeps the process alive in Node.
    if (typeof (timer as unknown as { unref?: () => void }).unref === 'function') {
      (timer as unknown as { unref: () => void }).unref();
    }

    img.onload = (): void => {
      clearTimeout(timer);
      const w = (img as HTMLImageElement).naturalWidth ?? 0;
      const h = (img as HTMLImageElement).naturalHeight ?? 0;
      if (w > 0 && h > 0) {
        settle({ width: w, height: h });
      } else {
        warn(`extractBackground: loaded "${url}" but natural dims are 0`);
        settle(null);
      }
    };
    img.onerror = (): void => {
      clearTimeout(timer);
      warn(`extractBackground: failed to load "${url}"`);
      settle(null);
    };

    try {
      (img as HTMLImageElement).src = url;
    } catch (err) {
      clearTimeout(timer);
      warn(`extractBackground: src assignment threw for "${url}": ${String(err)}`);
      settle(null);
    }
  });
}

function pickImageConstructor(doc: Document | null): (new () => HTMLImageElement) | null {
  const view = doc?.defaultView as
    | (Window & { Image?: new () => HTMLImageElement })
    | undefined;
  if (view && typeof view.Image === 'function') {
    return view.Image as new () => HTMLImageElement;
  }
  if (typeof Image !== 'undefined') {
    return Image as unknown as new () => HTMLImageElement;
  }
  return null;
}

// --- data: URI header decoders -------------------------------------------
//
// In happy-dom's test environment, `new Image()` is inert (load/error
// never fire, naturalWidth stays 0). Decoding common image-header byte
// patterns lets us return natural dimensions for the fixture cases we
// care about (PNG, GIF, JPEG) without depending on a real browser.
// Real browsers never hit this code path for HTTP URIs; they may hit
// it for data: URIs (it's faster than the load() round-trip and is
// deterministic across engines).

function decodeDataUriDimensions(
  url: string,
): { width: number; height: number } | null {
  // Form: data:<mime>;base64,<payload> OR data:<mime>,<payload>
  const comma = url.indexOf(',');
  if (comma < 0) return null;
  const meta = url.slice(5, comma); // strip leading "data:"
  const payload = url.slice(comma + 1);
  const isBase64 = /;base64$/i.test(meta) || /;base64;/i.test(meta);

  let bytes: Uint8Array;
  try {
    if (isBase64) {
      bytes = base64ToBytes(payload);
    } else {
      // URL-encoded payloads. Rare for raster images but spec-legal.
      const decoded = decodeURIComponent(payload);
      bytes = new Uint8Array(decoded.length);
      for (let i = 0; i < decoded.length; i++) {
        bytes[i] = decoded.charCodeAt(i) & 0xff;
      }
    }
  } catch {
    return null;
  }

  return sniffImageDimensions(bytes);
}

function base64ToBytes(b64: string): Uint8Array {
  // atob is available in browsers and modern Node (>=16). Fall back to
  // Buffer if we're somehow in a stripped runtime.
  let binary = '';
  if (typeof atob === 'function') {
    binary = atob(b64);
  } else if (typeof Buffer !== 'undefined') {
    const buf = Buffer.from(b64, 'base64');
    const out = new Uint8Array(buf.length);
    for (let i = 0; i < buf.length; i++) out[i] = buf[i]!;
    return out;
  } else {
    throw new Error('no base64 decoder available');
  }
  const out = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) out[i] = binary.charCodeAt(i) & 0xff;
  return out;
}

/**
 * Sniff width/height out of common image-format headers. Returns null
 * for formats we don't recognize (caller falls back to Image() load).
 *
 * Supported:
 *   PNG  — IHDR chunk at byte offset 16 (width/height as big-endian u32)
 *   GIF  — Logical Screen Descriptor at bytes 6..9 (width/height as
 *           little-endian u16)
 *   JPEG — scan markers for SOFn (0xC0/0xC1/0xC2) and read dims at
 *           offsets 5..8 of the segment payload (big-endian u16)
 */
function sniffImageDimensions(
  b: Uint8Array,
): { width: number; height: number } | null {
  if (b.length < 24) return null;

  // PNG: 89 50 4E 47 0D 0A 1A 0A
  if (
    b[0] === 0x89 &&
    b[1] === 0x50 &&
    b[2] === 0x4e &&
    b[3] === 0x47 &&
    b[4] === 0x0d &&
    b[5] === 0x0a &&
    b[6] === 0x1a &&
    b[7] === 0x0a
  ) {
    // IHDR begins at byte 8; width at byte 16 (big-endian u32),
    // height at byte 20.
    const w = readUint32BE(b, 16);
    const h = readUint32BE(b, 20);
    if (w > 0 && h > 0) return { width: w, height: h };
    return null;
  }

  // GIF: "GIF87a" or "GIF89a"
  if (
    b[0] === 0x47 &&
    b[1] === 0x49 &&
    b[2] === 0x46 &&
    b[3] === 0x38 &&
    (b[4] === 0x37 || b[4] === 0x39) &&
    b[5] === 0x61
  ) {
    const w = b[6]! | (b[7]! << 8);
    const h = b[8]! | (b[9]! << 8);
    if (w > 0 && h > 0) return { width: w, height: h };
    return null;
  }

  // JPEG: FF D8 FF ... then SOFn segments
  if (b[0] === 0xff && b[1] === 0xd8) {
    let i = 2;
    while (i < b.length - 9) {
      if (b[i] !== 0xff) return null; // out of sync
      // Skip any 0xFF padding bytes between segments.
      while (i < b.length && b[i] === 0xff) i += 1;
      const marker = b[i];
      i += 1;
      if (marker === undefined) return null;
      // Stand-alone markers (no length): SOI (D8), EOI (D9), RST0..7 (D0..D7), TEM (01)
      if (
        marker === 0xd8 ||
        marker === 0xd9 ||
        (marker >= 0xd0 && marker <= 0xd7) ||
        marker === 0x01
      ) {
        continue;
      }
      // Segment length (big-endian u16) including the length bytes themselves.
      if (i + 1 >= b.length) return null;
      const segLen = (b[i]! << 8) | b[i + 1]!;
      // SOFn markers: C0 (baseline), C1 (extended sequential), C2 (progressive),
      // C3, C5..C7, C9..CB, CD..CF. We don't need C4 (DHT) or CC (DAC).
      const isSof =
        (marker >= 0xc0 && marker <= 0xc3) ||
        (marker >= 0xc5 && marker <= 0xc7) ||
        (marker >= 0xc9 && marker <= 0xcb) ||
        (marker >= 0xcd && marker <= 0xcf);
      if (isSof) {
        // After the 2-byte length, the payload is: precision(1), height(2), width(2)
        if (i + 7 >= b.length) return null;
        const h = (b[i + 3]! << 8) | b[i + 4]!;
        const w = (b[i + 5]! << 8) | b[i + 6]!;
        if (w > 0 && h > 0) return { width: w, height: h };
        return null;
      }
      i += segLen; // advance past this segment
    }
    return null;
  }

  return null;
}

function readUint32BE(b: Uint8Array, off: number): number {
  if (off + 3 >= b.length) return 0;
  return (
    ((b[off]! << 24) >>> 0) +
    ((b[off + 1]! << 16) >>> 0) +
    ((b[off + 2]! << 8) >>> 0) +
    b[off + 3]!
  );
}

function warn(msg: string): void {
  // Single channel — keep consistent with svg.ts and table.ts. Tests
  // spy on console.warn to assert specific failure paths.
  // eslint-disable-next-line no-console
  console.warn(msg);
}

function makeId(prefix: string, path: string): string {
  // FNV-1a 32-bit, matching the pattern used by every other extractor.
  let h = 0x811c9dc5;
  for (let i = 0; i < path.length; i++) {
    h ^= path.charCodeAt(i);
    h = (h + ((h << 1) + (h << 4) + (h << 7) + (h << 8) + (h << 24))) >>> 0;
  }
  return `${prefix}-${h.toString(16)}`;
}
