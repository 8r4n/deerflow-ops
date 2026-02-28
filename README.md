<div align="center">
  <img src="assets/patronus-logo.png" alt="Patronus Logo" width="180" />
  <h1>Patronus</h1>
  <p><strong>A ByteDance DeerFlow Agentic System</strong></p>
  <p>
    <a href="https://github.com/8r4n/deerflow-ops"><img src="https://img.shields.io/badge/repo-deerflow--ops-blue?logo=github" alt="Repo"></a>
    <a href="https://github.com/8r4n/deerflow-skills"><img src="https://img.shields.io/badge/skills-deerflow--skills-green?logo=github" alt="Skills"></a>
    <a href="https://github.com/bytedance/deer-flow"><img src="https://img.shields.io/badge/runtime-ByteDance%20DeerFlow-orange?logo=github" alt="DeerFlow"></a>
    <a href="https://github.com/features/codespaces"><img src="https://img.shields.io/badge/runs%20on-GitHub%20Codespaces-blueviolet?logo=github" alt="Codespaces"></a>
  </p>
  <p><em>Operations, memory, and run journal for a cloud-hosted autonomous assistant.</em></p>
</div>

---

## Overview

**Patronus** is an autonomous personal assistant built on [ByteDance DeerFlow](https://github.com/bytedance/deer-flow) for agent orchestration, [Model Context Protocol (MCP)](https://modelcontextprotocol.io) for tool integration, and [GitHub Codespaces](https://github.com/features/codespaces) for safe, cloud-hosted execution. All durable memory, run logs, and mission records live as structured **GitHub Issues** — providing a transparent, portable, and auditable audit trail.

| Repository | Role |
|------------|------|
| [`8r4n/deerflow-ops`](https://github.com/8r4n/deerflow-ops) ← **this repo** | Issue-based durable memory, run logs, mission tracking, and bootstrap docs |
| [`8r4n/deerflow-skills`](https://github.com/8r4n/deerflow-skills) | Skill implementations — one folder per skill with Dockerfiles, tests, and manifests |
| [`bytedance/deer-flow`](https://github.com/bytedance/deer-flow) (submodule → `deer-flow/`) | Upstream DeerFlow runtime for agent orchestration |

---

## Architecture

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

**Core components:**

| Component | Purpose |
|-----------|---------|
| **DeerFlow** | Agent orchestration — planner → executor → verifier loop |
| **GitHub MCP** | Read/write issues and PRs, search code, update progress, plan missions |
| **Web Fetch MCP** | Ingest external documentation and web sources |
| **GitHub Codespaces** | Cloud-hosted, ephemeral execution environment |
| **GitHub Container Registry** | Versioned skill image publishing (`ghcr.io`) |
| **GitHub Issues** | Durable memory store, audit trail, and programmatic progress interface |

See [`docs/whitepaper.md`](docs/whitepaper.md) for the full design rationale.

---

## Quick start

### Prerequisites

| Requirement | Minimum |
|-------------|---------|
| GitHub account | With Codespaces access |
| Git | 2.x |
| Python | 3.11+ |
| Node.js | 18+ |
| Make | any |

You also need:
- API keys for at least one LLM provider (OpenAI, Anthropic, etc.) and a search provider (Tavily recommended)
- A `GITHUB_TOKEN` with `repo`, `write:packages`, and `codespace` scopes

### 1. Open in GitHub Codespaces (recommended)

Click **Code → Codespaces → Create codespace on main** in the GitHub UI, or use the CLI:

```bash
gh codespace create --repo 8r4n/deerflow-ops --machine standardLinux32gb
```

The dev container automatically initializes the submodule and installs all dependencies. Configure API keys (step 2), then start services (step 3).

### 1b. Clone locally

```bash
git clone --recurse-submodules https://github.com/8r4n/deerflow-ops.git
cd deerflow-ops
```

<details>
<summary>Already cloned without submodules?</summary>

```bash
git submodule update --init --recursive
```

</details>

### 2. Configure DeerFlow

```bash
cd deer-flow
make config          # generates .env and config.yaml from examples (auto-run in Codespaces)
```

Edit `deer-flow/.env` with your API keys:

```bash
OPENAI_API_KEY=your-openai-api-key
TAVILY_API_KEY=your-tavily-api-key
```

Edit `deer-flow/config.yaml` to select your preferred model(s). See the [upstream configuration guide](https://github.com/bytedance/deer-flow/blob/main/backend/docs/CONFIGURATION.md) for details.

To enable the aio sandbox (isolated Docker-based code execution), set this in `deer-flow/config.yaml`:

```yaml
sandbox:
  use: src.community.aio_sandbox:AioSandboxProvider
```

The aio sandbox image is pre-pulled during Codespace creation. See `docs/playbook-phase1-tooling.md` for details.

### 3. Start services

**GitHub Codespaces (recommended):**

```bash
cd deer-flow
make dev                             # starts backend + frontend + nginx
```

Access the UI via Codespace port-forwarding on port **2026**.

**Local development:**

```bash
cd deer-flow
pip install -e ".[dev]" && make dev
```

### 4. MCP server reference

| Server | Purpose | Authentication |
|--------|---------|----------------|
| **GitHub MCP** | Issues, PRs, code search, progress updates | `GITHUB_TOKEN` (`repo`, `write:packages`, `codespace`) |
| **Web Fetch MCP** | Ingest external documentation | None required |
| **Codespaces MCP** | Manage Codespace lifecycle | Planned — see Phase 1 roadmap |

### 5. Keep DeerFlow up to date

```bash
cd deer-flow && git fetch origin && git checkout main && git pull
cd .. && git add deer-flow && git commit -m "Update deer-flow submodule"
```

---

## Repository structure

```
deerflow-ops/
├── README.md                        ← you are here
├── extensions_config.json           ← MCP server configuration
├── assets/                          ← project logo and images
├── deer-flow/                       ← bytedance/deer-flow submodule
├── .devcontainer/
│   └── devcontainer.json            ← GitHub Codespaces dev container
├── docs/
│   ├── whitepaper.md                ← full system design
│   ├── deerflow-software-architecture.md
│   ├── labels.md                    ← GitHub label taxonomy
│   ├── index-issues.md              ← maintaining pinned index issues
│   └── playbook-phase1-tooling.md   ← Phase 1 tooling playbook
└── .github/
    ├── ISSUE_TEMPLATE/              ← mission, run log, memory templates
    └── workflows/
        ├── ghcr-publish.yml         ← GHCR image push workflow
        └── kickoff.yml              ← automatic mission kickoff
```

---

## Memory model

All durable memory lives as GitHub Issues, organized by label:

| Label | Purpose |
|-------|---------|
| `memory:skill` | Skill documentation and metadata |
| `memory:repo` | Repository evaluations (adopted / rejected) |
| `memory:playbook` | Reusable procedures and setup guides |
| `run:log` | Individual execution logs |
| `mission:*` | Mission categories (comms, dev, research, …) |
| `status:*` | Lifecycle state (active, blocked, done, deprecated) |

→ [`docs/labels.md`](docs/labels.md) — full taxonomy  
→ [`docs/index-issues.md`](docs/index-issues.md) — how pinned index issues are maintained

---

## Roadmap

| Phase | Description | Status |
|-------|-------------|--------|
| **0** | Repo bootstrap — templates, docs, labels, indexes | ✅ Done |
| **1** | Tooling foundation — GitHub MCP, Codespaces, GHCR, web fetch MCP | ✅ Done |
| **2** | Template skill — canonical `_template` skeleton with GHCR publish | 🔜 Next |
| **3** | First autonomous skill acquisition run (in Codespaces) | 🔜 Planned |
| **4+** | Expand mission coverage (planning, research, automation) | 🔜 Planned |

---

## Resources

- 📄 [System whitepaper](docs/whitepaper.md)
- 🛠 [DeerFlow Skills repo](https://github.com/8r4n/deerflow-skills)
- 🔗 [ByteDance DeerFlow upstream](https://github.com/bytedance/deer-flow#documentation)

---

## License

Maintained by [@8r4n](https://github.com/8r4n). The `deer-flow/` submodule is licensed under the [MIT License](https://github.com/bytedance/deer-flow/blob/main/LICENSE) by ByteDance.