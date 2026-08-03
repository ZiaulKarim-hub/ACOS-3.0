// git-manager — the live page.
//
// A saved file cannot update itself. Reloading one just re-reads the same
// frozen text, so an auto-reloading file would look live while being wrong,
// which is worse than admitting it is a snapshot. This module is the honest
// version: a small local server that re-scans when something actually changes
// and pushes the new table to any page that is open.
//
// STRICTLY READ-ONLY. It scans, it renders, it serves. It never commits, never
// pushes, never writes to a repo. The one thing it can be asked to do that
// touches the network is `git fetch`, and only when the human presses the
// button — because asking GitHub about 31 repos every few seconds would be slow
// and rude, and stale-but-labelled beats fast-and-rude.
//
// Bound to 127.0.0.1 on purpose: this machine only, never the network.

import { spawnSync } from "node:child_process";
import { renderBody, renderHtml } from "./render-html.ts";
import { scan } from "./scan.ts";
import type { Config, ScanResult } from "./types.ts";
import { startWatching } from "./watch.ts";

export interface ServeOptions {
  cfg: Config;
  /** First port to try. Taken ports are stepped over, never fought over. */
  port: number;
  loose: boolean;
  decisionsFile?: string;
  /** Open the page in Google Chrome once the server is up. */
  open: boolean;
}

interface Client {
  send: (payload: string) => void;
  close: () => void;
}

const ENC = new TextEncoder();

function nowStamp(): string {
  return new Date().toISOString().slice(11, 19);
}

/** Open in Google Chrome specifically. Failing is never fatal — the URL is printed. */
function openInBrowser(url: string): string {
  const chrome = spawnSync("open", ["-a", "Google Chrome", url], { encoding: "utf8" });
  if (chrome.status === 0) return "opened in Google Chrome";
  const fallback = spawnSync("open", [url], { encoding: "utf8" });
  if (fallback.status === 0) return "Google Chrome not available — opened in the default browser";
  return "could not open a browser — use the URL above";
}

