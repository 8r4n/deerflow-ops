# Whitepaper: Issue-Centric Autonomous Assistant with DeerFlow, MCP, and Docker Sandboxing

**Version:** 0.1 (draft)  
**Date:** 2026-02-27  
**Owner:** `@8r4n`  
**Primary repos:**  
- Memory & operations: `8r4n/deerflow-ops`  
- Skills codebase: `8r4n/deerflow-skills`  

---

## 1. Executive summary

This system implements an autonomous personal assistant architecture built on **ByteDance DeerFlow** for orchestration, **Model Context Protocol (MCP)** for tool integration, and **local Docker sandboxing** for safe execution of third‑party code and scalable “spawn other systems” behavior. The system uses **GitHub Issues as the durable memory store and audit trail** instead of a local filesystem, providing transparency, reproducibility, and long-term maintainability.

Key design decisions:
- **Durable memory = GitHub Issues** (`8r4n/deerflow-ops`), with structured templates and labels for machine parsing.
- **Code & skill artifacts = PRs in a dedicated sandbox repo** (`8r4n/deerflow-skills`) with “one folder per skill”.
- **Autonomy with safety = Docker-only spawning via a dedicated Docker Spawner MCP server**, enforcing strict policies (no privileged containers, no docker socket mounts, TTL, resource limits, workspace-only mounts).
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
- Cloud provisioning (VMs, Kubernetes, Terraform, etc.)  
- Non-Docker spawning (systemd services, background daemons outside the sandbox)  
- Assuming any remote hosted “agent platform”; this design is local-first.

---

## 3. System overview

### 3.1 Components
1) **DeerFlow (local runtime)**  
   - Orchestrates agent roles (planner/executor/verifier) and tool use.
   - Runs an autonomy loop: plan → act (tool calls) → observe → decide → repeat.

2) **MCP servers (tool layer)**  
   - **GitHub MCP server**: read/write issues and PRs; search code/repositories; create PRs.  
   - **Web fetch MCP server**: ingest external documentation and web sources.  
   - **Docker Spawner MCP server** (custom): build/run/stop containers; collect logs; enforce policy.  
   - Optional: command-exec MCP (allowlisted), if needed beyond Docker.

3) **GitHub repositories**
   - `8r4n/deerflow-ops`: issue-based memory store + run journal + playbooks.  
   - `8r4n/deerflow-skills`: PR-based codebase for skill implementations and wrappers.

### 3.2 Data flow (conceptual)
- Mission defined in `deerflow-ops` Issue → DeerFlow reads mission → creates run log issue → uses MCP tools (GitHub, Docker, fetch) → produces artifacts:
  - PR(s) in `deerflow-skills`
  - memory issues (`memory:skill`, `memory:repo`, `memory:playbook`) in `deerflow-ops`
  - links everything together for traceability.

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

### 4.3 Skills as “one folder per skill”
**Decision:** Each skill lives in `skills/<skill-name>/` in `deerflow-skills`.  
**Rationale:**
- Encourages modularity and stable interfaces.
- Low coupling and easy PR reviews.
- Makes “skill completeness” measurable.

### 4.4 Docker-only “spawn other systems” via a controlled Spawner MCP server (build allowed)
**Decision:** DeerFlow spawns systems only via local Docker containers, mediated by a dedicated Spawner MCP server implementing a restricted tool surface and strict policies. Docker **build** is allowed.  
**Rationale:**
- Sandboxes untrusted code (repo evaluation, tests).
- Provides an enforcement boundary for security policy.
- Enables reproducible skill builds and executions.

### 4.5 PR creation restricted to a sandbox repo
**Decision:** DeerFlow opens PRs only to `8r4n/deerflow-skills`.  
**Rationale:**
- Contains code changes in a safe sandbox.
- Prevents unintended edits to other repositories.

### 4.6 Measurable objective functions aligned to creator experience
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
2) Create a Run Log issue linked to the mission.  
3) Execute within tool and policy constraints.  
4) Produce artifacts (PRs, memories).  
5) Promote stable learnings into `memory:*` issues; update pinned indexes.  
6) Close the run as done/blocked with an actionable summary.

**Anti-noise rule:** raw detail lives in run logs; memories are curated.

---

## 7. Security and safety model

Threats:
- untrusted code execution
- secret leakage
- destructive repo writes
- runaway compute

Mitigations:
- Docker-only sandboxing
- Spawner MCP policy: no privileged, no docker socket mount, workspace-only mounts, TTL, resource limits, default no network
- least-privilege GitHub tokens
- explicit approval gates for escalation

---

## 8. Skill lifecycle and quality controls

Each skill must include:
- docs (`README.md`)
- `Dockerfile`
- contract tests
- `skill.yaml` manifest

Every shipped skill must have a `memory:skill` issue linking:
- PR, folder path, docker recipe, tools exposed, env vars (names only), verification evidence

---

## 9. Way forward (roadmap)

### Phase 0 — Repo bootstrap (now)
- Add issue templates + docs to `deerflow-ops`
- Add README + standards + template structure to `deerflow-skills`
- Create/pin index issues in `deerflow-ops`
- Add labels in `deerflow-ops`

### Phase 1 — Tooling foundation
- Stand up GitHub MCP locally
- Implement/run Docker Spawner MCP with strict policy + TTL cleanup
- Add Web fetch MCP

Deliverable: `memory:playbook` documenting local setup and spawner policy.

### Phase 2 — Template skill
- Add a canonical `_template` skill skeleton for fast skill generation.

### Phase 3 — First autonomous skill acquisition run
- Discover a repo, prototype in Docker, wrap/integrate as a skill, PR + memory entries.

### Phase 4+ — Expand mission coverage
- Add non-dev missions (planning, research, automation) as skills mature.

---

## 10. Open questions (later)
- CI strategy for `deerflow-skills`
- secrets management model
- formal schema for `skill.yaml`
- comment editing vs batching to reduce notification noise