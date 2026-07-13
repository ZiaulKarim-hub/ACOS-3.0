#!/usr/bin/env python3
"""
axiom_ledger.py — the single source of truth for the acos-axiom-synthesis claim ledger.

This module is the ONLY writer of claim state (PLAN.md §15.1). Every CLI wrapper
(ledger_writer / verify_ledger / next_claims / render) calls into here; nothing
else appends to claims.jsonl. It enforces, mechanically:

  1. Legal state transitions (PLAN.md §15.2 / STATE-MACHINE.md) — refuse any move
     not in LEGAL_TRANSITIONS.
  2. The corroboration gate — 'verified' / ESTABLISHED needs >=2 independent,
     distinct-family sources.
  3. The single-source cap — a single-source claim can never be 'verified'.
  4. The falsification gate — a claim cannot be promoted above CONJECTURE until it
     has passed the Stage-5 gate (gates.falsification == "passed").
  5. Dependency integrity — a claim cannot be ESTABLISHED while a depends_on claim
     is REFUTED.

An illegal write raises LedgerError; the CLI turns that into a NON-ZERO EXIT, so a
violation halts the run instead of silently entering the ledger.

The ledger is an append-only JSONL file. Each line is one *version* of a claim.
The current state of a claim id = the last line bearing that id. Superseded/refuted
versions stay on disk (never deleted) so history is auditable and revivable.

Stdlib only. Python 3.8+.
"""

import hashlib
import json

# --- constants ---------------------------------------------------------------

# Domain separation prefix for hashing (prevents cross-protocol hash reuse).
DOMAIN_PREFIX = "acos-axiom-synthesis/claim/v1\n"
GENESIS = "sha256-" + ("0" * 64)  # prev_hash of the very first ledger entry

STATES = {
    "CONJECTURE", "CORROBORATED", "ESTABLISHED",
    "CONTESTED", "SUPERSEDED", "REFUTED",
}
CONFIDENCE = {"verified", "probable", "unverified"}

# Legal state transitions. Key None = "create" (claim not yet in ledger).
# Same-state -> same-state is always legal (a metadata/provenance update).
# This dict MUST stay identical to STATE-MACHINE.md — that file is the authority
# when prose and code disagree; this is its executable form.
LEGAL_TRANSITIONS = {
    None:          {"CONJECTURE"},
    "CONJECTURE":  {"CONJECTURE", "CORROBORATED", "CONTESTED", "SUPERSEDED", "REFUTED"},
    "CORROBORATED": {"CORROBORATED", "ESTABLISHED", "CONTESTED", "SUPERSEDED", "REFUTED"},
    "ESTABLISHED": {"ESTABLISHED", "CONTESTED", "SUPERSEDED", "REFUTED"},
    "CONTESTED":   {"CONTESTED", "CORROBORATED", "ESTABLISHED", "SUPERSEDED", "REFUTED"},
    "SUPERSEDED":  {"SUPERSEDED", "CONTESTED", "CORROBORATED"},  # revival
    "REFUTED":     {"REFUTED", "CONTESTED", "CORROBORATED"},     # revival
}

# Exit / error codes (mirrors acos-synthesis-protocol's set-status.py convention).
CODE_SCHEMA = 2       # malformed record
CODE_INVARIANT = 3    # a hard invariant was violated (corroboration/cap/falsify/deps)
CODE_TRANSITION = 4   # an illegal state transition was attempted


