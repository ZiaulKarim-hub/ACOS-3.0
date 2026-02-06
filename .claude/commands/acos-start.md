# ACOS Start Command

Start a new ACOS project or resume an existing one.

## Instructions

When this command is invoked:

1. **Check for existing ACOS project:**
   - Look for `.acos/` directory in the current project
   - Look for `memory/source-of-truth/` directory

2. **If ACOS is not initialized:**
   - Read the ACOS system documentation from the ACOS 3.0 directory
   - Initialize the `.acos/` structure
   - Create the `memory/` and `planning/` directories
   - Begin the Vision Interview flow

3. **If ACOS exists but no vision:**
   - Read `ACOS-SYSTEM.md` to understand the framework
   - Start the `vision-creation-flow` from `agentic-flows/`
   - Conduct the vision interview with the user

4. **If ACOS exists with vision:**
   - Read the source of truth from `memory/source-of-truth/`
   - Read the current planning state
   - Check for active slices in progress
   - Present the current status and ask what to work on next

## Key Files to Read

- `/Users/zee/Documents/Vibe Coding/ACOS 3.0/ACOS-SYSTEM.md` - Core system documentation
- `/Users/zee/Documents/Vibe Coding/ACOS 3.0/agents/` - Agent definitions
- `/Users/zee/Documents/Vibe Coding/ACOS 3.0/agentic-flows/` - Available flows
- `./memory/source-of-truth/` - Project vision and user commands (if exists)
- `./planning/` - Current planning state (if exists)

## User Interaction

Guide the user through the appropriate next step based on project state. Be welcoming and explain what ACOS will do for them if they're new.
