/**
 * Request framing for the Oracle daemon's unix socket.
 *
 * The hook sends ONE JSON object per connection and then waits for the reply
 * without half-closing, so the daemon cannot use end-of-stream as the frame
 * boundary. Bun delivers the bytes in chunks (about 8 KB each on this Mac), so a
 * request larger than one chunk arrives in pieces. Until 2026-10-12 the daemon
 * parsed EACH chunk as a whole document, so every request over ~8 KB — a big
 * Bash heredoc, any Write of a real file — was answered "bad request" and, once
 * the parse failure stopped being fail-open, DENIED.
 *
 * This framer collects the pieces and reports `complete` only when the bytes
 * so far parse as a JSON object. It is pure (no sockets) so it can be tested.
 */

export const MAX_REQUEST_BYTES = 8 * 1024 * 1024;

export type FrameResult =
  | { kind: "incomplete"; bytes: number }
  | { kind: "complete"; value: unknown; bytes: number }
  | { kind: "malformed"; bytes: number; why: string }
  | { kind: "overflow"; bytes: number };

export class RequestFramer {
  private parts: Uint8Array[] = [];
  private size = 0;
  private settled = false;

  constructor(private readonly max: number = MAX_REQUEST_BYTES) {}

  get bytes(): number {
    return this.size;
  }

  /** Feed one chunk. Once a non-incomplete result is returned, further chunks are ignored. */
  feed(chunk: Uint8Array): FrameResult {
    if (this.settled) return { kind: "incomplete", bytes: this.size };
    this.parts.push(chunk);
    this.size += chunk.byteLength;
    if (this.size > this.max) {
      this.settled = true;
      return { kind: "overflow", bytes: this.size };
    }
    // The protocol is one JSON OBJECT. Anything that does not open with "{" can
    // never become one, so reject it at once instead of waiting for more bytes.
    const first = firstNonSpace(this.parts);
    if (first !== null && first !== 0x7b /* { */) {
      this.settled = true;
      return { kind: "malformed", bytes: this.size, why: "request does not open with a JSON object" };
    }
    // A complete object must end with "}". Skip the (quadratic) re-parse while the
    // last byte is anything else — that is every middle chunk of a big request.
    if (lastNonSpace(this.parts) !== 0x7d /* } */) return { kind: "incomplete", bytes: this.size };
    const text = new TextDecoder("utf-8").decode(concat(this.parts));
    try {
      const value: unknown = JSON.parse(text);
      this.settled = true;
      if (value === null || typeof value !== "object" || Array.isArray(value)) {
        return { kind: "malformed", bytes: this.size, why: "request is not a JSON object" };
      }
      return { kind: "complete", value, bytes: this.size };
    } catch {
      // Ends with "}" but does not parse yet: a "}" inside a string, or a nested
      // object closed while the outer one is still open. Keep waiting.
      return { kind: "incomplete", bytes: this.size };
    }
  }
}

function concat(parts: Uint8Array[]): Uint8Array {
  if (parts.length === 1) return parts[0]!;
  const out = new Uint8Array(parts.reduce((n, p) => n + p.byteLength, 0));
  let off = 0;
  for (const p of parts) {
    out.set(p, off);
    off += p.byteLength;
  }
  return out;
}

function firstNonSpace(parts: Uint8Array[]): number | null {
  for (const p of parts) for (const b of p) if (!isSpace(b)) return b;
  return null;
}

function lastNonSpace(parts: Uint8Array[]): number | null {
  for (let i = parts.length - 1; i >= 0; i--) {
    const p = parts[i]!;
    for (let j = p.byteLength - 1; j >= 0; j--) if (!isSpace(p[j]!)) return p[j]!;
  }
  return null;
}

function isSpace(b: number): boolean {
  return b === 0x20 || b === 0x0a || b === 0x0d || b === 0x09;
}
