# Whitepaper: Issue-Centric Autonomous Assistant with DeerFlow, MCP, and GitHub Codespaces

**Version:** 0.1 (draft)  
**Date:** 2026-02-27  
**Owner:** `@8r4n`  
**Primary repos:**  
- Memory & operations: `8r4n/deerflow-ops`  
- Skills codebase: `8r4n/deerflow-skills`  

---

## 1. Executive summary

This system implements an autonomous personal assistant architecture built on **ByteDance DeerFlow** for orchestration, **Model Context Protocol (MCP)** for tool integration, and **GitHub Codespaces** for safe, cloud-hosted execution environments. The system uses **GitHub Issues as the durable memory store and audit trail** instead of a local filesystem, providing transparency, reproducibility, and long-term maintainability. Skill images are published to the **GitHub Container Registry (ghcr.io)** to enable versioned, portable skill evolution.

Key design decisions:
- **Durable memory = GitHub Issues** (`8r4n/deerflow-ops`), with structured templates and labels for machine parsing.
- **Code & skill artifacts = PRs in a dedicated sandbox repo** (`8r4n/deerflow-skills`) with "one folder per skill".
- **Autonomy with safety = GitHub Codespaces** as the primary execution environment, replacing local Docker containers with cloud-hosted dev containers that offer pre-configured toolchains, resource limits, and automatic lifecycle management.
- **Skill image registry = GitHub Container Registry (ghcr.io)**, enabling the system to build, tag, push, and pull skill images for reproducible execution and capability evolution.
- **Programmatic GitHub Issues interface** for progress tracking and mission planning, using the GitHub MCP server to create, update, and query issues automatically during runs.
- **Quality-of-life optimization** targets **maintainability first** and **shipping speed second**, using measurable objective functions.

The system is intended to continuously expand its capabilities by exploring GitHub, evaluating repositories, and integrating suitable libraries/MCP servers as new skills—while logging every action, decision, and artifact to GitHub Issues.

---

## 2. Goals and non-goals

### 2.1 Goals
1) **Maximum safe autonomy**: the assistant can plan and execute multi-step tasks with minimal human involvement.  
2) **Capability growth**: the assistant can add new skills by discovering and integrating GitHub repositories.  
3) **Auditability**: all actions are traceable; all outcomes link back to a run log and durable memories.  
4) **Maintainability**: new skills are documented, tested, and versioned.  
5) **Fast shipping**: deliver working skill PRs and verified memories quickly.  

### 2.2 Non-goals (current scope)
- Self-managed Kubernetes or Terraform infrastructure provisioning  
- Non-Codespaces spawning (systemd services, background daemons on bare metal)  
- Running execution environments outside of GitHub-managed infrastructure

---

## 3. System overview

### 3.1 Components
1) **DeerFlow (GitHub Codespaces runtime)**  
   - Orchestrates agent roles (planner/executor/verifier) and tool use.
   - Runs an autonomy loop: plan → act (tool calls) → observe → decide → repeat.
   - Executes inside a GitHub Codespace with a pre-configured dev container.

2) **MCP servers (tool layer)**  
   - **GitHub MCP server**: read/write issues and PRs; search code/repositories; create PRs; programmatically update progress and plan future missions.  
   - **Web fetch MCP server**: ingest external documentation and web sources.  
   - **Codespaces MCP server**: manage Codespace lifecycle (create, start, stop, delete); execute commands in cloud-hosted environments.  
   - Optional: command-exec MCP (allowlisted), if needed beyond Codespaces.

3) **GitHub Container Registry (ghcr.io)**
   - Skill images are built, tagged, and pushed to `ghcr.io/8r4n/deerflow-skills/<skill-name>`.
   - Enables versioned, portable skill distribution and rollback.

4) **GitHub repositories**
   - `8r4n/deerflow-ops`: issue-based memory store + run journal + playbooks.  
   - `8r4n/deerflow-skills`: PR-based codebase for skill implementations and wrappers.

