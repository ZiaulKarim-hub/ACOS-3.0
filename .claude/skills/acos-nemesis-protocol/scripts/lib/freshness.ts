/**
 * freshness.ts — DOES A PASS VERDICT STILL COVER THE CODE ON DISK? (D-66, R-084)
 *
 * THE DEFECT THIS FIXES, measured on website-design-okoa/v2 2026-11-11.
 *
 * A holdout reveal already records exactly what it graded: `reveal.candidate_fingerprint_digest`
 * in the manifest, and a per-file sha256 map `candidate.fingerprint_before` in the sealed evidence
 * bundle. NOTHING EVER READ THEM BACK. The only callers of `fingerprintCandidate` were the reveal
 * itself and the holdout engine's own selftest, so after a reveal the project held every byte it
 * needed to say "this PASS is stale" and no code asked the question.
 *
 * The release gate was the place it mattered: `nemesis.ts` built its `holdouts` array from
 * `reveal?.verdict ?? "none"` alone, so a task whose graded code had since been rewritten still
 * reported a clean "PASS" to the release charter. R-019 was in exactly that state - revealed PASS
 * 2026-11-05T22:34:11.335Z, and 16 of the 54 files that PASS covered had changed since, including
 * `_build/headings.test.ts`, the very guard the task is about.
 *
 * The cost was a spin, not just a wrong answer. FUN-179 and FUN-180 are the two findings that say
 * "acceptance behavior not proven". From 2026-10-31 to 2026-11-10 they drew EIGHT consecutive
 * review verdicts with the same text - the PASS graded an older guard - because each review had to
 * re-derive staleness BY HAND from the snapshot store, and the diff each attempt produced edited
 * the guard again, re-staling the proof it was trying to establish. Eleven days, no progress
 * possible, because the loop's exit condition was never mechanical.
 *
 * WHICH FILES COUNT, and why it is two filters and not one. The pack generator declares
 * `candidate: { files: ["**[/]*"] }` (nemesis.ts), so the fingerprint swept 3,802 paths - 3,142 of
 * them gitignored, including a throwaway Chrome profile under `_build/_favicon-staging/_chrome/`
 * whose cache files are deleted between runs. Judged on that map, EVERY pack is stale forever and
 * the signal is worthless noise. Judged on Nemesis scope alone, the Chrome profile still counts,
 * because it sits under a source directory. Judged on git-tracked alone, `memory/handoffs/**`
 * counts, so writing a handoff would stale an acceptance proof. So a file counts only when it is
 * BOTH in Nemesis scope AND tracked by git: the project's own definition of code it judges,
 * intersected with the project's own committed state. On R-019 that cut 3,802 paths to 54, left
 * MISSING at zero, and still flagged all 16 real source changes - the guard among them.
 *
 * FAIL-SAFE DIRECTION. Every uncertainty resolves toward STALE, never toward fresh. No bundle, no
 * fingerprint recorded, or git unavailable all refuse to certify freshness, because a false
 * "stale" costs one re-author while a false "fresh" ships an unproven guard behind a green gate.
 */
import * as fs from "node:fs";
import * as path from "node:path";
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { P, readJson, readConfig, type Config } from "./state";
import { isInScope } from "./scope";

export interface FreshnessBase { task: string; state: string; why: string }
export interface Freshness extends FreshnessBase {
  /** "no-pack" | "unrevealed" | "unverifiable" | "fresh" | "stale" */
  state: "no-pack" | "unrevealed" | "unverifiable" | "fresh" | "stale";
  verdict: string | null;
  graded_at: string | null;
  covered: number;
  changed: string[];
  missing: string[];
}

/** A PASS that no longer covers the code is not a pass. Anything but "fresh" must not certify. */
export function certifies(f: Freshness): boolean {
  return f.state === "fresh" && f.verdict === "PASS";
}

/**
 * The committed file set, cached for TRACKED_TTL_MS.
 *
 * `nemesis status` asks freshness for every task, and one `git ls-files` per task was 41 git
 * processes on the live project for one answer. The TTL is deliberately shorter than any command
 * this is called from lives, so a single invocation shares one answer and two invocations never
 * do — a long-lived caller can never be handed a stale tree.
 */
