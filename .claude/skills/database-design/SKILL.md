---
name: database-design
description: Structured guidance for designing database schemas, writing migrations, and optimizing data access. Covers PostgreSQL, MySQL, SQLite, MongoDB, Redis, Prisma, TypeORM, Drizzle.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Database Design Skill

## Purpose

This skill provides structured guidance for designing database schemas, creating migrations, and implementing efficient data access patterns.

## When to Use

Apply this skill when:
- Designing new database tables/collections
- Creating or modifying migrations
- Implementing data access layers
- Optimizing query performance
- Setting up relationships between entities
- Adding indexes

## Skill Protocol

### Phase 1: Requirements Analysis

1. Identify entities and their attributes
2. Determine relationships (one-to-one, one-to-many, many-to-many)
3. Identify query patterns (what will be queried frequently)
4. Consider data volume and growth

### Phase 2: Schema Design

1. Define tables/collections
2. Choose appropriate data types
3. Set primary keys
4. Define foreign keys and relationships
5. Add constraints (unique, not null, checks)
6. Plan indexes based on query patterns

### Phase 3: Migration Creation

1. Create migration files
2. Implement up/down migrations
3. Handle data transformations
4. Consider rollback scenarios

### Phase 4: Data Access Layer

1. Create repository/model classes
2. Implement CRUD operations
3. Add query methods for common patterns
4. Implement pagination
5. Add caching where appropriate

## Quality Checklist

### Schema Design
- [ ] Appropriate data types chosen
- [ ] Primary keys defined
- [ ] Foreign keys properly set
- [ ] Constraints enforced
- [ ] Indexes on frequently queried columns

### Normalization
- [ ] No data duplication (where avoidable)
- [ ] Proper normal form (3NF typically)
- [ ] Denormalization only when justified for performance

### Performance
- [ ] Indexes cover common queries
- [ ] No missing indexes on foreign keys
- [ ] Large text/blob fields considered
- [ ] Pagination implemented for large datasets

### Security
- [ ] Sensitive fields encrypted at rest
- [ ] No PII in logs
- [ ] Access controls defined

### Migrations
- [ ] Migrations are reversible
- [ ] Data is preserved during migration
- [ ] Migration order is correct
- [ ] Tested in dev before production

## Common Patterns

### Prisma Schema

```prisma
model User {
  id        String   @id @default(cuid())
  email     String   @unique
  name      String?
  password  String
  role      Role     @default(USER)
  posts     Post[]
  profile   Profile?
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt

  @@index([email])
  @@map("users")
}
```

### SQL Migration

```sql
-- Up Migration
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) NOT NULL UNIQUE,
  name VARCHAR(255),
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(20) NOT NULL DEFAULT 'USER',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);

-- Down Migration
DROP TABLE IF EXISTS users;
```

### Repository Pattern

```typescript
export class UserRepository {
  constructor(private readonly db: PrismaClient) {}

  async findMany(options: {
    page: number;
    pageSize: number;
    role?: Role;
  }): Promise<PaginatedResult<User>> {
    const { page, pageSize, role } = options;
    const skip = (page - 1) * pageSize;

    const [users, total] = await Promise.all([
      this.db.user.findMany({
        where: role ? { role } : undefined,
        skip,
        take: pageSize,
        orderBy: { createdAt: 'desc' },
      }),
      this.db.user.count({
        where: role ? { role } : undefined,
      }),
    ]);

    return {
      data: users,
      pagination: { page, pageSize, total, totalPages: Math.ceil(total / pageSize) },
    };
  }
}
```

## Index Guidelines

| Query Pattern | Index Type |
|--------------|------------|
| Exact match (WHERE col = x) | B-tree |
| Range query (WHERE col > x) | B-tree |
| Text search (LIKE '%x%') | GIN/Full-text |
| JSON field query | GIN |
| Multiple columns | Composite |

## Output Requirements

When completing database work, ensure:

1. Schema changes are documented
2. Migrations are reversible
3. Indexes are appropriate
4. Tests verify data integrity
5. Evidence bundle includes migration files and query performance comparison (if optimization)

---

*Database Design Skill - Building efficient data foundations.*
