#!/usr/bin/env python3
"""hca-consensus.py — the ADVERSARIAL MULTI-MODEL CONSENSUS engine (SLICE-HCA-06, Demo 2).

WRAPS the deterministic spine (hca-deliver.py, slice-07) with blind N-agent consensus for
report / aggregation / high-stakes questions. The single trust idea: never trust ONE
extraction. Dispatch N INDEPENDENT, BLIND agents at the same scoped question, accept an
answer ONLY when >= quorum of them agree on the SUBSTANCE (the normalized number / name /
date — NOT the prose), and on disagreement RE-DISPATCH a fresh blind cohort (bounded), then
ESCALATE as a structured REFUSAL. There is NO silent pick: the engine never returns an
agreed value without quorum.

    NL question (report/aggregation/high-stakes)
      -> [dispatch]    N=agent_count BLIND general-purpose agents (Task(), subscription-only).
                       Each gets ONLY its scoped Tier-1 slice + the question — no shared
                       context, no sight of another agent's output. (The SKILL.md orchestrates
                       the real Task() spawn; THIS engine takes the N returned envelopes via
                       an injected `agent_runner` callable so it is fully testable.)
      -> [consensus]   normalize each agent's value to a SUBSTANCE KEY; group; count the
                       largest agreeing group. >= quorum (config default 2-of-3, asymmetric)
                       => an agreed value. < quorum => disagreement.
      -> [re-dispatch] disagreement => bounded BLIND re-dispatch (config redispatch_retries,
                       default 1). The re-dispatch carries NO feedback to the agents — they
                       never learn THAT or WHY a prior round split (blind independence). Still
                       split after the retries => ESCALATE.
      -> [bind+gates]  an agreed value is STILL run through the NON-BYPASSABLE provenance
                       binder (slice-04) + deterministic gate suite (slice-05) — consensus is
                       ADDITIVE, never a substitute. A bind/gate failure => REFUSE (pass-
                       through PROVENANCE_REFUSED / GATE_FAIL).
      -> [confidence]  confidence_record(source_count=agreeing_count): >= 2 agreeing sources
                       lift the figure above the single-source 0.7 cap; a lone source is
                       capped + flagged.
      -> [envelope]    a ConsensusEnvelope (DELIVERED | REFUSED).

THE HARD GUARANTEES (proven by tests; slice acceptance = REJECT on fail):
  - NO SILENT PICK. On unresolved disagreement the engine ESCALATES with value == None and
    agreeing_count < quorum. It never picks a plurality / first / most-confident answer.
  - BLIND RE-DISPATCH. The re-dispatch invocation of `agent_runner` receives NO feedback
    about the prior round (no values_seen, no "you disagreed", no other agent's answer). The
    `agent_runner` signature does not even have a channel for it.
  - ADDITIVE VERIFICATION. The agreed value still passes bind_and_verify/bind_aggregate AND
    the gate suite before it is ever DELIVERED.
  - SUBSTANCE, NOT PROSE. Agents that phrase the same number/name/date differently still
    agree; agents with different substance do not.

ESCALATION IS A STRUCTURED REFUSAL (state == REFUSED, reason_code == NO_CONSENSUS), plus the
pass-through refusal codes GATE_FAIL / PROVENANCE_REFUSED for an agreed value that then fails
verification.

GROUND RULES (memory/decisions/2026-06-18-hca-build-ground-rules.md):
  - Python 3 stdlib ONLY. No third-party deps.
  - Subscription-only Claude: this script makes NO model call and reads NO API key. The real
    blind agents are spawned by the orchestrating SKILL.md via Task() (subscription-only);
    THIS engine only ADJUDICATES the structured returns. `agent_runner` is injected.
  - Read-only: composes slice-04/05 modules; never writes Tier-1 outside the cache facade.
  - No real PII is printed by the CLI/envelope summary — values/field NAMES only.

Slices 01-05 + hca-deliver are COMPOSE-ONLY here (imported, never edited).
"""

from __future__ import annotations

import argparse
import datetime
import importlib.util
import json
import os
import re
import sys
from typing import Any, Callable, Optional


# ---------------------------------------------------------------------------
# Terminal states + refusal reason codes
# ---------------------------------------------------------------------------

STATE_DELIVERED = "DELIVERED"
STATE_REFUSED = "REFUSED"

