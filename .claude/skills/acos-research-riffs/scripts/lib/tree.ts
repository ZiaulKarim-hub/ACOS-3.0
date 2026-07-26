/**
 * The concept tree — the riff's living map of what has been learned.
 *
 * Every claim is filed under a concept together with the question that produced
 * it, so the tree records not just what was found but why it was looked for.
 * The same tree becomes the outline of the final report, which is what keeps the
 * report a projection of the record rather than a recollection of the chat.
 *
 * Reorganize fires when a concept exceeds TREE_K claims. The published system
 * this borrows from tracked its own discourse correctly only 71% of the time, so
 * `riff correct` exists and corrections are ledger supersessions — the tree is
 * never treated as self-evidently right.
 */

import { readJson, writeJson } from "./util.ts";
import { paths, TREE_K } from "./session.ts";

export interface ConceptNode {
  id: string;
  name: string;
  claim_ids: string[];
  children: ConceptNode[];
  needs_reorg?: boolean;
}

export interface Tree {
  root: ConceptNode;
}

function emptyTree(): Tree {
  return { root: { id: "root", name: "root", claim_ids: [], children: [] } };
}

export function loadTree(sessionId: string): Tree {
  return readJson<Tree>(paths(sessionId).tree, emptyTree());
}

export function saveTree(sessionId: string, t: Tree): void {
  writeJson(paths(sessionId).tree, t);
}

function childByName(node: ConceptNode, name: string): ConceptNode | undefined {
  return node.children.find((c) => c.name === name);
}

/** Insert a claim under a slash-delimited concept path, creating nodes as needed. */
export function insert(sessionId: string, conceptPath: string, claimId: string): ConceptNode {
  const t = loadTree(sessionId);
  const parts = conceptPath.split("/").map((p) => p.trim()).filter(Boolean);
  let node = t.root;
  const idParts: string[] = [];
  for (const part of parts) {
    idParts.push(part);
    let next = childByName(node, part);
    if (!next) {
      next = { id: idParts.join("/"), name: part, claim_ids: [], children: [] };
      node.children.push(next);
    }
    node = next;
  }
  if (!node.claim_ids.includes(claimId)) node.claim_ids.push(claimId);
  node.needs_reorg = node.claim_ids.length > TREE_K && node.children.length === 0;
  saveTree(sessionId, t);
  return node;
}

/**
 * File every unfiled claim under a default concept, so the report always has an
 * outline to project from.
 *
 * During a conversation, claims get filed as they come up, which produces a tree
 * shaped by the discussion. But a research-heavy session can land a hundred-plus
 * claims that were never individually discussed, and filing those one at a time
 * is not a real workflow — the practical result would be an empty tree and a
 * report with no structure.
 *
 * So this gives a defensible default: group by the coverage dimension the claim
 * answers (or by the seat that found it). It is a starting skeleton, not a
 * finished outline — reorganize afterwards to reflect what the material actually
 * says rather than which checklist row it came from.
 */
export function autofile(
  sessionId: string,
  claims: Array<{ id: string; dimension?: string; slug?: string }>,
  by: "dimension" | "agent" = "dimension",
): { filed: number; skipped: number; concepts: string[] } {
  const already = new Set<string>();
  walk(loadTree(sessionId).root, (n) => n.claim_ids.forEach((id) => already.add(id)));
  const concepts = new Set<string>();
  let filed = 0;
  let skipped = 0;
  for (const c of claims) {
    if (already.has(c.id)) {
      skipped++;
      continue;
    }
    const key =
      by === "agent" ? (c.slug ?? "unattributed") : (c.dimension ?? "unassigned");
    insert(sessionId, key, c.id);
    concepts.add(key);
    filed++;
  }
  return { filed, skipped, concepts: [...concepts] };
}

/** Concepts that have outgrown TREE_K claims and want splitting into subtopics. */
export function pendingReorg(sessionId: string): ConceptNode[] {
  const out: ConceptNode[] = [];
  walk(loadTree(sessionId).root, (n) => {
    if (n.claim_ids.length > TREE_K && n.children.length === 0) out.push(n);
  });
  return out;
}

/** Apply a split: move named claims into new child concepts under `conceptId`. */
export function reorganize(
  sessionId: string,
  conceptId: string,
  groups: Array<{ name: string; claim_ids: string[] }>,
): ConceptNode {
  const t = loadTree(sessionId);
  const target = find(t.root, conceptId);
  if (!target) throw new Error(`unknown concept: ${conceptId}`);
  const moved = new Set<string>();
  for (const g of groups) {
    const child: ConceptNode = {
      id: `${target.id}/${g.name}`,
      name: g.name,
      claim_ids: g.claim_ids.filter((id) => target.claim_ids.includes(id)),
      children: [],
    };
    for (const id of child.claim_ids) moved.add(id);
    target.children.push(child);
  }
  target.claim_ids = target.claim_ids.filter((id) => !moved.has(id));
  target.needs_reorg = false;
  clean(target);
  saveTree(sessionId, t);
  return target;
}

/** Bottom-up cleanup: drop empty concepts, collapse single-child pass-throughs. */
export function clean(node: ConceptNode): void {
  for (const c of node.children) clean(c);
  node.children = node.children.filter(
    (c) => c.claim_ids.length > 0 || c.children.length > 0,
  );
  if (node.children.length === 1 && node.claim_ids.length === 0 && node.id !== "root") {
    const only = node.children[0]!;
    node.name = `${node.name}/${only.name}`;
    node.claim_ids = only.claim_ids;
    node.children = only.children;
  }
}

export function find(node: ConceptNode, id: string): ConceptNode | null {
  if (node.id === id) return node;
  for (const c of node.children) {
    const hit = find(c, id);
    if (hit) return hit;
  }
  return null;
}

export function walk(node: ConceptNode, fn: (n: ConceptNode) => void): void {
  if (node.id !== "root") fn(node);
  for (const c of node.children) walk(c, fn);
}

/** Markdown outline — this is what the report compiler uses for its sections. */
export function outline(sessionId: string): string {
  const t = loadTree(sessionId);
  const lines: string[] = [];
  const render = (n: ConceptNode, depth: number) => {
    if (n.id !== "root") {
      lines.push(
        `${"  ".repeat(depth - 1)}- ${n.name} (${n.claim_ids.length} claim${
          n.claim_ids.length === 1 ? "" : "s"
        })${n.needs_reorg ? "  [needs-reorg]" : ""}`,
      );
    }
    for (const c of n.children) render(c, depth + 1);
  };
  render(t.root, 0);
  return lines.join("\n") || "(empty)";
}

export function stats(sessionId: string): Record<string, number> {
  let concepts = 0;
  let filed = 0;
  walk(loadTree(sessionId).root, (n) => {
    concepts += 1;
    filed += n.claim_ids.length;
  });
  return { concepts, filed_claims: filed, pending_reorg: pendingReorg(sessionId).length };
}
