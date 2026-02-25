#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# resolve-agent-model.sh — Resolves the model for a given ACOS agent
# ═══════════════════════════════════════════════════════════════════════════════
#
# Usage: bash .claude/scripts/resolve-agent-model.sh <agent-name>
#
# Outputs a single line in one of two formats:
#   Claude model:   "opus", "sonnet", or "haiku"      → use Task()
#   External model: "openai:gpt-4o", "openrouter:..." → use run-external-agent.py
#
# Resolution order:
#   1. Session state custom override (.acos/state/model-session.yaml → custom_overrides.<agent>)
#   2. Session state profile (.acos/state/model-session.yaml → active_profile → profile lookup)
#   3. Config file profile (.acos/config/model-profile.yaml → default_profile → profile lookup)
#   4. Hardcoded fallback: "opus" (architect/developer/reviewers), "sonnet" (memory), "haiku" (n/a)
#
# Safety: Agents that require tool access (architect, developer) are forced to
# Claude models even if an external model is configured. A warning is emitted.
#
# This script uses Python 3 stdlib for YAML-like parsing (matching Oracle pattern).
# Execution target: <100ms.
# ═══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

AGENT_NAME="${1:-}"

if [[ -z "$AGENT_NAME" ]]; then
  echo "Usage: resolve-agent-model.sh <agent-name>" >&2
  echo "opus"
  exit 0
fi

# Paths
STATE_FILE=".acos/state/model-session.yaml"
CONFIG_FILE=".acos/config/model-profile.yaml"

# ── Python resolver (stdlib only, fast) ─────────────────────────────────────

python3 - "$AGENT_NAME" "$STATE_FILE" "$CONFIG_FILE" <<'PYEOF'
import sys
import os

agent_name = sys.argv[1]
state_path = sys.argv[2]
config_path = sys.argv[3]

CLAUDE_MODELS = {"opus", "sonnet", "haiku"}

# Agents that MUST use Claude (they need tool access via Task())
CLAUDE_ONLY_AGENTS = {"architect", "developer"}

# Hardcoded fallbacks per agent (matches current ACOS defaults)
AGENT_DEFAULTS = {
    "architect": "opus",
    "developer": "opus",
    "qa-reviewer": "opus",
    "security-reviewer": "opus",
    "performance-reviewer": "opus",
    "integration-reviewer": "opus",
    "memory-agent": "sonnet",
    "learning-agent": "opus",
}


def is_valid_model(model_spec):
    """Check if a model spec is valid — either a Claude name or provider:model format."""
    if model_spec in CLAUDE_MODELS:
        return True
    if ":" in model_spec:
        provider, _, model = model_spec.partition(":")
        return bool(provider.strip()) and bool(model.strip())
    return False


def is_external(model_spec):
    """Check if model spec refers to a non-Claude provider."""
    if model_spec in CLAUDE_MODELS:
        return False
    if ":" in model_spec:
        provider = model_spec.partition(":")[0].strip()
        return provider != "claude"
    return False


def normalize_model(model_spec):
    """Normalize model spec output.

    - Bare Claude names (opus, sonnet, haiku) → returned as-is for backward compat
    - claude:opus → opus (strip claude: prefix for Task() compatibility)
    - openai:gpt-4o → openai:gpt-4o (kept as-is for external dispatch)
    """
    if model_spec in CLAUDE_MODELS:
        return model_spec
    if ":" in model_spec:
        provider, _, model = model_spec.partition(":")
        if provider.strip() == "claude" and model.strip() in CLAUDE_MODELS:
            return model.strip()
    return model_spec


def parse_simple_yaml(filepath):
    """Minimal YAML parser — handles flat keys, nested maps (1 level), and comments.

    Returns a dict. Nested keys like 'profiles.budget.developer' are stored as
    nested dicts: {'profiles': {'budget': {'developer': 'haiku'}}}.
    """
    if not os.path.isfile(filepath):
        return {}

    result = {}
    current_section = None
    current_subsection = None

    try:
        with open(filepath) as f:
            for line in f:
                stripped = line.rstrip()

                # Skip empty lines and comments
                if not stripped or stripped.lstrip().startswith('#'):
                    continue

                # Detect indentation level
                indent = len(line) - len(line.lstrip())

                # Top-level key (no indent)
                if indent == 0 and ':' in stripped:
                    key, _, val = stripped.partition(':')
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    if val:
                        result[key] = val
                    else:
                        result[key] = {}
                        current_section = key
                        current_subsection = None

                # Second-level key (2-space indent)
                elif indent == 2 and ':' in stripped and current_section is not None:
                    key, _, val = stripped.partition(':')
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    if isinstance(result.get(current_section), dict):
                        if val:
                            result[current_section][key] = val
                        else:
                            result[current_section][key] = {}
                            current_subsection = key

                # Third-level key (4-space indent)
                elif indent == 4 and ':' in stripped and current_section and current_subsection:
                    key, _, val = stripped.partition(':')
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    section = result.get(current_section, {})
                    if isinstance(section, dict):
                        subsection = section.get(current_subsection, {})
                        if isinstance(subsection, dict):
                            subsection[key] = val
                            section[current_subsection] = subsection
                            result[current_section] = section

    except (IOError, OSError):
        return {}

    return result


def resolve(agent, state, config):
    """Resolve model for agent using priority chain.

    Returns a model spec string:
    - Claude models: "opus", "sonnet", "haiku"
    - External models: "provider:model" (e.g., "openai:gpt-4o")
    """

    # Priority 1: Session custom override
    custom = state.get("custom_overrides", {})
    if isinstance(custom, dict) and agent in custom:
        model = custom[agent]
        if is_valid_model(model):
            return model

    # Priority 2: Session active profile
    session_profile = state.get("active_profile", "")
    if session_profile:
        profiles = config.get("profiles", {})
        if isinstance(profiles, dict) and session_profile in profiles:
            profile = profiles[session_profile]
            if isinstance(profile, dict) and agent in profile:
                model = profile[agent]
                if is_valid_model(model):
                    return model

    # Priority 3: Config default profile
    default_profile = config.get("default_profile", "premium")
    if default_profile:
        profiles = config.get("profiles", {})
        if isinstance(profiles, dict) and default_profile in profiles:
            profile = profiles[default_profile]
            if isinstance(profile, dict) and agent in profile:
                model = profile[agent]
                if is_valid_model(model):
                    return model

    # Priority 4: Hardcoded agent default
    return AGENT_DEFAULTS.get(agent, "opus")


# ── Main ────────────────────────────────────────────────────────────────────

state = parse_simple_yaml(state_path)
config = parse_simple_yaml(config_path)
model = resolve(agent_name, state, config)

# Safety gate: Claude-only agents cannot use external models
if agent_name in CLAUDE_ONLY_AGENTS and is_external(model):
    fallback = AGENT_DEFAULTS.get(agent_name, "opus")
    print(
        f"Warning: {agent_name} requires Claude (tool access). "
        f"Ignoring '{model}', falling back to '{fallback}'.",
        file=sys.stderr,
    )
    model = fallback

print(normalize_model(model))
PYEOF
