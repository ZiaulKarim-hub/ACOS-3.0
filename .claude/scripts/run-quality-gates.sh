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
export CONFIG STAGE
python3 << 'PYTHON'
import yaml, json, subprocess, sys, os

config_path = os.environ.get("CONFIG", ".acos/config/quality-gates.yaml")
stage_filter = os.environ.get("STAGE", "")

try:
    with open(config_path) as f:
        data = yaml.safe_load(f)
except Exception as e:
    print(json.dumps({"passed": True, "results": [], "error": str(e)}))
    sys.exit(0)

gates = data.get("gates", {})
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
        result = subprocess.run(
            command,
            shell=True,
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
