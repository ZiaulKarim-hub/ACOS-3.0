// git-manager — "what lives in this repo?"
//
// The user's question is about skills / systems / software, not about repos.
// A single repo (ACOS 3.0) hosts dozens of skills, so a repo row is only useful
// when it says what it contains. This module answers that cheaply: directory
// listings only, no deep walks, no file reads beyond package.json.

import { existsSync, readdirSync, readFileSync, realpathSync, statSync } from "node:fs";
import { basename, dirname, join } from "node:path";
import type { Inventory, LinkedSkill } from "./types.ts";

const PROJECT_MARKERS = [
  "package.json",
  "Cargo.toml",
  "pyproject.toml",
  "go.mod",
  "index.html",
  "SKILL.md",
  "README.md",
  "CLAUDE.md",
];

function safeList(dir: string): string[] {
  try {
    return readdirSync(dir, { withFileTypes: true })
      .filter((e) => e.isDirectory())
      .map((e) => e.name)
      .sort();
  } catch {
    return [];
  }
}

function safeListFiles(dir: string): string[] {
  try {
    return readdirSync(dir, { withFileTypes: true })
      .filter((e) => e.isFile())
      .map((e) => e.name)
      .sort();
  } catch {
    return [];
  }
}

/**
 * Skills live at <repo>/.claude/skills/* or, for ~/.claude itself, at <repo>/skills/*.
 *
 * A symlinked skill folder is reported separately: the skill is INSTALLED here but
 * HOSTED somewhere else, and that distinction is the whole point of the report.
 */
function findSkills(repo: string): { own: string[]; linked: LinkedSkill[] } {
  for (const rel of [join(".claude", "skills"), "skills"]) {
    const dir = join(repo, rel);
    if (!existsSync(dir)) continue;
    // If the skills folder is ITSELF a repo, its contents belong to that repo's
    // own row — counting them here would report protected work as at-risk.
    // This is exactly the ~/.claude case: ~/.claude is untracked, but
    // ~/.claude/skills is a tracked repo of its own.
    if (existsSync(join(dir, ".git"))) continue;

    let entries: import("node:fs").Dirent[] = [];
    try {
      entries = readdirSync(dir, { withFileTypes: true });
    } catch {
      continue;
    }

    const own: string[] = [];
    const linked: LinkedSkill[] = [];
    for (const e of entries) {
      const p = join(dir, e.name);
      if (e.isSymbolicLink()) {
        let target = "";
        try {
          target = realpathSync(p);
        } catch {
          linked.push({ name: e.name, target: "(broken link)", hostRepo: null, hostName: null });
          continue;
        }
        if (!existsSync(join(target, "SKILL.md"))) continue;
        const hostRepo = repoRootOf(target);
        linked.push({
          name: e.name,
          target,
          hostRepo,
          hostName: hostRepo ? basename(hostRepo) : null,
        });
        continue;
      }
      if (e.isDirectory() && existsSync(join(p, "SKILL.md"))) own.push(e.name);
    }
    if (own.length || linked.length) return { own: own.sort(), linked };
  }
  return { own: [], linked: [] };
}

/**
 * Walk upward from a path to the repo that tracks it, or null if nothing does.
 * This is what turns "24 skills are symlinked in" into "24 skills are hosted by
 * ACOS 3.0" — which is the actual question: where does this skill LIVE?
 */
export function repoRootOf(start: string): string | null {
  let dir = start;
  for (let i = 0; i < 40; i++) {
    if (existsSync(join(dir, ".git"))) return dir;
    const up = dirname(dir);
    if (up === dir) return null;
    dir = up;
  }
  return null;
}

/** Group linked skills by the repo that hosts them, biggest group first. */
export function groupByHost(linked: LinkedSkill[]): { host: string; names: string[] }[] {
  const map = new Map<string, string[]>();
  for (const l of linked) {
    const key = l.hostName ?? (l.hostRepo ? l.hostRepo : "not in any repo");
    (map.get(key) ?? map.set(key, []).get(key)!).push(l.name);
  }
  return [...map.entries()]
    .map(([host, names]) => ({ host, names: names.sort() }))
    .sort((a, b) => b.names.length - a.names.length || a.host.localeCompare(b.host));
}

