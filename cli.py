"""
CLI entry point for PowerShell Agent.

Commands:
  powershell-agent "do something"       run agent with prompt
  powershell-agent                      interactive mode
  powershell-agent --history            list past sessions
  powershell-agent --replay <id>         replay a saved session
  powershell-agent --github "query"     query GitHub via MCP (needs GITHUB_TOKEN)
  powershell-agent --review "..."       human-in-the-loop review mode
"""

import argparse
import asyncio
import os
import sys
import warnings

# Suppress asyncio cleanup warnings on Windows
warnings.filterwarnings("ignore", category=ResourceWarning, module="asyncio")

from powershell_agent import PowerShellAgent, __version__, list_sessions, load_session, clear_sessions
from powershell_agent.config import DEFAULT_MODEL, MAX_ITERATIONS
from powershell_agent.mcp import run_with_github_mcp
from powershell_agent.ui import (
    header,
    prompt as ui_prompt,
    history_table,
    error,
    success,
    warning,
    info,
    usage,
    separator,
    GREEN,
    RESET,
)


def _header(model: str) -> None:
    header(__version__, model, MAX_ITERATIONS)


def _check_rate_limit(model: str) -> None:
    """Check and display Groq API rate limits."""
    try:
        from groq import Groq
        client = Groq()
        
        # Use the model user specified or default
        check_model = model
        
        resp = client.chat.completions.with_raw_response.create(
            model=check_model,
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=1,
        )
        
        headers = resp.headers
        remaining_requests = headers.get("x-ratelimit-remaining-requests", "?")
        remaining_tokens = headers.get("x-ratelimit-remaining-tokens", "?")
        limit_requests = headers.get("x-ratelimit-limit-requests", "?")
        limit_tokens = headers.get("x-ratelimit-limit-tokens", "?")
        
        print(f"\n{GREEN}Rate Limits for model: {check_model}{RESET}")
        print(f"  Requests: {remaining_requests} / {limit_requests} remaining")
        print(f"  Tokens:   {remaining_tokens} / {limit_tokens} remaining")
        print()
    except Exception as exc:
        error(f"Failed to check rate limits: {exc}", None)


def _list_models() -> None:
    """List all available Groq models."""
    try:
        from groq import Groq
        client = Groq()
        
        models = client.models.list()
        
        print(f"\n{GREEN}Available Groq Models:{RESET}")
        for m in models.data:
            print(f"  - {m.id}")
        print()
    except Exception as exc:
        error(f"Failed to list models: {exc}", None)


def _replay_session(session_id: str) -> None:
    data = load_session(session_id)
    if not data:
        error(f"Session '{session_id}' not found.", None)
        return
    print(f"\nSession: {data['id']}")
    print(f"Prompt:  {data['user_prompt']}")
    print(f"Started: {data['started_at']}")
    print(f"Iterations: {data['iterations']}  /  Commands: {data['commands_run']}\n")
    for i, cmd in enumerate(data.get("commands", []), 1):
        print(f"[{i}] {cmd['command']}")
        print(f"     status={cmd['status']}  rc={cmd['return_code']}")
        if cmd.get("output_preview"):
            preview = cmd["output_preview"].replace("\n", "\n     ")
            print(f"     {preview}")
        print()
    print(f"Final response:\n{data.get('final_response', '')}")


async def _run_agent(args: argparse.Namespace, user_prompt: str) -> None:
    agent = PowerShellAgent(
        review_mode=args.review,
        model=args.model or None,
        max_iterations=args.iterations,
    )
    if args.review:
        warning("Review mode on: you will approve each command.\n")

    ui_prompt(user_prompt)

    response = await agent.run(user_prompt)

    print(separator())
    print(f"Result:")
    print(f"  {response}")
    print(separator())


async def main() -> None:
    parser = argparse.ArgumentParser(
        prog="powershell-agent",
        description="AI-powered PowerShell agentic tool (Groq + GitHub MCP)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("prompt", nargs="*", help="Natural language prompt")
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--model", type=str, help="Override LLM model")
    parser.add_argument("--review", action="store_true", help="Review each command before execution")
    parser.add_argument("--iterations", type=int, default=MAX_ITERATIONS, help=f"Max agent iterations (default {MAX_ITERATIONS})")
    parser.add_argument("--history", action="store_true", help="List past sessions")
    parser.add_argument("--clear-history", action="store_true", help="Delete all past sessions from disk")
    parser.add_argument("--replay", type=str, metavar="SESSION_ID", help="Replay a saved session")
    parser.add_argument("--github", type=str, metavar="QUERY", help="Query GitHub via MCP Responses API")
    parser.add_argument("--no-stream", action="store_true", help="Disable real-time streaming output")
    parser.add_argument("--rate", action="store_true", help="Check Groq API rate limits")
    parser.add_argument("--models", action="store_true", help="List all available Groq models")

    args = parser.parse_args()

    model = args.model or os.getenv("MODEL_PS", DEFAULT_MODEL)
    _header(model)

    if args.rate:
        rate_model = args.model or os.getenv("MODEL_PS", DEFAULT_MODEL)
        _check_rate_limit(rate_model)
        return

    if args.models:
        _list_models()
        return

    if args.history:
        history_table(list_sessions(limit=20))
        return

    if args.clear_history:
        count = clear_sessions()
        success(f"Cleared {count} saved session(s) from history.")
        return

    if args.replay:
        _replay_session(args.replay)
        return

    if args.github:
        print(f"\nGitHub MCP query: {args.github}\n")
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            warning("GITHUB_TOKEN not set, proceeding without auth (public repos only).\n")
        try:
            result = run_with_github_mcp(args.github, github_token=token)
            print(result)
        except ValueError as exc:
            error(str(exc), None)
        return

    if args.prompt:
        user_prompt = " ".join(args.prompt)
    else:
        info("Interactive mode. Enter your request:\n")
        user_prompt = input("You: ").strip()
        if not user_prompt:
            info("No prompt. Exiting.")
            return

    await _run_agent(args, user_prompt)


def cli() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    asyncio.run(main())
