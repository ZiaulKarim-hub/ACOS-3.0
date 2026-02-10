---
name: acos-interview
description: Conducts a comprehensive vision interview. Asks about users, platforms, features, scale, integrations, security, design, technology, and success criteria. Creates vision-interview.md and vision-document.md.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep
---

# Vision Interview

## Overview

This skill conducts a comprehensive interview with the user to fully understand their vision before any planning or implementation begins. It iterates through questioning rounds until sufficient understanding is reached or the user signals completion.

**This skill runs in the main conversation context** because it is interactive with the user — it asks questions and waits for answers.

### Pre-flight: Auto-Bootstrap

Before proceeding, ensure ACOS is initialized in this project:

```bash
bash .claude/scripts/acos-preflight.sh
```

This is idempotent — it exits immediately if ACOS is already initialized. If not, it runs the full bootstrap (symlinks, directories, config, gitignore).

## Protocol

### Step 1: Receive Initial Vision Statement

When the user provides their vision (even a one-liner):
- Acknowledge what you understood
- **Never accept one-liners as complete.** Always conduct a thorough interview.

### Step 2: Interview Loop (max 10 iterations)

For each round, ask targeted questions covering gaps in these categories:

#### Question Categories

1. **Users & Audience** — Who will use this? Technical level? Primary vs secondary users?
2. **Platforms & Devices** — Web? Mobile? Desktop? Responsive? Offline support?
3. **Features & Scope** — Must-have? Nice-to-have? Explicitly excluded? MVP vs full vision?
4. **Scale & Performance** — Expected users? Data volume? Growth? Performance requirements?
5. **Integrations** — External services? Third-party APIs? Existing systems?
6. **Security & Compliance** — Sensitive data? Compliance (HIPAA, GDPR)? Auth needs?
7. **Design & UX** — Visual style? Brand guidelines? Accessibility?
8. **Technology Preferences** — Preferred languages? Frameworks? Hosting? Existing infrastructure?
9. **Success Criteria** — How do we know it's done? Key metrics? Launch criteria?

**Per round:**
1. Ask 3-5 focused questions covering remaining gaps
2. Wait for user responses
3. Update your understanding
4. Check completeness — if all categories are sufficiently covered, or user says "that's enough", proceed to Step 3

### Step 3: Create Source of Truth Documents

Create two files:

#### `memory/source-of-truth/vision-interview.md`
Complete Q&A transcript organized by round. Use the template at `!cat templates/vision-interview.md`

#### `memory/source-of-truth/vision-document.md`
Synthesized requirements document. Use the template at `!cat templates/vision-document.md`

### Step 4: Confirm with User

Present a summary of the vision document to the user for confirmation. Make any requested adjustments.

## Exit Conditions

The interview ends when:
1. **Architect Satisfied:** All question categories covered with sufficient depth
2. **User Signal:** User says "that's enough" or equivalent
3. **Max Iterations:** 10 rounds reached

---

*Vision Interview - Understanding before building.*
