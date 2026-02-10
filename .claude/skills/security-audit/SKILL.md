---
name: security-audit
description: Structured guidance for conducting security audits using OWASP Top 10 methodology. Includes threat modeling, code review, configuration review, and dependency analysis.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Glob, Grep, Bash
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

1. Identify assets (what data is being protected, what systems are involved)
2. Identify threats (who might attack, what are they after)
3. Identify attack surfaces (user inputs, API endpoints, file uploads, external integrations)

### Phase 2: Code Review

1. Authentication (password handling, session management, token validation)
2. Authorization (access control checks, role verification, resource ownership)
3. Input validation (sanitization, query parameterization, file upload validation)
4. Output encoding (XSS prevention, content type headers)

### Phase 3: Configuration Review

1. Security headers
2. CORS configuration
3. Cookie settings
4. HTTPS enforcement

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
- [ ] HTTPS enforced

### A03: Injection
- [ ] SQL queries parameterized
- [ ] No eval() with user input
- [ ] Commands properly escaped

### A04: Insecure Design
- [ ] Threat modeling performed
- [ ] Defense in depth applied

### A05: Security Misconfiguration
- [ ] Security headers present
- [ ] Error messages don't leak info
- [ ] Default credentials changed

### A06: Vulnerable Components
- [ ] Dependencies up to date
- [ ] No known vulnerabilities

### A07: Authentication Failures
- [ ] Strong password policy
- [ ] Rate limiting on auth endpoints
- [ ] Secure session management

### A08: Software and Data Integrity
- [ ] CI/CD pipeline secured
- [ ] Serialization validated

### A09: Logging and Monitoring
- [ ] Security events logged
- [ ] Logs don't contain sensitive data

### A10: Server-Side Request Forgery
- [ ] URL validation implemented
- [ ] Allowlists for external requests

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
```

### Command Injection
```javascript
// VULNERABLE
exec(`ls ${userInput}`);
// SECURE
execFile('ls', [userInput]);
```

## Output: Security Audit Report

```markdown
# Security Audit Report

## Executive Summary
[High-level findings and risk assessment]

## Findings
### [Severity] - [Finding Title]
**OWASP Category:** [e.g., A03: Injection]
**Location:** [File:Line]
**Remediation:** [How to fix]

## Summary
| Severity | Count |
|----------|-------|
| Critical | [N] |
| High | [N] |
| Medium | [N] |
| Low | [N] |
```

---

*Security Audit Skill - Protecting systems through vigilance.*
