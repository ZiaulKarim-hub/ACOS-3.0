import { PALETTE, contrast } from "./a.ts";
/** Sorted darkest-first, so the ordering is stable across runs by construction. */
export function ranked(): string[] {
  return [...PALETTE].sort((x, y) => contrast(x) - contrast(y) || x.localeCompare(y));
}
export const LABEL = "ranked-by-contrast";
