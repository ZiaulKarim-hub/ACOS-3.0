#!/usr/bin/env python3
"""hca-figures.py — the FIGURE abstraction + the first figure (SLICE-HCA-12).

A "figure" is a NAMED, verifiable portfolio quantity computed from Hypercore. This module
is the seed of a future FIGURES REGISTRY: each figure declares a name + synonyms + a kind
(direct | derived) + a fetch-and-verify function that returns the STANDARD ANSWER ENVELOPE

    { state, answer, values:[{value, currency, provenance, confidence}],
      gate_verdict, complete, refusals[] }

so figures slot straight into the existing deliver / consensus / report spine.

THE FIRST FIGURE — `payoff_as_of` (a.k.a. `early_redemption`):
  Given a resolved loan id + an as-of date, it asks Hypercore for the SAME thing the
  Hypercore UI's "Early Redemption" button asks for:

      getLoanRepaymentDistribution(input: GetLoanRepaymentDistributionInput!) -> InstallmentComponents

  using the EXACT KNOWN-GOOD input shape (verified live 2026-06-19 — see
  memory/decisions/2026-06-19-hypercore-early-redemption-input.md). A minimal /
  `isPrepayment:true` input CRASHES the resolver with HTTP 500, so the input MUST be:

      { loanId, includeDraftChanges:false, date:"<YYYY-MM-DD>",
        repaymentType:"EarlyRedemption",
        applyExpectedRepaymentsUntilEarlyRedemption:false, isPrepayment:false }

  The figure then:
    1. RETRIES the live call up to 3x with short backoff (the resolver is intermittently
       flaky / returns HTTP 500); it only REFUSES after retries are exhausted, stating the 500.
    2. PROVENANCE-BINDS the `total` to a cached Tier-1 record (provenance = the operation +
       input + the `$.body.record.total` field path). A value never escapes unbound.
    3. RECONCILES the components — principal + indexedPrincipal + interest + compoundingInterest
       + accruedCompoundingInterest + totalFees + totalPenalties + totalTaxes == total, within
       $0.01. It REFUSES if it does not reconcile (a fabricated / internally-inconsistent total
       is never delivered).
    4. Sets CONFIDENCE (single-source -> capped + flagged via the provenance engine) and
       ITEMIZES every component in the envelope meta.

  Default date = today (UTC) when the caller gives none; an explicit date is honored.

`getLoanRepaymentDistribution` is a Query field (confirmed in the introspection) — this is a
READ / preview, NOT a mutation. The transport's `assert_query_only` guard still applies.

GROUND RULES (memory/decisions/2026-06-18-hca-build-ground-rules.md):
  - Python 3 stdlib ONLY. No third-party deps. No model calls; never ANTHROPIC_API_KEY.
  - Read-only: the only API touch is a GraphQL `query`.
  - No real PII committed: the figure deals in loan-level money totals/components only; tests
    use synthetic fixtures.
"""

from __future__ import annotations

import argparse
import datetime
import importlib.util
import json
import os
import sys
import time
from typing import Callable, Optional


# ---------------------------------------------------------------------------
# Terminal states (mirror the spine envelope vocabulary)
# ---------------------------------------------------------------------------

STATE_DELIVERED = "DELIVERED"
STATE_REFUSED = "REFUSED"
STATE_NO_LIVE_DATA = "NO_LIVE_DATA"

REASON_LIVE_500 = "LIVE_500"                 # getLoanRepaymentDistribution failed after retries
REASON_RECONCILE = "RECONCILE_FAILED"        # components do not sum to total within tolerance
REASON_PROVENANCE = "PROVENANCE_REFUSED"     # total could not be bound+verified to Tier-1
REASON_FETCH_EMPTY = "FETCH_EMPTY"           # no InstallmentComponents in the response
REASON_BAD_INPUT = "BAD_INPUT"               # missing loan id / malformed date
REASON_REQUIRES_EXTERNAL = "REQUIRES_EXTERNAL"  # metric needs KG data Hypercore can't source
REASON_DERIVE_FAILED = "DERIVE_FAILED"       # a derived figure's input could not be sourced
REASON_KG_NO_MATCH = "KG_NO_MATCH"           # no confident KG node matched the loan name
REASON_KG_FIELD_MISSING = "KG_FIELD_MISSING"  # the matched KG node lacks the required field


# Reconciliation tolerance (dollars). The brief's ground-truth reconciles to the cent.
RECONCILE_TOLERANCE = 0.01

# LTV cross-check tolerance: our computed LTV (outstanding/appraised_value) vs the KG's own
# stored `ltv_latest`. Beyond this absolute gap we FLAG a divergence (do not refuse — both are
# reported; a gap usually means the balance moved or the value was re-struck since ltv_latest).
LTV_CROSSCHECK_TOLERANCE = 0.05

# Retry policy for the flaky resolver (HTTP 500 intermittent).
RETRY_ATTEMPTS = 3
RETRY_BACKOFF_S = 0.5


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


def _vocab():
    # hca-vocab is a pure data LEAF (imports nothing from the skill) -> sourcing the payoff /
    # utilization vocabularies + KIND_* constants from it cannot create a circular import.
    return _load("hca_vocab", "hca-vocab.py")


def _adapter():
    return _load("hca_adapter", "hca-adapter.py")


def _cache():
    return _load("hca_cache", "hca-cache.py")


def _provenance():
    return _load("hca_provenance", "hca-provenance.py")


def _kg():
    return _load("hca_kg", "hca-kg.py")


# ---------------------------------------------------------------------------
# Time helper
# ---------------------------------------------------------------------------

def _today_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _valid_date(d: str) -> bool:
    try:
        datetime.datetime.strptime(d, "%Y-%m-%d")
        return True
    except (TypeError, ValueError):
        return False


# ---------------------------------------------------------------------------
# Envelope builders (the STANDARD answer envelope)
# ---------------------------------------------------------------------------

def _envelope(state: str, *, answer, values: list, gate_verdict, complete: bool,
              refusals: list, meta: Optional[dict] = None) -> dict:
    return {
        "state": state,
        "answer": answer,
        "values": values,
        "gate_verdict": gate_verdict,
        "complete": complete,
        "refusals": refusals,
        "meta": meta or {},
    }


def _refused(reason_code: str, reason: str, *, meta: Optional[dict] = None) -> dict:
    return _envelope(STATE_REFUSED, answer=None, values=[], gate_verdict=None,
                     complete=False,
                     refusals=[{"reason_code": reason_code, "reason": reason}],
                     meta=meta)


# ---------------------------------------------------------------------------
# The Figure abstraction (registry seed)
# ---------------------------------------------------------------------------

# Figure-kind constants — single source of truth in the shared vocabulary leaf (these were
# duplicated identically here and in hca-ontology.py). Re-exported as module attributes so
# existing `figures_mod.KIND_DIRECT` references (tests + deliver) keep working unchanged.
KIND_DIRECT = _vocab().KIND_DIRECT                      # a value read straight off one API field
KIND_DERIVED = _vocab().KIND_DERIVED                    # computed/reconciled from many fields
KIND_REQUIRES_EXTERNAL = _vocab().KIND_REQUIRES_EXTERNAL  # needs external KG data (refuses)


class Figure:
    """A named, verifiable portfolio figure.

    Attributes
    ----------
    name : str            canonical figure name (e.g. "payoff_as_of")
    synonyms : tuple      alternate names the planner/CLI may route on
                          (e.g. "early_redemption", "amount to redeem")
    kind : str            KIND_DIRECT | KIND_DERIVED
    fetch_verify : callable(**kwargs) -> answer-envelope dict
                          performs fetch + provenance-bind + verify and returns the
                          STANDARD ANSWER ENVELOPE (or a terminal REFUSED / NO_LIVE_DATA).
    description : str     one-line human description.
    """

    __slots__ = ("name", "synonyms", "kind", "fetch_verify", "description")

    def __init__(self, name: str, *, synonyms=(), kind: str = KIND_DERIVED,
                 fetch_verify: Callable[..., dict], description: str = ""):
        self.name = name
        self.synonyms = tuple(synonyms)
        self.kind = kind
        self.fetch_verify = fetch_verify
        self.description = description

    def matches(self, token: str) -> bool:
        """True if `token` is this figure's canonical name or one of its synonyms (normalized)."""
        t = (token or "").strip().lower()
        if not t:
            return False
        if t == self.name.lower():
            return True
        return any(t == s.lower() for s in self.synonyms)

    def run(self, **kwargs) -> dict:
        return self.fetch_verify(**kwargs)


