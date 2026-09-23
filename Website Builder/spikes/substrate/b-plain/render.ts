#!/usr/bin/env bun
/**
 * S03 candidate B — plain generated HTML from a TypeScript renderer.
 *
 * Zero third-party runtime. No package.json, no node_modules, no dev server
 * framework. Reads the SAME tokens.json and content.json as candidate A, so the
 * comparison is between substrates and not between two different pages.
 *
 * Usage: bun render.ts          -> dist/index.html
 *        bun render.ts --watch  -> rebuild on source change, print the latency
 */

import { mkdirSync, readFileSync, writeFileSync, watch } from "node:fs";
import { resolve } from "node:path";

const here = import.meta.dir;
const shared = resolve(here, "../shared");
const outDir = resolve(here, "dist");

type Tokens = Record<string, Record<string, string>>;
interface Content {
  title: string; tagline: string;
  sections: Array<{ heading: string; body: string }>;
  cta: { label: string; href: string };
}

/** Escape before interpolation, always. Content is data, never markup. */
const esc = (s: string) =>
  s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

function cssVars(t: Tokens): string {
  const lines: string[] = [];
  for (const group of Object.keys(t).sort())
    for (const key of Object.keys(t[group]).sort())
      lines.push(`  --${group}-${key}: ${t[group][key]};`);
  return lines.join("\n");
}

export function render(t: Tokens, c: Content): string {
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(c.title)}</title>
<meta name="description" content="${esc(c.tagline)}">
<style>
:root {
${cssVars(t)}
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--color-bg); color: var(--color-text);
       font-family: var(--type-family); font-size: var(--type-body); line-height: var(--type-lh); }
.wrap { max-width: 760px; margin: 0 auto; padding: var(--space-xl) var(--space-md); }
h1 { font-size: var(--type-h1); margin: 0 0 var(--space-sm); letter-spacing: -0.02em; }
h2 { font-size: var(--type-h2); margin: 0 0 var(--space-xs); }
.tagline { color: var(--color-muted); margin: 0 0 var(--space-xl); }
section { background: var(--color-surface); border-radius: var(--radius-md);
          padding: var(--space-md); margin-bottom: var(--space-md); }
section p { margin: 0; color: var(--color-muted); }
a.cta { display: inline-block; margin-top: var(--space-md); padding: var(--space-sm) var(--space-md);
        background: var(--color-accent); color: var(--color-bg); border-radius: var(--radius-md);
        text-decoration: none; font-weight: 600; }
</style>
</head>
<body>
<main class="wrap">
<h1>${esc(c.title)}</h1>
<p class="tagline">${esc(c.tagline)}</p>
${c.sections.map((s) => `<section>\n<h2>${esc(s.heading)}</h2>\n<p>${esc(s.body)}</p>\n</section>`).join("\n")}
<a class="cta" href="${esc(c.cta.href)}">${esc(c.cta.label)}</a>
</main>
</body>
</html>
`;
}

function build(): string {
  const t = JSON.parse(readFileSync(resolve(shared, "tokens.json"), "utf8")) as Tokens;
  const c = JSON.parse(readFileSync(resolve(shared, "content.json"), "utf8")) as Content;
  const html = render(t, c);
  mkdirSync(outDir, { recursive: true });
  writeFileSync(resolve(outDir, "index.html"), html);
  return html;
}

const html = build();
console.log(`built dist/index.html  ${Buffer.byteLength(html)} bytes`);

if (process.argv.includes("--watch")) {
  console.log("watching…");
  let last = 0;
  watch(shared, () => {
    const now = Date.now();
    if (now - last < 50) return; // fs.watch fires twice per write on macOS
    last = now;
    const t0 = performance.now();
    build();
    console.log(`rebuild ${(performance.now() - t0).toFixed(1)}ms`);
  });
}
