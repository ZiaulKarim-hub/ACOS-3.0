---
name: api-documentation
description: Structured guidance for creating comprehensive API documentation including endpoint docs, OpenAPI specs, and usage examples.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep
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
2. Identify endpoints, request/response schemas, auth requirements, error responses

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

[Brief description]

### Authentication
[Required/Optional] - [Auth type]

### Request
#### Headers
| Header | Type | Required | Description |

#### Request Body
| Field | Type | Required | Description |

### Response
#### Success Response (200 OK)
```json
{ "data": { ... } }
```

#### Error Responses
| Status | Code | Description |

### Example
```bash
curl -X POST https://api.example.com/v1/resource \
  -H "Authorization: Bearer <token>" \
  -d '{ "field1": "value" }'
```
```

## Quality Checklist

- [ ] All endpoints documented
- [ ] Request/response schemas accurate
- [ ] Examples are valid and work
- [ ] Error responses documented
- [ ] Authentication requirements clear
- [ ] Query and path parameters documented

---

*API Documentation Skill - Clear interfaces through clear documentation.*