export function serve(opts: ServeOptions): void {
  const clients = new Set<Client>();
  let current: ScanResult | null = null;
  let scanning = false;
  /** A change that arrived mid-scan. The result would be stale, so re-run once. */
  let queuedReason: string | null = null;

  const runScan = (reason: string, withFetch = false): void => {
    if (scanning) {
      queuedReason = reason;
      return;
    }
    scanning = true;
    const started = Date.now();
    try {
      current = scan(opts.cfg, {
        fetch: withFetch,
        loose: opts.loose,
        decisionsFile: opts.decisionsFile,
      });
      const ms = Date.now() - started;
      broadcast(reason, ms);
      console.log(
        `  ${nowStamp()}  ${reason}  →  rescanned in ${(ms / 1000).toFixed(1)}s  ` +
          `(${current.totals.needAttention} need attention, ${current.totals.uncommittedFiles} unsaved)`,
      );
    } catch (e) {
      // A scan that throws must not kill the server. The page keeps the last
      // good table and is TOLD the refresh failed, rather than silently
      // continuing to show old numbers as if they were current.
      const msg = (e as Error).message.split("\n")[0];
      console.error(`  ${nowStamp()}  scan FAILED: ${msg}`);
      for (const c of clients) {
        try {
          c.send(`data: ${JSON.stringify({ error: msg })}\n\n`);
        } catch {
          /* client gone */
        }
      }
    } finally {
      scanning = false;
      if (queuedReason !== null) {
        const r = queuedReason;
        queuedReason = null;
        runScan(r);
      }
    }
  };

  const broadcast = (reason: string, ms: number): void => {
    if (!current) return;
    const payload = `data: ${JSON.stringify({
      html: renderBody(current),
      generatedAtISO: current.generatedAtISO,
      scanMs: ms,
      reason,
    })}\n\n`;
    for (const c of clients) {
      try {
        c.send(payload);
      } catch {
        clients.delete(c);
      }
    }
  };

  // First scan before the server opens, so the very first page load is real
  // data rather than an empty shell that fills in a moment later.
  runScan("first scan");

  const tryListen = (port: number, attemptsLeft: number): ReturnType<typeof Bun.serve> => {
    try {
      return Bun.serve({
        port,
        hostname: "127.0.0.1",
        idleTimeout: 0, // a live connection is idle by design; never time it out
        fetch(req) {
          const url = new URL(req.url);

          if (url.pathname === "/events") {
            const stream = new ReadableStream({
              start(controller) {
                const client: Client = {
                  send: (s) => controller.enqueue(ENC.encode(s)),
                  close: () => {
                    try {
                      controller.close();
                    } catch {
                      /* already closed */
                    }
                  },
                };
                clients.add(client);
                // Send the current table immediately: a page that just opened
                // must not wait for the next change to show anything.
                if (current)
                  client.send(
                    `data: ${JSON.stringify({
                      html: renderBody(current),
                      generatedAtISO: current.generatedAtISO,
                      reason: "current state",
                    })}\n\n`,
                  );
                // A comment line every 20s keeps the connection from being
                // reaped by an idle timeout somewhere in the middle.
                const ping = setInterval(() => {
                  try {
                    client.send(`: ping\n\n`);
                  } catch {
                    clearInterval(ping);
                    clients.delete(client);
                  }
                }, 20_000);
                req.signal.addEventListener("abort", () => {
                  clearInterval(ping);
                  clients.delete(client);
                  client.close();
                });
              },
            });
            return new Response(stream, {
              headers: {
                "content-type": "text/event-stream",
                "cache-control": "no-store",
                connection: "keep-alive",
              },
            });
          }

          if (url.pathname === "/fetch" && req.method === "POST") {
            // The ONLY network-touching action, and only on a human's click.
            // `git fetch` is read-only: it downloads refs, it changes no commit.
            console.log(`  ${nowStamp()}  refresh from GitHub requested`);
            queueMicrotask(() => runScan("refreshed from GitHub", true));
            return new Response("ok");
          }

          if (url.pathname === "/" || url.pathname === "/index.html") {
            if (!current) return new Response("still scanning…", { status: 503 });
            return new Response(renderHtml(current, { live: true }), {
              headers: { "content-type": "text/html; charset=utf-8", "cache-control": "no-store" },
            });
          }

          return new Response("not found", { status: 404 });
        },
      });
    } catch (e) {
      const msg = (e as Error).message;
      const busy = /EADDRINUSE|in use|address already/i.test(msg);
      if (busy && attemptsLeft > 0) return tryListen(port + 1, attemptsLeft - 1);
      throw e;
    }
  };

  const server = tryListen(opts.port, 20);
  const url = `http://127.0.0.1:${server.port}/`;

  console.log("");
  console.log(`  GIT MANAGER — live at ${url}`);
  console.log("");
  console.log(`  ${current?.totals.needAttention ?? "?"} need attention · ` +
    `${current?.totals.decided ?? 0} you ruled out · ${current?.totals.clean ?? "?"} safe`);
  console.log("");
  console.log("  The page updates itself when a repo changes. It never pushes, never");
  console.log("  commits, and never writes to a repo — it only looks.");
  console.log("");
  console.log("  Remote counts stay as of each repo's last fetch. The 'refresh from");
  console.log("  GitHub' button on the page is the only thing that touches the network.");
  console.log("");
  console.log("  Press Ctrl-C to stop the server. The page will say so rather than");
  console.log("  quietly showing old numbers.");
  console.log("");

  if (opts.open) console.log(`  ${openInBrowser(url)}\n`);

  const stopWatching = startWatching({
    roots: opts.cfg.roots,
    skipDirs: opts.cfg.skipDirs,
    watchIgnore: opts.cfg.watchIgnore,
    onChange: (reason) => runScan(reason),
    onWatchError: (root, message) =>
      console.error(
        `  WARNING: cannot watch ${root} (${message}).\n` +
          `  Changes there will only appear on the periodic re-check, not instantly.`,
      ),
  });

  const shutdown = () => {
    console.log(`\n  ${nowStamp()}  stopping — open pages will say the connection was lost\n`);
    stopWatching();
    for (const c of clients) c.close();
    server.stop(true);
    process.exit(0);
  };
  process.on("SIGINT", shutdown);
  process.on("SIGTERM", shutdown);
}