### 3.2 Data flow (conceptual)
- Mission defined in `deerflow-ops` Issue → DeerFlow reads mission → creates run log issue → uses MCP tools (GitHub, Codespaces, fetch) → produces artifacts:
  - PR(s) in `deerflow-skills`
  - Skill images pushed to `ghcr.io/8r4n/deerflow-skills/<skill-name>`
  - memory issues (`memory:skill`, `memory:repo`, `memory:playbook`) in `deerflow-ops`
  - Progress updates posted to mission/run-log issues via GitHub MCP
  - Links everything together for traceability.

---

## 4. Core design decisions (and rationale)

### 4.1 Durable memory stored in GitHub Issues (not local filesystem)
**Decision:** Long-lived memory is stored as structured GitHub Issues in `8r4n/deerflow-ops`.  
**Rationale:**
- **Auditability**: issue history provides durable traceability.
- **Portability**: memory is not tied to one machine.
- **Maintainability**: consistent templates and review workflow.
- **Human-in-the-loop**: easy review/edit via GitHub UI.

**Tradeoffs:**
- Potential noise and verbosity → mitigated by promotion rules and index issues.

### 4.2 Split ops/memory repo vs skills code repo
**Decision:** Separate `deerflow-ops` (Issues/memory) from `deerflow-skills` (skills code).  
**Rationale:**
- Cleaner separation of concerns.
- Tighter permissions and reduced blast radius.
- Skill code is reviewable via PRs and testable.

### 4.3 Skills as "one folder per skill"
**Decision:** Each skill lives in `skills/<skill-name>/` in `deerflow-skills`.  
**Rationale:**
- Encourages modularity and stable interfaces.
- Low coupling and easy PR reviews.
- Makes “skill completeness” measurable.

### 4.4 GitHub Codespaces as the execution environment
**Decision:** DeerFlow runs inside GitHub Codespaces instead of local Docker containers. Codespaces provide cloud-hosted dev containers with pre-configured toolchains, managed lifecycle, and built-in resource limits.  
**Rationale:**
- Eliminates the need for local Docker infrastructure and the Docker Spawner MCP server.
- Provides ephemeral, reproducible environments with GitHub-managed security boundaries.
- Enables seamless integration with GitHub APIs (Issues, PRs, GHCR) from within the execution environment.
- Codespace idle timeout and retention policies replace manual TTL enforcement.

### 4.5 Skill images published to GitHub Container Registry (ghcr.io)
**Decision:** Skill container images are built and pushed to `ghcr.io/8r4n/deerflow-skills/<skill-name>` as part of the skill lifecycle.  
**Rationale:**
- Versioned images enable reproducible skill execution and rollback.
- GHCR integrates natively with GitHub Actions and Codespaces authentication (GITHUB_TOKEN).
- Images can be pulled into any Codespace or CI workflow without additional registry configuration.
- Supports the system's capability-growth goal: new skills are immediately available as published images.

### 4.6 PR creation restricted to a sandbox repo
**Decision:** DeerFlow opens PRs only to `8r4n/deerflow-skills`.  
**Rationale:**
- Contains code changes in a safe sandbox.
- Prevents unintended edits to other repositories.

### 4.7 Programmatic GitHub Issues interface for progress and planning
**Decision:** The system uses the GitHub MCP server to programmatically create, update, and query GitHub Issues during runs. Progress is posted as comments on run-log and mission issues; future missions are planned by creating new mission issues.  
**Rationale:**
- Provides real-time visibility into autonomous run progress without human polling.
- Enables the system to self-plan by creating future mission issues based on completed work.
- All progress updates are durable and auditable in the GitHub Issues timeline.
- Leverages existing GitHub MCP server capabilities (issue creation, commenting, label management).

### 4.8 Measurable objective functions aligned to creator experience
**Decision:** Optimize for **maintainability (primary)** and **shipping speed (secondary)**.  
**Rationale:** Autonomy only improves life if outputs are stable, documented, and tested.

