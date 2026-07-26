/**
 * Report compilation input.
 *
 * The report is written in ONE pass from this bundle. Splitting section-writing
 * across parallel agents is a known way to produce a disjoint report, so the
 * compiler gets everything at once and writes the whole thing itself.
 *
 * Nothing here summarizes or interprets. This module only assembles the record —
 * brief, concept outline, ledger (with supersession chains), the negative-space
 * coverage record, and the dossier claims. What the report says must be
 * traceable to what this bundle contains.
 */

import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { readJsonl, writeFileEnsured } from "./util.ts";
import { loadManifest, paths } from "./session.ts";
import { chains, view, type LedgerView } from "./ledger.ts";
import { evaluateGate, loadCoverage } from "./coverage.ts";
import { allClaims, corpusStats, looksNumeric } from "./claims.ts";
import { loadPanel } from "./panel.ts";
import { outline } from "./tree.ts";

function fence(lang: string, body: string): string {
  return "```" + lang + "\n" + body + "\n```";
}

function renderEntry(e: LedgerView): string {
  const parts = [`### ${e.id} · ${e.type} · ${e.status}`];
  if (e.concept) parts.push(`**Concept:** ${e.concept}`);
  if (e.question) parts.push(`**Originating question:** ${e.question}`);
  if (e.context) parts.push(`**Context:** ${e.context}`);
  parts.push(`**Body:** ${e.body}`);
  if (e.consequences?.length) {
    parts.push(`**Consequences:**\n${e.consequences.map((c) => `- ${c}`).join("\n")}`);
  }
  if (e.confidence) parts.push(`**Confidence:** ${e.confidence}`);
  if (e.supersedes) parts.push(`**Supersedes:** ${e.supersedes}`);
  if (e.superseded_by) parts.push(`**Superseded by:** ${e.superseded_by}`);
  if (e.provenance?.length) {
    parts.push(
      `**Provenance:**\n${e.provenance
        .map(
          (p) =>
            `- ${p.source}${p.url ? ` — ${p.url}` : ""}${p.tier ? ` [Tier ${p.tier}]` : ""}${
              p.as_of ? ` (as of ${p.as_of})` : ""
            }`,
        )
        .join("\n")}`,
    );
  }
  if (e.author) {
    parts.push(`**Author:** ${e.author.agent ?? "?"}${e.author.model ? ` / ${e.author.model}` : ""}`);
  }
  return parts.join("\n\n");
}

