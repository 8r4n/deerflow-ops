# Playbook: Phase 3 — Autonomous Skill Acquisition

**Status:** active  
**Phase:** 3  
**Date:** 2026-02-28  

---

## Purpose

Documents how to enable the autonomous DeerFlow agent to operate inside a GitHub Codespace, use the GitHub MCP server to interact with both `8r4n/deerflow-ops` and `8r4n/deerflow-skills`, and autonomously discover, evaluate, wrap, and publish new skills.

---

## 1. Prerequisites

### 1.1 Repository secrets

The following secrets must be configured on `8r4n/deerflow-ops` (**Settings → Secrets and variables → Actions** or **Codespaces**):

| Secret | Purpose | Required |
|--------|---------|----------|
| `OPENAI_API_KEY` (or other LLM provider key) | Powers DeerFlow's planner / executor / verifier agents | ✅ |
| `TAVILY_API_KEY` | Web search tool for skill discovery and research | ✅ |
| `GITHUB_TOKEN` | Automatically provided by Codespaces and Actions; needs `repo`, `write:packages`, `codespace` scopes | ✅ (automatic) |

> **Codespaces secrets** are injected as environment variables into every Codespace created from the repository. Add them at **Settings → Secrets and variables → Codespaces**.

### 1.2 GitHub MCP server

The GitHub MCP server must be configured in `extensions_config.json` (already present in the repo root):

```json
{
  "mcpServers": {
    "github": {
      "enabled": true,
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github@2025.4.8"],
      "env": {
        "GITHUB_TOKEN": "$GITHUB_TOKEN"
      }
    }
  }
}
```

The `$GITHUB_TOKEN` variable is resolved from the environment. In Codespaces it is automatically injected; in GitHub Actions it comes from `secrets.GITHUB_TOKEN`.

**Required token scopes:**

| Scope | Why |
|-------|-----|
| `repo` | Read/write issues in `deerflow-ops`, create PRs in `deerflow-skills`, search code |
| `write:packages` | Push skill images to `ghcr.io/8r4n/deerflow-skills/<skill-name>` |
| `codespace` | Manage Codespace lifecycle (create, start, stop) |

### 1.3 Dev container

The `.devcontainer/devcontainer.json` sets `DEER_FLOW_EXTENSIONS_CONFIG_PATH` so DeerFlow resolves the MCP config at startup. The `postCreateCommand` (`.devcontainer/post-create.sh`) installs all backend/frontend dependencies, enables the aio sandbox, authenticates to GHCR, and pre-pulls the sandbox image.

No additional setup is needed — opening a Codespace from this repo automatically provisions a ready-to-run DeerFlow environment.

---

## 2. Enabling Autonomous Operation in Codespaces

### 2.1 Create a Codespace

**Via the GitHub UI:**

Click **Code → Codespaces → Create codespace on main** on the `8r4n/deerflow-ops` repository page.

**Via the CLI:**

```bash
gh codespace create --repo 8r4n/deerflow-ops --machine standardLinux32gb
```

Wait for the post-create script to finish. It initializes the `deer-flow` submodule, installs dependencies, generates config files, and authenticates to GHCR.

### 2.2 Configure API keys

If API keys are set as **Codespaces secrets**, they are already available as environment variables. Otherwise, edit `deer-flow/.env`:

```bash
cd deer-flow
# Edit .env with your LLM and search provider API keys
OPENAI_API_KEY=your-openai-api-key
TAVILY_API_KEY=your-tavily-api-key
```

### 2.3 Verify the GitHub MCP server

Confirm that the GitHub MCP server can access both repositories:

```bash
# Verify the token is present
echo "$GITHUB_TOKEN" | head -c 8

# Verify access to deerflow-ops (issues, labels)
gh issue list --repo 8r4n/deerflow-ops --limit 5

# Verify access to deerflow-skills (PRs, code)
gh repo view 8r4n/deerflow-skills --json name
```

The GitHub MCP server uses the same `$GITHUB_TOKEN` for all API calls. As long as the token has the scopes listed in §1.2, DeerFlow can read/write issues in `deerflow-ops` and create PRs in `deerflow-skills`.

