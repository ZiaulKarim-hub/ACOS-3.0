#!/usr/bin/env python3
"""knowledge_lib.py — per-project knowledge store (ACOS Resurrection Protocol).

WHAT THIS IS (user brief 2026-08-04, workstream KB):
  A handoff answers "where was I". A knowledge base answers "what do I know".
  They are DIFFERENT JOBS and this file is the second one. Handoffs stay
  session-sized and are never merged into this.

SHAPE — a knowledge GRAPH, not a pile of notes (user preference 2026-08-05).
  The brief (D1) fixed only the LOCATION; the arrangement inside was open, and
  Zee asked for a graph. So the store is nodes + edges:

    fact   nodes  — one durable claim each, with its evidence
    entity nodes  — the things facts are about (a deal, a script, a tool)
    edges         — fact --about--> entity, fact --supersedes--> fact,
                    fact --learned_in--> project (carries cross-project reach,
                    which is what KB-E later walks)

  Storage is append-only JSONL, one file per node type. Append-only is a
  SAFETY property, not a filing preference: D5(b) requires that no write is
  ever destructive, so a wrong auto-written fact is always reversible by
  superseding it, and nothing a session wrote can be silently erased.

D1  keyed by project_uuid, NEVER by folder root — 19 registry rows share the
    ACOS 3.0 root, so a folder-keyed store would merge separate projects.
D2  sits BESIDE ~/.claude/skills/acos-okoa-works/references/, replaces nothing.
D4  Kind 1 (machine-verifiable) is auto-written silently; Kind 2 (Zee's own
    rulings) is asked about, capped at 2 questions per session. This module
    stores the kind and enforces the cap; the SORTING is a judgement the
    session makes, exactly like the intent core.
D5a EVIDENCE OR NO WRITE. append_fact refuses a fact with no source.
D5c staleness re-check — a fact naming a count, a path or a date carries a
    `verify` block, re-run on resurrect. This is what would have caught the
    "1,305 files" claim drifting to a live 1,594.
D6  honest risk, kept on the record: auto-writing means a wrong fact can enter
    without Zee seeing it. These rules shrink that risk; they do not remove it.

VERIFY BLOCKS ARE DECLARATIVE, NEVER SHELL. A stored fact can ask for
file_exists / file_count / path_contains / value_matches and nothing else.
Storing a shell command would make the store an execution channel: any wrong
or malicious auto-written fact would then run code at every resurrect. Checks
are interpreted here, in this file, against a fixed whitelist.

Constraints (shared with registry_lib.py, same script family):
  * system /usr/bin/python3 is 3.9.6, stdlib ONLY, no yaml module
  * atomic writes via the same mkstemp -> fsync -> os.replace discipline
  * every public function takes home=None so tests never touch the real ~
Python (not TypeScript/Rust) because this module is imported by the embedded
python bodies of close-project.sh and adopt-project.sh, which are fixed to the
system interpreter — the existing-code exception.

Self-test: python3 knowledge_lib.py --selftest --home DIR
"""

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone

KINDS = ("machine", "ruling")
"""machine = Kind 1, auto-written silently. ruling = Kind 2, Zee decided it."""

KIND2_QUESTION_CAP = 2
"""D4: at most TWO questions per session, ever. Overflow is DROPPED, not asked
and not auto-written — the brief's own guidance for an unsure sorter."""

EVIDENCE_TYPES = ("path", "command", "quote", "observation")
CHECK_TYPES = ("file_exists", "file_count", "path_contains", "value_matches")

FACTS_FILE = "facts.jsonl"
ENTITIES_FILE = "entities.jsonl"
EDGES_FILE = "edges.jsonl"
INDEX_FILE = "index.json"
SEEN_FILE = "last-seen.json"


# --------------------------------------------------------------------------
# paths
# --------------------------------------------------------------------------

def _home(home=None):
    return home if home else os.path.expanduser("~")


def store_dir(project_uuid, home=None):
    return os.path.join(_home(home), ".acos", "knowledge", project_uuid)


def _p(project_uuid, name, home=None):
    return os.path.join(store_dir(project_uuid, home), name)


def utc_now_iso():
    return datetime.now(timezone.utc).isoformat()


# --------------------------------------------------------------------------
# append-only primitives
# --------------------------------------------------------------------------

