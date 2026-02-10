---
name: knowledge-graph
description: Structured guidance for extracting entities, building relationships, and constructing knowledge graphs from documents and structured data. Supports any domain with configurable schemas. Use when connecting information across sources.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Knowledge Graph Skill

## Purpose

Extract entities and relationships from documents or structured data and build a queryable knowledge graph. Produces node and edge files that enable LLM context injection, cross-document correlation, and entity resolution.

## When to Use

Apply this skill when:
- Building knowledge bases from document collections
- Extracting entities and relationships from synthdocs or processed documents
- Connecting information across multiple sources
- Performing entity resolution (deduplicating across documents)
- Providing compressed, structured context for LLM reasoning

**Use `/document-synthesis` first if:** Source documents haven't been structured yet.
**Use `/deep-research` instead if:** You need to find new information, not structure existing information.

## Skill Protocol

### Phase 1: Schema Definition

Before extracting, define the graph schema for the project's domain. If the project already has a schema, load it.

1. Identify key **node types** relevant to the domain
2. Identify key **edge types** (relationships between nodes)
3. Save schema to the project's knowledge graph directory

```yaml
schema:
  node_types:
    - type: "[ENTITY_TYPE]"
      description: "[What this node represents]"
      id_pattern: "[prefix]:{slugified-name}"
      required_fields: [canonical_name, node_type]
      optional_fields: [aliases, tags, importance, source_documents]

  edge_types:
    - type: "[RELATIONSHIP_TYPE]"
      description: "[What this edge represents]"
      source_types: ["[valid source node types]"]
      target_types: ["[valid target node types]"]
      direction: "[forward|bidirectional]"
```

**Example schemas by domain** (adapt to project):

| Domain | Node Types | Edge Types |
|--------|-----------|------------|
| Software | SERVICE, API, DATABASE, LIBRARY, TEAM | DEPENDS_ON, CALLS, READS_FROM, OWNED_BY |
| Research | PAPER, AUTHOR, CONCEPT, DATASET, METHOD | CITES, AUTHORED_BY, USES_METHOD, CONTRADICTS |
| Business | PERSON, ORG, PROJECT, DOCUMENT, DECISION | WORKS_FOR, MANAGES, OWNS, REFERENCES |
| Legal/Finance | PARTY, INSTRUMENT, PROPERTY, RISK, EVENT | OWNS, GUARANTEES, EXPOSES_TO, SUBORDINATE_TO |

### Phase 2: Source Discovery

1. Identify all source documents (synthdocs, extracted text, structured data, code)
2. Group sources by subject where possible
3. Load existing graph data if any (append mode — never overwrite)

### Phase 3: Entity Extraction

For each source document, extract nodes:

```yaml
node:
  node_id: "[type-prefix]:{slugified-name}"
  canonical_name: "[Exact name from source]"
  node_type: "[From schema]"
  aliases: ["[Variant 1]", "[Variant 2]"]
  tags: ["[tag1]", "[tag2]"]
  importance: 1-5   # 5 = critical, 1 = minor
  source_documents: ["[source file paths]"]
```

**Alias generation** — for every node, auto-generate name variants:
- Remove articles ("The Company" → "Company")
- Remove entity suffixes ("Acme, Inc." → "Acme")
- Abbreviation expansion/contraction
- Person names: include last-name-only variant
- Case variants for acronyms

### Phase 4: Relationship Building

For each relationship between entities, create edges:

```yaml
edge:
  edge_id: "E{monotonic_id}"
  source_node_id: "[node_id]"
  target_node_id: "[node_id]"
  edge_type: "[From schema]"
  direction: "[forward|bidirectional]"
  weight: 1-10       # Higher = stronger relationship
  confidence: 0.0-1.0
  evidence: "[source reference]"
  qualifiers: {}      # Domain-specific attributes
```

### Phase 5: Entity Resolution

Detect and handle duplicate entities across sources:

1. Compare canonical names and aliases across nodes of the same type
2. Flag candidates where name similarity >= 0.9
3. Validate by checking shared neighbors (2+ shared connections = likely duplicate)
4. Create `SAME_AS` edges between confirmed duplicates
5. Mark the node with more connections as canonical
6. Log all resolution decisions

### Phase 6: Output

Write graph data in CSV format for portability:

**nodes.csv:**
```csv
node_id,canonical_name,node_type,aliases,tags,importance,source_documents
```

**edges.csv:**
```csv
edge_id,source_node_id,target_node_id,edge_type,direction,weight,confidence,evidence,qualifiers_json
```

Serialization: arrays as pipe-delimited (`a|b|c`), objects as compact JSON, monotonic edge IDs.

### Phase 7: Summary Report

```yaml
Knowledge Graph Summary:
  Sources Processed: [count]
  Total Nodes: [count by type]
  Total Edges: [count by type]
  Entity Resolution: [duplicates found, SAME_AS edges created]
  Graph Density: [edges / possible edges]
  Files Written: [list]
```

## Graph Query Patterns

Once built, the graph supports:

| Pattern | Use Case |
|---------|----------|
| **Direct lookup** | Find all nodes of type X with tag Y |
| **Neighbor traversal** | Find all entities connected to node X |
| **Path finding** | How does entity A connect to entity B |
| **Context injection** | Serialize node + 1-hop neighbors as LLM context |

## Quality Checklist

- [ ] Schema defined and saved before extraction begins
- [ ] All source documents processed or noted as skipped
- [ ] Entity names match source documents exactly
- [ ] No fabricated relationships — only edges with source evidence
- [ ] Entity resolution logged with reasoning
- [ ] Existing graph data preserved (append, not overwrite)
- [ ] CSV output is valid and parseable

## Integration with Other Skills

| Upstream | Provides |
|----------|----------|
| `/document-processing` | Extracted text ready for entity extraction |
| `/document-synthesis` | Structured synthdocs (ideal graph input) |

| Downstream | Consumes |
|------------|----------|
| `/deep-research` | Graph provides structured context for research |
| `/codebase-analysis` | Software graphs inform architecture understanding |

---

*Knowledge Graph Skill — Structure your knowledge, compress your context.*
