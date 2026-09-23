#!/usr/bin/env bun
/**
 * S04 topology A — the EDITOR origin. http://127.0.0.1:8831
 *
 * A separate process from the preview. Serves only the editor shell; every fact
 * about the preview arrives by postMessage, and every mutation crosses CORS.
 */
const PORT = 8831;
const PREVIEW_ORIGIN = "http://127.0.0.1:8832";                                 //CHANNEL

const EDITOR = `<!doctype html><meta charset="utf-8"><title>Editor — two origin</title>
<style>body{font:14px ui-sans-serif,system-ui;margin:0;display:flex;height:100vh}
#side{width:260px;padding:16px;border-right:1px solid #ddd;background:#fafafa}
iframe{flex:1;border:0}button{display:block;width:100%;margin:4px 0;padding:6px}
#log{font:12px ui-monospace,monospace;white-space:pre-wrap;margin-top:12px;color:#444}</style>
<div id="side"><strong>Editor</strong><div id="blocks"></div><div id="log">ready</div></div>
<iframe id="pv" src="${PREVIEW_ORIGIN}/preview/home"></iframe>
<script>
const PREVIEW = ${JSON.stringify(PREVIEW_ORIGIN)};                              //CHANNEL
const log = (m) => document.getElementById("log").textContent = m;
let seq = 0, pending = new Map();                                               //CHANNEL
window.addEventListener("message", (e) => {                                     //CHANNEL
  if (e.origin !== PREVIEW) return;             // origin check, mandatory      //CHANNEL
  if (e.data.type === "order" && pending.has(e.data.id)) {                      //CHANNEL
    pending.get(e.data.id)(e.data.order); pending.delete(e.data.id);            //CHANNEL
  }                                                                             //CHANNEL
});                                                                             //CHANNEL
function readOrder() {                                                          //CHANNEL
  return new Promise((res, rej) => {                                            //CHANNEL
    const id = ++seq; pending.set(id, res);                                     //CHANNEL
    document.getElementById("pv").contentWindow.postMessage(                     //CHANNEL
      { type: "read-order", id }, PREVIEW);                                     //CHANNEL
    setTimeout(() => { if (pending.delete(id)) rej(new Error("no reply")); }, 2000); //CHANNEL
  });                                                                           //CHANNEL
}                                                                               //CHANNEL
async function moveBlock(id, dir) {
  const t0 = performance.now();
  const r = await fetch(PREVIEW + "/api/move", { method: "POST",                //CHANNEL
      headers: { "content-type": "application/json" },                          //CHANNEL
      body: JSON.stringify({ page: "home", block: id, dir }) });                //CHANNEL
  const j = await r.json();
  const pv = document.getElementById("pv");                                     //CHANNEL
  await new Promise((res) => { pv.onload = res; pv.src = pv.src.split("#")[0].split("?r=")[0] + "?r=" + Date.now(); });            //CHANNEL
  const order = await readOrder();                                              //CHANNEL
  log("moved " + id + " -> " + order + "  " + (performance.now() - t0).toFixed(1) + "ms  unsaved=" + j.unsaved);
  render();
}
async function render() {
  const d = await (await fetch(PREVIEW + "/api/doc")).json();                    //CHANNEL
  document.getElementById("blocks").innerHTML = d.pages[0].blocks
    .map((b) => '<button onclick="moveBlock(\\'' + b.id + '\\',-1)">&uarr; ' + b.id + "</button>").join("");
}
window.moveBlock = moveBlock; render();
</script>`;


/** Benchmark harness: N move operations, INCLUDING the postMessage round trip. */
const BENCH = `<!doctype html><meta charset="utf-8"><title>bench A</title>
<iframe id="pv" src="${PREVIEW_ORIGIN}/preview/home" style="width:640px;height:320px;border:1px solid #ccc"></iframe>
<pre id="out">running…</pre>
<script>
const PREVIEW = ${JSON.stringify(PREVIEW_ORIGIN)};
let seq = 0; const pending = new Map();
window.addEventListener("message", (e) => {
  if (e.origin !== PREVIEW) return;
  if (e.data.type === "order" && pending.has(e.data.id)) { pending.get(e.data.id)(e.data.order); pending.delete(e.data.id); }
});
function readOrder(pv) {
  return new Promise((res, rej) => {
    const id = ++seq; pending.set(id, res);
    pv.contentWindow.postMessage({ type: "read-order", id }, PREVIEW);
    setTimeout(() => { if (pending.delete(id)) rej(new Error("no reply from preview")); }, 2000);
  });
}
(async () => {
  const N = Number(new URLSearchParams(location.search).get("n") || 5);
  const pv = document.getElementById("pv");
  await new Promise((r) => { pv.onload = r; setTimeout(r, 3000);
    pv.src = pv.src.split("#")[0].split("?r=")[0] + "?r=" + Date.now(); });
  const times = [];
  for (let i = 0; i < N; i++) {
    const dir = i % 2 === 0 ? -1 : 1;
    const t0 = performance.now();
    const res = await fetch(PREVIEW + "/api/move", { method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify({ page: "home", block: "p2", dir }) });
    await res.json();
    await new Promise((r) => { pv.onload = r; pv.src = pv.src.split("#")[0].split("?r=")[0] + "?r=" + Date.now(); });
    const order = await readOrder(pv);   // cross-origin: MUST go through postMessage
    times.push(performance.now() - t0);
    if (!order) throw new Error("empty order");
  }
  const sorted = [...times].sort((a, b) => a - b);
  const result = { topology: "A-two-origin", n: N,
    all_ms: times.map((t) => Number(t.toFixed(1))),
    median_ms: Number(sorted[Math.floor(sorted.length / 2)].toFixed(1)) };
  await fetch(PREVIEW + "/api/bench-result", { method: "POST",
    headers: { "content-type": "application/json" }, body: JSON.stringify(result) });
  document.getElementById("out").textContent = JSON.stringify(result);
})().catch((e) => {
  const err = { error: String((e && e.message) || e) };
  document.getElementById("out").textContent = JSON.stringify(err);
  fetch(PREVIEW + "/api/bench-result", { method: "POST",
    headers: { "content-type": "application/json" }, body: JSON.stringify(err) });
});
</script>`;

Bun.serve({
  hostname: "127.0.0.1",
  port: PORT,
  fetch(req) {
    const pth = new URL(req.url).pathname;
    if (pth === "/editor") return new Response(EDITOR, { headers: { "content-type": "text/html" } });
    if (pth === "/bench") return new Response(BENCH, { headers: { "content-type": "text/html" } });
    return new Response("not found", { status: 404 });
  },
});
console.log(`A editor origin listening on http://127.0.0.1:${PORT}/editor  pid=${process.pid}`);
