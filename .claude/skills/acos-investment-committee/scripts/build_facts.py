#!/usr/bin/env python3
"""
build_facts.py — C1: objection -> axiom-synthesis `fact` adapter + Axis-S side-channel.

Reads the per-seat objections collected for one IC session round
(`<session>/rounds/round-01/*.json`, each seat file authored per the A2 objection
schema below) and emits, into `<session>/synthesis/`:

  facts.json         — one axiom-synthesis `fact` dict per objection AND per mitigant,
                       shaped EXACTLY as the vendored orchestrate.py::process_fact()
                       consumes: {fact_id, statement, claim_type, candidates[{value,
                       source{id,family,origin,context_id,text}}], grading, flags,
                       refuter, conflict, depends_on, covers, falsifiable}. Objections
                       are top-level facts (depends_on == []); every mitigant_hypothesis
                       (inline on an objection OR authored by the Deal Advocate, seat #9)
                       becomes its OWN dependent fact that depends_on the objection it
                       retires. Objections are emitted first, then mitigants (so a
                       mitigant's depends_on target already exists when the ledger is
                       walked in order).

  severity-map.json  — THE Axis-S side-channel, orthogonal to the engine's truth-grading:
                       { objection_fact_id: {axis_s, raised_by_seat, rationale} }.
                       Axis S NEVER enters the engine (it is not a `fact` field and is not
                       arithmetically combined with Axis A / Axis B anywhere). This is the
                       contract compute_verdict.py (C3) reads.

  mitigant-map.json  — mitigant metadata the ledger cannot carry (residual_risk is a
                       rendering-time domain compute, not an engine field):
                       { mitigant_fact_id: {retires, mitigant_type, statement,
                       residual_risk, raised_by_seat} }. Read by render_memo.py (C4) to
                       build the Risk -> Mitigant -> Residual triplet + Conditions Precedent.

--- A2 objection schema (each `<session>/rounds/round-01/<seat>.json`) --------------
{
  "seat": 4, "seat_name": "Legal & Structural", "role_family": "legal",
  "objections": [
    {
      "objection_id": "OBJ-...",              # stable; auto-derived if absent
      "statement": "the deal fails because ...",
      "falsifiable_form": "fails if/because ___; evidence present/absent/untested",
      "claim_type": "categorical|numeric|textual",   # default categorical
      "assertion_value": "<token all evidence candidates carry>",  # default "holds"
      "axis_s": "informational|limitation|material-risk|deal-breaker-candidate",
      "axis_s_rationale": "why this materiality",
      "covers": ["<16-risk category>", ...],
      "grading": {"has_primary_citation": true, "downgrades": [...], "upgrades": [...]},
      "flags": {},                            # model-produced Stage-5 triggers (see SEAM)
      "refuter": null,                        # model-produced cross-exam verdict (see SEAM)
      "conflict": null,                       # same-fact contradiction -> resolve_conflict
      "falsifiable": true,
      "evidence": [{"citation": "...", "locator": "...", "origin": "...", "text": "..."}],
      "mitigant_hypothesis": { ...mitigant fields... }   # optional inline mitigant
    }
  ],
  "mitigants": [                              # optional; used by Deal Advocate (#9)
    { "mitigant_id": "MIT-...", "retires_objection_id": "OBJ-...",
      "statement": "...", "mitigant_type": "reserve|guaranty|covenant|insurance|holdback|CP",
      "residual_risk": "mandatory — what remains after the mitigant",
      "falsifiable": true,
      "evidence": [ ... ] }                   # documentary citation => traceable origin => can
                                              # reach CORROBORATED; NO documentary evidence
                                              # (empty list, or explicit "origin": null) =>
                                              # untraceable self-assertion => stays CONJECTURE
  ]
}

Evidence -> source.origin: if an evidence dict OMITS the "origin" key, a traceable origin is
derived from citation(+locator). If "origin" is present (even null), it is respected literally
— an explicit null marks non-documentary support the engine must NOT credit. Empty evidence
yields ONE untraceable self-assertion candidate (so an unsupported claim stays CONJECTURE
rather than crashing the fusion of an empty candidate set).

--- SEAM (model-produced fields) ----------------------------------------------------
`flags` (Stage-5 hard/soft triggers) and `refuter` ({objection, credible, rebutted}) are
produced UPSTREAM by Task()-spawned agents in the live skill (the DIFFERENT-discipline
falsification-gate refuter). This adapter passes whatever the seat file provides straight
through onto the `fact`; when a field is absent it defaults to {} / None (clean gate), which
is the deterministic stub used by the smoke test. The real skill fills them before C2 runs.

Axis S is NEVER blended: it is written ONLY to severity-map.json and is never read into any
`fact` field, grading input, or arithmetic here. Grep-clean separation of Axis A/B vs Axis S.

Stdlib only. Python 3.8+.
"""

