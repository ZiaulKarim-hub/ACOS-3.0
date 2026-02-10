---
name: backend-coding
description: Structured guidance for implementing server-side logic, APIs, services, and backend patterns. Covers Express, Fastify, NestJS, Django, Flask, FastAPI, Rails, Spring Boot.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Backend Coding Skill

## Purpose

This skill provides structured guidance for implementing server-side functionality, APIs, services, and backend logic.

## When to Use

Apply this skill when:
- Creating API endpoints
- Implementing business logic
- Building services and utilities
- Setting up middleware
- Handling server-side data processing
- Implementing authentication/authorization logic

## Skill Protocol

### Phase 1: Context Gathering

1. Read the API/feature specification
2. Identify the backend framework in use
3. Check existing patterns in the codebase:
   - Route organization
   - Controller/handler patterns
   - Service layer structure
   - Error handling conventions

### Phase 2: API Design

1. Define endpoints:
   - HTTP method
   - URL path
   - Request body schema
   - Response schema
   - Status codes
2. Plan middleware needs
3. Identify service dependencies

### Phase 3: Implementation

1. Create route definitions
2. Implement handlers/controllers:
   - Input validation
   - Business logic
   - Response formatting
3. Create/update service layer
4. Add middleware where needed

### Phase 4: Error Handling

1. Implement error responses
2. Add validation error handling
3. Handle edge cases
4. Log appropriately

## Quality Checklist

### API Design
- [ ] RESTful conventions followed
- [ ] Consistent URL patterns
- [ ] Appropriate HTTP methods
- [ ] Proper status codes

### Security
- [ ] Input validated
- [ ] Authentication checked
- [ ] Authorization verified
- [ ] No sensitive data in logs

### Error Handling
- [ ] All errors caught
- [ ] Meaningful error messages
- [ ] Proper status codes
- [ ] No stack traces in production

### Performance
- [ ] Queries are efficient
- [ ] No N+1 queries
- [ ] Appropriate caching
- [ ] Pagination implemented

### Code Quality
- [ ] Separation of concerns
- [ ] DRY principles
- [ ] Clear naming
- [ ] Documented where complex

## Common Patterns

### Express Route Handler

```typescript
import { Router } from 'express';
import { validateRequest } from '../middleware/validation';
import { authenticate } from '../middleware/auth';
import { UserService } from '../services/UserService';

const router = Router();
const userService = new UserService();

router.post(
  '/users',
  authenticate,
  validateRequest(createUserSchema),
  async (req, res, next) => {
    try {
      const user = await userService.createUser(req.body);
      res.status(201).json({ data: user });
    } catch (error) {
      next(error);
    }
  }
);

export default router;
```

### Service Layer

```typescript
export class UserService {
  constructor(private readonly userRepository: UserRepository) {}

  async createUser(data: CreateUserDTO): Promise<User> {
    await this.validateUniqueEmail(data.email);
    const hashedPassword = await this.hashPassword(data.password);
    return this.userRepository.create({
      ...data,
      password: hashedPassword,
    });
  }

  private async validateUniqueEmail(email: string): Promise<void> {
    const existing = await this.userRepository.findByEmail(email);
    if (existing) {
      throw new ConflictError('Email already in use');
    }
  }
}
```

### Error Handling Middleware

```typescript
export function errorHandler(err, req, res, next) {
  logger.error(err);

  if (err instanceof ValidationError) {
    return res.status(400).json({
      error: 'Validation Error',
      details: err.details,
    });
  }

  if (err instanceof NotFoundError) {
    return res.status(404).json({
      error: 'Not Found',
      message: err.message,
    });
  }

  res.status(500).json({
    error: 'Internal Server Error',
    message: process.env.NODE_ENV === 'production'
      ? 'An unexpected error occurred'
      : err.message,
  });
}
```

### Request Validation

```typescript
import { z } from 'zod';

export const createUserSchema = z.object({
  body: z.object({
    email: z.string().email(),
    password: z.string().min(8),
    name: z.string().min(1).max(100),
  }),
});

export function validateRequest(schema) {
  return async (req, res, next) => {
    try {
      await schema.parseAsync({
        body: req.body,
        query: req.query,
        params: req.params,
      });
      next();
    } catch (error) {
      next(new ValidationError(error.errors));
    }
  };
}
```

## Output Requirements

When completing backend work, ensure:

1. All endpoints respond correctly
2. Error cases are handled
3. Tests cover happy and error paths
4. API documentation is updated
5. Evidence bundle includes endpoint test results, request/response examples, build verification

---

*Backend Coding Skill - Building robust server-side systems.*
