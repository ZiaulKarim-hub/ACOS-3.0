import { customAlphabet } from "nanoid";
/**
 * A third-party runtime dependency, so Vite must lay out a VENDOR chunk
 * alongside first-party code. Cross-package module ordering is the most
 * common source of real bundler nondeterminism, and the previous fixture
 * had no third-party runtime code at all.
 *
 * The alphabet and size are fixed so the OUTPUT is deterministic too --
 * this measures the build, not the randomness.
 */
export const makeId = customAlphabet("abcdef0123456789", 12);
export const SEEDED = "fixed-not-random";
