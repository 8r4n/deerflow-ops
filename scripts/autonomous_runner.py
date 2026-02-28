#!/usr/bin/env python
"""Autonomous mission runner — headless DeerFlow entrypoint.

Reads a mission issue from GitHub, constructs a DeerFlow prompt, invokes the
lead agent, and posts results back to the issue. Can run a single mission or
loop continuously polling for ``status:active`` missions.

Usage:
    # Single mission
    python scripts/autonomous_runner.py --mission-issue 42 --mission-repo 8r4n/deerflow-ops

    # Continuous loop (polls every POLL_INTERVAL seconds)
    python scripts/autonomous_runner.py --loop --mission-repo 8r4n/deerflow-ops

Environment variables:
    GITHUB_TOKEN          GitHub token with repo scope (required)
    OPENAI_API_KEY        LLM provider API key (required by DeerFlow)
    TAVILY_API_KEY        Search provider API key (required by DeerFlow)
    POLL_INTERVAL         Seconds between polls in loop mode (default: 60)
    MAX_ITERATIONS        Maximum missions to process in loop mode (default: 0 = unlimited)
    DEER_FLOW_EXTENSIONS_CONFIG_PATH  Path to MCP config (default: ../extensions_config.json)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("autonomous_runner")

# ---------------------------------------------------------------------------
# GitHub helpers (using `gh` CLI — available in Codespaces and Actions)
# ---------------------------------------------------------------------------

GITHUB_TOKEN_ENV = "GITHUB_TOKEN"
MAX_COMMENT_LENGTH = 3000


def _run_gh(*args: str) -> str:
    """Run a ``gh`` CLI command and return its stdout."""
    cmd = ["gh"] + list(args)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            f"gh command failed: {' '.join(cmd)}\nstderr: {exc.stderr}"
        ) from exc
    return result.stdout.strip()


def fetch_issue(repo: str, issue_number: int) -> dict:
    """Fetch an issue's title, body, and labels via ``gh``."""
    raw = _run_gh(
        "issue", "view", str(issue_number),
        "--repo", repo,
        "--json", "title,body,labels,number,state",
    )
    return json.loads(raw)


def post_comment(repo: str, issue_number: int, body: str) -> None:
    """Post a comment on a GitHub issue."""
    _run_gh(
        "issue", "comment", str(issue_number),
        "--repo", repo,
        "--body", body,
    )


def list_active_missions(repo: str) -> list[dict]:
    """Return all open issues labelled ``status:active`` with a ``mission:*`` label."""
    raw = _run_gh(
        "issue", "list",
        "--repo", repo,
        "--label", "status:active",
        "--state", "open",
        "--json", "number,title,labels",
        "--limit", "50",
    )
    issues = json.loads(raw)
    # Keep only issues that also carry a mission:* label
    return [
        iss for iss in issues
        if any(lbl["name"].startswith("mission:") for lbl in iss.get("labels", []))
    ]

# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------


def build_mission_prompt(issue: dict, repo: str) -> str:
    """Turn a mission issue into a DeerFlow prompt."""
    title = issue.get("title", "")
    body = issue.get("body", "") or ""
    number = issue.get("number", "?")
    labels = ", ".join(lbl["name"] for lbl in issue.get("labels", []))

    return (
        f"You are processing mission issue #{number} from {repo}.\n\n"
        f"**Title:** {title}\n"
        f"**Labels:** {labels}\n\n"
        f"**Mission body:**\n{body}\n\n"
        "Instructions:\n"
        "1. Create a run:log issue in the same repo to track your progress.\n"
        "2. Execute the mission according to its objective and constraints.\n"
        "3. Post progress updates as comments on the run:log issue.\n"
        "4. When done, post a summary comment on this mission issue and close the run log.\n"
    )

# ---------------------------------------------------------------------------
# DeerFlow invocation
# ---------------------------------------------------------------------------


async def invoke_deerflow(prompt: str, model_name: str | None = None, issue_number: int = 0) -> str:
    """Invoke the DeerFlow lead agent with *prompt* and return its final response."""
    # Ensure the deer-flow backend is importable
    deer_flow_backend = Path(__file__).resolve().parent.parent / "deer-flow" / "backend"
    if str(deer_flow_backend) not in sys.path:
        sys.path.insert(0, str(deer_flow_backend))

    from dotenv import load_dotenv

    env_file = deer_flow_backend / ".env"
    if env_file.exists():
        load_dotenv(str(env_file))

    from langchain_core.messages import HumanMessage

    from src.agents import make_lead_agent

    # Optionally initialise MCP tools
    try:
        from src.mcp import initialize_mcp_tools
        await initialize_mcp_tools()
    except Exception as exc:
        logger.warning("MCP tool initialisation skipped: %s", exc)

    config: dict = {
        "configurable": {
            "thread_id": f"mission-{issue_number}-{int(time.time())}",
            "thinking_enabled": True,
            "is_plan_mode": True,
            "subagent_enabled": True,
        }
    }
    if model_name:
        config["configurable"]["model_name"] = model_name

    agent = make_lead_agent(config)

    logger.info("Invoking DeerFlow agent …")
    state = {"messages": [HumanMessage(content=prompt)]}
    result = await agent.ainvoke(state, config=config)

    if result.get("messages"):
        return result["messages"][-1].content
    return "(no response)"