class FigureRegistry:
    """A tiny registry of figures. Seed of the future full figures catalog.

    Lookup is by canonical name OR any synonym (so the CLI / deliver planner can route
    "payoff" / "early redemption" / "amount to redeem" onto the same figure).
    """

    def __init__(self):
        self._figures: list = []

    def register(self, figure: Figure) -> None:
        self._figures.append(figure)

    def names(self) -> list:
        return [f.name for f in self._figures]

    def get(self, token: str) -> Optional[Figure]:
        for f in self._figures:
            if f.matches(token):
                return f
        return None


# ---------------------------------------------------------------------------
# getLoanRepaymentDistribution — operation + the EXACT KNOWN-GOOD input shape
# ---------------------------------------------------------------------------

# InstallmentComponents fields we select (confirmed present in the introspection).
_INSTALLMENT_SELECTION = (
    "total totalWithTaxes principal indexedPrincipal compoundingInterest "
    "accruedCompoundingInterest interest totalFees totalPenalties totalTaxes"
)

# The components that, summed, MUST equal `total` (reconciliation identity).
_RECONCILE_COMPONENTS = (
    "principal", "indexedPrincipal", "interest", "compoundingInterest",
    "accruedCompoundingInterest", "totalFees", "totalPenalties", "totalTaxes",
)

_REPAYMENT_DISTRIBUTION_QUERY = (
    "query HCAEarlyRedemption($input: GetLoanRepaymentDistributionInput!) { "
    f"getLoanRepaymentDistribution(input: $input) {{ {_INSTALLMENT_SELECTION} }} "
    "}"
)


def known_good_redemption_input(loan_id: str, date: str) -> dict:
    """The EXACT input that the Hypercore UI's Early-Redemption button sends.

    A minimal / `isPrepayment:true` input CRASHES the resolver (HTTP 500); this shape is the
    verified-working one (2026-06-19). Do NOT trim fields from this dict.
    """
    return {
        "loanId": loan_id,
        "includeDraftChanges": False,
        "date": date,
        "repaymentType": "EarlyRedemption",
        "applyExpectedRepaymentsUntilEarlyRedemption": False,
        "isPrepayment": False,
    }


def _is_http_500(exc: Exception) -> bool:
    """Does this exception look like the intermittent HTTP 5xx the resolver returns?

    Match ONLY on a server-error signal: an explicit numeric `status` attribute in the 5xx
    range (LiveServerError carries this), or a "500" / "internal server error" string in the
    message. The bare substring "transport" was DROPPED — it caused fatal non-5xx transport
    errors (TLS handshake, connection reset, DNS failure) to be retried 3x as if flaky. A
    read-only violation (ReadOnlyViolation — no status attr, no 5xx text) is correctly NOT
    treated as retryable and is surfaced immediately by the caller.
    """
    status = getattr(exc, "status", None)
    if isinstance(status, int) and 500 <= status < 600:
        return True
    msg = f"{type(exc).__name__}: {exc}".lower()
    return ("500" in msg) or ("internal server error" in msg)


def _call_with_retry(client, query: str, variables: dict, *,
                     attempts: int = RETRY_ATTEMPTS, backoff_s: float = RETRY_BACKOFF_S,
                     sleep: Callable[[float], None] = time.sleep) -> tuple:
    """Run client.raw_query with bounded retry on the flaky 500.

    Returns (data, attempts_made, errors[]). Raises the LAST exception only after the retry
    budget is exhausted (the caller turns that into a REFUSED stating the 500). A non-500
    error (e.g. a read-only violation) is NOT retried — it is raised immediately.
    """
    errors: list = []
    last_exc: Optional[Exception] = None
    for i in range(1, max(1, attempts) + 1):
        try:
            data = client.raw_query(query, variables)
            return data, i, errors
        except Exception as e:  # noqa: BLE001 — bounded, classified below
            last_exc = e
            errors.append(f"attempt {i}: {type(e).__name__}: {str(e)[:160]}")
            if not _is_http_500(e):
                # Not the flaky 500 — surface immediately (don't burn retries on a real error).
                raise
            if i < attempts:
                sleep(backoff_s * i)  # linear backoff
    # Retries exhausted on the flaky 500.
    raise last_exc  # type: ignore[misc]


# ---------------------------------------------------------------------------
# The payoff / early-redemption figure
# ---------------------------------------------------------------------------

