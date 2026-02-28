# Playbook: Phase 1 — Tooling Foundation

**Status:** active  
**Phase:** 1  
**Date:** 2026-02-28  

---

## Purpose

Documents the tooling foundation for the Patronus autonomous assistant system (a ByteDance DeerFlow Agentic System): MCP server configuration, GitHub Codespaces setup, GHCR image push workflow, and automated mission kickoff.

---

## 1. MCP Server Configuration

### 1.1 GitHub MCP Server

The GitHub MCP server provides programmatic access to issues, PRs, code search, and repository operations. It is the backbone of the durable memory model (all `memory:*` and `run:log` issues) and the progress update interface.

**Configuration** (`extensions_config.json` in the repo root):

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

**Required token scopes:** `repo`, `write:packages`, `codespace`

> **Supply-chain note:** The GitHub MCP server version is pinned (`@2025.4.8`) in the config to prevent implicit latest-version resolution via `npx`. When upgrading, update the pinned version explicitly and verify the package integrity.

**Key capabilities enabled:**
- Read/write GitHub Issues (missions, run logs, memory entries)
- Create and update PRs in `8r4n/deerflow-skills`
- Search code and repositories for skill discovery
- Post progress updates to mission and run-log issues
- Plan future missions by creating new mission issues

### 1.2 Web Fetch MCP Server

The web fetch MCP server ingests external documentation and web sources for skill discovery and research missions. It is a Python package (`mcp-server-fetch`).

```json
{
  "mcpServers": {
    "fetch": {
      "enabled": true,
      "type": "stdio",
      "command": "mcp-server-fetch",
      "args": [],
      "env": {}
    }
  }
}
```

