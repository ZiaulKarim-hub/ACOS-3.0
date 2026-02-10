# Domain Security Profile

> Copy this file to `.acos/config/security-profile.md` and customize for your project.
> The security-reviewer receives this as additional context during review.
> Remove sections that don't apply. Be specific — generic content adds noise.

## Domain

<!-- What industry/sector does the application serve? -->
<!-- Example: "Healthcare SaaS — patient portal for outpatient clinics" -->

## Applicable Regulations

<!-- List regulations with brief relevance to this specific project -->
<!-- Remove any that don't apply -->

- **HIPAA**: [How it applies — e.g., "PHI stored and transmitted via API"]
- **PCI-DSS**: [How it applies — e.g., "Credit card processing via Stripe"]
- **SOC 2**: [How it applies — e.g., "Multi-tenant SaaS, customer audit requirements"]
- **GDPR**: [How it applies — e.g., "EU users, right to deletion required"]
- **FedRAMP**: [How it applies — e.g., "Government agency deployment"]
- **FERPA**: [How it applies — e.g., "Student educational records"]
- **Other**: [Specify]

## Data Classification

<!-- Classify all data types the application handles -->
<!-- Levels: Public, Internal, Confidential, Restricted -->

| Data Type | Classification | Handling Requirements |
|-----------|---------------|----------------------|
| [e.g., User email] | Internal | Encrypted at rest, no logging |
| [e.g., Patient records] | Restricted | AES-256, audit logging, access control |
| [e.g., Payment info] | Restricted | Never stored, tokenized via processor |
| [e.g., Session tokens] | Confidential | HttpOnly, Secure, SameSite flags |

## Domain-Specific Threats

<!-- Threats beyond OWASP Top 10 that are specific to your domain -->
<!-- Be concrete — "data breach" is too generic -->

- **[Threat name]**: [Specific description, attack vector, and why it's relevant]
- **[Threat name]**: [Specific description, attack vector, and why it's relevant]

<!-- Examples for healthcare: -->
<!-- - Patient record exfiltration via API pagination abuse -->
<!-- - Prescription data tampering through race conditions -->
<!-- - Insurance fraud via claims API manipulation -->

<!-- Examples for fintech: -->
<!-- - Balance manipulation via concurrent transaction exploits -->
<!-- - Account takeover through SIM-swap + SMS 2FA -->
<!-- - Regulatory reporting data manipulation -->

## Required Security Controls

<!-- Specific controls the reviewer should verify exist -->

- **[Control]**: [What it does and why it's required]
- **[Control]**: [What it does and why it's required]

<!-- Examples: -->
<!-- - Audit logging: All data access must be logged with user, timestamp, and action -->
<!-- - Field-level encryption: SSN and DOB must be encrypted independently of row-level -->
<!-- - Rate limiting: Authentication endpoints must enforce 5 req/min per IP -->

## Review Focus Areas

<!-- Guide the security reviewer on what to scrutinize beyond standard OWASP checks -->

When reviewing code for this project, pay extra attention to:

1. [Specific focus area and why]
2. [Specific focus area and why]
3. [Specific focus area and why]

<!-- Examples: -->
<!-- 1. Any endpoint that returns patient data — verify authorization checks user-patient relationship -->
<!-- 2. All database queries touching financial tables — verify parameterization and audit logging -->
<!-- 3. File upload handlers — verify content-type validation and malware scanning integration -->
