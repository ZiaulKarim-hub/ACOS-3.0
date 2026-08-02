#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
# run-external-agent.py — Execute an ACOS agent on a non-Claude model
# ═══════════════════════════════════════════════════════════════════════════════
#
# Calls an external model (OpenAI, Gemini, OpenRouter, etc.) with an ACOS agent's
# system prompt and a task prompt. Bundles file contents into the prompt since
# external models don't have tool access.
#
# Usage:
#   python3 .claude/scripts/run-external-agent.py \
#     --agent qa-reviewer \
#     --model "openai:gpt-4o" \
#     --task "Review slice S1-001..." \
#     [--context file1.py file2.py ...] \
#     [--providers .acos/config/providers.yaml] \
#     [--agents-dir .claude/agents] \
#     [--max-tokens 4096] \
#     [--temperature 0.2]
#
# Output: The model's response text (stdout). Errors go to stderr.
# Exit codes: 0 = success, 1 = usage error, 2 = API error, 3 = config error
#
# Python 3 stdlib only — no pip dependencies.
# ═══════════════════════════════════════════════════════════════════════════════

import sys
import os
import json
import argparse
import re
import urllib.request
import urllib.error
import ssl


# ── Agent Definition Parser ───────────────────────────────────────────────────

def parse_agent_md(filepath):
    """Extract system prompt and frontmatter from an agent .md file.

    Agent files have YAML frontmatter between --- markers, followed by the
    system prompt in markdown. We extract both.
    """
    if not os.path.isfile(filepath):
        return None, None

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Split frontmatter from body
    parts = content.split("---", 2)
    if len(parts) >= 3:
        frontmatter_raw = parts[1].strip()
        system_prompt = parts[2].strip()
    else:
        frontmatter_raw = ""
        system_prompt = content.strip()

    # Parse frontmatter minimally (key: value pairs)
    frontmatter = {}
    for line in frontmatter_raw.split("\n"):
        if ":" in line:
            key, _, val = line.partition(":")
            frontmatter[key.strip()] = val.strip()

    return frontmatter, system_prompt


# ── Provider Config Parser ────────────────────────────────────────────────────

def parse_providers_yaml(filepath):
    """Parse providers.yaml using a minimal YAML parser (stdlib only).

    Returns dict of provider_name -> {type, api_base, api_key_env, extra_headers, ...}
    """
    if not os.path.isfile(filepath):
        return {}

    providers = {}
    current_provider = None
    current_key = None
    current_list = None

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.rstrip()

            # Skip empty lines and comments
            if not stripped or stripped.lstrip().startswith("#"):
                continue

            indent = len(line) - len(line.lstrip())

            # Top-level key (e.g., "providers:")
            if indent == 0 and stripped.startswith("providers:"):
                continue

            # Provider name (indent 2, e.g., "  openai:")
            if indent == 2 and ":" in stripped:
                key, _, val = stripped.strip().partition(":")
                val = val.strip()
                if not val:
                    current_provider = key.strip()
                    providers[current_provider] = {}
                    current_key = None
                    current_list = None

            # Provider property (indent 4, e.g., "    api_base: ...")
            elif indent == 4 and current_provider and ":" in stripped:
                key, _, val = stripped.strip().partition(":")
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if val:
                    providers[current_provider][key] = val
                else:
                    # Could be a list or sub-map
                    providers[current_provider][key] = []
                    current_key = key
                    current_list = providers[current_provider][key]

            # List item or sub-map value (indent 6)
            elif indent == 6 and current_provider:
                item = stripped.strip()
                if item.startswith("- "):
                    # List item
                    item_val = item[2:].strip().strip('"').strip("'")
                    if current_key and isinstance(providers[current_provider].get(current_key), list):
                        providers[current_provider][current_key].append(item_val)
                elif ":" in item:
                    # Sub-map (e.g., extra_headers)
                    key, _, val = item.partition(":")
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    if current_key:
                        container = providers[current_provider].get(current_key)
                        if isinstance(container, list):
                            # Convert to dict on first sub-key
                            providers[current_provider][current_key] = {key: val}
                        elif isinstance(container, dict):
                            container[key] = val

    return providers


