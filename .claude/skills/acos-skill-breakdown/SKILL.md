---
name: acos-skill-breakdown
description: Turn any skill into a plain-language, step-by-step Microsoft Word (.docx) document. Reads a skill's SKILL.md, decomposes its whole process to the most granular level — every phase, substep, and command — and renders a styled Word table where each step has an exactly-five-word label and a simple explanation next to it. Use when someone wants to understand, teach, document, or hand off how a skill works, or says "break down <skill>", "explain the steps of <skill>", "make a Word doc of how <skill> works", "document this skill step by step", or "/acos-skill-breakdown <skill-name>".
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# ACOS Skill Breakdown

Turn any skill into a granular, plain-language **Microsoft Word (`.docx`)**
document: every phase, substep, and command, each named in **exactly five words**
with a simple explanation beside it.

The split that makes this reliable: **you** (the model) do the understanding —
read the target skill and decide what the steps are, their five-word labels, and
their plain explanations. A small Python renderer does the mechanics — it turns
your decided breakdown into a styled Word file and never invents content. Keeping
judgement and rendering apart is why the same renderer serves every skill.

## What you produce

- `​.acos/skill-breakdowns/<skill>-<YYYY-MM-DD>.json` — the structured breakdown
  (the reproducible source of truth for the document).
- `​.acos/skill-breakdowns/<skill>-skill-breakdown.docx` — the Word document.

---

## Step 1 — Resolve the target skill

Get the skill name from the user's argument (`/acos-skill-breakdown <name>`). If
none was given, ask which skill. Then locate its `SKILL.md`, searching in order:

```bash
ls .claude/skills/<name>/SKILL.md          # project skill (most common)
ls ~/.claude/skills/<name>/SKILL.md        # personal skill
```

If several match, prefer the project-scoped one. If none exists, tell the user and
stop — this skill breaks down skills that have a written `SKILL.md`.

## Step 2 — Read the whole SKILL.md

Read the target `SKILL.md` **in full**, plus anything it points to that defines
its process (a `templates/` charter, a phase map, an `ARCHITECTURE.md`). You are
building the most granular honest map of how the skill runs — you cannot map what
you have not read.

## Step 3 — Decompose to the most granular level

Break the process into ordered **phases**, and each phase into **atomic steps**.
Granularity rule: one step = one thing the skill actually does — a single command,
a single decision, a single dispatch. If a numbered substep in the source does
three things, that is three steps.

Cover the whole process, not just the happy path:

- **Ground rules / invariants**, if the skill has them, as a first section — they
  govern every later step.
- **Every phase and substep**, in order.
- **On-demand actions** (verbs the user can say, optional sub-modes) as their own
  section, so the map is complete.

For **each step**, decide three fields:

- `id` — a short tag matching the source's own numbering where it has one
  (`1.2a`, `I3`, `V4`), so a reader can trace it back.
- `label` — the step in **exactly five words**. Not four, not six. Make the five
  words carry the action (verb-first reads best: "Route the user's question
  first"). This is a hard constraint the renderer checks.
- `explanation` — one or two plain sentences: what the step does and why it
  matters. Define any jargon on first use. **Keep exact commands, file paths, and
  flags verbatim** (e.g. `` `riff coverage probe --novel 0` ``) — the explanation
  is where precision lives, so name the real command.

Write nothing the source does not support. This is a faithful map of an existing
skill, not a redesign of it.

## Step 4 — Write the breakdown JSON

Write the structured breakdown to
`​.acos/skill-breakdowns/<skill>-<YYYY-MM-DD>.json` using this schema (a worked,
real example lives at
`​.acos/skill-breakdowns/acos-research-riffs-2026-07-23.json` if one has been
generated):

```json
{
  "skill": "<skill-name>",
  "title": "/<skill-name> — Step-by-Step Breakdown",
  "subtitle": "one line: what the skill is, in plain words",
  "source": ".claude/skills/<skill-name>/SKILL.md",
  "generated": "<YYYY-MM-DD>",
  "phases": [
    {
      "id": "P1",
      "name": "Phase 1 — <name>",
      "purpose": "one line: why this phase runs",
      "steps": [
        {"id": "1.1", "label": "exactly five words per label", "explanation": "Plain sentence. Keep `exact --commands` verbatim."}
      ]
    }
  ]
}
```

`templates/breakdown-schema.json` is a minimal copy-me shape.

Get today's date from the environment (the harness states it); never guess it.

## Step 5 — Render the Word document

```bash
python3 .claude/skills/acos-skill-breakdown/scripts/render_docx.py \
  --in  .acos/skill-breakdowns/<skill>-<YYYY-MM-DD>.json \
  --out .acos/skill-breakdowns/<skill>-skill-breakdown.docx
```

The renderer prints a JSON summary and, on stderr, a `WARN` list of any label that
is **not exactly five words**. It styles the document in the OKOA system (sage
headers, zebra rows, IBM Plex Sans) and marks any off-count label with a `⚠` in
the document itself, so a slip is visible rather than silent.

> Python here is deliberate and within the repo rule: generating a real `.docx`
> needs `python-docx`, which has no viable TypeScript/Rust equivalent, and it is
> the project's established path for Word output. All judgement stays in the
> model-authored JSON; the Python only renders.

## Step 6 — Fix every label warning, then re-render

If `label_warnings` is non-empty, the job is **not done**. Fix each flagged label
in the JSON so it is exactly five words — re-word, do not pad — and run the
renderer again. Deliver only when `label_warnings` is `[]`.

Optionally verify the result visually (LibreOffice → PDF → PNG) before delivering
for an outward-facing audience:

```bash
soffice --headless --convert-to pdf --outdir /tmp <the>.docx
```

## Step 7 — Deliver

Give the user a clickable link to the `.docx` (a full `file://` URL, per the
project's link convention), and a one-line summary: how many phases and steps, and
where the reproducible JSON lives.

---

## Design rules

- **Exactly five words per label — always.** It is the whole point of the format.
  The renderer checks it; you must land it.
- **Faithful, not inventive.** The document maps what the skill does. If the
  source is silent on something, the breakdown is too.
- **Precision lives in the explanation.** Labels are plain; explanations keep the
  exact command names, paths, and flags verbatim.
- **Most granular means most granular.** One command or one decision per row. A
  breakdown with ten rows for a ten-phase skill is under-decomposed.

## Files

```
SKILL.md                       this procedure
scripts/render_docx.py         breakdown JSON -> styled .docx (python-docx)
templates/breakdown-schema.json  minimal shape to copy
```

---

*ACOS Skill Breakdown — read the skill, name each step in five words, prove it in Word.*
