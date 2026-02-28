# Playbook: Phase 4 — Agentic Loop (Continuous Operation)

**Status:** active  
**Phase:** 4  
**Date:** 2026-02-28  

---

## Purpose

Documents how the autonomous runner implements a continuous agentic loop: polling for active missions, invoking DeerFlow, and posting results — enabling the system to run unattended.

---

## 1. Overview

The agentic loop is a lightweight Python script (`scripts/autonomous_runner.py`) that sits between GitHub Issues and the DeerFlow runtime. It implements the cycle:

```
┌──────────────────────────────────────────────────────────┐
│  Poll GitHub for status:active mission issues            │
│          │                                               │
│          ▼                                               │
│  Read mission body, labels, and constraints              │
│          │                                               │
│          ▼                                               │
│  Construct DeerFlow prompt from mission                  │
│          │                                               │
│          ▼                                               │
│  Invoke DeerFlow lead agent (plan → act → observe)       │
│          │                                               │
│          ▼                                               │
│  Post results back to mission issue                      │
│          │                                               │
│          ▼                                               │
│  Sleep POLL_INTERVAL, then repeat                        │
└──────────────────────────────────────────────────────────┘
```

### Two modes of operation

| Mode | Trigger | Use case |
|------|---------|----------|
| **Single mission** | `--mission-issue <number>` | Process one specific mission (used by `kickoff.yml`) |
| **Continuous loop** | `--loop` | Poll for `status:active` missions indefinitely (used in Codespaces) |

---

## 2. Prerequisites

Same as [Phase 3](playbook-phase3-autonomous-skill-acquisition.md#1-prerequisites):

- LLM API keys (`OPENAI_API_KEY`, `TAVILY_API_KEY`) as Codespaces or repository secrets
- `GITHUB_TOKEN` with `repo` scope
- DeerFlow dependencies installed (`pip install -e ".[dev]"` in `deer-flow/`)

---

## 3. Running the Autonomous Runner

### 3.1 Single mission (from CLI or CI)

```bash
python scripts/autonomous_runner.py \
  --mission-issue 42 \
  --mission-repo 8r4n/deerflow-ops
```

This:
1. Fetches issue #42 via `gh issue view`
2. Builds a DeerFlow prompt from the issue title, body, and labels
3. Invokes the DeerFlow lead agent
4. Posts the agent's response as a comment on the issue

### 3.2 Continuous loop (in Codespaces)

```bash
python scripts/autonomous_runner.py \
  --loop \
  --mission-repo 8r4n/deerflow-ops \
  --poll-interval 60
```

This polls every 60 seconds for open issues with the `status:active` label and a `mission:*` label, then processes each one sequentially.

### 3.3 Via the kickoff workflow

The `.github/workflows/kickoff.yml` workflow invokes the runner automatically:

- **Manual dispatch:** `gh workflow run kickoff.yml -f mission_issue=42`
- **Auto-trigger:** Label an issue with `status:active` → workflow fires

If `OPENAI_API_KEY` is not configured as a repository secret, the step logs a notice and exits gracefully — no error, no failure.

---

## 4. Configuration

| Parameter | CLI flag | Env var | Default |
|-----------|----------|---------|---------|
| Mission issue | `--mission-issue` | `MISSION_ISSUE` | — |
| Repository | `--mission-repo` | `MISSION_REPO` | — |
| LLM model | `--model` | `MODEL_OVERRIDE` | DeerFlow default |
| Poll interval | `--poll-interval` | `POLL_INTERVAL` | 60s |
| Max iterations | `--max-iterations` | `MAX_ITERATIONS` | 0 (unlimited) |

### Environment variables (required)

| Variable | Purpose |
|----------|---------|
| `GITHUB_TOKEN` | GitHub API access (via `gh` CLI) |
| `OPENAI_API_KEY` | LLM provider key for DeerFlow |
| `TAVILY_API_KEY` | Search tool for DeerFlow (optional) |

---

## 5. Architecture

### 5.1 Components

```
scripts/autonomous_runner.py
├── GitHub helpers (fetch_issue, post_comment, list_active_missions)
│     └── Uses `gh` CLI — available in Codespaces and Actions
├── Prompt builder (build_mission_prompt)
│     └── Converts issue metadata into a structured DeerFlow prompt
├── DeerFlow invoker (invoke_deerflow)
│     └── Creates lead agent via make_lead_agent() and runs ainvoke()
├── Single-mission runner (run_single_mission)
│     └── Orchestrates: fetch → prompt → invoke → post result
└── Loop runner (run_loop)
      └── Polls → filters → processes sequentially → sleeps → repeat
```

### 5.2 Agent invocation

The runner imports DeerFlow's `make_lead_agent()` factory and calls `ainvoke()`:

```python
from src.agents import make_lead_agent
from langchain_core.messages import HumanMessage

agent = make_lead_agent(config)
result = await agent.ainvoke(
    {"messages": [HumanMessage(content=prompt)]},
    config=config,
)
```

This gives the agent full access to:
- All configured tools (GitHub MCP, web fetch, bash, file I/O)
- Sub-agent delegation
- Plan-mode todo tracking
- Middleware pipeline (sandbox, summarization, memory)

### 5.3 Error handling

- If a mission fails, an error comment is posted to the issue and the loop continues.
- Network errors during polling trigger a retry after `poll_interval`.
- The `max_iterations` flag provides a safety limit for CI environments.

---

## 6. Extending the Loop

### Adding a scheduler

For production use, wrap the runner in a cron-style scheduler:

```yaml
# .github/workflows/scheduled-loop.yml
on:
  schedule:
    - cron: '*/15 * * * *'  # every 15 minutes
jobs:
  process-missions:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          submodules: recursive
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -e deer-flow[dev]
      - run: |
          python scripts/autonomous_runner.py \
            --loop \
            --mission-repo ${{ github.repository }} \
            --max-iterations 3
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

### Adding mission prioritization

Override `list_active_missions()` to sort by priority labels (`risk:high` first) or by issue creation date.

---

## 7. Verification

- [ ] `python scripts/autonomous_runner.py --help` prints usage
- [ ] Single-mission mode fetches an issue and invokes DeerFlow
- [ ] Loop mode polls and processes missions
- [ ] Kickoff workflow invokes the runner (with API keys) or exits gracefully (without)
- [ ] Error in one mission does not stop the loop
- [ ] `max_iterations` correctly limits processing

---

## Related resources

- [Phase 3 playbook — autonomous skill acquisition](playbook-phase3-autonomous-skill-acquisition.md)
- [System whitepaper](whitepaper.md)
- [DeerFlow architecture](deerflow-software-architecture.md)
- [Label taxonomy](labels.md)