class LedgerError(Exception):
    """Raised by append_claim when a write is refused. `.code` is the exit code."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


# --- canonicalization + hashing ---------------------------------------------

def canonicalize(record):
    """Deterministic JSON for hashing.

    sort_keys + compact separators gives RFC-8785-equivalent determinism for the
    record shapes we use (strings, ints, ordered lists, nested dicts). We avoid
    floats entirely (confidence is an ordinal string; counts are ints), which is
    the only place plain json.dumps would be non-deterministic.
    """
    return json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def record_hash(record_without_entry_hash):
    """SHA-256 over the domain-prefixed canonical record (excluding entry_hash).

    prev_hash IS included, so each entry cryptographically commits to the one
    before it — tampering any field, or reordering lines, breaks the chain.
    """
    canon = canonicalize(record_without_entry_hash)
    digest = hashlib.sha256((DOMAIN_PREFIX + canon).encode("utf-8")).hexdigest()
    return "sha256-" + digest


# --- ledger IO ---------------------------------------------------------------

def read_ledger(path):
    """Return every ledger line (all claim versions) in file order. [] if absent."""
    records = []
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise LedgerError(CODE_SCHEMA, f"ledger line {lineno} is not valid JSON: {exc}")
    except FileNotFoundError:
        return []
    return records


def current_states(records):
    """Map claim id -> its latest version (last line wins)."""
    latest = {}
    for rec in records:
        latest[rec["id"]] = rec
    return latest


# --- validation --------------------------------------------------------------

def validate_schema(record):
    for field in ("id", "statement", "state", "confidence"):
        if field not in record or record[field] in (None, ""):
            return False, f"missing required field '{field}'"
    if record["state"] not in STATES:
        return False, f"unknown state '{record['state']}' (allowed: {sorted(STATES)})"
    if record["confidence"] not in CONFIDENCE:
        return False, f"unknown confidence '{record['confidence']}' (allowed: {sorted(CONFIDENCE)})"
    if "provenance" in record and not isinstance(record["provenance"], list):
        return False, "'provenance' must be a list"
    if "depends_on" in record and not isinstance(record["depends_on"], list):
        return False, "'depends_on' must be a list"
    return True, None


def validate_transition(from_state, to_state):
    allowed = LEGAL_TRANSITIONS.get(from_state)
    if allowed is None:
        return False, f"unknown from-state '{from_state}'"
    if to_state not in allowed:
        label = from_state or "CREATE"
        return False, f"illegal transition {label} -> {to_state} (legal: {sorted(allowed)})"
    return True, None


def _distinct_families(record):
    return {p.get("family") for p in (record.get("provenance") or []) if p.get("family")}


def validate_invariants(record, current_by_id):
    """The hard invariants (PLAN.md §15.1). Returns (ok, reason)."""
    state = record["state"]
    conf = record.get("confidence")
    basis = record.get("confidence_basis") or {}
    indep = basis.get("independent_sources")
    families = _distinct_families(record)
    gates = record.get("gates") or {}

    # (1)+(2) Corroboration gate + single-source cap.
    if conf == "verified" or state == "ESTABLISHED":
        if not isinstance(indep, int) or indep < 2:
            return False, ("corroboration gate: 'verified'/ESTABLISHED requires "
                           ">=2 independent sources (confidence_basis.independent_sources)")
        if len(families) < 2:
            return False, ("corroboration gate: 'verified'/ESTABLISHED requires "
                           ">=2 distinct source families in provenance")

    # (3) Falsification gate — no promotion above CONJECTURE without passing it.
    if state in ("CORROBORATED", "ESTABLISHED"):
        if gates.get("falsification") != "passed":
            return False, (f"falsification gate: promoting to {state} requires "
                           "gates.falsification == 'passed'")

    # (4) Dependency integrity.
    if state == "ESTABLISHED":
        for dep in (record.get("depends_on") or []):
            dep_rec = current_by_id.get(dep)
            if dep_rec and dep_rec.get("state") == "REFUTED":
                return False, (f"dependency integrity: cannot ESTABLISH while "
                               f"dependency '{dep}' is REFUTED")

    return True, None


# --- the single writer -------------------------------------------------------

def append_claim(path, record, now=None):
    """THE only function that appends a claim version. Validates, chains, writes.

    Raises LedgerError (with .code) on any refusal; the caller must NOT catch-and-
    ignore — a refusal is a hard stop by design.
    Returns the finalized record (with prev_hash + entry_hash) on success.
    """
    records = read_ledger(path)
    current = current_states(records)

    ok, reason = validate_schema(record)
    if not ok:
        raise LedgerError(CODE_SCHEMA, reason)

    cid = record["id"]
    from_state = current[cid]["state"] if cid in current else None

    ok, reason = validate_transition(from_state, record["state"])
    if not ok:
        raise LedgerError(CODE_TRANSITION, reason)

    ok, reason = validate_invariants(record, current)
    if not ok:
        raise LedgerError(CODE_INVARIANT, reason)

    rec = dict(record)
    # Timestamps: preserve first_synthesized across updates; stamp last_reviewed.
    if from_state is None:
        rec["first_synthesized"] = record.get("first_synthesized", now)
    else:
        rec["first_synthesized"] = current[cid].get(
            "first_synthesized", record.get("first_synthesized", now))
    if now is not None:
        rec["last_reviewed"] = now

    rec["prev_hash"] = records[-1]["entry_hash"] if records else GENESIS
    rec.pop("entry_hash", None)
    rec["entry_hash"] = record_hash(rec)

    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


# --- verifier ----------------------------------------------------------------

def verify_chain(path):
    """Recompute every entry_hash and check the prev_hash chain.

    Returns (ok, problems). A mutated field changes that line's entry_hash; a
    reordered/removed line breaks the prev_hash link. Both are localized to the
    offending line number.
    """
    records = read_ledger(path)
    problems = []
    prev = GENESIS
    for i, rec in enumerate(records, 1):
        stored = rec.get("entry_hash")
        body = {k: v for k, v in rec.items() if k != "entry_hash"}
        recomputed = record_hash(body)
        if recomputed != stored:
            problems.append(f"line {i} (id {rec.get('id')}): entry_hash mismatch — content altered")
        if rec.get("prev_hash") != prev:
            problems.append(f"line {i} (id {rec.get('id')}): prev_hash broken — chain/order tampered")
        prev = stored
    return (len(problems) == 0, problems)


def ledger_head(path):
    """The compact commitment: the last entry_hash (or GENESIS for an empty ledger)."""
    records = read_ledger(path)
    return records[-1]["entry_hash"] if records else GENESIS


# --- frontier (pure function of on-disk state; PLAN.md §15.3) ----------------

def compute_frontier(records):
    """What work remains, computed purely from the ledger. No in-memory to-do list.

    Re-running this after any interruption reproduces the exact frontier — that is
    what makes the run resumable. Extended in later build phases; the substrate
    version buckets by state.
    """
    cur = current_states(records)
    frontier = {
        "needs_falsification": [],
        "needs_corroboration": [],
        "needs_conflict_resolution": [],
        "settled": [],
        "terminal": [],
    }
    for cid, rec in cur.items():
        state = rec["state"]
        gates = rec.get("gates") or {}
        basis = rec.get("confidence_basis") or {}
        if state == "CONTESTED":
            frontier["needs_conflict_resolution"].append(cid)
        elif state == "CONJECTURE":
            if gates.get("falsification") != "passed":
                frontier["needs_falsification"].append(cid)
            else:
                frontier["needs_corroboration"].append(cid)
        elif state == "CORROBORATED":
            # A corroborated claim with enough independent support is a promotion
            # candidate; otherwise it is settled at 'probable'.
            if isinstance(basis.get("independent_sources"), int) and basis["independent_sources"] >= 2:
                frontier["needs_corroboration"].append(cid)
            else:
                frontier["settled"].append(cid)
        elif state in ("SUPERSEDED", "REFUTED"):
            frontier["terminal"].append(cid)
        else:  # ESTABLISHED
            frontier["settled"].append(cid)
    frontier["done"] = not (
        frontier["needs_falsification"]
        or frontier["needs_corroboration"]
        or frontier["needs_conflict_resolution"]
    )
    return frontier


# --- renderer ----------------------------------------------------------------

_TIER_LABEL = {"verified": "Verified", "probable": "Probable", "unverified": "Unverified"}


def render_markdown(records, path_for_head=None, question=None):
    """Render source-of-truth.md from the ledger (always generated, never hand-edited)."""
    cur = current_states(records)
    claims = list(cur.values())
    head = records[-1]["entry_hash"] if records else GENESIS

    working = [c for c in claims if c["state"] in ("ESTABLISHED", "CORROBORATED")]
    contested = [c for c in claims if c["state"] == "CONTESTED"]
    superseded = [c for c in claims if c["state"] in ("SUPERSEDED", "REFUTED")]
    open_qs = [c for c in claims if c["state"] == "CONJECTURE" or c.get("confidence") == "unverified"]

    lines = []
    lines.append("---")
    lines.append(f"synthesis_question: {json.dumps(question or 'UNSET', ensure_ascii=False)}")
    lines.append("artifact: source-of-truth")
    lines.append("schema_version: 1")
    lines.append(f"ledger_head: {head}")
    lines.append("confidence_tiers:")
    lines.append("  verified: \">=2 distinct-family agents AND >=2 independent sources\"")
    lines.append("  probable: \"single-source OR single-family agreement OR minor unresolved tension\"")
    lines.append("  unverified: \"one agent, weak/absent provenance, or contested — a lead, not a fact\"")
    lines.append("---")
    lines.append("")
    lines.append("# Source of Truth")
    lines.append("")
    lines.append(f"_Snapshot of the current best-supported claim set. Defeasible — nothing here is final._")
    lines.append("")

    lines.append("## Working truth")
    if not working:
        lines.append("_No established or corroborated claims yet._")
    for c in sorted(working, key=lambda x: x["id"]):
        tier = _TIER_LABEL.get(c.get("confidence"), c.get("confidence"))
        lines.append(f"- **[{c['state']} · {tier}]** {c['statement']}  `({c['id']})`")
        for p in (c.get("provenance") or []):
            loc = p.get("locator", "")
            src = p.get("source", "?")
            fam = p.get("family", "")
            lines.append(f"    - source: {src} {('('+loc+')') if loc else ''} {('['+fam+']') if fam else ''}")
    lines.append("")

    lines.append("## UNRESOLVED CONFLICTS")
    if not contested:
        lines.append("_None._")
    for c in sorted(contested, key=lambda x: x["id"]):
        lines.append(f"- **{c['statement']}**  `({c['id']})`")
        for alt in (c.get("alternatives") or []):
            lines.append(f"    - alternative: {alt.get('statement','?')} — {alt.get('why_not_adopted','')}")
    lines.append("")

    lines.append("## OPEN QUESTIONS")
    if not open_qs:
        lines.append("_None._")
    for c in sorted(open_qs, key=lambda x: x["id"]):
        lines.append(f"- {c['statement']}  `({c['id']}, {c['state']})`")
    lines.append("")

    lines.append("## SUPERSESSION LOG")
    if not superseded:
        lines.append("_None._")
    for c in sorted(superseded, key=lambda x: x["id"]):
        by = c.get("superseded_by") or "(refuted)"
        lines.append(f"- ~~{c['statement']}~~ → {by}  `({c['id']}, {c['state']})`")
    lines.append("")
    return "\n".join(lines)
