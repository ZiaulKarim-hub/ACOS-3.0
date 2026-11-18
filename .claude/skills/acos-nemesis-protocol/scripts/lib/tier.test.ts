/**
 * tier.test.ts — the sort that decides what may stop the work.
 *
 * Every row here is built from a shape measured on the live ledger of
 * website-design-okoa/v2 on 2026-11-18, not from an invented example. The one that matters
 * most is the 105: findings labelled FUNCTIONALITY that cite a SECURITY rule. A sort on the
 * label would hand all 105 to the tier that no longer blocks, which is the precise failure
 * this file exists to prevent.
 */
import { describe, expect, it } from "bun:test";
import { tierCounts, tierOf, blocks, citesSecurityRule, confirmedOverride, signalsDisagree } from "./tier.ts";
import type { Issue } from "./state.ts";

/** The smallest thing the sort will accept; every row overrides only what it is about. */
function finding(over: Partial<Issue> & Record<string, unknown> = {}): Issue {
  return {
    id: "FUN-1", lens: "PFC", checklist: "PFC-a", severity: "medium",
    status: "open", what: "", where: "", rung: 1,
    ...over,
  } as unknown as Issue;
}

describe("the rule number decides, never the label (the 105)", () => {
  it("keeps a finding labelled functionality that cites a security rule", () => {
    // FUN-1120 on the live ledger: lens PFC, checklist 3.14.
    const i = finding({ id: "FUN-1120", lens: "PFC", checklist: "3.14" });
    expect(citesSecurityRule(i)).toBe(true);
    expect(signalsDisagree(i)).toBe(true);
    expect(tierOf(i)).toBe("disputed");
    expect(blocks(i)).toBe(true);
  });

  it("keeps a finding labelled security that cites no security rule", () => {
    // The other direction, 2 findings on the live ledger: lens PSC on a gate step.
    const i = finding({ lens: "PSC", checklist: "S7" });
    expect(signalsDisagree(i)).toBe(true);
    expect(blocks(i)).toBe(true);
  });

  it("blocks on a security rule when the two signals agree", () => {
    expect(tierOf(finding({ lens: "PSC", checklist: "3.4" }))).toBe("blocking");
  });

  it("recognises every one of the fourteen security checklists, including the two-digit ones", () => {
    for (const n of [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]) {
      // 3.10 to 3.14 are the ones a single-digit pattern would silently miss.
      expect(citesSecurityRule(finding({ checklist: `3.${n}` }))).toBe(true);
    }
    expect(citesSecurityRule(finding({ checklist: "3.4.1" }))).toBe(true);
  });
});

describe("breakage blocks; the plan and the paperwork do not", () => {
  it("blocks when a caller or test depends on what changed", () => {
    expect(tierOf(finding({ checklist: "PFC-c" }))).toBe("blocking");
  });

  it("blocks on a newly introduced defect", () => {
    expect(tierOf(finding({ checklist: "PFC-e" }))).toBe("blocking");
  });

  it("blocks when a scan check actually failed", () => {
    expect(tierOf(finding({ checklist: "S3" }))).toBe("blocking");
  });

  it("does NOT block on the two plan rules, which were 446 and 119 of the 957", () => {
    expect(tierOf(finding({ checklist: "PFC-a" }))).toBe("backlog");
    expect(tierOf(finding({ checklist: "PFC-d" }))).toBe("backlog");
    expect(blocks(finding({ checklist: "PFC-a" }))).toBe(false);
  });

  it("does NOT block on Nemesis's own paperwork steps", () => {
    for (const s of ["S0", "S1", "S2", "S5", "S6", "S7", "S8"]) {
      expect(tierOf(finding({ checklist: s }))).toBe("backlog");
    }
  });
});

describe("the safe direction when the sort is unsure", () => {
  it("blocks anything critical, whatever rule it cites", () => {
    expect(tierOf(finding({ checklist: "PFC-a", severity: "critical" }))).toBe("blocking");
    expect(tierOf(finding({ checklist: "S7", lens: "PFC", severity: "critical" }))).toBe("blocking");
  });

  it("blocks a rule it has never seen, rather than assuming it is minor", () => {
    // "Q5", "Q12", "R-012" all occur on the live ledgers and none is in any list here.
    for (const r of ["Q5", "Q12", "R-012", "", "whatever-comes-next"]) {
      expect(tierOf(finding({ checklist: r }))).toBe("disputed");
      expect(blocks(finding({ checklist: r }))).toBe(true);
    }
  });
});

describe("a vote can move a finding, but only with its evidence attached", () => {
  it("honours an override that two of three readers agreed", () => {
    const i = finding({ checklist: "3.14", tier_override: "backlog", tier_votes: ["backlog", "backlog", "blocking"] });
    expect(confirmedOverride(i)).toBe("backlog");
    expect(tierOf(i)).toBe("backlog");
  });

  it("IGNORES an override with only one vote behind it", () => {
    const i = finding({ checklist: "3.14", tier_override: "backlog", tier_votes: ["backlog", "blocking", "blocking"] });
    expect(confirmedOverride(i)).toBe(null);
    // falls back to the mechanical sort, which blocks
    expect(blocks(i)).toBe(true);
  });

  it("IGNORES a bare override with no votes at all, which is the one-edit bypass", () => {
    expect(confirmedOverride(finding({ checklist: "3.14", tier_override: "backlog" }))).toBe(null);
    expect(blocks(finding({ checklist: "3.14", tier_override: "backlog" }))).toBe(true);
    expect(confirmedOverride(finding({ tier_override: "backlog", tier_votes: "backlog,backlog" }))).toBe(null);
  });

  it("lets a vote raise a finding too, not only lower it", () => {
    const i = finding({ checklist: "PFC-a", tier_override: "blocking", tier_votes: ["blocking", "blocking", "backlog"] });
    expect(tierOf(i)).toBe("blocking");
  });
});

describe("the counts a report prints", () => {
  it("adds up to the number of findings given, with nothing lost", () => {
    const list = [
      finding({ checklist: "3.4", lens: "PSC" }),
      finding({ checklist: "PFC-a" }),
      finding({ checklist: "PFC-a" }),
      finding({ checklist: "PFC-c" }),
      finding({ checklist: "3.14", lens: "PFC" }),
      finding({ checklist: "Q5" }),
    ];
    const c = tierCounts(list);
    expect(c.blocking).toBe(2);
    expect(c.backlog).toBe(2);
    expect(c.disputed).toBe(2);
    expect(c.blocking + c.backlog + c.disputed).toBe(list.length);
  });
});