class PayoffFigure:
    """`payoff_as_of` / `early_redemption` — verified early-redemption payoff as of a date.

    Construct with a `client` exposing raw_query(query, variables) -> data (the live
    LiveGraphQLClient satisfies this; tests inject a fake). `cache` + `engine` default to the
    shared Tier-1 cache + provenance engine so the bound value is independently re-resolvable.
    """

    NAME = "payoff_as_of"
    # Sourced from the shared vocabulary leaf (UNION of the prior figure synonyms + the deliver
    # payoff triggers — single source of truth so the two can never diverge again).
    SYNONYMS = _vocab().PAYOFF_TERMS

    def __init__(self, *, client=None, cache=None, engine=None,
                 currency: Optional[str] = None,
                 retry_attempts: int = RETRY_ATTEMPTS,
                 retry_backoff_s: float = RETRY_BACKOFF_S,
                 sleep: Callable[[float], None] = time.sleep):
        self._client = client
        self._cachelib = _cache()
        self._provlib = _provenance()
        self._cache = cache or self._cachelib.TwoTierCache()
        self._engine = engine or self._provlib.ProvenanceEngine(cache=self._cache)
        self._currency = currency
        self._attempts = int(retry_attempts)
        self._backoff = float(retry_backoff_s)
        self._sleep = sleep
        self._summary_fetcher = None  # optional: derive currency from loan.currency

    def attach_summary_fetcher(self, fetcher) -> None:
        """Attach a LoanSummaryFetcher so the payoff figure can read loan.currency (slice-A
        polish: the payoff value carries currency=loan.currency, not just a caller hint)."""
        self._summary_fetcher = fetcher

    def _derive_currency(self, loan_id: str, loan_name: Optional[str]) -> Optional[str]:
        """Best-effort loan.currency lookup (never fails the figure if it can't get it)."""
        if self._summary_fetcher is None:
            return None
        try:
            res = self._summary_fetcher.fetch(loan_id, loan_name=loan_name)
        except Exception:
            return None
        if res.get("ok") and isinstance(res.get("row"), dict):
            return res["row"].get("currency")
        return None

    # --- live client (lazy) ------------------------------------------------
    def _ensure_client(self):
        if self._client is not None:
            return self._client
        ad = _adapter()
        self._client = ad.LiveBackend().live_client()
        return self._client

    # --- main: compute the figure -----------------------------------------
    def fetch_verify(self, *, loan_id: str, date: Optional[str] = None,
                     loan_name: Optional[str] = None,
                     currency: Optional[str] = None) -> dict:
        """Compute the early-redemption payoff for `loan_id` as of `date` (default: today).

        Returns the STANDARD ANSWER ENVELOPE. Verification (retry -> bind -> reconcile) is
        non-bypassable: the `total` only reaches `answer` after it is bound to Tier-1 AND the
        components reconcile to it within $0.01.
        """
        if not loan_id:
            return _refused(REASON_BAD_INPUT, "no loan id supplied — cannot compute payoff")
        as_of = date or _today_iso()
        if not _valid_date(as_of):
            return _refused(REASON_BAD_INPUT,
                            f"invalid date {as_of!r} — expected YYYY-MM-DD")

        # 1) Build the EXACT known-good input + run with bounded retry on the flaky 500.
        gql_input = known_good_redemption_input(loan_id, as_of)
        variables = {"input": gql_input}
        try:
            client = self._ensure_client()
        except Exception as e:
            # Missing creds -> NO_LIVE_DATA (never fabricate); other build errors -> refuse.
            ad = _adapter()
            if isinstance(e, getattr(ad, "NoLiveDataError", ())):
                return _envelope(STATE_NO_LIVE_DATA, answer=None, values=[],
                                 gate_verdict=None, complete=False,
                                 refusals=[{"reason_code": STATE_NO_LIVE_DATA,
                                            "reason": str(e)}],
                                 meta={"loan_id": loan_id, "date": as_of})
            return _refused(REASON_LIVE_500,
                            f"could not build live client: {type(e).__name__}: {str(e)[:160]}",
                            meta={"loan_id": loan_id, "date": as_of})

        try:
            data, attempts_made, errors = _call_with_retry(
                client, _REPAYMENT_DISTRIBUTION_QUERY, variables,
                attempts=self._attempts, backoff_s=self._backoff, sleep=self._sleep)
        except Exception as e:
            note = ("getLoanRepaymentDistribution failed after "
                    f"{self._attempts} attempt(s): {type(e).__name__}: {str(e)[:200]} "
                    "(the resolver returns intermittent HTTP 500; refusing rather than "
                    "fabricating a payoff)")
            return _refused(REASON_LIVE_500, note,
                            meta={"loan_id": loan_id, "date": as_of,
                                  "operation": "getLoanRepaymentDistribution",
                                  "input": gql_input})

        components = (data or {}).get("getLoanRepaymentDistribution")
        if not isinstance(components, dict):
            return _refused(REASON_FETCH_EMPTY,
                            "getLoanRepaymentDistribution returned no InstallmentComponents "
                            "object — refusing (never guess a payoff)",
                            meta={"loan_id": loan_id, "date": as_of, "input": gql_input})

        total = components.get("total")
        if not isinstance(total, (int, float)) or isinstance(total, bool):
            return _refused(REASON_FETCH_EMPTY,
                            f"non-numeric/absent `total` in InstallmentComponents "
                            f"({total!r}) — refusing",
                            meta={"loan_id": loan_id, "date": as_of, "input": gql_input})

        # 2) CACHE the raw response as an immutable Tier-1 record (so the binder can re-read it).
        fetched_at = _now_iso()
        raw = self._cachelib_make_raw(loan_id, as_of, gql_input, components,
                                      attempts_made, fetched_at)
        rid = self._cache.put_raw(raw)
        raw = self._cache.get_raw(rid)

        # 3) PROVENANCE: bind `total` to its Tier-1 path. A mismatch/miss => REFUSE.
        total_path = "$.body.record.total"
        prov = self._engine.bind_and_verify(
            total, {"raw_response_id": rid, "json_field_path": total_path},
            value_ref=f"loan.{loan_id}.payoff_as_of.{as_of}")
        if prov["outcome"] != self._provlib.VERIFIED:
            return _refused(REASON_PROVENANCE, prov["reason"],
                            meta={"loan_id": loan_id, "date": as_of,
                                  "reason_code_inner": prov["reason_code"]})

        # 4) RECONCILE: components must sum to total within tolerance, else REFUSE.
        recon = self._reconcile(components, total)
        if not recon["ok"]:
            return _refused(
                REASON_RECONCILE,
                (f"components do not reconcile to total within ${RECONCILE_TOLERANCE}: "
                 f"sum(components)={recon['component_sum']} vs total={total} "
                 f"(diff={recon['diff']}) — refusing (an internally inconsistent payoff is "
                 "never delivered)"),
                meta={"loan_id": loan_id, "date": as_of,
                      "components": recon["components"],
                      "component_sum": recon["component_sum"], "total": total,
                      "diff": recon["diff"], "reconciles": False})

        # 5) CONFIDENCE: single-source figure -> capped + flagged via the engine.
        conf = self._engine.confidence_record(
            f"loan.{loan_id}.payoff_as_of.{as_of}", source_count=1,
            basis="single-source early-redemption distribution (reconciled)")

        cur = currency or self._currency or self._derive_currency(loan_id, loan_name)
        out_value = {
            "value": float(total),
            "currency": cur,
            "provenance": {
                "raw_response_id": rid,
                "json_field_path": total_path,
                "operation": "getLoanRepaymentDistribution",
                "input": gql_input,
                "fetched_at": fetched_at,
            },
            "confidence": conf["confidence"],
        }
        name_str = f" for {loan_name!r}" if loan_name else ""
        cur_str = f" {cur}" if cur else ""
        answer = (f"The early-redemption payoff{name_str} (loan {loan_id}) as of {as_of} "
                  f"is {float(total)}{cur_str}.")
        # gate_verdict here is the reconciliation verdict (the figure's own hard gate).
        gate_verdict = {
            "outcome": "pass",
            "reconciliation_ok": True,
            "reconcile_tolerance": RECONCILE_TOLERANCE,
            "component_sum": recon["component_sum"],
            "total": float(total),
            "diff": recon["diff"],
            "single_source": conf["single_source"],
        }
        return _envelope(
            STATE_DELIVERED, answer=answer, values=[out_value],
            gate_verdict=gate_verdict, complete=True, refusals=[],
            meta={
                "figure": self.NAME,
                "loan_id": loan_id,
                "loan_name": loan_name,
                "date": as_of,
                "currency": cur,
                "reconciles": True,
                "components": recon["components"],
                "totalWithTaxes": components.get("totalWithTaxes"),
                "attempts": attempts_made,
                "retry_errors": errors,
                "confidence_record": conf,
            })

    # --- reconciliation ----------------------------------------------------
    def _reconcile(self, components: dict, total: float) -> dict:
        """Sum the reconciliation components and compare to total within tolerance.

        Treats an absent component as 0.0 (the introspection guarantees the fields exist; a
        null is a real 0 contribution). Returns {ok, component_sum, diff, components}.
        """
        itemized = {}
        comp_sum = 0.0
        for f in _RECONCILE_COMPONENTS:
            v = components.get(f)
            num = float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else 0.0
            itemized[f] = num
            comp_sum += num
        comp_sum = round(comp_sum, 4)
        diff = round(abs(comp_sum - float(total)), 6)
        return {"ok": diff <= RECONCILE_TOLERANCE, "component_sum": comp_sum,
                "diff": diff, "components": itemized}

    # --- Tier-1 record assembly --------------------------------------------
    def _cachelib_make_raw(self, loan_id: str, as_of: str, gql_input: dict,
                           components: dict, attempts: int, fetched_at: str) -> dict:
        ad = _adapter()
        return ad.make_raw_api_response(
            raw_response_id=f"live:getLoanRepaymentDistribution:{loan_id}:{as_of}:{fetched_at}",
            endpoint="getLoanRepaymentDistribution",
            request_params={"graphql_operation": "HCAEarlyRedemption", "input": gql_input},
            timestamp=fetched_at,
            http_status=200,
            cursor=None,
            reported_total=None,
            body={"record": components,
                  "provenance": {"fetched_at": fetched_at,
                                 "operation": "getLoanRepaymentDistribution",
                                 "input": gql_input, "attempts": attempts}},
            backend="live",
        )


# ===========================================================================
# HYPERCORE-NATIVE FIGURES (SLICE-HCA-13)
# ===========================================================================
#
# Each native figure is a PROVENANCE-BOUND read off the loan's LoanSummary (the RELIABLE
# list+summary path — loan(id) is flaky), carrying currency + single-source confidence. A
# value never escapes unbound: the fetched summary is cached as an immutable Tier-1 record and
# the figure's value is re-walked + matched at its json_field_path before delivery.
#
# WHY THE LIST+SUMMARY PATH (verified live 2026-06-19):
#   loan(id) and the transaction-preview resolvers are intermittently HTTP 500. The reliable
#   read is loans(filter:{searchString}){ pageItems{ id name currency commitment summary{...} } },
#   then pick the row whose id matches the resolved loan id. So every native figure rides that
#   one query (one fetch per loan, shared/cached so a multi-figure report hits it once).

# The LoanSummary sub-selection (fields verified by the brief's field mapping). Each money
# block is an InstallmentComponents-shaped object with `total` + components.
_SUMMARY_SELECTION = (
    "summary { "
    "totalOutstanding { total principal interest compoundingInterest totalFees totalPenalties "
    "capitalizedBalance } "
    "totalDue { total principal interest } "
    "overdue { total } "
    "totalPaid { total } "
    "totalDisbursed unutilizedPrincipal distributedPrincipal interestRate "
    "}"
)

# Loan-level scalar fields fetched alongside the summary (currency + commitment + maturity).
_LOAN_SCALAR_SELECTION = "id name currency commitment scheduleEndDate scheduleExpectedEndDate status annualInterestRate"

_LOAN_SUMMARY_QUERY = (
    "query HCALoanSummary($filter: LoansFilterInput, $skip: Int, $limit: Int) { "
    "loans(filter: $filter, skip: $skip, limit: $limit) { "
    f"totalFilteredRecords pageItems {{ {_LOAN_SCALAR_SELECTION} {_SUMMARY_SELECTION} }} "
    "} }"
)

_SUMMARY_FETCH_LIMIT = 100


