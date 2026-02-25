---
name: acos-model-change
description: Manages model profiles for ACOS agents. Switch between Budget/Standard/Premium/Auto tiers, override individual agents, and view current assignments.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# ACOS Model Change

## Overview

This skill manages which model each ACOS agent uses when spawned. It provides Claude-only profiles (Budget/Standard/Premium/Auto) and multi-provider profiles (Hybrid-Review/Free-Tier/OpenAI-Review/Gemini-Review) that route reviewers and analysis agents to external models. Per-agent custom overrides are also supported. Changes persist for the current session only.

Configuration files:
- Model profiles: `.acos/config/model-profile.yaml`
- Provider registry: `.acos/config/providers.yaml`
- Session state: `.acos/state/model-session.yaml`

**Key constraints:**
- The main conversation model cannot be changed programmatically — advise `/model` if profile recommends differently.
- Architect and developer ALWAYS use Claude (they need tool access). External models are silently overridden to Claude defaults.
- External models require API keys set as environment variables (see providers.yaml).

## Skill Protocol

### Phase 1: Display Current State (Always Runs First)

1. Check for session state file (`.acos/state/model-session.yaml`):
   - If exists: read active profile and any custom overrides
   - If not: read default from `.acos/config/model-profile.yaml`

2. Resolve models for all 8 agents:
   ```bash
   for agent in architect developer qa-reviewer security-reviewer performance-reviewer integration-reviewer memory-agent learning-agent; do
     bash .claude/scripts/resolve-agent-model.sh "$agent"
   done
   ```

3. Display the current state:
   ```
   Model Profile Status
   ═══════════════════════════════════════
   Active Profile: [premium/standard/budget/auto/custom]
   Source: [session override / project default]

   Agent Assignments:
     architect            → opus
     developer            → opus
     qa-reviewer          → opus
     security-reviewer    → opus
     performance-reviewer → opus
     integration-reviewer → opus
     memory-agent         → sonnet
     learning-agent       → opus

   Main Model: opus (advisory — use /model to change)
   Custom Overrides: [none / list]
   ```

### Phase 2: Present Options

Present the user with options using AskUserQuestion:

1. **Switch Profile** — Change the active profile for this session:

   **Claude-only profiles:**
   - `budget` — Haiku for implementation, Sonnet for critical review. Lowest Claude cost.
   - `standard` — Sonnet across the board, Haiku for memory. Good balance.
   - `premium` — Opus everywhere, Sonnet for memory. Maximum quality. (Current default)
   - `auto` — Opus for critical decisions, Sonnet for implementation, Haiku for support.

   **Multi-provider profiles** (require API keys — see `.acos/config/providers.yaml`):
   - `hybrid-review` — Claude for implementation, GPT-4o/Gemini/Llama for diverse reviews.
   - `free-tier` — Free OpenRouter models for reviewers. Zero external cost.
   - `openai-review` — Claude for implementation, OpenAI for all reviews.
   - `gemini-review` — Claude for implementation, Google Gemini for all reviews.

2. **Override Individual Agent** — Set a specific model for one agent without changing the profile. Supports both Claude names (opus, sonnet, haiku) and external models (openai:gpt-4o, openrouter:google/gemini-2.5-pro). Architect and developer overrides are restricted to Claude models.

3. **Reset to Default** — Clear session state, revert to project config default.

4. **Switch Main Model (Guidance)** — Explain that the main conversation model must be changed via `/model` command. Show what the current profile recommends for main.

### Phase 3: Apply Changes

Based on user selection:

1. **Profile switch:**
   Write to `.acos/state/model-session.yaml`:
   ```yaml
   active_profile: [selected-profile]
   changed_at: "[timestamp]"
   changed_by: "acos-model-change"
   ```

2. **Individual override:**
   Write/update `.acos/state/model-session.yaml`:
   ```yaml
   active_profile: [current-profile]
   custom_overrides:
     [agent-name]: [model]
   changed_at: "[timestamp]"
   changed_by: "acos-model-change"
   ```

3. **Reset:**
   Remove `.acos/state/model-session.yaml`

### Phase 4: Validate and Confirm

1. Re-resolve all 8 agents using `resolve-agent-model.sh`
2. Display the updated assignment table
3. If the profile's recommended main model differs from the current conversation model, advise:
   > "This profile recommends **[model]** for the main conversation. Run `/model` and select **[model]** to match."

## Error Handling

| Scenario | Response |
|----------|----------|
| Config file missing | Copy template from `.claude/skills/acos-model-change/templates/model-profile-default.yaml` |
| State dir missing | Create `.acos/state/` |
| Invalid profile name | Show available profiles, ask again |
| resolve-agent-model.sh fails | Report error, use hardcoded defaults |

---

*ACOS Model Change — Cost control for your coding session.*