**Installation** (included in DeerFlow's dev dependencies, or install manually):
```bash
pip install mcp-server-fetch==2025.4.7
```

> **Supply-chain note:** Pin the version when installing (`==2025.4.7`). The config invokes the locally installed binary rather than downloading on each run.

> **Note:** DeerFlow also includes built-in web search (Tavily) and web fetch (Jina) tools. The MCP fetch server provides an additional integration point for use cases requiring the MCP protocol.

### 1.3 Config resolution

DeerFlow resolves the extensions config in this order:

1. `DEER_FLOW_EXTENSIONS_CONFIG_PATH` environment variable (used in Codespaces)
2. `extensions_config.json` in the current working directory
3. `extensions_config.json` in the parent directory of CWD
4. `mcp_config.json` (legacy fallback)

The devcontainer sets `DEER_FLOW_EXTENSIONS_CONFIG_PATH` to point to the repo-root config file.

---

## 2. GitHub Codespaces Setup

### 2.1 Dev container configuration

The `.devcontainer/devcontainer.json` configures:

| Component | Value |
|-----------|-------|
| Base image | `mcr.microsoft.com/devcontainers/python:3.12` |
| Node.js | 20 (via devcontainer feature) |
| Docker | Docker-in-Docker (for building skill images and running aio sandbox containers) |
| GitHub CLI | Pre-installed (for `gh` commands) |
| Ports | 2024 (LangGraph), 2026 (Nginx), 3000 (frontend), 8001 (Gateway API), 8080 (aio sandbox) |

### 2.2 Environment variables

| Variable | Source | Purpose |
|----------|--------|---------|
| `GITHUB_TOKEN` | Codespaces automatic injection | GitHub API access for MCP server |
| `DEER_FLOW_EXTENSIONS_CONFIG_PATH` | devcontainer.json | Points DeerFlow to the MCP config |
| `DOCKER_BUILDKIT` | devcontainer.json | Enables BuildKit for efficient image builds |

### 2.3 Post-create setup

The devcontainer automatically (via `.devcontainer/post-create.sh`):
1. Initializes the `deer-flow` submodule
2. Installs DeerFlow Python dependencies (`pip install -e '.[dev]'`)
3. Generates `config.yaml` and `.env` from example templates (`make config`)
4. Enables the aio sandbox in `config.yaml` (replaces `LocalSandboxProvider` with `AioSandboxProvider`)
5. Installs frontend dependencies (`pnpm install`)
6. Authenticates to GHCR using `GITHUB_TOKEN`
7. Pre-pulls the aio sandbox image (`all-in-one-sandbox:latest`)

### 2.4 Starting DeerFlow in a Codespace

```bash
# 1. Configure API keys (first time only — config.yaml and .env are auto-generated)
cd deer-flow
# Edit .env with your LLM and search provider API keys

# 2. Start all services (backend + frontend + nginx)
make dev

# 3. Access UI via Codespace port 2026
```

### 2.5 Aio sandbox in Codespaces

The aio sandbox is **enabled by default** in Codespaces. The post-create script patches `config.yaml` to use `AioSandboxProvider` instead of `LocalSandboxProvider`. The sandbox image (`enterprise-public-cn-beijing.cr.volces.com/vefaas-public/all-in-one-sandbox:latest`) is pre-pulled during codespace creation, and Docker-in-Docker is enabled so the provider can start and manage sandbox containers automatically.

To revert to local sandbox execution, edit `deer-flow/config.yaml`:

```yaml
sandbox:
  use: src.sandbox.local:LocalSandboxProvider
```

See the [upstream Sandbox Configuration Guide](https://github.com/bytedance/deer-flow/blob/main/backend/docs/CONFIGURATION.md#sandbox) for additional options (custom mounts, environment variables, provisioner mode).

---

## 3. GHCR Authentication and Image Push

### 3.1 Authentication

**In Codespaces:**
```bash
echo $GITHUB_TOKEN | docker login ghcr.io -u $GITHUB_USER --password-stdin
```

The devcontainer post-create command handles this automatically.

**In GitHub Actions:**
```yaml
- uses: docker/login-action@v3
  with:
    registry: ghcr.io
    username: ${{ github.actor }}
    password: ${{ secrets.GITHUB_TOKEN }}
```

### 3.2 Image push workflow

The `.github/workflows/ghcr-publish.yml` workflow:

- **Triggers:** `workflow_dispatch` only (manual)
- **Prerequisites:** A `Dockerfile` must exist at the repo root (the workflow checks and fails gracefully if absent)
- **Permissions:** `contents: read`, `packages: write`
- **Image naming:** `ghcr.io/8r4n/deerflow-ops:<tag>`
- **Tags:** `sha-<short-sha>`, `latest` (on main branch), custom tag (on dispatch)

> **Note:** This repo does not currently have a `Dockerfile`. The workflow serves as the reference pattern for GHCR publishing; the actual skill image builds will live in `8r4n/deerflow-skills`.

### 3.3 Skill image convention

Skill images follow the pattern:
```
ghcr.io/8r4n/deerflow-skills/<skill-name>:<version>
```

Each skill's `Dockerfile` in `8r4n/deerflow-skills` builds to this registry path. The GHCR workflow in this repo serves as the reference pattern.

---

## 4. Automated Mission Kickoff

### 4.1 Kickoff workflow

The `.github/workflows/kickoff.yml` workflow automates DeerFlow mission processing:

| Trigger | Behavior |
|---------|----------|
| `workflow_dispatch` | Manual kickoff — provide a mission issue number |
| `issues.labeled` | Auto-kickoff when an issue is labeled `status:active` |

### 4.2 Workflow steps

**Current behavior (scaffold)**

1. **Determine mission issue** — from dispatch input or triggering issue event
2. **Validate mission label** — confirms the issue has a `mission:*` label
3. **Set up environment** — Python 3.12, Node.js 20, DeerFlow dependencies
4. **Configure DeerFlow** — applies `config.yaml` and `.env` from examples
5. **Post kickoff comment** — notifies the mission issue that processing has started
6. **Validate environment** — confirms DeerFlow dependencies and config are present (does not yet invoke DeerFlow autonomously)
7. **Post completion comment** — reports success or failure back to the issue

**Planned enhancement (not yet implemented)**

Step 6 will be wired to the real DeerFlow entrypoint once LLM API keys are configured as repository secrets. This will enable full autonomous mission processing through the kickoff workflow.

### 4.3 Required secrets

| Secret | Purpose |
|--------|---------|
| `GITHUB_TOKEN` | Automatic — GitHub Actions provides this |
| LLM API keys | Must be added as repository secrets (e.g., `OPENAI_API_KEY`, `TAVILY_API_KEY`) |

### 4.4 Manual kickoff

```bash
gh workflow run kickoff.yml \
  --repo 8r4n/deerflow-ops \
  -f mission_issue=42
```

### 4.5 Automatic kickoff

When a mission issue is labeled `status:active`, the kickoff workflow runs automatically. This enables the flow:

1. Create a mission issue using the mission template
2. Add the appropriate `mission:*` label
3. Add `status:active` → triggers the kickoff workflow
4. DeerFlow processes the mission and posts updates to the issue

---

## 5. Programmatic GitHub Issues Interface

### 5.1 Progress update patterns

DeerFlow uses the GitHub MCP server to post progress updates during runs:

- **Run log creation:** Create a `run:log` issue linked to the mission
- **Status updates:** Post comments with step-by-step progress
- **Artifact links:** Comment with PR links, GHCR image references, and memory entries
- **Completion:** Close the run log with a summary; update the mission issue

### 5.2 Mission planning conventions

The system can self-plan by creating new mission issues:

1. During a run, identify follow-up work
2. Create a new mission issue using the mission template
3. Apply the appropriate `mission:*` label
4. Set `status:active` to trigger automatic kickoff (or leave for human review)

### 5.3 Label hygiene

- Every mission issue: exactly one `mission:*` + one `status:*`
- Every run log: `run:log` + one `status:*`
- Every memory entry: one `memory:*` + one `status:*`
- Add `risk:*` for high-sensitivity runs

---

## Verification

- [ ] `extensions_config.json` exists at repo root with GitHub and fetch MCP servers
- [ ] `.devcontainer/devcontainer.json` sets `DEER_FLOW_EXTENSIONS_CONFIG_PATH`
- [ ] `.github/workflows/ghcr-publish.yml` handles GHCR authentication and push
- [ ] `.github/workflows/kickoff.yml` triggers on `workflow_dispatch` and `issues.labeled`
- [ ] Codespace starts successfully with MCP config resolved
- [ ] Manual workflow dispatch runs without errors

---

## Related resources

- [System whitepaper](whitepaper.md)
- [DeerFlow architecture](deerflow-software-architecture.md)
- [Phase 2 playbook — template skill](playbook-phase2-template-skill.md)
- [Phase 3 playbook — autonomous skill acquisition](playbook-phase3-autonomous-skill-acquisition.md)
- [Label taxonomy](labels.md)
- [Index issues](index-issues.md)