class LoanSummaryFetcher:
    """Fetches a single loan's scalar fields + LoanSummary via the RELIABLE list query, caches
    it immutably as Tier-1, and hands figures a (row, raw_response_id) pair to bind against.

    One fetch per (loan_id) — the result is cached in-process AND in the shared Tier-1 cache so
    multiple figures over the same loan (a report) reuse it. Provenance binding re-reads the
    cached Tier-1 record by id, so every native figure's value is independently re-resolvable.
    """

    def __init__(self, *, client=None, cache=None,
                 retry_attempts: int = RETRY_ATTEMPTS,
                 retry_backoff_s: float = RETRY_BACKOFF_S,
                 sleep: Callable[[float], None] = time.sleep):
        self._client = client
        self._cachelib = _cache()
        self._cache = cache or self._cachelib.TwoTierCache()
        self._attempts = int(retry_attempts)
        self._backoff = float(retry_backoff_s)
        self._sleep = sleep
        self._memo: dict = {}  # loan_id -> {"row":..., "rid":..., "fetched_at":...} or {"error":...}

    def _ensure_client(self):
        if self._client is not None:
            return self._client
        ad = _adapter()
        self._client = ad.LiveBackend().live_client()
        return self._client

    def fetch(self, loan_id: str, *, loan_name: Optional[str] = None) -> dict:
        """Return {"ok":True,"row":<pageItem>,"rid":<tier1 id>,"fetched_at":...} or
        {"ok":False,"reason_code":...,"reason":...,"state":...}. Caches per loan_id."""
        if loan_id in self._memo:
            return self._memo[loan_id]
        try:
            client = self._ensure_client()
        except Exception as e:
            ad = _adapter()
            if isinstance(e, getattr(ad, "NoLiveDataError", ())):
                res = {"ok": False, "state": STATE_NO_LIVE_DATA, "reason_code": STATE_NO_LIVE_DATA,
                       "reason": str(e)}
            else:
                res = {"ok": False, "state": STATE_REFUSED, "reason_code": REASON_LIVE_500,
                       "reason": f"could not build live client: {type(e).__name__}: {str(e)[:160]}"}
            self._memo[loan_id] = res
            return res

        # Search by the loan name (most selective) then fall back to unfiltered; match by id.
        row = None
        search_terms = []
        if loan_name:
            search_terms.append(loan_name)
        search_terms.append(None)  # unfiltered fallback
        last_err = None
        for st in search_terms:
            try:
                row = self._find_row(client, loan_id, st)
            except Exception as e:  # noqa: BLE001 — surfaced below, never fabricated
                last_err = e
                continue
            # A search that COMPLETED without raising supersedes any earlier transport error:
            # a clean "no matching id" must report REASON_FETCH_EMPTY, not REASON_LIVE_500 from
            # a prior (e.g. name-filtered) attempt that 500'd. Reset the recorded error.
            last_err = None
            if row is not None:
                break
        if row is None:
            if last_err is not None:
                res = {"ok": False, "state": STATE_REFUSED, "reason_code": REASON_LIVE_500,
                       "reason": (f"loan summary fetch failed: {type(last_err).__name__}: "
                                  f"{str(last_err)[:200]}")}
            else:
                res = {"ok": False, "state": STATE_REFUSED, "reason_code": REASON_FETCH_EMPTY,
                       "reason": (f"no loan row with id {loan_id!r} returned by loans(...) — "
                                  "refusing (never invent a loan)")}
            self._memo[loan_id] = res
            return res

        # Cache the row as an immutable Tier-1 record so figures can bind against it.
        fetched_at = _now_iso()
        ad = _adapter()
        raw = ad.make_raw_api_response(
            raw_response_id=f"live:loanSummary:{loan_id}:{fetched_at}",
            endpoint="loans",
            request_params={"graphql_operation": "HCALoanSummary", "loan_id": loan_id},
            timestamp=fetched_at, http_status=200, cursor=None, reported_total=None,
            body={"record": row,
                  "provenance": {"fetched_at": fetched_at, "operation": "loans",
                                 "selection": "summary", "loan_id": loan_id}},
            backend="live")
        rid = self._cache.put_raw(raw)
        res = {"ok": True, "row": self._cache.get_raw(rid).get("body", {}).get("record", row),
               "rid": rid, "fetched_at": fetched_at}
        self._memo[loan_id] = res
        return res

    def _find_row(self, client, loan_id: str, search_string: Optional[str]):
        filt = {"searchString": search_string} if search_string else {}
        skip = 0
        pages = 0
        while True:
            pages += 1
            if pages > 1000:
                return None
            variables = {"filter": filt, "skip": skip, "limit": _SUMMARY_FETCH_LIMIT}
            data, _attempts, _errs = _call_with_retry(
                client, _LOAN_SUMMARY_QUERY, variables,
                attempts=self._attempts, backoff_s=self._backoff, sleep=self._sleep)
            page = (data or {}).get("loans") or {}
            items = page.get("pageItems") or []
            for it in items:
                if str(it.get("id")) == str(loan_id):
                    return it
            total = page.get("totalFilteredRecords")
            got = (skip + len(items))
            if not items or (total is not None and got >= total):
                return None
            if len(items) < _SUMMARY_FETCH_LIMIT:
                return None
            skip += _SUMMARY_FETCH_LIMIT


def _strip_loan_prefix(field_path: str) -> str:
    """Strip a leading 'loan.' prefix from a logical field path, returning the relative path.

    The cached loan row IS the loan record, so a 'loan.'-prefixed path ('loan.commitment') and
    a bare path ('summary.totalOutstanding.total') both address fields directly on the row.
    Single source of truth for the prefix strip used by _summary_path + the two figure fetchers.
    """
    fp = (field_path or "").strip()
    if fp.startswith("loan."):
        return fp[len("loan."):]
    return fp


def _summary_path(field_path: str) -> str:
    """Map a logical 'summary.totalOutstanding.total' source path to the Tier-1 json path.

    The cached Tier-1 record stores the loan row at $.body.record, so e.g.
      summary.totalOutstanding.total  ->  $.body.record.summary.totalOutstanding.total
      loan.commitment / commitment    ->  $.body.record.commitment
      loan.scheduleEndDate            ->  $.body.record.scheduleEndDate
    """
    return f"$.body.record.{_strip_loan_prefix(field_path)}"


