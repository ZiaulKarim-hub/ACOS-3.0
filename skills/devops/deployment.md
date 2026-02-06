---
name: deployment
description: Skill for deploying applications to various environments
version: 1.0.0
created_by: architect
created_date: 2026-01-31

category: devops

applicable_to:
  - ACOS-developer
  - any-execution-agent

tools_required:
  - Read
  - Write
  - Edit
  - Bash

platforms_supported:
  - Vercel
  - Netlify
  - AWS
  - Google Cloud
  - Azure
  - Heroku
  - Docker
  - Kubernetes
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

1. **Identify deployment target:**
   - What platform/service?
   - What environment (dev, staging, prod)?
   - What are the requirements?

2. **Check prerequisites:**
   - Build process works locally
   - All dependencies documented
   - Environment variables identified
   - Secrets management planned

### Phase 2: Environment Setup

1. **Configure the platform:**
   - Create account/project
   - Set up deployment target
   - Configure build settings

2. **Set up environment variables:**
   - Identify all required variables
   - Set values per environment
   - Secure sensitive values

### Phase 3: CI/CD Configuration

1. **Set up build pipeline:**
   - Configure build commands
   - Set up test running
   - Configure deployment triggers

2. **Configure deployment:**
   - Set deployment commands
   - Configure rollback capability
   - Set up health checks

### Phase 4: Deployment Verification

1. **Verify deployment:**
   - Check deployment logs
   - Test the deployed application
   - Verify all features work

2. **Monitor:**
   - Set up monitoring/alerts
   - Check for errors
   - Verify performance

## Deployment Checklist

### Pre-Deployment

- [ ] Build passes locally
- [ ] Tests pass
- [ ] Environment variables documented
- [ ] Secrets securely stored
- [ ] Database migrations ready (if applicable)

### Deployment

- [ ] Deployment triggered
- [ ] Build completes successfully
- [ ] Deployment completes successfully
- [ ] Health checks pass

### Post-Deployment

- [ ] Application accessible
- [ ] All features working
- [ ] No errors in logs
- [ ] Performance acceptable
- [ ] Monitoring active

## Platform-Specific Guides

### Vercel (Next.js, React)

```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy (preview)
vercel

# Deploy to production
vercel --prod
```

**vercel.json:**
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "framework": "nextjs",
  "env": {
    "DATABASE_URL": "@database-url"
  }
}
```

### Netlify (Static sites, Jamstack)

```bash
# Install Netlify CLI
npm i -g netlify-cli

# Login
netlify login

# Deploy
netlify deploy

# Deploy to production
netlify deploy --prod
```

**netlify.toml:**
```toml
[build]
  command = "npm run build"
  publish = "dist"

[build.environment]
  NODE_VERSION = "18"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

### Docker

**Dockerfile:**
```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:18-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./
EXPOSE 3000
CMD ["npm", "start"]
```

```bash
# Build image
docker build -t myapp:latest .

# Run locally
docker run -p 3000:3000 myapp:latest

# Push to registry
docker tag myapp:latest registry.example.com/myapp:latest
docker push registry.example.com/myapp:latest
```

### GitHub Actions CI/CD

**.github/workflows/deploy.yml:**
```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run tests
        run: npm test

      - name: Build
        run: npm run build

      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.ORG_ID }}
          vercel-project-id: ${{ secrets.PROJECT_ID }}
          vercel-args: '--prod'
```

## Environment Variables

### Best Practices

1. **Never commit secrets to git**
2. **Use `.env.example` for documentation**
3. **Use different values per environment**
4. **Use secret management services**

### .env.example
```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/db

# Authentication
JWT_SECRET=your-secret-here
SESSION_SECRET=your-session-secret

# External Services
STRIPE_SECRET_KEY=sk_test_xxx
SENDGRID_API_KEY=SG.xxx

# App Config
NEXT_PUBLIC_API_URL=https://api.example.com
```

## Rollback Procedures

### Vercel
```bash
# List deployments
vercel ls

# Rollback to previous
vercel rollback [deployment-url]
```

### Docker/Kubernetes
```bash
# Kubernetes rollback
kubectl rollout undo deployment/myapp

# Docker - run previous image
docker run -p 3000:3000 myapp:previous-tag
```

### Git-based
```bash
# Revert to previous commit
git revert HEAD
git push origin main
# CI/CD will redeploy
```

## Output: Deployment Documentation

```markdown
# Deployment Documentation - [Project Name]

## Environments

| Environment | URL | Branch | Auto-deploy |
|-------------|-----|--------|-------------|
| Production | https://app.example.com | main | Yes |
| Staging | https://staging.example.com | develop | Yes |
| Preview | Dynamic | PR branches | Yes |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| DATABASE_URL | Yes | PostgreSQL connection string |
| JWT_SECRET | Yes | JWT signing secret |

## Deployment Process

1. Push to `main` branch
2. GitHub Actions runs tests
3. If tests pass, deploys to Vercel
4. Vercel runs build
5. Deployment goes live

## Rollback

To rollback:
1. Go to Vercel dashboard
2. Select previous deployment
3. Click "Promote to Production"

## Monitoring

- Error tracking: [Sentry URL]
- Logs: [Logging service URL]
- Metrics: [Metrics dashboard URL]
```

---

*Deployment Skill - From code to production reliably.*