function findAgents(repo: string): string[] {
  for (const rel of [join(".claude", "agents"), "agents"]) {
    const dir = join(repo, rel);
    if (!existsSync(dir)) continue;
    const names = safeListFiles(dir)
      .filter((n) => n.endsWith(".md"))
      .map((n) => n.replace(/\.md$/, ""));
    if (names.length) return names;
  }
  return [];
}

function countScripts(repo: string): number {
  let total = 0;
  for (const rel of [join(".claude", "scripts"), "scripts", join(".claude", "hooks"), "hooks"]) {
    const dir = join(repo, rel);
    if (!existsSync(dir)) continue;
    try {
      total += readdirSync(dir, { withFileTypes: true }).filter((e) => e.isFile()).length;
    } catch {
      /* ignore */
    }
  }
  return total;
}

const NOT_A_SUBPROJECT = new Set([
  "node_modules",
  "dist",
  "build",
  "out",
  "target",
  "venv",
  ".venv",
  "__pycache__",
  "coverage",
  ".cache",
]);

/**
 * Top-level folders that look like a distinct product living inside this repo.
 * A folder qualifies if it carries a project marker file, holds any markdown, or
 * simply has real content (3+ entries). Deliberately generous: the user's question
 * is "what lives in this repo", and under-reporting hides work.
 */
function findSubProjects(repo: string): string[] {
  const out: string[] = [];
  for (const name of safeList(repo)) {
    if (name.startsWith(".")) continue;
    if (NOT_A_SUBPROJECT.has(name)) continue;
    const child = join(repo, name);
    // A nested .git makes it a repo of its own — the scanner reports it separately.
    if (existsSync(join(child, ".git"))) continue;
    if (PROJECT_MARKERS.some((m) => existsSync(join(child, m)))) {
      out.push(name);
      continue;
    }
    let entries: string[] = [];
    try {
      entries = readdirSync(child).filter((n) => n !== ".DS_Store");
    } catch {
      continue;
    }
    if (entries.some((n) => n.endsWith(".md")) || entries.length >= 3) out.push(name);
  }
  return out;
}

function packageName(repo: string): string | null {
  const p = join(repo, "package.json");
  if (!existsSync(p)) return null;
  try {
    const j = JSON.parse(readFileSync(p, "utf8"));
    return typeof j.name === "string" ? j.name : null;
  } catch {
    return null;
  }
}

export function inventory(repo: string): Inventory {
  const { own: skills, linked: linkedSkills } = findSkills(repo);
  const agents = findAgents(repo);
  const scriptCount = countScripts(repo);
  const subProjects = findSubProjects(repo);
  const pkg = packageName(repo);

  const parts: string[] = [];
  if (skills.length) parts.push(`${skills.length} skill${skills.length === 1 ? "" : "s"}`);
  if (agents.length) parts.push(`${agents.length} agent${agents.length === 1 ? "" : "s"}`);
  if (scriptCount) parts.push(`${scriptCount} script${scriptCount === 1 ? "" : "s"}`);
  if (subProjects.length)
    parts.push(`${subProjects.length} sub-project${subProjects.length === 1 ? "" : "s"}`);
  if (linkedSkills.length) {
    const hosts = groupByHost(linkedSkills);
    parts.push(
      `${linkedSkills.length} linked in from ${hosts
        .slice(0, 2)
        .map((h) => h.host)
        .join(", ")}${hosts.length > 2 ? ` +${hosts.length - 2} more` : ""}`,
    );
  }
  if (!parts.length && pkg) parts.push(`package ${pkg}`);
  if (!parts.length) {
    // Nothing recognised. Say how much is here anyway — "unknown" is not a
    // reason to imply the folder is empty.
    try {
      const n = readdirSync(repo).filter((x) => x !== ".git" && x !== ".DS_Store").length;
      if (n) parts.push(`${n} top-level item${n === 1 ? "" : "s"}`);
    } catch {
      /* ignore */
    }
  }

  // How much irreplaceable work sits here. Used to order rows that share a
  // state: an untracked folder holding 87 skills matters more than an untracked
  // folder holding build output, even though both read "NOT A REPO".
  const weight =
    skills.length * 4 + agents.length * 3 + subProjects.length * 2 + Math.min(scriptCount, 60);

  return {
    skills,
    linkedSkills,
    agents,
    scriptCount,
    subProjects,
    packageName: pkg,
    weight,
    summary: parts.length ? parts.join(" · ") : "—",
  };
}