class NativeFigure:
    """A Hypercore-native figure: a provenance-bound read off the loan summary/scalars.

    Construct with the source field path (logical, e.g. 'summary.totalOutstanding.total'),
    a unit, and a shared LoanSummaryFetcher. fetch_verify(loan_id, ...) fetches+caches the loan
    row, binds the value at its Tier-1 path, attaches currency (from loan.currency) + single-
    source confidence, and returns the STANDARD ANSWER ENVELOPE.
    """

    def __init__(self, name: str, *, field_path: str, unit: str = "currency",
                 synonyms=(), description: str = "",
                 fetcher: Optional[LoanSummaryFetcher] = None,
                 cache=None, engine=None,
                 reconcile_components: Optional[tuple] = None):
        self.name = name
        self.field_path = field_path
        self.unit = unit
        self.synonyms = tuple(synonyms)
        self.description = description
        self._fetcher = fetcher or LoanSummaryFetcher(cache=cache)
        self._cachelib = _cache()
        self._provlib = _provenance()
        self._cache = cache or self._fetcher._cache
        self._engine = engine or self._provlib.ProvenanceEngine(cache=self._cache)
        self._reconcile_components = reconcile_components

    def fetch_verify(self, *, loan_id: str, loan_name: Optional[str] = None,
                     date: Optional[str] = None, currency: Optional[str] = None) -> dict:
        if not loan_id:
            return _refused(REASON_BAD_INPUT, f"no loan id supplied — cannot read {self.name}")
        fetched = self._fetcher.fetch(loan_id, loan_name=loan_name)
        if not fetched.get("ok"):
            state = fetched.get("state", STATE_REFUSED)
            if state == STATE_NO_LIVE_DATA:
                return _envelope(STATE_NO_LIVE_DATA, answer=None, values=[], gate_verdict=None,
                                 complete=False,
                                 refusals=[{"reason_code": STATE_NO_LIVE_DATA,
                                            "reason": fetched.get("reason")}],
                                 meta={"figure": self.name, "loan_id": loan_id})
            return _refused(fetched.get("reason_code", REASON_FETCH_EMPTY),
                            fetched.get("reason", "loan summary fetch failed"),
                            meta={"figure": self.name, "loan_id": loan_id})

        row = fetched["row"]
        rid = fetched["rid"]
        cur = currency or row.get("currency")

        # Resolve the value at the logical path within the cached row.
        rel = _strip_loan_prefix(self.field_path)
        value = _walk_dotted(row, rel)
        if value is _ABSENT:
            return _refused(REASON_FETCH_EMPTY,
                            f"{self.name}: field {self.field_path!r} absent from the loan "
                            "summary — refusing (never guess)",
                            meta={"figure": self.name, "loan_id": loan_id})
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            if self.unit == "date" and isinstance(value, str):
                pass  # dates are strings; allowed
            else:
                return _refused(REASON_FETCH_EMPTY,
                                f"{self.name}: non-numeric value {value!r} at {self.field_path!r} "
                                "— refusing", meta={"figure": self.name, "loan_id": loan_id})

        # PROVENANCE-BIND the value to its Tier-1 path. A mismatch/miss => REFUSE.
        tpath = _summary_path(self.field_path)
        prov = self._engine.bind_and_verify(
            value, {"raw_response_id": rid, "json_field_path": tpath},
            value_ref=f"loan.{loan_id}.{self.name}")
        if prov["outcome"] != self._provlib.VERIFIED:
            return _refused(REASON_PROVENANCE, prov["reason"],
                            meta={"figure": self.name, "loan_id": loan_id,
                                  "reason_code_inner": prov["reason_code"]})

        # Optional reconciliation (e.g. outstanding_balance = principal + interest + ...).
        reconcile_meta = None
        if self._reconcile_components:
            reconcile_meta = self._reconcile(row, rel, value)
            if reconcile_meta and not reconcile_meta["ok"]:
                return _refused(
                    REASON_RECONCILE,
                    (f"{self.name}: components do not reconcile to total within "
                     f"${RECONCILE_TOLERANCE}: sum={reconcile_meta['component_sum']} vs "
                     f"total={value} (diff={reconcile_meta['diff']}) — refusing"),
                    meta={"figure": self.name, "loan_id": loan_id, "reconcile": reconcile_meta})

        conf = self._engine.confidence_record(
            f"loan.{loan_id}.{self.name}", source_count=1,
            basis=f"single-source Hypercore LoanSummary read ({self.field_path})")

        out_value = {
            "value": value,
            "currency": cur if self.unit == "currency" else None,
            "unit": self.unit,
            "provenance": {"raw_response_id": rid, "json_field_path": tpath,
                           "operation": "loans", "field_path": self.field_path,
                           "fetched_at": fetched.get("fetched_at")},
            "confidence": conf["confidence"],
        }
        name_str = f" for {loan_name!r}" if loan_name else ""
        cur_str = f" {cur}" if (cur and self.unit == "currency") else ""
        answer = f"The {self.name}{name_str} (loan {loan_id}) is {value}{cur_str}."
        gate_verdict = {"outcome": "pass", "single_source": conf["single_source"]}
        if reconcile_meta:
            gate_verdict["reconciliation_ok"] = True
            gate_verdict["component_sum"] = reconcile_meta["component_sum"]
        meta = {"figure": self.name, "loan_id": loan_id, "loan_name": loan_name,
                "currency": cur, "unit": self.unit, "confidence_record": conf}
        if reconcile_meta:
            meta["reconcile"] = reconcile_meta
        return _envelope(STATE_DELIVERED, answer=answer, values=[out_value],
                         gate_verdict=gate_verdict, complete=True, refusals=[], meta=meta)

    def _reconcile(self, row: dict, rel: str, total) -> Optional[dict]:
        """Reconcile a total against named sibling components under the same parent block.

        `self._reconcile_components` is a tuple of sibling field names (under the same parent as
        the total). Returns {ok, component_sum, diff, components} or None if the parent is absent.
        """
        parent_path = rel.rsplit(".", 1)[0] if "." in rel else ""
        parent = _walk_dotted(row, parent_path) if parent_path else row
        if not isinstance(parent, dict):
            return None
        itemized = {}
        comp_sum = 0.0
        for f in self._reconcile_components:
            v = parent.get(f)
            num = float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else 0.0
            itemized[f] = num
            comp_sum += num
        comp_sum = round(comp_sum, 4)
        diff = round(abs(comp_sum - float(total)), 6)
        return {"ok": diff <= RECONCILE_TOLERANCE, "component_sum": comp_sum,
                "diff": diff, "components": itemized}


_ABSENT = object()


def _walk_dotted(obj, dotted: str):
    """Walk a simple dotted path ('summary.totalOutstanding.total') over nested dicts.

    Returns the value or the _ABSENT sentinel. Pure structural walk; never coerces."""
    if not dotted:
        return obj
    cur = obj
    for key in dotted.split("."):
        if not isinstance(cur, dict) or key not in cur:
            return _ABSENT
        cur = cur[key]
    return cur


class DerivedFigure:
    """A figure computed from other registered figures via a TRANSPARENT formula.

    The current derived figure is `utilization = total_disbursed / commitment`. It RUNS its two
    input figures (so each input is itself provenance-bound + reconciled where applicable), shows
    the inputs + the formula in the envelope, and REFUSES if either input refuses (never guesses).
    """

    def __init__(self, name: str, *, formula: str, inputs: tuple,
                 compute: Callable[[dict], float], unit: str = "ratio",
                 synonyms=(), description: str = "", registry=None,
                 cache=None, engine=None):
        self.name = name
        self.formula = formula
        self.inputs = tuple(inputs)
        self._compute = compute
        self.unit = unit
        self.synonyms = tuple(synonyms)
        self.description = description
        self._registry = registry
        self._cachelib = _cache()
        self._provlib = _provenance()
        self._cache = cache
        self._engine = engine

    def fetch_verify(self, *, loan_id: str, loan_name: Optional[str] = None,
                     date: Optional[str] = None, currency: Optional[str] = None) -> dict:
        if not loan_id:
            return _refused(REASON_BAD_INPUT, f"no loan id supplied — cannot compute {self.name}")
        if self._registry is None:
            return _refused(REASON_DERIVE_FAILED,
                            f"{self.name}: no registry bound — cannot resolve inputs")
        input_envs = {}
        input_vals = {}
        for in_name in self.inputs:
            fig = self._registry.get(in_name)
            if fig is None:
                return _refused(REASON_DERIVE_FAILED,
                                f"{self.name}: input figure {in_name!r} not registered")
            env = fig.run(loan_id=loan_id, loan_name=loan_name, date=date)
            input_envs[in_name] = env
            if env.get("state") != STATE_DELIVERED:
                # propagate the input's terminal state (NO_LIVE_DATA stays NO_LIVE_DATA).
                if env.get("state") == STATE_NO_LIVE_DATA:
                    return _envelope(STATE_NO_LIVE_DATA, answer=None, values=[], gate_verdict=None,
                                     complete=False,
                                     refusals=[{"reason_code": STATE_NO_LIVE_DATA,
                                                "reason": (env.get("refusals") or [{}])[0]
                                                .get("reason", "no live data")}],
                                     meta={"figure": self.name, "loan_id": loan_id,
                                           "failed_input": in_name})
                inner = (env.get("refusals") or [{}])[0]
                return _refused(REASON_DERIVE_FAILED,
                                (f"{self.name}: input {in_name!r} did not deliver "
                                 f"({inner.get('reason_code')}): {inner.get('reason')}"),
                                meta={"figure": self.name, "loan_id": loan_id,
                                      "failed_input": in_name})
            input_vals[in_name] = env["values"][0]["value"]

        try:
            value = self._compute(input_vals)
        except ZeroDivisionError:
            return _refused(REASON_DERIVE_FAILED,
                            f"{self.name}: division by zero (a denominator input is 0) — refusing",
                            meta={"figure": self.name, "loan_id": loan_id, "inputs": input_vals})
        except Exception as e:  # noqa: BLE001
            return _refused(REASON_DERIVE_FAILED,
                            f"{self.name}: compute failed: {type(e).__name__}: {str(e)[:120]}",
                            meta={"figure": self.name, "loan_id": loan_id, "inputs": input_vals})

        # Per-input provenance is preserved verbatim (each input was already bound+verified).
        input_provenance = {n: input_envs[n]["values"][0].get("provenance")
                            for n in self.inputs}
        out_value = {
            "value": value,
            "currency": None,  # a ratio carries no currency
            "unit": self.unit,
            "provenance": {"derived": True, "formula": self.formula,
                           "inputs": input_provenance, "input_values": input_vals},
            "confidence": min((input_envs[n]["values"][0].get("confidence") or 0.7)
                              for n in self.inputs),
        }
        name_str = f" for {loan_name!r}" if loan_name else ""
        answer = (f"The {self.name}{name_str} (loan {loan_id}) is {value} "
                  f"({self.formula} = "
                  + " / ".join(str(input_vals[n]) for n in self.inputs) + ").")
        gate_verdict = {"outcome": "pass", "derived": True, "formula": self.formula}
        return _envelope(STATE_DELIVERED, answer=answer, values=[out_value],
                         gate_verdict=gate_verdict, complete=True, refusals=[],
                         meta={"figure": self.name, "loan_id": loan_id, "loan_name": loan_name,
                               "unit": self.unit, "formula": self.formula,
                               "inputs": input_vals, "input_provenance": input_provenance})


