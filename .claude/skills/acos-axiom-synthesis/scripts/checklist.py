#!/usr/bin/env python3
"""
checklist.py — the boolean confidence gate (Point-1 improvement, 2026-07).

Turns confidence from a buried derivation into an auditable YES/NO checklist:

  veto questions   — critical. ANY single NO (or unanswered) nullifies the claim,
                     regardless of how many other answers are yes. Fail-closed.
  normal questions — each YES counts toward a percentage. The yes-share on the
                     NORMAL questions (core + any domain pack) selects the tier.

Two extra hard requirements sit ON TOP of the percentage for 'verified', mirroring
the ledger writer's single-source cap: the yes-share can hit 90% and still cap at
'probable' if the claim lacks >=2 independent sources from >=2 distinct families.

Design rules preserved from PLAN.md:
  - confidence is DERIVED from evidence, never a model's self-report;
  - deterministic questions are computed by code (counts / field checks);
  - semantic questions are answered by a BLIND judge that is NOT the claim's
    author. Offline/tests supply those answers as fixtures.

The config lives in config/checklist.yaml (the human-editable audit surface).
DEFAULT_CHECKLIST below is an identical embedded fallback, so the code never
breaks if the file is missing or a hand-edit makes it unparseable. A drift test
(tests/test_checklist.py) asserts the two stay identical.

Stdlib only. Python 3.8+.
"""

import os


# ── The embedded canonical checklist (mirror of config/checklist.yaml) ────────
DEFAULT_CHECKLIST = {
    "version": 1,
    "thresholds": {"verified_min": 0.90, "probable_min": 0.70},
    "verified_also_requires": ["N1-TWO-INDEP-SOURCES", "N2-TWO-DISTINCT-FAMILIES"],
    "veto_questions": [
        {"id": "V1-FALSIFIABLE",
         "text": "Is the claim falsifiable — can you state an observation that would prove it wrong?",
         "evaluator": "semantic", "on_no": "nullify"},
        {"id": "V2-TRACEABLE-ORIGIN",
         "text": "Does the claim have a traceable origin (real provenance, not fabricated)?",
         "evaluator": "semantic", "on_no": "nullify"},
        {"id": "V3-NO-INTERNAL-CONTRADICTION",
         "text": "Is the claim free of contradiction with itself or with an already-ESTABLISHED claim?",
         "evaluator": "semantic", "on_no": "nullify"},
        {"id": "V4-SURVIVES-REFUTER",
         "text": "Did the claim survive the independent refuter with no fatal, unrebutted objection?",
         "evaluator": "semantic", "on_no": "nullify"},
    ],
    "normal_questions": [
        {"id": "N1-TWO-INDEP-SOURCES",
         "text": "Are there at least 2 independent sources after de-circularization?",
         "evaluator": "deterministic", "expr": "confidence_basis.independent_sources >= 2"},
        {"id": "N2-TWO-DISTINCT-FAMILIES",
         "text": "Do the sources come from at least 2 distinct model families?",
         "evaluator": "deterministic", "expr": "confidence_basis.distinct_families >= 2"},
        {"id": "N3-PRIMARY-CITATION",
         "text": "Is there a primary citation — a direct pointer to an original source, not a paraphrase?",
         "evaluator": "deterministic", "expr": "grading.has_primary_citation == true"},
        {"id": "N4-CITATION-SUPPORTS",
         "text": "Does the cited source actually support the claim (not misattributed)?",
         "evaluator": "semantic"},
        {"id": "N5-NOT-STALE",
         "text": "Is the claim current — not stale and not superseded?",
         "evaluator": "deterministic", "expr": "not superseded and grading.freshness_ok"},
        {"id": "N6-REPRODUCIBLE",
         "text": "Is the claim reproducible from the stated inputs?",
         "evaluator": "semantic"},
        {"id": "N7-SPECIFIC",
         "text": "Is the claim specific and precise (not vague or hedged into meaninglessness)?",
         "evaluator": "semantic"},
        {"id": "N8-NO-CONFLICT-OF-INTEREST",
         "text": "Is the claim free of an unmanaged source conflict-of-interest?",
         "evaluator": "semantic"},
        {"id": "N9-TALLY-AGREES",
         "text": "Do the equal-weighted and belief-weighted tallies agree (no divergence flag)?",
         "evaluator": "deterministic", "expr": "fused.divergence == false"},
        {"id": "N10-LATERAL-SUPPORT",
         "text": "Is the support lateral (independent corroboration), not just the same chain repeated?",
         "evaluator": "semantic"},
    ],
    "domain_packs": {},
}


