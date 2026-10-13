import { describe, expect, test } from "bun:test";
import { RequestFramer } from "./framing";

const enc = new TextEncoder();
const split = (bytes: Uint8Array, size: number): Uint8Array[] => {
  const out: Uint8Array[] = [];
  for (let i = 0; i < bytes.byteLength; i += size) out.push(bytes.subarray(i, i + size));
  return out;
};

describe("RequestFramer — the ~8 KB chunk bug of 2026-10-12", () => {
  test("a 20 KB request split into 8 KB chunks is incomplete until the last chunk, then parses whole", () => {
    const req = { tool_name: "Write", tool_input: { file_path: "/tmp/x", content: "a".repeat(20_000) }, cwd: "/tmp" };
    const chunks = split(enc.encode(JSON.stringify(req)), 8192);
    expect(chunks.length).toBeGreaterThan(2);
    const f = new RequestFramer();
    const results = chunks.map((c) => f.feed(c));
    for (const r of results.slice(0, -1)) expect(r.kind).toBe("incomplete");
    const last = results[results.length - 1]!;
    expect(last.kind).toBe("complete");
    if (last.kind === "complete") expect(last.value).toEqual(req);
  });

  test("a multibyte character split across a chunk boundary survives", () => {
    const req = { tool_name: "Bash", tool_input: { command: "echo " + "é".repeat(5000) }, cwd: "/" };
    const bytes = enc.encode(JSON.stringify(req));
    // force the cut inside a 2-byte sequence: find an odd offset into the run of é
    const cut = bytes.indexOf(0xc3) + 1;
    const f = new RequestFramer();
    expect(f.feed(bytes.subarray(0, cut)).kind).toBe("incomplete");
    const r = f.feed(bytes.subarray(cut));
    expect(r.kind).toBe("complete");
    if (r.kind === "complete") expect(r.value).toEqual(req);
  });

  test("a '}' inside a string does not end the frame early", () => {
    const req = { tool_name: "Bash", tool_input: { command: "printf '}'" }, cwd: "/" };
    const bytes = enc.encode(JSON.stringify(req));
    const cut = bytes.indexOf(0x7d) + 1; // right after the first "}" — the one inside the string
    const f = new RequestFramer();
    expect(f.feed(bytes.subarray(0, cut)).kind).toBe("incomplete");
    const r = f.feed(bytes.subarray(cut));
    expect(r.kind).toBe("complete");
  });

  test("bytes that do not open a JSON object are rejected at once", () => {
    const f = new RequestFramer();
    const r = f.feed(enc.encode("GET / HTTP/1.1\r\n"));
    expect(r.kind).toBe("malformed");
  });

  test("a JSON array or scalar is malformed, not a request", () => {
    expect(new RequestFramer().feed(enc.encode("[1,2]")).kind).toBe("malformed");
    expect(new RequestFramer().feed(enc.encode("42")).kind).toBe("malformed");
  });

  test("a request over the size cap is reported as overflow", () => {
    const f = new RequestFramer(1024);
    const r = f.feed(enc.encode('{"tool_name":"Write","tool_input":{"content":"' + "x".repeat(2000) + '"}}'));
    expect(r.kind).toBe("overflow");
  });

  test("a small request in one chunk still works exactly as before", () => {
    const req = { tool_name: "Bash", tool_input: { command: "ls" }, cwd: "/tmp", context: "", goal: "" };
    const r = new RequestFramer().feed(enc.encode(JSON.stringify(req)));
    expect(r.kind).toBe("complete");
    if (r.kind === "complete") expect(r.value).toEqual(req);
  });
});
