# ACOS Plan Command

Create or update planning documents (epics, stories, slices).

## Instructions

When this command is invoked:

1. **Determine planning level:**
   - Ask user what they want to plan: Epic, Story, or Slice
   - Or detect from context what's needed next

2. **For Epic Planning:**
   - Read the vision document for alignment
   - Use `planning/epics/.template.yaml`
   - Break down into stories
   - Define epic acceptance criteria
   - Save to `planning/epics/EPIC-XXX-[name].yaml`

3. **For Story Planning:**
   - Read the parent epic
   - Use `planning/stories/.template.yaml`
   - Define user story (As a... I want... So that...)
   - Break down into slices
   - Define story acceptance criteria
   - Save to `planning/stories/STORY-XXX-[name].yaml`

4. **For Slice Planning:**
   - Read the parent story
   - Use `planning/slices/.template.yaml`
   - Define specific acceptance criteria
   - List files that can be modified
   - Identify required skills
   - Define verification method
   - Save to `planning/slices/SLICE-XXX-[name].yaml`

## Planning Hierarchy

```
Vision (source of truth)
└── Epic (capability)
    └── Story (user value)
        └── Slice (atomic work unit)
```

## Key Principles

- **Epics** deliver capabilities
- **Stories** deliver user value
- **Slices** are atomic, completable in one session
- Each level references its parent
- Acceptance criteria must be verifiable

## Key Files

- `./memory/source-of-truth/vision-document.md` - Vision for alignment
- `./planning/vision/.template.yaml` - Vision template
- `./planning/epics/.template.yaml` - Epic template
- `./planning/stories/.template.yaml` - Story template
- `./planning/slices/.template.yaml` - Slice template

## Output

After planning:
1. Confirm the plan with the user
2. Save to appropriate location
3. Update parent document if needed
4. Suggest next steps
