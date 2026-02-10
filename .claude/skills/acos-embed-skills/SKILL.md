---
name: acos-embed-skills
description: Analyzes a target project and embeds relevant portable ACOS development skills. Automates skill selection based on tech stack detection.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Embed Skills Skill

## Purpose

This skill analyzes a target project's technology stack and embeds relevant portable ACOS development skills into it. It automates skill selection based on detection heuristics, handles conflicts with existing skills, and updates the target project's CLAUDE.md with documentation.

### Pre-flight: Auto-Bootstrap

Before proceeding, ensure ACOS is initialized in this project:

```bash
bash .claude/scripts/acos-preflight.sh
```

This is idempotent — it exits immediately if ACOS is already initialized. If not, it runs the full bootstrap (symlinks, directories, config, gitignore).

## When to Use

Apply this skill when:
- Sharing ACOS development skills with a non-ACOS project
- Setting up a new project with best-practice coding guidance
- Updating previously embedded skills to newer versions

## Portable Skills Catalog

The following 14 skills are portable (framework/language guidance, no ACOS orchestration dependencies):

| # | Skill | Category |
|---|-------|----------|
| 1 | frontend-coding | Development |
| 2 | backend-coding | Development |
| 3 | database-design | Development |
| 4 | testing | Development |
| 5 | deployment | Operations |
| 6 | ci-cd-generation | Operations |
| 7 | api-documentation | Documentation |
| 8 | security-audit | Security |
| 9 | bug-investigation | Universal |
| 10 | codebase-analysis | Universal |
| 11 | technology-research | Universal |
| 12 | user-guide-writing | Documentation |
| 13 | domain-security-profile | Security |
| 14 | mcp-setup | Tooling |

## Skill Protocol

### Phase 1: Validate Target Path

1. Parse `$ARGUMENTS` for the target project path (required, first argument)
2. If no path provided, print usage and stop:
   ```
   Usage: /acos-embed-skills <target-project-path>
   Example: /acos-embed-skills ~/projects/my-app
   ```
3. Resolve the path to an absolute path
4. Verify the directory exists — if not, error: `Target directory does not exist: <path>`
5. Verify write permissions — if not, error: `No write permission on target directory. Fix with: chmod u+w <path>`
6. If the target path resolves to the ACOS project itself (this repository), warn:
   ```
   ⚠ Target is the ACOS project itself. This will duplicate skills within ACOS.
   ```
   Ask the user to confirm before proceeding. If they decline, abort.

### Phase 2: Analyze Target Project

Run detection heuristics to score each portable skill 0–100 confidence. Use the ACOS source directory (the directory containing this skill) as the root for reading skill source files.

**Detection rules for each skill:**

#### frontend-coding (Development)
- `package.json` with react/vue/angular/svelte/next/nuxt in dependencies or devDependencies → +40
- `*.tsx`, `*.jsx`, `*.vue`, `*.svelte` files present → +30
- `src/components/` or `components/` directory exists → +20
- `public/` or `static/` directory with HTML files → +10

#### backend-coding (Development)
- `package.json` with express/fastify/nestjs/koa/hapi in dependencies → +30
- `requirements.txt` or `pyproject.toml` with django/flask/fastapi → +30
- `Gemfile` with rails/sinatra → +30
- `src/routes/`, `src/api/`, `routes/`, `api/` directory exists → +25
- `server.*`, `app.*`, `main.*` entry files in root or src/ → +20
- `go.mod` or `Cargo.toml` present → +25

#### database-design (Development)
- `prisma/schema.prisma` exists → +40
- `drizzle.config.*` exists → +40
- `ormconfig.*`, `typeorm` in dependencies → +35
- `alembic.ini`, `alembic/` directory → +35
- `migrations/`, `db/migrate/` directory exists → +30
- `*.sql` files present → +20
- `knex` or `sequelize` in dependencies → +30

#### testing (Development)
- `jest.config.*`, `vitest.config.*`, `cypress.config.*`, `playwright.config.*` exists → +40
- `pytest.ini`, `pyproject.toml` with `[tool.pytest]`, `conftest.py` → +40
- `__tests__/`, `tests/`, `test/`, `spec/` directory exists → +30
- `*.test.*`, `*.spec.*` files present → +20
- Test runner in devDependencies (jest, vitest, mocha, playwright, cypress) → +20

#### deployment (Operations)
- `Dockerfile` or `docker-compose.yml` exists → +35
- `vercel.json`, `netlify.toml`, `fly.toml`, `render.yaml` exists → +35
- `k8s/`, `kubernetes/`, `helm/` directory exists → +30
- `terraform/`, `*.tf` files → +25
- `serverless.yml`, `sam-template.yaml` → +30
- `Procfile`, `app.yaml` (Heroku/GCP) → +25

#### ci-cd-generation (Operations)
- `.github/workflows/` directory does NOT exist → +40
- `.gitlab-ci.yml` does NOT exist → +20
- No CI config detected at all → +30
- Has `package.json` or build system but no CI → +10 bonus

#### api-documentation (Documentation)
- `openapi.*`, `swagger.*` files exist → +40
- `docs/api/` directory exists → +30
- Express/Fastify/Django/FastAPI route patterns detected in code → +25
- README references API endpoints → +15

#### security-audit (Security)
- **Always recommended** — base score: 70
- `bcrypt`, `argon2`, `jwt`, `passport`, `auth0` in dependencies → +15
- `src/auth/`, `src/middleware/auth*` patterns → +10
- `.env` or `.env.example` present (handles secrets) → +5

#### bug-investigation (Universal)
- **Always recommended** — fixed score: 80

#### codebase-analysis (Universal)
- **Always recommended** — fixed score: 80

#### technology-research (Universal)
- **Always recommended** — fixed score: 75

