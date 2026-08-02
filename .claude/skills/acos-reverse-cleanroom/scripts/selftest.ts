#!/usr/bin/env bun
/**
 * selftest.ts — repeatable proof that the mechanical parts of the cleanroom
 * pipeline work, WITHOUT needing a live target, API keys, or Playwright.
 * Covers: fingerprint pure functions, the egress guard's three decision paths,
 * and HAR→OpenAPI inference. Run: bun selftest.ts   (exit 0 = all pass).
 */
import { mkdtempSync, writeFileSync, mkdirSync, rmSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";
import {
  normalize, shingles, forbiddenHits, sharedShingleCount, sharedChunkCount, sha256, type DirtyFingerprint,
} from "./lib/fingerprint.ts";
import { selectLayers, coverageOf, applicableLayers, LAYER_LIBRARY, type ReconSignals } from "./lib/layers.ts";
import { materialDelta, outerConverge, type PassFeatures } from "./lib/loops.ts";
import { completenessGate, protectedSetGate, buildabilityGate, traceabilityGate, mappingGate } from "./lib/gates.ts";
import { scanSecretsPII, shannonEntropy, chunkShingles, multiGranularityFingerprint } from "./lib/scan.ts";
import { spread, percentile, volatileFields, stableFields } from "./lib/stats.ts";
import { bindParity } from "./parity-bind.ts";

let pass = 0, fail = 0;
const ok = (name: string, cond: boolean) => {
  if (cond) { pass++; console.log("  PASS", name); }
  else { fail++; console.error("  FAIL", name); }
};
const dir = import.meta.dir;

// 1 — pure fingerprint functions
ok("normalize strips punctuation", normalize("Hello, World!") === "hello world");
const sh = shingles("one two three four five six seven eight nine", 8);
ok("shingles count = words-k+1 (2)", sh.size === 2);
const fp: DirtyFingerprint = {
  version: "1", session_id: "t", shingle_words: 8, shingles: [...sh],
  forbidden_tokens: ["SecretToken"], allow_hashes: [],
};
ok("forbiddenHits finds token", forbiddenHits("contains SecretToken here", fp).length === 1);
ok("forbiddenHits clean payload", forbiddenHits("nothing to see", fp).length === 0);
ok("sharedShingleCount overlap = 2", sharedShingleCount("one two three four five six seven eight nine", fp) === 2);

// 2 — egress guard integration (three decision paths)
const base = mkdtempSync(join(tmpdir(), "cr-selftest-"));
const sid = join(base, ".acos", "cleanroom", "s");
mkdirSync(join(sid, "audit"), { recursive: true });
writeFileSync(join(sid, "ACTIVE"), "");
writeFileSync(join(sid, "audit", "dirty-fingerprint.json"), JSON.stringify({
  version: "1", session_id: "s", shingle_words: 8, shingles: [],
  forbidden_tokens: ["ConvexMutation"], allow_hashes: [], max_shared_shingles: 3,
}));
const guard = (evt: unknown): number =>
  spawnSync("bun", [join(dir, "egress-guard.ts")], { input: JSON.stringify(evt), encoding: "utf8" }).status ?? -1;
ok("guard DENIES forbidden-token leak", guard({ tool_name: "WebFetch", tool_input: { body: "use ConvexMutation" }, cwd: base }) === 2);
ok("guard ALLOWS clean payload", guard({ tool_name: "WebFetch", tool_input: { body: "rebuild the form" }, cwd: base }) === 0);
ok("guard ALLOWS local tool", guard({ tool_name: "Read", tool_input: { file_path: "/x" }, cwd: base }) === 0);
// no ACTIVE marker anywhere → no-op allow
ok("guard no-op outside session", guard({ tool_name: "WebFetch", tool_input: { body: "ConvexMutation" }, cwd: tmpdir() }) === 0);

// 3 — HAR→OpenAPI inference
const har = { log: { entries: [{
  request: { method: "POST", url: "https://a/api/loans/123", postData: { text: '{"amount":100}' } },
  response: { status: 200, content: { mimeType: "application/json", text: '{"id":123,"ok":true}' } },
}] } };
const harPath = join(base, "n.har"), oasPath = join(base, "o.json");
writeFileSync(harPath, JSON.stringify(har));
spawnSync("bun", [join(dir, "har-to-openapi.ts"), harPath, oasPath], { encoding: "utf8" });
const oas = JSON.parse(readFileSync(oasPath, "utf8"));
ok("har2oas generalizes numeric id → {id}", Object.keys(oas.paths).includes("/api/loans/{id}"));
ok("har2oas infers POST method", !!oas.paths["/api/loans/{id}"]?.post);
ok("har2oas infers request schema", oas.paths["/api/loans/{id}"]?.post?.requestBody?.content?.["application/json"]?.schema?.properties?.amount?.type === "integer");

// 4 — adaptive layer selection (lib/layers.ts)
const sMin: ReconSignals = { roles: 1, detected: [] };
const selMin = selectLayers(sMin, { benchmark: 0.99 });
ok("layers: 6 core always selected", ["structure-discovery", "behavioral-capture", "contract-inference", "vision-capture", "accessibility-tree", "data-model-schema"].every((id) => selMin.selected.some((s) => s.id === id)));
ok("layers: core-role skipped at 1 role", !selMin.selected.some((s) => s.id === "auth-role-sweep"));
ok("layers: conditional skipped when signal absent", !selMin.selected.some((s) => s.id === "search-query-behavior"));
ok("layers: benchmark met via ext top-up", selMin.benchmark_met === true);
ok("layers: always-on probe present", selMin.always_on.includes("server-invisible-probe"));

const sRich: ReconSignals = { roles: 3, detected: ["search-present", "forms-or-calc", "realtime-detected"] };
const selRich = selectLayers(sRich, { benchmark: 0.99 });
ok("layers: core-role added when >1 role", selRich.selected.some((s) => s.id === "auth-role-sweep") && selRich.selected.some((s) => s.id === "authorization-matrix"));
ok("layers: conditionals fire on detected signals", ["search-query-behavior", "business-rules-validation", "realtime-transport"].every((id) => selRich.selected.some((s) => s.id === id)));
ok("layers: more signals → >= as many layers", selRich.selected.length >= selMin.selected.length);

const selPartial = selectLayers(sMin, { benchmark: 0.90 });
ok("layers: lower benchmark selects fewer ext", selPartial.selected.filter((s) => s.tier === "ext").length < selMin.selected.filter((s) => s.tier === "ext").length);
ok("layers: coverage >= benchmark after top-up", selPartial.coverage >= 0.90);

const selImposs = selectLayers(sMin, { benchmark: 1.5 });
ok("layers: unreachable benchmark terminates + not met", selImposs.benchmark_met === false && selImposs.selected.filter((s) => s.tier === "ext").length === LAYER_LIBRARY.filter((l) => l.tier === "ext").length);
ok("layers: coverageOf full applicable = 1.0", Math.abs(coverageOf(new Set(applicableLayers(sRich).map((l) => l.id)), sRich) - 1) < 1e-9);

// 5 — capture convergence loops (lib/loops.ts)
const fa: PassFeatures = { surfaces: ["/a", "/b"], intents: ["x"], rules: [], probes: [] };
const fb: PassFeatures = { surfaces: ["/a", "/b", "/c"], intents: ["x"], rules: [], probes: [] };
const d1 = materialDelta(fa, fb);
ok("loops: materialDelta detects added key", d1.material === true && d1.added.some((k) => k.includes("/c")));
ok("loops: no delta when equal", materialDelta(fa, fa).material === false);
ok("loops: normalized ignores case/space", materialDelta({ surfaces: ["/A "], intents: [], rules: [] }, { surfaces: ["/a"], intents: [], rules: [] }).material === false);
const seqConv: PassFeatures[] = [{ surfaces: ["/a"], intents: [], rules: [], probes: [] }, { surfaces: ["/a"], intents: [], rules: [], probes: [] }, { surfaces: ["/a"], intents: [], rules: [], probes: [] }];
const conv = await outerConverge(async (i) => seqConv[i], { maxReruns: 2 });
ok("loops: outerConverge converges when rerun adds nothing", conv.converged === true && conv.passes === 2);
const seqGrow: PassFeatures[] = [{ surfaces: ["/a"], intents: [], rules: [] }, { surfaces: ["/a", "/b"], intents: [], rules: [] }, { surfaces: ["/a", "/b", "/c"], intents: [], rules: [] }];
const conv2 = await outerConverge(async (i) => seqGrow[i], { maxReruns: 2 });
ok("loops: outerConverge caps at max_reruns", conv2.converged === false && conv2.passes === 3 && conv2.stopped_reason === "max_reruns");
ok("loops: cumulative unions all passes", conv2.cumulative.surfaces.length === 3);

// 6 — mechanical gates (lib/gates.ts)
const cg = completenessGate({ intents: ["I1", "I2"], surfaces: ["S1"], rules: ["R1"], parity: ["C1"] }, [{ req_id: "REQ-1", maps: ["I1", "S1"] }, { req_id: "REQ-2", maps: ["I2", "R1"] }], ["C1"]);
ok("gates: completeness PASS when all mapped/waived", cg.verdict === "PASS" && cg.unmapped.length === 0 && cg.waived === 1);
const cgFail = completenessGate({ intents: ["I1", "I9"] }, [{ req_id: "REQ-1", maps: ["I1"] }], []);
ok("gates: completeness FAIL lists unmapped", cgFail.verdict === "FAIL" && cgFail.unmapped.includes("I9"));
const ps = protectedSetGate([{ id: "F1" }, { id: "F2" }], { rule_ledger: ["F2"] });
ok("gates: protected-set BLOCK on protected cut", ps.verdict === "BLOCK" && ps.violations[0].id === "F2" && ps.violations[0].protected_by.includes("rule_ledger"));
ok("gates: protected-set OK when no protected cut", protectedSetGate([{ id: "F1" }], { behavior_critical: ["F2"] }).verdict === "OK");
const bOk = buildabilityGate([{ id: "leaf", deps: [], testable: true }, { id: "root", deps: ["leaf"], testable: true }]);
ok("gates: buildability PASS acyclic+testable leaves-first", bOk.verdict === "PASS" && bOk.order.indexOf("leaf") < bOk.order.indexOf("root"));
const bCycle = buildabilityGate([{ id: "a", deps: ["b"], testable: true }, { id: "b", deps: ["a"], testable: true }]);
ok("gates: buildability FAIL on cycle", bCycle.verdict === "FAIL" && bCycle.acyclic === false && bCycle.cycle.length === 2);
ok("gates: buildability FAIL on untestable leaf", buildabilityGate([{ id: "x", deps: [], testable: false }]).untestable.includes("x"));
ok("gates: traceability maps + waives", traceabilityGate(["I1", "REQ-2"], ["I1"], ["REQ-2"]).verdict === "PASS");
ok("gates: mappingGate dedupes items", mappingGate(["A", "A", "B"], ["A", "B"]).total === 2);

// 7 — secret/PII scan + multi-granularity (lib/scan.ts)
const findings = scanSecretsPII("email jane.doe@example.com key AKIAABCDEFGHIJKLMNOP block -----BEGIN PRIVATE KEY-----");
const ftypes = new Set(findings.map((f) => f.type));
ok("scan: finds email", ftypes.has("email"));
ok("scan: finds aws-access-key", ftypes.has("aws-access-key"));
ok("scan: finds private-key header", ftypes.has("private-key"));
ok("scan: masks tokens in report", findings.every((f) => f.token.length <= 8 || f.masked !== f.token));
ok("scan: clean prose → no findings", scanSecretsPII("the quick brown fox jumps over the lazy dog").length === 0);
ok("scan: entropy high on random token", shannonEntropy("aZ9kQ2mX7bL4pR8nW1cV6t") >= 3.6);
ok("scan: entropy low on repetition", shannonEntropy("aaaaaaaaaaaaaaaa") < 1);
ok("scan: chunkShingles whitespace-stable", chunkShingles("alpha bravo charlie delta")[0] === chunkShingles("alpha  bravo charlie   delta")[0]);
const mg = multiGranularityFingerprint("alpha bravo charlie delta echo foxtrot golf hotel india", 8);
ok("scan: multigranularity has all 3 layers", !!mg.file_hash && mg.chunk_shingles.length >= 1 && mg.phrase_shingles.length >= 1);

// 8 — stats (lib/stats.ts)
const sp = spread([10, 20, 30, 40, 100]);
ok("stats: spread min/max/mean/n", sp.min === 10 && sp.max === 100 && sp.n === 5 && sp.mean === 40);
ok("stats: percentile p50 = median", percentile([1, 2, 3, 4, 5], 0.5) === 3);
const samples = [{ a: 1, b: "x" }, { a: 2, b: "x" }];
ok("stats: volatile field detected, stable excluded", volatileFields(samples).includes("a") && !volatileFields(samples).includes("b"));
ok("stats: stable field is the complement", stableFields(samples).includes("b") && !stableFields(samples).includes("a"));

// 9 — capture-diff CLI (outer-loop exit codes)
const cdPrev = join(base, "cd-prev.json"), cdNext = join(base, "cd-next.json");
writeFileSync(cdPrev, JSON.stringify({ surfaces: ["/a"], intents: [], rules: [] }));
writeFileSync(cdNext, JSON.stringify({ surfaces: ["/a"], intents: [], rules: [] }));
ok("capture-diff: exit 0 when converged", (spawnSync("bun", [join(dir, "capture-diff.ts"), "--prev", cdPrev, "--next", cdNext], { encoding: "utf8" }).status ?? -1) === 0);
writeFileSync(cdNext, JSON.stringify({ surfaces: ["/a", "/b"], intents: [], rules: [] }));
ok("capture-diff: exit 3 when material", (spawnSync("bun", [join(dir, "capture-diff.ts"), "--prev", cdPrev, "--next", cdNext], { encoding: "utf8" }).status ?? -1) === 3);

// 10 — gate.ts CLI (exit codes the orchestrator branches on)
const gKept = join(base, "kept.json"), gReq = join(base, "req.json");
writeFileSync(gKept, JSON.stringify({ intents: ["I1"], surfaces: [], rules: [], parity: [] }));
writeFileSync(gReq, JSON.stringify([{ req_id: "REQ-1", maps: ["I1"] }]));
ok("gate.ts completeness PASS → exit 0", (spawnSync("bun", [join(dir, "gate.ts"), "completeness", "--kept", gKept, "--requirements", gReq], { encoding: "utf8" }).status ?? -1) === 0);
writeFileSync(gReq, JSON.stringify([{ req_id: "REQ-1", maps: ["I9"] }]));
ok("gate.ts completeness FAIL → exit 1", (spawnSync("bun", [join(dir, "gate.ts"), "completeness", "--kept", gKept, "--requirements", gReq], { encoding: "utf8" }).status ?? -1) === 1);
const gCuts = join(base, "cuts.json"), gProt = join(base, "prot.json");
writeFileSync(gCuts, JSON.stringify([{ id: "F2" }]));
writeFileSync(gProt, JSON.stringify({ rule_ledger: ["F2"] }));
ok("gate.ts protected-set BLOCK → exit 1", (spawnSync("bun", [join(dir, "gate.ts"), "protected-set", "--cuts", gCuts, "--protected", gProt], { encoding: "utf8" }).status ?? -1) === 1);
const gComp = join(base, "comp.json");
writeFileSync(gComp, JSON.stringify([{ id: "leaf", deps: [], testable: true }, { id: "root", deps: ["leaf"], testable: true }]));
ok("gate.ts buildability PASS → exit 0", (spawnSync("bun", [join(dir, "gate.ts"), "buildability", "--components", gComp], { encoding: "utf8" }).status ?? -1) === 0);

// 11 — select-layers CLI
const slSig = join(base, "signals.json"), slOut = join(base, "selected.json");
writeFileSync(slSig, JSON.stringify({ roles: 2, detected: ["search-present"] }));
const slRun = spawnSync("bun", [join(dir, "select-layers.ts"), "--signals", slSig, "--benchmark", "0.99", "--out", slOut], { encoding: "utf8" });
const slSelected = JSON.parse(readFileSync(slOut, "utf8"));
ok("select-layers CLI: exit 0 + writes selection", (slRun.status ?? -1) === 0 && slSelected.benchmark_met === true);
ok("select-layers CLI: search signal → search layer", slSelected.selected.some((s: any) => s.id === "search-query-behavior"));

// 12 — parity-bind (Phase-6 parity-as-verifier wiring)
const pbComps: any[] = [{ id: "c1", req: "REQ-1" }, { id: "c2", req: "REQ-2" }, { id: "c3" }];
const pb = bindParity(pbComps, ["CASE-A", "CASE-B", "CASE-Z"], [{ req_id: "REQ-1", parity: ["CASE-A"] }, { req_id: "REQ-2", maps: ["CASE-B"] }]);
ok("parity-bind: binds requirement → parity case", pb.report.bound === 2 && pbComps[0].verifier.auto_check.case_ids.includes("CASE-A"));
ok("parity-bind: reports unbound component", pb.report.unbound.some((u) => u.id === "c3"));
ok("parity-bind: reports orphan case", pb.report.orphan_cases.includes("CASE-Z"));

// 13 — egress guard chunk-overlap path (multi-granularity fingerprint)
const baseChunk = mkdtempSync(join(tmpdir(), "cr-chunk-"));
const sidChunk = join(baseChunk, ".acos", "cleanroom", "c");
mkdirSync(join(sidChunk, "audit"), { recursive: true });
writeFileSync(join(sidChunk, "ACTIVE"), "");
const dirtyPara = "the internal reconciliation ledger reference alpha bravo charlie";
writeFileSync(join(sidChunk, "audit", "dirty-fingerprint.json"), JSON.stringify({
  version: "1", session_id: "c", shingle_words: 8, shingles: [], forbidden_tokens: [], allow_hashes: [], max_shared_shingles: 3, chunk_shingles: chunkShingles(dirtyPara),
}));
const guardC = (evt: unknown): number => spawnSync("bun", [join(dir, "egress-guard.ts")], { input: JSON.stringify(evt), encoding: "utf8" }).status ?? -1;
ok("guard DENIES verbatim dirty paragraph (chunk fp)", guardC({ tool_name: "WebFetch", tool_input: { body: dirtyPara }, cwd: baseChunk }) === 2);
ok("guard ALLOWS unrelated paragraph (chunk fp)", guardC({ tool_name: "WebFetch", tool_input: { body: "completely unrelated clean sentence written here now" }, cwd: baseChunk }) === 0);
rmSync(baseChunk, { recursive: true, force: true });

// 14 — fingerprint-build --secret-scan folds a planted secret into forbidden tokens
const sidFp = mkdtempSync(join(tmpdir(), "cr-fp-"));
mkdirSync(join(sidFp, "01-intent"), { recursive: true });
writeFileSync(join(sidFp, "01-intent", "notes.md"), "the api key is AKIAABCDEFGHIJKLMNOP do not leak it");
spawnSync("bun", [join(dir, "fingerprint-build.ts"), sidFp, "--secret-scan", "--multigranularity"], { encoding: "utf8" });
const builtFp = JSON.parse(readFileSync(join(sidFp, "audit", "dirty-fingerprint.json"), "utf8"));
ok("fingerprint-build --secret-scan arms scanned secret", builtFp.forbidden_tokens.includes("AKIAABCDEFGHIJKLMNOP"));
ok("fingerprint-build --multigranularity adds chunk_shingles", Array.isArray(builtFp.chunk_shingles) && builtFp.chunk_shingles.length >= 1);
rmSync(sidFp, { recursive: true, force: true });

rmSync(base, { recursive: true, force: true });
console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
