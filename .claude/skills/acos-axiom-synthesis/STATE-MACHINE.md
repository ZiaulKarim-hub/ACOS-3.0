# Claim-State State Machine (acos-axiom-synthesis)

The formal contract for a claim's `state` field. The only writer is
`scripts/ledger_writer.py` → `axiom_ledger.append_claim`; the only reader-for-
scheduling is `scripts/next_claims.py` → `axiom_ledger.compute_frontier`.

**This document is the authority when prose and code disagree.** Its executable
form is `LEGAL_TRANSITIONS` + `validate_invariants` in `scripts/axiom_ledger.py`;
those two must stay identical to what is written here.

## States

| state | meaning |
|-------|---------|
| `CONJECTURE` | a guess — one source, not yet cross-checked. The initial state of every claim. |
| `CORROBORATED` | survived ≥1 independent check and passed the falsification gate; not refuted. |
| `ESTABLISHED` | multi-source convergence; defends all attackers; passed the falsification gate. Terminal-until-reopened, but always defeasible. |
| `CONTESTED` | a comparably-supported contradiction exists. |
| `SUPERSEDED` | displaced by a better-supported claim (archived, not deleted). |
| `REFUTED` | directly contradicted by stronger evidence with no defense (archived, not deleted). |

Every claim enters as `CONJECTURE`. Superseded/refuted versions stay on disk and
are **revivable** if their refuter is itself later refuted.

## Legal transitions

`None` = create (claim not yet in the ledger). A same-state → same-state write is
always legal (a metadata/provenance update). No transition outside this table is
writable — `append_claim` refuses it with **exit 4**.

```
CREATE        → CONJECTURE
CONJECTURE    → CONJECTURE | CORROBORATED | CONTESTED | SUPERSEDED | REFUTED
CORROBORATED  → CORROBORATED | ESTABLISHED | CONTESTED | SUPERSEDED | REFUTED
ESTABLISHED   → ESTABLISHED | CONTESTED | SUPERSEDED | REFUTED
CONTESTED     → CONTESTED | CORROBORATED | ESTABLISHED | SUPERSEDED | REFUTED
SUPERSEDED    → SUPERSEDED | CONTESTED | CORROBORATED           (revival)
REFUTED       → REFUTED | CONTESTED | CORROBORATED              (revival)
```

Notes:
- The happy path is `CONJECTURE → CORROBORATED → ESTABLISHED`; you **cannot** jump
  `CONJECTURE → ESTABLISHED` (must pass through `CORROBORATED`).
- Demotions go to `CONTESTED` (an active fight), or `SUPERSEDED` / `REFUTED`
  (settled against the claim).
- Revival re-enters at `CORROBORATED` (or `CONTESTED`), never straight to
  `ESTABLISHED` — a revived claim must re-earn establishment.

## The hard invariants (enforced in code, refuse with exit 3)

Checked on every write, regardless of transition legality:

1. **Corroboration gate.** `state == ESTABLISHED` OR `confidence == "verified"`
   requires `confidence_basis.independent_sources ≥ 2` AND ≥2 **distinct source
   families** in `provenance`. (Correlated same-family agreement is not corroboration.)
2. **Single-source cap.** A single-source claim can never be `verified` — it caps at
   `probable`. (Subsumed by (1), stated explicitly.)
3. **Falsification gate.** Promotion to `CORROBORATED` or `ESTABLISHED` requires
   `gates.falsification == "passed"`. A claim cannot rise above `CONJECTURE` until it
   has survived the Stage-5 falsification gate.
4. **Dependency integrity.** A claim cannot be `ESTABLISHED` while any `depends_on`
   claim's current state is `REFUTED`.

## Frontier rules (`compute_frontier`)

Computed purely from on-disk state, so the run is resumable by re-reading the ledger:

- `CONTESTED` → **needs_conflict_resolution**
- `CONJECTURE`, falsification not passed → **needs_falsification**
- `CONJECTURE`, falsification passed → **needs_corroboration**
- `CORROBORATED` with ≥2 independent sources → **needs_corroboration** (promotion candidate)
- `CORROBORATED` otherwise, `ESTABLISHED` → **settled**
- `SUPERSEDED`, `REFUTED` → **terminal**
- `done` ⇔ nothing needs falsification, corroboration, or conflict-resolution.
