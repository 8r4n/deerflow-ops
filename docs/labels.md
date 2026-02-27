# Label taxonomy (deerflow-ops)

This repository uses GitHub labels as a lightweight schema. The goal is to make issues:
- easy to filter and search
- consistent across missions and runs
- machine-parseable by DeerFlow

## Mission labels (exact set)
- `mission:comms`
- `mission:planning`
- `mission:memory`
- `mission:research`
- `mission:automation`
- `mission:dev`
- `mission:finance`
- `mission:health`
- `mission:logistics`
- `mission:learning`
- `mission:social`
- `mission:risk`

## Run and memory labels
- `run:log`
- `memory:skill`
- `memory:repo`
- `memory:playbook`

## Status labels
- `status:active`
- `status:blocked`
- `status:done`
- `status:deprecated`

## Risk labels
- `risk:low`
- `risk:med`
- `risk:high`

## Tool labels (optional but helpful)
- `tool:github`
- `tool:docker`
- `tool:mcp`
- `tool:web`

## Recommended label hygiene rules
1. Every Mission issue MUST have exactly one `mission:*` label and one `status:*` label.
2. Every Run Log MUST have `run:log` and a `status:*` label.
3. Every memory entry MUST have exactly one `memory:*` label and one `status:*` label.
4. Prefer adding `risk:*` to runs and high-sensitivity missions.

## Search recipes
- All skills: `repo:8r4n/deerflow-ops label:memory:skill`
- Active runs: `repo:8r4n/deerflow-ops label:run:log label:status:active`
- Blocked items: `repo:8r4n/deerflow-ops label:status:blocked`