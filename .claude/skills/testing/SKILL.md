---
name: testing
description: Structured guidance for writing unit tests, integration tests, and end-to-end tests. Covers Jest, Vitest, Mocha, Playwright, Cypress, Testing Library, Supertest, pytest.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Testing Skill

## Purpose

This skill provides structured guidance for writing comprehensive tests including unit tests, integration tests, and end-to-end tests.

## When to Use

Apply this skill when:
- Writing tests for new functionality
- Adding tests to existing code
- Creating integration tests for APIs
- Building end-to-end test suites
- Setting up test infrastructure

## Test Pyramid

```
         /\
        /  \     E2E Tests (Few)
       /----\    - User journeys
      /      \   - Critical paths
     /--------\  Integration Tests (Some)
    /          \ - API endpoints
   /            \- Service interactions
  /--------------\ Unit Tests (Many)
 /                \- Functions
/                  \- Components
```

## Skill Protocol

### Phase 1: Test Planning

1. Identify what needs testing
2. Determine test type (unit, integration, E2E)
3. List test cases: happy path, edge cases, error cases

### Phase 2: Test Setup

1. Set up test file structure
2. Configure mocks/stubs
3. Create test fixtures
4. Set up test database (if needed)

### Phase 3: Test Implementation

1. Write tests following AAA pattern:
   - Arrange: Set up test data
   - Act: Execute the code
   - Assert: Verify the result
2. Keep tests focused and independent
3. Use descriptive test names

### Phase 4: Test Validation

1. Run all tests
2. Verify coverage
3. Check for flaky tests
4. Review test quality

## Quality Checklist

### Test Structure
- [ ] Tests are independent
- [ ] Tests are deterministic
- [ ] Tests are fast
- [ ] Tests are readable

### Coverage
- [ ] Happy paths covered
- [ ] Edge cases covered
- [ ] Error cases covered
- [ ] Boundary conditions tested

### Maintainability
- [ ] No test code duplication
- [ ] Fixtures/helpers are reusable
- [ ] Mocks are appropriate
- [ ] Tests document behavior

## Common Patterns

### Unit Test (Jest)

```typescript
import { calculateTotal } from './cart';

describe('calculateTotal', () => {
  it('should return 0 for empty cart', () => {
    expect(calculateTotal([])).toBe(0);
  });

  it('should calculate total for multiple items', () => {
    const cart = [
      { price: 10, quantity: 2 },
      { price: 5, quantity: 3 },
    ];
    expect(calculateTotal(cart)).toBe(35);
  });

  it('should throw for negative prices', () => {
    const cart = [{ price: -10, quantity: 1 }];
    expect(() => calculateTotal(cart)).toThrow('Invalid price');
  });
});
```

### API Integration Test (Supertest)

```typescript
import request from 'supertest';
import { app } from '../app';

describe('POST /api/posts', () => {
  it('should create a new post', async () => {
    const response = await request(app)
      .post('/api/posts')
      .set('Authorization', `Bearer ${authToken}`)
      .send({ title: 'Test Post', content: 'Test content' })
      .expect(201);

    expect(response.body.data).toMatchObject({
      title: 'Test Post',
      content: 'Test content',
    });
  });

  it('should return 401 without auth token', async () => {
    await request(app)
      .post('/api/posts')
      .send({ title: 'Test', content: 'Content' })
      .expect(401);
  });
});
```

### E2E Test (Playwright)

```typescript
import { test, expect } from '@playwright/test';

test.describe('User Authentication Flow', () => {
  test('should complete signup, login, and logout', async ({ page }) => {
    const email = `test-${Date.now()}@example.com`;
    await page.goto('/signup');
    await page.fill('[name="email"]', email);
    await page.fill('[name="password"]', 'SecureP@ssw0rd');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL('/dashboard');
  });
});
```

## Test Naming Convention

```
describe('[Unit Under Test]', () => {
  describe('[Method/Scenario]', () => {
    it('should [expected behavior] when [condition]', () => {});
  });
});
```

## Output Requirements

When completing testing work, ensure:

1. All tests pass
2. Coverage meets project standards
3. No flaky tests
4. Evidence bundle includes test run output and coverage report

---

*Testing Skill - Confidence through verification.*