# Consensus-specific refusal reason (escalation after bounded re-dispatch).
REASON_NO_CONSENSUS = "NO_CONSENSUS"          # < quorum agreement after re-dispatch => ESCALATE
# Pass-through reasons from the binder / gate suite (an agreed value that fails verification).
REASON_GATE_FAIL = "GATE_FAIL"               # the deterministic gate suite returned `refuse`
REASON_PROVENANCE = "PROVENANCE_REFUSED"     # the agreed value could not be bound+verified
REASON_NO_AGENTS = "NO_AGENT_RESULTS"        # the runner returned zero usable agent results


# ---------------------------------------------------------------------------
# Sibling module loading (hyphenated filenames -> import by file path, cached)
# ---------------------------------------------------------------------------

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))


def _load(modname: str, filename: str):
    cached = sys.modules.get(modname)
    if cached is not None:
        return cached
    path = os.path.join(_THIS_DIR, filename)
    spec = importlib.util.spec_from_file_location(modname, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[modname] = mod
    spec.loader.exec_module(mod)
    return mod


def _provenance():
    return _load("hca_provenance", "hca-provenance.py")


def _gates():
    return _load("hca_gates", "hca-gates.py")


# ---------------------------------------------------------------------------
# Config — read consensus.* from config.yaml (stdlib; no YAML lib, mirrors
# hca-provenance._read_single_source_cap).
# ---------------------------------------------------------------------------

def _config_path() -> str:
    cfg = os.path.join(_THIS_DIR, os.pardir, os.pardir,
                       ".claude", "skills", "acos-hypercore-ask", "config.yaml")
    return os.path.abspath(cfg)


def _read_consensus_config() -> dict:
    """Scan config.yaml `consensus:` block for default_quorum/agent_count/redispatch_retries.

    Returns a dict with conservative built-in defaults if the file or any key is absent
    (2-of-3 quorum, 3 agents, 1 re-dispatch). Stdlib-only line scanner — no YAML dependency.
    """
    defaults = {"default_quorum": "2-of-3", "agent_count": 3, "redispatch_retries": 1}
    path = _config_path()
    if not os.path.isfile(path):
        return defaults
    in_block = False
    out = dict(defaults)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                if not line[:1].isspace():
                    in_block = stripped.startswith("consensus:")
                    continue
                if not in_block:
                    continue
                if ":" not in stripped:
                    continue
                key, _, rest = stripped.partition(":")
                key = key.strip()
                val = rest.split("#", 1)[0].strip().strip('"').strip("'")
                if key == "default_quorum":
                    out["default_quorum"] = val
                elif key == "agent_count":
                    try:
                        out["agent_count"] = int(val)
                    except ValueError:
                        pass
                elif key == "redispatch_retries":
                    try:
                        out["redispatch_retries"] = int(val)
                    except ValueError:
                        pass
    except OSError:
        return defaults
    return out


def parse_quorum(quorum: Any, n: int) -> int:
    """Resolve a quorum spec to an integer threshold of agreeing agents.

    Accepts:
      - "K-of-M"  (e.g. "2-of-3"): K is the threshold. (M is the *intended* cohort size; the
        ACTUAL n used for evaluation is the runtime `n`, so a "2-of-3" quorum needs 2 agreeing
        agents regardless of how many actually returned.)
      - a bare int / numeric string K: K agreeing agents.
      - None: caller supplies the config default before calling.
    The threshold is clamped to [1, n]: it can never demand more than the cohort, and never
    fewer than one (a single agent can never be a "consensus" by itself — see single-source
    cap interplay).
    """
    if quorum is None:
        raise ValueError("quorum must not be None at parse time")
    threshold = None
    if isinstance(quorum, int) and not isinstance(quorum, bool):
        threshold = quorum
    else:
        s = str(quorum).strip().lower()
        m = re.match(r"^\s*(\d+)\s*-?of-?\s*(\d+)\s*$", s)
        if m:
            threshold = int(m.group(1))
        else:
            try:
                threshold = int(s)
            except ValueError:
                raise ValueError(f"unparseable quorum spec {quorum!r} "
                                 f"(want 'K-of-M' or an int)")
    if threshold < 1:
        threshold = 1
    if threshold > n:
        threshold = n
    return threshold


# ---------------------------------------------------------------------------
# Substance normalization — group agent answers by their MEANING, not prose.
# ---------------------------------------------------------------------------

# Numbers agree when relative difference <= REL_EPS OR absolute difference <= ABS_FLOOR.
# The absolute floor lets near-zero values agree (where relative error explodes) and tiny
# float jitter from independent extractions not split the cohort.
REL_EPS = 1e-9
ABS_FLOOR = 1e-9

_WS_RE = re.compile(r"\s+")
# A number embedded in prose: optional sign, digits with optional thousands separators + dot.
_NUM_IN_TEXT_RE = re.compile(r"-?\$?\s*\d[\d,]*(?:\.\d+)?")


def _extract_value(agent_result: Any) -> Any:
    """Pull the SUBSTANCE value out of one agent's structured return.

    Accepts either:
      - an hca-deliver-style envelope: prefer values[0].value, else `value`, else `answer`;
      - a {value, ...} dict (the blind-extractor return schema: {value, json_field_path,
        raw_response_id, agent_confidence});
      - a bare scalar/str.
    Returns the raw value (further normalized into a substance KEY by _substance_key).
    """
    if isinstance(agent_result, dict):
        # hca-deliver envelope shape
        vals = agent_result.get("values")
        if isinstance(vals, list) and vals and isinstance(vals[0], dict) and "value" in vals[0]:
            return vals[0]["value"]
        if "value" in agent_result:
            return agent_result["value"]
        if "answer" in agent_result:
            return agent_result["answer"]
        return None
    return agent_result


def _as_number(value: Any) -> Optional[float]:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        m = _NUM_IN_TEXT_RE.search(value)
        if m:
            token = m.group(0).replace("$", "").replace(",", "").replace(" ", "")
            try:
                return float(token)
            except ValueError:
                return None
    return None


def _numbers_agree(a: float, b: float) -> bool:
    if a == b:
        return True
    diff = abs(a - b)
    if diff <= ABS_FLOOR:
        return True
    scale = max(abs(a), abs(b))
    if scale == 0:
        return diff <= ABS_FLOOR
    return (diff / scale) <= REL_EPS


def _normalize_text(value: str) -> str:
    """Case-fold + collapse whitespace + strip surrounding punctuation for text equality."""
    s = _WS_RE.sub(" ", str(value).strip().lower())
    return s.strip(" .,:;!?\"'")


def _normalize_list(value: list) -> frozenset:
    """A list/collection agrees by SET membership of its normalized elements (order-free)."""
    out = set()
    for el in value:
        if isinstance(el, (int, float)) and not isinstance(el, bool):
            out.add(("num", round(float(el), 9)))
        else:
            out.add(("txt", _normalize_text(el)))
    return frozenset(out)


def _substance_key(value: Any) -> tuple:
    """Map a value to a hashable SUBSTANCE KEY used for grouping equal-substance answers.

    - numbers (incl. numbers embedded in prose like "$5,000,000") -> a ("num", rounded) key
      with tolerant matching handled by _keys_agree (NOT by this key alone);
    - lists/sets -> a ("list", frozenset) key (order-free membership);
    - everything else -> a ("txt", normalized) key.
    None / unextractable -> a sentinel ("none",) key that NEVER agrees with a real value.
    """
    if value is None:
        return ("none",)
    if isinstance(value, (list, tuple, set)):
        return ("list", _normalize_list(list(value)))
    num = _as_number(value)
    if num is not None:
        # Coarse bucket so identical numbers hash together; fine tolerance is in _keys_agree.
        return ("num", round(num, 9), num)
    return ("txt", _normalize_text(value))


def _keys_agree(k1: tuple, k2: tuple) -> bool:
    """Two substance keys agree iff same kind AND substance-equal under the kind's rule.

    Numbers use tolerant numeric agreement; lists use exact set equality; text uses
    normalized equality. A ('none',) key never agrees with anything (including another none).
    """
    if k1[0] == "none" or k2[0] == "none":
        return False
    if k1[0] != k2[0]:
        return False
    if k1[0] == "num":
        return _numbers_agree(k1[2], k2[2])
    if k1[0] == "list":
        return k1[1] == k2[1]
    return k1[1] == k2[1]


def group_by_substance(values: list) -> list:
    """Cluster values into substance groups. Returns a list of groups, each a dict:
        {key, count, indices:[...], representative}
    sorted by descending count then by first-seen order. A ('none',) value never joins a
    group with a real value (it forms its own non-agreeing singleton, so it can never reach
    quorum)."""
    groups = []  # each: {"key": substance_key, "indices": [...], "rep": value}
    for i, v in enumerate(values):
        key = _substance_key(v)
        placed = False
        if key[0] != "none":
            for g in groups:
                if _keys_agree(g["key"], key):
                    g["indices"].append(i)
                    placed = True
                    break
        if not placed:
            groups.append({"key": key, "indices": [i], "rep": v})
    out = []
    for order, g in enumerate(groups):
        out.append({
            "key": g["key"],
            "count": len(g["indices"]),
            "indices": list(g["indices"]),
            "representative": g["rep"],
            "_order": order,
        })
    out.sort(key=lambda g: (-g["count"], g["_order"]))
    for g in out:
        g.pop("_order", None)
    return out


# ---------------------------------------------------------------------------
# Envelope builders
# ---------------------------------------------------------------------------

def _disagreement_summary(values: list, groups: list) -> dict:
    """A PII-light disagreement record for the envelope: distinct substance reps + spread."""
    values_seen = [g["representative"] for g in groups]
    nums = [n for n in (_as_number(v) for v in values) if n is not None]
    spread = (max(nums) - min(nums)) if len(nums) >= 2 else None
    return {"values_seen": values_seen, "spread": spread,
            "distinct_groups": len(groups)}


def _envelope(state: str, *, answer, value, agreeing_count: int, quorum: int, n: int,
              provenance, gate_verdict, confidence, redispatches: int,
              disagreement: dict, refusals: list, meta: Optional[dict] = None) -> dict:
    return {
        "state": state,
        "answer": answer,
        "value": value,
        "agreeing_count": agreeing_count,
        "quorum": quorum,
        "n": n,
        "provenance": provenance,
        "gate_verdict": gate_verdict,
        "confidence": confidence,
        "redispatches": redispatches,
        "disagreement": disagreement,
        "refusals": refusals,
        "meta": meta or {},
    }


def _refused(reason_code: str, reason: str, *, quorum: int, n: int, agreeing_count: int,
             redispatches: int, disagreement: dict, gate_verdict=None,
             extra: Optional[dict] = None, meta: Optional[dict] = None) -> dict:
    refusal = {"reason_code": reason_code, "reason": reason}
    if extra:
        refusal.update(extra)
    return _envelope(
        STATE_REFUSED, answer=None, value=None, agreeing_count=agreeing_count,
        quorum=quorum, n=n, provenance=None, gate_verdict=gate_verdict, confidence=None,
        redispatches=redispatches, disagreement=disagreement, refusals=[refusal], meta=meta)


# ---------------------------------------------------------------------------
# Provenance extraction from an agreeing agent return
# ---------------------------------------------------------------------------

def _binding_from_result(agent_result: Any) -> Optional[dict]:
    """Pull a {raw_response_id, json_field_path} binding out of an agent return, supporting
    both the blind-extractor schema (top-level keys) and the hca-deliver envelope
    (values[0].provenance)."""
    if not isinstance(agent_result, dict):
        return None
    rid = agent_result.get("raw_response_id")
    path = agent_result.get("json_field_path")
    if rid and path:
        return {"raw_response_id": rid, "json_field_path": path}
    vals = agent_result.get("values")
    if isinstance(vals, list) and vals and isinstance(vals[0], dict):
        prov = vals[0].get("provenance") or {}
        if prov.get("raw_response_id") and prov.get("json_field_path"):
            return {"raw_response_id": prov["raw_response_id"],
                    "json_field_path": prov["json_field_path"]}
        # aggregate-shaped provenance (carried through verbatim for the binder caller)
        if prov.get("aggregate"):
            return {"aggregate": True,
                    "contributing": prov.get("contributing", [])}
    return None


# ---------------------------------------------------------------------------
# The consensus engine
# ---------------------------------------------------------------------------

class ConsensusEngine:
    """Adjudicates N blind agent returns into a verified consensus answer (or a refusal).

    `agent_runner` is INJECTED (dependency injection): a callable that, given `(question, n)`,
    returns a list of n structured agent returns. In tests this is a simulated runner; in the
    real SKILL.md it wraps the Task()-spawned blind general-purpose agents. The engine NEVER
    calls a model itself — it only adjudicates whatever the runner returns.

    CRITICAL — BLIND RE-DISPATCH: the engine calls `agent_runner(question, n)` again on
    disagreement with the IDENTICAL arguments. There is no parameter through which prior-round
    information (values seen, "you disagreed", another agent's answer) can be passed to the
    runner. Re-dispatch is therefore structurally blind.
    """

    def __init__(self, *, binder=None, gate_suite=None,
                 value_ref: str = "consensus.value",
                 entity_type: Optional[str] = None,
                 gate_mode: str = "run_all",
                 prefer_graphql: bool = True,
                 gate_source: Optional[dict] = None,
                 gate_kwargs: Optional[dict] = None):
        self._provlib = _provenance()
        self._gatelib = _gates()
        self.binder = binder or self._provlib.ProvenanceEngine()
        self.gate_suite = gate_suite or self._gatelib.GateSuite()
        self.value_ref = value_ref
        self.entity_type = entity_type
        self.gate_mode = gate_mode
        self.prefer_graphql = prefer_graphql
        # `gate_source` is the Tier-1 RawApiResponse the gates inspect (schema/pagination/
        # freshness/etc). When omitted, consensus runs WITHOUT the deterministic gate suite
        # (substance + provenance only) — the SKILL.md / spine supplies the gate_source when a
        # full report/aggregation is being verified.
        self.gate_source = gate_source
        self.gate_kwargs = dict(gate_kwargs or {})

    # --- public entry ------------------------------------------------------
    def run(self, question: str, agent_runner: Callable[[str, int], list], *,
            quorum: Optional[Any] = None, n: Optional[int] = None,
            max_redispatch: Optional[int] = None) -> dict:
        """Run blind N-agent consensus for one question and return a ConsensusEnvelope.

        Never raises on a normal disagreement / verification problem — every outcome is a
        structured envelope (DELIVERED or REFUSED).
        """
        cfg = _read_consensus_config()
        n = int(n if n is not None else cfg["agent_count"])
        if n < 1:
            n = 1
        q_spec = quorum if quorum is not None else cfg["default_quorum"]
        quorum_threshold = parse_quorum(q_spec, n)
        max_rd = int(max_redispatch if max_redispatch is not None
                     else cfg["redispatch_retries"])
        if max_rd < 0:
            max_rd = 0

        last_disagreement = {"values_seen": [], "spread": None, "distinct_groups": 0}
        last_groups = []
        last_results = []
        last_values = []
        attempts = max_rd + 1  # round 0 (initial) + max_rd blind re-dispatches

        for attempt in range(attempts):
            # ---- DISPATCH (BLIND) -------------------------------------------
            # IDENTICAL call every round. No prior-round feedback is — or CAN be — passed.
            results = agent_runner(question, n)
            if not isinstance(results, list):
                results = list(results) if results is not None else []
            last_results = results
            values = [_extract_value(r) for r in results]
            last_values = values

            usable = [v for v in values if _substance_key(v)[0] != "none"]
            if not usable:
                # No agent produced a usable substance value this round. Treat like a
                # disagreement round (re-dispatch if budget remains, else escalate as
                # NO_CONSENSUS — never fabricate).
                last_groups = group_by_substance(values)
                last_disagreement = _disagreement_summary(values, last_groups)
                if attempt < attempts - 1:
                    continue
                return self._escalate(quorum_threshold, n, attempt, last_disagreement,
                                      reason_detail="no agent produced a usable value")

            # ---- CONSENSUS --------------------------------------------------
            groups = group_by_substance(values)
            last_groups = groups
            last_disagreement = _disagreement_summary(values, groups)
            top = groups[0]
            agreeing_count = top["count"]

            if agreeing_count >= quorum_threshold:
                # QUORUM REACHED -> verify the agreed value (binder + gates) before delivering.
                return self._verify_and_deliver(
                    question=question, groups=groups, results=results, values=values,
                    quorum=quorum_threshold, n=n, redispatches=attempt,
                    agreeing_count=agreeing_count)

            # ---- DISAGREEMENT -> bounded BLIND re-dispatch ------------------
            if attempt < attempts - 1:
                # Re-dispatch a FRESH cohort. The loop simply calls agent_runner again with
                # the SAME (question, n) — structurally no feedback reaches the agents.
                continue

            # ---- exhausted re-dispatch budget -> ESCALATE (no silent pick) --
            return self._escalate(quorum_threshold, n, attempt, last_disagreement,
                                  agreeing_count=agreeing_count)

        # Unreachable (the loop always returns), but be safe: escalate, never pick.
        return self._escalate(quorum_threshold, n, attempts - 1, last_disagreement)

    # --- escalation = structured REFUSAL (NEVER a silent pick) --------------
    def _escalate(self, quorum: int, n: int, attempt: int, disagreement: dict, *,
                  agreeing_count: int = 0, reason_detail: Optional[str] = None) -> dict:
        detail = reason_detail or (
            f"agents did not reach quorum ({agreeing_count}/{n} agreed; need {quorum}) "
            f"after {attempt} bounded blind re-dispatch(es)")
        reason = ("no consensus — escalating as a structured refusal. NO value is delivered "
                  "without quorum (no silent pick): " + detail)
        return _refused(
            REASON_NO_CONSENSUS, reason, quorum=quorum, n=n,
            agreeing_count=agreeing_count, redispatches=attempt,
            disagreement=disagreement,
            extra={"escalated": True, "agreeing_count": agreeing_count},
            meta={"escalated": True})

    # --- verify an agreed value (binder + gates) then deliver --------------
    def _verify_and_deliver(self, *, question: str, groups: list, results: list,
                            values: list, quorum: int, n: int, redispatches: int,
                            agreeing_count: int) -> dict:
        top = groups[0]
        agreed_value = top["representative"]
        disagreement = _disagreement_summary(values, groups)

        # 1) PROVENANCE — the agreed value must STILL bind+verify to Tier-1. Consensus is
        #    additive; it never bypasses the binder. We try each agreeing agent's binding
        #    until one VERIFIES (independent agents agreeing on substance may cite the same or
        #    equivalent source paths; any one resolvable+matching binding proves provenance).
        prov_result = None
        prov_attempts = []
        agreeing_indices = top["indices"]
        for idx in agreeing_indices:
            binding = _binding_from_result(results[idx]) if idx < len(results) else None
            if not binding:
                prov_attempts.append({"index": idx, "reason": "no binding on agent return"})
                continue
            extracted = _extract_value(results[idx])
            if binding.get("aggregate"):
                res = self.binder.bind_aggregate(
                    extracted, binding.get("contributing", []), value_ref=self.value_ref)
            else:
                res = self.binder.bind_and_verify(
                    extracted, binding, value_ref=self.value_ref)
            if res.get("outcome") == self._provlib.VERIFIED:
                prov_result = res
                break
            prov_attempts.append({"index": idx, "reason_code": res.get("reason_code"),
                                  "reason": res.get("reason")})

        if prov_result is None:
            # The agreed value cannot be bound to Tier-1 -> REFUSE (pass-through PROVENANCE).
            reason = ("consensus reached on substance but the agreed value could not be "
                      "bound+verified to Tier-1 — refusing (provenance is non-bypassable)")
            return _refused(
                REASON_PROVENANCE, reason, quorum=quorum, n=n,
                agreeing_count=agreeing_count, redispatches=redispatches,
                disagreement=disagreement,
                extra={"binding_attempts": prov_attempts})

        # 2) GATES — run the deterministic gate suite on the agreed value's source (when a
        #    gate_source is configured). source_count = agreeing_count so the single-source
        #    confidence cap is correctly NOT applied to a multi-source agreement.
        gate_verdict = None
        if self.gate_source is not None:
            gate_verdict = self._run_gates(agreeing_count)
            if gate_verdict.get("outcome") != self._gatelib.OUTCOME_PASS:
                failures = gate_verdict.get("failures") or ["<unknown>"]
                reason = ("consensus reached but deterministic gate(s) failed: "
                          + ", ".join(failures) +
                          " — refusing (no value delivered while a hard gate fails)")
                return _refused(
                    REASON_GATE_FAIL, reason, quorum=quorum, n=n,
                    agreeing_count=agreeing_count, redispatches=redispatches,
                    disagreement=disagreement, gate_verdict=gate_verdict,
                    extra={"failed_gates": failures})

        # 3) CONFIDENCE — driven by the AGREEING count (multi-source lifts above the cap).
        conf = self.binder.confidence_record(
            self.value_ref, source_count=agreeing_count,
            basis=f"{agreeing_count}-of-{n} blind-agent substance agreement")

        provenance = {
            "binding": prov_result.get("binding"),
            "raw_response_id": prov_result.get("raw_response_id"),
            "json_field_path": prov_result.get("json_field_path"),
            "contributing": prov_result.get("contributing", []),
            "agreeing_agent_indices": agreeing_indices,
        }
        answer = (f"{agreeing_count} of {n} independent blind agents agree (substance "
                  f"consensus at quorum {quorum}): {agreed_value}")
        return _envelope(
            STATE_DELIVERED, answer=answer, value=agreed_value,
            agreeing_count=agreeing_count, quorum=quorum, n=n, provenance=provenance,
            gate_verdict=gate_verdict, confidence=conf, redispatches=redispatches,
            disagreement=disagreement, refusals=[],
            meta={"agreeing_agent_indices": agreeing_indices})

    def _run_gates(self, source_count: int) -> dict:
        et = self.entity_type or (self.gate_source or {}).get("entity_type")
        kw = dict(self.gate_kwargs)
        kw.setdefault("entity_type", et)
        kw.setdefault("prefer_graphql", self.prefer_graphql)
        kw.setdefault("value_ref", self.value_ref)
        kw["source_count"] = source_count
        # provenance is verified separately above; tell the suite it is ok so its own
        # provenance_report check does not double-refuse.
        kw.setdefault("provenance_report", {"ok": True})
        if self.gate_mode == "deterministic_subset":
            return self.gate_suite.deterministic_subset(self.gate_source, **kw)
        return self.gate_suite.run_all(self.gate_source, **kw)


# ---------------------------------------------------------------------------
# Module-level convenience — the API the SKILL.md / slice-08 orchestration drives.
# ---------------------------------------------------------------------------

def run_consensus(question: str, agent_runner: Callable[[str, int], list], *,
                  quorum: Optional[Any] = None, n: Optional[int] = None,
                  max_redispatch: Optional[int] = None,
                  binder=None, gate_suite=None,
                  value_ref: str = "consensus.value",
                  entity_type: Optional[str] = None,
                  gate_mode: str = "run_all",
                  prefer_graphql: bool = True,
                  gate_source: Optional[dict] = None,
                  gate_kwargs: Optional[dict] = None) -> dict:
    """One-shot blind N-agent consensus adjudication. Returns a ConsensusEnvelope.

    `agent_runner(question, n) -> [agent_result, ...]` is INJECTED. Each agent_result is
    either an hca-deliver-style envelope or a blind-extractor return
    `{value, json_field_path, raw_response_id, agent_confidence}`. The engine NEVER calls a
    model itself; the SKILL.md wires `agent_runner` to N blind Task()-spawned
    general-purpose agents (subscription-only — never a direct model-API key / env secret).

    Defaults come from config.yaml `consensus:` (quorum 2-of-3, n 3, 1 re-dispatch).
    """
    engine = ConsensusEngine(
        binder=binder, gate_suite=gate_suite, value_ref=value_ref, entity_type=entity_type,
        gate_mode=gate_mode, prefer_graphql=prefer_graphql, gate_source=gate_source,
        gate_kwargs=gate_kwargs)
    return engine.run(question, agent_runner, quorum=quorum, n=n,
                      max_redispatch=max_redispatch)


# ---------------------------------------------------------------------------
# CLI — descriptive only. The engine cannot run real agents (no model call here); it prints
# the resolved consensus config + the contract so an operator can verify the wiring.
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="acos-hypercore-ask adversarial multi-model consensus engine (Demo 2). "
                    "Adjudicates N BLIND agent returns into a verified consensus answer or a "
                    "structured refusal. Spawns NO agents itself (subscription-only; the "
                    "SKILL.md wires the blind Task() agents and injects agent_runner).")
    parser.add_argument("--config", action="store_true",
                        help="print the resolved consensus config + the contract and exit")
    args = parser.parse_args(argv)
    cfg = _read_consensus_config()
    info = {
        "module": "hca-consensus",
        "consensus_config": cfg,
        "resolved_quorum_threshold": parse_quorum(cfg["default_quorum"], cfg["agent_count"]),
        "states": [STATE_DELIVERED, STATE_REFUSED],
        "refusal_reason_codes": [REASON_NO_CONSENSUS, REASON_GATE_FAIL, REASON_PROVENANCE,
                                 REASON_NO_AGENTS],
        "contract": {
            "substance_not_prose": "agents agree on the normalized number/name/date/list",
            "no_silent_pick": "below quorum -> REFUSED (NO_CONSENSUS), value == null",
            "blind_redispatch": "agent_runner is re-called with identical args; no feedback",
            "additive_verification": "an agreed value still passes binder + gate suite",
            "subscription_only": "no model call / no direct model-API key in this engine",
        },
    }
    print(json.dumps(info, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