export const TRACKED_TTL_MS = 2000;
const trackedCache = new Map<string, { at: number; tracked: Set<string> | null }>();

/**
 * Drop the cached committed-file set. ONLY for tests that change git state mid-run.
 *
 * The TTL is what makes this necessary and it is also why it is safe in production: a real command
 * run finishes well inside 2000ms and git's index does not change under it. A test, though, commits
 * a file and asks about it microseconds later, and the cache from the test's first call still says
 * that file is untracked. That masked a control completely — `git ls-files` called directly said
 * the file was tracked while the cached set said it was not, so the filter under test was never
 * reached and breaking it changed nothing.
 */
export function resetTrackedCache(root?: string): void {
  if (root) trackedCache.delete(root); else trackedCache.clear();
}

export function trackedFiles(root: string): Set<string> | null {
  const hit = trackedCache.get(root);
  if (hit && Date.now() - hit.at < TRACKED_TTL_MS) return hit.tracked;
  const ls = spawnSync("git", ["ls-files", "-z"], { cwd: root, encoding: "utf8", maxBuffer: 256 * 1024 * 1024 });
  const tracked = ls.status === 0 && typeof ls.stdout === "string" ? new Set(ls.stdout.split("\0").filter(Boolean)) : null;
  trackedCache.set(root, { at: Date.now(), tracked });
  return tracked;
}

/** The files a staleness judgement is allowed to rest on: Nemesis scope AND the committed tree. */
export function coveredFiles(root: string, rels: string[], cfg: Config): { covered: string[]; gitOk: boolean } {
  const inScope = rels.filter((r) => isInScope(root, path.join(root, r), cfg).inScope);
  const tracked = trackedFiles(root);
  if (!tracked) return { covered: inScope, gitOk: false };
  return { covered: inScope.filter((r) => tracked.has(r)), gitOk: true };
}

/**
 * Is task `taskId`'s revealed holdout verdict still about the code as it stands right now?
 *
 * Reads only records that already exist - no re-run, no re-grade, nothing destructive - so this is
 * safe to call from a gate, a hook or a status line.
 */
