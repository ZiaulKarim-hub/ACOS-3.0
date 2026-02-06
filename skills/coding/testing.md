---
name: testing
description: Skill for writing unit tests, integration tests, and end-to-end tests
version: 1.0.0
created_by: architect
created_date: 2026-01-31

category: coding

applicable_to:
  - ACOS-developer
  - any-execution-agent

tools_required:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash

frameworks_supported:
  - Jest
  - Vitest
  - Mocha
  - Playwright
  - Cypress
  - Testing Library
  - Supertest
  - pytest
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
2. Determine test type:
   - Unit: isolated function/component
   - Integration: multiple components together
   - E2E: full user flows
3. List test cases:
   - Happy path
   - Edge cases
   - Error cases

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
    const cart = [];
    expect(calculateTotal(cart)).toBe(0);
  });

  it('should calculate total for single item', () => {
    const cart = [{ price: 10, quantity: 2 }];
    expect(calculateTotal(cart)).toBe(20);
  });

  it('should calculate total for multiple items', () => {
    const cart = [
      { price: 10, quantity: 2 },
      { price: 5, quantity: 3 },
    ];
    expect(calculateTotal(cart)).toBe(35);
  });

  it('should apply discount when provided', () => {
    const cart = [{ price: 100, quantity: 1 }];
    expect(calculateTotal(cart, { discountPercent: 10 })).toBe(90);
  });

  it('should throw for negative prices', () => {
    const cart = [{ price: -10, quantity: 1 }];
    expect(() => calculateTotal(cart)).toThrow('Invalid price');
  });
});
```

### React Component Test (Testing Library)

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LoginForm } from './LoginForm';

describe('LoginForm', () => {
  const mockOnSubmit = jest.fn();

  beforeEach(() => {
    mockOnSubmit.mockClear();
  });

  it('should render email and password fields', () => {
    render(<LoginForm onSubmit={mockOnSubmit} />);

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
  });

  it('should submit form with valid data', async () => {
    const user = userEvent.setup();
    render(<LoginForm onSubmit={mockOnSubmit} />);

    await user.type(screen.getByLabelText(/email/i), 'test@example.com');
    await user.type(screen.getByLabelText(/password/i), 'password123');
    await user.click(screen.getByRole('button', { name: /submit/i }));

    expect(mockOnSubmit).toHaveBeenCalledWith({
      email: 'test@example.com',
      password: 'password123',
    });
  });

  it('should show error for invalid email', async () => {
    const user = userEvent.setup();
    render(<LoginForm onSubmit={mockOnSubmit} />);

    await user.type(screen.getByLabelText(/email/i), 'invalid-email');
    await user.click(screen.getByRole('button', { name: /submit/i }));

    expect(screen.getByText(/invalid email/i)).toBeInTheDocument();
    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  it('should disable submit button while loading', () => {
    render(<LoginForm onSubmit={mockOnSubmit} loading />);

    expect(screen.getByRole('button', { name: /submit/i })).toBeDisabled();
  });
});
```

### API Integration Test (Supertest)

```typescript
import request from 'supertest';
import { app } from '../app';
import { db } from '../db';
import { createTestUser, generateAuthToken } from './helpers';

describe('POST /api/posts', () => {
  let authToken: string;
  let userId: string;

  beforeAll(async () => {
    const user = await createTestUser();
    userId = user.id;
    authToken = generateAuthToken(user);
  });

  afterAll(async () => {
    await db.post.deleteMany({ where: { authorId: userId } });
    await db.user.delete({ where: { id: userId } });
  });

  it('should create a new post', async () => {
    const response = await request(app)
      .post('/api/posts')
      .set('Authorization', `Bearer ${authToken}`)
      .send({
        title: 'Test Post',
        content: 'Test content',
      })
      .expect(201);

    expect(response.body.data).toMatchObject({
      title: 'Test Post',
      content: 'Test content',
      authorId: userId,
    });
  });

  it('should return 401 without auth token', async () => {
    await request(app)
      .post('/api/posts')
      .send({ title: 'Test', content: 'Content' })
      .expect(401);
  });

  it('should return 400 for missing title', async () => {
    const response = await request(app)
      .post('/api/posts')
      .set('Authorization', `Bearer ${authToken}`)
      .send({ content: 'Content only' })
      .expect(400);

    expect(response.body.error).toBe('Validation Error');
  });
});
```

### E2E Test (Playwright)

```typescript
import { test, expect } from '@playwright/test';

test.describe('User Authentication Flow', () => {
  test('should complete signup, login, and logout', async ({ page }) => {
    // Generate unique email for test
    const email = `test-${Date.now()}@example.com`;
    const password = 'SecureP@ssw0rd';

    // Sign up
    await page.goto('/signup');
    await page.fill('[name="email"]', email);
    await page.fill('[name="password"]', password);
    await page.fill('[name="confirmPassword"]', password);
    await page.click('button[type="submit"]');

    // Should redirect to dashboard
    await expect(page).toHaveURL('/dashboard');
    await expect(page.locator('[data-testid="welcome-message"]')).toContainText('Welcome');

    // Logout
    await page.click('[data-testid="logout-button"]');
    await expect(page).toHaveURL('/');

    // Login with new account
    await page.goto('/login');
    await page.fill('[name="email"]', email);
    await page.fill('[name="password"]', password);
    await page.click('button[type="submit"]');

    await expect(page).toHaveURL('/dashboard');
  });

  test('should show error for invalid credentials', async ({ page }) => {
    await page.goto('/login');
    await page.fill('[name="email"]', 'wrong@example.com');
    await page.fill('[name="password"]', 'wrongpassword');
    await page.click('button[type="submit"]');

    await expect(page.locator('[data-testid="error-message"]'))
      .toContainText('Invalid credentials');
    await expect(page).toHaveURL('/login');
  });
});
```

### Test Fixtures

```typescript
// fixtures/users.ts
export const testUsers = {
  admin: {
    id: 'user-admin-1',
    email: 'admin@test.com',
    name: 'Test Admin',
    role: 'ADMIN',
  },
  regular: {
    id: 'user-regular-1',
    email: 'user@test.com',
    name: 'Test User',
    role: 'USER',
  },
};

// fixtures/posts.ts
export const testPosts = {
  published: {
    id: 'post-1',
    title: 'Published Post',
    content: 'Content here',
    published: true,
    authorId: testUsers.regular.id,
  },
  draft: {
    id: 'post-2',
    title: 'Draft Post',
    content: 'Draft content',
    published: false,
    authorId: testUsers.regular.id,
  },
};
```

## Test Naming Convention

```
describe('[Unit Under Test]', () => {
  describe('[Method/Scenario]', () => {
    it('should [expected behavior] when [condition]', () => {
      // test
    });
  });
});
```

Examples:
- `should return empty array when no items exist`
- `should throw ValidationError when email is invalid`
- `should create user when all fields are valid`

## Output Requirements

When completing testing work, ensure:

1. All tests pass
2. Coverage meets project standards
3. No flaky tests
4. Tests are documented
5. Evidence bundle includes:
   - Test run output
   - Coverage report
   - Any new fixtures created

---

*Testing Skill - Confidence through verification.*
