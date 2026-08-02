# S19-ast-validator-quarantine-and-reverification — AST-resolving validator, quarantine, deterministic re-verification and substitution

| Field | Value |
|---|---|
| Epic / Story | E5 / ST-06 |
| Type · MoSCoW · Size | build · MUST · L `[I]` |
| Phase / Demo | Phase 1 / — |
| Depends on | S18-import-parser-and-envelope-validation |
| Requirements | FR-052, FR-053, FR-054, FR-055, FR-057 |
| Acceptance criteria | A9 · A10 · A11 · §12.17-A101 · SL-S19-1 |
| CQ / evidence | CQ13 · CQ8 |
| Note | **NA-B06** — the carried requirement reads as a substring denylist; the source explicitly rejects that as insufficient. This slice implements the AST design |

## PM — slice definition

**Objective.** Treat the paste as untrusted input: resolve bindings through an AST with scope tracking, fail closed on anything undecidable, and independently re-verify every claimed contrast pair and font.

**In scope.** Component splitting by the substrate's compiler; a real ESTree parser for scripts and a real CSS parser for styles; **resolution-based** denial (not spelling-based); fail-closed quarantine for computed member access on globals, dynamic import specifiers, constructor chains, assembled-then-called strings, and non-literal URL-bearing attributes; template/CSS quarantine for remote script, link, import, url(), inline handlers, javascript: URLs, frame/object/embed elements and srcdoc; token schema validation; sandboxed first render under a policy with no network connect permission; per-item human accept; contrast recompute with auto-nudge and substitution logging; font substitution to the nearest same-classification open-licensed match; template-version range check with a defined upgrade path; the anti-slop lint as a **hard gate upstream** on the generated design-system JSON.

**Out of scope.** Being a sandbox-escape-proof boundary — this is a mistake-catcher and tamper-detector, and the slice must say so. Local Regeneration Mode (S20).

**Allowed files / contexts.**
- `scripts/lib/import-validator.ts`, `scripts/lib/contrast.ts`, `scripts/lib/font-substitute.ts`, `scripts/lib/antislop.ts`, `inbound/import-report.json` (write), quarantine area under the session.

**Steps.**
1. Parse every imported artifact with a real parser; a parse failure is a **quarantine**, never a pass-through.
2. Walk the AST with scope tracking; flag calls whose callee **resolves** to a denied binding.
3. Fail closed on the undecidable set; record each with its offending snippet.
4. Quarantine every remote origin in template and CSS — a remote origin is simultaneously a determinism and a licence-evidence violation.
5. Validate tokens as a schema; reject unknown types and non-literal values.
6. Render quarantined and newly accepted items first in a sandboxed frame with no network permission.
7. Recompute every claimed contrast pair; auto-nudge failures; log every substitution.
8. Substitute any font not on the pinned shortlist with the nearest same-classification open-licensed match; log it.
9. Check the template version against the supported range; apply the defined upgrade path or refuse.
10. Run the anti-slop lint as a hard gate on the design-system JSON **before the human sees any menu of choices**.

**Definition of Done.**
- Artifacts: validator, contrast module, substitution module, anti-slop gate, `import-report.json` with per-item status, reason and snippet.
- Validation: the obfuscated-call fixture is quarantined; a parse-failure fixture is quarantined; a false contrast claim is caught by recomputation; an off-shortlist font is substituted and logged.
- `slice.yaml` mapping — `acceptance_criteria: [A9, A10, A11, "§12.17-A101", SL-S19-1]`, `verification_method: exit-code` (A10: `recompute`).

## Dev — execution contract

Evidence bundle: (1) summary; (2) traceability FR-052…FR-057 → file:line; (3) structural quality — one validator module, one report writer; (4) functional testing — four fixtures (literal denied call, obfuscated denied call, parse failure, remote font URL) with recorded outcomes; (5) security/compliance — **state the honest limit explicitly**: the realistic threat is a mistake or an injected insertion, not a determined attacker; this is not a sandbox; (6) operational — the "retry just these three" repair-prompt flow, which is a functional requirement because partial paste-backs will happen on most runs; (7) self-assessment.

## QA — zero-trust verification

- **Write your own** obfuscated-call fixture (string concatenation and bracket access) and confirm quarantine.
- **Recompute two contrast pairs yourself** from the imported values; a logged "pass" you cannot reproduce is a rejection.
- **Grep the accepted output** for any remote origin; one hit is a rejection.
- **Confirm the anti-slop gate ran before** the selection menu, not after — order is the requirement.
- **Reject** if the security section claims the validator is a sandbox.

## Dev Learnings

_Not Done until filled. Required: what the AST caught that a substring filter would have missed, and the false-quarantine rate on real payloads._

## QA Learnings

_Not Done until filled. Required: which undecidable case was hardest to fail closed on without making ingest unusable._
