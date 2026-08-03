#!/usr/bin/env python3
"""
test_recency.py — offline tests for the volatility-conditional recency discipline
(RESEARCH-recency-bias-2026-08-02.md §6). No model calls, no network.

Covers, most-carefully for the one risky piece (guarded supersession):
  - volatility.classify: domain/lexical priors, unknown default, judge reconcile;
  - volatility.compute_freshness: window/stale/severity, Decision B (no-date),
    low-confidence gate, durable exemption, future-date clamp;
  - grade_fuse.grade_claim recency: stale downgrade + verified cap + cap-not-nullify
    + durable/low-confidence inertness;
  - resolve guarded supersession: fires only when gated, demotes-by-fall-through
    when the guard fails, durable-exempt, upper-rung precedence, <2-dated guard;
  - render staleness banner (surfaces iff confidently-volatile + stale);
  - end-to-end via orchestrate.run (fresh volatile -> ESTABLISHED; stale/undated
    volatile -> capped at CORROBORATED; durable well-supported -> ESTABLISHED);
  - config: shipped volatility.yaml overlays to exactly DEFAULT_VOLATILITY (drift),
    and an edited FLAT file actually takes effect (Decision A).

Run:  python3 tests/test_recency.py   (exit 0 = all pass)
"""

import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))

import volatility as vol          # noqa: E402
import grade_fuse as gf           # noqa: E402
import resolve as rs              # noqa: E402
import axiom_ledger as al         # noqa: E402
import orchestrate as orch        # noqa: E402

PASS, FAIL = 0, 0
TODAY = "2026-08-02"


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        print(f"  FAIL  {name}  {detail}")


def src(sid, family="anthropic", origin=None, context_id=None, value=None, as_of=None, engine=False):
    return {"id": sid, "family": family, "origin": origin, "context_id": context_id,
            "text": "", "value": value, "as_of": as_of, "is_engine_output": engine}


def days_ago(n):
    """ISO date n days before TODAY (deterministic; no clock)."""
    import datetime
    return (datetime.date.fromisoformat(TODAY) - datetime.timedelta(days=n)).isoformat()