import argparse
import json
import os
import re
import sys

AXIS_S_LADDER = ["informational", "limitation", "material-risk", "deal-breaker-candidate"]

# Casing / punctuation-tolerant Axis-S normalization. Keys are compared after lowercasing,
# stripping, and collapsing whitespace/underscores to hyphens; a hyphen-stripped fallback is
# also tried. A genuinely off-ladder value still raises (that is a real authoring error).
AXIS_S_ALIASES = {
    "info": "informational", "informational": "informational",
    "limit": "limitation", "limited": "limitation", "limitation": "limitation",
    "material": "material-risk", "material-risk": "material-risk",
    "materialrisk": "material-risk", "materialrisks": "material-risk",
    "deal-breaker": "deal-breaker-candidate", "dealbreaker": "deal-breaker-candidate",
    "deal-breaker-candidate": "deal-breaker-candidate",
    "dealbreakercandidate": "deal-breaker-candidate",
}


def _norm_axis_s(raw):
    """Map a seat-authored Axis-S token to the canonical ladder value (casing/punct tolerant).
    Unknown values pass through unchanged so the ladder check below still catches real errors."""
    if raw is None:
        return "limitation"
    key = re.sub(r"[\s_]+", "-", str(raw).strip().lower())
    return AXIS_S_ALIASES.get(key) or AXIS_S_ALIASES.get(key.replace("-", "")) or key


def _coerce_evidence(evidence):
    """Normalize the shapes a seat might emit into a list of evidence dicts. Accepts:
    None/[] -> []; a list of dicts/strings -> list of dicts; a lone dict -> [dict];
    a bare string -> [{"citation": string}]. Never invents documentary support — a string
    becomes a citation-only dict whose origin still resolves from the citation text."""
    if not evidence:
        return []
    if isinstance(evidence, dict):
        return [evidence]
    if isinstance(evidence, str):
        return [{"citation": evidence}]
    out = []
    for ev in evidence:
        if isinstance(ev, dict):
            out.append(ev)
        elif isinstance(ev, str) and ev.strip():
            out.append({"citation": ev})
        elif ev:
            out.append({"citation": str(ev)})
    return out


def _seat_from_filename(path):
    m = re.search(r"seat[-_]?0*(\d+)", os.path.basename(path), re.IGNORECASE)
    return int(m.group(1)) if m else None


def _coerce_seat_doc(seat_doc, path):
    """Tolerate a seat file that is a bare list of objections, a single objection/mitigant
    object written without the wrapper, or a wrapper missing its `seat` number. Returns a
    wrapper dict guaranteed to have `objections` and `mitigants` keys. Invents no evidence,
    no severity, no seat identity beyond what the filename literally encodes."""
    if isinstance(seat_doc, list):
        seat_doc = {"objections": seat_doc}
    elif isinstance(seat_doc, dict) and "objections" not in seat_doc and "mitigants" not in seat_doc:
        if seat_doc.get("retires_objection_id"):
            seat_doc = {"mitigants": [seat_doc]}
        elif seat_doc.get("statement") or seat_doc.get("falsifiable_form"):
            seat_doc = {"objections": [seat_doc]}
        else:
            seat_doc = dict(seat_doc)  # unknown wrapper-less shape: leave, defaults added below
    if not isinstance(seat_doc, dict):
        raise SystemExit("seat file {} is neither a JSON object nor a list".format(path))
    if seat_doc.get("seat") is None:
        derived = _seat_from_filename(path)
        if derived is not None:
            seat_doc["seat"] = derived
    seat_doc.setdefault("objections", [])
    seat_doc.setdefault("mitigants", [])
    return seat_doc


# A mitigant string that reads as a refusal ("None from this seat …", "N/A", "no cure") is
# dropped rather than turned into a conjecture. Intentionally narrow so it never eats a real
# cure that merely starts with "No" ("Notify…", "Negotiate…") — those do not match.
_MITIGANT_NONE_RE = re.compile(
    r"^\s*(none\b|n/?a\b|no\s+(mitigant|cure|further)|not\s+applicable)", re.IGNORECASE)