class LeverageFigure:
    """A leverage / coverage ratio (LTV / DSCR / debt_yield / cap_rate) computed by JOINING the
    Hypercore liability side to the OKOA knowledge-graph collateral side.

    Hypercore supplies the loan amounts (outstanding / commitment / rate); the KG supplies the
    collateral value + NOI that Hypercore cannot. Each ratio is computed from PRISM's definition
    (see planning/preeng/001-hypercore-ask/_prism-domain-learnings.md §1.3) and carries DUAL
    provenance — the Hypercore raw_response_id + json_field_path AND the KG node_id/field.

      metric        formula (PRISM)                              numerator src / denominator src
      ------------  -------------------------------------------  -------------------------------
      ltv           outstanding / appraised_value                Hypercore / KG
      debt_yield    NOI / loan_amount(commitment)                KG / Hypercore
      dscr          NOI / (loan_amount × interest_rate)          KG / Hypercore (I/O bridge)
      cap_rate      NOI / appraised_value                        KG / KG

    LTV additionally CROSS-CHECKS the KG's own stored `ltv_latest`: both are reported, and a
    divergence beyond LTV_CROSSCHECK_TOLERANCE is FLAGGED (not refused). Every ratio with a
    covenant compares to the PRISM threshold and flags a breach.

    REFUSAL DISCIPLINE: if the Hypercore side cannot be sourced (no loan / no live data) OR the
    KG side is absent (no confident node match, or the specific field — appraised_value / NOI —
    missing for this loan), the figure returns a CLEAN STRUCTURED REFUSAL naming the missing
    input. It NEVER fabricates a ratio. Confidence reflects dual-source AND the KG node's own
    confidence.
    """

    # metric -> (numerator_kind, denominator_kind) where each is a tag the compute step reads.
    #   "outstanding"  -> Hypercore summary.totalOutstanding.total
    #   "commitment"   -> Hypercore loan.commitment (PRISM loan_amount)
    #   "appraised"    -> KG appraised_value
    #   "noi"          -> KG NOI
    #   "debt_service" -> Hypercore commitment × KG/Hypercore interest_rate (annual I/O interest)
    _SPEC = {
        "ltv": {"num": "outstanding", "den": "appraised", "unit": "percent"},
        "debt_yield": {"num": "noi", "den": "commitment", "unit": "percent"},
        "dscr": {"num": "noi", "den": "debt_service", "unit": "ratio"},
        "cap_rate": {"num": "noi", "den": "appraised", "unit": "percent"},
    }

    def __init__(self, name: str, *, synonyms=(), unit: str = "percent",
                 covenant: Optional[dict] = None, description: str = "",
                 fetcher: Optional[LoanSummaryFetcher] = None,
                 cache=None, engine=None, kg_store=None):
        if name not in self._SPEC:
            raise ValueError(f"unknown leverage metric {name!r}")
        self.name = name
        self.synonyms = tuple(synonyms)
        self.unit = unit
        self.covenant = covenant
        self.description = description
        self._fetcher = fetcher or LoanSummaryFetcher(cache=cache)
        self._cachelib = _cache()
        self._provlib = _provenance()
        self._cache = cache or self._fetcher._cache
        self._engine = engine or self._provlib.ProvenanceEngine(cache=self._cache)
        self._kglib = _kg()
        # kg_store: an injectable hca_kg.KGStore (tests point it at a fixture CSV dir).
        self._kg_store = kg_store

    # --- KG access (injectable; defaults to the live read-only store) ------
    def _kg_lookup(self, loan_name: Optional[str]) -> Optional[dict]:
        if not loan_name:
            return None
        if self._kg_store is not None:
            return self._kg_store.lookup(loan_name)
        return self._kglib.kg_lookup(loan_name)

    # --- Hypercore side: fetch + provenance-bind a summary field -----------
    def _hypercore_value(self, loan_id: str, loan_name: Optional[str],
                         field_path: str) -> dict:
        """Fetch the loan summary, resolve `field_path`, and provenance-bind it.

        Returns {"ok":True,"value":..,"provenance":{raw_response_id,json_field_path,..},
        "currency":..,"row":..} or {"ok":False, "state":.., "reason_code":.., "reason":..}.
        """
        fetched = self._fetcher.fetch(loan_id, loan_name=loan_name)
        if not fetched.get("ok"):
            return {"ok": False, "state": fetched.get("state", STATE_REFUSED),
                    "reason_code": fetched.get("reason_code", REASON_FETCH_EMPTY),
                    "reason": fetched.get("reason", "loan summary fetch failed")}
        row = fetched["row"]
        rid = fetched["rid"]
        rel = _strip_loan_prefix(field_path)
        value = _walk_dotted(row, rel)
        if value is _ABSENT or not isinstance(value, (int, float)) or isinstance(value, bool):
            return {"ok": False, "state": STATE_REFUSED, "reason_code": REASON_FETCH_EMPTY,
                    "reason": (f"{self.name}: Hypercore field {field_path!r} absent/non-numeric "
                               "for this loan — refusing (never guess)")}
        tpath = _summary_path(field_path)
        prov = self._engine.bind_and_verify(
            value, {"raw_response_id": rid, "json_field_path": tpath},
            value_ref=f"loan.{loan_id}.{self.name}.{field_path}")
        if prov["outcome"] != self._provlib.VERIFIED:
            return {"ok": False, "state": STATE_REFUSED, "reason_code": REASON_PROVENANCE,
                    "reason": prov["reason"]}
        return {"ok": True, "value": float(value), "currency": row.get("currency"),
                "row": row,
                "provenance": {"source": "hypercore", "raw_response_id": rid,
                               "json_field_path": tpath, "operation": "loans",
                               "field_path": field_path,
                               "fetched_at": fetched.get("fetched_at")}}

    def fetch_verify(self, *, loan_id: Optional[str] = None, loan_name: Optional[str] = None,
                     date: Optional[str] = None, currency: Optional[str] = None) -> dict:
        spec = self._SPEC[self.name]
        meta_base = {"figure": self.name, "loan_id": loan_id, "loan_name": loan_name,
                     "unit": self.unit, "kind": "leverage", "covenant": self.covenant}

        if not loan_id:
            return _refused(REASON_BAD_INPUT,
                            f"{self.name}: no loan id supplied — cannot compute (a leverage "
                            "ratio needs a resolved Hypercore loan)", meta=dict(meta_base))

        # 1) KG side: join the loan name to its collateral facts (read-only).
        kg = self._kg_lookup(loan_name)
        if kg is None:
            return _envelope(
                STATE_REFUSED, answer=None, values=[], gate_verdict=None, complete=False,
                refusals=[{"reason_code": REASON_KG_NO_MATCH,
                           "reason": (f"{self.name} requires external data: no confident OKOA "
                                      f"knowledge graph match for loan {loan_name!r} — refusing "
                                      "rather than fabricating"),
                           "required_source": "OKOA knowledge graph (appraised_value / NOI)"}],
                meta={**meta_base, "kg_matched": False})

        # 2) Pull the KG inputs this metric needs; refuse cleanly if absent.
        appraised = kg.get("appraised_value")
        noi = kg.get("noi")
        kg_prov = kg.get("provenance") or {}

        def _kg_missing(field_label: str) -> dict:
            return _envelope(
                STATE_REFUSED, answer=None, values=[], gate_verdict=None, complete=False,
                refusals=[{"reason_code": REASON_KG_FIELD_MISSING,
                           "reason": (f"{self.name} requires external data: {field_label} not "
                                      f"found in the OKOA knowledge graph for loan {loan_name!r} "
                                      f"(matched node {kg.get('node_id')!r}) — refusing rather "
                                      "than fabricating"),
                           "required_source": f"OKOA knowledge graph ({field_label})"}],
                meta={**meta_base, "kg_matched": True, "kg_node_id": kg.get("node_id"),
                      "kg_confidence": kg.get("confidence")})

        # 3) Hypercore side (only fetched for metrics that need it).
        hc_outstanding = None
        hc_commitment = None
        if spec["num"] == "outstanding" or spec["den"] == "outstanding":
            hc_outstanding = self._hypercore_value(loan_id, loan_name,
                                                   "summary.totalOutstanding.total")
        if spec["den"] in ("commitment", "debt_service"):
            hc_commitment = self._hypercore_value(loan_id, loan_name, "loan.commitment")

        def _hc_failed(hc: dict) -> Optional[dict]:
            if hc is None or hc.get("ok"):
                return None
            if hc.get("state") == STATE_NO_LIVE_DATA:
                return _envelope(STATE_NO_LIVE_DATA, answer=None, values=[], gate_verdict=None,
                                 complete=False,
                                 refusals=[{"reason_code": STATE_NO_LIVE_DATA,
                                            "reason": hc.get("reason")}],
                                 meta=dict(meta_base))
            return _refused(hc.get("reason_code", REASON_FETCH_EMPTY),
                            hc.get("reason", "Hypercore fetch failed"), meta=dict(meta_base))

        for hc in (hc_outstanding, hc_commitment):
            failed = _hc_failed(hc)
            if failed is not None:
                return failed

        # 4) Assemble the numerator / denominator with their provenance.
        provenance_sources = []  # list of provenance dicts (for dual-source confidence)
        num = den = None
        num_prov = den_prov = None
        cur = currency or (hc_outstanding or {}).get("currency") or (hc_commitment or {}).get("currency")

        # numerator
        if spec["num"] == "outstanding":
            num = hc_outstanding["value"]; num_prov = hc_outstanding["provenance"]
        elif spec["num"] == "noi":
            if noi is None:
                return _kg_missing("NOI / net_operating_income")
            num = noi
            num_prov = {"source": "kg", **(kg_prov.get("noi") or
                        {"file": kg.get("kg_file"), "node_id": kg.get("node_id"), "field": "noi"})}

        # denominator
        if spec["den"] == "appraised":
            if appraised is None:
                return _kg_missing("appraised_value")
            den = appraised
            den_prov = {"source": "kg", **(kg_prov.get("appraised_value") or
                        {"file": kg.get("kg_file"), "node_id": kg.get("node_id"),
                         "field": "appraised_value"})}
        elif spec["den"] == "commitment":
            den = hc_commitment["value"]; den_prov = hc_commitment["provenance"]
        elif spec["den"] == "debt_service":
            # PRISM I/O bridge: annual debt service = loan_amount × interest_rate.
            rate = kg.get("interest_rate")
            rate_src = "kg"
            if rate is None:
                rate = (hc_commitment.get("row") or {}).get("annualInterestRate") if hc_commitment else None
                rate_src = "hypercore"
            if rate is None or not isinstance(rate, (int, float)) or isinstance(rate, bool) or rate <= 0:
                return _envelope(
                    STATE_REFUSED, answer=None, values=[], gate_verdict=None, complete=False,
                    refusals=[{"reason_code": REASON_KG_FIELD_MISSING,
                               "reason": (f"{self.name} requires an interest rate to derive "
                                          f"annual debt service for loan {loan_name!r} — not "
                                          "found in the KG or Hypercore; refusing"),
                               "required_source": "interest rate (KG or Hypercore)"}],
                    meta={**meta_base, "kg_matched": True, "kg_node_id": kg.get("node_id")})
            commit = hc_commitment["value"]
            den = commit * float(rate)
            den_prov = {"source": "derived",
                        "formula": "annual_debt_service = commitment * interest_rate",
                        "commitment": hc_commitment["provenance"],
                        "interest_rate": {"source": rate_src, "value": float(rate)}}

        if num_prov:
            provenance_sources.append(num_prov)
        if den_prov:
            provenance_sources.append(den_prov)

        # 5) Compute the ratio (guard div-by-zero).
        if den == 0:
            return _refused(REASON_DERIVE_FAILED,
                            f"{self.name}: denominator is zero — refusing (cannot divide)",
                            meta={**meta_base, "kg_node_id": kg.get("node_id")})
        value = round(num / den, 6)

        # 6) Covenant breach flag (compare to the PRISM threshold).
        breach = self._covenant_breach(value)

        # 7) LTV cross-check against the KG's own stored ltv_latest.
        crosscheck = None
        if self.name == "ltv" and kg.get("ltv_latest") is not None:
            ltv_latest = float(kg["ltv_latest"])
            divergence = round(abs(value - ltv_latest), 6)
            crosscheck = {
                "kg_ltv_latest": ltv_latest,
                "computed_ltv": value,
                "divergence": divergence,
                "tolerance": LTV_CROSSCHECK_TOLERANCE,
                "diverges": divergence > LTV_CROSSCHECK_TOLERANCE,
                "ltv_latest_provenance": {"source": "kg", **(kg_prov.get("ltv_latest") or
                    {"file": kg.get("kg_file"), "node_id": kg.get("node_id"),
                     "field": "ltv_latest"})},
            }

        # 8) Confidence: dual-source (>=2 distinct sources) is NOT single-source-capped, but it is
        #    bounded by the KG node's own confidence (a 0.85-confidence appraisal can't yield a
        #    1.0-confidence ratio). cap_rate is KG-only (single source for value) -> capped.
        distinct_sources = {p.get("source") for p in provenance_sources}
        kg_conf = kg.get("confidence")
        source_count = 2 if ({"hypercore", "kg"} <= distinct_sources or
                             ("derived" in distinct_sources and "kg" in distinct_sources)) else 1
        agreement = kg_conf if isinstance(kg_conf, (int, float)) else None
        conf_rec = self._engine.confidence_record(
            f"loan.{loan_id}.{self.name}", source_count=source_count, agreement=agreement,
            basis=(f"{self.name}: dual-source (Hypercore + OKOA KG node "
                   f"{kg.get('node_id')!r}, conf={kg_conf})"))

        out_value = {
            "value": value,
            "currency": None,  # a ratio carries no currency
            "unit": self.unit,
            "provenance": {"derived": True, "metric": self.name,
                           "numerator": num_prov, "denominator": den_prov,
                           "numerator_value": num, "denominator_value": den,
                           "sources": sorted(s for s in distinct_sources if s)},
            "confidence": conf_rec["confidence"],
        }
        gate_verdict = {"outcome": "pass", "metric": self.name, "value": value,
                        "dual_source": source_count >= 2}
        if self.covenant:
            gate_verdict["covenant"] = self.covenant
            gate_verdict["breach"] = breach
        if crosscheck:
            gate_verdict["ltv_crosscheck"] = crosscheck

        name_str = f" for {loan_name!r}" if loan_name else ""
        pct = f" ({round(value * 100, 2)}%)" if self.unit == "percent" else ""
        answer = (f"The {self.name}{name_str} (loan {loan_id}) is {value}{pct} "
                  f"[{num} / {den}].")
        if breach and breach.get("breached"):
            answer += (f" COVENANT BREACH: {self.name} {value} "
                       f"{'>' if breach['direction'] == 'max' else '<'} "
                       f"{breach['threshold']} ({self.covenant.get('basis')}).")
        if crosscheck and crosscheck.get("diverges"):
            answer += (f" CROSS-CHECK DIVERGENCE: computed LTV {value} vs KG ltv_latest "
                       f"{crosscheck['kg_ltv_latest']} (gap {crosscheck['divergence']} > "
                       f"{crosscheck['tolerance']}).")

        meta = {**meta_base, "kg_matched": True, "kg_node_id": kg.get("node_id"),
                "kg_confidence": kg_conf, "kg_verification_status": kg.get("verification_status"),
                "numerator": num, "denominator": den,
                "numerator_source": spec["num"], "denominator_source": spec["den"],
                "covenant_breach": breach, "ltv_crosscheck": crosscheck,
                "confidence_record": conf_rec, "dual_provenance": provenance_sources}
        return _envelope(STATE_DELIVERED, answer=answer, values=[out_value],
                         gate_verdict=gate_verdict, complete=True, refusals=[], meta=meta)

    def _covenant_breach(self, value: float) -> Optional[dict]:
        """Compare the computed ratio to the PRISM covenant threshold. Returns a breach record
        ({threshold, direction, breached, basis}) or None when the metric has no covenant."""
        if not self.covenant:
            return None
        threshold = self.covenant.get("threshold")
        direction = self.covenant.get("direction")
        if threshold is None or direction not in ("max", "min"):
            return None
        breached = (value > threshold) if direction == "max" else (value < threshold)
        return {"threshold": threshold, "direction": direction, "breached": bool(breached),
                "value": value, "basis": self.covenant.get("basis")}


