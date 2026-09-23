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
 *   3. The digest is computed over file CONTENT ONLY (plus, since wb-canon-2,
 *      the owner-execute bit). No mtime, no extended attributes, no tar header
 *      layout, no archive member order. Those are the inputs that produced the
 *      six orderings, so they are removed rather than documented.
 *      SECURITY TRADE-OFF, stated (re-review S7, executed): because xattrs are
 *      outside the digest, a macOS pack can carry an arbitrary hidden payload in
 *      an extended attribute without moving either published hash. Hashing them
 *      would fabricate false MISMATCHes on ordinary copies — the worst failure
 *      this file exists to prevent — so they stay excluded. Two mitigations:
 *      reveal.ts holds the pack in MEMORY during the run (file CONTENT only), so
 *      no case can read an xattr at grade time, and its restore is written fresh
 *      from those bytes, so xattrs are DROPPED rather than carried forward.
 *   4. The tool writes the hash and the tool verifies it. No hand-run `shasum`
 *      pipeline appears in any runbook, because that is where the drift came from.
 */

import { createHash } from "node:crypto";
import { lstatSync, readdirSync, readFileSync } from "node:fs";
import { join, relative, sep } from "node:path";

/**
 * The only method id this project mints. A manifest naming anything else is refused.
 *
 * wb-canon-2 (security review F5): wb-canon-1 hashed path + content only. A pack
 * may ship a helper script a case invokes as `./helper.sh`, and flipping its
 * executable bit changed behaviour from "runs" to "permission denied" with the
 * digest UNCHANGED — a pack that moved without its seal moving. The executable
 * bit now feeds the digest. ONLY the owner-execute bit: group/other permission
 * bits vary with umask across ordinary copies, and a hash that depends on the
 * copying machine is a false MISMATCH on a valid pack — the worst failure this
 * mechanism has (see the header). Empty directories are refused for the same
 * reason symlinks are: they exist without contributing anything the seal covers.
 * No pack was ever sealed under wb-canon-1 in this project (zero manifests), so
 * this is a rename, not a migration.
 */
export const HASH_METHOD = "wb-canon-2" as const;

/**
 * Files a SEALED pack must contain. R2P's pack shape (PRD §22.5) carried the
 * answer key as plaintext `expected.json`; since security review T1 (executed:
 * a pre-opened file descriptor read the plaintext straight through the mode-000
 * lockdown) the sealed shape holds only its CIPHERTEXT, `expected.json.enc`
 * (see keybox.ts). The plaintext exists at authoring time and seal.ts deletes
 * it in the act of sealing. An imported R2P pack must be RE-SEALED through
 * seal.ts; it cannot be verified as-is under this shape.
 */
export const PACK_FILES = ["cases.yaml", "expected.json.enc", "README.md"] as const;

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
      if (st.isDirectory()) {
        if (readdirSync(full).length === 0) {
          throw new Error(
            `pack refused: "${relative(dir, full).split(sep).join("/")}/" is an empty directory.\n` +
            `It exists without contributing anything the seal covers — a case could still\n` +
            `observe it (test -d), so its presence would be unpinned behaviour.`,
          );
        }
        walk(full);
      } else if (st.isFile()) {
        out.push(relative(dir, full).split(sep).join("/"));
      } else {
        // S6 (security re-review, EXECUTED): a FIFO in a pack left the digest
        // byte-identical — it fell off this if/else and contributed nothing,
        // while a case could still observe it (`test -p`). The same reasoning
        // that refuses empty directories applies to every non-regular file.
        throw new Error(
          `pack refused: "${relative(dir, full).split(sep).join("/")}" is not a regular file.\n` +
          `FIFOs, sockets and device nodes exist without contributing anything the seal\n` +
          `covers, so their presence would be unpinned behaviour.`,
        );
      }
    }
  };
  walk(dir);
  // Sort on the POSIX-joined name, not on directory-walk order — the walk order
  // depends on the filesystem, and a hash that depends on the filesystem is the
  // whole class of bug this file exists to remove.
  return out.sort((a, b) => (a < b ? -1 : a > b ? 1 : 0));
}

/**
 * wb-canon-2: sha256 over `<relpath>\0<x|->\0<sha256(content)>\n` per file, paths
 * sorted. The middle byte is "x" when the owner-execute bit is set, "-" otherwise.
 *
 * Content is hashed per file rather than concatenated, so a byte moving across a
 * file boundary cannot leave the stream unchanged. The NUL separates the fields
 * because NUL cannot occur in a POSIX path, so no path can be crafted to
 * impersonate a path-plus-digest pair. The digest is fixed-width hex, so the
 * framing stays injective for a distinct sorted path set — hand-traced in
 * security review (F5): a collision between two different packs reduces to a
 * sha256 collision.
 */
export function canonicalPackHash(dir: string): { digest: string; files: string[] } {
  const files = listPackFiles(dir);
  const h = createHash("sha256");
  for (const rel of files) {
    const full = join(dir, rel);
    const exec = (lstatSync(full).mode & 0o100) !== 0;
    h.update(Buffer.from(rel, "utf8"));
    h.update(Buffer.from([0x00]));
    h.update(Buffer.from(exec ? "x" : "-", "utf8"));
    h.update(Buffer.from([0x00]));
    h.update(Buffer.from(sha256Hex(readFileSync(full)), "utf8"));
    h.update(Buffer.from([0x0a]));
  }
  return { digest: h.digest("hex"), files };
}

/**
 * The expected-results digest: sha256 of `expected.json.enc` alone (the
 * CIPHERTEXT — the plaintext never exists on disk in a sealed pack; T1).
 *
 * Kept as a SECOND published hash even though it is inconvenient. Publishing only
 * the pack hash would let a custodian silently swap the answer key while keeping
 * the questions, and the point of the seal is that neither moves (PRD §22.6).
 *
 * HISTORY: this used to be byte-identical to `shasum -a 256 expected.json` for
 * R2P import compatibility. That property died with the plaintext (T1). It is
 * still `shasum -a 256 expected.json.enc`, so a hand check remains one command.
 */
export function expectedResultsHash(dir: string): string {
  return sha256Hex(readFileSync(join(dir, "expected.json.enc")));
}
