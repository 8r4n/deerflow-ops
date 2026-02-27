---
name: "Mission"
description: "Define an autonomous personal-assistant mission (goal, constraints, acceptance criteria)."
title: "mission: <type> - <short objective>"
labels: ["status:active"]
assignees: []
---

## Mission type
Choose one and add the matching label:
- [ ] mission:comms
- [ ] mission:planning
- [ ] mission:memory
- [ ] mission:research
- [ ] mission:automation
- [ ] mission:dev
- [ ] mission:finance
- [ ] mission:health
- [ ] mission:logistics
- [ ] mission:learning
- [ ] mission:social
- [ ] mission:risk

## Objective (1–3 sentences)
What should the system accomplish?

## Success / acceptance criteria (checklist)
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Constraints / guardrails

### Allowed repos
- Memory/logging repo (always): `8r4n/deerflow-ops`
- PR target repo (skills only): `8r4n/deerflow-skills`
- Other repos allowed (optional allowlist):
  - [ ] `<owner/repo>`

### Allowed tools (MCP allowlist)
- [ ] GitHub MCP (issues/PRs/search)
- [ ] Docker Spawner MCP (build/run/stop/logs)
- [ ] Web Fetch MCP
- [ ] Command Exec MCP (allowlisted)
- [ ] Other: ______________________

### Docker policy (defaults; override only if needed)
- Network: `none` by default; `bridge` only if required for installs
- No privileged containers
- No docker socket mounts
- Workspace-only mounts

## Budgets
- Max runtime: ___ minutes
- Max tool calls: ___
- Max containers spawned: ___
- Max Docker build minutes: ___

## Inputs / context
Links, pasted text, credentials *names* (no secrets), and any required context:
- Link 1:
- Link 2:
- Notes:

## Deliverables
What tangible outputs should be produced?
- [ ] Issue comment summary
- [ ] `memory:*` entry created/updated in `8r4n/deerflow-ops`
- [ ] PR opened in `8r4n/deerflow-skills` (if new/updated skill is needed)
- [ ] Other: ______________________

## Human checkpoints (approval gates)
List any steps that must pause for your approval:
- [ ] Open PR before merge (always)
- [ ] Any Docker policy escalation (host networking, extra mounts, etc.)
- [ ] Anything involving sensitive data
- [ ] Other: ______________________

## Run tracking
When execution starts, create/link a run log issue:
- Run log issue: <!-- paste URL once created -->