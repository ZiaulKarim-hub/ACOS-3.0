---
name: security-audit
description: Skill for conducting security audits and identifying vulnerabilities
version: 1.0.0
created_by: architect
created_date: 2026-01-31

category: security

applicable_to:
  - ACOS-security-reviewer
  - the-architect
  - any-agent

tools_required:
  - Read
  - Glob
  - Grep
  - Bash
---

# Security Audit Skill

## Purpose

This skill provides structured guidance for conducting security audits, identifying vulnerabilities, and ensuring secure coding practices.

## When to Use

Apply this skill when:
- Reviewing code for security issues
- Conducting security audits
- Implementing security features
- Validating authentication/authorization
- Checking for OWASP Top 10 vulnerabilities

## Skill Protocol

### Phase 1: Threat Modeling

1. **Identify assets:**
   - What data is being protected?
   - What systems are involved?

2. **Identify threats:**
   - Who might attack?
   - What are they after?

3. **Identify attack surfaces:**
   - User inputs
   - API endpoints
   - File uploads
   - External integrations

### Phase 2: Code Review

1. **Authentication:**
   - Password handling
   - Session management
   - Token validation

2. **Authorization:**
   - Access control checks
   - Role verification
   - Resource ownership

3. **Input validation:**
   - User input sanitization
   - Query parameterization
   - File upload validation

4. **Output encoding:**
   - XSS prevention
   - Content type headers

### Phase 3: Configuration Review

1. **Security headers**
2. **CORS configuration**
3. **Cookie settings**
4. **HTTPS enforcement**

### Phase 4: Dependency Review

1. Check for known vulnerabilities
2. Review third-party integrations
3. Assess supply chain risks

## OWASP Top 10 Checklist

### A01: Broken Access Control

- [ ] Authorization checked on every endpoint
- [ ] No IDOR vulnerabilities
- [ ] Principle of least privilege applied

### A02: Cryptographic Failures

- [ ] Strong encryption algorithms used
- [ ] Passwords properly hashed (bcrypt/argon2)
- [ ] Sensitive data encrypted at rest
- [ ] HTTPS enforced

### A03: Injection

- [ ] SQL queries parameterized
- [ ] No eval() with user input
- [ ] Commands properly escaped
- [ ] LDAP/XPath queries safe

### A04: Insecure Design

- [ ] Threat modeling performed
- [ ] Security controls documented
- [ ] Defense in depth applied

### A05: Security Misconfiguration

- [ ] Security headers present
- [ ] Error messages don't leak info
- [ ] Default credentials changed
- [ ] Unnecessary features disabled

### A06: Vulnerable Components

- [ ] Dependencies up to date
- [ ] No known vulnerabilities
- [ ] Components from trusted sources

### A07: Authentication Failures

- [ ] Strong password policy
- [ ] Rate limiting on auth endpoints
- [ ] Secure session management
- [ ] MFA available for sensitive ops

### A08: Software and Data Integrity

- [ ] Code integrity verified
- [ ] CI/CD pipeline secured
- [ ] Serialization validated

### A09: Logging and Monitoring

- [ ] Security events logged
- [ ] Logs don't contain sensitive data
- [ ] Alerting in place

### A10: Server-Side Request Forgery

- [ ] URL validation implemented
- [ ] Allowlists for external requests
- [ ] Internal services protected

## Common Vulnerability Patterns

### SQL Injection

```javascript
// VULNERABLE
const query = `SELECT * FROM users WHERE id = ${userId}`;

// SECURE
const query = 'SELECT * FROM users WHERE id = ?';
db.query(query, [userId]);
```

### XSS

```javascript
// VULNERABLE
element.innerHTML = userInput;

// SECURE
element.textContent = userInput;
// Or use DOMPurify for HTML
element.innerHTML = DOMPurify.sanitize(userInput);
```

### Command Injection

```javascript
// VULNERABLE
exec(`ls ${userInput}`);

// SECURE
execFile('ls', [userInput]);
```

### Path Traversal

```javascript
// VULNERABLE
const file = path.join('/uploads', userInput);

// SECURE
const file = path.join('/uploads', path.basename(userInput));
if (!file.startsWith('/uploads')) {
  throw new Error('Invalid path');
}
```

## Output: Security Audit Report

Create in `memory/reviews/security/`:

```markdown
# Security Audit Report

**Date:** [YYYY-MM-DD]
**Auditor:** [Agent Name]
**Scope:** [What was audited]

## Executive Summary

[High-level findings and risk assessment]

## Findings

### [CRITICAL/HIGH/MEDIUM/LOW] - [Finding Title]

**Severity:** [CRITICAL/HIGH/MEDIUM/LOW]
**OWASP Category:** [e.g., A03: Injection]
**Location:** [File:Line]

**Description:**
[What the vulnerability is]

**Impact:**
[What could happen if exploited]

**Proof of Concept:**
[How to reproduce]

**Remediation:**
[How to fix]

**Code Fix:**
```
[Before and after code]
```

---

## Summary

| Severity | Count |
|----------|-------|
| Critical | [N] |
| High | [N] |
| Medium | [N] |
| Low | [N] |

## Recommendations

1. [Priority recommendation 1]
2. [Priority recommendation 2]
3. [Priority recommendation 3]
```

---

*Security Audit Skill - Protecting systems through vigilance.*
