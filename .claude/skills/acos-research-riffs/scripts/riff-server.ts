#!/usr/bin/env bun
/**
 * riff-server — the browser bridge for the research room.
 *
 * Mirrors the Investment Committee's `ic-server.py` in shape: serve one page,
 * stream state changes to it over SSE (Server-Sent Events — a one-way channel
 * that lets a web page receive pushes without polling or refreshing), and never
 * do any research itself. This process only moves bytes between disk and the
 * browser; it never calls Task() and never writes to the session.
 *
 * It differs in one way, and deliberately. The IC server reads a state file its
 * engine maintains. This one RECOMPUTES state from the session directory on
 * every change, because every fact the room shows already lives on disk. A
 * mirror file would be one more thing to forget to update, and a stale mirror
 * looks exactly like live research.
 *
 * Read-only by construction: there is no route that writes to the session.
 *
 * Binds loopback only: the room is a local viewer and the chair channel drives
 * subscription-billed generations, so it is never exposed to the LAN.
 *
 * Usage:
 *   bun riff-server.ts --session <session-id> [--port 0] [--root <project dir>]
 */

import { existsSync, readFileSync, appendFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { parseArgs } from "./lib/util.ts";
import { buildIcState, stateFingerprint } from "./lib/room.ts";
import { paths, resolveSession } from "./lib/session.ts";

const HERE = dirname(fileURLToPath(import.meta.url));
const PAGE = join(HERE, "room", "room.html");

const args = parseArgs(process.argv.slice(2));
if (args.flags["root"]) process.env.RIFF_ROOT = args.flags["root"];

let sessionId: string;
try {
  sessionId = resolveSession(args.flags["session"]).session_id;
} catch (e) {
  console.error(`riff-server: ${e instanceof Error ? e.message : String(e)}`);
  process.exit(1);
}

const requestedPort = Number(args.flags["port"] ?? "0");
const POLL_MS = 700;
const CHAIR_MAX = 4000; // hard cap on chair text — it lands verbatim in seat prompts

// The chair channel — the ONLY thing this server writes, and it writes to a
// dedicated append-only inbox, never to session state. This mirrors IC's
// ic-server.py: the browser posts a chair command, it lands as one JSON line in
// chair-inbox.jsonl, and the moderator (the Claude session) reads it with a
// zero-token `tail -f`. The room stays a viewer of research; the inbox is how the
// human steers it, exactly as the committee chair steers the IC meeting.
const INBOX = join(paths(sessionId).root, "chair-inbox.jsonl");
if (!existsSync(INBOX)) writeFileSync(INBOX, "");

const encoder = new TextEncoder();
const subscribers = new Set<ReadableStreamDefaultController<Uint8Array>>();
let lastPrint = stateFingerprint(sessionId);

// DNS-rebinding guard: the loopback bind stops LAN peers, but a hostile page
// can point ITS OWN hostname at 127.0.0.1 — and then a Host-derived url.origin
// compares one attacker-controlled header against another. A genuine local
// request can only carry a loopback Host, so the Host header is checked against
// this fixed allowlist (any port) on EVERY route — /state alone exposes the
// whole research corpus — and the chair channel's Origin check compares against
// the same list, never against url.origin.
const LOOPBACK_HOSTS = new Set(["127.0.0.1", "localhost", "[::1]"]);

/** True when a Host header value ("localhost:4321", "[::1]:80") names loopback. */
function isLoopbackHost(host: string | null): boolean {
  if (!host) return false;
  const bare = host.startsWith("[") ? host.replace(/\]:\d+$/, "]") : host.replace(/:\d+$/, "");
  return LOOPBACK_HOSTS.has(bare.toLowerCase());
}

/** True when an Origin header value names a loopback host (any scheme/port). */
function isLoopbackOrigin(origin: string): boolean {
  try {
    return isLoopbackHost(new URL(origin).host);
  } catch {
    return false;
  }
}

