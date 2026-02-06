# ACOS Memory System

The memory system is the persistent knowledge store for ACOS. Nothing is summarized - everything is preserved for future reference.

## Directory Structure

```
memory/
├── source-of-truth/           # Tier 1 - ALWAYS loaded
│   ├── vision-interview.md    # Complete interview Q&A
│   ├── vision-document.md     # Synthesized requirements
│   └── user-commands.md       # Direct user commands log
│
├── interviews/                 # Interview transcripts
│   └── [timestamp]-[topic].md
│
├── decisions/                  # Architectural decisions
│   └── [YYYY-MM-DD]-[decision-title].md
│
├── reviews/                    # Review reports
│   ├── slice-reviews/
│   │   └── [SLICE-ID]-[reviewer].md
│   ├── story-reviews/
│   │   └── [STORY-ID]-[reviewer].md
│   ├── epic-reviews/
│   │   └── [EPIC-ID]-[reviewer].md
│   └── vision-reviews/
│       └── [reviewer].md
│
├── handoffs/                   # Agent-to-agent communication
│   ├── architect-to-developer/
│   │   └── HANDOFF-[SLICE-ID]-[timestamp].yaml
│   ├── developer-to-reviewer/
│   │   └── HANDOFF-[SLICE-ID]-[timestamp].yaml
│   ├── reviewer-to-architect/
│   │   └── FEEDBACK-[SLICE-ID]-[timestamp].yaml
│   └── developer-to-architect/
│       └── CLARIFY-[SLICE-ID]-[timestamp].yaml
│
├── agent-communications/       # General inter-agent messages
│   └── [timestamp]-[from]-to-[to].md
│
├── code-rationale/             # Why code decisions were made
│   └── [SLICE-ID]-rationale.md
│
├── feedback-history/           # Past feedback and resolutions
│   └── [SLICE-ID]-resolution-history.md
│
└── .index/                     # Search indexes (auto-generated)
    ├── keywords.yaml
    ├── timeline.yaml
    └── agents.yaml
```

## Access Tiers

### Tier 1: Always Loaded

Files in `source-of-truth/` are always available to all agents. This is the ground truth for the project.

- `vision-interview.md` - Complete Q&A from vision interview
- `vision-document.md` - Synthesized requirements document
- `user-commands.md` - Log of direct user commands

### Tier 2: Role-Based Access

Different agents have access to different directories based on their role:

| Agent | Access |
|-------|--------|
| The Architect | `decisions/`, `handoffs/`, `feedback-history/` |
| Developer | `decisions/`, `handoffs/`, `code-rationale/` |
| Reviewers | `reviews/` (own reports), `feedback-history/` |
| Memory Agent | All directories |

### Tier 3: On-Demand via RAG

Any agent can request information from any memory file through the Memory Agent's RAG retrieval system.

## File Templates

Templates for each type of memory file are in the corresponding `.template.md` files.

## Critical Rules

1. **Never summarize** - Store complete information
2. **Never delete without archiving** - Move to `.archive/` first
3. **Always include metadata** - Date, author, context
4. **Maintain indexes** - Memory Agent updates `.index/` files
5. **Respect access control** - Don't bypass tier restrictions