def _coerce_mitigant(m, retires_id=None):
    """Normalize a seat-authored mitigant into a dict (or None to skip). Seats emit them three
    ways: a full dict, a {cure, residual_risk} dict (key alias for statement), or a bare prose
    string. A refusal string is dropped; any other string becomes a no-evidence CONJECTURE
    mitigant — which can never reach CORROBORATED, so it cannot silently clear a deal-breaker.
    retires_id, when supplied, is stamped on so pass-2's integrity check can find its target."""
    if not m:
        return None
    if isinstance(m, str):
        if _MITIGANT_NONE_RE.match(m):
            return None
        out = {"statement": m.strip(), "mitigant_type": "conjecture", "evidence": [],
               "residual_risk": "", "falsifiable": True}
        if retires_id:
            out["retires_objection_id"] = retires_id
        return out
    if isinstance(m, dict):
        m = dict(m)
        if not m.get("statement") and m.get("cure"):      # key alias: {cure} -> statement
            m["statement"] = m["cure"]
        if retires_id and not m.get("retires_objection_id"):
            m["retires_objection_id"] = retires_id
        return m
    return None


def _slug(text):
    return re.sub(r"[^A-Za-z0-9]+", "-", str(text).strip()).strip("-").upper()[:40] or "X"


def _origin_for(ev):
    """Resolve an evidence dict's traceable origin. An explicit 'origin' key is respected
    literally (null => non-documentary, uncreditable). Otherwise derive from citation+locator."""
    if "origin" in ev:
        return ev["origin"] or None
    if ev.get("citation"):
        loc = ev.get("locator")
        return ev["citation"] + (("#" + _slug(loc)) if loc else "")
    return None


def _candidates_from_evidence(evidence, seat, family, assertion_value, id_prefix):
    """evidence[] -> candidate[] with source{id,family,origin,context_id,text}.

    seat -> source.family (role-diversity) and seat -> source.context_id, so multiple
    citations from ONE seat collapse to a single independent vote in de-circularization
    (one seat = one voice). A source with no traceable `origin` is NOT credited as a
    corroborator (aspirational/undocumented support). Empty evidence => one untraceable
    self-assertion candidate so the claim stays CONJECTURE (never crashes fusion)."""
    evidence = _coerce_evidence(evidence)
    if not evidence:
        return [{
            "value": assertion_value,
            "source": {"id": "{}-assert".format(id_prefix), "family": family,
                       "origin": None, "context_id": "seat-{}".format(seat),
                       "text": "(seat assertion; no documentary evidence supplied)"},
        }]
    cands = []
    for i, ev in enumerate(evidence):
        cands.append({
            "value": assertion_value,
            "source": {
                "id": "{}-e{}".format(id_prefix, i),
                "family": family,
                "origin": _origin_for(ev),
                "context_id": "seat-{}".format(seat),
                "text": ev.get("text") or ev.get("citation") or "",
            },
        })
    return cands


def _base_fact(fact_id, statement, claim_type, candidates, grading, flags, refuter,
               conflict, depends_on, covers, falsifiable):
    """Assemble a `fact` dict in the EXACT shape orchestrate.py::process_fact consumes."""
    return {
        "fact_id": fact_id,
        "statement": statement,
        "claim_type": claim_type or "categorical",
        "candidates": candidates,
        "grading": grading or {},          # engine Axis A/B inputs ONLY (never Axis S)
        "flags": flags or {},              # SEAM: model-produced Stage-5 triggers
        "refuter": refuter,                # SEAM: model-produced different-discipline verdict
        "conflict": conflict,              # same-fact contradiction -> resolve_conflict
        "depends_on": depends_on,
        "covers": covers or [],
        "falsifiable": bool(falsifiable) if falsifiable is not None else True,
    }


def _has_documentary(evidence):
    return any(_origin_for(ev) for ev in _coerce_evidence(evidence))


def _mitigant_fact(mit, retires_id, seat, family):
    mid = mit.get("mitigant_id") or ("MIT-" + _slug(mit.get("statement", retires_id)))
    cands = _candidates_from_evidence(
        mit.get("evidence"), seat, family,
        assertion_value=mit.get("assertion_value", "mitigant-holds"),
        id_prefix="{}-{}".format(seat, mid))
    fact = _base_fact(
        fact_id=mid,
        statement=mit.get("statement", ""),
        claim_type=mit.get("claim_type", "categorical"),
        candidates=cands,
        grading=mit.get("grading", {"has_primary_citation": _has_documentary(mit.get("evidence"))}),
        flags=mit.get("flags", {}),
        refuter=mit.get("refuter"),
        conflict=mit.get("conflict"),
        depends_on=[retires_id],           # the mitigant depends_on the objection it retires
        covers=mit.get("covers", []),
        falsifiable=mit.get("falsifiable", True),
    )
    meta = {
        "retires": retires_id,
        "mitigant_type": mit.get("mitigant_type", "control"),
        "statement": mit.get("statement", ""),
        "residual_risk": mit.get("residual_risk", ""),   # mandatory at render time (C4)
        "raised_by_seat": seat,
    }
    return fact, mid, meta


