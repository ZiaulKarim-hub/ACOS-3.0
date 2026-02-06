---
name: database-design
description: Skill for designing database schemas, writing migrations, and optimizing data structures
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

databases_supported:
  - PostgreSQL
  - MySQL
  - SQLite
  - MongoDB
  - Redis
  - DynamoDB

orms_supported:
  - Prisma
  - TypeORM
  - Sequelize
  - Drizzle
  - Mongoose
  - Knex
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
2. Determine relationships:
   - One-to-one
   - One-to-many
   - Many-to-many
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

model Post {
  id        String   @id @default(cuid())
  title     String
  content   String?
  published Boolean  @default(false)
  author    User     @relation(fields: [authorId], references: [id])
  authorId  String
  tags      Tag[]
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt

  @@index([authorId])
  @@index([published, createdAt])
  @@map("posts")
}

model Tag {
  id    String @id @default(cuid())
  name  String @unique
  posts Post[]

  @@map("tags")
}

enum Role {
  USER
  ADMIN
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
CREATE INDEX idx_users_role ON users(role);

-- Down Migration
DROP TABLE IF EXISTS users;
```

### Repository Pattern

```typescript
export class UserRepository {
  constructor(private readonly db: PrismaClient) {}

  async findById(id: string): Promise<User | null> {
    return this.db.user.findUnique({
      where: { id },
    });
  }

  async findByEmail(email: string): Promise<User | null> {
    return this.db.user.findUnique({
      where: { email },
    });
  }

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
      pagination: {
        page,
        pageSize,
        total,
        totalPages: Math.ceil(total / pageSize),
      },
    };
  }

  async create(data: CreateUserDTO): Promise<User> {
    return this.db.user.create({ data });
  }

  async update(id: string, data: UpdateUserDTO): Promise<User> {
    return this.db.user.update({
      where: { id },
      data,
    });
  }

  async delete(id: string): Promise<void> {
    await this.db.user.delete({ where: { id } });
  }
}
```

### Query Optimization

```sql
-- Before: Full table scan
SELECT * FROM posts WHERE title LIKE '%search%';

-- After: Full-text search with index
CREATE INDEX idx_posts_title_gin ON posts USING gin(to_tsvector('english', title));
SELECT * FROM posts WHERE to_tsvector('english', title) @@ plainto_tsquery('search');

-- Before: N+1 query problem
-- Query 1: SELECT * FROM users
-- Query N: SELECT * FROM posts WHERE author_id = ?

-- After: Single query with join
SELECT u.*, p.*
FROM users u
LEFT JOIN posts p ON p.author_id = u.id
WHERE u.id IN (...);
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
5. Evidence bundle includes:
   - Schema diagram (if significant changes)
   - Migration files
   - Query performance comparison (if optimization)

---

*Database Design Skill - Building efficient data foundations.*