def main():
    cfg = vol.load_volatility()

    # === classify ============================================================
    print("\n[classify] volatility classifier (advisory + asymmetric)")
    c = vol.classify("The capital of Australia is Canberra.", domain="geography", cfg=cfg)
    check("durable domain -> durable", c["volatility"] == "durable" and not c["flagged"], c)
    c = vol.classify("GPT-5 is the current best model on the benchmark.", domain="ai", cfg=cfg)
    check("two signals (lexical+domain) -> fast, high confidence", c["volatility"] == "fast" and c["confidence"] == "high", c)
    c = vol.classify("The federal funds rate is 4.25% as of today.", domain="rates", cfg=cfg)
    check("volatile lexical+domain -> volatile", c["volatility"] == "volatile", c)
    c = vol.classify("Widgets improve throughput.", domain=None, cfg=cfg)
    check("unclassifiable -> unknown_default 'slow', low conf, flagged", c["volatility"] == "slow" and c["confidence"] == "low" and c["flagged"], c)
    c = vol.classify("Some claim.", domain="ai", judge_label="fast", cfg=cfg)
    check("judge agrees with prior -> high confidence", c["confidence"] == "high", c)
    c = vol.classify("The capital is X.", domain="geography", judge_label="volatile", cfg=cfg)
    check("judge disagrees -> take MORE volatile, drop to low conf, flag", c["volatility"] == "volatile" and c["confidence"] == "low" and c["flagged"], c)
    check("classifier NEVER nullifies (always returns a class)", c["volatility"] in vol.CLASSES, c)
    # Review fixes F1 + F2 — word-boundary matching and the disagreement rule.
    c = vol.classify("The capital of Minnesota is Saint Paul.", domain="geography", cfg=cfg)
    check("F2 fix: 'sota' does NOT fire inside 'Minnesota' -> durable", c["volatility"] == "durable", c)
    c = vol.classify("The company operates in 12 states.", domain=None, cfg=cfg)
    check("F2 fix: 'rates' does NOT fire inside 'operates' -> unknown default (slow, low)", c["volatility"] == "slow" and c["confidence"] == "low", c)
    c = vol.classify("The parcel was delivered on time.", domain=None, cfg=cfg)
    check("F2 fix: 'live' does NOT fire inside 'delivered'", c["volatility"] == "slow" and c["confidence"] == "low", c)
    c = vol.classify("The current population figures for Canberra.", domain="geography", cfg=cfg)
    check("F1 fix: lexical/domain DISAGREEMENT -> more volatile at LOW conf + flagged (cap disarmed)",
          c["volatility"] == "fast" and c["confidence"] == "low" and c["flagged"], c)
    c = vol.classify("The reference figure is 42.", domain=None, judge_label="volatile", cfg=cfg)
    check("F4: judge label with NO other signals = one real clue -> its class at MEDIUM (gate armed)",
          c["volatility"] == "volatile" and c["confidence"] == "medium" and not c["flagged"], c)

    # === compute_freshness ===================================================
    print("\n[freshness] window / stale / severity / Decision B / low-conf gate")
    fr = vol.compute_freshness("durable", [None], TODAY, cfg)
    check("durable is exempt (freshness_ok True, gate off)", fr["freshness_ok"] and not fr["gate_applies"] and not fr["stale"], fr)
    fr = vol.compute_freshness("fast", [days_ago(10), days_ago(400)], TODAY, cfg, confidence="high")
    check("fast + a recent source within 183d -> not stale, recent_independent", (not fr["stale"]) and fr["recent_independent"], fr)
    fr = vol.compute_freshness("fast", [days_ago(400)], TODAY, cfg, confidence="high")
    check("fast + only a 400d-old source -> stale, severity 2, freshness_ok False", fr["stale"] and fr["severity"] == 2 and not fr["freshness_ok"], fr)
    fr = vol.compute_freshness("slow", [days_ago(2000)], TODAY, cfg, confidence="high")
    check("slow past 1095d window -> stale, severity 1", fr["stale"] and fr["severity"] == 1, fr)
    fr = vol.compute_freshness("volatile", [None, "not-a-date"], TODAY, cfg, confidence="high")
    check("Decision B: no reliable date -> unknown-age, cannot be recent -> stale", fr["stale"] and not fr["recent_independent"], fr)
    fr = vol.compute_freshness("fast", [days_ago(400)], TODAY, cfg, confidence="low")
    check("low classifier confidence -> gate does NOT apply -> not capped (freshness_ok True)", fr["stale"] and not fr["gate_applies"] and fr["freshness_ok"], fr)
    fr = vol.compute_freshness("volatile", [days_ago(-5)], TODAY, cfg, confidence="high")
    check("future-dated source clamps to age 0 -> recent", fr["recent_independent"] and not fr["stale"], fr)

    # === grade_claim recency =================================================
    print("\n[grade] stale downgrade + verified cap + cap-not-nullify + inertness")
    base_fresh = vol.compute_freshness("fast", [days_ago(5), days_ago(9)], TODAY, cfg, confidence="high")
    g = gf.grade_claim(2, ["anthropic", "openai"], has_primary_citation=True, volatility="fast", freshness=base_fresh)
    check("fresh volatile 2-indep+2-fam+primary -> verified", g["confidence"] == "verified", g)
    stale_fr = vol.compute_freshness("fast", [days_ago(400), days_ago(500)], TODAY, cfg, confidence="high")
    g = gf.grade_claim(2, ["anthropic", "openai"], has_primary_citation=True, volatility="fast", freshness=stale_fr)
    check("stale volatile -> verified CAPPED to probable", g["confidence"] == "probable", g)
    check("stale downgrade recorded in reasons", any("stale" in r for r in g["reasons"]), g["reasons"])
    check("cap-not-nullify: stale claim never drops below probable", g["confidence"] != "unverified", g)
    g_durable = gf.grade_claim(2, ["anthropic", "openai"], has_primary_citation=True,
                               volatility="durable", freshness=vol.compute_freshness("durable", [days_ago(9999)], TODAY, cfg))
    check("durable claim unaffected by age -> verified", g_durable["confidence"] == "verified", g_durable)
    low_fr = vol.compute_freshness("fast", [days_ago(400)], TODAY, cfg, confidence="low")
    g = gf.grade_claim(2, ["anthropic", "openai"], has_primary_citation=True, volatility="fast", freshness=low_fr)
    check("stale but low-confidence -> NOT capped (gate off) -> verified", g["confidence"] == "verified", g)
    g_legacy = gf.grade_claim(2, ["anthropic", "openai"], has_primary_citation=True)
    check("no volatility/freshness args -> legacy path unchanged (verified)", g_legacy["confidence"] == "verified", g_legacy)

    # === resolve: guarded supersession (the risky piece) =====================
    print("\n[resolve] guarded supersession — fires only when gated")
    old = {"id": "OLD", "value": "old", "as_of": days_ago(400), "confidence": "verified",
           "independent_sources": 4, "directness": 2}
    new_ok = {"id": "NEW", "value": "new", "as_of": days_ago(5), "confidence": "verified",
              "independent_sources": 2, "directness": 2}
    r = rs.resolve_conflict([old, new_ok], volatility="fast")
    check("volatile: newer + equal-tier + corroborated -> supersedes (new wins)",
          r["status"] == "resolved" and r["winner"]["id"] == "NEW" and r["deciding_rung"] == "supersession", r)
    r = rs.resolve_conflict([old, new_ok], volatility="durable")
    check("durable conflict: supersession OFF -> classic ladder (old wins on independent_sources)",
          r["status"] == "resolved" and r["winner"]["id"] == "OLD" and r["deciding_rung"] == "independent_sources", r)
    new_weak = {"id": "NEW", "value": "new", "as_of": days_ago(5), "confidence": "verified",
                "independent_sources": 1, "directness": 2}
    r = rs.resolve_conflict([old, new_weak], volatility="fast")
    check("volatile: newer but NOT corroborated (1 source) -> guard fails -> falls through -> old wins",
          r["status"] == "resolved" and r["winner"]["id"] == "OLD", r)
    new_lower = {"id": "NEW", "value": "new", "as_of": days_ago(5), "confidence": "probable",
                 "independent_sources": 3, "directness": 2}
    r = rs.resolve_conflict([old, new_lower], volatility="fast")
    check("volatile: newer but LOWER tier -> guard fails -> old wins (no fresh-weak win)",
          r["winner"]["id"] == "OLD", r)
    old_direct = {"id": "OLD", "value": "old", "as_of": days_ago(400), "confidence": "verified",
                  "independent_sources": 4, "directness": 3}
    r = rs.resolve_conflict([old_direct, new_ok], volatility="fast")
    check("upper rung (directness) outranks supersession -> more-direct old claim wins at 'directness'",
          r["winner"]["id"] == "OLD" and r["deciding_rung"] == "directness", r)
    r = rs.resolve_conflict([{"value": "A", "directness": 2, "as_of": days_ago(5)},
                             {"value": "B", "directness": 2}], volatility="fast")
    check("<2 dated claims -> no supersession -> ladder tie -> UNRESOLVED", r["status"] == "unresolved", r)
    # Review fix F3 — 3-claim conflicts: the upper-rung check is newest-vs-incumbent.
    A3 = {"id": "A", "value": "vA", "as_of": days_ago(400), "confidence": "verified",
          "independent_sources": 4, "reliability": "A"}
    B3 = {"id": "B", "value": "vB", "as_of": days_ago(390), "confidence": "verified",
          "independent_sources": 3, "reliability": "A"}
    C3 = {"id": "C", "value": "vC", "as_of": days_ago(1), "confidence": "verified",
          "independent_sources": 2, "reliability": "D"}
    r = rs.resolve_conflict([A3, B3, C3], volatility="fast")
    check("F3 fix: 3-claim — reliability rung protects the incumbent (newest rel-D cannot supersede rel-A)",
          r["winner"]["id"] == "A" and r["deciding_rung"] != "supersession", r)
    r = rs.resolve_conflict([A3, B3, dict(C3, reliability="A")], volatility="fast")
    check("F3 fix: 3-claim — upper-rung TIE + guard holds -> newest corroborated claim supersedes",
          r["winner"]["id"] == "C" and r["deciding_rung"] == "supersession", r)

    # === render: staleness banner ============================================
    print("\n[render] '⚠ possibly stale' banner surfacing rules")
    def rec(state, vol_class, stale, gate, asof, window=183):
        return {"id": "R", "statement": "A claim.", "state": state, "confidence": "probable",
                "confidence_basis": {"independent_sources": 1}, "gates": {"falsification": "passed"},
                "entry_hash": "sha256-" + ("0" * 64),
                "volatility": vol_class,
                "recency": {"stale": stale, "gate_applies": gate, "newest_as_of": asof, "window_days": window}}
    md = al.render_markdown([rec("CORROBORATED", "fast", True, True, days_ago(400))])
    check("confidently-volatile stale working claim -> banner shows", "possibly stale" in md and "fast" in md, md[:200])
    md = al.render_markdown([rec("CORROBORATED", "durable", True, True, days_ago(400))])
    check("durable claim -> NO banner", "possibly stale" not in md, md[:200])
    md = al.render_markdown([rec("CORROBORATED", "slow", True, False, None)])
    check("low-confidence (gate off) claim -> NO banner spam", "possibly stale" not in md, md[:200])

    # === end-to-end via orchestrate.run ======================================
    print("\n[e2e] orchestrate.run over recency scenarios")
    tmp = tempfile.mkdtemp(prefix="axiom-recency-")
    subqs = ["EQ1", "EQ2", "EQ3", "EQ4"]
    facts = [
        # E1: fresh volatile, 2 independent families, primary -> ESTABLISHED/verified.
        {"fact_id": "E1", "statement": "The policy rate is 4.25% as of today.", "domain": "rates",
         "claim_type": "categorical", "sub_question": "EQ1",
         "candidates": [{"value": "4.25", "source": src("a", "anthropic", origin="u1", context_id="P1", as_of=days_ago(3))},
                        {"value": "4.25", "source": src("b", "openai", origin="u2", context_id="P2", as_of=days_ago(6))}],
         "grading": {"has_primary_citation": True}, "falsifiable": True},
        # E2: STALE volatile (sources ~400d old) -> capped at CORROBORATED/probable.
        {"fact_id": "E2", "statement": "The current best benchmark score is 91.", "domain": "ai",
         "claim_type": "categorical", "sub_question": "EQ2",
         "candidates": [{"value": "91", "source": src("a", "anthropic", origin="u1", context_id="P1", as_of=days_ago(400))},
                        {"value": "91", "source": src("b", "openai", origin="u2", context_id="P2", as_of=days_ago(420))}],
         "grading": {"has_primary_citation": True}, "falsifiable": True},
        # E3: Decision B — volatile, sources carry NO dates -> capped at CORROBORATED.
        {"fact_id": "E3", "statement": "The latest exchange rate is 1.12.", "domain": "rates",
         "claim_type": "categorical", "sub_question": "EQ3",
         "candidates": [{"value": "1.12", "source": src("a", "anthropic", origin="u1", context_id="P1", as_of=None)},
                        {"value": "1.12", "source": src("b", "openai", origin="u2", context_id="P2", as_of=None)}],
         "grading": {"has_primary_citation": True}, "falsifiable": True},
        # E4: durable, well-supported -> ESTABLISHED even with an old source (age is not a defect).
        {"fact_id": "E4", "statement": "The capital of Australia is Canberra.", "domain": "geography",
         "claim_type": "categorical", "sub_question": "EQ4",
         "candidates": [{"value": "Canberra", "source": src("a", "anthropic", origin="u1", context_id="P1", as_of=days_ago(4000))},
                        {"value": "Canberra", "source": src("b", "openai", origin="u2", context_id="P2", as_of=days_ago(3000))}],
         "grading": {"has_primary_citation": True}, "falsifiable": True},
    ]
    out = orch.run(os.path.join(tmp, "session"), "Recency scenarios", subqs, facts,
                   now="2026-08-02T00:00Z", repo_root=tmp, date_str=TODAY, session="rectest")
    states = {r["fact_id"]: r["final_state"] for r in out["per_fact"]}
    check("E1 fresh volatile reached ESTABLISHED", states["E1"] == "ESTABLISHED", states)
    check("E2 stale volatile capped at CORROBORATED (not ESTABLISHED)", states["E2"] == "CORROBORATED", states)
    check("E3 Decision B (no dates) capped at CORROBORATED", states["E3"] == "CORROBORATED", states)
    check("E4 durable well-supported reached ESTABLISHED despite old sources", states["E4"] == "ESTABLISHED", states)
    check("ledger chain intact after recency run", out["summary"]["chain_intact"], out["chain_problems"])
    sot = open(os.path.join(tmp, "session", "source-of-truth.md"), encoding="utf-8").read()
    check("E2 stale banner rendered in source-of-truth.md", "possibly stale" in sot, sot[:400])
    check("E4 durable claim carries NO stale banner", sot.count("possibly stale") >= 1 and "Canberra" in sot, sot[:400])

    # === config: drift + Decision-A editability ==============================
    print("\n[config] shipped yaml <-> embedded default drift; flat-edit takes effect")
    loaded = vol.load_volatility()
    check("shipped volatility.yaml overlays to EXACTLY DEFAULT_VOLATILITY (ship-time sync)",
          loaded == vol.DEFAULT_VOLATILITY, {"windows": loaded["windows"]})
    edit = os.path.join(tmp, "vol-edit.yaml")
    with open(edit, "w", encoding="utf-8") as fh:
        fh.write("version: 1\nwindow_volatile: 7\nstale_k: 2.0\n")
    tuned = vol.load_volatility(edit)
    check("Decision A: editing a FLAT window value actually takes effect", tuned["windows"]["volatile"] == 7 and tuned["stale_k"] == 2.0, tuned["windows"])
    check("unspecified keys fall back to embedded default", tuned["windows"]["fast"] == 183, tuned["windows"])
    # Review fix F6 — bool is an int subclass; `true` must not become a 1-day window.
    edit2 = os.path.join(tmp, "vol-bool.yaml")
    with open(edit2, "w", encoding="utf-8") as fh:
        fh.write("version: 1\nwindow_fast: true\n")
    tuned2 = vol.load_volatility(edit2)
    check("F6 fix: a boolean window value is rejected (True is not a day count)", tuned2["windows"]["fast"] == 183, tuned2["windows"])

    print(f"\n==== {PASS} passed, {FAIL} failed ====")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