export function buildBundle(sessionId: string): string {
  const m = loadManifest(sessionId);
  const p = paths(sessionId);
  const brief = existsSync(p.brief) ? readFileSync(p.brief, "utf8") : "(no brief on disk)";
  const cov = loadCoverage(sessionId);
  const panel = loadPanel(sessionId);
  const entries = view(sessionId);
  const supersessions = chains(sessionId);
  const claims = allClaims(sessionId);
  const stats = corpusStats(sessionId);

  const negativeSpace = cov.dimensions
    .map(
      (d) =>
        `| ${d.id} | ${d.name} | ${d.status} | ${d.probes}/${d.cap} | ${d.novel_claims} | ${
          d.notes.length ? d.notes.join(" · ") : "—"
        } |`,
    )
    .join("\n");

  const sourceList = [
    ...new Map(
      claims
        .flatMap((c) => c.sources.map((s) => [s.url ?? s.source, { ...s, claim: c.id }] as const))
        .filter(([k]) => k),
    ).values(),
  ]
    .sort((a, b) => (a.tier ?? 9) - (b.tier ?? 9))
    .map((s) => `- [Tier ${s.tier ?? "?"}] ${s.source}${s.url ? ` — ${s.url}` : ""}${s.as_of ? ` (accessed ${s.as_of})` : ""}`)
    .join("\n");

  const gate = evaluateGate(sessionId);
  const pendingCount = stats.pending_ingest ?? 0;
  const warnings: string[] = [];
  if (!gate.passed) {
    warnings.push(
      `**THE COVERAGE GATE DID NOT PASS.** ${gate.reason}\n\n` +
        gate.blocking
          .map(
            (d) =>
              `- \`${d.id}\` — ${d.name}: ${d.status}, ${d.probes}/${d.cap} probes, ` +
              `${d.novel_claims} novel claims. Still producing new material when research stopped.`,
          )
          .join("\n") +
        `\n\nThe report MUST open its coverage section with this, name these ` +
        `dimensions, and state that the research was stopped short on them rather ` +
        `than exhausted. A reader acting on a thin dimension is acting on less ` +
        `evidence than the rest of the report implies, and only this notice tells them so.`,
    );
  }
  if (pendingCount > 0) {
    warnings.push(
      `**${pendingCount} claim(s) were written by an agent but never ingested**, so they ` +
        `carry no id, were never deduped, and are absent from section 7 below. Run ` +
        `\`riff claims ingest\` before compiling, or the report silently omits them.`,
    );
  }

  const out = `# Report compile bundle — ${sessionId}

Generated: ${new Date().toISOString()}
Phase: ${m.phase} · Tier: ${m.tier} · Mode: ${m.mode}

This bundle is the ONLY input to the report writer. Every statement in the final
report must trace to something below. Do not introduce claims, connections, or
numbers that are not present here; if two claims sit near each other that is not
evidence they are related.
${
  warnings.length
    ? `\n---\n\n## 0. WARNINGS — carry these into the report, do not quietly drop them\n\n${warnings.join(
        "\n\n",
      )}\n`
    : ""
}
---

## 1. Research brief (the question of record)

${brief}

---

## 2. Panel and charters

${panel.seats
  .map(
    (s) =>
      `- **${s.slug}** (${s.role}, ${s.status}) — ${s.title}\n  - lane: ${s.lane}\n  - excluded: ${s.not_lane}${
        s.added_at ? `\n  - added mid-session: ${s.added_at}${s.rationale ? ` — ${s.rationale}` : ""}` : ""
      }`,
  )
  .join("\n") || "(no panel recorded)"}

Panel changes during the session:

${panel.history.map((h) => `- ${h.ts} · ${h.action} · ${h.slug}${h.rationale ? ` — ${h.rationale}` : ""}`).join("\n") || "(none)"}

---

## 3. Concept outline (use this as the report's section structure)

${fence("text", outline(sessionId))}

---

## 4. Coverage and negative-space record

Saturation rule: a dimension is saturated after ${cov.k} consecutive probes that
produced no novel claim. A dimension with zero probes can never be saturated.

| id | dimension | status | probes/cap | novel claims | notes |
|---|---|---|---|---|---|
${negativeSpace || "| — | — | — | — | — | — |"}

---

## 5. Ledger — all entries (${entries.length}; ${entries.filter((e) => e.status === "active").length} active)

${entries.map(renderEntry).join("\n\n---\n\n") || "(empty)"}

---

## 6. Decisions and reversals (supersession chains)

${
  supersessions.length
    ? supersessions
        .map(
          (chain) =>
            `- ${chain.map((e) => `${e.id} (${e.type})`).join(" → ")}\n` +
            chain.map((e) => `    - ${e.id}: ${e.body}`).join("\n"),
        )
        .join("\n\n")
    : "(no reversals recorded)"
}

---

## 7. Claim corpus (${stats.claims} claims · ${stats.unique_sources} unique sources · ${stats.unsurfaced} never surfaced in conversation)

${
  claims
    .map(
      (c) =>
        `- \`${c.id}\` [${c.slug}${c.dimension ? ` · ${c.dimension}` : ""}] ${c.claim}\n` +
        `  - as of ${c.as_of}${c.volatile ? " · VOLATILE, re-verify before relying on it" : ""}\n` +
        (c.sources.length
          ? c.sources
              .map((s) => `  - source: ${s.source}${s.url ? ` — ${s.url}` : ""}${s.tier ? ` [Tier ${s.tier}]` : ""}`)
              .join("\n")
          : "  - source: NONE RECORDED — do not cite this claim"),
    )
    .join("\n") || "(no claims)"
}