# ── Deterministic evaluators (id -> pure function of the context dict) ─────────
# The YAML `expr` strings are documentation; the real computation lives here so
# nothing is eval()'d. A deterministic-marked question with no registry entry
# falls back to a semantic lookup (treated as unanswered unless provided).
DETERMINISTIC = {
    "N1-TWO-INDEP-SOURCES":    lambda ctx: int(ctx.get("independent_sources", 0)) >= 2,
    "N2-TWO-DISTINCT-FAMILIES": lambda ctx: int(ctx.get("distinct_families", 0)) >= 2,
    "N3-PRIMARY-CITATION":     lambda ctx: bool(ctx.get("has_primary_citation", False)),
    "N5-NOT-STALE":            lambda ctx: (not bool(ctx.get("superseded", False)))
                                           and bool(ctx.get("freshness_ok", True)),
    "N9-TALLY-AGREES":         lambda ctx: not bool(ctx.get("divergence", False)),
}


# ── Config loading ────────────────────────────────────────────────────────────

def default_config_path():
    """The shipped checklist.yaml next to this scripts/ dir (../config/checklist.yaml)."""
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "..", "config", "checklist.yaml")


def load_checklist(path=None):
    """Return the checklist config dict.

    Tries the YAML file (minimal built-in parser); on ANY problem falls back to
    DEFAULT_CHECKLIST so evaluation is never blocked by a missing/edited file.
    Pass an explicit path to load a per-run override.
    """
    if path is None:
        path = default_config_path()
    try:
        with open(path, "r", encoding="utf-8") as fh:
            parsed = _parse_yaml(fh.read())
        # Minimal sanity: must carry the question lists to be usable.
        if isinstance(parsed, dict) and parsed.get("veto_questions") is not None \
                and parsed.get("normal_questions") is not None:
            return _coerce_types(parsed)
    except Exception:
        pass
    return DEFAULT_CHECKLIST


# ── Evaluation ────────────────────────────────────────────────────────────────

def build_context(independent_sources, distinct_families, has_primary_citation,
                  divergence, semantic_answers=None, superseded=False, freshness_ok=True):
    """Assemble the context an evaluation reads. Deterministic inputs come from the
    pipeline (de-circularization counts, fusion divergence, grading flags); semantic
    answers come from blind judge agents (a dict of question_id -> bool)."""
    return {
        "independent_sources": independent_sources,
        "distinct_families": distinct_families,
        "has_primary_citation": has_primary_citation,
        "divergence": divergence,
        "superseded": superseded,
        "freshness_ok": freshness_ok,
        "semantic": dict(semantic_answers or {}),
    }


def _answer(question, ctx):
    """Resolve one question to True / False / None (None = unanswered)."""
    qid = question["id"]
    if qid in DETERMINISTIC:
        return bool(DETERMINISTIC[qid](ctx))
    # semantic (or a deterministic id with no registry entry): look it up
    val = ctx.get("semantic", {}).get(qid)
    if val is None:
        return None
    return bool(val)


