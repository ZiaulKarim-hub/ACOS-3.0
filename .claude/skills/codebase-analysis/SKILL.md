---
name: codebase-analysis
description: Structured approach for analyzing and understanding existing codebases, identifying patterns, mapping dependencies, and documenting architecture.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Glob, Grep, Bash
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

1. Check project files (package.json, README.md, config files)
2. Identify technology stack (languages, frameworks, build tools, testing)

### Phase 2: Structure Analysis

1. Map directory structure
2. Identify key directories (source, tests, config, assets)

### Phase 3: Pattern Discovery

1. Find entry points (main files, route definitions, app initialization)
2. Identify patterns (component structure, service layer, data access, error handling)

### Phase 4: Dependency Mapping

1. External dependencies: what libraries, why they're needed
2. Internal dependencies: how modules connect, shared utilities, common abstractions

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

## Output: Analysis Report

```markdown
# Codebase Analysis: [Project Name]

## Technology Stack
- **Language:** [e.g., TypeScript 5.x]
- **Framework:** [e.g., Express.js]

## Key Components
| Component | Location | Purpose |
|-----------|----------|---------|

## Patterns Used
### [Pattern Name]
**Example Location:** `path/to/file.ts`

## Conventions
- **Naming:** [e.g., camelCase for functions]
- **File Organization:** [e.g., feature-based folders]
```

---

*Codebase Analysis Skill - Understanding before action.*
