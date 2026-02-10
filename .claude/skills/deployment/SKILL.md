---
name: deployment
description: Structured guidance for deploying applications to production environments. Covers Vercel, Netlify, AWS, Docker, Kubernetes, GitHub Actions CI/CD.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Deployment Skill

## Purpose

This skill provides structured guidance for deploying applications to production and other environments, including CI/CD setup, environment configuration, and deployment verification.

## When to Use

Apply this skill when:
- Deploying an application for the first time
- Setting up CI/CD pipelines
- Configuring deployment environments
- Managing environment variables
- Verifying deployments

## Skill Protocol

### Phase 1: Deployment Planning

1. Identify deployment target (platform, environment, requirements)
2. Check prerequisites (build works locally, dependencies documented, env vars identified, secrets planned)

### Phase 2: Environment Setup

1. Configure the platform (account, deployment target, build settings)
2. Set up environment variables (identify all, set per environment, secure sensitive values)

### Phase 3: CI/CD Configuration

1. Set up build pipeline (build commands, test running, deployment triggers)
2. Configure deployment (deployment commands, rollback capability, health checks)

### Phase 4: Deployment Verification

1. Verify deployment (check logs, test deployed app, verify features)
2. Monitor (set up alerts, check for errors, verify performance)

## Deployment Checklist

### Pre-Deployment
- [ ] Build passes locally
- [ ] Tests pass
- [ ] Environment variables documented
- [ ] Secrets securely stored
- [ ] Database migrations ready (if applicable)

### Deployment
- [ ] Build completes successfully
- [ ] Deployment completes successfully
- [ ] Health checks pass

### Post-Deployment
- [ ] Application accessible
- [ ] All features working
- [ ] No errors in logs
- [ ] Performance acceptable
- [ ] Monitoring active

## Environment Variables Best Practices

1. Never commit secrets to git
2. Use `.env.example` for documentation
3. Use different values per environment
4. Use secret management services

## Rollback Procedures

Always have a rollback plan:
- Vercel: `vercel rollback [deployment-url]`
- Kubernetes: `kubectl rollout undo deployment/myapp`
- Git-based: `git revert HEAD && git push`

---

*Deployment Skill - From code to production reliably.*