### 2.4 Start DeerFlow

```bash
cd deer-flow
make dev
```

DeerFlow starts the LangGraph server (port 2024), the Gateway API (port 8001), the frontend (port 3000), and Nginx (port 2026). Access the UI via Codespace port-forwarding on port **2026**.

---

## 3. Autonomous Skill Acquisition Flow

When DeerFlow processes a `mission:dev` or `mission:research` mission that involves skill acquisition, it follows this end-to-end flow:

```
┌──────────────────────────────────────────────────────────────────┐
│ 1. Read mission issue (deerflow-ops)          ← GitHub MCP      │
│ 2. Create run:log issue (deerflow-ops)        ← GitHub MCP      │
│ 3. Discover candidate repos                   ← GitHub MCP +    │
│                                                  Web Fetch MCP  │
│ 4. Evaluate candidates (docs, tests, license) ← GitHub MCP      │
│ 5. Clone and prototype in Codespace sandbox   ← aio sandbox     │
│ 6. Copy _template, implement skill wrapper    ← local tools     │
│ 7. Write contract tests                       ← local tools     │
│ 8. Build and test image (make build/test)     ← Docker-in-Docker│
│ 9. Push image to GHCR                         ← Docker CLI      │
│10. Open PR in deerflow-skills                 ← GitHub MCP      │
│11. Create memory:skill issue in deerflow-ops  ← GitHub MCP      │
│12. Update run:log with results                ← GitHub MCP      │
│13. Close run:log and update mission           ← GitHub MCP      │
└──────────────────────────────────────────────────────────────────┘
```

### 3.1 Step-by-step details

**Step 1 — Read mission.**  
DeerFlow reads the mission issue body and labels via the GitHub MCP server. The mission should contain an objective (e.g., "Discover and wrap a Python library for PDF parsing as a skill"), constraints, and acceptance criteria.

**Step 2 — Create run log.**  
A `run:log` issue is created in `deerflow-ops` and linked to the mission. All progress is posted as comments on this issue.

**Step 3 — Discover candidate repos.**  
DeerFlow uses the GitHub MCP server's code/repository search to find candidates. It may also use the Web Fetch MCP server to research documentation, blog posts, or package indexes (e.g., PyPI).

**Step 4 — Evaluate candidates.**  
For each candidate repo, DeerFlow checks:
- README quality and documentation
- License compatibility (MIT, Apache-2.0, BSD preferred)
- Test coverage and CI status
- Stars, recent activity, and maintenance signals
- API surface suitability for MCP wrapping

DeerFlow creates a `memory:repo` issue in `deerflow-ops` documenting the evaluation (adopted / rejected / revisit).

**Step 5 — Prototype in sandbox.**  
The selected library is installed in the aio sandbox and tested with sample inputs to validate functionality. This runs inside Docker-in-Docker in the Codespace.

**Step 6 — Create skill from template.**  
DeerFlow copies `skills/_template/` from `deerflow-ops` into a new `skills/<skill-name>/` directory (locally, for the PR). It replaces `<skill-name>` placeholders and implements the skill wrapper code.

**Step 7 — Write contract tests.**  
Contract tests are added in `tests/test_contract.py` to validate that the skill server starts, tool endpoints respond, and errors are handled.

**Step 8 — Build and test the image.**  
```bash
cd skills/<skill-name>
make build   # builds the Docker image
make test    # runs contract tests inside Docker
```

**Step 9 — Push to GHCR.**  
```bash
make push      # pushes :version and :latest tags
make tag-sha   # pushes :sha-<short-sha> tag
```

Image naming follows the convention: `ghcr.io/8r4n/deerflow-skills/<skill-name>:<tag>`.

**Step 10 — Open PR in deerflow-skills.**  
DeerFlow uses the GitHub MCP server to create a pull request in `8r4n/deerflow-skills` containing the new skill folder. The PR description includes:
- Skill purpose and tools exposed
- Build/test evidence
- GHCR image reference
- Link to the mission and run-log issues

**Step 11 — Create memory issue.**  
A `memory:skill` issue is created in `deerflow-ops` with:
- Skill name and version
- PR link
- GHCR image reference
- Tools exposed
- Environment variables (names only, no values)
- Verification evidence (test output, build logs)

