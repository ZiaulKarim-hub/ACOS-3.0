---
name: research
description: Zee's light research launcher. When the user types /research (optionally /research <N> where N is a depth 1-5, optionally followed by a topic), do a grounded, sourced research pass on the message that preceded it — reusing the acos-research-riffs engine so every claim carries a source and a confidence label. Depth 1 is a single quick probe; depth 5 is a full multi-agent riff with a cited report. After delivering, offer "keep riffing?" to escalate one level. Trigger, the user types /research, /research 3, /research 3 <topic>, or /research <topic>. NOT for one-shot formal reports with no conversation (that is /acos-deep-research), and NOT the full conversational engine unless escalated (that is /acos-research-riffs).
user-invocable: true
disable-model-invocation: false
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, WebSearch, WebFetch, Task, AskUserQuestion
---

**Category: dial skill.** Append it to a message to shape the reply. It stacks with every other dial — run `/dials` to see them all.

# /research — light research launcher

## What this is

A thin front-door to the `acos-research-riffs` engine. You drop `/research`
after a question or comment, and it runs a **grounded, sourced** research pass on
that text — right inside the current chat. "Grounded" means every claim traces to
a real source gathered this session, with a confidence label; nothing is
improvised from memory (the engine's invariants I1, I2, I9 still bind).

It is a **launcher**, not a re-implementation. The actual research is done by the
same `riff` CLI and the same charters `/acos-research-riffs` uses. This skill only
decides **how much of that engine to run**, keyed to a 1–5 depth dial.

- **This skill (`/research`)** — quick, non-interactive, used mid-conversation.
- **`/acos-research-riffs`** — the full interactive engine (interview, plan gate,
  moderator, cited report). Depth 5 hands off to it.
- **`/acos-deep-research`** — a one-shot formal report with no conversation.

## The depth dial (source of truth: `scripts/research-plan.ts`)

Do not hardcode the mapping from prose. Parse the argument and read the plan:

```bash
bun "$HOME/.claude/skills/research/scripts/research-plan.ts" "<the exact text after /research>"
```

It prints `{ depth, topicOverride, plan }`. `plan` is authoritative — obey its
`tier`, `panel`, `maxProbes`, `gate`, `recency`, `report`, `handoff`, `costNote`,
`nextRung` fields. A leading integer outside 1–5 makes the tool exit non-zero with
`depth must be 1-5`; surface that verbatim and stop.

| Depth | Name | What runs |
|---|---|---|
| **1** | light | One probe. Grounded answer + sources + confidence label. No panel. **Default when no number given.** |
| **2** | light-plus | Up to 3 probes from a few angles. Still one answer, better corroborated. No panel. |
| **3** | higher-than-average | A small generated panel (`lite` tier) with dossiers + a recency check. No coverage gate. |
| **4** | deep | A fuller panel (`standard` tier) + the coverage gate + a recency sweep. No report unless asked. |
| **5** | research-riffs-deep | Hand off to the full `acos-research-riffs`: panel, dossiers, gate, ledger, **cited report**. |

## Step 0 — Target selection

- **No topic override** (`topicOverride === ""`): research the **most recent
  substantive user message before the `/research` invocation** — the question or
  comment it was appended to. Ignore small talk and meta-commands, same rule as
  `/restate`.
- **Topic override present**: research that text instead.
- If genuinely ambiguous which message is the target, ask ONE short question
  first; do not guess between two plausible targets.

State the resolved target and depth in one line before spending:
`Researching at level <N> (<name>): "<target, trimmed>"`.

## Step 1 — Engine prelude (run at the TOP of every engine bash block)

`/research` is global; the user may be in any repo. Pin a **central** session
store so quick research never litters the current project, and define `riff` as a
**shell function** (NOT a string variable — the user's shell is zsh, which does
not word-split an unquoted `$RIFF="bun …"`, so `$RIFF init` is read as one long
command name and fails). Each Bash tool call is a fresh shell, so prepend this
prelude to every block that calls the engine — or keep a phase's engine calls in
one block:

```bash
export RIFF_ROOT="$HOME/.acos-research"          # sessions land in ~/.acos-research/.acos/riffs/<id>
riff() { bun "$HOME/.claude/skills/acos-research-riffs/scripts/riff.ts" "$@"; }
```

The `$HOME/.claude/skills/...` path resolves through the global symlink, so it
works regardless of CWD. Capture `session_id`, `slug`, and `claims_path` from the
JSON each command prints (they are top-level fields).

## Step 2 — Execute the plan

### Depths 1–2 (no panel — the light path)

1. Open a lite session and capture its `session_id`:
   ```bash
   riff init --topic "<target>" --tier lite
   ```
2. Declare ONE coverage dimension (the question itself), so probes have a home:
   ```bash
   printf '[{"id":"q","name":"<target, short>","why":"the asked question"}]' > /tmp/research-dim.json
   riff coverage init --session <id> --json /tmp/research-dim.json
   ```
3. Render probe(s) — **1** at depth 1, **up to `maxProbes` (3)** at depth 2, each
   on a distinct angle of the question. Tag each `[L1 sweep]`:
   ```bash
   riff render probe --session <id> --question "[L1 sweep] <angle>" --dimension q
   ```
   Each prints `{ charter, slug, claims_path }`.
4. **Dispatch one `Task` per probe, in a single message** (concurrent), passing
   the charter BY PATH with the Phase-2 wrapper from `acos-research-riffs`
   (`SKILL.md` §"Phase 2"). Use `subagent_type: riff-researcher` if that agent is
   registered, else `claude` — **never `general-purpose`** (it has no web tools).
   Always state today's date in the wrapper.
5. Ingest each returned dossier and credit coverage (feed the ingest's
   `novel_by_dimension.q` count straight into the probe credit):
   ```bash
   riff claims ingest --session <id> --slug <slug>
   riff coverage probe q --session <id> --novel <count> --note "probe: <angle>"
   ```
6. Get the grounded answer:
   ```bash
   riff ask "<target>" --session <id>
   ```
   Deliver per the label table in `acos-research-riffs` §"Phase 4 → Route the
   question" — never answer past the label. Print the `stamp` field **verbatim**.
   Honour `numeric_unprimaried_ids` (those figures are provisional even under a
   `verified` label). Do not invent the stamp format; use what `ask` returns.

### Depths 3–4 (panel — abbreviated, NON-interactive)

Run `acos-research-riffs` Phases **1.3–1.4** (dimensions + generated panel) and
**2** (panel research), and at depth 4 also Phase **3** (coverage gate +
auditor) — with these deltas that make it a *launcher*, not the full skill:

- **Skip Phase 1.1 (the interview)** and **Phase 1.5 (the interactive plan
  gate).** Auto-derive the brief, dimensions, and panel from the target message.
  Instead of the gate, print the plan's `costNote` as a single line, then proceed.
- Use the plan's `tier` on `init` (`lite` at depth 3, `standard` at depth 4).
- Enforce `recency: true` — every `fast_moving` dimension gets its last-90-days
  sweep (`riff coverage probe … --recency`), per I11.
- **One synthesized answer, no report.** After research (and the gate at depth 4),
  answer the target via `riff ask "<target>" --session <id>` and deliver with its
  stamp. Do NOT compile a report at depths 3–4 (`plan.report === false`).
- Still write the central `RIFF_ROOT`; still dispatch charters by path.

### Depth 5 (full engine)

Invoke the `acos-research-riffs` skill via the `Skill` tool and run its complete
protocol (Phases 0–5) on the target message, at `deep` tier, ending in a
citation-verified report. Pass the target as the question of record; its own
Phase 1 interview refines scope. This is the one depth that is fully interactive.

## Step 3 — Offer to keep riffing

After delivering at any depth where `plan.nextRung !== null` (1–4), end with a
one-line, opt-in offer:

> keep riffing? (deepen to level `<nextRung>`, or jump to 5) — say the word.

- Only escalate on an explicit yes. Silence means stop; the answer already stands.
- At depth 5 there is no higher rung — make no offer.

## Step 4 — Escalation reuses the SAME session (no wasted work)

On "keep riffing → yes", **reuse the existing `session_id`** and run only the
*additional* work the higher rung needs (seat a panel, add the gate, etc.). The
engine's ledger and corpus are append-only, so the probes already gathered carry
forward automatically — escalation adds evidence, never restarts. Re-run
`research-plan.ts` with the new depth to get the higher plan; keep `RIFF_ROOT`
and the session id.

## Notes & non-goals

- **Central store.** Quick sessions live in `~/.acos-research/.acos/riffs/`. Find
  a past one by running the Step 1 prelude, then `riff preflight`.
- **Cost honesty.** Depths 1–2 are cheap (no panel). Depths 3–5 seat agents and
  cost roughly 15x ordinary chat (Anthropic, vendor-reported) — the plan's
  `costNote` says this before spending.
- **Not a search box.** If the user wants one bare fact and no rigor, just look it
  up — `/research` is for a grounded, labeled, sourced answer.
- **Register.** Answer at the user's active reading level; define terms on first
  use; never state a number that is not a claim in the corpus (I9).

---

*ACOS /research — one keystroke into grounded research; deepen only when you want to.*
