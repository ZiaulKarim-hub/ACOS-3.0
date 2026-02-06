# ACOS Automation Scripts

This directory contains automation scripts for ACOS v3.0.

## Main CLI

### `acos`

The main command-line interface for ACOS.

```bash
# Add to your PATH
export PATH="$PATH:/path/to/ACOS 3.0/automation-scripts"

# Or create a symlink
ln -s "/path/to/ACOS 3.0/automation-scripts/acos" /usr/local/bin/acos
```

**Commands:**

| Command | Description |
|---------|-------------|
| `acos init` | Initialize ACOS in current project |
| `acos start` | Start a new vision interview |
| `acos status` | Show current project status |
| `acos agents [list\|show <name>]` | List or show agents |
| `acos skills [list]` | List available skills |
| `acos flows [list]` | List available flows |
| `acos memory [search <query>\|list]` | Memory commands |
| `acos learn [list\|search <query>]` | Learning curve commands |
| `acos review [rules\|pending]` | Review commands |
| `acos help` | Show help |

## Helper Scripts

### `create-evidence-bundle.sh`

Creates the evidence bundle structure for a slice.

```bash
./create-evidence-bundle.sh SLICE-001
```

Creates:
```
.acos/evidence/[DATE]/SLICE-001/
├── before/
│   └── baseline-status.log
├── after/
├── verify.log (template)
└── Summary.md (template)
```

### `capture-evidence.sh`

Captures the "after" state for an evidence bundle.

```bash
./capture-evidence.sh SLICE-001
```

Captures:
- Modified files list
- Git diff
- Instructions for test/build capture

## Usage in Workflow

1. **Start work:**
   ```bash
   ./create-evidence-bundle.sh SLICE-001
   ```

2. **Implement the slice** (write code)

3. **Capture completion state:**
   ```bash
   ./capture-evidence.sh SLICE-001
   ```

4. **Run tests and build**, save output to evidence bundle

5. **Update Summary.md and verify.log**

6. **Create handoff** to reviewer

## Integration with Claude Code

These scripts are designed to be used alongside Claude Code. The typical workflow:

1. User describes vision to Claude Code
2. Architect conducts interview, creates plan
3. For each slice:
   - Developer creates evidence bundle
   - Developer implements code
   - Developer captures evidence
   - Developer creates handoff
   - Reviewers review
   - Feedback resolved (if needed)
4. Continue until project complete
