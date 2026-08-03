#!/usr/bin/env python3
"""
conductor.py — the live-run driver / pipeline for acos-axiom-synthesis.

Turns collected raw model replies (from the four families) into engine-ready
`fact` records and runs the deterministic pipeline (orchestrate.run).

WHY Python (repo default is TS/Rust): this is glue OVER the existing Python engine
— it imports orchestrate / decircularize / checklist and must build the exact
`fact` dicts orchestrate.run() consumes. Those structures live only in Python and
have no TS/Rust equivalent, so per the language rule's exception #2 (required
tooling exists only in Python) the conductor is Python.

WHAT THIS MODULE DOES (pure, deterministic, testable offline):
  - extract_json         : tolerantly pull a JSON object out of a model's text reply
                           (strips ```json fences, leading/trailing prose).
  - parse_elicitor/grader/refuter : validate a family's reply against the prompt
                           contract; return (obj, errors).
  - combine_graders      : per-question majority over N blind graders (fail-closed).
  - assemble_fact        : from an elicited claim + grader answers + refuter verdict,
                           build the `fact` dict orchestrate.process_fact expects.
  - cluster_claims       : group the same atomic claim surfaced by multiple families.
  - run_from_collected   : read a session collection dir, parse everything, cluster,
                           assemble facts, and call orchestrate.run().

WHAT THIS MODULE DOES NOT DO (driven by the orchestrating skill = main Claude at
runtime, because a subprocess cannot spawn Task() or drive a browser):
  - spawn Claude Task() elicitor/grader/refuter agents,
  - call run-external-agent.py for Gemini / GLM,
  - drive the ChatGPT browser voice.
  Those steps WRITE each raw reply into the collection layout this module reads.
  See RUNBOOK.md for the exact live-collection procedure and file layout.

Stdlib only. Python 3.8+.
"""

import json
import os
import re

import decircularize as dc
import orchestrate as orch
import volatility as vol


# ── tolerant JSON extraction ─────────────────────────────────────────────────

class ParseError(Exception):
    pass


_FENCE_RE = re.compile(r"```(?:json|JSON)?\s*(.*?)```", re.DOTALL)