def _load_refuters(round_dir):
    """Load a round's optional refuters.json (the model-produced SEAM): a map
    {fact_id: {objection, credible, rebutted}} produced UPSTREAM by moderator-spawned
    different-discipline refuter agents, applied onto the matching fact's `refuter` field so
    the vendored falsify gate can downgrade a merely-deferred "cure" (e.g. a "condition funding
    on getting an appraisal later" mitigant) out of CORROBORATED — so it can no longer clear a
    deal-breaker it does not actually cure now."""
    rf = os.path.join(round_dir, "refuters.json")
    if os.path.isfile(rf):
        with open(rf, "r", encoding="utf-8") as fh:
            return json.load(fh) or {}
    return {}


def _resolve_seat_files(session_dir, round_name):
    """Return (seat_file_paths, refuter_map).

    round_name == "all" (Mode B, multi-round): each seat's LATEST turn wins — for a given
    seat file name (seat-NN.json), the copy in the highest-numbered round-* dir supersedes any
    earlier one (a seat's most recent word is its committee position). Refuter maps are merged
    across rounds, later rounds overriding. Otherwise a single round dir is read as-is.
    """
    rounds_root = os.path.join(session_dir, "rounds")
    if round_name == "all":
        round_dirs = sorted(
            os.path.join(rounds_root, d) for d in (os.listdir(rounds_root) if os.path.isdir(rounds_root) else [])
            if d.startswith("round-") and os.path.isdir(os.path.join(rounds_root, d)))
        latest, refuter_map = {}, {}
        for rd in round_dirs:                      # ascending; later rounds override
            refuter_map.update(_load_refuters(rd))
            for f in os.listdir(rd):
                if f.endswith(".json") and f != "refuters.json":
                    latest[f] = os.path.join(rd, f)
        return sorted(latest.values()), refuter_map
    round_dir = os.path.join(rounds_root, round_name)
    seat_files = sorted(
        os.path.join(round_dir, f) for f in os.listdir(round_dir)
        if f.endswith(".json") and f != "refuters.json"
    ) if os.path.isdir(round_dir) else []
    return seat_files, _load_refuters(round_dir)


