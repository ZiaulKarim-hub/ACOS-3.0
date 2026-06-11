#!/bin/bash

# ═══════════════════════════════════════════════════════════════════════════
# ACOS v3.0 - Project Bootstrap / Auto-Initialization
# ═══════════════════════════════════════════════════════════════════════════
#
# Usage: acos-bootstrap.sh [--force] [--all-skills]
#
# Automatically initializes ACOS in the current working directory.
# Symlinks orchestration infrastructure from ACOS 3.0 source.
# SELECTIVELY links methodology skills based on detected tech stack.
# Creates data directories, project config, and gitignore entries.
#
# --force:       Re-initialize even if .acos/ already exists
# --all-skills:  Link ALL skills regardless of tech stack detection
#
# ═══════════════════════════════════════════════════════════════════════════

set -e

# ── Configuration ─────────────────────────────────────────────────────────

# Resolve symlinks to find the REAL script location (in ACOS source tree).
# When bootstrap is symlinked into a child project, BASH_SOURCE[0] is the
# symlink path. We follow it to find the actual ACOS root.
REAL_SCRIPT="${BASH_SOURCE[0]}"
while [[ -L "$REAL_SCRIPT" ]]; do
  LINK_TARGET="$(readlink "$REAL_SCRIPT")"
  # Handle relative symlinks
  if [[ "$LINK_TARGET" != /* ]]; then
    LINK_TARGET="$(dirname "$REAL_SCRIPT")/$LINK_TARGET"
  fi
  REAL_SCRIPT="$LINK_TARGET"
done
SCRIPT_DIR="$(cd "$(dirname "$REAL_SCRIPT")" && pwd)"
ACOS_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PROJECT_DIR="$(pwd)"

# Flags
FORCE=false
QUIET=false
ALL_SKILLS=false
for arg in "$@"; do
  case $arg in
    --force) FORCE=true ;;
    --quiet) QUIET=true ;;
    --all-skills) ALL_SKILLS=true ;;
  esac
done

# ── Colors ────────────────────────────────────────────────────────────────

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
DIM='\033[2m'
BOLD='\033[1m'
NC='\033[0m'

log()      { [[ "$QUIET" == false ]] && echo -e "$1"; }
log_step() { log "${CYAN}  ▸${NC} $1"; }
log_ok()   { log "${GREEN}  ✓${NC} $1"; }
log_warn() { log "${YELLOW}  ⚠${NC} $1"; }
log_skip() { log "  · $1 ${DIM}(skipped)${NC}"; }

# ── Guard: Don't initialize inside ACOS itself ────────────────────────────

if [[ "$PROJECT_DIR" == "$ACOS_ROOT" ]]; then
  log "${YELLOW}Already inside ACOS 3.0 source directory. Nothing to do.${NC}"
  exit 0
fi

# ── Guard: Already initialized ────────────────────────────────────────────

if [[ -d "$PROJECT_DIR/.acos" && "$FORCE" == false ]]; then
  BROKEN=false
  # Probe a representative link from EACH category (agents/, skills/, scripts/)
  # so a broken link in any category triggers repair — not just architect.md.
  for link in "$PROJECT_DIR/.claude/agents/architect.md" \
              "$PROJECT_DIR/.claude/agents/developer.md" \
              "$PROJECT_DIR/.claude/skills/acos-start" \
              "$PROJECT_DIR/.claude/scripts/resolve-agent-model.sh"; do
    if [[ -L "$link" && ! -e "$link" ]]; then
      BROKEN=true
      break
    fi
  done

  if [[ "$BROKEN" == true ]]; then
    log "${YELLOW}ACOS detected but symlinks are broken. Re-initializing...${NC}"
  else
    log "${GREEN}ACOS already initialized in this project.${NC}"
    exit 0
  fi
fi

# ═══════════════════════════════════════════════════════════════════════════
# TECH STACK DETECTION (runs early — drives skill selection)
# ═══════════════════════════════════════════════════════════════════════════

PROJECT_NAME="$(basename "$PROJECT_DIR")"
TECH_STACK="unknown"
PACKAGE_MANAGER="npm"
TEST_RUNNER="unknown"
LINTER="unknown"

# Feature flags for skill selection
HAS_FRONTEND=false
HAS_BACKEND=false
HAS_DATABASE=false
HAS_API=false
HAS_TESTS=false

# ── Detect from package.json ──────────────────────────────────────────────

if [[ -f "$PROJECT_DIR/package.json" ]]; then
  PKG_NAME=$(grep -o '"name"[[:space:]]*:[[:space:]]*"[^"]*"' "$PROJECT_DIR/package.json" | head -1 | sed 's/.*"name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/')
  [[ -n "$PKG_NAME" ]] && PROJECT_NAME="$PKG_NAME"

  # Framework detection
  if grep -q '"next"' "$PROJECT_DIR/package.json" 2>/dev/null; then
    TECH_STACK="nextjs"; HAS_FRONTEND=true; HAS_BACKEND=true; HAS_API=true
  elif grep -q '"nuxt"' "$PROJECT_DIR/package.json" 2>/dev/null; then
    TECH_STACK="nuxt"; HAS_FRONTEND=true; HAS_BACKEND=true; HAS_API=true
  elif grep -q '"svelte"' "$PROJECT_DIR/package.json" 2>/dev/null; then
    TECH_STACK="svelte"; HAS_FRONTEND=true
  elif grep -q '"react"' "$PROJECT_DIR/package.json" 2>/dev/null; then
    TECH_STACK="react"; HAS_FRONTEND=true
  elif grep -q '"vue"' "$PROJECT_DIR/package.json" 2>/dev/null; then
    TECH_STACK="vue"; HAS_FRONTEND=true
  elif grep -q '"angular"' "$PROJECT_DIR/package.json" 2>/dev/null; then
    TECH_STACK="angular"; HAS_FRONTEND=true
  fi

  # Backend detection
  if grep -qE '"express"|"fastify"|"hono"|"koa"|"nestjs"|"convex"' "$PROJECT_DIR/package.json" 2>/dev/null; then
    HAS_BACKEND=true; HAS_API=true
  fi

  # Database detection
  if grep -qE '"prisma"|"drizzle"|"typeorm"|"sequelize"|"mongoose"|"convex"|"knex"|"@supabase"' "$PROJECT_DIR/package.json" 2>/dev/null; then
    HAS_DATABASE=true
  fi

  # Package manager
  if [[ -f "$PROJECT_DIR/pnpm-lock.yaml" ]]; then PACKAGE_MANAGER="pnpm"
  elif [[ -f "$PROJECT_DIR/yarn.lock" ]]; then PACKAGE_MANAGER="yarn"
  elif [[ -f "$PROJECT_DIR/bun.lock" || -f "$PROJECT_DIR/bun.lockb" ]]; then PACKAGE_MANAGER="bun"
  fi

  # Test runner
  if grep -q '"vitest"' "$PROJECT_DIR/package.json" 2>/dev/null; then
    TEST_RUNNER="vitest"; HAS_TESTS=true
  elif grep -q '"jest"' "$PROJECT_DIR/package.json" 2>/dev/null; then
    TEST_RUNNER="jest"; HAS_TESTS=true
  elif grep -q '"mocha"' "$PROJECT_DIR/package.json" 2>/dev/null; then
    TEST_RUNNER="mocha"; HAS_TESTS=true
  elif grep -q '"playwright"' "$PROJECT_DIR/package.json" 2>/dev/null; then
    TEST_RUNNER="playwright"; HAS_TESTS=true
  elif grep -q '"cypress"' "$PROJECT_DIR/package.json" 2>/dev/null; then
    TEST_RUNNER="cypress"; HAS_TESTS=true
  fi

  # Linter
  if grep -q '"@biomejs/biome"' "$PROJECT_DIR/package.json" 2>/dev/null; then LINTER="biome"
  elif grep -q '"eslint"' "$PROJECT_DIR/package.json" 2>/dev/null; then LINTER="eslint"
  fi
fi

# ── Detect from Python ────────────────────────────────────────────────────

if [[ -f "$PROJECT_DIR/pyproject.toml" || -f "$PROJECT_DIR/setup.py" || -f "$PROJECT_DIR/requirements.txt" ]]; then
  TECH_STACK="python"; HAS_BACKEND=true
  PACKAGE_MANAGER="pip"
  [[ -f "$PROJECT_DIR/poetry.lock" ]] && PACKAGE_MANAGER="poetry"
  [[ -f "$PROJECT_DIR/uv.lock" ]] && PACKAGE_MANAGER="uv"

  if grep -qE "django|flask|fastapi|starlette" "$PROJECT_DIR/pyproject.toml" 2>/dev/null || \
     grep -qE "django|flask|fastapi|starlette" "$PROJECT_DIR/requirements.txt" 2>/dev/null; then
    HAS_API=true
  fi
  if grep -qE "sqlalchemy|django|tortoise|peewee|prisma" "$PROJECT_DIR/pyproject.toml" 2>/dev/null; then
    HAS_DATABASE=true
  fi
  if grep -q "pytest" "$PROJECT_DIR/pyproject.toml" 2>/dev/null; then
    TEST_RUNNER="pytest"; HAS_TESTS=true
  fi
  if grep -q "ruff" "$PROJECT_DIR/pyproject.toml" 2>/dev/null; then LINTER="ruff"; fi
fi

# ── Detect from Rust ──────────────────────────────────────────────────────

if [[ -f "$PROJECT_DIR/Cargo.toml" ]]; then
  TECH_STACK="rust"; HAS_BACKEND=true
  PACKAGE_MANAGER="cargo"; TEST_RUNNER="cargo-test"; LINTER="clippy"; HAS_TESTS=true
  if grep -qE "actix|axum|rocket|warp" "$PROJECT_DIR/Cargo.toml" 2>/dev/null; then HAS_API=true; fi
  if grep -qE "diesel|sqlx|sea-orm" "$PROJECT_DIR/Cargo.toml" 2>/dev/null; then HAS_DATABASE=true; fi
fi

# ── Detect from Go ────────────────────────────────────────────────────────

if [[ -f "$PROJECT_DIR/go.mod" ]]; then
  TECH_STACK="go"; HAS_BACKEND=true; HAS_API=true
  PACKAGE_MANAGER="go-modules"; TEST_RUNNER="go-test"; LINTER="golangci-lint"; HAS_TESTS=true
  if grep -qE "gorm|sqlx|ent" "$PROJECT_DIR/go.mod" 2>/dev/null; then HAS_DATABASE=true; fi
fi

# ═══════════════════════════════════════════════════════════════════════════
# SKILL SELECTION (based on detection)
# ═══════════════════════════════════════════════════════════════════════════

# Tier 1: Core ACOS orchestration — ALWAYS linked
CORE_SKILLS=(
  "acos-start"
  "acos-interview"
  "acos-plan"
  "acos-execute-slice"
  "acos-execute-story"
  "acos-execute-epic"
  "acos-complete"
  "acos-complete-vision"
  "acos-review"
  "acos-status"
  "acos-decide"
  "acos-handoff-protocol"
  "acos-learn"
  "acos-feedback-resolution"
  "acos-add-skills"
  "acos-embed-skills"
  "acos-oracle-protocol"
  "acos-model-change"
  "acos-update"
  "acos-electronics-repair"
)

# Tier 2: Universal methodology — ALWAYS linked (useful for any project)
UNIVERSAL_SKILLS=(
  "security-audit"
  "bug-investigation"
  "codebase-analysis"
  "testing"
)

# Tier 3: Conditional methodology — linked based on detected tech stack
CONDITIONAL_SKILLS=()

if [[ "$HAS_FRONTEND" == true ]]; then
  CONDITIONAL_SKILLS+=("frontend-coding")
fi

if [[ "$HAS_BACKEND" == true ]]; then
  CONDITIONAL_SKILLS+=("backend-coding")
fi

if [[ "$HAS_DATABASE" == true ]]; then
  CONDITIONAL_SKILLS+=("database-design")
fi

if [[ "$HAS_API" == true ]]; then
  CONDITIONAL_SKILLS+=("api-documentation")
fi

# Tier 4: On-demand — only linked with --all-skills flag
ONDEMAND_SKILLS=(
  "deployment"
  "ci-cd-generation"
  "mcp-setup"
  "user-guide-writing"
  "domain-security-profile"
  "quality-gates"
  "technology-research"
)

# Tier 5: Meta/ACOS-internal — only linked with --all-skills flag
META_SKILLS=(
  "agent-creation"
  "orchestration-creation"
)

# Build final skill list
SELECTED_SKILLS=("${CORE_SKILLS[@]}" "${UNIVERSAL_SKILLS[@]}" "${CONDITIONAL_SKILLS[@]}")

if [[ "$ALL_SKILLS" == true ]]; then
  SELECTED_SKILLS+=("${ONDEMAND_SKILLS[@]}" "${META_SKILLS[@]}")
fi

# ═══════════════════════════════════════════════════════════════════════════
log ""
log "${BOLD}═══════════════════════════════════════════════════════════════${NC}"
log "${BOLD}  ACOS v3.0 — Auto-Initializing Project${NC}"
log "${BOLD}═══════════════════════════════════════════════════════════════${NC}"
log ""
log "  Source:  ${CYAN}$ACOS_ROOT${NC}"
log "  Target:  ${CYAN}$PROJECT_DIR${NC}"
log "  Stack:   ${CYAN}$TECH_STACK${NC}"
log ""

# ═══════════════════════════════════════════════════════════════════════════
# STEP 1: Create data directories
# ═══════════════════════════════════════════════════════════════════════════

log "${BOLD}[1/8] Creating data directories...${NC}"

DATA_DIRS=(
  ".acos/config"
  ".acos/evidence"
  ".acos/metrics"
  "memory/source-of-truth"
  "memory/decisions"
  "memory/reviews/slice-reviews"
  "memory/reviews/story-reviews"
  "memory/reviews/epic-reviews"
  "memory/reviews/vision-reviews"
  "memory/handoffs"
  "memory/handoffs/archive"
  "memory/code-rationale"
  "memory/feedback-history"
  "planning/vision"
  "planning/epics"
  "planning/stories"
  "planning/slices"
  "learning-curve/patterns"
  "learning-curve/anti-patterns"
  "learning-curve/project-retrospectives"
)

for dir in "${DATA_DIRS[@]}"; do
  if [[ ! -d "$PROJECT_DIR/$dir" ]]; then
    mkdir -p "$PROJECT_DIR/$dir"
    log_step "Created $dir/"
  fi
done
log_ok "Data directories ready"
log ""

# ═══════════════════════════════════════════════════════════════════════════
# STEP 2: Symlink agents (all agents — always needed)
# ═══════════════════════════════════════════════════════════════════════════

log "${BOLD}[2/8] Symlinking agents...${NC}"

mkdir -p "$PROJECT_DIR/.claude/agents"

AGENTS=(
  "architect.md"
  "developer.md"
  "integration-reviewer.md"
  "learning-agent.md"
  "memory-agent.md"
  "performance-reviewer.md"
  "qa-reviewer.md"
  "security-reviewer.md"
)

SYMLINKED_AGENTS=()
SYMLINKED_SKILLS_LIST=()
SYMLINKED_SCRIPTS=()

for agent in "${AGENTS[@]}"; do
  src="$ACOS_ROOT/.claude/agents/$agent"
  dest="$PROJECT_DIR/.claude/agents/$agent"

  [[ ! -e "$src" ]] && { log_warn "Source not found: $src"; continue; }

  if [[ -L "$dest" ]]; then
    rm "$dest"
  elif [[ -f "$dest" ]]; then
    log_skip ".claude/agents/$agent (real file exists)"
    continue
  fi

  ln -s "$src" "$dest"
  SYMLINKED_AGENTS+=("$agent")
  log_step "Linked $agent"
done
log_ok "${#SYMLINKED_AGENTS[@]} agents linked"
log ""

# ═══════════════════════════════════════════════════════════════════════════
# STEP 3: Symlink SELECTED skills only
# ═══════════════════════════════════════════════════════════════════════════

log "${BOLD}[3/8] Symlinking skills (selective)...${NC}"

mkdir -p "$PROJECT_DIR/.claude/skills"

SKIPPED_SKILLS=()

for skill_name in "${SELECTED_SKILLS[@]}"; do
  src="$ACOS_ROOT/.claude/skills/$skill_name"
  dest="$PROJECT_DIR/.claude/skills/$skill_name"

  [[ ! -d "$src" ]] && { log_warn "Skill not found: $skill_name"; continue; }

  if [[ -L "$dest" ]]; then
    rm "$dest"
  elif [[ -d "$dest" ]]; then
    log_skip ".claude/skills/$skill_name (real directory exists)"
    continue
  fi

  ln -s "$src" "$dest"
  SYMLINKED_SKILLS_LIST+=("$skill_name")
  log_step "Linked $skill_name"
done

# Count what was NOT linked
ALL_AVAILABLE_SKILLS=()
for skill_dir in "$ACOS_ROOT/.claude/skills"/*/; do
  ALL_AVAILABLE_SKILLS+=("$(basename "$skill_dir")")
done

for avail in "${ALL_AVAILABLE_SKILLS[@]}"; do
  FOUND=false
  for sel in "${SELECTED_SKILLS[@]}"; do
    if [[ "$avail" == "$sel" ]]; then FOUND=true; break; fi
  done
  [[ "$FOUND" == false ]] && SKIPPED_SKILLS+=("$avail")
done

log_ok "${#SYMLINKED_SKILLS_LIST[@]} skills linked, ${#SKIPPED_SKILLS[@]} skipped (not needed for $TECH_STACK)"
if [[ ${#SKIPPED_SKILLS[@]} -gt 0 ]]; then
  log "  ${DIM}Skipped: ${SKIPPED_SKILLS[*]}${NC}"
  log "  ${DIM}Use --all-skills to link everything${NC}"

  # Write skipped skills manifest for interactive menu (CLI reads this)
  SKIPPED_MANIFEST="$PROJECT_DIR/.acos/state/skipped-skills.txt"
  mkdir -p "$PROJECT_DIR/.acos/state"
  > "$SKIPPED_MANIFEST"
  for sk in "${SKIPPED_SKILLS[@]}"; do
    sk_desc=$(sed -n 's/^description: *//p' "$ACOS_ROOT/.claude/skills/$sk/SKILL.md" 2>/dev/null | head -1)
    echo "$sk|$sk_desc" >> "$SKIPPED_MANIFEST"
  done
fi
log ""

# ═══════════════════════════════════════════════════════════════════════════
# STEP 4: Symlink scripts (all scripts — enforcement infrastructure)
# ═══════════════════════════════════════════════════════════════════════════

log "${BOLD}[4/8] Symlinking scripts...${NC}"

mkdir -p "$PROJECT_DIR/.claude/scripts"

for script_file in "$ACOS_ROOT/.claude/scripts"/*; do
  script_name="$(basename "$script_file")"

  if [[ -d "$script_file" ]]; then
    # Directories (like rag/) — symlink as whole dir
    dest="$PROJECT_DIR/.claude/scripts/$script_name"
    if [[ -L "$dest" ]]; then
      rm "$dest"
    elif [[ -d "$dest" ]]; then
      log_skip ".claude/scripts/$script_name (real directory exists)"
      continue
    fi
    ln -s "$script_file" "$dest"
    SYMLINKED_SCRIPTS+=("$script_name/")
    log_step "Linked dir: $script_name/"
    continue
  fi

  dest="$PROJECT_DIR/.claude/scripts/$script_name"
  if [[ -L "$dest" ]]; then
    rm "$dest"
  elif [[ -f "$dest" ]]; then
    log_skip ".claude/scripts/$script_name (real file exists)"
    continue
  fi

  ln -s "$script_file" "$dest"
  SYMLINKED_SCRIPTS+=("$script_name")
  log_step "Linked $script_name"
done
log_ok "${#SYMLINKED_SCRIPTS[@]} scripts linked"
log ""

# ═══════════════════════════════════════════════════════════════════════════
# STEP 5: Merge settings.local.json (hooks)
# ═══════════════════════════════════════════════════════════════════════════

log "${BOLD}[5/8] Configuring hooks...${NC}"

SETTINGS_FILE="$PROJECT_DIR/.claude/settings.local.json"
ACOS_SETTINGS="$ACOS_ROOT/.claude/settings.local.json"

if [[ ! -f "$SETTINGS_FILE" ]]; then
  cp "$ACOS_SETTINGS" "$SETTINGS_FILE"
  log_step "Created settings.local.json with ACOS hooks"
else
  # Always run idempotent merge — adds missing hooks without duplicating existing ones.
  # Previous versions used a sentinel guard (grep check-scope.sh) that skipped the entire
  # merge when ANY ACOS hook was present, preventing new hooks from being propagated.
  log_step "Merging ACOS hooks into existing settings.local.json..."
  MERGE_RESULT=$(python3 - "$SETTINGS_FILE" "$ACOS_SETTINGS" <<'PYEOF'
import json, sys

existing_path, acos_path = sys.argv[1], sys.argv[2]

try:
    with open(existing_path) as f:
        existing = json.load(f)
except (json.JSONDecodeError, FileNotFoundError):
    existing = {}

try:
    with open(acos_path) as f:
        acos = json.load(f)
except (json.JSONDecodeError, FileNotFoundError):
    print('ERROR: Cannot read ACOS settings', file=sys.stderr)
    sys.exit(1)

hooks_added = 0

# Merge permissions: combine allow lists, preserve deny/ask
if 'permissions' in acos:
    if 'permissions' not in existing:
        existing['permissions'] = {}
    for key in ('allow', 'deny', 'ask'):
        if key in acos['permissions']:
            if key not in existing['permissions']:
                existing['permissions'][key] = []
            for perm in acos['permissions'][key]:
                if perm not in existing['permissions'][key]:
                    existing['permissions'][key].append(perm)

# Merge hooks: add ACOS hook types, preserving existing non-ACOS hooks
if 'hooks' in acos:
    if 'hooks' not in existing:
        existing['hooks'] = {}
    for hook_type, hook_entries in acos['hooks'].items():
        if hook_type not in existing['hooks']:
            existing['hooks'][hook_type] = hook_entries
            hooks_added += len(hook_entries)
        else:
            # Extract script names from existing hook commands for fuzzy dedup.
            # This prevents duplicates when commands are reformatted (e.g.,
            # bare "bash .claude/scripts/foo.sh" vs prefixed with git rev-parse).
            import re
            def extract_script_id(cmd):
                """Extract the core script filename from a hook command."""
                m = re.search(r'[\w/.-]*\.(?:sh|py)\b', cmd)
                if m:
                    return m.group(0).rsplit('/', 1)[-1]  # just the filename
                return cmd  # fallback to full command

            existing_scripts = set()
            for entry in existing['hooks'][hook_type]:
                for h in entry.get('hooks', []):
                    existing_scripts.add(extract_script_id(h.get('command', '')))
            for entry in hook_entries:
                for h in entry.get('hooks', []):
                    if extract_script_id(h.get('command', '')) not in existing_scripts:
                        existing['hooks'][hook_type].append(entry)
                        hooks_added += 1
                        break

# Enforce ordering: token-gate.sh must be FIRST in PreToolUse
# (it must run before Oracle to gate tool execution on context budget)
if 'PreToolUse' in existing.get('hooks', {}):
    pre_hooks = existing['hooks']['PreToolUse']
    gate_idx = None
    for i, entry in enumerate(pre_hooks):
        for h in entry.get('hooks', []):
            if 'token-gate.sh' in h.get('command', ''):
                gate_idx = i
                break
        if gate_idx is not None:
            break
    if gate_idx is not None and gate_idx != 0:
        gate_entry = pre_hooks.pop(gate_idx)
        pre_hooks.insert(0, gate_entry)

if 'outputStyle' in acos and 'outputStyle' not in existing:
    existing['outputStyle'] = acos['outputStyle']

# Output the count as first line of stdout, then the JSON
print(f'HOOKS_ADDED:{hooks_added}')
print(json.dumps(existing, indent=2))
PYEOF
)

    # Parse hooks_added count from first line, JSON from remaining lines.
    # Sanitize to digits only so a non-numeric value can't make the later
    # arithmetic test (-eq 0) error out under set -e.
    HOOKS_ADDED=$(echo "$MERGE_RESULT" | sed -n 's/^HOOKS_ADDED:\([0-9]*\)$/\1/p' | head -1)
    HOOKS_ADDED="${HOOKS_ADDED:-0}"
    MERGE_JSON=$(echo "$MERGE_RESULT" | tail -n +2)

    if [[ -n "$MERGE_JSON" && "$MERGE_JSON" == "{"* ]]; then
      echo "$MERGE_JSON" > "$SETTINGS_FILE"
      if [[ "${HOOKS_ADDED:-0}" -eq 0 ]]; then
        log_ok "ACOS hooks already up to date (0 added)"
      else
        log_ok "Merged $HOOKS_ADDED new hook(s) into settings.local.json"
      fi
    else
      log_warn "Merge failed — copying ACOS settings as reference"
      cp "$ACOS_SETTINGS" "$PROJECT_DIR/.claude/settings.acos-hooks.json"
      log_warn "Manual merge may be needed — check settings.acos-hooks.json"
    fi
fi
log_ok "Hooks configured"
log ""

# ═══════════════════════════════════════════════════════════════════════════
# STEP 6: Copy review-rules.yaml & generate project.yaml
# ═══════════════════════════════════════════════════════════════════════════

log "${BOLD}[6/8] Generating project configuration...${NC}"

# Copy review-rules/ directory (per-reviewer trigger rules, editable per-project)
if [[ ! -d "$PROJECT_DIR/review-rules" ]]; then
  cp -r "$ACOS_ROOT/review-rules" "$PROJECT_DIR/review-rules"
  log_step "Copied review-rules/ directory (4 reviewers + global config)"
else
  log_skip "review-rules/ directory (already exists)"
fi

# Copy review-rules.yaml legacy pointer (for reference only)
if [[ ! -f "$PROJECT_DIR/review-rules.yaml" ]]; then
  if [[ -f "$ACOS_ROOT/review-rules.yaml" ]]; then
    cp "$ACOS_ROOT/review-rules.yaml" "$PROJECT_DIR/review-rules.yaml"
    log_step "Copied review-rules.yaml (legacy pointer)"
  fi
else
  log_skip "review-rules.yaml (already exists)"
fi

# Generate project.yaml
cat > "$PROJECT_DIR/.acos/config/project.yaml" << EOF
# ACOS Project Configuration
# Auto-generated by acos-bootstrap.sh on $(date +%Y-%m-%d)

project:
  name: "$PROJECT_NAME"
  initialized: true
  initialized_at: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  acos_version: "3.0.0"
  acos_source: "$ACOS_ROOT"

toolchain:
  tech_stack: "$TECH_STACK"
  package_manager: "$PACKAGE_MANAGER"
  test_runner: "$TEST_RUNNER"
  linter: "$LINTER"

detected_features:
  has_frontend: $HAS_FRONTEND
  has_backend: $HAS_BACKEND
  has_database: $HAS_DATABASE
  has_api: $HAS_API
  has_tests: $HAS_TESTS

skills_linked:
  core: ${#CORE_SKILLS[@]}
  universal: ${#UNIVERSAL_SKILLS[@]}
  conditional: ${#CONDITIONAL_SKILLS[@]}
  total: ${#SYMLINKED_SKILLS_LIST[@]}
  skipped: ${#SKIPPED_SKILLS[@]}

settings:
  review_depth: maximum
  auto_evidence: true

status:
  phase: not_started
  current_epic: null
  current_story: null
  current_slice: null
EOF

log_step "Generated .acos/config/project.yaml"
log_step "  name: $PROJECT_NAME"
log_step "  stack: $TECH_STACK | pkg: $PACKAGE_MANAGER | test: $TEST_RUNNER | lint: $LINTER"
log_step "  features: frontend=$HAS_FRONTEND backend=$HAS_BACKEND db=$HAS_DATABASE api=$HAS_API tests=$HAS_TESTS"

# Generate learning-curve index
if [[ ! -f "$PROJECT_DIR/learning-curve/index.yaml" ]]; then
  cat > "$PROJECT_DIR/learning-curve/index.yaml" << EOF
# ACOS Learning Curve Index
# Auto-generated on $(date +%Y-%m-%d)

version: "1.0.0"
project: "$PROJECT_NAME"

patterns: []
anti_patterns: []
domain_knowledge: []
agent_effectiveness: []
EOF
  log_step "Generated learning-curve/index.yaml"
fi

# Generate Oracle config (permission governance)
if [[ ! -f "$PROJECT_DIR/.acos/config/oracle.yaml" ]]; then
  cp "$ACOS_ROOT/.claude/skills/acos-oracle-protocol/templates/oracle-default.yaml" \
     "$PROJECT_DIR/.acos/config/oracle.yaml"
  log_step "Generated .acos/config/oracle.yaml (The Oracle)"
fi

# Generate model-profile config (agent model assignments)
if [[ ! -f "$PROJECT_DIR/.acos/config/model-profile.yaml" ]]; then
  cp "$ACOS_ROOT/.claude/skills/acos-model-change/templates/model-profile-default.yaml" \
     "$PROJECT_DIR/.acos/config/model-profile.yaml"
  log_step "Generated .acos/config/model-profile.yaml (Model Profiles)"
fi

# Generate providers.yaml template (external model API endpoints)
if [[ ! -f "$PROJECT_DIR/.acos/config/providers.yaml" ]]; then
  cat > "$PROJECT_DIR/.acos/config/providers.yaml" << 'PROVIDERS_EOF'
# External Model Provider Registry
# Configure API endpoints for non-Claude models used by ACOS agents.
# See /acos-model-change for provider profiles (hybrid-review, free-tier, etc.)

providers:
  openai:
    type: openai-compatible
    api_base: "https://api.openai.com/v1"
    api_key_env: "OPENAI_API_KEY"
    default_max_tokens: 4096

  google:
    type: openai-compatible
    api_base: "https://generativelanguage.googleapis.com/v1beta/openai"
    api_key_env: "GOOGLE_API_KEY"
    default_max_tokens: 4096

  openrouter:
    type: openai-compatible
    api_base: "https://openrouter.ai/api/v1"
    api_key_env: "OPENROUTER_API_KEY"
    default_max_tokens: 4096
    extra_headers:
      HTTP-Referer: "https://github.com/acos"

  # custom:
  #   type: openai-compatible
  #   api_base: "http://localhost:11434/v1"  # Ollama
  #   api_key_env: ""
  #   default_max_tokens: 4096
PROVIDERS_EOF
  log_step "Generated .acos/config/providers.yaml (External Providers)"
fi

log_ok "Project configuration ready"
log ""

# ═══════════════════════════════════════════════════════════════════════════
# STEP 7: Inject Confirmation Gate into project CLAUDE.md
# ═══════════════════════════════════════════════════════════════════════════

log "${BOLD}[7/8] Ensuring Confirmation Gate in CLAUDE.md...${NC}"

CLAUDE_MD="$PROJECT_DIR/CLAUDE.md"
GATE_MARKER="## Confirmation Gate (MANDATORY)"

if [[ -f "$CLAUDE_MD" ]] && grep -qF "$GATE_MARKER" "$CLAUDE_MD" 2>/dev/null; then
  log_ok "Confirmation Gate already present in CLAUDE.md"
else
  GATE_SECTION=$(cat <<'GATE_EOF'

## Confirmation Gate (MANDATORY)
Before executing ANY instruction that requires interpretation, understanding, or
summarization, Claude MUST:

1. **Pause** — Do NOT start executing (no tool calls, no file reads, no agent spawns).
2. **Restate** — Write a plain-language summary of what you understood the user wants.
3. **Ask** — "Did I understand this correctly?" and wait for explicit confirmation.
4. **Only after "yes"** — Proceed with execution.

If the user corrects your understanding, restate the corrected version and ask again.

**Exception:** If the instruction is small, unambiguous, and universally understood
(e.g., "read that file", "show git status", "what's in this directory"), execute
immediately without restating. The gate applies when there is any room for
misinterpretation — multi-step tasks, vague instructions, domain-specific requests,
or anything where your understanding of the intent could differ from what the user
actually meant.

**Rule of thumb:** If you need to make assumptions or inferences about what the user
wants, you MUST confirm those assumptions first. If the instruction maps 1:1 to a
concrete action with no ambiguity, just do it.
GATE_EOF
)

  if [[ -f "$CLAUDE_MD" ]]; then
    # Prepend the gate section right after the first heading line (or at the top)
    # We insert after the first line that starts with "# " (the project title)
    FIRST_HEADING_LINE=$(grep -n '^# ' "$CLAUDE_MD" | head -1 | cut -d: -f1)
    if [[ -n "$FIRST_HEADING_LINE" ]]; then
      # Insert after the first heading
      {
        head -n "$FIRST_HEADING_LINE" "$CLAUDE_MD"
        echo "$GATE_SECTION"
        echo ""
        tail -n +"$((FIRST_HEADING_LINE + 1))" "$CLAUDE_MD"
      } > "$CLAUDE_MD.tmp" && mv "$CLAUDE_MD.tmp" "$CLAUDE_MD"
    else
      # No heading found — prepend at top
      {
        echo "$GATE_SECTION"
        echo ""
        cat "$CLAUDE_MD"
      } > "$CLAUDE_MD.tmp" && mv "$CLAUDE_MD.tmp" "$CLAUDE_MD"
    fi
    log_ok "Injected Confirmation Gate into existing CLAUDE.md"
  else
    # No CLAUDE.md exists — create one with just the gate
    cat > "$CLAUDE_MD" << NEWCLAUDE_EOF
# $(basename "$PROJECT_DIR")
$GATE_SECTION
NEWCLAUDE_EOF
    log_ok "Created CLAUDE.md with Confirmation Gate"
  fi
fi
log ""

# ═══════════════════════════════════════════════════════════════════════════
# STEP 8: Update .gitignore
# ═══════════════════════════════════════════════════════════════════════════

GITIGNORE="$PROJECT_DIR/.gitignore"
ACOS_MARKER="# ACOS 3.0 (auto-generated — do not commit orchestration infrastructure)"
ACOS_END_MARKER="# End ACOS 3.0"

# If a prior ACOS-managed block exists, strip it (from start marker through end
# marker) so we can regenerate it fresh. Keying only on marker-presence and
# skipping wholesale would leave newly-linked skills/scripts un-ignored on a
# --force re-run where the selection changed. Only the ACOS-managed block is
# removed; user lines above and below are preserved.
if [[ -f "$GITIGNORE" ]] && grep -qF "$ACOS_MARKER" "$GITIGNORE" 2>/dev/null; then
  ESCAPED_START=$(printf '%s' "$ACOS_MARKER" | sed 's/[][\\/.*^$]/\\&/g')
  if grep -qF "$ACOS_END_MARKER" "$GITIGNORE" 2>/dev/null; then
    log "${BOLD}[+] Regenerating ACOS .gitignore block...${NC}"
    # Both markers present: delete from the start marker line through the end
    # marker line. macOS sed (BSD) requires the '' argument to -i. The /,/ range
    # deletes the managed block, preserving user lines above and below.
    ESCAPED_END=$(printf '%s' "$ACOS_END_MARKER" | sed 's/[][\\/.*^$]/\\&/g')
    sed -i '' "/^${ESCAPED_START}\$/,/^${ESCAPED_END}\$/d" "$GITIGNORE"
  else
    # SAFETY: end marker is missing (legacy/partial block, manual truncation, or
    # an older bootstrap version). A range delete to /end/ would delete from the
    # start marker through END OF FILE, destroying every user line below the ACOS
    # block. Instead, delete ONLY the start-marker line and append a fresh block.
    # This never deletes past the (absent) end marker. May leave a few stale ACOS
    # entries below, but NEVER destroys user data.
    log "${BOLD}[+] ACOS .gitignore block missing end marker — safe-appending fresh block...${NC}"
    sed -i '' "/^${ESCAPED_START}\$/d" "$GITIGNORE"
    # Also remove the known fixed ACOS data-dir lines so they don't become stale
    # orphans below the (now-deleted) start marker. These are exact literal lines
    # the fresh block re-appends; deleting only these specific entries is safe and
    # never touches user data or a range-to-EOF.
    for acos_line in \
      ".acos/" \
      "memory/" \
      "planning/" \
      "learning-curve/" \
      "review-rules.yaml" \
      ".claude/settings.acos-hooks.json"; do
      ESCAPED_LINE=$(printf '%s' "$acos_line" | sed 's/[][\\/.*^$]/\\&/g')
      sed -i '' "/^${ESCAPED_LINE}\$/d" "$GITIGNORE"
    done
  fi
else
  log "${BOLD}[+] Updating .gitignore...${NC}"
fi

{
  echo ""
  echo "$ACOS_MARKER"
  echo "# Data directories"
  echo ".acos/"
  echo "memory/"
  echo "planning/"
  echo "learning-curve/"
  echo "review-rules.yaml"
  echo ""
  echo "# Symlinked ACOS agents"
  for agent in "${AGENTS[@]}"; do
    echo ".claude/agents/$agent"
  done
  echo ""
  echo "# Symlinked ACOS skills (only linked skills are listed)"
  for skill in "${SYMLINKED_SKILLS_LIST[@]}"; do
    echo ".claude/skills/$skill"
  done
  echo ""
  echo "# Symlinked ACOS scripts"
  for script in "${SYMLINKED_SCRIPTS[@]}"; do
    echo ".claude/scripts/$script"
  done
  echo ""
  echo "# ACOS hook reference"
  echo ".claude/settings.acos-hooks.json"
  echo "$ACOS_END_MARKER"
} >> "$GITIGNORE"

log_ok ".gitignore updated with ACOS entries"

# ═══════════════════════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════════════════════

TOTAL_LINKED=$(( ${#SYMLINKED_AGENTS[@]} + ${#SYMLINKED_SKILLS_LIST[@]} + ${#SYMLINKED_SCRIPTS[@]} ))

log ""
log "${BOLD}═══════════════════════════════════════════════════════════════${NC}"
log "${GREEN}${BOLD}  ACOS v3.0 initialized successfully!${NC}"
log "${BOLD}═══════════════════════════════════════════════════════════════${NC}"
log ""
log "  Project:    ${CYAN}$PROJECT_NAME${NC} ($TECH_STACK)"
log "  Linked:     ${CYAN}${#SYMLINKED_AGENTS[@]}${NC} agents, ${CYAN}${#SYMLINKED_SKILLS_LIST[@]}${NC} skills, ${CYAN}${#SYMLINKED_SCRIPTS[@]}${NC} scripts"
log "  Skipped:    ${DIM}${#SKIPPED_SKILLS[@]} skills not needed for this stack${NC}"
log ""
log "  Next steps:"
log "    /acos-start       — Begin or resume your project"
log "    /acos-interview   — Conduct a vision interview"
log "    /acos-plan        — Create planning documents"
log ""
log "  ${DIM}To link all skills: bash .claude/scripts/acos-bootstrap.sh --force --all-skills${NC}"
log ""
