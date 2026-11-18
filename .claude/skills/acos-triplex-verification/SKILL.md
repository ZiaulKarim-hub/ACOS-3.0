---
name: acos-triplex-verification
description: Three independent agents measure the same questions blind, and NOTHING may be stated unless at least two of them got the same answer from primary evidence. Built 2026-11-18 after a session in which claims were made and later retracted; the retraction, not the error, is what this exists to stop. Use it whenever a report will be acted on and being wrong is expensive — a status report, an audit, a "what is still broken" list, a set of figures for Zee. Each agent is asked to MEASURE, never to agree, and never sees the claim it is checking or any sibling's answer. A 1/1/1 split is reported as UNRESOLVED, never resolved by the orchestrator's own opinion. Trigger phrases: "triplex", "triple check", "verify with three agents", "2 of 3", "/acos-triplex-verification".
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Task(general-purpose), Task(qa-reviewer), Task(developer)
argument-hint: "<what to verify>  (e.g. \"the website and SEO status report\")"
---

# ACOS Triplex Verification — two of three, or it does not get said

## The one rule

A statement reaches the report **only** when at least two of three independent agents
produced the same answer from primary evidence they gathered themselves. Everything else
is reported as UNRESOLVED or UNVERIFIABLE, with the disagreement shown. The orchestrator
never breaks a tie with its own reasoning.

## Why this exists (do not delete this section)

It was built because claims were made confidently and withdrawn afterwards. A reader who
has been corrected twice cannot tell a right answer from a wrong one any more, so the
VALUE of the report collapses even when its facts improve. Three blind measurements cost
more than one; a retraction costs more than three.

## The trap this is designed around: never show an agent the claim

The obvious design — "here is a claim, check it" — does not work. An agent handed a claim
tends to find support for it, and three agents handed the same claim agree with each other
rather than with reality. That is agreement, not verification, and it is worse than one
honest measurement because it arrives wearing a quorum.

**So every question is posed as a MEASUREMENT, with no expected answer in it.**

| Never ask | Always ask |
|---|---|
| "Confirm 958 findings are open." | "How many findings are open? Give the number and how you counted." |
| "Verify /bridge-loans/ returns 404." | "What HTTP status does /bridge-loans/ return? Paste the command and output." |
| "Check that the audit is clean." | "Run the dependency audit. Paste its exact output." |

The orchestrator holds the claim being checked. The agent never sees it.

## Procedure

1. **Write the question set.** Turn every statement to be verified into one neutral
   measurement question. One question per statement, numbered. No question may contain a
   number, a verdict or an adjective from the statement it tests.
2. **Fix the evidence rule.** Each answer must carry the command that was run or the file
   and line that was read, plus the raw output. An answer with no primary evidence is
   scored CANNOT-VERIFY however confident it sounds.
3. **Dispatch three agents, ONE AT A TIME.** Sequential, not parallel. Measured on this
   machine: a parallel fan-out of 3 reviewers froze within 48 seconds of each other on
   2026-09-22, and a 14-agent fan-out stalled on 2026-09-10. Every agent receives the
   IDENTICAL question set and nothing else — not the conversation, not a sibling's answer,
   not the orchestrator's expectations.

   **Put the turn budget in the prompt, as its first line.** The cap is near 30 tool
   calls. Measured on the very first run of this skill, 2026-11-18: agent one spent all 30
   measuring and was cut off having reported NOTHING, so a complete investigation produced
   a blank. It had to be resumed with "deliver now", and then answered all 12 questions in
   a single further call — the work had been done all along, and only the reporting was
   missing. So every agent prompt must say: you have about 30 calls, deliver by call 25
   even if questions are unfinished, batch several questions into one shell call, and a
   partial report that arrives beats a complete one that never does.

   **If an agent is cut off anyway, resume it rather than re-running it.** Its measurements
   are still in its transcript; a fresh agent would pay for them again and might measure a
   site that has changed in between.
4. **Score each question independently.** For each numbered question, line up the three
   answers and apply the table below.
5. **Write the report** from the scored table only.

## Scoring

| Pattern across the three answers | Verdict | What the report may say |
|---|---|---|
| 3 agree | CONFIRMED | state it plainly |
| 2 agree, 1 differs | CONFIRMED (2/3) | state it, and note what the third said |
| 2 say CANNOT-VERIFY | UNVERIFIABLE | say it could not be measured, and why |
| 1 / 1 / 1 | **UNRESOLVED** | say the three disagreed, show all three, claim nothing |
| 2 agree the statement is FALSE | REFUTED | correct the record explicitly |

**CANNOT-VERIFY never supports a statement.** It is a real vote and it can carry a
majority, but the majority it carries is "we do not know".

**A refuted statement must be named as refuted**, with the earlier wording quoted. Quietly
dropping a wrong claim is the same failure as never catching it.

## Numbers are compared exactly

Two agents reporting 958 and 957 have NOT agreed. Either reconcile with a fourth
measurement by the orchestrator, or record it as UNRESOLVED and print both. Rounding two
near answers into one is how a false figure gets a quorum.

## Hard rules

- **Never run the agents in parallel.** See step 3; this is measured, not stylistic.
- **Never pass the conversation to an agent.** Only the question set.
- **Never tell an agent what another agent said**, before or during its run.
- **Never break a 1/1/1 tie yourself.** Report it unresolved and say what a fourth
  measurement would need to settle it.
- **The orchestrator may measure, but its measurement is a fourth opinion, never a
  casting vote.** It is recorded as the orchestrator's own and labelled as such.
- **Report every question asked**, including the ones that came back UNRESOLVED or
  UNVERIFIABLE. A report that prints only the confirmed rows hides its own error rate.
- **State the count up front:** how many questions were asked, how many reached two of
  three, how many did not. That number is the report's own confidence, and it belongs in
  the first paragraph.

## Report shape

Open with the scoreboard — questions asked, confirmed, refuted, unresolved, unverifiable.
Then the findings grouped by what the reader would DO about them, not by which agent found
them. Then, last, the method. Deliverables follow the project rules: HTML or another real
document format, never a markdown file, saved under `~/Documents/OKOA` unless told
otherwise, and opened in Chrome.

## What this does NOT do

It does not make a measurement correct. Three agents reading the same stale file agree
three times and are wrong three times. Where a question can be answered against a LIVE
source — a running site, a real command, a current directory — the question must say so,
because the point of three readers is independent evidence, not three reads of one cache.
