/**
 * S04 shared page model + the ONE move operation both topologies must perform.
 *
 * Deliberately identical for both spikes. The comparison is between process
 * TOPOLOGIES, not between two different applications — an unequal comparison is
 * not a comparison (the same rule S03 had to satisfy).
 *
 * Substrate-neutral by construction: plain strings, no framework. ADR-03 left the
 * substrate open and invariant I6 forbids a hard framework dependency, so this
 * spike may not assume one either.
 */

export interface Block { id: string; kind: "heading" | "para"; text: string }
export interface Page { id: string; title: string; blocks: Block[] }
export interface Doc { pages: Page[] }

const esc = (s: string) =>
  s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

/** THE move operation: shift one block up or down within its page. */
export function move(doc: Doc, pageId: string, blockId: string, dir: -1 | 1): boolean {
  const page = doc.pages.find((p) => p.id === pageId);
  if (!page) return false;
  const i = page.blocks.findIndex((b) => b.id === blockId);
  const j = i + dir;
  if (i < 0 || j < 0 || j >= page.blocks.length) return false;
  [page.blocks[i], page.blocks[j]] = [page.blocks[j], page.blocks[i]];
  return true;
}

/** The PREVIEW render: visitor view. No editor chrome of any kind. */
export function renderPreview(doc: Doc, pageId: string): string {
  const page = doc.pages.find((p) => p.id === pageId) ?? doc.pages[0];
  const nav = doc.pages.map((p) =>
    `<a href="/preview/${esc(p.id)}"${p.id === page.id ? ' aria-current="page"' : ""}>${esc(p.title)}</a>`).join(" · ");
  const body = page.blocks.map((b) =>
    b.kind === "heading"
      ? `<h1 data-block="${esc(b.id)}">${esc(b.text)}</h1>`
      : `<p data-block="${esc(b.id)}">${esc(b.text)}</p>`).join("\n");
  return `<!doctype html><meta charset="utf-8"><title>${esc(page.title)}</title>
<style>body{font:16px/1.55 ui-sans-serif,system-ui;margin:32px;max-width:640px}
nav{margin-bottom:24px;color:#666}a{color:#36c;text-decoration:none;margin-right:6px}
[aria-current]{font-weight:700;color:#111}h1{font-size:34px;margin:0 0 12px}</style>
<nav>${nav}</nav>
${body}
`;
}
