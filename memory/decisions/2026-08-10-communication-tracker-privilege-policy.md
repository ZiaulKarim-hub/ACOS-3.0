# Decision — acos-communication-tracker privilege/litigation gap closed by POLICY

- **Date:** 2026-08-10
- **Decided by:** Zee (explicit answer, this session)
- **Status:** SETTLED — do not re-litigate without asking Zee
- **Project:** Skill Workshop (registry uuid `97ed3c46-ee91-453e-8746-6d179a79e433`)
- **Subject skill:** `~/.claude/skills/acos-communication-tracker/`

## Context

The first full live sweep (2026-08-08) of Zee's deal-labeled Gmail surfaced:

- an active fraud lawsuit filed by Rubin against OKOA, with outside counsel
  actively requesting discovery documents;
- creditor lawsuits against the Wolfgramm/Ascent guarantors;
- at least one message explicitly subject-lined
  "Attorney Client Privileged Communication."

The sweeping instance did not open or summarize the privileged message — but that
was its own judgment call, not an enforced rule. The skill has **zero built-in
privilege-exclusion step**. The only guard was a warning banner in `SKILL.md`,
which the Phase 7 watcher (a background timer that wakes a cmux pane to re-run the
sweep) does not read.

This was carried as an open question through the 2026-08-08, 2026-08-09 and
2026-08-10 Skill Workshop closes, each time recorded as "needs Zee's decision."

## Decision

**Close the gap by policy, not by code.**

- No privilege scanner will be built.
- No sender/label exclude-list will be built.
- **A human must be present for every sweep.** The Phase 7 watcher is never left
  to run unattended against live mail. "Started and walked away from" counts as
  unattended.

## Rejected alternatives

1. **Port `acos-dataroom-v2`'s `dr2-privilege-scanner` pattern** — three blind
   readers per thread, asymmetric veto (any single FLAG excludes the thread).
   Proven pattern already in this repo. Rejected: build cost plus 3x model calls
   per thread on every sweep.
2. **Deterministic exclude-list** — never sweep threads from named law-firm
   domains, counsel senders, or litigation Gmail labels. Rejected: build cost, and
   it only blocks what was thought to list.
3. **Both gates layered** (deterministic list first, AI scanner behind it).
   Rejected: highest build cost of the three.

## Accepted residual risk — stated plainly, not softened

Nothing mechanically prevents a privileged or litigation thread from being read
and summarized into `state/groups.json` and `state/communication-table.html`.
The control is a person watching each run. If that trade stops being acceptable,
the decision must be revisited with Zee — it must **not** be quietly re-opened by
building the scanner anyway.

## Where this is written down

- `~/.claude/skills/acos-communication-tracker/SKILL.md` — the ⚠ section at the
  top (rewritten from "unresolved" to "CLOSED BY POLICY"), the "Explicitly settled
  decisions" list, and a new ATTENDED-ONLY bullet in Phase 7.
- This file.

## Still open (NOT settled by this decision)

- The rougher first-pass Investors/deals/brokers groups in `state/groups.json`
  were never reconciled against the better second pass from the same fork.
- Whether Zee also wants Discard and Flag-as-spam buttons alongside the existing
  Mark-to-do-done and Deprecate buttons.
- Slack still blocked (OKOA workspace on a free plan at its 10-app limit).
- Google Messages paired but not wired into live tracking.
- Gmail MCP cannot fetch attachment file content at all — metadata only.
