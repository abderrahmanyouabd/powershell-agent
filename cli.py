"""
CLI entry point for PowerShell Agent.

Commands:
  powershell-agent "do something"       run agent with prompt
  powershell-agent                      interactive mode
  powershell-agent --history            list past sessions
  powershell-agent --replay <id>        replay a saved session
  powershell-agent --github "query"     query GitHub via MCP (needs GITHUB_TOKEN)
  powershell-agent --review "..."       human-in-the-loop review mode
"""

import argparse
import asyncio
import os
import sys

from powershell_agent import PowerShellAgent, __version__, list_sessions, load_session
from powershell_agent.mcp import run_with_github_mcp
from powershell_agent.config import MAX_ITERATIONS


def _header() -> None:
    print(f"powershell-agent v{__version__}")
    print("-" * 40)


def _print_history() -> None:
    sessions = list_sessions(limit=20)
    if not sessions:
        print("No sessions found.")
        return
    print(f"\n{'ID':<14}  {'Started':^26}  {'Iter':>4}  {'Cmds':>4}  Prompt")
    print("-" * 74)
    for s in sessions:
        ts = s["started_at"][:19].replace("T", " ")
        print(f"{s['id']:<14}  {ts:^26}  {str(s['iterations']):>4}  {str(s['commands_run']):>4}  {s['prompt_preview']}")


def _replay_session(session_id: str) -> None:
    data = load_session(session_id)
    if not data:
        print(f"Session '{session_id}' not found.")
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
        print("Review mode on: you will approve each command.\n")

    print(f"Prompt: {user_prompt}\n")
    print("-" * 40)

    response = await agent.run(user_prompt)

    print("\n" + "-" * 40)
    print(response)
    print("-" * 40 + "\n")


async def main() -> None:
    parser = argparse.ArgumentParser(
        prog="powershell-agent",
        description="AI-powered PowerShell agentic tool (Groq + GitHub MCP)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  powershell-agent "find all python files and count them"
  powershell-agent --review "create feature branch for dark mode"
  powershell-agent --history
  powershell-agent --replay abc123def456
  powershell-agent --github "summarise recent issues in abderrahmanyouabd/powershell-agent"
  powershell-agent --iterations 5 "explain what this project does"

Environment Variables:
  GROQ_API_KEY     Groq API key (required)
  MODEL_PS         override default LLM model
  GITHUB_TOKEN     GitHub PAT for --github flag (repo scope)
  PS_TIMEOUT       PowerShell command timeout in seconds (default 300)
        """,
    )

    parser.add_argument("prompt", nargs="*", help="Natural language prompt")
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--model", type=str, help="Override LLM model")
    parser.add_argument("--review", action="store_true", help="Review each command before execution")
    parser.add_argument("--iterations", type=int, default=MAX_ITERATIONS, help=f"Max agent iterations (default {MAX_ITERATIONS})")
    parser.add_argument("--history", action="store_true", help="List past sessions")
    parser.add_argument("--replay", type=str, metavar="SESSION_ID", help="Replay a saved session")
    parser.add_argument("--github", type=str, metavar="QUERY", help="Query GitHub via MCP Responses API")
    parser.add_argument("--no-stream", action="store_true", help="Disable real-time streaming output")

    args = parser.parse_args()

    _header()

    if args.history:
        _print_history()
        return

    if args.replay:
        _replay_session(args.replay)
        return

    if args.github:
        print(f"GitHub MCP query: {args.github}\n")
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            print("GITHUB_TOKEN not set, proceeding without auth (public repos only).\n")
        try:
            result = run_with_github_mcp(args.github, github_token=token)
            print(result)
        except ValueError as exc:
            print(f"Error: {exc}")
        return

    if args.prompt:
        user_prompt = " ".join(args.prompt)
    else:
        print("Interactive mode. Enter your request:\n")
        user_prompt = input("You: ").strip()
        if not user_prompt:
            print("No prompt. Exiting.")
            return

    await _run_agent(args, user_prompt)


def cli() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    asyncio.run(main())
