# <skill-name>

> **Replace this file** with your skill's documentation. All sections below are required per the [skill standard](https://github.com/8r4n/deerflow-skills/blob/main/docs/skill-standard.md).

## Purpose / When to use

Describe what this skill does and when the agent should invoke it.

## How to build and run

```bash
# Build the image
make build

# Run locally
make run

# Or manually:
docker build -t ghcr.io/8r4n/deerflow-skills/<skill-name>:latest .
docker run --rm -p 8080:8080 ghcr.io/8r4n/deerflow-skills/<skill-name>:latest
```

## Tools exposed

| Tool | Description |
|------|-------------|
| `tool_name` | One-line description of what this tool does |

## Required env vars (names only)

| Variable | Purpose |
|----------|---------|
| `EXAMPLE_VAR` | Description |

## Troubleshooting / limitations

- Known edge cases and failure modes
- Security notes