# ── Context Bundler ───────────────────────────────────────────────────────────

# Sensitive file patterns — never send to external APIs
SENSITIVE_PATTERNS = {
    ".env", ".env.local", ".env.production", ".env.development",
    "credentials.json", "credentials.yaml", "credentials.yml",
    "providers.yaml",  # Contains API key env var names
}
SENSITIVE_EXTENSIONS = {".key", ".pem", ".p12", ".pfx", ".jks", ".keystore"}


def _is_sensitive_file(path):
    """Check if a file path matches sensitive file patterns."""
    basename = os.path.basename(path)
    _, ext = os.path.splitext(basename)
    if basename in SENSITIVE_PATTERNS or basename.startswith(".env"):
        return True
    if ext in SENSITIVE_EXTENSIONS:
        return True
    return False


def bundle_context_files(file_paths, max_chars_per_file=50000):
    """Read files and format them as a code context block for the prompt.

    External models can't use Read/Grep tools, so we pre-bundle file contents
    into the prompt text. Sensitive files are filtered out to prevent
    credential leakage to external APIs.
    """
    if not file_paths:
        return ""

    sections = []
    for path in file_paths:
        if _is_sensitive_file(path):
            print(
                f"[external-agent] Skipping sensitive file: {path}",
                file=sys.stderr,
            )
            sections.append(f"\n### File: {path}\n(filtered: sensitive file)\n")
            continue
        if not os.path.isfile(path):
            sections.append(f"\n### File: {path}\n(file not found)\n")
            continue

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read(max_chars_per_file)
                if len(content) == max_chars_per_file:
                    content += "\n... (truncated)"
        except (IOError, OSError) as e:
            sections.append(f"\n### File: {path}\n(error reading: {e})\n")
            continue

        # Detect language for code fence
        ext = os.path.splitext(path)[1].lstrip(".")
        lang_map = {
            "py": "python", "js": "javascript", "ts": "typescript",
            "tsx": "tsx", "jsx": "jsx", "rs": "rust", "go": "go",
            "java": "java", "rb": "ruby", "sh": "bash", "yaml": "yaml",
            "yml": "yaml", "json": "json", "md": "markdown", "sql": "sql",
            "html": "html", "css": "css", "toml": "toml",
        }
        lang = lang_map.get(ext, ext or "text")

        sections.append(f"\n### File: {path}\n```{lang}\n{content}\n```\n")

    if not sections:
        return ""

    return (
        "\n\n---\n## Code Context\n"
        "The following files are provided for your review. "
        "Since you don't have direct file system access, all relevant code "
        "is included below.\n"
        + "".join(sections)
    )


# ── External Model Adaptation ─────────────────────────────────────────────────

def adapt_system_prompt(system_prompt, agent_name):
    """Adapt the agent system prompt for external (non-Claude) execution.

    Removes references to Claude Code tools since external models can't use them.
    Adds a note about operating in text-only mode.
    """
    adaptation_note = (
        "\n\n## External Execution Mode\n\n"
        "You are running as an ACOS agent via API call (not inside Claude Code). "
        "You do NOT have access to tools like Read, Grep, Glob, or Bash. "
        "All relevant code and context has been pre-bundled into the task prompt. "
        "Base your analysis entirely on the provided content.\n\n"
        "Your response format should match the Return Value specification below.\n"
    )

    # Insert adaptation note after the first heading
    lines = system_prompt.split("\n")
    inserted = False
    result = []
    for line in lines:
        result.append(line)
        if not inserted and line.startswith("# "):
            result.append(adaptation_note)
            inserted = True

    if not inserted:
        result.insert(0, adaptation_note)

    return "\n".join(result)


# ── API Caller ────────────────────────────────────────────────────────────────

