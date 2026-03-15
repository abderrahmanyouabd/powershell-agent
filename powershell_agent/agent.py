"""
Core agentic loop.

Coordinates LLM calls, tool execution, history, and loop termination.
Review mode (human-in-the-loop) is handled here before tool dispatch.
"""

import json
import os
from typing import Any, Dict, List, Optional

from groq import Groq

from .config import DEFAULT_MODEL, DEFAULT_TEMPERATURE, MAX_ITERATIONS
from .memory import Session, save_session
from .prompt import build_system_prompt
from .tools import ToolRegistry, build_default_registry

_MAX_TOOL_RETRIES = 2

DESTRUCTIVE_TOOLS = {"copy_file", "move_file", "delete_item", "set_registry"}


class PowerShellAgent:
    """
    LLM-driven agent that iteratively calls tools to satisfy a user request.

    Features:
    - Multi-turn tool-calling loop (up to max_iterations)
    - Pluggable ToolRegistry (easy to extend with new tools)
    - Human-in-the-loop review mode: y / n / e(dit) / q(uit)
    - Every session persisted to disk via Session
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        review_mode: bool = False,
        model: Optional[str] = None,
        max_iterations: int = MAX_ITERATIONS,
        registry: Optional[ToolRegistry] = None,
    ) -> None:
        self.client = Groq(api_key=api_key) if api_key else Groq()
        self.model = model or os.getenv("MODEL_PS", DEFAULT_MODEL)
        self.review_mode = review_mode
        self.max_iterations = max_iterations
        self.registry = registry or build_default_registry()

    def _review(self, command: str) -> tuple[str, bool]:
        """
        Interactive review prompt. Returns (final_command, should_quit).
        """
        print(f"\n  Command: {command}\n")
        while True:
            choice = input("  Run? [y/n/e(dit)/q(uit)]: ").strip().lower()
            if choice == "y":
                return command, False
            elif choice == "n":
                return command, False
            elif choice == "q":
                print("  Quitting agent.\n")
                return command, True
            elif choice == "e":
                new = input(f"  New command [{command}]: ").strip()
                if new:
                    command = new
                    print(f"  Updated: {command}\n")
            else:
                print("  Use y / n / e / q")

    async def _dispatch(self, tool_call, session: Session) -> tuple[Dict[str, Any], bool]:
        """
        Parse, optionally review, then execute one tool call.
        Returns (result_dict, quit_requested).
        """
        try:
            args: Dict[str, Any] = json.loads(tool_call.function.arguments)
        except json.JSONDecodeError as exc:
            return {"status": "error", "error": f"Bad JSON from LLM: {exc}", "output": "", "return_code": -1}, False

        name = tool_call.function.name
        command_str = args.get("command") or args.get("path") or name

        if name in DESTRUCTIVE_TOOLS and not self.review_mode:
            return {
                "status": "error",
                "error": f"Destructive tool '{name}' requires --review mode for safety. Run with --review flag.",
                "output": "",
                "return_code": -1,
            }, False

        if self.review_mode:
            final_cmd, quit_now = self._review(command_str)
            if quit_now:
                return {"status": "quit", "output": "", "error": "quit", "return_code": -1}, True
            if name == "run_powershell":
                args["command"] = final_cmd

        print(f"\n  [{name}] {command_str}\n")
        result = await self.registry.call(name, args)
        session.record_command(command_str, result)
        return result, False

    async def run(self, user_prompt: str, cwd: Optional[str] = None) -> str:
        """Drive the full agentic loop, persist session, and return the final response."""
        session = Session(user_prompt)
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": build_system_prompt(cwd=cwd)},
            {"role": "user", "content": user_prompt},
        ]
        tools = self.registry.schemas()

        for iteration in range(1, self.max_iterations + 1):
            session.iterations = iteration
            print(f"\n  Iteration {iteration}/{self.max_iterations}")

            tool_retries = 0
            while True:
                try:
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        tools=tools,
                        tool_choice="auto",
                        temperature=DEFAULT_TEMPERATURE,
                    )
                    break
                except Exception as exc:
                    err = str(exc)
                    if ("tool_use_failed" in err.lower() or "400" in err) and tool_retries < _MAX_TOOL_RETRIES:
                        tool_retries += 1
                        print(f"  Tool call error (attempt {tool_retries}/{_MAX_TOOL_RETRIES}), retrying...")
                        last_msg = messages[-1]
                        if isinstance(last_msg, dict) and "content" in last_msg:
                            if "invalid JSON" not in str(last_msg["content"]):
                                last_msg["content"] = str(last_msg["content"]) + "\n\n(System note: your last output was invalid JSON. Please strictly output a valid JSON tool call.)"
                        continue
                    final = _format_api_error(err)
                    session.finish(final)
                    save_session(session)
                    return final

            msg = response.choices[0].message
            messages.append(msg)

            if not msg.tool_calls:
                final = msg.content or ""
                session.finish(final)
                save_session(session)
                return final

            for tc in msg.tool_calls:
                result, quit_now = await self._dispatch(tc, session)
                if quit_now or result.get("status") == "quit":
                    final = "Agent terminated by user."
                    session.finish(final)
                    save_session(session)
                    return final

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": tc.function.name,
                    "content": json.dumps(result, indent=2),
                })

        final = "⚠️ Max iterations reached."
        session.finish(final)
        save_session(session)
        return final


def _format_api_error(err: str) -> str:
    if "authentication" in err.lower() or "api key" in err.lower():
        return "Invalid API key. Set GROQ_API_KEY. Get one at https://console.groq.com/keys"
    if "rate" in err.lower() or "quota" in err.lower():
        return "Rate limit hit. Wait a moment and retry."
    if "timeout" in err.lower():
        return "Request timed out. Try again."
    if "tool_use_failed" in err.lower() or "400" in err:
        return "Function-calling error: the model generated an invalid tool call. Try rephrasing your request."
    return f"API Error: {err}"
