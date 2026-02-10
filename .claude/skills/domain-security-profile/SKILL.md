---
name: domain-security-profile
description: Structured guidance for creating domain-specific security profiles that augment the security-reviewer with industry-specific threat awareness (finance, healthcare, government, etc.).
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Domain Security Profile Skill

## Purpose

This skill helps projects create a domain-specific security context file that gets passed to the security-reviewer during review. This augments the reviewer's default OWASP focus with industry-specific threats, compliance requirements, and data classification — without modifying the core agent.

## When to Use

Apply this skill when:
- The project operates in a regulated domain (finance, healthcare, government, education)
- There are domain-specific compliance requirements (PCI-DSS, HIPAA, SOC 2, GDPR, FedRAMP)
- The project handles sensitive data categories that need explicit classification
- Standard OWASP review is insufficient for the domain's threat landscape

## How It Integrates with ACOS

1. Project creates `.acos/config/security-profile.md` using this skill
2. During review (`/acos-review`), the review skill checks for this file
3. If present, its contents are included in the `Task(security-reviewer)` prompt as additional context
4. The security-reviewer sees domain threats alongside its standard OWASP checklist
5. No profile file = reviewer behaves exactly as today (pure OWASP)

## Skill Protocol

### Phase 1: Domain Discovery

Interview the user or read project documentation to identify:
1. **Industry domain** — What sector does the application serve?
2. **Regulatory landscape** — What compliance standards apply?
3. **Data sensitivity** — What categories of data are handled?
4. **Threat actors** — Who might target this application and why?
5. **Deployment context** — Cloud, on-prem, hybrid? Geographic restrictions?

### Phase 2: Profile Creation

Create `.acos/config/security-profile.md` with the following sections:

```markdown
# Domain Security Profile

## Domain
[Industry and sub-domain]

## Applicable Regulations
- [Regulation 1]: [Brief relevance]
- [Regulation 2]: [Brief relevance]

## Data Classification
| Data Type | Classification | Handling Requirements |
|-----------|---------------|----------------------|
| [type]    | [level]       | [requirements]       |

## Domain-Specific Threats
- [Threat 1]: [Description and relevance]
- [Threat 2]: [Description and relevance]

## Required Security Controls
- [Control 1]: [What and why]
- [Control 2]: [What and why]

## Review Focus Areas
[What the security reviewer should pay extra attention to beyond OWASP]
```

### Phase 3: Validate

1. Verify the profile covers all identified regulations
2. Confirm data classifications are complete
3. Ensure threats are specific and actionable (not generic)

## Template

See `templates/security-profile.example.md` for a fully annotated template.

---

*Domain Security Profile Skill - Industry-specific threat awareness.*
