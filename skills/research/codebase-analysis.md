---
name: codebase-analysis
description: Skill for analyzing and understanding existing codebases
version: 1.0.0
created_by: architect
created_date: 2026-01-31

category: research

applicable_to:
  - the-architect
  - ACOS-developer
  - any-agent

tools_required:
  - Read
  - Glob
  - Grep
  - Bash
---

# Codebase Analysis Skill

## Purpose

This skill provides structured guidance for analyzing and understanding existing codebases, identifying patterns, and documenting architecture.

## When to Use

Apply this skill when:
- Starting work on an unfamiliar codebase
- Understanding project structure
- Identifying existing patterns and conventions
- Mapping dependencies
- Finding relevant code for a task

## Skill Protocol

### Phase 1: Project Overview

1. **Check project files:**
   - `package.json` / `requirements.txt` / `Cargo.toml` etc.
   - `README.md`
   - Configuration files

2. **Identify technology stack:**
   - Language(s)
   - Framework(s)
   - Build tools
   - Testing frameworks

### Phase 2: Structure Analysis

1. **Map directory structure:**
   ```bash
   find . -type d -name "node_modules" -prune -o -type d -print | head -50
   ```

2. **Identify key directories:**
   - Source code location
   - Tests location
   - Configuration
   - Assets/resources

### Phase 3: Pattern Discovery

1. **Find entry points:**
   - Main files
   - Route definitions
   - App initialization

2. **Identify patterns:**
   - Component structure
   - Service layer patterns
   - Data access patterns
   - Error handling conventions

### Phase 4: Dependency Mapping

1. **External dependencies:**
   - What libraries are used
   - Why they're needed

2. **Internal dependencies:**
   - How modules connect
   - Shared utilities
   - Common abstractions

## Analysis Checklist

### Project Level

- [ ] Technology stack identified
- [ ] Build/run commands documented
- [ ] Entry points found
- [ ] Testing setup understood

### Code Level

- [ ] Directory structure mapped
- [ ] Key patterns documented
- [ ] Naming conventions noted
- [ ] Code style understood

### Architecture Level

- [ ] Component relationships mapped
- [ ] Data flow understood
- [ ] External integrations identified
- [ ] Security model understood

## Common Commands

```bash
# File structure
find . -type f -name "*.ts" | head -30

# Find patterns
grep -r "class.*Controller" --include="*.ts"
grep -r "export function" --include="*.ts"

# Find configurations
cat package.json | jq '.scripts'
cat tsconfig.json | jq '.compilerOptions'

# Find dependencies
cat package.json | jq '.dependencies'

# Find entry points
grep -r "createServer\|listen\|app\." --include="*.ts" | head -20
```

## Output: Analysis Report

Create in `memory/analysis/`:

```markdown
# Codebase Analysis: [Project Name]

## Technology Stack

- **Language:** [e.g., TypeScript 5.x]
- **Framework:** [e.g., Express.js]
- **Database:** [e.g., PostgreSQL via Prisma]
- **Testing:** [e.g., Jest]

## Directory Structure

```
[Directory tree]
```

## Key Components

| Component | Location | Purpose |
|-----------|----------|---------|
| [Name] | [path] | [Description] |

## Patterns Used

### [Pattern Name]

**Example Location:** `path/to/file.ts`

**Description:** [How it's implemented]

## Dependencies

### External
- [package]: [why used]

### Internal
[Dependency graph or description]

## Entry Points

- **Main:** `src/index.ts`
- **Routes:** `src/routes/`
- **Config:** `src/config/`

## Conventions

- **Naming:** [e.g., camelCase for functions, PascalCase for classes]
- **File Organization:** [e.g., feature-based folders]
- **Imports:** [e.g., absolute imports from src/]

## Notes

[Any additional observations]
```

---

*Codebase Analysis Skill - Understanding before action.*