**Step 12–13 — Close out.**  
The run-log issue is updated with a summary and closed. The mission issue is updated with links to the PR and memory issue.

### 3.2 Cross-repo access pattern

DeerFlow operates from a Codespace on `deerflow-ops` but creates PRs in `deerflow-skills`. This works because the `GITHUB_TOKEN` with `repo` scope grants access to both repositories under the same owner (`8r4n`).

```
Codespace (deerflow-ops)
  │
  ├─ GitHub MCP → deerflow-ops issues   (read/write)
  ├─ GitHub MCP → deerflow-skills PRs   (create/update)
  ├─ GitHub MCP → any public repo       (search/read)
  │
  └─ Docker CLI → ghcr.io              (push skill images)
```

> **Important:** The `GITHUB_TOKEN` automatically provided by Codespaces is scoped to the repository that created the Codespace. To access `deerflow-skills`, you need a **personal access token (classic)** or **fine-grained token** with `repo` scope covering both repositories. Add it as a Codespaces secret named `GITHUB_TOKEN`.

---

## 4. Triggering Autonomous Runs

### 4.1 Interactive (via Codespace UI)

1. Open the DeerFlow UI (port 2026) in the Codespace.
2. Paste the mission objective into the chat.
3. DeerFlow plans and executes the skill acquisition flow interactively — you can observe and intervene.

### 4.2 Via the kickoff workflow

The `.github/workflows/kickoff.yml` workflow automates mission processing:

**Manual dispatch:**

```bash
gh workflow run kickoff.yml \
  --repo 8r4n/deerflow-ops \
  -f mission_issue=42
```

**Automatic trigger:**

Label a mission issue with `status:active` → the kickoff workflow runs automatically.

> **Note:** The kickoff workflow currently validates the environment but does not invoke DeerFlow autonomously (see §5 on wiring the entrypoint). Full autonomous execution requires LLM API keys configured as repository secrets.

### 4.3 Creating a skill acquisition mission

Use the mission issue template in `deerflow-ops`:

**Title:** `Acquire skill: <library-name>`

**Body:**
```markdown
## Objective
Discover, evaluate, and wrap <library-name> as a DeerFlow skill.

## Constraints
- License must be MIT, Apache-2.0, or BSD
- Skill must expose at least one MCP-compatible tool
- Contract tests must pass

## Acceptance criteria
- [ ] PR opened in deerflow-skills with skill folder
- [ ] Skill image pushed to ghcr.io
- [ ] memory:skill issue created in deerflow-ops
- [ ] Contract tests pass (make test)
```

**Labels:** `mission:dev`, `status:active`

---

## 5. Wiring the DeerFlow Entrypoint (Planned)

The kickoff workflow currently runs a scaffold step (§4.2). To enable full autonomous execution, the "Validate environment" step in `.github/workflows/kickoff.yml` must be replaced with a call to the DeerFlow entrypoint.

**What is needed:**

1. **Add LLM API keys** as repository secrets (`OPENAI_API_KEY`, `TAVILY_API_KEY`, etc.)
2. **Add a cross-repo token** as a repository or Codespaces secret if the default `GITHUB_TOKEN` lacks sufficient scope for `deerflow-skills` access
3. **Replace the scaffold step** in `kickoff.yml` with the actual DeerFlow invocation:

```yaml
- name: Run DeerFlow autonomous mission
  working-directory: deer-flow
  env:
    MISSION_ISSUE: ${{ steps.mission.outputs.issue_number }}
    MISSION_REPO: ${{ github.repository }}
    MODEL_OVERRIDE: ${{ inputs.model }}
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
    TAVILY_API_KEY: ${{ secrets.TAVILY_API_KEY }}
  run: |
    python -m src.entrypoint \
      --mission-issue "$MISSION_ISSUE" \
      --mission-repo "$MISSION_REPO" \
      ${MODEL_OVERRIDE:+--model "$MODEL_OVERRIDE"}
```

> **Note:** The exact entrypoint command (`python -m src.entrypoint`) is a placeholder. It will be finalized when the DeerFlow autonomous runner module is implemented.