Metrics:
- Shipping: minimize TTFD, maximize verified deliverables/run, penalize stale runs.
- Maintainability: SCS (skill completeness), CTR (test reliability), MAS (memory alignment).
- Composite: QoLScore = 0.55 * MaintScore + 0.45 * ShipScore.

---

## 5. Mission model (purposes → missions)

Personal-assistant purposes are expressed as mission labels in `deerflow-ops`:
- comms, planning, memory, research, automation, dev, finance, health, logistics, learning, social, risk

Missions produce run logs, code PRs, and promoted durable memories.

---

## 6. Operational process: run lifecycle

1) Create a Mission issue (objective + constraints + acceptance criteria).  
2) Create a Run Log issue linked to the mission via the GitHub MCP server.  
3) Execute within tool and policy constraints inside a GitHub Codespace.  
4) Post progress updates to the run-log issue via the GitHub MCP server.  
5) Produce artifacts (PRs, skill images pushed to ghcr.io, memories).  
6) Promote stable learnings into `memory:*` issues; update pinned indexes.  
7) Plan follow-up missions by creating new mission issues when appropriate.  
8) Close the run as done/blocked with an actionable summary.

**Anti-noise rule:** raw detail lives in run logs; memories are curated.

---

## 7. Security and safety model

Threats:
- untrusted code execution
- secret leakage
- destructive repo writes
- runaway compute

Mitigations:
- GitHub Codespaces isolation: each execution runs in an ephemeral, cloud-hosted container managed by GitHub
- Codespace policies: idle timeout, retention limits, and resource quotas enforced at the organization/repository level
- Least-privilege GitHub tokens: `GITHUB_TOKEN` scoped to required permissions (issues, packages, codespaces)
- GHCR image signing and visibility controls for published skill images
- Explicit approval gates for escalation

---

## 8. Skill lifecycle and quality controls

Each skill must include:
- docs (`README.md`)
- `Dockerfile` (for building the skill image)
- contract tests
- `skill.yaml` manifest

Every shipped skill must have:
- A container image pushed to `ghcr.io/8r4n/deerflow-skills/<skill-name>` with a semantic version tag
- A `memory:skill` issue linking: PR, folder path, GHCR image reference, tools exposed, env vars (names only), verification evidence

---

## 9. Way forward (roadmap)

### Phase 0 — Repo bootstrap (now)
- Add issue templates + docs to `deerflow-ops`
- Add README + standards + template structure to `deerflow-skills`
- Create/pin index issues in `deerflow-ops`
- Add labels in `deerflow-ops`

### Phase 1 — Tooling foundation
- Stand up GitHub MCP server
- Configure dev container for GitHub Codespaces (`.devcontainer/devcontainer.json`)
- Set up GHCR authentication and image push workflow
- Add Web fetch MCP
- Configure programmatic GitHub Issues interface for progress updates

Deliverable: `memory:playbook` documenting Codespaces setup, GHCR workflow, and GitHub Issues integration (authentication, MCP configuration, progress update patterns, and mission planning conventions).

### Phase 2 — Template skill
- Add a canonical `_template` skill skeleton for fast skill generation.
- Include GHCR image build and push steps in the template.

### Phase 3 — First autonomous skill acquisition run
- Discover a repo, prototype in a Codespace, wrap/integrate as a skill, push image to GHCR, PR + memory entries.
- Post progress updates to the run-log issue throughout the run.

### Phase 4+ — Expand mission coverage
- Add non-dev missions (planning, research, automation) as skills mature.
- Enable the system to self-plan future missions by creating mission issues.

---

## 10. Open questions (later)
- Codespace machine type and retention policy tuning
- Secrets management model for Codespaces (Codespace secrets vs. repo secrets)
- Formal schema for `skill.yaml`
- GHCR image retention and cleanup policy
- Comment editing vs batching to reduce notification noise on GitHub Issues