def evaluate(checklist, ctx):
    """Run the checklist over one claim's context. Returns a structured verdict.

    Result keys:
      tier            'verified' | 'probable' | 'unverified' | 'nullified'
      nullified       bool  (a veto failed)
      veto_pass       bool
      veto_results    [{id, answer}]      answer in {True, False, None}
      normal_results  [{id, answer}]
      yes_count       int   (normal questions answered True)
      normal_total    int   (core + domain-pack normal questions)
      yes_share       float (yes_count / normal_total)
      reasons         [str] human-readable trace
    """
    th = checklist.get("thresholds", {})
    verified_min = float(th.get("verified_min", 0.90))
    probable_min = float(th.get("probable_min", 0.70))
    also = list(checklist.get("verified_also_requires", []))

    reasons = []

    # --- veto pass (fail-closed: None or False both fail) -------------------
    veto_results = []
    veto_pass = True
    for q in checklist.get("veto_questions", []):
        ans = _answer(q, ctx)
        veto_results.append({"id": q["id"], "answer": ans})
        if ans is not True:
            veto_pass = False
            reasons.append(f"VETO FAILED: {q['id']} = {ans!r} (need True)")
    if not veto_pass:
        return {
            "tier": "nullified", "nullified": True, "veto_pass": False,
            "veto_results": veto_results, "normal_results": [],
            "yes_count": 0, "normal_total": 0, "yes_share": 0.0,
            "reasons": reasons,
        }

    # --- normal questions (core + optional domain pack) --------------------
    normal_qs = list(checklist.get("normal_questions", []))
    domain = ctx.get("domain")
    if domain:
        pack = (checklist.get("domain_packs") or {}).get(domain) or []
        normal_qs = normal_qs + list(pack)
        if pack:
            reasons.append(f"domain pack '{domain}' added {len(pack)} question(s)")

    normal_results = []
    yes_count = 0
    answered_yes = set()
    for q in normal_qs:
        ans = _answer(q, ctx)
        normal_results.append({"id": q["id"], "answer": ans})
        if ans is True:
            yes_count += 1
            answered_yes.add(q["id"])
    normal_total = len(normal_qs)
    yes_share = (yes_count / normal_total) if normal_total else 0.0
    reasons.append(f"normal yes-share = {yes_count}/{normal_total} = {yes_share:.3f}")

    # --- tier mapping ------------------------------------------------------
    also_ok = all(q in answered_yes for q in also)
    if yes_share >= verified_min and also_ok:
        tier = "verified"
    elif yes_share >= verified_min and not also_ok:
        tier = "probable"
        missing = [q for q in also if q not in answered_yes]
        reasons.append(f"single-source cap: >= {verified_min:.0%} but missing {missing} -> capped at probable")
    elif yes_share >= probable_min:
        tier = "probable"
    else:
        tier = "unverified"
    reasons.append(f"tier = {tier} (verified_min={verified_min}, probable_min={probable_min})")

    return {
        "tier": tier, "nullified": False, "veto_pass": True,
        "veto_results": veto_results, "normal_results": normal_results,
        "yes_count": yes_count, "normal_total": normal_total, "yes_share": yes_share,
        "reasons": reasons,
    }


# ── Minimal YAML subset parser (stdlib-only; tailored to checklist.yaml) ───────
# Handles: nested maps, lists of scalars, lists of maps, scalars (int/float/bool/
# null/quoted/bare), `#` comments, and empty inline `{}` / `[]`. NOT a general
# YAML implementation — just enough for this one config, with DEFAULT_CHECKLIST
# as the safety net if anything here is exceeded.

def _strip_comment(line):
    out, in_s, q = [], False, ""
    for ch in line:
        if in_s:
            out.append(ch)
            if ch == q:
                in_s = False
        else:
            if ch in ("'", '"'):
                in_s = True
                q = ch
                out.append(ch)
            elif ch == "#":
                break
            else:
                out.append(ch)
    return "".join(out)


def _scalar(tok):
    tok = tok.strip()
    if tok == "" or tok == "~" or tok == "null":
        return None
    if tok in ("{}", "[]"):
        return {} if tok == "{}" else []
    if len(tok) >= 2 and tok[0] in "\"'" and tok[-1] == tok[0]:
        return tok[1:-1]
    low = tok.lower()
    if low in ("true", "yes"):
        return True
    if low in ("false", "no"):
        return False
    try:
        return int(tok)
    except ValueError:
        pass
    try:
        return float(tok)
    except ValueError:
        pass
    return tok


def _indent(line):
    return len(line) - len(line.lstrip(" "))


