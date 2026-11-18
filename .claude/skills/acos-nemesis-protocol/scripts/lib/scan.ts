/**
 * scan.ts — the S3 post-change scan (R-014, R-015). Mechanical, whole-repo, after EVERY
 * change. Each check is pass | fail | skipped, and `skipped` is NEVER clean (a `skip` is
 * not a `pass`). Built-ins cannot be removed by config; `extra_checks` only add.
 */
import * as fs from "node:fs";
import * as path from "node:path";
import { spawnSync } from "node:child_process";
import { type Config, P, writeJson, nowIso, sha256 } from "./state";
import { looksLikeCode, isInScope } from "./scope";

export type CheckKind = "typecheck" | "lint" | "test" | "secrets" | "deps" | "policy" | "data" | "extra";
export type CheckStatus = "pass" | "fail" | "skipped";
export interface Check { id: string; kind: CheckKind; cmd?: string; args?: string[]; builtin?: "secrets" | "policy" | "data"; note?: string }
export interface CheckResult { id: string; kind: CheckKind; status: CheckStatus; ms: number; output: string; findings?: ScanFinding[] }
export interface ScanFinding { severity: "critical" | "high" | "medium" | "low"; lens: "PSC" | "PFC"; checklist: string; where: string; what: string; fix_hint?: string }
export interface ScanResult {
  id: string; at: string; task?: string; trigger: string; changed: string[];
  checks: CheckResult[]; clean: boolean; tests_pass: boolean; repro_results: Record<string, boolean>;
  /** R-060: why each reproduction test was or was not credited, so a refusal is actionable. */
  repro_reasons?: Record<string, string>;
}

const CHECK_TIMEOUT_MS = 20 * 60 * 1000; // generous: a slow suite is accepted, a skipped one is not

/**
 * A dependency audit gets its OWN, much shorter timeout, and the retries get a budget.
 *
 * FUN-135. The retry added for SEC-38 inherited `CHECK_TIMEOUT_MS`, which is twenty
 * minutes, because a slow TEST SUITE has to be allowed to finish. An audit is not a test
 * suite — it is one request to a registry, measured at **151 ms** on this machine on
 * 2026-11-18 — so three attempts at twenty minutes each put a worst case of ONE HOUR on a
 * single check, with nothing bounding it. A scan that hangs for an hour is a scan nobody
 * waits for, which is how a gate quietly stops being run.
 *
 * Two minutes per attempt is roughly 800× the measured time, so a genuinely slow registry
 * still finishes. The budget then caps the whole sequence: once it is spent, no further
 * attempt STARTS. The honest worst case is the budget plus one attempt already in flight,
 * about seven minutes, and it is bounded rather than merely unlikely.
 */
const DEPS_TIMEOUT_MS = 2 * 60 * 1000;
const DEPS_RETRY_BUDGET_MS = 5 * 60 * 1000;

function has(root: string, rel: string): boolean { return fs.existsSync(path.join(root, rel)); }
function which(bin: string): boolean { return spawnSync("sh", ["-lc", `command -v ${bin}`], { encoding: "utf8" }).status === 0; }

/** R-015: detect the project's own checks. Order: package.json scripts → tsconfig → linters → runners → cargo → python. */
export function detectToolchain(root: string, cfg?: Config): Check[] {
  const checks: Check[] = [];
  const pkg = has(root, "package.json") ? JSON.parse(fs.readFileSync(path.join(root, "package.json"), "utf8")) as { scripts?: Record<string, string> } : null;
  const scripts = pkg?.scripts ?? {};
  const runner = has(root, "bun.lock") || has(root, "bun.lockb") ? "bun" : has(root, "pnpm-lock.yaml") ? "pnpm" : has(root, "yarn.lock") ? "yarn" : "npm";
  const runScript = (name: string) => (runner === "npm" ? ["npm", ["run", name, "--silent"]] : [runner, ["run", name]]) as [string, string[]];

  // type-check
  if (scripts.typecheck) { const [c, a] = runScript("typecheck"); checks.push({ id: "typecheck", kind: "typecheck", cmd: c, args: a }); }
  else if (has(root, "tsconfig.json")) checks.push({ id: "typecheck", kind: "typecheck", cmd: runner === "bun" ? "bunx" : "npx", args: ["tsc", "--noEmit", "-p", "tsconfig.json"] });
  else if (has(root, "Cargo.toml")) checks.push({ id: "typecheck", kind: "typecheck", cmd: "cargo", args: ["check", "--quiet"] });
  else checks.push({ id: "typecheck", kind: "typecheck", note: "no tsconfig/Cargo.toml/typecheck script" });

  // lint
  if (scripts.lint) { const [c, a] = runScript("lint"); checks.push({ id: "lint", kind: "lint", cmd: c, args: a }); }
  else if (has(root, "biome.json") || has(root, "biome.jsonc")) checks.push({ id: "lint", kind: "lint", cmd: runner === "bun" ? "bunx" : "npx", args: ["biome", "check", "."] });
  else if (fs.readdirSync(root).some((f) => /^(\.eslintrc|eslint\.config\.)/.test(f))) checks.push({ id: "lint", kind: "lint", cmd: runner === "bun" ? "bunx" : "npx", args: ["eslint", "."] });
  else if (has(root, "Cargo.toml")) checks.push({ id: "lint", kind: "lint", cmd: "cargo", args: ["clippy", "--quiet", "--", "-D", "warnings"] });
  else if (has(root, "pyproject.toml") && which("ruff")) checks.push({ id: "lint", kind: "lint", cmd: "ruff", args: ["check", "."] });
  else checks.push({ id: "lint", kind: "lint", note: "no linter detected" });

  // tests
  if (scripts.test && !/no test specified/.test(scripts.test)) { const [c, a] = runScript("test"); checks.push({ id: "test", kind: "test", cmd: c, args: a }); }
  else if (has(root, "vitest.config.ts") || has(root, "vitest.config.js")) checks.push({ id: "test", kind: "test", cmd: runner === "bun" ? "bunx" : "npx", args: ["vitest", "run"] });
  else if (has(root, "jest.config.js") || has(root, "jest.config.ts")) checks.push({ id: "test", kind: "test", cmd: "npx", args: ["jest", "--ci"] });
  else if (runner === "bun" && hasTestFiles(root)) checks.push({ id: "test", kind: "test", cmd: "bun", args: ["test"] });
  else if (has(root, "Cargo.toml")) checks.push({ id: "test", kind: "test", cmd: "cargo", args: ["test", "--quiet"] });
  else if (has(root, "pyproject.toml") && which("pytest")) checks.push({ id: "test", kind: "test", cmd: "pytest", args: ["-q"] });
  else checks.push({ id: "test", kind: "test", note: "no test runner detected — a project with no tests cannot be clean" });

  // dependency audit (a project may name its own: scripts.audit)
  if (scripts.audit) { const [c, a] = runScript("audit"); checks.push({ id: "deps", kind: "deps", cmd: c, args: a }); }
  // `--json` on the bun path is SEC-43's repair, not a formatting preference: it makes the
  // audit answer in a shape that can be parsed, so "did this run?" is decided by the tool's
  // own structured result instead of by searching its prose for words. Measured on bun
  // 1.3.9 — clean: exit 0, stdout `{}`; findings: exit 1, stdout an object keyed by package;
  // registry unreachable: exit 1, stdout ZERO bytes. The npm path is left alone because that
  // three-way behaviour has not been measured there, and the classifier's prose fallback
  // covers it. `renderAuditJson` puts the readable form back into the ledger.
  else if (pkg) checks.push({ id: "deps", kind: "deps", cmd: runner === "bun" ? "bun" : "npm", args: runner === "bun" ? ["audit", "--json"] : ["audit", "--audit-level=high"] });
  else if (has(root, "Cargo.toml")) checks.push(which("cargo-audit") ? { id: "deps", kind: "deps", cmd: "cargo", args: ["audit", "-q"] } : { id: "deps", kind: "deps", note: "cargo-audit not installed" });
  else if (has(root, "pyproject.toml") || has(root, "requirements.txt")) checks.push(which("pip-audit") ? { id: "deps", kind: "deps", cmd: "pip-audit", args: ["-q"] } : { id: "deps", kind: "deps", note: "pip-audit not installed" });
  else checks.push({ id: "deps", kind: "deps", note: "no dependency manifest" });

  // built-ins (always)
  checks.push({ id: "secrets", kind: "secrets", builtin: "secrets" });
  if (which("gitleaks")) checks.push({ id: "gitleaks", kind: "secrets", cmd: "gitleaks", args: ["detect", "--no-git", "--source", ".", "--no-banner", "--redact", "--exit-code", "1"] });
  checks.push({ id: "policy", kind: "policy", builtin: "policy" });
  checks.push({ id: "data", kind: "data", builtin: "data" });

  // additive extras — a config can only ADD
  for (const e of cfg?.extra_checks ?? []) {
    if (checks.some((c) => c.id === e.id)) { console.error(`nemesis: extra_check "${e.id}" collides with a built-in and is ignored (built-ins cannot be replaced)`); continue; }
    checks.push({ id: e.id, kind: "extra", cmd: e.cmd, args: e.args });
  }
  return checks;
}