# ---------------------------------------------------------------------------
# Registry construction (the seed + the native + derived + requires-external figures)
# ---------------------------------------------------------------------------

# (logical name, source field path, unit, synonyms, optional reconcile component tuple)
_NATIVE_FIGURE_SPECS = (
    ("outstanding_balance", "summary.totalOutstanding.total", "currency",
     ("outstanding", "total outstanding", "current balance", "balance"),
     # capitalizedBalance IS part of the additive totalOutstanding identity and is fetched in
     # _SUMMARY_SELECTION; including it here means a NON-ZERO capitalizedBalance reconciles
     # cleanly (its omission would cause a FALSE RECONCILE_FAILED refusal). Fixtures pin it 0.0,
     # so summing it in is a no-op for the existing suite (zero contribution).
     ("principal", "interest", "compoundingInterest", "totalFees", "totalPenalties",
      "capitalizedBalance")),
    ("principal_outstanding", "summary.totalOutstanding.principal", "currency",
     ("principal", "outstanding principal"), None),
    ("accrued_interest", "summary.totalOutstanding.interest", "currency",
     ("interest", "accrued interest"), None),
    ("default_interest", "summary.totalOutstanding.totalPenalties", "currency",
     ("penalties", "default interest", "penalty interest"), None),
    ("amount_due_today", "summary.totalDue.total", "currency",
     ("amount due", "total due", "due today"), None),
    ("overdue_amount", "summary.overdue.total", "currency",
     ("overdue", "past due", "arrears"), None),
    ("commitment", "loan.commitment", "currency",
     ("loan amount", "loan size", "committed", "face amount"), None),
    ("total_disbursed", "summary.totalDisbursed", "currency",
     ("disbursed", "drawn", "total drawn", "funded", "advanced"), None),
    ("maturity_date", "loan.scheduleEndDate", "date",
     ("maturity", "due date", "balloon date", "end date", "loan end date"), None),
)