def call_openai_compatible(api_base, api_key, model_name, system_prompt,
                           user_prompt, max_tokens=4096, temperature=0.2,
                           extra_headers=None):
    """Call an OpenAI-compatible chat completions endpoint.

    Works with: OpenAI, OpenRouter, Google Gemini, Ollama, vLLM,
    text-generation-inference, and any other OpenAI-compatible server.
    """
    url = f"{api_base.rstrip('/')}/chat/completions"

    headers = {
        "Content-Type": "application/json",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    if extra_headers and isinstance(extra_headers, dict):
        headers.update(extra_headers)

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    # Param shim: reasoning-family models (o1/o3/o4/gpt-5.x) use
    # `max_completion_tokens` and reject a custom `temperature`. Classic chat
    # models keep `max_tokens` + `temperature`.
    if is_reasoning_model(model_name):
        payload["max_completion_tokens"] = max_tokens
    else:
        payload["max_tokens"] = max_tokens
        payload["temperature"] = temperature

    data = json.dumps(payload).encode("utf-8")

    # Allow self-signed certs for local endpoints (Ollama, vLLM)
    # Use urlparse to check hostname only — substring match could be bypassed
    # (e.g., "https://evil.com/localhost" or "https://localhost.evil.com")
    from urllib.parse import urlparse
    ctx = ssl.create_default_context()
    parsed_host = urlparse(api_base).hostname or ""
    if parsed_host in ("localhost", "127.0.0.1", "::1"):
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=120, context=ctx) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = ""
        try:
            error_body = e.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        print(f"API error {e.code}: {error_body}", file=sys.stderr)
        sys.exit(2)
    except urllib.error.URLError as e:
        print(f"Connection error: {e.reason}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"Request failed: {e}", file=sys.stderr)
        sys.exit(2)

    # Extract response text
    choices = body.get("choices", [])
    if not choices:
        print("API returned no choices", file=sys.stderr)
        sys.exit(2)

    message = choices[0].get("message", {})
    content = message.get("content", "")

    # The API may return content as JSON null (-> Python None) or empty string,
    # e.g. when the model produced only tool calls or hit a content filter.
    # Never let "None"/"" reach stdout as the agent's verdict — treat as an error.
    if content is None or (isinstance(content, str) and not content.strip()):
        print(
            "API returned empty/null message content (no usable response text)",
            file=sys.stderr,
        )
        sys.exit(2)

    # Log usage to stderr for cost tracking
    usage = body.get("usage", {})
    if usage:
        print(
            f"[tokens] prompt={usage.get('prompt_tokens', '?')} "
            f"completion={usage.get('completion_tokens', '?')} "
            f"total={usage.get('total_tokens', '?')}",
            file=sys.stderr,
        )

    return content


# ── Model Spec Parser ─────────────────────────────────────────────────────────

def parse_model_spec(model_spec):
    """Parse 'provider:model' into (provider, model_name).

    Bare names (opus, sonnet, haiku) are treated as claude:name.
    Handles OpenRouter's slash format: openrouter:google/gemini-2.5-pro
    """
    claude_shorthand = {"opus", "sonnet", "haiku"}

    if model_spec in claude_shorthand:
        return "claude", model_spec

    if ":" in model_spec:
        provider, _, model = model_spec.partition(":")
        return provider.strip(), model.strip()

    # Unknown bare name — assume claude
    return "claude", model_spec


def is_reasoning_model(model_name):
    """True for OpenAI reasoning-family models (o1/o3/o4/gpt-5.x).

    These endpoints reject the classic `max_tokens` field (they require
    `max_completion_tokens`) and reject any non-default `temperature`. Detect by
    the final path segment so vendor-prefixed OpenRouter names also match
    (e.g. 'openai/gpt-5.6-sol').
    """
    base = model_name.lower().split("/")[-1]
    return base.startswith(("o1", "o3", "o4", "gpt-5"))


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Run an ACOS agent on an external (non-Claude) model"
    )
    parser.add_argument(
        "--agent", required=True,
        help="Agent name (e.g., qa-reviewer, security-reviewer)"
    )
    parser.add_argument(
        "--model", required=True,
        help="Model spec as provider:model (e.g., openai:gpt-4o, openrouter:google/gemini-2.5-pro)"
    )
    parser.add_argument(
        "--task", required=True,
        help="Task prompt to send to the agent"
    )
    parser.add_argument(
        "--context", nargs="*", default=[],
        help="File paths to bundle as code context"
    )
    parser.add_argument(
        "--providers", default=".acos/config/providers.yaml",
        help="Path to providers config (default: .acos/config/providers.yaml)"
    )
    parser.add_argument(
        "--agents-dir", default=".claude/agents",
        help="Directory containing agent .md files (default: .claude/agents)"
    )
    parser.add_argument(
        "--max-tokens", type=int, default=0,
        help="Max tokens for response (0 = use provider default)"
    )
    parser.add_argument(
        "--temperature", type=float, default=0.2,
        help="Temperature for generation (default: 0.2)"
    )

    args = parser.parse_args()

    # ── Validate agent ────────────────────────────────────────────────────
    agent_path = os.path.join(args.agents_dir, f"{args.agent}.md")
    frontmatter, system_prompt = parse_agent_md(agent_path)
    if system_prompt is None:
        print(f"Agent definition not found: {agent_path}", file=sys.stderr)
        sys.exit(1)

    # ── Parse model spec ──────────────────────────────────────────────────
    provider, model_name = parse_model_spec(args.model)

    if provider == "claude":
        print(
            "Error: Claude models should use Task(), not run-external-agent.py",
            file=sys.stderr,
        )
        sys.exit(1)

    # ── Load provider config ──────────────────────────────────────────────
    providers = parse_providers_yaml(args.providers)
    provider_config = providers.get(provider)

    if not provider_config:
        print(
            f"Unknown provider '{provider}'. Available: {', '.join(providers.keys())}",
            file=sys.stderr,
        )
        sys.exit(3)

    provider_type = provider_config.get("type", "")
    if provider_type != "openai-compatible":
        print(
            f"Provider '{provider}' has unsupported type: {provider_type}",
            file=sys.stderr,
        )
        sys.exit(3)

    # Resolve API base (direct value or env var)
    api_base = provider_config.get("api_base", "")
    if not api_base:
        api_base_env = provider_config.get("api_base_env", "")
        if api_base_env:
            api_base = os.environ.get(api_base_env, "")
    if not api_base:
        print(
            f"No api_base configured for provider '{provider}'. "
            f"Set it in {args.providers} or via environment variable.",
            file=sys.stderr,
        )
        sys.exit(3)

    # Resolve API key
    api_key_env = provider_config.get("api_key_env", "")
    api_key = os.environ.get(api_key_env, "") if api_key_env else ""
    if not api_key and provider != "custom":
        print(
            f"Warning: No API key found. Set {api_key_env} environment variable.",
            file=sys.stderr,
        )

    # Extra headers (e.g., OpenRouter requires HTTP-Referer)
    extra_headers = provider_config.get("extra_headers")
    if isinstance(extra_headers, list):
        extra_headers = None  # Was parsed as empty list, not a dict

    # Max tokens
    max_tokens = args.max_tokens
    if max_tokens <= 0:
        default_str = provider_config.get("default_max_tokens", "4096")
        try:
            max_tokens = int(default_str)
        except (ValueError, TypeError):
            max_tokens = 4096

    # ── Build prompt ──────────────────────────────────────────────────────
    adapted_prompt = adapt_system_prompt(system_prompt, args.agent)
    context_block = bundle_context_files(args.context)
    user_prompt = args.task + context_block

    # ── Call API ──────────────────────────────────────────────────────────
    print(
        f"[external-agent] Calling {provider}:{model_name} as {args.agent}...",
        file=sys.stderr,
    )

    response = call_openai_compatible(
        api_base=api_base,
        api_key=api_key,
        model_name=model_name,
        system_prompt=adapted_prompt,
        user_prompt=user_prompt,
        max_tokens=max_tokens,
        temperature=args.temperature,
        extra_headers=extra_headers,
    )

    # ── Output ────────────────────────────────────────────────────────────
    print(response)


if __name__ == "__main__":
    main()