function hasTestFiles(root: string): boolean {
  const out = spawnSync("sh", ["-lc", `find . -path ./node_modules -prune -o -path ./.git -prune -o \\( -name "*.test.ts" -o -name "*.spec.ts" -o -name "*.test.js" -o -name "*_test.ts" \\) -print -quit`], { cwd: root, encoding: "utf8" });
  return out.stdout.trim().length > 0;
}

// ── Built-in scanners ───────────────────────────────────────────────────────

/**
 * D-65: THE PLACEHOLDER EXCUSE JUDGED THE LINE, NOT THE MATCH, AND SWALLOWED REAL SECRETS.
 *
 * The excuse used to be one line-level test: `!/example|placeholder|dummy|xxxx|<.*>/i.test(l)`.
 * That last alternative, `<.*>`, exempts ANY line holding a `<` before a `>` — which is every
 * TypeScript generic. Measured 2026-11-10 by reading the real table and the real excuse out of
 * this file and running lines through them:
 *
 *   (AKIA·KEY below stands for a real-shaped key id: AKIA and sixteen more. It is written
 *   with a separator ON PURPOSE — a full one here is a finding in this very file, which is
 *   how the scanner reported its own documentation when scope widened on 2026-11-18.)
 *
 *   const k = "AKIA·KEY";                              -> reported   (correct)
 *   const m: Map<string, string> = { k: "AKIA·KEY" };  -> NOT reported (the hole)
 *   const f = (x: Array<number>) => "AKIA·KEY";        -> NOT reported (the hole)
 *
 * So a live AWS key sitting on any line that also carried a generic was invisible to the secret
 * scan, in a TypeScript codebase. Found because the website workspace's review re-opened a
 * finding and named this excuse; the scanner is this skill's code, so the fix is here.
 *
 * The two intents were always different and are now separated. A line that ANNOUNCES itself as
 * fake ("example", "placeholder", "dummy", "xxxx") still excuses the whole line — that is about
 * the line's purpose. An angle-bracket placeholder is about the VALUE: `password: "<your-pass>"`
 * is a template, and that judgement belongs on the matched text, never on its neighbours. Same
 * substitution as D-60: a property of the container is not a property of the thing inside it.
 */
const PLACEHOLDER_WORDS = /example|placeholder|dummy|xxxx/i;
const ANGLE_PLACEHOLDER = /<[^<>]{1,64}>/;

const SECRET_PATTERNS: { re: RegExp; what: string }[] = [
  { re: /AKIA[0-9A-Z]{16}/, what: "AWS access key id" },
  { re: /-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----/, what: "private key block" },
  { re: /sk-(?:live|test|proj)-[A-Za-z0-9_-]{16,}/, what: "secret API key (sk-…)" },
  { re: /ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{22,}/, what: "GitHub token" },
  { re: /xox[baprs]-[A-Za-z0-9-]{10,}/, what: "Slack token" },
  { re: /eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}/, what: "JWT literal" },
  { re: /(?:password|passwd|secret|api[_-]?key|token)\s*[:=]\s*["'][^"'\s]{8,}["']/i, what: "hard-coded credential assignment" },
  { re: /postgres(?:ql)?:\/\/[^:\s]+:[^@\s]+@/, what: "database URL with embedded password" },
];