def _parse_block(lines, i, indent):
    """Parse a block at the given indent. Returns (value, next_index)."""
    # Decide list vs map by the first non-empty line at this indent.
    while i < len(lines) and lines[i].strip() == "":
        i += 1
    if i >= len(lines) or _indent(lines[i]) < indent:
        return None, i
    if lines[i].lstrip().startswith("- "):
        return _parse_list(lines, i, indent)
    return _parse_map(lines, i, indent)


def _parse_map(lines, i, indent):
    result = {}
    while i < len(lines):
        raw = lines[i]
        if raw.strip() == "":
            i += 1
            continue
        ind = _indent(raw)
        if ind < indent:
            break
        if ind > indent:  # stray deeper line; let caller handle
            break
        content = raw.strip()
        key, sep, rest = content.partition(":")
        if not sep:
            i += 1
            continue
        key = key.strip()
        rest = rest.strip()
        if rest == "":
            # nested block (map or list) on following deeper lines
            child, i = _parse_block(lines, i + 1, indent + 1)
            result[key] = child if child is not None else {}
        else:
            result[key] = _scalar(rest)
            i += 1
    return result, i


def _parse_list(lines, i, indent):
    items = []
    while i < len(lines):
        raw = lines[i]
        if raw.strip() == "":
            i += 1
            continue
        ind = _indent(raw)
        if ind < indent or not raw.strip().startswith("- "):
            break
        after = raw.strip()[2:]  # text after "- "
        if ":" in after and not (after[0] in "\"'"):
            # list item is a map; first key sits on the dash line
            first_indent = ind + 2
            synthetic = " " * first_indent + after
            block_lines = [synthetic]
            j = i + 1
            while j < len(lines):
                if lines[j].strip() == "":
                    block_lines.append(lines[j])
                    j += 1
                    continue
                if _indent(lines[j]) >= first_indent and not lines[j].strip().startswith("- "):
                    block_lines.append(lines[j])
                    j += 1
                elif _indent(lines[j]) >= first_indent and lines[j].strip().startswith("- "):
                    # nested list under a key — handled inside _parse_map recursion
                    block_lines.append(lines[j])
                    j += 1
                else:
                    break
            m, _ = _parse_map(block_lines, 0, first_indent)
            items.append(m)
            i = j
        else:
            items.append(_scalar(after))
            i += 1
    return items, i


def _parse_yaml(text):
    lines = [_strip_comment(ln).rstrip() for ln in text.split("\n")]
    # drop document markers
    lines = [ln for ln in lines if ln.strip() not in ("---", "...")]
    value, _ = _parse_block(lines, 0, 0)
    return value if value is not None else {}


def _coerce_types(cfg):
    """Ensure thresholds are floats and structure is well-formed enough to use."""
    th = cfg.get("thresholds") or {}
    for k in ("verified_min", "probable_min"):
        if k in th:
            try:
                th[k] = float(th[k])
            except (TypeError, ValueError):
                th[k] = DEFAULT_CHECKLIST["thresholds"][k]
    cfg["thresholds"] = {**DEFAULT_CHECKLIST["thresholds"], **th}
    if not isinstance(cfg.get("verified_also_requires"), list):
        cfg["verified_also_requires"] = list(DEFAULT_CHECKLIST["verified_also_requires"])
    if not isinstance(cfg.get("domain_packs"), dict):
        cfg["domain_packs"] = {}
    return cfg


if __name__ == "__main__":
    # Tiny smoke: load config and evaluate a strong, fully-answered claim.
    import json as _json
    cl = load_checklist()
    ctx = build_context(
        independent_sources=2, distinct_families=2, has_primary_citation=True,
        divergence=False,
        semantic_answers={
            "V1-FALSIFIABLE": True, "V2-TRACEABLE-ORIGIN": True,
            "V3-NO-INTERNAL-CONTRADICTION": True, "V4-SURVIVES-REFUTER": True,
            "N4-CITATION-SUPPORTS": True, "N6-REPRODUCIBLE": True,
            "N7-SPECIFIC": True, "N8-NO-CONFLICT-OF-INTEREST": True,
            "N10-LATERAL-SUPPORT": True,
        },
    )
    print(_json.dumps(evaluate(cl, ctx), indent=2))
