import { ranked, LABEL } from "./b.ts";
export function describe(): string {
  return LABEL + ":" + ranked().join("|");
}
export const EXTRA = Array.from({ length: 40 }, (_, i) => `token-${i.toString(36)}`);
