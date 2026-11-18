---
name: acos-triplex-repairer
description: Repairs a list of items where the FIX must be checked by readers who did not write it — one repairer, then independent checkers, and a fix lands only when two agree it is actually fixed, measured from primary evidence. Built 2026-11-18 for the Nemesis backlog (comments, stale counts, wording, drift, the protocol's own records), but it takes any list: a punch list, a set of review comments, a batch of small corrections. Nemesis calls it as `/acos-nemesis-protocol repair`; it also runs standalone on anything. The author of a fix never votes on its own fix. Trigger phrases: "triplex repair", "repair the backlog", "fix these and check them", "/acos-triplex-repairer".
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Task(general-purpose), Task(developer)
argument-hint: "<what to repair>  (e.g. \"the nemesis backlog\" | \"<path to a list>\")"
---

# ACOS Triplex Repairer — the author never grades its own work

## The one rule

A fix is recorded as DONE only when **two readers who did not write it** independently
confirm, from evidence they gathered themselves, that the recorded defect is gone. The
repairer's own opinion is not a vote.

## Why the author gets no vote

The obvious shape is three agents fixing, two agreeing. That shape has a hole: the author
of a fix is the one party guaranteed to believe it works, so counting its vote means one
checker can carry a fix to "done". It also costs three repairs of every item.

So the votes belong to the CHECKERS:

| Stage | Who | What they see |
|---|---|---|
| Repair | one agent | the item, the file, nothing else |
| Check | two agents, run separately | the item and the file — **never** the repairer's reasoning |
| Tie-break | a third checker, only on disagreement | the same inputs as the other two |

Two confirmations land the fix. One confirmation and one refusal pulls in the third, and
two of those three decide. That is the 2-of-3 rule, with the author removed from the panel,
which is strictly stronger than 2-of-3 including the author and costs less.

## What a checker is asked

Never "is this fixed?" — that invites a yes. Always a measurement, exactly as in
[acos-triplex-verification](../acos-triplex-verification/SKILL.md):

| Never ask | Always ask |
|---|---|
| "Confirm the comment now matches the code." | "What does the comment at X say, and what does the code at X do? Quote both." |
| "Verify the count is right." | "What number does the file state, and what is the counted number? Show the command." |

The checker is told the ORIGINAL defect and the file. It is not told what was changed, and
it is not shown the repairer's explanation.

## Procedure

1. **Take the list.** From Nemesis, that is the backlog tier (`nemesis repair`). Standalone,
   it is any list of items, each with a defect and a place.
2. **Batch by file, not by topic.** Items in the same file are repaired together, because
   two repairs in one file by two agents collide. One file is owned by one repairer at a
   time.
3. **Repair.** One agent per batch. It fixes and reports what it changed, file and line.
4. **Check, twice, blind.** Two agents per batch, run one at a time, each told only the
   original defect and the file. Neither sees the other, nor the repairer.
5. **Tie-break only on disagreement.** A third checker, same inputs.
6. **Record.** Two confirmations → the item closes with both checkers' evidence attached.
   Otherwise it stays open with the disagreement recorded. **An unresolved item is never
   closed quietly.**

## Hard rules

- **Never run the agents in parallel.** Measured on this machine: a parallel fan-out of 3
  reviewers froze within 48 seconds of each other on 2026-09-22, and a 14-agent fan-out
  stalled on 2026-09-10. Sequential finishes.
- **Put the turn budget in every agent prompt, as its first line.** The cap is near 30 tool
  calls. Measured 2026-11-18 on the first run of the verification skill: an agent spent all
  30 gathering and reported NOTHING, so a complete investigation produced a blank. Tell each
  agent: about 30 calls, deliver by call 25, batch commands, a partial report beats a missing
  one. If one is cut off anyway, RESUME it — its work is in its transcript.
- **Never pass the conversation to an agent.** Only the item and the file.
- **Never let a checker see the repairer's reasoning**, before or during its run.
- **Never close an item on one confirmation.**
- **A repair that cannot be checked is not a repair.** If both checkers answer
  CANNOT-VERIFY, the item stays open and says why.
- **Report the refusals too.** A run that prints only what it closed hides its own error
  rate. State items attempted, closed, still open, and unresolved.

## Scope: what this may and may not repair

**May:** comments that contradict their code, stale counts and dates, wording, a document
disagreeing with another document, drift from the plan, and Nemesis's own records.

**May NOT:** anything in the blocking tier — the fourteen security checklists, anything that
breaks a test, a caller or the build, and anything marked critical. Those keep going through
Nemesis's own judge and ladder, unchanged. If a repair here turns out to need a change in
blocking-tier code, it STOPS and hands the item back rather than widening its own remit.

## What this does NOT do

It does not make a repair correct. Two checkers reading the same stale file agree twice and
are wrong twice. Where an item can be checked against a LIVE source — a running command, a
real count, a current file on disk — the question must say so, because the point of separate
readers is independent evidence, not two reads of one cache.