export function holdoutFreshness(root: string, taskId: string, cfg?: Config): Freshness {
  const base = { task: taskId, verdict: null as string | null, graded_at: null as string | null, covered: 0, changed: [] as string[], missing: [] as string[] };
  const mPath = path.join(P.holdout(root), taskId, "manifest.json");
  if (!fs.existsSync(mPath)) return { ...base, state: "no-pack", why: "no holdout manifest: the task has no sealed commitment" };

  const m = readJson<{ reveal?: { verdict?: string; revealed_at?: string; evidence_bundle?: string } | null }>(mPath, {});
  const rev = m.reveal;
  if (!rev || !rev.verdict) return { ...base, state: "unrevealed", why: "the pack is sealed but never graded, so there is no verdict to keep fresh" };

  const verdict = rev.verdict;
  const gradedAt = rev.revealed_at ?? null;
  const bundlePath = rev.evidence_bundle;
  if (!bundlePath || !fs.existsSync(bundlePath)) {
    return { ...base, state: "unverifiable", verdict, graded_at: gradedAt, why: `verdict ${verdict} recorded but its evidence bundle is missing (${bundlePath ?? "no path"}), so what it graded cannot be checked` };
  }

  const bundle = readJson<{ candidate?: { fingerprint_before?: Record<string, string> } }>(bundlePath, {});
  const fp = bundle.candidate?.fingerprint_before;
  if (!fp || typeof fp !== "object" || Object.keys(fp).length === 0) {
    return { ...base, state: "unverifiable", verdict, graded_at: gradedAt, why: `verdict ${verdict} recorded but the bundle holds no candidate fingerprint, so what it graded cannot be checked` };
  }

  const conf = cfg ?? readConfig(root);
  const { covered, gitOk } = coveredFiles(root, Object.keys(fp), conf);
  // A project with no git gets the WEAKER check, not a blanket refusal. Judging on Nemesis scope
  // alone still catches a rewritten source file, and it is strictly stronger than the verdict-only
  // reading this replaces; refusing outright would make the release gate unopenable for every
  // non-git project, which is a different defect rather than a safer one. The weaker basis is
  // named in `why` so a reader is never misled about which check actually ran.
  const basis = gitOk ? "in Nemesis scope and tracked by git" : "in Nemesis scope (no git here, so the committed tree could not narrow it)";
  if (covered.length === 0) {
    return { ...base, state: "unverifiable", verdict, graded_at: gradedAt, why: `verdict ${verdict} graded ${Object.keys(fp).length} path(s), none of them ${basis}, so it covers no judged source at all` };
  }

  // `fingerprintCandidate` records a literal path that did not exist as the string "(absent)"
  // rather than a hash, so "absent then, absent now" is UNCHANGED. Treating that sentinel as a
  // hash would mark every such path missing and report a permanent false stale.
  const ABSENT = "(absent)";
  const changed: string[] = [];
  const missing: string[] = [];
  for (const rel of covered) {
    const abs = path.join(root, rel);
    const wasAbsent = fp[rel] === ABSENT;
    let buf: Buffer | null = null;
    try { buf = fs.readFileSync(abs); } catch { buf = null; }
    if (buf === null) { if (!wasAbsent) missing.push(rel); continue; }
    if (wasAbsent) { changed.push(rel); continue; }          // absent when graded, present now
    if (createHash("sha256").update(buf).digest("hex") !== fp[rel]) changed.push(rel);
  }
  changed.sort(); missing.sort();

  if (changed.length === 0 && missing.length === 0) {
    return { task: taskId, state: "fresh", verdict, graded_at: gradedAt, covered: covered.length, changed, missing, why: `verdict ${verdict} still covers all ${covered.length} judged file(s) (${basis}) as they stand` };
  }
  const bits = [changed.length ? `${changed.length} changed` : "", missing.length ? `${missing.length} missing` : ""].filter(Boolean).join(", ");
  return {
    task: taskId, state: "stale", verdict, graded_at: gradedAt, covered: covered.length, changed, missing,
    why: `verdict ${verdict} was graded ${gradedAt ?? "at an unrecorded time"} against code that has since moved: of ${covered.length} judged file(s) (${basis}), ${bits}${changed.length ? ` (first: ${changed[0]})` : ""}. Re-author and re-grade: nemesis task holdout ${taskId} --new`,
  };
}

/** The one line the release charter should see instead of a bare verdict. */
export function holdoutLine(f: Freshness): string {
  if (f.state === "fresh") return String(f.verdict);
  if (f.state === "unrevealed") return "none";
  if (f.state === "no-pack") return "none";
  if (f.state === "stale") return `${f.verdict} (STALE — ${f.changed.length} changed, ${f.missing.length} missing of ${f.covered} judged file(s) since ${f.graded_at ?? "grading"})`;
  return `${f.verdict ?? "none"} (UNVERIFIABLE — ${f.why})`;
}

/**
 * The file list a NEW pack should commit to, instead of the old `["**[/]*"]`.
 *
 * WHY AN EXPLICIT LIST AND NOT A GLOB. `exclude_globs` is whack-a-mole: the live project excluded
 * `_build/_favicon-preview/**` and not `_build/_favicon-staging/**`, so a throwaway Chrome profile
 * under a source directory was fingerprinted - 176 of its files were deleted between runs, which
 * made the pack permanently and meaninglessly stale. An explicit list of the paths that were in
 * Nemesis scope AND committed at seal time cannot drift that way, and it makes the commitment
 * auditable: the pack says, in bytes, exactly which files its verdict is about.
 *
 * A file created AFTER the seal is deliberately not covered. The verdict is a statement about the
 * code that was graded, and a file that did not exist then was not graded.
 *
 * Falls back to the project's declared `source_globs` when git cannot answer or the list would be
 * unreasonably large - never back to `**[/]*`, which is the defect this replaces.
 */