# leverage / coverage figures (LTV / DSCR / debt yield / cap rate) — now KG-JOINED (SLICE-HCA-14).
# PRISM covenant thresholds (LTV 75% max, DSCR 1.25x min, Debt Yield 8% min) drive breach flags.
_LEVERAGE_SPECS = (
    ("ltv", "percent",
     ("loan to value", "loan-to-value", "ltv ratio"),
     {"threshold": 0.75, "direction": "max", "basis": "PRISM bridge-loan max_ltv (OKOA 75%)"}),
    ("dscr", "ratio",
     ("debt service coverage", "debt service coverage ratio", "debt coverage ratio"),
     {"threshold": 1.25, "direction": "min", "basis": "PRISM bridge-loan min_dscr (1.25x)"}),
    ("debt_yield", "percent",
     ("debt yield", "dy"),
     {"threshold": 0.08, "direction": "min", "basis": "PRISM bridge-loan min_debt_yield (8%)"}),
    ("cap_rate", "percent",
     ("cap rate", "capitalization rate"),
     None),
)


def build_registry(*, client=None, cache=None, engine=None,
                   sleep: Callable[[float], None] = time.sleep,
                   retry_attempts: int = RETRY_ATTEMPTS,
                   summary_client=None, kg_store=None) -> FigureRegistry:
    """Build the figures registry: the payoff figure + the Hypercore-native figures + the
    derived utilization figure + the KG-joined leverage (LTV/DSCR/debt_yield/cap_rate) figures.

    All figures share the injected client/cache/engine so they read through ONE Tier-1 cache
    (checkpointable / resumable) and so tests can inject a fake client + a temp cache.

    `summary_client` (optional) is the GraphQL client the native figures use for the
    loans+summary query; it defaults to `client` (the same live client serves both paths).
    `kg_store` (optional) is an hca_kg.KGStore the leverage figures join against (tests point it
    at a synthetic fixture CSV dir); it defaults to the live read-only KG.
    """
    reg = FigureRegistry()

    # 1) Payoff / early-redemption figure (now fetches the loan currency before computing —
    #    so its value carries currency=loan.currency, per the slice-A polish item).
    payoff = PayoffFigure(client=client, cache=cache, engine=engine,
                          sleep=sleep, retry_attempts=retry_attempts)
    summary_fetcher = LoanSummaryFetcher(
        client=summary_client if summary_client is not None else client,
        cache=cache, retry_attempts=retry_attempts, sleep=sleep)
    payoff.attach_summary_fetcher(summary_fetcher)
    reg.register(Figure(
        PayoffFigure.NAME, synonyms=PayoffFigure.SYNONYMS, kind=KIND_DERIVED,
        fetch_verify=payoff.fetch_verify,
        description=("verified early-redemption payoff as of a date — "
                     "getLoanRepaymentDistribution.total, reconciled to its components, "
                     "currency from loan.currency"),
    ))

    # 2) Hypercore-native figures (LoanSummary reads; share one fetcher so a report fetches once).
    for name, fpath, unit, syns, recon in _NATIVE_FIGURE_SPECS:
        nf = NativeFigure(name, field_path=fpath, unit=unit, synonyms=syns,
                          fetcher=summary_fetcher, cache=cache, engine=engine,
                          reconcile_components=recon,
                          description=f"Hypercore-native {name} ({fpath})")
        reg.register(Figure(name, synonyms=syns,
                            kind=KIND_DIRECT, fetch_verify=nf.fetch_verify,
                            description=nf.description))

    # 3) Derived utilization = total_disbursed / commitment (transparent; shows inputs).
    #    Synonyms sourced from the shared vocabulary leaf (single source; "utilization" itself
    #    is the figure NAME and already matches via Figure.matches, so including it is harmless).
    util = DerivedFigure(
        "utilization", formula="total_disbursed / commitment",
        inputs=("total_disbursed", "commitment"),
        compute=lambda v: round(v["total_disbursed"] / v["commitment"], 6),
        unit="ratio",
        synonyms=_vocab().UTILIZATION_TERMS,
        description="derived utilization = total_disbursed / commitment (inputs shown)",
        registry=reg, cache=cache, engine=engine)
    reg.register(Figure("utilization", synonyms=util.synonyms, kind=KIND_DERIVED,
                        fetch_verify=util.fetch_verify, description=util.description))

    # 4) leverage / coverage figures — KG-JOINED (SLICE-HCA-14). Compute the ratio from Hypercore
    #    amounts + KG collateral value/NOI with DUAL provenance; refuse cleanly (never fabricate)
    #    when the KG input is absent for the loan. Share the SAME summary fetcher (one loan fetch).
    for name, unit, syns, covenant in _LEVERAGE_SPECS:
        lf = LeverageFigure(name, synonyms=syns, unit=unit, covenant=covenant,
                            fetcher=summary_fetcher, cache=cache, engine=engine,
                            kg_store=kg_store,
                            description=f"{name} — Hypercore × OKOA-KG join")
        # Keep the registered KIND as requires_external so the planner still routes it down the
        # KG-aware path (and existing intent classification is unchanged); the figure now COMPUTES.
        reg.register(Figure(name, synonyms=syns, kind=KIND_REQUIRES_EXTERNAL,
                            fetch_verify=lf.fetch_verify, description=lf.description))

    return reg


# ---------------------------------------------------------------------------
# Module-level convenience
# ---------------------------------------------------------------------------

def payoff_as_of(loan_id: str, *, date: Optional[str] = None, client=None, cache=None,
                 engine=None, loan_name: Optional[str] = None,
                 currency: Optional[str] = None,
                 sleep: Callable[[float], None] = time.sleep,
                 retry_attempts: int = RETRY_ATTEMPTS) -> dict:
    """One-shot: compute the early-redemption payoff figure for a loan id + date."""
    fig = PayoffFigure(client=client, cache=cache, engine=engine, currency=currency,
                       sleep=sleep, retry_attempts=retry_attempts)
    return fig.fetch_verify(loan_id=loan_id, date=date, loan_name=loan_name,
                            currency=currency)


# ---------------------------------------------------------------------------
# CLI — `--loan-id <id> [--date YYYY-MM-DD]`. Prints the figure envelope as JSON.
# Loan-level money totals/components are portfolio figures (not borrower PII), safe to print.
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="acos-hypercore-ask figures — early-redemption payoff as of a date.")
    parser.add_argument("--loan-id", dest="loan_id", required=True,
                        help="resolved Hypercore loan id (use hca-resolve.py to resolve a name)")
    parser.add_argument("--date", dest="date", default=None,
                        help="as-of date YYYY-MM-DD (default: today UTC)")
    parser.add_argument("--currency", dest="currency", default=None,
                        help="currency label to attach to the figure (optional)")
    args = parser.parse_args(argv)

    env = payoff_as_of(args.loan_id, date=args.date, currency=args.currency)
    print(json.dumps(env, indent=2, default=str))
    return 0 if env.get("state") == STATE_DELIVERED else 1


if __name__ == "__main__":
    sys.exit(main())
