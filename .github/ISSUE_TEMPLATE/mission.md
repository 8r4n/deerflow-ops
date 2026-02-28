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
- [ ] mission:content — content creation, media, newsletters
- [ ] mission:marketing — social media, SEO, outreach
- [ ] mission:ops — business operations, reporting
- [ ] mission:sales — sales pipeline, CRM, lead tracking
- [ ] mission:commerce — e-commerce, inventory, orders

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
- [ ] GitHub MCP (issues/PRs/search/progress updates)
- [ ] Codespaces MCP (create/start/stop/delete Codespaces)
- [ ] Web Fetch MCP
- [ ] Command Exec MCP (allowlisted)
- [ ] Other: ______________________

### Codespaces policy (defaults; override only if needed)
- Machine type: `standardLinux32gb` by default
- Idle timeout: 30 minutes (default)
- Retention period: 7 days (default)
- GHCR push: allowed for `ghcr.io/8r4n/deerflow-skills/*` only

## Budgets
- Max runtime: ___ minutes
- Max tool calls: ___
- Max Codespaces created: ___

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
- [ ] Skill image pushed to `ghcr.io/8r4n/deerflow-skills/<skill-name>` (if applicable)
- [ ] Progress updates posted to run-log issue
- [ ] Other: ______________________

## Human checkpoints (approval gates)
List any steps that must pause for your approval:
- [ ] Open PR before merge (always)
- [ ] Any Codespaces policy escalation (larger machine type, extended retention, etc.)
- [ ] Anything involving sensitive data
- [ ] Other: ______________________

## Run tracking
When execution starts, create/link a run log issue:
- Run log issue: <!-- paste URL once created -->