def _atomic_write(path, text):
    """mkstemp in the target's own dir -> fsync -> os.replace -> fsync dir.
    Never a fixed .tmp name (registry_lib measured 180/360 torn under
    contention with a fixed name; mkstemp: 0)."""
    d = os.path.dirname(path)
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp-", suffix=".swap")
    try:
        with os.fdopen(fd, "w") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    dfd = os.open(d, os.O_RDONLY)
    try:
        os.fsync(dfd)
    finally:
        os.close(dfd)


def _append_line(path, obj):
    """ONE os.write of a complete line — the append-only guarantee. A partial
    line can never be produced, so a reader never sees half a fact."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    line = (json.dumps(obj, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        os.write(fd, line)
        os.fsync(fd)
    finally:
        os.close(fd)


def _read_lines(path):
    """Every parseable line. A corrupt line is SKIPPED and counted, never fatal
    — one bad line must not make a whole knowledge base unreadable."""
    rows, bad = [], 0
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except ValueError:
                    bad += 1
    except FileNotFoundError:
        return [], 0
    return rows, bad


# --------------------------------------------------------------------------
# node ids
# --------------------------------------------------------------------------

def fact_id(claim, subject):
    """Content-addressed: the same claim about the same subject is the same
    node, so re-closing a project cannot fill the store with duplicates."""
    h = hashlib.sha256(("%s\x00%s" % (subject.strip().casefold(),
                                      claim.strip().casefold())).encode("utf-8"))
    return "f-" + h.hexdigest()[:16]


def entity_id(name):
    h = hashlib.sha256(name.strip().casefold().encode("utf-8"))
    return "e-" + h.hexdigest()[:12]


# --------------------------------------------------------------------------
# validation — the gate that makes silent writing survivable
# --------------------------------------------------------------------------

def validate_check(check):
    """A verify block must be one of the declarative whitelist types. Anything
    else — notably a shell command — is refused."""
    if not isinstance(check, dict):
        raise ValueError("check must be an object, got %r" % (check,))
    t = check.get("type")
    if t not in CHECK_TYPES:
        raise ValueError("check type %r not allowed (allowed: %s) — a stored check is "
                         "interpreted, never executed as a shell command"
                         % (t, "/".join(CHECK_TYPES)))
    if t in ("file_exists", "file_count", "path_contains") and not check.get("path"):
        raise ValueError("check %r needs a path" % t)
    if t == "file_count" and not isinstance(check.get("expect"), int):
        raise ValueError("file_count needs an integer 'expect' — that integer is the "
                         "claim being guarded against drift")
    if t == "path_contains" and not check.get("needle"):
        raise ValueError("path_contains needs a needle")
    if t == "value_matches" and ("expect" not in check or "actual_of" not in check):
        raise ValueError("value_matches needs 'expect' and 'actual_of'")
    return check


def validate_fact(fact):
    """Schema gate. Refuses loudly — a silently-written fact that nobody
    validated is exactly the failure mode D5 exists to prevent."""
    for key in ("kind", "subject", "claim", "evidence"):
        if not fact.get(key):
            raise ValueError("fact missing required field %r: %r" % (key, fact))
    if "single_valued" in fact and not isinstance(fact["single_valued"], bool):
        raise ValueError("single_valued must be a bool, got %r" % (fact["single_valued"],))
    if fact["kind"] not in KINDS:
        raise ValueError("kind must be one of %s, got %r" % (KINDS, fact["kind"]))
    ev = fact["evidence"]
    if not isinstance(ev, dict) or ev.get("type") not in EVIDENCE_TYPES or not ev.get("value"):
        raise ValueError("EVIDENCE OR NO WRITE (D5a): evidence must be "
                         "{type: %s, value: <non-empty>}, got %r"
                         % ("/".join(EVIDENCE_TYPES), ev))
    for c in fact.get("checks") or []:
        validate_check(c)
    return fact


# --------------------------------------------------------------------------
# writing
# --------------------------------------------------------------------------

def append_entity(project_uuid, name, etype="thing", home=None):
    eid = entity_id(name)
    known = {e["id"] for e in load_entities(project_uuid, home)}
    if eid not in known:
        _append_line(_p(project_uuid, ENTITIES_FILE, home),
                     {"id": eid, "name": name, "type": etype, "at": utc_now_iso()})
    return eid


def append_edge(project_uuid, src, rel, dst, home=None):
    _append_line(_p(project_uuid, EDGES_FILE, home),
                 {"src": src, "rel": rel, "dst": dst, "at": utc_now_iso()})


def append_fact(project_uuid, fact, provenance=None, home=None):
    """Validate, de-duplicate, append. Returns (fact_id, written: bool).

    Never overwrites and never deletes (D5b). A repeat of a known claim is not
    written again; a CHANGED claim about the same subject is written as a new
    fact plus a `supersedes` edge, so the old one is superseded, never erased.
    """
    validate_fact(fact)
    fid = fact_id(fact["claim"], fact["subject"])
    existing = {f["id"]: f for f in load_facts(project_uuid, home)}
    if fid in existing:
        return fid, False

    row = {
        "id": fid,
        "at": utc_now_iso(),
        "kind": fact["kind"],
        "subject": fact["subject"],
        "claim": fact["claim"],
        "evidence": fact["evidence"],
        "checks": fact.get("checks") or [],
        "entities": fact.get("entities") or [],
        "tags": fact.get("tags") or [],
        # A SINGLE-VALUED subject can hold exactly one true claim at a time —
        # "data/ holds N files", "the branch is X". A new claim there replaces
        # the old one. Most subjects are NOT single-valued: "traps" and
        # "decisions" accumulate many independent facts, and superseding on
        # subject alone would leave only the last one standing. Measured on the
        # real corpus: 25 backfilled facts collapsed to 3 before this existed.
        # Whether a subject is single-valued is a judgement, so the CALLER
        # declares it, exactly as it declares Kind 1 vs Kind 2.
        "single_valued": bool(fact.get("single_valued", False)),
        "provenance": provenance or fact.get("provenance") or {},
    }
    _append_line(_p(project_uuid, FACTS_FILE, home), row)

    for name in row["entities"]:
        eid = append_entity(project_uuid, name, home=home)
        append_edge(project_uuid, fid, "about", eid, home=home)

    if row["single_valued"]:
        dead = superseded_ids(project_uuid, home)
        for old_id, old in existing.items():
            if (old["subject"].strip().casefold() == row["subject"].strip().casefold()
                    and old["claim"].strip().casefold() != row["claim"].strip().casefold()
                    and old_id not in dead):
                append_edge(project_uuid, fid, "supersedes", old_id, home=home)
    return fid, True


def write_learnings(project_uuid, candidates, provenance=None, home=None):
    """KB-A capture loop. Takes the session's candidate learnings and applies
    D4 + D5 to them. Returns a report the caller PRINTS — never a silent result.

      kind 'machine' -> written silently, always, no question asked
      kind 'ruling'  -> NOT written here; returned as `ask` for the session to
                        put to Zee in plain language, capped at 2 (D4). Items
                        past the cap are DROPPED, and the drop is reported —
                        the brief's rule for an unsure sorter is to lose the
                        doubtful fact rather than auto-write it.
    """
    report = {"written": [], "duplicate": [], "refused": [], "ask": [], "dropped": []}
    for cand in candidates or []:
        try:
            validate_fact(cand)
        except ValueError as exc:
            report["refused"].append({"claim": cand.get("claim", "(no claim)"),
                                      "reason": str(exc)})
            continue
        if cand["kind"] == "ruling":
            if len(report["ask"]) < KIND2_QUESTION_CAP:
                report["ask"].append(cand)
            else:
                report["dropped"].append({"claim": cand["claim"],
                                          "reason": "past the %d-question cap (D4)"
                                                    % KIND2_QUESTION_CAP})
            continue
        fid, written = append_fact(project_uuid, cand, provenance, home)
        (report["written"] if written else report["duplicate"]).append(
            {"id": fid, "claim": cand["claim"]})
    if report["written"]:
        build_index(project_uuid, home)
    return report


def confirm_ruling(project_uuid, fact, provenance=None, home=None):
    """Write a Kind 2 fact AFTER Zee answered yes. Separate entry point so a
    ruling can never be written by the silent path."""
    fact = dict(fact)
    fact["kind"] = "ruling"
    fid, written = append_fact(project_uuid, fact, provenance, home)
    if written:
        build_index(project_uuid, home)
    return fid, written


# --------------------------------------------------------------------------
# reading
# --------------------------------------------------------------------------

def load_facts(project_uuid, home=None):
    rows, _bad = _read_lines(_p(project_uuid, FACTS_FILE, home))
    return rows


def load_entities(project_uuid, home=None):
    rows, _bad = _read_lines(_p(project_uuid, ENTITIES_FILE, home))
    return rows


def load_edges(project_uuid, home=None):
    rows, _bad = _read_lines(_p(project_uuid, EDGES_FILE, home))
    return rows


def superseded_ids(project_uuid, home=None):
    """{old_fact_id: replacing_fact_id} — walked from the edge list."""
    out = {}
    for e in load_edges(project_uuid, home):
        if e.get("rel") == "supersedes":
            out[e["dst"]] = e["src"]
    return out


def live_facts(project_uuid, home=None):
    """Facts that still stand: not superseded by a newer claim, and not struck
    by Zee. Both exclusions are EDGES — every excluded row stays on disk, so
    'live' is a view, never a deletion (D5b)."""
    dead = superseded_ids(project_uuid, home)
    struck = struck_ids(project_uuid, home)
    return [f for f in load_facts(project_uuid, home)
            if f["id"] not in dead and f["id"] not in struck]


# --------------------------------------------------------------------------
# KB-C — staleness re-check
# --------------------------------------------------------------------------

def _run_check(check, root=None):
    """Interpret ONE declarative check. Returns (ok, detail). Never executes a
    shell command — see the module docstring."""
    t = check["type"]
    path = check.get("path") or ""
    if path and not os.path.isabs(path) and root:
        path = os.path.join(root, path)
    if t == "file_exists":
        ok = os.path.exists(path)
        return ok, ("exists" if ok else "MISSING: %s" % path)
    if t == "file_count":
        if not os.path.isdir(path):
            return False, "MISSING DIR: %s" % path
        n = 0
        for _dp, _dn, fns in os.walk(path):
            n += len(fns)
        exp = check["expect"]
        return n == exp, ("%d files (claim says %d)" % (n, exp))
    if t == "path_contains":
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                body = fh.read()
        except OSError as exc:
            return False, "UNREADABLE: %s (%s)" % (path, exc)
        ok = check["needle"] in body
        return ok, ("found %r" % check["needle"] if ok
                    else "NOT FOUND: %r in %s" % (check["needle"], path))
    if t == "value_matches":
        # No source to read here — this check is DECLARED but only a human or a
        # later caller can supply the actual. Reported as unverifiable, never
        # silently passed: an unchecked claim must not read as a checked one.
        return None, "not auto-checkable (actual_of=%r) — needs a person" % check.get("actual_of")
    return None, "unknown check type %r" % t


def recheck(project_uuid, root=None, home=None):
    """KB-C. Re-verify every live fact that carries a check. Returns a list of
    findings; DRIFTED entries are the ones worth showing.

    Why this ships WITH the capture loop and not after it: once writes are
    silent, this is the only thing standing between the store and a confident
    wrong answer. A stale fact is worse than a missing one — it reads as sure.
    """
    findings = []
    for f in live_facts(project_uuid, home):
        for c in f.get("checks") or []:
            try:
                ok, detail = _run_check(c, root)
            except (OSError, KeyError, ValueError) as exc:
                ok, detail = False, "check error: %s" % exc
            findings.append({
                "fact_id": f["id"], "subject": f["subject"], "claim": f["claim"],
                "status": ("ok" if ok else ("unverifiable" if ok is None else "DRIFTED")),
                "detail": detail,
            })
    return findings


# --------------------------------------------------------------------------
# KB-B support — the cheap index and the digest
# --------------------------------------------------------------------------

def build_index(project_uuid, home=None):
    """Small derived summary so a resurrect can load an INDEX, not the base
    (D8: the OKOA base alone is 156,622 characters)."""
    facts = live_facts(project_uuid, home)
    ents = load_entities(project_uuid, home)
    by_subject = {}
    for f in facts:
        by_subject.setdefault(f["subject"], 0)
        by_subject[f["subject"]] += 1
    idx = {
        "project_uuid": project_uuid,
        "built_at": utc_now_iso(),
        "live_fact_count": len(facts),
        "total_fact_count": len(load_facts(project_uuid, home)),
        "entity_count": len(ents),
        "subjects": sorted(by_subject.items(), key=lambda kv: (-kv[1], kv[0])),
        "entities": sorted(e["name"] for e in ents),
        "checked_fact_count": len([f for f in facts if f.get("checks")]),
    }
    _atomic_write(_p(project_uuid, INDEX_FILE, home),
                  json.dumps(idx, indent=2, sort_keys=True) + "\n")
    return idx


def load_index(project_uuid, home=None):
    try:
        with open(_p(project_uuid, INDEX_FILE, home), "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def get_last_seen(project_uuid, home=None):
    try:
        with open(_p(project_uuid, SEEN_FILE, home), "r", encoding="utf-8") as fh:
            return json.load(fh).get("at")
    except (OSError, ValueError):
        return None


def set_last_seen(project_uuid, at=None, home=None):
    _atomic_write(_p(project_uuid, SEEN_FILE, home),
                  json.dumps({"at": at or utc_now_iso()}, indent=2) + "\n")


def digest(project_uuid, since=None, home=None):
    """'Learned since you were last here' (D5d: review AFTER, not before).

    Returns the live facts added after `since`, newest first. Control moves
    from gatekeeper to editor — Zee reads this and can strike any line.
    """
    since = since or get_last_seen(project_uuid, home)
    facts = live_facts(project_uuid, home)
    if since:
        facts = [f for f in facts if f.get("at", "") > since]
    return sorted(facts, key=lambda f: f.get("at", ""), reverse=True)


# --------------------------------------------------------------------------
# KB-E — cross-project reach
# --------------------------------------------------------------------------

_ENTITY_PATTERNS = (
    re.compile(r"`([^`]{2,60})`"),                       # backticked spans
    re.compile(r"\b([\w.-]+\.(?:py|sh|ts|tsx|js|json|yaml|yml|md|html|css|toml))\b"),
    re.compile(r"\b((?:[A-Z][a-z0-9]+){2,})\b"),         # CamelCase tool names
    # Identifier-shaped capitals only: SLICE-RES-13, KB-A, MW-A2. A separator or
    # digit is REQUIRED. A bare all-caps word is emphasis far more often than it
    # is an acronym in this corpus — the handoffs shout NEVER, GLOBAL, BOTH,
    # SAME — and matching those linked unrelated projects on nothing at all.
    re.compile(r"\b([A-Z][A-Z0-9]*(?:[-_][A-Z0-9]+)+)\b"),
    re.compile(r"\b([a-z][a-z0-9]*(?:[-_.][a-z0-9]+)+)\b"),  # kebab/snake/dotted
)
# KNOWN LIMIT, stated rather than hidden: a bare lowercase library name with no
# separator and no capital ("openpyxl", "potrace") is indistinguishable from an
# ordinary English word without a dictionary, so it is NOT extracted. Facts
# about such tools still store fine; they just do not travel between projects
# on the name alone.
_ENTITY_STOP = {"THE", "AND", "NOT", "BUT", "FOR", "WITH", "THIS", "THAT", "NOTE",
                "TODO", "DONE", "NEXT", "WHY", "HOW", "ALL", "ANY", "NEVER",
                "ALWAYS", "MUST", "ONLY", "YAML", "JSON", "GLOBAL", "REAL",
                "UNKNOWN", "SKILL", "NAME", "ONE", "TWO", "USE", "ADD", "NEW",
                "OLD", "FIX", "BUG", "WAS", "ARE", "CAN", "DID", "DOES", "HAS",
                "NOW", "PER", "VIA", "AKA", "ETC", "SEE", "RUN"}

GENERIC_ENTITY_STORE_SHARE = 0.30
"""KB-E noise control, and the reason it is a RATIO not a word list.

