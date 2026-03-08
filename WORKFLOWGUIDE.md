# Workflow Guidelines

## Planning
- **Non-trivial tasks** (3+ steps or arch decisions): enter plan mode, write specs upfront. If blocked, stop and re-plan — don't push through.
- **Done means verified:** run tests, check logs, diff behavior. Ask: "Would a staff engineer approve this?"

## Execution
- **Subagents:** use freely — one focused task each. Offload research, exploration, parallel work.
- **Elegance check:** for non-trivial changes ask "is there a more elegant way?" Skip for obvious fixes.
- **Bug reports:** fix directly without hand-holding. Fix failing tests without being told how.

## Standards
- **Simplicity:** minimal code, minimal impact. Touch only what's necessary.
- **Root causes only:** no temporary fixes, no symptom treatment. Senior developer standards.

## Continuous Improvement
- **After corrections:** add pattern + prevention rule to `tasks/lessons.md`. Iterate until mistake rate drops.
- **Session start:** read `tasks/lessons.md` before starting work.

## Task Management
1. Write plan to `tasks/todo.md` with checkable items
2. Verify plan before starting
3. Mark items complete as you go; explain each change
4. Update `tasks/lessons.md` after any user correction
