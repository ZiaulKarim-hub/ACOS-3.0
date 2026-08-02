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

import { existsSync } from "node:fs";
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
  const p = paths(sessionId).tree;
  // Same crash mode loadManifest guards against: writeJson is non-atomic and
  // tree.json is rewritten on EVERY insert, so a hard-kill can leave it empty
  // or truncated. Missing means "no tree yet"; present-but-unreadable must NOT
  // silently reset to an empty tree — the next save would cement a
  // structureless outline over the whole reorganized record.
  if (!existsSync(p)) return emptyTree();
  let t: Tree | null;
  try {
    t = readJson<Tree>(p, null as unknown as Tree);
  } catch {
    t = null;
  }
  if (!t || !t.root) {
    throw new Error(
      `tree at ${p} is empty or corrupt — restore it from git, or delete the file and re-file claims (riff tree autofile)`,
    );
  }
  return t;
}

export function saveTree(sessionId: string, t: Tree): void {
  writeJson(paths(sessionId).tree, t);
}

function childByName(node: ConceptNode, name: string): ConceptNode | undefined {
  return node.children.find((c) => c.name === name);
}

/**
 * Insert a claim under a slash-delimited concept path, creating nodes as needed.
 *
 * When `knownIds` is provided, an id it does not contain throws instead of
 * filing a phantom that would inflate the outline's claim counts (reorganize
 * already surfaces typo'd ids as `ignored`; this is insert's counterpart).
 * Autofile omits it — its ids come from the dossiers by construction.
 */
export function insert(
  sessionId: string,
  conceptPath: string,
  claimId: string,
  knownIds?: Set<string>,
): ConceptNode {
  const t = loadTree(sessionId);
  const parts = conceptPath.split("/").map((p) => p.trim()).filter(Boolean);
  if (parts.length === 0) {
    // A whitespace-only or all-slash path would silently file the claim onto
    // the root node, where walk/outline/stats never see it.
    throw new Error('concept path is empty — pass at least one segment, e.g. "pricing/tiers"');
  }
  if (parts[0] === "root") {
    // "root" is the sentinel id walk()/outline()/stats() key on — a top-level
    // child named root would share that id and its claims silently vanish.
    throw new Error('"root" is reserved — file under a named concept, e.g. "pricing/tiers"');
  }
  if (knownIds && !knownIds.has(claimId)) {
    throw new Error(`unknown claim id: ${claimId} — not in any dossier`);
  }
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
): { filed: number; skipped: number; defaulted: number; concepts: string[] } {
  const already = new Set<string>();
  walk(loadTree(sessionId).root, (n) => n.claim_ids.forEach((id) => already.add(id)));
  const concepts = new Set<string>();
  const fallback = by === "agent" ? "unattributed" : "unassigned";
  let filed = 0;
  let skipped = 0;
  let defaulted = 0;
  for (const c of claims) {
    if (already.has(c.id)) {
      skipped++;
      continue;
    }
    // Agent-written dimension/slug values arrive unsanitized: a whitespace-only
    // or all-slash value (or one forging the reserved "root" sentinel) would
    // make insert() throw and abort the whole run half-filed — every run, since
    // the bad value persists in the dossier. Normalize the key; anything that
    // normalizes away files under the fallback bucket instead, counted in
    // `defaulted` so the caller can surface a warning. Never fatal.
    const raw = by === "agent" ? c.slug : c.dimension;
    let key = (raw ?? "").split("/").map((s) => s.trim()).filter(Boolean).join("/");
    if (!key || key.split("/")[0] === "root") {
      if (raw !== undefined) defaulted++; // absent is normal; present-but-unusable is the warning
      key = fallback;
    }
    insert(sessionId, key, c.id);
    concepts.add(key);
    filed++;
  }
  return { filed, skipped, defaulted, concepts: [...concepts] };
}

