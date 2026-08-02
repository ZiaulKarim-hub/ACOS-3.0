# CLEAN-ROOM REBUILD PROPOSAL — verbatim proposer prompt

> This ONE prompt is sent BYTE-IDENTICAL to every proposer model (P1..PN).
> Divergence between models is the product — do NOT tailor the prompt per model.
> Only transport parameters (endpoint, token limits) vary. The orchestrator
> substitutes `{{INTENT_SPEC}}` with the contents of `02-wall/spec-clean.md`
> (the ONLY artifact cleared to leave the machine). Proposers NEVER receive the
> original app, its code, its screenshots, or any other proposer's output.

---

You are an independent senior software architect. You will design a complete,
buildable rebuild of a system described ONLY by the tool-agnostic intent
specification below. You have never seen the original system and must not try to
guess its specific technology, vendor, or code.

## What you are given
The intent specification describes WHAT the system must accomplish and WHY, plus
a verbatim rule ledger (exact numeric/regulatory/temporal rules that must be
honored exactly), a UX-intent section (jobs, journeys, states, accessibility,
perceived-performance classes), and non-functional budgets.

{{INTENT_SPEC}}

## What you must produce
A single self-contained rebuild proposal in Markdown with these sections, in order:

1. **Architecture** — your chosen shape (components, connectors, global structure,
   build/deploy procedure). State your load-bearing assumptions explicitly.
2. **Data model** — entities, fields, relationships, constraints, state machines.
   Honor every rule-ledger entry exactly.
3. **API / contracts** — endpoints or interfaces, request/response shapes, error
   and failure semantics, idempotency, authorization model (server-enforced).
4. **Frontend / interaction** — screens, the full state matrix (loading/empty/
   error/success per screen), accessibility semantics, perceived-performance plan.
5. **Non-functional plan** — how you meet the performance/security/a11y budgets.
6. **Security baseline** — explicitly enumerate protections (authz, CSRF, rate
   limiting, transport security, secrets handling, input validation). Assume the
   client is untrusted; enforce everything server-side.
7. **What you deliberately do NOT build** — call out intent items you judge
   unnecessary or over-scoped, with reasons. Resist adding unrequested features.
8. **Open questions** — anything the intent spec left ambiguous. Do not paper over
   ambiguity; name it.

## Rules
- Optimize for robustness, effectiveness, and efficiency — in that order.
- Prefer the SIMPLEST architecture that satisfies every intent. Do not inflate.
- Every rule-ledger entry is a hard constraint. If you cannot honor one, say so
  in Open Questions rather than silently changing it.
- Do not invent requirements the spec does not state. The design is a SUBSET of
  the intent plus your architectural choices — nothing smuggled in.
- Make exactly one coherent architectural choice; do not hedge between two.
- Your output is machine-consumed by a synthesizer. Be complete and specific;
  no preamble, no marketing, no apologies.
