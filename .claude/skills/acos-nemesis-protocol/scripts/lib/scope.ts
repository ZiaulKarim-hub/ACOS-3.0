/**
 * scope.ts — what Nemesis judges and what it never touches (R-002, R-031, R-044).
 *
 * Paths are matched RELATIVE to the project root, forward slashes. `**` matches any
 * depth (including none); `*` matches within one segment.
 */
import * as fs from "node:fs";
import * as path from "node:path";

/** ACOS restricted files: never read (the reviewer-rules directory) / never written (agents). */
export const RESTRICTED: readonly string[] = ["review-rules/**", "review-rules.yaml", ".claude/agents/**"];

/**
 * Always excluded. The eternity protocol's own files are here on purpose (D-17): Nemesis
 * never stands down during the eternity window, and it also never judges the handoff
 * machinery, so a handoff can never be blocked by it.
 */
export const DEFAULT_EXCLUDES: readonly string[] = [
  ".nemesis/**",
  ".worktree/**",
  "node_modules/**",
  "**/node_modules/**",
  ".git/**",
  "memory/handoffs/**",
  "**/acos-token-monitor/**",
  ".claude/scripts/eternity*",
  ".claude/scripts/_autopilot_eternity.py",
  ".acos/state/**",
  ...RESTRICTED,
];

export interface ScopeConfig {
  source_globs?: string[];
  exclude_globs?: string[];
}

export function globToRegex(glob: string): RegExp {
  let re = "";
  for (let i = 0; i < glob.length; i++) {
    const c = glob[i]!;
    if (c === "*") {
      if (glob[i + 1] === "*") {
        // `**/` → any number of segments (including zero); trailing `**` → anything
        if (glob[i + 2] === "/") { re += "(?:.*/)?"; i += 2; } else { re += ".*"; i += 1; }
      } else re += "[^/]*";
    } else if (c === "?") re += "[^/]";
    else if ("\\^$+.()|{}[]".includes(c)) re += "\\" + c;
    else re += c;
  }
  return new RegExp(`^${re}$`);
}

/** Resolve symlinks (e.g. macOS `/var` → `/private/var`); a path that does not exist yet resolves its deepest existing ancestor. */
export function canonical(p: string): string {
  const abs = path.resolve(p);
  try { return fs.realpathSync.native(abs); } catch { /* not on disk yet */ }
  const parent = path.dirname(abs);
  if (parent === abs) return abs;
  return path.join(canonical(parent), path.basename(abs));
}

export function toRel(root: string, p: string): string {
  const r = canonical(root);
  const abs = canonical(path.isAbsolute(p) ? p : path.resolve(root, p));
  return path.relative(r, abs).split(path.sep).join("/");
}

/** Is this path judged? Excluded rules win; then source globs (default: everything). */
export function isInScope(root: string, p: string, cfg: ScopeConfig = {}): { inScope: boolean; rule?: string; rel: string } {
  const rel = toRel(root, p);
  if (rel.startsWith("../") || rel === "..") return { inScope: false, rule: "outside project", rel };
  const excludes = [...DEFAULT_EXCLUDES, ...(cfg.exclude_globs ?? [])];
  for (const g of excludes) if (globToRegex(g).test(rel)) return { inScope: false, rule: g, rel };
  const sources = cfg.source_globs?.length ? cfg.source_globs : ["**"];
  for (const g of sources) if (globToRegex(g).test(rel)) return { inScope: true, rel };
  return { inScope: false, rule: "not in source_globs", rel };
}

/** Files that look like code/config/SQL — used to skip binaries and assets in tree scans. */
export const CODE_EXT = new Set([
  ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".json", ".yaml", ".yml", ".toml", ".sql", ".py", ".rs", ".go",
  ".rb", ".sh", ".zsh", ".bash", ".env", ".html", ".css", ".md", ".txt", ".prisma", ".graphql", ".tf", ".ini", ".cfg",
]);

export function looksLikeCode(rel: string): boolean {
  const ext = path.extname(rel).toLowerCase();
  if (CODE_EXT.has(ext)) return true;
  const base = path.basename(rel);
  return base === "Dockerfile" || base === "Makefile" || base.startsWith(".env");
}