# ---------------------------------------------------------------------------
# Single-mission runner
# ---------------------------------------------------------------------------


async def run_single_mission(
    repo: str,
    issue_number: int,
    model: str | None = None,
) -> None:
    """Fetch a mission issue, invoke DeerFlow, and post the result."""
    logger.info("Fetching mission issue #%d from %s", issue_number, repo)
    issue = fetch_issue(repo, issue_number)

    if issue.get("state") != "OPEN":
        logger.warning("Issue #%d is not open (state=%s) — skipping.", issue_number, issue.get("state"))
        return

    prompt = build_mission_prompt(issue, repo)
    logger.info("Prompt length: %d chars", len(prompt))

    post_comment(repo, issue_number, "🦌 **Autonomous Runner** — processing this mission …")

    try:
        response = await invoke_deerflow(prompt, model_name=model, issue_number=issue_number)
        summary = response[:MAX_COMMENT_LENGTH]
        post_comment(
            repo, issue_number,
            f"✅ **Autonomous Runner** — mission processed.\n\n{summary}",
        )
        logger.info("Mission #%d completed.", issue_number)
    except Exception as exc:
        logger.exception("Mission #%d failed.", issue_number)
        post_comment(
            repo, issue_number,
            f"❌ **Autonomous Runner** — error: `{exc}`",
        )

# ---------------------------------------------------------------------------
# Continuous loop
# ---------------------------------------------------------------------------


async def run_loop(
    repo: str,
    model: str | None = None,
    poll_interval: int = 60,
    max_iterations: int = 0,
) -> None:
    """Poll for ``status:active`` missions and process them one at a time.

    Args:
        repo: GitHub repository (``owner/name``).
        model: Optional LLM model override.
        poll_interval: Seconds between polls.
        max_iterations: Stop after this many missions (0 = unlimited).
    """
    processed = 0
    logger.info(
        "Starting agentic loop — repo=%s poll=%ds max_iterations=%s",
        repo, poll_interval, max_iterations or "unlimited",
    )

    while True:
        try:
            missions = list_active_missions(repo)
        except Exception as exc:
            logger.error("Failed to list missions: %s", exc)
            await asyncio.sleep(poll_interval)
            continue

        if not missions:
            logger.info("No active missions — sleeping %ds …", poll_interval)
            await asyncio.sleep(poll_interval)
            continue

        for mission in missions:
            issue_number = mission["number"]
            logger.info(
                "Found active mission #%d: %s",
                issue_number, mission.get("title", ""),
            )
            await run_single_mission(repo, issue_number, model=model)
            processed += 1

            if max_iterations and processed >= max_iterations:
                logger.info("Reached max_iterations=%d — stopping.", max_iterations)
                return

        await asyncio.sleep(poll_interval)

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Autonomous DeerFlow mission runner",
    )
    parser.add_argument(
        "--mission-issue",
        type=int,
        default=None,
        help="Process a single mission issue by number",
    )
    parser.add_argument(
        "--mission-repo",
        type=str,
        default=os.environ.get("MISSION_REPO", ""),
        help="GitHub repository (owner/name)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=os.environ.get("MODEL_OVERRIDE", None),
        help="LLM model override",
    )
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Run continuously polling for active missions",
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=int(os.environ.get("POLL_INTERVAL", "60")),
        help="Seconds between polls in loop mode (default: 60)",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=int(os.environ.get("MAX_ITERATIONS", "0")),
        help="Max missions to process in loop mode (0 = unlimited)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    if not args.mission_repo:
        logger.error("--mission-repo is required (or set MISSION_REPO env var)")
        sys.exit(1)

    if not os.environ.get(GITHUB_TOKEN_ENV):
        logger.error("GITHUB_TOKEN environment variable is required")
        sys.exit(1)

    if args.loop:
        asyncio.run(
            run_loop(
                repo=args.mission_repo,
                model=args.model,
                poll_interval=args.poll_interval,
                max_iterations=args.max_iterations,
            )
        )
    elif args.mission_issue:
        asyncio.run(
            run_single_mission(
                repo=args.mission_repo,
                issue_number=args.mission_issue,
                model=args.model,
            )
        )
    else:
        logger.error("Provide --mission-issue <number> or --loop")
        sys.exit(1)


if __name__ == "__main__":
    main()