def build(session_dir, round_name="round-01"):
    seat_files, refuter_map = _resolve_seat_files(session_dir, round_name)

    objection_facts, mitigant_facts = [], []
    severity_map, mitigant_map = {}, {}
    known_objection_ids = set()

    # ---- pass 1: objections (+ inline mitigant_hypothesis) ----
    for path in seat_files:
        with open(path, "r", encoding="utf-8") as fh:
            seat_doc = json.load(fh)
        seat_doc = _coerce_seat_doc(seat_doc, path)
        seat = seat_doc.get("seat")
        family = seat_doc.get("role_family") or "seat-{}".format(seat)

        for obj in seat_doc.get("objections", []) or []:
            oid = (obj.get("objection_id") or obj.get("id")
                   or ("OBJ-{}-{}".format(seat, _slug(obj.get("statement", "")))))
            known_objection_ids.add(oid)
            cands = _candidates_from_evidence(
                obj.get("evidence"), seat, family,
                assertion_value=obj.get("assertion_value", "holds"),
                id_prefix="{}-{}".format(seat, oid))
            objection_facts.append(_base_fact(
                fact_id=oid,
                statement=obj.get("statement", ""),
                claim_type=obj.get("claim_type", "categorical"),
                candidates=cands,
                grading=obj.get("grading", {"has_primary_citation": _has_documentary(obj.get("evidence"))}),
                flags=obj.get("flags", {}),
                refuter=refuter_map.get(oid) or obj.get("refuter"),
                conflict=obj.get("conflict"),
                depends_on=[],                        # objections are top-level facts
                covers=obj.get("covers", []),
                falsifiable=obj.get("falsifiable", True),
            ))

            # Axis-S key aliases: seats have emitted `axis_s`, `axis_s_severity`, or `severity`.
            axis_s_raw = (obj.get("axis_s") or obj.get("axis_s_severity")
                          or obj.get("severity") or "limitation")
            axis_s = _norm_axis_s(axis_s_raw)
            if axis_s not in AXIS_S_LADDER:
                # Conservative fail: an unrecognized severity is treated as material-risk (so it
                # STILL counts in the deal-breaker predicate) rather than crashing the run or —
                # far worse for a lender — silently defaulting to the mildest rung. Warn loudly.
                sys.stderr.write(
                    "WARN: axis_s '{}' for {} not on ladder {} -> defaulting to 'material-risk'\n".format(
                        axis_s_raw, oid, AXIS_S_LADDER))
                axis_s = "material-risk"
            severity_map[oid] = {
                "axis_s": axis_s,                     # Axis S — side-channel ONLY
                "raised_by_seat": seat,
                "rationale": obj.get("axis_s_rationale", ""),
            }

            inline = _coerce_mitigant(obj.get("mitigant_hypothesis"))
            if inline:
                mfact, mid, meta = _mitigant_fact(inline, oid, seat, family)
                if mid in refuter_map:
                    mfact["refuter"] = refuter_map[mid]
                mitigant_facts.append(mfact)
                mitigant_map[mid] = meta

            # NEW (2026-07-10): each seat now proposes its own cures inline (Advocate retired).
            for sm in (obj.get("suggested_mitigants") or []):
                cm = _coerce_mitigant(sm, retires_id=oid)
                if not cm:
                    continue
                mfact, mid, meta = _mitigant_fact(cm, oid, seat, family)
                if mid in refuter_map:
                    mfact["refuter"] = refuter_map[mid]
                mitigant_facts.append(mfact)
                mitigant_map[mid] = meta

    # ---- pass 2: standalone mitigants (legacy Deal Advocate path — retired; usually empty now) ----
    for path in seat_files:
        with open(path, "r", encoding="utf-8") as fh:
            seat_doc = json.load(fh)
        seat_doc = _coerce_seat_doc(seat_doc, path)
        seat = seat_doc.get("seat")
        family = seat_doc.get("role_family") or "seat-{}".format(seat)
        for raw_mit in seat_doc.get("mitigants", []) or []:
            mit = _coerce_mitigant(raw_mit)
            if not mit:
                continue
            retires_id = mit.get("retires_objection_id")
            if retires_id not in known_objection_ids:
                # Skip (do not crash) a mitigant that retires an unknown objection. The safe
                # failure mode is that the targeted objection stays UN-mitigated (conservative),
                # never that the whole committee run aborts after the seats have already run.
                sys.stderr.write(
                    "WARN: mitigant {} retires unknown objection '{}' -> skipped\n".format(
                        mit.get("mitigant_id"), retires_id))
                continue
            mfact, mid, meta = _mitigant_fact(mit, retires_id, seat, family)
            if mid in refuter_map:
                mfact["refuter"] = refuter_map[mid]
            mitigant_facts.append(mfact)
            mitigant_map[mid] = meta

    facts = objection_facts + mitigant_facts       # objections first, then dependents

    out_dir = os.path.join(session_dir, "synthesis")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "facts.json"), "w", encoding="utf-8") as fh:
        json.dump({"facts": facts}, fh, indent=2, ensure_ascii=False)
    with open(os.path.join(out_dir, "severity-map.json"), "w", encoding="utf-8") as fh:
        json.dump(severity_map, fh, indent=2, ensure_ascii=False)
    with open(os.path.join(out_dir, "mitigant-map.json"), "w", encoding="utf-8") as fh:
        json.dump(mitigant_map, fh, indent=2, ensure_ascii=False)

    return {
        "objections": len(objection_facts),
        "mitigants": len(mitigant_facts),
        "severity_entries": len(severity_map),
        "out_dir": out_dir,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="Build axiom-synthesis facts + Axis-S side-channel from IC objections.")
    ap.add_argument("--session", required=True, help="IC session directory (contains rounds/)")
    ap.add_argument("--round", default="round-01",
                    help="round subdirectory name (default round-01); pass 'all' for Mode B "
                         "multi-round aggregation (each seat's latest turn wins, refuters merged)")
    args = ap.parse_args(argv)
    res = build(args.session, args.round)
    print("build_facts: {objections} objections + {mitigants} mitigants -> {out_dir}".format(**res))
    print("  severity-map entries: {}".format(res["severity_entries"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