/** Concepts that have outgrown TREE_K claims and want splitting into subtopics. */
export function pendingReorg(sessionId: string): ConceptNode[] {
  const out: ConceptNode[] = [];
  walk(loadTree(sessionId).root, (n) => {
    if (n.claim_ids.length > TREE_K && n.children.length === 0) out.push(n);
  });
  return out;
}

/**
 * Apply a split: move named claims into child concepts under `conceptId`.
 *
 * Merges into an existing child of the same name rather than pushing a
 * duplicate, so a retried or partially re-applied grouping is idempotent
 * instead of forking two children with identical ids. Claim ids that resolve
 * nowhere (typos) are returned as `ignored`, never dropped silently.
 */
export function reorganize(
  sessionId: string,
  conceptId: string,
  groups: Array<{ name: string; claim_ids: string[] }>,
): { node: ConceptNode; ignored: string[] } {
  // The payload is model-authored JSON (riff.ts casts readPayload straight to
  // this type) — validate before any mutation so a wrapper object or a missing
  // field fails naming the group, not with a deep TypeError mid-rewrite.
  if (!Array.isArray(groups)) {
    throw new Error('tree apply payload must be an ARRAY of {"name", "claim_ids"} groups');
  }
  for (let i = 0; i < groups.length; i++) {
    const g = groups[i];
    if (!g || typeof g !== "object" || typeof g.name !== "string" || !g.name.trim()) {
      // An empty-string name would pass the slash guard below and create an
      // effectively unaddressable child.
      throw new Error(`group ${i}: "name" must be a non-empty string`);
    }
    if (!Array.isArray(g.claim_ids)) {
      throw new Error(`group ${i} ("${g.name}"): "claim_ids" must be an array`);
    }
  }
  const t = loadTree(sessionId);
  const target = find(t.root, conceptId);
  if (!target) throw new Error(`unknown concept: ${conceptId}`);
  const moved = new Set<string>();
  const ignored: string[] = [];
  for (const g of groups) {
    // Slashes delimit concept paths in insert(); a slash inside a group name
    // would create a node no path can ever address again.
    if (g.name.includes("/")) {
      throw new Error(`group name must not contain "/": "${g.name}"`);
    }
    let child = childByName(target, g.name);
    if (!child) {
      child = { id: `${target.id}/${g.name}`, name: g.name, claim_ids: [], children: [] };
      target.children.push(child);
    }
    for (const id of g.claim_ids) {
      if (target.claim_ids.includes(id)) {
        if (!child.claim_ids.includes(id)) child.claim_ids.push(id);
        moved.add(id);
      } else if (!child.claim_ids.includes(id)) {
        // Not on the target and not already filed here — a typo'd id.
        ignored.push(id);
      }
    }
  }
  target.claim_ids = target.claim_ids.filter((id) => !moved.has(id));
  clean(target);
  // Recompute rather than blanket-clear: an all-typo apply moves nothing and
  // the node still needs splitting, and an oversized new child should carry
  // the marker pendingReorg would report — same predicate insert uses.
  const needsReorg = (n: ConceptNode) => n.claim_ids.length > TREE_K && n.children.length === 0;
  target.needs_reorg = needsReorg(target);
  for (const c of target.children) c.needs_reorg = needsReorg(c);
  saveTree(sessionId, t);
  return { node: target, ignored };
}

/**
 * Bottom-up cleanup: drop concepts left with no claims and no children.
 *
 * Deliberately does NOT collapse single-child pass-throughs: rewriting a
 * node's name to "parent/child" would make it unaddressable by insert()
 * (paths split on "/" and match per-segment), so the next insert to that
 * concept would fork a parallel duplicate node. A pass-through level in the
 * outline is cosmetic; a forked tree is not.
 */
export function clean(node: ConceptNode): void {
  for (const c of node.children) clean(c);
  node.children = node.children.filter(
    (c) => c.claim_ids.length > 0 || c.children.length > 0,
  );
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
