#!/usr/bin/env bun
/**
 * S04 topology B — SINGLE ORIGIN. One server proxies both surfaces.
 *
 * Editor at http://127.0.0.1:8830/editor
 * Preview at http://127.0.0.1:8830/preview/<pageId>   (same origin, in an iframe)
 *
 * Because the iframe is same-origin, the editor reaches the preview DOM directly.
 * No postMessage, no origin allowlist, no CORS. Lines that exist ONLY to carry the
 * editor<->preview channel are tagged  //CHANNEL  and counted by measure.ts.
 */
import { move, renderPreview, type Doc } from "../shared/model.ts";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const PORT = 8830;
const doc: Doc = JSON.parse(readFileSync(resolve(import.meta.dir, "../shared/doc.json"), "utf8"));
/** Unsaved edits live HERE, in the single process (invariant I5 probe). */
let unsavedEdits = 0;
let benchResult: unknown = null;

const EDITOR = `<!doctype html><meta charset="utf-8"><title>Editor — single origin</title>
<style>body{font:14px ui-sans-serif,system-ui;margin:0;display:flex;height:100vh}
#side{width:260px;padding:16px;border-right:1px solid #ddd;background:#fafafa}
iframe{flex:1;border:0}button{display:block;width:100%;margin:4px 0;padding:6px}
#log{font:12px ui-monospace,monospace;white-space:pre-wrap;margin-top:12px;color:#444}</style>
<div id="side">
  <strong>Editor</strong><div id="blocks"></div>
  <div id="log">ready</div>
</div>
<iframe id="pv" src="/preview/home"></iframe>
<script>
const log = (m) => document.getElementById("log").textContent = m;
async function moveBlock(id, dir) {
  const t0 = performance.now();
  const r = await fetch("/api/move", { method: "POST", headers: { "content-type": "application/json" },
                                       body: JSON.stringify({ page: "home", block: id, dir }) });
  const j = await r.json();
  const pv = document.getElementById("pv");                                   //CHANNEL
  await new Promise((res) => { pv.onload = res; pv.src = pv.src.split("#")[0].split("?r=")[0] + "?r=" + Date.now(); });          //CHANNEL
  // Same origin, so the editor can READ the preview's DOM directly to confirm.
  const order = [...pv.contentDocument.querySelectorAll("[data-block]")]      //CHANNEL
                  .map((n) => n.dataset.block).join(",");                     //CHANNEL
  log("moved " + id + " -> " + order + "  " + (performance.now() - t0).toFixed(1) + "ms  unsaved=" + j.unsaved);
  render();
}
async function render() {
  const r = await fetch("/api/doc"); const d = await r.json();
  document.getElementById("blocks").innerHTML = d.pages[0].blocks
    .map((b) => '<button onclick="moveBlock(\\'' + b.id + '\\',-1)">&uarr; ' + b.id + "</button>").join("");
}
window.moveBlock = moveBlock; render();
</script>`;


/** Benchmark harness: N move operations, reporting each round trip. */
const BENCH = `<!doctype html><meta charset="utf-8"><title>bench B</title>
<iframe id="pv" src="/preview/home" style="width:640px;height:320px;border:1px solid #ccc"></iframe>
<pre id="out">running…</pre>
<script>
(async () => {
  const N = Number(new URLSearchParams(location.search).get("n") || 5);
  const pv = document.getElementById("pv");
  await new Promise((r) => { pv.onload = r; setTimeout(r, 3000);
    pv.src = pv.src.split("#")[0].split("?r=")[0] + "?r=" + Date.now(); });
  const times = [];
  for (let i = 0; i < N; i++) {
    const dir = i % 2 === 0 ? -1 : 1;
    const t0 = performance.now();
    const res = await fetch("/api/move", { method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify({ page: "home", block: "p2", dir }) });
    await res.json();
    await new Promise((r) => { pv.onload = r; pv.src = pv.src.split("#")[0].split("?r=")[0] + "?r=" + Date.now(); });
    // Same origin: read the preview DOM directly. No message passing at all.
    const order = [...pv.contentDocument.querySelectorAll("[data-block]")].map((n) => n.dataset.block).join(",");
    times.push(performance.now() - t0);
    if (!order) throw new Error("preview DOM unreadable");
  }
  const sorted = [...times].sort((a, b) => a - b);
  const result = { topology: "B-single-origin", n: N,
    all_ms: times.map((t) => Number(t.toFixed(1))),
    median_ms: Number(sorted[Math.floor(sorted.length / 2)].toFixed(1)) };
  await fetch("/api/bench-result", { method: "POST",
    headers: { "content-type": "application/json" }, body: JSON.stringify(result) });
  document.getElementById("out").textContent = JSON.stringify(result);
})().catch((e) => {
  const err = { error: String((e && e.message) || e) };
  document.getElementById("out").textContent = JSON.stringify(err);
  fetch("/api/bench-result", { method: "POST",
    headers: { "content-type": "application/json" }, body: JSON.stringify(err) });
});
</script>`;

Bun.serve({
  hostname: "127.0.0.1",
  port: PORT,
  async fetch(req) {
    const url = new URL(req.url);
    const p = url.pathname;
    if (p === "/editor") return new Response(EDITOR, { headers: { "content-type": "text/html" } });
    if (p === "/bench") return new Response(BENCH, { headers: { "content-type": "text/html" } });
    if (p.startsWith("/preview/")) {
      return new Response(renderPreview(doc, p.slice("/preview/".length)), { headers: { "content-type": "text/html" } });
    }
    if (p === "/api/doc") return Response.json(doc);
    if (p === "/api/move" && req.method === "POST") {
      const { page, block, dir } = await req.json();
      const ok = move(doc, page, block, dir);
      if (ok) unsavedEdits++;
      return Response.json({ ok, unsaved: unsavedEdits });
    }
    if (p === "/api/bench-result" && req.method === "POST") { benchResult = await req.json(); return Response.json({ ok: true }); }
    if (p === "/api/bench-result") return Response.json(benchResult ?? { pending: true });
    if (p === "/api/state") return Response.json({ pid: process.pid, unsaved: unsavedEdits });
    return new Response("not found", { status: 404 });
  },
});
console.log(`B single-origin listening on http://127.0.0.1:${PORT}/editor  pid=${process.pid}`);
