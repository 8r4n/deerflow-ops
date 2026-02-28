# Playbook: Phase 5 — Expanded Mission Coverage

**Status:** active  
**Phase:** 5  
**Date:** 2026-02-28  

---

## Purpose

Expands the Patronus mission model beyond developer-centric tasks to cover the full breadth of autonomous personal-assistant use cases. The expanded categories are informed by real-world AI agent usage patterns documented in community resources such as the [RoboNuggets "336 Ways to Use OpenClaw"](https://youtu.be/miJLo234L9s?si=XHUQcggCsYkG_c9D) video and accompanying use-case directories.

---

## 1. Background

Phases 0–4 established the foundational infrastructure: tooling, skill templates, autonomous skill acquisition, and the agentic loop. The existing mission labels (`mission:dev`, `mission:research`, `mission:automation`, etc.) primarily target developer and system-administration workflows.

Real-world AI agent deployments — as surveyed in community directories and the RoboNuggets video — reveal significant demand across additional domains:

| Gap | Examples |
|-----|----------|
| **Content creation** | Newsletters, blog posts, video summaries, content calendars |
| **Marketing** | Social media scheduling, SEO analysis, outreach campaigns |
| **Business operations** | Report generation, project management, data entry automation |
| **Sales & CRM** | Lead tracking, outreach automation, CRM sync, meeting scheduling |
| **E-commerce** | Order processing, inventory monitoring, product listing updates |

These domains represent high-value automation opportunities that complement the existing mission categories.

---

## 2. New Mission Labels

Phase 5 adds five new `mission:*` labels to the label taxonomy:

| Label | Scope | Example missions |
|-------|-------|-----------------|
| `mission:content` | Content creation, media production, newsletters, blog/article drafting, video summarization | "Draft a weekly newsletter from RSS feeds"; "Summarize YouTube video and publish notes" |
| `mission:marketing` | Social media marketing, SEO, outreach campaigns, audience analytics, ad copy | "Schedule this week's social media posts"; "Generate SEO report for landing page" |
| `mission:ops` | Business operations, project management, reporting, data entry, process automation | "Generate weekly project status report"; "Automate daily standup digest" |
| `mission:sales` | Sales pipeline, CRM management, lead tracking, outreach automation, meeting scheduling | "Sync new leads from form to CRM"; "Draft personalized outreach emails" |
| `mission:commerce` | E-commerce operations, inventory management, order processing, product listings | "Monitor inventory levels and send low-stock alerts"; "Update product descriptions" |

These labels follow the existing conventions documented in [`docs/labels.md`](labels.md).

### Label hygiene

The same rules apply:
- Every mission issue MUST have exactly one `mission:*` label and one `status:*` label.
- Risk labels (`risk:*`) are recommended for high-sensitivity missions (e.g., `mission:sales` involving customer data, `mission:commerce` involving financial transactions).

---

## 3. Category Mapping

The table below maps the use-case categories from the [RoboNuggets video](https://youtu.be/miJLo234L9s?si=XHUQcggCsYkG_c9D) and community directories to Patronus mission labels (existing + new):

| Use-case category | Mission label | Status |
|-------------------|---------------|--------|
| Daily automation & briefings | `mission:automation` | Existing |
| Productivity & task management | `mission:planning` | Existing |
| Communication & messaging | `mission:comms` | Existing |
| Content creation & media | `mission:content` | **New** |
| Social media & marketing | `mission:marketing` | **New** |
| Research & knowledge management | `mission:research` | Existing |
| Coding & development | `mission:dev` | Existing |
| Business operations | `mission:ops` | **New** |
| Sales & CRM | `mission:sales` | **New** |
| E-commerce & finance | `mission:commerce` / `mission:finance` | **New** / Existing |
| Healthcare | `mission:health` | Existing |
| Education & learning | `mission:learning` | Existing |
| Personal & lifestyle | `mission:logistics` | Existing |
| Social & community | `mission:social` | Existing |
| Risk & security | `mission:risk` | Existing |
| Advanced autonomous workflows | `mission:automation` | Existing |

---

## 4. Example Missions per New Category

### 4.1 Content creation (`mission:content`)

```markdown
## Objective
Curate a weekly newsletter from tracked RSS feeds and publish as a GitHub Issue.

## Acceptance criteria
- [ ] RSS feeds summarized (top 5 articles per feed)
- [ ] Newsletter draft posted as an issue comment
- [ ] Links and attributions included

## Constraints
- Allowed tools: Web Fetch MCP, GitHub MCP
- Max runtime: 10 minutes
```

### 4.2 Marketing (`mission:marketing`)

```markdown
## Objective
Generate a social media content calendar for the next 7 days based on recent project updates.

## Acceptance criteria
- [ ] 7 posts drafted (one per day)
- [ ] Posts tailored for target platform tone
- [ ] Calendar posted as an issue comment

## Constraints
- Allowed tools: GitHub MCP, Web Fetch MCP
- Max runtime: 15 minutes
```

### 4.3 Business operations (`mission:ops`)

```markdown
## Objective
Generate a weekly project status report from open issues and recent PR activity.

## Acceptance criteria
- [ ] Summary of completed work (closed issues/PRs)
- [ ] List of blockers (status:blocked issues)
- [ ] Report posted as an issue comment

## Constraints
- Allowed tools: GitHub MCP
- Max runtime: 5 minutes
```

### 4.4 Sales (`mission:sales`)

```markdown
## Objective
Draft personalized outreach emails for 10 leads based on their public GitHub profiles.

## Acceptance criteria
- [ ] 10 draft emails generated
- [ ] Each email references the lead's recent activity
- [ ] Drafts posted as issue comments

## Constraints
- Allowed tools: GitHub MCP, Web Fetch MCP
- No sensitive data committed to issues
- Max runtime: 15 minutes
```

### 4.5 E-commerce (`mission:commerce`)

```markdown
## Objective
Monitor product inventory levels and generate a low-stock alert summary.

## Acceptance criteria
- [ ] Items below threshold identified
- [ ] Alert summary posted as an issue comment
- [ ] Reorder recommendations included

## Constraints
- Allowed tools: Web Fetch MCP, GitHub MCP
- Max runtime: 10 minutes
```

---

## 5. Skills Roadmap for New Categories

Each new mission category benefits from purpose-built skills. The following are candidate skills for future acquisition runs (`mission:dev` missions targeting skill creation):

| Category | Candidate skill | Purpose |
|----------|----------------|---------|
| Content | `rss-aggregator` | Fetch, filter, and summarize RSS feeds |
| Content | `markdown-newsletter` | Format curated content into newsletter templates |
| Marketing | `social-scheduler` | Generate and schedule social media posts |
| Marketing | `seo-analyzer` | Analyze page content for SEO optimization |
| Ops | `issue-reporter` | Generate project status reports from GitHub Issues |
| Ops | `standup-digest` | Aggregate daily standup notes from issues/PRs |
| Sales | `lead-researcher` | Enrich lead profiles from public data |
| Sales | `outreach-drafter` | Draft personalized outreach messages |
| Commerce | `inventory-monitor` | Track inventory levels and generate alerts |
| Commerce | `listing-updater` | Update product descriptions and metadata |

These skills follow the [skill standard](https://github.com/8r4n/deerflow-skills/blob/main/docs/skill-standard.md) and can be created using the [Phase 2 template](playbook-phase2-template-skill.md).

---

## 6. Implementation Steps

### 6.1 Add labels to GitHub

Create the new labels in `8r4n/deerflow-ops` via the GitHub UI or CLI:

```bash
gh label create "mission:content"   --repo 8r4n/deerflow-ops --color "0E8A16" --description "Content creation and media production"
gh label create "mission:marketing" --repo 8r4n/deerflow-ops --color "0E8A16" --description "Social media marketing and outreach"
gh label create "mission:ops"       --repo 8r4n/deerflow-ops --color "0E8A16" --description "Business operations and project management"
gh label create "mission:sales"     --repo 8r4n/deerflow-ops --color "0E8A16" --description "Sales, CRM, and lead management"
gh label create "mission:commerce"  --repo 8r4n/deerflow-ops --color "0E8A16" --description "E-commerce and online business operations"
```

### 6.2 Update mission issue template

The mission issue template (`.github/ISSUE_TEMPLATE/mission.md`) has been updated to include the new mission types in the type selection checklist.

### 6.3 Update documentation

- `docs/labels.md` — new labels added to the mission labels section
- `docs/whitepaper.md` — Phase 5 roadmap expanded
- `README.md` — roadmap table updated

---

## 7. Security Considerations

### 7.1 Data sensitivity by category

| Category | Sensitivity | Recommendation |
|----------|-------------|----------------|
| `mission:content` | Low | Standard token scoping |
| `mission:marketing` | Low–Medium | Review generated content before publishing |
| `mission:ops` | Medium | May involve internal project data; use `risk:med` |
| `mission:sales` | High | Customer data; always use `risk:high`; no PII in issues |
| `mission:commerce` | High | Financial data; always use `risk:high`; no payment info in issues |

### 7.2 Guardrails

- **No PII in issues:** Missions involving customer data (`mission:sales`, `mission:commerce`) must never commit personally identifiable information to GitHub Issues.
- **Content review gates:** `mission:content` and `mission:marketing` outputs should be reviewed before external publication.
- **Financial data isolation:** `mission:commerce` missions must not store financial credentials or transaction data in issues.

---

## 8. Verification

- [ ] New labels (`mission:content`, `mission:marketing`, `mission:ops`, `mission:sales`, `mission:commerce`) created in the repository
- [ ] Mission issue template includes new mission types
- [ ] `docs/labels.md` documents all new labels
- [ ] README roadmap reflects Phase 5 status
- [ ] Whitepaper Phase 5 section is expanded
- [ ] A sample mission can be created using each new label

---

## References

- [RoboNuggets: "336 Ways to Use OpenClaw"](https://youtu.be/miJLo234L9s?si=XHUQcggCsYkG_c9D) — community survey of AI agent use cases
- [OpenClaw Use Cases Directory](https://github.com/hesamsheikh/awesome-openclaw-usecases) — community-contributed use case examples
- [Phase 1 playbook — tooling foundation](playbook-phase1-tooling.md)
- [Phase 2 playbook — template skill](playbook-phase2-template-skill.md)
- [Phase 3 playbook — autonomous skill acquisition](playbook-phase3-autonomous-skill-acquisition.md)
- [Phase 4 playbook — agentic loop](playbook-phase4-agentic-loop.md)
- [System whitepaper](whitepaper.md)
- [Label taxonomy](labels.md)