export const PACK_FILE_LIST_CAP = 4000;

export function candidateFilesForPack(root: string, cfg?: Config): string[] {
  const conf = cfg ?? readConfig(root);
  const fallback = (conf.source_globs && conf.source_globs.length ? conf.source_globs : ["**/*"]).slice();
  const trackedSet = trackedFiles(root);
  if (!trackedSet) return fallback;
  const inScope = [...trackedSet].filter((r) => isInScope(root, path.join(root, r), conf).inScope);
  if (inScope.length === 0 || inScope.length > PACK_FILE_LIST_CAP) return fallback;
  return inScope.sort();
}

/**
 * THE FILES A TASK'S EXAM IS ACTUALLY ABOUT (D-66, second half).
 *
 * `candidateFilesForPack` fixed the worst of it - a pack no longer commits to `["**[/]*"]` and its
 * 3,802 paths of browser cache - but scope-intersect-tracked is still the WHOLE source tree, 54
 * files on the live project, of which 16 changed in six days. A proof scoped that way is fresh for
 * about a day: R-019's own subject `_build/headings.test.ts` had not been touched for 39 hours
 * while its proof read stale, because OTHER tasks had edited `_server/admin-lib.ts` and
 * `_build/worker.ts`. A warning that is always on is not a warning, and re-grading into that scope
 * would have rebuilt the same eleven-day spin with a fresher date on it.
 *
 * So the subject is taken from two RECORDED facts about this task, never from a guess:
 *   1. the paths its own holdout cases name - every R-019 case does `readFileSync('_build/
 *      headings.test.ts')`, so the exam says in its own bytes what it reads;
 *   2. the paths its S2 verdict records name - `.nemesis/tasks/<id>/artifacts/s2-*.json` each
 *      carry `{"path": "<file>", "candidate_sha256": …}`, which is the file the judge actually saw
 *      (202 such records for R-019).
 *
 * Fail-safe stays the same direction: anything this cannot establish falls back to the broader
 * scope-intersect-tracked list, which is wider and therefore more likely to read stale. Narrowing
 * is only ever done on evidence, because a subject narrowed too far would certify a proof that
 * never looked at the code it claims to cover.
 *
 * KNOWN LIMIT, stated rather than hidden: a file the exam depends on WITHOUT naming it - something
 * its subject imports - is not in this set, so a change there will not mark the proof stale. The
 * two records above are what the project actually writes down; an import closure is not, and
 * inventing one would be a guess dressed as evidence.
 */
const PATHISH = /['"`]([A-Za-z0-9_][A-Za-z0-9_./-]*\.[A-Za-z0-9]{1,6})['"`]/g;

export function packSubjectFiles(root: string, taskId: string, cases: unknown, cfg?: Config): string[] {
  const conf = cfg ?? readConfig(root);
  const named = new Set<string>();

  // (1) whatever the cases name, read out of the case definitions themselves
  for (const m of JSON.stringify(cases ?? []).matchAll(PATHISH)) named.add(m[1]!);

  // (2) whatever this task's own S2 verdict records name as the judged file
  const art = path.join(P.task(root, taskId), "artifacts");
  if (fs.existsSync(art)) {
    for (const f of fs.readdirSync(art)) {
      if (!f.startsWith("s2-") || !f.endsWith(".json")) continue;
      const rec = readJson<{ path?: string }>(path.join(art, f), {});
      if (rec.path) named.add(rec.path);
    }
  }

  const tracked = trackedFiles(root);
  const keep = [...named].filter((rel) => {
    if (rel.includes("..") || path.isAbsolute(rel)) return false;
    if (!fs.existsSync(path.join(root, rel))) return false;          // "0.5" and friends die here
    if (!isInScope(root, path.join(root, rel), conf).inScope) return false;
    return tracked ? tracked.has(rel) : true;
  }).sort();

  return keep.length ? keep : candidateFilesForPack(root, conf);
}