---

## 8. Sources by tier

${sourceList || "(none)"}

---

## 9. Compiler instructions

Write \`report/REPORT.md\` in ONE pass with these sections, in this order:

1. Question of Record — restate the brief's question and success criteria.
2. Executive Summary — what was found and what it means, 2-3 paragraphs.
3. Panel and Charters — who researched what, including mid-session changes and why.
4. Findings — organized by the section 3 concept outline. Every finding carries a
   confidence label (verified / provisional) and its provenance. Preserve
   disagreements between sources; do not harmonize them.
5. Decisions and Reversals — the supersession chains from section 6, in plain
   language: what was believed, what changed it, what is now held.
6. Coverage and Negative Space — what was searched and NOT found, per dimension,
   from section 4. State plainly which dimensions hit their budget cap rather
   than saturating, because those are the thin ones.
7. Open Questions — what remains unresolved, and what would resolve it.
8. Methodology and Limitations — how the research ran, and where it is weak.
9. Sources — section 8, grouped by tier.
10. Audit Trail — session id, dates, tier, entry counts.

Rules: cite every material claim; never state a number that is not in this
bundle; mark any claim tagged VOLATILE as needing re-verification; if a claim has
no recorded source, exclude it rather than citing it loosely.
`;

  const outPath = join(p.report, "compile-input.md");
  writeFileEnsured(outPath, out);
  return outPath;
}

/**
 * Mechanical self-evaluation of a finished session.
 *
 * This scores the things that can be counted — coverage completeness, source
 * independence, how much of the research ever reached the reader, whether the
 * report's citations resolve. It deliberately does NOT score whether the
 * findings are any good; that is the judged half, and it belongs to an agent
 * working from templates/eval-rubric.md.
 *
 * Every check states what it measured so a WARN can be argued with.
 */
export interface EvalCheck {
  id: string;
  verdict: "pass" | "warn" | "fail";
  measured: string;
  why_it_matters: string;
}

/**
 * Read the citation verifier's verdict file(s) off disk and decide whether the
 * newest one can still be believed.
 *
 * Phase 5 loops: verify, fix, re-verify with a fresh agent. Each round rewrites
 * the report. The verdict file does not rewrite itself, and in the first real
 * session it did not get rewritten either — round 1's `FAIL` sat in
 * `report/CITATIONS.md` while rounds 2 and 3 fixed everything and the ledger
 * recorded the final `PASS`. The session was correct and its own delivered
 * artifact said otherwise. Anyone opening that file alone, which is exactly what
 * a verdict file is for, read a false FAIL.
 *
 * The rule is mtime, not text: a verification older than the artifact it
 * verifies is stale by construction, because the artifact changed after it was
 * checked. That needs no cooperation from the agent that wrote it.
 */
