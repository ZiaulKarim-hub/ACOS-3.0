/**
 * keybox.ts — the answer key is CIPHERTEXT on disk, always (security review T1).
 *
 * WHY, from the executed defeat: v3 locked the pack at mode 000 and tripwired
 * ctime, on the theory that "to read anything a case must chmod something".
 * The reviewer proved the theory false twice in one finding:
 *   1. POSIX checks permission at open(2), not read(2). A file descriptor
 *      opened while the pack was mode 644 keeps reading after the file drops
 *      to 000, and nothing on the inode moves. EXECUTED: a background daemon
 *      held a pre-opened fd and dumped the whole answer key mid-run; the
 *      sealed record read post_run_pack_untouched: true.
 *   2. The pack is mode 644 from the moment the custodian writes it until the
 *      instant of lockdown, so a lingering poller from an EARLIER reveal
 *      harvests every FUTURE pack without touching this run at all.
 *
 * Both attacks read plaintext that had no business being plaintext. So
 * expected.json never ships as plaintext: seal.ts encrypts it in place
 * (AES-256-GCM) and prints the key ONCE, to the custodian, who stores it
 * OUTSIDE the repository. reveal.ts takes the key on stdin — not argv, not
 * env: on macOS `ps -E` shows both for same-user processes — and decrypts in
 * memory only. A pre-opened descriptor now yields ciphertext; a poller
 * harvests ciphertext; the mode-000 lockdown and the ctime tripwire become
 * defence in depth instead of the whole defence.
 *
 * GCM rather than CBC/CTR because the tag is an integrity check: a wrong key
 * or a bit-flipped ciphertext THROWS instead of decrypting to garbage that
 * JSON.parse might half-accept (measured: wrong key throws on this bun).
 *
 * STATED LIMIT, same boundary as ever: the key exists in reveal's process
 * memory during the run, and wherever the custodian keeps it. A same-user
 * debugger, or an insider who finds the custodian's copy, still wins. That is
 * OS-sandbox territory; this closes the on-disk-plaintext class, not that one.
 */

import { createCipheriv, createDecipheriv, randomBytes } from "node:crypto";

/** The sealed answer key's filename inside a pack. */
export const ENC_NAME = "expected.json.enc";
/** The authoring-time plaintext name seal.ts consumes and DELETES. */
export const PLAIN_NAME = "expected.json";
export const KEY_HEX = /^[0-9a-f]{64}$/;

const MAGIC = Buffer.from("WBSEAL1\0");
const IV_LEN = 12, TAG_LEN = 16;

export function newKeyHex(): string {
  return randomBytes(32).toString("hex");
}

/** magic(8) | iv(12) | tag(16) | ciphertext. One format, no negotiation. */
export function encryptExpected(plaintext: Buffer, keyHex: string): Buffer {
  if (!KEY_HEX.test(keyHex)) throw new Error("keybox: key must be 64 lowercase hex characters");
  const iv = randomBytes(IV_LEN);
  const c = createCipheriv("aes-256-gcm", Buffer.from(keyHex, "hex"), iv);
  const ct = Buffer.concat([c.update(plaintext), c.final()]);
  return Buffer.concat([MAGIC, iv, c.getAuthTag(), ct]);
}

/** Throws on wrong key, truncation, or any modified byte — that is the point. */
export function decryptExpected(blob: Buffer, keyHex: string): Buffer {
  if (!KEY_HEX.test(keyHex)) throw new Error("keybox: key must be 64 lowercase hex characters");
  if (blob.length < MAGIC.length + IV_LEN + TAG_LEN || !blob.subarray(0, MAGIC.length).equals(MAGIC)) {
    throw new Error(`keybox: not a ${ENC_NAME} blob (bad magic or truncated)`);
  }
  const iv = blob.subarray(MAGIC.length, MAGIC.length + IV_LEN);
  const tag = blob.subarray(MAGIC.length + IV_LEN, MAGIC.length + IV_LEN + TAG_LEN);
  const d = createDecipheriv("aes-256-gcm", Buffer.from(keyHex, "hex"), iv);
  d.setAuthTag(tag);
  return Buffer.concat([d.update(blob.subarray(MAGIC.length + IV_LEN + TAG_LEN)), d.final()]);
}