#### user-guide-writing (Documentation)
- `docs/` directory exists → +35
- Substantial README.md (>100 lines) → +25
- `CONTRIBUTING.md` exists → +15
- User-facing application detected (frontend or CLI) → +20

#### domain-security-profile (Security)
- Domain keywords in codebase/docs (case-insensitive scan of README, docs/, comments):
  - HIPAA, PHI, medical, healthcare, patient → healthcare domain
  - PCI, PCI-DSS, payment, credit card, banking, fintech → finance domain
  - FedRAMP, federal, FISMA, government, .gov → government domain
  - FERPA, student, education → education domain
- Need 3+ keyword matches across any domain to recommend → score 75
- Fewer than 3 matches → score 20

#### mcp-setup (Tooling)
- `.claude/` directory already exists → +40
- References to MCP, Model Context Protocol, or Claude Code in README/docs → +30
- `.claude/settings.local.json` exists → +20
- No `.claude/` directory at all → +10 (still mildly useful)

**Score threshold:** Skills scoring >60 are marked "Recommended." All others are marked "Skip."

### Phase 3: Present Recommendations

Display results as a markdown table sorted by status (Recommended first, then Skip):

```
## Skill Analysis for [project-name]

| Skill                   | Score | Status      | Rationale                                        |
|-------------------------|-------|-------------|--------------------------------------------------|
| backend-coding          |    85 | Recommended | Express.js in package.json, src/api/ directory   |
| testing                 |    90 | Recommended | vitest.config.ts found, tests/ directory present |
| security-audit          |    70 | Recommended | Always recommended (universal security guidance) |
| frontend-coding         |    15 | Skip        | No frontend framework detected                   |
| ...                     |       |             |                                                  |

**Summary:** X of 14 skills recommended for embedding.
```

Then present four choices using `AskUserQuestion`:
1. **Embed recommended** — proceed with all Recommended skills
2. **Customize** — user provides adjustments: "+frontend-coding -testing" to toggle
3. **Embed all 14** — skip analysis, embed everything
4. **Abort** — cancel without changes

If the user chooses **Customize**, parse their `+skill` / `-skill` input to adjust the selected set and confirm the final list before proceeding.

### Phase 4: Detect Conflicts

For each selected skill, check whether `<target>/.claude/skills/<skill-name>/` already exists.

**If no conflicts:** proceed to Phase 5.

**If conflicts found:** display the conflicts and ask the user:
1. **Skip conflicts** — only embed skills that don't already exist
2. **Overwrite all** — replace all conflicting skill directories
3. **Review individually** — for each conflict, show the file count difference and ask skip/overwrite

### Phase 5: Copy Skills

Determine the ACOS source directory — the root of the repository containing this skill file. Use it as the source for all copies.

For each selected skill (respecting conflict resolution from Phase 4):

1. Create `<target>/.claude/skills/` if it does not exist
2. Copy the full skill directory: `cp -r <acos-source>/.claude/skills/<skill-name> <target>/.claude/skills/<skill-name>`
   - This preserves `templates/` subdirectories (e.g., ci-cd-generation has templates/)
3. Log success: `✓ Embedded: <skill-name>`
4. On failure, log error: `✗ Failed: <skill-name> — <error message>`
5. Continue with remaining skills even if one fails

### Phase 6: Update Target CLAUDE.md

**If `<target>/CLAUDE.md` does not exist:**

Create it with this structure:

```markdown
# [Project Name]

## Embedded Development Skills

The following development skills are available as `/slash-commands`:

| Skill | Command | Description |
|-------|---------|-------------|
| [name] | /[name] | [description from skill frontmatter] |
| ... | ... | ... |

> Embedded from ACOS v3.0 on [YYYY-MM-DD]
```

Use the directory name as `[Project Name]` if no better name is available (e.g., from package.json `name` field).

**If `<target>/CLAUDE.md` already exists:**

Read the existing file. If it already contains an "Embedded Development Skills" section, replace that section. Otherwise, append the section at the end, preceded by a blank line separator.

### Phase 7: Summary

Display a final report:

```
## Embedding Complete

### Skills Embedded (X)
| Skill | Path |
|-------|------|
| backend-coding | <target>/.claude/skills/backend-coding/ |
| testing | <target>/.claude/skills/testing/ |
| ... | ... |

### Skills Skipped (Y)
| Skill | Reason |
|-------|--------|
| frontend-coding | Score below threshold (15) |
| database-design | Already exists (conflict: skip) |
| ... | ... |

### Files Created/Modified
- Created: <target>/.claude/skills/ (directory)
- Created: <target>/.claude/skills/backend-coding/SKILL.md
- Modified: <target>/CLAUDE.md (appended Embedded Development Skills section)

### Next Steps
1. Open Claude Code in the target project: `cd <target> && claude`
2. The embedded skills will load automatically from `.claude/skills/`
3. Use `/skill-name` to invoke any embedded skill
4. Run `/codebase-analysis` first to orient Claude to your project
```

## Edge Cases

### Target is ACOS itself
Phase 1 detects this by comparing resolved paths. Requires explicit confirmation before proceeding.

### Empty or new project
If the target has very few files (no package.json, no source directories), most heuristics will score low. The universal skills (bug-investigation, codebase-analysis, technology-research) and security-audit will still be recommended — typically 4 skills.

### All skills already exist
Phase 4 will show all 14 as conflicts. The user can choose overwrite (to update) or abort. This effectively functions as an "update" mechanism.

### Partial copy failure
Phase 5 continues past failures and reports them all in Phase 7. The user gets a clear list of what succeeded and what didn't.

### Permission errors
Phase 1 checks write permissions upfront. Phase 5 catches per-file errors and reports them without aborting the entire operation.

---

*Embed Skills Skill - Sharing development expertise across projects.*
