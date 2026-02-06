---
name: api-documentation
description: Skill for creating comprehensive API documentation
version: 1.0.0
created_by: architect
created_date: 2026-01-31

category: documentation

applicable_to:
  - ACOS-developer
  - any-execution-agent

tools_required:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
---

# API Documentation Skill

## Purpose

This skill provides structured guidance for creating clear, comprehensive API documentation.

## When to Use

Apply this skill when:
- Documenting new API endpoints
- Updating existing API docs
- Creating OpenAPI/Swagger specs
- Writing API usage guides

## Skill Protocol

### Phase 1: Gather Information

1. Read the API implementation
2. Identify:
   - Endpoints
   - Request/response schemas
   - Authentication requirements
   - Error responses

### Phase 2: Structure Documentation

1. Group endpoints logically
2. Define consistent format
3. Include all necessary details

### Phase 3: Write Documentation

1. Document each endpoint
2. Provide examples
3. Document errors
4. Include authentication info

### Phase 4: Validate

1. Test examples work
2. Verify schemas are accurate
3. Check for completeness

## Endpoint Documentation Template

```markdown
## [HTTP Method] [Endpoint Path]

[Brief description of what this endpoint does]

### Authentication

[Required/Optional] - [Auth type: Bearer token, API key, etc.]

### Request

#### Headers

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| Authorization | string | Yes | Bearer token |
| Content-Type | string | Yes | application/json |

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| id | string | Yes | Resource ID |

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| page | integer | No | 1 | Page number |
| limit | integer | No | 20 | Items per page |

#### Request Body

```json
{
  "field1": "string",
  "field2": 123
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| field1 | string | Yes | Description |
| field2 | integer | No | Description |

### Response

#### Success Response (200 OK)

```json
{
  "data": {
    "id": "abc123",
    "field1": "value"
  }
}
```

#### Error Responses

| Status | Code | Description |
|--------|------|-------------|
| 400 | VALIDATION_ERROR | Invalid request body |
| 401 | UNAUTHORIZED | Missing or invalid token |
| 404 | NOT_FOUND | Resource not found |

### Example

#### Request

```bash
curl -X POST https://api.example.com/v1/resource \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "field1": "value",
    "field2": 123
  }'
```

#### Response

```json
{
  "data": {
    "id": "abc123",
    "field1": "value",
    "field2": 123,
    "createdAt": "2024-01-15T10:30:00Z"
  }
}
```
```

## OpenAPI Template

```yaml
openapi: 3.0.3
info:
  title: API Name
  description: API description
  version: 1.0.0

servers:
  - url: https://api.example.com/v1
    description: Production

security:
  - bearerAuth: []

paths:
  /resource:
    get:
      summary: List resources
      tags:
        - Resources
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            default: 1
        - name: limit
          in: query
          schema:
            type: integer
            default: 20
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ResourceList'
        '401':
          $ref: '#/components/responses/Unauthorized'

    post:
      summary: Create resource
      tags:
        - Resources
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateResource'
      responses:
        '201':
          description: Created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Resource'
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

  schemas:
    Resource:
      type: object
      properties:
        id:
          type: string
        field1:
          type: string
        createdAt:
          type: string
          format: date-time

    CreateResource:
      type: object
      required:
        - field1
      properties:
        field1:
          type: string
        field2:
          type: integer

    ResourceList:
      type: object
      properties:
        data:
          type: array
          items:
            $ref: '#/components/schemas/Resource'
        pagination:
          $ref: '#/components/schemas/Pagination'

    Pagination:
      type: object
      properties:
        page:
          type: integer
        limit:
          type: integer
        total:
          type: integer
        totalPages:
          type: integer

  responses:
    BadRequest:
      description: Bad request
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
    Unauthorized:
      description: Unauthorized
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'

    Error:
      type: object
      properties:
        error:
          type: string
        message:
          type: string
```

## Quality Checklist

- [ ] All endpoints documented
- [ ] Request/response schemas accurate
- [ ] Examples are valid and work
- [ ] Error responses documented
- [ ] Authentication requirements clear
- [ ] Query parameters documented
- [ ] Path parameters documented

---

*API Documentation Skill - Clear interfaces through clear documentation.*
