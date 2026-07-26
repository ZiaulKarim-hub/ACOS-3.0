#!/usr/bin/env bun
/**
 * riff — the state engine behind /acos-research-riffs.
 *
 * The skill's protocol lives in SKILL.md; this binary owns everything that must
 * be deterministic rather than narrated: session state, the append-only ledger,
 * coverage saturation counting, dedup, sufficiency routing, moderator selection,
 * and assembly of the report bundle. Nothing here writes prose about research —
 * it only records and computes.
 *
 * Usage:  bun .claude/skills/acos-research-riffs/scripts/riff.ts <command> [...]
 */

import { existsSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import {
  fail,
  parseArgs,
  readPayload,
  requireFlag,
  slugify,
  writeFileEnsured,
  type Args,
} from "./lib/util.ts";
import {
  autopilotActive,
  findResumable,
  initSession,
  loadManifest,
  paths,
  projectRoot,
  resolveSession,
  saveManifest,
  TIERS,
  MODERATOR_L,
  type Phase,
  type Tier,
} from "./lib/session.ts";
import { addEntry, chains, summarize, view, type LedgerEntry } from "./lib/ledger.ts";
import {
  addDimension,
  attest,
  evaluateGate,
  initCoverage,
  loadCoverage,
  recordProbe,
  renderTable,
} from "./lib/coverage.ts";
import {
  addClaims,
  allClaims,
  assess,
  corpusStats,
  ingestFile,
  markSurfaced,
  moderatorPick,
  recordQuestion,
  search,
  type Claim,
} from "./lib/claims.ts";
import {
  addSeat,
  approvePanel,
  emitCharter,
  emitRoleCharter,
  loadPanel,
  renderPanel,
  retireSeat,
  savePanel,
  setPanel,
  validatePanel,
  type Seat,
} from "./lib/panel.ts";
import { buildBundle, citationAudit, evaluate } from "./lib/report.ts";
import { buildRoomState } from "./lib/room.ts";
import { autofile, insert, outline, pendingReorg, reorganize, stats as treeStats } from "./lib/tree.ts";

const HERE_SCRIPTS = dirname(fileURLToPath(import.meta.url));

/** Chrome specifically — the user's default handler is not Chrome. */
function openInChrome(url: string): void {
  try {
    Bun.spawn(["open", "-a", "Google Chrome", url], { stdout: "ignore", stderr: "ignore" }).unref();
  } catch {
    /* headless or no Chrome; the URL is printed regardless */
  }
}

function out(v: unknown): void {
  console.log(typeof v === "string" ? v : JSON.stringify(v, null, 2));
}

function sid(args: Args): string {
  return resolveSession(args.flags["session"]).session_id;
}

function brief(sessionId: string): string {
  const p = paths(sessionId).brief;
  return existsSync(p) ? readFileSync(p, "utf8") : "";
}

const USAGE = `riff — state engine for /acos-research-riffs

SESSION
  preflight                                  environment + autopilot check
  init --topic "<question>" [--tier lite|standard|deep] [--force]
  status [--session ID]
  phase <scope|panel-research|coverage-gate|riff|report|complete>
  mode <standard|direct>
  resume

SCOPE
  brief --file <path>                        install the frozen research brief
  coverage init --json <file>                [{id,name,why}, ...]
  coverage add --json <file>                 add one dimension mid-session
  coverage show
  coverage probe <dim-id> --novel <n> [--note "..."] [--agent-saturated]
  coverage attest <dim-id> --by <who> --note "..."   auditor judgment on a thin dimension
  gate                                       evaluate the coverage gate

PANEL
  panel set --json <file>                    [{slug,role,title,objective,lane,not_lane,dimensions}]
  panel show
  panel approve
  panel add --json <file>                    add one seat mid-session
  panel retire <slug> --note "why"
  charter <slug>                             render this seat's delegation contract
  render probe --question "..." [--dimension <id>]     one-shot live probe charter
  render auditor|compiler|citer|eval          one-shot role charter

CORPUS
  claims ingest --slug <slug>                read the agent-written dossier claims file, dedup in place
  claims add --slug <slug> --json <file>     append claims from an external array file
  claims search "<query>" [--limit N]
  ask "<question>"                           sufficiency check -> verified|provisional|not-in-corpus
  surfaced <claim-id...>                     mark claims as shown to the user
  moderator                                  pick the best unsurfaced finding

LEDGER
  ledger add --json <file>                   {type,body,...}
  ledger supersede <old-id> --json <file>    append a correction that supersedes
  ledger show [--type T] [--tail N] [--active]
  ledger chains

TREE
  tree insert --claim <id> --concept "a/b"
  tree autofile [--by dimension|agent]        file every unfiled claim under a default concept
  tree show
  tree reorg                                 list concepts that outgrew the cap
  tree apply --concept <id> --json <file>    [{name, claim_ids}]

ROOM
  room [--port N] [--no-open] [--state]     launch the live browser dashboard

REPORT
  report bundle                              assemble the single compile input
  report audit --file <path>                 cross-check citations vs the corpus
  eval [--json]                              mechanical self-check of the session
`;

async function main(): Promise<void> {
  const argv = process.argv.slice(2);
  const cmd = argv[0];
  const args = parseArgs(argv.slice(1));

  if (!cmd || cmd === "help" || cmd === "--help") {
    out(USAGE);
    return;
  }

  switch (cmd) {
    // ---------------------------------------------------------------- session
    case "preflight": {
      const resumable = findResumable();
      out({
        ok: true,
        bun: process.versions.bun ?? null,
        cwd: process.cwd(),
        autopilot_active: autopilotActive(),
        autopilot_note: autopilotActive()
          ? "live riff needs a present human — subagents cannot ask questions"
          : null,
        resumable: resumable
          ? { session_id: resumable.session_id, phase: resumable.phase, topic: resumable.topic }
          : null,
      });
      return;
    }

    case "init": {
      const topic = requireFlag(args, "topic");
      const tier = (args.flags["tier"] ?? "standard") as Tier;
      if (!TIERS[tier]) fail(`unknown tier: ${tier}`);
      const m = initSession(topic, slugify(topic), tier, args.bools.has("force"));
      addEntry(m.session_id, {
        type: "decision",
        body: `Opened riff session on: ${topic}`,
        context: `Tier ${tier}: ${TIERS[tier].researchers} researchers, ${TIERS[tier].searchesPerResearcher} searches each.`,
        author: { agent: "riff-cli" },
      });
      out({ session_id: m.session_id, root: paths(m.session_id).root, tier, phase: m.phase });
      return;
    }

    case "status": {
      const id = sid(args);
      const m = loadManifest(id);
      const gate = evaluateGate(id);
      out({
        session_id: id,
        topic: m.topic,
        phase: m.phase,
        tier: m.tier,
        mode: m.mode,
        panel_approved: m.panel_approved,
        moderator_streak: m.moderator_streak,
        moderator_fires_at: MODERATOR_L,
        gate: { passed: gate.passed, reason: gate.reason },
        corpus: corpusStats(id),
        tree: treeStats(id),
        ledger: summarize(id),
        root: paths(id).root,
      });
      return;
    }

    case "phase": {
      const id = sid(args);
      const next = args.positional[0] as Phase;
      const valid: Phase[] = ["scope", "panel-research", "coverage-gate", "riff", "report", "complete"];
      if (!valid.includes(next)) fail(`phase must be one of: ${valid.join(", ")}`);
      const m = loadManifest(id);
      const prev = m.phase;
      m.phase = next;
      saveManifest(m);
      addEntry(id, {
        type: "decision",
        body: `Phase ${prev} -> ${next}`,
        author: { agent: "riff-cli" },
      });
      out({ session_id: id, phase: next });
      return;
    }

    case "mode": {
      const id = sid(args);
      const mode = args.positional[0];
      if (mode !== "standard" && mode !== "direct") fail("mode must be standard or direct");
      const m = loadManifest(id);
      m.mode = mode;
      saveManifest(m);
      out({ session_id: id, mode });
      return;
    }

    case "resume": {
      const m = resolveSession(args.flags["session"]);
      const id = m.session_id;
      const gate = evaluateGate(id);
      const entries = view(id);
      out(
        [
          `session:  ${id}`,
          `topic:    ${m.topic}`,
          `phase:    ${m.phase}  (tier ${m.tier}, mode ${m.mode})`,
          `root:     ${paths(id).root}`,
          ``,
          `panel:`,
          renderPanel(loadPanel(id)),
          ``,
          `coverage: ${gate.reason}`,
          renderTable(loadCoverage(id)),
          ``,
          `corpus:   ${JSON.stringify(corpusStats(id))}`,
          `tree:`,
          outline(id),
          ``,
          `last 8 ledger entries:`,
          entries
            .slice(-8)
            .map((e) => `  ${e.id} [${e.type}/${e.status}] ${e.body.slice(0, 100)}`)
            .join("\n") || "  (none)",
        ].join("\n"),
      );
      return;
    }

    // ------------------------------------------------------------------ scope
    case "brief": {
      const id = sid(args);
      const src = requireFlag(args, "file");
      const text = readFileSync(src, "utf8");
      writeFileEnsured(paths(id).brief, text);
      addEntry(id, {
        type: "decision",
        body: "Froze the research brief; all later work is measured against it.",
        context: text.split("\n").slice(0, 3).join(" ").slice(0, 300),
        author: { agent: "riff-cli" },
      });
      out({ session_id: id, brief: paths(id).brief, bytes: text.length });
      return;
    }

    case "coverage": {
      const id = sid(args);
      const sub = args.positional[0];
      if (sub === "init") {
        const dims = readPayload(args) as Array<{ id: string; name: string; why: string }>;
        if (!Array.isArray(dims) || dims.length === 0) fail("coverage init needs a non-empty array");
        const m = loadManifest(id);
        const c = initCoverage(id, dims, m.tier);
        addEntry(id, {
          type: "decision",
          body: `Declared ${c.dimensions.length} coverage dimensions. A dimension with zero probes can never count as saturated.`,
          consequences: c.dimensions.map((d) => `${d.id}: ${d.name}`),
          author: { agent: "riff-cli" },
        });
        out({ dimensions: c.dimensions.length, ids: c.dimensions.map((d) => d.id) });
        return;
      }
      if (sub === "add") {
        const d = readPayload(args) as { id: string; name: string; why: string };
        const added = addDimension(id, d);
        addEntry(id, {
          type: "gap",
          body: `Added coverage dimension mid-session: ${added.id} — ${added.name}`,
          context: added.why,
          author: { agent: "riff-cli" },
        });
        out(added);
        return;
      }
      if (sub === "attest") {
        const dimId = args.positional[1];
        if (!dimId) fail("coverage attest needs a dimension id");
        const by = args.flags["by"] ?? "auditor";
        const note = args.flags["note"];
        if (!note) fail("coverage attest needs --note explaining the basis");
        const d = attest(id, dimId, by, note);
        addEntry(id, {
          type: "stop-decision",
          body: `Dimension ${d.id} attested as covered by ${by} without reaching mechanical saturation.`,
          context: note,
          consequences: [
            `${d.probes} probe(s), ${d.novel_claims} novel claims, dry streak ${d.dry_streak}`,
            "Recorded as a judgment call, not a counted result — weigh it accordingly in the report.",
          ],
          author: { agent: by },
        });
        out(d);
        return;
      }
      if (sub === "probe") {
        const dimId = args.positional[1];
        if (!dimId) fail("coverage probe needs a dimension id");
        const novel = Number(args.flags["novel"] ?? "0");
        const d = recordProbe(
          id,
          dimId,
          novel,
          args.flags["note"],
          args.bools.has("agent-saturated"),
        );
        if (d.status === "saturated") {
          addEntry(id, {
            type: "stop-decision",
            body: `Dimension ${d.id} reached saturation: ${d.dry_streak} consecutive probes produced no novel claim.`,
            context: `Probes ${d.probes}/${d.cap}; ${d.novel_claims} novel claims total. Notes: ${
              d.notes.slice(-2).join(" · ") || "none"
            }`,
            author: { agent: "riff-cli" },
          });
        }
        out(d);
        return;
      }
      if (sub === "show" || !sub) {
        const c = loadCoverage(id);
        out(renderTable(c) || "(no dimensions declared)");
        return;
      }
      fail(`unknown coverage subcommand: ${sub}`);
      return;
    }

    case "gate": {
      const id = sid(args);
      const g = evaluateGate(id);
      const m = loadManifest(id);
      if (g.passed && !m.gate_passed) {
        m.gate_passed = true;
        saveManifest(m);
        addEntry(id, {
          type: "stop-decision",
          body: `Coverage gate PASSED: ${g.reason}`,
          consequences: g.ready.map(
            (d) => `${d.id}: ${d.status} after ${d.probes} probe(s), ${d.novel_claims} novel claims`,
          ),
          author: { agent: "riff-cli" },
        });
      }
      out({
        passed: g.passed,
        reason: g.reason,
        blocking: g.blocking.map((d) => ({
          id: d.id,
          status: d.status,
          probes: d.probes,
          cap: d.cap,
          dry_streak: d.dry_streak,
        })),
        ready: g.ready.map((d) => ({ id: d.id, status: d.status, probes: d.probes })),
      });
      return;
    }

    // ------------------------------------------------------------------ panel
    case "panel": {
      const id = sid(args);
      const sub = args.positional[0] ?? "show";
      if (sub === "set") {
        const seats = readPayload(args) as Seat[];
        const p = setPanel(id, seats);
        const problems = validatePanel(p);
        out({ seats: p.seats.length, problems, approved: p.approved });
        return;
      }
      if (sub === "approve") {
        const p = loadPanel(id);
        const problems = validatePanel(p);
        if (problems.length && !args.bools.has("force")) {
          fail(`panel not approvable:\n  - ${problems.join("\n  - ")}\n(use --force to override)`);
        }
        approvePanel(id);
        const m = loadManifest(id);
        m.panel_approved = true;
        saveManifest(m);
        addEntry(id, {
          type: "decision",
          body: `Panel approved: ${p.seats.map((s) => s.slug).join(", ")}`,
          consequences: problems.length ? [`Approved with warnings: ${problems.join("; ")}`] : [],
          author: { agent: "riff-cli" },
        });
        out({ approved: true, seats: p.seats.map((s) => s.slug), warnings: problems });
        return;
      }
      if (sub === "add") {
        const seat = readPayload(args) as Seat;
        addSeat(id, seat);
        addEntry(id, {
          type: "panel-change",
          body: `Added seat mid-session: ${seat.slug} (${seat.role}) — ${seat.title}`,
          context: seat.rationale ?? "steered by the user",
          author: { agent: "riff-cli" },
        });
        out({ added: seat.slug });
        return;
      }
      if (sub === "retire") {
        const slug = args.positional[1];
        if (!slug) fail("panel retire needs a seat slug");
        const note = args.flags["note"] ?? "no longer relevant to the brief";
        retireSeat(id, slug, note);
        addEntry(id, {
          type: "panel-change",
          body: `Retired seat: ${slug}`,
          context: note,
          author: { agent: "riff-cli" },
        });
        out({ retired: slug });
        return;
      }
      out(renderPanel(loadPanel(id)));
      return;
    }

    case "charter": {
      const id = sid(args);
      const slug = args.positional[0];
      if (!slug) fail("charter needs a seat slug");
      const m = loadManifest(id);
      const seat = loadPanel(id).seats.find((s) => s.slug === slug);
      if (!seat) fail(`unknown seat: ${slug}`);
      const written = emitCharter({
        sessionId: id,
        seat: seat!,
        brief: brief(id),
        tier: m.tier,
        dimensions: loadCoverage(id).dimensions,
      });
      out({ charter: written });
      return;
    }

    case "render": {
      const id = sid(args);
      const role = args.positional[0] as "probe" | "auditor" | "compiler" | "citer" | "eval";
      if (!["probe", "auditor", "compiler", "citer", "eval"].includes(role)) {
        fail("render needs one of: probe | auditor | compiler | citer | eval");
      }
      const m = loadManifest(id);
      let slug = args.flags["slug"];
      if (role === "probe" && !slug) {
        const n = loadPanel(id).history.filter((h) => h.action === "probe").length + 1;
        slug = `probe-${String(n).padStart(2, "0")}`;
        const p = loadPanel(id);
        p.history.push({
          ts: new Date().toISOString(),
          action: "probe",
          slug,
          rationale: args.flags["question"],
        });
        savePanel(id, p);
      }
      const r = emitRoleCharter(id, role, {
        slug,
        objective: args.flags["question"] ?? args.flags["objective"],
        dimension: args.flags["dimension"],
        brief: brief(id) || m.topic,
        tier: m.tier,
      });
      if (role === "probe") {
        addEntry(id, {
          type: "question",
          body: `Dispatched probe ${r.slug}: ${args.flags["question"] ?? "(no question recorded)"}`,
          context: "The corpus could not answer this, so the session abstained and went to look.",
          author: { agent: "riff-cli" },
        });
      }
      out({
        charter: r.path,
        slug: r.slug,
        claims_path: join(paths(id).dossiers, `${r.slug}.claims.jsonl`),
        note: "pass this file's contents to one Task as the prompt",
      });
      return;
    }

    // ----------------------------------------------------------------- corpus
    case "claims": {
      const id = sid(args);
      const sub = args.positional[0];
      if (sub === "add") {
        const slug = requireFlag(args, "slug");
        const payload = readPayload(args) as Array<Partial<Claim>>;
        if (!Array.isArray(payload)) fail("claims add expects an array");
        const res = addClaims(id, slug, payload);
        out({
          slug,
          added: res.added.length,
          duplicates: res.duplicates.length,
          duplicate_of: res.duplicates.map((d) => d.duplicate_of),
          ids: res.added.map((c) => c.id),
        });
        return;
      }
      if (sub === "ingest") {
        const slug = requireFlag(args, "slug");
        const res = ingestFile(id, slug);
        if (res.malformed > 0) {
          addEntry(id, {
            type: "note",
            body: `${res.malformed} malformed line(s) dropped while ingesting ${slug}'s claims.`,
            context: `Read ${res.total_read} lines, kept ${res.added.length}.`,
            author: { agent: "riff-cli" },
          });
        }
        out({
          slug,
          total_read: res.total_read,
          added: res.added.length,
          duplicates: res.duplicates.length,
          malformed: res.malformed,
          novel_by_dimension: res.added.reduce<Record<string, number>>((acc, c) => {
            const k = c.dimension ?? "(unassigned)";
            acc[k] = (acc[k] ?? 0) + 1;
            return acc;
          }, {}),
          sourceless: res.added.filter((c) => c.sources.length === 0).length,
          note: "feed novel_by_dimension counts into `riff coverage probe`",
        });
        return;
      }
      if (sub === "search") {
        const q = args.positional.slice(1).join(" ");
        if (!q) fail("claims search needs a query");
        out(
          search(id, q, Number(args.flags["limit"] ?? "8")).map((c) => ({
            id: c.id,
            score: Number(c.score.toFixed(3)),
            claim: c.claim,
            as_of: c.as_of,
            sources: c.sources.length,
          })),
        );
        return;
      }
      fail(`unknown claims subcommand: ${sub}`);
      return;
    }

    case "ask": {
      const id = sid(args);
      const q = args.positional.join(" ");
      if (!q) fail("ask needs a question");
      recordQuestion(id, q);
      const a = assess(id, q, {
        minScore: args.flags["min"] ? Number(args.flags["min"]) : undefined,
        strongScore: args.flags["strong"] ? Number(args.flags["strong"]) : undefined,
      });
      const m = loadManifest(id);
      m.moderator_streak = a.label === "not-in-corpus" ? 0 : m.moderator_streak + 1;
      saveManifest(m);
      out({
        question: q,
        label: a.label,
        reason: a.reason,
        action:
          a.label === "not-in-corpus"
            ? "ABSTAIN and dispatch a probe — do not improvise an answer"
            : a.label === "provisional"
              ? "answer, say it is provisional, offer to deepen"
              : "answer from the corpus with citations",
        stale: a.stale,
        volatile: a.volatile,
        numeric: a.numeric,
        primary_sourced: a.primary_sourced,
        independent_sources: a.independent_sources,
        moderator_due: m.mode === "standard" && m.moderator_streak >= MODERATOR_L,
        hits: a.hits.map((h) => ({
          id: h.id,
          score: Number(h.score.toFixed(3)),
          claim: h.claim,
          as_of: h.as_of,
          sources: h.sources,
        })),
      });
      return;
    }

    case "surfaced": {
      const id = sid(args);
      if (args.positional.length === 0) fail("surfaced needs at least one claim id");
      markSurfaced(id, args.positional);
      out({ marked: args.positional.length });
      return;
    }

    case "moderator": {
      const id = sid(args);
      const m = loadManifest(id);
      if (m.mode === "direct") {
        out({ mode: "direct", pick: null, note: "moderator is off in direct mode" });
        return;
      }
      const pick = moderatorPick(id, brief(id) || m.topic);
      if (pick) {
        markSurfaced(id, [pick.id]);
        m.moderator_streak = 0;
        saveManifest(m);
      }
      out(
        pick
          ? {
              claim_id: pick.id,
              score: Number(pick.score.toFixed(3)),
              claim: pick.claim,
              from: pick.slug,
              as_of: pick.as_of,
              sources: pick.sources,
              note: "surface this as a 'you did not ask, but' aside",
            }
          : { pick: null, note: "nothing unsurfaced worth raising" },
      );
      return;
    }

    // ----------------------------------------------------------------- ledger
    case "ledger": {
      const id = sid(args);
      const sub = args.positional[0] ?? "show";
      if (sub === "add") {
        const e = addEntry(id, readPayload(args) as Partial<LedgerEntry>);
        out({ id: e.id, type: e.type });
        return;
      }
      if (sub === "supersede") {
        const oldId = args.positional[1];
        if (!oldId) fail("ledger supersede needs the id being superseded");
        const payload = readPayload(args) as Partial<LedgerEntry>;
        const e = addEntry(id, {
          type: "correction",
          ...payload,
          supersedes: oldId,
        });
        out({ id: e.id, supersedes: oldId });
        return;
      }
      if (sub === "chains") {
        out(
          chains(id).map((c) => c.map((e) => ({ id: e.id, type: e.type, body: e.body }))),
        );
        return;
      }
      let entries = view(id);
      if (args.flags["type"]) entries = entries.filter((e) => e.type === args.flags["type"]);
      if (args.bools.has("active")) entries = entries.filter((e) => e.status === "active");
      const tail = Number(args.flags["tail"] ?? "0");
      if (tail > 0) entries = entries.slice(-tail);
      out(entries);
      return;
    }

    // ------------------------------------------------------------------- tree
    case "tree": {
      const id = sid(args);
      const sub = args.positional[0] ?? "show";
      if (sub === "insert") {
        const claim = requireFlag(args, "claim");
        const concept = requireFlag(args, "concept");
        const node = insert(id, concept, claim);
        out({ concept: node.id, claims: node.claim_ids.length, needs_reorg: !!node.needs_reorg });
        return;
      }
      if (sub === "autofile") {
        const by = (args.flags["by"] ?? "dimension") as "dimension" | "agent";
        if (by !== "dimension" && by !== "agent") fail("--by must be dimension or agent");
        const res = autofile(id, allClaims(id), by);
        out({
          ...res,
          note: "a starting skeleton grouped by checklist row — reorganize it to reflect what the material says",
        });
        return;
      }
      if (sub === "reorg") {
        out(
          pendingReorg(id).map((n) => ({
            concept: n.id,
            claims: n.claim_ids.length,
            claim_ids: n.claim_ids,
          })),
        );
        return;
      }
      if (sub === "apply") {
        const concept = requireFlag(args, "concept");
        const groups = readPayload(args) as Array<{ name: string; claim_ids: string[] }>;
        const node = reorganize(id, concept, groups);
        out({ concept: node.id, children: node.children.map((c) => c.id), left: node.claim_ids });
        return;
      }
      out(outline(id));
      return;
    }

    // ----------------------------------------------------------------- report
    case "report": {
      const id = sid(args);
      const sub = args.positional[0] ?? "bundle";
      if (sub === "bundle") {
        const p = buildBundle(id);
        out({ bundle: p, note: "hand this to ONE compiler agent; never split section-writing" });
        return;
      }
      if (sub === "audit") {
        const file = args.flags["file"] ?? join(paths(id).report, "REPORT.md");
        const a = citationAudit(id, file);
        out({
          report: file,
          cited_claims: a.claimIdsCited.length,
          unknown_ids: a.unknownIds,
          sourceless_cited: a.sourcelessCited,
          uncited_claims: a.uncitedClaims.length,
          verdict:
            a.unknownIds.length === 0 && a.sourcelessCited.length === 0
              ? "PASS"
              : "FAIL — fix unknown or sourceless citations before delivery",
        });
        return;
      }
      fail(`unknown report subcommand: ${sub}`);
      return;
    }

    case "room": {
      const id = sid(args);
      const serverPath = join(HERE_SCRIPTS, "riff-server.ts");
      if (args.bools.has("state")) {
        out(buildRoomState(id));
        return;
      }
      const portFile = join(paths(id).root, "room.port");
      // Reuse a live room rather than starting a second server on a new port —
      // otherwise every invocation leaves an orphan listening in the background.
      if (existsSync(portFile)) {
        const prev = readFileSync(portFile, "utf8").trim();
        try {
          const res = await fetch(`http://localhost:${prev}/state`, {
            signal: AbortSignal.timeout(700),
          });
          if (res.ok) {
            const url = `http://localhost:${prev}`;
            if (!args.bools.has("no-open")) openInChrome(url);
            out({ url, port: Number(prev), reused: true });
            return;
          }
        } catch {
          /* stale port file; fall through and start a fresh server */
        }
      }

      const proc = Bun.spawn(
        [
          "bun",
          serverPath,
          "--session",
          id,
          "--port",
          args.flags["port"] ?? "0",
          "--root",
          projectRoot(),
        ],
        { stdout: "pipe", stderr: "pipe", stdin: "ignore" },
      );

      // The server prints one JSON line with its chosen port, then serves.
      const reader = proc.stdout.getReader();
      const deadline = Date.now() + 8000;
      let buf = "";
      let info: { url?: string; port?: number } | null = null;
      while (Date.now() < deadline) {
        const { value, done } = await reader.read();
        if (done) break;
        buf += new TextDecoder().decode(value);
        const nl = buf.indexOf("\n");
        if (nl >= 0) {
          try {
            info = JSON.parse(buf.slice(0, nl));
          } catch {
            /* keep reading */
          }
          break;
        }
      }
      reader.releaseLock();
      if (!info?.url) {
        const err = await new Response(proc.stderr).text();
        fail(`room server did not start${err ? `: ${err.slice(0, 400)}` : ""}`);
      }
      writeFileEnsured(portFile, String(info!.port));
      proc.unref();
      if (!args.bools.has("no-open")) openInChrome(info!.url!);
      out({
        url: info!.url,
        port: info!.port,
        session_id: id,
        note: "read-only dashboard; it recomputes from the session directory, so it can never show stale research as live",
      });
      return;
    }

    case "eval": {
      const id = sid(args);
      const e = evaluate(id);
      if (args.bools.has("json")) {
        out(e);
        return;
      }
      const lines = [
        `session ${id} — mechanical self-check: ${e.verdict}`,
        "",
        ...e.checks.map(
          (c) =>
            `  [${c.verdict.toUpperCase().padEnd(4)}] ${c.id}\n` +
            `          measured: ${c.measured}\n` +
            `          why:      ${c.why_it_matters}`,
        ),
        "",
        `  summary: ${JSON.stringify(e.summary)}`,
        "",
        "  This scores what can be counted. It does NOT score whether the findings",
        "  are good — that is the judged half, and it belongs to an agent working",
        "  from templates/eval-rubric.md.",
      ];
      out(lines.join("\n"));
      return;
    }

    default:
      fail(`unknown command: ${cmd}\n\n${USAGE}`);
  }
}

main().catch((e) => fail(e instanceof Error ? e.message : String(e)));
