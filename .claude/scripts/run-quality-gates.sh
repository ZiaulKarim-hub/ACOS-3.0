#!/bin/bash
# Reads .acos/config/quality-gates.yaml and runs each gate's command.
# Optionally filters by stage via first argument (e.g., "pre-review").
# Outputs JSON: {"passed": true/false, "results": [{name, command, passed, output}]}
# Exit 0 always (caller decides what to do with the JSON).
# If no config file exists, outputs {"passed": true, "results": []} (fail-open).

CONFIG=".acos/config/quality-gates.yaml"
STAGE="${1:-}"

# Fail-open: no config = all clear
if [ ! -f "$CONFIG" ]; then
  echo '{"passed": true, "results": [], "skipped": true}'
  exit 0
fi

# Parse config and run gates
# Uses stdlib-only YAML parsing (no PyYAML dependency)
# Uses shlex.split + shell=False to prevent command injection via config
export CONFIG STAGE
python3 << 'PYTHON'
import json, subprocess, sys, os, re, shlex

config_path = os.environ.get("CONFIG", ".acos/config/quality-gates.yaml")
stage_filter = os.environ.get("STAGE", "")

# ── Minimal stdlib YAML parser ─────────────────────────────────────────
# Handles the simple structure of quality-gates.yaml:
#   gates:
#     lint:
#       command: "npm run lint"
#       required: true
#       stage: "pre-review"
def parse_quality_gates_yaml(filepath):
    """Parse quality-gates.yaml using regex (no PyYAML dependency)."""
    try:
        with open(filepath, "r") as f:
            text = f.read()
    except Exception as e:
        return None, str(e)

    gates = {}
    # Find each gate block: indented name followed by properties
    # Pattern: 2-space indented key (gate name), then 4-space indented properties
    gate_pattern = re.compile(r'^  (\w[\w-]*):\s*$', re.MULTILINE)
    prop_pattern = re.compile(r'^    (\w+):\s*(.+)$', re.MULTILINE)

    gate_positions = [(m.group(1), m.start()) for m in gate_pattern.finditer(text)]

    for i, (gate_name, start_pos) in enumerate(gate_positions):
        end_pos = gate_positions[i + 1][1] if i + 1 < len(gate_positions) else len(text)
        block = text[start_pos:end_pos]

        gate_config = {}
        for prop_match in prop_pattern.finditer(block):
            key = prop_match.group(1)
            val = prop_match.group(2).strip().strip('"').strip("'")
            if key == "required":
                gate_config[key] = val.lower() in ("true", "yes", "1")
            else:
                gate_config[key] = val

        gates[gate_name] = gate_config

    return gates, None

# ── Parse config ────────────────────────────────────────────────────────
gates, parse_error = parse_quality_gates_yaml(config_path)
if gates is None:
    print(json.dumps({"passed": True, "results": [], "error": parse_error}))
    sys.exit(0)

results = []
all_required_passed = True

for name, gate in gates.items():
    command = gate.get("command", "")
    required = gate.get("required", False)
    gate_stage = gate.get("stage", "")

    # Filter by stage if specified
    if stage_filter and gate_stage != stage_filter:
        continue

    if not command:
        continue

    try:
        # Use shlex.split + shell=False to prevent command injection
        cmd_parts = shlex.split(command)
        result = subprocess.run(
            cmd_parts,
            shell=False,
            capture_output=True,
            text=True,
            timeout=300
        )
        passed = result.returncode == 0
        output = result.stdout[-2000:] if result.stdout else ""
        error = result.stderr[-2000:] if result.stderr else ""
    except subprocess.TimeoutExpired:
        passed = False
        output = ""
        error = "Gate timed out after 300 seconds"
    except Exception as e:
        passed = False
        output = ""
        error = str(e)

    if required and not passed:
        all_required_passed = False

    results.append({
        "name": name,
        "command": command,
        "required": required,
        "stage": gate_stage,
        "passed": passed,
        "output": output,
        "error": error
    })

print(json.dumps({
    "passed": all_required_passed,
    "results": results
}, indent=2))
PYTHON