export function citationVerdict(sessionId: string): {
  file: string | null;
  verdict: "PASS" | "FAIL" | "UNKNOWN";
  stale: boolean;
  checked_at: string | null;
  report_at: string | null;
} {
  const p = paths(sessionId);
  const reportPath = join(p.report, "REPORT.md");
  const none = { file: null, verdict: "UNKNOWN" as const, stale: false, checked_at: null, report_at: null };
  if (!existsSync(p.report)) return none;

  // Any CITATIONS*.md counts, so per-round filenames (CITATIONS-r2.md) work
  // without the engine having to know the naming scheme the citer chose.
  const files = readdirSync(p.report)
    .filter((f) => /^CITATIONS.*\.md$/i.test(f))
    .map((f) => ({ f, mtime: statSync(join(p.report, f)).mtimeMs }))
    .sort((a, b) => b.mtime - a.mtime);
  if (!files.length) return none;

  const newest = files[0]!;
  const text = readFileSync(join(p.report, newest.f), "utf8");
  // The charter fixes the verdict line's shape; fall back to UNKNOWN rather
  // than guessing from prose that merely contains the word.
  const m = text.match(/^\s*(?:#{1,6}\s*)?\**\s*Verdict\s*:?\**\s*:?\s*\**\s*(PASS|FAIL)/im);
  const reportMtime = existsSync(reportPath) ? statSync(reportPath).mtimeMs : 0;
  return {
    file: newest.f,
    verdict: (m?.[1]?.toUpperCase() as "PASS" | "FAIL") ?? "UNKNOWN",
    stale: reportMtime > newest.mtime,
    checked_at: new Date(newest.mtime).toISOString(),
    report_at: reportMtime ? new Date(reportMtime).toISOString() : null,
  };
}

export function evaluate(sessionId: string): {
  checks: EvalCheck[];
  summary: Record<string, number | string>;
  verdict: "PASS" | "WARN" | "FAIL";
} {
  const cov = loadCoverage(sessionId);
  const claims = allClaims(sessionId);
  const stats = corpusStats(sessionId);
  const entries = view(sessionId);
  const panel = loadPanel(sessionId);
  const p = paths(sessionId);
  const checks: EvalCheck[] = [];

  const unprobed = cov.dimensions.filter((d) => d.status === "unprobed");
  const capped = cov.dimensions.filter((d) => d.status === "capped");
  const thin = cov.dimensions.filter((d) => d.status === "thin");

  checks.push({
    id: "coverage-complete",
    verdict: unprobed.length > 0 ? "fail" : thin.length > 0 ? "warn" : "pass",
    measured: `${cov.dimensions.length} dimensions: ${
      cov.dimensions.filter((d) => d.status === "saturated").length
    } saturated, ${capped.length} capped, ${thin.length} thin, ${unprobed.length} unprobed`,
    why_it_matters:
      "An unprobed dimension is the shape of the failure this skill exists to prevent: research that looks finished because the lanes it worked went quiet.",
  });

  // Two different ways to run out of budget, and both mean the same thing to a
  // reader: this section stopped short. `capped` hit its own probe ceiling;
  // `thin` was still producing new claims when the session's gap rounds ran out.
  // Counting only `capped` would report a reassuring zero while half the
  // dimensions were unfinished.
  const budgetStopped = [...capped, ...thin];
  checks.push({
    id: "budget-vs-saturation",
    verdict:
      budgetStopped.length === 0
        ? "pass"
        : budgetStopped.length > cov.dimensions.length / 2
          ? "warn"
          : "pass",
    measured:
      budgetStopped.length === 0
        ? `all ${cov.dimensions.length} dimensions reached saturation or were attested`
        : `${budgetStopped.length} of ${cov.dimensions.length} dimensions stopped for a budget reason, not because they ran dry: ${budgetStopped
            .map((d) => `${d.id} (${d.status})`)
            .join(", ")}`,
    why_it_matters:
      "Running out of budget is not the same as running out of things to find. `capped` hit its own probe ceiling; `thin` was still producing novel claims when the session's gap rounds ended. Either way the reader must be told those sections are the shallow ones.",
  });

  const multiSourced = claims.filter((c) => c.sources.length >= 2).length;
  const sourceless = claims.filter((c) => c.sources.length === 0).length;
  checks.push({
    id: "source-independence",
    verdict: claims.length === 0 ? "fail" : multiSourced / claims.length < 0.3 ? "warn" : "pass",
    measured: `${multiSourced}/${claims.length} claims carry 2+ sources; ${stats.unique_sources} unique sources overall`,
    why_it_matters:
      "Single-sourced claims can only ever be delivered as provisional. A corpus that is mostly single-sourced cannot support a confident report.",
  });

  checks.push({
    id: "sourceless-claims",
    verdict: sourceless > 0 ? "warn" : "pass",
    measured: `${sourceless} claim(s) with no recorded source`,
    why_it_matters: "Sourceless claims are excluded from the report; if there are many, research effort was wasted.",
  });

  const tier12 = claims.filter((c) => c.sources.some((s) => (s.tier ?? 9) <= 2)).length;
  checks.push({
    id: "source-quality",
    verdict: claims.length === 0 ? "fail" : tier12 / claims.length < 0.5 ? "warn" : "pass",
    measured: `${tier12}/${claims.length} claims rest on at least one Tier 1-2 source`,
    why_it_matters: "Load-bearing claims should not sit on blogs and forums alone.",
  });

  // Figures are where second-hand sourcing does the most damage: a latency or
  // price lifted from a blog or from memory reads as settled fact. Every claim
  // that states a measurement must carry a primary (Tier 1-2) source, or the
  // number is unverified no matter how many blogs repeat it.
  const numericClaims = claims.filter((c) => looksNumeric(c.claim));
  const numericUnprimaried = numericClaims.filter(
    (c) => !c.sources.some((s) => (s.tier ?? 9) <= 2),
  );
  checks.push({
    id: "figures-primary-sourced",
    verdict: numericUnprimaried.length === 0 ? "pass" : "fail",
    measured:
      numericClaims.length === 0
        ? "no measurement claims in the corpus"
        : `${numericUnprimaried.length}/${numericClaims.length} measurement claim(s) rest on no Tier 1-2 source` +
          (numericUnprimaried.length
            ? ` — e.g. ${numericUnprimaried.slice(0, 3).map((c) => c.id).join(", ")}`
            : ""),
    why_it_matters:
      "A figure with no primary source is how a wrong latency or price gets stated as fact. Verify each against the vendor's own page before delivery, or label it provisional.",
  });

  // "Nobody asked anything" and "questions were asked but findings never got
  // surfaced" both show up as a 0% ratio and mean completely different things.
  // Reporting the first as moderator under-use would be a false accusation, and
  // would train the reader to ignore this check.
  const asked = readJsonl<{ text: string }>(p.questions).length;
  const surfacedRatio = stats.claims ? stats.surfaced / stats.claims : 0;
  checks.push({
    id: "research-reached-the-reader",
    verdict:
      stats.claims === 0
        ? "fail"
        : asked === 0
          ? "pass"
          : surfacedRatio < 0.25
            ? "warn"
            : "pass",
    measured:
      asked === 0
        ? `no conversation took place — ${stats.claims} claims researched, 0 questions asked, so nothing was surfaced. Not a moderator failure; this session ran research-only.`
        : `${stats.surfaced}/${stats.claims} claims surfaced across ${asked} question(s) (${Math.round(
            surfacedRatio * 100,
          )}%)`,
    why_it_matters:
      "Research the reader never saw fails them the same way research never done does. A low ratio DURING a conversation means the moderator was under-used; no conversation at all is a different situation and is reported as such.",
  });

  const corrections = entries.filter((e) => e.type === "correction").length;
  const assumptions = entries.filter((e) => e.type === "assumption").length;
  const stops = entries.filter((e) => e.type === "stop-decision").length;
  checks.push({
    id: "everything-ingested",
    verdict: (stats.pending_ingest ?? 0) > 0 ? "fail" : "pass",
    measured:
      (stats.pending_ingest ?? 0) > 0
        ? `${stats.pending_ingest} claim(s) across ${stats.pending_dossiers} dossier(s) written but never ingested`
        : "all dossier claims have been ingested",
    why_it_matters:
      "An un-ingested claim has no id, was never deduped, and cannot be cited — so it is invisible to the report no matter how good it is.",
  });

  checks.push({
    id: "ledger-completeness",
    verdict: entries.length < 5 ? "warn" : "pass",
    measured: `${entries.length} entries — ${corrections} correction(s), ${assumptions} assumption(s), ${stops} stop-decision(s)`,
    why_it_matters:
      "The report is compiled from the ledger. A thin ledger produces a thin report no matter how much research happened.",
  });

  checks.push({
    id: "stop-decisions-evidenced",
    verdict: stops === 0 && cov.dimensions.length > 0 ? "warn" : "pass",
    measured: `${stops} stop-decision entr(ies) recorded`,
    why_it_matters:
      "Saturation asserted is not saturation evidenced. Every stop should record what the last dry probes were.",
  });

  const live = panel.seats.filter((s) => s.status !== "retired");
  checks.push({
    id: "panel-structure",
    verdict:
      live.some((s) => s.role === "generalist") && live.some((s) => s.role === "skeptic")
        ? "pass"
        : "fail",
    measured: `${live.length} live seats: ${live.map((s) => s.role).join(", ") || "none"}`,
    why_it_matters:
      "Without a generalist the specialists skip fundamentals; without a skeptic nothing is tasked with finding what the others missed.",
  });

  const reportPath = join(p.report, "REPORT.md");
  if (existsSync(reportPath)) {
    const audit = citationAudit(sessionId, reportPath);
    checks.push({
      id: "citations-resolve",
      verdict: audit.unknownIds.length || audit.sourcelessCited.length ? "fail" : "pass",
      measured: `${audit.claimIdsCited.length} claim citations; ${audit.unknownIds.length} unresolvable; ${audit.sourcelessCited.length} pointing at sourceless claims`,
      why_it_matters: "A citation that does not resolve is worse than no citation — it looks checked.",
    });
  } else {
    checks.push({
      id: "citations-resolve",
      verdict: "warn",
      measured: "no report written yet",
      why_it_matters: "Run this again after Phase 5 to check the delivered report.",
    });
  }

  if (existsSync(reportPath)) {
    const cv = citationVerdict(sessionId);
    checks.push({
      id: "citation-verdict-current",
      verdict:
        cv.file === null ? "warn" : cv.stale || cv.verdict === "FAIL" ? "fail" : cv.verdict === "UNKNOWN" ? "warn" : "pass",
      measured:
        cv.file === null
          ? "no CITATIONS*.md on disk — the report has not been verified, or the verdict was never written down"
          : cv.stale
            ? `${cv.file} says ${cv.verdict} but was written ${cv.checked_at} — before REPORT.md's own ${cv.report_at}`
            : `${cv.file} says ${cv.verdict}, written after the report it checks`,
      why_it_matters:
        "The verdict file is what a reader opens to find out whether the report was checked. A verdict older than the report it verifies describes a document that no longer exists, and a stale FAIL discredits a report that actually passed.",
    });
  }

  const verdict = checks.some((c) => c.verdict === "fail")
    ? "FAIL"
    : checks.some((c) => c.verdict === "warn")
      ? "WARN"
      : "PASS";

  return {
    checks,
    summary: {
      dimensions: cov.dimensions.length,
      claims: stats.claims,
      unique_sources: stats.unique_sources,
      ledger_entries: entries.length,
      live_seats: live.length,
    },
    verdict,
  };
}

/** Cross-check a written report's citations against the claim corpus. */
export function citationAudit(sessionId: string, reportPath: string): {
  claimIdsCited: string[];
  unknownIds: string[];
  uncitedClaims: string[];
  sourcelessCited: string[];
} {
  const text = existsSync(reportPath) ? readFileSync(reportPath, "utf8") : "";
  const claims = allClaims(sessionId);
  const byId = new Map(claims.map((c) => [c.id, c]));
  const cited = [...new Set(text.match(/\b[a-z0-9-]+-\d{3}\b/g) ?? [])];
  const claimIdsCited = cited.filter((id) => byId.has(id));
  const unknownIds = cited.filter((id) => !byId.has(id));
  const uncitedClaims = claims.filter((c) => !claimIdsCited.includes(c.id)).map((c) => c.id);
  const sourcelessCited = claimIdsCited.filter((id) => (byId.get(id)?.sources.length ?? 0) === 0);
  return { claimIdsCited, unknownIds, uncitedClaims, sourcelessCited };
}
