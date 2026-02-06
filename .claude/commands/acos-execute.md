# ACOS Execute Command

Execute a slice using the ACOS workflow.

## Instructions

When this command is invoked:

1. **Identify the slice to execute:**
   - Check for argument: `/acos-execute SLICE-001`
   - Or find the next pending slice in the current story
   - Or ask user which slice to work on

2. **Read slice specification:**
   - Load the slice from `planning/slices/[slice-id].yaml`
   - Understand acceptance criteria
   - Note file permissions and constraints

3. **Load the Architect agent:**
   - Read `/Users/zee/Documents/Vibe Coding/ACOS 3.0/agents/the-architect.md`
   - Have Architect analyze the slice and create execution plan

4. **Execute the slice-execution-flow:**
   - Read `/Users/zee/Documents/Vibe Coding/ACOS 3.0/agentic-flows/slice-execution-flow.yaml`
   - Follow the flow stages:
     1. Read slice specification
     2. Create evidence bundle (before state)
     3. Architect plans implementation
     4. Architect creates/orchestrates Developer agent
     5. Developer executes with skills
     6. Capture evidence (after state)
     7. Verify against acceptance criteria

5. **Create evidence bundle:**
   - Run `./automation-scripts/create-evidence-bundle.sh [SLICE-ID]` if available
   - Or manually create evidence in `.acos/evidence/[date]/[SLICE-ID]/`

6. **After execution:**
   - Update slice status to `complete` or `ready_for_review`
   - Create summary of what was done
   - Suggest running `/acos-review` if complete

## Key Files

- `/Users/zee/Documents/Vibe Coding/ACOS 3.0/agents/the-architect.md` - Architect agent
- `/Users/zee/Documents/Vibe Coding/ACOS 3.0/agents/ACOS-developer.md` - Developer agent
- `/Users/zee/Documents/Vibe Coding/ACOS 3.0/agentic-flows/slice-execution-flow.yaml` - Execution flow
- `./planning/slices/` - Slice specifications
- `./.acos/evidence/` - Evidence bundles

## Constraints

- Only modify files listed in slice's `file_permissions`
- Follow the skills specified in the slice
- Capture evidence before and after
- Verify against acceptance criteria before marking complete
