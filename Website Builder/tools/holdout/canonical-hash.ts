/**
 * canonical-hash.ts — THE ONE derivation method for holdout pack hashes.
 *
 * WHY THIS FILE EXISTS, stated because the rule is worthless without the incident.
 *
 * R2P (the project this system is imported from) publishes `private_pack_sha256`
 * in every holdout manifest, and its own `planning/holdouts/HASHING.md` runs to
 * 922 lines for one reason, quoted from that file verbatim:
 *
 *   "Different custodians used different derivation methods, and most manifests
 *    do not document theirs in-manifest. Evaluators MUST consult this file before
 *    running a holdout hash-verification step — guessing the wrong method
 *    produces a false MISMATCH on a valid, unmodified pack."
 *
 * The one verified recipe there needs member order README.md, cases.yaml,
 * expected.json (NOT alphabetical), dir-prefixed names, a specific cwd,
 * `COPYFILE_DISABLE=1 tar --no-xattrs --no-mac-metadata`, and pack files touched
 * to a normalised mtime because tar headers embed mtime. The custodian found it
 * by "exhaustively trying all 6 orderings x {bare filename, dir-prefixed} x
 * {with/without --no-xattrs --no-mac-metadata}".
 *
 * A false MISMATCH on a valid pack is the WORST failure this mechanism has. It is
 * indistinguishable from tampering, and it trains everyone to stop believing the
 * check. PRD §22.6 is the fix and this file is that fix:
 *
 *   1. ONE method, in code, with no per-manifest variation permitted.
 *   2. The method id is written INTO every manifest as `hash_method`, so a
 *      manifest is self-describing and no external lookup table can go stale.
 *   3. The digest is computed over file CONTENT ONLY. No mtime, no extended
 *      attributes, no tar header layout, no archive member order. Those are the
 *      inputs that produced the six orderings, so they are removed rather than
 *      documented.
 *   4. The tool writes the hash and the tool verifies it. No hand-run `shasum`
 *      pipeline appears in any runbook, because that is where the drift came from.
 */

import { createHash } from "node:crypto";
import { lstatSync, readdirSync, readFileSync } from "node:fs";
import { join, relative, sep } from "node:path";

/** The only method id this project mints. A manifest naming anything else is refused. */
export const HASH_METHOD = "wb-canon-1" as const;

/** Files a pack must contain, per PRD §22.5 (R2P's pack shape, carried over). */
export const PACK_FILES = ["cases.yaml", "expected.json", "README.md"] as const;

export function sha256Hex(data: Buffer | string): string {
  return createHash("sha256").update(data).digest("hex");
}

/** Every file under `dir`, as POSIX-separated paths relative to it, sorted by byte order. */
export function listPackFiles(dir: string): string[] {
  const out: string[] = [];
  const walk = (d: string) => {
    for (const name of readdirSync(d).sort()) {
      const full = join(d, name);
      // A pack must be self-contained, so a symlink REFUSES it outright.
      // Skipping links would be worse than useless: reveal.ts reads cases.yaml
      // with readFileSync, which follows links, so a skipped symlinked cases
      // file would still RUN while contributing nothing to the pack hash.
      // lstatSync, not statSync, because statSync resolves the link and would
      // report the target — the exact bug this replaces.
      const st = lstatSync(full, { throwIfNoEntry: false });
      if (!st) continue;
      if (st.isSymbolicLink()) {
        throw new Error(
          `pack refused: "${relative(dir, full).split(sep).join("/")}" is a symlink.\n` +
          `A holdout pack must be self-contained. What a link points at can change ` +
          `without the pack changing, so the pack hash would no longer pin what runs.`,
        );
      }
      if (st.isDirectory()) walk(full);
      else if (st.isFile()) out.push(relative(dir, full).split(sep).join("/"));
    }
  };
  walk(dir);
  // Sort on the POSIX-joined name, not on directory-walk order — the walk order
  // depends on the filesystem, and a hash that depends on the filesystem is the
  // whole class of bug this file exists to remove.
  return out.sort((a, b) => (a < b ? -1 : a > b ? 1 : 0));
}

/**
 * wb-canon-1: sha256 over `<relpath>\0<sha256(content)>\n` per file, paths sorted.
 *
 * Content is hashed per file rather than concatenated, so a byte moving across a
 * file boundary cannot leave the stream unchanged. The NUL separates a path from
 * its digest because NUL cannot occur in either, so no path can be crafted to
 * impersonate a path-plus-digest pair.
 */
export function canonicalPackHash(dir: string): { digest: string; files: string[] } {
  const files = listPackFiles(dir);
  const h = createHash("sha256");
  for (const rel of files) {
    h.update(Buffer.from(rel, "utf8"));
    h.update(Buffer.from([0x00]));
    h.update(Buffer.from(sha256Hex(readFileSync(join(dir, rel))), "utf8"));
    h.update(Buffer.from([0x0a]));
  }
  return { digest: h.digest("hex"), files };
}

/**
 * The expected-results digest: sha256 of `expected.json` alone.
 *
 * Kept as a SECOND published hash even though it is inconvenient. Publishing only
 * the pack hash would let a custodian silently swap the answer key while keeping
 * the questions, and the point of the seal is that neither moves (PRD §22.6).
 *
 * Deliberately byte-identical to `shasum -a 256 <pack>/expected.json`, which
 * R2P's HASHING.md reports holds "for every one of the 15 in-scope manifests,
 * with no exceptions found" — so an imported R2P pack verifies on this field
 * without re-derivation.
 */
export function expectedResultsHash(dir: string): string {
  return sha256Hex(readFileSync(join(dir, "expected.json")));
}