The handoff corpus writes emphasis in capitals — GLOBAL, NEVER, REAL — and a
shape-based extractor cannot tell those from acronyms. A hand-maintained stop
list would need endless upkeep and would still miss the next one.

So an entity appearing in more than this share of a person's project stores is
treated as too generic to link on. A term that shows up everywhere carries no
signal about which two projects are actually related — the same reason a search
engine ignores "the". This self-tunes as projects are added, and it is measured
against stores, not facts, so one chatty project cannot make a term look common.
"""


def extract_entities(text, limit=8):
    """Mechanically pull the THINGS a claim is about — tools, files, systems.

    Deliberately shallow: entities are index keys, not claims, so a slightly
    noisy key costs a spurious cross-project suggestion, while a missing one
    costs a lesson that never resurfaces. The asymmetry favours recall.
    Nothing here is asserted as fact — the CLAIM carries the assertion.
    """
    found, seen = [], set()
    for pat in _ENTITY_PATTERNS:
        for m in pat.finditer(text or ""):
            tok = m.group(1).strip().strip(".,;:")
            if len(tok) < 3 or tok.upper() in _ENTITY_STOP:
                continue
            key = tok.casefold()
            if key in seen:
                continue
            seen.add(key)
            found.append(tok)
            if len(found) >= limit:
                return found
    return found


def entity_names(project_uuid, home=None):
    return {e["name"].casefold(): e["name"] for e in load_entities(project_uuid, home)}


def all_project_uuids(home=None):
    d = os.path.join(_home(home), ".acos", "knowledge")
    try:
        return sorted(n for n in os.listdir(d)
                      if os.path.isdir(os.path.join(d, n)))
    except OSError:
        return []


def cross_project_hits(project_uuid, home=None, limit=8, subjects=("traps",)):
    """KB-E — lessons another project learned that touch something THIS project
    also works with.

    Match rule, deliberately conservative: a fact from another project counts
    only if one of THIS project's known entities appears in it, either as a
    declared entity or as a whole word in the claim. A loose rule here is worse
    than no rule — a wall of vaguely-related facts from 17 projects would be
    ignored, and an ignored surface is the same as a missing one.

    `subjects` limits which kinds of fact travel. Traps travel by default
    because a trap is the thing most worth not hitting twice; decisions are
    usually project-local and are not offered unless asked for.
    """
    mine = entity_names(project_uuid, home)
    if not mine:
        return []
    stores = all_project_uuids(home)
    # Drop entities that show up nearly everywhere — see
    # GENERIC_ENTITY_STORE_SHARE. Measured on the real corpus: without this,
    # every hit linked on emphasis words (GLOBAL, NEVER, UNKNOWN) rather than
    # on any shared tool, which is worse than showing nothing.
    if len(stores) > 2:
        seen_in = {}
        for u in stores:
            for name in {e["name"].casefold() for e in load_entities(u, home)}:
                seen_in[name] = seen_in.get(name, 0) + 1
        ceiling = max(2, int(len(stores) * GENERIC_ENTITY_STORE_SHARE))
        mine = {k: v for k, v in mine.items() if seen_in.get(k, 0) <= ceiling}
        if not mine:
            return []
    hits = []
    for other in stores:
        if other == project_uuid:
            continue
        for f in live_facts(other, home):
            if subjects and f.get("subject") not in subjects:
                continue
            declared = {e.casefold() for e in (f.get("entities") or [])}
            shared = sorted(set(mine) & declared)
            if not shared:
                claim = (f.get("claim") or "").casefold()
                shared = sorted(k for k in mine
                                if re.search(r"(?<!\w)%s(?!\w)" % re.escape(k), claim))
            if shared:
                hits.append({"project_uuid": other, "fact_id": f["id"],
                             "subject": f["subject"], "claim": f["claim"],
                             "shared": [mine[s] for s in shared[:3]],
                             "evidence": f.get("evidence", {})})
            if len(hits) >= limit:
                return hits
    return hits


def strike_fact(project_uuid, fact_id_, reason="struck by the user", home=None):
    """D5d: 'can strike any line with one word'. A strike is an EDGE, not a
    delete — the row stays on disk and the strike is auditable."""
    append_edge(project_uuid, "user-strike", "struck", fact_id_, home=home)
    _append_line(_p(project_uuid, EDGES_FILE, home),
                 {"src": "user-strike", "rel": "strike-reason", "dst": fact_id_,
                  "note": reason, "at": utc_now_iso()})
    build_index(project_uuid, home)
    return True


def struck_ids(project_uuid, home=None):
    return {e["dst"] for e in load_edges(project_uuid, home) if e.get("rel") == "struck"}


# --------------------------------------------------------------------------
# self-test
# --------------------------------------------------------------------------

def _selftest(home):
    if not home:
        print("REFUSED: selftest must run under a --home override, never the real ~")
        return 1
    u = "11111111-2222-4333-8444-555555555555"
    failures = []

    def ck(label, cond, detail=""):
        if cond:
            print("  PASS  %s" % label)
        else:
            print("  FAIL  %s %s" % (label, detail))
            failures.append(label)

    print("evidence gate")
    r = write_learnings(u, [{"kind": "machine", "subject": "s", "claim": "c"}], home=home)
    ck("a fact with no evidence is refused", len(r["refused"]) == 1 and not r["written"])
    r = write_learnings(u, [{"kind": "machine", "subject": "s", "claim": "c",
                             "evidence": {"type": "path", "value": "/tmp/x"}}], home=home)
    ck("a fact with evidence is written", len(r["written"]) == 1, r)

    print("no shell in checks")
    try:
        validate_check({"type": "shell", "cmd": "rm -rf /"})
        ck("shell check refused", False, "it was accepted")
    except ValueError:
        ck("shell check refused", True)

    print("append-only + supersede")
    # A NON-single-valued subject accumulates: "traps" holds many facts at once.
    write_learnings(u, [{"kind": "machine", "subject": "s", "claim": "c2",
                         "evidence": {"type": "path", "value": "/tmp/x"}}], home=home)
    ck("both rows still on disk", len(load_facts(u, home)) == 2)
    ck("a multi-valued subject accumulates, it does not overwrite",
       len(live_facts(u, home)) == 2, len(live_facts(u, home)))
    # A SINGLE-VALUED subject holds one true claim: the new one replaces it.
    write_learnings(u, [{"kind": "machine", "subject": "count", "claim": "holds 5",
                         "evidence": {"type": "path", "value": "/tmp/x"},
                         "single_valued": True}], home=home)
    write_learnings(u, [{"kind": "machine", "subject": "count", "claim": "holds 9",
                         "evidence": {"type": "path", "value": "/tmp/x"},
                         "single_valued": True}], home=home)
    counts = [f for f in live_facts(u, home) if f["subject"] == "count"]
    ck("single-valued keeps only the newest claim", len(counts) == 1, counts)
    ck("and it is the newer one", counts and counts[0]["claim"] == "holds 9", counts)
    ck("the superseded row is still on disk",
       len([f for f in load_facts(u, home) if f["subject"] == "count"]) == 2)

    print("kind 2 cap")
    rulings = [{"kind": "ruling", "subject": "s%d" % i, "claim": "r%d" % i,
                "evidence": {"type": "quote", "value": "Zee said so"}} for i in range(5)]
    r = write_learnings(u, rulings, home=home)
    ck("at most 2 asked", len(r["ask"]) == KIND2_QUESTION_CAP, len(r["ask"]))
    ck("overflow dropped, not written", len(r["dropped"]) == 3)
    ck("no ruling auto-written", not any(f["kind"] == "ruling" for f in load_facts(u, home)))

    print("staleness re-check")
    d = os.path.join(home, "countme")
    os.makedirs(d, exist_ok=True)
    for i in range(3):
        with open(os.path.join(d, "f%d.txt" % i), "w") as fh:
            fh.write("x")
    write_learnings(u, [{"kind": "machine", "subject": "countme", "claim": "holds 99 files",
                         "evidence": {"type": "command", "value": "ls | wc -l"},
                         "checks": [{"type": "file_count", "path": d, "expect": 99}]}],
                    home=home)
    drift = [f for f in recheck(u, home=home) if f["status"] == "DRIFTED"]
    ck("wrong count is caught as drift", len(drift) == 1, drift)
    ck("drift names both numbers", "3 files (claim says 99)" in drift[0]["detail"], drift)

    print("digest + strike")
    idx = build_index(u, home)
    ck("index counts live facts", idx["live_fact_count"] == len(live_facts(u, home)))
    dg = digest(u, since="1970-01-01T00:00:00+00:00", home=home)
    ck("digest returns the new facts", len(dg) >= 1)
    target = dg[0]["id"]
    strike_fact(u, target, home=home)
    ck("strike is recorded", target in struck_ids(u, home))
    ck("struck fact is NOT deleted", any(f["id"] == target for f in load_facts(u, home)))

    print()
    if failures:
        print("FAILED: %d — %s" % (len(failures), "; ".join(failures)))
        return 1
    print("knowledge_lib selftest: ALL PASSED")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="per-project knowledge store")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--home", default=None)
    ap.add_argument("--project", default=None)
    ap.add_argument("--index", action="store_true", help="print the index")
    ap.add_argument("--recheck", action="store_true", help="run staleness checks")
    ap.add_argument("--root", default=None, help="project root for relative check paths")
    args = ap.parse_args(argv)
    if args.selftest:
        return _selftest(args.home)
    if args.project and args.index:
        print(json.dumps(build_index(args.project, args.home), indent=2))
        return 0
    if args.project and args.recheck:
        print(json.dumps(recheck(args.project, args.root, args.home), indent=2))
        return 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
