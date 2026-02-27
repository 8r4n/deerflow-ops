# DeerFlow Software Architecture White Paper

## Abstract

DeerFlow (**D**eep **E**xploration and **E**fficient **R**esearch **F**low) is an open-source AI agent platform that orchestrates sub-agents, persistent memory, and sandboxed execution environments for complex, multi-step task automation. Built on LangGraph and LangChain, DeerFlow provides a production-ready runtime where autonomous agents can execute code, browse the web, manage files, delegate work to specialized sub-agents, and retain long-term context across sessions.

This white paper presents a high-level analysis of DeerFlow's software architecture, covering its layered system design, key abstractions, and the design patterns that enable extensibility, safety, and scalability.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Deployment Architecture](#2-deployment-architecture)
3. [Backend Architecture](#3-backend-architecture)
   - 3.1 [Lead Agent and Agent Factory](#31-lead-agent-and-agent-factory)
   - 3.2 [Thread State Model](#32-thread-state-model)
   - 3.3 [Middleware Pipeline](#33-middleware-pipeline)
   - 3.4 [Tool Ecosystem](#34-tool-ecosystem)
   - 3.5 [Sub-Agent System](#35-sub-agent-system)
   - 3.6 [Sandbox Execution](#36-sandbox-execution)
   - 3.7 [Memory System](#37-memory-system)
   - 3.8 [Skills System](#38-skills-system)
   - 3.9 [Model Context Protocol (MCP) Integration](#39-model-context-protocol-mcp-integration)
   - 3.10 [LLM Model Management](#310-llm-model-management)
4. [Frontend Architecture](#4-frontend-architecture)
   - 4.1 [Application Structure](#41-application-structure)
   - 4.2 [State Management](#42-state-management)
   - 4.3 [Real-Time Streaming](#43-real-time-streaming)
5. [Gateway API](#5-gateway-api)
6. [Key Architectural Patterns](#6-key-architectural-patterns)
7. [Security Considerations](#7-security-considerations)
8. [Conclusion](#8-conclusion)

---

## 1. System Overview

DeerFlow is structured as a modular, service-oriented platform composed of four primary services:

| Service | Technology | Port | Role |
|---------|-----------|------|------|
| **Frontend** | Next.js 16 / React 19 | 3000 | Web-based user interface |
| **LangGraph Server** | LangGraph / Python | 2024 | Agent orchestration and streaming |
| **Gateway API** | FastAPI / Python | 8001 | REST API for configuration, skills, memory, and uploads |
| **Nginx** | Nginx | 2026 | Reverse proxy and unified entry point |

These services communicate through well-defined interfaces: the frontend connects to the LangGraph Server via WebSocket for real-time agent streaming, and to the Gateway API via REST for configuration and auxiliary operations. Nginx acts as a single entry point that routes requests based on URL path prefixes.

```
                    ┌─────────────────────────────────┐
                    │   Nginx Reverse Proxy (:2026)   │
                    └────────┬──────────┬─────────────┘
                             │          │
              ┌──────────────┤          ├──────────────────┐
              │              │          │                  │
              ▼              ▼          ▼                  ▼
        ┌──────────┐  ┌───────────┐  ┌─────────┐  ┌────────────┐
        │ Frontend │  │ LangGraph │  │ Gateway │  │Provisioner │
        │ (:3000)  │  │  Server   │  │  API    │  │ (optional) │
        │ Next.js  │  │  (:2024)  │  │ (:8001) │  │   k3s/k8s  │
        └──────────┘  └─────┬─────┘  └────┬────┘  └────────────┘
                            │              │
                            ▼              ▼
                      ┌───────────────────────┐
                      │   Shared Components   │
                      │  ┌─────┐ ┌────────┐   │
                      │  │Tools│ │Sandbox │   │
                      │  └─────┘ └────────┘   │
                      │  ┌──────┐ ┌───────┐   │
                      │  │Memory│ │Skills │   │
                      │  └──────┘ └───────┘   │
                      └───────────────────────┘
```

---

## 2. Deployment Architecture

DeerFlow supports three deployment modes, each offering a different level of isolation for code execution:

### Local Mode

All services run directly on the host machine. The sandbox executes commands via local subprocesses with path-mapped isolation. This mode is suited for development and trusted environments.

### Docker All-in-One (AIO) Mode

Services are containerized using Docker Compose on a shared bridge network. Sandbox execution occurs within dedicated containers that are lifecycle-managed by the platform. This mode provides process-level isolation suitable for single-tenant deployments.

### Provisioner Mode

An optional Kubernetes-based provisioner service dynamically creates isolated sandbox Pods via the Kubernetes API. Each sandbox runs as an independent Pod with its own filesystem and resource limits, providing enterprise-grade multi-tenant isolation. This mode uses k3s for lightweight Kubernetes orchestration.

### Reverse Proxy Routing

Nginx provides a unified entry point on port 2026 with the following routing rules:

- `/api/langgraph/*` → LangGraph Server (agent streaming, threads)
- `/api/*` → Gateway API (models, skills, memory, uploads)
- `/` → Frontend (static assets, pages)

CORS handling is centralized at the Nginx layer to prevent duplication across upstream services.

---

## 3. Backend Architecture

The backend is a Python application (3.12+) organized into modular subsystems under `backend/src/`. Each subsystem has a clearly defined responsibility and communicates with others through well-defined interfaces.

### 3.1 Lead Agent and Agent Factory

The **Lead Agent** is the central orchestration entity in DeerFlow. It is constructed by the `make_lead_agent()` factory function, which assembles the agent from its constituent parts at runtime:

```
make_lead_agent(config)
  → resolve model configuration
  → create_chat_model(model_name, thinking_enabled)
  → build middleware chain from config
  → collect tools (built-in + configured + MCP)
  → compose system prompt with skills awareness
  → return streaming-capable agent
```

The factory pattern enables the agent to be fully configured through external configuration (`config.yaml`) without code changes. Model selection, tool availability, middleware composition, and behavioral parameters are all config-driven.

The Lead Agent operates as a **stateful conversation loop**: it receives user messages, processes them through the middleware pipeline, invokes tools as needed, and returns streaming responses. The agent maintains state across turns via the Thread State model.

### 3.2 Thread State Model

The `ThreadState` class extends LangChain's `AgentState` to capture the full execution context of a conversation thread:

| Field | Type | Purpose |
|-------|------|---------|
| `messages` | list | Conversation history (inherited from AgentState) |
| `artifacts` | list | Files created during execution (deduplicated) |
| `viewed_images` | dict | Base64-encoded images for vision-capable models |
| `sandbox` | SandboxState | Active sandbox identifier and configuration |
| `thread_data` | ThreadDataState | Workspace, uploads, and outputs directory paths |
| `title` | str | Auto-generated conversation title |
| `todos` | list | Task plan (when plan mode is enabled) |
| `uploaded_files` | list | Metadata for user-uploaded files |

Custom **state reducers** handle merge semantics; for example, `merge_artifacts()` deduplicates file lists across state updates, and `merge_viewed_images()` supports additive merges while allowing full replacement when an empty dictionary is provided.

### 3.3 Middleware Pipeline

DeerFlow employs an **ordered middleware pipeline** that intercepts and transforms agent execution at well-defined points. Each middleware is a composable unit that adds cross-cutting behavior without modifying the core agent logic.

The execution order is critical and proceeds as follows:

| Order | Middleware | Responsibility |
|-------|-----------|---------------|
| 1 | **ThreadDataMiddleware** | Initializes isolated workspace, uploads, and outputs directories |
| 2 | **UploadsMiddleware** | Processes user file uploads and injects content into messages |
| 3 | **SandboxMiddleware** | Acquires and manages sandboxed execution environments |
| 4 | **DanglingToolCallMiddleware** | Patches missing tool response messages before LLM invocation |
| 5 | **SummarizationMiddleware** | Compresses conversation context when approaching token limits |
| 6 | **TodoListMiddleware** | Tracks and updates the task plan (plan mode only) |
| 7 | **TitleMiddleware** | Auto-generates a conversation title after the first exchange |
| 8 | **MemoryMiddleware** | Queues conversation turns for persistent memory extraction |
| 9 | **ViewImageMiddleware** | Injects image details for vision-capable models |
| 10 | **SubagentLimitMiddleware** | Truncates excess parallel sub-agent invocations |
| 11 | **ClarificationMiddleware** | Intercepts user clarification requests (always last) |

This architecture follows the **Chain of Responsibility** pattern, where each middleware can modify the state, short-circuit execution, or pass control to the next handler. The ordering ensures dependencies are satisfied: for example, `SandboxMiddleware` must run before any tool that executes code, and `ClarificationMiddleware` must be last to properly handle user interruptions.

### 3.4 Tool Ecosystem

Tools are the agent's interface to the external world. DeerFlow provides a layered tool system:

**Built-in Tools:**
- `present_file_tool` — Display generated files to the user
- `ask_clarification_tool` — Request additional input from the user
- `view_image_tool` — Process images for vision-capable models
- `task_tool` — Delegate work to sub-agents

**Configured Tools** (from `config.yaml`):
- Web tools: `web_search` (Tavily), `web_fetch` (Jina), `image_search` (DuckDuckGo)
- File I/O: `ls`, `read_file`, `write_file`, `str_replace`
- Execution: `bash`

**MCP Tools:** Dynamically loaded from external Model Context Protocol servers.

The `get_available_tools()` function acts as a tool registry, resolving the active tool set based on configuration, model capabilities, and the current execution context (e.g., sub-agents may have restricted tool access).

### 3.5 Sub-Agent System

DeerFlow supports **parallel task delegation** through a sub-agent system. When the Lead Agent determines that a task benefits from parallel execution, it invokes the `task_tool` to spawn up to three concurrent sub-agents.

Each sub-agent is an isolated agent instance that:

- Inherits the parent's sandbox and workspace directories
- Has its own filtered tool set (configurable allow/deny lists)
- Runs in a dedicated thread with a configurable timeout (default: 15 minutes)
- Captures streaming output for real-time status reporting

The `SubagentExecutor` manages the lifecycle:

```
SubagentExecutor._create_agent()
  → Create LangChain agent with ThreadState schema
  → Apply ThreadDataMiddleware (lazy_init=True, reuses parent paths)
  → Apply SandboxMiddleware (lazy_init=True, reuses parent sandbox)

execute_async()
  → Submit to thread pool
  → Track status: PENDING → RUNNING → COMPLETED / FAILED / TIMED_OUT
  → Capture AI messages during streaming
```

Built-in sub-agent types include a **general-purpose executor** (all tools except task delegation) and a **bash agent** (command execution specialist). Custom sub-agents can be defined through configuration.

### 3.6 Sandbox Execution

The sandbox system provides isolated execution environments for code and commands. It is designed around a provider abstraction:

- **`Sandbox`** — Abstract base class defining the execution interface: `execute_command()`, `read_file()`, `write_file()`, `list_dir()`
- **`LocalSandboxProvider`** — Local filesystem implementation using subprocess execution with path mappings between container and host paths
- **Remote Providers** — Docker container and Kubernetes Pod implementations for stronger isolation

Key design decisions:

- **Lazy initialization**: Sandboxes are created on first use and reused across conversation turns, minimizing resource overhead.
- **Path mapping**: Container-style paths (e.g., `/mnt/workspace/`) are transparently mapped to host paths, allowing consistent path references regardless of deployment mode.
- **Lifecycle management**: Sandboxes are acquired, tracked in thread state, and released when no longer needed.

### 3.7 Memory System

DeerFlow implements **persistent, LLM-powered memory** that extracts and retains key facts across conversations:

**Memory Schema:**
```json
{
  "user": {
    "workContext": "...",
    "personalContext": "...",
    "topOfMind": "..."
  },
  "history": {
    "recentMonths": "...",
    "earlierContext": "...",
    "longTermBackground": "..."
  },
  "facts": ["fact1", "fact2", "..."]
}
```

The memory system operates through three components:

1. **MemoryMiddleware** — Filters conversation messages (keeping only user inputs and final responses), then queues them for memory extraction.
2. **Memory Queue** — A debounced async queue that batches conversation updates to prevent excessive LLM calls.
3. **Memory Updater** — Uses an LLM to summarize conversations and extract structured facts, writing updates to a local JSON store with file-mtime-based cache invalidation.

Configuration allows tuning the maximum number of stored facts (default: 100) and the confidence threshold for fact extraction (default: 0.7).

### 3.8 Skills System

Skills are **domain-specific workflows** defined as Markdown files that provide the agent with structured guidance for specialized tasks. Each skill resides in a directory under `skills/public/` or `skills/custom/` and contains a `SKILL.md` file with metadata and instructions.

The skills system supports:

- **Progressive loading** — Skills are loaded on-demand to minimize context consumption.
- **Category-based organization** — Public (community-maintained) and custom (user-defined) categories.
- **Enable/disable control** — Managed through `extensions_config.json`.
- **Container mounting** — Skills are mounted at `/mnt/skills/{category}/{name}` in sandboxed environments.

Built-in skills span research and analysis, content creation (reports, slides, podcasts, videos), web development, data visualization, and developer tooling.

### 3.9 Model Context Protocol (MCP) Integration

DeerFlow integrates with external tool servers via the **Model Context Protocol (MCP)**, an open standard for connecting AI models to external data sources and tools.

The MCP subsystem provides:

- **Multi-transport support** — stdio, Server-Sent Events (SSE), and HTTP connections to MCP servers.
- **Tool caching with invalidation** — MCP tools are cached in memory and automatically refreshed when the configuration file is modified (tracked via file mtime).
- **Dynamic configuration** — MCP servers can be added or removed through the Gateway API, with changes reflected in the next tool resolution cycle.

### 3.10 LLM Model Management

The model subsystem provides a **factory-based abstraction** over multiple LLM providers:

- **Provider support**: OpenAI, Anthropic, DeepSeek, and other LangChain-compatible providers.
- **Capability flags**: Models declare support for `thinking` (extended reasoning) and `vision` (image analysis), enabling the agent to adapt its behavior.
- **Runtime configuration**: Model parameters (temperature, max tokens, API keys) are resolved from `config.yaml` and can be overridden at runtime.
- **Thinking mode**: When enabled, models receive additional configuration via `when_thinking_enabled` settings, supporting providers with extended reasoning capabilities.

---

## 4. Frontend Architecture

The frontend is a Next.js 16 application built with React 19, Tailwind CSS 4, and a component library based on Radix UI primitives.

### 4.1 Application Structure

The frontend follows the Next.js App Router convention:

| Route | Purpose |
|-------|---------|
| `/` | Landing page with feature showcase |
| `/workspace` | Main application workspace |
| `/workspace/chats/[thread_id]` | Individual conversation threads |

Core modules are organized under `src/core/`:

- **api** — LangGraph API client (singleton pattern)
- **threads** — Thread lifecycle management (hooks, types, utilities)
- **messages** — Message parsing and rendering utilities
- **artifacts** — Generated file and document management
- **skills** — Skill discovery and configuration
- **memory** — User memory management
- **mcp** — MCP server configuration
- **uploads** — File upload handling
- **i18n** — Internationalization
- **config** — Environment configuration
- **settings** — User preferences

### 4.2 State Management

The frontend employs a hybrid state management approach:

- **React Query** (`@tanstack/react-query`) for server state — caching, background refresh, and optimistic updates for thread lists, model configurations, and skill inventories.
- **React Context API** for thread-scoped state — the `ThreadContext` provides the active thread's data, stream handle, and control functions to descendant components.
- **Custom Hooks** for domain logic — `useThreadStream()`, `useSubmitThread()`, and `useThreads()` encapsulate complex state interactions behind clean interfaces.

### 4.3 Real-Time Streaming

The frontend communicates with the LangGraph Server via the **LangGraph SDK** for real-time conversation streaming:

```typescript
useStream<AgentThreadState>({
  client: getAPIClient(),
  assistantId: "lead_agent",
  threadId,
  streamMode: ["values", "messages-tuple", "custom"],
  streamSubgraphs: true,
  onCustomEvent: handleTaskEvents,
  onFinish: invalidateCache,
})
```

This streaming connection supports multiple event types:

- **values** — Full state snapshots for conversation updates
- **messages-tuple** — Incremental message chunks for real-time text display
- **custom** — Application-defined events (e.g., sub-agent task progress)

The frontend renders streaming content as it arrives, providing a responsive user experience even for long-running agent tasks.

---

## 5. Gateway API

The Gateway API is a FastAPI application that provides REST endpoints for operations outside the core agent conversation loop:

| Endpoint Group | Responsibility |
|----------------|---------------|
| `/api/models` | List available LLM models and their capabilities |
| `/api/mcp` | Manage MCP server configurations |
| `/api/skills` | Discover and toggle skills |
| `/api/memory` | Read and manage persistent memory |
| `/api/uploads` | Handle file uploads with format conversion |
| `/api/artifacts` | Serve generated artifacts |

The Gateway API shares the same Python codebase as the LangGraph Server but runs as a separate service, enabling independent scaling and clear separation between real-time agent operations and administrative REST operations.

---

## 6. Key Architectural Patterns

### Config-Driven Architecture

Nearly every aspect of DeerFlow's behavior is externally configurable: models, tools, skills, sandbox mode, middleware composition, and memory parameters. This enables deployment customization without code changes and supports diverse use cases from a single codebase.

### Middleware Composition

The ordered middleware pipeline provides clean separation of cross-cutting concerns. Each middleware operates on the shared thread state, and the ordering guarantees that dependencies between middlewares are satisfied. New behaviors can be added by inserting a new middleware at the appropriate position.

### Lazy Initialization and Resource Reuse

Sandboxes, MCP connections, and sub-agent instances are created on demand and reused across conversation turns. This balances resource efficiency with responsiveness, avoiding the overhead of creating execution environments for every interaction.

### Factory Pattern

Both agents and LLM models are constructed through factory functions that resolve configuration at runtime. This decouples the construction logic from the usage site and centralizes configuration resolution.

### Cache with File-Mtime Invalidation

The MCP tool cache and memory store use file modification time tracking to detect external changes. This simple but effective strategy ensures that configuration changes made through the Gateway API (or direct file edits) are reflected without requiring service restarts.

### Event-Driven Streaming

The LangGraph SDK provides a bidirectional streaming protocol between frontend and backend. Custom events extend this protocol for application-specific notifications (e.g., sub-agent progress), enabling a responsive UI without polling.

---

## 7. Security Considerations

DeerFlow incorporates several security measures in its architecture:

- **Sandboxed Execution**: Code execution is isolated through configurable sandbox providers, from local subprocess isolation to full Kubernetes Pod isolation.
- **Path Mapping**: Container-style path mappings prevent direct host filesystem access in sandboxed environments.
- **Tool Access Control**: Sub-agents operate with restricted tool sets, and the `task_tool` is excluded from sub-agent tool lists to prevent recursive delegation.
- **Sub-Agent Limits**: Concurrency limits (default: 3 concurrent sub-agents) and timeouts (default: 15 minutes) prevent resource exhaustion.
- **CORS Centralization**: Cross-origin request handling is managed at the Nginx layer, preventing inconsistent policies across services.
- **API Key Management**: Sensitive credentials are managed through environment variables (`.env`) and are not embedded in configuration files.

---

## 8. Conclusion

DeerFlow's architecture achieves a balance between flexibility and structure through its layered, config-driven design. The middleware pipeline provides clean extensibility for cross-cutting concerns, the sandbox abstraction enables deployment-appropriate isolation, and the sub-agent system enables parallel task execution within controlled resource bounds.

The separation of the LangGraph Server (real-time agent interactions) from the Gateway API (administrative operations) allows each to scale independently, while the Nginx reverse proxy provides a unified entry point that simplifies client integration.

By building on established frameworks (LangGraph, LangChain, FastAPI, Next.js) and open standards (Model Context Protocol), DeerFlow leverages a mature ecosystem while adding the orchestration, memory, and safety layers needed for production autonomous agent workflows.