/**
 * A build or project-definition file. Its presence is strong evidence that a
 * folder is software someone maintains, not a folder of deliverables.
 * `.gitignore` is deliberately NOT here — it is often leftover clutter and it
 * would make a whole container folder look like one project.
 */
const CODE_MARKERS = new Set([
  "package.json",
  "Cargo.toml",
  "pyproject.toml",
  "requirements.txt",
  "go.mod",
  "tsconfig.json",
  "deno.json",
  "bun.lockb",
  "Makefile",
  "Gemfile",
  "pom.xml",
  "build.gradle",
  "SKILL.md",
  "CLAUDE.md",
]);

/** Source files. HTML/CSS/Markdown are excluded: here they are usually output. */
const SCRIPT_EXT =
  /\.(ts|tsx|js|jsx|mjs|cjs|py|rs|sh|bash|zsh|go|rb|java|kt|swift|c|h|cpp|cs|php|vue|svelte|sql)$/i;

const CODE_SUBDIRS = ["src", "scripts", "lib", "app", "bin", "hooks", "skills", "agents"];

/** How many loose source files make a folder a project in its own right. */
const LOOSE_FILE_THRESHOLD = 5;

export type ProjectKind = "strong" | "weak" | "none";

/**
 * True when a folder looks like SOFTWARE, not documents.
 *
 * This is the filter that keeps the report useful. Without it, every OKOA deal
 * folder full of PDFs is reported as "not tracked by git" — technically true,
 * completely useless. A folder qualifies on a build/config marker, on code files
 * at its top level, or on code files one level down in a conventional subfolder.
 */
export function projectKind(dir: string): ProjectKind {
  try {
    const entries = readdirSync(dir, { withFileTypes: true });
    if (!entries.length) return "none";

    const files = entries.filter((e) => e.isFile()).map((e) => e.name);
    if (files.some((n) => CODE_MARKERS.has(n))) return "strong";

    const scripts = files.filter((n) => SCRIPT_EXT.test(n)).length;
    if (scripts >= LOOSE_FILE_THRESHOLD) return "strong";

    for (const sub of CODE_SUBDIRS) {
      if (!entries.some((e) => e.isDirectory() && e.name === sub)) continue;
      try {
        const inner = readdirSync(join(dir, sub), { withFileTypes: true });
        if (inner.filter((e) => e.isFile() && SCRIPT_EXT.test(e.name)).length >= 3) return "strong";
        if (inner.some((e) => e.isFile() && CODE_MARKERS.has(e.name))) return "strong";
        // A skills/agents folder full of SKILL.md files counts.
        if (inner.some((e) => e.isDirectory() && existsSync(join(dir, sub, e.name, "SKILL.md"))))
          return "strong";
      } catch {
        /* ignore */
      }
    }

    // A handful of scripts sitting next to deliverables: real work, but almost
    // always a document folder with a render script. Counted, not listed,
    // unless the caller asks for the loose set.
    return scripts > 0 ? "weak" : "none";
  } catch {
    return "none";
  }
}

export function isDir(p: string): boolean {
  try {
    return statSync(p).isDirectory();
  } catch {
    return false;
  }
}