def _first_balanced_object(s):
    """Return the substring of the first balanced {...} object, respecting strings
    and escapes. None if no balanced object is present."""
    start = s.find("{")
    if start == -1:
        return None
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(s)):
        ch = s[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return s[start:i + 1]
    return None


def extract_json(text):
    """Pull one JSON object out of a model's text reply, tolerating markdown code
    fences and surrounding prose/commentary. Raises ParseError if none is parseable.

    Order of attempts: (1) whole string; (2) inside a ```json fence; (3) the first
    balanced {...} object found anywhere in the text.
    """
    if text is None:
        raise ParseError("empty reply (None)")
    text = str(text).strip()
    if not text:
        raise ParseError("empty reply")

    # (1) the whole thing is JSON
    try:
        return json.loads(text)
    except Exception:
        pass

    # (2) a fenced block
    for m in _FENCE_RE.finditer(text):
        block = m.group(1).strip()
        try:
            return json.loads(block)
        except Exception:
            obj = _first_balanced_object(block)
            if obj is not None:
                try:
                    return json.loads(obj)
                except Exception:
                    pass

    # (3) the first balanced object anywhere
    obj = _first_balanced_object(text)
    if obj is not None:
        try:
            return json.loads(obj)
        except Exception as exc:
            raise ParseError(f"found a JSON object but it did not parse: {exc}")

    raise ParseError("no JSON object found in reply")


# ── per-family reply parsers (validate against the prompt contract) ───────────

_CHECKLIST_SEMANTIC = {  # questions the grader is allowed/expected to answer
    "V1-FALSIFIABLE", "V2-TRACEABLE-ORIGIN", "V3-NO-INTERNAL-CONTRADICTION",
    "N4-CITATION-SUPPORTS", "N6-REPRODUCIBLE", "N7-SPECIFIC",
    "N8-NO-CONFLICT-OF-INTEREST", "N10-LATERAL-SUPPORT",
}


def parse_elicitor(text):
    """Return (obj, errors). obj = {elicitor_id, family, claims:[...]}."""
    errors = []
    try:
        obj = extract_json(text)
    except ParseError as exc:
        return None, [f"elicitor: {exc}"]
    if not isinstance(obj, dict):
        return None, ["elicitor: top-level is not an object"]
    fam = obj.get("family") or ""
    claims = obj.get("claims")
    if not isinstance(claims, list):
        return None, ["elicitor: 'claims' missing or not a list"]
    clean = []
    for i, c in enumerate(claims):
        if not isinstance(c, dict) or not c.get("statement"):
            errors.append(f"elicitor claim {i}: missing 'statement' — skipped")
            continue
        clean.append({
            "statement": str(c["statement"]).strip(),
            "claim_type": c.get("claim_type", "categorical"),
            "value": c.get("value", c.get("statement")),
            "sub_question": c.get("sub_question"),
            "origin": c.get("origin"),
            "source_url": c.get("source_url", ""),
            "source_date": c.get("source_date", "undated"),
            "locator": c.get("locator", ""),
            "extraction_confidence": c.get("extraction_confidence", "medium"),
        })
    return {"elicitor_id": obj.get("elicitor_id", ""), "family": fam, "claims": clean}, errors


def parse_grader(text):
    """Return (obj, errors). obj = {grader_id, family, claim_id, checklist_answers,
    grading_flags}."""
    errors = []
    try:
        obj = extract_json(text)
    except ParseError as exc:
        return None, [f"grader: {exc}"]
    ans = obj.get("checklist_answers")
    if not isinstance(ans, dict):
        return None, ["grader: 'checklist_answers' missing or not an object"]
    coerced = {}
    for qid, v in ans.items():
        if qid not in _CHECKLIST_SEMANTIC:
            errors.append(f"grader: unexpected/ignored question '{qid}'")
            continue
        coerced[qid] = _as_bool(v)
    missing = _CHECKLIST_SEMANTIC - set(coerced)
    for qid in sorted(missing):
        errors.append(f"grader: missing answer for '{qid}' (treated as unanswered)")
    flags = obj.get("grading_flags") or {}
    # F4: the grader now emits a blind volatility label (durable/slow/fast/volatile)
    # instead of the retired freshness_ok flag (freshness is computed by code from
    # source dates; a legacy freshness_ok in the reply is silently ignored).
    vol_label = flags.get("volatility")
    if isinstance(vol_label, str):
        vol_label = vol_label.strip().lower()
    if vol_label not in vol.CLASSES:
        vol_label = None   # absent/invalid -> no judge signal (legacy replies OK)
    return {
        "grader_id": obj.get("grader_id", ""),
        "family": obj.get("family", ""),
        "claim_id": obj.get("claim_id", ""),
        "checklist_answers": coerced,
        "grading_flags": {
            "has_primary_citation": _as_bool(flags.get("has_primary_citation", False)) is True,
            "volatility": vol_label,
            "falsifiable": _as_bool(flags.get("falsifiable", True)) is not False,
        },
    }, errors


def parse_refuter(text):
    """Return (obj, errors). obj = {refuter_id, family, claim_id, objection, credible,
    rebutted, fatal, different_family_from_claim}."""
    errors = []
    try:
        obj = extract_json(text)
    except ParseError as exc:
        return None, [f"refuter: {exc}"]
    objection = obj.get("objection")
    if isinstance(objection, str) and objection.strip().lower() in ("", "null", "none"):
        objection = None
    return {
        "refuter_id": obj.get("refuter_id", ""),
        "family": obj.get("family", ""),
        "claim_id": obj.get("claim_id", ""),
        "objection": objection,
        "credible": _as_bool(obj.get("credible", False)) is True,
        "rebutted": _as_bool(obj.get("rebutted", False)) is True,
        "fatal": _as_bool(obj.get("fatal", False)) is True,
        "different_family_from_claim": _as_bool(obj.get("different_family_from_claim", True)) is not False,
    }, errors


def _as_bool(v):
    """Coerce a model's answer to True / False / None (None = unanswered/unknown)."""
    if isinstance(v, bool):
        return v
    if v is None:
        return None
    s = str(v).strip().lower()
    if s in ("true", "yes", "y", "1"):
        return True
    if s in ("false", "no", "n", "0"):
        return False
    return None


# ── grader consensus (N blind graders → one answer set) ───────────────────────

def combine_graders(graders):
    """Majority per question over N blind graders. Fail-closed: a tie or all-unanswered
    resolves to False (conservative — a veto False nullifies, a normal False costs a
    point). Returns {checklist_answers, grading_flags}."""
    answers = {}
    for qid in sorted(_CHECKLIST_SEMANTIC):
        yes = sum(1 for g in graders if g["checklist_answers"].get(qid) is True)
        no = sum(1 for g in graders if g["checklist_answers"].get(qid) is False)
        answers[qid] = True if yes > no else False
    # grading flags: majority, fail-closed to the conservative side
    def _flag(name, conservative):
        yes = sum(1 for g in graders if g["grading_flags"].get(name) is True)
        no = len(graders) - yes
        if name == "has_primary_citation":
            return yes > no  # need a majority to claim a primary citation
        return yes >= no     # falsifiable: keep True unless majority says no
    # F4 — volatility label: unique-max vote over the judges that answered. A tie
    # or no answers -> None (no judge signal; the deterministic lexical/domain
    # classifier stands alone, which is the conservative direction).
    labels = [g["grading_flags"].get("volatility") for g in graders]
    labels = [l for l in labels if l in vol.CLASSES]
    vote = None
    if labels:
        tally = {}
        for l in labels:
            tally[l] = tally.get(l, 0) + 1
        best = max(tally.values())
        winners = [l for l, n in tally.items() if n == best]
        if len(winners) == 1:
            vote = winners[0]
    return {
        "checklist_answers": answers,
        "grading_flags": {
            "has_primary_citation": _flag("has_primary_citation", False),
            "volatility": vote,
            "falsifiable": _flag("falsifiable", True),
        },
    }


# ── fact assembly ─────────────────────────────────────────────────────────────

def _source_from_claim(claim, family, sid, engine=False):
    """Build a decircularize-shaped source dict from an elicited claim.

    IMPORTANT: `text` is left empty on purpose. Independence is judged by
    origin + family + context_id — NOT by the claim's wording. Clustering groups
    candidates that assert the SAME statement, so putting that statement in `text`
    would make the verbatim-fingerprint rule wrongly merge two genuinely
    independent families into one vote, destroying cross-family corroboration.
    (This mirrors the engine's own fixtures, which use text="".)"""
    # The de-circularization ORIGIN key is the source URL when present (distinct
    # URLs = distinct sources = independent). Falls back to the source name, then to
    # whatever origin was given (e.g. the "model-internal" sentinel, which stays
    # non-independent and caps the claim at 'probable').
    decirc_origin = claim.get("source_url") or claim.get("origin")
    return {
        "id": sid,
        "family": family,
        "origin": decirc_origin,
        "context_id": claim.get("elicitor_id") or family,
        "text": "",
        "value": claim.get("value"),
        "locator": claim.get("locator", ""),
        "as_of": claim.get("source_date"),      # valid-time date; recorded for recency work
        "is_engine_output": engine,
    }


def assemble_fact(fact_id, cluster, grader_consensus, refuter, conflict=None,
                  domain=None, depends_on=None):
    """Build the engine `fact` dict from one clustered claim + its judgments.

    cluster = {statement, claim_type, sub_question, candidates:[{value, source}]}
    grader_consensus = output of combine_graders()
    refuter = a parse_refuter() dict (or None)
    """
    answers = dict(grader_consensus["checklist_answers"])
    flags = grader_consensus["grading_flags"]

    # V4-SURVIVES-REFUTER is derived from the refuter verdict (never asked of the grader):
    #   survives unless the objection is fatal AND credible AND not rebutted.
    if refuter is None:
        answers["V4-SURVIVES-REFUTER"] = True
        refuter_payload = None
    else:
        survives = not (refuter.get("fatal") and refuter.get("credible")
                        and not refuter.get("rebutted"))
        answers["V4-SURVIVES-REFUTER"] = bool(survives)
        refuter_payload = {
            "objection": refuter.get("objection"),
            "credible": bool(refuter.get("credible")),
            "rebutted": bool(refuter.get("rebutted")),
        }

    fact = {
        "fact_id": fact_id,
        "statement": cluster["statement"],
        "claim_type": cluster.get("claim_type", "categorical"),
        "sub_question": cluster.get("sub_question"),
        "candidates": cluster["candidates"],
        "grading": {
            "has_primary_citation": flags["has_primary_citation"],
        },
        "falsifiable": flags["falsifiable"],
        "checklist_answers": answers,           # engages checklist mode in orchestrate
    }
    if refuter_payload is not None:
        fact["refuter"] = refuter_payload
    if conflict is not None:
        fact["conflict"] = conflict
    if domain:
        fact["domain"] = domain
    # F4: the graders' blind volatility vote reaches the classifier as judge_label.
    if flags.get("volatility"):
        fact["volatility_judge"] = flags["volatility"]
    if depends_on:
        fact["depends_on"] = depends_on
    return fact


# ── claim clustering across families ──────────────────────────────────────────

def _norm(s):
    return re.sub(r"[^a-z0-9 ]", "", re.sub(r"\s+", " ", str(s).strip().lower()))


def _coerce_num(v):
    """Extract a float from a model-supplied value (often a string like '5,638,830').
    Returns None if no number can be recovered."""
    if isinstance(v, (int, float)):
        return float(v)
    s = re.sub(r"[^0-9.\-]", "", str(v))
    try:
        return float(s)
    except ValueError:
        return None


def cluster_claims(elicited):
    """Group the SAME atomic claim surfaced by multiple families into one cluster.

    elicited = [{family, elicitor_id, claim:{...}}].  v1 heuristic: group by
    normalized statement text. Claims with the same statement but DIFFERENT values
    become a `conflict`. This is deterministic and honest; a semantic-match model
    upgrade is noted in RUNBOOK.md (matching is a judgement step, like de-circ).

    Returns [ {statement, claim_type, sub_question, candidates:[{value,source}],
               conflict|None, families:[...] } ], stable-ordered by first appearance.
    """
    order = []
    groups = {}
    for e in elicited:
        c = e["claim"]
        key = _norm(c["statement"])
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(e)

    clusters = []
    for idx, key in enumerate(order):
        members = groups[key]
        candidates = []
        values_seen = {}
        for j, e in enumerate(members):
            sid = f"{e['family']}-{e.get('elicitor_id') or 'x'}-{j}"
            src = _source_from_claim({**e["claim"], "elicitor_id": e.get("elicitor_id")},
                                     e["family"], sid)
            candidates.append({"value": e["claim"].get("value"), "source": src})
            values_seen.setdefault(_norm(e["claim"].get("value")), e["claim"].get("value"))
        first = members[0]["claim"]
        claim_type = first.get("claim_type", "categorical")
        # Numeric fusion needs real numbers. Coerce string values to float; if ANY
        # candidate can't be coerced, fall back to categorical so fusion still works
        # (the engine's median/mean path would otherwise crash on a string).
        if claim_type == "numeric":
            coerced = [_coerce_num(cand["value"]) for cand in candidates]
            if all(x is not None for x in coerced):
                for cand, num in zip(candidates, coerced):
                    cand["value"] = num
            else:
                claim_type = "categorical"
        conflict = None
        if len(values_seen) > 1:
            conflict = [{"value": v, "directness": 2} for v in values_seen.values()]
        clusters.append({
            "statement": first["statement"],
            "claim_type": claim_type,
            "sub_question": first.get("sub_question"),
            "candidates": candidates,
            "conflict": conflict,
            "families": sorted({e["family"] for e in members if e["family"]}),
        })
    return clusters


# ── collection-layout reader + end-to-end runner ──────────────────────────────

# Map a collection filename stem to the authoritative model family (the transport
# we actually called). Models mis-report their own family, so the filename — which
# WE control when writing the reply — is the source of truth for independence.
_FAMILY_BY_STEM = {
    "gemini": "google", "google": "google",
    "glm": "zai", "zai": "zai",
    "claude": "anthropic", "anthropic": "anthropic", "opus": "anthropic", "sonnet": "anthropic",
    "chatgpt": "openai-web", "gpt": "openai-web", "openai": "openai-web",
}


def family_from_filename(fn):
    """Authoritative family from a collection filename (e.g. 'gemini.json' -> 'google',
    'C1__glm.json' -> 'zai'). Falls back to the raw stem if unrecognized."""
    base = os.path.basename(fn).rsplit(".", 1)[0]
    stem = base.split("__")[-1] if "__" in base else base
    stem = stem.split("-")[0].lower()
    return _FAMILY_BY_STEM.get(stem, stem)


def _read(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def load_collected(session_dir):
    """Read the collection layout written by the live orchestrator.

    Layout:
      <session_dir>/collected/elicitor/<family>[-<n>].json     (raw elicitor replies)
      <session_dir>/collected/grader/<claim_id>__<family>.json (raw grader replies)
      <session_dir>/collected/refuter/<claim_id>.json          (raw refuter reply)

    Returns {elicited:[...], graders_by_claim:{cid:[...]}, refuter_by_claim:{cid:...},
             parse_errors:[...]}.
    """
    base = os.path.join(session_dir, "collected")
    elicited, parse_errors = [], []
    graders_by_claim, refuter_by_claim = {}, {}

    edir = os.path.join(base, "elicitor")
    if os.path.isdir(edir):
        for fn in sorted(os.listdir(edir)):
            if not fn.endswith(".json"):
                continue
            obj, errs = parse_elicitor(_read(os.path.join(edir, fn)))
            parse_errors += errs
            if obj:
                # Family is tagged by the KNOWN transport (the filename = which
                # endpoint we actually called), NOT the model's self-report — models
                # frequently mis-name their own family, which would silently collapse
                # cross-family independence in de-circularization.
                fam = family_from_filename(fn)
                if obj["family"] and obj["family"] != fam:
                    parse_errors.append(
                        f"elicitor {fn}: model self-reported family '{obj['family']}' "
                        f"overridden by transport family '{fam}'")
                for c in obj["claims"]:
                    elicited.append({"family": fam,
                                     "elicitor_id": obj["elicitor_id"], "claim": c})

    gdir = os.path.join(base, "grader")
    if os.path.isdir(gdir):
        for fn in sorted(os.listdir(gdir)):
            if not fn.endswith(".json"):
                continue
            cid = fn.split("__")[0]
            obj, errs = parse_grader(_read(os.path.join(gdir, fn)))
            parse_errors += errs
            if obj:
                graders_by_claim.setdefault(cid, []).append(obj)

    rdir = os.path.join(base, "refuter")
    if os.path.isdir(rdir):
        for fn in sorted(os.listdir(rdir)):
            if not fn.endswith(".json"):
                continue
            cid = fn.split("__")[0].rsplit(".", 1)[0]
            obj, errs = parse_refuter(_read(os.path.join(rdir, fn)))
            parse_errors += errs
            if obj:
                refuter_by_claim[cid] = obj

    return {"elicited": elicited, "graders_by_claim": graders_by_claim,
            "refuter_by_claim": refuter_by_claim, "parse_errors": parse_errors}


def build_facts(collected, domain=None):
    """Cluster elicited claims and assemble one `fact` per cluster, attaching each
    cluster's grader consensus + refuter verdict by cluster index (claim id 'C<idx>').
    `domain` is an optional run-level subject tag (F4) that feeds the volatility
    classifier's domain prior on every fact. Returns (facts, notes)."""
    clusters = cluster_claims(collected["elicited"])
    facts, notes = [], []
    for idx, cl in enumerate(clusters, 1):
        cid = f"C{idx}"
        graders = collected["graders_by_claim"].get(cid, [])
        if graders:
            consensus = combine_graders(graders)
        else:
            # No grader answers → engine falls back to the legacy grade path for this
            # claim (checklist not engaged). Flag it so the gap is visible, not silent.
            notes.append(f"{cid}: no grader answers collected — legacy grade path used")
            facts.append({
                "fact_id": cid, "statement": cl["statement"],
                "claim_type": cl.get("claim_type", "categorical"),
                "sub_question": cl.get("sub_question"), "candidates": cl["candidates"],
                "grading": {"has_primary_citation": False}, "falsifiable": True,
                **({"conflict": cl["conflict"]} if cl["conflict"] else {}),
                **({"domain": domain} if domain else {}),
            })
            continue
        refuter = collected["refuter_by_claim"].get(cid)
        facts.append(assemble_fact(cid, cl, consensus, refuter, conflict=cl["conflict"],
                                   domain=domain))
    return facts, notes


def run_from_collected(session_dir, question, sub_questions, now,
                       repo_root=".", date_str="1970-01-01", session="live",
                       domain=None):
    """Full offline half of the pipeline: read collected raw replies → parse →
    cluster → assemble facts → run the deterministic engine. Returns the orchestrate
    summary augmented with parse_errors + assembly notes.

    F4: pass the REAL run date as `date_str` (freshness windows measure source ages
    against it) and, when the question has a known subject, a `domain` tag (e.g.
    'rates', 'ai', 'geography') so the volatility classifier gets its domain prior."""
    collected = load_collected(session_dir)
    facts, notes = build_facts(collected, domain=domain)
    result = orch.run(session_dir, question, sub_questions, facts, now,
                      repo_root=repo_root, date_str=date_str, session=session)
    result["parse_errors"] = collected["parse_errors"]
    result["assembly_notes"] = notes
    result["facts_built"] = len(facts)
    return result