const SENSITIVE_DATA_PATTERNS: { re: RegExp; what: string }[] = [
  { re: /\b\d{3}-\d{2}-\d{4}\b/, what: "SSN-shaped value" },
  { re: /\b(?:4\d{3}|5[1-5]\d{2}|3[47]\d{2}|6011)[ -]?\d{4}[ -]?\d{4}[ -]?\d{4}\b/, what: "card-number-shaped value" },
  { re: /\bBearer\s+[A-Za-z0-9._-]{20,}/, what: "bearer token literal" },
  { re: /\b\d{2}-\d{7}\b/, what: "TIN/EIN-shaped value" },
  { re: /\b(?:routing|aba|account|acct|iban)[\s_-]*(?:number|no|num|#)?\s*[:=]\s*["']?\d{8,17}\b/i, what: "bank account/routing-shaped value" },
  { re: /\b[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7}[A-Z0-9]{1,16}\b/, what: "IBAN-shaped value" },
];
/** Error-message constructs: a sensitive value inside one leaks through the response or the log. */
const ERROR_LINE = /\b(throw\s+new\s+\w*Error|new\s+\w*Error\s*\(|raise\s+\w+(Error|Exception)|panic!\(|errorMessage|error_message|err(?:or)?_?msg|message\s*[:=]\s*[`"'])/;
const LOG_LINE = /\b(console\.(log|error|warn|info|debug)|logger\.|log\.(info|error|warn|debug)|print\(|println!|eprintln!|tracing::)/;

function listScanFiles(root: string, cfg: Config, changed: string[]): string[] {
  const files = new Set<string>(changed.filter((f) => fs.existsSync(path.join(root, f))));
  const walk = (dir: string, depth: number) => {
    if (depth > 12) return;
    let ents: fs.Dirent[]; try { ents = fs.readdirSync(dir, { withFileTypes: true }); } catch { return; }
    for (const e of ents) {
      if (e.name === "node_modules" || e.name === ".git" || e.name === ".nemesis" || e.name === ".worktree") continue;
      const abs = path.join(dir, e.name);
      const rel = path.relative(root, abs).split(path.sep).join("/");
      if (e.isDirectory()) walk(abs, depth + 1);
      else if (e.isFile() && looksLikeCode(rel) && isInScope(root, rel, cfg).inScope) {
        try { if (fs.statSync(abs).size <= 1_000_000) files.add(rel); } catch { /* skip */ }
      }
    }
  };
  walk(root, 0);
  return [...files];
}

function runBuiltin(kind: "secrets" | "policy" | "data", root: string, cfg: Config, changed: string[]): CheckResult {
  const t0 = Date.now();
  const findings: ScanFinding[] = [];
  const files = listScanFiles(root, cfg, changed);
  for (const rel of files) {
    let text: string; try { text = fs.readFileSync(path.join(root, rel), "utf8"); } catch { continue; }
    const lines = text.split("\n");
    if (kind === "secrets") {
      if (/(^|\/)\.env(\.|$)/.test(rel) && rel !== ".env.example") findings.push({ severity: "high", lens: "PSC", checklist: "3.4.1", where: rel, what: ".env file inside the project tree — must be gitignored and never committed", fix_hint: "add to .gitignore; move values to environment injection" });
      lines.forEach((l, i) => {
        for (const p of SECRET_PATTERNS) {
          const m = p.re.exec(l);
          if (!m) continue;
          if (PLACEHOLDER_WORDS.test(l)) continue;              // the LINE announces itself as fake
          if (ANGLE_PLACEHOLDER.test(m[0])) continue;           // the VALUE is <like-this>
          findings.push({ severity: "critical", lens: "PSC", checklist: "3.4.2", where: `${rel}:${i + 1}`, what: `${p.what} in source`, fix_hint: "remove, rotate the secret, load from environment" });
        }
      });
    } else if (kind === "policy") {
      if (!/\.sql$|migrations?\//i.test(rel)) continue;
      const lower = text.toLowerCase();
      for (const m of text.matchAll(/create\s+table\s+(?:if\s+not\s+exists\s+)?([\w."]+)/gi)) {
        const t = m[1]!.replace(/"/g, "").split(".").pop()!;
        if (!new RegExp(`alter\\s+table\\s+(?:[\\w".]*\\.)?"?${t}"?\\s+enable\\s+row\\s+level\\s+security`, "i").test(lower)) findings.push({ severity: "high", lens: "PSC", checklist: "3.2.1", where: `${rel}: table ${t}`, what: `table ${t} created without ENABLE ROW LEVEL SECURITY in the same migration`, fix_hint: `ALTER TABLE ${t} ENABLE ROW LEVEL SECURITY; and add policies + a negative test` });
      }
      for (const m of text.matchAll(/create\s+(?:or\s+replace\s+)?view\s+([\w."]+)/gi)) {
        const v = m[1]!.replace(/"/g, "").split(".").pop()!;
        if (!new RegExp(`view\\s+(?:[\\w".]*\\.)?"?${v}"?[\\s\\S]{0,400}security_invoker`, "i").test(text)) findings.push({ severity: "high", lens: "PSC", checklist: "3.2.2", where: `${rel}: view ${v}`, what: `view ${v} does not set security_invoker`, fix_hint: `WITH (security_invoker = true)` });
      }
      if (/\bdisable\s+row\s+level\s+security\b/i.test(text)) findings.push({ severity: "critical", lens: "PSC", checklist: "3.2.1", where: rel, what: "DISABLE ROW LEVEL SECURITY present", fix_hint: "remove; RLS stays on every table" });
    } else {
      lines.forEach((l, i) => {
        const isLog = LOG_LINE.test(l);
        const isError = !isLog && ERROR_LINE.test(l);
        const isFixture = /fixtures?\/|seed|\.test\.|\.spec\./i.test(rel);
        if (!isLog && !isError && !isFixture) return;
        for (const p of SENSITIVE_DATA_PATTERNS) if (p.re.test(l)) findings.push({ severity: "high", lens: "PSC", checklist: isLog ? "3.7.2" : isError ? "3.3.6" : "3.6.2", where: `${rel}:${i + 1}`, what: `${p.what} in ${isLog ? "a log statement" : isError ? "an error message" : "a fixture"}`, fix_hint: "mask to last-4 or remove" });
        if (isLog && /(req\.body|request\.body|JSON\.stringify\(req)/.test(l)) findings.push({ severity: "medium", lens: "PSC", checklist: "3.7.2", where: `${rel}:${i + 1}`, what: "full request body logged", fix_hint: "log only the fields needed, never the raw body" });
      });
    }
  }
  return { id: kind, kind, status: findings.length ? "fail" : "pass", ms: Date.now() - t0, output: findings.map((f) => `${f.where}: ${f.what}`).join("\n").slice(0, 8000), findings };
}

/**
 * D-71: THE LINES THAT NAME A FAILURE, kept whatever else is dropped.
 *
 * A check's output used to be stored as `out.slice(-8000)` — the LAST eight
 * thousand characters — and a failing check's finding quoted the last SIX lines
 * of that. Every runner this scan knows how to start prints its failures as it
 * goes and its SUMMARY at the end, so on a suite of any size the tail is the
 * summary and the names are gone. Measured on website-design-okoa/v2: two
 * failing `test` records in a row whose stored output contains no `(fail)` line
 * at all, so the finding read `test check FAILED: ... | Ran 818 tests ... |
 * error: script "test" exited with code 1` — true, and useless. Three findings
 * were opened that way and one of them quoted a `console.warn` line from the
 * application that happened to be the last thing printed, which sent the reader
 * after a contact-form bug that was not failing.
 *
 * SO THE NAMED LINES ARE KEPT FIRST AND THE TAIL AFTER THEM. The patterns are a
 * short declared list, one per runner this file's own detector can start, and
 * EACH ONE CARRIES WHETHER IT WAS CHECKED AGAINST A REAL FAILING RUN OR ONLY
 * AGAINST THE RUNNER'S DOCUMENTED SHAPE. Three were run on this machine - bun
 * test, tsc and biome - and five are from documentation, because those runners
 * are not installed here and a pattern nobody has seen fire is a guess however
 * confident it reads. Saying which is which is the point: a later reader can
 * promote one by running it rather than by trusting this comment. A runner whose
 * shape is on neither list is no worse off than before - nothing matches, and
 * the stored output is the tail exactly as it was.
 * THE `deps` CHECK GETS NO PATTERN, deliberately. Its failure IS its report, and
 * SEC-120 on website-design-okoa/v2 just finished making that report the tail on
 * purpose. A pattern there would have to be guessed at with no vulnerable
 * fixture to fire it, and it would compete with the thing the tail already
 * carries.
 *
 * WHY A PATTERN LIST AND NOT A BIGGER WINDOW. Raising the cap moves the problem
 * rather than fixing it — a thousand-row suite overflows any window, and the
 * part that overflows is always the part a reader needs. Keeping both ends was
 * tried on paper and refused: failures are interleaved through the run, so the
 * head is the first tests' chatter and names nothing.
 */
const NAMES_A_FAILURE: { re: RegExp; runner: string; checked: "a real failing run on this machine" | "the runner's documented shape, not run here" }[] = [
  { re: /^\(fail\)/, runner: "bun test", checked: "a real failing run on this machine" },
  { re: /\berror TS\d+\b/, runner: "tsc", checked: "a real failing run on this machine" },
  { re: /^[^\s:][^:]*:\d+:\d+\s+\S+\/\S+\s/, runner: "biome diagnostics, eslint", checked: "a real failing run on this machine" },
  { re: /^\s*[✕×✗]\s/, runner: "vitest, jest", checked: "the runner's documented shape, not run here" },
  { re: /^\s*FAIL\s/, runner: "jest, the file headline", checked: "the runner's documented shape, not run here" },
  { re: /^\s*[✖]\s/, runner: "biome's own summary marker", checked: "the runner's documented shape, not run here" },
  { re: /^error(\[E\d+\])?:/, runner: "cargo, rustc", checked: "the runner's documented shape, not run here" },
  { re: /^(FAILED|ERROR)\s/, runner: "pytest", checked: "the runner's documented shape, not run here" },
];
/**
 * The lines of a check's output that NAME a failure, in the order the runner
 * printed them, deduplicated and capped. Reading the stored output rather than a
 * field of its own is deliberate: a record written before D-71 has no named
 * lines in it, so it answers exactly as it did before and no old record has to
 * be migrated or re-read.
 */
export function failureLines(out: string, limit = 40): string[] {
  const seen = new Set<string>();
  const kept: string[] = [];
  for (const raw of out.split("\n")) {
    const line = raw.trimEnd();
    if (line === "" || seen.has(line)) continue;
    if (!NAMES_A_FAILURE.some((p) => p.re.test(line))) continue;
    seen.add(line);
    kept.push(line);
    if (kept.length >= limit) break;
  }
  return kept;
}
/** The named lines first, then the tail, inside the same 8000-character budget. */
function keptOutput(out: string): string {
  const named = failureLines(out);
  if (named.length === 0) return out.slice(-8000);
  const head = named.join("\n");
  if (head.length >= 8000) return head.slice(0, 8000);
  const room = 8000 - head.length - 2;
  const tail = out.slice(-room);
  return `${head}\n\n${tail}`;
}

/**
 * FUN-1757, and with it FUN-952 and FUN-953: THE ENVIRONMENT A CHECK CHILD GETS, built
 * rather than inherited whole.
 *
 * This used to be `{ ...process.env, CI: "1", FORCE_COLOR: "0" }` inline. The operator's
 * own `NODE_OPTIONS` therefore reached every check child, and a STALE `--require` naming a
 * preload file that no longer exists makes node refuse to start at all:
 * `MODULE_NOT_FOUND, requireStack: [ 'internal/preload' ]`. That happened on
 * website-design-okoa/v2 with a vanished cmux preload, and it failed typecheck, lint AND
 * test before tsc, biome or bun test ever ran — three high findings for one inherited
 * variable, and each one looked like a defect in the project rather than in the gate.
 *
 * WHY THE WHOLE VARIABLE GOES, which is the first remedy FUN-1757 names. Dropping only the
 * broken `--require` would mean parsing a quoted argument list and resolving each target,
 * and a parser that gets it slightly wrong fails the gate in a quieter way than the bug it
 * replaces. None of the checks needs the variable: measured 2026-11-18, this project's four
 * scripts are `tsc --noEmit`, `biome lint --error-on-warnings _build _server scripts`,
 * `bun test ./_build ./_server ./scripts ./tests` and its audit line, and not one of them
 * mentions NODE_OPTIONS. A project that genuinely needs a preload should name it in the
 * script, where it is reviewable, rather than inherit it from whoever happened to run.
 *
 * It is EXPORTED so the claim can be tested: a selftest can hand it a NODE_OPTIONS naming
 * a file that does not exist and assert the variable does not survive into the child.
 */
export function checkEnv(base: NodeJS.ProcessEnv = process.env): NodeJS.ProcessEnv {
  const env: NodeJS.ProcessEnv = { ...base, CI: "1", FORCE_COLOR: "0" };
  delete env.NODE_OPTIONS;
  return env;
}

/**
 * THERE IS NO TRANSPORT WORD LIST HERE ANY MORE, and its deletion is the repair.
 *
 * SEC-38 was first fixed with `REGISTRY_UNREACHABLE`, a pattern of transport vocabulary —
 * `timed out`, `ECONNRESET`, `socket hang up`, `request failed` — searched over the whole
 * audit output. SEC-43 then showed that advisory TITLES use that same vocabulary, so a
 * genuine finding could be retried and stamped NOT a vulnerability report. SEC-46 showed
 * the hole was wider still: the pattern's companion marker list knew `GHSA-` and `CVE-`
 * but not `RUSTSEC-` or `PYSEC-`, so a cargo or pip advisory whose title said "timeout"
 * walked straight into the same mislabelling.
 *
 * Extending the vocabulary would have been the third guess at words nobody can enumerate,
 * on tools this machine cannot even run — neither `cargo-audit` nor `pip-audit` is
 * installed here, so any claim about their exact wording would have been unverifiable,
 * which is precisely how SEC-43 happened. So the list is GONE instead. See
 * `isRegistryOutage`: anything printed to stdout already proves the tool answered, which
 * makes the word list unreachable for every case it was supposed to cover, in every
 * ecosystem, with nothing left to get wrong.
 */

/**
 * Does this output contain anything an ADVISORY says? If so it is a finding, full stop.
 *
 * This is now used in EXACTLY ONE place — the stderr test in `isRegistryOutage` — and it
 * is worth knowing why, because the pattern used to carry far more weight than it could
 * hold. SEC-43: it was the guard that stopped a transport word list from excusing a real
 * advisory. SEC-46: as that guard it was incomplete, knowing `GHSA-` and `CVE-` but not
 * `RUSTSEC-` or `PYSEC-`, so a cargo or pip finding fell through it. The word list it
 * guarded has since been deleted, which is what actually fixed both; this pattern now
 * covers only the narrow case of a tool that prints its findings to stderr and nothing
 * to stdout.
 *
 * The markers are deliberately structural — an advisory identifier, a severity label, a
 * vulnerability tally, a version range — because those appear when packages were actually
 * named and never when a request simply failed.
 *
 * RUSTSEC and PYSEC identifiers are included on the strength of their published ID
 * FORMAT, which is stable and public, and NOT on any claim about the surrounding prose:
 * neither `cargo-audit` nor `pip-audit` is installed on this machine, so their exact
 * output could not be measured here and is not asserted anywhere.
 *
 * The asymmetry is deliberate: a real outage misread as a finding costs a retry and a
 * confusing line, while a real finding misread as an outage is a vulnerability shipped
 * with a note saying it was not one.
 */
export const ADVISORY_PRESENT =
  /(GHSA-[0-9a-z-]+|CVE-\d{4}-\d+|(RUST|PY)SEC-\d{4}-\d+|\b\d+\s+(known\s+)?vulnerabilit|\b(critical|high|moderate|low)\s*:|severity\s*:|[<>]=?\s*\d+\.\d+)/i;

/** How many times a transport failure is retried before it is reported as a failure. */
export const DEPS_ATTEMPTS = 3;

/**
 * Did the audit fail to RUN, as opposed to running and finding something?
 *
 * SEC-43, second attempt. The first attempt answered this question by searching the
 * combined output for transport words, and a review was right to refuse it: deciding by
 * loose words over whole text IS the recorded root cause, and adding a second word-pattern
 * to mask the first one does not replace it. Advisory titles legitimately contain
 * "timeout", "socket" and "request failed".
 *
 * SO THE TOOL'S OWN ANSWER DECIDES, AND IT IS A STRUCTURAL SIGNAL, NOT A VOCABULARY ONE.
 * Measured on bun 1.3.9, three states, stdout and stderr kept apart:
 *
 *   clean tree ............ exit 0, stdout "No vulnerabilities found"  (24 bytes)
 *   advisories found ...... exit 1, stdout the advisory list           (489 bytes)
 *   registry unreachable .. exit 1, stdout EMPTY (0 bytes), the message on stderr
 *
 * A report on stdout means the audit reached the registry and answered, whatever the
 * answer says. Empty stdout with a non-zero exit means it never got to answer. That
 * distinction needs no word list and cannot be fooled by an advisory's title.
 *
 * TWO TESTS, AND NEITHER ONE READS THE OUTPUT'S MEANING.
 *
 *   1. ANYTHING ON STDOUT means the tool answered. Measured on bun 1.3.9: a clean tree
 *      prints `{}` under `--json` (3 bytes) or "No vulnerabilities found" in prose, a
 *      tree with findings prints a report, and a tree it could not audit prints ZERO
 *      bytes with its message on stderr. This one test separates all three, needs no
 *      vocabulary, and an advisory title cannot fake it.
 *
 *      It is also the test that closes SEC-46 for ecosystems this machine cannot run.
 *      `cargo audit -q` and `pip-audit -q` print their findings to stdout like every
 *      other audit, so their advisories are recognised as answers whatever words or
 *      identifier scheme they use — RUSTSEC, PYSEC, or something invented next year.
 *      The cost is small and it falls on the safe side: a prose audit that printed a
 *      transport error to stdout is recorded as a plain failure rather than a retried
 *      "REGISTRY UNREACHABLE". It still fails, and it still blocks. Nothing is excused.
 *
 *   2. An ADVISORY MARKER ON STDERR, for the one shape test 1 cannot see: a tool that
 *      prints nothing to stdout and reports its findings on stderr. Without this, such
 *      a tool's real findings would be retried and labelled unreachable.
 *
 *      This is the ONLY surviving pattern match, and it sits where being incomplete is
 *      almost always harmless, because every audit on record reports to stdout. The
 *      honest residual: a tool that reports findings on stderr ONLY, using an identifier
 *      scheme `ADVISORY_PRESENT` does not know, would still be mislabelled. No such tool
 *      is known, and it is recorded here rather than papered over.
 *
 * A crash with no output on either stream is reported as "did not run", and is retried.
 * That is deliberate: it still ends in a failure, and three attempts at a crash cost a
 * few seconds, while treating a crash as a vulnerability report would be a lie.
 *
 * WHY THE JSON PARSE IS NOT HERE. `parseAuditJson` was briefly the first test. It was
 * provably dead: a parsed JSON object is non-empty text, so test 1 had already returned
 * the same answer, and no input could tell the two orderings apart. `--json` stays,
 * because it earns its place rendering a readable record (`renderAuditJson`) — not
 * because it decides anything.
 */
export function isRegistryOutage(res: { stdout?: string | null; stderr?: string | null }): boolean {
  if (String(res.stdout ?? "").trim() !== "") return false;
  if (ADVISORY_PRESENT.test(String(res.stderr ?? ""))) return false;
  return true;
}

/**
 * The audit's structured result, or null if it did not produce one.
 *
 * Deliberately strict about what counts. Only a JSON OBJECT counts, because that is the
 * shape `bun audit --json` emits in both of its answering states, and because a bare
 * `null`, `0` or `""` is valid JSON that would otherwise be read as "the audit answered"
 * when it plainly did not. An array does not count either: no audit on record emits one,
 * and accepting shapes nobody emits is how a strict check quietly becomes a loose one.
 *
 * ONE CHECK, DELIBERATELY. An earlier version opened with `if (s === "" ||
 * !s.startsWith("{")) return null;` as a cheap guard. It was not cheap, it was load-bearing
 * in the wrong place: every valid JSON document beginning with `{` IS an object, so the
 * brace test made the shape test below unreachable, and mutating the shape test away then
 * broke nothing. Measured 2026-11-18 — the mutation that replaced the whole shape test with
 * `return (v ?? {})` passed the entire suite. Empty and blank input need no guard either;
 * `JSON.parse("")` throws, which the catch already handles.
 *
 * `v !== null` is an EQUIVALENT MUTANT and no test can catch it, which is stated here so
 * nobody spends an afternoon trying. `JSON.parse("null")` yields `null`, and returning that
 * as the parsed object is indistinguishable from returning the sentinel `null`, so removing
 * the clause changes no caller's behaviour. It stays because without it the cast below is a
 * lie about the type, not because it changes an answer.
 */
export function parseAuditJson(stdout: string): Record<string, unknown> | null {
  try {
    const v = JSON.parse(stdout);
    return v !== null && typeof v === "object" && !Array.isArray(v) ? (v as Record<string, unknown>) : null;
  } catch {
    return null;
  }
}

/**
 * Turn a parsed `--json` audit back into lines a person can act on, or null if this is
 * not an audit's JSON.
 *
 * WHY THIS EXISTS. Adding `--json` fixed the classification and broke the record: the
 * ledger is read by a person deciding what to fix, and a wall of JSON is worse than the
 * table it replaced. So the machine shape decides and the readable shape is recorded.
 * Every line names the package, the severity, the affected range and the advisory URL,
 * which is strictly more than the prose table carried.
 */
export function renderAuditJson(stdout: string): string | null {
  const parsed = parseAuditJson(stdout);
  if (!parsed) return null;
  const names = Object.keys(parsed);
  if (names.length === 0) return "no advisories";

  const lines: string[] = [];
  let total = 0;
  for (const name of names) {
    const entries = parsed[name];
    if (!Array.isArray(entries)) return null; // not the shape we measured — keep the raw text
    for (const e of entries) {
      const a = (e ?? {}) as Record<string, unknown>;
      const sev = String(a.severity ?? "unknown");
      const range = String(a.vulnerable_versions ?? "?");
      const title = String(a.title ?? "(no title)");
      const url = String(a.url ?? "");
      lines.push(`${name} ${range} ${sev}: ${title}${url ? ` - ${url}` : ""}`);
      total += 1;
    }
  }
  if (total === 0) return "no advisories";
  return `${total} advisory/advisories in ${names.length} package(s)\n${lines.join("\n")}`;
}

/** Blocks this thread without spawning anything; the scan is synchronous by design. */
function sleepSync(ms: number): void {
  Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms);
}

/**
 * Was this child KILLED at its ceiling, whatever it managed to print first?
 *
 * FUN-142. `isRegistryOutage` reads the OUTPUT, and a killed audit that had already printed
 * a banner or half a JSON chunk looks, by output alone, exactly like a tool that answered —
 * so it was not retried, while the record one line later correctly called it unreachable.
 * The two disagreed because only one of them could see the kill.
 *
 * A timeout is definitive regardless of output: a process that was killed did not finish,
 * so it did not answer, so there is something to retry. This is deliberately a check on
 * `error.code` and not on the text, because the text is exactly what cannot be trusted here.
 */
export function wasKilledAtTimeout(res: { error?: unknown }): boolean {
  return /ETIMEDOUT/.test(String((res.error as NodeJS.ErrnoException | undefined)?.code ?? ""));
}

/** The per-attempt ceiling: short for an audit, generous for anything that compiles or tests. */
export function timeoutFor(kind: CheckKind): number {
  return kind === "deps" ? DEPS_TIMEOUT_MS : CHECK_TIMEOUT_MS;
}

function spawnOnce(root: string, c: Check, timeoutMs: number) {
  return spawnSync(c.cmd as string, c.args ?? [], { cwd: root, encoding: "utf8", timeout: timeoutMs, env: checkEnv(), maxBuffer: 64 * 1024 * 1024 });
}

/**
 * Run one check, and for a dependency audit retry a transport failure before believing it.
 *
 * WHY THE RETRY NEVER TURNS INTO A PASS (SEC-38). The tempting repair is to let an
 * unreachable registry count as clean, because "we could not check" feels different from
 * "we found something". It is not different in the direction that matters: the protocol's
 * own rule is that a check it could not run is never clean, so an unreachable registry
 * stays a FAILURE here however many times it is retried. What the retry buys is the
 * difference between a blip and an outage, and what the distinct wording buys is an
 * operator who can tell, from the recorded output alone, which of the two they are
 * looking at without re-running anything.
 */
export function runCommand(root: string, c: Check, limits?: { timeoutMs?: number; budgetMs?: number }): CheckResult {
  const t0 = Date.now();
  if (!c.cmd) return { id: c.id, kind: c.kind, status: "skipped", ms: 0, output: c.note ?? "not configured" };

  // The ceilings are arguments with defaults, not constants read inside the loop, so the
  // timeout and budget behaviour can be DRIVEN by a test instead of described by one. The
  // scan passes nothing and gets the real ceilings; waiting two minutes to prove a two
  // minute ceiling works is how a timeout path ends up with no test at all (FUN-135).
  const timeoutMs = limits?.timeoutMs ?? timeoutFor(c.kind);
  const budgetMs = limits?.budgetMs ?? DEPS_RETRY_BUDGET_MS;

  let r = spawnOnce(root, c, timeoutMs);
  let out = `${r.stdout ?? ""}\n${r.stderr ?? ""}`.trim();
  let attempts = 1;

  // Only a dependency audit talks to a network, so only it is retried. Retrying a type
  // check or a test suite would hide a flaky test, which is a defect worth seeing.
  //
  // The budget check is part of the CONDITION, not a thing to remember later: no attempt
  // may START once the sequence has already spent its wall clock (FUN-135).
  if (c.kind === "deps") {
    while (attempts < DEPS_ATTEMPTS && Date.now() - t0 < budgetMs && r.status !== 0 && (wasKilledAtTimeout(r) || isRegistryOutage(r))) {
      sleepSync(attempts * 2_000);
      r = spawnOnce(root, c, timeoutMs);
      out = `${r.stdout ?? ""}\n${r.stderr ?? ""}`.trim();
      attempts += 1;
    }
  }

  // A `--json` audit answers in a machine shape; the ledger is read by a person. The
  // decision above used the parsed result, so the record can carry the readable one.
  if (c.kind === "deps") {
    const readable = renderAuditJson(String(r.stdout ?? ""));
    if (readable !== null) out = `${readable}\n${r.stderr ?? ""}`.trim();
  }

  if (r.error && (r.error as NodeJS.ErrnoException).code === "ENOENT") return { id: c.id, kind: c.kind, status: "skipped", ms: Date.now() - t0, output: `${c.cmd} not found` };
  // A check killed at its own ceiling. The number quoted has to be the ceiling that
  // ACTUALLY applied (FUN-135): quoting the global one on a deps check that was killed at
  // two minutes put a figure in the ledger that was wrong by a factor of ten.
  if (wasKilledAtTimeout(r)) {
    const secs = timeoutMs / 1000;
    // An audit that never finished did not answer, which is the same thing as an
    // unreachable registry and must be recorded in the same words. Reporting it as a bare
    // "timed out" left the one case SEC-38 exists for looking like an ordinary slow check.
    const note = c.kind === "deps"
      ? `REGISTRY UNREACHABLE after ${attempts} attempt(s) — the audit did not finish within ${secs}s, so this is NOT a clean result and NOT a vulnerability report`
      : `timed out after ${secs}s`;
    return { id: c.id, kind: c.kind, status: "fail", ms: Date.now() - t0, output: keptOutput(`${note}\n${out}`) };
  }

  // A transport failure that survived every attempt is reported in its own words, so the
  // ledger does not record an outage as if the audit had found vulnerable packages.
  if (c.kind === "deps" && r.status !== 0 && isRegistryOutage(r)) {
    return { id: c.id, kind: c.kind, status: "fail", ms: Date.now() - t0, output: keptOutput(`REGISTRY UNREACHABLE after ${attempts} attempt(s) — the audit could not be performed, so this is NOT a clean result and NOT a vulnerability report\n${out}`) };
  }

  return { id: c.id, kind: c.kind, status: r.status === 0 ? "pass" : "fail", ms: Date.now() - t0, output: keptOutput(out) };
}

export function isClean(r: Pick<ScanResult, "checks">): boolean { return r.checks.every((c) => c.status === "pass"); }

/**
 * Run the whole S3 scan, record it, and return it. `repro` lists the registered reproduction
 * tests so their individual results can be recorded for closure (R-025).
 */
/**
 * R-060 — can any DYNAMIC test title in this file actually produce `name`?
 *
 * Two shapes cover what test runners offer: a template literal title with `${...}` holes, and an
 * `.each` title carrying printf-style placeholders (`%s`, `%d`, `%i`, `%f`, `%j`, `%o`, `%p`,
 * `%#`). Each becomes a regex with the static parts anchored and the holes as wildcards, then the
 * registered name is matched against it. A pattern that cannot produce the name is no evidence,
 * so this narrows the refusal rather than removing it.
 */
function findDynamicDeclaration(src: string, name: string): { matched: boolean; anyDynamic: boolean; lines: string[] } {
  const decl = src.split("\n").filter((l) => /\b(test|it|describe|bench)\b/.test(l));
  const lines: string[] = [];
  let anyDynamic = false;
  const statics = (tpl: string, splitter: RegExp): RegExp =>
    new RegExp("^" + tpl.split(splitter).map((part) => part.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("[\\s\\S]*") + "$");
  for (const l of decl) {
    // a template literal title with at least one ${...}
    for (const m of l.matchAll(/`([^`]*)`/g)) {
      const tpl = m[1] ?? "";
      if (!tpl.includes("${")) continue;
      anyDynamic = true;
      if (statics(tpl, /\$\{[^}]*\}/).test(name)) { lines.push(l); }
    }
    // an .each title with printf-style placeholders
    if (/\.each\b/.test(l)) {
      for (const m of l.matchAll(/["'\`]([^"'\`]*)["'\`]/g)) {
        const tpl = m[1] ?? "";
        if (!/%[sdifjop#]/.test(tpl)) continue;
        anyDynamic = true;
        if (statics(tpl, /%[sdifjop#]/).test(name)) { lines.push(l); }
      }
    }
  }
  return { matched: lines.length > 0, anyDynamic, lines };
}

export function runScan(root: string, cfg: Config, args: { trigger: string; changed: string[]; task?: string; repro?: { file: string; name: string }[] }): ScanResult {
  const checks = detectToolchain(root, cfg);
  const results: CheckResult[] = checks.map((c) => (c.builtin ? runBuiltin(c.builtin, root, cfg, args.changed) : runCommand(root, c)));
  const testRes = results.find((r) => r.kind === "test");
  const repro_results: Record<string, boolean> = {};
  const repro_reasons: Record<string, string> = {};
  for (const rp of args.repro ?? []) {
    // D-59: the body of this loop is now `reproEvidence`, so the release gate can ask the
    // very same question of a CLOSED finding instead of a second, drifting copy of the rule.
    const ev = reproEvidence(root, rp, testRes);
    repro_results[ev.key] = ev.ok;
    repro_reasons[ev.key] = ev.reason;
  }
  const result: ScanResult = {
    id: `scan-${Date.now()}-${sha256(String(Math.random())).slice(0, 6)}`, at: nowIso(), task: args.task, trigger: args.trigger, changed: args.changed,
    checks: results, clean: results.every((c) => c.status === "pass"), tests_pass: testRes?.status === "pass", repro_results, repro_reasons,
  };
  writeJson(path.join(P.scans(root), `${result.id}.json`), result);
  return result;
}

export function listScans(root: string, task?: string): ScanResult[] {
  if (!fs.existsSync(P.scans(root))) return [];
  return fs.readdirSync(P.scans(root)).filter((f) => f.endsWith(".json")).sort()
    .map((f) => { try { return JSON.parse(fs.readFileSync(path.join(P.scans(root), f), "utf8")) as ScanResult; } catch { return null; } })
    .filter((s): s is ScanResult => !!s && (!task || s.task === task));
}

export function scanSummary(s: ScanResult): string {
  return s.checks.map((c) => `${c.id}:${c.status}`).join(" ") + (s.clean ? "  → clean" : "  → NOT clean");
}

/** Turn scan failures into judge-shaped findings (R-014): FUN for test/type/lint, SEC for the rest. */
export function scanFindings(s: ScanResult): ScanFinding[] {
  const out: ScanFinding[] = [];
  for (const c of s.checks) {
    if (c.status === "pass") continue;
    if (c.findings?.length) { out.push(...c.findings); continue; }
    const lens: "PSC" | "PFC" = c.kind === "typecheck" || c.kind === "lint" || c.kind === "test" || c.kind === "extra" ? "PFC" : "PSC";
    const checklist = c.kind === "test" ? "PFC-c" : c.kind === "typecheck" ? "PFC-e" : c.kind === "lint" ? "PFC-e" : c.kind === "deps" ? "3.11.2" : "S3";
    out.push({
      severity: c.status === "skipped" ? "high" : c.kind === "deps" ? "high" : "high", lens, checklist, where: `S3 ${c.id}`,
      /* D-71: the finding quotes the lines that NAME the failures when the output
         carries any, and falls back to the last six lines when it does not — which
         is what a record written before D-71 has, so nothing old reads differently. */
      what: c.status === "skipped" ? `${c.id} check SKIPPED (${c.output}) — a skip is not a pass; the project needs this check to exist` : `${c.id} check FAILED: ${(failureLines(c.output, 6).length > 0 ? failureLines(c.output, 6) : c.output.split("\n").filter(Boolean).slice(-6)).join(" | ").slice(0, 400)}`,
      fix_hint: c.status === "skipped" ? `add a ${c.id} step to the project (or an extra_check) so S3 can run it` : `make ${c.id} pass; the output is in .nemesis/records/scans/`,
    });
  }
  return out;
}


/**
 * D-59 — IS THIS REPRODUCTION TEST STILL REAL EVIDENCE, RIGHT NOW?
 *
 * Lifted verbatim out of `runScan`'s loop so the RELEASE GATE can ask the same question of a
 * finding that is already CLOSED. It was previously unreachable for those: every live caller
 * passes `listIssues(root, true)` - OPEN findings only - so the moment a finding closed, the test
 * that proved it stopped being checked by anything, ever, and its closure record became a claim
 * about the past stated in the present tense.
 *
 * Measured on website-design-okoa/v2, 2026-11-09: 177 closed findings rest on 13 proof files, and
 * ONE of them, `_build/headers.test.ts`, carries 34 of those closes. Deleting that single file
 * would un-prove 34 findings and `cmdReleaseGate` would not notice, because it reads only open
 * findings. The ledger page meanwhile tells Zee each one was "Closed after the reproduction test
 * passed".
 *
 * The three realistic ways a proof evaporates are all caught, because all three are visible in
 * the file: the file is deleted, the named test is removed, or it is marked skip/todo/failing.
 * `suite` is optional so a caller with no fresh run can still check the first three - a missing
 * runner yields `ok: false` with that stated as the reason, never a silent pass.
 */
export function reproEvidence(root: string, rp: { file: string; name: string }, suite?: { status?: string; output?: string }): { key: string; ok: boolean; reason: string } {
    // R-060. The old rule was: the file exists, the suite passed, and the suite output does not
    // mark this test failed. That credits a test name that is PRESENT NOWHERE, because a name no
    // runner ever saw produces no failure line either. Found by the v2-ee session on 2026-11-04:
    // FUN-93 carried a reproduction pointing at an unrelated test and still satisfied closure
    // criterion (1). "Nothing said it failed" is not evidence that anything ran.
    //
    // The fix cannot lean on the suite OUTPUT naming the test: `bun test` prints only
    // "1 pass / 0 fail" on success and names a test only when it fails, so demanding a pass
    // marker would block closure on every project using it. Measured, not assumed.
    //
    // So the evidence comes from the file instead, which is runner-agnostic: the named test must
    // be DECLARED in the file the reproduction points at, and must not be skipped or todo. With
    // the whole suite green, a declared and unskipped test in that file did run and did pass.
    const key = `${rp.file}::${rp.name}`;
    const abs = path.resolve(root, rp.file);
    const esc = rp.name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const out = suite?.output ?? "";
    const exists = fs.existsSync(abs);
    const src = exists ? fs.readFileSync(abs, "utf8") : "";
    // the name, as a quoted string, on a line that declares a test
    const lines = src.split("\n").filter((l) => new RegExp(`["'\`]${esc}["'\`]`).test(l));
    const literal = lines.some((l) => /\b(test|it|describe|bench)\b/.test(l));
    // A DYNAMICALLY NAMED test never has its literal name in the source, so a literal-only rule
    // would refuse a perfectly real reproduction. Raised by the v2-ee session on 2026-11-04:
    // none existed on that project, but the rule will meet one. So also accept a declaration
    // whose name PATTERN can produce the registered name: a template literal with `${...}`
    // holes, or an `.each` title with printf-style placeholders. The pattern must actually be
    // able to produce that name, so this is evidence, not a waiver.
    const dyn = findDynamicDeclaration(src, rp.name);
    const declared = literal || dyn.matched;
    const declLines = literal ? lines : dyn.lines;
    const skipped = declLines.some((l) => /\.(skip|todo|failing)\b|\bxit\b|\bxtest\b/.test(l));
    const failed = new RegExp(`(\u2717|\u2715|\u00d7|FAIL|fail)[^\\n]*${esc}|${esc}[^\\n]*(\u2717|\u2715|\u00d7|FAIL|fail)`).test(out);
    let why = "";
    if (!exists) why = `the file ${rp.file} does not exist`;
    else if (!lines.length && !dyn.matched && dyn.anyDynamic) why = `${rp.file} declares its test names dynamically and none of those patterns can produce "${rp.name}" \u2014 register a name one of them really produces, or add a statically named test for this bug: nemesis issue repro <id> <file> "<name>"`;
    else if (!lines.length && !dyn.matched) why = `${rp.file} contains no test named "${rp.name}" \u2014 the reproduction points at a test that is not there, so nothing proves this bug is fixed; register the real name: nemesis issue repro <id> <file> "<name>"`;
    else if (!declared) why = `"${rp.name}" appears in ${rp.file} but not as a test declaration`;
    else if (skipped) why = `"${rp.name}" is declared in ${rp.file} but skipped, so it never ran`;
    else if (!suite) why = "no test runner ran in this scan";
    else if (suite.status !== "pass") why = `the suite did not pass (${suite.status})`;
    else if (failed) why = `the suite output marks "${rp.name}" failed`;
    const ok = exists && declared && !skipped && suite?.status === "pass" && !failed;
    // `||` NOT `??`: `why` is a string and the empty string is the "no problem found" case.
    // `??` only falls through on null/undefined, so switching it silently replaced the positive
    // explanation with "". Caught by selftest R-060 one minute after the extraction, which is
    // exactly what that test is for.
    const reason = why || `${literal ? "declared" : "declared by a name pattern that produces it"} and unskipped in ${rp.file}, and the whole suite passed`;
    return { key, ok, reason };
}