function sse(event: string, data: unknown): Uint8Array {
  return encoder.encode(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`);
}

function broadcast(event: string, data: unknown): void {
  const chunk = sse(event, data);
  for (const c of [...subscribers]) {
    try {
      c.enqueue(chunk);
    } catch {
      subscribers.delete(c);
    }
  }
}

const server = Bun.serve({
  port: requestedPort,
  hostname: "127.0.0.1", // loopback only — riff.ts fetches http://localhost:<port>
  idleTimeout: 0,
  fetch(req: Request) {
    // A rebound hostile hostname fails here, before any route logic runs.
    if (!isLoopbackHost(req.headers.get("host"))) {
      return new Response("forbidden: loopback hosts only", { status: 403 });
    }
    const url = new URL(req.url);

    if (url.pathname === "/") {
      if (!existsSync(PAGE)) {
        return new Response(`room page missing: ${PAGE}`, { status: 500 });
      }
      return new Response(readFileSync(PAGE, "utf8"), {
        headers: { "content-type": "text/html; charset=utf-8" },
      });
    }

    if (url.pathname === "/state") {
      try {
        return Response.json(buildIcState(sessionId));
      } catch (e) {
        return Response.json(
          { error: e instanceof Error ? e.message : String(e) },
          { status: 500 },
        );
      }
    }

    if (url.pathname === "/events") {
      // cancel() receives the cancellation REASON, not the controller — stash
      // the controller at start() so a disconnect actually leaves the set
      // instead of lingering until an enqueue happens to throw.
      let ctrl: ReadableStreamDefaultController<Uint8Array> | undefined;
      const stream = new ReadableStream<Uint8Array>({
        start(controller) {
          ctrl = controller;
          subscribers.add(controller);
          try {
            controller.enqueue(sse("state", buildIcState(sessionId)));
          } catch {
            /* first push failed; the poller will retry */
          }
        },
        cancel() {
          if (ctrl) subscribers.delete(ctrl);
        },
      });
      return new Response(stream, {
        headers: {
          "content-type": "text/event-stream",
          "cache-control": "no-cache",
          connection: "keep-alive",
        },
      });
    }

    if (req.method === "POST" && url.pathname === "/chair-cmd") {
      // The chair channel is the one writable route, so it gets the guards the
      // read routes don't need. Browsers fire cross-origin "simple" POSTs at
      // localhost with no preflight (CSRF), so: reject any request whose Origin
      // is present and not loopback (against the fixed allowlist above — never
      // url.origin, which is Host-derived and rebinding-controlled), require the
      // exact application/json media type (a substring match lets a
      // 'text/plain; charset=application/json' simple request through), and keep
      // only the known command keys so the inbox holds bounded, known-shape lines.
      const origin = req.headers.get("origin");
      if (origin && !isLoopbackOrigin(origin)) {
        return Response.json({ ok: false, error: "cross-origin rejected" }, { status: 403 });
      }
      // Media-type essence only — everything before ";" — must equal
      // application/json, so cross-origin JSON genuinely requires a preflight.
      const ctype = (req.headers.get("content-type") ?? "").split(";")[0]!.trim().toLowerCase();
      if (ctype !== "application/json") {
        return Response.json(
          { ok: false, error: "content-type must be application/json" },
          { status: 415 },
        );
      }
      return req
        .json()
        .then((cmd: Record<string, unknown>) => {
          if (typeof cmd?.type !== "string" || !cmd.type || cmd.type.length > 40) {
            return Response.json({ ok: false, error: "bad command" }, { status: 400 });
          }
          // Key whitelist mirrors what riff-live reads: type, seat, value/level,
          // chair/text (aliases), ts. Anything else is dropped, chair text capped.
          const stamped: Record<string, unknown> = {
            type: cmd.type,
            ts: typeof cmd.ts === "string" ? cmd.ts.slice(0, 40) : new Date().toISOString(),
          };
          if (typeof cmd.seat === "number" && Number.isFinite(cmd.seat)) stamped.seat = cmd.seat;
          if (typeof cmd.value === "number" && Number.isFinite(cmd.value)) stamped.value = cmd.value;
          if (typeof cmd.level === "number" && Number.isFinite(cmd.level)) stamped.level = cmd.level;
          if (typeof cmd.chair === "string") stamped.chair = cmd.chair.slice(0, CHAIR_MAX);
          if (typeof cmd.text === "string") stamped.text = cmd.text.slice(0, CHAIR_MAX);
          appendFileSync(INBOX, JSON.stringify(stamped) + "\n");
          broadcast("chair", { ...stamped, status: "queued" });
          return Response.json({ ok: true, queued: stamped });
        })
        .catch(() => Response.json({ ok: false, error: "bad command" }, { status: 400 }));
    }

    return new Response("not found", { status: 404 });
  },
});

// Poll the session's fingerprint and push only when something actually changed.
// A heartbeat every ~15s keeps idle connections from being reaped by proxies or
// the browser's own timeouts.
let ticks = 0;
const poller = setInterval(() => {
  ticks++;
  try {
    const fp = stateFingerprint(sessionId);
    if (fp !== lastPrint) {
      // Build BEFORE advancing lastPrint: buildIcState can throw on a file
      // caught mid-write, and advancing first would swallow this state push
      // permanently — the fingerprint would already match on the retry tick.
      const state = buildIcState(sessionId);
      lastPrint = fp;
      broadcast("state", state);
    } else if (ticks % Math.round(15000 / POLL_MS) === 0) {
      for (const c of [...subscribers]) {
        try {
          c.enqueue(encoder.encode(": heartbeat\n\n"));
        } catch {
          subscribers.delete(c);
        }
      }
    }
  } catch {
    /* a half-written file mid-append; the next tick picks it up */
  }
}, POLL_MS);

function shutdown(): void {
  clearInterval(poller);
  server.stop(true);
  process.exit(0);
}
process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);

console.log(
  JSON.stringify({
    url: `http://localhost:${server.port}`,
    port: server.port,
    session_id: sessionId,
    root: paths(sessionId).root,
    note: "read-only; recomputes state from the session directory on every change",
  }),
);
