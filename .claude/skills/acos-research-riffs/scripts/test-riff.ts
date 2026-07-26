#!/usr/bin/env bun
/**
 * End-to-end smoke test for the riff state engine.
 *
 * Drives the real CLI against a throwaway project root and asserts the behaviour
 * the design depends on: append-only supersession, per-dimension saturation
 * (including the rule that an unprobed dimension can never pass), dedup, the
 * three-way sufficiency routing, moderator selection of unsurfaced material, and
 * report bundle assembly.
 *
 * Run:  bun .claude/skills/acos-research-riffs/scripts/test-riff.ts
 */

import { mkdtempSync, rmSync, writeFileSync, existsSync, readFileSync, utimesSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const CLI = join(HERE, "riff.ts");
const ROOT = mkdtempSync(join(tmpdir(), "riff-test-"));

let pass = 0;
let failed = 0;
const failures: string[] = [];

function check(name: string, cond: boolean, detail?: unknown): void {
  if (cond) {
    pass++;
    console.log(`  ok   ${name}`);
  } else {
    failed++;
    failures.push(name);
    console.log(`  FAIL ${name}${detail !== undefined ? ` :: ${JSON.stringify(detail)}` : ""}`);
  }
}

function run(...args: string[]): { code: number; out: string; err: string } {
  const p = Bun.spawnSync(["bun", CLI, ...args], {
    env: { ...process.env, RIFF_ROOT: ROOT },
    stdout: "pipe",
    stderr: "pipe",
  });
  return {
    code: p.exitCode,
    out: new TextDecoder().decode(p.stdout).trim(),
    err: new TextDecoder().decode(p.stderr).trim(),
  };
}

function json(...args: string[]): any {
  const r = run(...args);
  if (r.code !== 0) throw new Error(`riff ${args.join(" ")} exited ${r.code}: ${r.err}`);
  try {
    return JSON.parse(r.out);
  } catch {
    return r.out;
  }
}

function tmpJson(name: string, value: unknown): string {
  const p = join(ROOT, name);
  writeFileSync(p, JSON.stringify(value), "utf8");
  return p;
}

console.log(`riff smoke test — throwaway root ${ROOT}\n`);

try {
  // -- preflight ------------------------------------------------------------
  console.log("preflight");
  const pre = json("preflight");
  check("preflight reports ok", pre.ok === true, pre);
  check("preflight finds no resumable session", pre.resumable === null, pre.resumable);

  // -- init -----------------------------------------------------------------
  console.log("\ninit + brief");
  const init = json("init", "--topic", "Which vector store for a small RAG app", "--tier", "standard");
  const S = init.session_id as string;
  check("session id is date-prefixed", /^\d{4}-\d{2}-\d{2}-/.test(S), S);
  check("phase starts at scope", init.phase === "scope", init.phase);

  const briefPath = join(ROOT, "brief.md");
  writeFileSync(
    briefPath,
    "# Research brief\n\nQuestion of record: which vector store should a small retrieval app use?\nMust cover managed platforms, self-hosted options, pricing, and licensing.\n",
    "utf8",
  );
  const b = json("brief", "--file", briefPath, "--session", S);
  check("brief installed", b.bytes > 0 && existsSync(b.brief), b);

  const reinit = run("init", "--topic", "Which vector store for a small RAG app", "--tier", "standard");
  check(
    "re-init refuses to clobber an existing session",
    reinit.code !== 0 && reinit.err.includes("already exists"),
    reinit.err,
  );

  // -- coverage -------------------------------------------------------------
  console.log("\ncoverage dimensions + saturation");
  const dims = tmpJson("dims.json", [
    { id: "managed", name: "Managed vector platforms", why: "the default buy option" },
    { id: "selfhost", name: "Self-hosted engines", why: "the default build option" },
    { id: "pricing", name: "Pricing and limits", why: "decides feasibility" },
  ]);
  const cov = json("coverage", "init", "--session", S, "--json", dims);
  check("three dimensions declared", cov.dimensions === 3, cov);

  let gate = json("gate", "--session", S);
  check("gate blocks while everything is unprobed", gate.passed === false, gate.reason);
  check("gate names all three as blocking", gate.blocking.length === 3, gate.blocking);

  // saturation: novel then two dry probes
  json("coverage", "probe", "managed", "--session", S, "--novel", "4", "--note", "wide sweep");
  let d = json("coverage", "probe", "managed", "--session", S, "--novel", "0", "--note", "dry 1");
  check("dry streak increments", d.dry_streak === 1, d);
  d = json("coverage", "probe", "managed", "--session", S, "--novel", "0", "--note", "dry 2");
  check("two dry probes saturate the dimension", d.status === "saturated", d);

  // novelty resets the streak
  json("coverage", "probe", "selfhost", "--session", S, "--novel", "0");
  d = json("coverage", "probe", "selfhost", "--session", S, "--novel", "3");
  check("novelty resets the dry streak", d.dry_streak === 0, d);
  check("dimension with novelty is thin, not saturated", d.status === "thin", d.status);

  gate = json("gate", "--session", S);
  check("gate still blocks on an unprobed dimension", gate.passed === false, gate.reason);
  check(
    "unprobed dimension is reported as unprobed, never saturated",
    gate.blocking.some((x: any) => x.id === "pricing" && x.status === "unprobed"),
    gate.blocking,
  );

  // an agent reporting its own loop went dry counts as evidence, in one probe
  console.log("\nsaturation shortcuts");
  json("coverage", "add", "--session", S, "--json", tmpJson("dim-sat.json", { id: "sat-test", name: "Agent-saturated", why: "test" }));
  json("coverage", "probe", "sat-test", "--session", S, "--novel", "5", "--agent-saturated", "--note", "seat self-reported dry");
  const satTable = String(json("coverage", "show", "--session", S));
  check("agent-reported saturation closes a dimension in one probe", /saturated\s+sat-test/.test(satTable), satTable);

  // attestation may settle a thin dimension, but never an unprobed one
  json("coverage", "add", "--session", S, "--json", tmpJson("dim-extra.json", { id: "extra", name: "Extra", why: "test" }));
  const cannotAttest = run("coverage", "attest", "extra", "--session", S, "--by", "auditor", "--note", "looks fine");
  check(
    "attestation refuses an unprobed dimension",
    cannotAttest.code !== 0 && cannotAttest.err.includes("never been probed"),
    cannotAttest.err,
  );
  json("coverage", "probe", "extra", "--session", S, "--novel", "2");
  const attested = json("coverage", "attest", "extra", "--session", S, "--by", "auditor", "--note", "one seat covered this thoroughly");
  check("attestation settles a probed thin dimension", attested.status === "attested", attested);
  check("attestation records who and why", attested.attested_by === "auditor" && !!attested.attested_note, attested);
  check(
    "attestation is ledgered as a judgment call",
    json("ledger", "show", "--session", S, "--type", "stop-decision").some((e: any) => e.body.includes("attested")),
    null,
  );
  const noNote = run("coverage", "attest", "extra", "--session", S, "--by", "auditor");
  check("attestation requires a stated basis", noNote.code !== 0, noNote.err);

  // -- panel ----------------------------------------------------------------
  console.log("\npanel validation");
  const badPanel = tmpJson("bad-panel.json", [
    {
      slug: "a",
      role: "researcher",
      title: "A",
      objective: "o",
      lane: "same lane",
      not_lane: "x",
      dimensions: [],
    },
    {
      slug: "b",
      role: "researcher",
      title: "B",
      objective: "o",
      lane: "same lane",
      not_lane: "x",
      dimensions: [],
    },
  ]);
  const bad = json("panel", "set", "--session", S, "--json", badPanel);
  check("missing generalist is flagged", bad.problems.some((p: string) => p.includes("generalist")), bad.problems);
  check("missing skeptic is flagged", bad.problems.some((p: string) => p.includes("skeptic")), bad.problems);
  check("overlapping lanes are flagged", bad.problems.some((p: string) => p.includes("overlapping")), bad.problems);

  const approveBlocked = run("panel", "approve", "--session", S);
  check("approve refuses an invalid panel", approveBlocked.code !== 0, approveBlocked.err.slice(0, 80));

  const goodPanel = tmpJson("panel.json", [
    {
      slug: "managed-scout",
      role: "researcher",
      title: "Managed platform scout",
      objective: "Map the managed options",
      lane: "hosted vector databases and their limits",
      not_lane: "self-hosted engines, licensing",
      dimensions: ["managed", "pricing"],
    },
    {
      slug: "generalist",
      role: "generalist",
      title: "Basic facts",
      objective: "Cover fundamentals the specialists skip",
      lane: "what a vector store is, the standard decision factors",
      not_lane: "deep vendor comparison",
      dimensions: [],
    },
    {
      slug: "skeptic",
      role: "skeptic",
      title: "Skeptic",
      objective: "Refute the emerging consensus",
      lane: "what the other seats will miss; failure cases",
      not_lane: "cheerleading any option",
      dimensions: ["selfhost"],
    },
  ]);
  const good = json("panel", "set", "--session", S, "--json", goodPanel);
  check("valid panel has no problems", good.problems.length === 0, good.problems);
  const appr = json("panel", "approve", "--session", S);
  check("valid panel approves", appr.approved === true, appr);

  // -- charters -------------------------------------------------------------
  console.log("\ncharter rendering");
  const ch = json("charter", "managed-scout", "--session", S);
  const charterText = readFileSync(ch.charter, "utf8");
  check("charter written", existsSync(ch.charter), ch);
  check("charter has no unresolved placeholders", !/\{\{[A-Z_]+\}\}/.test(charterText),
    charterText.match(/\{\{[A-Z_]+\}\}/g));
  check("charter carries the lane", charterText.includes("hosted vector databases"), null);
  check("charter carries the exclusion", charterText.includes("self-hosted engines, licensing"), null);
  check("charter carries the search cap", charterText.includes("15 searches"), null);
  check("charter carries the brief", charterText.includes("Question of record"), null);

  for (const seat of ["generalist", "skeptic"]) {
    const c = json("charter", seat, "--session", S);
    const t = readFileSync(c.charter, "utf8");
    check(`${seat} charter renders clean`, !/\{\{[A-Z_]+\}\}/.test(t), t.match(/\{\{[A-Z_]+\}\}/g));
  }
  const badSeat = run("charter", "no-such-seat", "--session", S);
  check("charter rejects an unknown seat", badSeat.code !== 0, badSeat.err);

  // -- one-shot role charters ----------------------------------------------
  console.log("\none-shot role charters");
  const probe = json("render", "probe", "--session", S, "--question", "what is the SOC 2 status", "--dimension", "managed");
  const probeText = readFileSync(probe.charter, "utf8");
  check("probe charter auto-slugs", probe.slug === "probe-01", probe);
  check("probe charter has no placeholders", !/\{\{[A-Z_]+\}\}/.test(probeText),
    probeText.match(/\{\{[A-Z_]+\}\}/g));
  check("probe charter carries the question", probeText.includes("what is the SOC 2 status"), null);
  check("probe dispatch is ledgered", json("ledger", "show", "--session", S, "--type", "question").length >= 1, null);
  const probe2 = json("render", "probe", "--session", S, "--question", "second question");
  check("probe slugs increment", probe2.slug === "probe-02", probe2);

  for (const role of ["auditor", "compiler", "citer", "eval"]) {
    const r = json("render", role, "--session", S);
    const t = readFileSync(r.charter, "utf8");
    check(`${role} charter has no placeholders`, !/\{\{[A-Z_]+\}\}/.test(t), t.match(/\{\{[A-Z_]+\}\}/g));
    check(`${role} charter knows the session root`, t.includes(S), null);
  }
  const badRole = run("render", "nonsense", "--session", S);
  check("unknown role rejected", badRole.code !== 0, badRole.err);

  // -- claims + dedup -------------------------------------------------------
  console.log("\nclaims ingest + dedup");
  const claims1 = tmpJson("claims1.json", [
    {
      claim: "Pinecone is a managed vector database with a serverless tier",
      dimension: "managed",
      question: "what managed options exist?",
      sources: [{ source: "Pinecone docs", url: "https://example.test/pinecone", tier: 1, as_of: "2026-07-22" }],
      as_of: "2026-07-22",
      agent: "managed-scout",
    },
    {
      claim: "Weaviate offers both managed cloud and self-hosted deployment",
      dimension: "managed",
      sources: [{ source: "Weaviate docs", url: "https://example.test/weaviate", tier: 1, as_of: "2026-07-22" }],
      as_of: "2026-07-22",
      agent: "managed-scout",
    },
    {
      claim: "Managed vector pricing is quoted per million vectors stored per month",
      dimension: "pricing",
      sources: [{ source: "Vendor pricing page", url: "https://example.test/pricing", tier: 1, as_of: "2026-07-22" }],
      as_of: "2026-07-22",
      agent: "managed-scout",
      volatile: true,
    },
  ]);
  const added1 = json("claims", "add", "--session", S, "--slug", "managed-scout", "--json", claims1);
  check("three claims ingested", added1.added === 3, added1);

  const claims2 = tmpJson("claims2.json", [
    { claim: "Pinecone is a managed vector database with a serverless tier", sources: [], as_of: "2026-07-22" },
    {
      claim: "LanceDB is an embedded vector store that runs in-process with no server",
      dimension: "selfhost",
      sources: [{ source: "LanceDB docs", url: "https://example.test/lancedb", tier: 1, as_of: "2026-07-22" }],
      as_of: "2026-07-22",
      agent: "skeptic",
    },
    {
      claim: "Self-hosted engines shift operational burden onto the team running them",
      dimension: "selfhost",
      sources: [{ source: "Engineering blog", url: "https://example.test/ops", tier: 4, as_of: "2026-07-22" }],
      as_of: "2026-07-22",
      agent: "skeptic",
    },
  ]);
  const added2 = json("claims", "add", "--session", S, "--slug", "skeptic", "--json", claims2);
  check("duplicate claim rejected", added2.duplicates === 1, added2);
  check("novel claims accepted", added2.added === 2, added2);

  const found = json("claims", "search", "serverless", "--session", S);
  check("search finds the seeded claim", Array.isArray(found) && found.length > 0, found);

  // agents write their own claims file; ingest must read it in place, not re-add it
  const agentWritten = join(ROOT, ".acos", "riffs", S, "dossiers", "generalist.claims.jsonl");
  writeFileSync(
    agentWritten,
    [
      JSON.stringify({
        claim: "Vector search quality depends on the embedding model, not only the store",
        dimension: "selfhost",
        sources: [{ source: "Docs", url: "https://example.test/embed", tier: 1, as_of: "2026-07-22" }],
        as_of: "2026-07-22",
      }),
      JSON.stringify({
        claim: "Pinecone is a managed vector database with a serverless tier",
        sources: [{ source: "dup", url: "https://example.test/pinecone", tier: 1 }],
        as_of: "2026-07-22",
      }),
      "{ this is not valid json",
      "",
    ].join("\n"),
    "utf8",
  );
  const ing = json("claims", "ingest", "--session", S, "--slug", "generalist");
  check("ingest reads the agent-written file", ing.total_read === 3, ing);
  check("ingest keeps novel claims", ing.added === 1, ing);
  check("ingest drops cross-dossier duplicates", ing.duplicates === 1, ing);
  check("ingest counts malformed lines", ing.malformed === 1, ing);
  check("ingest reports novelty per dimension", ing.novel_by_dimension.selfhost === 1, ing.novel_by_dimension);
  const reIngest = json("claims", "ingest", "--session", S, "--slug", "generalist");
  check("re-ingest is idempotent, not self-duplicating", reIngest.added === 1 && reIngest.duplicates === 0, reIngest);
  const missing = run("claims", "ingest", "--session", S, "--slug", "never-ran");
  check("ingest errors when the agent wrote nothing", missing.code !== 0 && missing.err.includes("no claims file"), missing.err);

  // -- sufficiency routing --------------------------------------------------
  console.log("\nsufficiency routing");
  const miss = json("ask", "what is the SOC 2 audit status of each vendor", "--session", S);
  check("unknown question abstains", miss.label === "not-in-corpus", miss);
  check("abstention instructs a dispatch", /ABSTAIN/.test(miss.action), miss.action);

  const hit = json("ask", "which managed vector database options exist", "--session", S);
  check("known question is answerable", hit.label !== "not-in-corpus", hit);
  check("answerable question returns hits", hit.hits.length > 0, hit.hits.length);
  check("verified requires 2+ independent sources", hit.label === "verified" ? hit.independent_sources >= 2 : true, hit);

  const vol = json("ask", "how is managed vector pricing quoted", "--session", S);
  check("volatile claims raise the volatile flag", vol.volatile === true, vol);

  // weak lexical overlap must abstain, not answer "provisionally" from unrelated evidence
  const weak = json("ask", "what are the licensing terms for offshore drilling equipment", "--session", S);
  check("weak overlap abstains rather than answering", weak.label === "not-in-corpus", weak);
  const forced = json("ask", "which managed vector database options exist", "--session", S, "--strong", "0.99");
  check("strength floor is tunable", forced.label === "not-in-corpus", forced.reason);

  // -- moderator ------------------------------------------------------------
  console.log("\nmoderator");
  const pick1 = json("moderator", "--session", S);
  check("moderator finds unsurfaced material", pick1.claim_id !== undefined, pick1);
  const pick2 = json("moderator", "--session", S);
  check("moderator does not repeat itself", pick2.claim_id !== pick1.claim_id, { pick1, pick2 });

  json("mode", "direct", "--session", S);
  const quiet = json("moderator", "--session", S);
  check("direct mode silences the moderator", quiet.pick === null, quiet);
  json("mode", "standard", "--session", S);

  // -- ledger ---------------------------------------------------------------
  console.log("\nledger: append-only + supersession");
  const e1 = json(
    "ledger",
    "add",
    "--session",
    S,
    "--json",
    tmpJson("e1.json", {
      type: "finding",
      body: "Managed platforms look like the default choice for a small app",
      confidence: "provisional",
      author: { agent: "riff", model: "test" },
    }),
  );
  check("entry gets a sequential id", /^L-\d{4}$/.test(e1.id), e1);

  const e2 = json(
    "ledger",
    "supersede",
    e1.id,
    "--session",
    S,
    "--json",
    tmpJson("e2.json", {
      body: "Corrected: an embedded store fits this app better than a managed platform",
      context: "The skeptic seat found the app never leaves one process",
      confidence: "verified",
    }),
  );
  check("supersession recorded", e2.supersedes === e1.id, e2);

  const entries = json("ledger", "show", "--session", S);
  const old = entries.find((x: any) => x.id === e1.id);
  const nu = entries.find((x: any) => x.id === e2.id);
  check("superseded entry is still on disk", old !== undefined, null);
  check("superseded status is derived", old.status === "superseded", old.status);
  check("superseded entry points forward", old.superseded_by === e2.id, old.superseded_by);
  check("replacement is active", nu.status === "active", nu.status);

  const ch2 = json("ledger", "chains", "--session", S);
  check("supersession chain reconstructed", ch2.length >= 1 && ch2[0].length === 2, ch2);

  const stopEntries = json("ledger", "show", "--session", S, "--type", "stop-decision");
  check("saturation wrote an evidenced stop-decision", stopEntries.length >= 1, stopEntries.length);

  const activeOnly = json("ledger", "show", "--session", S, "--active");
  check("active filter excludes superseded", !activeOnly.some((x: any) => x.id === e1.id), null);

  // -- tree -----------------------------------------------------------------
  console.log("\nconcept tree");
  json("tree", "insert", "--session", S, "--claim", "managed-scout-001", "--concept", "options/managed");
  json("tree", "insert", "--session", S, "--claim", "managed-scout-002", "--concept", "options/managed");
  json("tree", "insert", "--session", S, "--claim", "skeptic-001", "--concept", "options/embedded");
  const outlineText = json("tree", "show", "--session", S);
  check("outline renders concepts", String(outlineText).includes("managed"), outlineText);
  check("outline counts claims", String(outlineText).includes("2 claims"), outlineText);

  const auto = json("tree", "autofile", "--session", S);
  check("autofile files every unfiled claim", auto.filed > 0, auto);
  check("autofile skips claims already in the tree", auto.skipped >= 3, auto);
  const auto2 = json("tree", "autofile", "--session", S);
  check("autofile is idempotent", auto2.filed === 0 && auto2.skipped > 0, auto2);
  const badBy = run("tree", "autofile", "--session", S, "--by", "nonsense");
  check("autofile rejects an unknown grouping", badBy.code !== 0, badBy.err);

  for (let i = 0; i < 12; i++) {
    json("tree", "insert", "--session", S, "--claim", `bulk-${i}`, "--concept", "pricing");
  }
  const reorg = json("tree", "reorg", "--session", S);
  check("overgrown concept flagged for reorg", reorg.length === 1 && reorg[0].concept === "pricing", reorg);
  const applied = json(
    "tree",
    "apply",
    "--session",
    S,
    "--concept",
    "pricing",
    "--json",
    tmpJson("groups.json", [
      { name: "storage", claim_ids: reorg[0].claim_ids.slice(0, 6) },
      { name: "egress", claim_ids: reorg[0].claim_ids.slice(6) },
    ]),
  );
  check("reorg split into subtopics", applied.children.length === 2, applied);
  check("reorg cleared the parent", applied.left.length === 0, applied.left);
  check("reorg pending list is now empty", json("tree", "reorg", "--session", S).length === 0, null);

  // -- panel mutation -------------------------------------------------------
  console.log("\npanel mutation");
  json(
    "panel",
    "add",
    "--session",
    S,
    "--json",
    tmpJson("seat.json", {
      slug: "licensing",
      role: "researcher",
      title: "Licensing",
      objective: "Check licence terms",
      lane: "open-source licences and commercial restrictions",
      not_lane: "pricing",
      dimensions: [],
      rationale: "user steered here mid-conversation",
    }),
  );
  json("panel", "retire", "licensing", "--session", S, "--note", "answered inside another seat");
  const changes = json("ledger", "show", "--session", S, "--type", "panel-change");
  check("panel changes are ledgered with rationale", changes.length === 2, changes.length);

  // -- gate pass ------------------------------------------------------------
  console.log("\ngate closure");
  json("coverage", "probe", "pricing", "--session", S, "--novel", "2");
  json("coverage", "probe", "pricing", "--session", S, "--novel", "0");
  json("coverage", "probe", "pricing", "--session", S, "--novel", "0");
  json("coverage", "probe", "selfhost", "--session", S, "--novel", "0");
  json("coverage", "probe", "selfhost", "--session", S, "--novel", "0");
  gate = json("gate", "--session", S);
  check("gate passes once every dimension is settled", gate.passed === true, gate);

  // -- report ---------------------------------------------------------------
  console.log("\nreport bundle + citation audit");
  const bundle = json("report", "bundle", "--session", S);
  const bundleText = readFileSync(bundle.bundle, "utf8");
  check("bundle written", existsSync(bundle.bundle), bundle);
  check("bundle carries the brief", bundleText.includes("Question of record"), null);
  check("bundle carries the negative-space table", bundleText.includes("negative-space record"), null);
  check("bundle carries supersession chains", bundleText.includes(e1.id) && bundleText.includes(e2.id), null);
  check("bundle flags volatile claims", bundleText.includes("VOLATILE"), null);
  check("clean bundle has no uncitable claims", !bundleText.includes("do not cite this claim"), null);

  // a claim with no source must be marked uncitable rather than quietly included
  json(
    "claims",
    "add",
    "--session",
    S,
    "--slug",
    "generalist",
    "--json",
    tmpJson("sourceless.json", [
      { claim: "Embedding dimensionality affects index size in some way", sources: [], as_of: "2026-07-22" },
    ]),
  );
  const bundle2 = json("report", "bundle", "--session", S);
  const bundleText2 = readFileSync(bundle2.bundle, "utf8");
  check("sourceless claim is marked uncitable", bundleText2.includes("do not cite this claim"), null);
  check("bundle carries compiler instructions", bundleText.includes("Compiler instructions"), null);
  check("bundle omits the gate warning when the gate passed", !bundleText.includes("COVERAGE GATE DID NOT PASS"), null);

  // an un-ingested dossier must be flagged loudly, not silently omitted
  writeFileSync(
    join(ROOT, ".acos", "riffs", S, "dossiers", "orphan.claims.jsonl"),
    JSON.stringify({ claim: "Never ingested, so it has no id", sources: [], as_of: "2026-07-22" }) + "\n",
    "utf8",
  );
  const bundleOrphan = readFileSync(json("report", "bundle", "--session", S).bundle, "utf8");
  check("bundle warns about un-ingested claims", bundleOrphan.includes("never ingested"), null);
  const evalOrphan = json("eval", "--session", S, "--json");
  check(
    "eval fails when a dossier was never ingested",
    evalOrphan.checks.find((c: any) => c.id === "everything-ingested").verdict === "fail",
    evalOrphan.checks.find((c: any) => c.id === "everything-ingested"),
  );
  const statOrphan = json("status", "--session", S);
  check("status counts pending ingest", statOrphan.corpus.pending_ingest === 1, statOrphan.corpus);
  rmSync(join(ROOT, ".acos", "riffs", S, "dossiers", "orphan.claims.jsonl"));

  const fakeReport = join(ROOT, "fake-report.md");
  writeFileSync(
    fakeReport,
    "Managed options exist (managed-scout-001). A ghost citation (managed-scout-999) should be caught.\n",
    "utf8",
  );
  const audit = json("report", "audit", "--session", S, "--file", fakeReport);
  check("audit catches an unknown claim id", audit.unknown_ids.includes("managed-scout-999"), audit);
  check("audit fails on a bad citation", audit.verdict.startsWith("FAIL"), audit.verdict);

  // -- self-evaluation ------------------------------------------------------
  console.log("\nself-evaluation");
  const ev = json("eval", "--session", S, "--json");
  check("eval returns a verdict", ["PASS", "WARN", "FAIL"].includes(ev.verdict), ev.verdict);
  check("eval runs every check", ev.checks.length >= 9, ev.checks.length);
  check(
    "eval passes coverage once the gate is closed",
    ev.checks.find((c: any) => c.id === "coverage-complete").verdict !== "fail",
    ev.checks.find((c: any) => c.id === "coverage-complete"),
  );
  check(
    "eval flags the sourceless claim",
    ev.checks.find((c: any) => c.id === "sourceless-claims").verdict === "warn",
    ev.checks.find((c: any) => c.id === "sourceless-claims"),
  );
  check(
    "eval confirms the mandatory seats",
    ev.checks.find((c: any) => c.id === "panel-structure").verdict === "pass",
    ev.checks.find((c: any) => c.id === "panel-structure"),
  );
  check(
    "eval distinguishes no-conversation from moderator under-use",
    /no conversation took place|surfaced across/.test(
      ev.checks.find((c: any) => c.id === "research-reached-the-reader").measured,
    ),
    ev.checks.find((c: any) => c.id === "research-reached-the-reader").measured,
  );
  check(
    "eval warns when no report exists yet",
    ev.checks.find((c: any) => c.id === "citations-resolve").verdict === "warn",
    ev.checks.find((c: any) => c.id === "citations-resolve"),
  );
  check("every eval check explains why it matters", ev.checks.every((c: any) => c.why_it_matters.length > 20), null);
  const evText = run("eval", "--session", S);
  check("eval renders human-readable output", evText.code === 0 && evText.out.includes("mechanical self-check"), evText.err);

  // -- citation verdict freshness -------------------------------------------
  // The Phase 5 loop rewrites the report each round; the verdict file does not
  // rewrite itself. In the first real session that left a round-1 FAIL on disk
  // describing a report that three later rounds had fixed. mtime catches it
  // without needing the citer to cooperate.
  console.log("\ncitation verdict freshness");
  const reportDir = join(ROOT, ".acos", "riffs", S, "report");
  const cvCheck = () => json("eval", "--session", S, "--json").checks.find((c: any) => c.id === "citation-verdict-current");
  check("no verdict check runs before a report exists", cvCheck() === undefined, cvCheck());

  writeFileSync(join(reportDir, "REPORT.md"), "# Report\n\nA finding [generalist-001].\n");
  check(
    "missing verdict file warns once a report exists",
    cvCheck()?.verdict === "warn" && /no CITATIONS/.test(cvCheck().measured),
    cvCheck(),
  );

  const older = new Date(Date.now() - 600_000);
  writeFileSync(join(reportDir, "CITATIONS.md"), "# Citation verification\n\n## Verdict: **FAIL** — 3 unsupported statements\n");
  utimesSync(join(reportDir, "CITATIONS.md"), older, older);
  check("a verdict written before the report it checks is stale", cvCheck()?.verdict === "fail", cvCheck());
  check(
    "the stale message names both timestamps so it can be argued with",
    /before REPORT\.md's own/.test(cvCheck().measured),
    cvCheck().measured,
  );

  // Round 3 rewrites the verdict. Fresh + PASS is the only state that passes.
  writeFileSync(join(reportDir, "CITATIONS.md"), "# Citation verification\n\n## Verdict: **PASS** — zero regressions\n");
  check("a fresh PASS passes", cvCheck()?.verdict === "pass", cvCheck());

  // A fresh FAIL is still a fail: it means a known-bad report was delivered.
  writeFileSync(join(reportDir, "CITATIONS.md"), "# Citation verification\n\n**Verdict:** FAIL\n");
  check("a fresh FAIL still fails", cvCheck()?.verdict === "fail", cvCheck());

  // Per-round filenames must work without the engine knowing the scheme, and
  // the NEWEST file is the one that counts.
  writeFileSync(join(reportDir, "CITATIONS-r3.md"), "# Round 3\n\n## Verdict: PASS\n");
  check(
    "the newest CITATIONS*.md wins, whatever it is called",
    cvCheck()?.verdict === "pass" && cvCheck().measured.includes("CITATIONS-r3.md"),
    cvCheck(),
  );

  writeFileSync(join(reportDir, "CITATIONS-r3.md"), "# Round 3\n\nWe considered whether this would fail.\n");
  check("a verdict file with no verdict line warns rather than guessing", cvCheck()?.verdict === "warn", cvCheck());

  rmSync(join(reportDir, "CITATIONS.md"));
  rmSync(join(reportDir, "CITATIONS-r3.md"));
  rmSync(join(reportDir, "REPORT.md"));

  // -- room -----------------------------------------------------------------
  console.log("\nroom state + server");
  const rs = json("room", "--state", "--no-open", "--session", S);
  check("room state has every panel the page renders",
    ["coverage", "claims_recent", "moderator", "ledger", "panel", "outline", "eval", "gate"].every(
      (k) => k in rs,
    ), Object.keys(rs));
  check("room reports the gate", typeof rs.gate.passed === "boolean", rs.gate);
  check("room marks blocking dimensions", Array.isArray(rs.gate.blocking), rs.gate);
  check(
    "unprobed dimension renders as an empty bar",
    rs.coverage.filter((d: any) => d.status === "unprobed").every((d: any) => d.fill === 0),
    rs.coverage.map((d: any) => [d.id, d.status, d.fill]),
  );
  check(
    "settled dimension renders as a full bar",
    rs.coverage
      .filter((d: any) => ["saturated", "capped", "attested"].includes(d.status))
      .every((d: any) => d.fill === 1),
    rs.coverage.map((d: any) => [d.id, d.status, d.fill]),
  );
  check("room counts claims per seat", rs.panel.every((p: any) => typeof p.claims === "number"), rs.panel);

  const serverPath = join(HERE, "riff-server.ts");
  const srv = Bun.spawn(["bun", serverPath, "--session", S, "--port", "0", "--root", ROOT], {
    stdout: "pipe",
    stderr: "pipe",
  });
  // Read only the FIRST line. Awaiting the whole stdout stream would block
  // forever, because the server is still running and never closes it.
  let srvPort = 0;
  {
    const reader = srv.stdout.getReader();
    const deadline = Date.now() + 8000;
    let buf = "";
    while (Date.now() < deadline && !buf.includes("\n")) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += new TextDecoder().decode(value);
    }
    reader.releaseLock();
    const first = buf.split("\n").find((l) => l.trim().startsWith("{"));
    if (first) {
      try {
        srvPort = JSON.parse(first).port;
      } catch {
        /* asserted below */
      }
    }
  }
  check("room server announces its port", srvPort > 0, srvPort);
  if (srvPort) {
    const page = await fetch(`http://localhost:${srvPort}/`).then((r) => r.text());
    check("server serves the room page", page.includes("Research Riff"), page.slice(0, 80));
    const st = (await fetch(`http://localhost:${srvPort}/state`).then((r) => r.json())) as any;
    check("server serves live state", st.session_id === S, st.session_id);
    const missing = await fetch(`http://localhost:${srvPort}/nope`);
    check("server 404s unknown routes", missing.status === 404, missing.status);

    // The whole point of the room is that it updates itself. Open the stream,
    // change the session, and assert a SECOND state event arrives unprompted.
    const es = await fetch(`http://localhost:${srvPort}/events`);
    const esReader = es.body!.getReader();
    const dec = new TextDecoder();
    let seenEvents = 0;
    let sawChange = false;
    const firstChunk = await esReader.read();
    if (firstChunk.value && dec.decode(firstChunk.value).includes("event: state")) seenEvents++;

    json("ledger", "add", "--session", S, "--data",
      '{"type":"note","body":"room push test — this must reach the browser without a refresh"}');

    const pushDeadline = Date.now() + 6000;
    while (Date.now() < pushDeadline && !sawChange) {
      const { value, done } = await esReader.read();
      if (done) break;
      const text = dec.decode(value);
      if (text.includes("event: state")) {
        seenEvents++;
        if (text.includes("room push test")) sawChange = true;
      }
    }
    esReader.cancel().catch(() => {});
    check("stream pushes the initial state on connect", seenEvents >= 1, seenEvents);
    check("stream pushes again when the session changes", sawChange, { seenEvents, sawChange });
  }
  srv.kill();

  // -- status / resume ------------------------------------------------------
  console.log("\nstatus + resume");
  const st = json("status", "--session", S);
  check("status reports the gate", st.gate.passed === true, st.gate);
  check("status counts the corpus", st.corpus.claims === 7, st.corpus);
  check("status counts the ledger", st.ledger.total > 5, st.ledger);
  const res = run("resume");
  check("resume prints without a session flag", res.code === 0 && res.out.includes("session:"), res.err);

  // completing a session must not make it unreachable — eval/status/resume are
  // exactly what you want on a finished session
  json("phase", "complete", "--session", S);
  const afterComplete = run("eval", "--session", S);
  check("eval works on a completed session with an explicit id", afterComplete.code === 0, afterComplete.err);
  const implicit = run("status");
  check("status finds a completed session with no flag", implicit.code === 0 && implicit.out.includes(S), implicit.err);
  const implicitResume = run("resume");
  check("resume finds a completed session with no flag", implicitResume.code === 0, implicitResume.err);
  json("phase", "report", "--session", S);

  // -- figures must be primary-sourced (failure-log regression) -------------
  // A latency or price lifted from a blog, or from memory, must never read as
  // "verified". This is the root cause of the ElevenLabs ~264 ms / Cartesia
  // 188 ms errors. Isolated session so it does not disturb S's fixed counts.
  console.log("\nfigures need a primary source");
  const S2 = json("init", "--topic", "Which speech engine has the lowest streaming latency", "--tier", "lite").session_id;
  const numClaims = tmpJson("num.json", [
    {
      claim: "AcmeTTS streams audio at roughly 264 ms end-to-end latency",
      dimension: "latency",
      sources: [
        { source: "Personal blog benchmark", url: "https://example.test/blog-a", tier: 4, as_of: "2026-07-22" },
        { source: "Forum post", url: "https://example.test/forum-b", tier: 4, as_of: "2026-07-22" },
      ],
      as_of: "2026-07-22",
      agent: "latency-scout",
    },
    {
      claim: "BoreaTTS streams audio at roughly 90 ms latency per its own model card",
      dimension: "latency",
      sources: [
        { source: "Vendor model card", url: "https://example.test/borea-docs", tier: 1, as_of: "2026-07-22" },
        { source: "Vendor latency page", url: "https://example.test/borea-page", tier: 1, as_of: "2026-07-22" },
      ],
      as_of: "2026-07-22",
      agent: "latency-scout",
    },
  ]);
  json("claims", "add", "--session", S2, "--slug", "latency-scout", "--json", numClaims);

  const blogFig = json("ask", "what is AcmeTTS streaming latency", "--session", S2);
  check("a blog-sourced figure is detected as numeric", blogFig.numeric === true, blogFig);
  check("a figure with no Tier 1-2 source cannot be verified", blogFig.label === "provisional", blogFig);
  check("the blog-figure reason points at primary verification", /Tier 1-2 source/.test(blogFig.reason), blogFig.reason);

  const primFig = json("ask", "what is BoreaTTS streaming latency", "--session", S2);
  check("a figure on a Tier 1-2 source is primary_sourced", primFig.primary_sourced === true, primFig);
  check("a primary-sourced figure can verify", primFig.label === "verified", primFig);

  const evalNum = json("eval", "--session", S2, "--json").checks.find((c: any) => c.id === "figures-primary-sourced");
  check("eval has the figures-primary-sourced check", !!evalNum, evalNum);
  check("eval fails when a figure lacks a primary source", evalNum && evalNum.verdict === "fail", evalNum);
  check("the figures check names the offending count", evalNum && /1\/2 measurement/.test(evalNum.measured), evalNum && evalNum.measured);

  // -- error handling -------------------------------------------------------
  console.log("\nerror handling");
  const badDim = run("coverage", "probe", "nope", "--session", S, "--novel", "1");
  check("unknown dimension errors cleanly", badDim.code !== 0 && badDim.err.includes("unknown coverage dimension"), badDim.err);
  const badCmd = run("frobnicate");
  check("unknown command errors cleanly", badCmd.code !== 0 && badCmd.err.includes("unknown command"), badCmd.err);
  const noBody = run("ledger", "add", "--session", S, "--data", '{"type":"finding"}');
  check("ledger rejects an entry with no body", noBody.code !== 0, noBody.err);
} catch (e) {
  failed++;
  failures.push(`EXCEPTION: ${e instanceof Error ? e.message : String(e)}`);
  console.log(`\n  FAIL exception :: ${e instanceof Error ? e.stack : String(e)}`);
} finally {
  console.log(`\n${pass} passed, ${failed} failed`);
  if (failed) console.log(`failures:\n  - ${failures.join("\n  - ")}`);
  if (!process.env.RIFF_KEEP) rmSync(ROOT, { recursive: true, force: true });
  else console.log(`kept: ${ROOT}`);
  process.exit(failed ? 1 : 0);
}
