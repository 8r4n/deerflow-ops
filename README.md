# 🦌 DeerFlow Ops

**Operations, memory, and run journal** for a cloud-hosted autonomous assistant built on [ByteDance DeerFlow](https://github.com/bytedance/deer-flow) and [GitHub Codespaces](https://github.com/features/codespaces).

| Repo | Purpose |
|------|---------|
| [`8r4n/deerflow-ops`](https://github.com/8r4n/deerflow-ops) (this repo) | Issue-based durable memory, run logs, mission tracking, and bootstrap docs |
| [`8r4n/deerflow-skills`](https://github.com/8r4n/deerflow-skills) | Skill implementations — one folder per skill with Dockerfiles, tests, and manifests |
| [`bytedance/deer-flow`](https://github.com/bytedance/deer-flow) (submodule → `deer-flow/`) | Upstream DeerFlow runtime for orchestration |

---

## Architecture overview

The system implements an autonomous personal assistant that uses:

- **DeerFlow** for agent orchestration (planner → executor → verifier loop)
- **MCP servers** for tool integration (GitHub, web fetch, Codespaces)
- **GitHub Codespaces** for safe, cloud-hosted execution environments
- **GitHub Container Registry (ghcr.io)** for versioned skill image publishing
- **GitHub Issues** as the durable memory store, audit trail, and programmatic progress interface

See [`docs/whitepaper.md`](docs/whitepaper.md) for the full design rationale.

### Data flow

```
Mission issue (deerflow-ops)
  └─► DeerFlow reads mission (via GitHub MCP)
        └─► Creates run log issue (via GitHub MCP)
              └─► Executes in GitHub Codespace
                    ├─► PRs in deerflow-skills
                    ├─► Skill images pushed to ghcr.io
                    ├─► Progress posted to issues (via GitHub MCP)
                    ├─► memory:* issues in deerflow-ops
                    └─► Links everything for traceability
```

---

## Bootstrap guide

### Prerequisites

| Requirement | Minimum |
|-------------|---------|
| GitHub account | With Codespaces access |
| Git | 2.x |
| Python | 3.11+ |
| Node.js | 18+ (for DeerFlow frontend) |
| Make | any |

You also need API keys for at least one LLM provider (OpenAI, Anthropic, etc.) and a search provider (Tavily recommended). A `GITHUB_TOKEN` with `repo`, `write:packages`, and `codespace` scopes is required for GHCR and Codespaces integration.

### 1. Open in GitHub Codespaces (recommended)

Click **Code → Codespaces → Create codespace on main** in the GitHub UI, or use the CLI:

```bash
gh codespace create --repo 8r4n/deerflow-ops --machine standardLinux32gb
```

The dev container will automatically initialize the submodule and install backend/frontend dependencies. You will still need to configure API keys (see step 2) and start services manually (see step 3).

### 1b. Alternative: Clone locally

```bash
git clone --recurse-submodules https://github.com/8r4n/deerflow-ops.git
cd deerflow-ops
```

If you already cloned without `--recurse-submodules`:

```bash
git submodule update --init --recursive
```

### 2. Set up DeerFlow

```bash
cd deer-flow
make config          # generates .env and config.yaml from examples
```

Edit `deer-flow/.env` and add your API keys:

```bash
OPENAI_API_KEY=your-openai-api-key
TAVILY_API_KEY=your-tavily-api-key
# Add other provider keys as needed
```

Edit `deer-flow/config.yaml` to configure your preferred model(s). See the [upstream configuration guide](https://github.com/bytedance/deer-flow/blob/main/backend/docs/CONFIGURATION.md) for details.

### 3. Run DeerFlow

#### Option A — GitHub Codespaces (recommended)

If running in a Codespace, dependencies are pre-installed by the dev container. Start services manually:

```bash
cd deer-flow
make backend         # start backend services
cd frontend && pnpm dev  # start frontend (separate terminal)
```

Access the UI through the Codespace port-forwarding on port **2026**.

#### Option B — Local development

```bash
cd deer-flow

# Backend
pip install -e ".[dev]"
make backend

# Frontend (separate terminal)
cd frontend && pnpm install && pnpm dev
```

### 4. Configure MCP servers

The system uses these MCP servers:

| Server | Purpose | Setup |
|--------|---------|-------|
| **GitHub MCP** | Read/write issues and PRs, search code, update progress, plan missions | Provide a `GITHUB_TOKEN` with `repo`, `write:packages`, and `codespace` scopes |
| **Web fetch MCP** | Ingest external documentation | Included in DeerFlow |
| **Codespaces MCP** | Manage Codespace lifecycle (create, start, stop, delete) | Planned — see Phase 1 roadmap |

### 5. Staying up to date with upstream DeerFlow

```bash
cd deer-flow
git fetch origin
git checkout main
git pull
cd ..
git add deer-flow
git commit -m "Update deer-flow submodule to latest upstream"
```

---

## Repository structure

```
deerflow-ops/
├── README.md                   ← you are here
├── extensions_config.json      ← MCP server configuration (GitHub, fetch)
├── deer-flow/                  ← bytedance/deer-flow submodule
├── .devcontainer/
│   └── devcontainer.json      ← GitHub Codespaces dev container config
├── docs/
│   ├── whitepaper.md           ← full system design
│   ├── deerflow-software-architecture.md ← DeerFlow architecture analysis
│   ├── labels.md               ← GitHub label taxonomy
│   ├── index-issues.md         ← how to maintain pinned index issues
│   └── playbook-phase1-tooling.md ← Phase 1 tooling setup playbook
└── .github/
    ├── ISSUE_TEMPLATE/         ← structured templates for missions,
    │                              run logs, and memory entries
    └── workflows/
        ├── ghcr-publish.yml    ← GHCR authentication and image push
        └── kickoff.yml         ← automatic mission kickoff
```

---

## Memory model

All durable memory lives as GitHub Issues in this repo, organized by labels:

| Label | Purpose |
|-------|---------|
| `memory:skill` | Skill documentation and metadata |
| `memory:repo` | Repository evaluations (adopted/rejected) |
| `memory:playbook` | Reusable procedures and setup guides |
| `run:log` | Individual execution logs |
| `mission:*` | Mission categories (comms, dev, research, etc.) |
| `status:*` | Lifecycle state (active, blocked, done, deprecated) |

See [`docs/labels.md`](docs/labels.md) for the full taxonomy and [`docs/index-issues.md`](docs/index-issues.md) for how pinned index issues are maintained.

---

## Roadmap

| Phase | Description | Status |
|-------|-------------|--------|
| **0** | Repo bootstrap — templates, docs, labels, indexes | ✅ |
| **1** | Tooling foundation — GitHub MCP, Codespaces, GHCR, web fetch MCP | ✅ |
| **2** | Template skill — canonical `_template` skeleton in `deerflow-skills` with GHCR publish | 🔜 |
| **3** | First autonomous skill acquisition run (in Codespaces) | 🔜 |
| **4+** | Expand mission coverage (planning, research, automation) | 🔜 |

---

## Related resources

- [DeerFlow upstream docs](https://github.com/bytedance/deer-flow#documentation)
- [DeerFlow Skills repo](https://github.com/8r4n/deerflow-skills)
- [System whitepaper](docs/whitepaper.md)

## License

This repository is maintained by [@8r4n](https://github.com/8r4n). The `deer-flow/` submodule is licensed under the [MIT License](https://github.com/bytedance/deer-flow/blob/main/LICENSE) by ByteDance.