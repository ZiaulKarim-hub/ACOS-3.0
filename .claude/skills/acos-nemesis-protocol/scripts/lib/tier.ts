/**
 * tier.ts — which findings may stop the work, and which are merely owed.
 *
 * WHY THIS EXISTS. `laneOf` answers WHO repairs a finding (the machine, or Zee). It does
 * not answer WHETHER a finding should hold the whole project still, and until now nothing
 * did: every open finding blocked completion, at every severity. Measured on
 * website-design-okoa/v2 on 2026-11-18, that rule produced a list that cannot be emptied —
 * 2,085 findings filed, 1,128 closed, and the open count pinned between 950 and 981 for
 * ten days because each fix is itself judged and files more. 957 were open at the time of
 * measurement; 950 of them carried the FUNCTIONALITY label and 7 the SECURITY one.
 *
 * Zee's instruction, 2026-11-18: Nemesis keeps working exactly as it does now on security
 * findings "and other important issues like anything that breaks the system being built or
 * causes goal achievement to fail". Everything else is still owed, still repaired, and no
 * longer blocks.
 *
 * THE LABEL IS NOT THE KEY, AND THAT IS THE WHOLE TRAP. The obvious implementation sorts
 * on `lens`. Measured over the same 957: 105 findings carry `lens: "PFC"` while citing a
 * rule from the SECURITY checklists (3.1 to 3.14), and only 5 carry `lens: "PSC"` together
 * with a security rule. Sorting on the label alone would therefore have swept 105 real
 * security findings into the tier that no longer blocks — the exact opposite of the ask.
 * So the RULE NUMBER decides, and the label is treated as a second opinion that can only
 * ever raise the tier, never lower it.
 */
import type { Issue } from "./state.ts";

/**
 * blocking — holds the release, exactly as every finding did before this file existed.
 * backlog  — still open, still repaired, never blocks.
 * disputed — the two signals disagree, so it BLOCKS until three readers say otherwise.
 */
export type Tier = "blocking" | "backlog" | "disputed";

/** The fourteen security checklists are numbered 3.1 to 3.14, with optional sub-parts. */
const SECURITY_RULE = /^3\.\d+/;

/**
 * Rules that describe something ALREADY BROKEN rather than something imperfect.
 *
 * PFC-c is "nothing broke — does the chunk change a contract a caller or test depends on";
 * PFC-e is "no new defect — off-by-one, wrong null handling, swallowed error, race". Both
 * are Zee's "breaks the system being built", so both keep blocking.
 *
 * PFC-a ("does it do what the plan says") and PFC-d ("no drift") are deliberately NOT here.
 * They were 446 and 119 of the 957, the two largest categories by a wide margin, and they
 * are overwhelmingly where the wording-and-comment findings live. Zee was asked directly
 * whether PFC-a should keep blocking and chose the line that leaves it out.
 */
const BREAKS_SOMETHING = new Set(["PFC-c", "PFC-e"]);

/** A scan check that actually FAILED is observed breakage, not a prediction about it. */
const FAILED_CHECK_STEPS = new Set(["S3"]);

/** Steps that are purely Nemesis's own paperwork about its own process. */
const PAPERWORK_STEPS = new Set(["S0", "S1", "S2", "S5", "S6", "S7", "S8"]);

/** Rules that are about the plan rather than about something broken. */
const PLAN_RULES = new Set(["PFC-a", "PFC-d"]);

const rule = (i: Issue): string => String(i.checklist ?? "").trim();

/** Does this finding cite one of the fourteen security checklists? */
export function citesSecurityRule(i: Issue): boolean {
  return SECURITY_RULE.test(rule(i));
}

/**
 * Do the finding's two signals — its lens LABEL and the RULE it cites — disagree?
 *
 * Both directions count, and both end up blocking, for different reasons. A finding
 * labelled functionality that cites a security rule is one of the 105 the label would have
 * lost; a finding labelled security that cites no security rule may be a real security
 * concern filed under the wrong number. Neither is safe to demote without a reader.
 */
export function signalsDisagree(i: Issue): boolean {
  return citesSecurityRule(i) !== (i.lens === "PSC");
}

/**
 * A tier recorded by a confirmed three-reader vote, or null.
 *
 * AN OVERRIDE IS ONLY HONOURED WITH ITS EVIDENCE ATTACHED. The field alone proves nothing:
 * anything that can write the issue file can write a tier, and "trust the field" would make
 * the whole sort a single edit away from meaningless. So the votes must be present, and at
 * least two of them must name the tier being claimed. Fewer than two agreeing is not a
 * quiet failure — it is ignored, and the mechanical sort stands.
 */
export function confirmedOverride(i: Issue): Tier | null {
  const claimed = (i as { tier_override?: unknown }).tier_override;
  if (claimed !== "blocking" && claimed !== "backlog") return null;
  const votes = (i as { tier_votes?: unknown }).tier_votes;
  if (!Array.isArray(votes)) return null;
  const agreeing = votes.filter((v) => v === claimed).length;
  return agreeing >= 2 ? (claimed as Tier) : null;
}

/**
 * which tier does this finding belong to?
 *
 * The order is the argument, so it is written down rather than left to be inferred:
 *
 * 1. A confirmed vote wins, because three readers beat one rule.
 * 2. `critical` blocks whatever rule it cites. A critical finding that nobody can name a
 *    rule for is still critical.
 * 3. Disagreeing signals block, pending a vote. This is the 105, and it is the case the
 *    label-based sort got wrong.
 * 4. A security rule blocks.
 * 5. Observed breakage blocks — a failed check, a broken caller, a new defect.
 * 6. Plan rules and paperwork steps do not block.
 * 7. Anything UNRECOGNISED is disputed, therefore blocks. A rule this file has never seen
 *    is not evidence that the finding is minor; it is evidence that this file is out of
 *    date, and the safe reading of "I do not know" is "do not demote it".
 */
export function tierOf(i: Issue): Tier {
  const confirmed = confirmedOverride(i);
  if (confirmed) return confirmed;

  if (String(i.severity) === "critical") return "blocking";
  if (signalsDisagree(i)) return "disputed";
  if (citesSecurityRule(i)) return "blocking";

  const r = rule(i);
  if (BREAKS_SOMETHING.has(r)) return "blocking";
  if (FAILED_CHECK_STEPS.has(r)) return "blocking";
  if (PLAN_RULES.has(r) || PAPERWORK_STEPS.has(r)) return "backlog";

  return "disputed";
}

/**
 * Does this finding hold the release?
 *
 * `disputed` blocks. That is the asymmetry the whole design rests on: being too careful
 * costs a repair that was not urgent, while being too relaxed ships the thing Nemesis was
 * built to catch.
 */
export function blocks(i: Issue): boolean {
  return tierOf(i) !== "backlog";
}

/** Counts for a report line, so a reader never has to recompute the split by hand. */
export function tierCounts(issues: Issue[]): Record<Tier, number> {
  const out: Record<Tier, number> = { blocking: 0, backlog: 0, disputed: 0 };
  for (const i of issues) out[tierOf(i)] += 1;
  return out;
}
