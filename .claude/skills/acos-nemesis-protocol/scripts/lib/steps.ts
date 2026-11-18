/**
 * steps.ts — the per-task STEP LEDGER (R-029, D-24).
 *
 * Every protocol step leaves an artifact; this ledger records the artifact's hash. Only the
 * Nemesis CLI and hooks (through this library) write it. A hand edit is detected: the
 * ledger carries a seal over its own entries, and `status` re-hashes every artifact.
 */
import * as fs from "node:fs";
import * as path from "node:path";
import { P, readJson, writeJson, sha256, nowIso, NEMESIS_HOME } from "./state";

export const STEP_IDS = ["S0", "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "PFC-a", "PFC-c", "PFC-d", "PFC-e"] as const;
export type StepId = (typeof STEP_IDS)[number];
export const LIST_STEPS: readonly StepId[] = ["S2", "S3"];

export interface StepMark { done: boolean; artifact?: string; sha256?: string; at?: string; by?: string; note?: string; versions?: StepMark[] }
export interface StepsLedger {
  task: string;
  entries: Record<string, StepMark | { items: StepMark[] }>;
  seal: string;
  updated_at: string;
}

function ledgerPath(root: string, task: string): string { return path.join(P.task(root, task), "steps.json"); }

/** The seal key is the per-machine Nemesis token; hooks and CLI share it, a hand editor does not. */
function sealKey(): string {
  const home = process.env.NEMESIS_HOME_OVERRIDE || NEMESIS_HOME;
  try { return fs.readFileSync(path.join(home, "seal-key"), "utf8").trim(); } catch {
    fs.mkdirSync(home, { recursive: true });
    const k = sha256(`${Date.now()}-${Math.random()}`);
    fs.writeFileSync(path.join(home, "seal-key"), k + "\n", { mode: 0o600 });
    return k;
  }
}
function computeSeal(entries: StepsLedger["entries"]): string { return sha256(sealKey() + JSON.stringify(entries)); }

export function emptyLedger(task: string): StepsLedger {
  const entries: StepsLedger["entries"] = {};
  for (const id of STEP_IDS) entries[id] = LIST_STEPS.includes(id) ? { items: [] } : { done: false };
  return { task, entries, seal: computeSeal(entries), updated_at: nowIso() };
}

export function readSteps(root: string, task: string): StepsLedger {
  const l = readJson<StepsLedger | null>(ledgerPath(root, task), null);
  return l ?? emptyLedger(task);
}

function save(root: string, l: StepsLedger): void {
  l.seal = computeSeal(l.entries);
  l.updated_at = nowIso();
  writeJson(ledgerPath(root, l.task), l);
}

/**
 * Mark a step done with its artifact. `artifact` is a path (hashed from disk) or
 * `{ inline: string }` (hashed from content, stored as a record file under the task).
 */
export function markStep(root: string, task: string, id: StepId, artifact: string | { inline: string; name: string }, by: string, note?: string): StepMark {
  const l = readSteps(root, task);
  let artifactPath: string, digest: string;
  if (typeof artifact === "string") {
    artifactPath = path.isAbsolute(artifact) ? path.relative(root, artifact) : artifact;
    digest = sha256(fs.readFileSync(path.resolve(root, artifactPath)));
  } else {
    const dir = path.join(P.task(root, task), "artifacts");
    fs.mkdirSync(dir, { recursive: true });
    const p = path.join(dir, artifact.name);
    fs.writeFileSync(p, artifact.inline);
    artifactPath = path.relative(root, p);
    digest = sha256(artifact.inline);
  }
  const mark: StepMark = { done: true, artifact: artifactPath, sha256: digest, at: nowIso(), by, note };
  if (LIST_STEPS.includes(id)) {
    (l.entries[id] as { items: StepMark[] }).items.push(mark);
  } else {
    const prev = l.entries[id] as StepMark;
    if (prev.done && (prev.artifact !== artifactPath || prev.sha256 !== digest)) mark.versions = [...(prev.versions ?? []), { ...prev, versions: undefined }];
    l.entries[id] = mark;
  }
  save(root, l);
  return mark;
}

/** Reset a step (used by rung 5 redesign for S2/S3 and by selftests). Keeps history in versions. */
export function resetStep(root: string, task: string, id: StepId, by: string): void {
  const l = readSteps(root, task);
  if (LIST_STEPS.includes(id)) {
    const cur = l.entries[id] as { items: StepMark[] };
    l.entries[`${id}.history.${Date.now()}`] = { items: cur.items };
    l.entries[id] = { items: [] };
  } else {
    const prev = l.entries[id] as StepMark;
    l.entries[id] = { done: false, versions: prev.done ? [...(prev.versions ?? []), { ...prev, versions: undefined }] : prev.versions, note: `reset by ${by}` };
  }
  save(root, l);
}

export interface StepStatus { id: string; done: boolean; count?: number; tampered: boolean; detail?: string }

/** Re-verify every mark against disk and the seal. A hand edit shows as `tampered`. */
export function stepsStatus(root: string, task: string): { steps: StepStatus[]; sealOk: boolean } {
  const l = readSteps(root, task);
  const sealOk = l.seal === computeSeal(l.entries);
  const steps: StepStatus[] = [];
  const verify = (m: StepMark): string | null => {
    if (!m.done) return null;
    if (!m.artifact || !m.sha256) return "mark without artifact";
    const p = path.resolve(root, m.artifact);
    if (!fs.existsSync(p)) return `artifact missing: ${m.artifact}`;
    return sha256(fs.readFileSync(p)) === m.sha256 ? null : `artifact changed since marked: ${m.artifact}`;
  };
  for (const id of STEP_IDS) {
    const e = l.entries[id];
    if (!e) { steps.push({ id, done: false, tampered: !sealOk }); continue; }
    if ("items" in e) {
      const bad = e.items.map(verify).filter((x): x is string => !!x);
      steps.push({ id, done: e.items.length > 0, count: e.items.length, tampered: !sealOk || bad.length > 0, detail: bad[0] });
    } else {
      const bad = verify(e);
      steps.push({ id, done: e.done, tampered: !sealOk || !!bad, detail: bad ?? undefined });
    }
  }
  return { steps, sealOk };
}

export function unfinishedSteps(root: string, task: string): string[] {
  return stepsStatus(root, task).steps.filter((s) => !s.done || s.tampered).map((s) => s.tampered ? `${s.id} (tampered: ${s.detail ?? "seal mismatch"})` : s.id);
}
