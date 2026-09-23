#!/usr/bin/env bun
/**
 * S04 topology A — the PREVIEW origin. http://127.0.0.1:8832
 *
 * A separate process from the editor. The editor cannot read this DOM, because
 * the browser's same-origin policy forbids it across ports. So every fact the
 * editor needs about the preview has to be MESSAGED back, and this file has to
 * carry the listener that sends it.
 *
 * Lines tagged //CHANNEL exist ONLY to carry the editor<->preview channel.
 */
import { move, renderPreview, type Doc } from "../shared/model.ts";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const PORT = 8832;
const EDITOR_ORIGIN = "http://127.0.0.1:8831";                                 //CHANNEL
const doc: Doc = JSON.parse(readFileSync(resolve(import.meta.dir, "../shared/doc.json"), "utf8"));
let unsavedEdits = 0;
let benchResult: unknown = null;

/** Injected into every preview page so the editor can hear back from it.
 *  THIS IS EDITOR CHROME LIVING IN THE PREVIEW — see ADR-04 on screenshots. */
const BRIDGE = `<script>                                                        //CHANNEL
(function(){                                                                    //CHANNEL
  var ORIGIN = ${JSON.stringify(EDITOR_ORIGIN)};                                //CHANNEL
  window.addEventListener("message", function (e) {                             //CHANNEL
    if (e.origin !== ORIGIN) return;              // origin check, mandatory     //CHANNEL
    if (e.data && e.data.type === "read-order") {                               //CHANNEL
      var order = [].slice.call(document.querySelectorAll("[data-block]"))       //CHANNEL
                    .map(function (n) { return n.dataset.block; }).join(",");    //CHANNEL
      e.source.postMessage({ type: "order", order: order, id: e.data.id }, ORIGIN); //CHANNEL
    }                                                                           //CHANNEL
  });                                                                           //CHANNEL
  parent.postMessage({ type: "ready" }, ORIGIN);                                //CHANNEL
})();                                                                           //CHANNEL
</script>`;                                                                     //CHANNEL

const cors = (h: Record<string, string> = {}) => ({                             //CHANNEL
  ...h,                                                                          //CHANNEL
  "access-control-allow-origin": EDITOR_ORIGIN,                                 //CHANNEL
  "access-control-allow-headers": "content-type",                               //CHANNEL
  "access-control-allow-methods": "GET,POST,OPTIONS",                           //CHANNEL
});                                                                              //CHANNEL

Bun.serve({
  hostname: "127.0.0.1",
  port: PORT,
  async fetch(req) {
    const url = new URL(req.url);
    const p = url.pathname;
    if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: cors() });  //CHANNEL
    if (p.startsWith("/preview/")) {
      const html = renderPreview(doc, p.slice("/preview/".length));
      // ?bare=1 serves the page WITHOUT the bridge — the only way to get a
      // genuinely chrome-free screenshot on this topology.
      const bare = url.searchParams.get("bare") === "1";
      return new Response(bare ? html : html + BRIDGE, { headers: cors({ "content-type": "text/html" }) });
    }
    if (p === "/api/move" && req.method === "POST") {
      const { page, block, dir } = await req.json();
      const ok = move(doc, page, block, dir);
      if (ok) unsavedEdits++;
      return Response.json({ ok, unsaved: unsavedEdits }, { headers: cors() });                 //CHANNEL
    }
    if (p === "/api/doc") return Response.json(doc, { headers: cors() });                       //CHANNEL
    if (p === "/api/bench-result" && req.method === "POST") { benchResult = await req.json(); return Response.json({ ok: true }, { headers: cors() }); }
    if (p === "/api/bench-result") return Response.json(benchResult ?? { pending: true }, { headers: cors() });
    if (p === "/api/state") return Response.json({ pid: process.pid, unsaved: unsavedEdits }, { headers: cors() });
    return new Response("not found", { status: 404, headers: cors() });
  },
});
console.log(`A preview origin listening on http://127.0.0.1:${PORT}  pid=${process.pid}`);