---

## 6. Security Considerations

### 6.1 Token scoping

- Use the **least-privilege** token that covers both repositories. Prefer fine-grained tokens scoped to `8r4n/deerflow-ops` and `8r4n/deerflow-skills` over classic tokens with broad `repo` scope.
- Never commit tokens into source code. Use Codespaces secrets or repository secrets exclusively.

### 6.2 Codespace isolation

- Each Codespace runs in an ephemeral, GitHub-managed container with automatic idle timeout and retention policies.
- The aio sandbox provides an additional layer of isolation for code execution within the Codespace (Docker-in-Docker).

### 6.3 PR review gates

- DeerFlow opens PRs in `deerflow-skills` but does **not** merge them automatically.
- All skill PRs require human review before merging, providing a safety checkpoint.

### 6.4 GHCR image visibility

- Skill images pushed to `ghcr.io/8r4n/deerflow-skills/<skill-name>` default to the repository's visibility setting.
- Review image visibility after the first push to ensure it matches your intent (public vs. private).

### 6.5 Secret rotation

- Rotate LLM API keys and personal access tokens periodically.
- After rotation, update the Codespaces secrets immediately to avoid failed runs.

---

## 7. Troubleshooting

### GitHub MCP server cannot access deerflow-skills

**Symptom:** DeerFlow fails when creating a PR in `deerflow-skills` with a 403 or 404 error.

**Cause:** The `GITHUB_TOKEN` does not have `repo` scope for `deerflow-skills`.

**Fix:** Create a personal access token with `repo` scope covering both repositories. Add it as a Codespaces secret named `GITHUB_TOKEN` (this overrides the auto-injected token).

### DeerFlow cannot push images to GHCR

**Symptom:** `docker push` fails with "denied" or "unauthorized".

**Cause:** Missing `write:packages` scope on the token, or GHCR authentication was not completed.

**Fix:**
```bash
echo "$GITHUB_TOKEN" | docker login ghcr.io -u "$GITHUB_USER" --password-stdin
```
Ensure the token has `write:packages` scope. The post-create script runs this automatically, but it may fail silently if the token lacks permissions.

### Kickoff workflow does not invoke DeerFlow

**Symptom:** The workflow posts kickoff/completion comments but does not perform any autonomous work.

**Cause:** The kickoff workflow currently runs a scaffold step (see §5). LLM API keys are not yet configured as repository secrets, or the entrypoint has not been wired.

**Fix:** Add the required secrets and replace the scaffold step per §5.

### Codespace runs out of disk space

**Symptom:** Docker builds or image pulls fail with "no space left on device".

**Fix:** Use a larger machine type when creating the Codespace:
```bash
gh codespace create --repo 8r4n/deerflow-ops --machine largePremiumLinux
```
Or clean up unused Docker images: `docker system prune -af`

---

## Verification

- [ ] LLM API keys are added as Codespaces secrets
- [ ] `GITHUB_TOKEN` (or equivalent PAT) can access both `deerflow-ops` and `deerflow-skills`
- [ ] Codespace starts successfully and post-create script completes
- [ ] DeerFlow starts with `make dev` and the UI is accessible on port 2026
- [ ] GitHub MCP server resolves correctly (`DEER_FLOW_EXTENSIONS_CONFIG_PATH` set)
- [ ] Agent can list issues in `deerflow-ops` via the GitHub MCP server
- [ ] Agent can create a test PR in `deerflow-skills` via the GitHub MCP server
- [ ] Docker build and push to GHCR work from within the Codespace
- [ ] Kickoff workflow triggers on `status:active` label

---

## Related resources

- [Phase 1 playbook — tooling foundation](playbook-phase1-tooling.md)
- [Phase 2 playbook — template skill](playbook-phase2-template-skill.md)
- [System whitepaper](whitepaper.md)
- [DeerFlow architecture](deerflow-software-architecture.md)
- [Label taxonomy](labels.md)
- [Index issues](index-issues.md)
- [Skill standard (deerflow-skills)](https://github.com/8r4n/deerflow-skills/blob/main/docs/skill-standard.md)
