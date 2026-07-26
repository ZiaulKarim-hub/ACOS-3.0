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
  idleTimeout: 0,
  fetch(req: Request) {
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
      const stream = new ReadableStream<Uint8Array>({
        start(controller) {
          subscribers.add(controller);
          try {
            controller.enqueue(sse("state", buildIcState(sessionId)));
          } catch {
            /* first push failed; the poller will retry */
          }
        },
        cancel(controller) {
          subscribers.delete(controller as never);
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
      return req
        .json()
        .then((cmd: Record<string, unknown>) => {
          const stamped = {
            ...cmd,
            ts: typeof cmd?.ts === "string" ? cmd.ts : new Date().toISOString(),
          };
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
      lastPrint = fp;
      broadcast("state", buildIcState(sessionId));
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
